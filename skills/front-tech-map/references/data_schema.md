# 数据 Schema

## 节点类型

| 类型 | shape | fillcolor | 边框色 | 说明 | 示例 |
|------|-------|-----------|--------|------|------|
| **海外学者** (person_overseas) | `box` | `#dae8fc` 柔蓝 | 所属流派色 | 学者、实验室负责人 | "Dennis Whyte (MIT PSFC)" |
| **🇨🇳 中国学者** (person_china) | `box` | `#fce5cd` 柔橙 | 所属流派色 | 标注教育背景+上游 | "🇨🇳 谭熠 (清华副教授)" |
| **海外公司** (company_overseas) | `box` (rounded) | `#d5e8d4` 柔绿 | 所属流派色 | 估值/融资+技术来源 | "CFS ($3B+)" |
| **🇨🇳 中国公司** (company_china) | `box` (rounded) | `#f8cecc` 柔粉 | 所属流派色 | 估值/融资+技术来源 | "🇨🇳 星环聚能 (10亿A轮)" |
| **里程碑/装置** (milestone) | `diamond` | `#fff2cc` 柔黄 | 所属流派色 | 年份+关键指标 | "T-3 (1968) Te=1keV" |
| **技术概念** (tech_concept) | `note` | `#e1d5e7` 柔紫 | `#a64d79` | 技术路线差异描述 | "HTS 紧凑高场: REBCO 20T+" |
| **溯源终止** (terminated) | `box` | 同类型色 | 同类型色 | ⛔ 标注终止原因 | "⛔ 领域奠基人" |
| **时间轴** (timeline) | `plaintext` | 无 | 无 | 左侧时间刻度 | "1950s" |

> ⚠️ 节点 fillcolor 按类型固定，边框色（`color`）按所属技术流派动态分配。
> 流派色调色板：蓝 `#3d85c6`、绿 `#6aa84f`、紫 `#8e7cc3`、红 `#cc4125`、橙 `#e69138`、灰 `#999999`。

## 边类型

| 类型 | Graphviz 颜色 | penwidth | Label 模板 | 连接强度 |
|------|--------------|----------|-----------|---------|
| **师承** (mentorship) | `#5b9bd5` 蓝 | 1.5 | "PhD advisor" / "postdoc advisor" | Tier 1 |
| **创办** (founded) | `#27ae60` 绿 | 1.2 | "founded" / "co-founded" | Tier 1 |
| **同一实验室** (lab) | `#5b9bd5` 蓝 | 1.2 | "lab colleague" | Tier 1 |
| **核心维护者** (maintainer) | `#e69138` 橙 | 1.2 | "co-maintainer" | Tier 1 |
| **大厂核心团队脱出** (spun_off) | `#27ae60` 绿 | 1.2 | "spun off from [大厂]" | Tier 1 |
| **大厂同事** (lab_colleague_industry) | `#5b9bd5` 蓝 | 1.2 | "colleague at [大厂 Lab]" | Tier 1 |
| **合著奠基论文** (co_authored) | `#cc4125` 红 | 1.0 | "co-authored [论文]" | Tier 2 |
| **代码派生** (derived) | `#e69138` 橙 | 0.8 | "forked from" | Tier 2 |
| **技术借鉴** (inspired) | `#e69138` 橙 | 0.8 | "独立发展" | Tier 2 |
| **就职** (employed) | `#b4b4b4` 灰 | 0.7 | "at" / "joined" | Tier 1 |
| **技术演进** (evolution) | `#999999` 灰虚线 | 0.7 | — | — |
| **时间轴连线** (timeline) | `#cccccc` 浅灰虚线 | 0.5 | — | — |

> ⚠️ Tier 3 关系（普通引用、同校不同系等）**不出现在图谱中**，详见 `connection_strength.md`。

## 置信度标记

当多源交叉验证未完全通过时，在节点文本中附加：
```
⚠️ Confidence: 70% — OpenAlex 匹配但 LinkedIn 未确认
```

- Wikidata P184 确认 → 85%（如有额外搜索引擎验证则 95%）
- 2+ 来源匹配 → 80-95%
- 仅 1 来源 → 60-70%
- 0 来源可验证 → 不放入图谱
- ⚠️ 诺奖获得者例外：即使只有 1 来源也保留

## 路线特征卡格式

```markdown
## [路线名称] 技术特征
**核心方案**：[一句话描述]
**关键参数**：[qubit 数、操控方式、精度等]
**优势**：[1-2 个核心优势]
**挑战**：[1-2 个核心挑战]
**商业化阶段**：[实验室/原型机/量产/上市]
```
