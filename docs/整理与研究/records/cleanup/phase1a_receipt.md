# Phase 1A 降噪清理与嵌套 `.git` 清理执行回执

- **执行时间**：2026-11-25 14:34–14:41 (UTC+8)
- **工作区根目录**：`C:\Wq\WorldQuant Brain`
- **受保护资产校验状态**：`ALL_INTACT`（10/10 项文件数、字节数、全量聚合 SHA-256 前后 100% 一致）
- **嵌套 `.git` 残留检查**：`0`（共清除 5 个嵌套 `.git`，全工作区已无任何 `.git` 目录或文件）
- **边界合规**：未触碰 `docs/整理与研究/00`–`09` 及 `records/{rules,fields,sources,hypotheses}`；未执行 `git init` / `git commit`

---

## 一、总体清理成效（Before vs After）

| 指标 | 清理前（Baseline） | 清理后（Final） | 净释放 / 变化 |
| --- | ---: | ---: | ---: |
| 总文件数 | 68,691 | 7,978 | **-60,713 (-88.4%)** |
| 总磁盘占用 | 10.325 GB | 1.910 GB（2,050,500,564 B） | **-8.415 GB (-81.5%)** |
| 其中：硬保护 `Core/runtime_data` | 1,532 文件 / 1.277 GB | 1,532 文件 / 1.277 GB | 0（完整保护） |
| 根 `.gitignore` 过滤后预计 Git 纳管规模 | — | **5,771 文件 / 72.51 MB** | 未忽略 `> 5 MB` 文件 = **0** |

---

## 二、高价值资产前置保留清单（Step 1）

1. **Share Core HTTP 429 重试逻辑摘录**
   - 文件：`docs/整理与研究/records/cleanup/share_core_client_429_ref.txt`
   - 内容：完整提取原 `wqb-share-03/tools/Core/api/client.py`（L178–204）中对 `Retry-After` / `RateLimit-Reset` / `X-RateLimit-Reset` 的 429 退避等待逻辑，并已显式剥离原文件中不安全的 `self.session.verify = False` 与硬编码代理 `127.0.0.1:7897`（附安全警告注释）。
2. **2026Q4 Top 100 论坛精华帖抢救保存**
   - 目录：`管理员论坛爬取资料/Top100_2026Q4_精选/`
   - 扫描范围：`WL13229` 与 `KH94146` 下全部 `参与回复的帖子` 与 `引用的关联帖L2`（共 2,343 篇 Markdown，100% 识别作者头）。
   - 保留成果：按 `TopUser/2026Q4.txt` Rank 1–100 精确匹配 299 份原始文件，按帖子 ID 去重（保留较大较完整版本）后保存 **264 篇独立精华帖**（3.44 MB），覆盖 **43 位** 2026Q4 Top 100 顾问（高产作者包括 `R083 XX42289` 40 篇、`R015 JX79797` 25 篇、`R032 ZS59763` 18 篇、`R047 SZ83096` 16 篇、`R012 JR23144` 15 篇、`R045 RM49262` 15 篇、`R087 KZ79256` 15 篇、`R097 QQ68782` 14 篇、`R072 JL11546` 12 篇、`R075 JG15244` 10 篇等；完整作者明细见附录）。
3. **管理员模板审计索引保留**
   - 保留：`管理员论坛爬取资料/模板/20261012_管理员模板审计/标题筛选与来源清单.json`（742,579 B，校验完好）。
   - 清除：该目录下 `WL13229/`（1,630 文件，31.13 MB）与 `KH94146/`（203 文件，7.88 MB）共 1,833 份重复 `.md` 镜像。
4. **最新版 WebDataScope 归位唯一副本**
   - 将 `wqb-share-03/WebDataScope-1.0.6` 移至根目录 `WebDataScope-1.0.6/`（229 文件，36.77 MB），删除全部旧版副本（根目录与 `goal/` 下 `WebDataScope-0.10.11`、`wqb-share-03/WebData_20260219_V0.10.9` 及 `.zip`）。

---

## 三、分项清理明细（Step 2 & Step 3）

