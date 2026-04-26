
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
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style"></a>
  </p>
</div>
<div align="center">
  <p>
    <a href="README.md">English</a> | 
    <a href="README.zh-CN.md">简体中文</a> | 
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    Français | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>

<div align="center">
  <h1>LightAgent🚀 (Next Generation Agentic AI Framework)</h1>
</div>

**LightAgent** est un cadre agentique actif extrêmement léger avec mémoire (`mem0`), outils (`Tools`), et arbre de pensée (`ToT`), et il est entièrement open source. Il prend en charge une collaboration multi-agents plus simple que OpenAI Swarm, permettant de construire en un seul pas des agents capables d'apprentissage autonome, et prend en charge l'accès au protocole MCP via stdio et sse. Le modèle sous-jacent prend en charge OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen et d'autres grands modèles. De plus, LightAgent prend en charge la sortie de service API au format de flux OpenAI, s'intégrant sans couture aux principaux cadres de chat. 🌟

---

## ✨ Features

- **Light and Efficient** 🚀: Minimalist design, rapid deployment, suitable for various application scenarios. (No LangChain, No LlamaIndex) 100% implemented in Python, with no extra dependencies, core code only 1000 lines, completely open source. 
- **Memory Support** 🧠: Supports user-customizable long-term memory for each user, natively supporting `mem0` memory module, automatically managing personalized memory during conversations to make agents smarter.
- **Autonomous Learning** 📚️: Each agent has independent learning capabilities, and authorized administrators can manage each agent.
- **Tool Integration** 🛠️: Supports customizable tools (`Tools`), automated tool generation, and flexible expansion to meet diverse needs.  
- **Complex Goals** 🌳: Built-in reflective Tree of Thought (`ToT`) module supports complex task decomposition and multi-step reasoning, enhancing task processing capabilities.  
- **Multi-agent Collaboration** 🤖: Multi-agent cooperation that is easier to implement than Swarm, with built-in LightSwarm for intent recognition and task transfer capabilities, intelligently handling user input and transferring tasks to other agents as needed. 
- **Independent Execution** 🤖: Tasks are completed autonomously without human intervention.  
- **Multi-model Support** 🔄: Compatible with OpenAI, Zhiyu ChatGLM, Baichuan large models, Jumpshop Star, DeepSeek, Qwen series large models.  
- **Streaming API** 🌊: Supports OpenAI streaming API service output, seamlessly integrating with mainstream chat frameworks, enhancing user experience.  
- **Tools Generator** 🚀: Just hand over your API documentation to the [Tools Generator], and it will automatically create your exclusive tools, helping you quickly build hundreds of personalized custom tools in just one hour, enhancing efficiency and unleashing your creative potential.
- **Agent Self-Learning** 🧠️: Each agent has its own contextual memory capability, enabling self-learning from user conversations.
- **Adaptive Tools Mechanism** 🛠️: Support for adding unlimited tools, allowing the large model to first select a candidate tool set from tens of thousands of tools, filtering out irrelevant tools before submitting context to the large model, significantly reducing token consumption.


## 🚧 Coming Soon

- **Communication collaborative des agents** 🛠️ : Les agents peuvent également partager des informations et transmettre des messages, réalisant ainsi une communication complexe des informations et une collaboration sur les tâches.
- **Agent Evaluation** 📊: Built-in Agent evaluation tools for assessing and optimizing the agents you build, aligning with business scenarios, and continuously improving intelligence.  

## Built-in "Thought Flow"
(Thought Flow) method through systematic, structured, and flexible thinking processes can effectively tackle challenges in complex scenarios. 
Here are the specific implementation steps:
```text
Problem Definition: Clearly define the core problem and goals.

Information Gathering: Systematically collect relevant information and data.

Decompose Problems: Break complex problems down into multiple sub-problems or modules.

Multidimensional Analysis: Analyze each sub-problem from different perspectives and levels.

Establish Connections: Identify the correlations and dependencies between sub-problems.

Generate Solutions: Propose possible solutions for each sub-problem.

Evaluate and Choose: Assess the feasibility and impact of each solution, and select the best one.

Implementation and Feedback: Implement the chosen solution and adjust based on feedback.
```

