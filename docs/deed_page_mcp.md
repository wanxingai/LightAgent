## Publishing Pages With deed.page Over MCP

[deed.page](https://deed.page) is a static hosting service with a remote MCP
server at `https://deed.page/mcp` (Streamable HTTP). With LightAgent's existing
`transport: "streamable-http"` support, an agent can write an HTML page or a
small set of files and get back a public URL, without any new dependency.

> Affiliation: this example is contributed by the deed.page team (Avatar 8 LLC),
> which operates the service. Service documentation: https://deed.page/docs.
> An MIT-licensed agent skill with the same API is at
> https://github.com/f-o-x11/deed-page-skill.

The example lives in [`example/deed_page_mcp.py`](../example/deed_page_mcp.py).

### Configure

```python
import asyncio

from LightAgent import LightAgent
from example.deed_page_mcp import (
    DEFAULT_TOKEN_FILE,
    setup_deed_page,
)

agent = LightAgent(model="your-model", api_key="your-api-key", base_url="https://your-endpoint/v1")

asyncio.run(setup_deed_page(agent, DEFAULT_TOKEN_FILE))

print(agent.run("Write a one-page HTML status report and publish it with deedpage__publish_site. Reply with the URL."))
```

`deed_page_mcp_config()` returns:

```python
{"mcpServers": {"deedpage": {"transport": "streamable-http", "url": "https://deed.page/mcp", "namespace": "deedpage", "namespace_tools": True}}}
```

When `DEEDPAGE_TOKEN` is set, Python adds `{"Authorization": "Bearer <token>"}`
to `headers`; LightAgent does not interpolate header strings itself. The example
also installs a credential provider that re-reads the private token file before
each connection, so a newly saved owner token is reused within the same run.

### Run the example

```bash
# Check the connection and publish a sample page (no model needed).
PYTHONPATH=. python example/deed_page_mcp.py --direct --ttl 3600

# Let an agent write and publish a page (any OpenAI-compatible model).
export OPENAI_API_KEY=...            # plus OPENAI_BASE_URL / LIGHTAGENT_MODEL if needed
PYTHONPATH=. python example/deed_page_mcp.py
```

`publish_site` takes `files` as a map of path to content (for example
`{"index.html": "<h1>Hi</h1>"}`), plus optional `slug` and `ttl_seconds`.
Pages without `ttl_seconds` stay up until deleted. Plan limits and the full
tool list are described in the service documentation linked above and may
change.

### Security notes

- **Owner token.** Without `DEEDPAGE_TOKEN`, the first publish is anonymous
  and the result contains a one-time owner token, which is needed to update or
  delete the page later. `protect_publish_token` removes it from the tool
  result before the model sees it and writes it to the token file with mode
  `0600`. The default is `$XDG_CONFIG_HOME/lightagent/credentials/deedpage.token`
  or `~/.config/lightagent/credentials/deedpage.token`, outside the repository.
  A newly created credentials directory has mode `0700`. Stored tokens are
  reused automatically; `DEEDPAGE_TOKEN` takes precedence. An existing different
  owner token is never silently replaced. Preserve each owner token if you
  intentionally use multiple anonymous owners.
- **File safety.** Token files must be current-user-owned regular files with
  owner-only permissions. Symlinks, directories, FIFOs, and insecure files fail
  closed. Writes use a `0600` temporary file and atomic, no-clobber publication.
  `token_saved` is added only after successful storage. File handling requires
  POSIX `O_NOFOLLOW`; use `DEEDPAGE_TOKEN` where it is unavailable. Existing
  legacy `.deedpage-token` files are ignored by Git but are not loaded or migrated
  automatically. Never point `--token-file` at a tracked or unrelated file.
- **Tool surface.** The server lists more tools than publishing (for example
  `delete_site`, `rotate_token`, `add_domain`). LightAgent registers every tool
  a server lists, so the example removes the ones the agent does not need right
  after setup. Only `deedpage__publish_site` and `deedpage__get_site` are exposed.
  The namespace is reserved before registration, and local tools with the bare
  names are preserved. Setup requires a separate agent without an existing
  MCP client; its credential resolver sends owner credentials only to the
  `deedpage` server. Calling raw `refresh_tools()` registers blocked tools
  again: use `await refresh_deed_page(agent, DEFAULT_TOKEN_FILE)` instead, which
  re-applies the allowlist and token wrapper. Import it from the same example.
- **Public output.** Published pages are public URLs. Do not let the agent
  publish secrets, private data, or anything you would not post on the web.

### Compatibility evidence

The hardened revision is validated offline by
`tests/test_deed_page_mcp_example.py` and `tests/test_deed_page_mcp_security.py`:
configuration, token redaction, permissions, symlink/race rejection, failed
storage, repeated publication, namespace collisions, and refresh protection.

The original contributor reported live publication/cleanup tests with the
locked MCP SDK, without running agent model calls. Those observations predate
this hardening revision. No live deed.page publication or model call was made
to validate the hardened revision; offline tests do not certify the service.
