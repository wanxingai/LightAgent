import json
import time
from types import SimpleNamespace

from LightAgent import (
    ApprovalDecision,
    HookContext,
    HumanApprovalHook,
    HumanFeedback,
    InMemoryReviewStore,
    JsonReviewStore,
    JsonLightFlowStore,
    LightAgent,
    LightFlow,
    RunResult,
)


class FakeAgent:
    name = "writer"

    def __init__(self):
        self.calls = []

    def run(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return RunResult(content=f"agent:{query}")


def tool_context(*, metadata=None, arguments=None, user_id="alice"):
    return HookContext(
        phase="before_tool_call",
        payload={"tool_name": "pay", "arguments": arguments or {"amount": 10}},
        trace_id="trace-1",
        run_id="run-1",
        user_id=user_id,
        agent_name="finance",
        metadata=metadata or {},
    )


def test_pending_approval_can_be_resolved_and_reused_for_matching_action():
    store = InMemoryReviewStore()
    hook = HumanApprovalHook(store=store, tools={"pay"})

    pending = hook(tool_context())
    request = store.list_pending()[0]
    store.resolve(request.request_id, ApprovalDecision.approve(reviewer_id="reviewer"))
    approved = hook(tool_context(metadata={"approval_id": request.request_id}))

    assert pending.action == "block"
    assert pending.metadata["review_events"][0]["type"] == "approval_required"
    assert approved.action == "continue"
    assert approved.metadata["review_events"][0]["reused"] is True


def test_approval_id_cannot_be_reused_for_different_arguments():
    store = InMemoryReviewStore()
    hook = HumanApprovalHook(store=store, tools={"pay"})
    pending = hook(tool_context())
    request_id = pending.metadata["approval_request_id"]
    store.resolve(request_id, ApprovalDecision.approve())

    mismatched = hook(tool_context(
        metadata={"approval_id": request_id},
        arguments={"amount": 999},
    ))

    assert mismatched.action == "block"
    assert mismatched.reason == "approval does not match the current action"
    assert mismatched.metadata["review_events"][0]["type"] == "approval_rejected"

    cross_user = hook(tool_context(
        metadata={"approval_id": request_id},
        user_id="bob",
    ))
    assert cross_user.action == "block"
    assert cross_user.reason == "approval does not match the current action"

    missing = hook(tool_context(metadata={"approval_id": "missing"}))
    assert missing.action == "block"
    assert missing.reason == "approval request not found or unresolved"
    assert len(store.list_pending()) == 0


def test_sync_reviewer_can_edit_tool_arguments():
    hook = HumanApprovalHook(
        reviewer=lambda request: ApprovalDecision.edit(
            {"amount": 5},
            reviewer_id="reviewer",
        ),
        tools={"pay"},
    )

    decision = hook(tool_context())

    assert decision.action == "replace"
    assert decision.payload["arguments"] == {"amount": 5}
    assert decision.metadata["review_events"][0]["type"] == "approval_edit"


def test_reviewer_timeout_fails_closed():
    def slow_reviewer(request):
        time.sleep(0.05)
        return True

    hook = HumanApprovalHook(reviewer=slow_reviewer, timeout=0.001)

    decision = hook(tool_context())

    assert decision.action == "block"
    assert "timed out" in decision.reason
    assert decision.metadata["review_events"][0]["type"] == "approval_reject"


def test_json_review_store_persists_decisions_and_feedback(tmp_path):
    path = tmp_path / "reviews.json"
    store = JsonReviewStore(path)
    pending = HumanApprovalHook(store=store)(tool_context())
    request_id = pending.metadata["approval_request_id"]
    store.resolve(request_id, ApprovalDecision.reject("not authorized"))
    store.add_feedback(HumanFeedback(
        trace_id="trace-1",
        rating=0.25,
        label="unsafe",
        reviewer_id="reviewer",
    ))

    restored = JsonReviewStore(path)

    assert restored.get_decision(request_id).reason == "not authorized"
    assert restored.list_feedback("trace-1")[0].label == "unsafe"


def test_agent_run_uses_internal_approval_id_without_forwarding_it_to_model():
    executions = []

    def pay(amount):
        executions.append(amount)
        return "paid"

    pay.tool_info = {
        "tool_name": "pay",
        "tool_description": "Send a payment.",
        "tool_params": [
            {"name": "amount", "type": "number", "description": "Amount", "required": True},
        ],
    }

    class ToolCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **params):
            self.calls.append(params)
            if len(self.calls) == 1:
                tool_call = SimpleNamespace(
                    id="call-pay",
                    function=SimpleNamespace(
                        name="pay",
                        arguments=json.dumps({"amount": 10}),
                    ),
                )
                message = SimpleNamespace(content=None, tool_calls=[tool_call])
            else:
                message = SimpleNamespace(content="finished", tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    store = InMemoryReviewStore()
    hook = HumanApprovalHook(store=store, tools={"pay"})
    agent = LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        hooks=[hook],
    )
    first_completions = ToolCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=first_completions))

    pending = agent.run("pay", tools=[pay], result_format="object", trace=True)
    request = store.list_pending()[0]
    store.resolve(request.request_id, ApprovalDecision.approve())
    approved_completions = ToolCompletions()
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=approved_completions))
    approved = agent.run(
        "pay",
        tools=[pay],
        approval_id=request.request_id,
        result_format="object",
        trace=True,
    )

    assert executions == [10]
    assert any(event["type"] == "approval_required" for event in pending.trace)
    assert any(event["type"] == "approval_approve" for event in approved.trace)
    assert all("approval_id" not in call for call in approved_completions.calls)


