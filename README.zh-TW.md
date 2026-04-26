
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
    繁體中文 | 
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
  <h1>LightAgent🚀（下一代Agentic AI框架）</h1>
</div>

**LightAgent** 是一個極其輕量的帶記憶（`mem0`）、工具（`Tools`）、思維樹（`ToT`）的主動式 Agentic Framework（自主性框架），並且完全開源。它支持比Openai Swarm更簡單的多智能體協同，簡單一步即可構建具備自我學習能力的agent，並支持stdio和sse方式接入MCP協議。底層模型支持 OpenAI、智譜 ChatGLM、DeepSeek、階躍星辰、Qwen通義千問大模型等。同時，LightAgent 支持 OpenAI 流格式 API 服務輸出，無縫接入各大主流 Chat 框架。🌟

---

## ✨ 特性

- **輕量高效** 🚀：極簡設計，快速部署，適合各種規模的應用場景。（No LangChain, No LlamaIndex）100% Python 實現，無需額外依賴，核心代碼僅1000行，完全開源。 
- **記憶支持** 🧠：支持為每個用戶自定義長期記憶，原生支持 `mem0` 記憶模塊，實現對話過程中自動管理用戶個性化記憶，讓 Agent 更智能。
- **自主學習** 📚️：每個 agent 擁有自主學習能力，並且擁有權限的管理員可以管理每個 agent。
- **工具集成** 🛠️：支持自定義工具（`Tools`），自動化工具生成，靈活擴展，滿足多樣化需求。  
- **複雜目標** 🌳：內置帶反思的思維樹（ToT）模塊，支持複雜任務分解和多步推理，提升任務處理能力。  
- **多智能體協同** 🤖：比Swarm更簡單實現的多智能體協同工作，內置LightSwarm實現意圖判斷和任務轉移功能，能夠更智能地處理用戶輸入，並根據需要將任務轉移給其他代理。 
- **獨立執行** 🤖：無人為干預自主完成任務工具調用。  
- **多模型支持** 🔄：兼容 OpenAI、智譜 ChatGLM、百川大模型、StepFun、DeepSeek、Qwen 系列大模型。  
- **流式 API** 🌊：支持 OpenAI 流格式 API 服務輸出，無縫接入主流 Chat 框架，提升用戶體驗。  
- **Tools工具生成器** 🚀：只需將您的 API 文檔交給[Tools工具生成器]，它將自動化地為您打造專屬的 tools，助您在短短1小時內快速構建數百個個性化的自定義工具，提高效率，釋放您的創新潛能。
- **agent 自我學習** 🧠️：每個 agent 擁有自己的場景記憶能力，擁有從用戶的對話中進行自我學習能力。
- **自適應 tools 機制** 🛠️：支持添加無限量 tools，在上萬個工具中讓大模型先選取候選工具集合，過濾無關工具後再提交上下文給大模型，可大幅度降低 Token 消耗。


## 🚧 即將推出

- **智能體協同通訊** 🛠️：智能體之間還可以共享資訊和傳遞消息，實現複雜的信息通訊和任務協同。
- **Agent 測評** 📊：內置 Agent 測評工具，方便評估和優化您構建的 Agent，對齊業務場景，持續提升智能水平。  


## 內置 “思考流”
（Thought Flow）方法通過系統性、結構化和靈活的思維過程，能夠有效應對複雜場景中的挑戰。
以下是具體實施步驟：
```text
問題定義：明確核心問題和目標。

信息收集：系統地收集相關信息和數據。

分解問題：將複雜問題分解為多個子問題或模塊。

多維度分析：從不同角度和層面分析每個子問題。

建立關聯：識別子問題之間的關聯和依賴關係。

生成解決方案：針對每個子問題提出可能的解決方案。

評估與選擇：評估各解決方案的可行性和影響，選擇最優方案。

實施與反饋：實施選定方案，並根據反饋進行調整。
```

---
## 🌟 為什麼選擇 LightAgent？

