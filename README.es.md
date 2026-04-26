
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

**LightAgent** es un marco de trabajo activo y autónomo extremadamente ligero que cuenta con memoria (`mem0`), herramientas (`Tools`) y un árbol de pensamiento (`ToT`), y es completamente de código abierto. Soporta una colaboración multiagente más simple que OpenAI Swarm, permitiendo construir agentes con capacidad de autoaprendizaje en un solo paso, y admite la conexión al protocolo MCP a través de stdio y sse. El modelo subyacente es compatible con OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen y otros grandes modelos. Al mismo tiempo, LightAgent admite la salida de servicios API en formato de flujo de OpenAI, integrándose sin problemas con los principales marcos de Chat. 🌟

---

## ✨ Características

- **Ligero y eficiente** 🚀: Diseño minimalista, implementación rápida, adecuado para diversas escalas de aplicaciones. (Sin LangChain, Sin LlamaIndex) 100% implementado en Python, sin dependencias adicionales, con solo 1000 líneas de código central, completamente de código abierto. 
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

## 🚧 Próximamente

- **Comunicación colaborativa de agentes** 🛠️: Los agentes también pueden compartir información y transmitir mensajes entre sí, logrando una comunicación de información compleja y colaboración en tareas.
- **Evaluación de Agentes** 📊: Herramienta de evaluación de agentes integrada, facilitando la evaluación y optimización del agente que construyas, alineándose con el escenario empresarial y mejorando continuamente su inteligencia.  

## Integrado “Flujo de Pensamiento”
(Thought Flow) El método a través de un proceso de pensamiento sistemático, estructurado y flexible, puede enfrentar efectivamente los desafíos en escenarios complejos.
 A continuación se presentan los pasos específicos de implementación:
```text
Definición del problema: Definir claramente el problema central y el objetivo.

Recopilación de información: Recoger información y datos relevantes de manera sistemática.

Descomposición de problemas: Descomponer problemas complejos en múltiples sub-problemas o módulos.

Análisis multidimensional: Analizar cada sub-problema desde diferentes ángulos y niveles.

Establecer asociaciones: Identificar las relaciones y dependencias entre los sub-problemas.

Generar soluciones: Proponer soluciones posibles para cada sub-problema.

Evaluación y selección: Evaluar la viabilidad y el impacto de las soluciones, seleccionando la mejor.

Implementación y retroalimentación: Implementar la solución elegida y ajustar según la retroalimentación.
```

---
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

### 1. Módulo de memoria completamente automático ( `mem0` )
LightAgent soporta la extensión externa del módulo de memoria `mem0`, permitiendo una gestión automática de la memoria contextual e histórica, sin que los desarrolladores necesiten activar manualmente la adición y búsqueda de memoria. A través del módulo de memoria, el agente puede mantener la coherencia del contexto en conversaciones múltiples.

```python
# Activar el módulo de memoria

# O utilizar un módulo de memoria personalizado, a continuación el ejemplo de mem0 https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_API_BASE"] = "your_base_url"
        # Inicializar Mem0
        config = {
            "version": "v1.1"
        }
        # En mem0 si necesitas usar qdrant como una base de datos de vectores para almacenar recuerdos, cambia la configuración a la siguiente
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
        """Almacenar recuerdo Los desarrolladores pueden modificar su implementación interna, el ejemplo actual es el método de añadir recuerdo de mem0"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """Recuperar recuerdos relevantes Los desarrolladores pueden modificar su implementación interna, el ejemplo actual es el método de búsqueda de recuerdo de mem0"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="Por favor recuerda que eres LightAgent, un asistente útil que puede ayudar a los usuarios con el uso de múltiples herramientas.",  # descripción del rol del sistema
        model="deepseek-chat",  # Modelos soportados: openai, chatglm, deepseek, qwen, etc.
        api_key="your_api_key",  # reemplazar por tu API Key del proveedor del modelo
        base_url="your_base_url",  # reemplazar por la URL API de tu proveedor del modelo
        memory=CustomMemory(),  # Habilitar función de memoria
        tree_of_thought=False,  # Habilitar cadena de pensamientos
    )

# Prueba con memoria & Si necesitas añadir herramientas puedes añadir tools al agente para habilitar la llamada de herramientas con memoria

user_id = "user_01"
logger.info("\n=========== siguiente conversación ===========")
query = "Háblame sobre los lugares interesantes en Sanya, muchos amigos han viajado a Sanya, yo también quiero ir a divertirme"
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== siguiente conversación ===========")
query = "¿A dónde debería ir de vacaciones?"
print(agent.run(query, stream=False, user_id=user_id))
```

