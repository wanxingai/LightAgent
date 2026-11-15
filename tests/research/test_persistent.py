from LightResearch import enable_legacy_api
enable_legacy_api()
"""Small, deterministic end-to-end research and supervisor failure scenarios."""
import asyncio
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pytest
from LightAgent import (AgentService, AgentHandle, ResearchContract, BackendResult,
                        LightAgent, SecurityContext, ResearchEvaluator)
from LightAgent.persistent import StateConflict
from LightResearch.panel import ResearchPanel
from LightResearch import snapshot_workspace
from LightResearch.evolution import AgentVersion


def wait_for(predicate, timeout=10):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        result=predicate()
        if result:
            return result
        time.sleep(.03)
    raise AssertionError('condition did not become true')


@contextmanager
def running(service):
    errors=[]
    def run():
        try:
            service.serve_forever(poll_interval=.02)
        except BaseException as exc:
            errors.append(exc)
    thread=threading.Thread(target=run)
    thread.start()
    try:
        wait_for(service.healthy)
        yield service
    finally:
        service.stop()
        thread.join(10)
        assert not thread.is_alive()
        assert not errors, errors


class ResearchBackend:
    calls=[]
    async def execute(self, request):
        work=Path(request.workspace)
        self.calls.append(request)
        if request.prompt.startswith('Independent research chat'):
            (work/'chat-only.txt').write_text('isolated')
            return BackendResult('Research continues independently.')
        (work/'evidence.txt').write_text('observed data: 1, 2, 3; held-out forecast 4')
        prediction=4 if 'improved' in request.prompt else 0
        result=dict(summary='small forecast experiment',hypothesis='linear trend',
                    evidence=['evidence.txt'],predictions=[prediction],next_action='wait')
        if 'Evaluate this candidate' not in request.prompt:
            result['proposal']={'instructions':'improved: use the linear trend', 'files':{'model.txt':'trend'}}
        return BackendResult(json.dumps(result))


@pytest.fixture
def setup(tmp_path):
    work=tmp_path/'project';work.mkdir()
    (work/'README.md').write_text('Use local data, no external service needed.')
    (work/'data.csv').write_text('1\n2\n3\n')
    service=AgentService(tmp_path/'state',backend_factories={'fixture':ResearchBackend})
    return service,work


def test_research_inbox_evolution_rollback_chat_and_artifacts(setup):
    s,w=setup
    contract=ResearchContract(evaluator='numeric_mae',expected=(4,),recursive=True,mutable_files=('model.txt',))
    h=s.submit('forecast',w,backend='fixture',contract=contract)
    initial=h.status()['active_version_id']
    assert h.status()['limits'] == {
        name: getattr(contract, name) for name in (
            'max_records', 'max_events', 'max_storage_bytes', 'max_concurrent_jobs',
        )
    }
    message=h.send('Use chronological evaluation.',idempotency_key='update-1')
    assert h.send('Use chronological evaluation.',idempotency_key='update-1')['id']==message['id']
    with pytest.raises(StateConflict):h.send('different',idempotency_key='update-1')
    with running(s):
        wait_for(lambda:h.status()['active_version_id']!=initial)
        assert h.receipt(message['id'])['status']=='applied'
        experiment=h.experiments()[0]
        assert experiment['evaluation']['score']==-4
        candidate=h.records('candidate')[0]
        assert candidate['evaluation']['score']==0
        assert candidate['evaluated_version_id']==h.status()['active_version_id']
        assert h.read_artifact(h.artifacts()[0]['blob']).startswith(b'observed')
        assert h.open_chat().run('What are you doing?',timeout=5)=='Research continues independently.'
        assert not (w/'chat-only.txt').exists()
        assert h.status()['cycles']==1
        h.pause();wait_for(lambda:h.status()['status']=='paused')
        h.rollback(initial)
        assert h.status()['active_version_id']==initial
    reconnected=AgentHandle.connect(h.id,root=s.root)
    assert reconnected.experiments()==h.experiments()
    events=h.events();assert h.events(events[-1]['sequence'])==[]
    assert any(e['type']=='dag.updated' for e in events)


def test_input_and_candidate_authority_are_frozen(setup):
    s,w=setup
    contract=ResearchContract(evaluator='numeric_mae',expected=(4,),mutable_files=('model.txt',))
    (w/'research.json').write_text(json.dumps(contract.to_dict()))
    h=s.submit('forecast',w,backend='fixture')
    (w/'research.json').write_text('{"evaluator":"evidence"}')
    assert h.status()['contract']['evaluator']=='numeric_mae'
    with pytest.raises(ValueError):AgentVersion.create(h.id,contract,proposal={'permissions':'all'})
    with pytest.raises(ValueError):AgentVersion.create(h.id,contract,proposal={'files':{'research.json':'{}'}})
    manifest=snapshot_workspace(w,s.root/'snapshot',contract)
    assert 'research.json' not in manifest['files']
    assert not (s.root/'snapshot'/'research.json').exists()
    (s.root/'snapshot'/'data.csv').write_text('changed')
    with pytest.raises(ValueError,match='immutable'):
        ResearchEvaluator().verify({'summary':'x','hypothesis':'x','evidence':['data.csv']},s.root/'snapshot',contract,manifest)


