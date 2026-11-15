# 干净环境与持续负载验收

验收入口位于 `tests/acceptance`。历史实测结果见 [v1.0.0 验收记录](v100_validation.zh-CN.md)，不要把脚本存在、短试跑通过或可选测试跳过当作发布通过。

## Python 3.10–3.13 干净矩阵

需要 Git、Docker daemon 和 Python 3.10+。先准备四个官方基础镜像，再从项目根目录运行：

```bash
docker pull python:3.10-slim-bookworm
docker pull python:3.11-slim-bookworm
docker pull python:3.12-slim-bookworm
docker pull python:3.13-slim-bookworm
python tests/acceptance/clean_matrix.py \
  --output /tmp/lightagent-clean-matrix --jobs 2
```

输出目录必须尚不存在且位于项目外。驱动会生成只读输入用途的源码副本；不修改原工作区，不读取宿主 Python 包，也不挂载 Docker socket、用户主目录或 API 凭据。默认不复制未跟踪的业务示例、dist、日志、密钥文件及 `.DS_Store`/`__pycache__` 等平台缓存。快照不是通用秘密扫描器，包含新的业务文件前仍需审查。

每个版本执行：

1. 将已拉取的基础镜像解析为 digest/image ID，记录实际身份；四版本使用同一个源码 SHA-256 清单。
2. 在容器新建不继承系统包的 venv，Poetry 2.4.1 按 `poetry.lock` 安装依赖并启用 `mcp` extra；另安装可选签名验证依赖 `cryptography>=41,<52`。基础依赖已包含 PyYAML；CI 在安装 MCP extra 前验证基础 wheel、默认技能发现和 Codex 动态工具桥。
3. 安装 Git 与 Node.js，构建核心 wheel。默认不复制或构建 LightResearch。
4. 在 `--network none`、2 CPU、2500 MiB、512 PID 限制下运行 `pip check`、核心 pytest 和仓库外 wheel 安装/执行验证。
5. 保存 Python/平台、依赖版本、freeze/pip inspect、wheel 摘要、JUnit、日志和结果 JSON。任何失败返回非零状态；只有明确列出的 opt-in 集成跳过原因被接受。

完整套件包含真实进程中断事务并强制缓存溢出的热日志恢复回归：核对原实例读取与冷重连、已提交值保留、未提交修改回滚及只读 SQL 限制。ControlStore 根目录由服务持有且必须可写；`query_only` 是业务 SQL 约束，不是只读文件系统或不可信 SQL 的安全沙箱。SQLite 的内部崩溃恢复可能写回数据库，但普通读取不会使用 `BEGIN IMMEDIATE` 预留 writer。

本地特意保留的两份旧 MCP/工具测试不会被覆盖；驱动另外从 HEAD 提取同名测试到 `upstream-tests`，单独运行并记录，不合并为完整套件计数。干净矩阵验证的是锁定依赖组合及上述可选签名依赖，不代表所有 extras、所有允许依赖版本或所有操作系统组合均已覆盖。

主要输出：`snapshot.json`、`matrix.json`、各 `python-3.x/report.json`、`full.xml`、`full.log`、`wheel.log`、`freeze.txt` 和 `installed.json`。联合模式另有 `research-install.log` 和 `extension.log`。镜像和报告保留供排查；测试容器退出后自动删除。

## 核心与联合验收

默认核心模式要求测试环境未安装 LightResearch，不收集 `tests/research/`，并排除标记 `requires_lightresearch` 的跨包测试，不记为跳过。联合模式显式提供研究源码或 wheel，执行完整套件并验证两个 wheel 在仓库外共同安装后可用。联合测试需要 Node.js 验证研究面板；不会自动寻找同级目录或下载研究包。

进入联合验收前请确认 LightResearch 的包元数据支持当前 LightAgent 版本。原先只支持 `LightAgent>=0.13.0.dev0,<0.14.0` 的 wheel 不能用于 v1.0.0 联合验收。

从 LightAgent 根目录运行以下任一种 Docker 联合验收：

```bash
python tests/acceptance/clean_matrix.py \
  --output /tmp/lightagent-joint-source --research-source ../LightResearch
python tests/acceptance/clean_matrix.py \
  --output /tmp/lightagent-joint-wheel --research-wheel /path/to/lightresearch.whl
```

