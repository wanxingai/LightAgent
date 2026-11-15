from LightResearch import enable_legacy_api
enable_legacy_api()
"""Host-reviewed instruction retirement without losing receipts or authority."""
import json
from pathlib import Path

import pytest

from LightAgent import AgentService, BackendResult, CancellationToken, ResearchContract
from LightResearch.instructions import (archive_instructions, cycle_instructions,
                                                instruction_state)
from LightAgent.persistent.store import StateConflict


class ArchiveBackend:
    async def execute(self, request):
        assert 'Reviewed constraints: keep the chronological split.' in request.prompt
        assert 'NEW PENDING REQUIREMENT' in request.prompt
        assert 'x' * 1000 not in request.prompt
        Path(request.workspace, 'evidence.txt').write_text('used the reviewed constraints')
        return BackendResult(json.dumps(dict(summary='continued after host review', hypothesis='baseline',
                          evidence=['evidence.txt'], next_action='wait')))


@pytest.fixture
def researcher(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'README.md').write_text('Local input instructions.')
    service = AgentService(tmp_path / 'control', backend_factories={'fixture': ArchiveBackend})
    handle = service.submit('bounded research', project, backend='fixture')
    with service.store.transaction() as db:
        owner = service.store.get('agent', handle.id, db)
        owner.update(status='paused', desired='paused')
        service.store.put('agent', owner, db)
    return service, handle, project


def applied(service, handle, content, key):
    record = handle.send(content, idempotency_key=key)
    with service.store.transaction() as db:
        record = service.store.get('message', record['id'], db)
        record.update(status='applied', applied_at=1, goal_revision=1)
        service.store.put('message', record, db)
    return handle.receipt(record['id'])


def archive(service, handle, **kwargs):
    return archive_instructions(service.store, handle.id,
        replacement='Reviewed constraints: keep the chronological split.', rationale='Host reviewed every original requirement.',
        expected_fingerprint=instruction_state(service.store, handle.id)['fingerprint'], **kwargs)


def test_overflow_recovers_after_review_and_restart_without_losing_receipts(researcher):
    service, handle, project = researcher
    originals = [applied(service, handle, 'x' * 65536, f'message-{n}') for n in range(2)]
    pending = handle.send('NEW PENDING REQUIREMENT')
    state = instruction_state(service.store, handle.id)
    assert state['active_bytes'] > state['context_budget']
    handle.resume()
    failed = service._claim(handle.id, 'fixture')
    assert failed is None
    assert handle.status()['status'] == 'blocked'
    assert handle.status()['backend_calls'] == 0
    # A paused, drained supervisor is the explicit approval boundary.
    with service.store.transaction() as db:
        owner = service.store.get('agent', handle.id, db)
        owner.update(desired='paused', status='paused')
        service.store.put('agent', owner, db)
    revision = archive(service, handle, idempotency_key='review-1')
    before = handle.status()
    assert before['cycles'] == 0 and before['desired'] == 'paused'
    for original in originals:
        after = handle.receipt(original['id'])
        for key in ('content', 'status', 'applied_at', 'goal_revision'):
            assert after[key] == original[key]
        assert after['instruction_revision_id'] == revision['id']
    assert 'instruction_revision_id' not in handle.receipt(pending['id'])
    restarted = AgentService(service.root, backend_factories={'fixture': ArchiveBackend})
    handle.resume()
    cycle = restarted._claim(handle.id, 'fixture')
    restarted._cycle(cycle, CancellationToken())
    assert handle.status()['status'] == 'waiting'
    assert handle.status()['cycles'] == 1 and handle.status()['backend_calls'] == 1
    assert handle.receipt(pending['id'])['status'] == 'applied'
    assert handle.experiments()[0]['instruction_revision_id'] == revision['id']


def test_archive_is_idempotent_but_stale_review_and_changed_key_fail(researcher):
    service, handle, _ = researcher
    applied(service, handle, 'original instruction', 'one')
    snapshot = instruction_state(service.store, handle.id)
    args = dict(replacement='reviewed text', rationale='reviewed explicitly',
                expected_fingerprint=snapshot['fingerprint'], idempotency_key='once')
    result = archive_instructions(service.store, handle.id, **args)
    assert archive_instructions(service.store, handle.id, **args)['id'] == result['id']
    with pytest.raises(StateConflict, match='reused'):
        archive_instructions(service.store, handle.id, **{**args, 'replacement': 'different'})
    with pytest.raises(StateConflict, match='changed'):
        archive_instructions(service.store, handle.id, **{**args, 'idempotency_key': 'again'})
    assert len(service.store.list('instruction_revision', handle.id)) == 1


@pytest.mark.parametrize('kind,status', [('cycle','running'), ('cycle','reconciling'),
    ('candidate','evaluating'), ('candidate_retry','queued'), ('job','running'), ('attempt','running')])
def test_archive_waits_for_unresolved_work(researcher, kind, status):
    service, handle, _ = researcher
    applied(service, handle, 'keep this constraint', 'one')
    with service.store.transaction() as db:
        service.store.put(kind, dict(id='active', agent=handle.id, status=status), db)
    with pytest.raises(StateConflict, match='unresolved'):
        archive(service, handle)
    assert 'instruction_revision_id' not in handle.receipt('one')