---
## 🌟 Why Choose LightAgent?

- **Open Source and Free** 💖: Completely open source, community-driven, continuously updated, contributions welcomed!  
- **Easy to Get Started** 🎯: Detailed documentation, abundant examples, quick to start, and easy to integrate into your projects.  
- **Community Support** 👥: An active developer community ready to assist and answer your questions.  
- **High Performance** ⚡: Optimized design for efficient operation, meeting high concurrency scenario demands.  

---

## 🛠️ Quick Start

### Install the Latest Version of LightAgent

```bash
pip install lightagent
```

(Optional installation) Install the Mem0 package via pip:

```bash
pip install mem0ai
```

Alternatively, you can use Mem0 on a hosting platform with one-click [click here](https://www.mem0.ai/).

### Hello World Sample Code

```python
from LightAgent import LightAgent

# Initialize the Agent
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url="your_base_url")

# Run the Agent
response = agent.run("Hello, who are you?")
print(response)
```

### Set Agent Self-Recognition Through System Prompts

```python
from LightAgent import LightAgent

# Initialize the Agent
agent = LightAgent(
     role="Please remember you are LightAgent, a helpful assistant that can help users utilize multiple tools.",  # system role description
     model="deepseek-chat",  # Supported models: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # Replace with your large model service provider API Key
     base_url="your_base_url",  # Replace with your large model service provider api url
 )
# Run the Agent
response = agent.run("May I ask who you are?")
print(response)
```

### Tool Usage Sample Code

```python
from LightAgent import LightAgent

# Define Tool
def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"Query result: {city_name} Weather is clear"
# Define tool information within the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get the current weather information for a specified city",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Initialize the Agent
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url="your_base_url", tools=tools)

# Run the Agent
response = agent.run("Please help me check the weather condition in Shanghai")
print(response)
```
Supports custom tools in unlimited quantities.

Multiple tool examples: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## Detailed Function Descriptions

### 1. Detachable Fully Automated Memory Module (`mem0`)
LightAgent supports external extension of the `mem0` memory module for fully automated context memory and historical record management without manual triggering of memory addition and retrieval by developers. Through the memory module, agents can maintain contextual consistency over multiple conversation rounds.

```python
# Enable Memory Module

# Or use a custom memory module, here we use mem0 as an example https://github.com/mem0ai/mem0/
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
        # If using qdrant as a vector database in mem0 to store memories, change config to the code below
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
        """Store memory developers can modify the internal implementation of the storage method, the current example is mem0's memory addition method"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """Retrieve related memory developers can modify the internal implementation of the retrieval method, the current example is mem0's memory searching method"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="Please remember you are LightAgent, a helpful assistant that can help users utilize multiple tools.",  # system role description
        model="deepseek-chat",  # Supported models: openai, chatglm, deepseek, qwen, etc.
        api_key="your_api_key",  # Replace with your large model service provider API Key
        base_url="your_base_url",  # Replace with your large model service provider api url
        memory=CustomMemory(),  # Enable memory functionality
        tree_of_thought=False,  # Enable Thought Chain
    )

# Memory tests & If tools need to be added, they can be added to the agent to realize memory-enabled tool calls

user_id = "user_01"
logger.info("\n=========== next conversation ===========")
query = "Introduce some fun attractions in Sanya, many of my friends have traveled to Sanya, and I also want to go play."
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== next conversation ===========")
query = "Where do I want to travel?"
print(agent.run(query, stream=False, user_id=user_id))
```

The output is as follows:
```python
=========== next conversation ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
Starting to think about the problem: Introduce some fun attractions in Sanya, many of my friends have traveled to Sanya, and I also want to go play.
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Final Reply: 
Sanya is a popular tourist city in Hainan Province, China, known for its beautiful beaches, tropical climate, and rich tourist resources. Here are some attractions worth visiting in Sanya:

1. **Yalong Bay**: Known as the "Hawaii of the East," it has long beaches and clear waters, making it ideal for swimming, diving, and sunbathing.

2. **Tianya Haijiao**: A famous cultural landscape known for its magnificent sea views and romantic legends. The boulders here are inscribed with the words "Tianya" and "Haijiao," symbolizing eternal love.

3. **Nanshan Cultural Tourism Zone**: Home to a 108-meter tall Nanshan Avalokitesvara statue, the highest sea Avalokitesvara statue in the world. Visitors can experience Buddhist culture and tour temples and gardens.

4. **Wuzhizhou Island**: A small island known for its pristine natural scenery and rich water activities. Visitors can engage in diving, snorkeling, and sea fishing here.

5. **Dadonghai**: A beach in downtown Sanya loved by tourists for its convenient transportation and vibrant nightlife.

6. **Sanya Bay**: A beach that stretches for 22 kilometers, making it a great place to watch the sunset. The beach here is quieter, suitable for those who enjoy tranquility.

7. **Yanuoda Rainforest Cultural Tourism Zone**: A tropical rainforest park where visitors can experience the natural beauty of tropical rainforests and participate in various adventure activities.

8. **Luhuitou Park**: A mountaintop park that offers stunning views of Sanya city and Sanya Bay. There is also a beautiful legend about a deer.

9. **Xidao**: A relatively primitive small island attracting tourists with its serene beaches and rich marine life.

10. **Sanya Qianguqing**: A large cultural theme park showcasing Hainan's history and culture through performances and exhibitions.

In addition to the attractions mentioned above, Sanya has many other places worth exploring, such as the Tropical Botanical Garden and seafood markets. Don't miss out on Sanya's delicious food, especially fresh seafood and tropical fruits. When planning a trip, it is recommended to check the weather forecast and the opening hours of attractions in advance to ensure an enjoyable travel experience.
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== next conversation ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
Starting to think about the problem: Where do I want to travel?
Found related memory:
User wants to travel to Sanya
User's friends have traveled to Sanya。
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Final Reply: 
Based on the information previously mentioned by the user, the user's friends have traveled to Sanya, and the user has also expressed interest in Sanya. Therefore, Sanya might be a suitable travel destination for the user. Here are some travel recommendations for Sanya:
### Recommendations for Traveling to Sanya:
1. **Yalong Bay**: Known as the "Hawaii of the East," it features beautiful beaches and clear waters, ideal for swimming and sunbathing.
2. **Tianya Haijiao**: A landmark attraction in Sanya, it attracts visitors with its unique rocks and romantic legends.
3. **Nanshan Cultural Tourism Zone**: Famous for the Nanshan Temple and the 108-meter high sea Avalokitesvara statue, an important site for Buddhist culture.
4. **Wuzhizhou Island**: Suitable for diving and water activities, the island is rich in marine life and coral reefs.
5. **Dadonghai**: A conveniently located beach in Sanya city, popular with families and couples.

### Additional Recommendations:
If the user is already familiar with Sanya or wants to explore other destinations, here are some other popular travel locations:
1. **Guilin**: Known for its unique karst topography and scenery along the Li River.
2. **Lijiang**: The ancient town and Jade Dragon Snow Mountain are its main attractions, suitable for visitors who enjoy cultural history and natural beauty.
3. **Zhangjiajie**: Known for its unique stone pillars and natural scenery, it was one of the filming locations for the movie "Avatar."

Users can choose suitable travel destinations based on their interests and time arrangements. If they need more detailed information or help planning their trip, please let them know!
```

### 2. Tool Integration (Unlimited Custom Tool Support)
Embrace personalized tool customization (`Tools`) and easily integrate your exclusive tools through the `tools` method. These tools can be any Python function, supporting parameter type annotations for flexibility and precision. In addition, we provide AI-driven tool generators to help you automate tool building and unleash creativity.

```python
import requests
from LightAgent import LightAgent

# Define Tool
def get_weather(
        city_name: str
) -> str:
    """
    Get the weather information for a city
    :param city_name: The name of the city
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
# Define Tool Information within the function
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Get the current weather information for a specified city",
    "tool_params": [
        {"name": "city_name", "description": "The name of the city to query", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    Search for news by keyword
    :param keyword: Search keyword
    :param max_results: Maximum number of results to return, default is 5
    :return: News search results
    """
    results = f"Through searching {keyword}, I found {max_results} related information."
    return str(results)

# Define Tool Information within the function
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "Search for news by keyword",
    "tool_params": [
        {"name": "keyword", "description": "Search keyword", "type": "string", "required": True},
        {"name": "max_results", "description": "Maximum results to return", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    Get information of a user
    :param user_id: User ID
    :return: User information
    """
    if not isinstance(user_id, str):
        raise TypeError("User ID must be a string")

    try:
        # Assuming using a user information API, here is a sample URL
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

# Define Tool Information within the function
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "Get information of a specified user",
    "tool_params": [
        {"name": "user_id", "description": "User ID", "type": "string", "required": True},
    ]
}

# Custom Tools
tools = [get_weather, search_news, get_user_info]  # Include all tools

# Initialize the Agent
# Replace with your model parameters: model, api_key, base_url
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url="your_base_url", tools=tools)

query = "What is the current weather like in Sanya?"
response = agent.run(query, stream=False)  # Use agent to run the query
print(response)
```

### 3. Tools Generator
The Tools Generator is a module for automating the generation of tool code. It can automatically generate the corresponding tool code based on the text description provided by the user and save it to a specified directory. This function is particularly suitable for quickly generating API calling tools, data processing tools, and other scenarios.

Usage example

Here’s an example of using the Tools Generator:

```python
import json
import os
import sys
from LightAgent import LightAgent

# Initialize LightAgent
agent = LightAgent(
    name="Agent A",  # Agent name
    instructions="You are a helpful agent.",  # Role description
    role="Please remember you are a tool generator, your task is to automatically generate corresponding tool code based on the text description provided by the user and save it to the specified directory. Please ensure that the generated code is accurate, usable, and meets the user's needs.",  # Tool generator's role description
    model="deepseek-chat",  # Replace with your model. Supported models: openai, chatglm, deepseek, qwen, etc.
    api_key="your_api_key",  # Replace with your API Key
    base_url="your_base_url",  # Replace with your API URL
)

# Sample text description
text = """
The Sina Stock API provides functionality for obtaining stock market data, including stock quotes, real-time trading data, K-line data, etc.

Sina Stock API Functional Introduction
1. Get Stock Quote Data:
Real-time quote data: Use the real-time quote API to obtain the latest quotes, transaction volumes, price changes, and other information for stocks.
Minute line quote data: Use the minute line API to obtain the minute-by-minute trading data for stocks, including opening price, closing price, highest price, lowest price, etc.

2. Get Historical K-line Data for Stocks:
K-line data: Through the K-line API, you can obtain historical transaction data for stocks, including opening price, closing price, highest price, lowest price, transaction volume, etc. You can choose different time periods and moving average cycles as needed.
Stock dividends data: You can choose to get stock price data adjusted for dividends, including forward and backward adjustments, to analyze stock price changes more accurately.

Sample of Getting Data from the Sina Stock API
1. Get Stock Quote Data:
API Address: http://hq.sinajs.cn/list=[Stock Code]
Example: To get the real-time quote data for the stock code "sh600519" (Kweichou Moutai), you can use the following API address: http://hq.sinajs.cn/list=sh600519
By sending an HTTP GET request to the above API address, you will receive a response containing the real-time quote data for the stock.

2. Get Historical K-line Data for Stocks:
API Address: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[Stock Code]&scale=[Time Period]&ma=[Moving Average Period]&datalen=[Data Length]
Example: To get the daily K-line data for the stock code "sh600519" (Kweichou Moutai), you can use the following API address: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
By sending an HTTP GET request to the above API address, you will receive a response containing the historical K-line data for the stock.
"""

# Build the path to the tools directory
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# If the tools directory does not exist, create it
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Tools directory created: {tools_directory}")

# Use the agent to generate tool code
agent.create_tool(text, tools_directory=tools_directory)
```
Executing this will generate 2 files in the tools directory: get_stock_kline_data.py and get_stock_realtime_data.py

### 4. Tree of Thought (ToT)
Built-in thought tree module supports complex task decomposition and multi-step reasoning. Through the Tree of Thought, the agent can better handle complex tasks.

```python
# Activer l'arbre de pensée
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # Activer l'arbre de pensée
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # Remplacez par votre clé API deepseek r1
    tot_base_url="https://api.openai.com/v1",  # url de l'API
    filter_tools=False,  # Désactiver le mécanisme d'outils adaptatifs
)
```
Après avoir activé ToT, le mécanisme d'outils adaptatifs est activé par défaut. Si vous souhaitez le désactiver, veuillez ajouter le paramètre filter_tools=False lors de l'initialisation de LightAgent.

### 5. Multi-Agent Collaboration
Supports swarm-like multi-agent collaboration to enhance task processing efficiency. Multiple agents can collaborate to complete complex tasks.

```python
from LightAgent import LightAgent, LightSwarm
# Set the environment variables OPENAI_API_KEY and OPENAI_BASE_URL
# The model defaults to gpt-4o-mini

# Create a LightSwarm instance
light_swarm = LightSwarm()

# Create multiple agents
agent_a = LightAgent(
    name="Agent A",
    instructions="I am Agent A, a front desk receptionist",
    role="Front desk receptionist responsible for receiving visitors and providing basic information guidance. Please introduce your identity before each response, and you may only guide users to other roles, not directly answer customers' business questions. If you cannot resolve the user's question, please reply: I'm sorry, I cannot provide help at the moment!",
)

agent_b = LightAgent(
    name="Agent B",
    instructions="I am Agent B, responsible for booking meeting rooms",
    role="Meeting room reservation administrator, responsible for processing reservations, cancellations, and inquiries for rooms 1, 2, and 3. Please introduce your identity before each response and politely respond to users' queries.",
)

agent_c = LightAgent(
    name="Agent C",
    instructions="I am Agent C, a technical support specialist responsible for technical issues. Please introduce your identity before each response and provide detailed answers to users' technical questions. If the question exceeds my abilities, please guide the user to contact higher-level technical support.",
    role="Technical support specialist responsible for handling inquiries and solutions regarding hardware, software, network issues, etc.",
)

agent_d = LightAgent(
    name="Agent D",
    instructions="I am Agent D, a human resources specialist responsible for handling HR-related issues. Please introduce your identity before each response and provide detailed answers to users' questions. If the issue requires further processing, please guide the user to contact the HR department.",
    role="HR specialist responsible for handling employee onboarding, resignations, leave, benefits, etc.",
)

# Automatically register agents to the LightSwarm instance
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# Run Agent A
res = light_swarm.run(agent=agent_a, query="Hello, I am Alice. I need to check if Wang Xiaoming has completed his onboarding.", stream=False)
print(res)
```
The output is as follows:
```python
Hello, I am Human Resources Specialist Agent D. Regarding whether Wang Xiaoming has completed his onboarding, I need to check our system records. Please hold on a moment.
(Querying system records...)
According to our records, Wang Xiaoming completed his onboarding procedures on January 5, 2025. He has signed all necessary documents and has been assigned an employee number and office location. If you need further details, or have any other questions, please feel free to contact the HR department. We are always ready to assist you.
```

### 6. Streaming API 
Supports OpenAI streaming API service output, seamlessly integrating with mainstream chat frameworks.

```python
# Enable streaming output
response = agent.run("Please generate an article about AI", stream=True)
for chunk in response:
    print(chunk)
```

### 7. Agent Evaluation (Coming Soon)
Built-in agent evaluation tools for convenient assessment and optimization of agent performance.

## Supported Mainstream Agent Models
Compatible with various large models including OpenAI, Zhiyu ChatGLM, DeepSeek, Qwen series large models.

#### Currently Tested Compatible Large Models
OpenAI Series
 - gpt-3.5-turbo
 - gpt-4
 - gpt-4o
 - gpt-4o-mini
 - gpt-4.1
 - gpt-4.1-mini
 - gpt-4.1-nano
 - and GPT-5、GPT-5.1、GPT-5.2、GPT-5.3、GPT-5.4 

ChatGLM
 - GLM-5.1
 - GLM-4.7
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
 - DeepSeek-v4

stepfun
 - step-1-8k
 - step-1-32k
 - step-1-128k (issues with multi-tool calls)
 - step-1-256k (issues with multi-tool calls)
 - step-1-flash (recommended, cost-effective)
 - step-2-16k (issues with multi-tool calls)
 - step-3.5-flash

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
 - Qwen3.5
 - Qwen3.6


MiniMax Series
- MiniMax-M2.7
- MiniMax-M2.5
- MiniMax-M2.1
- MiniMax-M2


Moonshot Series (Kimi)
- moonshot-v1-8k
- moonshot-v1-32k
- moonshot-v1-128k
- Kimi K2.6


---

## Use Cases

- **Intelligent Customer Service**: Provide efficient customer support through multi-turn conversations and tool integration.
- **Data Analysis**: Use Tree of Thought and multi-agent collaboration to process complex data analysis tasks.
- **Automated Tools**: Quickly build customized tools through automated tool generation.
- **Educational Assistance**: Provide personalized learning experiences through memory modules and streaming APIs.

---
 
## 🛠️ Contribution Guidelines

We welcome contributions of any form! Whether it's code, documentation, testing, or feedback, every bit helps the project immensely. If you have good ideas or find bugs, please submit an issue or pull request. Here are the contribution steps:

1. **Fork This Project**: Click the `Fork` button in the upper right corner to copy the project to your GitHub repository.
2. **Create a Branch**: Create your development branch locally:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Submit Changes**: After completing the development, submit your changes:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **Push Branch**: Push the branch to your remote repository:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Submit Pull Request**: Submit a pull request on GitHub and describe your changes.

We will review your contributions as soon as possible. Thank you for your support! ❤️

---

## 🙏 Acknowledgments

The development and implementation of LightAgent would not have been possible without the inspiration and support from the following open-source projects, especially the excellent teams behind them:

- **mem0**: Thanks to [mem0](https://github.com/mem0ai/mem0) for providing the memory module, which offers strong support for contextual management in LightAgent.  
- **Swarm**: Thanks to [Swarm](https://github.com/openai/swarm) for the multi-agent collaborative design ideas that underpin the multi-agent functionality of LightAgent.  
- **ChatGLM3**: Thanks to [ChatGLM3](https://github.com/THUDM/ChatGLM3) for high-performance Chinese large model support and design inspiration.  
- **Qwen**: Thanks to [Qwen](https://github.com/QwenLM/Qwen) for high-performance Chinese large model support.  
- **DeepSeek-V3**: Thanks to [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) for high-performance Chinese large model support.  
- **StepFun**: Thanks to [step](https://www.stepfun.com/) for high-performance Chinese large model support.  

---

## 📄 License

LightAgent is licensed under the [Apache 2.0 License](LICENSE). You are free to use, modify, and distribute this project, but please comply with the terms of the license.

---

## 📬 Contact Us

For any questions or suggestions, feel free to contact us:

- **Email**: service@wanxingai.com  
- **GitHub Issues**: [https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

We look forward to your feedback to make LightAgent stronger! 🚀

- **More Tools** 🛠️: Continuously integrating more practical tools to meet various scenario needs.
- **More Model Support** 🔄: Continuously expanding support for more large models to meet more application scenarios.
- **More Functionality** 🎯: More practical features, continuously updated, stay tuned!
- **More Documentation** 📚: Detailed documentation with rich examples, quick to start and easy to integrate into your projects.
- **More Community Support** 👥: An active developer community ready to assist and answer your questions.
- **More Performance Optimization** ⚡: Continuously optimizing performance to meet high concurrency scenario demands.
- **More Open Source Contributions** 🌟: Contributions of code are welcome to build a better LightAgent together!

---

<p align="center">
  <strong>LightAgent - Make intelligence lighter and the future simpler.</strong> 🌈
</p>

 
**LightAgent** —— A lightweight, flexible, and powerful proactive Agent framework to help you quickly build intelligent applications!