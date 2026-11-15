# v1.0.0 开发验收

下列历史验收基于更名之前的 LightAgent `0.13.0.dev0`、LightResearch `0.1.0.dev0` 及各节标明的快照。该开发线现以 v1.0.0 为发布目标，**历史结果不代表当前提交的发布验收已完成**。

## 本阶段范围

- 普通持久执行不再必须依赖研究契约、Evaluator 或研究员版本。
- 研究业务、面板、示例与服务模板迁入可选 LightResearch；旧模式通过显式注册保持研究语义。
- 原研究测试与界面行为测试迁入 `tests/research`，核心旧面板及测试入口已移除；普通 Backend、Job、Flow、Memory、Hooks、Guardrails 回归保留。
- 新增 Session 原子追加/CAS/幂等校验、新会话哈希链、跨实例事务、持久预算、父子取消、租约 fencing、交互请求和事务唤醒。
- 普通任务与研究任务的宿主隔离要求均可拒绝 Docker-only 降级；能力声明不是实际 Docker 隔离证明。

## 第一阶段验证结果

| 项目 | 结果 |
| --- | --- |
| 本地完整测试 `python -m pytest -q tests -rs` | **689 passed, 3 skipped，97.34 秒** |
| 单独验证远端 HEAD 的 MCP/工具测试 | **39 passed，1.41 秒**；没有覆盖用户要求保留的本地同名测试文件 |
| 新增及相关执行/预算/Job 定向回归 | 84 passed；其后的补充用例包含在最终完整测试中，不累加计数 |
| 核心 wheel 仓库外安装 | 通过；禁用研究包导入仍可使用核心；不包含原核心面板 |
| LightResearch 独立 wheel 安装及执行 | 通过；仓库外产生一轮有效实验，依赖核心公开契约 |
| 普通持久任务示例 | 离线执行成功，1 次 backend 调用 |
| 迁移后的研究示例 | 三组各 3 轮；采用代数分别为 0/1/2，回滚验证成功；均为确定性 fixture，不是科学效果评估 |
| 当前文档相对链接与围栏 | 101 个相对链接通过，无缺失 |
| 核心依赖方向与删除路径检查 | 通过；不反向导入 LightResearch/LightWorker；旧核心面板与旧测试入口不存在 |
| 编译与差异检查 | compileall、git diff --check 通过 |
| 保护文件 | 原 dist、测试示例及两个要求保留的同名测试文件与开发前快照一致 |

验证环境为 macOS、Python 3.11.7。另建 venv，选用 pytest 8.4.2、MCP 1.12.4、OpenAI 1.109.1；其余依赖继承本机环境，包括 Pydantic 2.12.5、pydantic-settings 2.12.0。这不是全新依赖解析环境，不能代替正式干净 CI。未修改用户原 Python 环境。

第一阶段的三个跳过项是两个真实 Codex 可选集成测试、一个真实 Mem0 Graph 安全矩阵，均未显式启用。当时 Docker daemon 不可连接；第三阶段已恢复可用并单独完成真实容器验收，不能把第一阶段的模拟结果倒算为真实证据。

冻结 v0.12.0 基线时，首轮研究/后端测试为 250 通过、1 失败：存储超限取消场景出现只读数据库异常。后续完整回归中该失败未重现；保留这条基线记录，不将“未重现”描述为已定位并修复的根因。

## 第二阶段：Job/Subagent 与历史迁移

- 删除原 Runtime 中独立 Job/Subagent 执行状态机。协程和外部进程适配同一 Job 转换/fencing 规则；Subagent 的执行状态、并发和取消来自 Job。
- 新增跨 Runtime 活动租约保护、原子幂等提交、陈旧输出拒绝、父子/Session 取消、显式宿主绑定、完成通知 outbox 崩溃恢复。
- 取消后的同步线程不冒充已经停止；未知 runner 保留容量，宿主核对后才释放。历史未知 runner 的恢复需要核对说明。
- 核心/研究 Job 公开投影、研究调试界面、[离线示例](../example/16.jobs_and_history.py)、[迁移指南](jobs_history_migration.zh-CN.md)及相关测试同步更新。
- 新增 `HistoryBundle` 离线一致性备份和只恢复到新目录的回退接口；显式 `anchor_legacy` 保留原事件并记录检查点审计，不追溯授信旧内容。

