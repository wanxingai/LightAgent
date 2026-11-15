# 持续研究入口迁移

v1.0.0 将研究契约、实验、评估、晋升、历史选择和研究调试面板移到可选 **LightResearch** 扩展。其开发目录现在与 LightAgent 同级，默认不随 LightAgent 安装或参与 CI。

- 普通持久任务使用 [通用持久执行指南](durable_execution.zh-CN.md)。
- 研究开发指南位于同级项目的 `../LightResearch/docs/persistent_research.zh-CN.md`（路径相对 LightAgent 根目录）。
- 本地调试面板为 `LightResearch.panel.ResearchPanel`，核心 runner 不再接受 `--panel-port`。
- 新研究代码使用 `from LightResearch import ResearchService, ResearchContract`。
- 旧 `mode="persistent"` 仅在显式调用 `LightResearch.enable_legacy_api()` 后可用，继续保持研究语义；未注册时会报迁移错误，不静默改行为。

先确认 LightResearch 声明兼容 LightAgent `1.0.0`。早期 LightResearch 开发包的 `<0.14.0` 依赖上限需要在扩展项目单独更新。兼容后，从 LightAgent 根目录安装两个相邻的开发项目：

```bash
python -m pip install -e . -e ../LightResearch
```

使用构建产物时，在同一次 `pip install` 中指定两个匹配的 wheel。核心不反向依赖扩展，单独安装 LightAgent 不需要 LightResearch。参见[核心和联合验收命令](clean_environment_acceptance.zh-CN.md)。

历史控制目录、版本摘要、实验、工件和回执不得删除或重写来绕过校验。已固定旧执行摘要的实例应使用备份的 v0.12.0 wheel，或经过完整审查后建立新执行身份。详见 [v1.0.0 开发计划](lightagent_v100_development_plan.zh-CN.md)。
