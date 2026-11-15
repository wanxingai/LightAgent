from LightResearch import enable_legacy_api
enable_legacy_api()
"""Reference console security, state visibility and new control routes."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import shutil
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from LightAgent import AgentService, BackendResult
from LightResearch import __version__
from LightResearch.handle import AgentHandle
from LightResearch.panel import HTML, ResearchPanel
from LightAgent.persistent.storage import StorageBudgetExceeded


class PanelBackend:
    async def execute(self, request):
        return BackendResult('unused by this HTTP test')


@pytest.fixture
def panel(tmp_path):
    work = tmp_path / 'workspace'
    work.mkdir()
    service = AgentService(tmp_path / 'state', backend_factories={'fixture': PanelBackend})
    handle = service.submit('观察数据，并保留 <script>bad()</script> 字面文本', work, backend='fixture')
    panel = ResearchPanel(service, port=0).start()
    try:
        yield panel, handle
    finally:
        panel.close()


def request(panel, path, body=None, *, headers=None, raw=None):
    merged = {'Authorization': 'Bearer ' + panel.token, 'Content-Type': 'application/json'}
    merged.update(headers or {})
    data = raw if raw is not None else json.dumps(body).encode() if body is not None else None
    return urlopen(Request(panel.url + path, data=data, headers=merged), timeout=5)


def test_console_snapshot_chats_contracts_and_service_health(panel):
    p, h = panel
    chat = json.load(request(p, '/api/agents/' + h.id + '/chat', {}))
    msg = json.load(request(p, '/api/agents/' + h.id + '/chat',
                            {'chat_id': chat['id'], 'content': '最近进展如何？'}))
    snapshot = json.load(request(p, '/api/agents/' + h.id))
    assert snapshot['agent']['goal'] == h.status()['goal']
    assert snapshot['chats'][0]['id'] == chat['id']
    assert snapshot['messages'][0]['id'] == msg['id']
    assert snapshot['service']['healthy'] is False
    assert snapshot['jobs'] == snapshot['candidate_retries'] == []
    assert snapshot['contract_proposals'] == []
    assert snapshot['contract_revisions'][0]['contract'] == h.status()['contract']
    assert snapshot['versions'][0]['id'] == h.status()['active_version_id']
    response = urlopen(p.url, timeout=5)
    assert '<script>bad()</script>' not in response.read().decode()
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert "connect-src 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control'] == 'no-store'


def test_console_jobs_use_public_lifecycle_projection_without_rewriting_legacy(panel, monkeypatch):
    p, h = panel
    with h.store.transaction() as db:
        h.store.put('job', dict(id='legacy-job', agent=h.id, nonce='old-attempt',
                    status='uncertain', argv=['not-executed']), db)
        h.store.put('job', dict(id='foreign-job', agent='other-owner', nonce='foreign', status='queued'), db)
    original = h.store.get('job', 'legacy-job')
    projection = AgentHandle.job_status
    calls = []
    def observe(self, job_id):
        calls.append((self.id, job_id))
        return projection(self, job_id)
    monkeypatch.setattr(AgentHandle, 'job_status', observe)
    snapshot = json.load(request(p, '/api/agents/' + h.id))
    assert calls == [(h.id, 'legacy-job')]
    assert len(snapshot['jobs']) == 1
    state = snapshot['jobs'][0]['lifecycle']
    assert state['attempt_id'] == 'old-attempt' and state['epoch'] == 0
    assert state['output_cursor'] is None and state['reconciliation_required'] is True
    assert h.store.get('job', 'legacy-job') == original
    with pytest.raises(KeyError):
        h.job_status('foreign-job')


def test_console_rejects_invalid_json_shapes_and_cross_origin(panel):
    p, h = panel
    for data in [b'[]', b'null', b'"string"', b'{']:
        with pytest.raises(HTTPError) as e:
            request(p, '/api/agents/' + h.id + '/control', raw=data)
        assert e.value.code == 409
    for headers in [{'Host': 'attacker.example'}, {'Origin': 'https://attacker.example'}]:
        with pytest.raises(HTTPError) as e:
            request(p, '/api/agents', headers=headers)
        assert e.value.code == 403
    with pytest.raises(HTTPError) as e:
        request(p, '/api/agents', headers={'Authorization': 'Bearer wrong'})
    assert e.value.code == 401
    with pytest.raises(HTTPError) as e:
        request(p, '/api/agents', headers={'Authorization': 'Bearer invalid-é'})
    assert e.value.code == 401


def test_console_control_routes_preserve_host_decisions(panel, monkeypatch):
    p, h = panel
    calls = []
    def candidate(self, candidate_id, *, action):
        calls.append((self.id, candidate_id, action))
        return {'status': 'queued'}
    def adopt(self, proposal_id):
        calls.append((self.id, proposal_id))
        return {'status': 'adopted'}
    def prune(self, *, dry_run, older_than_seconds):
        calls.append((self.id, dry_run, older_than_seconds))
        return {'bytes': 128, 'dry_run': dry_run}
    def job(self, job_id, *, status, note):
        calls.append((self.id, job_id, status, note))
        return {'status': status}
    monkeypatch.setattr(AgentHandle, 'reconcile_candidate', candidate)
    monkeypatch.setattr(AgentHandle, 'adopt_contract', adopt)
    monkeypatch.setattr(AgentHandle, 'prune_workspaces', prune)
    monkeypatch.setattr(AgentHandle, 'reconcile_job', job)
    control = '/api/agents/' + h.id + '/control'
    assert json.load(request(p, control, {'action': 'reconcile_candidate',
        'candidate_id': 'candidate-1', 'resolution': 'retry'}))['status'] == 'queued'
    assert json.load(request(p, control, {'action': 'adopt_contract',
        'proposal_id': 'proposal-1'}))['status'] == 'adopted'
    assert json.load(request(p, control, {'action': 'preview_storage', 'dry_run': False}))['dry_run'] is True
    assert json.load(request(p, control, {'action': 'reconcile_job', 'job_id': 'job-1',
        'resolved_status': 'completed', 'note': 'Checked output.'}))['status'] == 'completed'
    assert calls == [(h.id, 'candidate-1', 'retry'), (h.id, 'proposal-1'),
                     (h.id, True, 86400), (h.id, 'job-1', 'completed', 'Checked output.')]
    assert h.status()['contract']['evaluator'] == 'evidence'
    proposal = json.load(request(p, control, {'action': 'propose_contract',
        'contract': {**h.status()['contract'], 'min_improvement': 0.5},
        'rationale': '测试审核流程，保持原有运行权限。'}))
    assert proposal['status'] == 'proposed'
    assert proposal['rationale'].startswith('测试审核流程')
    assert h.status()['contract']['min_improvement'] == 0


def test_console_budget_exhaustion_is_reported_without_dropping_connection(panel, monkeypatch):
    p, h = panel
    def fail(self, **kwargs):
        raise StorageBudgetExceeded('fixture limit')
    monkeypatch.setattr(AgentHandle, 'prune_workspaces', fail)
    with pytest.raises(HTTPError) as e:
        request(p, '/api/agents/' + h.id + '/control', {'action': 'preview_storage'})
    assert e.value.code == 429
    assert json.load(request(p, '/api/agents'))[0]['id'] == h.id


def test_console_semantics_unique_ids_safe_content_and_javascript(tmp_path):
    class Elements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = []
            self.references = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if 'id' in attrs:
                self.ids.append(attrs['id'])
            for key in ['for', 'aria-controls', 'aria-labelledby', 'aria-describedby']:
                self.references.extend(attrs.get(key, '').split())
    elements = Elements()
    elements.feed(HTML)
    assert len(elements.ids) == len(set(elements.ids))
    assert set(elements.references) <= set(elements.ids)
    assert 'role="log"' in HTML and 'role="alert"' in HTML
    assert '@media(max-width:760px)' in HTML
    assert f'<span>v{__version__}</span>' in HTML
    assert '__LIGHTRESEARCH_VERSION__' not in HTML
    script = re.search(r'<script>(.*?)</script>', HTML, re.S).group(1)
    assert 'textContent' in script
    assert not any(value in script for value in ['innerHTML', 'document.write', 'sessionStorage'])
    node = shutil.which('node')
    if node:
        path = tmp_path / 'panel.js'
        path.write_text(script)
        subprocess.run([node, '--check', str(path)], check=True, capture_output=True)


@pytest.mark.parametrize('scenario', [
    'verified_persistence_and_reload',
    'selected_agent_removed',
    'unsubmitted_input_is_not_authority',
    'unauthorized_invalid_json_clears_session',
    'rejected_restore_clears_credentials',
    'restored_snapshot_unauthorized_is_not_resaved',
    'logout_ignores_late_refresh',
    'logout_ignores_late_login',
    'logout_during_json_read',
    'older_unauthorized_cannot_clear_new_login',
    'cross_tab_logout_and_late_response',
    'storage_clear_event_logs_out',
    'temporary_failures_preserve_credentials',
    'automatic_restore_retry_and_logout_cancellation',
    'rejected_new_token_preserves_validated_session',
    'storage_failures_keep_in_memory_login',
    'invalid_saved_record_does_not_authenticate',
])
def test_console_login_session_behavior(tmp_path, scenario):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js is needed to exercise the real console JavaScript')
    page = tmp_path / 'panel.html'
    page.write_text(HTML, encoding='utf-8')
    harness = Path(__file__).with_name('panel_session_behavior.cjs')
    result = subprocess.run(
        [node, str(harness), str(page), scenario],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
