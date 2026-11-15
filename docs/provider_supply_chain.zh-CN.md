# Provider 供应链与重授信

适用源码：`1.0.0`。此契约针对受信宿主注册的 Skill、MCP 和通用 Provider，不提供插件下载器，也不从清单动态导入 Python。

## 信任链

1. 宿主从可信渠道配置 `(publisher, key_id) -> Ed25519 公钥`，不能接受包内自报公钥作为信任根。
2. 发布者签署 `ProviderAttestation`，绑定 schema、kind、name/version、递增 release_sequence、完整文件树摘要、Provider 配置/能力摘要和有效期。
3. 宿主核对摘要后显式调用 `ProviderTrustStore.approve(..., expected_digest=..., note=...)`，在现有 ControlStore 中保存批准和审计。
4. 用 `AttestedProvider` 包装受信代码，再交给 CapabilityRegistry/CapabilityGate。挂载、启动、调用和健康检查重新验证；不自动信任新内容。
5. 文件、路径、配置、能力、Skill 路径或 MCP 连接配置发生变化，需要新的签名/宿主批准；同序号不同内容和版本降级被拒绝。配置变更不能通过 `reload()` 先执行再补审批，必须构造新的 Provider。

`release_sequence` 是发布者的单调序号，不按版本字符串排序。密钥轮换不能重置该序号。相同内容迁移到另一个本地目录也需要宿主批准；清单本身不包含机器私有路径。

签名实现使用可选的 [cryptography Ed25519 API](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/)，没有自制加密算法。核心默认导入不要求此依赖；签名功能缺少依赖时拒绝执行，不降级为无签名信任。

```bash
pip install 'lightagent[signing]'
PYTHONPATH=. python example/17.signed_providers.py
```

完整示例：[离线签名 Provider](../example/17.signed_providers.py)。示例私钥只在内存生成，仅用于演示；生产私钥应由发布者离线管理。

## 状态与撤销

- `ProviderTrustStore.verify()` 只读校验当前批准，不会自动批准新版本。
- `revoke(attestation)` 撤销当前发布；陈旧发布不能误撤销另一个新发布。
- `revoke_key(publisher, key_id)` 持久撤销密钥，重启后仍有效。新密钥必须由宿主重新配置，并提供新签名和批准。
- 批准/撤销事件只记录身份、清单和说明的摘要，不记录私钥、原始 Provider 配置或工具内容。
- 信任存储是宿主权限边界，不是多用户鉴权服务。不要把 approve/revoke 暴露为模型工具或未经鉴权的 HTTP 路由。

## 文件与执行边界

本地文件验证当前要求 POSIX。目录通过固定目录 FD 遍历，拒绝符号链接、硬链接、特殊文件和检查期间的目录/文件替换；限制深度 32、总条目 2048、文件数 1024、单文件 2 MiB、总内容 16 MiB。签名应作为目录外的独立 sidecar 保存，文件树内没有自动排除项。

批准后的包及信任数据库必须放在模型/容器不可写的宿主目录中。签名检查不是对抗恶意宿主写入者的文件锁，也不是安装后的代码沙箱；不要让被执行工具同时改写批准包。此契约验证声明和文件，不证明任意 Python 对象的实现可信，更不能证明远端 MCP 服务的内部代码。

`SkillProviderAdapter` 和 `MCPProviderAdapter` 提供动态绑定摘要。MCP endpoint、启动配置、工具集合变化会导致旧批准失效；远端服务实际实现和 TLS/身份治理仍由部署方负责。签名不授予网络、Sandbox、敏感操作审批或用户权限，CapabilityGate 和 Guardrails 继续独立生效；工具返回值仍是不可信数据。

## Worker 接入

Worker 的 `ProviderComposition` 可显式配置 `provider_trust_store` 与 `provider_attestations`。严格模式下，Skill/MCP 分组缺少批准即拒绝挂载；后续文件或绑定变更会在调用前拒绝。MCP server 配置/schema、Skill 实际路径和工具参数纳入动态绑定；签署的必须是实际组合后的 ToolProvider，而不是另一套不同能力清单。

现有声明式插件的兼容入口没有被静默替换；新契约不会自动把旧插件批准变成 Provider 执行批准。产品默认启用及管理 UI 由 Worker 宿主配置，不属于核心的自动行为。

## 安全矩阵

| 类别 | 已覆盖的拒绝/恢复行为 |
| --- | --- |
| 签名和发布者 | 无批准、错误签名、未知发布者/key、撤销后重启、缺少加密依赖 |
| 清单 | 未知 schema/kind、非法身份、布尔序号、NaN/Infinity、过期与未来生效 |
| 更新 | 内容增删改、位置变化、配置/能力/风险/版本变化、MCP endpoint 漂移、reload 提前产生副作用 |
| 回滚 | 新版本显式批准；旧序号和同序号不同内容不自动获得信任 |
| 文件安全 | symlink/hardlink/FIFO、目录替换、单文件和条目耗尽 |
| 权限 | 有效签名不绕过用户拒绝、Sandbox 或敏感脚本审批；自称 trusted 的 Skill 文本没有批准效力 |
| Worker | 实际能力组合层拒绝未批准/已改变的 Skill 和 MCP 分组 |

单元矩阵不等于远端 MCP 真实服务评估或生产供应链审计。结果和剩余发布门槛见 [v1.0.0 验收记录](v100_validation.zh-CN.md)。
