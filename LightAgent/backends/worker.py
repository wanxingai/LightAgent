"""Adapt bounded backends to the existing verification-gated DAG worker."""

from .base import BackendError, BackendRequest
from ..dag.worker import DAGWorkerProtocolError, LightAgentWorkerAdapter, normalize_task_outcome
import json


class BackendWorkerAdapter:
    def __init__(self, backend, workspace, *, timeout=1800):
        self.backend = backend
        # Callable allows the host to provision an isolated workspace per attempt.
        self.workspace = workspace
        self.timeout = timeout

    async def execute(self, context):
        workspace = self.workspace(context) if callable(self.workspace) else self.workspace
        result = await self.backend.execute(BackendRequest(
            prompt=LightAgentWorkerAdapter._default_prompt(context),
            workspace=str(workspace), security_context=context.security_context,
            attempt_id=context.attempt.attempt_id, timeout=self.timeout,
            cancellation_token=context.cancellation_token,
        ))
        if result.status != "completed" or result.error:
            raise BackendError(result.error or f"backend ended as {result.status}")
        try:
            return normalize_task_outcome(json.loads(result.content), context)
        except (ValueError, TypeError, DAGWorkerProtocolError) as exc:
            raise BackendError("backend did not return a valid JSON TaskOutcome") from exc
