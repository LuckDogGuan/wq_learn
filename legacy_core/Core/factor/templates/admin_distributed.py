"""管理员分发模板的保守实现；出处见 ADMIN_SOURCES，收益均待实测。

二元字段必须来自同数据集且语义、方向匹配。字段表达式由调用方做
VECTOR->MATRIX 转换；group 是平台分组维度，不引入外部经济字段。
"""

import re


ADMIN_SOURCES = {
    "profit_to_size": "25066216209687",
    "net_sentiment": "25066287753367",
    "term_structure": "32092606398999",
    "dupont_difference": "32198029389207",
    "peg_relative_value": "32495294399895",
    "group_residual": "25329078901911",
    "group_beta": "25526497127959",
}


def operator_count(expression):
    """保守总计函数调用及算术/比较/逻辑符号，不能只数嵌套函数。"""
    return len(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\(", expression)) + len(re.findall(r">=|<=|==|!=|&&|\|\||[+\-*/<>]", expression))


def profit_to_size(profit, size, d=66):
    # 非正规模没有可解释的盈利/规模比率，保留为 NaN。
    return f"ts_rank(if_else({size} > 0, {profit} / {size}, NaN), {d})"


def net_sentiment(positive, negative, d=22):
    return f"ts_rank({positive} - {negative}, {d})"


def term_structure(near, far, group="industry"):
    return f"group_zscore(subtract(group_zscore({near}, {group}), group_zscore({far}, {group})), {group})"


def dupont_difference(roe, profit_margin, d=66, group="industry"):
    return f"group_zscore(subtract(ts_zscore({roe}, {d}), ts_zscore({profit_margin}, {d})), {group})"


def peg_relative_value(pe, growth, group="industry"):
    # PEG 对非正盈利/增长不适用；避免零分母。growth 必须统一百分比口径。
    return f"-group_zscore(if_else({growth} > 0, if_else({pe} > 0, {pe} / {growth} - 1, NaN), NaN), {group})"


def group_residual(field, d=252, backfill=63, group="sector"):
    # 单数据集改编：原帖 cap 加权改为等权，保留组内残差机制，非原式性能继承。
    return (f"admin_target = winsorize(ts_backfill({field}, {backfill}), std=4); "
            f"admin_peer = group_mean(admin_target, 1, {group}); "
            f"ts_regression(admin_target, admin_peer, {d}, rettype=0)")


def group_beta(target, peer, d=252, group="sector"):
    # 单数据集低复杂度改编：等权组均值；预处理由数据质量证据决定。
    return f"ts_regression({target}, group_mean({peer}, 1, {group}), {d}, rettype=2)"


def semantic_pair(fields, condition):
    """保守绑定具名经济量，不把随机同数据集字段对当模板匹配。"""
    if len(fields) != 2:
        return None
    datasets = {f.get("dataset_id") for f in fields}
    if len(datasets) != 1 or next(iter(datasets)) in {None, "", "UNKNOWN"}:
        return None
    if any(str(f.get("type", "")).upper() != "MATRIX" for f in fields):
        return None

    def text(field):
        return " ".join(str(field.get(k) or "").lower() for k in ("id", "name", "description"))

    patterns = {
        "admin_profit_size": (r"profit|net.income|earnings", r"assets|equity|capitalization|market.cap|sales|revenue"),
        "admin_sentiment_pair": (r"positive|bullish|buyrec|uptarget", r"negative|bearish|sellrec|downtarget"),
        "admin_dupont_pair": (r"\broe\b|_roe|return.on.equity", r"profit.margin|net.margin"),
        "admin_peg_pair": (r"price.to.earnings|p/e|\bpe\b|_pe_|pe.ratio", r"earnings.growth|eps.growth|profit.growth"),
    }
    for first, second in (fields, list(reversed(fields))):
        a, b = text(first), text(second)
        if condition == "admin_term_pair":
            # 同指标、同频率、不同期限；季度与年度 EPS 不做随机相减。
            left = re.fullmatch(r"(.+?)(fy|fp)(\d+)(.*)", first["id"].lower())
            right = re.fullmatch(r"(.+?)(fy|fp)(\d+)(.*)", second["id"].lower())
            if left and right and (left[1], left[2], left[4]) == (right[1], right[2], right[4]) and int(left[3]) < int(right[3]):
                return first, second
        elif condition in patterns:
            p, q = patterns[condition]
            if re.search(p, a) and re.search(q, b):
                return first, second
        elif condition == "admin_beta_pair":
            # 用户/字段元数据明确标注关系后才启用 Beta；宽泛关键词不够。
            if first.get("relation_group") and first.get("relation_group") == second.get("relation_group"):
                return first, second
    return None
