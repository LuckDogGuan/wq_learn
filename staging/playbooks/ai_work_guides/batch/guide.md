# 指引：批量回测与跟踪

## 用途
一次性回测多个候选表达式并跟踪状态。

## 最少路径
- 小批量（2-8 个）：`create_multi_simulation`（一次提交，等待全部完成）。
- 大批量 + 断点续传：`brain-simAlphasinBatch-and-track`（JSON 输入 → CSV 状态 → resume）。
- 错误排查：`lookINTO_SimError_message`（批量看模拟错误）。

## 限制
- 每批表达式 2-8 个；模拟前先本地校验（`alpha-expression-verifier`）。
- 长任务用后台 / `--detached`；超时不立即判失败，先查产物 / CSV 行数。
- 只在一处跟踪（fingerprint + 同一 CSV），不重复起跑。

## 相关
- 生成候选：`idea/guide.md`；选优后：`submit/guide.md`。
