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

## Third-Party Services And Provider Documentation

Contributions that add or replace a hosted model provider, gateway, external
API, badge, chart, or other remote service must make the dependency and its
trust boundary reviewable.

- Disclose any employment, ownership, sponsorship, or other affiliation with
  the service in the issue and pull request.
- Link the service's official, publicly accessible API documentation, model or
  feature catalog, and source repository when the service is open source.
- Prefer provider-neutral OpenAI-compatible configuration guidance. A dedicated
  provider section should document a meaningful compatibility detail that is
  not already covered by `model`, `api_key`, and `base_url`.
- Use stable example identifiers where possible. When model names or features
  are controlled by the service, link the live catalog and state that
  availability may change.
- Read credentials from environment variables. Never include working keys,
  encrypted tokens, account identifiers, or credentials embedded in public
  URLs.
- Include reproducible compatibility evidence for the behavior being claimed.
  For model gateways, cover chat completions and any claimed streaming or tool
  calling support. Clearly separate local or CI validation from credentialed
  live-service validation.
- Limit project documentation to verifiable configuration and compatibility
  facts. Do not add unverified pricing, model-count, availability, performance,
  failover, security, privacy, or regulatory guarantees.
- For externally hosted images or embeds, identify the operator and source,
  describe what request data leaves GitHub, and explain why a repository-owned
  static asset is not sufficient.
- External-contributor workflows may remain unapproved until maintainers finish
  reviewing the proposed service dependency. CI approval does not imply project
  endorsement of that service.

Maintainers may decline or remove a dedicated listing when its claims cannot be
independently verified, its maintenance burden is disproportionate, or generic
OpenAI-compatible documentation already covers the integration.

## Reporting Issues

Please use the bug or feature templates when possible. Security issues should be
reported privately through GitHub Security Advisories.