La salida es la siguiente:
```python
=========== siguiente conversación ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
Comenzando a reflexionar sobre el problema: Háblame sobre los lugares interesantes en Sanya, muchos amigos han viajado a Sanya, yo también quiero ir a divertirme
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Respuesta final: 
Sanya es una popular ciudad turística en la provincia de Hainan, China, conocida por sus hermosas playas, clima tropical y rica variedad de recursos turísticos. Aquí algunos lugares recomendados para visitar en Sanya:

1. **Bahía Yalong**: Llamada “Hawái Oriental”, tiene largas playas de arena y aguas cristalinas, ideal para nadar, bucear y tomar el sol.

2. **Punta Tianya**: Es un famoso lugar cultural, conocido por su espléndido paisaje marino y romántica leyenda. Las enormes rocas tienen grabados las palabras "Tianya" y "Haijiao", simbolizando el amor eterno.

3. **Zona Cultural Nanshan**: Aquí se encuentra la famosa estatua de Kuan Yin de 108 metros sobre el mar, la más alta del mundo. Los turistas pueden experimentar la cultura budista visitando templos y jardines.

4. **Isla Wuzhizhou**: Esta pequeña isla es conocida por su naturaleza virgen y diversas actividades acuáticas. Los visitantes pueden practicar buceo, snorkel y pesca.

5. **Bahía Dadonghai**: Es una playa en la ciudad de Sanya, popular por su fácil acceso y animada vida nocturna.

6. **Bahía Sanya**: Esta playa de 22 kilómetros es un buen lugar para observar el atardecer. Es más tranquila, ideal para los amantes de la paz y quietud.

7. **Zona Cultural de la Selva Yanuoda**: Un parque tropical donde los turistas pueden explorar la belleza natural de la selva tropical y participar en diversas actividades de aventura.

8. **Parque Luhuitou**: Ubicado en la cima de una colina, permite vistas panorámicas de la ciudad de Sanya y la bahía de Sanya. También hay una hermosa leyenda sobre un ciervo.

9. **Isla Xidao**: Esta pequeña isla, relativamente virgen, atrae a los turistas por sus playas tranquilas y rica vida marina.

10. **La Historia de Sanya**: Un gran parque temático cultural que muestra la historia y cultura de Hainan a través de actuaciones y exposiciones.

Además de los lugares mencionados, Sanya tiene muchos otros sitios que vale la pena explorar, como jardines botánicos y mercados de mariscos. La gastronomía de Sanya también es imperdible, especialmente los mariscos frescos y las frutas tropicales. Al planear su viaje, se recomienda revisar el pronóstico del tiempo y los horarios de apertura de las atracciones para garantizar una grata experiencia.
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== siguiente conversación ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
Comenzando a reflexionar sobre el problema: ¿A dónde debería ir de vacaciones?
Se encontró recuerdo relevante:
El usuario quiere viajar a Sanya
Los amigos del usuario han viajado a Sanya.
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Respuesta final: 
Basado en la información proporcionada anteriormente por el usuario, sus amigos han viajado a Sanya y el usuario también ha mostrado interés en este destino. Por lo tanto, Sanya podría ser un lugar adecuado para que el usuario viaje. Aquí tienes información sobre los viajes a Sanya para su consideración:

### Recomendaciones para viajar a Sanya:
1. **Bahía Yalong**: Conocida como “Hawái Oriental”, tiene hermosas playas y aguas cristalinas, ideal para nadar y tomar el sol.
2. **Punta Tianya**: Un icónico punto de atracción de Sanya, famoso por sus rocas únicas y románticas leyendas que atraen a los turistas.
3. **Zona Cultural Nanshan**: Aquí se encuentran el conocido Templo Nanshan y la estatua de Kuan Yin de 108 metros, un importante punto de referencia cultural budista.
4. **Isla Wuzhizhou**: Ideal para actividades acuáticas y buceo, la isla alberga una rica vida marina y arrecifes de coral.
5. **Bahía Dadonghai**: Una playa dentro de la ciudad de Sanya, conveniente para familias y parejas.

### Otras recomendaciones:
Si el usuario ya conoce Sanya o desea explorar otros destinos, aquí hay algunos otros lugares turísticos populares:
1. **Guilin**: Famoso por su impresionante paisaje kárstico y el río Li.
2. **Lijiang**: La antigua ciudad y la montaña Yulong son sus principales atracciones, ideales para quienes disfrutan de la historia y la cultura.
3. **Zhangjiajie**: Conocido por sus singulares columnas de piedra y paisajes naturales, es un lugar de filmación de la película "Avatar".

El usuario puede elegir su destino de viaje basado en sus intereses y tiempo disponible. Si necesita más información o ayuda para planificar su viaje, ¡no dude en avisarnos!
```

