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

见 [AGENTS.md](AGENTS.md) 第 2 节目录职责地图。`Password/`、`data/`、`legacy_core/Core/runtime_data/` 与 `WebDataScope-1.0.6/` 均已纳入根 `.gitignore`，不会进入 Git 仓库。
