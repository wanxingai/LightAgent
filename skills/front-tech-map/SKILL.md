---
name: front-tech-map
version: 2.1.1
author: "Yilin"
description: "全自动生成前沿技术领域的全景图谱。适用于以技术为核心的赛道（如量子计算、核聚变、AI Agent 等），通过双向挖掘（正向追踪学术源头 + 逆向溯源独角兽创始团队）构建学术→开源→商业化的完整脉络。触发词：「技术mapping」「技术全景图」「technology map」「赛道图谱」「前沿技术」「技术路线图」。"
---

# Technology Mapping Skill (v2.1.1)

## Overview

全自动生成指定前沿技术领域的技术全景图谱（技术源流 mapping）。通过 7 个阶段的系统性工作流，自动完成环境依赖检查、领域分析、目标发现、师承溯源、剪枝聚类、可视化输出和质量验证。

**核心特点**：
- 🧠 **领域自适应**：LLM 在运行时动态分析领域特征并生成定制化搜索策略（替代固定模板）
- 🔄 **双向挖掘**：正向追踪学术源头 + 逆向溯源明星项目创始团队
- 🔗 **Wikidata 师承查询**：整合 38 万条博士导师关系数据，大幅减少溯源断点
- ✂️ **强力剪枝 + 连接强度分级**：三级连接强度体系，只保留 Tier 1/2 连接
- 📊 **溯源质量可衡量**：自动统计溯源完成率、验证率、孤儿率

## When to Use

当用户需要对一个**以技术为核心的前沿赛道**进行全景式研究时使用：
- "帮我做一个中性原子量子计算的技术mapping"
- "生成 LLM Agent 框架的技术全景图"
- "核聚变领域的赛道图谱"

**不适用**：已高度成熟的非技术驱动产业。

## 输入与输出

### 输入
用户提供一个技术领域关键词：`"中性原子量子计算"` / `"LLM Agent 框架"` / `"核聚变磁约束"`

### 输出
1. **`[Topic]_TechMap.svg`** — Graphviz dot 生成的 SVG 矢量图谱

2. **`[Topic]_TechMap_Report.md`** — 伴随文字报告（节点简介 + 置信度标注 + 溯源统计 + VC 分析结论）

**输出路径**：`[Topic]_TechMap_YYYYMMDD/`

---

## 数据 Schema

> 节点类型表、边类型表、置信度规则详见 [data_schema.md](references/data_schema.md)
> 连接强度三级分层体系详见 [connection_strength.md](references/connection_strength.md)
> 可视化节点配色/边样式/时间轴/Legend 规范详见 [visual_spec.md](references/visual_spec.md)
> VC 分析框架（创始人评估 + 技术路线 + 中外对比 + 可追溯性）详见 [vc_framework.md](references/vc_framework.md)

---

## 搜索工具选择规范

在任何需要执行网页搜索的步骤中，按以下流程选择工具：
1. **优先使用**：yiyanxuangu MCP 工具（get_stock_basic_info、search_securities_code 等）
2. **新闻搜索**：@skill://万行-news 检索工具
3. **Web 搜索**：workbuddy 的网页搜索工具作为补充

---

## 执行工作流

> [!CAUTION]
> 严格按照 Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 的顺序执行。每个 Phase 完成后，在内部检查输出质量，再进入下一个 Phase。

---

### Phase 0: 环境准备与依赖检查 🛠️

**目的**：检查依赖是否存在，并安装依赖，作为执行所有图谱生成逻辑的前置第一步。

**步骤**：
1. **检查系统依赖**：执行 `dot -V`，检查核心工具 Graphviz 是否可用。注意：如果遇到报错，**这是正常现象，说明尚未安装。** 作为 Agent 保持冷静，**切勿报错中断或询问用户处理**，而是直接在内置终端自动执行以下安装命令，按以下顺位尝试直到成功：
   - macOS: `brew install graphviz`
   - 备选（若无 brew）：下载免安装版并添加到 PATH
2. **检查 Python 库**：执行 `pip install graphviz`，确保 Python `graphviz` 库已安装。

**Phase 0 交付物**：能够正常调用相应的依赖包和命令行工具（不会抛出 NotFound 的报错）。

---

### Phase 1: 领域适应 & 策略生成 🧠

**目的**：让 LLM 在运行时分析该技术领域的特征，动态生成适配的搜索策略和溯源路径。

**步骤**：

