"""离线示例：Subagent 使用 Job 状态，冷重连后由宿主重新绑定实例。"""
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from LightAgent import AgentRuntime, HistoryBundle, SqliteSessionStore


class LocalChild:
    name = "本地子代理"

    async def arun(self, query):
        return "已完成：" + query


async def run(root):
    source = root / "source"
    source.mkdir(mode=0o700)
    store = SqliteSessionStore(source / "sessions.sqlite3")
    runtime = AgentRuntime(session_store=store)
    runtime.open_session("demo")
    child = runtime.subagents.register(LocalChild(), persistent=True)
    result = await runtime.subagents.run(child.agent_id, "检查本地数据", idempotency_key="check-once", lease_seconds=60)
    job = runtime.jobs.list()[0]
    assert runtime.subagents.tree()[0]["job_id"] == job.job_id
    print(json.dumps({"结果": result, "Job": runtime.jobs.status(job.job_id)}, ensure_ascii=False, indent=2))

    # 所有写入者已结束。只备份到新目录，不覆盖原始数据。
    HistoryBundle.capture(source, root / "backup", quiescent=True)
    restored_root = HistoryBundle.restore(root / "backup", root / "restored")
    restored = AgentRuntime(session_store=SqliteSessionStore(restored_root / "sessions.sqlite3"))
    restored.open_session("demo")
    assert restored.subagents.tree()[0]["bound"] is False
    restored.subagents.bind(child.agent_id, LocalChild())
    cached = await restored.subagents.run(child.agent_id, "检查本地数据", idempotency_key="check-once")
    assert cached == result and len(restored.jobs.list()) == 1
    print("冷重连成功；相同幂等键读取旧结果，没有重新执行。")


if __name__ == "__main__":
    with TemporaryDirectory() as directory:
        asyncio.run(run(Path(directory)))
