
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
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    한국어 | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
<div align="center">
  <h1>LightAgent🚀（차세대 Agentic AI 프레임워크）</h1>
</div>

**LightAgent**는 기억(`mem0`), 도구(`Tools`), 사고 트리(`ToT`)를 갖춘 극히 경량의 능동형 에이전틱 프레임워크로, 완전 오픈 소스입니다. 이는 OpenAI Swarm보다 더 간단한 다중 에이전트 협업을 지원하며, 단 한 단계로 자기 학습 능력을 갖춘 에이전트를 구축할 수 있고, stdio 및 sse 방식으로 MCP 프로토콜에 접속할 수 있습니다. 기본 모델은 OpenAI, 지프 ChatGLM, DeepSeek, 계단별 별, Qwen 통의 천문 대모델 등을 지원합니다. 또한, LightAgent는 OpenAI 스트림 형식 API 서비스 출력을 지원하여 주요 Chat 프레임워크에 원활하게 접속할 수 있습니다.🌟

---

## 뉴스
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0: 영속 LightFlow checkpoint, resume/rerun, 승인 노드, 명확한 단계 상태, trace 메타데이터, Guardrails 템플릿, MemoryPolicy 제어, SharedMemoryPool 프로토타입을 추가했습니다.
- **[2026-06-14]** LightAgent v0.8.1: MemoryScope 규약과 MemoryPolicy 출처/범위/신뢰도 필터를 추가했습니다.
- **[2026-06-02]** LightAgent v0.8.0: 결정적 다단계 workflow를 위한 LightFlow를 도입했습니다.

