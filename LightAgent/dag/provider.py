"""Capability Provider adapter for LightDAG control and inspection."""

from __future__ import annotations

from typing import Any

from ..capabilities import BaseCapabilityProvider, CapabilityRisk, CapabilitySpec


class LightDAGProvider(BaseCapabilityProvider):
    name = "lightdag"
    version = "1"

    def __init__(self, dag: Any):
        self.dag = dag
        super().__init__([
            CapabilitySpec("workflow.dag.get_run", read=True),
            CapabilitySpec("workflow.dag.list_tasks", read=True),
            CapabilitySpec("workflow.dag.events", read=True),
            CapabilitySpec(
                "workflow.dag.pause",
                write=True,
                persistent=True,
                risk=CapabilityRisk.SENSITIVE,
                requires_approval=True,
            ),
            CapabilitySpec(
                "workflow.dag.cancel",
                write=True,
                persistent=True,
                risk=CapabilityRisk.DESTRUCTIVE,
                requires_approval=True,
            ),
        ])

    async def invoke(self, capability: str, **arguments: Any) -> Any:
        run_id = arguments["run_id"]
        if capability == "workflow.dag.get_run":
            value = self.dag.get_run(run_id)
            return value.to_dict() if value else None
        if capability == "workflow.dag.list_tasks":
            return [task.to_dict() for task in self.dag.list_tasks(run_id)]
        if capability == "workflow.dag.events":
            return [
                event.to_dict()
                for event in self.dag.events(
                    run_id,
                    after=int(arguments.get("after", 0)),
                    limit=int(arguments.get("limit", 100)),
                )
            ]
        if capability == "workflow.dag.pause":
            return self.dag.pause(run_id, arguments.get("reason")).to_dict()
        if capability == "workflow.dag.cancel":
            return self.dag.cancel(run_id, arguments.get("reason")).to_dict()
        raise LookupError(capability)


__all__ = ["LightDAGProvider"]
