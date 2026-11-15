"""Experimental transport/bridge contract tests; no account usage."""
import asyncio
import json
import os
import sys
import time
from types import SimpleNamespace
import pytest
from LightAgent import (CodexAppServerBackend, BackendRequest,
                        SecurityContext, BackendError, CancellationToken, MCPToolBridge,
                        CapabilitySpec, CapabilityRisk, PermissionSet)
from LightAgent.version import __version__


@pytest.fixture
def cli(tmp_path,monkeypatch):
    binary=tmp_path/'bin';binary.mkdir()
    home=tmp_path/'home';home.mkdir()
    monkeypatch.setenv('CODEX_HOME',str(home))
    monkeypatch.setenv('PATH',str(binary)+os.pathsep+os.environ.get('PATH',''))
    monkeypatch.setenv('XDG_STATE_HOME',str(tmp_path/'state'))
    monkeypatch.setenv('LIGHTAGENT_TEST_VERSION', __version__)
    executable=binary/'codex'
    executable.write_text('#!'+sys.executable+'''\nimport sys,json,os
if '--version' in sys.argv:
 print('codex-cli 0.160.0');sys.exit()
if '--help' in sys.argv:
 print('--json --ignore-user-config --strict-config --config --skip-git-repo-check --sandbox --stdio');sys.exit()
assert sys.argv[1]=='app-server'
assert 'approval_policy="never"' in sys.argv
assert 'features.hooks=false' in sys.argv
thread='thread-fixture'
turn='turn-fixture'
def send(value):print(json.dumps(value),flush=True)
for line in sys.stdin:
 req=json.loads(line);method=req.get('method');params=req.get('params',{})
 if method=='initialize':
  assert params['clientInfo']['version']==os.environ['LIGHTAGENT_TEST_VERSION']
  send({'id':req['id'],'result':{'userAgent':'fixture'}})
 elif method=='initialized':pass
 elif method in ('thread/start','thread/resume'):
  send({'id':req['id'],'result':{'thread':{'id':thread}}})
 elif method=='turn/start':send({'id':req['id'],'result':{'turn':{'id':turn}}})
 elif method=='turn/steer':
  assert params['expectedTurnId']==turn
  send({'id':req['id'],'result':{'turnId':turn}})
  send({'method':'item/completed','params':{'threadId':thread,'turnId':turn,'item':{'type':'agentMessage','text':'steered successfully'}}})
  send({'method':'turn/completed','params':{'threadId':thread,'turn':{'id':turn,'status':'completed'}}})
 elif method=='turn/interrupt':
  send({'id':req['id'],'result':{}})
  send({'method':'turn/completed','params':{'threadId':thread,'turn':{'id':turn,'status':'interrupted'}}})
''')
    executable.chmod(0o755)
    workspace=tmp_path/'workspace';workspace.mkdir()
    return workspace,home


def context(workspace):
    return SecurityContext(network_allowed=True,resources=frozenset({str(workspace.resolve())}))


def test_appserver_handshake_exact_steering_resume_and_cancel(cli):
    work,home=cli
    backend=CodexAppServerBackend()
    assert backend.probe().capabilities.steer
    def event(event):
        if event.type=='backend.turn':
            with pytest.raises(BackendError,match='stale'):backend.steer('wrong',expected_turn_id='stale')
            backend.steer('additional direction',expected_turn_id=event.data['turn_id'])
    first=asyncio.run(backend.execute(BackendRequest('test',str(work),context(work),timeout=5,on_event=event)))
    assert first.content=='steered successfully'
    token=CancellationToken()
    second=asyncio.run(backend.execute(BackendRequest('resume',str(work),context(work),timeout=5,
        session_id=first.session_id,cancellation_token=token,
        on_event=lambda e:token.cancel() if e.type=='backend.turn' else None)))
    assert second.status=='cancelled'
    assert second.session_id==first.session_id
    assert backend.active_turn_id is None


def test_appserver_rejects_config_and_deadlines(cli, monkeypatch):
    work,home=cli
    (home/'config.toml').write_text('[mcp_servers.untrusted]\ncommand="bad"')
    with pytest.raises(BackendError,match='config-free'):
        asyncio.run(CodexAppServerBackend().execute(BackendRequest('test',str(work),context(work))))
    (home/'config.toml').unlink()
    import LightAgent.backends.app_server as app_server
    offset = [0]
    monkeypatch.setattr(app_server, 'time', SimpleNamespace(monotonic=lambda: time.monotonic() + offset[0]))
    def expire_after_handshake(event):
        if event.type == 'backend.turn':
            offset[0] = 10
    result=asyncio.run(CodexAppServerBackend().execute(BackendRequest('test',str(work),context(work),
        timeout=5, on_event=expire_after_handshake)))
    assert result.status=='timed_out'


