# v1.0.0 通用持久执行（开发中）

本接口属于 `1.0.0` 开发版本，尚未满足正式发布验收。普通 `run()`、`arun()`、流式输出、Tools、Hooks、Guardrails、Memory、LightSwarm、LightFlow、LightDAG 的默认入口不变。

## 普通任务

`ExecutionService` 接受宿主注册的 Backend 工厂。普通任务不需要 ResearchContract、Evaluator、研究版本，也不默认依赖 Codex、Docker 或宿主 Shell。

```python
from LightAgent import ExecutionService, SecurityContext

# factory 返回实现 probe()/execute(BackendRequest) 的独立后端。
service = ExecutionService("/absolute/private/state", backend_factories={"worker": factory})
handle = service.submit(
    "检查工作目录并生成报告", "/absolute/workspace",
    backend="worker",
    security_context=SecurityContext(user_id="alice", tenant_id="acme", project_id="report"),
    idempotency_key="report-42",
)
# 宿主进程负责工厂和配置恢复；数据库不能指定待导入的 Python 对象。
service.serve_forever()
```

客户端可调用 `ExecutionHandle.connect(id, root=...)` 重连，通过 `status()`、`events(after=...)`、`records(...)`、`send()`、`receipt()`、`budget()` 访问公开控制接口。控制目录是可信宿主权限边界，不是公开 HTTP 鉴权服务；不要把任意控制目录访问直接暴露给用户。

## 状态与恢复

- 提交和消息以幂等键防止重复创建；参数不一致时拒绝复用键。
- 领取、epoch、租约、消息状态和预算预留在 SQLite 写事务内提交。
- `pause()` 阻止后续领取；运行中的有界调用到安全边界后收尾，不假装立即终止。
- `cancel()` 传递给子任务和受控 Job；已接受的调用仍必须协作退出。
- 中断、租约过期或结果不明确时进入 `reconciling`，不能自动重放潜在副作用。
- 宿主核对后调用 `reconcile(action="retry"或"discard", note=...)`；重试创建新 attempt，旧证据保留。
- `session_id` 通过 BackendRequest 显式传给支持 resume 的后端；不会从任意会话 ID 自动导入历史。

任务 `completed` 仅表示后端确认执行结束，不等于成果验证、研究评估或版本采用。继续需要 LightDAG Verifier、领域 Evaluator 等独立验收。

## 权限与宿主能力

`ExecutionRequirements(isolation="docker")` 必须匹配 BackendProbe 的 Docker 能力。宿主执行、Codex 自带 sandbox 或能力未知均不能替代 Docker。BackendProbe 是受信宿主适配器的声明，不是模型提交的数据，更不是实际隔离测试的替代品。

身份、权限、资源、网络、sandbox 和 deadline 不能通过子任务扩张。配置或后端探测摘要变化后拒绝执行，不能重写历史摘要来获得信任。原生后端、Codex 和 App Server 的原有独立校验继续保留。

当前参考实现为单机、本地 SQLite、单个活动 supervisor。暂停、取消和超时不能撤销已产生的外部副作用；任意 Python 函数不保证可被强制终止。

## 预算

`BudgetLedger` 提供 `open/reserve/settle/reconcile/snapshot`。子账户同时占用祖先额度，重复预留和结算不重复扣减，未知费用明确标记为 unknown。有限预算在未知消耗核对前不继续放行。

`backend_calls` 和 `seconds` 可直接约束普通调用。`model_calls/tool_calls/tokens/cost` 硬限额要求后端声明并实施对应约束，同时提供预留上限；未具备此能力的原生/Codex 适配器不能宣称实现精确费用硬上限。报告的真实消耗超出预留仍记账，不伪造较低数值。

研究调用及聊天使用同一 BudgetLedger；研究轮次、比较序列与评估规则属于 LightResearch。v0.12 旧账本没有的计费信息不会被追溯写成“零费用”。

## 交互与唤醒

`InteractionRequests` 统一 question、plan_review、approval 请求和响应，绑定身份、attempt、epoch、过期时间与幂等键。正向操作批准还需匹配精确操作、参数、资源及身份的 ApprovalToken；迟到或重复消费的批准被拒绝。协议本身不提供产品弹窗，也不自动执行批准的操作。

`WakeupScheduler` 在现有 supervisor tick 内投递触发，不启动第二个定时进程。支持持久化去重、取消、skip/coalesce 错过触发策略和事务投递；研究周期由研究层决定，产品计划和通知由 Worker 决定。

## 研究迁移与当前边界

研究契约、评估、晋升、历史选择和参考面板已迁至[同级 LightResearch 项目](persistent_research.zh-CN.md)。本仓库的研究兼容测试仅在联合验收中执行。旧 `mode="persistent"` 需要 `LightResearch.enable_legacy_api()`，仍是研究模式，不是普通任务的别名。

Runtime Job/Subagent 已改为同一 Job 生命周期的适配；冻结 v0.12.0 wheel 的本地历史迁移、恢复与旧 wheel 回退读取演练已通过。具体 API、线程取消限制和离线备份流程见 [Job 与历史迁移](jobs_history_migration.zh-CN.md)。

Worker 可选 Docker 适配已通过真实容器、精确审批、父取消和独立进程冷恢复验收；供应链签名/重授信与拒绝矩阵见 [Provider 供应链契约](provider_supply_chain.zh-CN.md)。源码与独立发行物验证和模型 fixture 的范围在验收记录中分开列出。

这不是 v1.0.0 正式发布。多 Python 干净 CI、持续负载、生产规模迁移和部署方实际远端 MCP 服务仍须按开发计划验收；不能由本地 fixture 或有限测试样本替代。
