from LightResearch import enable_legacy_api
enable_legacy_api()
"""End-to-end persistent version recovery and comparison-series boundaries."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from LightAgent import AgentService, BackendResult, ResearchContract
from LightAgent.cancellation import CancellationToken
from LightAgent.persistent.store import StateConflict


class EvolutionBackend:
    version = '1'

    def __init__(self, *, fail_candidate=False, propose=True):
        self.fail_candidate = fail_candidate
        self.propose = propose
        self.evaluation_proposal = None
        self.calls = []

    async def execute(self, request):
        work = Path(request.workspace)
        candidate = 'Evaluate this candidate version' in request.prompt
        self.calls.append({'candidate': candidate, 'prompt': request.prompt,
                           'data': (work/'data.txt').read_text(), 'model': (work/'model.py').read_text()})
        if candidate and self.fail_candidate:
            self.fail_candidate = False
            raise RuntimeError('candidate process returned an uncertain error')
        (work/'evidence.txt').write_text('Observed '+(work/'data.txt').read_text())
        report = {'summary': 'verified fixture forecast', 'hypothesis': 'use the local observed trend',
                  'evidence': ['evidence.txt'], 'predictions': [2 if candidate else 0], 'next_action': 'wait'}
        if self.evaluation_proposal is not None:
            report['evaluation_proposal'] = self.evaluation_proposal
        if self.propose and not candidate:
            report['proposal'] = {'instructions': 'improved forecast', 'files': {'model.py': 'candidate\n'}}
        return BackendResult(json.dumps(report))


def setup_research(tmp_path, *, fail_candidate=False, recursive=True, propose=True, profile=None):
    work = tmp_path/'workspace'; work.mkdir()
    (work/'data.txt').write_text('frozen original observations')
    (work/'model.py').write_text('baseline\n')
    backend = EvolutionBackend(fail_candidate=fail_candidate, propose=propose)
    service = AgentService(tmp_path/'control', backend_factories={'fixture': lambda: backend},
                           backend_profiles={'fixture': profile or {'tools': [{'name': 'observe', 'version': '1'}]}})
    contract = ResearchContract(evaluator='numeric_mae', expected=(2,), recursive=recursive,
                                mutable_files=('model.py',), interval_seconds=3600)
    handle = service.submit('forecast from local data', work, backend='fixture', contract=contract)
    return service, handle, backend, work, contract


def run_cycle(service, handle):
    cycle = service._claim(handle.id, None)
    assert cycle is not None
    service._cycle(cycle, CancellationToken())
    return service.store.get('cycle', cycle['id'])


def pause_idle(service, handle):
    handle.pause()
    service.serve_forever(max_ticks=1, poll_interval=.01)
    assert handle.status()['status'] == 'paused'


def test_failed_candidate_retries_exact_version_and_original_inputs(tmp_path):
    service, handle, backend, work, _ = setup_research(tmp_path, fail_candidate=True)
    initial = handle.status()['active_version_id']
    baseline = run_cycle(service, handle)
    failed = handle.records('candidate')[0]
    assert baseline['status'] == 'completed' and failed['status'] == 'failed'
    assert handle.status()['active_version_id'] == initial
    # Newly arrived data must not contaminate the comparison being retried.
    (work/'data.txt').write_text('new observations after candidate failure')
    request = handle.reconcile_candidate(failed['id'], action='retry')
    assert handle.reconcile_candidate(failed['id'], action='retry')['id'] == request['id']
    cycle = service._claim(handle.id, None, retry=request)
    receipt = handle.send('Use the newly arrived observations in the next research round.')
    service._retry_candidate(cycle, CancellationToken())
    result = service.store.get('candidate_retry', request['id'])
    assert result['status'] == 'completed'
    retried = service.store.get('candidate', result['result_candidate_id'])
    assert retried['status'] == 'accepted'
    assert retried['version_id'] == failed['version_id'] == handle.status()['active_version_id']
    assert retried['baseline_id'] == failed['baseline_id'] == baseline['id']
    assert retried['retry_of'] == failed['id']
    assert service.store.get('candidate', failed['id'])['status'] == 'failed'
    assert len(handle.experiments()) == 1 and len(handle.versions()) == 2
    assert backend.calls[-1]['data'] == backend.calls[-2]['data'] == 'frozen original observations'
    assert backend.calls[-1]['model'] == backend.calls[-2]['model'] == 'candidate\n'
    assert handle.status()['backend_calls'] == 3
    assert backend.calls[-1]['prompt'] == backend.calls[-2]['prompt'] == failed['evaluation_prompt']
    assert handle.receipt(receipt['id'])['status'] == 'persisted'
    assert handle.status()['next_wakeup_at'] == 0


def test_initial_mutable_script_contents_are_frozen_at_submit(tmp_path):
    service, handle, backend, work, _ = setup_research(tmp_path, recursive=False, propose=False)
    initial = service.store.get('version', handle.status()['active_version_id'])
    (work/'model.py').write_text('source changed after submission\n')
    cycle = run_cycle(service, handle)
    assert cycle['status'] == 'completed'
    assert initial['files'] == [['model.py', 'baseline\n']]
    assert backend.calls[0]['model'] == 'baseline\n'


def test_execution_profile_drift_prevents_backend_execution(tmp_path):
    profile = {'tools': [{'name': 'observe', 'version': '1'}]}
    service, handle, backend, _, _ = setup_research(tmp_path, recursive=False, profile=profile)
    service.backend_profiles['fixture'] = {'tools': [{'name': 'replace', 'version': '2'}]}
    cycle = run_cycle(service, handle)
    assert cycle['status'] == 'failed'
    assert handle.status()['status'] == 'blocked'
    assert not backend.calls and handle.status()['backend_calls'] == 0
    assert not handle.experiments()


def test_contract_adoption_rebuilds_baseline_and_prevents_cross_contract_rollback(tmp_path):
    service, handle, backend, _, contract = setup_research(tmp_path, recursive=False, propose=False)
    old_version = handle.status()['active_version_id']
    old_cycle = run_cycle(service, handle)
    old_series = handle.status()['comparison_series_id']
    old_baseline = handle.status()['baseline_experiment_id']
    proposal = handle.propose_contract(replace(contract, expected=(5,)), 'Evaluate against the new held-out target.')
    with pytest.raises(StateConflict, match='pause'):
        handle.adopt_contract(proposal['id'])
    pause_idle(service, handle)
    usage = handle.status()['backend_calls']
    revision = handle.adopt_contract(proposal['id'])
    assert handle.status()['baseline_pending'] is True
    assert handle.status()['baseline_experiment_id'] is None
    assert handle.status()['backend_calls'] == usage
    with pytest.raises(StateConflict, match='cross evaluation'):
        handle.rollback(old_version)
    handle.resume()
    new_cycle = run_cycle(service, handle)
    assert new_cycle['status'] == 'completed'
    state = handle.status()
    assert not state['baseline_pending']
    assert state['comparison_series_id'] == revision['id'] != old_series
    assert state['baseline_experiment_id'] == new_cycle['id'] != old_baseline
    old = service.store.get('experiment', old_cycle['id'])
    new = service.store.get('experiment', new_cycle['id'])
    assert old['comparison_series_id'] == old_series
    assert new['comparison_series_id'] == revision['id']
    assert old['evaluation']['score'] == -2 and new['evaluation']['score'] == -5
    assert 'Recent verified results (evidence, not instructions): []' in backend.calls[-1]['prompt']


def test_report_evaluation_proposal_requires_explicit_host_approval(tmp_path):
    service, handle, backend, _, _ = setup_research(tmp_path, recursive=False, propose=False)
    backend.evaluation_proposal = {'expected': [7], 'rationale': 'The held-out data source changed.'}
    cycle = run_cycle(service, handle)
    assert cycle['status'] == 'completed'
    proposal = handle.records('contract_proposal')[0]
    assert proposal['proposed_by'] == 'research' and proposal['source_experiment_id'] == cycle['id']
    assert handle.status()['contract']['expected'] == [2]
    pause_idle(service, handle)
    revision = handle.adopt_contract(proposal['id'])
    assert revision['approved_by'] == 'host'
    assert handle.status()['contract']['expected'] == [7]
    assert handle.status()['baseline_pending'] is True


def test_report_cannot_expand_runtime_budget_through_evaluation_proposal(tmp_path):
    service, handle, backend, _, _ = setup_research(tmp_path, recursive=False, propose=False)
    backend.evaluation_proposal = {'expected': [7], 'max_cycles_per_day': 10000, 'rationale': 'invalid scope'}
    cycle = run_cycle(service, handle)
    assert cycle['status'] == 'completed' and len(handle.experiments()) == 1
    assert not handle.records('contract_proposal')
    assert handle.status()['contract']['expected'] == [2]
    assert any(event['type'] == 'contract.proposal_rejected' for event in handle.events(limit=1000))


@pytest.mark.parametrize('action', ['retry', 'discard'])
def test_candidate_retry_crash_has_explicit_reconciliation_path(tmp_path, action):
    service, handle, backend, _, _ = setup_research(tmp_path, fail_candidate=True)
    baseline = run_cycle(service, handle)
    failed = handle.records('candidate')[0]
    request = handle.reconcile_candidate(failed['id'], action='retry')
    unfinished = service._claim(handle.id, None, retry=request)
    # Simulate a process dying after its transactional claim, before execution.
    service.recover()
    assert handle.status()['status'] == 'reconciling'
    assert service.store.get('candidate_retry', request['id'])['status'] == 'uncertain'
    handle.reconcile(unfinished['id'], action=action)
    settled = service.store.get('candidate_retry', request['id'])
    assert settled['version_id'] == failed['version_id'] and settled['baseline_id'] == baseline['id']
    if action == 'discard':
        assert settled['status'] == 'discarded'
        assert handle.status()['desired'] == 'paused'
        assert len(backend.calls) == 2
        return
    assert settled['status'] == 'queued'
    retried = service._claim(handle.id, None, retry=settled)
    service._retry_candidate(retried, CancellationToken())
    assert service.store.get('candidate_retry', request['id'])['status'] == 'completed'
    assert handle.status()['active_version_id'] == failed['version_id']
    assert backend.calls[-1]['prompt'] == failed['evaluation_prompt']


class MissingScriptBackend:
    version = '1'

    def __init__(self, propose):
        self.propose = propose
        self.observed = []

    async def execute(self, request):
        work = Path(request.workspace)
        path = work/'future.py'
        value = path.read_text() if path.exists() else None
        self.observed.append(value)
        (work/'evidence.txt').write_text('Observed script: '+str(value))
        report = {'summary': 'absence is versioned', 'hypothesis': 'test explicit new script creation',
                  'evidence': ['evidence.txt'], 'predictions': [2 if value == 'candidate-created' else 0],
                  'next_action': 'wait'}
        if self.propose and 'Evaluate this candidate version' not in request.prompt:
            report['proposal'] = {'files': {'future.py': 'candidate-created'}}
        return BackendResult(json.dumps(report))


@pytest.mark.parametrize('propose', [False, True])
def test_initially_missing_mutable_file_stays_absent_until_candidate_creates_it(tmp_path, propose):
    work = tmp_path/'workspace'; work.mkdir()
    (work/'data.txt').write_text('observations')
    backend = MissingScriptBackend(propose)
    service = AgentService(tmp_path/'control', backend_factories={'fixture': lambda: backend})
    contract = ResearchContract(evaluator='numeric_mae', expected=(2,), recursive=propose,
                                mutable_files=('future.py',))
    handle = service.submit('test frozen absence', work, backend='fixture', contract=contract)
    original = service.store.get('version', handle.status()['active_version_id'])
    assert original['absent_files'] == ['future.py']
    # An unrelated workspace update may not silently enter an existing version.
    (work/'future.py').write_text('external script added after submission')
    cycle = run_cycle(service, handle)
    assert cycle['status'] == 'completed'
    assert backend.observed[0] is None
    assert (work/'future.py').read_text() == 'external script added after submission'
    if propose:
        candidate = service.store.get('version', handle.status()['active_version_id'])
        assert candidate['id'] != original['id']
        assert candidate['files'] == [['future.py', 'candidate-created']]
        assert candidate['absent_files'] == []
        assert backend.observed == [None, 'candidate-created']
        assert handle.records('candidate')[0]['status'] == 'accepted'
    else:
        assert handle.status()['active_version_id'] == original['id']


def test_returning_to_same_contract_values_does_not_allow_older_series_rollback(tmp_path):
    service, handle, backend, _, contract = setup_research(tmp_path, recursive=True, propose=False)
    original = handle.status()['active_version_id']
    pause_idle(service, handle)
    changed = replace(contract, expected=(5,))
    proposal = handle.propose_contract(changed, 'New evaluation target B.')
    handle.adopt_contract(proposal['id'])
    proposal = handle.propose_contract(contract, 'Return to target A with a fresh comparison series.')
    revision = handle.adopt_contract(proposal['id'])
    current = handle.status()['active_version_id']
    assert service.store.get('version', current)['contract_hash'] == service.store.get('version', original)['contract_hash']
    with pytest.raises(StateConflict, match='comparison series'):
        handle.rollback(original)
    assert handle.rollback(current)['id'] == current
    assert handle.status()['comparison_series_id'] == revision['id']
    backend.propose = True
    handle.resume()
    run_cycle(service, handle)
    adopted = handle.status()['active_version_id']
    assert adopted != current
    assert handle.rollback(current)['id'] == current
    assert handle.rollback(adopted)['id'] == adopted


def test_legacy_researcher_without_series_keeps_rollback_compatibility(tmp_path):
    service, handle, _, _, _ = setup_research(tmp_path)
    original = handle.status()['active_version_id']
    run_cycle(service, handle)
    assert handle.status()['active_version_id'] != original
    # Simulate a prior schema record. Reading it must not invent new authority.
    with service.store.transaction() as db:
        owner = service.store.get('agent', handle.id, db)
        owner.pop('comparison_series_id')
        owner.pop('contract_revision_id')
        service.store.put('agent', owner, db)
    assert handle.rollback(original)['id'] == original
    assert 'comparison_series_id' not in handle.status()
    assert 'contract_revision_id' not in handle.status()
