
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
  <h1>LightAgent🚀 超轻量、可“成长”的智能体框架，现已原生支持Skill</h1>
</div>


🚀 **LightAgent** 
不再只是“聊天”，而是真正的“完成任务”。LightAgent 把记忆（`mem0`）、工具（`Tools`）、思维树（`ToT`）和多智能体协作融合进一个极简的包中，而你只需 **一行代码** 就能构建一个**能自我学习、按需加载Skill**的智能体 —— 就像给大模型装上“招式库”与“执行大脑”。

🔥 为什么开发者会爱上它？

- **Skill 原生支持**：像管理代码一样管理 AI 能力。把 PDF 处理、代码审查、SOP 流程打包成可复用的 Skill，Agent 按需调用 —— 告别 prompt 堆积，迎接工程化 AI。
- **比 OpenAI Swarm 更简易的多智能体协作**：无需复杂编排，轻松构建“Agent 小分队”，并行拆解复杂任务。
- **MCP 协议（stdio/sse）开箱即连**：无缝接入外部数据源与工具，Agent 的“手”从此无限延伸。
- **零成本切换底层模型**：OpenAI、智谱 ChatGLM、DeepSeek、阶跃星辰、通义千问…… 想用哪个用哪个。
- **开箱即用的 API 服务**：标准 OpenAI 流式输出格式，可直接接入主流 Chat 前端（如 NextChat、LobeChat），秒变生产级应用。

🌟 **LightAgent = 轻 + 灵 + 可扩展**  
从个人脚本到企业级 Workflow，它帮你把“聪明的模型”变成“可靠的员工”。  
**Star 我们，尝试你的第一个 Skill 驱动的 Agent —— 改动几行代码，见证 AI 真正“动手做事”。**


---
## 新闻
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0 开发版：新增可持久化 LightFlow checkpoint、resume/rerun、审批节点、更清晰的步骤状态和 trace 元数据，同时补充 Guardrails 模板、MemoryPolicy 控制和 SharedMemoryPool 原型。
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-14]** LightAgent v0.8.1 开发版：新增 MemoryScope 元数据约定、MemoryPolicy 来源/范围/可信度过滤，并补充 Trace、用户记忆、自我反思记忆和 LightSwarm 委托状态的边界说明。
- **[2026-06-02]** LightAgent v0.8.0 开发版：新增 LightFlow 工作流编排能力，支持确定性多步骤 Agent 执行、DAG 依赖、步骤输出传递、重试和 flow trace 事件。
- **[2026-05-29]** LightAgent v0.7.0 开发版：新增可选的结构化 Trace 可观测能力，支持记录运行生命周期、模型请求摘要、工具调用、工具结果和错误事件，并提供 `agent.export_trace()` 便于生产调试。
- **[2026-05-28]** LightAgent v0.6.5 正式发布：新增可选结构化运行结果、结构化流式事件、可捕获的 LightAgent 错误和工具参数校验，同时保持默认 `agent.run()` 与 `stream=True` 行为兼容。
- **[2026-05-27]** LightAgent v0.6.4 正式发布：提升运行时工具调度可靠性，新增结构化错误码和排查文档，扩展 OpenAI 兼容模型配置说明。