| 最终检查 | 结果 |
| --- | --- |
| 本地完整测试 | **723 passed, 3 skipped，100.09 秒**；包含本阶段全部新增回归 |
| 保留文件对应的远端 HEAD MCP/工具测试 | 39 passed，1.37 秒；单独运行，不覆盖本地保留文件，不累加到完整套件 |
| 核心 wheel 仓库外安装与运行 | 通过；无研究包也能运行 Job/Subagent/历史备份恢复接口 |
| 独立 LightResearch wheel 安装与执行 | 通过；核心不包含研究实现，研究扩展产生有效实验 |
| 冻结旧 wheel 到新 wheel 的历史迁移/回退 | 通过；产物与外部 Job 输出按摘要校验，旧 wheel 回退读取一致 |
| 界面与示例 | HTTP 生命周期投影、宿主核对路由、JS 行为、两个离线执行示例均纳入完整测试 |
| 编译、依赖方向、旧路径与文档 | compileall、核心无 Research/Worker 反向导入、旧入口删除检查、120 个相对链接检查通过 |
| 用户保护文件 | dist、两份保留测试、本地示例等共 6 个冻结样本文件逐字节一致；未清理其他本地文件 |

环境与跳过项同第一阶段，仍不是全新依赖解析环境或远端多 Python CI。完成通知事务故障注入也验证了数据库与进程内投影一起回滚，不会在当前 Runtime 中留下未提交的收件箱消息。

冻结基线 wheel SHA-256：`8b42adbf1637bd0a7f6502f7cfa49ae92e4cc5c209eec37df3e02c835faa324b`。通过旧 wheel 的独立进程生成历史，在活动 Job 处冷退出，再使用新源码及仓库外安装的新 wheel 分别完成迁移/回退演练。样本包括 **21 条 Session 事件、19 条控制记录、20 条控制事件、1 个验证实验与产物**。

演练验证：Session/Job/Subagent、已应用和待处理消息、预算计数、研究版本与产物均可读；未知 Job/cycle 保留核对状态，backend 调用数不增加；旧执行 profile 不被自动重授信；从原备份恢复的副本由旧 wheel 读取，历史摘要与原始样本完全一致。报告仅在本机私有备份目录保存，历史数据没有上传。复现入口为 [migration_v012_rehearsal.py](../tests/migration_v012_rehearsal.py)。

本阶段也修正了测试发现的备份问题：SQLite 备份连接必须显式关闭并封存为无 WAL 的独立数据库；复制目录必须保持私有权限。外部 Job 新增输出游标后，恢复回执白名单和校验同步更新，旧回执仍兼容。

## 第三阶段：真实 Worker/Docker 与供应链

- Worker 新增可选 DockerWorkspaceProvider，不在核心引入 Docker/Worker 依赖，也不静默替换产品默认运行时。
- Docker 探测固定 image ID、资源限制、文件/程序策略和审批配置；Native probe 与会话绑定纳入该探测，控制/历史数据库不得位于容器工作目录内。
- helper protocol 3 增加有界编辑、唯一替换和内容 CAS，保留受保护文件、路径、符号链接、变更文件数和程序允许列表限制。内联 Python/容器 shell 禁令未放宽。
- 独立进程恢复父 Runtime 和子注册，由宿主重新绑定实际 Native Agent，加载原 SQLite 历史；不同身份不能导入该会话。
- 新增 ProviderAttestation、ProviderTrustStore、AttestedProvider；Ed25519 验签、显式批准、持久撤销、更新重授信、降级拒绝及路径/资源攻击矩阵接入实际 Skill/MCP 适配与 Worker 严格组合层。

真实环境：Docker Engine **29.6.1**、Docker Desktop **4.81.0**，Linux/amd64 容器。最终测试镜像为 `sha256:e36494f211689d1ac372d182d1b2b62f2bf91e69e8682e563eb7d0e68908d12d`，基于本机已有 Worker 镜像更新 helper，没有覆盖原镜像标签。起初原 `lightworker-python:3.11` 标签可列出但无法解析，验收使用显式 image ID；缺少指定镜像时测试失败而不是跳过。

真实探测确认 UID 10001、只读根文件系统、无 Docker socket、无网络、单一工作区 bind mount、CPU/内存/PID 限制。父取消后核对容器已退出；独立进程 PID 与原进程不同并读回首轮上下文。模型响应是确定性 fixture，未调用真实 LLM API，不把该结果描述为线上模型或完整 Worker 产品流程验收。

源码和独立 wheel 均执行了真实容器验收；wheel 模式明确断言 LightAgent 与 Worker 来自仓库外安装目录。签名及 Native 边界测试在安装后的代码上运行，结果单独记录，不累加为默认套件覆盖率。Worker 配套改动尚在相邻本地仓库，未推送。

