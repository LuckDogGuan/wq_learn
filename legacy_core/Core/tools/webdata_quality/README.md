# WebDataScope 分类导出工具

## 先说明：程序读取的是 ZIP 压缩包内的数据

本目录中的 `webdata_quality.py` 默认读取同目录下的 **`WebData_20260219_V0.10.9.zip`**。程序不是读取某个已经导出的 XLSX，也不是只读取 ZIP 文件名；它会打开 ZIP，并从 ZIP 内部逐项读取 `data/...` 文件。当前目录随工具一起保存的这个 ZIP 就是本次 WebDataScope 离线快照的实际数据源。

如果命令没有传 `--source`，`webdata_loader.py` 会在脚本目录查找 `WebData_*.zip`，按文件名排序后使用最后一个 ZIP；在当前目录中就是 `WebData_20260219_V0.10.9.zip`。也可以用 `--source` 显式指定另一个 ZIP，或指定已解压的同等目录进行离线检查。

程序读取 ZIP 内的数据后，按以下层级筛选并导出离线研究先验：

`Region → Delay → Universe → Category → Dataset → Field`

字段档位表示覆盖率、稳定性、偏度和单边性等离线健康特征，不是 Alpha 回测表现，也不会模拟、提交或修改 Alpha 属性。

## 安装

```powershell
python -m pip install msgpack openpyxl
```

## 基本用法

```powershell
python webdata_quality.py `
  --source "WebData_20260219_V0.10.9.zip" `
  --region GLB `
  --delay 1 `
  --universe TOP3000 `
  --categories "news,model" `
  --field-tiers "T1,T2" `
  --count-min 5 `
  --count-max 500 `
  --sharpe-min auto `
  --fitness-min auto `
  --output "result\GLB_TOP3000"
```

默认只输出满足 `5 ≤ Count < 500`、`Sharpe > min(Region/Delay 平均 Sharpe, 0.4)`、`Fitness ≥ Region/Delay 平均 Fitness` 的字段中性化行。四个门槛参数可填写数字，传空字符串或 `all` 可关闭对应门槛；`--neutralizations` 可指定中性化列表。

`--region`、`--universe`、`--categories`、`--dataset-grades`、`--field-tiers`、`--neutralizations` 支持逗号分隔；省略、空字符串或 `all` 表示不过滤。`--delay` 省略时默认 D1，显式传空字符串或 `all` 才表示全部 Delay。

`--source` 可以是：

- 未解压的 WebData ZIP；
- 已解压的插件根目录；
- 插件中的 `data` 目录。

省略 `--source` 时，程序自动寻找脚本旁最新的 `WebData_*.zip`。

## 输出文件

输出按 `Region/Category` 保存。默认 D1，例如：

```text
result/
  GLB/
    news.xlsx
