# 服务模板已迁移

**v1.0.0 动态（2026-11-15）：** 已合入 `main`，尚未正式发布。核心新增用于普通任务的可重连 `ExecutionService`，参见[版本介绍](../../README.zh-CN.md#v100通用持久执行与恢复)与[持久执行指南](../durable_execution.zh-CN.md)。

研究服务模板属于[同级 LightResearch 项目](../persistent_research.zh-CN.md)，位于其 `docs/service_templates/`。核心 runner 不再启动研究面板，也不自动安装 systemd/launchd 配置。
