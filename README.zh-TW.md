
![LightAgent Banner](docs/images/lightagent-banner.jpg)
<div align="center">
  <p>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://github.com/wanxingai/LightAgent/releases"><img src="https://img.shields.io/github/release/wanxingai/LightAgent.svg" alt="GitHub release"></a>
    <a href="https://github.com/wanxingai/LightAgent/issues"><img src="https://img.shields.io/github/issues/wanxingai/LightAgent.svg" alt="GitHub issues"></a>
    <a href="https://github.com/wanxingai/LightAgent/stargazers"><img src="https://img.shields.io/github/stars/wanxingai/LightAgent.svg" alt="GitHub stars"></a>
    <a href="https://github.com/wanxingai/LightAgent/network"><img src="https://img.shields.io/github/forks/wanxingai/LightAgent.svg" alt="GitHub forks"></a>
    <a href="https://github.com/wanxingai/LightAgent/graphs/contributors"><img src="https://img.shields.io/github/contributors/wanxingai/LightAgent.svg" alt="GitHub contributors"></a>
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

## 新聞
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0 開發版：新增可持久化 LightFlow checkpoint、resume/rerun、審批節點、更清楚的步驟狀態與 trace metadata，並補充 Guardrails 範本、MemoryPolicy 控制與 SharedMemoryPool 原型。
- **[2026-06-14]** LightAgent v0.8.1 開發版：新增 MemoryScope metadata 約定、MemoryPolicy 來源/範圍/可信度過濾，並說明 Trace、使用者記憶、自我反思記憶與 LightSwarm 委派狀態的邊界。
- **[2026-06-02]** LightAgent v0.8.0 開發版：新增 LightFlow 工作流程編排，支援確定性多步驟 Agent 執行、DAG 依賴、步驟輸出傳遞、重試與 flow trace 事件。

