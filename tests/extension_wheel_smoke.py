"""Verify optional research installation outside the source checkout."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def main():
    core, research = (Path(name).resolve() for name in sys.argv[1:3])
    with zipfile.ZipFile(core) as wheel:
        assert not any(name.startswith("LightResearch/") for name in wheel.namelist())
        assert "LightAgent/persistent/panel.py" not in wheel.namelist()
    with zipfile.ZipFile(research) as wheel:
        assert {"LightResearch/steering.py", "LightResearch/store.py"} <= set(wheel.namelist())
    with tempfile.TemporaryDirectory(prefix="lightagent-extension-wheel-") as directory:
        target = Path(directory) / "installed"
        environment = {**os.environ, "PYTHONPATH": str(target), "PATH": ""}
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index",
                        "--target", str(target), str(core)], check=True)
        subprocess.run([sys.executable, "-c", '''
import importlib.abc, sys
from pathlib import Path
class NoResearch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('LightResearch'):
            raise ModuleNotFoundError('research is intentionally unavailable')
sys.meta_path.insert(0, NoResearch())
from tempfile import TemporaryDirectory
from LightAgent import ControlStore, ExecutionService, BackendProbe, BackendCapabilities
from LightAgent.extensions import ExtensionRequired
from LightAgent.persistent import steering
from LightAgent.persistent.jobs import _claim_queued_job, run_job
from LightAgent.persistent.store import RecordBudgetExceeded, StateConflict
from types import SimpleNamespace
assert 'installed' in sys.modules['LightAgent'].__file__
with TemporaryDirectory() as directory:
    store = ControlStore(directory)
    assert store.page('agent', 'fixture')['items'] == []
    legacy_limits = dict(max_records=4, max_events=2, max_concurrent_jobs=1, max_storage_bytes=256 * 1024)
    with store.transaction() as db:
        owner = store.put('agent', dict(id='legacy', desired='paused', status='paused', contract=legacy_limits), db)
        for job_id in ('first', 'second'):
            store.put('job', dict(id=job_id, agent='legacy', nonce=job_id, status='queued', timeout=5,
                      cancel=False, workspace=directory, argv=[sys.executable, '-c',
                      "from pathlib import Path; Path('ran').touch()"]), db)
        frozen = store.put('version', dict(id='old-version', agent='other'), db)
        try:
            store.put('version', frozen, db)
        except StateConflict:
            pass
        else:
            raise AssertionError('core-only store weakened historical immutability')
    store.enqueue('legacy', 'fixture message')
    try:
        store.enqueue('legacy', 'excess record')
    except RecordBudgetExceeded:
        pass
    else:
        raise AssertionError('historical record cap did not apply')
    supervisor = SimpleNamespace(store=store, max_concurrent_jobs=8)
    assert _claim_queued_job(supervisor, 'first')
    assert _claim_queued_job(supervisor, 'second') is None
    (store.root / 'preexisting.bin').write_bytes(b'x' * legacy_limits['max_storage_bytes'])
    run_job(store.root, 'first')
    assert store.get('job', 'first')['error'] == 'storage_budget'
    assert not (Path(directory) / 'ran').exists()
    assert len(store.events('legacy')) == legacy_limits['max_events']
    assert store.get('agent', 'legacy') == owner
    for access in (lambda: steering.dispatch, lambda: store.page('experiment', 'fixture', query='fixture')):
        try:
            access()
        except ExtensionRequired:
            pass
        else:
            raise AssertionError('legacy research path activated without host registration')
assert 'LightResearch' not in sys.modules
print('Core import without research: PASS')
'''], cwd=directory, env=environment, check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index",
                        "--target", str(target), str(research)], check=True)
        subprocess.run([sys.executable, "-m", "pip", "check"], cwd=directory, env=environment, check=True)
        subprocess.run([sys.executable, "-c", '''
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import LightAgent, LightResearch
from LightAgent import AgentHandle, BackendResult, ChatHandle
from LightResearch import ResearchService, enable_legacy_api, steering
from LightAgent.persistent import steering as legacy_steering
from LightAgent.persistent.store import ResearchStore as LegacyResearchStore
assert 'installed' in LightAgent.__file__ and 'installed' in LightResearch.__file__
class Fixture:
    async def execute(self, request):
        if request.prompt.startswith('Independent research chat'):
            return BackendResult('wheel chat reply')
        (Path(request.workspace) / 'evidence.txt').write_text('bounded local evidence')
        return BackendResult(json.dumps(dict(summary='wheel fixture', hypothesis='package wiring',
            evidence=['evidence.txt'], next_action='wait')))
with TemporaryDirectory() as directory:
    root=Path(directory)
    workspace=root/'work'
    workspace.mkdir()
    service=ResearchService(root/'state',backend_factories={'fixture':Fixture})
    handle=service.submit('Verify optional extension packaging.',workspace,backend='fixture')
    service.serve_forever(max_ticks=1)
    assert len(handle.experiments()) == 1, handle.status()
    page = handle.records_page('experiment', query='PACKAGE', limit=1)
    assert page['total'] == 1 and page['items'] == handle.experiments()
    enable_legacy_api()
    assert legacy_steering.dispatch is steering.dispatch
    assert LegacyResearchStore(service.root).page('experiment', handle.id, query='PACKAGE', limit=1) == page
    legacy_store = LegacyResearchStore(service.root)
    assert handle.status()['status'] == 'waiting' and handle.status()['next_wakeup_at'] > 0
    message = legacy_store.enqueue(handle.id, 'wheel wakeup', 'wheel-wakeup')
    assert handle.receipt(message['id']) == message and handle.status()['next_wakeup_at'] == 0
    handle.pause()
    legacy_handle = AgentHandle.connect(handle.id, root=service.root)
    chat = legacy_handle.open_chat()
    receipt = ChatHandle(legacy_handle, chat.id).send('wheel chat', idempotency_key='wheel-chat')
    service.serve_forever(max_ticks=1)
    completed = legacy_handle.receipt(receipt['id'])
    assert completed['status'] == 'applied' and completed['response'] == 'wheel chat reply'
    assert chat.send('wheel chat', idempotency_key='wheel-chat') == completed
print('Optional extension wheel execution: PASS')
'''], cwd=directory, env=environment, check=True)


if __name__ == "__main__":
    main()
