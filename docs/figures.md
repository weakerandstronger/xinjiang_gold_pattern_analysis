# 图件与数据对应

| 目录 | 文件主名 | 论文或实验含义 | 计算来源 |
|---|---|---|---|
| F1 | `feature_support_coverage` | 原论文图3，全部正模式特征支撑份额及观测覆盖率 | `results/baseline/features.csv` |
| F2 | `feature_internal_support_v3` | 原论文图4，各特征内部Top-5属性 | `data/intermediate/F2.csv` |
| F3 | `high_order_pattern_forest_table` | 原论文图5，8个展示模式及证据 | `data/intermediate/F3.csv` |
| F4 | `feature_support_order2_order3` | 新增二项/三项独立份额对照 | `results/order_decomposition/feature_reconciliation.csv` |

每张图提供 PNG（600 dpi）、PDF 和 SVG。F1—F3 采用 10 月 4 日版的最终布局，F4 采用蓝色双面板布局。“赋矿岩性”标签显示在 F1、F2 和 F4 中。

## 样式与排序

F1沿用原始蓝色柱、灰蓝覆盖率圆点、字体和数值精度；F2、F3保持各自原版排版。F4沿用F1蓝色`#3F6F8E`、9×5英寸画布及字体：左侧a二项，右侧b三项，数值以ROUND_HALF_UP显示一位小数。F4共享原合计份额的特征顺序，以便逐行比较，不在左右各自重新排序。

F4每个面板单独归一化为100%。展示四舍五入后，各标签直接求和可能不严格等于100%；应从CSV全精度值核验。

## 独立重绘前三图

常规使用`python scripts/reproduce.py --output runs/full`即可。若只修改图形样式，可将相应`plot_data.csv`复制到新目录，通过环境变量指定输出位置。例如PowerShell：

```powershell
$env:XINJIANG_FIGURE_DIR = (Resolve-Path 'runs/my-figure').Path
python src/plotting/plot_f1.py
Remove-Item Env:XINJIANG_FIGURE_DIR
```

该目录需要事先存在，且包含该图正确的`plot_data.csv`。F2、F3分别调用`plot_f2.py`、`plot_f3.py`。F4的`render(rows, output)`由总入口调用，输入为阶数重构表的记录列表。

最终图保持原稿的固定数量和坐标范围，仅适用于当前固定实验；新增数据或更多展示项时，应同步调整布局并重新检查文字边界。
