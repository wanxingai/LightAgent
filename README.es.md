
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
    Español | 
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    <a href="README.ja.md">日本語</a> | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>

<div align="center">
  <h1>LightAgent🚀（Próximo marco de IA Agentic）</h1>
</div>

**LightAgent** es un framework modular de código abierto para Python con Skills reutilizables, herramientas, memoria a largo plazo opcional y modelos y streaming compatibles con OpenAI. `LightSwarm` gestiona el enrutamiento, `LightFlow` los pasos conocidos y `LightDAG` las tareas dinámicas persistentes y verificadas. El runtime opcional basado en eventos añade sesiones persistentes, ejecución asíncrona, políticas y aprobaciones. MCP admite stdio, SSE y Streamable HTTP.

---

## Noticias
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-10-01]** LightAgent v0.11.0 publicado: incorpora DAG dinámicos multiagente persistentes y opcionales, artefactos inmutables sujetos a verificación, recuperación mediante leases y fencing, y un `SecurityContext` unificado con permisos que solo pueden restringirse y controles de aprobación.
- **[2026-08-15]** LightAgent v0.10.0 publicado: incorpora el runtime basado en eventos con sesiones persistentes, ejecución asíncrona, Capability Registry y Policy, Inbox, Goals, Budgets, Jobs, subagentes, compactación del contexto y búsqueda SQLite FTS5.
- **[2026-08-15]** LightAgent v0.9.7 publicado: añade un contrato Connector ligero y sin dependencias con validación sin conexión y ejemplos, amplía las comprobaciones de seguridad del ejecutor de Python, incorpora una matriz de seguridad opcional para Mem0 Graph y prepara la estabilización de v1.0 con un inventario de compatibilidad de la API pública.
- **[2026-07-30]** LightAgent v0.9.6 publicado: añade resúmenes y exportadores de trazas para producción, evaluación determinista, aprobación humana persistente para herramientas, handoffs y LightFlow, además de admisión de escritura fail-closed y auditoría para memoria gráfica compartida.
- **[2026-06-24]** LightAgent v0.9.0: añade workflows LightFlow con checkpoints, resume/rerun, nodos de aprobación, estados de paso más claros, metadatos de trace, plantillas Guardrails, controles MemoryPolicy y el prototipo SharedMemoryPool.
- **[2026-06-14]** LightAgent v0.8.1: añade convenciones MemoryScope y filtros MemoryPolicy por procedencia, alcance y confianza.
- **[2026-06-02]** LightAgent v0.8.0: introduce LightFlow para workflows deterministas de varios pasos.