Docker 只把显式选择的输入放入快照及 SHA-256 清单。源码模式暂存 LightResearch 的包文件和构建配置，不复制同级项目的测试、数据或本机配置；研究 wheel 在镜像构建时准备，运行测试时不联网。

也可直接在隔离 venv 验收（先按锁文件安装开发依赖、`mcp` 和 `signing`，且不要装 LightResearch，再用 `poetry build --format wheel --output /tmp/lightagent-core` 构建核心）：

```bash
python tests/acceptance/verify.py --output /tmp/lightagent-core-report \
  --core-wheel /tmp/lightagent-core
python tests/acceptance/verify.py --output /tmp/lightagent-joint-report \
  --core-wheel /tmp/lightagent-core --research-source ../LightResearch
python tests/acceptance/verify.py --output /tmp/lightagent-joint-wheel-report \
  --core-wheel /tmp/lightagent-core --research-wheel /path/to/lightresearch.whl
```

`--core-wheel` 和直接验收的 `--research-wheel` 也接受仅含一个 wheel 的目录。源码构建可能需要下载构建依赖，不修改传入的 LightResearch 目录；已构建 wheel 模式不需要这一步。传错路径、构建失败或研究测试未通过时验收失败，不会退回核心模式。

## 持续负载

使用矩阵记录中的 Python 3.11 **image ID**，在同一不可变镜像内运行，不挂载实时源码：

```bash
mkdir -m 700 /tmp/lightagent-soak-reports
docker run --rm --network none --cpus 2 --memory 1g --pids-limit 256 \
  --volume /tmp/lightagent-soak-reports:/reports \
  ACCEPTANCE_IMAGE_ID python tests/acceptance/soak.py \
  --output /reports/run --seconds 900 --concurrency 4 --interval 2 \
  --fault-interval 60 --min-rounds 100
```

`ACCEPTANCE_IMAGE_ID` 替换为本次 `container.json` 中实际验证过的 ID。报告目录只存放合成测试数据，`run` 子目录必须不存在。

负载持续复用一个控制库和 supervisor，每轮提交 4 个子任务，并重复相同幂等键。每轮检查预算扣减与唯一外部效果计数，同时在持续增长的 Session 库中验证 Inbox、Job、Subagent 幂等和冷重连。每约 60 秒重启主 supervisor，并启动独立子进程，在效果提交后真实 `os._exit(23)`，核对恢复进入 `reconciling`、没有自动重放、预算不重复扣减；精确审批及 token 防重放也在该周期验证。

门槛：至少 900 秒、100 轮及 3 个预热后资源样本；预热后 RSS 增长不超过 128 MiB；退出后的 FD 不超过预热值 +8、线程不超过 +2；没有容器 OOM 或状态/去重/预算断言失败。`release_gate` 只在满足时长/轮次/样本要求时为真；短试跑即使 `status=passed` 也不是正式持续负载通过。崩溃、断言或中断保留失败报告，不删除证据。

`report.json` 记录总时长、完成任务、重启/崩溃核对次数、批次延迟、资源和最终门槛；`samples.jsonl` 每约 30 秒记录一次。报告应与矩阵快照和镜像身份一起保存。

这是单机、确定性本地 backend 的有界持续运行检查，不是实际 LLM 费用、极限吞吐、多机调度或 24 小时生产稳定性证明。真实 Worker/Docker、远端 MCP、Codex 与 Mem0 Graph 按各自的显式集成矩阵验收，不能通过去掉 opt-in 标记冒充完成。

## CI

`.github/workflows/ci.yml` 的四版本任务复用 `verify.py` 的核心模式，核对隔离 venv、依赖、核心套件和核心 wheel，并在成功/失败时上传报告。MCP SDK 兼容矩阵保持独立。手动 `workflow_dispatch` 的 `run-soak` 可在四版本通过后执行 15 分钟负载；默认 PR 不重复运行长负载。构建产物写入 runner 临时目录而非用户 dist。

本地 Docker 结果不等于远端 GitHub Actions 结果；只有实际提交、推送并观察对应 CI 后才能记录远端通过。这里未配置定期任务，也不需要真实模型 API key。
