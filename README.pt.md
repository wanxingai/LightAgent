
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
    Português | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>
<div align="center">
  <h1>LightAgent🚀（Próxima geração de estrutura de IA Agentic）</h1>
</div>

**LightAgent** é uma estrutura ativa e autônoma extremamente leve com memória (`mem0`), ferramentas (`Tools`) e árvore de pensamento (`ToT`), e é totalmente de código aberto. Ele suporta uma colaboração multiagente mais simples do que o OpenAI Swarm, permitindo a construção de agentes com capacidade de autoaprendizado em um único passo, e suporta a conexão ao protocolo MCP via stdio e sse. O modelo subjacente suporta OpenAI, Zhiyu ChatGLM, DeepSeek, Jieyue Xingchen, Qwen Tongyi Qianwen e outros grandes modelos. Além disso, o LightAgent suporta a saída de serviços de API em formato de fluxo da OpenAI, integrando-se perfeitamente a várias estruturas de chat populares. 🌟

---

## Notícias
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0: adiciona workflows LightFlow com checkpoints, resume/rerun, nós de aprovação, estados de etapa mais claros, metadados de trace, modelos Guardrails, controles MemoryPolicy e o protótipo SharedMemoryPool.
- **[2026-06-14]** LightAgent v0.8.1: adiciona convenções MemoryScope e filtros MemoryPolicy por origem, escopo e confiança.
- **[2026-06-02]** LightAgent v0.8.0: introduz LightFlow para workflows determinísticos de várias etapas.

