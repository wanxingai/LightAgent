
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
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    한국어 | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
```html
<div align="center">
  <h1>LightAgent🚀（차세대 Agentic AI 프레임워크）</h1>
</div>

**LightAgent**는 기억(`mem0`), 도구(`Tools`), 사고 트리(`ToT`)를 갖춘 극히 경량의 능동형 에이전틱 프레임워크로, 완전 오픈 소스입니다. 이는 OpenAI Swarm보다 더 간단한 다중 에이전트 협업을 지원하며, 단 한 단계로 자기 학습 능력을 갖춘 에이전트를 구축할 수 있고, stdio 및 sse 방식으로 MCP 프로토콜에 접속할 수 있습니다. 기본 모델은 OpenAI, 지프 ChatGLM, DeepSeek, 계단별 별, Qwen 통의 천문 대모델 등을 지원합니다. 또한, LightAgent는 OpenAI 스트림 형식 API 서비스 출력을 지원하여 주요 Chat 프레임워크에 원활하게 접속할 수 있습니다.🌟

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


## 🚧 곧 출시 예정

- **지능형 에이전트 협동 통신** 🛠️: 지능형 에이전트 간에 정보를 공유하고 메시지를 전달하여 복잡한 정보 통신 및 작업 협동을 실현할 수 있습니다.
- **에이전트 평가** 📊: 내장된 에이전트 평가 도구로 귀하가 구축한 에이전트를 평가하고 최적화하여 비즈니스 장면에 맞춰 지속적으로 스마트 수준을 향상시킬 수 있습니다.  


## 내장 “사고 흐름”
(Thought Flow) 방법은 체계적이고 구조화된 유연한 사고 프로세스를 통해 복잡한 상황에서의 도전에 효과적으로 대응할 수 있습니다.
 구체적인 실행 단계는 다음과 같습니다:
```text
문제 정의: 핵심 문제 및 목표를 명확히 하십시오.

정보 수집: 관련 정보 및 데이터를 체계적으로 수집합니다.

문제 분해: 복잡한 문제를 여러 하위 문제 또는 모듈로 나누기.

다차원 분석: 각 하위 문제를 다른 관점과 수준에서 분석합니다.

연관 구축: 하위 문제 간의 연관성과 의존 관계를 식별합니다.

해결책 생성: 각 하위 문제에 대한 가능한 해결책을 제안합니다.

평가 및 선택: 각 해결책의 실행 가능성과 영향을 평가하고 최적의 해결책을 선택합니다.

실행 및 피드백: 선택된 해결책을 실행하고 피드백에 따라 조정합니다.
```

---
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

### 1. 분리 가능한 완전 자동 기억 모듈(`mem0`)
LightAgent는 외부 확장 `mem0` 기억 모듈을 지원하여 완전 자동으로 문맥 기억 및 이력 관리를 수행하며, 개발자가 수동으로 기억 추가 및 검색을 트리거할 필요가 없습니다. 기억 모듈을 통해 에이전트는 다회 대화에서 문맥 일관성을 유지할 수 있습니다.

```python
# 기억 모듈 활성화

# 또는 아래와 같이 사용자 정의 기억 모듈을 사용할 수 있습니다. https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_API_BASE"] = "your_base_url"
        # Mem0 초기화
        config = {
            "version": "v1.1"
        }
        # mem0에서 Qdrant를 벡터 데이터베이스로 사용하려면 아래 코드로 config를 변경하세요
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
        """기억 저장 - 개발자가 저장 방법의 내부 구현을 수정할 수 있으며, 현재 예시는 mem0의 기억 추가 방법입니다."""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """관련 기억 검색 - 개발자가 검색 방법의 내부 구현을 수정할 수 있으며, 현재 예시는 mem0의 기억 검색 방법입니다."""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="당신은 LightAgent로, 사용자에게 여러 도구 사용을 돕는 유용한 도우미임을 기억하세요.",  # 시스템 역할 설명
        model="deepseek-chat",  # 지원 모델: openai, chatglm, deepseek, qwen 등
        api_key="your_api_key",  # 당신의 대형 모델 서비스 제공자가 사용하는 API Key로 교체
        base_url="your_base_url",  # 당신의 대형 모델 서비스 제공자의 api url로 교체
        memory=CustomMemory(),  # 기억 기능 활성화
        tree_of_thought=False,  # 사고 체인 활성화
    )