Las notas históricas están en [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

---

## ✨ Características

- **Ligero y eficiente**: Framework Python modular y de código abierto, sin LangChain ni LlamaIndex, con dependencias específicas para modelos, MCP, memoria y trazas.
- **Runtime basado en eventos**: Sesiones persistentes opcionales, replay, checkpoints, llamadas asíncronas, Capability y Policy, Inbox, Goals, Budgets, Jobs, subagentes, compactación del contexto y búsqueda SQLite FTS5.
- **DAG dinámicos verificados**: LightDAG persiste cambios del grafo, ejecuta Workers independientes en paralelo y publica artefactos inmutables solo después de la verificación definida por la aplicación.
- **Soporte de memoria** 🧠: Permite a cada usuario personalizar su memoria a largo plazo, soportando nativamente el módulo de memoria `mem0`, gestionando automáticamente la memoria personalizada del usuario durante el diálogo, haciendo que el agente sea más inteligente.
- **Aprendizaje autónomo** 📚️: Cada agente tiene la capacidad de aprender de manera autónoma, y los administradores con permiso pueden gestionar cada agente.
- **Integración de herramientas** 🛠️: Permite herramientas personalizadas (`Tools`), generación automática de herramientas y expansión flexible, satisfaciendo diversas necesidades.  
- **Objetivos complejos** 🌳: Módulo de árbol de pensamiento (ToT) integrado, que soporta la descomposición de tareas complejas y razonamiento de múltiples pasos, mejorando la capacidad de procesamiento de tareas.  
- **Colaboración multi-agente** 🤖: Colaboración multi-agente de implementación más sencilla que Swarm, con LightSwarm integrado para juzgar intenciones y transferir tareas, procesando entradas de usuario más inteligentemente y transferiendo tareas a otros agentes según sea necesario. 
- **Ejecución independiente** 🤖: Ejecución autónoma de llamadas a herramientas sin intervención humana.  
- **Soporte para múltiples modelos** 🔄: Compatible con OpenAI, ChatGLM de Zhiyun, modelos de Baichuan, DeepSeek, la serie Qwen.  
- **API en flujo** 🌊: Soporta salida de servicios API en formato de flujo de OpenAI, integrándose sin problemas en las principales plataformas de chat, mejorando la experiencia del usuario.  
- **Generador de herramientas `Tools`** 🚀: Simplemente proporciona tu documentación de API al [Generador de herramientas `Tools`] y se construirá automáticamente para ti, permitiéndote crear rápidamente cientos de herramientas personalizadas en solo una hora, aumentando la eficiencia y liberando tu potencial innovador.
- **Auto-aprendizaje del agente** 🧠️: Cada agente tiene capacidad para recordar sus propios escenarios y aprender de él mismo a partir de la conversación del usuario.
- **Mecanismo de herramientas adaptativas** 🛠️: Soporta añadir herramientas ilimitadas, seleccionando primero un conjunto de herramientas candidato entre miles antes de enviar el contexto al modelo de Big Data, lo que puede reducir significativamente el consumo de tokens.
- **Orquestación de workflows** 🔁: LightFlow encadena agentes en workflows deterministas con dependencias explícitas, paso de salidas, reintentos, checkpoints, resume/rerun, aprobaciones, agentes fallback y trazabilidad.
- **Prototipo de memoria compartida** 🧠: SharedMemoryPool ofrece memoria compartida en memoria con metadatos de procedencia, recuperación por alcance y resultados compatibles con MemoryPolicy.
- **Plantillas Guardrails** 🛡️: Políticas reutilizables de entrada, herramientas y salida para bloquear datos privados, confirmar herramientas sensibles, validar parámetros de alto riesgo y redactar salidas.
- **Runtime Hooks** 🧩: Middleware ordenado `hooks=[...]` para observar, reemplazar o bloquear fases de ejecución, modelo, herramienta, memoria y pasos LightFlow.
- **Evaluación y revisión humana** 📊: `LightEvaluator` ejecuta regresiones deterministas; `HumanApprovalHook`, los review stores persistentes y los checkpoints de LightFlow permiten aprobar, rechazar, editar argumentos y registrar feedback.

## 🧭 Arquitectura de un vistazo

| Capa | API principal | Úsalo cuando necesites |
| --- | --- | --- |
| Runtime de un agente | `LightAgent` | Un agente con modelo, herramientas, memoria, streaming, trace y guardrails. |
| Estado persistente del runtime | `Session`, `AgentRuntime` | Replay, checkpoints, Inbox, Goals, Budgets, Jobs y recuperación del contexto. |
| Capa de capacidades | `CapabilityRegistry`, `PolicyEngine` | Proveedores con alcance limitado, políticas, ciclo de vida y auditoría. |
| Contexto de seguridad unificado | `SecurityContext`, `CapabilityGate`, `ApprovalToken` | Identidad, permisos que solo se reducen, autorización y aprobaciones ligadas a una operación. |
| Enrutamiento multiagente | `LightSwarm` | Delegación por roles entre agentes especializados. |
| Workflow determinista | `LightFlow` | DAG, reintentos, checkpoints, aprobaciones, resume y rerun. |
| Workflow dinámico verificado | `LightDAG` | Descomposición dinámica, verificadores, artefactos, Workers paralelos y recuperación. |
| Herramientas e integraciones | `tools`, `ToolRegistry`, MCP | Herramientas Python, generadas, carga en runtime o servidores MCP. |
| Límite de memoria | `MemoryPolicy`, `MemoryScope` | Aislamiento de tenants, procedencia, confianza, expiración y admisión de escritura. |
| Memoria compartida | `SharedMemoryPool` | Experimentos de memoria compartida entre agentes. |
| Seguridad | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Privacidad, confirmación de herramientas, parámetros de riesgo y redacción de salida. |
| Runtime hooks | `hooks`, `HookContext`, `HookDecision` | Políticas, auditoría, redacción, routing y mutación de payloads en límites del ciclo de vida. |
| Observabilidad | `trace=True`, `agent.export_trace()` | Eventos estructurados de ejecución, modelo, herramienta, error y workflow. |

## Patrones principales de uso

LightAgent mantiene simple la llamada por defecto y permite añadir controles de producción de forma incremental.

| Patrón | Llamada mínima | Notas |
| --- | --- | --- |
| Respuesta básica | `agent.run(query)` | Devuelve string por defecto. |
| Streaming | `agent.run(query, stream=True)` | Devuelve chunks compatibles con OpenAI. |
| Resultado estructurado | `agent.run(query, result_format="object")` | Devuelve contenido y metadatos. |
| Trace | `agent.run(query, trace=True)` | Registra eventos sin cambiar el string por defecto. |
| Memoria de usuario | `agent.run(query, user_id="alice")` | Usa el backend de memoria y MemoryPolicy configurados. |
| Herramientas | `LightAgent(..., tools=[fn])` | Las funciones deben exponer `tool_info`. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | Añade políticas de entrada, herramienta y salida. |
| Runtime hooks | `LightAgent(..., hooks=[fn])` | Observa, reemplaza o bloquea payloads del ciclo de vida. |
| Workflow | `LightFlow().step(...).run(query)` | Para ejecución determinista multi-etapa. |
| Workflow dinámico | `LightDAG(...).create_run(...)` | Proponer tareas y verificar resultados antes de publicarlos. |
| Sesión persistente | `agent.run(query, session_id="project-42")` | Requiere configurar un SessionStore persistente para replay y continuación. |
| Asíncrono | `await agent.arun(query)` | Entrada no bloqueante para aplicaciones asyncio. |

## v0.11.0: Workflows dinámicos verificados

Usa `LightSwarm` para enrutar por roles, `LightFlow` para pasos conocidos y el `LightDAG` opcional cuando los Workers deban proponer nuevas tareas durante la ejecución.

- `SqliteTaskGraphStore` persiste tareas, intentos, cambios del grafo, eventos y estado de recuperación. Las instancias independientes de Worker pueden ejecutarse en paralelo.
- Los Workers devuelven `TaskOutcome.candidate(...)`, `TaskOutcome.decompose(...)` o `TaskOutcome.blocked(...)`. Solo un Verifier definido por la aplicación puede aprobar una descomposición o publicar artefactos inmutables.
- Los leases y el fencing rechazan intentos obsoletos al recuperar una ejecución. `SecurityContext`, `CapabilityGate` y `ApprovalToken` vinculado a la operación explicitan identidad, permisos que solo pueden restringirse y aprobaciones.

### Ejemplo LightDAG sin conexión

No requiere modelo, clave de API ni red. Utiliza una base SQLite y un directorio de artefactos temporales que se eliminan al terminar.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from LightAgent import (
    CallableVerifier, LightDAG, LocalArtifactStore, PermissionSet,
    SecurityContext, SqliteTaskGraphStore, TaskOutcome, TaskSpec,
)

with TemporaryDirectory() as directory:
    root = Path(directory)
    store = SqliteTaskGraphStore(root / "dag.sqlite3")
    try:
        dag = LightDAG(
            store=store,
            artifact_store=LocalArtifactStore(root / "artifacts"),
            verifiers={"exact": CallableVerifier(
                "exact", lambda request: request.candidate_content == b"42",
            )},
        )
        dag.register_worker("local", lambda context: TaskOutcome.candidate("42"))
        dag.create_run([TaskSpec(
            task_id="answer", goal="42",
            acceptance_contract={"equals": "42"},
            worker_key="local", verifier_key="exact",
        )], run_id="readme-demo", context=SecurityContext(
            user_id="alice", tenant_id="demo", project_id="readme",
            permissions=PermissionSet(allowed=frozenset({"dag.task.execute"})),
        ))
        result = dag.run("readme-demo")
        assert result.success
        print(result.status.value)
    finally:
        store.close()
```

Para persistencia real, conserva rutas explícitas de base de datos y artefactos en lugar de directorios temporales. El [ejemplo completo de descomposición y reparación](example/14.dynamic_dag.py) y la [guía LightDAG](docs/lightdag.md) cubren dependencias, integración, reintentos y recuperación.

La [guía del runtime](docs/runtime_v010.md) explica sesiones persistentes, llamadas asíncronas, Capability Providers, Policy, Inbox, Goals, Budgets y Jobs.

### Compatibilidad y límites de seguridad

- `agent.run(query)`, `stream=True` y `user_id` siguen disponibles. LightDAG es opcional y no sustituye a LightFlow.
- v0.11.0 se limita a un host, SQLite local y un planificador activo por ejecución. La ejecución es al menos una vez; los efectos externos requieren idempotencia. No incluye Workers distribuidos, interfaz web ni sandbox de código integrado.
- Los antiguos `execute_python_code`, `execute_python_file` y `execute_python_code_stream` están bloqueados en la ejecución de herramientas del modelo, incluso con `enable_unsafe_python=True` o un `SandboxProvider` registrado. Usa `safe_expression` o una herramienta realmente aislada; la llamada directa a estas utilidades no es un sandbox de seguridad.
- Siguen siendo necesarias las políticas de procedencia, admisión y promoción de memoria. Las pruebas del framework no certifican un backend real de memoria gráfica compartida; consulta [seguridad de memoria](docs/memory_security.md).

### Versión publicada y main actual

[v0.11.0](https://github.com/wanxingai/LightAgent/releases/tag/v0.11.0) se publicó el 2026-10-01. Las correcciones posteriores de JSON de selección de herramientas, MCP SDK 1.x/2.x y el ejemplo opcional deed.page se integraron después de ese tag y pueden no estar en el paquete publicado. El siguiente comando instala `main` actual, no el tag original:

```bash
pip install --upgrade "git+https://github.com/wanxingai/LightAgent.git@main"
```

Consulta [Tools Guide](docs/tools.md), el [adaptador Memcode](docs/memcode_memory_adapter.md) opcional, el [ejemplo deed.page](docs/deed_page_mcp.md) y el [inventario de compatibilidad pública](docs/public_api_compatibility.md). Estos servicios externos no son un requisito del runtime principal.

## 📋 Documentación

- Para instalación, modelos, herramientas, memoria, MCP, Skills, streaming y LightSwarm, consulta [FAQ](docs/FAQ.md).
- Para workflows deterministas, checkpoints, resume/rerun, aprobaciones, fallback agents y estados de paso, consulta [LightFlow](docs/lightflow.md).
- Para herramientas personalizadas, ToolRegistry, ToolLoader, AsyncToolDispatcher y MCP, consulta [Tools Guide](docs/tools.md).
- Para memoria compartida o memoria de grafo, consulta [Memory Security Guidance](docs/memory_security.md).
- Para SharedMemoryPool, consulta [SharedMemoryPool](docs/shared_memory_pool.md).
- Para admisión de escritura de memoria y expiración, consulta [Memory Admission And Mutation Controls](docs/memory_admission.md).
- Para seguridad de entrada, herramientas y salida, consulta [Guardrails](docs/guardrails.md).
- Para middleware runtime que observa, reemplaza o bloquea payloads, consulta [Runtime Hooks](docs/runtime_hooks.md).
- Para OpenRouter, modelos locales y proveedores compatibles con OpenAI, consulta [Model Provider Configuration](docs/model_providers.md).
- Para trazas estructuradas, consulta [Trace Observability](docs/tracing.md).
- Para regresiones deterministas, consulta [Evaluation Harness](docs/evaluation.md).
- Para aprobación de herramientas/handoffs, revisión persistente y feedback, consulta [Human Review](docs/human_review.md).

## Hoja de ruta

Consulta la [hoja de ruta](roadmap.md) para los hitos entregados y los planes futuros. Inbox, Jobs y subagentes ya están disponibles en el runtime opcional.

## 🌟 ¿Por qué elegir LightAgent?

- **Código abierto y gratuito** 💖: Completamente de código abierto, impulsado por la comunidad, actualizaciones continuas, ¡contribuciones bienvenidas!  
- **Fácil de usar** 🎯: Documentación detallada, ejemplos abundantes, integración rápida y sencilla en tu proyecto.  
- **Soporte comunitario** 👥: Comunidad activa de desarrolladores, lista para ayudarte y responder a tus preguntas.  
- **Alto rendimiento** ⚡: Diseño optimizado, funcionamiento eficiente, capaz de satisfacer demandas de alta concurrencia.  

---

## 🛠️ Comenzar rápido

### Instalar la última versión de LightAgent

```bash
pip install lightagent
```

(Instalación opcional) Instalar el paquete Mem0 a través de pip:

```bash
pip install mem0ai
```

O puedes utilizar Mem0 con un solo clic en la plataforma de alojamiento, [haz clic aquí](https://www.mem0.ai/).


### Ejemplo de código Hello world

```python
from LightAgent import LightAgent

# Inicializar el Agente
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url= "your_base_url")

