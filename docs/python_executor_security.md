## Python Executor Security

`execute_python_code`, `execute_python_file`, and
`execute_python_code_stream` are controlled utilities, not security sandboxes.
They parse source with an AST blocklist and execute accepted code in a temporary
working directory, but the child process still runs with the operating-system
identity and permissions of the LightAgent application.

### What The AST Check Covers

The v0.9.7 regression suite checks direct and aliased dangerous imports,
dangerous builtins, attribute calls, constant-string `getattr` and
`attrgetter`, `__dict__`/subscript dispatch, and common child-process methods.
It also contains false-positive cases for ordinary math, strings, collections,
and application objects with a harmless `run()` method.

AST filtering is defense in depth. Python introspection and dynamic behavior
cannot be made fully safe with a static denylist. New bypasses may exist, and
accepted code can still consume CPU, memory, disk, or allowed network APIs.

### Production Controls

- Do not expose Python execution to untrusted users by default.
- Use a strict tool allowlist and protect the executor with `PolicyHook` and
  Human Review.
- Run the application or executor in a dedicated container or worker with a
  read-only filesystem, low privileges, CPU/memory/process limits, and no
  ambient credentials.
- Disable outbound network access unless an explicit destination allowlist is
  required.
- Keep `timeout` small and enforce a parent-level worker timeout as well.
- Do not allow model-selected `requirements` in production. Dependency
  installation downloads and executes third-party package build/install code.
- Record tool approval, block, timeout, and result metadata without logging
  secrets or complete source when it may contain private data.

### Fail-Closed Hook Example

```python
from LightAgent import HookDecision, HumanApprovalHook, LightAgent, PolicyHook


def python_execution_policy(context):
    if context.payload.get("tool_name") != "execute_python_code":
        return HookDecision.continue_()
    arguments = context.payload.get("arguments") or {}
    if arguments.get("requirements"):
        return HookDecision.block("Runtime dependency installation is disabled.")
    return HookDecision.continue_()


agent = LightAgent(
    model="your-model",
    api_key="your-api-key",
    base_url="your-base-url",
    hooks=[
        PolicyHook(
            python_execution_policy,
            phases={"before_tool_call"},
            failure_mode="block",
            timeout=1.0,
        ),
        HumanApprovalHook(tools={"execute_python_code"}),
    ],
)
```

Human approval confirms intent; it does not make the submitted code safe. The
runtime isolation controls remain necessary after approval.
