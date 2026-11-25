"""从只读导出的日志生成差模板隔离文件；稳定ID/原公式阻止换版本重新入池。"""
import ast
import json
import pprint
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "factor" / "templates"


def main(source):
    report = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = report["bad_scopes"]
    code = ['"""差模板隔离文件：来自实际日志，包含停用原因、证据和原模板本体。',
            '本文件绝不注册轮动。相同模板即使代码版本变化，仍按日志范围停用；',
            '相同公式的论坛新名称也不能绕过停用。PENDING不是失败，其他区域的优良结果保留。', '"""', '',
            'import ast', 'from functools import lru_cache', '', '# 范围为Region×Category×Stage及原参数/公式；不可误当全局字段黑名单。',
            'DISABLED_SCOPES = ' + pprint.pformat(rows, width=110, sort_dicts=False), '',
            '@lru_cache(maxsize=8192)',
            'def _canonical(expression):',
            '    if not isinstance(expression, str):',
            '        return None',
            '    try:',
            '        tree = ast.parse(expression, mode="eval")',
            '        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}',
            '        groups = {"market", "sector", "industry", "subindustry", "country", "exchange"}',
            '        fields = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} - calls - groups',
            '        if len(fields) == 1:',
            '            field = next(iter(fields))',
            '            for node in ast.walk(tree):',
            '                if isinstance(node, ast.Name) and node.id == field:',
            '                    node.id = "FIELD_PLACEHOLDER"',
            '        return ast.dump(tree, include_attributes=False)',
            '    except (SyntaxError, ValueError):',
            '        return None', '',
            'def blocked_reason(candidate, context):',
            '    """从轮动入口直接排除日志差模板，不允许改名/改版本自动复活。"""',
            '    params = candidate.get("resolved_params") or candidate.get("params") or {}',
            '    expression = candidate.get("expression", "")',
            '    canonical = _canonical(expression)',
            '    for row in DISABLED_SCOPES:',
            '        if any(str(row.get(key, "")) != str(context.get(key, "")) for key in ("region", "category", "stage")):',
            '            continue',
            '        saved = row.get("resolved_params") or {}',
            '        if isinstance(saved, str):',
            '            import json',
            '            saved = json.loads(saved)',
            '        if row["template_id"] == candidate.get("template_id") and all(params.get(key) == value for key, value in saved.items()):',
            '            return row["reason"]',
            '        for original in row.get("expressions", []):',
            '            if canonical is not None and _canonical(original) == canonical:',
            '                return row["reason"]',
            '    return ""', '', '# 下列原函数仅保全审查；显式抛错保证不能被误用作轮动。']
    for template_id in dict.fromkeys(row["template_id"] for row in rows):
        body = report["template_bodies"].get(template_id)
        related = [row for row in rows if row["template_id"] == template_id]
        name = "disabled_" + re.sub(r"\W", "_", template_id)
        code.extend(['', '# ' + template_id + '；' + related[0]["reason"]])
        if body:
            tree = ast.parse(body["source_code"])
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
            function.name = name
            offset = 1 if function.body and isinstance(function.body[0], ast.Expr) and isinstance(function.body[0].value, ast.Constant) and isinstance(function.body[0].value.value, str) else 0
            function.body.insert(offset, ast.Raise(exc=ast.Call(func=ast.Name(id='RuntimeError', ctx=ast.Load()), args=[ast.Constant(value='历史差模板已隔离，禁止轮动：' + template_id)], keywords=[])))
            code.append(ast.unparse(ast.fix_missing_locations(function)))
        else:
            # 动态局部探针原本没有独立函数，只保全日志中的真实公式。
            expression = next((expr for row in related for expr in row.get("expressions", [])), "")
            code.append(f'def {name}(field):\n    """动态探针原公式保全；非可用模板。"""\n    raise RuntimeError("历史差模板已隔离，禁止轮动")\n    return {expression!r}')
    (ROOT / "disabled_templates.py").write_text("\n".join(code) + "\n", encoding="utf-8")
    (ROOT / "forum_catalog" / "差模板日志证据.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bad_scopes": len(rows), "isolated_templates": len({row['template_id'] for row in rows})}))


if __name__ == "__main__":
    main(sys.argv[1])
