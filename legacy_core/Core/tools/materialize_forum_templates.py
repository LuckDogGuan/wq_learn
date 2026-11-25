"""将论坛目录逐项生成真实Python函数；默认调用必须与原始公式一致。"""
import ast
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "factor" / "templates"
GROUPS = {"market", "sector", "industry", "subindustry", "country", "exchange"}
NAMES = {"ts_av_diff": "average_difference", "ts_mean": "moving_average", "ts_delta": "difference",
         "ts_ir": "information_ratio", "ts_std_dev": "rolling_volatility", "ts_rank": "time_series_rank",
         "ts_zscore": "time_series_zscore", "rank": "cross_sectional_rank", "group_zscore": "within_group_zscore",
         "group_rank": "within_group_rank", "group_neutralize": "group_neutralization"}
LOGIC = {"ts_av_diff": "将当前值与滚动均值比较；正值表示高于窗口均值。",
         "ts_mean": "对输入字段取滚动均值，平滑短期变化。", "ts_delta": "计算当前值与历史值的差异。",
         "ts_ir": "按滚动波动调整窗口均值。", "ts_std_dev": "计算输入字段的滚动标准差。",
         "ts_rank": "计算当前值在历史窗口中的排名。", "ts_zscore": "按历史均值和标准差标准化。",
         "rank": "比较输入值在当前截面中的排名。", "group_zscore": "在同一组内标准化输入值。",
         "group_rank": "比较输入值在同一组中的排名。", "group_neutralize": "去除输入值的组间均值差异。"}


def function_body(item, used_names):
    tree = ast.parse(item["formula"].replace("{field}", "field_placeholder"), mode="eval")
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    windows = [node.args[1] for node in calls if isinstance(node.func, ast.Name)
               and node.func.id.startswith("ts_") and len(node.args) > 1
               and isinstance(node.args[1], ast.Constant) and type(node.args[1].value) is int
               and node.args[1].value > 0]
    params = {}
    for index, node in enumerate(windows):
        name = "d" if len(windows) == 1 else f"d{index + 1}"
        params[name] = node.value
        node.value = "__PARAM_" + name
    group_names = list(dict.fromkeys(node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in GROUPS))
    for index, group in enumerate(group_names):
        name = "group" if len(group_names) == 1 else f"group{index + 1}"
        params[name] = group
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == group:
                node.id = "__GROUP_" + name
    expression = ast.unparse(tree.body).replace("field_placeholder", "{field}")
    for name, value in params.items():
        expression = expression.replace(repr("__PARAM_" + name), "{" + name + "}")
        expression = expression.replace("__GROUP_" + name, "{" + name + "}")
    root_call = tree.body if isinstance(tree.body, ast.Call) else None
    simple = root_call is not None and len(calls) == 1
    op = calls[0].func.id if calls else "transform"
    base = NAMES.get(op, op) if simple else op + "_transform"
    name = base if base not in used_names else base + "_" + item["template_id"].split(".")[-1][:8]
    used_names.add(name)
    operators = list(dict.fromkeys(node.func.id for node in calls))
    logic = LOGIC.get(op, "按下列公式对单一输入字段进行统计变换。")
    if not simple:
        logic = "依次组合 " + "、".join(operators) + "；变换方向以模板公式为准，收益尚未验证。"
    signature = ", ".join(["field"] + [f"{key}={value!r}" for key, value in params.items()])
    doc = [item["usage_category"], f"逻辑 (Logic): {logic}", f"模板 (Template): {item['formula']}",
           "使用算子 (Operators Used): " + ", ".join(operators),
           "参数建议 (Parameter Recommendations): " + (", ".join(f"{key} 默认{value!r}，窗口可比较20或60（必须重新验证）" if key.startswith("d")
               else f"{key} 默认{value!r}，需有效分组字段" for key, value in params.items()) or "无窗口参数；替换field即可。"),
           "验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。",
           f"模板ID: {item['template_id']}", f"来源帖子: {item.get('source_url', '')}"]
    code = f"def {name}({signature}):\n    \"\"\"\n" + "\n".join("    " + line for line in doc) + "\n    \"\"\"\n"
    code += f"    return f{expression!r}\n"
    return name, params, code


def main():
    path = ROOT / "admin_verified_catalog.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    used_names = set()
    for item in data["templates"]:
        item["stages"] = [1, 2, 3]  # 用户要求优先验证目录模板，不再被旧Stage1局部流程挡住。
        name, params, code = function_body(item, used_names)
        module = "Core.factor.templates.callable_templates." + item["family"]
        item.update(template_module=module, template_function=name, template_params=params)
        grouped[item["family"]].append(code)
    output = ROOT / "callable_templates"
    output.mkdir(exist_ok=True)
    (output / "__init__.py").write_text('"""224个可直接调用的论坛模板函数；爬山通过注册清单按分类加载。"""\n', encoding="utf-8")
    for family, bodies in grouped.items():
        (output / (family + ".py")).write_text('"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""\n\n' + "\n\n".join(bodies), encoding="utf-8")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text("# 224个可调用模板函数\n\n按8个用途模块放置。每个函数接受field及可选窗口/分组参数，直接返回Fast Expression。爬山实际注册module/function调用，不是只提供JSON指引。\n\n```python\nfrom Core.factor.templates.callable_templates.trend_change import average_difference\nexpression = average_difference('mdl110_value', d=20)\n```\n\n收益未验证的模板保留；disabled_templates.py集中记录旧日志差模板、失败范围和原函数本体，爬山筛选时强制跳过。\n", encoding="utf-8")
    print(json.dumps({"functions": sum(len(items) for items in grouped.values()), "modules": len(grouped)}))


if __name__ == "__main__":
    main()
