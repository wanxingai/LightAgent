"""LiteLLM client wrapper with the same interface as OpenAI's client.

Provides ``client.chat.completions.create(**params)`` so all existing
call sites in core.py work unchanged while routing through litellm SDK.
"""

from types import SimpleNamespace


class _LiteLLMCompletions:
    def __init__(self, api_key=None, base_url=None, litellm_module=None):
        self._api_key = api_key
        self._base_url = base_url
        if litellm_module is None:
            try:
                import litellm as litellm_module
            except ImportError as exc:
                raise ImportError(
                    "LiteLLM provider requires the optional `litellm` dependency. "
                    "Install it with `pip install LightAgent[litellm]`."
                ) from exc
        self._litellm = litellm_module

    def create(self, **params):
        if self._api_key:
            params['api_key'] = self._api_key
        if self._base_url:
            params['api_base'] = self._base_url
        params['drop_params'] = True
        return self._litellm.completion(**params)


class LiteLLMClient:
    """Drop-in replacement for ``openai.OpenAI`` that routes through LiteLLM SDK."""

    def __init__(self, api_key=None, base_url=None, litellm_module=None):
        self.chat = SimpleNamespace(
            completions=_LiteLLMCompletions(
                api_key=api_key,
                base_url=base_url,
                litellm_module=litellm_module,
            )
        )
