# Contributing to LightAgent

Thanks for helping improve LightAgent. The project values small, focused changes
that preserve the lightweight core and keep existing APIs compatible.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

## Before Opening a Pull Request

Run the focused regression suite:

```bash
python -m compileall -q LightAgent
PYTHONPATH=. python -m pytest -q tests/test_v065_core.py tests/test_v070_tracing.py tests/test_memory_policy.py
```

## Contribution Guidelines

- Keep default `agent.run()` behavior backward compatible unless a breaking
  change is explicitly approved and documented.
- Prefer focused modules and tests over adding more logic to `LightAgent/core.py`.
- Do not include credentials, local logs, generated build artifacts, or private
  tool implementations.
- For memory, MCP, tool loading, or code execution changes, include a short
  security note in the PR.
- Update README or `docs/` when behavior, configuration, or public APIs change.

## Reporting Issues

Please use the bug or feature templates when possible. Security issues should be
reported privately through GitHub Security Advisories.