# Ejecutar el Agente
response = agent.run("Hola, ¿quién eres?")
print(response)
```

### Inspeccionar un trace de ejecución (v0.7.0)

Trace es opcional y mantiene compatible el comportamiento por defecto de `agent.run()`.

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

### Guardar checkpoint de una ejecución LightFlow (v0.9.0)

`LightFlow` puede persistir checkpoints y reanudar ejecuciones fallidas sin empezar desde el primer paso.

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

### Usar SharedMemoryPool (v0.9.0)

`SharedMemoryPool` es un prototipo ligero en memoria para experimentos de memoria compartida multiagente.

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


### Establecer la auto-consciencia del modelo mediante el prompt del sistema

```python
from LightAgent import LightAgent

# Inicializar el Agente
agent = LightAgent(
     role="Por favor recuerda que eres LightAgent, un asistente útil que puede ayudar a los usuarios a utilizar múltiples herramientas.",  # descripción del rol del sistema
     model="deepseek-chat",  # Modelos soportados: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # reemplazar por tu API Key del proveedor del modelo
     base_url="your_base_url",  # reemplazar por la URL API de tu proveedor del modelo
 )
# Ejecutar el Agente
response = agent.run("¿Quién eres?")
print(response)
```

### Ejemplo de código utilizando herramientas

```python
from LightAgent import LightAgent

