from LightResearch import enable_legacy_api
enable_legacy_api()
"""Version content fingerprints and host-reviewed evaluation changes."""
from dataclasses import replace
import copy
import pytest
from LightResearch.evolution import AgentVersion
from LightResearch.revisions import initialize_contract, propose_contract, adopt_contract
from LightAgent.persistent.store import ResearchStore, StateConflict, dumps
from LightResearch.contracts import ResearchContract, digest
from LightResearch.store import ResearchStore as DomainResearchStore


@pytest.fixture
def records(tmp_path):
    store = ResearchStore(tmp_path/'state')
    contract = ResearchContract(evaluator='numeric_mae', expected=(1,), mutable_files=('model.py',))
    profile = {'backend': {'kind': 'fixture', 'version': '1'},
               'workflow': {'name': 'research-dag', 'version': '1'},
               'context': {'strategy': 'verified-evidence', 'version': '1'},
               'tools': [{'name': 'measure', 'schema': {'type': 'object'}}]}
    version = AgentVersion.create('agent', contract, execution_profile=profile,
                                  proposal={'instructions': 'forecast', 'files': {'model.py': 'print(1)\n'}}).to_dict()
    with store.transaction() as db:
        store.put('version', version, db)
        store.put('agent', {'id': 'agent', 'contract': contract.to_dict(), 'active_version_id': version['id'],
                           'activation_revision': 0, 'epoch': 0, 'desired': 'paused', 'status': 'paused',
                           'backend': profile['backend'], 'execution_profile': profile, 'security': {},
                           'authority': {'evaluator_version': '1'}, 'cycles': 5, 'daily_cycles': 3,
                           'backend_calls': 9, 'daily_chat_calls': 2}, db)
        initialize_contract(store, 'agent', db)
    return store, contract, version


@pytest.mark.parametrize("kind", sorted(DomainResearchStore.immutable_kinds))
def test_frozen_research_record_is_immutable_through_both_stores(tmp_path, kind):
    store = DomainResearchStore(tmp_path / "state")
    with store.transaction() as db:
        record = store.put(kind, {"id": "historical", "payload": "original"}, db)
    legacy = ResearchStore(store.root)
    for writer in (store, legacy):
        with pytest.raises(StateConflict, match="immutable"), writer.transaction() as db:
            writer.put(kind, {**record, "payload": "changed"}, db, expected=record["revision"])
        assert writer.get(kind, "historical") == record


def test_execution_profile_snapshot_is_deeply_frozen_and_inherited():
    profile = {'backend': {'kind': 'codex', 'network': False}, 'tools': [{'name': 'inspect'}]}
    contract = ResearchContract(mutable_files=('model.py',))
    version = AgentVersion.create('a', contract, execution_profile=profile,
                                  proposal={'files': {'model.py': 'baseline'}})
    before = version.to_dict()
    profile['backend']['network'] = True
    public = version.to_dict(); public['execution_profile']['tools'].append({'name': 'danger'})
    assert version.to_dict() == before
    child = AgentVersion.create('a', contract, parent=before, proposal={'files': {'model.py': 'candidate'}}).to_dict()
    assert child['execution_profile_hash'] == before['execution_profile_hash']
    assert child['id'] != before['id']
    AgentVersion.validate_record(child)
    with pytest.raises(ValueError, match='cannot change'):
        AgentVersion.create('a', contract, parent=before, execution_profile=profile)
    with pytest.raises(ValueError, match='may only change'):
        AgentVersion.create('a', contract, parent=before, proposal={'execution_profile': profile})


def test_version_fingerprint_covers_configuration_and_script_contents(records):
    _, contract, version = records
    for changes in ({'instructions': 'replaced'}, {'files': [['model.py', 'changed']]},
                    {'execution_profile': {'backend': {'kind': 'other'}}}, {'generation': 500}):
        tampered = {**copy.deepcopy(version), **changes}
        with pytest.raises(ValueError, match='fingerprint'):
            AgentVersion.validate_record(tampered)
    with pytest.raises(ValueError, match='another agent'):
        AgentVersion.create('another', contract, parent=version)


def test_legacy_version_content_identity_remains_readable():
    body = dict(agent='a', parent_version_id=None, proposer_version_id=None, generation=0,
                instructions='old', files=(), contract_hash='old-contract')
    legacy = {'id': digest(dumps(body).encode()), **body, 'revision': 1}
    assert AgentVersion.validate_record(legacy) is legacy
    assert 'execution_profile' not in legacy