1. **创建文件夹**：创建文件夹 `[Topic]_TechMap_YYYYMMDD`，用于保存所有中间文件、交付物和最终输出。
2. **领域特征分析**：基于 LLM 自身知识，分析以下维度并输出 `domain_profile`：
   ```json
   {
     "domain": "量子计算-中性原子",
     "knowledge_carrier": {
       "论文": 0.8, "专利": 0.3, "开源代码": 0.1, "产品": 0.05
     },
     "talent_flow_pattern": "大学PhD → 博后 → 教授创业 or 大厂",
     "known_anchor_persons": ["Mikhail Lukin", "Antoine Browaeys", "..."],
     "known_anchor_companies": ["QuEra", "Pasqal", "..."],
     "china_pattern": "海归教授 + 中科大/清华系",
     "upstream_path_type": "PhD advisor chain (2-3 layers)",
     "special_relations": ["同实验室师兄弟", "共同导师", "技术迁移(冷原子→中性原子)"],
     "search_templates": {
       "company_overseas": "[keyword] startup unicorn funding series",
       "company_china": "[关键词] 中国 创业公司 融资 A轮 B轮",
       "academic": "[person] PhD advisor [field] university",
       "academic_china": "[中文名] 博士 导师 留学 [领域]",
       "lab_alumni": "[advisor] lab alumni students notable startup"
     }
   }
   ```
   - ⚠️ AI/开源型领域：`talent_flow_pattern` 应为 `"大厂核心团队 → 独立创业"` 或 `"顶级实验室 → 开源项目 → 创业"`
   - ⚠️ 硬科技领域（量子/核聚变/生物）：应为 `"大学PhD → 博后/教授 → 创业"`

3. **锚点验证**：用搜索引擎快速验证 2-3 个 anchor，修正偏差。

**Phase 1 交付物**：`domain_profile`（领域特征 + 搜索策略 + 锚点列表），保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

### Phase 2: 全球目标发现 (Target Discovery)

**目的**：找到赛道的"北极星"节点——海外头部公司、国内创业公司、核心开源项目和学术里程碑。

**步骤**：

1. **搜索头部公司（海外）**：使用 `search_templates.company_overseas`，筛选估值 >$1B 独角兽或大科技公司标杆项目。
2. **搜索国内创业公司**：使用 `search_templates.company_china`，筛选融资总额 >1 亿元 或 近两年有公开融资。
   - ⚠️ 以上模板默认面向中国市场。如需覆盖日本/韩国/以色列等其他创业生态，适配当地语言。
3. **搜索核心开源项目**（当 `knowledge_carrier.开源代码 > 0.3` 时）：行业公认的奠基级框架/模型。
4. **搜索学术里程碑与重大奖项**（当 `knowledge_carrier.论文 > 0.3` 时）：诺奖/Wolf Prize/国家最高奖获得者必须纳入。
5. **搜索国内学术源头**：中科院系统、清华/北大/复旦/中科大等重要研究机构。
6. **构建技术演进时间线**：提取 3-7 个关键技术里程碑年份。

**Phase 2 交付物**：Target 列表（12-25 个高价值节点） + 技术演进时间线，保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

### Phase 3: 逆向溯源 (Upstream Tracing)

**目的**：从全部 Target 出发，向上游挖掘源头人物和师承脉络。溯源深度 2-3 层。

> ⚠️ **连接强度规则**：所有关系必须按 [connection_strength.md](references/connection_strength.md) 分类。只有 **Tier 1/2** 进入图谱。
> **核心判定：引用 ≠ 传承**。

**步骤**：

1. **Wikidata P184 快速查询（优先）**：对每个人物先查博士导师关系。有结果 → 跳过搜索；无结果 → 进入渐进式搜索漏斗。
2. **渐进式搜索漏斗**（Wikidata 无结果时）：
   - **第 1 层**（<30s/人）：搜索引擎直查 PhD advisor / 教育背景
   - **第 2 层**（<60s/人）：共同作者交叉验证 + 大学官网
   - **第 3 层**（<2min/人）：中文专用模板 + 新闻/采访
   - 仍未找到 → 标记为孤儿节点
3. **继续上溯导师的导师（2-3 层）**：保留条件—诺奖级 / 培养 2+ 核心人物 / 桥接节点。
4. **溯源终止规则**：满足任一即停止—领域奠基人 / 诺奖图灵奖 / 跨领域边界 / 信息不可获取 / 年代超过阈值（硬科技 60 年、AI/软件 20 年）。
5. **实验室横向扫描**：对核心导师搜索全部重要学生/博士后，发现同门创业者。
6. **AI/开源领域适配**（当 `talent_flow_pattern` 含"大厂"时）：构建「大厂 Lab → 创业公司」溯源链。
7. **VC 分析框架**：每个公司节点必须按 [vc_framework.md](references/vc_framework.md) 标注技术来源标签。
8. **溯源完整性检查** ⛔：逐一检查节点，统计溯源完成率 / 验证率 / 孤儿率。目标：完成率 >70%，孤儿率 <20%。
9. **实体消歧义**：多源交叉验证。

**Phase 3 交付物**：Origin 节点列表 + 关系边 + 孤儿节点清单 + 溯源指标。预期 30-50 个节点，保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

### Phase 4: 强力剪枝 & 正向补漏 (Pruning & Forward Fill)

**目的**：清洗数据质量，聚合为技术流派。