### 2. Integración de herramientas (soporte para personalización ilimitada de herramientas)
Adopta la personalización de herramientas ( `Tools` ) y las integra fácilmente con el método `tools`. Estas herramientas pueden ser cualquier función de Python y soportan anotaciones de tipo de parámetros para asegurar flexibilidad y precisión. Además, ofrecemos un generador de herramientas impulsado por AI inteligente que te ayuda a construir herramientas de manera automatizada, liberando tu creatividad.

```python

import requests
from LightAgent import LightAgent

# Definir herramienta
def get_weather(
        city_name: str
) -> str:
    """
    Obtener información sobre el clima de la ciudad
    :param city_name: Nombre de la ciudad
    :return: Información sobre el clima
    """
    if not isinstance(city_name, str):
        raise TypeError("El nombre de la ciudad debe ser una cadena")

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
        ret = "¡Se produjo un error al obtener los datos del clima!\n" + traceback.format_exc()

    return str(ret)

# Definir información de la herramienta dentro de la función
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Obtener información climática actual para la ciudad especificada",
    "tool_params": [
        {"name": "city_name", "description": "Nombre de la ciudad a consultar", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    Buscar noticias según una palabra clave
    :param keyword: Palabra clave de búsqueda
    :param max_results: Número máximo de resultados devueltos, por defecto 5
    :return: Resultados de la búsqueda de noticias
    """
    results = f"A través de la búsqueda de {keyword}, encontré {max_results} informaciones relevantes"
    return str(results)

# Definir información de la herramienta dentro de la función
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "Buscar noticias según una palabra clave",
    "tool_params": [
        {"name": "keyword", "description": "Palabra clave de búsqueda", "type": "string", "required": True},
        {"name": "max_results", "description": "Número máximo de resultados devueltos", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    Obtener información del usuario
    :param user_id: ID del usuario
    :return: Información del usuario
    """
    if not isinstance(user_id, str):
        raise TypeError("El ID del usuario debe ser una cadena")

    try:
        # Supongamos que estamos usando una API de información de usuario, aquí un ejemplo de URL
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
        user_info = "¡Se produjo un error al obtener los datos del usuario!\n" + traceback.format_exc()

    return str(user_info)

# Definir información de la herramienta dentro de la función
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "Obtener información del usuario especificado",
    "tool_params": [
        {"name": "user_id", "description": "ID del usuario", "type": "string", "required": True},
    ]
}

# Herramientas personalizadas
tools = [get_weather, search_news, get_user_info]  # Incluye todas las herramientas

# Inicializar Agente
# Reemplazar con tus parámetros del modelo, api_key, base_url
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

query = "¿Cuál es el clima actual en Sanya?"
response = agent.run(query, stream=False)  # Usar agente para ejecutar la consulta
print(response)
```

### 3. Generador de herramientas `Tools`
El generador de herramientas `Tools` es un módulo que permite generar automáticamente el código de herramientas según la descripción de texto proporcionada por el usuario y guardar el código en un directorio específico. Esta función es especialmente útil para generar rápidamente herramientas de llamada a API, herramientas de procesamiento de datos, etc.

Ejemplo de uso

