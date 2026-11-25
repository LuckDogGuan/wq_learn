"""按表达式作用分类224个模板，保留来源；不把未验证模板冒称有效。"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "factor" / "templates"
CATEGORIES = (
    ("group_relative", "组内比较与中性化", lambda ops: any(op.startswith("group_") for op in ops)),
    ("event_recency", "事件频率与距今时间", lambda ops: bool(ops & {"days_from_last_change", "ts_count_nans", "ts_arg_max", "ts_arg_min"})),
    ("time_series_risk", "波动与风险调整", lambda ops: bool(ops & {"ts_std_dev", "ts_ir", "ts_zscore", "ts_skewness", "ts_kurtosis"})),
    ("time_series_position", "时序排名与区间位置", lambda ops: bool(ops & {"ts_rank", "ts_quantile", "ts_scale", "ts_max", "ts_min", "ts_percentage"})),
    ("trend_change", "趋势变化与反转", lambda ops: bool(ops & {"ts_delta", "ts_av_diff", "ts_returns"})),
    ("smoothing", "时序平滑与加权", lambda ops: bool(ops & {"ts_mean", "ts_sum", "ts_decay_linear", "ts_decay_exp_window", "ts_product"})),
    ("preprocessing", "缺失值与异常值处理", lambda ops: bool(ops & {"ts_backfill", "winsorize", "kth_element", "hump"})),
    ("cross_sectional", "截面排序与非线性变换", lambda ops: True),
)


def classify(formula):
    ops = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", formula))
    return next((key, label) for key, label, matches in CATEGORIES if matches(ops))


def main():
    catalog_path = TEMPLATES / "admin_verified_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for item in catalog["templates"]:
        key, label = classify(item["formula"])
        item.update(family=key, usage_category=label, classification_status="UNVALIDATED")
        grouped[(key, label)].append(item)
    assert len(catalog["templates"]) == len({item["template_id"] for item in catalog["templates"]}) == 224
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target = TEMPLATES / "forum_catalog" / "分类模板"
    for (key, label), items in grouped.items():
        folder = target / "待验证" / label
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "templates.json").write_text(json.dumps({"category": key, "category_name": label,
            "count": len(items), "status": "UNVALIDATED", "templates": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [f"# {label}：{len(items)}个模板", "", "全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。", "", "| 模板编号 | 表达式 | 来源帖子 |", "|---|---|---|"]
        lines.extend(f"| {item['template_id']} | `{item['formula']}` | {item.get('source_post_id', '')} |" for item in items)
        (folder / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    excluded = target / "差表现与禁用"
    excluded.mkdir(parents=True, exist_ok=True)
    history = json.loads((TEMPLATES / "forum_catalog" / "quarantined" / "historical_disabled_scopes_20261012.json").read_text(encoding="utf-8"))
    (excluded / "历史范围证据.json").write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (excluded / "README.md").write_text("# 差表现与禁用\n\n历史禁用56个范围保留在历史范围证据.json；禁用只适用于记录的模板版本、参数、区域、字段类别和阶段，不能扩大为整个模板永久无效。实时账本中的LOW_PRIORITY、DISABLED_SCOPE、MANUAL_DISABLED及明确过拟合FAIL均不进入爬山轮动。PENDING不算差表现。\n", encoding="utf-8")
    overfit = target / "过拟合禁用"
    overfit.mkdir(parents=True, exist_ok=True)
    (overfit / "README.md").write_text("# 过拟合禁用\n\n目前224个新骨架没有可核实的过拟合失败实证，因此本类不虚构名单。平台检查或真实记录明确overfit/robust FAIL后，在对应运行范围禁用，不再轮动。检查未完成归入待验证。\n", encoding="utf-8")
    counts = {label: len(items) for (_, label), items in grouped.items()}
    (target / "分类索引.json").write_text(json.dumps({"total_templates": 224, "categories": counts,
        "rotation": "按模板编号及实际使用次数轮动；管理员优先；差表现及过拟合失败退出范围轮动", "initial_state": "UNVALIDATED"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "README.md").write_text("# 224个模板分类\n\n按用途分入待验证子目录，每个模板恰好出现一次；分类清单中的表达式就是模板。好模板与差模板用运行证据更新状态；待验证不能当作好模板。\n\n" + "\n".join(f"- {label}：{count}个" for label, count in counts.items()) + "\n\n程序从根admin_verified_catalog.json加载相同224个模板，family字段对应这里的分类；不是读取分类副本重复注册。\n", encoding="utf-8")
    print(json.dumps({"total": sum(counts.values()), "categories": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
