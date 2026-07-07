import os

from LightAgent import LightAgent


api_key = os.environ.get("ATLASCLOUD_API_KEY")
if not api_key:
    raise RuntimeError("Set ATLASCLOUD_API_KEY before running this example.")


agent = LightAgent(
    model=os.environ.get("ATLASCLOUD_MODEL", "deepseek-ai/deepseek-v4-pro"),
    api_key=api_key,
    base_url=os.environ.get("ATLASCLOUD_BASE_URL", "https://api.atlascloud.ai/v1"),
    role="You are a concise assistant for LightAgent integration examples.",
)


response = agent.run("Explain how LightAgent connects to OpenAI-compatible providers.")
print(response)