歷史版本說明請查看 [GitHub Releases](https://github.com/wanxingai/LightAgent/releases)。

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
- **工作流程編排** 🔁：LightFlow 將多個 Agent 編排為確定性多步驟工作流程，支援顯式依賴、步驟輸出、重試、checkpoint、resume/rerun、審批節點、fallback agent 與可追蹤執行。
- **共享記憶原型** 🧠：SharedMemoryPool 提供帶來源 metadata 與範圍檢索的追加式記憶，適合多 Agent 實驗。
- **Guardrails 範本** 🛡️：可重用的輸入、工具與輸出安全策略，可用於隱私攔截、敏感工具確認、高風險參數校驗與輸出脫敏。

## 🧭 架構速覽

| 層級 | 主要 API | 適用場景 |
| --- | --- | --- |
| 單 Agent 執行時 | `LightAgent` | 一個 Agent 的模型呼叫、工具、記憶、串流輸出、trace 和 guardrails。 |
| 多 Agent 路由 | `LightSwarm` | 在多個專業 Agent 之間進行角色化委派。 |
| 確定性工作流程 | `LightFlow` | DAG 工作流程、重試、checkpoint、審批、resume 和 rerun。 |
| 工具與整合 | `tools`、`ToolRegistry`、MCP | Python 工具、生成工具、執行時載入工具或 MCP 工具服務。 |
| 記憶邊界 | `MemoryPolicy`、`MemoryScope` | 租戶隔離、來源、可信度、過期和寫入准入控制。 |
| 共享記憶原型 | `SharedMemoryPool` | 多 Agent 共享記憶實驗。 |
| 安全控制 | `input_guardrails`、`tool_guardrails`、`output_guardrails` | 隱私攔截、敏感工具確認、高風險參數校驗和輸出脫敏。 |
| 可觀測性 | `trace=True`、`agent.export_trace()` | 結構化執行、模型、工具、錯誤和工作流程事件。 |

## 核心使用模式

LightAgent 保持預設呼叫路徑簡單，同時允許逐步加入生產級控制。

| 模式 | 最小呼叫 | 說明 |
| --- | --- | --- |
| 基礎回應 | `agent.run(query)` | 預設回傳字串。 |
| 串流輸出 | `agent.run(query, stream=True)` | 回傳 OpenAI 相容的串流 chunk。 |
| 結構化結果 | `agent.run(query, result_format="object")` | 回傳內容與結構化 metadata。 |
| Trace | `agent.run(query, trace=True)` | 記錄事件，不改變預設字串回傳。 |
| 使用者記憶 | `agent.run(query, user_id="alice")` | 使用設定的記憶後端與 MemoryPolicy。 |
| 工具 | `LightAgent(..., tools=[fn])` | 函式應提供 `tool_info` metadata。 |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | 為 Agent 加入輸入、工具與輸出策略。 |
| 工作流程 | `LightFlow().step(...).run(query)` | 用於確定性多步驟執行。 |

## 📋 文件

- 常見安裝、模型、工具、記憶、MCP、Skills、串流輸出與 LightSwarm 問題，請查看 [FAQ](docs/FAQ.md)。
- 確定性多步驟工作流程、checkpoint、resume/rerun、審批節點、fallback agent 與步驟狀態，請查看 [LightFlow](docs/lightflow.md)。
- 自訂工具、執行時工具、ToolRegistry、ToolLoader、AsyncToolDispatcher 與 MCP 工具整合，請查看 [Tools Guide](docs/tools.md)。
- 共享長期記憶或圖記憶部署，請查看 [Memory Security Guidance](docs/memory_security.md)。
- SharedMemoryPool 原型請查看 [SharedMemoryPool](docs/shared_memory_pool.md)。
- 記憶寫入准入、過期檢索與低品質寫入攔截，請查看 [Memory Admission And Mutation Controls](docs/memory_admission.md)。
- 輸入、工具與輸出安全策略，請查看 [Guardrails](docs/guardrails.md)。
- OpenRouter、本地模型與 OpenAI 相容設定，請查看 [Model Provider Configuration](docs/model_providers.md)。
- Trace 可觀測能力請查看 [Trace Observability](docs/tracing.md)。

## 🚧 即將推出

- **智能體協同通訊** 🛠️：智能體之間還可以共享資訊和傳遞消息，實現複雜的信息通訊和任務協同。
- **Agent 測評** 📊：內置 Agent 測評工具，方便評估和優化您構建的 Agent，對齊業務場景，持續提升智能水平。  


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

### 查看執行 Trace（v0.7.0）

Trace 預設關閉，需要顯式傳入 `trace=True`，不會改變原有 `agent.run()` 預設回傳字串的相容行為。

```python
from LightAgent import LightAgent

agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

result = agent.run("Hello, who are you?", result_format="object", trace=True)
print(result.content)
print(result.trace_id)
print(result.trace)

for event in agent.export_trace():
    print(event["type"], event["data"])
```

### Checkpoint 一個 LightFlow 執行（v0.9.0）

`LightFlow` 可以持久化 workflow checkpoint，並在失敗後從上次 checkpoint 繼續執行。

```python
from LightAgent import JsonLightFlowStore, LightAgent, LightFlow

research_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")
writer_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

store = JsonLightFlowStore(".lightflow_runs")
flow = (
    LightFlow(store=store)
    .step("research", agent=research_agent, timeout=30)
    .step("write", agent=writer_agent, depends_on=["research"], max_retry=2)
)

result = flow.run("Analyze this company", run_id="report-001", trace=True)

if not result.success:
    result = flow.resume("report-001")

print(result.status)
print(flow.get_run("report-001")["steps"])
```

### 使用 SharedMemoryPool（v0.9.0）

`SharedMemoryPool` 是面向多 Agent 共享記憶實驗的輕量記憶體原型。

```python
from LightAgent import LightAgent, MemoryPolicy, SharedMemoryPool

shared_memory = SharedMemoryPool(agent_name="writer")

agent = LightAgent(
    name="writer",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=shared_memory,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    ),
)

agent.run("Remember that I prefer concise reports.", user_id="alice")
print(shared_memory.list_records(user_id="tenant-a:alice"))
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

README 保留核心使用模型；更長的示例、適配器設定與生產實踐放在專門文件中。

### 1. 可拆卸記憶模組（`mem0`）
LightAgent 接受任何提供 `store(data, user_id)` 和 `retrieve(query, user_id)` 的記憶後端。使用 `user_id` 隔離對話；當記憶跨使用者、租戶、Agent 或 trace 共享時，應設定 `MemoryPolicy`。

### 2. 工具整合
使用帶 `tool_info` metadata 的 Python 函式向 Agent 暴露受控能力。進階執行時工具、ToolRegistry、ToolLoader、AsyncToolDispatcher 與 MCP 請查看 [Tools Guide](docs/tools.md)。

### 3. Tools 工具生成器
`agent.create_tool()` 可以根據 API 文件或自然語言描述生成工具程式碼。生成工具應放在可審查的 tools 目錄中，並在生產使用前測試。

### 4. 思維樹（ToT）
當任務需要顯式規劃、反思和多工具選擇時，啟用 `tree_of_thought=True`。

### 5. 多智能體協同
`LightSwarm` 用於在專業 Agent 之間進行角色化委派。保持每個 Agent 角色清楚，並用記憶策略約束跨 Agent 記憶寫入。

### 6. 串流 API
`agent.run(query, stream=True)` 回傳 OpenAI 相容串流 chunk，適合聊天 UI 與長輸出。

### 7. Agent 自我學習
自我學習應與記憶後端和 `MemoryPolicy` 配合使用，避免低品質、隱私、過期或無關內容進入長期記憶。

### 8. Trace 與 Langfuse
LightAgent 可透過內建 trace 或 Langfuse 設定觀察執行過程。

### 9. Agent 測評
Agent 測評將在後續版本中圍繞業務場景評估 Agent 行為。

### 10. LightFlow 工作流程
`LightFlow` 是確定性工作流程層，適合讓任務按已知步驟執行，而不是完全依賴自由形式規劃。

- 步驟狀態：`pending`、`running`、`success`、`failed`、`skipped`、`waiting_approval`。
- DAG 校驗：`flow.validate(strict=True)`。
- 步驟控制：`timeout`、`max_retry`、`cancel_if`、`fallback_agent`、`requires_approval`、`approval_handler`。
- 持久化與恢復：`JsonLightFlowStore`、`flow.resume(run_id)`、`flow.rerun_step(run_id, step_name)`、`flow.get_run(run_id)`、`flow.list_runs()`。

請查看 [LightFlow](docs/lightflow.md)。

### 11. Guardrails
Guardrails 是圍繞 Agent 執行的輕量策略鉤子：輸入策略檢查使用者問題，工具策略檢查工具呼叫，輸出策略檢查或脫敏最終輸出。

```python
from LightAgent import (
    LightAgent,
    high_risk_parameter_guardrail,
    output_redaction_guardrail,
    privacy_input_guardrail,
    sensitive_tool_confirmation_guardrail,
)

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    input_guardrails=[privacy_input_guardrail()],
    tool_guardrails=[
        sensitive_tool_confirmation_guardrail(["transfer_money"], approved=False),
        high_risk_parameter_guardrail({"amount": lambda value: float(value) <= 1000}),
    ],
    output_guardrails=[output_redaction_guardrail()],
)
```

請查看 [Guardrails](docs/guardrails.md)。

### 12. SharedMemoryPool
`SharedMemoryPool` 是多 Agent 共享記憶實驗的記憶體原型，建議與 `MemoryPolicy` 配合控制 namespace、source、scope、trust、confidence 和 agent name。

## 主流 Agent 模型支持

LightAgent 相容 OpenAI 風格 chat completion endpoint，包括 OpenAI、OpenRouter、智譜 ChatGLM、DeepSeek、Qwen、StepFun、Moonshot/Kimi、MiniMax、vLLM、llama.cpp、Ollama 相容介面和自託管閘道。

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

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
- **GitHub Issues**：[https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

我們期待您的反饋，一起讓 LightAgent 變得更強大！🚀


---

<p align="center">
  <strong>LightAgent - 讓智能更輕量，讓未來更簡單。</strong> 🌈
</p>

 
**LightAgent** —— 輕量、靈活、強大的主動式 Agent 框架，助您快速構建智能應用！