def test_uncertain_recovery_requires_reconciliation_and_fences_old_epoch(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture')
    msg=h.send('new data',idempotency_key='one')
    cycle=s._claim(h.id,'digest')
    restarted=AgentService(s.root,backend_factories={'fixture':ResearchBackend})
    with restarted.bindings.lock('supervisor','main'):
        restarted.recover()
    assert h.status()['status']=='reconciling'
    with pytest.raises(StateConflict):h.resume()
    with pytest.raises(StateConflict):s._phase(cycle,'publish')
    h.reconcile(cycle['id'],action='retry')
    assert h.receipt(msg['id'])['status']=='persisted'
    with running(restarted):
        wait_for(h.experiments)
    assert h.receipt(msg['id'])['status']=='applied'
    assert h.status()['daily_cycles']==2


def test_submitted_result_recovered_without_backend_replay(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture')
    c=s._claim(h.id,'d')
    work=s.root/'work'/'submitted'
    manifest=snapshot_workspace(w,work,ResearchContract())
    (work/'result.txt').write_text('result')
    s._phase(c,'evaluate',status='submitted',workspace=str(work),manifest=manifest,
             report={'summary':'ready','hypothesis':'test','evidence':['result.txt'],'next_action':'wait'})
    s.recover()
    assert len(h.experiments())==1
    assert h.status()['backend_calls']==0
    s.recover()
    assert len(h.experiments())==1


def test_budget_survives_restart_and_no_hot_loop(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture',contract=ResearchContract(max_cycles_per_day=1,interval_seconds=.03))
    with running(s):
        wait_for(h.experiments)
        time.sleep(.15)
        assert h.status()['cycles']==1
    restarted=AgentService(s.root,backend_factories={'fixture':ResearchBackend})
    h.send('wake up')
    with running(restarted):
        time.sleep(.15)
        assert h.status()['cycles']==1
        assert h.status()['next_wakeup_at']>time.time()+1


def test_concurrent_supervisor_rejected(setup):
    s,w=setup
    with running(s):
        with pytest.raises(Exception,match='busy'):
            AgentService(s.root).serve_forever(max_ticks=1)


def test_pause_interrupt_and_new_message_boundary(setup):
    s,w=setup
    started=threading.Event();release=threading.Event()
    class Slow(ResearchBackend):
        async def execute(self,r):
            started.set()
            while not release.is_set() and not r.cancellation_token.cancelled:
                await asyncio.sleep(.01)
            if r.cancellation_token.cancelled:return BackendResult('',status='cancelled')
            return await super().execute(r)
    s.backend_factories['slow']=Slow
    h=s.submit('forecast',w,backend='slow')
    with running(s):
        wait_for(started.is_set)
        msg=h.send('new priority')
        assert h.receipt(msg['id'])['status']=='persisted'
        h.interrupt()
        wait_for(lambda:h.status()['status']=='paused')
        assert not h.experiments()
        release.set();h.resume()
        wait_for(h.experiments)
        assert h.receipt(msg['id'])['status']=='applied'


def test_panel_auth_origin_safe_render_and_mutation(setup):
    s,w=setup
    h=s.submit('<script>bad()</script>',w,backend='fixture')
    panel=ResearchPanel(s,port=0).start()
    try:
        assert b'textContent' in urlopen(panel.url).read()
        with pytest.raises(HTTPError) as e:urlopen(panel.url+'/api/agents')
        assert e.value.code==401
        def request(path,body=None,origin=None):
            headers={'Authorization':'Bearer '+panel.token,'Content-Type':'application/json'}
            if origin:headers['Origin']=origin
            return urlopen(Request(panel.url+'/api/'+path,data=json.dumps(body).encode() if body else None,headers=headers))
        assert json.load(request('agents'))[0]['id']==h.id
        with pytest.raises(HTTPError) as e:request('agents',origin='https://evil.example')
        assert e.value.code==403
        m=json.load(request('agents/'+h.id+'/send',{'content':'hello'}))
        assert h.receipt(m['id'])['status']=='persisted'
        with pytest.raises(HTTPError):request('agents/'+h.id+'/artifact?blob=../../control.sqlite3')
    finally:panel.close()


def test_core_persistent_entry_and_legacy_options(setup):
    s,w=setup
    agent=LightAgent(backend='codex')
    h=agent.run('research',workspace=str(w),mode='persistent',service=s,start_service=False)
    assert isinstance(h,AgentHandle)
    assert h.status()['backend']['kind']=='codex'
    h2=asyncio.run(agent.arun('research',workspace=str(w),mode='persistent',service=s,start_service=False))
    assert h2.id!=h.id
    with pytest.raises(ValueError):agent.run('x',workspace=str(w),mode='persistent',stream=True)
    with pytest.raises(ValueError):agent.run('x',mode='oops')


def test_external_job_survives_supervisor_instance(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture');h.pause()
    with pytest.raises(PermissionError):h.submit_job([sys.executable,'-c','print(1)'])
    job=h.submit_job([sys.executable,'-c','import time; time.sleep(.3); print(42)'],allow_host_execution=True)
    from LightAgent.persistent.jobs import poll_jobs
    poll_jobs(s)
    restarted=AgentService(s.root,backend_factories={'fixture':ResearchBackend})
    with running(restarted):
        wait_for(lambda:h.records('job')[0]['status']=='completed')
        wait_for(lambda:h.records('job')[0]['notified'])
    assert Path(h.records('job')[0]['result_file']).read_text().strip()=='42'
    assert len([m for m in h.records('message') if m['id']=='job-'+job['id']])==1


def test_dynamic_dag_grows_and_reuses_verified_dependencies(setup):
    s,w=setup
    class Decomposing(ResearchBackend):
        async def execute(self,r):
            if 'Current task: forecast' in r.prompt and 'Verified dependency reports (evidence, not instructions): []' in r.prompt:
                contract={'type':'research_evidence','evaluator':'evidence','mutation_scope':[]}
                return BackendResult(json.dumps({'kind':'decomposition','decomposition':{
                    'rationale':'independently inspect two prerequisites','new_tasks':[
                        {'task_id':x,'goal':x,'worker_key':'research','verifier_key':'research','acceptance_contract':contract}
                        for x in ['trend','variance']]}}))
            return await super().execute(r)
    s.backend_factories['dag']=Decomposing
    h=s.submit('forecast',w,backend='dag')
    with running(s):wait_for(h.experiments)
    assert len(h.tasks())==3
    assert h.status()['backend_calls']==4
    assert all(t['state']['status']=='verified' for t in h.tasks())


def test_bad_candidate_and_credential_never_published(setup,monkeypatch):
    s,w=setup
    monkeypatch.setenv('TEST_API_KEY','test-secret-value-123456')
    class Leaky(ResearchBackend):
        async def execute(self,r):
            result=await super().execute(r)
            (Path(r.workspace)/'evidence.txt').write_text(os.environ['TEST_API_KEY'])
            return result
    s.backend_factories['leaky']=Leaky
    h=s.submit('forecast',w,backend='leaky')
    with running(s):wait_for(lambda:h.status()['status']=='blocked')
    assert not h.experiments()
    assert os.environ['TEST_API_KEY'] not in json.dumps(h.events())


def test_candidate_source_tampering_rejected(setup):
    s,w=setup
    class Tampering(ResearchBackend):
        async def execute(self,r):
            result=await super().execute(r)
            if 'Evaluate this candidate' in r.prompt:
                (Path(r.workspace)/'model.txt').write_text('different evaluated code')
            return result
    s.backend_factories['tamper']=Tampering
    h=s.submit('forecast',w,backend='tamper',contract=ResearchContract(
        evaluator='numeric_mae',expected=(4,),recursive=True,mutable_files=('model.txt',)))
    original=h.status()['active_version_id']
    with running(s):wait_for(lambda:h.records('candidate') and h.records('candidate')[0]['status']=='failed')
    assert h.status()['active_version_id']==original
    with s.store.transaction() as db:
        version=s.store.get('version',original,db)
        with pytest.raises(StateConflict):s.store.put('version',version,db)


def test_cursor_retention_and_chat_budget(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture',contract=ResearchContract(max_events=3,max_chat_calls_per_day=1))
    with running(s):
        wait_for(h.experiments)
        chat=h.open_chat()
        chat.run('one',timeout=5)
        with pytest.raises(RuntimeError):chat.run('two',timeout=5)
    assert h.events(1)[0]['type']=='cursor.expired'
    assert h.status()['daily_chat_calls']==1
    assert h.status()['cycles']==1


@contextmanager
def model_server():
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            messages=request['messages']
            prompt='\n'.join(str(m.get('content','')) for m in messages)
            if 'Independent research chat.' in prompt:
                message={'role':'assistant','content':'Independent native chat works.'}
            elif messages[-1]['role']=='tool':
                report={'summary':'native fixture experiment','hypothesis':'constant baseline','evidence':['evidence.txt'],'next_action':'wait'}
                message={'role':'assistant','content':json.dumps(report)}
            else:
                message={'role':'assistant','content':None,'tool_calls':[{'id':'call_1','type':'function','function':{
                    'name':'edit_file','arguments':json.dumps({'path':'evidence.txt','new_text':'computed by native workspace tool'})}}]}
            response={'id':'test-response','object':'chat.completion','created':0,'model':'fixture',
                      'choices':[{'index':0,'message':message,'finish_reason':'tool_calls' if message.get('tool_calls') else 'stop'}],
                      'usage':{'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}}
            data=json.dumps(response).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield 'http://127.0.0.1:'+str(server.server_address[1])+'/v1'
    finally:server.shutdown();server.server_close();thread.join(3)


def test_native_detached_client_exit_inbox_chat_restart(tmp_path):
    work=tmp_path/'input';work.mkdir();(work/'README.md').write_text('Run a tiny local experiment.')
    root=tmp_path/'control'
    with model_server() as url:
        script='''from LightResearch import enable_legacy_api
enable_legacy_api()
import sys
from LightAgent import LightAgent, LocalWorkspaceProvider
agent=LightAgent(model='fixture',base_url=sys.argv[3],execution_provider=LocalWorkspaceProvider(allow_host_execution=True))
h=agent.run('Research a tiny baseline.',workspace=sys.argv[1],mode='persistent',service_root=sys.argv[2])
print('HANDLE='+h.id,flush=True)
'''
        env=dict(os.environ,OPENAI_API_KEY='local-fixture-credential')
        client=subprocess.run([sys.executable,'-c',script,str(work),str(root),url],env=env,capture_output=True,text=True,timeout=30)
        assert client.returncode==0, client.stderr
        aid=next(line[7:] for line in client.stdout.splitlines() if line.startswith('HANDLE='))
        h=AgentHandle(aid,root);s=AgentService(root)
        try:
            wait_for(h.experiments,20)
            msg=h.send('Verify again after this update.')
            wait_for(lambda:h.receipt(msg['id'])['status']=='applied',20)
            assert h.open_chat().run('Status?',timeout=20)=='Independent native chat works.'
            h.pause();wait_for(lambda:h.status()['status']=='paused')
            s.request_shutdown();wait_for(lambda:not s.healthy())
            # Recovery is a new daemon, using env credentials rather than persisted secrets.
            s.start(env={'OPENAI_API_KEY':'local-fixture-credential'})
            h.resume();wait_for(lambda:len(h.experiments())>=3,20)
            assert 'local-fixture-credential' not in (root/'control.sqlite3').read_bytes().decode('latin1')
        finally:
            s.request_shutdown();wait_for(lambda:not s.healthy(),20)


def test_process_crash_does_not_replay_claimed_work(tmp_path):
    w=tmp_path/'input';w.mkdir();(w/'README.md').write_text('fixture')
    s=AgentService(tmp_path/'state')
    h=s.submit('do work',w)
    msg=h.send('durable human input')
    script='''from LightResearch import enable_legacy_api
enable_legacy_api()
import sys,time
from LightAgent import AgentService
s=AgentService(sys.argv[1])
with s.bindings.lock('supervisor','main'):
 c=s._claim(sys.argv[2],'watch')
 print(c['id'],flush=True)
 time.sleep(30)
'''
    process=subprocess.Popen([sys.executable,'-c',script,str(s.root),h.id],stdout=subprocess.PIPE,text=True)
    try:
        cycle_id=process.stdout.readline().strip()
        assert cycle_id
        process.kill();process.wait(timeout=5)
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=5)
        process.stdout.close()
    with s.bindings.lock('supervisor','main'):s.recover()
    assert h.status()['status']=='reconciling'
    assert h.status()['backend_calls']==0
    h.reconcile(cycle_id,action='discard')
    assert h.receipt(msg['id'])['status']=='discarded'
    assert h.status()['status']=='paused'


def test_rollback_during_candidate_evaluation_prevents_late_adoption(setup):
    s,w=setup
    started=threading.Event();release=threading.Event()
    class SlowCandidate(ResearchBackend):
        async def execute(self,r):
            if 'Evaluate this candidate' in r.prompt:
                started.set()
                while not release.is_set():await asyncio.sleep(.01)
            return await super().execute(r)
    s.backend_factories['slow-candidate']=SlowCandidate
    h=s.submit('forecast',w,backend='slow-candidate',contract=ResearchContract(
        evaluator='numeric_mae',expected=(4,),recursive=True,mutable_files=('model.txt',)))
    original=h.status()['active_version_id']
    with running(s):
        wait_for(started.is_set)
        h.rollback(original)
        release.set()
        wait_for(lambda:h.records('candidate')[0]['status']=='accepted_not_adopted')
        assert h.status()['active_version_id']==original


def test_recursive_versions_continue_from_adopted_parent(setup):
    s,w=setup
    class Improving(ResearchBackend):
        async def execute(self,r):
            if r.prompt.startswith('Independent research chat'):return await super().execute(r)
            marker=r.prompt.split('Version instructions: ',1)[1].split('\nHuman updates:',1)[0]
            generation=int(marker.split('=')[1]) if marker.startswith('level=') else 0
            (Path(r.workspace)/'evidence.txt').write_text('level '+str(generation))
            return BackendResult(json.dumps({'summary':'incremental fixture','hypothesis':'test lineage',
                'evidence':['evidence.txt'],'predictions':[generation],'next_action':'wait',
                'proposal':{'instructions':'level='+str(generation+1)}}))
    s.backend_factories['recursive']=Improving
    h=s.submit('forecast',w,backend='recursive',contract=ResearchContract(
        evaluator='numeric_mae',expected=(3,),recursive=True,max_generations=2,interval_seconds=.06,max_cycles_per_day=3))
    with running(s):
        wait_for(lambda:len([c for c in h.records('candidate') if c['status']=='accepted'])==2)
        wait_for(lambda:len(h.experiments())==3)
    active=s.store.get('version',h.status()['active_version_id'])
    assert active['generation']==2
    assert active['proposer_version_id']==active['parent_version_id']
    assert s.store.get('version',active['parent_version_id'])['generation']==1
    assert h.status()['backend_calls']==5


def test_process_death_during_publish_rolls_back_and_recovers_once(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture')
    message=h.send('durable update')
    c=s._claim(h.id,'watch')
    work=s.root/'submitted-work'
    manifest=snapshot_workspace(w,work,ResearchContract())
    (work/'evidence.txt').write_text('durable result')
    s._phase(c,'evaluate',status='submitted',workspace=str(work),manifest=manifest,
             report={'summary':'recovered','hypothesis':'test atomic publish','evidence':['evidence.txt'],'next_action':'wait'})
    script='''from LightResearch import enable_legacy_api
enable_legacy_api()
import sys,time
from LightAgent import AgentService
s=AgentService(sys.argv[1])
# Match the host authority used to prepare this test record.
original=s.store.event
def event(agent,kind,data,db):
 if kind=='experiment.published':
  print('before_commit',flush=True)
  time.sleep(30)
 return original(agent,kind,data,db)
s.store.event=event
s._finalize(s.store.get('cycle',sys.argv[2]))
'''
    child=subprocess.Popen([sys.executable,'-c',script,str(s.root),c['id']],stdout=subprocess.PIPE,text=True)
    try:
        assert child.stdout.readline().strip()=='before_commit'
        child.kill();child.wait(timeout=5)
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
        child.stdout.close()
    assert not h.experiments()
    assert h.receipt(message['id'])['status']=='claimed'
    s.recover();s.recover()
    assert len(h.experiments())==1
    assert h.receipt(message['id'])['status']=='applied'


def test_uncertain_candidate_never_adopted_on_recovery(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture')
    original=h.status()['active_version_id']
    from LightAgent.persistent.store import uid
    candidate=AgentVersion.create(h.id,ResearchContract(),parent=s.store.get('version',original),proposal={'instructions':'candidate'}).to_dict()
    with s.store.transaction() as db:
        s.store.put('version',candidate,db)
        s.store.put('candidate',dict(id=uid(),agent=h.id,version_id=candidate['id'],status='evaluating'),db)
    s.recover()
    assert h.records('candidate')[0]['status']=='uncertain'
    assert h.status()['active_version_id']==original


def test_durable_experimental_steering_is_bound_to_exact_attempt(setup):
    from LightAgent import BackendCapabilities
    s,w=setup
    received=threading.Event()
    class Steerable(ResearchBackend):
        capabilities=BackendCapabilities(steer=True)
        def steer(self,content,*,expected_turn_id):
            if expected_turn_id!='current-turn':raise RuntimeError('stale turn')
            received.set()
        async def execute(self,r):
            r.emit('backend.turn',turn_id='current-turn',session_id='current-session')
            until=time.monotonic()+5
            while not received.is_set() and time.monotonic()<until:await asyncio.sleep(.01)
            return await super().execute(r)
    s.backend_factories['steerable']=Steerable
    h=s.submit('forecast',w,backend='steerable')
    with running(s):
        attempt=wait_for(lambda:next((a for a in h.records('attempt') if a.get('turn_id')),None))
        stale=h.steer('wrong',attempt_id=attempt['id'],expected_turn_id='old')
        wait_for(lambda:h.receipt(stale['id'])['status']=='rejected')
        current=h.steer('additional constraint',attempt_id=attempt['id'],expected_turn_id='current-turn')
        wait_for(lambda:h.receipt(current['id'])['status']=='applied')
        assert h.experiments()


def test_expanded_input_rejected_without_unbounded_read(setup):
    s,w=setup
    contract=ResearchContract()
    work=s.root/'expanded-input'
    manifest=snapshot_workspace(w,work,contract)
    with (work/'data.csv').open('wb') as stream:stream.truncate(1024*1024*1024)
    (work/'e.txt').write_text('small evidence')
    with pytest.raises(ValueError,match='immutable'):
        ResearchEvaluator().verify({'summary':'test','hypothesis':'test','evidence':['e.txt']},work,contract,manifest)


def test_old_inbox_and_applied_instructions_survive_more_than_1000_chat_records(setup):
    from LightAgent.cancellation import CancellationToken
    s,w=setup
    h=s.submit('forecast',w,backend='fixture')
    applied=h.send('Always preserve chronological evaluation.',idempotency_key='old-applied')
    pending=h.send('Include the oldest pending update.',idempotency_key='old-pending')
    with s.store.transaction() as db:
        m=s.store.get('message',applied['id'],db);m['status']='applied';s.store.put('message',m,db)
        for i in range(1005):
            s.store.put('message',dict(id='noise-'+str(i),agent=h.id,kind='chat',chat_id='unrelated',
                                      status='applied',content='irrelevant'),db)
    c=s._claim(h.id,'watch')
    assert c['messages']==[pending['id']]
    s._cycle(c,CancellationToken())
    assert h.receipt(pending['id'])['status']=='applied'
    assert 'Always preserve chronological evaluation.' in ResearchBackend.calls[-1].prompt
    assert 'Include the oldest pending update.' in ResearchBackend.calls[-1].prompt


def test_old_chat_is_scheduled_despite_newer_history(setup):
    s,w=setup
    h=s.submit('forecast',w,backend='fixture');h.pause()
    chat=h.open_chat();message=chat.send('old pending chat')
    with s.store.transaction() as db:
        for i in range(1005):
            s.store.put('message',dict(id='recent-chat-'+str(i),agent=h.id,kind='chat',chat_id='other',
                                      status='applied',content='irrelevant'),db)
    with running(s):
        wait_for(lambda:h.receipt(message['id'])['status']=='applied')
    assert 'independently' in h.receipt(message['id'])['response']


@pytest.mark.parametrize('legacy', [False, True])
def test_inbox_and_research_wakeup_commit_or_rollback_together(setup, monkeypatch, legacy):
    from LightAgent.persistent.store import ResearchStore as LegacyResearchStore

    s, w = setup
    h = s.submit('forecast', w, backend='fixture')
    store = LegacyResearchStore(s.root) if legacy else h.store
    with store.transaction() as db:
        owner = store.get('agent', h.id, db)
        owner['next_wakeup_at'] = 12345
        store.put('agent', owner, db)
    before = h.status()
    event = store.event

    def fail_event(agent, kind, payload, db):
        event(agent, kind, payload, db)
        assert store.get('message', 'atomic', db)['status'] == 'persisted'
        assert store.get('agent', h.id, db)['next_wakeup_at'] == 0
        assert h.store.get('message', 'atomic') is None
        assert h.status() == before
        raise RuntimeError('injected failure after writing receipt, wakeup and event')

    events = h.events()
    with monkeypatch.context() as patch:
        patch.setattr(store, 'event', fail_event)
        with pytest.raises(RuntimeError, match='injected failure'):
            store.enqueue(h.id, 'wake up', 'atomic')
    assert h.store.get('message', 'atomic') is None
    assert h.status() == before and h.events() == events

    message = store.enqueue(h.id, 'wake up', 'atomic')
    assert h.receipt('atomic') == message and h.status()['next_wakeup_at'] == 0
    with store.transaction() as db:
        owner = store.get('agent', h.id, db)
        owner['next_wakeup_at'] = 23456
        store.put('agent', owner, db)
    assert store.enqueue(h.id, 'wake up', 'atomic') == message
    assert h.status()['next_wakeup_at'] == 23456
    chat = h.open_chat()
    other = s.submit('other research', w, backend='fixture')
    with pytest.raises(ValueError, match='does not belong'):
        store.enqueue(other.id, 'foreign chat', kind='chat', chat_id=chat.id)
    assert store.enqueue(h.id, 'independent chat', kind='chat', chat_id=chat.id)['status'] == 'persisted'
    assert h.status()['next_wakeup_at'] == 23456


def test_shutdown_drains_claimed_chat_and_restart_keeps_unclaimed_chat(setup):
    s, w = setup
    started, release = threading.Event(), threading.Event()
    calls = []

    class BoundedChat:
        async def execute(self, request):
            calls.append(request.prompt.rsplit('\nUser: ', 1)[-1])
            started.set()
            while not release.is_set():
                assert not request.cancellation_token.cancelled
                await asyncio.sleep(.01)
            return BackendResult('chat complete')

    s.backend_factories['chat-fixture'] = BoundedChat
    h = s.submit('forecast', w, backend='chat-fixture')
    h.pause()
    chat = h.open_chat()
    first = chat.send('first', idempotency_key='first')
    with running(s):
        try:
            assert started.wait(5)
            second = chat.send('second', idempotency_key='second')
            s.request_shutdown()
            wait_for(lambda: s.store.get('service', 'main')['status'] == 'stopping')
            assert h.receipt(first['id'])['status'] == 'delivered'
            assert h.receipt(second['id'])['status'] == 'persisted'
        finally:
            release.set()
    receipt = h.receipt(first['id'])
    assert receipt['status'] == 'applied' and calls == ['first']
    assert h.status()['desired'] == 'paused'
    assert s.store.get('service', 'main')['status'] == 'stopped'
    restarted = AgentService(s.root, backend_factories={'chat-fixture': BoundedChat})
    reconnected = AgentHandle.connect(h.id, root=s.root)
    assert reconnected.chat(chat.id).send('first', idempotency_key='first') == receipt
    with running(restarted):
        wait_for(lambda: reconnected.receipt(second['id'])['status'] == 'applied')
    assert reconnected.receipt(first['id']) == receipt
    assert calls == ['first', 'second']


def test_service_shutdown_drains_work_and_restart_preserves_running_intent(setup):
    s,w=setup
    started=threading.Event();release=threading.Event();errors=[]
    class Bounded(ResearchBackend):
        async def execute(self,r):
            started.set()
            while not release.is_set():
                assert not r.cancellation_token.cancelled
                await asyncio.sleep(.01)
            return await super().execute(r)
    s.backend_factories['bounded']=Bounded
    h=s.submit('forecast',w,backend='bounded')
    message=h.send('Survive shutdown.')
    def serve():
        try:s.serve_forever(poll_interval=.01)
        except BaseException as exc:errors.append(exc)
    thread=threading.Thread(target=serve);thread.start()
    try:
        wait_for(started.is_set)
        s.request_shutdown()
        wait_for(lambda:s.store.get('service','main')['status']=='stopping')
        assert h.status()['desired']=='running'
    finally:
        release.set();thread.join(10)
    assert not thread.is_alive() and not errors
    assert h.receipt(message['id'])['status']=='applied'
    assert h.status()['desired']=='running'
    assert len(h.experiments())==1
    h.send('Next cycle after restart.')
    restarted=AgentService(s.root,backend_factories={'bounded':Bounded})
    with running(restarted):wait_for(lambda:len(h.experiments())==2)
    assert h.status()['daily_cycles']==2


def test_job_notification_capacity_backpressure_isolated_and_retried(setup):
    from LightAgent.persistent.jobs import poll_jobs
    s,w=setup
    # The shared execution-budget account is now a durable control record too.
    h=s.submit('limited',w,backend='fixture',contract=ResearchContract(max_records=7))
    job=h.submit_job([sys.executable,'-c','pass'],allow_host_execution=True)
    with s.store.transaction() as db:
        j=s.store.get('job',job['id'],db);j['status']='completed';s.store.put('job',j,db)
        s.store.put('fixture',dict(id='removable',agent=h.id),db)
    other=s.submit('unaffected',w,backend='fixture')
    with running(s):
        wait_for(other.experiments)
        pending=s.store.get('job',job['id'])
        assert not pending['notified']
        assert pending['notification_error']=='inbox_record_budget'
        assert pending['notification_retry_at']>time.time()
    # Free a disposable record, then reconnect with a fresh supervisor instance.
    with s.store.transaction() as db:
        db.execute("DELETE FROM records WHERE kind='fixture' AND id='removable'")
        j=s.store.get('job',job['id'],db);j['notification_retry_at']=0;s.store.put('job',j,db)
    restarted=AgentService(s.root,backend_factories={'fixture':ResearchBackend})
    poll_jobs(restarted);poll_jobs(restarted)
    assert s.store.get('job',job['id'])['notified']
    assert len([m for m in s.store.scan('message',h.id) if m['id']=='job-'+job['id']])==1


def test_submission_retry_concurrency_and_startup_failure_are_idempotent(setup,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from LightAgent import ServiceStartupError
    s,w=setup
    def fail_start(**kwargs):raise TimeoutError('simulated startup timeout')
    monkeypatch.setattr(s,'start',fail_start)
    with pytest.raises(ServiceStartupError) as error:
        s.submit('one researcher',w,backend='fixture',start=True,idempotency_key='request-1')
    original=error.value.handle
    assert error.value.agent_id==original.id
    assert error.value.root==str(s.root)
    assert error.value.request_id=='request-1'
    # Concurrent retries from independent host instances race on the same DB.
    def retry(_):
        host=AgentService(s.root,backend_factories={'fixture':ResearchBackend})
        return host.submit('one researcher',w,backend='fixture',idempotency_key='request-1').id
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert set(pool.map(retry,range(8)))=={original.id}
    assert len(list(s.store.scan('agent')))==1
    assert len([e for e in original.events() if e['type']=='agent.created'])==1
    with pytest.raises(StateConflict):
        s.submit('different researcher',w,backend='fixture',idempotency_key='request-1')
    with pytest.raises(ServiceStartupError) as generated:
        s.submit('generated request',w,backend='fixture',start=True)
    retry_handle=s.submit('generated request',w,backend='fixture',idempotency_key=generated.value.request_id)
    assert retry_handle.id==generated.value.agent_id


def test_core_persistent_run_accepts_creation_idempotency_key(tmp_path):
    w=tmp_path/'project';w.mkdir()
    agent=LightAgent(backend='codex')
    kwargs=dict(workspace=w,mode='persistent',service_root=tmp_path/'state',start_service=False,idempotency_key='sdk-create')
    first=agent.run('goal',**kwargs)
    assert agent.run('goal',**kwargs).id==first.id
    with pytest.raises(StateConflict):agent.run('changed',**kwargs)


def test_snapshot_copies_cannot_publish_after_storage_budget_exhaustion(setup):
    from LightAgent.cancellation import CancellationToken
    from LightAgent.persistent.storage import StorageBudget
    s,w=setup
    (w/'large.txt').write_bytes(b'x'*(100*1024))
    # Reserve room for the version/contract ledger and graph database. This
    # scenario exhausts capacity on additional snapshots, not initial metadata.
    limit=384*1024
    h=s.submit('forecast',w,backend='fixture',contract=ResearchContract(max_storage_bytes=limit))
    assert s._storage_bytes()+100*1024+StorageBudget.CONTROL_HEADROOM<limit
    calls=len(ResearchBackend.calls)
    cycle=s._claim(h.id,'watch');assert cycle
    s._cycle(cycle,CancellationToken())
    assert (s.root/'inputs'/cycle['id']/'large.txt').stat().st_size==100*1024
    assert len(ResearchBackend.calls)==calls
    assert not h.experiments()
    assert h.status()['status']=='blocked'
    assert s._storage_bytes()<limit


def test_managed_storage_allocation_is_serialized_across_processes(setup):
    s,w=setup
    script='''from LightResearch import enable_legacy_api
enable_legacy_api()
import sys
from pathlib import Path
from LightAgent.persistent.store import ResearchStore
from LightAgent.persistent.storage import StorageBudget,StorageBudgetExceeded
budget=StorageBudget(ResearchStore(sys.argv[1]),450*1024)
try:
 budget.write_bytes(Path(sys.argv[1])/sys.argv[2],b'x'*(256*1024))
 print('written')
except StorageBudgetExceeded:
 print('blocked')
'''
    children=[subprocess.Popen([sys.executable,'-c',script,str(s.root),str(i)+'.bin'],stdout=subprocess.PIPE,text=True) for i in range(2)]
    results=[]
    try:
        for child in children:
            output,_=child.communicate(timeout=15)
            assert child.returncode==0
            results.append(output.strip())
    finally:
        for child in children:
            if child.poll() is None:child.kill();child.wait(timeout=5)
    assert sorted(results)==['blocked','written']
    assert s._storage_bytes()<450*1024


def test_backend_storage_overrun_is_cancelled_and_never_published(setup):
    s,w=setup
    cancelled=threading.Event()
    class Overflow:
        async def execute(self,r):
            (Path(r.workspace)/'huge.bin').write_bytes(b'x'*(2*1024*1024))
            until=time.monotonic()+5
            while not r.cancellation_token.cancelled and time.monotonic()<until:await asyncio.sleep(.01)
            if r.cancellation_token.cancelled:cancelled.set()
            return BackendResult(json.dumps(dict(summary='must not publish',hypothesis='test',evidence=['huge.bin'],next_action='wait')))
    s.backend_factories['overflow']=Overflow
    h=s.submit('forecast',w,backend='overflow',contract=ResearchContract(max_storage_bytes=1024*1024))
    with running(s):
        wait_for(lambda:h.status()['status']=='blocked')
        assert cancelled.is_set()
        assert not h.experiments()
        assert h.status()['desired']=='running'


def test_chat_storage_budget_checked_before_backend(setup):
    s,w=setup
    (w/'large.txt').write_bytes(b'x'*(256*1024))
    h=s.submit('forecast',w,backend='fixture',contract=ResearchContract(max_storage_bytes=256*1024))
    h.pause();message=h.open_chat().send('status')
    calls=len(ResearchBackend.calls)
    with running(s):wait_for(lambda:h.receipt(message['id'])['status']=='failed')
    assert len(ResearchBackend.calls)==calls
    assert h.receipt(message['id'])['error']=='StorageBudgetExceeded'
    assert not (s.root/'chat-work'/message['id']).exists()


def test_job_output_and_notification_share_storage_budget(setup):
    from LightAgent.persistent.jobs import run_job,poll_jobs
    from LightAgent.persistent.storage import StorageBudget
    s,w=setup
    limit=512*1024
    h=s.submit('limited disk',w,backend='fixture',contract=ResearchContract(max_storage_bytes=limit))
    job=h.submit_job([sys.executable,'-c',"print('x'*60000)"],allow_host_execution=True)
    with s.store.transaction() as db:
        j=s.store.get('job',job['id'],db);j.update(status='launching',launched_at=time.time());s.store.put('job',j,db)
    padding=s.root/'host-archive.bin'
    padding.write_bytes(b'x'*(limit-s._storage_bytes()-StorageBudget.CONTROL_HEADROOM-32*1024))
    run_job(s.root,job['id'])
    result=s.store.get('job',job['id'])
    assert result['status']=='failed' and result['error']=='storage_budget'
    assert not (s.root/'job-output'/job['id']).exists()
    # Consume remaining admission capacity: notification must stay durable.
    with padding.open('ab') as stream:stream.write(b'x'*(40*1024))
    poll_jobs(s)
    assert s.store.get('job',job['id'])['notification_error']=='storage_budget'
    assert not s.store.get('job',job['id'])['notified']
    padding.unlink()
    with s.store.transaction() as db:
        j=s.store.get('job',job['id'],db);j['notification_retry_at']=0;s.store.put('job',j,db)
    poll_jobs(s)
    assert s.store.get('job',job['id'])['notified']
