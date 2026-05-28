## Error Handling

LightAgent exposes stable user-facing error codes for common model-provider,
tool, and parsing failures. Error strings begin with a code such as `[LA-401]`
and include a short troubleshooting hint.

### Error Codes

| Code | Meaning | Common Fix |
| --- | --- | --- |
| `LA-400` | Invalid request | Check request parameters, message format, tool schema, and model name. |
| `LA-401` | Authentication failed | Check `api_key` or `OPENAI_API_KEY`. |
| `LA-403` | Permission or policy rejection | Check model access, account permissions, and provider policy settings. |
| `LA-404` | Endpoint or model not found | Check `base_url` and the exact model name. |
| `LA-408` | Request timed out | Retry, reduce input size, or increase timeout settings. |
| `LA-413` | Request or response too large | Reduce prompt, history, tool output, or requested completion size. |
| `LA-429` | Rate limit or quota exceeded | Wait before retrying or check quota and billing status. |
| `LA-500` | Provider server error | Retry later or use another provider endpoint. |
| `LA-503` | Provider temporarily unavailable | Retry later or switch model/provider. |
| `LA-JSON` | Tool-call JSON parse failure | Check that tool arguments match the registered schema. |
| `LA-TOOL` | Tool execution failed | Check tool code, dependencies, arguments, and credentials. |
| `LA-UNKNOWN` | Unexpected error | Enable debug logging and inspect the original exception. |

### Programmatic Classification

```python
from LightAgent import LightAgentError, classify_exception, format_lightagent_error

try:
    response = agent.run("Hello")
except LightAgentError as exc:
    print(exc.code, exc.message, exc.guidance)
except Exception as exc:
    info = classify_exception(exc)
    print(info.code, info.message)
    print(format_lightagent_error(exc, "run agent"))
```

Most `agent.run()` model-provider failures are returned as user-facing strings
instead of raw provider exceptions. Tool failures are returned to the model with
`LA-TOOL` so the agent can explain or retry with corrected arguments.

### Structured Run Results

The default `agent.run()` behavior remains backward compatible:

```python
response = agent.run("Hello")
print(response)  # str
```

For structured diagnostics, request an object explicitly:

```python
result = agent.run("Hello", result_format="object")

print(result.content)
print(result.tool_calls)
print(result.trace_id)
print(result.error)
```

For streaming, the default remains a legacy generator:

```python
for chunk in agent.run("Hello", stream=True):
    print(chunk)
```

Structured streaming events are opt-in:

```python
for event in agent.run("Hello", stream=True, result_format="event"):
    print(event.type, event.data)
```

### Debugging Long Operations

For long or complex tasks:

- Set `debug=True` and `log_level="debug"` on `LightAgent`.
- Use `stream=True` to receive model chunks and tool events as they happen.
- Keep tool output compact; large tool responses can trigger `LA-413`.
- If a partial result matters, make the tool write it to durable storage and
  return the saved path or identifier.
