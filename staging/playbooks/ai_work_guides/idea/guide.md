# 指引：找想法 / 生成新因子

## 用途
用户要「想法、灵感、新因子、特征」时，给出最少路径。

## 最少路径（按数据基础分类）
- 已有数据集 / 字段 → 特征工程：`brain-data-feature-engineering`（输入 category/delay/region，产出特征想法 md）。
- 要批量候选表达式 → `brain-makeSomeGem`（region/datasetID/delay/universe → `final_expressions.json`）。
- 从模板批量增强 → `brain-enhance-template`（模板须含 `{}` 占位符）。
- 补充灵感 → 先查已安装 skill；仍不足时最后查论坛（见 `forum/guide.md`）。

## 限制
- 想法必须来自真实字段（先用 `get_datafields` 验证存在性）。
- 禁止套通用模板 / 凭空拼字段；每个特征要有逻辑依据。
- 批量任务用 `--detached` 后台运行，超时先查产物再判失败。

## 相关
- 拿到候选后：`optimize/guide.md`（改进）、`evaluate/guide.md`（理解字段）。