def test_running_researcher_cannot_archive_or_silently_discard_pending_messages(researcher):
    service, handle, _ = researcher
    applied(service, handle, 'must remain', 'one')
    handle.resume()
    with pytest.raises(StateConflict, match='pause'):
        archive(service, handle)
    assert instruction_state(service.store, handle.id)['active_message_count'] == 1


def test_repeated_review_keeps_lineage_and_freezes_workspace_text(researcher):
    service, handle, project = researcher
    applied(service, handle, 'old constraint', 'one')
    (project / 'constraints.txt').write_text('Host-reviewed initial constraints.')
    first = archive_instructions(service.store, handle.id, workspace_file='constraints.txt',
        rationale='Reviewed into the project file.',
        expected_fingerprint=instruction_state(service.store, handle.id)['fingerprint'])
    (project / 'constraints.txt').write_text('Unreviewed changed text')
    assert cycle_instructions(service.store, handle.id, [], revision_id=first['id']) == 'Host-reviewed initial constraints.'
    applied(service, handle, 'additional constraint', 'two')
    second = archive(service, handle)
    assert second['parent_revision_id'] == first['id']
    assert second['source_message_ids'] == ['two']
    assert first['source_message_ids'] == ['one']
    assert instruction_state(service.store, handle.id)['active_message_count'] == 0
    with service.store.transaction() as db, pytest.raises(StateConflict, match='immutable'):
        existing = service.store.get('instruction_revision', second['id'], db)
        existing['replacement'] = 'tampered'
        service.store.put('instruction_revision', existing, db)


def test_archive_rejects_symlinks_and_other_agent_revision(researcher, tmp_path):
    service, handle, project = researcher
    applied(service, handle, 'original', 'one')
    outside = tmp_path / 'outside.txt'; outside.write_text('outside')
    (project / 'linked.txt').symlink_to(outside)
    with pytest.raises(ValueError, match='symlink'):
        archive_instructions(service.store, handle.id, workspace_file='linked.txt', rationale='review',
            expected_fingerprint=instruction_state(service.store, handle.id)['fingerprint'])
    revision = archive(service, handle)
    with pytest.raises(StateConflict, match='missing'):
        cycle_instructions(service.store, 'another-agent', [], revision_id=revision['id'])


def test_archive_rejects_invalid_replacement_and_does_not_change_budget(researcher, monkeypatch):
    service, handle, _ = researcher
    applied(service, handle, 'original', 'one')
    snapshot = instruction_state(service.store, handle.id)
    for value in ('', ' ' * 4, 'z' * 65537):
        with pytest.raises(ValueError):
            archive_instructions(service.store, handle.id, replacement=value, rationale='host review',
                                 expected_fingerprint=snapshot['fingerprint'])
    before = handle.status()
    archive(service, handle)
    after = handle.status()
    for key in ('contract','security','active_version_id','backend_calls','daily_cycles','cycles'):
        assert before[key] == after[key]


class PrefixBackend:
    async def execute(self, request):
        assert not ('A' * 1000 in request.prompt and 'B' * 1000 in request.prompt)
        Path(request.workspace, 'evidence.txt').write_text('bounded pending prefix')
        return BackendResult(json.dumps(dict(summary='prefix processed', hypothesis='bounded context',
                          evidence=['evidence.txt'], next_action='wait')))


def test_large_pending_inbox_is_claimed_in_prefixes_and_can_be_archived(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    service = AgentService(tmp_path / 'state', backend_factories={'fixture': PrefixBackend})
    h = service.submit('large pending input', project, backend='fixture')
    first = h.send('A' * 65536, idempotency_key='first')
    second = h.send('B' * 65536, idempotency_key='second')
    cycle = service._claim(h.id, 'fixture')
    assert cycle['messages'] == [first['id']]
    service._cycle(cycle, CancellationToken())
    assert h.receipt(first['id'])['status'] == 'applied'
    assert h.receipt(second['id'])['status'] == 'persisted'
    assert service._claim(h.id, 'fixture') is None
    assert h.status()['status'] == 'blocked' and h.status()['backend_calls'] == 1
    assert h.status()['cycles'] == 1
    with service.store.transaction() as db:
        owner = service.store.get('agent', h.id, db)
        owner.update(desired='paused', status='paused')
        service.store.put('agent', owner, db)
    revision = archive_instructions(service.store, h.id, replacement='Reviewed first requirement.',
        rationale='Host removed repetition.', expected_fingerprint=h.instruction_state()['fingerprint'])
    restarted = AgentService(service.root, backend_factories={'fixture': PrefixBackend})
    h.resume()
    cycle = restarted._claim(h.id, 'fixture')
    assert cycle['messages'] == [second['id']]
    restarted._cycle(cycle, CancellationToken())
    assert h.receipt(second['id'])['status'] == 'applied'
    assert h.status()['backend_calls'] == 2 and h.status()['cycles'] == 2
    assert h.experiments()[0]['instruction_revision_id'] == revision['id']
