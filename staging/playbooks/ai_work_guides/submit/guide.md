# 指引：提交前审查 / 过测试

## 用途
准备提交时，用最少路径确认「能否提交、值不值得提交」。

## 最少路径
1. 硬检查：`get_submission_check`（Fitness / Sharpe / Turnover / Weight / Sub-universe / 相关）。
2. 对照阈值：`brain-how-to-pass-AlphaTest`（D1: Sharpe>1.25、Fitness>1 等）。
3. 相关性：`check_correlation`（阈值 0.7）；本地快算用 `brain-calculate-alpha-selfcorrQuick`。
4. 值不值得：`brain-alpha-judge`（平台检查 + 语料规则 + 趋势上下文）。
5. 提交：仅整理候选与说明，由用户在平台手动提交。

## 限制
- 严禁调用 `submit_alpha`；AI 不得以任何方式自动提交。
- 审查与人工提交过程写入 `guides/submit/submission_log.md`。
- `PROD correlation ≥ 0.7` 视为不合格，即使其他全过。
- ATOM（单数据集）优先，享受放宽阈值。
- 年度统计缺失 >5 年视为数据质量问题，先补 `ts_backfill` 再提。

## 相关
- 不过：`optimize/guide.md`；数据问题：`evaluate/guide.md`。