| 本阶段最终检查 | 结果 |
| --- | --- |
| LightAgent 默认完整套件 | **763 passed, 8 skipped，107.01 秒** |
| Worker 非 Docker/network/live 套件 | **141 passed, 3 deselected，45.10 秒** |
| 新跨项目真实 Docker 契约 | **5 passed，27.28 秒**；含独立进程冷恢复 |
| Worker 原有真实 Docker 套件 | **3 passed，20.55 秒**；含临时 pip 网络回收 |
| 仓库外安装 wheel 的签名/Native/Docker 验收 | **44 passed，30.51 秒**；36 项供应链、3 项 Native 边界和 5 项真实 Docker，不累加到默认套件 |
| 核心及可选研究 wheel | 构建、独立安装、无研究包核心导入及研究执行通过 |
| 新 wheel 的 v0.12 迁移/回退复测 | 通过；原事件、回执、产物及 Job 输出摘要保持一致 |
| 静态检查 | compileall、两仓库 git diff --check、Worker 改动文件 Ruff 检查通过 |

默认套件的 8 个跳过包括 5 个显式启用的 Worker Docker 用例；它们已经另行在真实环境中执行通过。另 3 个真实 Codex/Mem0 Graph 可选集成仍未启用。未把 opt-in 跳过视为通过，也未把多次执行结果相加作为覆盖率。

