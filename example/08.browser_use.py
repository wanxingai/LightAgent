import os
import time

from LightAgent import LightAgent
from browser_use import Agent
from langchain_openai import ChatOpenAI


os.environ["OPENAI_API_KEY"] = "<your_api_key>"
os.environ["OPENAI_BASE_URL"] = "http://<your_base_url>/v1"


async def fetch_data_with_browser(task_description: str) -> str:
    """
    Fetch data using a browser for tasks that cannot be directly accessed by other tools.
    """
    time_start = time.time()
    llm = ChatOpenAI(
        base_url='http://api.openai.com/v1',
        model='gpt-4.1-mini',
        api_key="sk-**********************************"
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
    "tool_title": "使用浏览器",
    "tool_description": "对于无法通过其他工具直接访问的任务，使用浏览器获取文本数据或者文件的URL地址。",
    "tool_params": [
        {"name": "task_description", "description": "浏览器要执行的任务的描述。", "type": "string", "required": True}
    ]
}

tools = [fetch_data_with_browser]

# Initialize Agent
agent = LightAgent(model="gpt-4.1-mini", api_key="<your_api_key>",
                   base_url="http://<your_base_url>/v1",
                   tools=tools,
                   debug=True,
                   log_level="debug",
                   log_file="example.log")

# Run Agent
response = agent.run("Please search the weather in Shanghai.", stream=True)
full_response = ''
for chunk in response:
    print(chunk, end="\n", flush=True)
