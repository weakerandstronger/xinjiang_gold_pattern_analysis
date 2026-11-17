# 文件整理与来源

## 保留范围

- 10月4日版处理后CSV、固定参数和科学计算逻辑。
- 来源到名称组的映射、合并属性、全部模式与成员、份额、案例来源行及论文表。
- 原最终三张图的排版、PNG/PDF/SVG、全精度绘图数据和几何检查元数据。
- 新增二项/三项分解的完整结果，以及最后确认的蓝色双面板图。
- 可独立运行的复现入口、数学核验、结果回归、方法测试及引用信息。

文件来源采用项目内相对标识记录在`validation/source_manifest.json`，不携带本机账户路径。完整发布清单见`validation/artifact_manifest.json`。

## 排除范围

不纳入Word稿件、PDF文献、整页渲染、临时图片、旧图形草稿、重复嵌套交付包、压缩包副本、对话恢复记录、个人路径、运行环境缓存和服务器配置。历史`update_manuscript.py`、`finalize_delivery.py`依赖私人桌面路径且不属于关联挖掘复现，未纳入。

未迁入更早目录中的其他研究原型，以免把不属于最终论文基线的输入或算法混入本包。这里的“全部实验”是当前已确认的10月4日基线和新增阶数分解。

## 代码调整

`io_records.py`与`mine_support.py`的解析和计算逻辑原样保留。主分析和导表模块改为从本轮工作目录读取配置、将结果写入本轮目录；输出溯源使用相对代码标识和解释器名称，避免发布私人绝对路径。原版三图仅调整输入输出定位，绘图样式不变。

阶数分解整理为独立分析模块，F4 采用最终绘图公式、色彩和布局。总入口通过临时目录运行分析并归档产物。本次发布统一更新了 `HostRockUnit` 的中文显示标签“赋矿岩性”，并重绘显示该标签的图件。

不自动生成GitHub仓库、不提交远端、不填写未提供的仓库地址或许可证。引用只使用用户提供的论文题目与作者。

## 参考的仓库组织方式

- [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science)：数据、代码与输出分离。
- [Cookiecutter Reproducible Science](https://github.com/mkrapp/cookiecutter-reproducible-science)：围绕复现组织科研项目。
- [howfairis](https://github.com/fair-software/howfairis)：清楚提供安装、使用与软件引用入口。
- [GitHub CITATION文件文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)：仓库根目录使用`CITATION.cff`提供机器可读引用。

借鉴其组织原则；未复制这些项目的程序代码、许可证或作者信息。
