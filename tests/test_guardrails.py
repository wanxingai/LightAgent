import json
from types import SimpleNamespace

from LightAgent import (
    GuardrailDecision,
    LightAgent,
    high_risk_parameter_guardrail,
    output_redaction_guardrail,
    privacy_input_guardrail,
    sensitive_tool_confirmation_guardrail,
)


def make_agent(**kwargs):
    return LightAgent(
        model="gpt-4o-mini",
        api_key="test-key",
        base_url="http://127.0.0.1:9/v1",
        auto_discover_skills=False,
        **kwargs,
    )


class StaticCompletions:
    def __init__(self, content="done"):
        self.calls = []
        self.content = content

    def create(self, **params):
        self.calls.append(params)
        message = SimpleNamespace(content=self.content, tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ToolCallCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **params):
        self.calls.append(params)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(
                id="call_dangerous_tool",
                function=SimpleNamespace(name="dangerous_tool", arguments=json.dumps({"path": "/etc/passwd"})),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
        message = SimpleNamespace(content="tool was blocked", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def attach_client(agent, completions):
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return completions


def dangerous_tool(path):
    raise AssertionError(f"tool should not execute: {path}")


dangerous_tool.tool_info = {
    "tool_name": "dangerous_tool",
    "tool_description": "Dangerous file action.",
    "tool_params": [
        {"name": "path", "type": "string", "description": "path", "required": True},
    ],
}


def test_input_guardrail_blocks_before_model_request():
    def block_secret(query, context):
        if "api_key" in query.lower():
            return GuardrailDecision(False, reason="secret detected")
        return True

    agent = make_agent(input_guardrails=[block_secret])
    completions = attach_client(agent, StaticCompletions())

    result = agent.run("my api_key is abc", result_format="object", trace=True)

    assert result.error.startswith("[LA-GUARDRAIL]")
    assert "secret detected" in result.error
    assert completions.calls == []
    assert "guardrail_block" in [event["type"] for event in result.trace]
    assert result.trace[-1]["data"]["success"] is False


def test_input_guardrail_can_rewrite_query():
    def rewrite(query, context):
        return GuardrailDecision(True, value=query.replace("bad", "safe"))

    agent = make_agent(input_guardrails=[rewrite])
    completions = attach_client(agent, StaticCompletions("ok"))

    result = agent.run("bad input")

    assert result == "ok"
    assert completions.calls[0]["messages"][-1]["content"] == "safe input"


def test_tool_guardrail_blocks_tool_execution_and_returns_tool_error_to_model():
    def block_file_tool(tool_call, context):
        if tool_call["tool_name"] == "dangerous_tool":
            return "file access requires approval"
        return True

    agent = make_agent(tool_guardrails=[block_file_tool])
    completions = attach_client(agent, ToolCallCompletions())

    result = agent.run("read a file", tools=[dangerous_tool], result_format="object", trace=True)

    assert result.content == "tool was blocked"
    assert completions.calls[1]["messages"][-1]["content"].startswith("[LA-GUARDRAIL]")
    assert "file access requires approval" in completions.calls[1]["messages"][-1]["content"]
    assert "guardrail_block" in [event["type"] for event in result.trace]


def test_output_guardrail_can_rewrite_non_streaming_response():
    def redact(output, context):
        return GuardrailDecision(True, value=output.replace("INTERNAL_ONLY", "[redacted]"))

    agent = make_agent(output_guardrails=[redact])
    attach_client(agent, StaticCompletions("visible INTERNAL_ONLY"))

    result = agent.run("hello")

    assert result == "visible [redacted]"


def test_output_guardrail_can_block_non_streaming_response():
    def block_output(output, context):
        if "secret" in output:
            return "final answer contains a secret"
        return True

    agent = make_agent(output_guardrails=[block_output])
    attach_client(agent, StaticCompletions("secret answer"))

    result = agent.run("hello", result_format="object", trace=True)

    assert result.error.startswith("[LA-GUARDRAIL]")
    assert "final answer contains a secret" in result.error
    assert result.trace[-1]["data"]["success"] is False


def test_default_privacy_input_guardrail_blocks_private_data():
    agent = make_agent(input_guardrails=[privacy_input_guardrail()])
    completions = attach_client(agent, StaticCompletions())

    result = agent.run("my email is user@example.com", result_format="object")

    assert result.error.startswith("[LA-GUARDRAIL]")
    assert completions.calls == []


def test_sensitive_tool_confirmation_guardrail_blocks_selected_tools():
    agent = make_agent(tool_guardrails=[sensitive_tool_confirmation_guardrail(["dangerous_tool"])])
    completions = attach_client(agent, ToolCallCompletions())

    result = agent.run("read a file", tools=[dangerous_tool], result_format="object")

    assert result.content == "tool was blocked"
    assert "requires approval" in completions.calls[1]["messages"][-1]["content"]


def test_high_risk_parameter_guardrail_validates_arguments():
    guardrail = high_risk_parameter_guardrail({"path": lambda value: str(value).startswith("/safe/")})
    agent = make_agent(tool_guardrails=[guardrail])
    completions = attach_client(agent, ToolCallCompletions())

    result = agent.run("read a file", tools=[dangerous_tool], result_format="object")

    assert result.content == "tool was blocked"
    assert "path" in completions.calls[1]["messages"][-1]["content"]


def test_output_redaction_guardrail_redacts_private_data():
    agent = make_agent(output_guardrails=[output_redaction_guardrail()])
    attach_client(agent, StaticCompletions("contact user@example.com"))

    result = agent.run("hello")

    assert result == "contact [redacted]"
