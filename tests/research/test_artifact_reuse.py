from LightResearch import enable_legacy_api
enable_legacy_api()
"""Verified artifacts are real bounded inputs to later research rounds."""
from dataclasses import replace
import json
from pathlib import Path
import stat

import pytest

from LightAgent import AgentService, BackendResult, ResearchContract
from LightAgent.cancellation import CancellationToken
from LightResearch.reuse import (HistoryLimits, INDEX_PATH, install_history,
                                        validate_reuse_request, clear_reuse_request)
from LightAgent.persistent.storage import StorageBudgetExceeded
from LightAgent.persistent.store import dumps, uid
from LightResearch.contracts import digest


class ReusingBackend:
    version = '1'

    def __init__(self, *, recursive=False, tamper=False, report_update=None):
        self.calls = []
        self.recursive = recursive
        self.tamper = tamper
        self.report_update = report_update or {}

    async def execute(self, request):
        work = Path(request.workspace)
        index = json.loads((work/INDEX_PATH).read_text()) if (work/INDEX_PATH).exists() else None
        files = [(item, work/item['local_path']) for item in index['files']] if index else []
        observed = {'candidate': 'Evaluate this candidate version' in request.prompt,
                    'index': (work/INDEX_PATH).read_bytes() if index else None,
                    'files': {item['local_path']: path.read_bytes() for item, path in files},
                    'modes': [stat.S_IMODE(path.stat().st_mode) for _, path in files],
                    'prediction': None, 'prompt': request.prompt}
        for item, path in files:
            if item['path'] == 'forecast.py':
                # This is known fixture source, exercising use rather than just
                # checking that the prompt contains a historic filename.
                namespace = {}
                exec(compile(path.read_text(), str(path), 'exec'), namespace)
                observed['prediction'] = namespace['forecast']()
        self.calls.append(observed)
        if self.tamper and files:
            files[0][1].chmod(0o600)
            files[0][1].write_text('modified history')
        (work/'forecast.py').write_text('def forecast():\n    return 42\n')
        report = {'summary': 'Reusable forecast script', 'hypothesis': 'reuse the verified implementation',
                  'evidence': ['forecast.py'], 'next_action': 'wait',
                  'predictions': [2 if observed['candidate'] else 0]}
        if self.recursive and index and not observed['candidate']:
            report['proposal'] = {'instructions': 'Use verified history before proposing another experiment.'}
        report.update(self.report_update)
        return BackendResult(json.dumps(report))


def make_service(tmp_path, *, contract=None, backend=None):
    work = tmp_path/'project'; work.mkdir()
    (work/'README.md').write_text('Run bounded research using prior verified scripts.')
    backend = backend or ReusingBackend()
    service = AgentService(tmp_path/'state', backend_factories={'fixture': lambda: backend})
    contract = contract or ResearchContract()
    handle = service.submit('Develop an experiment and reuse its verified script', work,
                            backend='fixture', contract=contract)
    return service, handle, backend, work, contract


def cycle(service, handle):
    current = service._claim(handle.id, None)
    assert current is not None
    service._cycle(current, CancellationToken())
    return service.store.get('cycle', current['id'])


def published(service, handle, *, name=None, path='artifact.txt', data=b'verified evidence',
              summary='fixture publication', hypothesis='verify provenance', report=None, **updates):
    owner = handle.status()
    blob = digest(data)
    directory = service.root/'blobs'; directory.mkdir(exist_ok=True)
    (directory/blob).write_bytes(data)
    value = {'id': name or uid(), 'agent': handle.id, 'version_id': owner['active_version_id'],
             'comparison_series_id': owner['comparison_series_id'], 'contract_hash': digest(dumps(owner['contract']).encode()),
             'published': True, 'evaluation': {'valid': True, 'score': None},
             'report': {'summary': summary, 'hypothesis': hypothesis, **(report or {})},
             'artifacts': [{'path': path, 'sha256': blob, 'blob': blob, 'bytes': len(data)}],
             **updates}
    with service.store.transaction() as db:
        service.store.put('experiment', value, db)
    return value


def history(service, handle, work, contract, **kwargs):
    target = service.root/'inputs'/uid()
    manifest = service._snapshot(work, target, contract)
    updated = install_history(service.store, handle.status(), target, contract, manifest, **kwargs)
    index = json.loads((target/INDEX_PATH).read_text()) if (target/INDEX_PATH).exists() else None
    return target, updated, index


def test_second_cycle_can_execute_first_published_script(tmp_path):
    service, handle, backend, work, _ = make_service(tmp_path)
    first, second = cycle(service, handle), cycle(service, handle)
    assert first['status'] == second['status'] == 'completed'
    assert len(handle.experiments()) == 2
    assert backend.calls[0]['index'] is None
    assert backend.calls[1]['prediction'] == 42
    assert all(mode & 0o222 == 0 for mode in backend.calls[1]['modes'])
    assert INDEX_PATH in second['manifest']['files']
    assert all(path in second['manifest']['files'] for path in backend.calls[1]['files'])
    assert 'evidence, not instructions' in backend.calls[1]['prompt'].lower()
    assert 'reuse_query' in backend.calls[1]['prompt']
    assert not (work/'forecast.py').exists() and not (work/'lightagent_history').exists()


