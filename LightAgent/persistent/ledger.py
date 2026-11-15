"""Transactional, idempotent execution accounting shared by domain extensions."""
from __future__ import annotations

import math
import time
from .store import StateConflict, dumps
from ..security import canonical_digest

DIMENSIONS = frozenset({"backend_calls", "model_calls", "tool_calls", "tokens", "seconds", "cost"})


class LedgerLimitExceeded(RuntimeError):
    pass


def _amounts(value, *, limits=False):
    if not isinstance(value, dict) or set(value) - DIMENSIONS:
        raise ValueError("unsupported budget dimensions")
    for amount in value.values():
        if limits and amount is None:
            continue
        if type(amount) not in (int, float) or not math.isfinite(amount) or amount < 0:
            raise ValueError("budget amounts must be nonnegative and finite")
    return dict(value)


class BudgetLedger:
    def __init__(self, store):
        self.store = store

    def open(self, account, *, limits=None, parent=None, db=None):
        limits = _amounts(limits or {}, limits=True)
        if db is None:
            with self.store.transaction() as db:
                return self.open(account, limits=limits, parent=parent, db=db)
        if not isinstance(account, str) or not account or account == parent:
            raise ValueError("invalid budget account")
        existing = self.store.get("budget_account", account, db)
        if existing:
            if existing["limits"] != limits or existing["parent"] != parent:
                raise StateConflict("budget account configuration changed")
            return existing
        if parent and self.store.get("budget_account", parent, db) is None:
            raise KeyError(parent)
        return self.store.put("budget_account", dict(id=account, agent=account, parent=parent,
                              limits=limits, used={}, reserved={}, unknown={}), db)

    def _chain(self, account, db):
        chain, seen = [], set()
        while account:
            if account in seen or len(seen) >= 64:
                raise StateConflict("invalid budget ancestry")
            seen.add(account)
            item = self.store.get("budget_account", account, db)
            if item is None:
                raise KeyError(account)
            chain.append(item)
            account = item["parent"]
        return chain

    @staticmethod
    def _key(account, key):
        if not isinstance(key, str) or not 1 <= len(key) <= 256:
            raise ValueError("invalid budget idempotency key")
        return canonical_digest({"account": account, "key": key})

    def reserve(self, account, key, amounts, *, db=None):
        amounts = _amounts(amounts)
        if db is None:
            with self.store.transaction() as db:
                return self.reserve(account, key, amounts, db=db)
        identity = self._key(account, key)
        previous = self.store.get("budget_reservation", identity, db)
        if previous:
            if previous["amounts"] != amounts:
                raise StateConflict("budget idempotency key reused with different amounts")
            return previous
        chain = self._chain(account, db)
        for item in chain:
            for dimension, limit in item["limits"].items():
                if limit is not None and (item["unknown"].get(dimension, 0) or
                        item["used"].get(dimension, 0) + item["reserved"].get(dimension, 0)
                        + amounts.get(dimension, 0) > limit):
                    raise LedgerLimitExceeded("budget exhausted or unsettled: " + dimension)
        for item in chain:
            for dimension, amount in amounts.items():
                item["reserved"][dimension] = item["reserved"].get(dimension, 0) + amount
            self.store.put("budget_account", item, db)
        return self.store.put("budget_reservation", dict(id=identity, agent=account,
                              amounts=amounts, status="reserved"), db)

    def settle(self, account, key, actual, *, unknown=(), db=None):
        actual = _amounts(actual)
        unknown = sorted(set(unknown))
        if set(unknown) - DIMENSIONS or set(unknown) & set(actual):
            raise ValueError("invalid unknown budget dimensions")
        if db is None:
            with self.store.transaction() as db:
                return self.settle(account, key, actual, unknown=unknown, db=db)
        record = self.store.get("budget_reservation", self._key(account, key), db)
        if record is None:
            raise KeyError(key)
        if record["status"] != "reserved":
            if record["actual"] != actual or record["unknown"] != unknown:
                raise StateConflict("budget settlement already committed")
            return record
        for item in self._chain(account, db):
            for dimension, amount in record["amounts"].items():
                item["reserved"][dimension] -= amount
            for dimension, amount in actual.items():
                item["used"][dimension] = item["used"].get(dimension, 0) + amount
            for dimension in unknown:
                item["unknown"][dimension] = item["unknown"].get(dimension, 0) + 1
            # Actual costs are evidence, even if the provider exceeded a reservation.
            item["overdrawn"] = any(limit is not None and item["used"].get(d, 0) > limit
                                    for d, limit in item["limits"].items())
            self.store.put("budget_account", item, db)
        record.update(status="unknown" if unknown else "settled", actual=actual, unknown=unknown)
        return self.store.put("budget_reservation", record, db)

    def reconcile(self, account, key, actual):
        actual = _amounts(actual)
        with self.store.transaction() as db:
            record = self.store.get("budget_reservation", self._key(account, key), db)
            if not record or record["status"] != "unknown":
                raise StateConflict("reservation is not awaiting usage reconciliation")
            if set(actual) != set(record["unknown"]):
                raise ValueError("reconciliation must resolve exactly the unknown dimensions")
            for item in self._chain(account, db):
                for dimension, amount in actual.items():
                    item["unknown"][dimension] -= 1
                    item["used"][dimension] = item["used"].get(dimension, 0) + amount
                item["overdrawn"] = any(limit is not None and item["used"].get(d, 0) > limit
                                        for d, limit in item["limits"].items())
                self.store.put("budget_account", item, db)
            record["actual"].update(actual)
            record.update(status="settled", unknown=[])
            return self.store.put("budget_reservation", record, db)

    def snapshot(self, account):
        value = self.store.get("budget_account", account)
        if value is None:
            raise KeyError(account)
        return value

    async def execute_backend(self, account, key, backend, request):
        """Domain adapters use the same reservation/settlement path as plain tasks."""
        with self.store.transaction() as db:
            record = self.reserve(account, key, {"backend_calls": 1, "seconds": request.timeout}, db=db)
            if record['status'] != 'reserved' or record.get('dispatched'):
                raise StateConflict('backend operation was already dispatched; reconcile or create a new attempt')
            record['dispatched'] = True
            self.store.put('budget_reservation', record, db)
        started, result = time.monotonic(), None
        try:
            result = await backend.execute(request)
            return result
        finally:
            usage = {"backend_calls": 1, "seconds": max(0, time.monotonic() - started)}
            reported = getattr(result, "usage", None) or {}
            if isinstance(reported, dict):
                for source, dimension in (("total_tokens", "tokens"), ("model_calls", "model_calls"),
                                          ("tool_calls", "tool_calls"), ("cost", "cost")):
                    value = reported.get(source)
                    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
                        usage[dimension] = value
            self.settle(account, key, usage, unknown={"tokens", "model_calls", "tool_calls", "cost"} - usage.keys())
