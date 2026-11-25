# 224个可调用模板函数

按8个用途模块放置。每个函数接受field及可选窗口/分组参数，直接返回Fast Expression。爬山实际注册module/function调用，不是只提供JSON指引。

```python
from Core.factor.templates.callable_templates.trend_change import average_difference
expression = average_difference('mdl110_value', d=20)
```

收益未验证的模板保留；disabled_templates.py集中记录旧日志差模板、失败范围和原函数本体，爬山筛选时强制跳过。
