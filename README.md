# WorldQuant BRAIN 统一研究与工程工作区（D1-Only）

本仓库整合 WorldQuant BRAIN 顾问研究文档、高确定性知识语料、离线字段快照分析与全新模块化研究引擎 **`wq_research_v2/`**。

## 快速入口

- **全局研究索引与排期**：[docs/整理与研究/00_索引.md](docs/整理与研究/00_索引.md)
- **活跃引擎文档**：[wq_research_v2/README.md](wq_research_v2/README.md)
- **领域术语规范**：[CONTEXT.md](CONTEXT.md) · [docs/整理与研究/09_术语表与交接协议.md](docs/整理与研究/09_术语表与交接协议.md)
- **AI 与工程红线**：[AGENTS.md](AGENTS.md)

## 常用命令

```powershell
# 1. 跨平台环境、依赖、保护资产与 AST 静态自检
python wq_research_v2/check_env.py

# 2. 运行 wq_research_v2 全套离线回归测试（零平台写入）
python -m pytest wq_research_v2/tests -v

# 3. Stage-0 数据字段筛选（从 WebDataScope-1.0.6/data D1 + 华子哥四大差距 + 管理员推荐出发）
python -m wq_research_v2 screen fields --region GLB,ASI,CHN,DEU,GBR --export

# 4. 表达式静态预检（验证 D1、Gold 81 算子、永禁 +/*/trade_when、42 缺陷模板、Alphas=0 纯度）
python -m wq_research_v2 validate --expr "reverse(min(rank(ts_delta(ts_backfill(vec_avg(snt26_top50pctranking),500),55)), rank(ts_decay_linear(ts_backfill(mad_underweight_rating_score,5),378))))" --region DEU --universe TOP500

# 5. 同步最新 92+ 条 OS Alpha 便携 PnL 缓存 & 计算本地 SC / 候选池两两相关性矩阵
python -m wq_research_v2 sc sync
python -m wq_research_v2 sc matrix --alpha-ids mL6vGEzE,j287pqwO,bl8LnbA6,KPVlkqwE --region GBR

# 6. 只读异步轮询远程 PC 与 Alpha Pre-Submission Check（零 /submit 调用）
python -m wq_research_v2 pc check --alpha-ids KPVlkqwE,2rG8ZR8Z
```

## 目录总览

| 顶层目录 | 定位 | Git 追踪 |
| --- | --- | :---: |
| `wq_research_v2/` | **唯一活跃开发引擎**（模块化 D1-Only 研究、筛选、回测、本地 SC/PC、消融与 `Useful` 标签器） | 是 |
| `data/` | `wq_research_v2/` 运行期 SQLite WAL 账本、便携 PnL 缓存、日志与导出 | 否（仅 `.gitkeep` 与 `README.md`） |
| `docs/整理与研究/` | 唯一战略总计划（`00`–`09`）、四阶段流程 JSON/HTML（`workflow/`）、分地区档案（`regions/`）与节点记录（`records/`） | 是 |
| `docs/official_guides/` | 高确定性官方总结、SPC API、官方术语表、`wqapi.hualabtech.com` 全量 API/算子目录、课件与笔记 | 是 |
| `docs/memory/` | 高确定性实证复盘（黑名单登记表、USA D1 复盘、Master 指南、224/RA 审计） | 是 |
| `docs/顾问课堂视频总结/` | 53 段顾问课堂视频整理（原始转录、逐课纪要与 6 份主题知识） | 是 |
| `reference/` | **永久只读参考库**：`2026Q4` 前百榜单、254 管理员原创、264 前百精华与审计账本 | 是 |
| `config/standards/` | RA / PPA 本地标准与禁用字段 JSON | 是 |
| `legacy_core/` | 冻结只读历史 `Core/`（含硬保护 `runtime_data/`）与旧管线参考 | 源码是 / `runtime_data` 否 |
| `scripts/` | 精选可复用小工具（`corr_map`、`webdata_unexploited_analytics` 等）与运维脚本 | 是 |
| `tests/` | 38 个历史离线核心回归与单元测试 | 是 |
| `staging/` | **待实证验证暂存区**：模板、待验总结、MAB 实验与旧分析工具（验证有效晋升，无效删除） | 是 |
| `WebDataScope-1.0.6/` | 唯一离线字段快照源（约 37 MB，Stage-0 筛选入口） | 否 |
| `Password/` | 唯一有效平台凭据目录（严禁提交或泄露） | 否 |

## Git 仓库配置与大日志/敏感文件忽略说明

- **远程仓库（`origin`）**：`https://github.com/LuckDogGuan/wq_learn.git`（默认主分支 `main`）
- **版本库规模控制**：仅追踪源代码、测试、结构化文档、配置模板与静态参考库（`wq_research_v2/`、`docs/`、`config/`、`scripts/`、`tests/`、`staging/`、`legacy_core/` 源码、`reference/`），总追踪体积约 **35 MB**。

### 以下文件已通过根 [.gitignore](.gitignore) 明确排除、不上传至 GitHub

| 排除类别 | 具体路径 / 匹配规则 | 说明与不上传原因 |
| --- | --- | --- |
| **敏感凭据与密钥** | `Password/`、`**/config.yaml`、`.env*`、`*secret*`、`*.key`、`*.pem`、`brain.txt`、`scratch_jwt.json` | 严禁上传任何平台账号、密码、Cookie/JWT 或私钥 |
| **超大历史运行日志与数据库** | `legacy_core/Core/runtime_data/`（本地约 1.32 GB，含 `catalog.db`、`events*.jsonl`、`state.json` 等） | 单文件最高近 480 MB，仅本地只读保留，绝不上传 |
| **新引擎运行期数据与缓存** | `data/*`（仅保留 `data/.gitkeep` 与 `data/README.md`）、`*.db`、`*.sqlite*`、`*.pkl`、`*.parquet` | SQLite WAL 账本、OS PnL 缓存及导出表随运行动态变化，不纳入版本库 |
| **通用日志与临时文件** | `*.log`、`*.log.*`、`*.jsonl`、`logs/`、`**/logs/`、`scratch/`、`tmp/`、`*.tmp` | 防止后续回测/守护进程产生的大体积日志意外提交 |
| **离线字段快照与索引缓存** | `WebDataScope-*/`（约 37 MB）、`.gitnexus/`（约 160 MB）、`__pycache__/`、`.pytest_cache/` | 体积庞大的浏览器插件离线快照与本地代码图谱索引 |
| **二进制、媒体与大导出表** | `*.csv`、`*.xlsx`、`*.pdf`、`*.gz`、`*.zip`、`*.png`/`*.jpg`、`*.mp4` 等 | 遵循仓库大文件过滤规范，避免二进制膨胀污染提交历史 |

### 日常同步与提交前自检

```powershell
# 1. 检查当前改动与待提交文件（确认无大日志与凭据）
git status

# 2. 确认敏感目录与大日志处于被忽略状态
git check-ignore -v Password/config.yaml data/wq_v2_ledger.db legacy_core/Core/runtime_data/catalog.db

# 3. 暂存、提交并推送至 GitHub
git add -A
git commit -m "feat: <简明中文或英文提交说明>"
git push origin main
```