# 기억을 가진 테스트 & 도구를 추가할 수 있는 경우, 도구를 추가하여 기억된 도구 호출을 구현합니다.

user_id = "user_01"
logger.info("\n=========== 다음 대화 ===========")
query = "삼아에서 즐길 만한 관광지가 무엇인지 소개해 줘, 내 주위의 많은 친구들이 삼아 여행 갔어, 나도 가고 싶어."
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== 다음 대화 ===========")
query = "나는 어디로 여행을 가고 싶지?"
print(agent.run(query, stream=False, user_id=user_id))
```

출력 예시:
```python
=========== 다음 대화 ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
문제 생각 시작: 삼아에서 즐길 만한 관광지가 무엇인지 소개해 줌, 내 주위의 많은 친구들이 삼아 여행 갔어, 나도 가고 싶어.
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - 최종 답변: 
삼아는 중국 하이난 성의 인기 관광 도시로, 아름다운 해변, 열대 기후 및 풍부한 관광 자원으로 유명합니다. 다음은 삼아에서 꼭 가봐야 할 관광지의 목록입니다:

1. **야롱만**: "동양의 하와이"로 불리며 긴 백사장과 맑은 바다를 가지고 있어 수영, 다이빙 및 일광욕을 위한 가장 적합한 곳입니다.

2. **천애해각**: 장엄한 해경과 로맨틱한 전설로 관광객을 매료시키는 유명한 문화적 명소입니다. 여기에 있는 거대한 바위에는 "천애"와 "해각"이라는 문자이 새겨져 있으며, 영원한 사랑을 상징합니다.

3. **남산 문화 관광지**: 108미터 높이의 남산 해상 관음상이 있으며, 세계에서 가장 높은 해상 관음상입니다. 관광객들은 여기에서 불교 문화를 경험하고 사원과 정원을 방문할 수 있습니다.

4. **오지주도**: 순수한 자연 풍경과 많은 수상 활동으로 유명한 작은 섬입니다. 관광객들은 여기에서 스노클링, 바다 낚시 등 다양한 활동을 할 수 있습니다.

5. **대동해**: 삼아 시내에 위치한 해변으로 교통이 편리하며, 풍부한 야경으로 관광객에게 인기가 많습니다.

6. **삼아만**: 22킬로미터에 달하는 해변으로 일몰을 감상하기에 좋습니다. 해변은 비교적 조용한 편으로, 조용함을 좋아하는 관광객에게 적합합니다.

7. **아노다 열대 우림 문화 관광지**: 열대 우림 공원으로, 관광객들은 여기에서 열대 우림의 자연 경관을 경험하고 다양한 탐험 활동에 참여할 수 있습니다.

8. **사슴 회두공원**: 산꼭대기에 위치한 공원으로 삼아 시내와 삼아만의 아름다운 경치를 감상할 수 있습니다. 여기에는 사슴에 대한 아름다운 전설이 있습니다.

9. **서섬**: 비교적 원시적인 작은 섬으로, 고요한 해변과 풍부한 해양 생물로 관광객을 끌어들입니다.

10. **삼아 천고정**: 대형 문화 테마 공원으로, 공연과 전시를 통해 하이난의 역사와 문화를 보여줍니다.

위의 관광지 외에도 삼아에는 열대 식물원, 해산물 시장 등 탐험할 만한 많은 장소가 있습니다. 삼아의 미각도 놓칠 수 없으며, 특히 신선한 해산물과 열대 과일이 일품입니다. 여행 계획 시에는 날씨 예보와 관광지 개방 시간을 미리 확인하는 것이 좋으며, 즐거운 여행을 보장할 수 있습니다.
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== 다음 대화 ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
문제 생각 시작: 나는 어디로 여행을 가고 싶어?
관련 기억 발견:
사용자가 삼아 여행을 가고 싶어 한다.
사용자의 친구는 삼아 여행을 갔다.
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - 최종 답변: 
사용자가 이전에 언급한 정보에 따르면, 사용자 친구들은 삼아(Sanya)에 이미 가봤으며, 사용자는 삼아에 대한 관심을 표명했습니다. 따라서 삼아는 사용자가 가기 적합한 여행지가 될 수 있습니다. 아래는 삼아에 대한 여행 정보입니다:

