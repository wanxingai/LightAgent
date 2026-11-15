# v0.12.0 P0 执行层验证报告

日期：2026-10-03。环境：macOS、Python 3.11、Codex CLI 0.160.0。状态：P0 执行层开发与本地验收完成，尚未发布 v0.12.0。

## 本次实现

- 增加 BackendProbe，检查真实 CLI 版本、exec/resume 所需参数及不支持的能力；当前支持 POSIX 与 Codex 0.160.x 协议线。
- 增加独立的 BackendSessionStore，将本地和外部会话绑定到工作目录、用户、项目、Agent 身份、权限、策略版本及后端配置。未知 Codex 会话不自动导入；配置或身份变化必须创建新会话。
- 使用 POSIX 文件锁保护同一会话和相同工作目录，覆盖多个实例与进程；进程退出释放锁，绑定元数据持久保留。元数据目录位于 Codex 可写工作区外。
- 补齐原生历史跨实例恢复、历史缺失拒绝和忙碌 Agent 实例检测；会话恢复不重放 shell 命令。
- 明确 CLI 沙箱、命令网络、临时目录写入、hooks、Apps、子 Agent 和环境继承配置。拒绝无法实施的逐工具权限、预算及原生客户端参数。
- 加固 CLI 会话 ID、终态事件与输出校验、错误分类、过期请求的锁清理，以及 macOS 退出期间的进程组清理竞态。

## 验证结果

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| 已跟踪测试与新增 P0 测试 | 424 通过、2 跳过 | 40 个测试模块，Python 3.11；跳过项为需显式启用的 Mem0 与 Codex 集成测试 |
| P0 离线测试 | 59 项，包含于上述总数 | 假 CLI、原生假模型、真实本地进程、会话持久化、跨进程锁、取消、权限与兼容性 |
| 真实 Codex 集成 | 1 通过，单独执行 | 读取临时 fixture、写出 result.txt、取消活动轮次、新后端实例恢复相同会话并核对历史内容 |
| Python 3.10 语法 | 通过 | 后端模块、core.py 与 workspace.py；不等于 Python 3.10 运行时 CI |
| wheel 构建 | 通过 | poetry-core 2.5.0，确认新后端与工作区模块进入安装包 |
| wheel 安装与导入 | 通过 | 临时目录无依赖安装；从安装目录导入，PATH 中无 Codex 时仍可创建外部后端 Agent，未初始化原生模型客户端 |
| 差异检查 | 通过 | git diff --check；文档本地链接与代码块检查 |

真实联调需要宿主允许 CLI 写入自身会话和日志目录；最初的外层只读沙箱阻止 CLI 初始化，允许宿主运行后完成测试。整个测试保持 Codex 自身 workspace-write 沙箱与审批限制，没有使用跳过沙箱的参数。

构建依赖仅安装在临时目录，未变更项目依赖或全局 Python 环境。构建包仍标为 0.11.0，因为此轮验证不构成 v0.12.0 发布。

## 可重复执行的集成测试

先在宿主完成 Codex CLI 安装和登录，再在项目测试环境运行：

```sh
LIGHTAGENT_CODEX_INTEGRATION=1 python -m pytest tests/integration/test_codex_backend_opt_in.py -q
```

该测试使用临时业务目录与独立控制元数据目录，复用 CLI 认证并消耗账号额度；不读取真实研究数据，不要求额外 API key。CLI 自身保留的会话遵循其存储配置。正常离线 CI 默认跳过此测试。

## 本阶段边界

P0 提供有限单次执行、显式会话继续及基础互斥。AgentService、事务 Inbox、后台 Job 恢复、研究循环、聊天面板和递归版本采用仍属于 P1–P4。不能将本报告视为 7×24 小时服务、分布式锁或外部副作用 exactly-once 的证明。

多进程必须共享控制元数据目录；调用方保证不同并发写入目录不互相重叠。绕过框架的 CLI 调用不受框架锁保护。权限变更不自动迁移旧历史，原生恢复依赖应用配置的持久 SessionStore。

当前 Codex 预设关闭命令网络、Apps 与 web search，项目 .codex 配置不自动载入。逐工具限制、token/tool/context 预算与任意读取范围隔离不在此适配器的实施能力内，应使用明确支持这些约束的执行环境。详细用法见 [工作目录执行说明](workspace_execution.zh-CN.md)。

尚未执行多版本运行时 CI、原生真实模型长跑或任一后端至少 24 小时持续运行；这些仍按 [v0.12.0 开发方案](lightagent_v012_development_plan.zh-CN.md) 验收。

CLI 配置依据：[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference) 与 [非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)。真实命令帮助和上述集成测试是本地兼容性证据。