| 类别 | 清理目标 | 清理前文件数 | 释放空间 | 说明 |
| --- | --- | ---: | ---: | --- |
| 论坛冗余图片 | `管理员论坛爬取资料/WL13229/images/` | 14,610 | 2,256.98 MB | 非结构化截图噪声 |
| 论坛冗余图片 | `管理员论坛爬取资料/KH94146/images/` | 7,626 | 1,110.90 MB | 非结构化截图噪声 |
| 论坛非 Top100 关联/回复帖 | `管理员论坛爬取资料/{WL13229,KH94146}/{引用的关联帖L2,参与回复的帖子}/` | 2,343 | 36.11 MB | 已前置提取 264 篇 Top100 精华帖 |
| 模板审计重复镜像 | `管理员论坛爬取资料/模板/20261012_管理员模板审计/{WL13229,KH94146}/` | 1,833 | 39.01 MB | 已保留 `标题筛选与来源清单.json` |
| WebData 巨型导出 | `goal/testFile/webdata_quality_*_20260831`（6 目录） | 1,466 | 1,462.87 MB | 完整保留 `core_regression/` 与全部测试脚本 |
| 临时测试输出 | `goal/testFile/tmp_check*`（17 个）& `batch*_result*`（110 个） | 127 | 0.08 MB | 仅清理临时检查与批结果文件 |
| 重复 Core 副本 | `wqb-share-03/tools/Core/` | 1,845 | 1,400.85 MB | 已提取 429 逻辑；Goal Core 为唯一主本 |
| Share WebData 导出 | `wqb-share-03/tools/webdata_quality/` & `webdata_quality_output_*`（9 目录） | 151 | 96.54 MB | 历史导出产物 |
| 废弃旧账号目录 | `consultant/`（含 `consultant/.git`） | 6,641 | 812.32 MB | 旧账号及 713 MB 旧 Excel |
| 废弃第三方代码仓 | `wqb-share-03/src/worldquant-miner/`（含 `.git`） | 5,994 | 134.99 MB | 第三方旧仓库镜像（polymarket/stone_age 等） |
| 空洞 SQLite 备份 | `local-backup/` | 2 | 130.45 MB | 93.5% 空 freelist 页、0 独有实体 |
| 旧版 WebDataScope & 压缩包 | `WebDataScope-0.10.11`（根+goal）、`WebData_20260219_V0.10.9*`、`wqb-share-03.zip` | 645 | 181.34 MB | 仅保留根目录下 `WebDataScope-1.0.6/` |
| `.gitnexus` 索引 | `goal/.gitnexus`、`wqb-share-03/.gitnexus`、`Ai_Work/.gitnexus` | ~30 | ~239 MB | 本地代码图谱缓存 |
| 临时草稿目录 | `goal/scratch/`、`wqb-share-03/scratch/` | 445 | 101.18 MB | 历史临时草稿 |
| 爬山历史日志/JSON | `goal/代码/优化代码/爬山代码/{hill_climbing_v4.7,background_logs}/` | 5,100 | 67.54 MB | 保留核心代码 `hill_climbing/` 等 |
| 其余废弃顶层目录 | `test_alpha/`、`ACE API [Gold]/`、`新人大礼包/`、`人工智能打工人技能/`、`AIResearchReports/`、根 `skills/` | 107 | 34.64 MB | 冗余旧资料与重复技能子集 |
| 根目录零散临时文件 | `sim.py`、`mine_glb_ppa.py`、`test_*.py`、`*results*.json`、`fields_sample.json`、`mcp_log.txt`（12 文件） | 12 | 0.05 MB | 保留 `CLAUDE.md`、`CONTEXT.md`、`pyrightconfig.json` |
| Python 缓存目录 | 全工作区 `__pycache__/` & `.pytest_cache/`（51 个目录） | 262 | 3.66 MB | 主动跳过 `goal/testFile/core_regression/__pycache__` 以保证受保护目录零修改 |
| 独立清除的嵌套 `.git` | `goal/.git`（229.46 MB）、`wqb-share-03/.git`（201.02 MB）、`Ai_Work/.git`（10.62 MB） | 11,681 | 441.10 MB | 加上随 `consultant/` 与 `worldquant-miner/` 删除的 2 个，共清除 **5 个**嵌套 `.git` |