**步骤**：

1. **连接强度过滤**：Tier 1 → 保留；Tier 2 → 保留但标弱连线；Tier 3 → 删除。
2. **节点剪枝**：保留——开创子方向 / 培养 2+ 创业学生 / 奠基开源 / 顶级大奖 / 桥接节点。删除——纯优化论文 / 无商业化纯学术 / 被上游覆盖的中间节点 / 只有 Tier 3 关系的孤立节点。
3. **正向补漏**：对祖师爷级节点，正向查找遗漏的商业化转化。⚠️ 特别检查国内学者/学生。
4. **聚类分组**：按核心技术框架/路线名称聚合为 3-8 个流派。⛔ **绝不允许按国家/地域分组**。
5. **生成技术路线差异注解**：每个 Group 生成「路线特征卡」。

**Phase 4 交付物**：干净的 graph 数据（nodes + edges + groups + route_notes + timeline），预期 40-60 个节点，保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

### Phase 5: 可视化输出 (Graphviz SVG)

**目的**：将图数据转化为高质量、结构化的 SVG 矢量图谱。

**技术方案**：使用 Python `graphviz` 库 + `dot` 布局引擎。

> [!CAUTION]
> 必须使用 Graphviz dot 引擎生成 SVG。禁止使用 Obsidian Canvas (.canvas)、NetworkX + PyVis HTML、或任何替代方案。
> 生成脚本 `generate_techmap.py` 必须使用 `import graphviz` 并调用 `graphviz.Digraph`，输出 `.svg` 文件。

**步骤**：

1. 创建 `generate_techmap.py`，使用 `graphviz.Digraph(format='svg', engine='dot')`
2. 图谱全局设置：白底科研风格，`rankdir: TB`，`dpi: 150`，`fontname: Microsoft YaHei`
3. 节点配色、边样式、时间轴、Legend — 严格遵守 [visual_spec.md](references/visual_spec.md)
4. **布局约束** — 严格遵守布局约束规范（边方向、cluster 聚类、weight/constraint、rank 锚定）
5. 节点/边类型定义 — 严格遵守 [data_schema.md](references/data_schema.md)
6. VC 分析标注 — 严格遵守 [vc_framework.md](references/vc_framework.md)
7. **布局验证** — 生成 SVG 后按调试 checklist 检查布局正确性

**Phase 5 交付物**：SVG 矢量图谱 + 生成脚本，保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

### Phase 6: 质量验证 & 报告生成 📊

**目的**：生成质量报告，让用户了解图谱的可信度和完整度。

**步骤**：

1. **生成伴随报告** (`[Topic]_TechMap_Report.md`)：
   - 赛道概述 + 领域适应分析 + 技术路线列表 + 所有节点清单表 + 关键发现
   - **VC 分析结论**（独立章节，必须包含）：创始人深度排名、路线成熟度对比、中国公司海外溯源清晰度评级、投资风险信号汇总

2. **溯源验证表** ⚠️（必须包含）：`| 人物 | 关系声明 | Source 1 (URL) | Source 2 (URL) | 置信度 | 状态 |`

3. **溯源质量统计**：溯源完成率 / 多源验证率 / 孤儿率 / 平均置信度

**Phase 6 交付物**：文字报告（含溯源验证表 + 质量统计），保存在 `[Topic]_TechMap_YYYYMMDD` 文件夹下。

---

## 依赖技能

| 技能                       | 用途                                                | 必需                   |
| -------------------------- | --------------------------------------------------- | ---------------------- |
| yiyanxuangu MCP            | **首选数据源**：股票/公司/指数基础信息查询            | ⚠️ 必需                 |
| @skill://万行-news         | **新闻搜索**：最新融资、技术突破、公司动态            | ⚠️ 必需                 |
| graphviz (系统+Python库)   | **Phase 5 唯一出图方案**：dot 引擎生成 SVG 矢量图谱 | ⚠️ 必需                 |

---

## 重要原则

1. **全自动**：用户只提供关键词即可启动，一直到生成最终输出交付物，不需要用户确认任何中间结果。
2. **领域自适应**：通过 Phase 1 动态生成策略，不依赖固定模板
3. **适度密集**：目标节点数 40-60 个
4. **国内覆盖**：必须主动搜索国内创业公司（融资>1亿元 或 近两年有融资）
5. **技术差异可见**：每个技术路线 Group 必须有路线特征卡注解
6. **诺奖保留例外**：顶级大奖学者只要与技术路线相关就保留
7. **置信度透明**：无法确认时标注置信度，绝不编造师承关系
8. **中文标注**：人名保留英文原名 + 中文注释，🇨🇳 标记中国公司/学者
9. **时间线必备**：左侧必须有时间轴锚定
10. **VC 分析必备**：每个公司节点必须标注 🏷️ 技术来源
11. **Graphviz dot 标准**：SVG 输出，白底科研风配色