### 삼아 여행 추천:
1. **야롱만**: "동양의 하와이"로 불리며 아름다운 해변과 맑은 바다를 가지고 있어 수영과 일광욕을 즐기기에 적합합니다.
2. **천애해각**: 삼아의 상징적인 명소로 독특한 바위와 로맨틱한 전설로 관광객을 끌어들입니다.
3. **남산 문화 관광지**: 유명한 남산 사원과 108미터 높은 해상 관음상이 있는 불교 문화의 중요한 관광 명소입니다.
4. **오지주도**: 다이빙과 수상 스포츠에 적합하며, 섬에는 풍부한 해양 생물과 산호초가 있습니다.
5. **대동해**: 삼아 시내에 있는 해변으로, 교통이 편리하여 가족 및 커플 여행에 적합합니다.

### 기타 추천:
사용자가 삼아에 대해 이미 알고 있거나 다른 목적지를 탐색하고자 한다면, 다음은 몇 가지 다른 인기 여행지입니다:
1. **구이린**: 독특한 카르스트 지형과 리장 강 풍경으로 유명합니다.
2. **리장**: 고도와 옥룡 눈산이 주요 관광지로 역사 문화와 자연 경관을 선호하는 관광객에게 적합합니다.
3. **장자제**: 특이한 바위 기둥과 자연 경관으로 유명하며, "아바타" 영화 촬영지 중 하나입니다.

사용자는 자신의 흥미와 시간 계획에 따라 적합한 여행지를 선택할 수 있습니다. 사용자가 더 자세한 정보나 일정 계획 도움이 필요하면 언제든지 알려주십시오!
```

### 2. 도구 통합 (무한 확장 가능한 사용자 정의 도구 지원)
개인화된 도구 사용자 정의(`Tools`)를 수용하며, `tools` 메서드를 통해 귀하의 전용 도구를 쉽게 통합할 수 있습니다. 이 도구들은 Python 함수일 수 있으며, 유연성과 정확성을 보장하기 위해 매개변수 유형 주석을 지원합니다. 또한, AI 기반 도구 생성기를 제공하여 귀하의 도구를 자동화하여 창의력을 발휘할 수 있도록 돕습니다.

```python

import requests
from LightAgent import LightAgent

# 도구 정의
def get_weather(
        city_name: str
) -> str:
    """
    도시 날씨 정보를 가져옵니다.
    :param city_name: 도시 이름
    :return: 날씨 정보
    """
    if not isinstance(city_name, str):
        raise TypeError("도시 이름은 문자열이어야 합니다.")

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
        ret = "날씨 데이터를 가져오는 중 에러 발생!\n" + traceback.format_exc()

    return str(ret)
