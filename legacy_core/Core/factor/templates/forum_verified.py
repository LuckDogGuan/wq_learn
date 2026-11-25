"""只读取本地合规检测通过的论坛模板；字段替换后仍由调用方实时重验。"""

import json
import re
from pathlib import Path

from Core.factor.filter.expression_checker import verify_alpha_expression
from Core.factor.templates.admin_distributed import operator_count
from Core.tools.forum_template_audit import strict_unary, _local_checks


def render_formula(field, formula):
    return formula.replace("{field}", field)


def load_verified_catalog():
    path = Path(__file__).with_name("admin_verified_catalog.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("不支持的论坛模板目录版本")
    verified = []
    checker, allowed, _ = _local_checks()
    for item in data.get("templates", []):
        formula = item.get("formula", "")
        expression = render_formula("forum_probe_field", formula)
        local_pass, _ = strict_unary({"raw_expression": formula, "local_names": []}, checker, allowed)
        if (item.get("status") != "LOCAL_PASS_UNVALIDATED"
                or "{field}" not in formula or re.search(r"\{(?!field\})", formula)
                or re.search(r"\b(trade_when|add|multiply)\s*\(", expression)
                or operator_count(expression) >= 6
                or not verify_alpha_expression(expression).get("valid") or local_pass is None):
            continue
        verified.append(item)
    return verified