- **開源免費** 💖：完全開源，社區驅動，持續更新，歡迎貢獻！  
- **易於上手** 🎯：文檔詳盡，示例豐富，快速上手，輕鬆集成到您的項目中。  
- **社區支持** 👥：活躍的開發者社區，隨時為您提供幫助和解答。  
- **高性能** ⚡：優化設計，高效運行，滿足高並發場景需求。  

---

## 🛠️ 快速開始

### 安裝 LightAgent 最新版本

```bash
pip install lightagent
```

（可選安裝）通過 pip 安裝 Mem0 包：

```bash
pip install mem0ai
```

或者，您可以通過一鍵點擊在托管平台上使用 Mem0，[點擊這裡](https://www.mem0.ai/)。


### Hello world 示例代碼

```python
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url= "your_base_url")

# 運行 Agent
response = agent.run("你好，你是誰？")
print(response)
```

### 透過 system 提示詞設定模型自我認知

```python
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(
     role="請記住你是 LightAgent，一個可以幫助用戶完成多工具使用的有用助手。",  # system 角色描述
     model="deepseek-chat",  # 支持的模型：openai, chatglm, deepseek, qwen 等
     api_key="your_api_key",  # 替換為你的大模型服務商 API Key
     base_url="your_base_url",  # 替換為你的大模型服務商 api url
 )
# 運行 Agent
response = agent.run("請問你是誰？")
print(response)
```

### 使用工具示例代碼

```python
from LightAgent import LightAgent


# 定義工具
def get_weather(city_name: str) -> str:
    """
    獲取 `city_name` 的當前天氣
    """
    return f"查詢結果: {city_name} 天氣晴"
# 在函數內部定義工具信息
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "獲取指定城市的當前天氣信息",
    "tool_params": [
        {"name": "city_name", "description": "要查詢的城市名稱", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# 初始化 Agent
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# 運行 Agent
response = agent.run("請幫我查詢一下上海的天氣情況")
print(response)
```
支持自定義無限數量的工具。

多個工具示例： tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## 功能詳解

### 1. 可拆卸的全自動記憶模塊（`mem0`）
LightAgent 支持外部擴展 `mem0` 記憶模塊，全自動進行上下文記憶和歷史記錄管理，無需開發人員手動觸發添加記憶和記憶查找。通過記憶模塊，Agent 可以在多輪對話中保持上下文一致性。

```python
# 啟用記憶模塊

# 或者使用自定義記憶模塊，下面以 mem0 為例 https://github.com/mem0ai/mem0/
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
        # mem0中如需使用qdrant作為向量數據庫存儲記憶，請將config改為下面代碼
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
        """存儲記憶開發者可以自行修改存儲方法的內部實現，當前示例為mem0的添加記憶方法"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """檢索相關記憶開發者可以自行修改檢索方法的內部實現，當前示例為mem0的查找記憶方法"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="請記住你是 LightAgent，一個可以幫助用戶完成多工具使用的有用助手。",  # system 角色描述
        model="deepseek-chat",  # 支持的模型：openai, chatglm, deepseek, qwen 等
        api_key="your_api_key",  # 替換為你的大模型服務商 API Key
        base_url="your_base_url",  # 替換為你的大模型服務商 api url
        memory=CustomMemory(),  # 啟用記憶功能
        tree_of_thought=False,  # 啟用思維鏈
    )

# 帶記憶的測試 & 如果需要添加工具可以自行添加tools到agent來實現帶記憶的工具調用

user_id = "user_01"
logger.info("\n=========== next conversation ===========")
query = "介紹下三亞的有什麼好玩的景點，身邊很多朋友都去三亞旅遊了，我也想去玩"
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== next conversation ===========")
query = "我想去哪裡旅遊呢？"
print(agent.run(query, stream=False, user_id=user_id))
```

輸出如下：
```python
=========== next conversation ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
開始思考問題: 介紹下三亞的有什麼好玩的景點，身邊很多朋友都去三亞旅遊了，我也想去玩
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Final Reply: 
三亞是中國海南省的一個熱門旅遊城市，以其美麗的海灘、熱帶氣候和豐富的旅遊資源而聞名。以下是一些三亞值得一遊的景點：

1. **亞龍灣**：被譽為“東方夏威夷”，擁有綿長的沙灘和清澈的海水，是游泳、潛水和日光浴的理想之地。

2. **天涯海角**：這是一個著名的文化景觀，以其壯麗的海景和浪漫的傳說而吸引遊客。這裡的巨石上刻有“天涯”和“海角”字樣，象徵著永恆的愛情。

3. **南山文化旅遊區**：這裡有一個高達108米的南山海上觀音像，是世界上最高的海上觀音像。遊客可以在這裡體驗佛教文化，參觀寺廟和園林。

4. **蜈支洲島**：這是一個小島，以其原始的自然風光和豐富的水上活動而聞名。遊客可以在這裡進行潛水、浮潛、海釣等活動。

5. **大東海**：這是三亞市區內的一個海灘，以其便利的交通和豐富的夜生活而受到遊客的喜愛。

6. **三亞灣**：這是一個長達22公里的海灘，是觀賞日落的好地方。這裡的海灘較為安靜，適合喜歡寧靜的遊客。

7. **呀諾達雨林文化旅遊區**：這是一個熱帶雨林公園，遊客可以在這裡體驗熱帶雨林的自然風光，參與各種探險活動。

8. **鹿回頭公園**：這是一個位於山頂的公園，可以俯瞰整個三亞市區和三亞灣的美景。這裡還有一個關於鹿的美麗傳說。

9. **西島**：這是一個相對較為原始的小島，以其寧靜的海灘和豐富的海洋生物而吸引遊客。

10. **三亞千古情**：這是一個大型的文化主題公園，通過表演和展覽展示海南的歷史和文化。

除了上述景點，三亞還有許多其他值得探索的地方，如熱帶植物園、海鮮市場等。三亞的美食也不容錯過，尤其是新鮮的海鮮和熱帶水果。在規劃旅行時，建議提前查看天氣預報和景點開放時間，以確保有一個愉快的旅行體驗。
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== next conversation ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
開始思考問題: 我想去哪裡旅遊呢？
發現相關記憶:
用戶想去旅遊三亞
用戶的朋友已經去過三亞。
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Final Reply: 
根據用戶之前提到的信息，用戶的朋友已經去過三亞（Sanya），而用戶自己也表達了對三亞的興趣。因此，三亞可能是一個適合用戶的旅遊目的地。以下是一些關於三亞的旅遊信息，供用戶參考：

### 三亞旅遊推薦：
1. **亞龍灣**：被譽為“東方夏威夷”，擁有美麗的海灘和清澈的海水，適合游泳和日光浴。
2. **天涯海角**：三亞的標誌性景點，以其獨特的岩石和浪漫的傳說吸引遊客。
3. **南山文化旅遊區**：這裡有著名的南山寺和108米高的海上觀音像，是佛教文化的重要景點。
4. **蜈支洲島**：適合潛水和海上運動，島上有豐富的海洋生物和珊瑚礁。
5. **大東海**：三亞市區內的海灘，交通便利，適合家庭和情侶遊玩。

### 其他推薦：
如果用戶對三亞已經有所了解，或者想要探索其他目的地，以下是一些其他熱門旅遊地：
1. **桂林**：以其獨特的喀斯特地貌和漓江風光聞名。
2. **麗江**：古城和玉龍雪山是其主要景點，適合喜歡歷史文化和自然風光的遊客。
3. **張家界**：以其奇特的石柱和自然景觀著稱，是《阿凡達》電影的取景地之一。

用戶可以根據自己的興趣和時間安排選擇合適的旅遊目的地。如果用戶需要更詳細的信息或幫助規劃行程，請隨時告知！
```

### 2. 工具集成（無限擴展的自定義工具支持）
擁抱個性化工具定製（`Tools`），並通過 `tools` 方法輕鬆集成您的專屬工具。這些工具可以是任何 Python 函數，並且支持參數類型註解，以確保靈活性和精確性。此外，我們還提供智能 AI 驅動的工具生成器，助力您自動化構建工具，釋放創造力。

```python

import requests
from LightAgent import LightAgent

# 定義工具
def get_weather(
        city_name: str
) -> str:
    """
    獲取城市天氣信息
    :param city_name: 城市名稱
    :return: 天氣信息
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
# 在函數內部定義工具信息
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "獲取指定城市的當前天氣信息",
    "tool_params": [
        {"name": "city_name", "description": "要查詢的城市名稱", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    根據關鍵詞搜索新聞
    :param keyword: 搜索關鍵詞
    :param max_results: 返回的最大結果數量，默認為 5
    :return: 新聞搜索結果
    """
    results = f"通過搜索{keyword}, 我找到{max_results}條相關信息"
    return str(results)

# 在函數內部定義工具信息
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "根據關鍵詞搜索新聞",
    "tool_params": [
        {"name": "keyword", "description": "搜索關鍵詞", "type": "string", "required": True},
        {"name": "max_results", "description": "返回的最大結果數量", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    獲取用戶信息
    :param user_id: 用戶 ID
    :return: 用戶信息
    """
    if not isinstance(user_id, str):
        raise TypeError("User ID must be a string")

    try:
        # 假設使用一個用戶信息 API，這裡用示例 URL
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

# 在函數內部定義工具信息
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "獲取指定用戶的信息",
    "tool_params": [
        {"name": "user_id", "description": "用戶 ID", "type": "string", "required": True},
    ]
}

# 自定義工具
tools = [get_weather, search_news, get_user_info]  # 包含所有工具

# 初始化 Agent
# 替換為你的模型參數model、api_key、base_url
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

query = "當前三亞天氣如何？"
response = agent.run(query, stream=False)  # 使用 agent 運行查詢
print(response)
```

### 3. Tools 工具生成器
Tools 工具生成器是一個用於自動化生成工具代碼的模塊。它可以根據用戶提供的文本描述，自動生成相應的工具代碼，並將其保存到指定的目錄中。該功能特別適用於需要快速生成 API 調用工具、數據處理工具等場景。

使用示例

以下是一個使用 Tools 工具生成器的示例代碼：

```python
import json
import os
import sys
from LightAgent import LightAgent

# 初始化 LightAgent
agent = LightAgent(
    name="Agent A",  # 代理名稱
    instructions="You are a helpful agent.",  # 角色描述
    role="請記住你是工具生成器，你的任務是根據用戶提供的文本描述，自動生成相應的工具代碼，並將其保存到指定的目錄中。請確保生成的代碼準確、可用，並符合用戶的需求。",  # 工具生成器的角色描述
    model="deepseek-chat",  # 替換為你的模型。支持的模型：openai, chatglm, deepseek, qwen 等
    api_key="your_api_key",  # 替換為你的 API Key
    base_url="your_base_url",  # 替換為你的 api url
)

# 示例文本描述
text = """
新浪股票接口提供了獲取股票市場數據的功能，包括股票行情、即時交易數據、K線圖數據等。

新浪股票接口功能介紹
1、獲取股票行情數據：
即時行情數據：使用即時行情 API 可以獲取股票的最新報價、成交量、漲跌幅等信息。
分鐘線行情數據：使用分鐘線行情 API 可以獲取股票的逐分鐘交易數據，包括開盤價、收盤價、最高價、最低價等。

2、獲取股票歷史 K 線圖數據：
K 線圖數據：通過 K 線圖 API，可以獲取股票的歷史交易數據，包括開盤價、收盤價、最高價、最低價、成交量等。可以根據需要選擇不同的時間周期和均線周期。
復權數據：可以選擇獲取復權後的 K 線圖數據，包括前復權和後復權，以便更準確地分析股票的價格變動。

新浪股票接口獲取數據示例
1、獲取股票行情數據：
API 地址：http://hq.sinajs.cn/list=[股票代碼]
示例：要獲取股票代碼為"sh600519"（貴州茅台）的即時行情數據，可以使用以下 API 地址：http://hq.sinajs.cn/list=sh600519
通過發送 HTTP GET 請求到上述 API 地址，您將收到一個包含該股票即時行情數據的響應。

2、獲取股票歷史 K 線圖數據：
API 地址：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[股票代碼]&scale=[時間周期]&ma=[均線周期]&datalen=[數據長度]
示例：要獲取股票代碼為"sh600519"（貴州茅台）的日線 K 線圖數據，可以使用以下 API 地址：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
通過發送 HTTP GET 請求到上述 API 地址，您將收到一個包含該股票歷史 K 線圖數據的響應。
"""

# 構建 tools 目錄的路徑
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# 如果 tools 目錄不存在，則創建它
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Tools 目錄已創建: {tools_directory}")

# 使用 agent 生成工具代碼
agent.create_tool(text, tools_directory=tools_directory)
```
執行後將在 tools 目錄中生成 2 個文件：get_stock_kline_data.py 和 get_stock_realtime_data.py

### 4. 思維樹（ToT）
內置思維樹模塊，支持複雜任務分解和多步推理。通過思維樹，Agent 可以更好地處理複雜任務。

```python
# 啟用思維樹
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # 啟用思維樹
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # 替換為你的 deepseek r1 API Key
    tot_base_url="https://api.openai.com/v1",  # api url
    filter_tools=False,  # 禁用 自適應工具機制
)
```
開啟ToT後，默認開啟自適應工具機制，如需要關閉，請在初始化LightAgent時添加參數filter_tools=False。

### 5. 多智能體協同
支持類 Swarm 的多智能體協同工作，提升任務處理效率。多個 Agent 可以協同完成複雜任務。

```python
from LightAgent import LightAgent, LightSwarm
#設置環境變量 OPENAI_API_KEY 和 OPENAI_BASE_URL
#模型默認使用 gpt-4o-mini

# 創建 LightSwarm 實例
light_swarm = LightSwarm()

# 創建多個 Agent
agent_a = LightAgent(
    name="Agent A",
    instructions="我是代理A，是前台接待員",
    role="前台接待員，負責接待來訪者並提供基本信息指引。每次回答前請前說明自己的身份信息，你只能幫助用戶引導至其他角色，不可以直接回答顧客的業務問題。如果當前不發解決用戶的問題，請回復：對不起當前我無法提供幫助！",
)

agent_b = LightAgent(
    name="Agent B",
    instructions="我代理B，負責會議室的預定",
    role="會議室預定管理員，負責處理1號、2號、3號會議室的預定、取消和查詢。每次回答前請前說明自己的身份信息，並非常客氣地回復用戶的提問。",
)

agent_c = LightAgent(
    name="Agent C",
    instructions="我是代理C，是技術支持專員，負責處理技術問題。每次回答前請說明自己的身份信息，並盡可能詳細地解答用戶的技術問題。如果問題超出我的能力範圍，請引導用戶聯系更高級的技術支持。",
    role="技術支持專員，負責處理硬體、軟體、網絡等技術問題的諮詢和解決。",
)

agent_d = LightAgent(
    name="Agent D",
    instructions="我是代理D，是人力資源專員，負責處理人力資源相關的問題。每次回答前請說明自己的身份信息，並盡可能詳細地解答用戶的問題。如果問題需要進一步處理，請引導用戶聯系人力資源部門。",
    role="人力資源專員，負責處理員工入職、離職、請假、福利等事務的諮詢和處理。",
)

# 自動註冊代理到 LightSwarm 實例
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# 運行代理 A
res = light_swarm.run(agent=agent_a, query="你好，我是 Alice，我需要查詢王小明是否已經辦理入職", stream=False)
print(res)
```
輸出如下：
```python
你好，我是人力資源專員 Agent D。關於王小明是否已經辦理入職的問題，我需要查詢一下我們的系統記錄。請稍等片刻。
（查詢系統記錄中...）
根據我們的記錄，王小明已於2025年1月5日完成了入職手續。他已經簽署了所有必要的文件，並且已經分配了員工編號和辦公位置。如果您需要進一步的詳細信息，或者有任何其他問題，請隨時聯系人力資源部門。我們隨時準備幫助您。
```

### 6. 流式 API 
支持 OpenAI 流格式 API 服務輸出，無縫接入主流 Chat 框架。

```python
# 啟用流式輸出
response = agent.run("請生成一篇關於 AI 的文章", stream=True)
for chunk in response:
    print(chunk)
```


### 7. Agent 測評 (即將推出)
內置 Agent 測評工具，方便評估和優化 Agent 性能。



## 主流 Agent 模型支持
兼容多種大模型，包括 OpenAI、智譜 ChatGLM、DeepSeek、Qwen 系列大模型。

#### 目前已經測試兼容的大模型
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

## 使用場景

- **智能客服**：通過多輪對話和工具集成，提供高效的客戶支持。
- **數據分析**：利用思維樹和多智能體協同，處理複雜的數據分析任務。
- **自動化工具**：通過自動化工具生成，快速構建定制化工具。
- **教育輔助**：通過記憶模塊和流式 API，提供個性化的學習體驗。

---
 
## 🛠️ 貢獻指南

我們歡迎任何形式的貢獻！無論是代碼、文檔、測試還是反饋，都是對項目的巨大幫助。如果您有好的想法或發現 Bug，請提交 Issue 或 Pull Request。以下是貢獻步驟：

1. **Fork 本項目**：點擊右上角的 `Fork` 按鈕，將項目複製到您的 GitHub 倉庫。
2. **創建分支**：在本地創建您的開發分支：  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **提交更改**：完成開發後，提交您的更改：  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **推送分支**：將分支推送到您的遠程倉庫：  
   ```bash
   git push origin feature/YourFeature
   ```
5. **提交 Pull Request**：在 GitHub 上提交 Pull Request，並描述您的更改內容。

我們會在第一時間審核您的貢獻，感謝您的支持！❤️

---

## 🙏 致謝

LightAgent 的開發和實現離不开以下開源項目的啟發和支持，特別感謝這些優秀的項目和團隊：

- **mem0**：感謝 [mem0](https://github.com/mem0ai/mem0) 提供的記憶模塊，為 LightAgent 的上下文管理提供了強大支持。  
- **Swarm**：感謝 [Swarm](https://github.com/openai/swarm) 提供的多智能體協同設計思路，為 LightAgent 的多智能體功能奠定了基礎。  
- **ChatGLM3**：感謝 [ChatGLM3](https://github.com/THUDM/ChatGLM3) 提供的高性能中文大模型支持和設計靈感。  
- **Qwen**：感謝 [Qwen](https://github.com/QwenLM/Qwen) 提供的高性能中文大模型支持。  
- **DeepSeek-V3**：感謝 [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) 提供的高性能中文大模型支持。  
- **StepFun**：感謝 [step](https://www.stepfun.com/) 提供的高性能中文大模型支持。  

---

## 📄 許可證

LightAgent 采用 [Apache 2.0 許可證](LICENSE)。您可以自由使用、修改和分發本項目，但請遵守許可證條款。

---

## 📬 聯繫我們

如有任何問題或建議，歡迎隨時聯繫我們：

- **郵箱**：service@wanxingai.com  
- **GitHub Issues**：[https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

我們期待您的反饋，一起讓 LightAgent 變得更強大！🚀

- **更多工具** 🛠️：持續集成更多實用工具，滿足更多場景需求。
- **更多模型支持** 🔄：持續擴展支持更多大模型，滿足更多應用場景。
- **更多功能** 🎯：更多實用功能，持續更新，敬請期待！
- **更多文檔** 📚：詳盡文檔，示例豐富，快速上手，輕鬆集成到你的項目中。
- **更多社區支持** 👥：活躍的開發者社區，隨時為你提供幫助和解答。
- **更多性能優化** ⚡：持續優化性能，滿足高並發場景需求。
- **更多開源貢獻** 🌟：歡迎貢獻代碼，一起打造更好的 LightAgent！

---

<p align="center">
  <strong>LightAgent - 讓智能更輕量，讓未來更簡單。</strong> 🌈
</p>

 
**LightAgent** —— 輕量、靈活、強大的主動式 Agent 框架，助您快速構建智能應用！