def bridge():
    value=MCPToolBridge('research',version='1')
    async def add(x,security_context=None):
        assert security_context is not None
        return {'result':x+1}
    value.register('add',add,schema={'type':'object','properties':{'x':{'type':'integer'}},'required':['x'],'additionalProperties':False},
        capability=CapabilitySpec('research.add',read=True,risk=CapabilityRisk.READ_ONLY,timeout=1,output_limit=100))
    return value


def test_tool_bridge_schema_namespace_gate_and_digest():
    from jsonschema import ValidationError
    value=bridge();digest=value.digest
    assert value.dynamic_tools()[0]['tools'][0]['type']=='function'
    assert json.loads(asyncio.run(value.call('add',{'x':1},SecurityContext(),namespace='research')))['result']==2
    with pytest.raises(PermissionError):asyncio.run(value.call('add',{'x':1},SecurityContext(),namespace='wrong'))
    with pytest.raises(ValidationError):asyncio.run(value.call('add',{'x':'wrong'},SecurityContext(),namespace='research'))
    denied=SecurityContext(permissions=PermissionSet(denied=frozenset({'research.add'})))
    with pytest.raises(PermissionError):asyncio.run(value.call('add',{'x':1},denied,namespace='research'))
    assert value.digest==digest
    with pytest.raises(ValueError):value.register('new',None,schema={},capability=None)


def test_real_mcp_stdio_bridge_roundtrip(tmp_path):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    script='''import asyncio
from LightAgent import MCPToolBridge, CapabilitySpec, SecurityContext
bridge=MCPToolBridge('research',version='1')
async def add(x):return {'result':x+1}
bridge.register('add',add,schema={'type':'object','properties':{'x':{'type':'integer'}},'required':['x'],'additionalProperties':False},capability=CapabilitySpec('research.add',read=True,timeout=1,output_limit=100))
asyncio.run(bridge.serve_stdio(SecurityContext()))
'''
    async def run():
        params=StdioServerParameters(command=sys.executable,args=['-c',script])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                assert tools.tools[0].name=='research__add'
                result=await session.call_tool('research__add',{'x':4})
                assert not getattr(result, "is_error", getattr(result, "isError", False))
                assert json.loads(result.content[0].text)['result']==5
    asyncio.run(run())


def test_appserver_calls_only_registered_tool_bridge(cli,monkeypatch):
    work,home=cli
    executable=home.parent/'bin'/'codex'
    source=executable.read_text()
    source=source.replace("elif method=='turn/start':send({'id':req['id'],'result':{'turn':{'id':turn}}})", """elif method=='turn/start':
  send({'id':req['id'],'result':{'turn':{'id':turn}}})
  send({'id':'tool-request','method':'item/tool/call','params':{'callId':'call-1','threadId':thread,'turnId':turn,'namespace':'research','tool':'add','arguments':{'x':2}}})
 elif req.get('id')=='tool-request':
  assert req['result']['success'] is True
  assert json.loads(req['result']['contentItems'][0]['text'])['result']==3
  send({'method':'item/completed','params':{'threadId':thread,'turnId':turn,'item':{'type':'agentMessage','text':'tool bridge completed'}}})
  send({'method':'turn/completed','params':{'threadId':thread,'turn':{'id':turn,'status':'completed'}}})""")
    executable.write_text(source)
    result=asyncio.run(CodexAppServerBackend(tool_bridge=bridge()).execute(
        BackendRequest('use registered tool',str(work),context(work),timeout=5)))
    assert result.content=='tool bridge completed'


def test_tool_bridge_inherits_shorter_parent_deadline():
    from datetime import datetime,timedelta,timezone
    bridge=MCPToolBridge('deadline',version='1')
    async def slow():
        await asyncio.sleep(10)
    bridge.register('slow',slow,schema={'type':'object','properties':{},'additionalProperties':False},
                    capability=CapabilitySpec('deadline.slow',read=True,timeout=5,output_limit=100))
    ctx=SecurityContext(deadline=(datetime.now(timezone.utc)+timedelta(seconds=.08)).isoformat())
    with pytest.raises(asyncio.TimeoutError):asyncio.run(bridge.call('slow',{},ctx,namespace='deadline'))
