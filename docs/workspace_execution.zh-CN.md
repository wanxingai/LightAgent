# 工作目录执行（v1.0.0 开发版）

本文描述 LightAgent v1.0.0 开发版的工作区执行：能力探测、会话绑定、并发保护、权限映射和 Codex 执行。默认 `run()` 仍是一次调用。普通持久任务使用 [ExecutionService](durable_execution.zh-CN.md)；研究循环、聊天与可选调试面板属于[同级 LightResearch 项目](persistent_research.zh-CN.md)。旧 `mode="persistent"` 保留研究语义，须由宿主显式调用 `LightResearch.enable_legacy_api()`。

## 原生模型：两个工作区工具

```python
from LightAgent import LightAgent, LocalWorkspaceProvider

agent = LightAgent(
    model="your-model",
    api_key="your-api-key",
    base_url="https://your-model-endpoint/v1",
    execution_provider=LocalWorkspaceProvider(allow_host_execution=True),
)
result = agent.run(
    "阅读 README 和数据说明，找出已下载数据以及更新数据的脚本。给出文件依据。",
    workspace="./research/bonds",
    execution_timeout=300,
    result_format="object",
)
print(result.content)
print(result.error)
```

`LocalWorkspaceProvider` 是应用显式授权的宿主机执行方式，只适用于可信本地项目。它可以运行宿主机命令，cwd 不构成文件系统或网络隔离。配置要求沙箱或禁止网络时，此 Provider 会拒绝执行；受限环境应实现 `WorkspaceExecutionProvider`，由容器或其他执行环境实施约束。框架不会自动降级为宿主执行。

传入目录后，原生模式创建独立工具注册表，默认向模型暴露 `shell` 与 `edit_file`；构造 Agent 时显式注册的业务工具也可组合。普通 `agent.run("问题")` 的工具集合不变。目录不自动变成数据索引，也不要求数据 Provider。

- `shell(command, timeout=60)`：持久 bash，可用 `rg --files`、`grep`、`sed`、项目脚本查找和读取信息。返回 status、exit_code、有限 output、truncated 和 session_alive。同一次 run 内保留 cwd、环境变量和 shell 状态，命令串行执行；下一次 run 创建新终端。
- `edit_file(path, new_text, old_text=None, expected_sha256=None)`：只接受目录内相对路径。省略 old_text 时仅创建新文件；替换要求 old_text 恰好匹配一次，可同时指定旧内容的 SHA-256。拒绝符号链接、路径越界、歧义与陈旧编辑。不自动创建父目录。

当前原生工具支持 POSIX（macOS/Linux）。默认单条命令最多 300 秒、保留 64 KiB 输出、编辑文件最多 1 MiB；可在 Provider 构造时调整。输出截断会明确标识，目前不会自动生成溢出文件。大输出应让项目脚本写入文件，再读取所需片段。

工作区根目录的 `AGENTS.override.md` 优先于 `AGENTS.md`，最多读取 32 KiB，跳过符号链接及非普通文件；提示模型按需阅读 README 和相关子目录指引。目前没有完整的父目录/子目录指令继承解析器。独立 Worker 应使用独立写入目录；编辑器的冲突检查不是跨进程事务锁。

## 可选 Codex CLI

```python
from LightAgent import LightAgent

agent = LightAgent(name="bond_researcher", backend="codex", instructions="保留实验依据，不把猜测当作验证结果。")
result = agent.run(
    "阅读工作目录，整理已有数据与研究进展。",
    workspace="./research/bonds",
    execution_timeout=600,
    result_format="object",
    session_id="bond-local-session",
)
if result.error:
    raise RuntimeError(result.error)

# 两类 ID 含义不同，恢复外部会话需显式指定。
codex_session_id = agent.last_backend_result.session_id
result = agent.run(
    "继续检查数据缺失情况。",
    workspace="./research/bonds",
    session_id="bond-local-session",
    backend_session_id=codex_session_id,
)
```

运行时通过 PATH 查找 `codex`，无需指定安装路径，也无需在 LightAgent 中另填模型 API key。需由应用预先完成 CLI 安装和认证；缺少命令或 CLI 接口不兼容时返回失败，不回退到其他执行方式。

适配器使用 argv 数组与 stdin，解析 `codex exec --json` 的 JSONL。恢复使用确切 ID，绝不使用 `--last`；拒绝可能被解析为 CLI 参数的会话 ID。当前兼容线限定为 0.160.x，实际联调版本为 0.160.0。每次执行前检查版本与 exec/resume 必需参数，配置使用 `--strict-config`，不支持的版本或参数在模型调用前失败。

```python
from LightAgent import CodexBackend

report = CodexBackend().probe()  # 只检查本地命令，不调用模型、不读取凭据内容
print(report.version, report.capabilities, report.limitations)
```

复用 CLI 认证，但通过 `--ignore-user-config` 排除用户模型、MCP 与 hooks 配置；可显式使用 `CodexBackend(model="...", sandbox="read-only")` 配置模型和沙箱。默认 workspace-write，审批策略 never；关闭命令网络访问、额外写根、隐式 /tmp 与 TMPDIR 写入、hooks、Apps、子 Agent、远程插件目录和 web search，关闭登录 shell 并限制 shell 环境变量继承。不使用跳过沙箱的参数；支持非 Git 工作目录。项目及父目录的 `.codex/config.toml` 或 `hooks.json` 当前明确拒绝，避免加载未映射的执行配置。

