import time
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio

async def fetch_data_with_browser(task_description: str, api_key: str) -> str:
    """
    Fetch data using a browser for tasks that cannot be directly accessed by other tools.
    
    :param task_description: Description of the task to be performed by the browser.
    :param api_key: API key for accessing the ChatOpenAI service.
    :return: Result of the task execution.
    """
    time_start = time.time()
    llm = ChatOpenAI(
        base_url='http://oneapi.wanxingai.com/v1',
        model='deepseek-r1-distill-qwen-32b',
        api_key=api_key
    )
    agent = Agent(
        task=task_description,
        llm=llm,
        use_vision=False
    )
    result = await agent.run()
    time_end = time.time()
    print("\n======== Task Execution Time ========")
    print("Time taken:", int(time_end - time_start), "seconds")
    print("\n======== Task Result ========")
    print(result.final_result())
    return result.final_result()

# Define tool information within the function
fetch_data_with_browser.tool_info = {
    "tool_name": "browser_data_fetcher",
    "tool_title": "Browser Data Fetcher",
    "tool_description": "Fetch data using a browser for tasks that cannot be directly accessed by other tools.",
    "tool_params": [
        {"name": "task_description", "description": "Description of the task to be performed by the browser.", "type": "string", "required": True},
        {"name": "api_key", "description": "API key for accessing the ChatOpenAI service.", "type": "string", "required": True}
    ]
}