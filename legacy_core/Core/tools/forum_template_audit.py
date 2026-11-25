"""离线论坛模板盘点：先筛标题复制，再提取正文/评论代码块；不调用平台。

原始帖子只读。输出包含每个排除原因与来源哈希；静态可检查不代表收益有效。
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import math
from collections import Counter
from pathlib import Path

TITLE_PATTERN = re.compile(r"模板|模版|Template|Alpha Example|Alpha灵感|Data Idea|Machine Alpha|数据推荐|数据集探索|价量动量|Turnover|turnover|预处理|回归|残差|动量|反转|中性化|算子", re.I)
CALLS = re.compile(r"\b([a-zA-Z_][a-zA-Z_0-9]*)\s*\(")

# 本地语法支持与项目模板库词汇的交集，不猜测平台未知算子。
FORBIDDEN = {"trade_when", "add", "multiply", "rank_by_side"}
GROUPS = {"industry", "subindustry", "sector", "market", "country", "exchange"}
FIELD_SLOTS = {"field", "data", "datafield", "data_field", "field1", "input", "x", "a", "alpha", "signal", "fundamental", "sentiment", "news_sentiment", "finance_var"}
KNOWN_BASE_FIELDS = {"close", "open", "high", "low", "vwap", "volume", "returns", "cap", "assets", "sharesout", "adv20", "eps", "roe"}


def _local_checks():
    project = Path(__file__).resolve().parents[2]
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    from Core.factor.filter.expression_checker import verify_alpha_expression
    from Core.factor.filter.expression_verifier.validator import supported_functions
    operator_library = project / "Core/factor/templates/all_operator_templates.py"
    library_calls = set(CALLS.findall(operator_library.read_text(encoding="utf-8-sig")))
    allowed = set(supported_functions) & library_calls
    # 只接纳标量一元变换；回归/多元及向量输入需要另外的字段类型语义审查。
    allowed -= FORBIDDEN | {name for name in allowed if name.startswith("vec_") or "regression" in name}
    return verify_alpha_expression, allowed, operator_library


def _counts(formula):
    without_strings = re.sub(r'"[^"\n]*"|\'[^\'\n]*\'', '"STRING"', formula)
    function_count = len(CALLS.findall(without_strings))
    symbols = len(re.findall(r">=|<=|==|!=|&&|\|\||[+\-*/<>]", without_strings))
    return function_count, function_count + symbols


def strict_parameter_check(ast):
    """补足本地parser宽松的参数域；未知规则保守隔离，而非猜测签名。"""
    def number(node):
        if node.node_type == "number" and isinstance(node.value, (int, float)) and math.isfinite(node.value):
            return node.value
        if node.node_type == "operator" and node.value == "-" and len(node.children) == 1:
            child = number(node.children[0])
            return -child if child is not None else None
        return None
    def numeric(node, integer=False, positive=False, nonnegative=False):
        value = number(node)
        return value is not None and (not integer or value == int(value)) and (not positive or value > 0) and (not nonnegative or value >= 0)
    def group(node):
        if node.node_type == "category":
            return node.value in GROUPS
        if node.node_type == "function" and node.value == "densify":
            return len(node.children) == 1 and group(node.children[0]["value"])
        if node.node_type == "function" and node.value in {"bucket", "group_cartesian_product"}:
            return visit(node) is None
        return False
    def visit(node):
        if node is None:
            return "MISSING_AST"
        if node.node_type != "function":
            for child in node.children:
                issue = visit(child)
                if issue:
                    return issue
            return None
        name = node.value
        arguments = [child["value"] for child in node.children]
        keywords = {child["name"]: child["value"] for child in node.children if child.get("type") == "named"}
        positional = [child["value"] for child in node.children if child.get("type") == "positional"]
        if name.startswith("ts_"):
            if name == "ts_step":
                if len(arguments) != 1 or not numeric(arguments[0], integer=True, positive=True):
                    return "TS_STEP_POSITIVE_INTEGER"
            else:
                window_index = 2 if name in {"ts_corr", "ts_covariance"} else 1
                window = arguments[window_index] if len(arguments) > window_index else keywords.get("d")
                if window is None or not numeric(window, integer=True, positive=True):
                    return "TS_WINDOW_POSITIVE_INTEGER:" + name
                if name == "ts_returns" and len(arguments) != 2:
                    return "TS_RETURNS_MODE_UNVERIFIED"
                if name == "ts_quantile" and len(arguments) == 3:
                    if arguments[2].node_type != "string" or arguments[2].value not in {"gaussian", "uniform", "cauchy"}:
                        return "QUANTILE_DRIVER_UNVERIFIED"
                if name == "ts_decay_linear" and len(arguments) == 3 and arguments[2].node_type != "boolean":
                    return "TS_DECAY_DENSE_BOOLEAN"
                if name in {"ts_rank", "ts_scale"} and len(arguments) == 3 and not numeric(arguments[2]):
                    return "TS_CONSTANT_LITERAL_NUMBER"
        elif name.startswith("group_"):
            if name == "group_cartesian_product":
                if len(arguments) != 2 or not all(group(arg) for arg in arguments):
                    return "GROUP_PRODUCT_REQUIRES_TWO_GROUPS"
            elif name == "group_mean":
                if len(arguments) != 3 or not numeric(arguments[1], positive=True) or not group(arguments[2]):
                    return "GROUP_MEAN_POSITIVE_CONSTANT_WEIGHT_AND_GROUP"
            elif name == "group_backfill":
                if len(arguments) not in {3, 4} or not group(arguments[1]) or not numeric(arguments[2], integer=True, positive=True):
                    return "GROUP_BACKFILL_GROUP_AND_POSITIVE_WINDOW"
                if len(arguments) == 4 and not numeric(arguments[3], positive=True):
                    return "GROUP_BACKFILL_STD_POSITIVE"
            elif len(arguments) != 2 or not group(arguments[1]):
                return "GROUP_PARAMETER_REQUIRED:" + name
        elif name == "kth_element":
            if len(arguments) != 3 or not all(numeric(arg, integer=True, positive=True) for arg in arguments[1:]) or number(arguments[2]) > number(arguments[1]):
                return "KTH_POSITIVE_INTEGER_D_AND_K"
        elif name == "bucket":
            if len(positional) != 1 or set(keywords) != {"range"} or keywords["range"].node_type != "string":
                return "BUCKET_RANGE_REQUIRED"
            try:
                start, stop, step = map(float, keywords["range"].value.split(","))
            except (TypeError, ValueError):
                return "BUCKET_RANGE_THREE_NUMBERS"
            if not all(math.isfinite(v) for v in (start, stop, step)) or step <= 0 or stop <= start:
                return "BUCKET_RANGE_INVALID"
        elif name == "quantile":
            if len(arguments) > 1 and (arguments[1].node_type != "string" or arguments[1].value not in {"gaussian", "uniform", "cauchy"}):
                return "QUANTILE_DRIVER_UNVERIFIED"
            if len(arguments) > 2 and not numeric(arguments[2], positive=True):
                return "QUANTILE_SIGMA_POSITIVE"
        elif name == "normalize":
            if len(arguments) > 1 and arguments[1].node_type != "boolean":
                return "NORMALIZE_BOOLEAN"
            if len(arguments) > 2 and not numeric(arguments[2], nonnegative=True):
                return "NORMALIZE_LIMIT_NONNEGATIVE"
        elif name == "scale":
            if not all(numeric(arg, nonnegative=True) for arg in arguments[1:]):
                return "SCALE_LITERAL_NONNEGATIVE"
        elif name in {"rank", "hump", "tail"}:
            if not all(numeric(arg) for arg in arguments[1:]):
                return "OPTIONAL_LITERAL_NUMERIC_PARAMETER:" + name
            if name in {"rank", "hump"} and len(arguments) > 1 and not numeric(arguments[1], nonnegative=True):
                return "OPTIONAL_PARAMETER_NONNEGATIVE:" + name
        elif name in {"abs", "days_from_last_change", "densify", "inverse", "last_diff_value", "log", "max", "min", "pasteurize", "sign", "sqrt", "zscore"}:
            if name == "last_diff_value" and (len(arguments) != 2 or not numeric(arguments[1], integer=True, positive=True)):
                return "LAST_DIFF_POSITIVE_INTEGER_WINDOW"
        else:
            return "NO_EXPLICIT_PARAMETER_RULE:" + name
        for argument in arguments:
            issue = visit(argument)
            if issue:
                return issue
        return None
    return visit(ast)


def _statements(text):
    """只切完整顶层语句，不从被排除的复杂式中采摘嵌套子式。"""
    start, depth, quoted, escape = 0, 0, None, False
    for index, char in enumerate(text):
        if quoted:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quoted:
                quoted = None
        elif char in "\"'":
            quoted = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char in ";\n" and depth == 0:
            yield text[start:index], start
            start = index + 1
    yield text[start:], start


def extract_fragments(text):
    """全文件扫描围栏、inline、引用/普通行、JSON字符串；保留完整语句。"""
    fragments, occupied = [], []
    # 无围栏代码可能跨行赋值；宁可保守拒绝本帖定义过的变量，不能漏掉隐藏依赖。
    post_local_names = set(re.findall(r"(?:^|[;\n])\s*(?:>\s*)?([A-Za-z_]\w*)\s*=(?!=)", text))

    def emit(content, offset, form):
        local_names = post_local_names | set(re.findall(r"(?:^|[;\n])\s*([A-Za-z_]\w*)\s*=(?!=)", content))
        for statement, relative in _statements(content):
            if CALLS.search(statement):
                fragments.append({"raw_expression": statement.strip(), "offset": offset if form == "JSON_STRING" else offset + relative,
                                  "format": form, "local_names": sorted(local_names)})

    for match in re.finditer(r"```[^\n]*\n(.*?)```", text, re.S):
        occupied.append(match.span())
        emit(match[1], match.start(1), "FENCED")
    for match in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", text):
        if not any(a <= match.start() < b for a, b in occupied):
            emit(match[1], match.start(1), "INLINE")
            occupied.append(match.span())
    offset = 0
    for line in text.splitlines(keepends=True):
        if not any(a <= offset < b for a, b in occupied):
            emit(line, offset, "QUOTE_LINE" if line.lstrip().startswith(">") else "PLAIN_LINE")
        offset += len(line)

    # 解析JSON字符串值，含嵌套对象里的template。独立扫描，不依赖围栏语言标签。
    decoder = json.JSONDecoder()
    json_seen = set()
    def walk(value, anchor):
        if isinstance(value, str):
            if CALLS.search(value):
                encoded = json.dumps(value, ensure_ascii=False)
                found = text.find(encoded, anchor)
                emit(value, found if found >= 0 else anchor, "JSON_STRING")
        elif isinstance(value, dict):
            for child in value.values():
                walk(child, anchor)
        elif isinstance(value, list):
            for child in value:
                walk(child, anchor)
    for match in re.finditer(r"[\[{]", text):
        if match.start() in json_seen:
            continue
        try:
            value, length = decoder.raw_decode(text[match.start():])
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(value, (dict, list)):
            json_seen.update(range(match.start(), match.start() + length))
            walk(value, match.start())

    # 同一帖同一文本/行只记一次，格式差异放在全文件覆盖说明中。
    unique = {}
    for row in fragments:
        row["line"] = text[:row.pop("offset")].count("\n") + 1
        key = (row["line"], row["raw_expression"])
        unique.setdefault(key, row)
    return list(unique.values())


def strict_unary(fragment, verify, allowed):
    raw = fragment["raw_expression"]
    formula = re.sub(r"^\s*(?:>\s*|[-*]\s+|\d+[.)]\s+)+", "", raw).strip()
    # 可识别的展示标签不属于表达式，除此之外不截断尾部自然语言。
    formula = re.sub(r"^(?:模板|表达式|formula|template)\s*[:：]\s*", "", formula, flags=re.I)
    assign = re.match(r"^([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$", formula, re.S)
    if assign:
        formula = assign[2]
    calls = CALLS.findall(formula)
    if set(calls) & {"trade_when", "add", "multiply"}:
        return None, "FORBIDDEN_OPERATOR"
    if set(calls) - allowed:
        return None, "UNKNOWN_OR_UNAPPROVED_OR_NON_UNARY_OPERATOR:" + ",".join(sorted(set(calls) - allowed))
    if not calls:
        return None, "PURE_CONCEPT_OR_NO_OPERATOR"
    if any(term in formula for term in ("import ", "def ", "np.", "pd.", "requests.", "lambda", "\\", "```")):
        return None, "NON_FAST_EXPRESSION_OR_ESCAPED_SCRIPT"
    string_literals = re.findall(r'"([^"\n]*)"|\'([^\'\n]*)\'', formula)
    if any(CALLS.search(left or right) for left, right in string_literals):
        return None, "RAW_STRING_TEMPLATE_OR_HIDDEN_FIELDS"
    if formula.lstrip().startswith(("\"", "'")):
        return None, "STRING_VALUE_NOT_ALPHA"
    if re.search(r"[\u3400-\u9fff]", formula):
        return None, "UNBOUND_CONCEPT_OR_PROSE"
    placeholders = re.findall(r"\{([^{}]+)\}|<([A-Za-z_][\w ]*)/?\s*>", formula)
    if len({(left or right).strip().lower() for left, right in placeholders}) > 1:
        return None, "MULTIPLE_ABSTRACT_FIELDS"
    for left, right in placeholders:
        slot = (left or right).strip().lower()
        if slot not in FIELD_SLOTS:
            return None, "UNBOUND_ABSTRACT_SLOT:" + slot
    formula = re.sub(r"\{([^{}]+)\}|<([A-Za-z_][\w ]*)/?\s*>", "audit_field", formula)
    if "{" in formula or "}" in formula:
        return None, "UNBOUND_SLOT_OR_SYNTAX"
    stripped = re.sub(r'"[^"\n]*"|\'[^\'\n]*\'', "", formula)
    identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", stripped))
    keywords = set(re.findall(r"\b([A-Za-z_]\w*)\s*=(?!=)", stripped))
    fields = identifiers - set(calls) - GROUPS - keywords - {"true", "false", "True", "False", "NaN", "nan"}
    if len(fields) != 1:
        return None, "MULTIPLE_FIELDS_OR_UNBOUND_PARAMETERS:" + ",".join(sorted(fields))
    field = next(iter(fields))
    if field in fragment.get("local_names", []):
        return None, "DEPENDENT_LOCAL_VARIABLE"
    recognized = (field == "audit_field" or field.lower() in FIELD_SLOTS | KNOWN_BASE_FIELDS
                  or bool(re.match(r"(?:mdl|anl|fnd|oth|rsk|nws|snt|pv|opt|mcr)\d+_", field, re.I)))
    if not recognized:
        return None, "UNRESOLVED_IDENTIFIER:" + field
    formula = re.sub(r"\b" + re.escape(field) + r"\b", "audit_field", formula)
    function_count, total = _counts(formula)
    if total >= 6:
        return None, "TOTAL_OPERATOR_COUNT_GE_6"
    if formula.count("(") != formula.count(")"):
        return None, "SYNTAX_UNBALANCED"
    if re.match(r"^\s*-?\s*(?:bucket|densify|group_cartesian_product)\s*\(", formula):
        return None, "GROUP_OUTPUT_NOT_ALPHA_SIGNAL"
    result = verify(formula)
    if not result.get("valid"):
        return None, "LOCAL_VALIDATOR:" + " | ".join(str(x) for x in result.get("errors", []))
    parameter_issue = strict_parameter_check(result.get("ast"))
    if parameter_issue:
        return None, "LOCAL_PARAMETER_DOMAIN:" + parameter_issue
    # 明确恒等式零信号/自相关不是研究模板。
    if re.search(r"audit_field\s*[-/]\s*audit_field\b", formula) or re.search(r"ts_(?:corr|covariance)\(\s*audit_field\s*,\s*audit_field\s*,", formula):
        return None, "TRIVIAL_SELF_COMPARISON"
    formula = re.sub(r"\s+", " ", formula).strip().replace("audit_field", "{field}")
    skeleton = re.sub(r"\b(?:industry|subindustry|sector|market|country|exchange)\b", "GROUP", formula)
    skeleton = re.sub(r'"[^"\n]*"|\'[^\'\n]*\'', "PARAM_STRING", skeleton)
    skeleton = re.sub(r"(?<![\w.])\d+(?:\.\d+)?", "N", skeleton)
    skeleton = re.sub(r"\s+", "", skeleton).lstrip("-")
    digest = hashlib.sha256(skeleton.encode()).hexdigest()
    return {"template_id": "admin.catalog." + digest[:16], "formula": formula,
            "canonical_formula_skeleton": skeleton, "skeleton_sha256": digest,
            "function_count": function_count, "total_operator_count": total,
            "status": "LOCAL_PASS_UNVALIDATED", "template_class": "STATISTICAL_CONTROL",
            "stages": [2, 3], "field_type": "MATRIX", "category_allowlist": [], "semantic_keywords": [],
            "adaptation": "单一输入字段抽象为{field}；可移植的是统计变换骨架，不继承原经济假设、收益或输入数据域。",
            "local_validator_valid": True, "local_parameter_domain_valid": True}, None


def full_inventory(root, destination, output, catalog):
    root, destination, output, catalog = map(Path, (root, destination, output, catalog))
    verify, allowed, operator_library = _local_checks()
    destination.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    manifest, fragments, rejected, templates = [], [], [], {}
    validation_cache = {}
    formats, reasons = Counter(), Counter()
    paths = sorted(path for path in root.rglob("*.md") if root / "模板" not in path.parents)
    for source in paths:
        raw = source.read_bytes()
        text = raw.decode("utf-8-sig")
        relative = source.relative_to(root).as_posix()
        digest = hashlib.sha256(raw).hexdigest()
        post = re.search(r"_(\d+)\.md$", source.name)
        post_id = post[1] if post else None
        relation = "ADMIN_POSTED" if "自己发布的帖子" in source.parts else "ADMIN_REPLIED" if "参与回复的帖子" in source.parts else "LINKED_POST"
        author_match = re.search(r"\*\*作者\*\*:\s*([^\n]+)", text)
        author = author_match[1].strip() if author_match else None
        comments = [(text[:match.start()].count("\n") + 1, match[1]) for match in re.finditer(r"### 评论[^\n]*作者:\s*([^,，)]+)", text)]
        comment_heading = text.find("## 讨论与评论")
        comment_line = text[:comment_heading].count("\n") + 1 if comment_heading >= 0 else 10 ** 9
        rows = extract_fragments(text)
        copied = bool(rows)
        if copied:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw:
                raise ValueError(f"保留不同内容的现有文件: {target}")
            shutil.copy2(source, target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError("副本SHA256未通过: " + relative)
        manifest.append({"source": relative, "source_sha256": digest, "body_and_comments_scanned": True,
                         "research_copy": copied, "fragment_count": len(rows)})
        for fragment in rows:
            section = "COMMENT" if fragment["line"] >= comment_line else "BODY"
            row_author = author
            if section == "COMMENT":
                preceding = [value for line, value in comments if line <= fragment["line"]]
                row_author = preceding[-1] if preceding else None
            origin = {"source_post_id": post_id,
                      "source_url": f"https://support.worldquantbrain.com/hc/zh-cn/community/posts/{post_id}" if post_id else None,
                      "source_relation": relation, "source_section": section, "source_author": row_author,
                      "source_path": relative, "source_line": fragment["line"], "source_sha256": digest,
                      "blockline": fragment["line"], "extraction_format": fragment["format"],
                      "source_line_scope": "JSON_STRING_OR_CONTAINER_ANCHOR" if fragment["format"] == "JSON_STRING" else "STATEMENT_START",
                      "expression_sha256": hashlib.sha256(fragment["raw_expression"].encode()).hexdigest()}
            formats[fragment["format"]] += 1
            record = {**origin, "raw_expression": fragment["raw_expression"]}
            fragments.append(record)
            cache_key = (fragment["raw_expression"], tuple(fragment["local_names"]))
            if cache_key not in validation_cache:
                validation_cache[cache_key] = strict_unary(fragment, verify, allowed)
            valid, reason = validation_cache[cache_key]
            if not valid:
                reasons[reason.split(":", 1)[0]] += 1
                rejected.append({**record, "status": "EXCLUDED_LOCAL", "reason": reason})
                continue
            record["formula"] = valid["formula"]
            key = valid["skeleton_sha256"]
            priority = 0 if relation == "ADMIN_POSTED" and section == "BODY" else 1 if row_author in {"WL13229", "KH94146"} else 2
            if key not in templates:
                templates[key] = {**valid, **origin, "origins": [], "variant_values": [], "_priority": priority}
            item = templates[key]
            item["origins"].append(record)
            if valid["formula"] not in item["variant_values"]:
                item["variant_values"].append(valid["formula"])
            if priority < item["_priority"]:
                item.update({**valid, **origin, "_priority": priority})
    source_unchanged = all(hashlib.sha256((root / row["source"]).read_bytes()).hexdigest() == row["source_sha256"] for row in manifest)
    if not source_unchanged:
        raise ValueError("原帖哈希发生变化，不生成完成声明")
    verified = []
    for item in templates.values():
        item.pop("_priority")
        verified.append(item)
    verified.sort(key=lambda item: (item["source_relation"] != "ADMIN_POSTED", item["source_section"] != "BODY", item["template_id"]))
    summary = {"original_posts": len(manifest), "full_files_scanned": len(manifest), "research_copied_posts": sum(row["research_copy"] for row in manifest),
               "fragments": len(fragments), "extraction_formats": dict(formats), "local_pass_distinct_skeletons": len(verified),
               "local_pass_instances": sum(len(item["origins"]) for item in verified), "excluded_instances": len(rejected),
               "exclusion_reasons": dict(reasons), "all_original_hashes_unchanged": source_unchanged,
               "all_research_copy_hashes_match": True, "allowed_operator_names": sorted(allowed),
               "operator_library_sha256": hashlib.sha256(operator_library.read_bytes()).hexdigest(),
               "coverage_limit": "扫描所有文件；提取可识别围栏、inline、完整普通/引用行与可解码JSON字符串。图片、链接外部正文、无函数调用的概念、损坏JSON、Markdown表格多列与复杂语句变量依赖不保证自动恢复。"}
    for name, value in (("full_scan_manifest.json", manifest), ("full_scan_fragments.json", fragments),
                        ("quarantined/full_scan_excluded.json", rejected), ("full_scan_summary.json", summary)):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog.write_text(json.dumps({"schema_version": 1, "status": "LOCAL_PASS_UNVALIDATED", "coverage": summary,
                                  "templates": verified}, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def classify_block(code):
    calls = CALLS.findall(code)
    reasons = []
    if set(calls) & {"trade_when", "add", "multiply"}:
        reasons.append("项目明确禁用 trade_when/add/multiply，不能进入轮动")
    if len(calls) >= 6:
        reasons.append("算子调用数 >=6；需重构并重新验证，不继承原式表现")
    if code.count("(") != code.count(")") or code.count("{") != code.count("}"):
        reasons.append("括号/占位符不配对，属于语法问题而非性能失败")
    if re.search(r"nlp_sentiment|count_keywords|np\.|pd\.|def |import |requests\.", code):
        reasons.append("Python/NLP/网络脚本，非可直接运行的 Fast Expression 模板")
    families = set(re.findall(r"\b((?:mdl|anl|fnd|oth|rsk|nws|snt|pv|opt|mcr)\d+)_", code, re.I))
    if len(families) > 1:
        reasons.append("字段前缀显示跨数据集；当前单数据集要求不满足，须以实时元数据复核")
    return {"status": "EXCLUDED_STATIC" if reasons else "UNVALIDATED", "reasons": reasons or ["静态未发现上述禁用项；字段、权限、单位和收益仍待验证"], "operator_calls": len(calls)}


def inventory(root, destination, output):
    root, destination, output = map(Path, (root, destination, output))
    destination.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    posts = []
    sources = []
    blocks = []
    # 完成标题与复制阶段后才读正文。
    for source in sorted(root.rglob("*.md")):
        if root / "模板" in source.parents:
            continue
        relative = source.relative_to(root)
        selected = bool(TITLE_PATTERN.search(source.name))
        raw = source.read_bytes()
        row = {"source": relative.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
               "selected": selected, "relation": "ADMIN_AUTHORED" if "自己发布的帖子" in relative.parts else "ADMIN_REPLIED" if "参与回复的帖子" in relative.parts else "LINKED_POST"}
        if selected:
            copied = destination / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            if copied.exists() and copied.read_bytes() != raw:
                raise ValueError(f"目标已存在不同内容，保留原文件: {copied}")
            shutil.copy2(source, copied)
            assert hashlib.sha256(copied.read_bytes()).hexdigest() == row["sha256"]
            sources.append((copied, row))
        posts.append(row)
    (destination / "标题筛选与来源清单.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    analyses = []
    for copied, row in sources:
        text = copied.read_text(encoding="utf-8-sig")
        post_id = re.search(r"_(\d+)\.md$", copied.name)
        title = text.splitlines()[0].lstrip("# ") if text else copied.stem
        found = list(re.finditer(r"```[^\n]*\n(.*?)```", text, re.S))
        analysis = {**row, "title": title, "post_id": post_id[1] if post_id else None,
                    "body_read": True, "code_blocks": len(found),
                    "analysis": "无围栏代码；保留经济机制说明，需人工绑定字段后实现" if not found else "已逐块静态分类；包括评论，不把管理员回复等同管理员原创"}
        analyses.append(analysis)
        for index, match in enumerate(found, 1):
            code = match[1].strip()
            blocks.append({**row, "post_id": analysis["post_id"], "block_index": index,
                           "line": text[:match.start()].count("\n") + 1,
                           "section": "COMMENT" if "## 讨论与评论" in text[:match.start()] else "BODY",
                           "code": code, **classify_block(code)})
    # 镜像帖子保留来源记录，代码按内容去重，不能重复计入模板多样性。
    unique = {}
    for block in blocks:
        key = hashlib.sha256(re.sub(r"\s+", " ", block["code"]).encode()).hexdigest()
        if key not in unique:
            unique[key] = {**block, "block_sha256": key, "origins": []}
        unique[key]["origins"].append({k: block[k] for k in ("source", "post_id", "line", "relation", "section")})
    for name, value in (("posts_analyzed.json", analyses), ("unvalidated_blocks.json", [v for v in unique.values() if v["status"] == "UNVALIDATED"]), ("quarantined/forum_blocks.json", [v for v in unique.values() if v["status"] != "UNVALIDATED"])):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"original_posts": len(posts), "copied_posts": len(sources), "blocks": len(blocks), "unique_blocks": len(unique), "unvalidated": sum(v["status"] == "UNVALIDATED" for v in unique.values()), "quarantined": sum(v["status"] != "UNVALIDATED" for v in unique.values())}
    (output / "inventory_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # 证明处理没有改动任何原始帖子。
    assert all(hashlib.sha256((root / row["source"]).read_bytes()).hexdigest() == row["sha256"] for row in posts)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--full-scan", action="store_true", help="扫描全部原帖并执行严格单字段本地验证")
    parser.add_argument("--catalog", help="严格注册目录JSON输出，仅供本地合规通过模板")
    args = parser.parse_args()
    if args.full_scan:
        if not args.catalog:
            parser.error("--full-scan requires --catalog")
        print(json.dumps(full_inventory(args.root, args.destination, args.output, args.catalog), ensure_ascii=False))
    else:
        print(json.dumps(inventory(args.root, args.destination, args.output), ensure_ascii=False))
