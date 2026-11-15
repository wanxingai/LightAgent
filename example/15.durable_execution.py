"""Offline ordinary durable task; no model, key, CLI, research or UI required."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from LightAgent import (BackendCapabilities, BackendProbe, BackendResult,
                        ExecutionHandle, ExecutionService, SecurityContext)


class LocalFixture:
    def probe(self):
        return BackendProbe("offline-fixture", "1", BackendCapabilities())

    async def execute(self, request):
        request.emit("progress", completed=1)
        return BackendResult("Local validation completed.", usage={
            "total_tokens": 0, "model_calls": 0, "tool_calls": 0, "cost": 0,
        })


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        workspace = root / "workspace"
        workspace.mkdir()
        service = ExecutionService(root / "state", backend_factories={"local": LocalFixture})
        handle = service.submit("Check the offline execution contract.", workspace,
            backend="local", security_context=SecurityContext(
                user_id="alice", tenant_id="demo", project_id="offline", network_allowed=True),
            budget={"backend_calls": 1}, idempotency_key="offline-example")
        handle.pause()
        handle.send("Keep the run bounded.", idempotency_key="followup")
        handle.resume()
        service.serve_forever(max_ticks=1)
        restored = ExecutionHandle.connect(handle.id, root=service.root)
        assert restored.status()["status"] == "completed"
        print(json.dumps({"status": restored.status()["status"],
            "backend_calls": restored.budget()["used"]["backend_calls"],
            "events": len(restored.events())}, indent=2))


if __name__ == "__main__":
    main()
