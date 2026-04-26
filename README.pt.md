
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
    <a href="README.ko.md">한국어</a> | 
    Português | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
<div align="center">
  <h1>LightAgent🚀（Próxima geração de estrutura de IA Agentic）</h1>
</div>

**LightAgent** é uma estrutura ativa e autônoma extremamente leve com memória (`mem0`), ferramentas (`Tools`) e árvore de pensamento (`ToT`), e é totalmente de código aberto. Ele suporta uma colaboração multiagente mais simples do que o OpenAI Swarm, permitindo a construção de agentes com capacidade de autoaprendizado em um único passo, e suporta a conexão ao protocolo MCP via stdio e sse. O modelo subjacente suporta OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen e outros grandes modelos. Além disso, o LightAgent suporta a saída de serviços de API em formato de fluxo da OpenAI, integrando-se perfeitamente a várias estruturas de chat populares. 🌟

---

## ✨ Funcionalidades

- **Leve e eficiente** 🚀: Design minimalista, implementação rápida, adequado para vários cenários de aplicação. (Sem LangChain, Sem LlamaIndex) Implementação 100% em Python, sem dependências adicionais, com apenas 1000 linhas de código principal, totalmente open source.
- **Suporte a memória** 🧠: Suporte a customização de memória de longo prazo para cada usuário, com o módulo de memória `mem0`, gerenciando automaticamente memórias personalizadas do usuário durante o diálogo, tornando o agente mais inteligente.
- **Aprendizado autônomo** 📚️: Cada agente tem a capacidade de aprender de forma autônoma, enquanto administradores com permissões podem gerenciar cada agente.
- **Integração de ferramentas** 🛠️: Suporte a ferramentas personalizadas (`Tools`), geração automatizada de ferramentas, flexibilidade para atender a diversas necessidades.
- **Objetivos complexos** 🌳: Módulo de árvore de raciocínio (ToT) incorporado, suportando decomposição de tarefas complexas e raciocínio em múltiplos passos, aprimorando a capacidade de lidar com tarefas.
- **Colaboração multiagente** 🤖: Colaboração multiagente mais simples de implementar do que o Swarm, com LightSwarm incorporado para avaliação de intenções e transferência de tarefas, capaz de processar entradas de usuário de forma mais inteligente e transferir tarefas para outros agentes conforme necessário.
- **Execução independente** 🤖: Conclusão autônoma da chamada de ferramentas sem intervenção humana.
- **Suporte a múltiplos modelos** 🔄: Compatível com OpenAI, ChatGLM, Baichuan, DeepSeek e séries de modelos Qwen.
- **API em tempo real** 🌊: Suporte à saída de serviços de API em formato de fluxo OpenAI, integrado perfeitamente aos principais frameworks de chat, melhorando a experiência do usuário.
- **Gerador de ferramentas** 🚀: Basta fornecer sua documentação de API ao [gerador de ferramentas], que ele criará automaticamente suas ferramentas personalizadas, permitindo a construção rápida de centenas de ferramentas personalizadas em apenas 1 hora, aumentando a eficiência e liberando seu potencial criativo.
- **Auto-aprendizado de agentes** 🧠️: Cada agente terá sua própria capacidade de memória de cenário, permitindo o aprendizado autônomo a partir das interações do usuário.
- **Mecanismo adaptativo de ferramentas** 🛠️: Suporte à adição de ferramentas em quantidade ilimitada, permitindo que o modelo grande selecione um conjunto de ferramentas candidatas entre milhares de opções, filtrando as irrelevantes antes de enviar o contexto para o modelo grande, reduzindo significativamente o consumo de tokens.


## 🚧 Em breve

- **Comunicação colaborativa entre agentes** 🛠️: Os agentes também podem compartilhar informações e transmitir mensagens, realizando comunicações complexas de informações e colaboração em tarefas.
- **Avaliação de agentes** 📊: Ferramenta de avaliação de agentes embutida, facilitando a avaliação e otimização do agente que você criou, alinhando-se aos cenários de negócios e melhorando continuamente o nível de inteligência.


## Integração do "Fluxo de Pensamento"
Método através de um processo de pensamento sistemático, estruturado e flexível que pode lidar efetivamente com desafios em cenários complexos.
 As etapas específicas de implementação são:
