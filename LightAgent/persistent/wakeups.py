"""Durable trigger delivery inside the existing supervisor tick, not a second scheduler."""
import math
import time
from ..security import canonical_digest
from .redaction import contains_secret
from .store import StateConflict, dumps

WAKEUP_SCHEMA_VERSION = 1


class WakeupScheduler:
    def __init__(self, store):
        self.store = store

    def schedule(self, task_id, *, due_at, idempotency_key, payload="Scheduled wakeup", interval=None, misfire="coalesce"):
        if type(due_at) not in (int, float) or not math.isfinite(due_at) or due_at < 0:
            raise ValueError("invalid trigger deadline")
        if interval is not None and (type(interval) not in (int, float) or not math.isfinite(interval) or interval <= 0):
            raise ValueError("trigger interval must be finite and positive")
        if misfire not in ("skip", "coalesce"):
            raise ValueError("unsupported missed-trigger policy")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256:
            raise ValueError("invalid trigger idempotency key")
        if not isinstance(payload, str) or not payload.strip() or len(payload.encode()) > 65536 or contains_secret(payload):
            raise ValueError("invalid wakeup payload")
        identity = canonical_digest(dict(task=task_id, key=idempotency_key))
        spec = dict(due_at=due_at, interval=interval, misfire=misfire, payload=payload)
        with self.store.transaction() as db:
            if self.store.get("agent", task_id, db) is None:
                raise KeyError(task_id)
            previous = self.store.get("wakeup", identity, db)
            if previous:
                if previous["fingerprint"] != canonical_digest(spec):
                    raise StateConflict("trigger key reused for a different schedule")
                return previous
            return self.store.put("wakeup", dict(id=identity, agent=task_id,
                schema_version=WAKEUP_SCHEMA_VERSION, **spec, fingerprint=canonical_digest(spec),
                status="pending", deliveries=0), db)

    def cancel(self, trigger_id):
        with self.store.transaction() as db:
            trigger = self.store.get("wakeup", trigger_id, db)
            if not trigger:
                raise KeyError(trigger_id)
            trigger["status"] = "cancelled"
            return self.store.put("wakeup", trigger, db)

    def deliver_due(self, *, now=None, limit=100):
        now = time.time() if now is None else now
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError("invalid trigger clock")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("invalid delivery batch limit")
        delivered = []
        with self.store.transaction() as db:
            for trigger in self.store.scan("wakeup", db=db, filters={"status": ("pending",)}):
                if len(delivered) >= limit:
                    break
                if trigger["due_at"] > now:
                    continue
                task = self.store.get("agent", trigger["agent"], db)
                if not task or task["desired"] == "cancelled" or task["status"] in ("completed", "failed", "cancelled"):
                    trigger["status"] = "cancelled"
                elif task["desired"] != "running":
                    continue
                else:
                    interval = trigger["interval"]
                    missed = interval is not None and trigger["due_at"] + interval <= now
                    if not (missed and trigger["misfire"] == "skip"):
                        key = canonical_digest(dict(trigger=trigger["id"], due=trigger["due_at"]))
                        self.store.enqueue(task["id"], trigger["payload"], key, db=db)
                        trigger["deliveries"] += 1
                        delivered.append(trigger["id"])
                        self.store.event(task["id"], "wakeup.delivered", {"trigger_id": trigger["id"], "message_id": key}, db)
                    else:
                        self.store.event(task["id"], "wakeup.missed", {"trigger_id": trigger["id"]}, db)
                    if interval is None:
                        trigger["status"] = "delivered"
                    else:
                        trigger["due_at"] += (math.floor((now - trigger["due_at"]) / interval) + 1) * interval
                self.store.put("wakeup", trigger, db)
        return delivered