```

每个 XLSX 只有一张筛选后的 `数据` 表，每行是 `Dataset → Field → Neutralization → Count/Sharpe/Fitness`。没有匹配结果时仍生成只有表头的文件。默认不生成分类 JSON；只有显式使用 `--json-out` 才生成 JSON。

## 文件分工、调用关系与 ZIP 内数据

主入口是 `webdata_quality.py`，其他 Python 文件由它导入使用，不需要单独运行。一次完整执行的实际顺序是：

`webdata_quality.py` 解析命令参数
→ `webdata_loader.py` 打开 `WebData_20260219_V0.10.9.zip`
→ 从 ZIP 读取并解压 `data/oth/*.bin` 和精确字段 archive
→ `webdata_classifier.py` 计算 Dataset 档位、Category、字段 Tier 和风险标记
→ `webdata_exporter.py` 生成并校验 Region/Category XLSX

### Python 文件

| 文件 | 作用 | 实际使用的数据 | 产出/影响 |
|---|---|---|---|
| `webdata_quality.py` | 参数解析、筛选 Region/Delay/Universe/Category、构建统一 ledger，并调用其他模块 | 通过 loader 从 ZIP 读取 `data/oth/info_data.bin`、`data/oth/osis_data.bin`、`data/..._Delay<N>.bin`；读取本地 `tier_rules.json` | 控制完整流程；生成 XLSX、可选 JSON、输出目录 README；本身不生成 Alpha、不提交 Alpha |
| `webdata_loader.py` | 打开 ZIP 或兼容的已解压目录，并把 ZIP 内压缩数据转换成 Python 对象 | 直接读取 ZIP 条目；对 `.bin` 执行 Zlib 解压和 MsgPack 解码，对 JSON 执行 UTF-8 JSON 解码；解析 archive 文件名中的 Dataset/Region/Universe/Delay | 提供 `SnapshotSource`、快照清单和坐标识别；不计算 Sharpe、Fitness 或字段 Tier |
| `webdata_classifier.py` | 对 loader 读出的 ZIP 数据进行分类和字段画像 | Dataset/Category/Field/Neutralization 统计来自 ZIP 内 `info_data.bin`/`osis_data.bin`；Coverage、偏度、峰度、单边性、离散性和频率来自 ZIP 内精确字段 archive；阈值来自 `tier_rules.json` | 生成 `GREEN/YELLOW/RED/GRAY`、`T1-T4`、`FIELD_PROFILE_*`、Category 映射和风险标签 |
| `webdata_exporter.py` | 把主流程整理出的 ledger 写成 XLSX/JSON，并检查工作簿 | 不重新读取 ZIP；使用 `webdata_quality.py` 已整理的 `datasets`、`fields`、`neutralizations` 和门槛结果 | 每个 Region/Category 一个 XLSX，包含 `数据` 表；同时写输出说明、条件格式、冻结表头、自动筛选和工作簿校验 |
| `tier_rules.json` | 配置字段 Tier、稀疏 Category、Category 别名和风险阈值 | 不属于 WebData 快照；是本地规则配置 | 改变字段分档、风险标记和 Category 映射，不改变原始数据 |

### `WebData_20260219_V0.10.9.zip` 内哪些数据真正参与流程

这个 ZIP 是一个包含多个 `data/...` 条目的 WebDataScope 快照。当前主流程不是把所有 ZIP 条目混在一起，而是按下面的用途读取：

1. **`data/oth/info_data.bin`：主统计数据。** 这是 ZIP 内压缩的 MsgPack/Zlib 数据，包含 Region/Delay 范围的 Dataset、Category、Field 统计和 Count/Sharpe/Fitness。程序用它计算 Region/Delay 均值、Dataset 档位、自动 Sharpe/Fitness 门槛、Category 统计和结果排序。
2. **`data/oth/osis_data.bin`：审计和中性化统计数据。** 同样从 ZIP 内读取，用于 Count 审计以及补充 Dataset/Category/Field 的中性化统计。`webdata_loader.py` 将 `info_data.bin` 和 `osis_data.bin` 视为快照必需文件，缺任意一个就停止处理。
3. **`data/<dataset>_<REGION>_<UNIVERSE>_Delay<N>.bin`：精确字段档案。** 这些文件也是 ZIP 内的压缩 MsgPack 数据，文件名携带 Dataset、Region、Universe 和 Delay。程序只在 archive 坐标与命令筛选条件匹配时使用它们，从字段记录读取 Coverage、CoverageRatio、Positive/Negative 比例、IntegerStatus、偏度、峰度、频率及年度历史，进而计算字段 Tier 和风险标记。

4. **`data/dataSetList.json`：快照目录辅助数据。** ZIP 内存在该文件，loader 支持读取 JSON，但当前 `webdata_quality.py` 的字段筛选主链不依赖它推断字段健康，也不把它当作 Alpha 表现数据。

ZIP 中其他 `.bin` 文件如果不能从文件名解析出完整坐标，只会在未指定 Region、Delay、Universe、Category、Dataset 等筛选条件时保留为 `ARCHIVE_NAME_UNPARSED`；程序不会猜测它们的 Region/Universe，也不会拿其他坐标的 archive 冒充当前筛选范围。

因此，`Dataset Sharpe/Fitness` 只能作为社区导航先验，`T1-T4` 只能表示字段健康；两者都不能证明 Alpha 回测通过、生产相关性或可提交性。

## 档位规则

数据集档位复刻插件口径：

- `GREEN`：Dataset Sharpe 高于当前 Region/Delay 均值；
- `YELLOW`：Sharpe 不低于 0，但不高于均值；
- `RED`：Sharpe 小于 0；
- `GRAY`：Sharpe 缺失。

数据集档位默认只展示和排序，不会连带删除字段。只有显式传入 `--dataset-grades` 才过滤数据集。

字段默认采用 `tier_rules.json` 中的稀疏/常规双阈值。T1-T4 都保留在同一张表，可直接筛选。比例越界、厚尾、离散、单边等作为风险标记保留；精确 archive 缺失时使用 `FIELD_PROFILE_UNOBSERVED`，不会借用其他 Universe 数据。

Dataset 到 Category 默认按快照中的正式 Category 前缀映射，已由本地字段目录证实的例外放在 `tier_rules.json` 的 `category_aliases` 中；无法证明的项进入 `UNMAPPED`。

## 旧命令兼容

以下参数继续保留：`--zip`、`--dataset`、`--fields`、`--json-out`、`--top`、`--field-top`、`--universes`、`--universe-top`。

```powershell
python webdata_quality.py --zip "WebData_20260219_V0.10.9.zip" `
  --region GLB --delay 1 --universe TOP3000 --dataset analyst15 `
  --fields --json-out "analyst15.json"
```

## 输入错误与解压

输入位置错误、ZIP 损坏或目录层级错误时，程序会显示完整帮助、检测到的候选文件和可复制的解压命令，并以退出码 2 结束。

工具可以直接读取正常 ZIP；需要手动解压时使用：

```powershell
Expand-Archive -LiteralPath "WebData_20260219_V0.10.9.zip" -DestinationPath "WebData_20260219_V0.10.9"
```

命令默认不使用 `-Force`，避免覆盖已有目录。

## 待办与优化建议 (TODOs & Suggestions)

以下优化建议均作为独立脚本（不修改现有核心逻辑）逐步实现：

### 1. 数据风控与离线测试 (Data Risk & Offline Testing)
- **本地0误差计算自相关性 (Local Self-Corr)**: 引入华子哥 (KZ79256) 提出的本地 0 误差自相关性计算模块，在提交平台前离线拦截高自相关的 Alpha。
- **本地预估 Prod Corr 下限**: 参考 KZ79256 的 Prod Corr 预估方案，在本地利用已过检的 Alpha 集合提前估算 Prod Corr 下限，减少提交额度的浪费。
- **Failed RA/PPA 过滤器**: 结合 WebDataScope 的失败网关统计，对极易在 Turnover、Margin 失败的字段进行预警，并在结果中新增一列 `Risk_Mitigation`（例如提示“高换手风险，建议包裹 decay_linear”）。

### 2. 挖掘策略与算子推荐 (Strategy & Operator Recommendation)
- **Genius Rank 与算子多样性适配**: 借助 KZ79256 插件的 Genius Rank 分析思路，自动推进等级晋升。
  - **核心原理**: Genius 晋升（如从 Expert 到 Master）除了硬性数量要求，对 `Operators` (算子类别如 ts、group、vec) 和 `Datafields` (数据字段) 的多样性有隐藏的卡点。
  - **详细做法**: (1) 自动拉取或解析本地已跑通 Alpha 的算子使用统计表；(2) 识别当前严重缺乏使用的算子家族；(3) 在为新挖掘的数据集生成公式模板时，强行插入缺乏的算子（例如在基础公式外层包裹缺乏的 `group_rank` 或 `ts_zscore`），从而不仅保证回测通过，更能“凑齐”晋升多样性指标。
- **低覆盖度与特殊数据平滑**: 自动识别稀疏数据或 VECTOR 数据，在 Excel 备注中补充推荐使用 `ts_mean` / `vec_avg` 等处理代码段。

### 3. 数据去重与效率提升 (Deduplication & Efficiency)
- **基于相关性剪枝 (Correlation Pruning)**: 结合 KZ79256 等黄金顾问倡导的相关性剪枝方法，在回测前就干掉无效组合。
  - **核心原理**: 如果一阶段的两个基础因子（例如同一数据集内的 `1m_chg` 与 `3m_chg`）在原始层面就具有高相关性（如相关系数 > 0.7），那么不管二阶段包什么复杂的算子，最终产出的 Alpha 依然极大概率互相高相关，从而在平台上报自相关失败。
  - **详细做法**: 
    1. **矩阵计算**: 获取本批次所有待测字段（或已生成的一阶 Alpha）的两两相关系数矩阵。
    2. **图论聚类 (团划分)**: 设定一个相关性阈值（通常设定为 `0.7` 或 `0.75`），将高于阈值的因子连成一条边，从而划分出若干个高度相关的“团”。
    3. **择优保留**: 遍历每一个“团”，仅保留历史 Sharpe、Fitness 或 Count 最高的一个“代表因子”。
    4. **增量提效**: 被剪枝掉的因子直接跳过后续昂贵的二阶、三阶组合回测。该方法也可直接应用在 SA (Super Alpha) 阶段的最大独立集筛选中。