이전 릴리스 노트는 [GitHub Releases](https://github.com/wanxingai/LightAgent/releases)를 참고하세요.

---

## ✨ 특징

- **경량 및 효율성** 🚀: 극단적으로 간단한 디자인, 빠른 배포, 다양한 규모의 애플리케이션에 적합합니다. (No LangChain, No LlamaIndex) 100% 파이썬으로 구현되어 추가 의존성이 필요 없으며, 핵심 코드는 단 1000줄이며 완전히 오픈 소스입니다. 
- **기억 지원** 🧠: 각 사용자에 대한 맞춤형 장기 기억을 지원하며, 기본적으로 `mem0` 기억 모듈을 지원하여 대화 과정에서 사용자 맞춤 기억을 자동으로 관리하여 에이전트를 더욱 스마트하게 만듭니다.
- **자율 학습** 📚️: 각 에이전트는 자율 학습 능력을 가지며 권한이 있는 관리자는 각 에이전트를 관리할 수 있습니다.
- **도구 통합** 🛠️: 사용자 정의 도구(`Tools`)를 지원하며, 자동화 도구 생성을 통해 유연하게 확장 가능하며 다양한 요구를 충족합니다.  
- **복잡한 목표** 🌳: 반성적 사고가 가능한 사고 트리(ToT) 모듈이 내장되어 복잡한 작업 분해 및 다단계 추론을 지원하여 작업 처리 능력을 향상시킵니다.  
- **다중 에이전트 협업** 🤖: 스웜보다 더 간단하게 구현할 수 있는 다중 에이전트 협업 시스템으로, 내장된 LightSwarm을 통해 의도 판단 및 작업 전송 기능을 제공하여 사용자 입력을 보다 스마트하게 처리하고 필요에 따라 작업을 다른 에이전트에게 전송할 수 있습니다. 
- **독립 실행** 🤖: 인위적 개입 없이 자율적으로 작업 도구 호출을 완료합니다.  
- **다양한 모델 지원** 🔄: OpenAI, Zhiyun ChatGLM, Baichuan 대모델, StepFun, DeepSeek, Qwen 시리즈 대모델을 호환합니다.  
- **스트리밍 API** 🌊: OpenAI 스트리밍 형식 API 서비스 출력을 지원하여 주요 채팅 프레임워크와 원활하게 통합되어 사용자 경험을 향상시킵니다.  
- **Tools 도구 생성기** 🚀: API 문서만 제공하면 [Tools 도구 생성기]가 자동으로 귀하만의 도구를 만들고, 단 1시간 내에 수백 개의 맞춤형 도구를 신속하게 구축하여 효율성을 높이고 혁신 잠재력을 발휘할 수 있습니다.
- **에이전트 자기 학습** 🧠️: 각 에이전트는 사용자 대화에서 자기 학습 능력을 가진 장면 기억 능력을 가지고 있습니다.
- **적응형 도구 메커니즘** 🛠️: 무제한 도구 추가를 지원하며, 수천 개의 도구 중에서 대모델이 후보 도구 집합을 선택한 후 관련 없는 도구를 필터링하여 대모델에 문맥을 제출하여 Token 소비를 대폭 줄일 수 있습니다.
- **워크플로 오케스트레이션** 🔁: LightFlow는 명시적 의존성, 출력 전달, 재시도, checkpoint, resume/rerun, 승인 노드, fallback agent, 추적 가능한 실행을 갖춘 결정적 workflow를 구성합니다.
- **공유 메모리 프로토타입** 🧠: SharedMemoryPool은 출처 메타데이터, 범위 기반 검색, MemoryPolicy 호환 결과를 제공하는 인메모리 공유 기억입니다.
- **Guardrails 템플릿** 🛡️: 입력, 도구, 출력에 대한 재사용 가능한 안전 정책으로 개인정보 차단, 민감 도구 확인, 고위험 인자 검증, 출력 마스킹을 수행합니다.

## 🧭 아키텍처 한눈에 보기

| 계층 | 주요 API | 사용 시점 |
| --- | --- | --- |
| 단일 Agent 런타임 | `LightAgent` | 모델 호출, 도구, 메모리, 스트리밍, trace, guardrails가 필요한 경우. |
| 다중 Agent 라우팅 | `LightSwarm` | 전문 Agent 간 역할 기반 위임. |
| 결정적 workflow | `LightFlow` | DAG, 재시도, checkpoint, 승인, resume, rerun. |
| 도구와 통합 | `tools`, `ToolRegistry`, MCP | Python 도구, 생성 도구, 런타임 로딩, MCP 서버. |
| 메모리 경계 | `MemoryPolicy`, `MemoryScope` | 테넌트 격리, 출처, 신뢰, 만료, 쓰기 승인. |
| 공유 메모리 | `SharedMemoryPool` | Agent 간 공유 기억 실험. |
| 안전 제어 | `input_guardrails`, `tool_guardrails`, `output_guardrails` | 개인정보, 도구 확인, 위험 인자, 출력 마스킹. |
| 관측성 | `trace=True`, `agent.export_trace()` | 실행, 모델, 도구, 오류, workflow 구조화 이벤트. |

## 핵심 사용 패턴

LightAgent는 기본 호출 경로를 단순하게 유지하면서 운영 제어를 단계적으로 추가할 수 있습니다.

| 패턴 | 최소 호출 | 설명 |
| --- | --- | --- |
| 기본 응답 | `agent.run(query)` | 기본적으로 문자열을 반환합니다. |
| 스트리밍 | `agent.run(query, stream=True)` | OpenAI 호환 chunk를 반환합니다. |
| 구조화 결과 | `agent.run(query, result_format="object")` | 내용과 메타데이터를 반환합니다. |
| Trace | `agent.run(query, trace=True)` | 기본 문자열 반환을 바꾸지 않고 이벤트를 기록합니다. |
| 사용자 메모리 | `agent.run(query, user_id="alice")` | 설정된 메모리 backend와 MemoryPolicy를 사용합니다. |
| 도구 | `LightAgent(..., tools=[fn])` | 함수는 `tool_info`를 제공해야 합니다. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | 입력, 도구, 출력 정책을 추가합니다. |
| Workflow | `LightFlow().step(...).run(query)` | 결정적 다단계 실행에 사용합니다. |

## 📋 문서

- 설치, 모델, 도구, 메모리, MCP, Skills, 스트리밍, LightSwarm은 [FAQ](docs/FAQ.md)를 참고하세요.
- 결정적 workflow, checkpoint, resume/rerun, 승인, fallback agent, 단계 상태는 [LightFlow](docs/lightflow.md)를 참고하세요.
- 사용자 정의 도구, ToolRegistry, ToolLoader, AsyncToolDispatcher, MCP는 [Tools Guide](docs/tools.md)를 참고하세요.
- 공유 장기 기억 또는 그래프 기억은 [Memory Security Guidance](docs/memory_security.md)를 참고하세요.
- SharedMemoryPool은 [SharedMemoryPool](docs/shared_memory_pool.md)를 참고하세요.
- 메모리 쓰기 승인과 만료 제어는 [Memory Admission And Mutation Controls](docs/memory_admission.md)를 참고하세요.
- 입력, 도구, 출력 안전 정책은 [Guardrails](docs/guardrails.md)를 참고하세요.
- OpenRouter, 로컬 모델, OpenAI 호환 공급자는 [Model Provider Configuration](docs/model_providers.md)를 참고하세요.
- 구조화 trace는 [Trace Observability](docs/tracing.md)를 참고하세요.

## 🚧 곧 출시 예정

- **지능형 에이전트 협동 통신** 🛠️: 지능형 에이전트 간에 정보를 공유하고 메시지를 전달하여 복잡한 정보 통신 및 작업 협동을 실현할 수 있습니다.
- **에이전트 평가** 📊: 내장된 에이전트 평가 도구로 귀하가 구축한 에이전트를 평가하고 최적화하여 비즈니스 장면에 맞춰 지속적으로 스마트 수준을 향상시킬 수 있습니다.  


## 🌟 왜 LightAgent를 선택해야 하나요?

- **오픈 소스 무료** 💖: 완전 오픈 소스이며, 커뮤니티 주도로 지속적으로 업데이트되며 기여를 환영합니다!  
- **손쉬운 사용** 🎯: 문서가 자세하고 예시가 풍부하여 빠르게 배우고 쉽게 프로젝트에 통합할 수 있습니다.  
- **커뮤니티 지원** 👥: 활발한 개발자 커뮤니티가 언제든지 도움과 답변을 제공합니다.  
- **고성능** ⚡: 최적화된 설계로 고효율로 실행되며 고병렬 요구를 충족합니다.  

---

## 🛠️ 빠른 시작

### LightAgent 최신 버전 설치

```bash
pip install lightagent
```

(선택 설치) pip를 통해 Mem0 패키지 설치:

```bash
pip install mem0ai
```

또는 호스팅 플랫폼에서 Mem0을 한 번 클릭하여 사용할 수 있습니다. [여기 클릭](https://www.mem0.ai/).


### Hello world 예제 코드

```python
from LightAgent import LightAgent

# 에이전트 초기화
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url= "your_base_url")

# 에이전트 실행
response = agent.run("안녕하세요, 당신은 누구인가요?")
print(response)
```

### 실행 Trace 확인 (v0.7.0)

Trace는 선택 기능이며 기본 `agent.run()` 동작과 호환됩니다.

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

### LightFlow 실행 checkpoint 저장 (v0.9.0)

`LightFlow`는 workflow checkpoint를 저장하고 실패한 실행을 첫 단계부터 다시 시작하지 않고 재개할 수 있습니다.

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

### SharedMemoryPool 사용 (v0.9.0)

`SharedMemoryPool`은 다중 Agent 공유 기억 실험을 위한 가벼운 인메모리 프로토타입입니다.

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


### 시스템 프롬프트로 모델 자기 인식 설정

```python
from LightAgent import LightAgent

# 에이전트 초기화
agent = LightAgent(
     role="당신은 LightAgent로, 사용자에게 여러 도구 사용을 돕는 유용한 도우미임을 기억하세요.",  # 시스템 역할 설명
     model="deepseek-chat",  # 지원 모델: openai, chatglm, deepseek, qwen 등
     api_key="your_api_key",  # 당신의 대형 모델 서비스 제공자가 사용하는 API Key로 교체
     base_url="your_base_url",  # 당신의 대형 모델 서비스 제공자의 api url로 교체
 )
# 에이전트 실행
response = agent.run("당신은 누구인가요?")
print(response)
```

### 도구 사용 예제 코드

```python
from LightAgent import LightAgent


# 도구 정의
def get_weather(city_name: str) -> str:
    """
    `city_name`의 현재 날씨를 가져옵니다.
    """
    return f"조회 결과: {city_name} 날씨 맑음"
# 함수 내부에서 도구 정보를 정의
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "지정된 도시의 현재 날씨 정보를 가져옵니다.",
    "tool_params": [
        {"name": "city_name", "description": "조회할 도시 이름", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# 에이전트 초기화
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# 에이전트 실행
response = agent.run("상하이의 날씨를 확인해 주세요")
print(response)
```
무제한 수의 사용자 정의 도구를 지원합니다.

여러 도구 예제: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## 기능 상세 설명

README는 핵심 사용 모델을 유지하고, 긴 예제와 어댑터 설정, 운영 지침은 전용 문서에 둡니다.

### 1. 분리 가능한 메모리 모듈(`mem0`)
LightAgent는 `store(data, user_id)`와 `retrieve(query, user_id)`를 제공하는 모든 메모리 backend를 받을 수 있습니다. 대화 격리는 `user_id`, 공유 메모리는 `MemoryPolicy`를 사용합니다.

### 2. 도구 통합
`tool_info` 메타데이터가 있는 Python 함수로 Agent에 제어된 기능을 제공합니다. ToolRegistry, ToolLoader, AsyncToolDispatcher, MCP는 [Tools Guide](docs/tools.md)를 참고하세요.

### 3. 도구 생성기
`agent.create_tool()`는 API 문서나 자연어 설명에서 도구 코드를 생성할 수 있습니다. 운영 전 리뷰와 테스트가 필요합니다.

### 4. 사고 트리(ToT)
명시적 계획, 성찰, 도구 선택이 필요한 작업에는 `tree_of_thought=True`를 사용합니다.

### 5. 다중 Agent 협업
`LightSwarm`은 전문 Agent 사이에 작업을 위임합니다. 역할은 좁게 유지하고 메모리 쓰기는 정책으로 제한하세요.

### 6. 스트리밍 API
`agent.run(query, stream=True)`는 채팅 UI와 긴 응답을 위해 OpenAI 호환 chunk를 반환합니다.

### 7. Agent 자기 학습
자기 학습은 `MemoryPolicy`와 함께 사용해 개인정보, 만료, 무관한 내용을 장기 기억에 넣지 않도록 해야 합니다.

### 8. Trace와 Langfuse
LightAgent는 내장 trace 또는 Langfuse로 실행을 관측할 수 있습니다.

### 9. Agent 평가
Agent 평가는 업무 시나리오에 대한 동작 측정을 목표로 합니다.

### 10. LightFlow Workflow
`LightFlow`는 알려진 단계대로 실행하기 위한 결정적 workflow 계층입니다.

- 단계 상태: `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- DAG 검증: `flow.validate(strict=True)`.
- 단계 제어: `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, `approval_handler`.
- 영속화와 복구: `JsonLightFlowStore`, `flow.resume(run_id)`, `flow.rerun_step(run_id, step_name)`, `flow.get_run(run_id)`, `flow.list_runs()`.

[LightFlow](docs/lightflow.md)를 참고하세요.

### 11. Guardrails
Guardrails는 입력, 도구 호출, 출력을 검사하는 가벼운 hook입니다.

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

[Guardrails](docs/guardrails.md)를 참고하세요.

### 12. SharedMemoryPool
`SharedMemoryPool`은 다중 Agent 공유 기억 실험용 인메모리 프로토타입이며 `MemoryPolicy`와 함께 사용합니다.

## 주요 에이전트 모델 지원

LightAgent는 OpenAI 호환 chat completion endpoint와 동작합니다: OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama, 자체 gateway.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

## 사용 사례

- **스마트 고객 서비스**: 다중 회화 및 도구 통합을 통해 효과적인 고객 지원을 제공합니다.
- **데이터 분석**: 사고 트리 및 다중 에이전트 협업을 활용하여 복잡한 데이터 분석 작업을 처리합니다.
- **자동화 도구**: 자동화 도구 생성을 통해 맞춤형 도구를 신속하게 구축합니다.
- **교육 지원**: 기억 모듈 및 스트리밍 API를 통해 개인화된 학습 경험을 제공합니다.

---
 
## 🛠️ 기여 안내

우리는 어떤 형태의 기여든 환영합니다! 코드, 문서, 테스트 또는 피드백은 모두 프로젝트에 큰 도움이 됩니다. 좋은 아이디어가 있거나 버그를 발견한 경우, Issue 또는 Pull Request를 제출해 주십시오. 기여 방법은 다음과 같습니다:

1. **이 프로젝트 포크하기**: 오른쪽 상단의 `Fork` 버튼을 클릭하여 프로젝트를 귀하의 GitHub 리포지토리로 복사합니다.
2. **브랜치 생성**: 로컬에서 개발 브랜치를 생성합니다:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **변경 내역 제출**: 개발을 완료한 후 변경 사항을 제출합니다:  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **브랜치 푸시**: 브랜치를 귀하의 원격 리포지토리에 푸시합니다:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Pull Request 제출**: GitHub에서 Pull Request를 제출하고 변경 사항에 대해 설명합니다.

우리는 귀하의 기여를 즉시 검토할 것이며, 귀하의 지원에 감사드립니다!❤️

---

## 🙏 감사의 말씀

LightAgent의 개발 및 구현은 다음 오픈 소스 프로젝트의 영감과 지원에 힘입었습니다. 특히 이러한 뛰어난 프로젝트와 팀에 감사를 드립니다:

- **mem0**: [mem0](https://github.com/mem0ai/mem0)에서 제공하는 기억 모듈에 감사드립니다. LightAgent의 문맥 관리에 강력한 지원을 제공했습니다.  
- **Swarm**: [Swarm](https://github.com/openai/swarm)에서 제공한 다중 에이전트 협업 디자인 아이디어에 감사드립니다. LightAgent의 다중 에이전트 기능의 기본을 마련했습니다.  
- **ChatGLM3**: [ChatGLM3](https://github.com/THUDM/ChatGLM3)에서 제공하는 고성능 중국어 대형 모델 지원과 디자인 영감에 감사드립니다.  
- **Qwen**: [Qwen](https://github.com/QwenLM/Qwen)에서 제공하는 고성능 중국어 대형 모델 지원에 감사드립니다.  
- **DeepSeek-V3**: [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3)에서 제공하는 고성능 중국어 대형 모델 지원에 감사드립니다.  
- **阶跃星辰**: [step](https://www.stepfun.com/)에서 제공하는 고성능 중국어 대형 모델 지원에 감사드립니다.  

---

## 📄 라이센스

LightAgent는 [Apache 2.0 라이센스](LICENSE)를 따릅니다. 본 프로젝트는 자유롭게 사용, 수정 및 배포할 수 있지만 라이센스 조건을 준수해야 합니다.

---

## 📬 문의하기

질문이나 제안이 있는 경우 언제든지 문의해 주십시오:

- **이메일**: service@wanxingai.com  
- **GitHub Issues**：[https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

우리는 귀하의 피드백을 기대하며 함께 LightAgent를 더 강력하게 만들어 갑시다!🚀

- **더 많은 도구** 🛠️: 사용 사례 요구를 충족하기 위해 더 많은 유용한 도구를 지속적으로 통합합니다.
- **더 많은 모델 지원** 🔄: 더 많은 대형 모델을 지속적으로 지원하여 더 다양한 응용 사례를 충족합니다.
- **더 많은 기능** 🎯: 더 많은 유용한 기능이 지속적으로 업데이트됩니다. 기대해 주세요!
- **더 많은 문서** 📚: 자세한 문서와 풍부한 예시로 빠르게 배워 프로젝트에 쉽게 통합할 수 있습니다.
- **더 많은 커뮤니티 지원** 👥: 활발한 개발자 커뮤니티가 언제든지 도움과 해답을 제공합니다.
- **더 많은 성능 최적화** ⚡: 고병렬 요구를 충족하기 위해 성능을 지속적으로 최적화합니다.
- **더 많은 오픈 소스 기여** 🌟: 기여 코드를 환영하며 함께 더 나은 LightAgent를 만들어 갑시다!

---

<p align="center">
  <strong>LightAgent - 스마트함을 더 가볍게, 미래를 더 단순하게 만듭니다.</strong> 🌈
</p>

 
**LightAgent** —— 경량화, 유연성, 강력한 능동적 에이전트 프레임워크로, 스마트 애플리케이션을 신속하게 구축합니다!
