"""Experimental Codex 0.160.x stdio transport. Default deployments use exec.

Unlike exec, this CLI transport cannot ignore global configuration. It therefore
requires a CODEX_HOME without config TOML/hooks; authentication is managed by the
user in that home. The adapter never copies or reads credential files.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
from ..version import __version__
from .base import BackendCapabilities, BackendError, BackendProbe, BackendResult
from .codex import CodexBackend
from .process import run_process, terminate_group


class _StdioRPC:
    def __init__(self, argv, cwd, on_request=None):
        self.process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, start_new_session=True)
        self.pending = {}
        self.events = queue.Queue(maxsize=64)
        self.lock = threading.Lock()
        self.serial = 0
        self.closed = False
        self.error = None
        self.on_request = on_request
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _write(self, value, timeout=5):
        payload = (json.dumps(value, allow_nan=False)+'\n').encode()
        if len(payload) > 2*1024*1024:
            raise BackendError('App Server request exceeds output limit')
        import select
        fd = self.process.stdin.fileno()
        os.set_blocking(fd,False)
        deadline=time.monotonic()+timeout
        view=memoryview(payload)
        while view:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([], [fd], [], remaining)[1]:
                raise BackendError('App Server stdin write deadline exceeded')
            try:written=os.write(fd,view)
            except BlockingIOError:continue
            view=view[written:]

    def notify(self, method, params=None):
        with self.lock:
            self._write({'method':method, 'params':params or {}})

    def call(self, method, params, timeout=10):
        result = queue.Queue(maxsize=1)
        with self.lock:
            self.serial += 1
            key = self.serial
            self.pending[key] = result
            self._write({'id':key,'method':method,'params':params}, timeout)
        try:
            response = result.get(timeout=max(.01,timeout))
            if 'error' in response:
                raise BackendError('App Server rejected '+method)
            return response['result']
        except queue.Empty as exc:
            raise BackendError('App Server request outcome uncertain: '+method) from exc
        finally:
            with self.lock:
                self.pending.pop(key,None)

    def _read(self):
        try:
            while True:
                line = self.process.stdout.readline(256*1024+1)
                if not line:
                    break
                if len(line)>256*1024:
                    raise BackendError('App Server event exceeds limit')
                event = json.loads(line)
                if not isinstance(event,dict):
                    raise BackendError('invalid App Server envelope')
                if 'id' in event and 'method' not in event:
                    with self.lock:
                        target = self.pending.get(event['id'])
                    if target:
                        target.put_nowait(event)
                else:
                    self.events.put_nowait(event)
        except Exception as exc:
            self.error = type(exc).__name__
        finally:
            self.closed = True
            with self.lock:
                for target in self.pending.values():
                    try:target.put_nowait({'error':{'message':'transport closed'}})
                    except queue.Full:pass

    def respond(self, event, result=None):
        with self.lock:
            self._write({'id':event['id'],'result':result} if result is not None else
                        {'id':event['id'],'error':{'code':-32601,'message':'Host denied unsupported server request'}})

    def close(self):
        terminate_group(self.process)
        self.reader.join(timeout=3)
        for stream in (self.process.stdin,self.process.stdout):
            stream.close()


class CodexAppServerBackend(CodexBackend):
    capabilities = BackendCapabilities(resume=True, steer=True, isolation="sandbox", network_control=True)

    def __init__(self, *, tool_bridge=None, **kwargs):
        super().__init__(**kwargs)
        self.tool_bridge = tool_bridge
        self._active_lock = threading.Lock()
        self._rpc = None
        self.active_thread_id = None
        self.active_turn_id = None

    def _probe(self, token, deadline):
        binary, probe = super()._probe(token, deadline)
        help_result = run_process([binary,'app-server','--help'],cwd=os.getcwd(),token=token,
                                  timeout=max(.01,min(10,deadline-time.monotonic())),output_limit=65536)
        if help_result.returncode or '--stdio' not in help_result.stdout or '--strict-config' not in help_result.stdout:
            raise BackendError('App Server stdio/strict configuration capability unavailable')
        return binary, BackendProbe('codex-app-server',probe.version,self.capabilities,(
            'Experimental 0.160.x JSON-RPC transport',
            'Requires a config-free CODEX_HOME; no automatic fallback or credential copying',
            'Steering requires the exact current turn ID; an RPC timeout is an uncertain outcome',
        ))

    def _validate_permissions(self, request):
        super()._validate_permissions(request)
        home = Path(os.environ.get('CODEX_HOME',Path.home()/'.codex')).expanduser()
        if list(home.glob('*.toml')) or (home/'hooks.json').exists():
            raise BackendError('App Server requires a config-free CODEX_HOME; exec can ignore user config')
        if self.tool_bridge and request.session_id:
            raise BackendError('dynamic tool bridge resume is unsupported; start a new bound thread')

    def steer(self, content, *, expected_turn_id, timeout=5):
        if not isinstance(content,str) or not content.strip() or len(content.encode())>65536:
            raise ValueError('steering input must contain 1..65536 bytes')
        with self._active_lock:
            rpc, thread, turn = self._rpc, self.active_thread_id, self.active_turn_id
        if not rpc or not turn or turn != expected_turn_id:
            raise BackendError('stale or inactive App Server turn')
        return rpc.call('turn/steer',{'threadId':thread,'expectedTurnId':turn,
                                    'input':[{'type':'text','text':content}]}, timeout)

    def _extra_binding(self):
        return {'transport':'app-server', 'tool_bridge':self.tool_bridge.digest if self.tool_bridge else None}

    def _run_turn(self, request, binary, stack, binding, expires):
        config = self._configuration_options()
        argv = [binary,'app-server','--stdio','--strict-config',*config,
                '-c','sandbox_mode='+json.dumps(self.sandbox)]
        rpc = _StdioRPC(argv, request.workspace)
        session_id = request.session_id
        turn_id = None
        content = ''
        interrupted = False
        cancel_deadline = None
        remaining=lambda: max(.01,min(10,expires-time.monotonic()))
        try:
            rpc.call('initialize',{'clientInfo':{'name':'lightagent','title':'LightAgent','version':__version__},
                                   'capabilities':{'experimentalApi':True}}, remaining())
            rpc.notify('initialized')
            params = {'cwd':request.workspace,'approvalPolicy':'never','sandbox':self.sandbox}
            if self.model:params['model']=self.model
            if session_id:
                params['threadId']=session_id
                params['excludeTurns']=True
                response=rpc.call('thread/resume',params,remaining())
            else:
                if self.tool_bridge:params['dynamicTools']=self.tool_bridge.dynamic_tools()
                response=rpc.call('thread/start',params,remaining())
            returned=response['thread']['id']
            if not isinstance(returned,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',returned):
                raise BackendError('invalid App Server thread id')
            if session_id and returned != session_id:
                raise BackendError('App Server switched threads')
            if not session_id:
                session_id=returned
                stack.enter_context(self.session_store.claim('codex',session_id,binding,create=True))
            response=rpc.call('turn/start',{'threadId':session_id,'input':[{'type':'text','text':request.prompt}]},remaining())
            turn_id=response['turn']['id']
            if not isinstance(turn_id,str) or not turn_id or len(turn_id)>128:
                raise BackendError('invalid App Server turn ID')
            with self._active_lock:
                self._rpc,self.active_thread_id,self.active_turn_id=rpc,session_id,turn_id
            request.emit('backend.turn',session_id=session_id,turn_id=turn_id)
            while True:
                expired=time.monotonic()>=expires
                if (request.cancellation_token.cancelled or expired) and not interrupted:
                    interrupted=True
                    cancel_deadline=time.monotonic()+3
                    try:rpc.call('turn/interrupt',{'threadId':session_id,'turnId':turn_id},timeout=1)
                    except BackendError:pass
                if interrupted and time.monotonic()>=cancel_deadline:
                    # Process cleanup is confirmed in finally; no successful turn is claimed.
                    return BackendResult('', 'timed_out' if expired else 'cancelled',session_id,error='interrupted without terminal acknowledgement')
                try:event=rpc.events.get(timeout=.05)
                except queue.Empty:
                    if rpc.closed:raise BackendError('App Server closed without a terminal event')
                    continue
                method=event.get('method')
                params=event.get('params',{})
                if 'id' in event:
                    if method=='item/tool/call' and self.tool_bridge and params.get('threadId')==session_id and params.get('turnId')==turn_id:
                        deadline=(datetime.now(timezone.utc)+timedelta(seconds=max(0,expires-time.monotonic()))).isoformat()
                        if request.security_context.deadline:
                            parent=datetime.fromisoformat(request.security_context.deadline.replace('Z','+00:00'))
                            if parent.tzinfo is None:parent=parent.replace(tzinfo=timezone.utc)
                            deadline=min(parent,datetime.fromisoformat(deadline)).isoformat()
                        context=request.security_context.narrow(deadline=deadline)
                        result=asyncio.run(self.tool_bridge.call(params['tool'],params['arguments'],context,
                                                              namespace=params.get('namespace'), cancellation_token=request.cancellation_token))
                        rpc.respond(event,{'success':True,'contentItems':[{'type':'inputText','text':result}]})
                    else:
                        rpc.respond(event)
                    continue
                if params.get('threadId') not in (None,session_id):
                    raise BackendError('App Server event belongs to another thread')
                request.emit('backend.progress',method=method)
                if method=='item/completed' and params.get('turnId')==turn_id:
                    item=params.get('item',{})
                    if item.get('type')=='agentMessage':content=item.get('text','')
                    if not isinstance(content,str) or len(content.encode())>self.output_limit:
                        raise BackendError('App Server result exceeds output limit')
                if method=='turn/completed':
                    turn=params.get('turn',{})
                    if turn.get('id')!=turn_id:raise BackendError('App Server completed another turn')
                    status=turn.get('status')
                    if interrupted:return BackendResult('', 'timed_out' if expired else 'cancelled',session_id,error='interrupted')
                    if status!='completed' or not content:
                        return BackendResult('', 'failed', session_id,error='App Server did not produce a completed result')
                    return BackendResult(content,session_id=session_id)
        except asyncio.CancelledError:
            return BackendResult('', 'cancelled',session_id,error='tool bridge cancelled')
        finally:
            with self._active_lock:
                self._rpc=self.active_thread_id=self.active_turn_id=None
            rpc.close()
