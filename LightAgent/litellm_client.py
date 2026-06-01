"""LiteLLM client wrapper with the same interface as OpenAI's client.

Provides ``client.chat.completions.create(**params)`` so all existing
call sites in core.py work unchanged while routing through litellm SDK.
"""

from types import SimpleNamespace

import litellm


class _LiteLLMCompletions:
    def __init__(self, api_key=None, base_url=None):
        self._api_key = api_key
        self._base_url = base_url

    def create(self, **params):
        if self._api_key:
            params['api_key'] = self._api_key
        if self._base_url:
            params['api_base'] = self._base_url
        params['drop_params'] = True
        return litellm.completion(**params)


class LiteLLMClient:
    """Drop-in replacement for ``openai.OpenAI`` that routes through LiteLLM SDK."""

    def __init__(self, api_key=None, base_url=None):
        self.chat = SimpleNamespace(
            completions=_LiteLLMCompletions(api_key=api_key, base_url=base_url)
        )
