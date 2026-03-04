[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/wxai-space-lightagent-badge.png)](https://mseep.ai/app/wxai-space-lightagent)


![LightAgent Banner](docs/images/lightagent-banner.jpg)
<div align="center">
  <p>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://github.com/wxai-space/LightAgent/releases"><img src="https://img.shields.io/github/release/wxai-space/LightAgent.svg" alt="GitHub release"></a>
    <a href="https://github.com/wxai-space/LightAgent/issues"><img src="https://img.shields.io/github/issues/wxai-space/LightAgent.svg" alt="GitHub issues"></a>
    <a href="https://github.com/wxai-space/LightAgent/stargazers"><img src="https://img.shields.io/github/stars/wxai-space/LightAgent.svg" alt="GitHub stars"></a>
    <a href="https://github.com/wxai-space/LightAgent/network"><img src="https://img.shields.io/github/forks/wxai-space/LightAgent.svg" alt="GitHub forks"></a>
    <a href="https://github.com/wxai-space/LightAgent/graphs/contributors"><img src="https://img.shields.io/github/contributors/wxai-space/LightAgent.svg" alt="GitHub contributors"></a>
    <a href="https://sufe-aiflm-lab.github.io/LightAgent/"><img src="https://img.shields.io/badge/docs-latest-brightgreen.svg" alt="Docs"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/v/lightagent.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/dm/lightagent.svg" alt="Downloads"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/pyversions/lightagent.svg" alt="Python Version"></a>
    <a href="https://arxiv.org/abs/2509.09292"><img src="https://img.shields.io/badge/arXiv-Paper-B31B1B?logo=arxiv&logoColor=white" alt="Code Style"></a>
  </p>
</div>
<div align="center">
  <p>
    English | 
    <a href="README.zh-CN.md">简体中文</a> | 
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
<div align="center">
  <h1>LightAgent🚀 (Production-level open-source Agentic AI development framework)</h1>
</div>

**LightAgent** is an extremely lightweight active Agentic Framework with memory (`mem0`), tools (`Tools`), and a tree of thought (`ToT`), and it is completely open source. It supports simpler multi-agent collaboration than OpenAI Swarm, allowing you to build self-learning agents in just one step, and supports connecting to the MCP protocol via stdio and sse. The underlying models support OpenAI, Zhiyuan ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen large models, and more. At the same time, LightAgent supports OpenAI streaming format API service output, seamlessly integrating with major mainstream Chat frameworks. 🌟

---

![lightswarm_demo_en.png](docs%2Fimages%2Flightswarm_demo_en.png)

## ✨ Features

- **Lightweight and Efficient** 🚀: Minimalist design, quick deployment, suitable for various application scenarios. (No LangChain, No LlamaIndex) 100% Python implementation, no additional dependencies, core code is only 1000 lines, fully open source. 
- **Memory Support** 🧠: Supports custom long-term memory for each user, natively supporting the `mem0` memory module, automatically managing user personalized memory during conversations, making agents smarter.
- **Autonomous Learning** 📚️: Each agent possesses autonomous learning capabilities, and admins with permissions can manage each agent.
- **Tool Integration** 🛠️: Support for custom tools (`Tools`) and MCP tool integration, flexible expansion to meet diverse needs.  
- **Complex Goals** 🌳: Built-in Tree of Thought (`ToT`) module with reflection, supporting complex task decomposition and multi-step reasoning, enhancing task processing capabilities.  
- **Multi-Agent Collaboration** 🤖: Simpler to implement multi-agent collaboration than Swarm, with built-in LightSwarm for intent recognition and task delegation, enabling smarter handling of user input and delegating tasks to other agents as needed. 
- **Independent Execution** 🤖: Tasks and tool calls are completed autonomously without human intervention.  
- **Multi-Model Support** 🔄: Compatible with OpenAI, Zhipu ChatGLM, Baichuan Large Model, StepFun, DeepSeek, Qwen series large models.  
- **Streaming API** 🌊: Supports OpenAI streaming format API service output, seamlessly integrates with mainstream chat frameworks, enhancing user experience.  
- **Tool Generator** 🚀: Just provide your API documentation to the [Tool Generator], which will automatically create exclusive tools for you, allowing you to quickly build hundreds of personalized custom tools in just 1 hour to improve efficiency and unleash your creative potential.
- **Agent Self-Learning** 🧠️: Each agent has its own scene memory capabilities and the ability to self-learn from user conversations.
- **Adaptive Tool Mechanism** 🛠️: Supports adding an unlimited number of tools, allowing the large model to first select a candidate tool set from thousands of tools, filtering irrelevant tools before submitting context to the large model, significantly reducing token consumption.

## 🧩 Multi-agent troubleshooting (failure map)

If you are using LightSwarm or other multi-agent patterns and start seeing role drift, cross-agent memory issues or confusing logs, you can check the
[Multi-agent failure map](docs/multi_agent_failure_map.md) for a small symptom → mode → debug checklist.  
This page is docs-only and does not change any framework code.

---
## News
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-09-16]** Our paper is now available as a preprint on arXiv: https://arxiv.org/pdf/2509.09292. We invite the research community to read and cite our work.
- **[2025-06-12]** We are pleased to announce the official release of LightAgent v0.4.0! This version upgrade brings architectural improvements, with significant enhancements in performance, stability, and maintainability.
- **[2025-05-05]** LightAgent v0.3.3 Released: Deep [Langfuse](https://langfuse.com/) Logging Integration, Enhanced Context Management and Tool Invocation Stability [View](#8-integrating-langfuse-log-tracking)
- **[2025-04-21]** LightAgent v0.3.2 adds an adaptive Tools mechanism, supports unlimited intelligent tool filtering, reduces Token consumption by 80%, and improves response speed by 52%! [View](#4-tree-of-thought-tot)
- **[2025-04-01]** LightAgent v0.3.0 Support browser interaction [browser_use](https://github.com/browser-use/browser-use) and fully supports the MCP protocol, enabling collaborative work with multiple models and tools to achieve more efficient handling of complex tasks.<a href="mcp_release.md">View MCP release introduction.>></a>
- **[2025-02-19]** LightAgent v0.2.7  supports deepseek-r1 model for tot now.Significantly enhances the multi-tool planning capability for complex tasks.
- **[2025-02-06]** LightAgent version 0.2.5 is released now.
- **[2025-01-20]** LightAgent version 0.2.0 is released now.
- **[2025-01-05]** LightAgent version 0.1.0 is released now.

---

## 🚧 Coming Soon

- **Agent Collaborative Communication** 🛠️: Agents can also share information and transmit messages, achieving complex information communication and task collaboration.
- **Agent Assessment** 📊: Built-in agent assessment tool for conveniently evaluating and optimizing the agents you build, aligning with business scenarios, and continuously improving intelligence levels.  

## Built-in "Thought Flow"
### ToT now supports DeepSeek-R1.
The Thought Flow method effectively addresses challenges in complex scenarios through systematic, structured, and flexible thinking processes. Here are the specific implementation steps:
```text
Problem Definition: Clarify the core problems and objectives.

Information Collection: Systematically gather relevant information and data.

Problem Decomposition: Break down complex problems into multiple subproblems or modules.

Multi-dimensional Analysis: Analyze each subproblem from different angles and levels.

Establish Connections: Identify the relationships and dependencies between subproblems.

Generate Solutions: Propose possible solutions for each subproblem.

Evaluation and Selection: Assess the feasibility and impact of each solution, choosing the best one.

Implementation and Feedback: Implement the selected solution and adjust based on feedback.
```

---
## 🌟 Why Choose LightAgent?

- **Open Source and Free** 💖: Fully open source, community-driven, continuously updated, contributions are welcome!  
- **Easy to Get Started** 🎯: Detailed documentation, rich examples, quick to get started, easy integration into your project.  
- **Community Support** 👥: An active developer community ready to assist and provide answers at any time.  
- **High Performance** ⚡: Optimized design, efficient operation, meeting high concurrency requirements.  

---

## 🛠️ Quick Start

### Install the latest version of LightAgent

```bash
pip install lightagent
```

(Optional installation) Install the Mem0 package via pip:

```bash
pip install mem0ai
```

Alternatively, you can use Mem0 on a hosted platform by clicking [here](https://www.mem0.ai/).

### Hello World Example Code

```python
from LightAgent import LightAgent

# Initialize Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

# Run Agent
response = agent.run("Hello, who are you?")
print(response)
```

### Set Model Self-Perception via System Prompt

```python
from LightAgent import LightAgent

# Initialize Agent
agent = LightAgent(
     role="Please remember that you are LightAgent, a useful assistant that helps users use multiple tools.",  # system role description
     model="gpt-4.1",  # Supported models: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # Replace with your large model provider API Key
     base_url="your_base_url",  # Replace with your large model provider api url
 )
# Run Agent
response = agent.run("Who are you?")
print(response)
```

### Tool Example Code

```python
from LightAgent import LightAgent

# Define Tool
def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"Query result: {city_name} is sunny."
# Define tool information inside the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Initialize Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url", tools=tools)

# Run Agent
response = agent.run("Please check the weather in Shanghai.")
print(response)
```
Supports an unlimited number of customizable tools.

Multiple tool examples: tools = [search_news, get_weather, get_stock_realtime_data, get_stock_kline_data]

---

## Function Details

### 1. Detachable Fully Automated Memory Module (`mem0`)
LightAgent supports external extensions of the `mem0` memory module, automating context memory and historical record management without requiring developers to manually trigger memory addition and retrieval. With the memory module, the agent can maintain contextual consistency across multiple rounds of dialogue.

```python
# Enable Memory Module

# Or use a custom memory module, here is an example with mem0 https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_API_BASE"] = "your_base_url"
        # Initialize Mem0
        config = {
            "version": "v1.1"
        }
        # Use qdrant as a vector database for storing memories in mem0, change config to the code below
        # config = {
        #     "vector_store": {
        #         "provider": "qdrant",
        #         "config": {
        #             "host": "localhost",
        #             "port": 6333,
        #         }
        #     },
        #     "version": "v1.1"
        # }
        self.m = Memory.from_config(config_dict=config)

    def store(self, data: str, user_id):
        """Store memory. Developers can modify the internal implementation of the storage method; the current example is the mem0 method for adding memory."""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """Retrieve related memory. Developers can modify the internal implementation of the retrieval method; the current example is the mem0 method for searching memory."""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4.1",  # Supported models: openai, chatglm, deepseek, qwen, etc.
        api_key="your_api_key",  # Replace with your large model provider API Key
        base_url="your_base_url",  # Replace with your large model provider api url
        memory=CustomMemory(),  # Enable memory function
        tree_of_thought=False,  # Enable Chain of Thought
    )

# Memory-enabled test & if tools need to be added, you can add tools to the agent for memory-enabled tool calls

user_id = "user_01"
logger.info("\n=========== next conversation ===========")
query = "Introduce me to the attractions in Sanya. Many of my friends have traveled to Sanya, and I want to visit too."
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== next conversation ===========")
query = "Where should I travel?"
print(agent.run(query, stream=False, user_id=user_id))
```

Output as follows:
```python
=========== next conversation ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
Starting to think about the question: Introduce me to the attractions in Sanya, many of my friends have traveled to Sanya, and I want to visit too.
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Final Reply: 
Sanya is a popular tourist city in Hainan Province, China, known for its beautiful beaches, tropical climate, and rich tourist resources. Here are some attractions worth visiting in Sanya:

1. **Yalong Bay**: Known as the "Hawaii of the East," it has a long beach and clear waters, ideal for swimming, diving, and sunbathing.

2. **Tianya Haijiao**: This is a famous cultural landscape, attracting tourists with its magnificent sea view and romantic legends. The giant rocks here are inscribed with the words "Tianya" and "Haijiao," symbolizing eternal love.

3. **Nanshan Cultural Tourism Zone**: Here there is a 108-meter-tall Nanshan Sea Guanyin statue, the highest sea Guanyin statue in the world. Visitors can experience Buddhist culture and visit temples and gardens.

4. **Wuzhizhou Island**: This small island is known for its pristine natural scenery and rich water activities. Visitors can engage in diving, snorkeling, and sea fishing among other activities.

5. **Dadonghai**: This is a beach located in Sanya city, favored by tourists for its convenient transportation and vibrant nightlife.

6. **Sanya Bay**: It is a 22-kilometer long beach and a great place to watch the sunset. This beach is relatively quiet, suitable for visitors who enjoy tranquility.

7. **Ya Nui National Park**: This is a tropical rainforest park where visitors can experience the natural scenery of tropical rainforests and participate in various adventure activities.

8. **Luohuitou Park**: A park located on a mountaintop, offering a panoramic view of Sanya city and Sanya Bay. There is also a beautiful legend about a deer.

9. **Xidao**: This is a relatively pristine small island attracting tourists with its serene beaches and rich marine life.

10. **Sanya Ancient Love**: This is a large cultural theme park showcasing the history and culture of Hainan through performances and exhibitions.

In addition to the above attractions, Sanya has many other places worth exploring, such as tropical botanical gardens and seafood markets. The local cuisine, especially fresh seafood and tropical fruits, should not be missed. When planning a trip, it is advisable to check the weather forecast and attraction opening times in advance to ensure a pleasant travel experience.
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== next conversation ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
Starting to think about the question: Where should I travel?
Relevant memory found:
User wants to travel to Sanya
User's friends have traveled to Sanya.
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Final Reply: 
Based on previously mentioned information, the user’s friends have already traveled to Sanya, and the user has also expressed interest in going there. Therefore, Sanya might be a suitable travel destination for the user. Here is some travel information about Sanya for the user’s reference:

### Recommended Travel Spots in Sanya:
1. **Yalong Bay**: Known as the "Hawaii of the East," it has beautiful beaches and clear waters, suitable for swimming and sunbathing.
2. **Tianya Haijiao**: This iconic site of Sanya attracts tourists with its unique rocks and romantic legends.
3. **Nanshan Cultural Tourism Area**: It features the famous Nanshan Temple and the 108-meter-high Sea Guanyin statue, an important Buddhist cultural site.
4. **Wuzhizhou Island**: Suitable for diving and marine sports, the island is home to a rich marine ecosystem and coral reefs.
5. **Dadonghai**: A beach within Sanya city, conveniently located and suitable for family and couple visits.

### Other Recommendations:
If the user is already familiar with Sanya or wishes to explore other destinations, here are some other popular travel places:
1. **Guilin**: Known for its unique karst landscape and Lijiang River scenery.
2. **Lijiang**: The ancient town and Jade Dragon Snow Mountain are its main attractions, suitable for those who enjoy history and natural scenery.
3. **Zhangjiajie**: Famous for its unique stone pillars and natural scenery, it is one of the shooting locations for the movie "Avatar."

Users can choose suitable travel destinations based on their interests and schedule. If the user needs more detailed information or assistance in planning the trip, feel free to let us know!
```

### 2. Tool Integration (Unlimited Custom Tool Support)
Embrace personalized tool customization (`Tools`) and easily integrate your exclusive tools through the `tools` method. These tools can be any Python function and support parameter type annotations, ensuring flexibility and accuracy. Additionally, we provide an AI-driven tool generator to help you automatically build tools and unleash creativity.

```python

import requests
from LightAgent import LightAgent

# Define Tool
def get_weather(
        city_name: str
) -> str:
    """
    Get weather information for a city
    :param city_name: Name of the city
    :return: Weather information
    """
    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

    return str(ret)
# Define tool information inside the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_title": "get weather",
    "tool_description": "Get current weather information for the specified city.",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    Search news based on keywords
    :param keyword: Search keyword
    :param max_results: Maximum number of results to return, default is 5
    :return: News search results
    """
    results = f"By searching for {keyword}, I've found {max_results} related pieces of information."
    return str(results)

# Define tool information inside the function
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_title": "search news",
    "tool_description": "Search news based on keywords.",
    "tool_params": [
        {"name": "keyword", "description": "Search keyword", "type": "string", "required": True},
        {"name": "max_results", "description": "Maximum number of results to return", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    Get user information
    :param user_id: User ID
    :return: User information
    """
    if not isinstance(user_id, str):
        raise TypeError("User ID must be a string")

    try:
        # Assume using a user info API; this is a sample URL
        url = f"https://api.example.com/users/{user_id}"
        response = requests.get(url)
        response.raise_for_status()
        user_data = response.json()
        user_info = {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "created_at": user_data.get("created_at")
        }
    except:
        import traceback
        user_info = "Error encountered while fetching user data!\n" + traceback.format_exc()

    return str(user_info)

# Define tool information inside the function
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "Retrieve information for the specified user.",
    "tool_params": [
        {"name": "user_id", "description": "User ID", "type": "string", "required": True},
    ]
}

# Custom Tools
tools = [get_weather, search_news, get_user_info]  # including all tools

# Initialize Agent
# Replace with your model parameters, API key, and base URL
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url", tools=tools)

query = "How is the weather in Sanya today?"
response = agent.run(query, stream=False)  # Use agent to run the query
print(response)
```

### 3. Tool Generator
The Tool Generator is a module for automatically generating tool code. It can create the corresponding tool code based on the text description provided by users and save it to the specified directory. This functionality is particularly useful for quickly generating API call tools, data processing tools, and more.

Usage example

Here is an example code using the Tool Generator:

```python
import json
import os
import sys
from LightAgent import LightAgent

# Initialize LightAgent
agent = LightAgent(
    name="Agent A",  # Agent name
    instructions="You are a helpful agent.",  # Role description
    role="Please remember that you are a tool generator; your task is to automatically generate corresponding tool code based on the text description provided by the user and save it to the specified directory. Please ensure that the generated code is accurate, usable, and meets the user's needs.",  # Tool generator's role description
    model="gpt-4.1",  # Replace with your model. Supported models: openai, chatglm, deepseek, qwen, etc.
    api_key="your_api_key",  # Replace with your API Key
    base_url="your_base_url",  # Replace with your API URL
)

# Sample text description
text = """
The Sina stock interface provides functionalities for obtaining stock market data, including stock quotes, real-time trading data, and K-line chart data.

Introduction to Sina stock interface functions
1. Get stock quote data:
Realtime quote data: Using the real-time quote API, you can obtain the latest prices, trading volume, and changes for stocks.
Minute line quote data: Using the minute line quote API, you can obtain the minute-by-minute trading data for stocks, including opening price, closing price, highest price, and lowest price.

2. Obtain historical K-line chart data:
K-line chart data: Through the K-line chart API, you can obtain the historical trading data for stocks, including opening price, closing price, highest price, lowest price, trading volume, etc. You can choose different time periods and moving average periods as needed.
Adjusted data: You can choose to retrieve adjusted K-line data, including pre-adjusted and post-adjusted data, for more accurate analysis of stock price changes.

Example of obtaining data from the Sina stock interface
1. Get stock quote data:
API address: http://hq.sinajs.cn/list=[stock_code]
Example: To obtain real-time quote data for the stock code "sh600519" (Kweichow Moutai), you can use the following API address: http://hq.sinajs.cn/list=sh600519
By sending an HTTP GET request to the above API address, you will receive a response containing the real-time data for that stock.

2. Get historical K-line chart data:
API address: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[stock_code]&scale=[time_period]&ma=[average_period]&datalen=[data_length]
Example: To obtain daily K-line chart data for the stock code "sh600519" (Kweichow Moutai), you can use the following API address: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
By sending an HTTP GET request to the above API address, you will receive a response containing the historical K-line chart data for that stock.
"""

# Build the path to the tools directory
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# Create tools directory if it does not exist
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Tools directory has been created: {tools_directory}")

# Use agent to generate tool code
agent.create_tool(text, tools_directory=tools_directory)
```
After execution, two files will be generated in the tools directory: get_stock_kline_data.py and get_stock_realtime_data.py.

### 4. Tree of Thought (ToT)
Currently, it is already supported to independently customize the use of the deepseek-r1 model for planning and thinking.The built-in Tree of Thought module supports complex task decomposition and multi-step reasoning. Through the Tree of Thought, the agent can better handle complex tasks.

```python
# Enable Tree of Thought
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url="your_base_url", 
    tree_of_thought=True,  # Enable Tree of Thought
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # your deepseek r1 API Key
    tot_base_url="https://api.openai.com/v1",  # api url
    filter_tools=False,  # Disable the adaptive tool mechanism
)
```
After enabling ToT, the adaptive tool mechanism is enabled by default. If you need to disable it, please add the parameter filter_tools=False when initializing LightAgent.

### 5. Multi-Agent Collaboration
Supports swarm-like multi-agent collaboration, enhancing task processing efficiency. Multiple agents can work together to complete complex tasks.

```python
from LightAgent import LightAgent, LightSwarm
# Set Environment Variables OPENAI_API_KEY and OPENAI_BASE_URL
# The default model uses gpt-4o-mini

# Create an instance of LightSwarm
light_swarm = LightSwarm()

# Create multiple agents
agent_a = LightAgent(
    name="Agent A",
    instructions="I am Agent A, the front desk receptionist.",
    role="Receptionist responsible for welcoming visitors and providing basic information guidance. Before each reply, please state your identity and that you can only guide users to other roles, not directly answer business questions. If you cannot help the user, please respond: Sorry, I am currently unable to assist!"
)

agent_b = LightAgent(
    name="Agent B",
    instructions="I am Agent B, responsible for the reservation of meeting rooms.",
    role="Meeting room reservation administrator in charge of handling reservations, cancellations, and inquiries for meeting rooms 1, 2, and 3."
)

agent_c = LightAgent(
    name="Agent C",
    instructions="I am Agent C, a technical support specialist, responsible for handling technical issues. Please state your identity before each reply, offering detailed responses to technical inquiries, and guide users to contact higher-level technical support for issues beyond your capability."
)

agent_d = LightAgent(
    name="Agent D",
    instructions="I am Agent D, an HR specialist, responsible for handling HR-related questions.",
    role="HR specialist managing inquiries and processes related to employee onboarding, offboarding, leave, and benefits."
)

# Automatically register agents to the LightSwarm instance
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# Run Agent A
res = light_swarm.run(agent=agent_a, query="Hello, I am Alice. I need to check if Wang Xiaoming has completed onboarding.", stream=False)
print(res)
```
Output as follows:
```python
Hello, I am Agent D, the HR specialist. Regarding whether Wang Xiaoming has completed onboarding, I need to check our system records. Please wait a moment.
(Checking system records...)
According to our records, Wang Xiaoming completed his onboarding procedures on January 5, 2025. He has signed all necessary documents and has been assigned an employee number and office location. If you need further details or have any other questions, please feel free to contact the HR department. We are always ready to assist you.
```

### 6. Streaming API 
Supports OpenAI streaming format API service output, seamlessly integrating with mainstream chat frameworks.

```python
# Enable streaming output
response = agent.run("Please generate an article about AI.", stream=True)
for chunk in response:
    print(chunk)
```

### 7. Agent Self-Learning
The Agent possesses a unique scene memory capability, allowing it to accurately retain key information from interactions with users. At the same time, it has a powerful ability to extract knowledge from user dialogues and engage in self-learning, continuously optimizing its understanding and response strategies for various scenarios with each conversation, thereby achieving a continuous improvement in intelligence levels to better meet the diverse needs of users. Through this self-learning mechanism, the Agent can continuously adapt to complex and changing task scenarios, providing users with higher quality, more efficient, and personalized services.
```python
agent = LightAgent(
        name="Agent A",  # Agent name
        instructions="You are a helpful agent.",  # Role description
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4.1",  # Supported models: openai, chatglm, deepseek, qwen, etc. qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # Replace with your API Key
        base_url="http://your_base_url/v1",  # API URL
        memory=CustomMemory(),  # Enable memory function
        self_learning=True,  # Enable agent self-learning
        debug=True,
        log_level="DEBUG",
        log_file="example.log"
    )

user_id = "test_user_1"
query = "I now have a procurement payment that needs to be transferred. What is my approval process?"
agent.run(query, stream=False, user_id=user_id)
query = "Please remember: According to the new company regulations, starting from January 2025, all procurement payments must first be signed by Manager Ding, who is responsible for procurement, then submitted to the finance manager for approval. After the finance manager's approval, the general manager of the company must also approve before the cashier can make the payment."
agent.run(query, stream=False, user_id=user_id)

user_id = "test_user_2"
query = "Hello, I have a procurement payment to transfer to the other party. How do I apply for the transfer?"
agent.run(query, stream=False, user_id=user_id)

```

### 8. Integrating Langfuse Log Tracking

LightAgent integrates with the [Langfuse open-source platform](https://github.com/langfuse/langfuse), providing full-link monitoring and log analysis capabilities, real-time tracking of key metrics such as token consumption and response latency, and supporting interactive data management and version control. The platform's visualization analysis features clearly display the core decision-making processes of the Agent, such as context retrieval and tool invocation, and fully record user interaction flows.
```python
from LightAgent import LightAgent

tracetools = {
    "TraceTool": "langfuse",
    "TraceToolConfig": {
        "langfuse_enabled": True,
        "langfuse_host": "https://cloud.langfuse.com",
        "langfuse_public_key": "pk-lf-9fedb073-a*86-4**5-b**2-52****1b1**7",
        "langfuse_secret_key": "sk-lf-27bdbdec-c**6-4**3-a**2-28**0140**c7"
    }
}

agent = LightAgent(
        name="Agent A",  # Agent Name
        instructions="You are a helpful agent.",  # Role Description
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4o-mini",  # Supported models: openai, chatglm, deepseek, qwen, etc. qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # Replace with your API Key
        base_url="http://your_base_url/v1",  # API URL
        debug=True,
        log_level="DEBUG",
        log_file="example.log",
        tracetools=tracetools
    )
```
The LLM call logs tracked by Langfuse are shown in the figure below:
![langfuse.png](docs/images/langfuse.png)

### 9. Agent Assessment (Coming Soon)
Built-in agent assessment tool for conveniently evaluating and optimizing agent performance.

## Mainstream Agent Model Support
Compatible with various large models, including OpenAI, Zhipu ChatGLM, DeepSeek, Qwen series large models.

#### Currently tested compatible large models
OpenAI Series
 - gpt-3.5-turbo
 - gpt-4
 - gpt-4o
 - gpt-4o-mini
 - gpt-4.1
 - gpt-4.1-mini
 - gpt-4.1-nano

ChatGLM
 - GLM-4.5
 - GLM-4.5-Air
 - GLM-4.5-X
 - GLM-4.5-AirX
 - GLM-4.5-Flash
 - GLM-4-Plus
 - GLM-4-Air-0111
 - GLM-4-Flash
 - GLM-4-FlashX
 - GLM-4-alltools
 - GLM-4
 - GLM-3-Turbo
 - ChatGLM3-6B
 - GLM-4-9B-Chat

DeepSeek Series
 - DeepSeek-r1
 - DeepSeek-v3

stepfun
 - step-1-8k
 - step-1-32k
 - step-1-128k (issues with multi-tool calls)
 - step-1-256k (issues with multi-tool calls)
 - step-1-flash (recommended, cost-effective)
 - step-2-16k (issues with multi-tool calls)

Qwen Series
 - qwen-plus-2024-11-25
 - qwen-plus-2024-11-27
 - qwen-plus-1220
 - qwen-plus
 - qwen-plus-latest 
 - qwen2.5-72b-instruct
 - qwen2.5-32b-instruct
 - qwen2.5-14b-instruct
 - qwen2.5-7b-instruct 
 - qwen-turbo-latest
 - qwen-turbo-2024-11-01
 - qwen-turbo
 - qwen-long
 - qwq-32b
 - qwen3-0.6b
 - qwen3-1.7b
 - qwen3-4b
 - qwen3-8b
 - qwen3-14b
 - qwen3-32b
 - qwen3-30b-a3b
 - qwen3-235b-a22b
 - Qwen3-30B-A3B-Thinking-2507
 - Qwen3-30B-A3B-Instruct-2507

---

## Use Cases

- **Intelligent Customer Service**: Provide efficient customer support through multi-turn dialogue and tool integration.
- **Data Analysis**: Use Tree of Thought and multi-agent collaboration to handle complex data analysis tasks.
- **Automated Tools**: Quickly build customized tools through automated tool generation.
- **Educational Assistance**: Provide personalized learning experiences using memory modules and streaming API.

---
 
## 🛠️ Contribution Guidelines

We welcome any form of contribution! Whether it's code, documentation, tests, or feedback, it's a tremendous help to the project. If you have great ideas or find bugs, please submit an Issue or Pull Request. Here are the contribution steps:

1. **Fork this project**: Click the `Fork` button at the top right corner to copy the project to your GitHub repository.
2. **Create a branch**: Create your development branch locally:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Submit changes**: After finishing development, submit your changes:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Push the branch**: Push the branch to your remote repository:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Submit Pull Request**: Submit a Pull Request on GitHub and describe your changes.

We will review your contributions promptly. Thank you for your support! ❤️

---

## 🙏 Acknowledgments

Shanghai Wanxing AI and Professor Zhang Liwen's research group from the School of Statistics and Data Science at Shanghai University of Finance and Economics have jointly open-sourced a new generation intelligent agent framework called LightAgent.The development and implementation of LightAgent owe much to the inspiration and support from the following open-source projects, especially the outstanding projects and teams:

- **MCP**: Thanks to [mcp](https://modelcontextprotocol.io/introduction) for providing the **Model Context Protocol (MCP)**, which offers a standardized infrastructure for the **dynamic tool integration** of LightAgent.
- **mem0**: Thanks to [mem0](https://github.com/mem0ai/mem0) for providing the memory module, which offers strong support for LightAgent's context management.  
- **Swarm**: Thanks to [Swarm](https://github.com/openai/swarm) for designing ideas for multi-agent collaboration, laying the groundwork for LightAgent's multi-agent features.  
- **ChatGLM3**: Thanks to [ChatGLM3](https://github.com/THUDM/ChatGLM3) for providing high-performance Chinese large model support and design inspiration.  
- **Qwen**: Thanks to [Qwen](https://github.com/QwenLM/Qwen) for providing high-performance Chinese large model support.  
- **DeepSeek-V3**: Thanks to [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) for providing high-performance Chinese large model support.  
- **StepFun**: Thanks to [step](https://www.stepfun.com/) for providing high-performance Chinese large model support.  

---

## 📄 License

LightAgent is licensed under the [Apache 2.0 License](LICENSE). You can freely use, modify, and distribute this project, but please adhere to the terms of the license.

---

## 📬 Contact Us

If you have any questions or suggestions, please feel free to contact Wanxing AI or Professor Zhang Liwen from the School of Statistics and Data Science at Shanghai University of Finance and Economics:

- **Wanxing AI Email**: service@wanxingai.com 
- **Professor Zhang Liwen Email**: zhang.liwen@shufe.edu.cn
- **GitHub Issues**: [https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

We look forward to your feedback and work together to make LightAgent even stronger! 🚀

- **More Tools** 🛠️: Continuously integrating more practical tools to meet various scenario needs.
- **More Model Support** 🔄: Continuously expanding support for more large models, catering to diverse application scenarios.
- **More Features** 🎯: More practical features, ongoing updates, stay tuned!
- **More Documentation** 📚: Detailed documentation with abundant examples for quick onboarding and easy integration into your projects.
- **More Community Support** 👥: An active developer community ready to provide help and answers anytime.
- **More Performance Optimization** ⚡: Continuously optimizing performance to meet high concurrency demands.
- **More Open Source Contributions** 🌟: Contributions in code are welcome for building a better LightAgent together!

---

<p align="center">
  <strong>LightAgent - Making intelligence lighter, making the future simpler.</strong> 🌈
</p>

**LightAgent** —— A lightweight, flexible, and powerful active Agent framework that assists you in quickly building intelligent applications!

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wxai-space/LightAgent&type=Date)](https://star-history.com/#wxai-space/LightAgent&Date)

## Paper

```bibtex
@misc{2509.09292,
Author = {Weige Cai and Tong Zhu and Jinyi Niu and Ruiqi Hu and Lingyao Li and Tenglong Wang and Xiaowu Dai and Weining Shen and Liwen Zhang},
Title = {LightAgent: Production-level Open-source Agentic AI Framework},
Year = {2025},
Eprint = {arXiv:2509.09292},
Eprinttype = {arXiv},
Eprintclass = {cs.AI},
Url = {https://arxiv.org/abs/2509.09292},
Doi = {10.48550/arXiv.2509.09292},
Note = {Submitted on 11 Sep 2025}
}
```

## Features
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/wxai-space-lightagent-badge.png)](https://mseep.ai/app/wxai-space-lightagent)
