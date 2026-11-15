import builtins
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from LightAgent import LightAgent
from LightAgent.builtin_tools.nos import upload_file_to_oss


def test_lightagent_import_does_not_require_boto3():
    script = """
import builtins

real_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "boto3" or name.startswith("botocore"):
        raise ImportError(f"blocked optional dependency: {name}")
    return real_import(name, *args, **kwargs)

builtins.__import__ = guarded_import
import LightAgent
assert LightAgent.LightAgent is not None
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_upload_file_to_oss_reports_missing_optional_boto3(monkeypatch, tmp_path):
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "boto3" or name.startswith("botocore"):
            raise ImportError(f"blocked optional dependency: {name}")
        return real_import(name, *args, **kwargs)

    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = upload_file_to_oss(str(sample))

    assert "缺少可选依赖库" in result
    assert "LightAgent[oss]" in result


def test_plain_agent_runs_without_optional_integrations():
    script = """
import importlib.abc
import sys
from types import SimpleNamespace

class BlockIntegrations(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'mem0', 'langfuse', 'mcp'}:
            raise AssertionError(f'unexpected optional import: {fullname}')

sys.meta_path.insert(0, BlockIntegrations())
from LightAgent import LightAgent

class MemoryFixture:
    def retrieve(self, query, user_id):
        return {'results': []}

    def store(self, data, user_id):
        pass

agent = LightAgent(model='fixture', api_key='fixture', memory=MemoryFixture(),
                   auto_discover_skills=False)
message = SimpleNamespace(content='local', tool_calls=None)
agent.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
    create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=message)]))))
assert agent.run('hello', user_id='optional-test') == 'local'

def stream(**kwargs):
    assert kwargs['stream']
    delta = SimpleNamespace(content='streamed', tool_calls=None, role='assistant')
    return iter([SimpleNamespace(choices=[SimpleNamespace(delta=delta, finish_reason='stop')])])

agent.client.chat.completions.create = stream
chunks = agent.run('hello', stream=True, user_id='optional-test')
assert ''.join(chunk.choices[0].delta.content or '' for chunk in chunks) == 'streamed'
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_mcp_legacy_imports_and_install_hint_without_sdk():
    script = """
import asyncio
import importlib.abc
import sys

class BlockMCP(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'mcp':
            raise ModuleNotFoundError('no MCP SDK', name=fullname)

sys.meta_path.insert(0, BlockMCP())
from LightAgent import LightAgent, MCPClientManager, MCPToolBridge, SecurityContext, ToolRegistry
from LightAgent.core import MCPClientManager as core_manager
from LightAgent.mcp_client_manager import MCPClientManager as module_manager
assert MCPClientManager is core_manager is module_manager
agent = LightAgent(model='fixture', api_key='fixture', auto_discover_skills=False)
asyncio.run(agent.setup_mcp())
assert agent.mcp_client is None
config = {'mcpServers': {'local': {'command': 'unused', 'args': []}}}
bridge = MCPToolBridge('fixture', version='1')
for call in (lambda: MCPClientManager(config, ToolRegistry()),
             lambda: asyncio.run(agent.setup_mcp(mcp_setting=config)),
             lambda: asyncio.run(bridge.serve_stdio(SecurityContext()))):
    try:
        call()
    except ImportError as error:
        assert 'LightAgent[mcp]' in str(error)
        assert error.__cause__.name == 'mcp'
    else:
        raise AssertionError('MCP operation did not reject a missing SDK')
assert agent.mcp_client is None
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_mcp_preserves_installed_sdk_dependency_error():
    script = """
import importlib.abc
import sys

class BrokenMCP(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'mcp':
            raise ModuleNotFoundError('broken SDK dependency', name='sdk_dependency')

sys.meta_path.insert(0, BrokenMCP())
import LightAgent
try:
    from LightAgent import MCPClientManager
except ModuleNotFoundError as error:
    assert error.name == 'sdk_dependency'
    assert 'LightAgent[mcp]' not in str(error)
else:
    raise AssertionError('the SDK dependency error was hidden')
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def trace_options():
    return {"TraceToolConfig": {
        "langfuse_public_key": "public-fixture",
        "langfuse_secret_key": "secret-fixture",
        "langfuse_enabled": False,
        "langfuse_host": "http://127.0.0.1:9",
    }}


@pytest.mark.parametrize("missing", ["langfuse", "openai.resources.beta.chat"])
def test_langfuse_missing_extra_error_does_not_mask_broken_dependency(monkeypatch, missing):
    real_import = builtins.__import__
    error = ModuleNotFoundError(f"missing: {missing}", name=missing)

    def guarded_import(name, *args, **kwargs):
        if name == "langfuse.openai":
            raise error
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    if missing == "langfuse":
        with pytest.raises(ImportError, match=r"LightAgent\[langfuse\]") as exc:
            LightAgent(model="fixture", api_key="fixture", tracetools=trace_options(), auto_discover_skills=False)
        assert exc.value.__cause__ is error
    else:
        with pytest.raises(ModuleNotFoundError) as exc:
            LightAgent(model="fixture", api_key="fixture", tracetools=trace_options(), auto_discover_skills=False)
        assert exc.value is error


def test_legacy_langfuse_import_and_trace_config(monkeypatch):
    calls = []

    def complete(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(content="observed", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))
    package = ModuleType("langfuse")
    package.__path__ = []
    module = ModuleType("langfuse.openai")
    module.openai = client
    monkeypatch.setitem(sys.modules, "langfuse", package)
    monkeypatch.setitem(sys.modules, "langfuse.openai", module)
    config = trace_options()
    agent = LightAgent(model="fixture", api_key="fixture", tracetools=config, auto_discover_skills=False)
    assert agent.client is client
    assert all(getattr(client, name) == value for name, value in config["TraceToolConfig"].items())
    assert agent.run("hello") == "observed"
    assert calls[0]["session_id"]
