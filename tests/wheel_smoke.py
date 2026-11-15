"""Install a built wheel into a temporary target and import outside the checkout."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    wheel=Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='lightagent-wheel-') as directory:
        target=Path(directory)/'installed'
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(target),str(wheel)],check=True)
        subprocess.run([sys.executable,'-c',
            "import sys,importlib.util; import LightAgent; from LightAgent import ExecutionService, ExecutionHandle, InteractionRequests, WakeupScheduler, CodexAppServerBackend, MCPToolBridge, HistoryBundle, JobConflict; "
            "assert 'installed' in LightAgent.__file__; "
            "assert not any(name.startswith('LightResearch') for name in sys.modules); "
            "assert importlib.util.find_spec('LightAgent.persistent.panel') is None; "
            "assert LightAgent.LightAgent(backend='codex').backend.capabilities.resume; print(LightAgent.__version__)"],
            cwd=directory,env={**os.environ,'PYTHONPATH':str(target),'PATH':''},check=True)
        subprocess.run([sys.executable, '-c', '''
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from LightAgent import AgentRuntime, SqliteSessionStore, HistoryBundle
class Child:
    async def arun(self, query):
        return 'wheel result'
async def run(root):
    source = root / 'source'
    source.mkdir(mode=0o700)
    runtime = AgentRuntime(session_store=SqliteSessionStore(source / 'sessions.sqlite3'))
    runtime.open_session('wheel')
    child = runtime.subagents.register(Child(), persistent=True)
    assert await runtime.subagents.run(child.agent_id, 'verify', lease_seconds=10) == 'wheel result'
    job = runtime.jobs.list()[0]
    assert runtime.jobs.status(job.job_id)['status'] == 'completed'
    HistoryBundle.capture(source, root / 'bundle', quiescent=True)
    restored = HistoryBundle.restore(root / 'bundle', root / 'restored')
    reopened = AgentRuntime(session_store=SqliteSessionStore(restored / 'sessions.sqlite3'))
    reopened.open_session('wheel')
    assert reopened.subagents.tree()[0]['job_id'] == job.job_id
    assert reopened.subagents.tree()[0]['bound'] is False
with TemporaryDirectory() as directory:
    asyncio.run(run(Path(directory)))
print('Installed Job/Subagent/history contract: PASS')
'''], cwd=directory, env={**os.environ, 'PYTHONPATH':str(target), 'PATH':''}, check=True)


if __name__=='__main__':main()
