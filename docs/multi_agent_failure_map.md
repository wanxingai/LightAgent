# Multi-agent failure map for LightAgent (ProblemMap No.13)

This page is a small troubleshooting lens for multi-agent setups built with LightAgent and **LightSwarm**. It focuses on a specific cluster of problems:

- agents overwriting or polluting each other’s memory  
- roles drifting over time  
- hidden feedback loops between agents  
- logs that are hard to interpret when something goes wrong

The structure is:

1. a very short overview of the 16-problem failure map behind this guide  
2. a LightAgent-specific view of **No.7** and **No.13**  
3. a symptom → mode → “what to inspect in LightAgent” checklist  

It is intentionally **diagnostic only**. It points to where things usually break, but leaves the exact fixes and architecture choices to you.

---

## 1. Quick overview: the 16-problem map

The original ProblemMap compresses a lot of odd failures into 16 recurring modes. The short version, in prompt-engineering language, looks like this:

| No. | Short label | What usually goes wrong (one line) |
| --- | --- | --- |
| **1** | Hallucination & chunk drift | Retrieval brings in a “close enough” chunk that is actually about the wrong thing, and the model builds a confident answer on top of it. |
| **2** | Interpretation collapse | The right chunk is present, but the reasoning never really lands on it, so the answer contradicts the document that is already in context. |
| **3** | Long-chain drift | Over a long chat or plan, the system forgets the original goal and each local step looks fine while the final outcome is off. |
| **4** | Bluffing / overconfidence | There is no supporting context at all, but the model still answers as if it had one, inventing APIs, endpoints or policies. |
| **5** | “Embedding says yes, semantics say no” | Vector similarity looks good, but the meaning is wrong, especially for short questions against long, generic articles. |
| **6** | Logic collapse and partial recovery | The chain hits a gap, starts looping or mixing unrelated facts, and then tries to “patch over” the hole with vague language. |
| **7** | Memory fracture and persona drift | The “who am I” and “what are we doing” parts of the conversation slowly break, roles blur, constraints are forgotten. |
| **8** | Retrieval is a black box | The system works but nobody can tell which chunk supported which sentence, so debugging feels like random trial and error. |
| **9** | Entropy collapse | The model gives up on structure and falls into repetition or topic soup, not quite hallucination, more like heat-death. |
| **10** | Creative freeze | For creative tasks the output becomes very average and cautious, technically safe but not useful or insightful. |
| **11** | Symbolic collapse | Tasks that lean on analogy, abstraction or layered symbolism lose their structure, parts of the analogy contradict or disappear. |
| **12** | Philosophical recursion | Self-reference and nested perspectives make the model spin in circles instead of converging on a stable position. |
| **13** | Multi-agent chaos | In tool-using or multi-agent systems, roles bleed together, one agent’s memory overwrites another, or agents wait on each other forever. |
| **14** | Bootstrap ordering | All services are “up” but brought online in the wrong order, so you get empty indexes, missing schemas or half-wired components. |
| **15** | Deployment deadlock | Circular dependencies between components stop the system from making progress, even though each piece looks fine in isolation. |
| **16** | Pre-deploy collapse | The first real request hits a mismatch that tests and CI never caught, such as a wrong tokenizer, model, secret or prompt variant. |

In a LightAgent context you will most often see:

- **No.7** when long chats break your assumptions about identity, role and task  
- **No.13** when you start using LightSwarm or multi-agent collaboration  
- **No.14–16** when the underlying RAG or memory pipeline is only half-initialized

The rest of this page focuses on those modes.

---

## 2. Multi-agent chaos in LightAgent

LightAgent is designed to make multi-agent collaboration easier than Swarm, through **LightSwarm** and explicit agent registration.:contentReference[oaicite:5]{index=5}  
That also means the wiring between roles, memory and tools becomes very important when you add more than one agent.

### 2.1 Typical failure patterns

Some recurring patterns seen in LightAgent-style setups:

1. **Role blending**  
   One agent starts replying in the tone, language or responsibility of another, even though their instructions are very different.

2. **Shared memory pollution**  
   A conversation between Agent A and the user silently rewrites or pollutes information that Agent B later relies on.