A continuación se muestra un ejemplo de código utilizando el generador de herramientas:

```python
import json
import os
import sys
from LightAgent import LightAgent

# Inicializar LightAgent
agent = LightAgent(
    name="Agente A",  # Nombre del agente
    instructions="Eres un agente útil.",  # Descripción del rol
    role="Por favor recuerda que eres un generador de herramientas, tu tarea es generar automáticamente el código de herramientas basado en la descripción de texto proporcionada por el usuario y guardarlo en el directorio especificado. Asegúrate de que el código generado sea preciso, utilizable y cumpla con los requisitos del usuario.",  # Descripción del rol del generador de herramientas
    model="deepseek-chat",  # Reemplazar con tu modelo. Modelos soportados: openai, chatglm, deepseek, qwen, etc.
    api_key="your_api_key",  # Reemplazar con tu API Key
    base_url="your_base_url",  # Reemplazar con la URL API
)

# Ejemplo de descripción de texto
text = """
La API de acciones de Sina proporciona la funcionalidad de obtener datos del mercado de acciones, incluyendo cotizaciones de acciones, datos de transacciones en tiempo real, datos de gráficos K, etc.

Descripción de funciones de la API de acciones de Sina
1. Obtener datos de cotización de acciones:
Datos de cotización en tiempo real: Se puede obtener la última cotización, volumen de transacciones y cambios en la cotización utilizando la API de cotización en tiempo real.
Datos de cotización de minutos: Se puede obtener los datos de transacciones por minutos, incluyendo el precio de apertura, precio de cierre, precio más alto y más bajo.

2. Obtener datos históricos de gráficos K:
Datos de gráficos K: A través de la API de gráficos K, se pueden obtener los datos de transacciones históricas, incluyendo el precio de apertura, precio de cierre, precio más alto, precio más bajo y volumen de transacciones. Se pueden seleccionar diferentes periodos de tiempo y promedios móviles según sea necesario.
Datos de ajuste: Se puede elegir obtener datos de gráficos K ajustados, incluyendo ajuste hacia adelante y ajuste hacia atrás, para analizar más precisamente las variaciones de precios de las acciones.

Ejemplo de obtención de datos de la API de acciones de Sina
1. Obtener datos de cotización de acciones:
URL de la API: http://hq.sinajs.cn/list=[código de acción]
Ejemplo: Para obtener datos de cotización en tiempo real de la acción con el código "sh600519" (Kweichow Moutai), puede usar la siguiente URL de la API: http://hq.sinajs.cn/list=sh600519
Al enviar una solicitud HTTP GET a la URL de la API anterior, recibirá una respuesta que incluye los datos de cotización en tiempo real de esa acción.

2. Obtener datos históricos de gráficos K:
URL de la API: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[código de acción]&scale=[periodo de tiempo]&ma=[periodo de promedio móvil]&datalen=[longitud de datos]
Ejemplo: Para obtener datos del gráfico K diario de la acción con el código "sh600519" (Kweichow Moutai), puede usar la siguiente URL de la API: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
Al enviar una solicitud HTTP GET a la URL de la API anterior, recibirá una respuesta que incluye los datos históricos del gráfico K de esa acción.
"""

# Construir la ruta del directorio de herramientas
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# Si el directorio de herramientas no existe, créalo
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Directorio de herramientas creado: {tools_directory}")

# Usar agente para generar el código de la herramienta
agent.create_tool(text, tools_directory=tools_directory)
```
Después de ejecutarlo, se generarán 2 archivos en el directorio de herramientas: get_stock_kline_data.py y get_stock_realtime_data.py

### 4. Árbol de Pensamiento (ToT)
Módulo de árbol de pensamiento integrado, que soporta la descomposición de tareas complejas y el razonamiento de múltiples pasos. A través del árbol de pensamiento, el agente puede manejar mejor tareas complejas.

```python
# Habilitar el árbol de pensamiento
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # Habilitar el árbol de pensamiento
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # Reemplaza con tu clave API de deepseek r1
    tot_base_url="https://api.openai.com/v1",  # url de la API
    filter_tools=False,  # Deshabilitar el mecanismo de herramientas adaptativas
)
```
Al habilitar ToT, el mecanismo de herramientas adaptativas se habilita de forma predeterminada. Si necesitas desactivarlo, agrega el parámetro filter_tools=False al inicializar LightAgent.

