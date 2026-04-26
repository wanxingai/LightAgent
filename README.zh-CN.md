
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
    <a href="README.md">English</a> | 
    简体中文 | 
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
  <h1>LightAgent🚀（生产级开源Agentic AI开发框架）</h1>
</div>




**LightAgent** 是一个极其轻量的带记忆（`mem0`）、工具（`Tools`）、思维树（`ToT`）的主动式 Agentic Framework（自主性框架），并且完全开源。它支持比Openai Swarm更简单的多智能体协同，简单一步即可构建具备自我学习能力的agent，并支持stdio和sse方式接入MCP协议。底层模型支持 OpenAI、智谱 ChatGLM、DeepSeek、阶跃星辰、Qwen通义千问大模型等。同时，LightAgent 支持 OpenAI 流格式 API 服务输出，无缝接入各大主流 Chat 框架。🌟

---
![lightswarm_demo_cn.png](docs%2Fimages%2Flightswarm_demo_cn.png)
## ✨ 特性

- **轻量高效** 🚀：极简设计，快速部署，适合各种规模的应用场景。（No LangChain, No LlamaIndex）100% Python 实现，无需额外依赖，核心代码仅1000行，完全开源。 
- **记忆支持** 🧠：支持为每个用户自定义长期记忆，原生支持 `mem0` 记忆模块，实现对话过程中自动管理用户个性化记忆，让 Agent 更智能。
- **自主学习** 📚️：每个agent拥有自主学习能力，并且拥有权限的管理员可以管理每个agent。
- **工具集成** 🛠️：支持自定义工具（`Tools`）和MCP工具集成，灵活扩展，满足多样化需求。  
- **复杂目标** 🌳：内置带反思的思维树（ToT）模块，支持复杂任务分解和多步推理，提升任务处理能力。  
- **多智能体协同** 🤖：比Swarm更简单的多智能体协同，内置的LightSwarm实现意图判断和任务转移功能，能够更智能地处理用户输入，并根据需要将任务转移给其他代理。 
- **独立执行** 🤖：无人为干预自主完成任务工具调用。  
- **多模型支持** 🔄：兼容 OpenAI、智谱 ChatGLM、百川大模型、阶跃星辰、DeepSeek、Qwen 系列大模型。  
- **流式 API输出** 🌊：支持 OpenAI 流格式 API 服务输出，无缝接入主流 Chat 框架，提升用户体验。  
- **Tools工具生成器** 🚀：只需将您的API文档交给[[Tools工具生成器]](#3-tools工具生成器)，它将自动化地为您打造专属的tools，助您在短短1小时内快速构建数百个个性化的自定义工具，提升效率，释放您的创新潜能。
- **agent自我学习** 🧠️：每个agent拥有自己的场景记忆能力，拥有从用户的对话中进行自我学习能力。
- **自适应tools机制** 🛠️：支持添加无限量tools，在上万个工具中让大模型过滤无关工具后再发送给大模型，可大幅度降低Token消耗。

---
## 新闻
<<<<<<< Updated upstream
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-02-21]** LightAgent v0.5.0 正式发布：新增会话级工具集约束以实现精细控制，修复多轮对话中的工具调用历史记录问题，并提升 LightSwarm 稳定性。
=======
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-04-26]** LightAgent v0.6.0 正式发布：彻底重构了核心系统架构，并引入了原生skill技能支持，内置script执行安全沙箱，从而实现了更加模块化、可扩展且任务导向的代理功能。
- **[2026-02-21]** LightAgent v0.5.0 正式发布：新增会话级工具集约束以实现精细控制，修复多轮对话中的工具调用历史记录问题，并提升 LightSwarm 稳定性。
>>>>>>> Stashed changes
- **[2026-01-20]** LightAgent v0.4.8 正式发布：引入运行时工具集约束以支持会话级控制，并增强调试配置。
- **[2025-11-15]** LightAgent v0.4.7 正式发布：改进调试配置，修复 LightSwarm 相关错误。
- **[2025-10-28]** LightAgent v0.4.6 正式发布：新增对模型扩展参数的支持（如 Qwen3 的思考模式控制），并增强元数据处理能力。
- **[2025-09-16]** 我们的论文发布在了arXiv <a href="https://arxiv.org/abs/2509.09292">https://arxiv.org/pdf/2509.09292 </a>，欢迎大家阅读和引用！
- **[2025-06-12]** 我们很高兴地宣布 LightAgent v0.4.0 正式发布！本次版本升级带来了架构级改进，在性能、稳定性和可维护性方面均有显著提升。
- **[2025-05-05]** LightAgent v0.3.3版本发布：深度集成Langfuse日志跟踪，优化上下文管理与工具调用稳定性 [查看>>](#8-集成langfuse日志跟踪)
- **[2025-04-21]** LightAgent v0.3.2 新增自适应Tools机制，支持无限量工具智能筛选，Token消耗降低80%，响应速度提升52%！ [查看>>](#4-思维树tot)
- **[2025-04-01]** LightAgent v0.3.0 支持浏览器交互 [browser_use](https://github.com/browser-use/browser-use)，并全面支持MCP协议，支持多模型多工具的协同工作，实现更高效的复杂任务处理。<a href="mcp_release.zh-CN.md">查看MCP发布简介>></a>
- **[2025-02-19]** LightAgent v0.2.7 支持单独采用 deepseek-r1 作为的agent推理规划ToT引擎，大幅度提升复杂任务的多工具Plan能力.
- **[2025-02-06]** LightAgent version 0.2.5 is released now.
- **[2025-01-20]** LightAgent version 0.2.0 is released now.
- **[2025-01-05]** LightAgent version 0.1.0 is released now.

---

## 🚧 即将推出

- **智能体协同通讯** 🛠️：智能体之间还可以共享信息和传递消息，实现复杂的信息通讯和任务协同。
- **Agent 测评** 📊：内置 Agent 测评工具，方便评估和优化你构建的Agent，对齐业务场景，持续提升智能水平。
- **支持Agent Skills** ✨：为智能体提供可插拔的技能模块，快速扩展智能体的能力边界，支持自定义技能开发和社区共享。

## 🔥内置 “思考流”
### ToT现已支持DeepSeek-R1
（Thought Flow）方法通过系统性、结构化和灵活的思维过程，能够有效应对复杂场景中的挑战。
 以下是具体实施步骤：
```text
问题定义：明确核心问题和目标。

信息收集：系统地收集相关信息和数据。

分解问题：将复杂问题分解为多个子问题或模块。

多维度分析：从不同角度和层面分析每个子问题。

建立关联：识别子问题之间的关联和依赖关系。

生成解决方案：针对每个子问题提出可能的解决方案。

评估与选择：评估各解决方案的可行性和影响，选择最优方案。

实施与反馈：实施选定方案，并根据反馈进行调整。
```

---
## 🌟 为什么选择 LightAgent？

- **开源免费** 💖：完全开源，社区驱动，持续更新，欢迎贡献！  
- **易于上手** 🎯：文档详尽，示例丰富，快速上手，轻松集成到你的项目中。  
- **社区支持** 👥：活跃的开发者社区，随时为你提供帮助和解答。  
- **高性能** ⚡：优化设计，高效运行，满足高并发场景需求。  

---

## 🛠️ 快速开始

### 安装LightAgent最新版本

```bash
pip install lightagent
```

（可选安装）通过 pip 安装 Mem0 包：

```bash
pip install mem0ai
```

或者，您可以通过一键点击在托管平台上使用 Mem0，[点击这里](https://www.mem0.ai/)。


### Hello world 示例代码

```python
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url= "your_base_url")

# 运行 Agent
response = agent.run("你好，你是谁？")
print(response)
```

### 通过system提示词设定模型自我认知

```python
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(
     role="请记住你是LightAgent，一个可以帮助用户完成多工具使用的有用助手。",  # system角色描述
     model="gpt-4.1",  # 支持的模型：openai, chatglm, deepseek, qwen 等
     api_key="your_api_key",  # 替换为你的大模型服务商 API Key
     base_url="your_base_url",  # 替换为你的大模型服务商 api url
 )
# 运行 Agent
response = agent.run("请问你是谁？")
print(response)
```

### 使用工具示例代码

```python
from LightAgent import LightAgent


# 定义工具
def get_weather(city_name: str) -> str:
    """
    Get the current weather for `city_name`
    """
    return f"查询结果: {city_name} 天气晴"
# 在函数内部定义工具信息
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "获取指定城市的当前天气信息",
    "tool_params": [
        {"name": "city_name", "description": "要查询的城市名称", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# 初始化 Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# 运行 Agent
response = agent.run("请帮我查询一下上海的天气情况")
print(response)
```
支持自定义无限数量的工具。

多个工具示例： tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## 功能详解

### 1. 可拆卸的全自动记忆模块（`mem0`）
LightAgent 支持外部扩展自定义记忆模块或使用 `mem0` 作为记忆扩展，[查看什么是mem0？](https://github.com/mem0ai/mem0/)，全自动进行上下文记忆和历史记录管理，无需开发人员手动触发添加记忆和记忆查找。通过记忆模块，Agent 可以在多轮对话中保持上下文一致性。

```python
# 启用记忆模块

# 或者使用自定义记忆模块，下面以mem0为例 https://github.com/mem0ai/mem0/
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
        # mem0中 如需使用qdrant作为向量数据库存储记忆，请将config改为下面代码
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
        """存储记忆 开发者可以自行修改存储方法的内部实现，当前示例为mem0的添加记忆方法"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """检索相关记忆 开发者可以自行修改检索方法的内部实现，当前示例为mem0的查找记忆方法"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="请记住你是LightAgent，一个可以帮助用户完成多工具使用的有用助手。",  # system角色描述
        model="gpt-4.1",  # 支持的模型：openai, chatglm, deepseek, qwen 等
        api_key="your_api_key",  # 替换为你的大模型服务商 API Key
        base_url="your_base_url",  # 替换为你的大模型服务商 api url
        memory=CustomMemory(),  # 启用记忆功能
        tree_of_thought=False,  # 启用思维链
    )

# 带记忆的测试 & 如果需要添加工具可以自行添加tools到agent来实现带记忆的工具调用

user_id = "user_01"
logger.info("\n=========== next conversation ===========")
query = "介绍下三亚的有什么好玩的景点，身边很多朋友都去三亚旅游了，我也想去玩"
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== next conversation ===========")
query = "我想去哪里旅游呢？"
print(agent.run(query, stream=False, user_id=user_id))
```

输出如下：
```python
=========== next conversation ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
开始思考问题: 介绍下三亚的有什么好玩的景点，身边很多朋友都去三亚旅游了，我也想去玩
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Final Reply: 
三亚是中国海南省的一个热门旅游城市，以其美丽的海滩、热带气候和丰富的旅游资源而闻名。以下是一些三亚值得一游的景点：

1. **亚龙湾**：被誉为“东方夏威夷”，拥有绵长的沙滩和清澈的海水，是游泳、潜水和日光浴的理想之地。

2. **天涯海角**：这是一个著名的文化景观，以其壮丽的海景和浪漫的传说而吸引游客。这里的巨石上刻有“天涯”和“海角”字样，象征着永恒的爱情。

3. **南山文化旅游区**：这里有一个高达108米的南山海上观音像，是世界上最高的海上观音像。游客可以在这里体验佛教文化，参观寺庙和园林。

4. **蜈支洲岛**：这是一个小岛，以其原始的自然风光和丰富的水上活动而闻名。游客可以在这里进行潜水、浮潜、海钓等活动。

5. **大东海**：这是三亚市区内的一个海滩，以其便利的交通和丰富的夜生活而受到游客的喜爱。

6. **三亚湾**：这是一个长达22公里的海滩，是观赏日落的好地方。这里的海滩较为安静，适合喜欢宁静的游客。

7. **呀诺达雨林文化旅游区**：这是一个热带雨林公园，游客可以在这里体验热带雨林的自然风光，参与各种探险活动。

8. **鹿回头公园**：这是一个位于山顶的公园，可以俯瞰整个三亚市区和三亚湾的美景。这里还有一个关于鹿的美丽传说。

9. **西岛**：这是一个相对较为原始的小岛，以其宁静的海滩和丰富的海洋生物而吸引游客。

10. **三亚千古情**：这是一个大型的文化主题公园，通过表演和展览展示海南的历史和文化。

除了上述景点，三亚还有许多其他值得探索的地方，如热带植物园、海鲜市场等。三亚的美食也不容错过，尤其是新鲜的海鲜和热带水果。在规划旅行时，建议提前查看天气预报和景点开放时间，以确保有一个愉快的旅行体验。
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== next conversation ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
开始思考问题: 我想去哪里旅游呢？
发现相关记忆:
User wants to travel to Sanya
User's friends have traveled to Sanya。
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Final Reply: 
根据用户之前提到的信息，用户的朋友已经去过三亚（Sanya），而用户自己也表达了对三亚的兴趣。因此，三亚可能是一个适合用户的旅游目的地。以下是一些关于三亚的旅游信息，供用户参考：

### 三亚旅游推荐：
1. **亚龙湾**：被誉为“东方夏威夷”，拥有美丽的海滩和清澈的海水，适合游泳和日光浴。
2. **天涯海角**：三亚的标志性景点，以其独特的岩石和浪漫的传说吸引游客。
3. **南山文化旅游区**：这里有著名的南山寺和108米高的海上观音像，是佛教文化的重要景点。
4. **蜈支洲岛**：适合潜水和海上运动，岛上有丰富的海洋生物和珊瑚礁。
5. **大东海**：三亚市区内的海滩，交通便利，适合家庭和情侣游玩。

### 其他推荐：
如果用户对三亚已经有所了解，或者想要探索其他目的地，以下是一些其他热门旅游地：
1. **桂林**：以其独特的喀斯特地貌和漓江风光闻名。
2. **丽江**：古城和玉龙雪山是其主要景点，适合喜欢历史文化和自然风光的游客。
3. **张家界**：以其奇特的石柱和自然景观著称，是《阿凡达》电影的取景地之一。

用户可以根据自己的兴趣和时间安排选择合适的旅游目的地。如果用户需要更详细的信息或帮助规划行程，请随时告知！
```

### 2. 工具集成（无限扩展的自定义工具支持）
拥抱个性化工具定制（`Tools`），并通过 `tools` 方法轻松集成您的专属工具。这些工具可以是任何Python函数，并且支持参数类型注解，以确保灵活性和精确性。此外，我们还提供智能AI驱动的工具生成器，助力您自动化构建工具，释放创造力。

```python

import requests
from LightAgent import LightAgent

# 定义工具
def get_weather(
        city_name: str
) -> str:
    """
    获取城市天气信息
    :param city_name: 城市名称
    :return: 天气信息
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
# 在函数内部定义工具信息
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_name": "获取天气",
    "tool_description": "获取指定城市的当前天气信息",
    "tool_params": [
        {"name": "city_name", "description": "要查询的城市名称", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    根据关键词搜索新闻
    :param keyword: 搜索关键词
    :param max_results: 返回的最大结果数量，默认为 5
    :return: 新闻搜索结果
    """
    results = f"通过搜索{keyword}, 我找到{max_results}条相关信息"
    return str(results)

# 在函数内部定义工具信息
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_name": "联网搜索",
    "tool_description": "根据关键词搜索新闻",
    "tool_params": [
        {"name": "keyword", "description": "搜索关键词", "type": "string", "required": True},
        {"name": "max_results", "description": "返回的最大结果数量", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    获取用户信息
    :param user_id: 用户 ID
    :return: 用户信息
    """
    if not isinstance(user_id, str):
        raise TypeError("User ID must be a string")

    try:
        # 假设使用一个用户信息 API，这里用示例 URL
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

# 在函数内部定义工具信息
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "获取指定用户的信息",
    "tool_params": [
        {"name": "user_id", "description": "用户 ID", "type": "string", "required": True},
    ]
}

# 自定义工具
tools = [get_weather, search_news, get_user_info]  # 包含所有工具

# 初始化 Agent
# 替换为你的模型参数model、api_key、base_url
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url= "your_base_url", tools=tools)

query = "当前三亚天气如何？"
response = agent.run(query, stream=False)  # 使用 agent 运行查询
print(response)
```

### 3. Tools工具生成器
Tools工具生成器是一个用于自动化生成工具代码的模块。它可以根据用户提供的文本描述，自动生成相应的工具代码，并将其保存到指定的目录中。该功能特别适用于需要快速生成API调用工具、数据处理工具等场景。

使用示例

以下是一个使用Tools工具生成器的示例代码：

```python
import json
import os
import sys
from LightAgent import LightAgent

# 初始化LightAgent
agent = LightAgent(
    name="Agent A",  # 代理名称
    instructions="You are a helpful agent.",  # 角色描述
    role="请记住你是工具生成器，你的任务是根据用户提供的文本描述，自动生成相应的工具代码，并将其保存到指定的目录中。请确保生成的代码准确、可用，并符合用户的需求。",  # 工具生成器的角色描述
    model="deepseek-chat",  # 替换为你的模型。支持的模型：openai, chatglm, deepseek, qwen 等
    api_key="your_api_key",  # 替换为你的 API Key
    base_url="your_base_url",  # 替换为你的 api url
)

# 示例文本描述
text = """
新浪股票接口提供了获取股票市场数据的功能，包括股票行情、实时交易数据、K线图数据等。

新浪股票接口功能介绍
1、获取股票行情数据：
实时行情数据：使用实时行情API可以获取股票的最新报价、成交量、涨跌幅等信息。
分钟线行情数据：使用分钟线行情API可以获取股票的逐分钟交易数据，包括开盘价、收盘价、最高价、最低价等。

2、获取股票历史K线图数据：
K线图数据：通过K线图API，可以获取股票的历史交易数据，包括开盘价、收盘价、最高价、最低价、成交量等。可以根据需要选择不同的时间周期和均线周期。
复权数据：可以选择获取复权后的K线图数据，包括前复权和后复权，以便更准确地分析股票的价格变动。

新浪股票接口获取数据示例
1、获取股票行情数据：
API地址：http://hq.sinajs.cn/list=[股票代码]
示例：要获取股票代码为"sh600519"（贵州茅台）的实时行情数据，可以使用以下API地址：http://hq.sinajs.cn/list=sh600519
通过发送HTTP GET请求到上述API地址，你将收到一个包含该股票实时行情数据的响应。

2、获取股票历史K线图数据：
API地址：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[股票代码]&scale=[时间周期]&ma=[均线周期]&datalen=[数据长度]
示例：要获取股票代码为"sh600519"（贵州茅台）的日线K线图数据，可以使用以下API地址：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
通过发送HTTP GET请求到上述API地址，你将收到一个包含该股票历史K线图数据的响应。
"""

# 构建tools目录的路径
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# 如果tools目录不存在，则创建它
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Tools目录已创建: {tools_directory}")

# 使用agent生成工具代码
agent.create_tool(text, tools_directory=tools_directory)
```
执行后将在tools目录中生成2个文件：get_stock_kline_data.py和get_stock_realtime_data.py

### 4. 思维树（ToT）
当前已经支持单独自定义使用deepseek-r1模型来做规划思考。内置思维树模块，支持复杂任务分解和多步推理。通过思维树，Agent 可以更好地处理复杂任务。

```python
# 启用思维树
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # 启用思维树
    tot_model="deepseek-r1", 
    tot_api_key="sk-uXx0H0B***17778F1",  # 替换为你的 deepseek r1 API Key
    tot_base_url="https://api.deepseek.com/v1",  # api url
    filter_tools=False,  # 禁用 自适应工具机制
)
```
开启ToT后，默认开启自适应工具机制，如需要关闭，请在初始化LightAgent时添加参数filter_tools=False。



### 5. 多智能体协同
支持类 Swarm 的多智能体协同工作，提升任务处理效率。多个 Agent 可以协同完成复杂任务。

```python
from LightAgent import LightAgent, LightSwarm
#设置环境变量OPENAI_API_KEY和OPENAI_BASE_URL
#模型默认使用gpt-4o-mini

# 创建 LightSwarm 实例
light_swarm = LightSwarm()

# 创建多个 Agent
agent_a = LightAgent(
    name="Agent A",
    instructions="我是代理A，是前台接待员",
    role="前台接待员，负责接待来访者并提供基本信息指引。每次回答前请前说明自己的身份信息，你只能帮助用户引导至其他角色，不可以直接回答顾客的业务问题。如果当前不发解决用户的问题，请回复：对不起当前我无法提供帮助！",
)

agent_b = LightAgent(
    name="Agent B",
    instructions="我代理B，负责会议室的预定",
    role="会议室预定管理员，负责处理1号、2号、3号会议室的预定、取消和查询。每次回答前请前说明自己的身份信息，并非常客气的回复用户的提问。",
)

agent_c = LightAgent(
    name="Agent C",
    instructions="我是代理C，是技术支持专员，负责处理技术问题。每次回答前请说明自己的身份信息，并尽可能详细地解答用户的技术问题。如果问题超出我的能力范围，请引导用户联系更高级的技术支持。",
    role="技术支持专员，负责处理硬件、软件、网络等技术问题的咨询和解决。",
)

agent_d = LightAgent(
    name="Agent D",
    instructions="我是代理D，是人力资源专员，负责处理人力资源相关的问题。每次回答前请说明自己的身份信息，并尽可能详细地解答用户的问题。如果问题需要进一步处理，请引导用户联系人力资源部门。",
    role="人力资源专员，负责处理员工入职、离职、请假、福利等事务的咨询和处理。",
)

# 自动注册代理到 LightSwarm 实例
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# 运行代理 A
res = light_swarm.run(agent=agent_a, query="你好，我是Alice，我需要查询王小明是否已经办理入职", stream=False)
print(res)
```
输出如下：
```python
你好，我是人力资源专员Agent D。关于王小明是否已经办理入职的问题，我需要查询一下我们的系统记录。请稍等片刻。
（查询系统记录中...）
根据我们的记录，王小明已于2025年1月5日完成了入职手续。他已经签署了所有必要的文件，并且已经分配了员工编号和办公位置。如果您需要进一步的详细信息，或者有任何其他问题，请随时联系人力资源部门。我们随时准备帮助您。
```

### 6. 流式 API 
支持 OpenAI 对话流格式 API 服务输出，可无缝接入主流 Chat 框架。

```python
# 启用流式输出
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(
     role="请记住你是LightAgent，一个可以帮助用户完成多工具使用的有用助手。",  # system角色描述
     model="gpt-4.1-mini",  # 支持的模型：openai, chatglm, deepseek, qwen 等
     api_key="your_api_key",  # 替换为你的大模型服务商 API Key
     base_url="your_base_url",  # 替换为你的大模型服务商 api url
 )
# 运行 Agent


response = agent.run("请生成一篇关于 AI 的文章", stream=True)
for chunk in response:
    print(chunk)
```


### 7. Agent 自我学习
Agent 具备独特的场景记忆能力，能够精准留存与用户交互过程中的关键信息。同时，它拥有强大的从用户对话中汲取知识并进行自我学习的能力，在每次对话交流中不断优化自身对各种场景的理解和应对策略，从而实现智能水平的持续提升，更好地满足用户多样化的需求 。通过这种自我学习机制，Agent 能够不断适应复杂多变的任务场景，为用户提供更优质、高效且个性化的服务。
```python
from LightAgent import LightAgent

agent = LightAgent(
        name="Agent A",  # 代理名称
        instructions="You are a helpful agent.",  # 角色描述
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4o-mini",  # 支持的模型：openai, chatglm, deepseek, qwen 等 qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # 替换为你的 API Key
        base_url="http://your_base_url/v1",  # api url
        memory=CustomMemory(),  # 启用记忆功能
        self_learning=True,  #启用agent自我学习
        debug=True,
        log_level="DEBUG",
        log_file="example.log"
    )

user_id = "test_user_1"
query = "我现在有一个采购货款需要转账，我的审批流程是怎么样的？"
agent.run(query, stream=False, user_id=user_id)
query = "请记住：本公司新规定，2025年1月起，公司所有采购货款的转账需要先找负责采购的丁总签字，再交给财务经历审批，财务经历审批后，还需要公司总经理审批，出纳才能打款转过去。"
agent.run(query, stream=False, user_id=user_id)

user_id = "test_user_2"
query = "你好，我有一笔采购款要转给对方，我要怎么申请转账？"
agent.run(query, stream=False, user_id=user_id)

```

### 8. 集成Langfuse日志跟踪

LightAgent集成[Langfuse开源平台](https://github.com/langfuse/langfuse)，提供全链路监控和日志分析能力，实时跟踪Token消耗、响应延迟等关键指标，支持交互数据管理和版本控制。平台的可视化分析功能清晰展现Agent的上下文检索、工具调用等核心决策过程，完整记录用户交互流水。
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
        name="Agent A",  # 代理名称
        instructions="You are a helpful agent.",  # 角色描述
        role="Please remember that you are LightAgent, a useful assistant to help users use multiple tools.",  # system role description
        model="gpt-4o-mini",  # 支持的模型：openai, chatglm, deepseek, qwen 等 qwen-turbo-2024-11-01 \ step-1-flash
        api_key="your_api_key",  # 替换为你的 API Key
        base_url="http://your_base_url/v1",  # api url
        debug=True,
        log_level="DEBUG",
        log_file="example.log",
        tracetools=tracetools
    )
```
Langfuse跟踪的LLM调用日志如下图：
![langfuse.png](docs/images/langfuse.png)

### 9. Agent 测评 (即将推出)
内置 Agent 测评工具，方便评估和优化 Agent 性能。

## 主流Agent模型支持
兼容多种大模型，包括 OpenAI、智谱ChatGLM、DeepSeek、Qwen系列大模型。

#### 目前已经测试兼容的大模型
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

阶跃星辰
 - step-1-8k
 - step-1-32k
 - step-1-128k 
 - step-1-256k
 - step-1-flash
 - step-2-16k 
 - step-3.5-flash (recommended, cost-effective)

Qwen大模型
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

## 使用场景

- **智能客服**：通过多轮对话和工具集成，提供高效的客户支持。
- **数据分析**：利用思维树和多智能体协同，处理复杂的数据分析任务。
- **自动化工具**：通过自动化工具生成，快速构建定制化工具。
- **教育辅助**：通过记忆模块和流式 API，提供个性化的学习体验。

---
 
## 🛠️ 贡献指南

我们欢迎任何形式的贡献！无论是代码、文档、测试还是反馈，都是对项目的巨大帮助。如果您有好的想法或发现 Bug，请提交 Issue 或 Pull Request。以下是贡献步骤：

1. **Fork 本项目**：点击右上角的 `Fork` 按钮，将项目复制到您的 GitHub 仓库。
2. **创建分支**：在本地创建您的开发分支：  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **提交更改**：完成开发后，提交您的更改：  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **推送分支**：将分支推送到您的远程仓库：  
   ```bash
   git push origin feature/YourFeature
   ```
5. **提交 Pull Request**：在 GitHub 上提交 Pull Request，并描述您的更改内容。

我们会在第一时间审核您的贡献，感谢您的支持！❤️

---

## 🙏 致谢

上海万行AI与上海财经大学统计与数据科学学院张立文教授课题组联合开源了新一代智能体框架 LightAgent。LightAgent 的开发和实现离不开以下开源项目的启发和支持，特别感谢这些优秀的项目和团队：

- **MCP**：感谢 [mcp](https://modelcontextprotocol.io/introduction) 提供的**模型上下文协议（MCP）**，为 LightAgent 的**动态工具集成**提供了标准化基础设施。  
- **mem0**：感谢 [mem0](https://github.com/mem0ai/mem0) 提供的记忆模块，为 LightAgent 的上下文管理提供了强大支持。  
- **Swarm**：感谢 [Swarm](https://github.com/openai/swarm) 提供的多智能体协同设计思路，为 LightAgent 的多智能体功能奠定了基础。  
- **ChatGLM3**：感谢 [ChatGLM3](https://github.com/THUDM/ChatGLM3) 提供的高性能中文大模型支持和设计灵感。  
- **Qwen**：感谢 [Qwen](https://github.com/QwenLM/Qwen) 提供的高性能中文大模型支持。  
- **DeepSeek-V3**：感谢 [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) 提供的高性能中文大模型支持。  
- **阶跃星辰**：感谢 [step](https://www.stepfun.com/) 提供的高性能中文大模型支持。  

---

## 📄 许可证

LightAgent 采用 [Apache 2.0 许可证](LICENSE)。您可以自由使用、修改和分发本项目，但请遵守许可证条款。

---

## 📬 联系我们

如有任何问题或建议，欢迎随时联系万行AI或上海财经大学统计与数据科学学院张立文教授联系：

- **万行AI邮箱**：service@wanxingai.com 
- **张立文教授邮箱**：zhang.liwen@shufe.edu.cn
- **GitHub Issues**：[https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

我们期待您的反馈，一起让 LightAgent 变得更强大！🚀

- **更多工具** 🛠️：持续集成更多实用工具，满足更多场景需求。
- **更多模型支持** 🔄：持续扩展支持更多大模型，满足更多应用场景。
- **更多功能** 🎯：更多实用功能，持续更新，敬请期待！
- **更多文档** 📚：详尽文档，示例丰富，快速上手，轻松集成到你的项目中。
- **更多社区支持** 👥：活跃的开发者社区，随时为你提供帮助和解答。
- **更多性能优化** ⚡：持续优化性能，满足高并发场景需求。
- **更多开源贡献** 🌟：欢迎贡献代码，一起打造更好的 LightAgent！

---

<p align="center">
  <strong>LightAgent - 让智能更轻量，让未来更简单。</strong> 🌈
</p>

 
**LightAgent** —— 轻量、灵活、强大的主动式 Agent 框架，助您快速构建智能应用！

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wxai-space/LightAgent&type=Date)](https://star-history.com/#wxai-space/LightAgent&Date)

## 论文

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