Codex 的服务请求需要 `network_allowed=True`。内部工具不经过 Python 的逐工具策略：LightAgent 做后端入口授权，内部约束由 CLI 沙箱与配置实施。Capability allow/deny 仅支持 backend.execute/backend.codex 及由 LightDAG 检查的 dag.task.execute 入口；逐工具限制或收窄 max_risk 会明确报错。SecurityContext.resources 约束选用的工作根，不代表 CLI 文件读取只能位于该目录；需要更强读取隔离的应用应使用独立隔离环境。

目前不桥接 Python Tools、Memory、工具 guardrails，也不支持 LightAgent 的 token/tool/context 预算或外部后端 max_retry/max_tool_iterations；显式传入会报错。传入原生 api_key/base_url/provider、execution_provider 或 skills_directories 也会拒绝，防止误以为这些参数改变了 Codex 行为。外部后端 `PolicyHook` 仅支持 before_run、after_run、on_error，输入与最终输出 guardrails 仍会执行。普通观察 hooks 不会收到 Python 内部模型/工具阶段，查看进度使用后端事件。原生模式可以通过已授权的本地脚本获取数据；Codex 默认关闭命令网络；应用可以显式使用 `CodexBackend(network_access=True)` 授权项目脚本联网。这是独立且绑定会话的权限配置，不是自动放宽沙箱。

`session_id` 始终是 LightAgent 的 Session ID；`backend_session_id` 是外部引擎会话 ID。框架通过 `BackendSessionStore` 将会话与规范化工作目录、用户、tenant、project、Agent 身份、权限、policy_version 及后端配置绑定；Codex 另绑定 CLI home 和对应本地会话。任何绑定改变均拒绝恢复，收窄权限也应创建新会话。未知外部会话不自动导入。跨实例恢复必须使用相同 Agent name 或显式稳定 SecurityContext，避免随机默认名称导致身份不一致。

绑定与锁默认放在 `$XDG_STATE_HOME/lightagent/backends`，未设置时使用 `~/.local/state/lightagent/backends`。该目录要求 0700，不得位于 Codex 可写工作根内。默认使用标准库 SQLite 保存绑定、POSIX flock 管理活动锁；这是控制元数据，不是工作区检索索引。需要指定服务控制目录时，可向 LightAgent 传 `backend_session_store=BackendSessionStore(control_dir)`，或向后端直接传 `session_store`。同一引擎的所有调用者必须共享这一个注册表；绕过框架直接调用 CLI 不受其锁保护。

原生模式使用原有 SessionStore 恢复消息历史，不恢复 shell 内存。默认历史仍在内存，跨进程恢复必须配置持久 SessionStore。绑定已知但历史缺失时明确失败，不能伪装成空白会话继续。本地和外部会话 ID 均由应用保存；普通持久任务通过 `ExecutionHandle` 重连，研究任务通过 `LightResearch.ResearchHandle` 重连。

## 事件、取消与 DAG

`on_backend_event` 接受 `BackendEvent(type, attempt_id, data)`。Codex 发出 started、原始 JSONL 事件和 finished；原生模式发出模型/工具阶段进度。外部调用另外保存 `backend.result`，记录外部 session ID 与目录。事件可能包含输入、文件内容和工具结果，应用展示或外传前应执行自己的脱敏策略。

`CancellationToken` 与 `arun()` 取消会通知执行层并等待进程组清理。超时/取消后的原生终端不可复用。清理覆盖本工具创建的进程组，不保证终止自行脱离进程组的宿主进程；长期实验不能通过无人管理的后台 shell 作业承载。原生模型请求采用剩余超时并关闭 OpenAI SDK 隐式重试；其他模型客户端与业务工具须遵守超时/取消契约，正在进行的任意 Python/网络调用无法强制安全杀死。

`AgentBackend` 的 execute 方法接受 `BackendRequest` 并返回 `BackendResult`。`NativeBackend(agent_factory, execution_provider)` 可用于每次创建独立 Agent。`BackendWorkerAdapter(backend, workspace)` 将后端接入已有 LightDAG；workspace 可以是按 TaskContext 分配隔离目录的函数。后端必须返回 JSON TaskOutcome，候选结果仍经过 v0.11 的 Verifier 才能发布；成功退出、turn.completed 和模型文本都不等于成果验证通过。

同一 Agent、同一会话或相同规范化工作目录的执行禁止重叠，保护覆盖使用同一注册表的多个实例与进程。进程退出后 OS 自动释放活动锁，绑定保留；调用方自行保证不同并发工作目录不存在父子重叠或硬链接共享写入。单次工作区调用不自动重放；持久服务通过任务账本记录中断，由宿主核对未知副作用后再决定是否重试。工作区 `stream=True` 暂不支持；原生工作区暂不支持 trace 参数、运行时 tools/history/metadata/approval 或 Swarm 交接，显式使用会报错。普通调用的对应接口保持原行为。

## 兼容性与后续验收

旧系统继续使用普通 run/arun、stream、Tools、Hooks、Memory、LightFlow 和 LightSwarm 时无需接入这些新增接口，也不会隐式获得 shell 或要求安装 Codex。仅采用工作区和外部后端的代码需要新配置。

离线测试覆盖信息发现、权限映射与拒绝、会话绑定、跨进程锁与退出恢复、原生历史恢复、JSONL 契约、超时取消、DAG 验证和旧 API 回归。真实 CLI 测试位于 `tests/integration/test_codex_backend_opt_in.py`，需显式设置 `LIGHTAGENT_CODEX_INTEGRATION=1`，使用已登录账号并消耗额度；流程包含临时文件读写、取消及恢复后历史核对。

当前本地和部署级验收边界见 [v1.0.0 验收记录](v100_validation.zh-CN.md)。[v0.12 P0 验收记录](v012_p0_validation.zh-CN.md) 仅作为历史基线保留，不代表当前远端 CI 或真实服务已通过。
