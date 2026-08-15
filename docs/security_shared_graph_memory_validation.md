## Shared Graph Memory Security Validation

This guide separates LightAgent framework mitigations from behavior owned by a
shared Graph Memory backend. It supports the engineering follow-up for issue
#39 without declaring an affected-version range or a fully patched backend.

### Framework Boundary

LightAgent can fail closed before writes, namespace users, require provenance
and trust metadata, filter retrievals, keep internal memory non-injectable until
promotion, and emit admission/retrieval audit events. The tracked fake-backend
tests verify that these controls stop a destructive low-trust write before it
reaches a backend that would otherwise remove trusted facts.

These controls cannot make an external graph transaction safe, recover facts
mutated outside LightAgent, or prove how a specific Mem0 Graph release resolves
entities and updates relationships.

### Validation Matrix

| Scenario | Default tracked test | Opt-in real backend |
| --- | --- | --- |
| Cross-user poisoning attempt | Required | Required |
| Tenant/user/agent isolation | Required | Required |
| Unattributed and low-trust quarantine | Required | Required |
| Trusted relation/neighborhood preservation | Destructive fake backend | Exact backend configuration |
| Admission and retrieval audit counts | Required | Required |
| Mem0 version and storage configuration | Not applicable | Explicitly pinned |

### Running The Opt-In Mem0 Graph Test

The test is skipped during normal CI. It writes and deletes data and must only
target an isolated, disposable Graph and vector store.

```bash
export LIGHTAGENT_RUN_MEM0_GRAPH_SECURITY=1
export LIGHTAGENT_MEM0_EXPECTED_VERSION="the-installed-mem0ai-version"
export LIGHTAGENT_MEM0_GRAPH_CONFIG_JSON='{"version":"v1.1","graph_store":{"provider":"your-provider","config":{"url":"your-isolated-url"}}}'

PYTHONPATH=. python -m pytest -q \
  tests/integration/test_mem0_graph_security_opt_in.py
```

Supply provider credentials through the provider's environment variables or a
secret manager. Never commit credentials inside the JSON value. The test also
requires a `graph_store` entry and fails if
`LIGHTAGENT_MEM0_EXPECTED_VERSION` does not match the installed `mem0ai`
package.

Record the Mem0 version, graph provider/version, vector provider/version,
isolation strategy, test timestamp, and sanitized pass/fail output for each
production-like configuration. Move reproduction details, affected-version
analysis, CWE/CVSS discussion, and reporter attribution to a private advisory
workflow when appropriate.

### Closure Criteria

Do not describe v0.9.5, v0.9.6, or v0.9.7 as a complete backend fix solely
because framework tests pass. Issue #39 can be scoped responsibly only after
the exact maintained configurations pass the opt-in matrix and the remaining
mutation behavior is attributed to the framework boundary, backend boundary,
unsafe deployment configuration, or a documented combination of them.
