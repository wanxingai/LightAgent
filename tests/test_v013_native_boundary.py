import asyncio

import pytest

from LightAgent import (BackendCapabilities, BackendProbe, BackendRequest, BackendSessionStore,
                        LightAgent, LocalWorkspaceProvider, NativeBackend, SecurityContext, SqliteSessionStore)
from LightAgent.backends import BackendError


@pytest.mark.parametrize("state", ["bindings", "history"])
def test_native_control_state_is_never_mounted_into_worker_workspace(tmp_path, state):
    work = tmp_path / "work"
    work.mkdir()
    history = SqliteSessionStore((work if state == "history" else tmp_path) / "history.sqlite3")
    def agent():
        return LightAgent(model="fixture", api_key="fixture", auto_discover_skills=False, session_store=history)
    backend = NativeBackend(agent, LocalWorkspaceProvider(allow_host_execution=True),
        session_store=BackendSessionStore((work if state == "bindings" else tmp_path) / "bindings"))
    context = SecurityContext(resources=frozenset({str(work.resolve())}), network_allowed=True)
    with pytest.raises(BackendError, match="outside the worker workspace"):
        asyncio.run(backend.execute(BackendRequest("must not execute", str(work), context)))


def test_native_probe_pins_provider_version_and_configuration():
    class Provider:
        version = "one"
        def probe(self):
            return BackendProbe("host", self.version, BackendCapabilities(isolation="docker", network_control=True))
        def open(self, *args, **kwargs):
            pytest.fail("probe must not open a workspace")
    provider = Provider()
    backend = NativeBackend(lambda: None, provider)
    initial = backend.probe()
    provider.version = "two"
    assert initial.version != backend.probe().version
    assert initial.capabilities.isolation == "docker"
