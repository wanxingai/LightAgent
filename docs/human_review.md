## Human Review

LightAgent v0.9.6 adds small, optional primitives for Human-in-the-loop approval
and Human-on-the-loop feedback. They do not add a web UI, queue service, or
database dependency.

### Protect Sensitive Tools

`HumanApprovalHook` can protect selected tools. Without a synchronous reviewer,
it stores a pending request and blocks the action:

```python
from LightAgent import HumanApprovalHook, JsonReviewStore, LightAgent

review_store = JsonReviewStore(".lightagent/reviews.json")
approval_hook = HumanApprovalHook(
    store=review_store,
    tools={"send_payment", "delete_file"},
)

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    hooks=[approval_hook],
)

result = agent.run(
    "Pay invoice 42",
    result_format="object",
    trace=True,
)
pending = review_store.list_pending()
```

After an external reviewer resolves the request, rerun the action with the
dedicated approval ID:

```python
from LightAgent import ApprovalDecision

request = pending[0]
review_store.resolve(
    request.request_id,
    ApprovalDecision.approve(reviewer_id="finance-reviewer"),
)

result = agent.run(
    "Pay invoice 42",
    approval_id=request.request_id,
    result_format="object",
    trace=True,
)
```

`approval_id` is internal hook context and is not forwarded to the model API.
An approval can only be reused when the phase, tool, arguments, source agent,
and target agent match the original request.

### Synchronous Decisions And Argument Editing

Use a callback when the application can make the review decision immediately:

```python
from LightAgent import ApprovalDecision, HumanApprovalHook


def review(request):
    if request.tool_name == "send_payment":
        return ApprovalDecision.edit(
            {"amount": min(request.arguments["amount"], 100)},
            reviewer_id="budget-policy",
        )
    return ApprovalDecision.approve()


approval_hook = HumanApprovalHook(
    reviewer=review,
    tools={"send_payment"},
    timeout=2,
)
```

Reviewer exceptions and timeouts fail closed. Supported decisions are approve,
reject, and edit for runtime tools and handoffs. `ApprovalRequest` also carries
run, trace, agent, reviewer, and application metadata for external audit
systems.

### Durable LightFlow Approval

LightFlow stores pending request IDs and decisions in its checkpoint:

```python
from LightAgent import ApprovalDecision, JsonLightFlowStore, LightFlow

flow = LightFlow(store=JsonLightFlowStore(".lightflow_runs")).step(
    "publish",
    agent=publisher,
    requires_approval=True,
)

waiting = flow.run("Publish the report", run_id="report-42")
request_id = waiting.steps[0].approval_request_id

flow.approve(
    "report-42",
    "publish",
    ApprovalDecision.edit(
        {"query": "Publish the approved redacted report"},
        reviewer_id="editor",
    ),
)
result = flow.resume("report-42")
```

LightFlow supports approve, reject, edit, and respond. A respond decision
supplies the step output without invoking the agent. Existing Boolean approval
handlers remain supported.

### Approval Batches

`InMemoryReviewStore` and `JsonReviewStore` provide `create_batch()` and
`resolve_batch()` for applications that want to present several proposed
actions in one review screen. Batch orchestration remains application-owned so
the core does not impose a UI or queue model.

### Human Feedback

Attach offline labels or ratings to a trace:

```python
from LightAgent import HumanFeedback

feedback = HumanFeedback(
    trace_id=result.trace_id,
    rating=0.9,
    label="correct",
    reviewer_id="qa-17",
)
review_store.add_feedback(feedback)
```

`TraceRecorder.record_feedback()` emits a `human_feedback` event when feedback
must travel with an exported trace. Avoid storing prompts, secrets, or full tool
arguments in reviewer metadata unless the destination is approved for that
data.
