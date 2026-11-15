"""Real CLI smoke test; explicitly opt in because it consumes account usage."""
import asyncio
import os
from uuid import uuid4

import pytest

from LightAgent import BackendRequest, BackendSessionStore, CancellationToken, CodexBackend, SecurityContext


pytestmark = pytest.mark.skipif(
    os.environ.get("LIGHTAGENT_CODEX_INTEGRATION") != "1",
    reason="set LIGHTAGENT_CODEX_INTEGRATION=1 with a logged-in local Codex CLI",
)


def test_real_codex_workspace_resume_cancel_and_recover(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = "lightagent-p0-" + uuid4().hex
    (workspace / "fixture.txt").write_text(marker + "\n")
    store = BackendSessionStore(tmp_path / "control")
    context = SecurityContext(user_id="p0-integration", project_id="p0-fixture",
                              resources=frozenset({str(workspace.resolve())}),
                              sandbox_required=True, network_allowed=True)

    def run(prompt, **kwargs):
        # A new backend instance for each call exercises persisted bindings.
        return asyncio.run(CodexBackend(session_store=store).execute(BackendRequest(
            prompt, str(workspace), context, timeout=120, **kwargs)))

    result = run("Read fixture.txt. Copy its exact contents to result.txt in this workspace. "
                 "Do not access network or other directories. Reply with only the text you copied.")
    assert result.status == "completed", result.error
    assert marker in result.content
    assert (workspace / "result.txt").read_text().strip() == marker
    session_id = result.session_id

    token = CancellationToken()
    def cancel_after_start(event):
        if event.type == "backend.event" and event.data["event"]["type"] == "thread.started":
            token.cancel("integration interruption")

    cancelled = run("Wait for further instructions; do not modify any files.",
                    session_id=session_id, cancellation_token=token, on_event=cancel_after_start)
    assert cancelled.status == "cancelled", cancelled.error
    assert cancelled.session_id == session_id

    resumed = run("Without using tools, repeat the exact contents of fixture.txt from our earlier conversation. "
                  "Reply with only that text.", session_id=session_id)
    assert resumed.status == "completed", resumed.error
    assert marker in resumed.content
    assert resumed.session_id == session_id


@pytest.mark.requires_lightresearch
def test_real_codex_persistent_research_inbox_chat_and_restart(tmp_path):
    """Small real research scenario; no market data, trading, or long soak."""
    import threading
    import time
    from LightResearch import enable_legacy_api

    enable_legacy_api()
    from LightAgent import AgentService, ResearchContract
    workspace=tmp_path/'research-input';workspace.mkdir()
    (workspace/'README.md').write_text('A tiny reproducibility fixture. data.txt contains 1,2,3. Read it locally. Do not access network or other projects.')
    (workspace/'data.txt').write_text('1\n2\n3\n')
    service=AgentService(tmp_path/'research-control')
    handle=service.submit('Read README.md and data.txt. Compute their arithmetic mean (2). '
                          'Write evidence.txt with the calculation. Return the required research report JSON. '
                          'Set next_action to wait; do not propose versions or decompose this tiny task.',
                          workspace,contract=ResearchContract(task_timeout=120))
    message=handle.send('Include the number of data rows in the evidence.',idempotency_key='real-update')
    def wait(predicate,timeout=180):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if predicate():return
            if handle.status()['status']=='blocked':
                pytest.fail('research blocked: '+str(handle.records('cycle')))
            time.sleep(.2)
        pytest.fail('real research timed out')
    thread=threading.Thread(target=service.serve_forever);thread.start()
    try:
        wait(handle.experiments)
        assert handle.receipt(message['id'])['status']=='applied'
        assert handle.artifacts()
        for artifact in handle.artifacts():handle.read_artifact(artifact['blob'])
        answer=handle.open_chat().run('What did the completed experiment publish? Answer briefly without modifying files.',timeout=150)
        assert answer
        handle.pause();wait(lambda:handle.status()['status']=='paused')
    finally:
        service.stop();thread.join(15)
        assert not thread.is_alive()
    restarted=AgentService(service.root)
    second=threading.Thread(target=restarted.serve_forever);second.start()
    try:
        update=handle.send('Repeat the local mean calculation as a new verified experiment.',idempotency_key='real-restart')
        handle.resume()
        wait(lambda:handle.receipt(update['id'])['status']=='applied')
        assert len(handle.experiments())==2
        assert handle.status()['backend_calls']==2
    finally:
        restarted.stop();second.join(15)
        assert not second.is_alive()