# Definir herramienta
def get_weather(city_name: str) -> str:
    """
    Obtener el clima actual para `city_name`
    """
    return f"Resultado de consulta: El clima en {city_name} es soleado"
# Definir información de la herramienta dentro de la función
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Obtener información climática actual para la ciudad especificada",
    "tool_params": [
        {"name": "city_name", "description": "Nombre de la ciudad a consultar", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Inicializar el Agente
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# Ejecutar el Agente
response = agent.run("Ayúdame a consultar sobre el clima en Shanghái")
print(response)
```
Soporta una cantidad ilimitada de herramientas personalizadas.

Ejemplo de múltiples herramientas: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## Detalle de funciones

README conserva el modelo de uso central; los ejemplos largos, configuración de adaptadores y prácticas de producción viven en la documentación dedicada.

### 1. Módulo de memoria desmontable (`mem0`)
LightAgent acepta cualquier backend de memoria que implemente `store(data, user_id)` y `retrieve(query, user_id)`. Usa `user_id` para aislar conversaciones y `MemoryPolicy` cuando la memoria se comparte entre usuarios, tenants, agentes o traces.

### 2. Integración de herramientas
Usa funciones Python con metadatos `tool_info` para exponer capacidades controladas al agente. Para runtime tools, ToolRegistry, ToolLoader, AsyncToolDispatcher y MCP, consulta [Tools Guide](docs/tools.md).

### 3. Generador de herramientas
`agent.create_tool()` puede generar código de herramientas desde documentación de API o descripciones naturales. Revisa y prueba las herramientas antes de producción.

### 4. Árbol de Pensamiento (ToT)
Activa `tree_of_thought=True` cuando una tarea requiere planificación explícita, reflexión y selección de herramientas.

### 5. Colaboración multiagente
`LightSwarm` delega trabajo entre agentes especializados. Mantén roles claros y limita escrituras de memoria entre agentes con políticas.

### 6. API streaming
`agent.run(query, stream=True)` devuelve chunks compatibles con OpenAI para interfaces de chat y respuestas largas.

### 7. Autoaprendizaje del agente
El autoaprendizaje debe combinarse con memoria y `MemoryPolicy` para evitar contenido privado, vencido o irrelevante.

### 8. Trace y Langfuse
LightAgent permite observar la ejecución con traces internos o configuración Langfuse.

### 9. Evaluación de agentes
`LightEvaluator` mide salida, selección de herramientas, eventos de política, recuperación, latencia, usage y coste estimado.

### 10. Workflows LightFlow
`LightFlow` es la capa de workflow determinista para ejecutar tareas por pasos conocidos.

- Estados de paso: `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- Validación DAG: `flow.validate(strict=True)`.
- Controles de paso: `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, `approval_handler`.
- Persistencia y recuperación: `JsonLightFlowStore`, `flow.resume(run_id)`, `flow.rerun_step(run_id, step_name)`, `flow.get_run(run_id)`, `flow.list_runs()`.

Consulta [LightFlow](docs/lightflow.md).

### 11. Guardrails
Guardrails son hooks ligeros alrededor de la ejecución: entrada, herramientas y salida.

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

Consulta [Guardrails](docs/guardrails.md).

### 12. SharedMemoryPool
`SharedMemoryPool` es un prototipo en memoria para memoria compartida multiagente; combínalo con `MemoryPolicy`.

## Soporte para modelos de agentes principales

LightAgent funciona con endpoints chat completion compatibles con OpenAI: OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama y gateways propios.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

## Casos de uso

- **Atención al cliente inteligente**: A través de conversaciones múltiples y la integración de herramientas, ofrecer soporte eficiente al cliente.
- **Análisis de datos**: Utilizando árboles de pensamiento y colaboración multi-agente para manejar tareas complejas de análisis de datos.
- **Herramientas automatizadas**: A través de la generación automática de herramientas, construir rápidamente herramientas personalizadas.
- **Asistencia educativa**: A través de módulos de memoria y API en flujo, proporcionar experiencias de aprendizaje personalizadas.

---
 
## 🛠️ Guía de contribuciones

¡Damos la bienvenida a cualquier forma de contribución! Ya sea código, documentación, pruebas o comentarios, ¡cada aportación es de gran ayuda para el proyecto! Si tienes buenas ideas o encuentras errores, por favor presenta un Issue o un Pull Request. A continuación se presentan los pasos para contribuir:

1. **Fork este proyecto**: Haz clic en el botón `Fork` en la parte superior derecha para copiar el proyecto a tu repositorio de GitHub.
2. **Crear una rama**: Crea tu rama de desarrollo local:  
   ```bash
   git checkout -b feature/TuCaracterística
   ```
3. **Enviar cambios**: Después de completar el desarrollo, envía tus cambios:  
   ```bash
   git commit -m 'Agregar alguna característica'
   ```
4. **Enviar la rama**: Envía tu rama a tu repositorio remoto:  
   ```bash
   git push origin feature/TuCaracterística
   ```
5. **Enviar Pull Request**: En GitHub, envía un Pull Request y describe los cambios realizados.

Revisaremos tu contribución a la mayor brevedad posible, ¡gracias por tu apoyo!❤️

---

## 🙏 Agradecimientos

El desarrollo e implementación de LightAgent no hubiera sido posible sin la inspiración y apoyo de los siguientes proyectos de código abierto, agradecimientos especiales a estos excepcionales proyectos y equipos:

- **mem0**: Agradecimientos a [mem0](https://github.com/mem0ai/mem0) por proporcionar el módulo de memoria que soporta fuertemente la gestión del contexto de LightAgent.  
- **Swarm**: Agradecimientos a [Swarm](https://github.com/openai/swarm) por la idea de diseño de colaboración multi-agente que establece la base de la funcionalidad multi-agente en LightAgent.  
- **ChatGLM3**: Agradecimientos a [ChatGLM3](https://github.com/THUDM/ChatGLM3) por el apoyo en modelos grandes de alto rendimiento en chino y la inspiración en el diseño.  
- **Qwen**: Agradecimientos a [Qwen](https://github.com/QwenLM/Qwen) por el soporte en modelos grandes de alto rendimiento en chino.  
- **DeepSeek-V3**: Agradecimientos a [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) por el soporte en modelos grandes de alto rendimiento en chino.  
- **StepFun**: Agradecimientos a [step](https://www.stepfun.com/) por el soporte en modelos grandes de alto rendimiento en chino.  

---

## 📄 Licencia

LightAgent utiliza la [Licencia Apache 2.0](LICENSE). Puedes usar, modificar y distribuir este proyecto libremente, pero asegúrate de cumplir con los términos de la licencia.

---

## 📬 Contáctanos

Si tienes alguna pregunta o sugerencia, no dudes en contactarnos:

- **Correo electrónico**: service@wanxingai.com  
- **Issues en GitHub**: [https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

Esperamos tus comentarios para hacer de LightAgent un proyecto aún más fuerte.🚀

- **Más herramientas** 🛠️: Integrando continuamente más herramientas útiles para satisfacer más necesidades.
- **Más soporte de modelos** 🔄: Ampliando continuamente el soporte para más grandes modelos para más escenarios de aplicación.
- **Más funcionalidades** 🎯: Más funciones útiles, actualizaciones continuas, ¡mantente atento!
- **Más documentación** 📚: Documentación detallada y ejemplos abundantes, fácil integración en tu proyecto.
- **Más soporte comunitario** 👥: Comunidad activa de desarrolladores, lista para ayudarte y responder a tus preguntas.
- **Más optimización de rendimiento** ⚡: Continuamente optimizando el rendimiento para satisfacer las demandas de alta concurrencia.
- **Más contribuciones de código abierto** 🌟: Bienvenidas las contribuciones de código, ¡unámonos para crear un mejor LightAgent!

---

<p align="center">
  <strong>LightAgent - Hace que la inteligencia sea más ligera y el futuro más simple.</strong> 🌈
</p>

 
**LightAgent** —— Un marco Agentic ligero, flexible y potente, ¡te ayuda a construir aplicaciones inteligentes rápidamente!