def test_contract_review_creates_new_series_without_resetting_budgets(records):
    store, contract, version = records
    before = store.get('agent', 'agent')
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'Use the revised held-out target.')
    # Proposal alone never changes evaluation authority.
    assert store.get('agent', 'agent')['contract'] == before['contract']
    revision = adopt_contract(store, 'agent', proposal['id'])
    after = store.get('agent', 'agent')
    assert after['contract']['expected'] == [2]
    assert after['comparison_series_id'] == revision['id'] != before['comparison_series_id']
    assert revision['parent_contract_revision_id'] == before['contract_revision_id']
    assert after['baseline_pending'] is True and after['desired'] == after['status'] == 'paused'
    for name in ('cycles', 'daily_cycles', 'backend_calls', 'daily_chat_calls'):
        assert after[name] == before[name]
    new = store.get('version', after['active_version_id'])
    assert new['parent_version_id'] == version['id'] and new['generation'] == 0
    assert new['files'] == [['model.py', 'print(1)\n']]
    assert new['execution_profile_hash'] == version['execution_profile_hash']
    assert new['contract_hash'] != version['contract_hash']
    assert store.get('version', version['id'])['instructions'] == 'forecast'
    assert adopt_contract(store, 'agent', proposal['id'])['id'] == revision['id']
    assert len(store.list('contract_revision', 'agent')) == 2


@pytest.mark.parametrize('kind,status', [('cycle', 'running'), ('cycle', 'reconciling'),
    ('candidate', 'evaluating'), ('candidate', 'uncertain'), ('candidate_retry', 'queued'),
    ('job', 'queued'), ('job', 'running'), ('attempt', 'running')])
def test_contract_approval_waits_for_quiescence(records, kind, status):
    store, contract, _ = records
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'revised target')
    with store.transaction() as db:
        store.put(kind, {'id': 'active', 'agent': 'agent', 'status': status}, db)
    with pytest.raises(StateConflict, match='unresolved'):
        adopt_contract(store, 'agent', proposal['id'])
    assert store.get('agent', 'agent')['contract']['expected'] == [1]


def test_running_researcher_cannot_adopt_contract(records):
    store, contract, _ = records
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'revised target')
    with store.transaction() as db:
        owner = store.get('agent', 'agent', db)
        owner.update(status='waiting', desired='running')
        store.put('agent', owner, db)
    with pytest.raises(StateConflict, match='pause'):
        adopt_contract(store, 'agent', proposal['id'])


@pytest.mark.parametrize('change', [{'max_storage_bytes': 1024*1024*1024}, {'max_cycles_per_day': 25},
    {'mutable_files': ('model.py', 'eval.py')}, {'recursive': True}, {'interval_seconds': 1}])
def test_contract_proposal_cannot_change_runtime_authority(records, change):
    store, contract, _ = records
    with pytest.raises(ValueError, match='may only change'):
        propose_contract(store, 'agent', replace(contract, **change), 'would expand runtime')
    assert not store.list('contract_proposal', 'agent')


def test_contract_approval_rejects_stale_execution_authority(records):
    store, contract, _ = records
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'revised target')
    with store.transaction() as db:
        owner = store.get('agent', 'agent', db)
        owner['backend']['version'] = 'changed-after-review'
        store.put('agent', owner, db)
    with pytest.raises(StateConflict, match='stale'):
        adopt_contract(store, 'agent', proposal['id'])


def test_contract_proposal_fingerprint_detects_out_of_band_tampering(records):
    store, contract, _ = records
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'revised target')
    with store.transaction() as db:
        bad = {**proposal, 'rationale': 'altered'}
        # Simulate damaged storage, not a supported writer API.
        db.execute('UPDATE records SET body=? WHERE kind=? AND id=?',
                   (dumps(bad), 'contract_proposal', proposal['id']))
    with pytest.raises(StateConflict, match='fingerprint'):
        adopt_contract(store, 'agent', proposal['id'])


def test_contract_changes_require_explicit_host_series(records):
    _, contract, version = records
    with pytest.raises(ValueError, match='host-approved'):
        AgentVersion.create('agent', replace(contract, expected=(2,)), parent=version)