### 5. Colaboración multi-agente
Soporta colaboración de agentes estilo Swarm, mejorando la eficiencia del procesamiento de tareas. Múltiples agentes pueden colaborar para completar tareas complejas.

```python
from LightAgent import LightAgent, LightSwarm
# Estableciendo las variables de entorno OPENAI_API_KEY y OPENAI_BASE_URL
# El modelo predeterminado utiliza gpt-4o-mini

# Crear instancia de LightSwarm
light_swarm = LightSwarm()

# Crear múltiples Agentes
agent_a = LightAgent(
    name="Agente A",
    instructions="Soy el Agente A, el recepcionista.",
    role="Recepcionista, encargada de recibir a los visitantes y proporcionar información básica. Antes de cada respuesta, por favor identifícate; solo puedes ayudar a los usuarios a ser dirigidos a otros roles, no puedes responder directamente a las preguntas de los clientes. Si no puedes responder al problema actual, por favor responde: ¡Lo siento, no puedo ayudar en este momento!",
)

agent_b = LightAgent(
    name="Agente B",
    instructions="Soy el Agente B, encargado de la reservación de salas.",
    role="Administrador de reservaciones de salas, responsable de manejar las reservaciones, cancelaciones y consultas sobre las salas 1, 2 y 3. Antes de cada respuesta, por favor identifícate y responde de manera muy cortés a las preguntas del usuario.",
)

agent_c = LightAgent(
    name="Agente C",
    instructions="Soy el Agente C, un asistente técnico encargado de resolver problemas técnicos. Antes de cada respuesta, por favor identifícate y trata de dar respuestas lo más detalladas posible a las preguntas del usuario. Si el problema está fuera de mi alcance, por favor dirige al usuario a un soporte técnico de mayor nivel.",
    role="Especialista en soporte técnico, encargado de atender consultas sobre problemas de hardware, software y red.",
)

agent_d = LightAgent(
    name="Agente D",
    instructions="Soy el Agente D, responsable de los recursos humanos, encargado de manejar cuestiones relacionadas con recursos humanos. Antes de cada respuesta, por favor identifícate y trata de dar detalles a las consultas del usuario. Si el problema requiere seguimiento, por favor dirige al usuario al departamento de recursos humanos.",
    role="Especialista en recursos humanos, encargado de atender consultas y gestionar procesos de incorporación, salida, licencia y beneficios de empleados.",
)

# Registrar automáticamente los agentes en la instancia de LightSwarm
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# Ejecutar Agente A
res = light_swarm.run(agent=agent_a, query="Hola, soy Alice, necesito saber si Wang Xiaoming ha completado su incorporación", stream=False)
print(res)
```
La salida es la siguiente:
```python
Hola, soy el Agente D, especialista en recursos humanos. Sobre la consulta de si Wang Xiaoming ha completado su incorporación, necesito revisar nuestros registros. Por favor espera un momento.
(Revisando registros del sistema...)
Según nuestros registros, Wang Xiaoming completó su incorporación el 5 de enero de 2025. Ha firmado todos los documentos necesarios y se le ha asignado un número de empleado y un lugar de trabajo. Si necesitas más detalles o tienes otros problemas, por favor contacta al departamento de recursos humanos. Estamos aquí para ayudarte.
```

### 6. API en flujo 
Soporta salida de servicios API en formato de flujo de OpenAI, integrándose sin problemas en las principales plataformas de chat.

```python
# Habilitar salida en flujo
response = agent.run("Por favor genera un artículo sobre IA", stream=True)
for chunk in response:
    print(chunk)
```

### 7. Evaluación de Agentes (próximamente)
Herramienta de evaluación de agentes integrada que facilita la evaluación y optimización del rendimiento de los agentes.



## Soporte para modelos de agentes principales
Compatible con varios grandes modelos, incluyendo OpenAI, ChatGLM de Zhiyun, DeepSeek, la serie Qwen.

#### Modelos de grandes modelos que han sido probados y son compatibles
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
- **Issues en GitHub**: [https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

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