import os
import time

from browser_use import Agent
from LightAgent import LightAgent
from langchain_openai import ChatOpenAI


os.environ["OPENAI_API_KEY"] = "<your_api_key>"
os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
os.environ["BROWSER_USE_MODEL"] = "gpt-4.1-mini"


def ensure_browser_use_provider(llm, provider: str = "openai"):
    """browser-use 0.11+ expects llm.provider; older ChatOpenAI objects may not expose it."""
    if hasattr(llm, "provider"):
        return llm
    try:
        setattr(llm, "provider", provider)
    except Exception:
        object.__setattr__(llm, "provider", provider)
    return llm


async def fetch_data_with_browser(task_description: str) -> str:
    """
    Fetch data using a browser for tasks that cannot be directly accessed by other tools.
    """
    time_start = time.time()
    llm = ensure_browser_use_provider(ChatOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("BROWSER_USE_MODEL", "gpt-4.1-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
    ))
    browser_agent = Agent(
        task=task_description,
        llm=llm,
        use_vision=False,
    )
    result = await browser_agent.run()
    time_end = time.time()
    print("\n======== Task Execution Time ========")
    print("Time taken:", int(time_end - time_start), "seconds")
    print("\n======== Task Result ========")
    print(result.final_result())
    return result.final_result()


# Define tool information within the function
fetch_data_with_browser.tool_info = {
    "tool_name": "browser_data_fetcher",
    "tool_title": "使用浏览器",
    "tool_description": "对于无法通过其他工具直接访问的任务，使用浏览器获取文本数据或者文件的URL地址。",
    "tool_params": [
        {"name": "task_description", "description": "浏览器要执行的任务的描述。", "type": "string", "required": True}
    ]
}

tools = [fetch_data_with_browser]

# Initialize Agent
agent = LightAgent(model="gpt-4.1-mini", api_key="<your_api_key>",
                   base_url="https://api.openai.com/v1",
                   tools=tools,
                   debug=True,
                   log_level="debug",
                   log_file="example.log")

# Run Agent
response = agent.run("Please search the weather in Shanghai.", stream=True)
full_response = ''
for chunk in response:
    print(chunk, end="\n", flush=True)