def test_history_is_scoped_to_verified_agent_and_comparison_series(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    own = published(service, handle, summary='allowed')
    published(service, handle, summary='other series', comparison_series_id='other-series')
    published(service, handle, summary='wrong contract', contract_hash='0'*64)
    published(service, handle, summary='unverified', evaluation={'valid': False})
    published(service, handle, summary='unpublished', published=False)
    other = service.submit('another researcher', work, backend='fixture')
    foreign = published(service, other, summary='foreign researcher')
    _, _, index = history(service, handle, work, contract)
    assert index['catalog_total'] == 1 and index['catalog_complete'] is True
    assert [item['experiment_id'] for item in index['files']] == [own['id']]
    assert 'foreign researcher' not in dumps(index)
    with pytest.raises(ValueError, match='this agent and comparison series'):
        history(service, handle, work, contract, selection=[foreign['id']])


def test_report_can_request_old_experiment_and_query_beyond_recent_catalog(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    old = published(service, handle, path='archived_orchid_model.py', data=b'print("old verified model")',
                    summary='An old orchid forecast')
    for i in range(70):
        published(service, handle, path=f'recent-{i}.txt', data=f'new result {i}'.encode())
    _, _, before = history(service, handle, work, contract)
    assert before['catalog_complete'] is False
    assert old['id'] not in {record['experiment_id'] for record in before['catalog']}
    published(service, handle, report={'reuse_query': 'orchid'})
    target, _, found = history(service, handle, work, contract)
    item = next(item for item in found['files'] if item['experiment_id'] == old['id'])
    assert (target/item['local_path']).read_bytes() == b'print("old verified model")'
    assert found['query_match_count'] == 1 and found['query_complete'] is True
    assert old['id'] in {record['experiment_id'] for record in found['catalog']}
    published(service, handle, report={'reuse_experiments': [old['id']], 'reuse_query': 'recent-69'})
    _, _, explicit = history(service, handle, work, contract)
    assert explicit['files'][0]['experiment_id'] == old['id']
    assert explicit['reuse_experiments'] == [old['id']]


@pytest.mark.parametrize('reuse_request', [
    {'reuse_experiments': ['missing']}, {'reuse_experiments': ['same']*2},
    {'reuse_experiments': [str(i) for i in range(9)]}, {'reuse_query': 'x'*1025},
    {'reuse_query': ['invalid']},
])
def test_invalid_or_unavailable_report_selection_is_rejected(tmp_path, reuse_request):
    service, handle, _, work, contract = make_service(tmp_path)
    published(service, handle, report=reuse_request)
    with pytest.raises(ValueError):
        history(service, handle, work, contract)


def test_invalid_worker_request_is_rejected_before_publication(tmp_path):
    backend = ReusingBackend(report_update={'reuse_experiments': ['not-a-verified-experiment']})
    service, handle, _, _, _ = make_service(tmp_path, backend=backend)
    assert cycle(service, handle)['status'] == 'failed'
    assert not handle.experiments()
    # A corrected next execution is not poisoned by an already-published request.
    backend.report_update = {}
    handle.resume()
    assert cycle(service, handle)['status'] == 'completed'


def test_oversized_request_is_rejected_before_publication(tmp_path):
    service, handle, _, _, _ = make_service(tmp_path)
    record = published(service, handle, data=b'x'*2048)
    with pytest.raises(ValueError, match='budget'):
        validate_reuse_request(service.store, handle.status(), {'reuse_experiments': [record['id']]},
                               limits=HistoryLimits(max_bytes=1000))


def test_host_can_clear_unusable_request_without_modifying_history(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    old = published(service, handle)
    bad = published(service, handle, report={'reuse_experiments': ['legacy-unavailable-id']})
    with pytest.raises(ValueError):
        history(service, handle, work, contract)
    with pytest.raises(Exception, match='pause'):
        clear_reuse_request(service.store, handle.id)
    handle.pause()
    service.serve_forever(max_ticks=1, poll_interval=.01)
    override = clear_reuse_request(service.store, handle.id)
    assert override['source_experiment_id'] == bad['id']
    _, _, index = history(service, handle, work, contract)
    assert index['reuse_experiments'] == []
    assert service.store.get('experiment', bad['id'])['report']['reuse_experiments'] == ['legacy-unavailable-id']
    # New publications supply their own requests; the host override isn't global.
    published(service, handle, report={'reuse_experiments': [old['id']]})
    _, _, index = history(service, handle, work, contract)
    assert index['reuse_experiments'] == [old['id']]


def test_requested_foreign_series_is_rejected_not_copied(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    old = published(service, handle, comparison_series_id='old-series')
    published(service, handle, report={'reuse_experiments': [old['id']]})
    with pytest.raises(ValueError, match='comparison series'):
        history(service, handle, work, contract)


@pytest.mark.parametrize('corruption', ['body', 'symlink', 'traversal'])
def test_history_rejects_tampered_blob_and_unsafe_paths(tmp_path, corruption):
    service, handle, _, work, contract = make_service(tmp_path)
    record = published(service, handle)
    blob = service.root/'blobs'/record['artifacts'][0]['blob']
    if corruption == 'body':
        blob.write_bytes(b'corrupt evidence!')
    elif corruption == 'symlink':
        outside = tmp_path/'outside'; outside.write_bytes(b'verified evidence')
        blob.unlink(); blob.symlink_to(outside)
    else:
        with service.store.transaction() as db:
            current = service.store.get('experiment', record['id'], db)
            current['artifacts'][0]['path'] = '../outside.py'
            service.store.put('experiment', current, db)
    with pytest.raises((ValueError, OSError)):
        history(service, handle, work, contract)
    assert not list((service.root/'inputs').glob('*/lightagent_history'))


def test_history_limits_truncate_default_but_reject_oversized_explicit_request(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    first = published(service, handle, data=b'a'*16000)
    published(service, handle, data=b'b'*16000)
    limits = HistoryLimits(max_files=1, max_bytes=20000, catalog_bytes=4096)
    target, manifest, index = history(service, handle, work, contract, limits=limits)
    assert len({item['local_path'] for item in index['files']}) == 1
    assert index['omitted_count'] == 1
    original_bytes = sum(path.stat().st_size for path in work.iterdir() if path.is_file())
    assert manifest['bytes']-original_bytes <= limits.max_bytes
    assert (target/INDEX_PATH).stat().st_size <= limits.catalog_bytes
    with pytest.raises(ValueError, match='budget'):
        history(service, handle, work, contract, selection=[first['id']],
                limits=HistoryLimits(max_bytes=1000))
    with pytest.raises(ValueError, match='file budget'):
        history(service, handle, work, replace(contract, max_snapshot_files=1))


def test_history_uses_global_storage_budget_and_cleans_its_partial_copy(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    published(service, handle, data=b'x'*50000)
    target = service.root/'inputs'/uid()
    manifest = service._snapshot(work, target, contract)
    with pytest.raises(StorageBudgetExceeded):
        install_history(service.store, handle.status(), target,
                        replace(contract, max_storage_bytes=1), manifest)
    assert not (target/'lightagent_history').exists()
    assert (target/'README.md').read_text() == (work/'README.md').read_text()


def test_history_rejects_source_or_mutable_namespace_collisions(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    published(service, handle)
    with pytest.raises(ValueError, match='mutation scope'):
        history(service, handle, work, replace(contract, mutable_files=('lightagent_history/index.json',)))
    (work/'lightagent_history').mkdir()
    (work/'lightagent_history'/'index.json').write_text('project-owned content')
    with pytest.raises(ValueError, match='reserved history namespace'):
        history(service, handle, work, contract)
    assert (work/'lightagent_history'/'index.json').read_text() == 'project-owned content'


def test_history_is_the_same_frozen_input_for_baseline_and_candidate(tmp_path):
    backend = ReusingBackend(recursive=True)
    contract = ResearchContract(evaluator='numeric_mae', expected=(2,), recursive=True)
    service, handle, backend, _, _ = make_service(tmp_path, contract=contract, backend=backend)
    cycle(service, handle)
    current = cycle(service, handle)
    assert current['status'] == 'completed'
    baseline, candidate = backend.calls[-2:]
    assert not baseline['candidate'] and candidate['candidate']
    assert baseline['index'] == candidate['index']
    assert baseline['files'] == candidate['files']
    assert baseline['prediction'] == candidate['prediction'] == 42
    assert handle.records('candidate')[0]['status'] == 'accepted'


def test_editing_history_context_prevents_publication(tmp_path):
    backend = ReusingBackend(tamper=True)
    service, handle, backend, _, _ = make_service(tmp_path, backend=backend)
    assert cycle(service, handle)['status'] == 'completed'
    assert cycle(service, handle)['status'] == 'failed'
    assert len(handle.experiments()) == 1
    assert handle.status()['status'] == 'blocked'


def test_log_named_artifact_survives_snapshot_filtering(tmp_path):
    service, handle, _, work, contract = make_service(tmp_path)
    published(service, handle, path='experiment.log', data=b'archived log evidence')
    target, _, index = history(service, handle, work, contract)
    local = index['files'][0]['local_path']
    copied = service.root/'work'/uid()
    manifest = service._snapshot(target, copied, contract)
    assert local in manifest['files']
    assert (copied/local).read_bytes() == b'archived log evidence'