验收 venv 额外配置 Typer 0.19.2、cryptography 50.0.2、CFFI 2.1.1、hatchling 1.33.0、packaging 26.3。首次 Worker 全套出现 Typer 0.15.1 与 Click 8.3.1 的 CLI 帮助页兼容错误，仅在该独立 venv 调整后重跑通过；未修改用户原环境，也未借机改动 Worker 的既有版本约束。兼容背景见 [Typer 发布记录](https://typer.tiangolo.com/release-notes/)。该 venv 仍继承其他本机包，存在无关项目依赖冲突提示，不是干净的正式发行环境。

复现与完整矩阵见 [Provider 供应链](provider_supply_chain.zh-CN.md)；实际 Worker 适配说明位于相邻 Worker 工程的 `docs/lightagent_v013_integration.zh-CN.md`。签名证明声明/文件与宿主批准，不证明远端 MCP 内部代码，也不替代 Sandbox、CapabilityGate、敏感操作审批或部署侧身份治理。

## 第四阶段：干净环境与持续负载（2026-11-09）

新增 [可复现验收入口](clean_environment_acceptance.zh-CN.md)：四版本使用统一源码快照、官方基础镜像 digest、新建且不继承系统包的 venv；按锁文件安装依赖，另安装可选签名依赖，测试容器断网。Node.js 和 Git 明确安装，JS 行为测试不能以工具缺失为由静默跳过。核心/研究 wheel 在仓库外安装执行；本地保留测试的 HEAD 版本另行运行，不覆盖用户文件。

本阶段发现并处理的问题：

- Python 3.10 未暴露 `sqlite3.SQLITE_BUSY/SQLITE_LOCKED` 常量。Job 数据库错误分类改用 SQLite 标准数值回退 5/6；参数化测试兼容缺失常量，新增删除常量后的回归。
- 30 毫秒执行超时测试混入了数据库准备耗时，在并行容器中可能尚未调用 backend 就过期。现将准备租约与调用超时隔离，仍使用真实 `asyncio.wait_for`，并断言 backend 已调用、已 dispatch、错误为 `TimeoutError` 和状态为 `reconciling`。
- 陈旧 Job 输出测试原先在任务开始前就设置 10 毫秒租约，过期后会一直等待未触发的进入信号。现先确认任务开始，再缩短租约，等待有上限且 `finally` 释放旧任务；没有放宽运行时 fencing 规则。
- App Server 测试原先把进程启动/探测/握手和执行超时都压在 300 毫秒内。现握手成功后只推进该模块的测试时钟，断言确实走到 turn 并得到 `timed_out`；保留真实进程、协议和中断回执验证，不放宽生产超时。
- 真实进程退出后复现控制库只读重连失败；强制事务缓存溢出并 `os._exit(23)` 可稳定生成 hot rollback journal。`mode=ro` 阻止 SQLite 自身恢复，现用 `mode=rw` 配合 `query_only=ON` 和普通 `BEGIN`：允许 pager 回滚未提交事务，业务 SQL 仍不能修改数据，正常读取不预留唯一 writer。两个回归覆盖原实例和重新构造，核对已提交值、未提交记录消失、完整性及写入拒绝；三轮复测均通过。机制依据见 [SQLite 热日志恢复](https://www.sqlite.org/lockingv3.html#dealing_with_hot_journals)与 [query_only](https://www.sqlite.org/pragma.html#pragma_query_only)。第一阶段的同类错误不能仅凭消息就认定全部同源，但本次已有确定性复现及修复。
- 验收命令增加 60 秒诊断栈和 600 秒子命令上限。短负载与正式负载区分 `release_gate`；异常、中断与清理失败仍保留失败报告。

首轮 3.10 收集失败、3.11 时序失败、3.10 挂起后的人工终止栈、后续 App Server 时序失败，以及 459.515/695.013 秒的两次中断试跑均保留，没有覆盖为成功或累加为最终验收。第二次中断是为了让运行时代码修复后的负载重新计时。定向回归 **49 passed，8.26 秒**；Job 监控及验收脚本回归 **20 passed，11.52 秒**；热日志/控制面竞争/脚本回归 **25 passed，16.44 秒**；App Server/脚本/预算回归 **25 passed，11.16 秒**。这些是辅助检查，不累加到完整套件。

CI 已复用同一验证入口，收集 JUnit、依赖版本及 wheel 证据，并添加手动启用的 15 分钟负载任务。此处是本地配置更新，尚未提交和推送，不代表远端 Actions 已通过。

### 最终干净矩阵

平台为 Linux/amd64、glibc 2.36；每个测试容器断网，最多 2 CPU、2500 MiB、512 PID。以下均为修复后的统一快照，不以首轮通过替代最终复测；各版本结果不累加成测试数量或覆盖率。

| Python | 默认完整套件 | JUnit 执行时长 | pip check / 核心与研究 wheel | 单独 HEAD 测试 |
| --- | --- | --- | --- | --- |
| 3.10.22 | **770 passed, 8 skipped** | 135.273 秒 | 全部通过 | 39 passed |
| 3.11.18 | **770 passed, 8 skipped** | 208.203 秒 | 全部通过 | 39 passed |
| 3.12.16 | **770 passed, 8 skipped** | 142.398 秒 | 全部通过 | 39 passed |
| 3.13.18 | **770 passed, 8 skipped** | 143.919 秒 | 全部通过 | 39 passed |

统一依赖组合包括 OpenAI **1.109.1**、MCP **1.12.4**、Mem0 **2.0.12**、Pydantic **2.10.4**、pydantic-settings **2.8.1**、cryptography **50.0.2**、pytest **8.4.2**，Node.js **18.20.4**。完整依赖与解释器信息另有 freeze、pip inspect 和 report.json，不声称覆盖所有允许的依赖组合。3.12/3.13 各有 6 条非阻塞 `datetime.utcnow()` 弃用警告，来自已有 memory promotion 时间戳代码，保留在日志中，后续需在保持序列化格式的前提下清理。

8 个跳过与第三阶段相同：5 个 Worker/Docker、2 个真实 Codex、1 个真实 Mem0 Graph。本次另用新 wheel 复测了 **44 项签名/Native/真实 Worker Docker 契约，43.07 秒通过**，包含这 5 个 Docker 用例；剩余 3 项真实 Codex/Mem0 Graph 未启用。wheel 复测首轮被安装路径断言拒绝（pytest 默认导入模式载入源码），改用 `--import-mode=importlib` 后确实从独立安装目录运行通过；没有删掉该断言来绕过验证。

补充结果：macOS 本地完整回归 **770 passed, 8 skipped，200.34 秒**，但该 venv 仍继承本机包，不并入干净矩阵。新 wheel 在断网的 3.11 容器中再次完成冻结 v0.12 wheel 的历史生成、迁移与旧 wheel 回退读取；仍为 21 条 Session 事件、19 条控制记录、20 条控制事件和 1 个实验/产物，原始摘要一致，backend 调用数不增加。

快照 SHA-256：`08b52d914218b497de895a95630977c647e5a23000adac273f97d87a7f922b4f`（343 个文件；174 个源码/测试/锁定配置输入与当前工作区逐一核对一致）。本轮核心 wheel SHA-256 为 `1b2cb466f4092f61ffd2ade83e14e4973d17fa065cc1cc82479933a3ce6cadb3`。LightResearch wheel 分别记录摘要，不把 ZIP 构建时间差异误当成代码差异。平台缓存没有进入最终 wheel；原工作区缓存及保护文件未删除。

原始矩阵、快照、JUnit、完整日志、依赖清单及镜像身份保留于本机私有备份目录的 `lightagent-v013-acceptance-20261109-recovery`。迁移报告位于 `lightagent-v013-migration-20261109-recovery`；安装后的跨项目契约报告位于 `lightagent-v013-installed-20261109-recovery/contracts-installed.xml`。未推送这些报告中的本机数据。

### 最终持续负载

使用上述快照的 Python 3.11 镜像 `sha256:325c9ec433806f13fcc0f555957d009efbf8a6a0e474e3c9c4757cb03fd4f0c3`，不挂载实时源码，断网、2 CPU、1 GiB、256 PID。模型为确定性本地 fixture，没有真实 LLM/API 调用；与其他回归有同期运行，不作为独占机器的性能基准。

| 指标 | 实测结果 |
| --- | --- |
| 最终判定 | **status=passed，release_gate=true，退出码 0** |
| 时长与负载 | **900.483 秒，310 轮，1240 个完成任务**；每轮 4 个，同键重复提交不重复执行 |
| 故障与恢复 | 15 次子进程提交效果后 `os._exit(23)`，全部进入核对而非自动重放；主 supervisor 重启 15 次 |
| 交互与状态 | 每个故障周期验证参数不匹配审批拒绝、精确批准、token 重放拒绝；各轮验证 Inbox/Job/Subagent、冷重连及 Session 哈希链 |
| 效果与预算 | 唯一外部效果数精确对应完成任务与故障样本；共享父账户仅按实际调用结算，无重复扣减 |
| 预热后 RSS 最大增长 | **4.289 MiB**，低于 128 MiB 门槛 |
| 退出后资源 | RSS 84.563 MiB、FD 4、线程 1；容器内存峰值约 154.230 MiB，无 OOM |
| 四任务批次耗时 | p50 2.231 秒、p95 3.762 秒、最大 7.725 秒；包含提交/去重/状态查询，不是模型延迟或吞吐 SLA |

报告与约每 30 秒资源样本保存在本机私有备份目录 `lightagent-v013-soak-20261109-recovery/run/report.json`、`samples.jsonl`。本轮未执行 24 小时负载、真实模型计费、高并发极限或分布式场景；不能用这 15 分钟合成负载推断生产长期稳定性。

收尾检查：编译、CI YAML 结构/权限及变更差异检查通过；文档相对链接有效。原 dist 的两个产物、本地两个示例和两份保留测试共 6 个冻结文件仍逐字节一致，未覆盖或删除其他本地未提交文件。

## v0.12 残留清理复测（2026-11-14）

- App Server 握手使用 LightAgent 的版本常量，研究调试面板显示 LightResearch 自己的包版本；握手 fixture 与面板测试覆盖这两处。
- 修复迁移后的文档入口，清理 6 个无对应源码的字节码缓存与空的旧示例目录。历史验收、显式兼容入口和仍被研究扩展调用的代码不删除。
- macOS/Python 3.11 本地完整套件：**770 passed, 8 skipped，121.81 秒**。跳过项与上文相同。两个 wheel 从过滤后的源码快照重新构建，仓库外安装/执行通过；核心 wheel 未包含研究面板、LightResearch 或缓存。417 个相对链接及图片引用通过，6 个保护文件与冻结基线一致。
- 本次未重跑四版本干净矩阵或 15 分钟负载；上文保留的是对应快照的原始结果。

## 研究专用逻辑迁移复测（2026-11-14）

- 精确轮次 steering 的验证与投递、实验摘要及假设筛选迁入 LightResearch。核心保留通用分页和显式注册的兼容入口，不反向导入可选包。数据库结构、回执语义、分页游标的格式和归属检查均不变。
- macOS/Python 3.11 完整套件：**773 passed, 8 skipped，121.00 秒**。新增回归验证旧 steering 入口、绑定验证和幂等回执，以及旧游标续页与历史数据库逐字节不变。
- 两个 wheel 的仓库外安装和执行通过。单独安装核心时通用分页可用，旧研究入口在未注册时拒绝执行；安装扩展后，新旧入口返回一致的结果。
- 冻结 v0.12.0 wheel 到新 wheel 的历史演练通过：旧实验可以搜索，历史摘要、工件与回执保留，无后端重放，旧 wheel 读取回退副本与原始样本一致。未操作用户的真实历史数据或原 `dist/`。
- 未重新运行四版本干净矩阵、远端 CI 或 15 分钟负载；原结果仍对应其测试快照。

## 研究聊天、唤醒与停机排空复测（2026-11-14）

- LightResearch 负责聊天归属校验、入队后唤醒和聊天/steering 排空范围；核心保留通用事务、预算、幂等与停机协调。旧 `AgentHandle`、`ChatHandle` 和 `ResearchStore.enqueue()` 继续通过显式注册使用。SQLite 表、字段、历史回执格式不变。
- 新旧入队路径均验证回执、唤醒和事件在同一事务：提交前其他连接不可见，注入故障后三者一并回滚；同键重试不重置唤醒，跨研究员聊天拒绝入队。停机时排空已领取聊天，未领取聊天留待重启，已完成回执不重放。
- macOS/Python 3.11 完整套件：**776 passed, 8 skipped，121.74 秒**。核心和 LightResearch wheel 均通过仓库外安装与执行，覆盖旧聊天入口、唤醒和回执重读。
- 用冻结 v0.12.0 wheel 生成含已完成和中断聊天的历史（21 条 Session 事件、22 条控制记录、23 条控制事件）。新 wheel 保留已完成回执，中断回执恢复为 `uncertain`，无后端重放；旧 wheel 读取回退副本与原始摘要一致。未操作真实历史数据或原 `dist/`。
- 本轮未重跑四版本干净矩阵、远端 CI 或 15 分钟负载。

## 研究记录规则与额度兼容复测（2026-11-14）

- LightResearch 声明研究记录类型的不可变规则，并从已验证的研究合同为新任务生成通用 `limits`。核心继续执行不可变写入限制、CAS、记录数、事件保留、并发和存储额度检查。
- 数据库结构不变，不回填历史记录；核心优先使用非空 `limits`，否则按原语义读取旧 `contract`，不合并两套字段。旧版五类不可变记录在未注册、甚至未安装 LightResearch 时仍受保护。
- macOS/Python 3.11 完整套件：**785 passed, 8 skipped，112.48 秒**。首轮有一条测试只修改了新记录的旧合同字段；重写为使用真实合同提交并分别覆盖现行记录与无 `limits` 的历史记录，两条均通过。新增测试用独立进程阻止导入 LightResearch，验证保存的并发和存储额度；超额时命令未启动。
- 两个 wheel 通过仓库外安装与执行。核心单装验证历史不可变记录、旧额度和独立 Job 执行入口。冻结 v0.12.0 wheel 历史演练通过：旧记录及聊天回执保留，旧 wheel 读取回退副本与原始摘要一致，无后端重放。原 `dist/` 和保护文件未变。
- 本轮未重跑四版本干净矩阵、远端 CI 或 15 分钟负载。

## Mem0 与 Langfuse 可选依赖复测（2026-11-14）

- 基础安装不再要求 `mem0ai` 和 `langfuse`，可分别选装 `mem0`、`langfuse` extras。保留 `from mem0 import Memory`、`memory=`、`from langfuse.openai import openai` 和旧 `tracetools["TraceToolConfig"]` 配置。只在启用 Langfuse 而未安装 SDK 时提示安装；已安装 SDK 的内部导入错误仍原样抛出。
- Poetry 锁文件按原版本重新生成，`poetry check --lock` 通过。检查新 wheel 的 `Requires-Dist`，两个 SDK 都只在对应 extra 启用时纳入依赖。验收报告允许可选 SDK 未安装，用 `null` 记录；其余必需依赖仍需通过检查。
- macOS/Python 3.11.7 全新 venv，不继承系统包，两个 SDK 均未安装。`pip check` 通过；完整套件 **789 passed, 8 skipped，135.54 秒**。跳过的仍是 5 项真实 Worker/Docker、2 项真实 Codex 和 1 项真实 Mem0 Graph。新增回归覆盖无 SDK 普通调用和自定义记忆适配器、Langfuse 缺包提示、内部错误传播及原配置/会话 ID。
- 核心与 LightResearch wheel 均在仓库外安装并执行通过。另在独立环境中安装两个 extras，使用锁定的 Mem0 **2.0.12**、Langfuse **4.14.0** 和 OpenAI **1.109.1** 从实际安装的核心 wheel 验证旧 SDK 导入及旧 Langfuse 配置，`pip check` 通过；未调用真实供应商 API。已有本机 Langfuse 3.0.0 与 OpenAI 1.109.1 组合存在 SDK 内部导入不兼容，本次未修改供应商版本约束。
- 本地临时证据位于 `/private/tmp/lightagent-v013-extras.MgoiLR/reports/`。本轮未覆盖原 `dist/`，未重跑四版本干净矩阵、远端 CI 或 15 分钟负载。

## MCP 可选依赖与工具桥复测（2026-11-14）

- 基础 wheel 的直接依赖为 `openai`、`httpx`、`PyYAML`、`jsonschema`。MCP 仅在 `mcp` extra 启用时安装；不再直接依赖 `httpx-sse`、`pydantic-settings` 或示例用的 `requests`、`loguru`、`colorama`。对应依赖仍可由其他 extras 或平台间接安装。Poetry 锁文件保留现有 SDK 版本，`poetry check --lock` 通过。
- 保留 `MCPClientManager` 旧导入以及 `setup_mcp(mcp_setting=...)`、`mcpServers` 配置。验证了无 SDK 时导入仍可用，实际启用连接或 MCP stdio 服务才提示安装；已安装 SDK 的依赖错误不伪装成缺包。Codex 动态工具桥直接使用 `jsonschema`，不依赖 MCP SDK。
- macOS/Python 3.11.7 全新 venv，按锁文件启用 `mcp` extra：最终完整套件 **791 passed, 8 skipped，114.54 秒**，跳过项与前次相同。从 HEAD 提取的保留测试另有 **39 passed**，不累加到总数。CI 改为先测无 MCP 的基础安装，再启用 extra 跑完整套件。
- 重新构建 LightAgent 和 LightResearch，均在仓库外安装与执行通过。基础环境通过 `pip check`，确认没有 MCP、`httpx-sse`、`pydantic-settings`、`requests`、`loguru` 或 `colorama`。从已安装核心 wheel 运行 **13 项**定向测试，覆盖普通与流式调用、旧导入、缺包提示和 Codex 动态工具桥；另通过独立 Job/Subagent、历史恢复与研究扩展安装验证。
- 同一核心 wheel 启用 `mcp` extra，在三个独立环境复测。首轮扩展 stdio 测试发现 MCP 2.3.0 已移除旧服务端装饰器；补齐 2.x 请求处理入口后全部重跑通过。旧 `setup_mcp` 配置均完成本地 stdio 工具注册与调用；HTTP 通过已有 Postman 契约模拟验证初始化、枚举、调用、请求头覆盖和清理，未连接生产 MCP 服务。

| MCP SDK | Pydantic | 兼容用例 | 实际传输 |
| --- | --- | --- | --- |
| 1.12.4 | 2.10.4 | 16 passed | stdio、回环 Streamable HTTP 通过 |
| 1.30.0 | 2.14.3 | 16 passed | stdio、回环 Streamable HTTP 通过 |
| 2.3.0 | 2.14.3 | 16 passed | stdio、回环 Streamable HTTP 通过 |

最终本地证据在 `/private/tmp/lightagent-v013-mcp.f6DacL/final-reports/`；模拟日志为同目录层级的 `simulation.ndjson`。本地保留脚本和原 `dist/` 未覆盖，6 个保护文件与冻结基线逐字节一致。本轮未重跑远端 CI、四版本干净矩阵或持续负载。

## Skills 可选依赖试验（2026-11-15，已恢复为基础依赖）

- `skills` extra 提供 PyYAML，`all` 同时包含它；基础 wheel 直接依赖仅 `openai`、`httpx`、`jsonschema`。`poetry check --lock` 通过。Poetry 重新求解时更新了 Python 3.10 的签名依赖与 `typing-extensions` 锁定组合；本轮执行环境为 macOS/Python 3.11.7，不代表重新通过四版本矩阵。
- `Skill`、`SkillManager` 和 `create_skill_tools` 的导入不变。默认仍扫描 `skills/`，并支持 `skills_directories` 和 `auto_discover_skills=False`。发现 `SKILL.md` 才加载 PyYAML；确实缺包时报告文件路径及 `pip install 'LightAgent[skills]'`。其他导入故障不被掩盖，原 YAML 解析、目录优先级和工具路径限制不变。
- 全新 venv 启用锁定的 `mcp`、`skills`、`signing` 后，完整套件 **796 passed, 8 skipped，134.61 秒**。跳过项仍为真实 Worker/Docker、Codex 和 Mem0 Graph 的 opt-in 用例。HEAD 测试另行运行，不计入这一总数。
- LightAgent 与 LightResearch wheel 均在仓库外安装并执行通过。基础安装明确没有 MCP、PyYAML：**17 项定向测试通过**，并用实际缺包验证了安装提示。单装 `[skills]` 在新 venv 安装 PyYAML 6.0.3、未安装 MCP，**12 项技能测试通过**。在隔离的 `[all]` 环境复装新 wheel 后，`pip check`、默认发现和技能激活均通过。
- 日志与 wheel 验收证据保存在本地 `/private/tmp/lightagent-v013-skills.C1TjVx/reports/`。原 `dist/` 和本地保留脚本未覆盖，6 个保护文件与冻结基线逐字节一致；未运行远端 CI 或持续负载。

## Skills 恢复为基础依赖（2026-11-15）

- 基础 wheel 直接依赖为 `openai`、`httpx`、`jsonschema`、`PyYAML`。默认技能发现及旧导入保持不变；MCP 等其余 extras 保持可选。
- macOS/Python 3.11.7，从本地 wheel 缓存在全新环境用 pip 安装基础 wheel，自动安装 PyYAML 6.0.3，未安装 MCP，默认技能发现和激活通过。另验证 `[skills]` 别名和 `[all]` 的安装，`pip check`、基础环境 25 项定向测试及 wheel 冒烟通过。
- 完整回归 **796 passed, 8 skipped，110.69 秒**；另有 HEAD 测试 **39 passed**。新版核心 wheel 和现有 LightResearch wheel 在仓库外联合验收通过。完整回归复用了上一轮隔离 venv；新锁定依赖在独立基础环境验证。本轮未运行远端 CI。报告位于 `/private/tmp/lightagent-v013-base-skills.J0VBh7/reports/`，本地保留的测试脚本和 `dist/` 未改动。
- 随后移除空的 `[skills]` 别名。重建 wheel 后核对 `Provides-Extra` 和 `Requires-Dist`，确认只有此别名被移除，全部依赖声明及其他 extras 不变。锁文件和基础 wheel 冒烟复测通过。

## 同级 LightResearch 联合验收（2026-11-15）

- LightResearch 已移到同级目录。默认 Actions 和 Docker 矩阵只验收核心，不构建或安装研究扩展。核心模式不收集 `tests/research/`，并排除两项显式标记的跨包测试；其余运行时、Worker 及 MCP 契约照常保留。
- 联合模式必须显式指定 `--research-source ../LightResearch` 或 `--research-wheel`。源码暂存后构建，不修改同级目录；测试使用暂存安装的研究 wheel。Docker 快照记录显式输入的摘要，不隐式纳入同级目录。
- macOS/Python 3.11.7 隔离环境：核心 **613 passed, 7 skipped**，两项跨包测试未运行；研究源码与预构建 wheel 两条联合入口分别 **797 passed, 8 skipped**。三次验收另各有 **39 项** HEAD 测试通过，不累加到套件计数。跳过项为原有真实环境 opt-in 测试。
- 两个 wheel 在仓库外通过联合安装、`pip check` 和研究运行烟测；另在全新 venv 中用单条 pip 命令安装两个 wheel，验证包来源和旧研究 API 的显式注册。CI YAML、Docker 构建分支语法和两种快照输入检查通过；本机 Docker daemon 不可用，未实跑容器矩阵或远端 Actions。
- 本地日志见 `/private/tmp/lightagent-v013-sibling.aVhaVR/` 下的 `core-report`、`joint-source-final`、`joint-wheel-final`。原 `dist/` 和四份保留测试文件与冻结基线逐字节一致。

## v1.0.0 更名与待验收项

- 核心运行时和打包版本从 `0.13.0.dev0` 改为 `1.0.0`，不改变存储或协议 schema。
- LightResearch 不随本次变更提交。上述联合验收使用旧开发版本；针对 `1.0.0` 重新做联合验收，需要先由扩展维护者提供声明兼容的 LightResearch wheel。

1. 生产规模历史数据、部署方远端 MCP 真实服务/身份验证；可选适配不等于默认 Worker 产品运行时已全量切换。普通/研究控制根仍不允许静默混用。
2. 提交并推送后实际核对远端 Python 3.10–3.13 Actions 与 MCP 兼容矩阵。本地干净矩阵和 15 分钟负载已经通过，不能代替远端执行记录。
3. 按部署要求补充更长时间/更大规模/真实服务负载；明确是否需要启用尚未运行的真实 Codex 与 Mem0 Graph 集成。当前没有 24 小时生产稳定性证据。

v0.12.0 源码快照、原始 wheel 与开发验证用 wheel 均保存在本机私有备份目录，未覆盖 dist、未上传历史数据或发布 release。接口说明见[通用执行指南](durable_execution.zh-CN.md)，后续工作见[v1.0.0 开发计划](lightagent_v100_development_plan.zh-CN.md)。
