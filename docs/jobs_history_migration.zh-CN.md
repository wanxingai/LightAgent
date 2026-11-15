# Job/Subagent 收敛与历史迁移

适用源码：`1.0.0`。本文是开发契约，不代表正式版本已发布。

## 单一状态权威

Runtime 的协程 Job、Subagent 执行和持久外部 Job 共用 `job_lifecycle` 的状态转换、attempt/epoch fencing 和公开状态投影。不是新增调度器，也不复制一张“权威状态表”：Runtime 从 Session 事件恢复，外部进程仍以 ControlStore 的原 Job 记录为权威。`SubagentManager` 只管理注册、父子关系和可信实例绑定，运行状态、并发容量、结果和取消均来自 Job；不再独立维护运行计数和执行状态机。

| 项目 | Runtime 协程 / Subagent | 持久外部进程 |
| --- | --- | --- |
| 状态存储 | Session 的 `job.*` 事件 | ControlStore 原 `job` 记录 |
| 调用边界 | `runtime.jobs` / `runtime.subagents` | `handle.submit_job()` 等宿主 API |
| 公开状态 | `runtime.jobs.status(job_id)` | `handle.job_status(job_id)` |
| 旧状态兼容 | `pending/success` 保留；公开投影为 `queued/completed` | 保留旧 `nonce`，作为 attempt 的读取兼容值 |
| 输出游标 | 已保存输出项的数量 | 受控输出文件的字节位置；旧记录未知时为 `None` |
| 冷恢复 | 只恢复记录，不反序列化函数或自动重放协程 | 读取 nonce 绑定回执；结果未知则保留 `uncertain` |

SQLite 的 Job 检查与追加使用同一写事务，跨 Runtime/实例不能重复领取或以陈旧结果覆盖新 attempt。InMemory/JSONL 和不提供事务的自定义 SessionStore 仅保证进程内协调，不能宣称具备跨进程 CAS。

新 Job 的完成通知有可恢复的 outbox 标记：重连补投，消息与确认在同一 SQLite 事务内保存，重复恢复不重复通知。旧记录没有该标记时不猜测其通知状态，避免迁移时重复发送历史通知。

显式租约未过期时，另一个 Runtime 的只读重连不会把它标记为中断。过期租约不能续租或追加输出。旧的无租约活动记录在重连时按 `interrupted` 处理；需要并行观察的长任务应显式指定 `lease_seconds` 并由所有者续租，或使用持久 ExecutionService。

## Subagent 与宿主重绑定

```python
child = runtime.subagents.register(child_agent, persistent=True)
result = await runtime.subagents.run(
    child.agent_id, "检查本地数据",
    idempotency_key="check-42", lease_seconds=60,
)
job = runtime.jobs.list()[-1]
print(runtime.jobs.status(job.job_id))

# 重启后，先 open_session() 恢复注册，再提供受信代码实例。
restored.subagents.bind(child.agent_id, trusted_child_agent)
```

`persistent=True` 保存注册信息，不承诺 Python 对象可跨进程存活。父注册必须存在，子权限不能扩大；父子取消和 Session 取消沿 Job/注册树传递。Subagent 幂等键按 agent 隔离，输入参数不同会拒绝复用；使用幂等键时输入需能规范化为 JSON。重复调用读取同一 Job，不启动第二份工作。

旧版独立状态机留下的 `running` Subagent 没有关联 Job 时，展示为中断，`bind(..., note=...)` 必须记录宿主对旧执行的核对；不把它直接算作已停止或已成功。同步 Job callable 现在在线程执行，需要当前事件循环的操作应写成 async callable。

协程和外部副作用不能等同于可强杀进程。`cancelled` 表示取消已接受，不保证撤销已有副作用。线程型同步调用可能在取消后仍运行：`runner_stopped=False`，并继续占用 Subagent 容量。宿主独立确认线程/外部效果后，才调用 `runtime.jobs.reconcile(job_id, note=...)` 释放容量。历史未知 runner 的 `resume(..., note=...)` 也是显式宿主决定，不能用于自动重试；每次恢复产生新 attempt/epoch，旧结果和旧输出无法写回。

完整离线示例见 [16.jobs_and_history.py](../example/16.jobs_and_history.py)。研究调试面板只展示公开生命周期投影；`uncertain` 仍必须通过宿主核对接口处理，没有自动重跑按钮。

## 离线迁移与回退

迁移不原地替换控制根，也不向旧事件回填字段。先停止所有 Runtime、supervisor、Job 和其他写入者，并保护备份目录。`quiescent=True` 是宿主对停写状态的显式确认；工具额外检查活动租约和 supervisor/Job OS 锁，但无法发现不遵守这些协议的任意写入者。

```python
from LightAgent import HistoryBundle, SqliteSessionStore

HistoryBundle.capture("/private/history", "/private/backups/v012", quiescent=True)
candidate = HistoryBundle.restore("/private/backups/v012", "/private/migration-candidate")
store = SqliteSessionStore(candidate / "sessions.sqlite3")

# 审查原始记录和来源后，显式建立从该检查点开始的完整性链。
digest = store.history_digest("existing-session")
store.anchor_legacy("existing-session", expected_digest=digest, note="宿主已核对冻结历史")

# 回退始终从原备份恢复到新目录；不覆盖活动副本。
HistoryBundle.restore("/private/backups/v012", "/private/rollback-candidate")
```

- SQLite 使用一致性备份 API，封存为独立数据库，不直接复制活动 WAL/SHM。
- 文件及数据库备份带 SHA-256 清单；目录与文件收紧为 `0700/0600`，拒绝 symlink/特殊文件、覆盖目标和递归恢复。
- 清单用于发现非预期损坏，不是发布者签名；备份本身必须保存在受信宿主目录，不能当作恶意输入安全导入器。
- `anchor_legacy()` 校验检查时摘要，另存迁移审计，不改事件内容；只建立检查点后的完整性，不追溯证明旧历史可信。
- 研究版本、契约、执行配置摘要、消息回执、产物和计数保持原值。旧配置与新宿主不匹配时拒绝执行，不能改摘要“修复”兼容。
- 绝对 workspace/result_file 路径不自动改写。副本首先用于读取和核对；恢复执行需宿主重新确认原路径、权限与后端配置。旧 wheel 不应写入已经加锚的新副本；回退只能使用迁移前的备份。

## 冻结 v0.12.0 演练

```bash
PYTHONPATH=. python tests/migration_v012_rehearsal.py \
  --baseline-wheel /private/frozen/lightagent-0.12.0-py3-none-any.whl \
  --output /private/rehearsals/new-run
```

脚本在独立子进程从指定旧 wheel 创建实际历史，并在活动 Runtime Job 处冷退出；验证新版本读取、显式加锚、恢复、未知副作用不重放、研究 profile 不自动重授信，再用旧 wheel 读取回退副本。报告包含旧 wheel 摘要、事件/记录计数和各项断言，不上传历史数据。

该演练覆盖本地 SQLite/文件存储，不代表真实 Worker Docker、生产数据库全集、全量供应链签名或长期压力验收。发布剩余门槛见 [开发计划](lightagent_v100_development_plan.zh-CN.md)。