def test_contract_revision_immutable_through_store(records):
    store, _, _ = records
    revision = store.list('contract_revision', 'agent')[0]
    with store.transaction() as db, pytest.raises(StateConflict, match='immutable'):
        store.put('contract_revision', {**revision, 'approved_by': 'model'}, db)


def test_research_contract_proposal_requires_verified_current_publication(records):
    store, contract, _ = records
    with pytest.raises(ValueError, match='published source'):
        propose_contract(store, 'agent', replace(contract, expected=(2,)), 'new target', proposed_by='research')
    with pytest.raises(StateConflict, match='verified publication'):
        propose_contract(store, 'agent', replace(contract, expected=(2,)), 'new target',
                         proposed_by='research', source_experiment_id='missing')
    owner = store.get('agent', 'agent')
    with store.transaction() as db:
        store.put('experiment', {'id': 'published', 'agent': 'agent', 'published': True,
                  'evaluation': {'valid': True}, 'contract_hash': digest(dumps(owner['contract']).encode()),
                  'comparison_series_id': owner['comparison_series_id']}, db)
    proposal = propose_contract(store, 'agent', replace(contract, expected=(2,)), 'new target',
                                proposed_by='research', source_experiment_id='published')
    assert proposal['proposed_by'] == 'research' and proposal['source_experiment_id'] == 'published'
    assert store.get('agent', 'agent')['contract']['expected'] == [1]
    revision = adopt_contract(store, 'agent', proposal['id'])
    assert revision['approved_by'] == 'host'


def test_legacy_contract_default_fields_preserve_comparison_identity():
    current = ResearchContract(evaluator='numeric_mae', expected=(3,))
    raw = current.to_dict()
    for field in ('max_safe_retries', 'retry_base_seconds', 'retry_max_seconds', 'max_concurrent_jobs'):
        raw.pop(field)
    body = dict(agent='legacy', parent_version_id=None, proposer_version_id=None, generation=0,
                instructions='original', files=(), contract_hash=digest(dumps(raw).encode()))
    legacy = {'id': digest(dumps(body).encode()), **body}
    child = AgentVersion.create('legacy', current, parent=legacy, parent_contract=raw,
                                proposal={'instructions': 'improved'}).to_dict()
    assert child['contract_hash'] == legacy['contract_hash']
    assert child['execution_profile'] == {}  # Compatibility does not invent binding.
    assert child['generation'] == 1 and child['parent_version_id'] == legacy['id']
    AgentVersion.validate_record(child)
    # A later generation must retain the same series identity as well.
    grandchild = AgentVersion.create('legacy', current, parent=child, parent_contract=raw,
                                     proposal={'instructions': 'improved again'}).to_dict()
    assert grandchild['contract_hash'] == legacy['contract_hash']
    with pytest.raises(ValueError, match='host-approved'):
        AgentVersion.create('legacy', replace(current, expected=(9,)), parent=legacy, parent_contract=raw)
    with pytest.raises(ValueError, match='host-approved'):
        AgentVersion.create('legacy', replace(current, max_safe_retries=3), parent=legacy, parent_contract=raw)
    with pytest.raises(ValueError, match='host-approved'):
        AgentVersion.create('legacy', current, parent=legacy, parent_contract={**raw, 'expected': [9]})
    with pytest.raises(ValueError, match='host-approved'):
        AgentVersion.create('legacy', current, parent=legacy)


def test_absence_manifest_is_immutable_and_old_version_ids_remain_valid():
    contract = ResearchContract(mutable_files=('future.py',))
    version = AgentVersion.create('a', contract, absent_files=('future.py',)).to_dict()
    with pytest.raises(ValueError, match='absence manifest'):
        AgentVersion.create('a', contract, parent=version, absent_files=())
    tampered = {**version, 'absent_files': []}
    with pytest.raises(ValueError, match='fingerprint'):
        AgentVersion.validate_record(tampered)
    # The prior schema had execution profiles but no absence field.
    body = {key: value for key, value in version.items() if key not in ('id', 'absent_files')}
    old = {'id': digest(dumps(body).encode()), **body}
    AgentVersion.validate_record(old)
    child = AgentVersion.create('a', contract, parent=old, proposal={'files': {'future.py': 'new'}}).to_dict()
    assert child['absent_files'] == () and child['files'] == (('future.py', 'new'),)