3. **Hidden feedback loops**  
   Two or more agents keep handing tasks back and forth without converging on a final answer, or repeatedly ask each other for clarification.

4. **Unreadable logs**  
   Logs contain useful data, but without clear tagging of agent name, role and turn index it becomes hard to see who did what and when.

All of these can be described as combinations of **No.7 memory fracture** and **No.13 multi-agent chaos**.

---

### 2.2 Symptom → mode → what to inspect

The table below is meant as a **debugging checklist** for LightAgent and LightSwarm. It does not prescribe fixes, it only points at where to look.

| Symptom in a LightAgent run | ProblemMap mode(s) | What to inspect in LightAgent |
| --- | --- | --- |
| Agent A suddenly talks like Agent B, including style or responsibilities. | No.7 memory fracture, No.13 multi-agent chaos | Check how you build each `LightAgent` instance: names, instructions and roles. Make sure you are not reusing the same `LightAgent` object for multiple logical roles when registering with `LightSwarm`. |
| All agents start to forget earlier constraints after a few turns and answer with very generic text. | No.7 memory fracture | Check how `mem0` is configured: user identifiers, per-agent vs shared memory, and whether long histories are truncated without preserving key constraints. Turn on `debug` logging and confirm that each agent sees the expected conversation window. |
| Two agents keep asking each other for updates and the conversation never reaches a final answer. | No.13 multi-agent chaos | Inspect how tasks are delegated inside LightSwarm. Look for recursive or circular hand-offs, and add simple limits such as maximum delegation depth, maximum number of hops per user query and explicit “stop” conditions. |
| Logs show a mix of messages but you cannot tell which agent took which action. | No.8 retrieval is a black box, No.13 multi-agent chaos | Enable `debug=True`, use a higher `log_level` and set a dedicated `log_file`. Conventionally prefix log lines with the agent name and role, and when possible log the current tool call or LightSwarm step. |
| A single mis-configured tool causes several agents to fail in similar ways. | No.4 bluffing, No.5 embedding says yes, No.13 multi-agent chaos | Review the shared tools and tool routing. Make sure that tools which can change external state are clearly separated from read-only tools, and that each agent only receives tools that match its responsibility. |
| Multi-agent runs behave differently between deployments even though code did not change. | No.14 bootstrap ordering, No.16 pre-deploy collapse | Check whether your vector stores, memory stores and environment variables are all initialized before LightAgent starts serving. Empty or partial indexes often show up first in multi-agent flows, where one agent depends on another’s retrieval. |
| A multi-agent demo works locally but fails in CI or on the first real user. | No.15 deployment deadlock, No.16 pre-deploy collapse | Compare configs between environments: model names, tool registration, memory backends, and any external services used by LightSwarm. Look specifically for missing secrets or different default models. |

You can extend this table with your own rows as you discover new patterns. The important part is to keep classifying failures into modes first, and only then adjust prompts, tools or memory.

---

## 3. Minimal tracing recipe

The goal of this section is not to prescribe a particular logging stack, but to suggest a few concrete hooks that make **No.7** and **No.13** visible.

When you build a multi-agent demo:

1. **Give every agent a clear name and role**  
   Use stable, descriptive names when you create each `LightAgent`. Avoid recycling one instance for multiple roles in the same run.

2. **Log with agent name, role and turn index**  
   Whatever logging library you use, include at least these fields for each message:
   - `agent_name`  
   - `agent_role`  
   - `turn` or `step` index  
   - whether this is a user message, an internal reflection, a tool call or a hand-off  

3. **Tag runs with a trace id**  
   When sending a request through LightSwarm, attach a simple trace id string so that all logs and external telemetry can be grouped by run.

4. **Keep an eye on memory writes**  
   Log when each agent writes to long-term memory or updates user state. For early debugging, it is often useful to print the keys or high-level summary of what changed, without dumping full raw content.

You can start with very lightweight print-style logging and then move to a structured logger once the patterns are clear.

---

## 4. Attribution

This troubleshooting guide is adapted from an MIT-licensed open source project that defines a 16-problem “ProblemMap” for RAG and agentic pipelines.:contentReference[oaicite:6]{index=6}  

The original ProblemMap and longer examples live in that project. Here we only reuse the failure-mode vocabulary and apply it to LightAgent and LightSwarm.