---

## 四、硬保护资产完整性校验（Before = After，10/10 `ALL_INTACT`）

| 保护资产 | 相对路径 | 文件数 | 字节数 | 聚合 SHA-256（前后完全一致） | 状态 |
| --- | --- | ---: | ---: | --- | :---: |
| Goal Core 运行库 | `goal/代码/优化代码/Core/runtime_data` | 1,532 | 1,371,626,709 | `a44dda1bc2a358867b11ad86895ff1739c4d137999dc52f0c5ee335a25eb4951` | `INTACT` |
| 有效账号凭证 | `goal/Password` | 1 | 332 | `8f04afe4f1a248233a80947a5c9d25f2f2ba44382cf144cc320f4c8a2f7043c1` | `INTACT` |
| 2026Q4 排行榜 | `TopUser/2026Q4.txt` | 1 | 4,624 | `434f4a16a4429d3a8c36f435ad9539bf5d5d28324111ab91f25d442a88865eab` | `INTACT` |
| WL13229 原创帖 | `管理员论坛爬取资料/WL13229/自己发布的帖子` | 192 | 14,935,240 | `2adae88a1d567a08a175d276ffa1bd8bc25e069be64d94c64dcdf901de2e8c2d` | `INTACT` |
| KH94146 原创帖 | `管理员论坛爬取资料/KH94146/自己发布的帖子` | 62 | 1,076,109 | `8f321be924f0bb9ab703565b47b7f4b7ef0b0030dde3df607f0ed77af55ed721` | `INTACT` |
| Core 回归测试集 | `goal/testFile/core_regression` | 28 | 250,753 | `8f0adfc245747678647e00aed4efcf3a3f57d6b2ad1d1342ee5a22cf4be47292` | `INTACT` |
| 爬山韧性测试 | `goal/testFile/test_hill_climbing_resilience.py` | 1 | 59,168 | `b98601a65a7fb037202bd83abcc3af842e180f39e938c9eec8ea4e9dd375a8de` | `INTACT` |
| 根目录指引 | `CLAUDE.md` | 1 | 4,355 | `c421c77bb7428335441a5f134e9337dad5b84b4c018d93ebf01757310c05005b` | `INTACT` |
| 根目录上下文 | `CONTEXT.md` | 1 | 3,698 | `aa9fda1b4c821dfb1930dc9d511389d9f8a79be87199c4686c5feea00a20c76c` | `INTACT` |
| 模板审计清单 | `管理员论坛爬取资料/模板/20261012_管理员模板审计/标题筛选与来源清单.json` | 1 | 742,579 | `b0e413f76c28a19450b896ea5f1236100f3e84b1b87458cfc0da38cd17bbb887` | `INTACT` |

> 注：全工作区未发现任何 `reference/` 目录；`docs/` 目录中仅按授权写入本目录（`docs/整理与研究/records/cleanup/`）下 2 个文件，其余文档零触碰。

---

## 五、清理后工作区顶层分布与统一 `git init` 前检查

### 5.1 顶层目录与文件分布

| 顶层条目 | 类型 | 文件数 | 大小 (MB) |
| --- | --- | ---: | ---: |
| `goal` | DIR | 3,595 | 1,771.11 |
| `wqb-share-03` | DIR | 2,000 | 118.14 |
| `WebDataScope-1.0.6` | DIR | 229 | 36.77 |
| `管理员论坛爬取资料` | DIR | 524 | 24.27 |
| `Ai_Work` | DIR | 1,596 | 4.34 |
| `alpha info` | DIR | 10 | 0.68 |
| `docs` | DIR | 13 | 0.12 |
| `message_images` | DIR | 1 | 0.07 |
| `.claude` / `.vscode` / `TopUser` / `因子提升` / `过程` / 根目录配置文件（5 文件） | MIXED | 10 | 0.02 |
| **总计** | — | **7,978** | **1,955.52 MB (1.910 GB)** |

### 5.2 统一根 `.gitignore` 覆盖与大文件扫描