```text
Definição do problema: Esclarecer o problema central e os objetivos.

Coleta de informações: Coletar sistematicamente informações e dados relevantes.

Decomposição do problema: Dividir problemas complexos em múltiplas sub-tarefas ou módulos.

Análise multidimensional: Analisar cada sub-tarefa sob diferentes perspectivas e níveis.

Estabelecer conexões: Identificar as relações e dependências entre as sub-tarefas.

Geração de soluções: Propor possíveis soluções para cada sub-tarefa.

Avaliação e seleção: Avaliar a viabilidade e o impacto de cada solução e escolher a melhor.

Implementação e feedback: Implementar a solução selecionada e fazer ajustes com base no feedback.
```

---
## 🌟 Por que escolher o LightAgent?

- **Open source e gratuito** 💖: Totalmente open source, dirigido pela comunidade, atualizações contínuas, contribuições são bem-vindas!  
- **Fácil de usar** 🎯: Documentação detalhada, exemplos ricos, fácil integração ao seu projeto.  
- **Suporte da comunidade** 👥: Comunidade de desenvolvedores ativa, pronta para ajudar e responder a suas perguntas.  
- **Alto desempenho** ⚡: Design otimizado, operação eficiente, atendendo a necessidades de alto tráfego.  

---

## 🛠️ Começando rapidamente

### Instale a versão mais recente do LightAgent

```bash
pip install lightagent
```

(Instalação opcional) Instale o pacote Mem0 via pip:

```bash
pip install mem0ai
```

