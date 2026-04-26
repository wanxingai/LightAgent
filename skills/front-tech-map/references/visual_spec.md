# 可视化规范 (Graphviz SVG)

> Phase 4 节点配色、边样式、时间轴、Legend 的完整规范。

## 节点类型 + 配色规范

节点类型完整定义（shape / fillcolor / 边框色）见 [data_schema.md](data_schema.md#节点类型)，此处不再重复。

⚠️ 必须严格遵守：节点 fillcolor 按类型固定，边框色（`color`）按所属技术流派动态分配。

## 流派边框色

由 Phase 0 的 domain_profile 动态确定，按流派发现顺序依次分配：

| 序号 | 边框色 | 色名 |
|------|--------|------|
| 流派 1 | `#3d85c6` | 蓝 |
| 流派 2 | `#6aa84f` | 绿 |
| 流派 3 | `#8e7cc3` | 紫 |
| 流派 4 | `#cc4125` | 红 |
| 流派 5 | `#e69138` | 橙 |
| 流派 6+ | `#999999` | 灰 |

## 核心节点标注

- **奠基人 / 核心贡献者**：`penwidth='2.2'`（粗边框），`bold=True`
- **溯源终止节点**：节点内标注 `⛔ [终止原因]`
- **中国学者**：必须标注完整教育背景（硕导/博导/博后/访问学者）

## 边类型

| 边类型 | 样式 | penwidth | 说明 |
|--------|------|----------|------|
| PhD advisor | 实线 + label | 1.5 | Tier 1 师承 |
| 创办公司 | 实线 + `#27ae60` 绿 | 1.2 | founded/co-founded |
| 技术→芯片 | 虚线 | 0.7 | 技术概念→实现 |
| 合作/影响 | 虚线 | 0.7 | 非师承的学术关联 |
| spin-off | 实线 + `#27ae60` 绿 | 1.2 | 学术→商业化 |

> 完整边类型定义（含 AI 领域扩展）见 [data_schema.md](data_schema.md)。

## 时间轴锚定

⚠️ 必须实现：
- 左侧使用 `plaintext` 节点作为时间刻度（如 1971, 1980s, ~2005, 2014, ...）
- 时间刻度之间用虚线连接：`style='dotted', arrowhead='none'`
- 使用 `rank=same` 子图约束：同一时代的节点水平对齐

```python
with g.subgraph() as s:
    s.attr(rank='same')
    s.node('E2014'); s.node('TrueNorth'); s.node('BrainScaleS')
```

## 技术概念节点

⚠️ 必须包含：
- 每个技术路线至少 1 个紫色技术概念节点
- 节点内标注：技术名称 + 核心差异 + 代表性实现
- 技术概念之间用虚线表示演进关系

## Legend 子图

- 必须包含 `cluster_legend` 子图
- 展示所有节点类型 + 颜色含义
- 位置：图谱右下角

---

## 布局约束规范（Layout Constraints）

> [!CAUTION]
> Graphviz `dot` 引擎的节点位置完全由**边方向**和**rank 约束**决定。如果以下规则未严格遵守，图谱上的节点位置将不可预测。

### 1. 边方向规则（source → target = 上 → 下）

`rankdir=TB` 意味着**边的 source 在上方，target 在下方**。每种边类型的 `edge()` 调用方向必须遵守：

| 边类型 | source（上方） | target（下方） | 语义 |
|--------|---------------|---------------|------|
| PhD advisor / postdoc advisor | 导师 | 学生 | 上游在上 |
| founded / co-founded | 创始人 | 公司 | 人→商业实体 |
| spun off from | 大厂/实验室 | 创业公司 | 源组织→衍生 |
| lab colleague | 共同 PI/Lab 节点 | 任一同事 | 或用 `constraint=false` |
| co-maintainer | 项目节点 | 任一维护者 | 或用 `constraint=false` |
| co-authored | 较早/较资深作者 | 较晚/较年轻作者 | 按时间/资历 |
| forked from | 原项目 | fork 项目 | 上游在上 |
| 技术演进 (evolution) | 旧技术/里程碑 | 新技术/里程碑 | 时间正序 |
| 时间轴 (timeline) | 较早年份 | 较晚年份 | 时间正序 |

⚠️ **绝不允许反向连边**。如果语义上「导师受学生影响」，不画反向边，而是在报告中文字说明。

### 2. 流派聚类（Cluster Subgraphs）

Phase 3 输出的 3-8 个流派，每个流派必须使用 `cluster_` 前缀的子图包裹：

```python
with g.subgraph(name='cluster_tokamak') as c:
    c.attr(label='Tokamak 路线', style='dashed', color='#3d85c6')
    c.node('Dennis_Whyte')
    c.node('CFS')
    # ... 该流派的所有节点
```

- `cluster_` 前缀让 dot 引擎画出可见的分组边界
- 跨 cluster 的边会自动绕行，保持组内紧凑
- cluster 内的节点不会被 dot 引擎散布到其他 cluster 中

### 3. Edge Weight / Constraint 设置

| 场景 | Graphviz 属性 | 效果 |
|------|--------------|------|
| 师承链（核心骨架） | `weight=3` | 强制垂直对齐，减少弯折 |
| 创办公司 | `weight=2` | 次优先垂直对齐 |
| 跨流派关联（co-authored, inspired） | `constraint=false` | 不影响垂直 rank 排列 |
| 时间轴→内容节点的隐形对齐边 | `style=invis, weight=0` | 辅助水平对齐但不显示 |
| 同级节点横向排列（如同门师兄弟） | `constraint=false` | 避免强制一个在另一个上方 |

⚠️ **不设 weight 的后果**：dot 引擎会让所有边权重相同，导致师承链弯折、公司节点跑到导师上方。

### 4. 时间轴 Rank 锚定

```python
# 1) 时间轴节点串联（已有规范）
timeline_years = ['1960s', '1980s', '2000s', '2010s', '2020s']
for i in range(len(timeline_years) - 1):
    g.edge(timeline_years[i], timeline_years[i+1],
           style='dotted', arrowhead='none')

# 2) 每个时间段的 rank=same 必须包含对应年代的内容节点
with g.subgraph() as s:
    s.attr(rank='same')
    s.node('2010s')        # 时间刻度
    s.node('CFS')          # 2018 年创办
    s.node('Pasqal')       # 2019 年创办

# 3) 奠基人/最早节点用 rank=min 固定在顶部
with g.subgraph() as s:
    s.attr(rank='min')
    s.node('Lev_Artsimovich')  # 1960s 奠基人
```

### 5. 节点排列顺序

同一 `rank=same` 子图内的节点，dot 引擎按**代码中添加节点的顺序**从左到右排列。因此：
- 同一 rank 下，先添加「主线人物」，再添加「分支人物」
- 国内节点和海外节点交替排列会导致视觉混乱 → 建议按流派 cluster 自然分组

### 6. 调试 checklist

生成 SVG 后，必须检查以下布局问题：

- [ ] 导师是否在学生上方？（如果不是 → 检查边方向）
- [ ] 同一流派的节点是否在同一个 cluster 内？（如果散布 → 检查 `cluster_` 前缀）
- [ ] 公司节点是否在创始人下方？（如果不是 → 检查 `founded` 边方向）
- [ ] 时间轴是否从上到下递增？（如果跳跃 → 检查 `rank=same` 绑定）
- [ ] 是否有边穿越整个图谱造成视觉混乱？（如果有 → 给该边加 `constraint=false`）
- [ ] Legend 是否与主图重叠？（如果重叠 → 调整 `cluster_legend` 位置）
