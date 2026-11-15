"""Independent-process half of the real Docker child-session acceptance test."""
import asyncio
import json
import os
from pathlib import Path
import runpy
import sys

from LightAgent import AgentRuntime, BackendRequest, SqliteSessionStore


async def main(root, agent_id):
    namespace = runpy.run_path(str(Path(__file__).parents[1] / "integration" / "test_worker_docker_v013.py"))
    if os.getenv("LIGHTWORKER_SOURCE"):
        sys.path.insert(0, str(Path(os.environ["LIGHTWORKER_SOURCE"]) / "src"))
    from lightworker.lightagent_execution import DockerWorkspaceProvider
    clients = []
    work = root / "work"
    class Child:
        async def arun(self, query):
            backend = namespace["factory"](DockerWorkspaceProvider, root, "python check.py", clients)
            return (await backend.execute(BackendRequest(query, str(work), namespace["context"](work),
                session_id="continuous-child", timeout=60))).content
    cold = AgentRuntime(session_store=SqliteSessionStore(root / "parent.sqlite3"))
    cold.open_session("parent")
    assert not cold.subagents.tree()[0]["bound"]
    cold.subagents.bind(agent_id, Child())
    result = await cold.subagents.run(agent_id, "continue", lease_seconds=120)
    print(json.dumps(dict(result=result, pid=os.getpid(), jobs=len(cold.jobs.list()),
                         restored_history="first private question" in str(clients[-1].calls[0]["messages"]))))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]), sys.argv[2]))
