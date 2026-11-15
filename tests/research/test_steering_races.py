from LightResearch import enable_legacy_api
enable_legacy_api()
"""Late steering acknowledgements cannot resurrect terminal receipts."""
from LightAgent import AgentService
from LightResearch.steering import _deliver_bound
from LightAgent.persistent.store import ResearchStore as LegacyResearchStore
import pytest


def test_legacy_steering_module_delegates_after_registration():
    from LightAgent.persistent import steering as legacy
    from LightResearch import steering

    assert legacy.dispatch is steering.dispatch
    assert legacy._deliver_bound is steering._deliver_bound


def prepare(tmp_path):
    workspace=tmp_path/'project';workspace.mkdir()
    service=AgentService(tmp_path/'state')
    handle=service.submit('test',workspace)
    cycle=service._claim(handle.id,'watch')
    with service.store.transaction() as db:
        service.store.put('attempt',dict(id='attempt',agent=handle.id,cycle_id=cycle['id'],
                                        status='running',turn_id='turn'),db)
    message=handle.steer('extra constraint',attempt_id='attempt',expected_turn_id='turn')
    return service,handle,cycle,message


def test_late_ack_preserves_failed_cycle_receipt(tmp_path):
    s,h,c,m=prepare(tmp_path)
    class Backend:
        def steer(self,*args,**kwargs):
            with s.store.transaction() as db:
                cycle=s.store.get('cycle',c['id'],db);cycle['status']='failed';s.store.put('cycle',cycle,db)
                message=s.store.get('message',m['id'],db);message['status']='unapplied';s.store.put('message',message,db)
    _deliver_bound(s,m,dict(epoch=c['epoch'],cycle=c['id'],backend=Backend()))
    assert h.receipt(m['id'])['status']=='unapplied'
    assert h.receipt(m['id'])['steering_ack']=='delivered'


def test_ack_cannot_commit_across_execution_epoch(tmp_path):
    s,h,c,m=prepare(tmp_path)
    class Backend:
        def steer(self,*args,**kwargs):
            with s.store.transaction() as db:
                a=s.store.get('agent',h.id,db);a['epoch']+=1;s.store.put('agent',a,db)
                cycle=s.store.get('cycle',c['id'],db);cycle['status']='completed';s.store.put('cycle',cycle,db)
    _deliver_bound(s,m,dict(epoch=c['epoch'],cycle=c['id'],backend=Backend()))
    assert h.receipt(m['id'])['status']=='uncertain'


def test_repeated_dispatch_and_stale_turn_do_not_reapply(tmp_path):
    s,h,c,m=prepare(tmp_path)
    class Backend:
        calls=0
        def steer(self,*args,**kwargs):self.calls+=1
    backend=Backend();live=dict(epoch=c['epoch'],cycle=c['id'],backend=backend)
    _deliver_bound(s,m,live);_deliver_bound(s,m,live)
    assert backend.calls==1
    stale=h.steer('old turn',attempt_id='attempt',expected_turn_id='previous-turn')
    old_revision=h.status()['goal_revision']
    _deliver_bound(s,stale,live)
    assert backend.calls==1
    assert h.receipt(stale['id'])['status']=='rejected'
    assert h.status()['goal_revision']==old_revision


def test_legacy_store_keeps_exact_turn_validation_and_receipt_format(tmp_path):
    service, handle, _, message = prepare(tmp_path)
    legacy = LegacyResearchStore(service.root)
    with pytest.raises(ValueError, match='exact turn'):
        legacy.enqueue(handle.id, 'missing turn', kind='steer', steering={'attempt_id': 'attempt'})
    repeated = legacy.enqueue(handle.id, message['content'], key=message['id'], kind='steer',
                              steering=message['steering'])
    assert repeated == handle.receipt(message['id'])