def test_lightflow_approval_can_edit_query_or_supply_response():
    edited_agent = FakeAgent()
    edit_flow = LightFlow().step(
        "write",
        agent=edited_agent,
        requires_approval=True,
        approval_handler=lambda step, context: ApprovalDecision.edit({"query": "reviewed"}),
    )
    respond_agent = FakeAgent()
    respond_flow = LightFlow().step(
        "write",
        agent=respond_agent,
        requires_approval=True,
        approval_handler=lambda step, context: ApprovalDecision.respond("human response"),
    )

    edited = edit_flow.run("original", trace=True)
    responded = respond_flow.run("original", trace=True)

    assert edited.content == "agent:reviewed"
    assert edited_agent.calls[0][0] == "reviewed"
    assert any(event["type"] == "approval_edit" for event in edited.trace)
    assert responded.content == "human response"
    assert respond_agent.calls == []
    assert any(event["type"] == "approval_respond" for event in responded.trace)


def test_lightflow_rejection_stops_before_agent_execution():
    agent = FakeAgent()
    flow = LightFlow().step(
        "write",
        agent=agent,
        requires_approval=True,
        approval_handler=lambda step, context: ApprovalDecision.reject("declined"),
    )

    result = flow.run("original", trace=True)

    assert result.success is False
    assert result.status == "failed"
    assert result.error == "declined"
    assert agent.calls == []
    assert any(event["type"] == "approval_reject" for event in result.trace)


def test_lightflow_legacy_false_handler_still_waits_for_approval():
    agent = FakeAgent()
    flow = LightFlow().step(
        "write",
        agent=agent,
        requires_approval=True,
        approval_handler=lambda step, context: False,
    )

    result = flow.run("original")

    assert result.status == "waiting_approval"
    assert result.steps[0].approval_decision == "pending"
    assert agent.calls == []


def test_lightflow_checkpoint_approval_resumes_with_persisted_edit(tmp_path):
    store = JsonLightFlowStore(tmp_path)
    agent = FakeAgent()
    flow = LightFlow(store=store).step(
        "write",
        agent=agent,
        requires_approval=True,
    )

    waiting = flow.run("original", run_id="review-run", trace=True)
    request_id = waiting.steps[0].approval_request_id
    flow.approve(
        "review-run",
        "write",
        ApprovalDecision.edit({"query": "approved query"}, reviewer_id="reviewer"),
    )
    resumed = flow.resume("review-run", trace=True)
    record = flow.get_run("review-run")

    assert waiting.status == "waiting_approval"
    assert request_id
    assert resumed.success is True
    assert resumed.content == "agent:approved query"
    assert agent.calls[0][0] == "approved query"
    assert resumed.steps[0].approval_request_id == request_id
    assert record["approvals"]["write"]["action"] == "edit"

    try:
        flow.approve("review-run", "write", True)
    except ValueError as exc:
        assert "not waiting for approval" in str(exc)
    else:
        raise AssertionError("completed step must not accept another approval")

    rerun = flow.rerun_step("review-run", "write")
    assert rerun.status == "waiting_approval"
    assert rerun.steps[0].approval_request_id != request_id
