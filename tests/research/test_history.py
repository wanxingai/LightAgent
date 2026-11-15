from LightResearch import enable_legacy_api
enable_legacy_api()
"""Durable history stays accessible beyond the compatibility display window."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from LightAgent import AgentService, BackendResult
from LightResearch.handle import AgentHandle
from LightResearch.panel import HTML, ResearchPanel
from LightAgent.persistent.store import ResearchStore as LegacyResearchStore, StateConflict, dumps
from LightResearch.contracts import digest


class UnusedBackend:
    async def execute(self, request):
        return BackendResult('This history test never calls a model.')


@pytest.fixture
def history(tmp_path):
    workspace = tmp_path/'workspace'
    workspace.mkdir()
    service = AgentService(tmp_path/'state', backend_factories={'fixture': UnusedBackend})
    h = service.submit('History fixture', workspace, backend='fixture')
    other = service.submit('Other researcher', workspace, backend='fixture')
    data = b'Published before the latest 1000 experiments'
    blob = digest(data)
    (service.root/'blobs').mkdir()
    (service.root/'blobs'/blob).write_bytes(data)
    version_id = h.status()['active_version_id']
    with service.store.transaction() as db:
        for index in range(1005):
            service.store.put('experiment', dict(id='exp-'+str(index), agent=h.id,
                created_at=index, published=True, version_id=version_id,
                report={'summary': 'rare oldest baseline' if index == 0 else 'ordinary experiment',
                        'hypothesis': 'A bounded fixture'},
                artifacts=[{'blob':blob, 'path':'evidence.txt', 'bytes':len(data)}] if index == 0 else []), db)
            service.store.put('cycle', dict(id='cycle-'+str(index),agent=h.id,created_at=index), db)
    return service, h, other, blob, data


def test_pages_cover_all_history_and_keep_boundary_under_new_inserts(history):
    service, h, other, blob, data = history
    assert len(h.experiments()) == 1000  # Existing callers still receive a list.
    page = h.records_page('experiment', limit=200)
    assert page['total'] == 1005 and page['has_more']
    ids = [r['id'] for r in page['items']]
    with service.store.transaction() as db:
        service.store.put('experiment', dict(id='new-after-first-page',agent=h.id), db)
    while page['next_cursor']:
        page = h.records_page('experiment', limit=200, cursor=page['next_cursor'])
        assert page['total'] == 1005
        ids.extend(r['id'] for r in page['items'])
    assert len(ids) == len(set(ids)) == 1005
    assert ids[0] == 'exp-1004' and ids[-1] == 'exp-0'
    assert 'new-after-first-page' not in ids
    assert h.records_page('experiment')['total'] == 1006


def test_cursor_scope_validation_and_search_precedes_pagination(history):
    service, h, other, blob, data = history
    cursor = h.records_page('experiment', limit=1)['next_cursor']
    for handle, kind, query in [(other,'experiment',None),(h,'cycle',None),(h,'experiment','rare')]:
        with pytest.raises(ValueError, match='cursor'):
            handle.records_page(kind, cursor=cursor, query=query)
    for value in ['garbage', base64.urlsafe_b64encode(b'[]').decode(), 'a'*1025]:
        with pytest.raises(ValueError):
            h.records_page('experiment', cursor=value)
    for value in [0, 201, True, '20']:
        with pytest.raises(ValueError):
            h.records_page('experiment', limit=value)
    page = h.records_page('experiment', query='rare', limit=1)
    assert page['total'] == 1 and page['next_cursor'] is None
    assert page['items'][0]['id'] == 'exp-0'
    assert h.search_results('rare', limit=1)[0]['id'] == 'exp-0'
    assert len(h.search_results('ordinary', limit=3)) == 3


def test_research_search_accepts_legacy_cursor_without_rewriting_history(history):
    service, handle, other, _, _ = history
    with service.store.read_transaction() as db:
        upper = db.execute('SELECT max(rowid) FROM records').fetchone()[0]
        before = db.execute("SELECT rowid FROM records WHERE kind='experiment' AND id='exp-1004'").fetchone()[0]
    original = service.store.path.read_bytes()
    query = 'ORDINARY'
    scope = hashlib.sha256(dumps(['experiment', handle.id, query]).encode()).hexdigest()
    cursor = base64.urlsafe_b64encode(dumps(
        dict(v=1, scope=scope, upper=upper, before=before)).encode()).decode()
    page = handle.records_page('experiment', cursor=cursor, query=' ORDINARY ', limit=1)
    assert page['total'] == 1004 and page['items'][0]['id'] == 'exp-1003'
    legacy = LegacyResearchStore(service.root)
    assert legacy.page('experiment', handle.id, cursor=cursor, query=query, limit=1) == page
    with pytest.raises(ValueError, match='cursor'):
        legacy.page('experiment', other.id, cursor=cursor, query=query, limit=1)
    assert service.store.path.read_bytes() == original


def test_direct_lookup_old_artifact_and_cycle_tasks_preserve_ownership(history):
    service, h, other, blob, data = history
    assert h.record('experiment','exp-0')['artifacts'][0]['blob'] == blob
    assert h.read_artifact(blob) == data
    for method in [lambda: other.record('experiment','exp-0'), lambda: other.read_artifact(blob)]:
        with pytest.raises(KeyError):
            method()
    for value in ['../../control.sqlite3', 'f'*63, 'F'*64, None]:
        with pytest.raises(ValueError):
            h.read_artifact(value)
    folder = service.root/'graphs'/'cycle-0'
    folder.mkdir(parents=True)
    with sqlite3.connect(folder/'tasks.sqlite3') as db:
        db.execute('CREATE TABLE dag_tasks(run_id TEXT,spec TEXT,state TEXT)')
        db.execute('INSERT INTO dag_tasks VALUES(?,?,?)',('cycle-0','{"goal":"old task"}','{"status":"verified"}'))
    assert h.tasks('cycle-0')[0]['spec']['goal'] == 'old task'
    assert other.tasks('cycle-0') == []
    (service.root/'blobs'/blob).write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='integrity'):
        h.read_artifact(blob)


def test_old_candidate_artifacts_and_symlink_are_not_hidden_or_followed(history, tmp_path):
    service, h, other, _, _ = history
    data = b'older candidate evidence'; blob = digest(data)
    target = service.root/'blobs'/blob
    target.write_bytes(data)
    with service.store.transaction() as db:
        for index in range(1001):
            service.store.put('candidate', {'id':'candidate-'+str(index), 'agent':h.id,
                'artifacts':[{'blob':blob}] if index == 0 else []}, db)
    assert h.read_artifact(blob) == data
    outside = tmp_path/'outside'; outside.write_bytes(data)
    target.unlink(); target.symlink_to(outside)
    with pytest.raises(ValueError, match='unsafe'):
        h.read_artifact(blob)


def test_instruction_revisions_are_queryable_and_immutable(history):
    service, h, _, _, _ = history
    with service.store.transaction() as db:
        revision = service.store.put('instruction_revision',{'id':'instruction-test','agent':h.id},db)
    assert h.records_page('instruction_revision')['items'][0]['id'] == revision['id']
    with service.store.transaction() as db, pytest.raises(StateConflict, match='immutable'):
        service.store.put('instruction_revision', revision, db)


def test_history_http_pages_lookup_search_and_authorization(history):
    service, h, other, blob, data = history
    panel = ResearchPanel(service, port=0).start()
    def request(route, query=None, token=None):
        path = panel.url+'/api/agents/'+h.id+'/'+route
        if query:
            path += '?'+urlencode(query)
        return urlopen(Request(path, headers={'Authorization':'Bearer '+(token or panel.token)}),timeout=5)
    try:
        page = json.load(request('records',{'kind':'experiment','query':'rare'}))
        assert page['total'] == 1 and page['items'][0]['id'] == 'exp-0'
        assert json.load(request('record',{'kind':'experiment','id':'exp-0'}))['id'] == 'exp-0'
        assert json.load(request('search',{'query':'rare','limit':1}))[0]['id'] == 'exp-0'
        assert json.load(request('artifact',{'blob':blob}))['text'] == data.decode()
        with pytest.raises(HTTPError) as error:
            request('records',{'kind':'experiment'},token='wrong')
        assert error.value.code == 401
        with pytest.raises(HTTPError) as error:
            request('records',{'kind':'experiment','cursor':other.records_page('version',limit=1)['next_cursor'] or 'invalid'})
        assert error.value.code == 409
        with pytest.raises(HTTPError) as error:
            request('record',{'kind':'agent','id':other.id})
        assert error.value.code == 409
    finally:
        panel.close()


def test_host_instruction_and_reuse_maintenance_http(tmp_path, monkeypatch):
    workspace = tmp_path/'workspace'; workspace.mkdir()
    service = AgentService(tmp_path/'state', backend_factories={'fixture': UnusedBackend})
    h = service.submit('Maintenance fixture',workspace,backend='fixture')
    message = h.send('Use chronological evaluation.')
    with service.store.transaction() as db:
        m = service.store.get('message',message['id'],db); m['status']='applied'
        service.store.put('message',m,db)
        owner = service.store.get('agent',h.id,db); owner.update(status='paused',desired='paused')
        service.store.put('agent',owner,db)
    calls=[]
    def clear(handle):
        calls.append(handle.id)
        return {'cleared':True}
    monkeypatch.setattr(AgentHandle,'clear_reuse_request',clear)
    panel = ResearchPanel(service,port=0).start()
    def request(route, body=None):
        return json.load(urlopen(Request(panel.url+'/api/agents/'+h.id+'/'+route,
            data=json.dumps(body).encode() if body is not None else None,
            headers={'Authorization':'Bearer '+panel.token,'Content-Type':'application/json'}),timeout=5))
    try:
        state = request('instructions')
        assert state['source_message_ids'] == [message['id']]
        result = request('control',{'action':'archive_instructions',
            'replacement':'Use only information available at the forecast date.',
            'rationale':'Reviewed the source instruction.', 'expected_fingerprint':state['fingerprint'],
            'idempotency_key':'archive-once'})
        assert result['approved_by'] == 'host'
        assert h.receipt(message['id'])['status'] == 'applied'
        assert h.receipt(message['id'])['instruction_revision_id'] == result['id']
        assert request('instructions')['active_message_count'] == 0
        assert request('control',{'action':'clear_reuse_request'}) == {'cleared':True}
        assert calls == [h.id] and h.status()['desired'] == 'paused'
    finally:
        panel.close()


@pytest.mark.parametrize('scenario', ['history_search_paging_and_polling', 'history_stale_responses',
                                     'instruction_preview_and_explicit_archive'])
def test_history_panel_behavior(tmp_path, scenario):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js is required for the real panel behavior test')
    page = tmp_path/'panel.html'
    page.write_text(HTML)
    result = subprocess.run([node,str(Path(__file__).with_name('panel_session_behavior.cjs')),str(page),scenario],
                            capture_output=True,text=True,timeout=20)
    assert result.returncode == 0, result.stdout+result.stderr