历史版本说明请查看 [GitHub Releases](https://github.com/wanxingai/LightAgent/releases)。


---
![lightswarm_demo_cn.png](docs%2Fimages%2Flightswarm_demo_cn.png)
## ✨ 特性

- **轻量高效** 🚀：极简设计，快速部署，适合各种规模的应用场景。（No LangChain, No LlamaIndex）核心框架保持小而清晰，按需使用模型、MCP、记忆和可观测相关依赖，完全开源。 
- **记忆支持** 🧠：支持为每个用户自定义长期记忆，原生支持 `mem0` 记忆模块，实现对话过程中自动管理用户个性化记忆，让 Agent 更智能。
- **自主学习** 📚️：每个agent拥有自主学习能力，并且拥有权限的管理员可以管理每个agent。
- **工具集成** 🛠️：支持自定义工具（`Tools`）和MCP工具集成，灵活扩展，满足多样化需求。  
- **复杂目标** 🌳：内置带反思的思维树（ToT）模块，支持复杂任务分解和多步推理，提升任务处理能力。  
- **多智能体协同** 🤖：比Swarm更简单的多智能体协同，内置的LightSwarm实现意图判断和任务转移功能，能够更智能地处理用户输入，并根据需要将任务转移给其他代理。 
- **独立执行** 🤖：无人为干预自主完成任务工具调用。  
- **多模型支持** 🔄：兼容 OpenAI、智谱 ChatGLM、百川大模型、阶跃星辰、DeepSeek、Qwen 系列大模型。  
- **流式 API输出** 🌊：支持 OpenAI 流格式 API 服务输出，无缝接入主流 Chat 框架，提升用户体验。  
- **Trace 可观测性** 🔎：通过 `trace=True` 可选开启结构化运行轨迹，记录运行开始/结束、模型请求摘要、工具调用、工具结果和错误，同时保持默认字符串返回行为不变。  
- **Tools工具生成器** 🚀：只需将您的API文档交给[[Tools工具生成器]](#3-tools工具生成器)，它将自动化地为您打造专属的tools，助您在短短1小时内快速构建数百个个性化的自定义工具，提升效率，释放您的创新潜能。
- **agent自我学习** 🧠️：每个agent拥有自己的场景记忆能力，拥有从用户的对话中进行自我学习能力。
- **自适应tools机制** 🛠️：支持添加无限量tools，在上万个工具中让大模型过滤无关工具后再发送给大模型，可大幅度降低Token消耗。
- **工作流编排** 🔁：LightFlow 将多个 Agent 编排为确定性多步骤工作流，支持显式依赖、步骤输出传递、重试、checkpoint、resume/rerun、审批节点、fallback agent 和可追踪执行。
- **共享记忆原型** 🧠：SharedMemoryPool 提供带来源元数据和范围检索的追加式内存共享记忆，适合多 Agent 实验。
- **Guardrails 模板** 🛡️：可复用的输入、工具和输出安全策略模板，可用于隐私拦截、敏感工具确认、高风险参数校验和输出脱敏。

## 🧭 架构速览

| 层级 | 主要 API | 适用场景 |
| --- | --- | --- |
| 单 Agent 运行时 | `LightAgent` | 一个 Agent 的模型调用、工具、记忆、流式输出、trace 和 guardrails。 |
| 多 Agent 路由 | `LightSwarm` | 在多个专业 Agent 之间进行角色化委托。 |
| 确定性工作流 | `LightFlow` | DAG 工作流、重试、checkpoint、审批、resume 和 rerun。 |
| 工具与集成 | `tools`、`ToolRegistry`、MCP | Python 工具、生成工具、运行时加载工具或 MCP 工具服务。 |
| 记忆边界 | `MemoryPolicy`、`MemoryScope` | 租户隔离、来源、可信度、过期和写入准入控制。 |
| 共享记忆原型 | `SharedMemoryPool` | 多 Agent 共享记忆实验。 |
| 安全控制 | `input_guardrails`、`tool_guardrails`、`output_guardrails` | 隐私拦截、敏感工具确认、高风险参数校验和输出脱敏。 |
| 可观测性 | `trace=True`、`agent.export_trace()` | 结构化运行、模型、工具、错误和工作流事件。 |

## 核心使用模式

LightAgent 保持默认调用路径简单，同时允许逐步加入生产级控制。

| 模式 | 最小调用 | 说明 |
| --- | --- | --- |
| 基础响应 | `agent.run(query)` | 默认返回字符串。 |
| 流式输出 | `agent.run(query, stream=True)` | 返回 OpenAI 兼容的流式 chunk。 |
| 结构化结果 | `agent.run(query, result_format="object")` | 返回内容和结构化元数据。 |
| Trace | `agent.run(query, trace=True)` | 记录事件，不改变默认字符串返回。 |
| 用户记忆 | `agent.run(query, user_id="alice")` | 使用配置的记忆后端和 MemoryPolicy。 |
| 工具 | `LightAgent(..., tools=[fn])` | 函数应提供 `tool_info` 元数据。 |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | 为 Agent 添加输入、工具和输出策略。 |
| 工作流 | `LightFlow().step(...).run(query)` | 用于确定性多步骤执行。 |

## 📋 文档

- 常见安装、模型、工具、记忆、MCP、Skills、流式输出和 LightSwarm 问题，请查看 [FAQ](docs/FAQ.md)。
- 确定性多步骤工作流、checkpoint、resume/rerun、审批节点、fallback agent 和步骤状态，请查看 [LightFlow](docs/lightflow.md)。
- 自定义工具、运行时工具、ToolRegistry、ToolLoader、AsyncToolDispatcher 和 MCP 工具集成，请查看 [Tools Guide](docs/tools.md)。
- 共享长期记忆或图记忆部署，请查看 [Memory Security Guidance](docs/memory_security.md)。
- SharedMemoryPool 原型请查看 [SharedMemoryPool](docs/shared_memory_pool.md)。
- 记忆写入准入、过期检索和低质量写入拦截，请查看 [Memory Admission And Mutation Controls](docs/memory_admission.md)。
- 输入、工具和输出安全策略，请查看 [Guardrails](docs/guardrails.md)。
- OpenRouter、本地模型和 OpenAI 兼容配置，请查看 [Model Provider Configuration](docs/model_providers.md)。
- Trace 可观测能力请查看 [Trace Observability](docs/tracing.md)。

---

## 🚧 即将推出

- **智能体协同通讯** 🛠️：智能体之间还可以共享信息和传递消息，实现复杂的信息通讯和任务协同。
- **Agent 测评** 📊：内置 Agent 测评工具，方便评估和优化你构建的Agent，对齐业务场景，持续提升智能水平。


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

### 查看运行 Trace（v0.7.0）

Trace 默认关闭，需要显式传入 `trace=True`，不会改变原有 `agent.run()` 默认返回字符串的兼容行为。

```python
from LightAgent import LightAgent

# 初始化 Agent
agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url= "your_base_url")

# 以结构化对象形式查看运行轨迹
result = agent.run("你好，你是谁？", result_format="object", trace=True)
print(result.content)
print(result.trace_id)
print(result.trace)

for event in agent.export_trace():
    print(event["type"], event["data"])
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

README 保留核心使用模型；更长的示例、适配器配置和生产实践放在专门文档中。

### 1. 可拆卸记忆模块（`mem0`）
LightAgent 接受任何提供 `store(data, user_id)` 和 `retrieve(query, user_id)` 的记忆后端。使用 `user_id` 隔离对话；当记忆跨用户、租户、Agent 或 trace 共享时，应配置 `MemoryPolicy`。

### 2. 工具集成
使用带 `tool_info` 元数据的 Python 函数向 Agent 暴露受控能力。高级运行时工具、ToolRegistry、ToolLoader、AsyncToolDispatcher 和 MCP 请查看 [Tools Guide](docs/tools.md)。

### 3. Tools 工具生成器
`agent.create_tool()` 可以根据 API 文档或自然语言描述生成工具代码。生成工具应放在可审查的 tools 目录中，并在生产使用前测试。

### 4. 思维树（ToT）
当任务需要显式规划、反思和多工具选择时，启用 `tree_of_thought=True`。

### 5. 多智能体协同
`LightSwarm` 用于在专业 Agent 之间进行角色化委托。保持每个 Agent 角色清晰，并用记忆策略约束跨 Agent 记忆写入。

### 6. 流式 API
`agent.run(query, stream=True)` 返回 OpenAI 兼容流式 chunk，适合聊天 UI 和长输出。

### 7. Agent 自我学习
自我学习应与记忆后端和 `MemoryPolicy` 配合使用，避免低质量、隐私、过期或无关内容进入长期记忆。

### 8. Trace 与 Langfuse
LightAgent 可通过内置 trace 或 Langfuse 配置观察运行过程。

### 9. Agent 测评
Agent 测评将在后续版本中围绕业务场景评估 Agent 行为。

### 10. LightFlow 工作流
`LightFlow` 是确定性工作流层，适合让任务按已知步骤执行，而不是完全依赖自由形式规划。

- 步骤状态：`pending`、`running`、`success`、`failed`、`skipped`、`waiting_approval`。
- DAG 校验：`flow.validate(strict=True)`。
- 步骤控制：`timeout`、`max_retry`、`cancel_if`、`fallback_agent`、`requires_approval`、`approval_handler`。
- 持久化与恢复：`JsonLightFlowStore`、`flow.resume(run_id)`、`flow.rerun_step(run_id, step_name)`、`flow.get_run(run_id)`、`flow.list_runs()`。

请查看 [LightFlow](docs/lightflow.md)。

### 11. Guardrails
Guardrails 是围绕 Agent 执行的轻量策略钩子：输入策略检查用户问题，工具策略检查工具调用，输出策略检查或脱敏最终输出。

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

请查看 [Guardrails](docs/guardrails.md)。

### 12. SharedMemoryPool
`SharedMemoryPool` 是多 Agent 共享记忆实验的内存原型，建议与 `MemoryPolicy` 配合控制 namespace、source、scope、trust、confidence 和 agent name。

## 主流Agent模型支持

LightAgent 兼容 OpenAI 风格 chat completion endpoint，包括 OpenAI、OpenRouter、智谱 ChatGLM、DeepSeek、Qwen、StepFun、Moonshot/Kimi、MiniMax、vLLM、llama.cpp、Ollama 兼容接口和自托管网关。

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

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
- **GitHub Issues**：[https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

我们期待您的反馈，一起让 LightAgent 变得更强大！🚀


---

<p align="center">
  <strong>LightAgent - 让智能更轻量，让未来更简单。</strong> 🌈
</p>

 
**LightAgent** —— 轻量、灵活、强大的主动式 Agent 框架，助您快速构建智能应用！

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wanxingai/LightAgent&type=Date)](https://star-history.com/#wanxingai/LightAgent&Date)

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
