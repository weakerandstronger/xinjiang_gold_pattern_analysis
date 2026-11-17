# 复现与验证

## 固定版本

输入数据为 10 月 4 日修订版，配置在 `configs/baseline.json`。F1—F3 使用该版最终图形布局，F4 使用补充实验最终蓝色双面板布局。

本仓库是固定论文实验的复现包，未宣称是任意数据集的通用关联挖掘工具。数据版本哈希、10 类特征断言及论文规模断言用于防止无意混用历史版本。

## 命令

```bash
# 安装完整绘图依赖
python -m pip install -r requirements-reproduced.txt

# 完整实验和四图
python scripts/reproduce.py --output runs/full

# 仅数值流程，不依赖第三方包和字体
python scripts/reproduce.py --skip-figures --output runs/numerical

# 方法测试
python -m unittest discover -s tests -v

# 再次核查某个已生成的运行
python scripts/verify.py --run runs/full
```

默认输出为仓库内 `runs/reproduction`，可显式指定其他新目录。命令不覆盖仓库固定结果，也不覆盖已有运行。失败运行保留已输出内容；修复问题后使用新的运行目录。

路径以脚本位置解析，从其他工作目录调用 `scripts/reproduce.py` 的完整路径也可以运行。Python 解释器由当前执行环境决定，不依赖某台机器的 Anaconda 安装位置。

## 执行顺序

1. 读取固定配置并校验输入哈希。
2. 在本轮临时工作目录执行解析、聚合、模式挖掘、分配与内置数学核验。
3. 导出完整结果、案例来源行和论文表格。
4. 保存到本轮 `results/baseline/`、`tables/`、`data/intermediate/`、`validation/baseline/`。
5. 计算二项/三项分解，并从输入数据独立运行仅二项挖掘作交叉核验。
6. 完整运行时绘制 F1—F4，均使用本轮新计算的数据。
7. 将本轮数值产物与仓库发布参考值比较，写入 `validation/regression.json`。

临时工作目录在运行结束时清理。图形不会从旧目录引用图片来代替重绘。

## 数学与工程核验

- 候选库：穷举所有符合次数和观测条件的二项/三项候选，与剪枝实现对照。
- 模式计数：用直接集合运算重新计算 count、valid_n、分组次数及 Lift/证据。
- 分配守恒：模式贡献、特征贡献及属性贡献总量一致；内部份额守恒。
- 阶数分解：分组公式与逐属性分配一致；仅二项重新挖掘与全库二项子集一致；两阶重构原结果。
- 发布回归：22 个 CSV 按表结构、字符串与数值逐单元比较；基线 `summary.json`、`cases.json` 另外完整比较。
- 图件：报告四张 PNG 是否与参考图逐字节一致。图形差异不被误当作数值差异。

数值回归使用绝对容差 $10^{-12}$、相对容差 $10^{-10}$；内置独立数学检查采用原版容差，详见 `validation/baseline/checks.json`。

## 已执行的验证

本次发布在 Windows 和 Python 3.13.5 中运行完整复现。22 个 CSV 和四张 PNG 与本包参考文件逐字节一致，两项方法测试通过。另对照更新前的结果，确认 CSV 差异仅来自中文标签调整。记录见 `validation/release_validation.json`。

`.github/workflows/reproduce.yml` 配置 Ubuntu/Python 3.13 的数值测试与回归，未配置安装依赖或字体，因为该路径只使用标准库。远程 GitHub Actions 尚未执行，不能将工作流文件存在视为跨平台运行已通过。

## 常见问题

**输出目录已存在：** 换用新的 `--output` 路径，不要覆盖参考结果。

**中文字体缺失：** 安装受支持中文字体后重启 Python。若只需核查数值，使用 `--skip-figures`。F1—F4 使用字体回退，实际字体见各图元数据。

**新数据触发哈希或论文快照断言：** 本入口固定复现论文版本。新增数据实验应另建配置、更新输入契约及图形布局，并建立新的预期结果，不应关闭全部断言。

**PNG不同但CSV匹配：** 检查字体、Matplotlib版本和平台。PDF/SVG的创建时间及自动标识也可能变化。

**使用 `python -O`：** 不支持。原方法中的数学核验使用 `assert`，优化模式会跳过这些检查。

## 复现不包含的事项

不修改或生成 Word 稿件，不执行上游 LLM 抽取，不重新核验原始地质文献，不进行远端训练或服务器实验。随包历史审计不等于这些流程在本次整理中重新执行。
