## Guardrails

LightAgent v0.7.5 adds a lightweight opt-in guardrail layer for safer agent
runs. Guardrails are disabled by default and do not change existing
`agent.run()` behavior unless configured.

### Input Guardrails

Input guardrails run before memory lookup and before the first model request.
They can block a run or rewrite the input.

```python
from LightAgent import GuardrailDecision, LightAgent


def block_secrets(query, context):
    if "api_key" in query.lower():
        return GuardrailDecision(False, reason="Do not send secrets to the model.")
    return True


agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    input_guardrails=[block_secrets],
)

response = agent.run("hello")
```

### Tool Guardrails

Tool guardrails run after tool arguments are parsed and before the Python tool
function is executed. This is useful for high-risk tools such as file, network,
database, payment, or external-action tools.

```python
def block_large_transfers(tool_call, context):
    if tool_call["tool_name"] == "transfer_money":
        amount = tool_call["arguments"].get("amount", 0)
        if amount > 1000:
            return "Transfers above 1000 require approval."
    return True
```

### Output Guardrails

Output guardrails run on final non-streaming responses before returning them to
the caller.

```python
def redact_internal_notes(output, context):
    return GuardrailDecision(True, value=output.replace("INTERNAL_ONLY", "[redacted]"))
```

### Default Templates

LightAgent includes small guardrail template factories for common production
patterns. They are opt-in and can be combined with custom guardrails.

```python
from LightAgent import (
    LightAgent,
    high_risk_parameter_guardrail,
    output_redaction_guardrail,
    privacy_input_guardrail,
    sensitive_tool_confirmation_guardrail,
)

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    input_guardrails=[
        privacy_input_guardrail(),
    ],
    tool_guardrails=[
        sensitive_tool_confirmation_guardrail(["transfer_money", "delete_file"]),
        high_risk_parameter_guardrail({
            "amount": lambda value: float(value or 0) <= 1000,
        }),
    ],
    output_guardrails=[
        output_redaction_guardrail(),
    ],
)
```

Available templates:

| Template | Stage | Purpose |
| --- | --- | --- |
| `privacy_input_guardrail()` | Input | Blocks common private data patterns such as emails, tokens, and payment-like numbers. |
| `sensitive_tool_confirmation_guardrail(tool_names)` | Tool | Blocks selected tools unless configured as approved. |
| `high_risk_parameter_guardrail(rules)` | Tool | Validates high-risk argument values before a tool executes. |
| `output_redaction_guardrail()` | Output | Redacts common private data patterns from final output. |

### Return Values

A guardrail can return:

- `True` or `None` to allow the current value.
- `False` to block with a default reason.
- A string to block with that string as the reason.
- `GuardrailDecision(allowed=False, reason="...")` to block.
- `GuardrailDecision(allowed=True, value=...)` to allow and rewrite.
- A dict with `allowed`, `reason`, and `value` keys.

Blocked operations return a stable `[LA-GUARDRAIL]` error string. When
`trace=True` is enabled, blocked operations also emit `guardrail_block` trace
events.
