# 指引：理解与评估

## 用途
理解一个字段 / 数据集 / 表达式的含义与质量。

## 最少路径
- 字段评估 6 法：`brain-datafield-exploration-general`（覆盖率 / 非零 / 更新频率 / 边界 / 中心 / 分布）。
- 数据集概览：`brain-dataset-exploration-general`。
- 解释表达式：`brain-explain-alphas`（拆字段→算子→文档→综合）。
- 语法 / 算子校验：`alpha-expression-verifier`（所有模拟前必过）。

## 限制
- 评估模拟固定用 Neutralization=NONE、Decay=0、Test Period=P0Y0M。
- VECTOR 字段先包 `vec_*` 算子再评估。
- 字段存在性与属性以 `get_datafields` 返回为准，禁止猜测。

## 相关
- 评估完要改进：`optimize/guide.md`；要提交：`submit/guide.md`。
