
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
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    Русский
  </p>
</div>

**LightAgent** является крайне легковесным активным агентным фреймворком с памятью (`mem0`), инструментами (`Tools`) и деревом мышления (`ToT`), полностью с открытым исходным кодом. Он поддерживает более простую многослойную координацию агентов, чем OpenAI Swarm, и позволяет в один шаг создать агента с возможностью самообучения, а также поддерживает подключение к протоколу MCP через stdio и sse. Базовая модель поддерживает OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen и другие крупные модели. В то же время, LightAgent поддерживает вывод API-сервиса в формате OpenAI Stream, бесшовно интегрируясь с основными чат-фреймворками.🌟

---

## Новости
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0: добавлены сохраняемые checkpoint для LightFlow, resume/rerun, узлы утверждения, более ясные состояния шагов, trace-метаданные, шаблоны Guardrails, управление MemoryPolicy и прототип SharedMemoryPool.
- **[2026-06-14]** LightAgent v0.8.1: добавлены соглашения MemoryScope и фильтры MemoryPolicy по источнику, области и уровню доверия.
- **[2026-06-02]** LightAgent v0.8.0: представлен LightFlow для детерминированных многошаговых workflow.

История релизов доступна в [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

---

## ✨ Особенности

- **Легковесность и эффективность** 🚀: ультра-упрощённый дизайн, быстрая настройка, подходит для приложений любого размера. (Нет LangChain, Нет LlamaIndex) 100% реализация на Python, без дополнительных зависимостей, основная кодовая база составляет всего 1000 строк, полностью открытый исходный код.
- **Поддержка памяти** 🧠: поддержка пользовательской долгосрочной памяти для каждого пользователя, нативная поддержка модуля памяти `mem0`, позволяющая автоматически управлять персонализированной памятью пользователя в процессе диалога, делая агента более умным.
- **Автономное обучение** 📚️: каждый агент обладает способностью самостоятельно обучаться, а администраторы с соответствующими правами могут управлять каждым агентом.
- **Интеграция инструментов** 🛠️: поддержка пользовательских инструментов (`Tools`), автоматическая генерация инструментов, гибкое расширение для удовлетворения разнообразных потребностей.  
- **Сложные цели** 🌳: встроенный модуль дерева мышления с рефлексией (ToT), поддержка декомпозиции сложных задач и многошагового вывода, повышение эффективности обработки задач.  
- **Многослойное взаимодействие агентов** 🤖: более простая реализация многослойного взаимодействия агентов, встроенный LightSwarm для определения намерений и переноса задач, что позволяет более умно обрабатывать ввод пользователя и при необходимости передавать задачи другим агентам. 
- **Автономное выполнение** 🤖: выполнение вызовов инструментов без человеческого вмешательства.  
- **Поддержка множества моделей** 🔄: совместимость с OpenAI, ChatGLM от Zhipu, Baichuan и другим.  
- **Потоковый API** 🌊: поддержка вывода сервисов API в потоковом формате OpenAI, бесшовная интеграция с основными чат-фреймворками, улучшение пользовательского опыта.  
- **Генератор инструментов Tools** 🚀: просто передайте вашу документацию API [генератору инструментов Tools], и он автоматически создаст для вас индивидуальные инструменты, позволяя вам быстро создать сотни персонализированных инструментов всего за час, повысив производительность и освободив ваши творческие возможности.
- **Самообучение агентов** 🧠️: каждый агент обладает способностью запоминать информацию о сценах и самообучаться на основе разговоров с пользователями.
- **Адаптивный механизм инструментов** 🛠️: поддержка неограниченного количества инструментов, выбор кандидатов из десятков тысяч инструментов крупной моделью, фильтрация нерелевантных инструментов и передача контекста крупной модели, что может значительно снизить потребление токенов.
- **Оркестрация workflow** 🔁: LightFlow связывает агентов в детерминированные workflow с явными зависимостями, передачей результатов, повторами, checkpoint, resume/rerun, утверждениями, fallback-agent и трассировкой.
- **Прототип общей памяти** 🧠: SharedMemoryPool предоставляет общую память в памяти процесса с метаданными происхождения, выборкой по области и результатами, совместимыми с MemoryPolicy.
- **Шаблоны Guardrails** 🛡️: Переиспользуемые политики ввода, инструментов и вывода блокируют приватные данные, требуют подтверждения чувствительных инструментов, проверяют рискованные параметры и редактируют вывод.

## 🧭 Архитектура кратко

| Слой | Основной API | Когда использовать |
| --- | --- | --- |
| Runtime одного агента | `LightAgent` | Один агент с моделью, инструментами, памятью, streaming, trace и guardrails. |
| Маршрутизация агентов | `LightSwarm` | Делегирование по ролям между специализированными агентами. |
| Детерминированный workflow | `LightFlow` | DAG, повторы, checkpoints, утверждения, resume и rerun. |
| Инструменты и интеграции | `tools`, `ToolRegistry`, MCP | Python-инструменты, генерация, runtime-загрузка или MCP-серверы. |
| Граница памяти | `MemoryPolicy`, `MemoryScope` | Изоляция tenants, происхождение, доверие, срок действия и допуск записи. |
| Общая память | `SharedMemoryPool` | Эксперименты общей памяти между агентами. |
| Безопасность | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Приватность, подтверждение инструментов, рискованные параметры и редактирование вывода. |
| Наблюдаемость | `trace=True`, `agent.export_trace()` | Структурированные события run, модели, инструмента, ошибки и workflow. |

## Основные паттерны использования

LightAgent сохраняет простой путь вызова по умолчанию и позволяет постепенно добавлять production-контроль.

| Паттерн | Минимальный вызов | Примечания |
| --- | --- | --- |
| Базовый ответ | `agent.run(query)` | По умолчанию возвращает строку. |
| Streaming | `agent.run(query, stream=True)` | Возвращает OpenAI-совместимые chunks. |
| Структурированный результат | `agent.run(query, result_format="object")` | Возвращает контент и метаданные. |
| Trace | `agent.run(query, trace=True)` | Пишет события, не меняя строковый ответ по умолчанию. |
| Память пользователя | `agent.run(query, user_id="alice")` | Использует настроенный backend памяти и MemoryPolicy. |
| Инструменты | `LightAgent(..., tools=[fn])` | Функции должны иметь `tool_info`. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | Добавляет политики ввода, инструментов и вывода. |
| Workflow | `LightFlow().step(...).run(query)` | Для детерминированного многошагового выполнения. |

## 📋 Документация

- По установке, моделям, инструментам, памяти, MCP, Skills, streaming и LightSwarm см. [FAQ](docs/FAQ.md).
- По детерминированным workflow, checkpoint, resume/rerun, утверждениям, fallback-agent и состояниям шагов см. [LightFlow](docs/lightflow.md).
- По пользовательским инструментам, ToolRegistry, ToolLoader, AsyncToolDispatcher и MCP см. [Tools Guide](docs/tools.md).
- По общей долговременной или графовой памяти см. [Memory Security Guidance](docs/memory_security.md).
- По SharedMemoryPool см. [SharedMemoryPool](docs/shared_memory_pool.md).
- По допуску записи памяти и срокам действия см. [Memory Admission And Mutation Controls](docs/memory_admission.md).
- По безопасности ввода, инструментов и вывода см. [Guardrails](docs/guardrails.md).
- По OpenRouter, локальным моделям и OpenAI-совместимым провайдерам см. [Model Provider Configuration](docs/model_providers.md).
- По структурированным trace см. [Trace Observability](docs/tracing.md).

## 🚧 В ближайшем будущем

- **Согласованная связь агентов** 🛠️: Агенты также могут обмениваться информацией и передавать сообщения, реализуя сложную информационную связь и совместное выполнение задач.
- **Оценка Агентов** 📊: встроенные инструменты оценки агентов, удобные для оценки и оптимизации созданных вами агентов для привязки к бизнес-сценариям, постоянное повышение уровня интеллекта.  

## 🌟 Почему выбирают LightAgent?

- **Открытый и бесплатный** 💖: полностью открытый, управляемый сообществом, регулярно обновляемый, все желающие могут внести свой вклад!  
- **Легкость в освоении** 🎯: подробная документация, множество примеров, быстрое освоение, простая интеграция в ваши проекты.  
- **Поддержка сообщества** 👥: активное сообщество разработчиков, готовое помочь и ответить на вопросы.  
- **Высокая производительность** ⚡: оптимизированный дизайн, высокая эффективность, удовлетворяющая требования к высокой конкуренции.  

---

## 🛠️ Быстрый старт

### Установка последней версии LightAgent

```bash
pip install lightagent
```

(Опционально установите пакет Mem0):

```bash
pip install mem0ai
```

Или вы можете использовать Mem0 в облачной стороне, кликнув [здесь](https://www.mem0.ai/).


### Пример кода Hello world

```python
from LightAgent import LightAgent

# Инициализация агента
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url= "your_base_url")

# Запуск агента
response = agent.run("Привет, кто ты?")
print(response)
```

### Проверка trace выполнения (v0.7.0)

Trace включается явно и сохраняет совместимость поведения `agent.run()` по умолчанию.

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

### Checkpoint выполнения LightFlow (v0.9.0)

`LightFlow` может сохранять checkpoint workflow и продолжать неудачный запуск не с первого шага.

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

### Использование SharedMemoryPool (v0.9.0)

`SharedMemoryPool` — легкий in-memory прототип для экспериментов с общей памятью между агентами.

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


### Установка самосознания модели через системные подсказки

```python
from LightAgent import LightAgent

# Инициализация агента
agent = LightAgent(
     role="Пожалуйста, помните, что вы - LightAgent, полезный помощник, который может помочь пользователям с использованием нескольких инструментов.",  # Описание системной роли
     model="deepseek-chat",  # Поддерживаемые модели: openai, chatglm, deepseek, qwen и т.д.
     api_key="your_api_key",  # Замените на ключ API вашего провайдера крупной модели
     base_url="your_base_url",  # Замените на URL API вашего провайдера крупной модели
 )
# Запуск агента
response = agent.run("Кто ты?")
print(response)
```

### Пример кода использования инструмента

```python
from LightAgent import LightAgent


# Определение инструмента
def get_weather(city_name: str) -> str:
    """
    Получить текущую погоду для `city_name`
    """
    return f"Результат запроса: Погода в {city_name} солнечная"
# Определить информацию о инструменте внутри функции
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Получите текущую информацию о погоде в заданном городе",
    "tool_params": [
        {"name": "city_name", "description": "Название города для запроса", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Инициализация агента
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# Запуск агента
response = agent.run("Пожалуйста, проверьте погоду в Шанхае")
print(response)
```
Поддерживает настройку неограниченного количества инструментов.

Примеры нескольких инструментов: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## Подробное описание функций

README сохраняет основную модель использования; длинные примеры, настройка адаптеров и production-практики находятся в отдельных документах.

### 1. Съемный модуль памяти (`mem0`)
LightAgent принимает любой backend памяти с `store(data, user_id)` и `retrieve(query, user_id)`. Используйте `user_id` для изоляции диалогов и `MemoryPolicy` для общей памяти.

### 2. Интеграция инструментов
Python-функции с метаданными `tool_info` открывают контролируемые возможности агенту. ToolRegistry, ToolLoader, AsyncToolDispatcher и MCP описаны в [Tools Guide](docs/tools.md).

### 3. Генератор инструментов
`agent.create_tool()` может генерировать код инструментов из API-документации или естественного описания. Перед production выполните review и тесты.

### 4. Дерево мышления (ToT)
Включайте `tree_of_thought=True`, когда нужны явное планирование, рефлексия и выбор инструментов.

### 5. Совместная работа агентов
`LightSwarm` делегирует работу между специализированными агентами. Роли должны быть узкими, а записи памяти контролироваться политиками.

### 6. Streaming API
`agent.run(query, stream=True)` возвращает OpenAI-совместимые chunks для chat UI и длинных ответов.

### 7. Самообучение агента
Самообучение следует сочетать с `MemoryPolicy`, чтобы не сохранять приватный, устаревший или нерелевантный контент.

### 8. Trace и Langfuse
LightAgent позволяет наблюдать выполнение через встроенный trace или Langfuse.

### 9. Оценка агентов
Оценка агентов будет измерять поведение в бизнес-сценариях.

### 10. Workflow LightFlow
`LightFlow` — детерминированный workflow-слой для выполнения известных шагов.

- Состояния шагов: `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- Проверка DAG: `flow.validate(strict=True)`.
- Управление шагом: `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, `approval_handler`.
- Сохранение и восстановление: `JsonLightFlowStore`, `flow.resume(run_id)`, `flow.rerun_step(run_id, step_name)`, `flow.get_run(run_id)`, `flow.list_runs()`.

См. [LightFlow](docs/lightflow.md).

### 11. Guardrails
Guardrails — легкие hooks для проверки ввода, вызовов инструментов и вывода.

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

См. [Guardrails](docs/guardrails.md).

### 12. SharedMemoryPool
`SharedMemoryPool` — in-memory прототип общей памяти между агентами, используйте его вместе с `MemoryPolicy`.

## Поддержка основных моделей агентств

LightAgent работает с OpenAI-совместимыми chat completion endpoint: OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama и собственные gateways.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

## Сценарии использования

- **Умный клиент**: Обеспечение эффективной поддержки клиентов через многоуровневое взаимодействие и интеграцию инструментов.
- **Анализ данных**: Использование дерева мышления и многослойного взаимодействия для обработки сложных задач анализа данных.
- **Автоматизация инструментов**: Быстрое создание индивидуальных инструментов через автоматическую генерацию.
- **Учебная помощь**: Обеспечение персонализированного опыта обучения с помощью модуля памяти и потокового API.

---
 
## 🛠️ Рекомендации по вкладу

Мы приветствуем любую форму вклада! Будь то код, документация, тестирование или обратная связь - всё это огромная помощь проекту. Если у вас есть хорошие идеи или вы нашли ошибку, пожалуйста, подайте заявку или Pull Request. Вот шаги по вкладке:

1. **Сделайте форк проекта**: нажмите кнопку `Fork` в правом верхнем углу, чтобы скопировать проект в ваш репозиторий GitHub.
2. **Создайте ветвь**: создайте вашу разработческую ветвь локально:  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **Подайте измененные данные**: после завершения разработки подайте ваши изменения:  
   ```bash
   git commit -m 'Добавление новой функции'
   ```
4. **Отправьте ветвь**: отправьте ветвь в ваш удалённый репозиторий:  
   ```bash
   git push origin feature/YourFeature
   ```
5. **Подайте Pull Request**: в GitHub подайте Pull Request с описанием ваших изменений.

Мы проверим ваш вклад как можно быстрее, спасибо за поддержку!❤️

---

## 🙏 Благодарности

Разработка и реализация LightAgent стали возможны благодаря вдохновению и поддержке следующих открытых проектов, особенно благодарим эти замечательные проекты и команды:

- **mem0**: Спасибо [mem0](https://github.com/mem0ai/mem0) за предоставление модуля памяти, который стал важным элементом управления контекстом для LightAgent.  
- **Swarm**: Спасибо [Swarm](https://github.com/openai/swarm) за идеи по многослойному взаимодействию агентов, которые стали основой функций LightAgent.  
- **ChatGLM3**: Спасибо [ChatGLM3](https://github.com/THUDM/ChatGLM3) за поддержку высокопроизводительных китайских моделей и идеи по проектированию.  
- **Qwen**: Спасибо [Qwen](https://github.com/QwenLM/Qwen) за поддержку высокопроизводительных китайских моделей.  
- **DeepSeek-V3**: Спасибо [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) за поддержку высокопроизводительных китайских моделей.  
- **Серия шагов**: Спасибо [step](https://www.stepfun.com/) за поддержку высокопроизводительных китайских моделей.  

---

## 📄 Лицензия

LightAgent лицензирован под [Apache 2.0 лицензией](LICENSE). Вы можете свободно использовать, изменять и распространять этот проект, но пожалуйста, соблюдайте условия лицензии.

---

## 📬 Свяжитесь с нами

Если у вас есть вопросы или предложения, команда всегда открыта для контакта:

- **Электронная почта**: service@wanxingai.com  
- **GitHub Issues**：[https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

Мы ждём ваших отзывов, чтобы вместе сделать LightAgent ещё сильнее!🚀


---

<p align="center">
  <strong>LightAgent - сделаем интеллект легче, а будущее проще.</strong> 🌈
</p>

**LightAgent** — легковесная, гибкая, мощная активная платформа агента, помогающая вам быстро разрабатывать интеллектуальные приложения!