Notas antigas estão em [GitHub Releases](https://github.com/wanxingai/LightAgent/releases).

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
- **Orquestração de workflows** 🔁: LightFlow encadeia agentes em workflows determinísticos com dependências explícitas, passagem de saídas, retentativas, checkpoints, resume/rerun, aprovações, agentes fallback e execução rastreável.
- **Protótipo de memória compartilhada** 🧠: SharedMemoryPool fornece memória compartilhada em memória com metadados de procedência, recuperação por escopo e resultados compatíveis com MemoryPolicy.
- **Modelos Guardrails** 🛡️: Políticas reutilizáveis de entrada, ferramentas e saída bloqueiam dados privados, confirmam ferramentas sensíveis, validam parâmetros de alto risco e redigem saídas.

## 🧭 Arquitetura em resumo

| Camada | API principal | Use quando precisar |
| --- | --- | --- |
| Runtime de agente único | `LightAgent` | Um agente com modelo, ferramentas, memória, streaming, trace e guardrails. |
| Roteamento multiagente | `LightSwarm` | Delegação por papéis entre agentes especializados. |
| Workflow determinístico | `LightFlow` | DAG, retentativas, checkpoints, aprovações, resume e rerun. |
| Ferramentas e integrações | `tools`, `ToolRegistry`, MCP | Ferramentas Python, geradas, carregamento em runtime ou servidores MCP. |
| Limite de memória | `MemoryPolicy`, `MemoryScope` | Isolamento de tenants, procedência, confiança, expiração e admissão de escrita. |
| Memória compartilhada | `SharedMemoryPool` | Experimentos de memória compartilhada entre agentes. |
| Segurança | `input_guardrails`, `tool_guardrails`, `output_guardrails` | Privacidade, confirmação de ferramentas, parâmetros de risco e redação de saída. |
| Observabilidade | `trace=True`, `agent.export_trace()` | Eventos estruturados de execução, modelo, ferramenta, erro e workflow. |

## Padrões principais de uso

LightAgent mantém a chamada padrão simples e permite adicionar controles de produção gradualmente.

| Padrão | Chamada mínima | Notas |
| --- | --- | --- |
| Resposta básica | `agent.run(query)` | Retorna string por padrão. |
| Streaming | `agent.run(query, stream=True)` | Retorna chunks compatíveis com OpenAI. |
| Resultado estruturado | `agent.run(query, result_format="object")` | Retorna conteúdo e metadados. |
| Trace | `agent.run(query, trace=True)` | Registra eventos sem mudar a string padrão. |
| Memória de usuário | `agent.run(query, user_id="alice")` | Usa backend de memória e MemoryPolicy configurados. |
| Ferramentas | `LightAgent(..., tools=[fn])` | Funções devem expor `tool_info`. |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | Adiciona políticas de entrada, ferramenta e saída. |
| Workflow | `LightFlow().step(...).run(query)` | Para execução determinística multi-etapa. |

## 📋 Documentação

- Para instalação, modelos, ferramentas, memória, MCP, Skills, streaming e LightSwarm, consulte [FAQ](docs/FAQ.md).
- Para workflows determinísticos, checkpoints, resume/rerun, aprovações, agentes fallback e estados de etapa, consulte [LightFlow](docs/lightflow.md).
- Para ferramentas customizadas, ToolRegistry, ToolLoader, AsyncToolDispatcher e MCP, consulte [Tools Guide](docs/tools.md).
- Para memória compartilhada ou memória em grafo, consulte [Memory Security Guidance](docs/memory_security.md).
- Para SharedMemoryPool, consulte [SharedMemoryPool](docs/shared_memory_pool.md).
- Para admissão de escrita de memória e expiração, consulte [Memory Admission And Mutation Controls](docs/memory_admission.md).
- Para segurança de entrada, ferramentas e saída, consulte [Guardrails](docs/guardrails.md).
- Para OpenRouter, modelos locais e provedores compatíveis com OpenAI, consulte [Model Provider Configuration](docs/model_providers.md).
- Para traces estruturados, consulte [Trace Observability](docs/tracing.md).

## 🚧 Em breve

- **Comunicação colaborativa entre agentes** 🛠️: Os agentes também podem compartilhar informações e transmitir mensagens, realizando comunicações complexas de informações e colaboração em tarefas.
- **Avaliação de agentes** 📊: Ferramenta de avaliação de agentes embutida, facilitando a avaliação e otimização do agente que você criou, alinhando-se aos cenários de negócios e melhorando continuamente o nível de inteligência.


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

### Inspecionar um trace de execução (v0.7.0)

Trace é opcional e mantém compatível o comportamento padrão de `agent.run()`.

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

### Criar checkpoint de uma execução LightFlow (v0.9.0)

`LightFlow` pode persistir checkpoints e retomar execuções com falha sem reiniciar do primeiro passo.

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

`SharedMemoryPool` é um protótipo leve em memória para experimentos de memória compartilhada multiagente.

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

README mantém o modelo central de uso; exemplos longos, configuração de adaptadores e práticas de produção ficam nos docs dedicados.

### 1. Módulo de memória destacável (`mem0`)
LightAgent aceita qualquer backend de memória com `store(data, user_id)` e `retrieve(query, user_id)`. Use `user_id` para isolar conversas e `MemoryPolicy` quando a memória for compartilhada.

### 2. Integração de ferramentas
Use funções Python com metadados `tool_info` para expor capacidades controladas. Para ToolRegistry, ToolLoader, AsyncToolDispatcher e MCP, consulte [Tools Guide](docs/tools.md).

### 3. Gerador de ferramentas
`agent.create_tool()` pode gerar código de ferramentas a partir de documentação de API ou descrições naturais. Revise e teste antes de produção.

### 4. Árvore de Pensamento (ToT)
Ative `tree_of_thought=True` quando a tarefa exigir planejamento explícito, reflexão e seleção de ferramentas.

### 5. Colaboração multiagente
`LightSwarm` delega trabalho entre agentes especializados. Mantenha papéis claros e controle escritas de memória.

### 6. API streaming
`agent.run(query, stream=True)` retorna chunks compatíveis com OpenAI para chat UIs e respostas longas.

### 7. Autoaprendizado do agente
Autoaprendizado deve ser combinado com `MemoryPolicy` para evitar conteúdo privado, expirado ou irrelevante.

### 8. Trace e Langfuse
LightAgent permite observar execução por trace integrado ou Langfuse.

### 9. Avaliação de agentes
A avaliação de agentes medirá comportamento em cenários de negócio.

### 10. Workflows LightFlow
`LightFlow` é a camada de workflow determinística para executar etapas conhecidas.

- Estados de etapa: `pending`, `running`, `success`, `failed`, `skipped`, `waiting_approval`.
- Validação DAG: `flow.validate(strict=True)`.
- Controles de etapa: `timeout`, `max_retry`, `cancel_if`, `fallback_agent`, `requires_approval`, `approval_handler`.
- Persistência e recuperação: `JsonLightFlowStore`, `flow.resume(run_id)`, `flow.rerun_step(run_id, step_name)`, `flow.get_run(run_id)`, `flow.list_runs()`.

Consulte [LightFlow](docs/lightflow.md).

### 11. Guardrails
Guardrails são hooks leves para entrada, chamadas de ferramenta e saída.

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

Consulte [Guardrails](docs/guardrails.md).

### 12. SharedMemoryPool
`SharedMemoryPool` é um protótipo em memória para memória compartilhada multiagente, usado com `MemoryPolicy`.

## Modelos principais de Agentes suportados

LightAgent funciona com endpoints chat completion compatíveis com OpenAI: OpenAI, OpenRouter, Zhipu ChatGLM, DeepSeek, Qwen, StepFun, Moonshot/Kimi, MiniMax, vLLM, llama.cpp, Ollama e gateways próprios.

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

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
- **Issues no GitHub**: [https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

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