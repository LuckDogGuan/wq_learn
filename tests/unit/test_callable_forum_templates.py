import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "代码" / "优化代码"))
from Core.factor.templates import forum_verified, disabled_templates
from Core.factor.templates.callable_templates.trend_change import average_difference
from Core.factor.filter.expression_checker import verify_alpha_expression
from Core.factor import template_usage


def canonical(expression):
    return ast.dump(ast.parse(expression, mode="eval"), include_attributes=False)


def test_all_224_templates_are_distinct_real_functions_and_match_original_formula():
    catalog = forum_verified.load_verified_catalog()
    assert len(catalog) == 224
    functions = set()
    registry = {entry["template_id"]: entry for entry in template_usage._VERIFIED_FORUM_ENTRIES}
    for item in catalog:
        module = importlib.import_module(item["template_module"])
        function = getattr(module, item["template_function"])
        functions.add((module.__name__, function.__name__))
        expression = function("forum_probe_field", **item["template_params"])
        assert canonical(expression) == canonical(item["formula"].replace("{field}", "forum_probe_field")), item["template_id"]
        assert verify_alpha_expression(expression)["valid"]
        assert "return f" in inspect.getsource(function)
        assert "模板 (Template)" in function.__doc__
        assert registry[item["template_id"]]["function"] == function.__name__
        assert registry[item["template_id"]]["module"] == module.__name__
    assert len(functions) == 224


def test_average_difference_is_directly_callable_with_custom_window():
    assert average_difference("mdl110_value", d=20) == "ts_av_diff(mdl110_value, 20)"


def test_old_bad_template_cannot_return_by_version_or_renaming():
    row = next(row for row in disabled_templates.DISABLED_SCOPES if row["expressions"])
    context = {key: row[key] for key in ("region", "category", "stage")}
    candidate = {"template_id": "renamed.new.template", "template_version": "new-version", "expression": row["expressions"][0]}
    assert disabled_templates.blocked_reason(candidate, context)
    candidate["template_id"] = row["template_id"]
    params = row.get("resolved_params") or {}
    if isinstance(params, str):
        import json
        params = json.loads(params)
    candidate["resolved_params"] = params
    assert disabled_templates.blocked_reason(candidate, context)
    other_context = {**context, "region": "UNRELATED"}
    assert not disabled_templates.blocked_reason(candidate, other_context)


def test_quarantined_functions_cannot_be_called():
    functions = [value for name, value in vars(disabled_templates).items() if name.startswith("disabled_") and callable(value)]
    assert len(functions) == 21
    for function in functions:
        parameters = inspect.signature(function).parameters
        args = ["field" for parameter in parameters.values()
                if parameter.default is inspect.Parameter.empty and parameter.kind in
                {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}]
        with pytest.raises(RuntimeError):
            function(*args)