- 已写入统一根 `.gitignore`（`C:\Wq\WorldQuant Brain\.gitignore`），覆盖敏感凭证（`Password/`、`**/Password/`、`*credentials*.json`、`*secret*`、`.env`、`brain.txt`、`scratch_jwt.json`）、受保护运行库与数据库（`**/runtime_data/`、`*.db*`、`*.sqlite*`、`*.pickle`、`*.pkl`、`*.parquet`）、图片/音视频/压缩包/表格/PDF（`*.png`/`*.jpg`/`*.zip`/`*.pdf`/`*.xlsx`/`*.csv` 等）、各类缓存日志、`WebDataScope-*/` 以及 15 个大体积生成 JSON（原共计 268 MB，含 `full_scan_excluded.json`、`full_scan_fragments.json`、`all_glb.json`、`wqb-share-03/EUR_delay1.json`、`wqb-share-03/{result,tracking}/webdata_*.json`）。
- **未忽略且 `> 5 MB` 的剩余文件**：**0 个**。
- **未忽略且 `2–5 MB` 的剩余文件（4 个，供 Coordinator 在 `git init` 前知悉）**：
  1. `4.79 MB` — `wqb-share-03/result/usa_multisim_candidates.json`
  2. `3.92 MB` — `goal/代码/优化代码/Core/notebooks/Alpha_Test.ipynb`
  3. `3.44 MB` — `goal/代码/优化代码/Core/factor/templates/forum_catalog/quarantined/forum_blocks.json`
  4. `2.85 MB` — `wqb-share-03/result/eur_goal_results.json`
- **子目录遗留 `.gitignore` 提示（4 个）**：
  - `goal/.gitignore`、`wqb-share-03/.gitignore`、`Ai_Work/.gitignore`、`WebDataScope-1.0.6/.gitignore`
  - **特别注意**：`goal/.gitignore` 曾屏蔽了 `总结/`、`代码/优化代码/论坛代码/`、部分 `testFile/` 及 `.gitignore` 本身。Coordinator 在执行统一 `git init` 前可按需审查或移除旧的子目录 `.gitignore`，以免与统一根 `.gitignore` 产生意外屏蔽冲突。

---

## 附录：已保留的 2026Q4 Top 100 作者分布（43 位作者，264 篇去重帖）

| 排名 & 作者 | 篇数 | 排名 & 作者 | 篇数 | 排名 & 作者 | 篇数 |
| --- | ---: | --- | ---: | --- | ---: |
| R004 `ES81271` | 1 | R050 `SC23342` | 1 | R077 `SY90356` | 1 |
| R006 `CR35762` | 1 | R051 `ZH87224` | 9 | R078 `SJ65808` | 7 |
| R009 `JL71699` | 5 | R057 `SM63503` | 2 | R079 `LW67640` | 4 |
| R012 `JR23144` | 15 | R058 `ML38868` | 1 | R080 `ZZ10277` | 1 |
| R013 `LD22811` | 7 | R059 `XJ80376` | 1 | R082 `AJ39409` | 1 |
| R015 `JX79797` | 25 | R065 `QL47372` | 3 | R083 `XX42289` | 40 |
| R016 `XH32267` | 1 | R066 `YX23928` | 3 | R084 `WT73952` | 1 |
| R017 `FD69320` | 9 | R068 `SD81732` | 1 | R086 `LU53797` | 2 |
| R018 `WX89624` | 1 | R070 `JW89289` | 1 | R087 `KZ79256` | 15 |
| R032 `ZS59763` | 18 | R071 `SC77987` | 2 | R090 `LL49894` | 1 |
| R039 `QP72475` | 1 | R072 `JL11546` | 12 | R091 `JL16510` | 6 |
| R045 `RM49262` | 15 | R073 `WX64154` | 1 | R093 `MY49971` | 2 |
| R046 `BA51127` | 1 | R074 `YL58219` | 1 | R095 `JZ61289` | 1 |
| R047 `SZ83096` | 16 | R075 `JG15244` | 10 | R097 `QQ68782` | 14 |
| | | | | R100 `JX14975` | 4 |
