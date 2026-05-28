# Security Policy

## Supported Versions

Security fixes are prioritized for the latest released version and active
development branch.

## Reporting a Vulnerability

Please do not open a public issue for vulnerabilities. Use GitHub Security
Advisories:

https://github.com/wanxingai/LightAgent/security/advisories/new

Include:

- affected version or commit
- minimal reproduction
- impact and affected component
- suggested mitigation, if known

## Security-Sensitive Areas

Extra review is required for changes involving:

- memory storage, retrieval, namespaces, and provenance
- dynamic tool loading or generated tool code
- MCP server/client integration
- code execution tools
- tracing and logs that may capture tool arguments or outputs