# 함수 내부에서 도구 정보 정의
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "지정된 도시의 현재 날씨 정보를 가져옵니다.",
    "tool_params": [
        {"name": "city_name", "description": "조회할 도시 이름", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    키워드 기반 뉴스 검색
    :param keyword: 검색 키워드
    :param max_results: 반환할 최대 결과 개수, 기본값은 5
    :return: 뉴스 검색 결과
    """
    results = f"{keyword}를 검색하여 {max_results}개의 관련 정보를 찾았습니다."
    return str(results)

# 함수 내부에서 도구 정보 정의
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "키워드 기반 뉴스 검색",
    "tool_params": [
        {"name": "keyword", "description": "검색 키워드", "type": "string", "required": True},
        {"name": "max_results", "description": "반환할 최대 결과 개수", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    사용자 정보 가져오기
    :param user_id: 사용자 ID
    :return: 사용자 정보
    """
    if not isinstance(user_id, str):
        raise TypeError("사용자 ID는 문자열이어야 합니다.")

    try:
        # 사용자 정보 API를 사용한다고 가정하며, 예시 URL을 사용합니다.
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
        user_info = "사용자 데이터를 가져오는 중 에러 발생!\n" + traceback.format_exc()

    return str(user_info)

# 함수 내부에서 도구 정보 정의
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "지정된 사용자의 정보를 가져옵니다.",
    "tool_params": [
        {"name": "user_id", "description": "사용자 ID", "type": "string", "required": True},
    ]
}

# 사용자 정의 도구
tools = [get_weather, search_news, get_user_info]  # 모든 도구를 포함

# 에이전트 초기화
# 모델, api_key, base_url을 적절히 교체하세요.
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

query = "현재 삼아 날씨가 어떤지요?"
response = agent.run(query, stream=False)  # 에이전트를 사용하여 쿼리 실행
print(response)
```

### 3. Tools 도구 생성기
Tools 도구 생성기는 사용자 제공 텍스트 설명에 따라 도구 코드를 자동으로 생성하는 모듈입니다. 이 기능은 API 호출 도구, 데이터 처리 도구 등을 빠르게 생성해야 하는 상황에 특히 유용합니다.

사용 예시

다음은 Tools 도구 생성기를 사용하는 예제 코드입니다:

```python
import json
import os
import sys
from LightAgent import LightAgent

# LightAgent 초기화
agent = LightAgent(
    name="Agent A",  # 에이전트 이름
    instructions="당신은 유용한 에이전트입니다.",  # 역할 설명
    role="당신은 도구 생성기로, 사용자가 제공한 텍스트 설명에 따라 자동으로 적절한 도구 코드를 생성하고 지정된 디렉터리에 저장하는 역할을 합니다. 생성된 코드가 정확하고 사용 가능하며 사용자의 요구에 맞도록 보장하십시오.",  # 도구 생성기의 역할 설명
    model="deepseek-chat",  # 모델을 적절히 교체하세요. 지원된 모델: openai, chatglm, deepseek, qwen 등
    api_key="your_api_key",  # 당신의 API Key로 교체
    base_url="your_base_url",  # 당신의 api url로 교체
)

# 예시 텍스트 설명
text = """
시나 주식 API는 주식 시장 데이터를 얻기 위한 기능을 제공하며, 주식 시세, 실시간 거래 데이터, K선 데이터 등을 포함합니다.

시나 주식 API 기능 소개
1. 주식 시세 데이터 얻기:
실시간 시세 데이터: 실시간 시세 API를 사용하여 주식의 최신 가격, 거래량, 상승 하락폭 등을 얻을 수 있습니다.
분 단위 시세 데이터: 분 단위 시세 API를 사용하여 주식의 분 단위 거래 데이터를 포함하여 시세 정보(시가, 종가, 고가, 저가 등)를 얻을 수 있습니다.

2. 주식 역사 K선 데이터 얻기:
K선 데이터: K선 API를 통해 주식의 역사적 거래 데이터를 얻을 수 있으며, 시가, 종가, 고가, 저가, 거래량 등을 포함합니다. 필요한 경우 서로 다른 시간 주기 및 이동 평균 주기를 선택할 수 있습니다.
재무 데이터: K선 데이터(전면 재무 및 후면 재무)를 선택하여 주식의 가격 변동을 더 정확하게 분석할 수 있습니다.

시나 주식 API 데이터 예시
1. 주식 시세 데이터 얻기:
API 주소：http://hq.sinajs.cn/list=[주식코드]
예시: 주식 코드가 "sh600519"(구이저우 마오타이)인 실시간 시세 데이터를 얻으려면 다음 API 주소를 사용할 수 있습니다： http://hq.sinajs.cn/list=sh600519
위 API 주소에 HTTP GET 요청을 보내면 해당 주식의 실시간 시세 데이터가 포함된 응답을 받을 수 있습니다。

2. 주식 역사 K선 데이터 얻기:
API 주소：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[주식코드]&scale=[시간 주기]&ma=[이동 평균 주기]&datalen=[데이터 길이]
예시: 주식 코드가 "sh600519"(구이저우 마오타이)인 일일 K선 데이터가 필요한 경우 다음 API 주소를 사용할 수 있습니다：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
위 API 주소에 HTTP GET 요청을 보내면 해당 주식의 역사 K선 데이터가 포함된 응답을 받을 수 있습니다.
"""

# 도구 디렉터리 경로 구축
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# 도구 디렉터리가 없는 경우 생성
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"도구 디렉터리가 생성되었습니다: {tools_directory}")

# 에이전트를 사용하여 도구 코드를 생성
agent.create_tool(text, tools_directory=tools_directory)
```
실행 후에서 tools 디렉터리 내에 2개의 파일이 생성됩니다: get_stock_kline_data.py 및 get_stock_realtime_data.py

### 4. 사고 트리(ToT)
내장된 사고 트리 모듈은 복잡한 작업 분해 및 다단계 추론을 지원합니다. 사고 트리를 통해 에이전트는 더 나은 방식으로 복잡한 작업을 처리할 수 있습니다.

```python
# 사고 나무 활성화
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # 사고 나무 활성화
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # 당신의 deepseek r1 API Key로 교체
    tot_base_url="https://api.openai.com/v1",  # api url
    filter_tools=False,  # 적응형 도구 메커니즘 비활성화
)
```
ToT를 활성화하면 기본적으로 적응형 도구 메커니즘이 활성화됩니다. 비활성화하려면 LightAgent 초기화 시 filter_tools=False 매개변수를 추가하십시오.

### 5. 다중 에이전트 협업
스웜(Swarm) 유사한 다중 에이전트 협업 작업을 지원하여 작업 처리 효율성을 높입니다. 여러 에이전트가 협력하여 복잡한 작업을 완료할 수 있습니다.

```python
from LightAgent import LightAgent, LightSwarm
# 환경 변수 OPENAI_API_KEY 및 OPENAI_BASE_URL 설정
# 모델 기본값: gpt-4o-mini

