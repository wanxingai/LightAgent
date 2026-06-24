import builtins
from types import SimpleNamespace

import pytest

from LightAgent.litellm_client import LiteLLMClient


class FakeLiteLLM:
    def __init__(self):
        self.calls = []

    def completion(self, **params):
        self.calls.append(params)
        return SimpleNamespace(choices=[])


def test_litellm_client_forwards_openai_style_create_params():
    fake_litellm = FakeLiteLLM()
    client = LiteLLMClient(
        api_key="provider-key",
        base_url="https://provider.example/v1",
        litellm_module=fake_litellm,
    )

    response = client.chat.completions.create(
        model="anthropic/claude-sonnet",
        messages=[{"role": "user", "content": "ping"}],
        stream=False,
    )

    assert response.choices == []
    assert fake_litellm.calls == [
        {
            "model": "anthropic/claude-sonnet",
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
            "api_key": "provider-key",
            "api_base": "https://provider.example/v1",
            "drop_params": True,
        }
    ]


def test_litellm_client_preserves_explicit_drop_params():
    fake_litellm = FakeLiteLLM()
    client = LiteLLMClient(litellm_module=fake_litellm)

    client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "ping"}],
        drop_params=False,
    )

    assert fake_litellm.calls == [
        {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}],
            "drop_params": False,
        }
    ]


def test_litellm_client_has_clear_optional_dependency_error(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "litellm":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match=r"LightAgent\[litellm\]"):
        LiteLLMClient()
