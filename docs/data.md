# 数据与中间产物

## 数据版本

唯一分析输入为 [`1004end_entity_summary.csv`](../data/processed/1004end_entity_summary.csv)。SHA256：

```text
090ab0ba13b6ce86eb81fc0b8d9a9228a7cb189c3025c81ba0a90cd9d4ed90c2
```

这是处理后属性数据，不是原始文献或直接观测测量。保留原始提供的 CSV 字节；本次整理未修改属性内容。字符清理和名称组合并由代码在运行时完成。

## 输入字段

| 字段 | 含义 | 用途 |
|---|---|---|
| `Deposit` | 矿床名称记载 | 标准化后作为名称组合并键 |
| `doc_id` | 来源记录标识 | 连接来源行；不等同于已核验的唯一文献 |
| `Alteration` | 蚀变 | 分析 |
| `Fluid` | 流体 | 分析 |
| `Geochem` | 化探 | 分析 |
| `Geophysics` | 物探 | 分析 |
| `HostRockUnit` | 赋矿岩性 | 分析 |
| `IntrusiveBody` | 侵入体 | 分析 |
| `Mineral` | 矿物 | 分析 |
| `Region` | 区域 | 分析 |
| `StratUnit` | 地层 | 分析 |
| `Structure` | 构造 | 分析 |
| `Isotope`（兼容规则） | 同位素 | 本版CSV没有该列；解析器遇到该列时也会排除 |

355 条来源聚合后为 76 个名称组。760 个名称组—特征单元中，555 个已观测、205 个未知；394 个多值、161 个单值。1037 个类型化属性中 777 个只在一个名称组出现，153 个达到模式候选基本项门槛。

## 全库结果与追溯表

所有结果表保存在 `results/baseline/`。CSV 使用 UTF-8 BOM，列表/字典单元格使用 JSON 字符串；读取时不要直接按逗号拆分行。

| 文件 | 粒度 | 主要内容 |
|---|---|---|
| `entities.csv` | 名称组 | `entity_id`、名称、来源行数、按特征聚合后的属性 |
| `group_sources.csv` | 来源行 | 名称组 ID、CSV 原始行号、doc_id、原名 |
| `features.csv` | 特征 | score、share、rank、observed_n、coverage |
| `items.csv` | 类型化属性 | item_id、typed_key、次数、全局与内部份额 |
| `patterns.csv` | 正共现模式 | stable_key、阶数、组数、count、valid_n、support、group_lift、evidence、匹配名称组 |
| `pattern_members.csv` | 模式—属性成员 | pattern_id、item_id、特征和原值 |
| `display_selection.csv` | 图形展示项 | 入选池、排序、展示位置与规则 |
| `label_map.csv` | 属性显示映射 | 原词与标签，无语义缩写 |
| `cases.json` | 选定案例 | 模式、匹配名称组及单来源/并集支持数 |
| `case_record_evidence.csv` | 案例中的来源行 | 该行覆盖哪些模式属性、是否完整共述 |
| `summary.json` | 全局汇总 | 数据规模、模式数、总证据、输入哈希 |

`pattern_id` 和 `item_id` 是当前版本编号，跨数据版本可能改变；跨版本匹配使用 `stable_key` 和 `typed_key`。名称组 ID 由当前输入顺序生成。

## 阶数分解

`results/order_decomposition/` 中保留：

- `patterns_order2.csv`、`patterns_order3.csv`：完整阶数子集。
- `features_order2.csv`、`features_order3.csv`：各阶排序的原始分数、阶内份额及对总量贡献。
- `feature_reconciliation.csv`：每个特征的二项/三项分数、两种归一化、原值、重构值及误差。`*_share` 为 0—1 比例，`*_pp` 为百分点。
- `summary.json`、`checks.json`：参考运行的统计和核查记录。新运行的总验证位于其 `validation/` 下。

## 绘图与论文表

`data/intermediate/F1.csv` 为特征汇总，F2 为 30 个展示属性，F3 为 8 个展示模式。`figures/F1`—`F3` 中 `plot_data.csv` 是独立绘图输入副本，为图件自包含而保留；F4 的 `display_data.csv` 同时存全精度份额和一位小数显示标签。

`tables/` 包含数据规模、固定分析参数、案例统计、主题模式以及 F3 匹配集合重叠表。Jaccard 只描述展示模式的匹配集合重叠，不是外部准确率。

当前 `source_lookup.json` 为空，源文献标题/页码没有补齐；`case_record_evidence.csv` 中的原文定位占位字段不应作为已核验原文证据引用。
