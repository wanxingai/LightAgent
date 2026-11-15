"""Optional, host-registered async tools shared by MCP and App Server.

No callable/module names are accepted from model output. Native Codex tools
remain subject to its sandbox, not this bridge's CapabilityGate.
"""
import asyncio
from copy import deepcopy
import inspect
import json
import re
from ..security import CapabilityGate, canonical_digest
from ..cancellation import CancellationToken, accepts_keyword


class MCPToolBridge:
    def __init__(self, namespace, *, version, gate=None):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',namespace) or not version:
            raise ValueError('bridge requires a stable namespace and version')
        self.namespace, self.version = namespace, str(version)
        self.gate = gate or CapabilityGate()
        self._tools = {}
        self._frozen = False

    def register(self, name, function, *, schema, capability, description=''):
        if self._frozen:
            raise ValueError('bridge registration is frozen after binding')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}',name) or name in self._tools:
            raise ValueError('invalid or duplicate tool name')
        if not inspect.iscoroutinefunction(function):
            raise TypeError('experimental bridge tools must be cancellable async functions')
        if capability.name != self.namespace+'.'+name or capability.timeout is None or capability.output_limit is None:
            raise ValueError('bridge capability requires namespaced identity, timeout and output_limit')
        from jsonschema import Draft202012Validator
        def reject_refs(value):
            if isinstance(value,dict):
                if '$ref' in value or '$dynamicRef' in value:raise ValueError('bridge schemas cannot resolve external references')
                for item in value.values():reject_refs(item)
            elif isinstance(value,list):
                for item in value:reject_refs(item)
        reject_refs(schema)
        Draft202012Validator.check_schema(schema)
        if schema.get('type')!='object' or schema.get('additionalProperties') is not False:
            raise ValueError('tool input must be an object with additionalProperties=false')
        if {'security_context','cancellation_token'} & set(schema.get('properties',{})):
            raise ValueError('authority arguments cannot be supplied by the model')
        self._tools[name] = dict(function=function,schema=deepcopy(schema),capability=capability,description=description)

    @property
    def digest(self):
        self._frozen = True
        return canonical_digest({'namespace':self.namespace,'version':self.version,'tools':{
            name:{'schema':t['schema'],'capability':t['capability'].to_dict(),'description':t['description']}
            for name,t in self._tools.items()}})

    def dynamic_tools(self):
        self._frozen = True
        return [{'type':'namespace','name':self.namespace,'description':'Host registered LightAgent tools',
                 'tools':[{'type':'function','name':name,'description':t['description'],'inputSchema':deepcopy(t['schema'])}
                          for name,t in self._tools.items()]}]

    async def call(self, name, arguments, context, *, namespace=None, cancellation_token=None):
        from jsonschema import Draft202012Validator
        from ..persistent.redaction import redact
        self._frozen = True
        if namespace != self.namespace or name not in self._tools:
            raise PermissionError('tool namespace or registration mismatch')
        token = cancellation_token or CancellationToken()
        if token.cancelled:raise asyncio.CancelledError
        tool=self._tools[name]
        Draft202012Validator(tool['schema']).validate(arguments)
        decision=await self.gate.authorize(tool['capability'],self.namespace,arguments,context)
        values=deepcopy(arguments if decision.arguments is None else decision.arguments)
        Draft202012Validator(tool['schema']).validate(values)
        for key,value in [('security_context',context),('cancellation_token',token)]:
            if accepts_keyword(tool['function'],key):values[key]=value
        timeout=tool['capability'].timeout
        if context.deadline:
            from datetime import datetime,timezone
            deadline=datetime.fromisoformat(context.deadline.replace('Z','+00:00'))
            if deadline.tzinfo is None:deadline=deadline.replace(tzinfo=timezone.utc)
            timeout=min(timeout,max(.001,(deadline-datetime.now(timezone.utc)).total_seconds()))
        result=await asyncio.wait_for(tool['function'](**values),timeout=timeout)
        if token.cancelled:raise asyncio.CancelledError
        text=redact(result if isinstance(result,str) else json.dumps(result,ensure_ascii=False,allow_nan=False))
        if len(text.encode())>tool['capability'].output_limit:
            raise ValueError('bridge output exceeds capability limit')
        return text

    async def serve_stdio(self, context):
        """Run only from a trusted host entry point with a fixed context."""
        try:
            from mcp.server import Server
        except ModuleNotFoundError as error:
            if error.name != "mcp":
                raise
            raise ImportError("MCP stdio serving requires the optional dependency: pip install 'LightAgent[mcp]'") from error
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
        self._frozen = True
        prefix = self.namespace + "__"
        server_name = "lightagent-" + self.namespace

        def listed_tools(schema_field):
            return [Tool(name=prefix + name, description=tool["description"],
                         **{schema_field: tool["schema"]}) for name, tool in self._tools.items()]

        async def call_tool(name, arguments):
            if not name.startswith(prefix):
                raise PermissionError("MCP namespace mismatch")
            result = await self.call(name[len(prefix):], arguments, context, namespace=self.namespace)
            return [TextContent(type="text", text=result)]

        if hasattr(Server, "list_tools"):
            server = Server(server_name, version=self.version)

            @server.list_tools()
            async def list_tools():
                return listed_tools("inputSchema")

            server.call_tool()(call_tool)
        else:
            from mcp.types import CallToolResult, ListToolsResult

            async def on_list_tools(_context, _params):
                return ListToolsResult(tools=listed_tools("input_schema"))

            async def on_call_tool(_context, params):
                content = await call_tool(params.name, params.arguments or {})
                return CallToolResult(content=content)

            server = Server(server_name, version=self.version,
                            on_list_tools=on_list_tools, on_call_tool=on_call_tool)

        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())