Ou você pode usar o Mem0 em uma plataforma de hospedagem clicando [aqui](https://www.mem0.ai/).


### Exemplo de código Hello world

```python
from LightAgent import LightAgent

# Inicializa o Agente
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url= "your_base_url")

# Executa o Agente
response = agent.run("Olá, quem é você?")
print(response)
```

### Definindo a auto-percepção do modelo através do sistema de prompt

```python
from LightAgent import LightAgent

# Inicializa o Agente
agent = LightAgent(
     role="Por favor, lembre-se de que você é o LightAgent, um assistente útil que pode ajudar os usuários com o uso de múltiplas ferramentas.",  # descrição do papel do sistema
     model="deepseek-chat",  # modelos suportados: openai, chatglm, deepseek, qwen, etc.
     api_key="your_api_key",  # substitua pela chave de API de seu fornecedor de modelo grande
     base_url="your_base_url",  # substitua pela URL API de seu fornecedor de modelo grande
 )
# Executa o Agente
response = agent.run("Quem é você?")
print(response)
```

### Exemplo de código usando ferramentas

```python
from LightAgent import LightAgent


# Define a ferramenta
def get_weather(city_name: str) -> str:
    """
    Obtém o clima atual para `city_name`
    """
    return f"Resultado da consulta: O clima em {city_name} está ensolarado."
# Informações de ferramenta definidas dentro da função
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Obtém as informações climáticas atuais para a cidade especificada",
    "tool_params": [
        {"name": "city_name", "description": "Nome da cidade a ser consultada", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# Inicializa o Agente
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

# Executa o Agente
response = agent.run("Por favor, verifique a situação do clima em Xangai.")
print(response)
```
Suporte a um número ilimitado de ferramentas personalizadas.

Exemplos de múltiplas ferramentas: tools = [search_news,get_weather,get_stock_realtime_data,get_stock_kline_data]

---

## Explicação das funcionalidades

### 1. Módulo de memória totalmente automático (`mem0`)
LightAgent suporta a extensão externa do módulo de memória `mem0`, gerenciando automaticamente o contexto e o histórico sem intervenção manual. Com o módulo de memória, o Agente pode manter consistência de contexto em diálogos contínuos.

```python
# Ativando o módulo de memória

# Ou usando um módulo de memória personalizado, abaixo um exemplo com mem0 https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_API_BASE"] = "your_base_url"
        # Inicializa o Mem0
        config = {
            "version": "v1.1"
        }
        # Se você deseja usar o qdrant como banco de dados vetorial para armazenamento de memória, altere a configuração para o código abaixo
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
        """Armazena a memória, desenvolvedores podem modificar a implementação de armazenamento, este exemplo é da função de adicionar memória do mem0"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """Recupera a memória relevante, desenvolvedores podem modificar a implementação, este exemplo é da função de busca de memória do mem0"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="Por favor, lembre-se de que você é o LightAgent, um assistente útil que pode ajudar os usuários com o uso de múltiplas ferramentas.",  # descrição do papel do sistema
        model="deepseek-chat",  # suportando modelos: openai, chatglm, deepseek, qwen, etc.
        api_key="your_api_key",  # substitua pela chave de API do seu provedor de modelo grande
        base_url="your_base_url",  # substitua pela URL API do seu provedor de modelo grande
        memory=CustomMemory(),  # habilita a funcionalidade de memória
        tree_of_thought=False,  # habilita a cadeia de pensamento
    )

# Teste com memória & se precisar adicionar ferramentas, você pode adicionar ferramentas ao agente para habilitar chamadas de ferramentas com memória

user_id = "user_01"
logger.info("\n=========== próxima conversa ===========")
query = "Quais são os pontos turísticos interessantes em Sanya? Muitos amigos ao meu redor foram a Sanya e eu também quero ir."
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== próxima conversa ===========")
query = "Aonde eu deveria viajar?"
print(agent.run(query, stream=False, user_id=user_id))
```

A saída será:
```python
=========== próxima conversa ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
Começando a pensar no problema: Quais são os pontos turísticos interessantes em Sanya? Muitos amigos ao meu redor foram a Sanya e eu também quero ir.
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - Resposta Final: 
Sanya é uma cidade turística popular na província de Hainan, China, famosa por suas belas praias, clima tropical e recursos turísticos ricos. Aqui estão alguns pontos turísticos que valem a pena visitar em Sanya:

1. **Baía de Yalong**: Conhecida como a "Hawaii Oriental", possui uma longa praia e águas cristalinas, ideal para nadar, mergulhar e tomar sol.

2. **Cantos do Mundo**: Um famoso ponto turístico cultural, atraindo visitantes com sua bela vista do mar e lendas românticas. As enormes rochas aqui têm as palavras "Cantos" e "Mundo" esculpidas, simbolizando amor eterno.

3. **Área Cultural Turística de Nanshan**: Um local com uma estátua de Guanyin do Mar de Nanshan com 108 metros de altura, a maior do mundo. Os visitantes podem experimentar a cultura budista, visitando templos e jardins.

4. **Ilha de Wuzhizhou**: Uma pequena ilha famosa por sua paisagem natural intocada e diversas atividades aquáticas. Os visitantes podem mergulhar, praticar snorkeling e pesca em alto-mar aqui.

5. **Baía de Dadonghai**: Uma praia no centro da cidade de Sanya, muito apreciada por sua facilidade de acesso e vibrante vida noturna.

6. **Baía de Sanya**: Uma praia de 22 km de extensão, excelente para admirar o pôr do sol. A praia é mais tranquila, ideal para visitantes que preferem sossego.

7. **Área Cultural da Floresta Tropical de Yanoda**: Um parque de floresta tropical onde os visitantes podem experimentar a beleza natural da floresta e participar de várias atividades de aventura.

8. **Parque de Lu Hui Tou**: Um parque localizado no topo da montanha, oferecendo vistas panorâmicas da cidade de Sanya e da baía de Sanya. Aqui, também existe uma bela lenda sobre cervos.

9. **Ilha de Xijiao**: Uma pequena ilha mais intocada, famosa por suas praias tranquilas e rica vida marinha que atraem turistas.

10. **Sanya Qian Gu Qing**: Um grande parque temático cultural que apresenta a história e cultura de Hainan por meio de performances e exposições.

Além dos pontos turísticos mencionados, Sanya também possui muitos outros lugares que merecem ser explorados, como o Jardim Botânico Tropical e o Mercado de Frutos do Mar. A culinária de Sanya também é imperdível, especialmente os frutos do mar frescos e as frutas tropicais. Ao planejar a viagem, é aconselhável verificar a previsão do tempo e os horários de funcionamento dos pontos turísticos para garantir uma experiência agradável.
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== próxima conversa ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
Começando a pensar no problema: Aonde eu deveria viajar?
Encontrou memória relevante:
Usuário quer viajar para Sanya.
Amigos do usuário viajaram para Sanya.
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - Resposta Final: 
Com base nas informações previamente mencionadas pelo usuário, seus amigos já viajaram para Sanya, e o usuário também expressou interesse em Sanya. Portanto, Sanya pode ser um destino adequado para o usuário. Aqui estão algumas informações sobre viagens para Sanya, para referência do usuário:

### Recomendações de viagem para Sanya:
1. **Baía de Yalong**: Conhecida como a "Hawaii Oriental", possui belas praias e águas cristalinas, ideal para nadar e tomar sol.
2. **Cantos do Mundo**: Um ponto turístico icônico de Sanya, atrai visitantes com suas rochas únicas e lenda romântica.
3. **Área Cultural de Nanshan**: Lar do famoso templo Nanshan e da estátua de Guanyin do Mar de 108 metros, é um ponto importante da cultura budista.
4. **Ilha de Wuzhizhou**: Ideal para mergulho e atividades marinhas, a ilha tem uma rica vida marinha e recifes de corais.
5. **Baía de Dadonghai**: Uma praia na cidade de Sanya, de fácil acesso, popular entre famílias e casais.

### Outras recomendações:
Se o usuário já está familiarizado com Sanya ou deseja explorar outros destinos, aqui estão alguns outros locais turísticos populares:
1. **Guilin**: Famosa por sua geologia karstica única e paisagem do Rio Li.
2. **Lijiang**: A antiga cidade e montanha Yuolong são os principais pontos turísticos, perfectos para quem gosta de história e cultura, assim como de natureza.
3. **Zhangjiajie**: Conhecida por suas colunas de pedra únicas e paisagens naturais, é um dos locais filmados em "Avatar".

O usuário pode escolher um destino de viagem apropriado com base em seus interesses e cronograma. Se o usuário precisar de mais informações ou ajuda com o planejamento da viagem, sinta-se à vontade para avisar!
```

### 2. Integração de ferramentas (suporte à customização ilimitada)
Abrace a personalização de ferramentas (`Tools`), integrando facilmente suas ferramentas personalizadas por meio do método `tools`. Essas ferramentas podem ser quaisquer funções Python e suportam anotações de tipo de parâmetro para garantir flexibilidade e precisão. Além disso, oferecemos um gerador de ferramentas inteligente acionado por IA, ajudando você a automatizar a criação de ferramentas e liberando sua criatividade.

```python

import requests
from LightAgent import LightAgent

# Definindo a ferramenta
def get_weather(
        city_name: str
) -> str:
    """
    Obtém informações sobre o clima da cidade
    :param city_name: Nome da cidade
    :return: Informações sobre o clima
    """
    if not isinstance(city_name, str):
        raise TypeError("O nome da cidade deve ser uma string")

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
        ret = "Erro ao buscar dados do clima!\n" + traceback.format_exc()

    return str(ret)
# Informações da ferramenta definidas dentro da função
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "Obtém as informações climáticas atuais para a cidade especificada",
    "tool_params": [
        {"name": "city_name", "description": "Nome da cidade a ser consultada", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    Busca notícias com base em palavras-chave
    :param keyword: Palavra-chave de busca
    :param max_results: Número máximo de resultados a serem retornados, padrão é 5
    :return: Resultados da busca de notícias
    """
    results = f"Encontrei {max_results} informações relacionadas à busca por {keyword}"
    return str(results)

# Informações da ferramenta definidas dentro da função
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "Busca notícias com base em palavras-chave",
    "tool_params": [
        {"name": "keyword", "description": "Palavra-chave de busca", "type": "string", "required": True},
        {"name": "max_results", "description": "Número máximo de resultados a serem retornados", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    Obtém informações sobre o usuário
    :param user_id: ID do usuário
    :return: Informações sobre o usuário
    """
    if not isinstance(user_id, str):
        raise TypeError("O ID do usuário deve ser uma string")

    try:
        # Supondo o uso de uma API de informações do usuário, aqui é um exemplo de URL
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
        user_info = "Erro ao buscar dados do usuário!\n" + traceback.format_exc()

    return str(user_info)

# Informações da ferramenta definidas dentro da função
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "Obtém as informações de um usuário específico",
    "tool_params": [
        {"name": "user_id", "description": "ID do usuário", "type": "string", "required": True},
    ]
}

# Ferramentas personalizadas
tools = [get_weather, search_news, get_user_info]  # Inclui todas as ferramentas

# Inicializa o Agente
# Substitua pelos parâmetros do seu modelo, chave de API e URL base
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url= "your_base_url", tools=tools)

query = "Qual é o clima atual em Sanya?"
response = agent.run(query, stream=False)  # Usa o agente para executar a consulta
print(response)
```

### 3. Gerador de ferramentas
O gerador de ferramentas é um módulo para automatizar a geração de código de ferramentas. Ele pode gerar automaticamente o código correspondente com base na descrição fornecida pelo usuário e salvá-lo em um diretório especificado. Este recurso é especialmente útil para a rápida geração de ferramentas de chamadas de API, ferramentas de processamento de dados, e outros cenários.

Exemplo de uso

Aqui está um exemplo de código usando o gerador de ferramentas:

```python
import json
import os
import sys
from LightAgent import LightAgent

# Inicializa o LightAgent
agent = LightAgent(
    name="Agente A",  # Nome do agente
    instructions="Você é um agente útil.",  # Descrição do papel
    role="Por favor, lembre-se de que você é um gerador de ferramentas, sua tarefa é gerar automaticamente o código de ferramentas com base na descrição fornecida pelo usuário e salvá-lo no diretório especificado. Certifique-se de que o código gerado seja preciso, utilizável e atenda às necessidades do usuário.",  # Descrição do papel do gerador de ferramentas
    model="deepseek-chat",  # Substitua pelo seu modelo. Modelos suportados: openai, chatglm, deepseek, qwen, etc.
    api_key="your_api_key",  # Substitua pela sua chave de API
    base_url="your_base_url",  # Substitua pela sua URL API
)

# Descrição de texto exemplo
text = """
A interface de ações de ações da Sina fornece a funcionalidade de obter dados do mercado de ações, incluindo cotações de ações, dados de negociação em tempo real, dados de gráficos de K-line, etc.

Introdução à interface de ações da Sina
1. Obter dados de cotações de ações:
Dados de cotações em tempo real: usando a API de cotações em tempo real é possível obter a última cotação, volume de negociação, variação percentual, etc.
Dados de K-line por minuto: usando a API de K-line por minuto, é possível obter dados de negociação gradativos da ação, incluindo preço de abertura, preço de fechamento, preço mais alto, preço mais baixo, etc.

2. Obter dados históricos do gráfico de K-line das ações:
Dados de K-line: por meio da API de K-line é possível obter dados de negociação históricos da ação, incluindo preço de abertura, preço de fechamento, preço mais alto, preço mais baixo, volume de negociação, etc. Os ciclos de tempo e média móvel podem ser selecionados conforme necessário.
Dados de ajuste: escolha obter dados de gráficos de K-line ajustados, incluindo ajustes reversos e pós-ajuste, para uma análise mais precisa das alterações de preço das ações.

Exemplos de obtenção de dados da interface de ações da Sina
1. Obter dados de cotações de ações:
URL da API: http://hq.sinajs.cn/list=[código da ação]
Exemplo: Para obter dados de cotações em tempo real da ação com código "sh600519" (Kweichow Moutai), use a URL: http://hq.sinajs.cn/list=sh600519
Ao enviar um pedido HTTP GET para a URL da API mencionada, você receberá uma resposta contendo dados de cotações em tempo real dessa ação.

2. Obter dados históricos do gráfico de K-line de ações:
URL da API: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[código da ação]&scale=[ciclo de tempo]&ma=[ciclo da média móvel]&datalen=[comprimento dos dados]
Exemplo: Para obter dados diários do gráfico de K-line da ação com código "sh600519" (Kweichow Moutai), use a URL: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
Ao enviar um pedido HTTP GET para essa URL da API, você receberá uma resposta contendo dados históricos do gráfico de K-line dessa ação.
"""

# Constrói o caminho do diretório tools
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# Cria o diretório de tools se não existir
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Diretório de ferramentas criado: {tools_directory}")

# Usa o agente para gerar o código da ferramenta
agent.create_tool(text, tools_directory=tools_directory)
```
Após a execução, ele gerará 2 arquivos no diretório de ferramentas: get_stock_kline_data.py e get_stock_realtime_data.py

### 4. Árvore de Pensamento (ToT)
Módulo de árvore de raciocínio embutido, suportando decomposição de tarefas complexas e raciocínio em múltiplos passos. Com a árvore de raciocínio, o agente pode lidar melhor com tarefas complexas.

```python
# Ativar árvore de pensamento
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # Ativar árvore de pensamento
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # Substitua pela sua chave de API do deepseek r1
    tot_base_url="https://api.openai.com/v1",  # url da API
    filter_tools=False,  # Desativar mecanismo de ferramentas adaptativas
)
```
Após ativar o ToT, o mecanismo de ferramentas adaptativas é ativado por padrão; se precisar desativá-lo, adicione o parâmetro filter_tools=False ao inicializar o LightAgent.

### 5. Colaboração Multiagente
Suporte à colaboração multiagente em estilo Swarm, aumentando a eficiência no tratamento de tarefas. Vários agentes podem colaborar para completar tarefas complexas.

```python
from LightAgent import LightAgent, LightSwarm
# definir variáveis de ambiente OPENAI_API_KEY e OPENAI_BASE_URL
# O modelo padrão usa gpt-4o-mini

# Cria uma instância do LightSwarm
light_swarm = LightSwarm()

# Cria múltiplos Agentes
agent_a = LightAgent(
    name="Agente A",
    instructions="Sou o Agente A, um recepcionista.",
    role="Recepcionista, responsável por receber visitantes e fornecer orientações básicas. Sempre que responder, informe sua identidade; você só pode ajudar os usuários a se orientarem com outros papéis, não pode responder diretamente às perguntas de negócios dos clientes. Se não puder resolver a questão do usuário no momento, responda: Desculpe, não posso ajudar no momento!",
)

agent_b = LightAgent(
    name="Agente B",
    instructions="Sou o Agente B, responsável pela reserva de salas de reuniões.",
    role="Administrador de reservas de salas, encarregado de processar, cancelar e consultar reservas para as salas 1, 2 e 3. Sempre que responder, informe sua identidade e responda educadamente às perguntas dos usuários.",
)

agent_c = LightAgent(
    name="Agente C",
    instructions="Sou o Agente C, um especialista em suporte técnico, encarregado de resolver problemas técnicos. Sempre que responder, informe sua identidade e responda o mais detalhadamente possível às perguntas dos usuários. Se o problema estiver além da minha capacidade, direcione o usuário para contatar um suporte técnico mais avançado.",
    role="Especialista em suporte técnico, responsável por lidar com perguntas e soluções relacionadas a hardware, software e redes.",
)

agent_d = LightAgent(
    name="Agente D",
    instructions="Sou o Agente D, um especialista em recursos humanos, encarregado de resolver questões relacionadas a recursos humanos. Sempre que responder, informe sua identidade e responda o mais detalhadamente possível às perguntas dos usuários. Se o problema necessitar de processamento adicional, direcione o usuário para o departamento de RH.",
    role="Especialista em recursos humanos, encarregado de lidar com questões de ingresso, saída, licença e benefícios dos funcionários.",
)

# Registra automaticamente os agentes na instância do LightSwarm
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# Executa o agente A
res = light_swarm.run(agent=agent_a, query="Olá, sou Alice e preciso consultar se o Wang Xiaoming já completou seu ingresso.", stream=False)
print(res)
```
A saída será:
```python
Olá, sou o Agente D, especialista em recursos humanos. Sobre a pergunta se Wang Xiaoming já completou seu ingresso, preciso verificar nossos registros do sistema. Por favor, aguarde um momento.
(Consultando registros do sistema...)
De acordo com nossos registros, Wang Xiaoming completou os trâmites de ingresso em 5 de janeiro de 2025. Ele já assinou todos os documentos necessários e recebeu o número de funcionário e a localização do escritório. Se você precisar de mais informações ou tiver outras perguntas, entre em contato com o departamento de recursos humanos. Estamos sempre prontos para ajudar você.
```

### 6. API em tempo real 
Suporte à saída de serviços de API em formato de fluxo OpenAI, perfeito para integração com os principais frameworks de chat.

```python
# Ativando saída em tempo real
response = agent.run("Por favor, gere um artigo sobre IA.", stream=True)
for chunk in response:
    print(chunk)
```


### 7. Avaliação de Agentes (em breve)
Ferramenta de avaliação de agentes embutida, facilitando a avaliação e otimização do desempenho dos Agentes.


## Modelos principais de Agentes suportados
Compatível com uma variedade de modelos grandes, incluindo OpenAI, ChatGLM, DeepSeek e séries de modelos Qwen.

#### Modelos grandes testados até agora:
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

## Cenários de uso

- **Atendimento ao cliente inteligente**: Através de diálogos multironda e integração de ferramentas, proporcionando suporte ao cliente eficiente.
- **Análise de dados**: Utilizando árvores de raciocínio e colaboração multiagente, lidando com tarefas de análise de dados complexas.
- **Ferramentas automatizadas**: Usando geração automatizada de ferramentas, construindo rapidamente ferramentas personalizadas.
- **Assistência educacional**: Oferecendo experiências de aprendizagem personalizadas por meio de módulos de memória e API em tempo real.

---
 
## 🛠️ Guias de contribuição

Agradecemos qualquer forma de contribuição! Seja código, documentação, testes ou feedback, todos são de grande ajuda para o projeto. Se você tiver boas ideias ou encontrar Bugs, por favor, apresente um Issue ou Pull Request. Aqui estão as etapas para contribuir:

1. **Fork este projeto**: Clique no botão `Fork` no canto superior direito para copiar o projeto para seu repositório GitHub.
2. **Crie uma branch**: Crie uma branch de desenvolvimento local:  
   ```bash
   git checkout -b feature/SuaFuncionalidade
   ```
3. **Submeta suas alterações**: Após a conclusão do desenvolvimento, submeta suas alterações:  
   ```bash
   git commit -m 'Adicionando nova funcionalidade'
   ```
4. **Envie a branch**: Envie a branch para o seu repositório remoto:  
   ```bash
   git push origin feature/SuaFuncionalidade
   ```
5. **Submeta um Pull Request**: Apresente um Pull Request no GitHub, descrevendo o que você alterou.

Revisaremos sua contribuição assim que possível, agradecemos seu apoio!❤️

---

## 🙏 Agradecimentos

O desenvolvimento e implementação do LightAgent não seriam possíveis sem a inspiração e apoio dos seguintes projetos open source, com um agradecimento especial a estas incríveis equipes:

- **mem0**: Agradecimentos ao [mem0](https://github.com/mem0ai/mem0) pelo fornecimento do módulo de memória, que oferece suporte robusto para gerenciamento de contexto no LightAgent.  
- **Swarm**: Agradecimentos ao [Swarm](https://github.com/openai/swarm) pela concepção de colaboração multiagente, que serve como base para as funcionalidades multiagente do LightAgent.  
- **ChatGLM3**: Agradecimentos ao [ChatGLM3](https://github.com/THUDM/ChatGLM3) pelo suporte de modelos grandes de alto desempenho em chinês e por inspirar o design.  
- **Qwen**: Agradecimentos ao [Qwen](https://github.com/QwenLM/Qwen) pelo suporte de modelos grandes de alto desempenho em chinês.  
- **DeepSeek-V3**: Agradecimentos ao [DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3) pelo suporte de modelos grandes de alto desempenho em chinês.  
- **StepFun**: Agradecimentos à [step](https://www.stepfun.com/) pelo suporte de modelos grandes de alto desempenho em chinês.  

---

## 📄 Licença

LightAgent usa a [Licença Apache 2.0](LICENSE). Você pode usar, modificar e distribuir este projeto livremente, mas deve respeitar os termos da licença.

---

## 📬 Contate-nos

Para qualquer dúvida ou sugestão, não hesite em entrar em contato conosco:

- **Email**: service@wanxingai.com  
- **Issues no GitHub**: [https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

Aguardamos seu feedback para tornar o LightAgent ainda mais poderoso!🚀

- **Mais ferramentas** 🛠️: Integração contínua de mais ferramentas úteis para atender a mais necessidades de cenários.
- **Mais suporte a modelos** 🔄: Expansão contínua para suportar mais modelos grandes, atendendo a mais casos de uso.
- **Mais funcionalidades** 🎯: Mais funcionalidades úteis, atualizações contínuas, fique atento para mais novidades!
- **Mais documentação** 📚: Documentação expansiva, exemplos muitos, fácil implementação nos seus projetos.
- **Mais apoio da comunidade** 👥: Comunidade de desenvolvedores ativa, disponível para ajudá-lo a qualquer momento.
- **Mais otimizações de desempenho** ⚡: Otimizações contínuas para atender a necessidades de cenários de alta concorrência.
- **Mais contribuições open source** 🌟: Contribuições de código são bem-vindas, vamos criar um LightAgent ainda melhor juntos!

---

<p align="center">
  <strong>LightAgent - Reduzindo a complexidade da inteligência, simplificando o futuro.</strong> 🌈
</p>

 
**LightAgent** —— Estrutura de agente leve, flexível e poderosa para ajudá-lo a construir aplicações inteligentes rapidamente!