# LightSwarm 인스턴스 생성
light_swarm = LightSwarm()

# 여러 에이전트 생성
agent_a = LightAgent(
    name="Agent A",
    instructions="저는 에이전트 A입니다, 안내원입니다.",
    role="안내원, 방문자를 맞이하고 기본 정보 안내를 책임집니다. 매번 답변하기 전에 자신의 신원을 언급해야 하며, 고객의 비즈니스 문제에 직접적으로 답변할 수 없습니다. 현재 고객 문제를 해결할 수 없다면 '죄송하지만 현재 도와드릴 수 없습니다!'라고 답하십시오.",
)

agent_b = LightAgent(
    name="Agent B",
    instructions="저는 에이전트 B입니다, 회의실 예약을 담당하고 있습니다.",
    role="회의실 예약 관리자, 1호, 2호, 3호 회의실의 예약, 취소 및 조회를 처리합니다. 매번 답변하기 전에 자신의 신원을 언급하며 매우 공손하게 사용자 질문에 답합니다.",
)

agent_c = LightAgent(
    name="Agent C",
    instructions="저는 에이전트 C입니다, 기술 지원 담당입니다.",
    role="기술 지원 전문가, 하드웨어, 소프트웨어, 네트워크 등 기술 문제의 문의 및 해결을 맡습니다. 고객의 질문에 대해 가능한 한 상세히 답변해야 하며, 문제가 제 능력 범위를 넘어서면 사용자에게 더 높은 기술 지원팀에 연락하도록 안내합니다.",
)

agent_d = LightAgent(
    name="Agent D",
    instructions="저는 에이전트 D입니다, 인사 담당자입니다.",
    role="인사 전문가, 직원 입사, 퇴사, 휴가, 복리후생 등을 처리하는 업무를 맡습니다. 고객 질문에 대해 가능한 한 상세히 답변해야 하며, 추가적인 처리가 필요할 경우 사용자에게 인사 부서에 연락하도록 안내합니다.",
)

# 에이전트를 LightSwarm 인스턴스에 자동 등록
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# 에이전트 A 실행
res = light_swarm.run(agent=agent_a, query="안녕하세요, 저는 앨리스입니다. 왕샤오밍의 입사 여부를 확인하고 싶습니다.", stream=False)
print(res)
```
출력 예시:
```python
안녕하세요, 저는 인사 담당 에이전트 D입니다. 왕샤오밍의 입사 여부에 대해서는 시스템 기록을 조회해야 합니다. 잠시만 기다려 주십시오.
(시스템 기록 조회 중...)
우리 기록에 따르면, 왕샤오밍은 2025년 1월 5일에 입사 수속을 완료했습니다. 그는 모든 필요한 문서에 서명했고, 직원 번호와 사무실 위치가 배정되었습니다. 추가 정보가 필요하시거나 다른 문의 사항이 있으면 언제든지 인사 부서에 연락 주십시오. 저희는 언제든지 도와드릴 준비가 되어 있습니다.
```

### 6. 스트리밍 API 
OpenAI 스트리밍 형식 API 서비스 출력을 지원하여 주요 채팅 프레임워크와 원활하게 통합됩니다.

```python
# 스트리밍 출력 활성화
response = agent.run("AI에 관한 기사를 생성해 주십시오.", stream=True)
for chunk in response:
    print(chunk)
```


### 7. 에이전트 평가 (곧 출시 예정)
내장된 에이전트 평가 도구로 에이전트 성과를 평가하고 최적화하는 데 편리합니다.



## 주요 에이전트 모델 지원
OpenAI, Zhiyun ChatGLM, DeepSeek, Qwen 시리즈 대모델을 호환합니다.

#### 현재 테스트된 호환 대모델
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
- **GitHub Issues**：[https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

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