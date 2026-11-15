"""Durable responses and triggers with no UI or external service required."""
from dataclasses import replace
import time
import pytest
from LightAgent import (ExecutionService, SecurityContext, ApprovalToken, BackendCapabilities,
                        BackendProbe, BackendResult)
from LightAgent.persistent.interactions import InteractionRequests
from LightAgent.persistent.wakeups import WakeupScheduler
from LightAgent.persistent.store import StateConflict


class Backend:
    def probe(self):
        return BackendProbe("fixture", "1", BackendCapabilities(isolation="docker", network_control=True))

    async def execute(self, request):
        return BackendResult("okay")


@pytest.fixture
def live(tmp_path):
    workspace = tmp_path / "work"
    workspace.mkdir()
    service = ExecutionService(tmp_path / "state", backend_factories={"fixture": Backend})
    context = SecurityContext(user_id="alice", tenant_id="acme", project_id="demo", sandbox_required=True)
    handle = service.submit("task", workspace, backend="fixture", security_context=context)
    attempt = service.claim(handle.id)
    return service, handle, attempt, context.narrow(task_id=handle.id, attempt_id=attempt["id"])


def request(live, kind="question", payload=None, **kwargs):
    service, handle, attempt, _ = live
    return InteractionRequests(service.store).request(handle.id, attempt_id=attempt["id"], epoch=attempt["epoch"],
        kind=kind, payload=payload or {"question": "Proceed?"}, idempotency_key=kwargs.pop("idempotency_key", "one"), **kwargs)


def test_question_response_is_correlated_and_idempotent(live):
    service, handle, attempt, context = live
    first = request(live)
    assert request(live)["id"] == first["id"]
    protocol = InteractionRequests(service.store)
    assert protocol.respond(first["id"], "yes", context=context)["status"] == "responded"
    assert protocol.respond(first["id"], "yes", context=context)["answer"] == "yes"
    with pytest.raises(StateConflict):
        protocol.respond(first["id"], "no", context=context)


def test_wrong_tenant_stale_attempt_and_late_responses_fail_closed(live):
    service, handle, _, context = live
    protocol = InteractionRequests(service.store)
    first = request(live)
    with pytest.raises(PermissionError):
        protocol.respond(first["id"], "yes", context=replace(context, tenant_id="other"))
    handle.cancel()
    with pytest.raises(StateConflict):
        protocol.respond(first["id"], "yes", context=context)
    assert protocol.get(first["id"])["status"] == "cancelled"


def test_expired_response_is_persisted_as_expired(live):
    service, _, _, context = live
    first = request(live, ttl_seconds=.001)
    time.sleep(.01)
    protocol = InteractionRequests(service.store)
    with pytest.raises(StateConflict, match="expired"):
        protocol.respond(first["id"], "yes", context=context)
    assert protocol.get(first["id"])["status"] == "expired"


def test_approval_binds_exact_parameters_and_consumption_is_durable(live):
    service, _, _, context = live
    payload = dict(operation="send_report", arguments={"destination": "review"}, resource="report")
    first = request(live, "approval", payload)
    second = request(live, "approval", payload, idempotency_key="two")
    protocol = InteractionRequests(service.store)
    wrong = ApprovalToken.issue("send_report", {"destination": "public"}, context, resource="report")
    with pytest.raises(PermissionError):
        protocol.respond(first["id"], True, context=context, approval_token=wrong)
    token = ApprovalToken.issue("send_report", payload["arguments"], context, resource="report")
    protocol.respond(first["id"], True, context=context, approval_token=token)
    with pytest.raises(StateConflict):
        protocol.respond(second["id"], True, context=context, approval_token=ApprovalToken.from_dict(token.to_dict()))


def test_wakeup_delivery_is_transactional_deduplicated_and_recoverable(live):
    service, handle, _, _ = live
    scheduler = WakeupScheduler(service.store)
    trigger = scheduler.schedule(handle.id, due_at=100, idempotency_key="timer", interval=10)
    assert scheduler.deliver_due(now=135) == [trigger["id"]]
    assert scheduler.deliver_due(now=135) == []
    assert service.store.get("wakeup", trigger["id"])["due_at"] == 140
    restarted = WakeupScheduler(service.store)
    assert restarted.deliver_due(now=140) == [trigger["id"]]
    assert len(list(service.store.scan("message", handle.id))) == 2


def test_skip_misfire_and_parent_cancel_do_not_create_work(live):
    service, handle, _, _ = live
    scheduler = WakeupScheduler(service.store)
    trigger = scheduler.schedule(handle.id, due_at=100, idempotency_key="timer", interval=10, misfire="skip")
    assert scheduler.deliver_due(now=135) == []
    assert service.store.get("wakeup", trigger["id"])["due_at"] == 140
    handle.cancel()
    assert scheduler.deliver_due(now=140) == []
    assert service.store.get("wakeup", trigger["id"])["status"] == "cancelled"


def test_wakeup_idempotency_key_cannot_change_payload(live):
    service, handle, _, _ = live
    scheduler = WakeupScheduler(service.store)
    scheduler.schedule(handle.id, due_at=100, idempotency_key="timer")
    with pytest.raises(StateConflict):
        scheduler.schedule(handle.id, due_at=200, idempotency_key="timer")
