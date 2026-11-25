import datetime
import io
import json
import logging
import math
import re
import sys
import time
import urllib.parse
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

CORE_PARENT = Path(__file__).resolve().parents[2]
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.api import (
    COMPLETE, fetch_alpha_window,
    get_datafields, login, set_alpha_properties, get_user_diversity,
    get_pyramid_tower_status, get_pyramid_lit_tower_counts, get_pyramid_alphas,
)
from Core.sim.sc_engine import calc_ppac, refresh_ppac_data, get_alpha_pnls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
BEIJING_TZ = ZoneInfo("Asia/Shanghai")

CONFIG_BATCH_SIZE = 2
CONFIG_REST_DURATION = 2
CONFIG_DAYS_AGO = 30
CACHE_DIR = Path(__file__).resolve().parent / "output" / "raw_alphas_cache"

FILTER_SHARPE = 1.4
FILTER_FITNESS = 1
FILTER_MARGIN = 5  # 过滤门槛：Margin > 8bp（8 表示 0.0008；若为 None/0 则不筛选）


def get_margin_ratio(margin_val):
    """解析 margin 过滤阈值。支持 bp 基点（如 5 -> 0.0005）或直接小数比率（如 0.0005）。"""
    if margin_val is None:
        return 0.0
    try:
        val = float(margin_val)
    except (ValueError, TypeError):
        return 0.0
    if val <= 0:
        return 0.0
    return val / 10000.0 if val >= 0.05 else val


def metric_meets_threshold(value, threshold, *, strict=False):
    """判断可配置指标门槛；缺失/非法指标按 0 处理，None/0 门槛表示不筛选。"""
    try:
        threshold = float(threshold)
    except (ValueError, TypeError):
        return True
    if threshold <= 0:
        return True
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0.0
    return value > threshold if strict else value >= threshold
TARGET_REGION = ["GLB"]  # 如果为空列表 []，则表示不筛选，处理所有 Region
#  "KOR", "JPN", "CHN", "AMR", "TWN", "HKG"
TARGET_DELAY = 1

CONFIG_PNL_DELAY = 30  # 获取目标 Alpha 的 PnL 数据后，计算 PPAC 之前的强制延时（秒）
TARGET_UNIVERSE = ["TOPDIV3000"]
TARGET_NEUTRALIZATION = None

PPC_LIMIT = 0.4
PPC_HIGH_TAG = "PPC_IS_HIGHT"
PPC_EXCLUDED_WARNING_PATTERNS = []
EXCLUDE_REGULAR_RA = False
# 默认只处理塔未点亮（lit_towers == 0）的区域；True = 同时处理已点亮区域（全量模式）
CONFIG_PROCESS_LIT_TOWERS = True

CATEGORY_HELPER_FIELDS = {
    "close", "open", "high", "low", "volume", "returns", "split", "ticker",
    "vwap", "sharesout", "market_cap", "adv20", "adv60",
}
CATEGORY_NON_FIELD_TOKENS = {
    "abs", "add", "and", "bucket", "country", "densify", "divide", "equal",
    "greater", "group", "group_backfill", "group_count", "group_max",
    "group_mean", "group_min", "group_neutralize", "group_rank", "group_scale",
    "group_std_dev", "group_sum", "group_zscore", "if_else", "industry",
    "inverse", "is_nan", "less", "market", "max", "min", "multiply",
    "nan_mask", "neutralize", "not", "not_equal", "or", "pasteurize", "power",
    "quantile", "rank", "reverse", "scale", "sector", "sign", "signed_power",
    "sqrt", "subtract", "subindustry", "tail", "target_tvr", "ts_arg_max",
    "ts_arg_min", "ts_av_diff", "ts_backfill", "ts_count_nans", "ts_corr",
    "ts_covariance", "ts_decay_linear", "ts_delta", "ts_kurtosis", "ts_max_diff",
    "ts_mean", "ts_product", "ts_quantile", "ts_rank", "ts_returns", "ts_scale",
    "ts_std_dev", "ts_step", "ts_sum", "ts_target_tvr_decay", "ts_target_tvr_hump",
    "ts_zscore", "winsorize", "zscore", "lambda_min", "lambda_max", "std", "nth",
}
_FIELD_METADATA_CACHE = {}


def alpha_tags(alpha):
    """返回 Alpha 的字符串标签，兼容缺失或单字符串响应。"""
    tags = alpha.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [tag for tag in tags if isinstance(tag, str) and tag]


def has_alpha_tag(alpha, tag):
    return tag in alpha_tags(alpha)


def high_ppc_tags(alpha):
    """移除 PPA、保留其他标签，并追加高 PPC 终止标签。"""
    return list(dict.fromkeys([tag for tag in alpha_tags(alpha) if tag != "PPA"] + [PPC_HIGH_TAG]))


def add_alpha_tag(alpha, tag):
    return list(dict.fromkeys(alpha_tags(alpha) + [tag]))


def extract_expression_fields(expression):
    """提取表达式中的真实字段，跳过算子和命名参数。"""
    expression = str(expression or "")
    fields = []
    for match in re.finditer(r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)", expression):
        field_id = match.group(1)
        if re.match(r"\s*(?:\(|=)", expression[match.end():]):
            continue
        if field_id.lower() in CATEGORY_NON_FIELD_TOKENS | CATEGORY_HELPER_FIELDS:
            continue
        if field_id not in fields and not field_id.isupper():
            fields.append(field_id)
    return fields


def get_expression_categories(client, alpha):
    """查询表达式字段的 Category；失败时返回已找到的部分结果。"""
    settings = alpha.get("settings") or {}
    categories = []
    expression = (alpha.get("regular") or {}).get("code") or ""
    for field_id in extract_expression_fields(expression):
        cache_key = json.dumps({
            "field": field_id,
            "region": settings.get("region"),
            "universe": settings.get("universe"),
            "delay": settings.get("delay"),
        }, sort_keys=True)
        metadata = _FIELD_METADATA_CACHE.get(cache_key)
        if metadata is None:
            metadata_rows = get_datafields(
                client,
                instrument_type=settings.get("instrumentType", "EQUITY"),
                region=settings.get("region", "GLB"),
                universe=settings.get("universe", "TOPDIV3000"),
                delay=settings.get("delay", 1),
                search=field_id,
            )
            if metadata_rows.empty:
                logging.warning("Alpha %s 字段 %s 的 Category 查询失败或无匹配。", alpha.get("id"), field_id)
                continue
            if "id" not in metadata_rows:
                logging.warning("Alpha %s 字段 %s 的 Category 响应缺少 id。", alpha.get("id"), field_id)
                continue
            matches = metadata_rows.loc[metadata_rows["id"] == field_id]
            if matches.empty:
                logging.warning("Alpha %s 字段 %s 未得到精确匹配。", alpha.get("id"), field_id)
                continue
            metadata = matches.iloc[0].to_dict()
            _FIELD_METADATA_CACHE[cache_key] = metadata
        category = metadata.get("category") or {}
        category_name = category.get("name") or category.get("id") if isinstance(category, dict) else None
        if category_name and category_name not in categories:
            categories.append(category_name)
    return categories


def extract_alpha_pyramid_categories(alpha):
    """从 Alpha 的 MATCHES_PYRAMID 检查中提取所属金字塔分类 (region, delay, category_upper)。"""
    cats = []
    checks = (alpha.get("is") or {}).get("checks") or []
    for c in checks:
        if isinstance(c, dict) and c.get("name") == "MATCHES_PYRAMID":
            for p in (c.get("pyramids") or []):
                name = str(p.get("name") or "").strip()
                m = re.fullmatch(r"([^/]+)/D(\d+)/(.+)", name, re.IGNORECASE)
                if m:
                    cats.append((m.group(1).upper(), int(m.group(2)), m.group(3).upper()))
    if not cats:
        reg = str((alpha.get("settings") or {}).get("region") or "").strip().upper()
        d = int((alpha.get("settings") or {}).get("delay") or TARGET_DELAY)
        for t in alpha_tags(alpha):
            cats.append((reg, d, t.upper()))
    return cats


def get_lit_tower_counts(client):
    """调用 Core 统一接口查询金字塔点亮与未点亮状态。
    同时输出 Delay 0 概况和 Delay 1 的详细明细，并返回类别计数映射表用于两级优先级排序。
    """
    try:
        # 1. 输出 Delay 0 概况说明（帮助用户确认 Day 0 状态）
        d0_status = get_pyramid_tower_status(client, delay=0, min_count=3)
        d0_lit = sum(s["lit_count"] for s in d0_status.values())
        d0_almost = sum(len(s["almost_lit_cats"]) for s in d0_status.values())
        logging.info("金字塔概况: [Delay 0] 已点亮总塔数=%d, 差1-2个临界类别数=%d (全部区域当前均为 0)", d0_lit, d0_almost)

        # 2. 输出当前任务目标 Delay (通常是 Delay 1) 的区域明细
        status_map = get_pyramid_tower_status(client, delay=TARGET_DELAY, min_count=3)
        lit_counts = {}
        logging.info("========== 金字塔点亮与未点亮塔状态明细 (Delay %s) ==========", TARGET_DELAY)
        for reg, info in sorted(status_map.items()):
            lit_counts[reg] = info["lit_count"]
            lit_desc = ", ".join(info["lit_cats"]) if info["lit_cats"] else "无"
            almost_desc = f" | 临近点亮(差1-2个): [{', '.join(info['almost_lit_cats'])}]" if info["almost_lit_cats"] else ""
            logging.info(
                "[%s] 已点亮=%d [%s] | 未点亮=%d%s",
                reg, info["lit_count"], lit_desc, info["unlit_count"], almost_desc
            )
        logging.info("================================================================")

        # 3. 提取所有类别的实际 alphaCount，用于精细化优先级排序
        pyramid_data = get_pyramid_alphas(client)
        cat_counts = {}
        for p in (pyramid_data.get("pyramids") or []):
            if not isinstance(p, dict):
                continue
            reg = str(p.get("region") or "").strip().upper()
            d = p.get("delay")
            cnt = int(p.get("alphaCount", 0))
            cid = str((p.get("category") or {}).get("id") or "").strip().upper()
            cname = str((p.get("category") or {}).get("name") or "").strip().upper()
            if reg and d is not None:
                if cid:
                    cat_counts[(reg, d, cid)] = cnt
                if cname:
                    cat_counts[(reg, d, cname)] = cnt

        return lit_counts, cat_counts
    except Exception as exc:
        logging.error("拉取金字塔塔数失败，将默认全量区域塔数为 0: %s", exc)
        return {}, {}


def normalize_warning_patterns(patterns):
    if patterns is None:
        return []
    values = patterns if isinstance(patterns, (list, tuple, set)) else [patterns]
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def find_excluded_warning(checks, patterns):
    normalized_patterns = [re.sub(r"[\W_]+", " ", pattern).casefold() for pattern in patterns]
    for check in checks:
        if check.get("result") != "WARNING":
            continue
        check_text = json.dumps(check, ensure_ascii=False, default=str)
        normalized_check_text = re.sub(r"[\W_]+", " ", check_text).casefold()
        for pattern, normalized_pattern in zip(patterns, normalized_patterns):
            if normalized_pattern in normalized_check_text:
                return pattern, check_text
    return None, None


def configure_output_logging(output_dir, today_str):
    """将本次运行日志写入与 Excel 同目录的当日日志文件。"""
    log_path = (output_dir / f"filtered_PPAs_{today_str}.log").resolve()
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if not getattr(handler, "ppa_output_log", False):
            continue
        if Path(handler.baseFilename) == log_path:
            return log_path
        root_logger.removeHandler(handler)
        handler.close()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.ppa_output_log = True
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(handler)
    return log_path


NEUTRALIZATION_MAP = {
    "ram": "REVERSION_AND_MOMENTUM",
    "crowding factors": "CROWDING",
    "slow factors": "SLOW",
    "fast factors": "FAST",
    "slow + fast factors": "SLOW_FAST",
    "reversion_and_momentum": "REVERSION_AND_MOMENTUM",
    "crowding": "CROWDING",
    "slow": "SLOW",
    "fast": "FAST",
    "slow_fast": "SLOW_FAST",
}


def normalize_neutralization_targets(target):
    """None/[] 表示不筛选；只有大写 NONE 表示 API 枚举 NONE。"""
    if target is None:
        return []
    raw_targets = target if isinstance(target, (list, tuple, set)) else [target]
    normalized = []
    for value in raw_targets:
        if value is None:
            continue
        value = str(value).strip()
        if not value:
            continue
        if value.casefold() == "none" and value != "NONE":
            raise ValueError('中性化不筛选请使用 Python None；精确匹配请使用大写字符串 "NONE"。')
        value = NEUTRALIZATION_MAP.get(value.casefold(), value)
        if value.casefold() not in {item.casefold() for item in normalized}:
            normalized.append(value)
    return normalized


def normalize_neutralization_value(value):
    if value is None:
        return None
    values = normalize_neutralization_targets(value)
    return values[0] if len(values) == 1 else None


def build_query_params():
    """构建平台候选查询参数；多选条件留给内存过滤。"""
    params = [
        "limit=100",
        "status=UNSUBMITTED",
        "order=-dateCreated",
    ]
    if float(FILTER_SHARPE or 0) > 0:
        params.append(f"is.sharpe>={FILTER_SHARPE}")
    if float(FILTER_FITNESS or 0) > 0:
        params.append(f"is.fitness>={FILTER_FITNESS}")
    margin_ratio = get_margin_ratio(FILTER_MARGIN)
    if margin_ratio > 0:
        params.append(f"is.margin>={margin_ratio}")
    neutralization_targets = normalize_neutralization_targets(TARGET_NEUTRALIZATION)
    if TARGET_DELAY is None or str(TARGET_DELAY).lower() == "none":
        raise ValueError("严重错误：TARGET_DELAY 一定不能等于 None！必须明确指定。")

    def add_single(field_name, value, allow_none_enum=False):
        if value is not None and (allow_none_enum or str(value).lower() != "none"):
            params.append(f"{field_name}={urllib.parse.quote(str(value))}")

    def add_single_from_list(field_name, value, allow_none_enum=False):
        values = [] if value is None else value if isinstance(value, list) else [value]
        values = [
            str(item) for item in values
            if item and (allow_none_enum or str(item).lower() != "none")
        ]
        if len(values) == 1:
            add_single(field_name, values[0], allow_none_enum=allow_none_enum)

    add_single_from_list("settings.region", TARGET_REGION)
    add_single("settings.delay", TARGET_DELAY)
    add_single_from_list("settings.universe", TARGET_UNIVERSE)
    add_single_from_list("settings.neutralization", neutralization_targets, allow_none_enum=True)
    return "&".join(params)


def beijing_date_window(now=None):
    """返回最近 CONFIG_DAYS_AGO 个北京时间自然日的半开区间。"""
    current = now or datetime.datetime.now(BEIJING_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING_TZ)
    current = current.astimezone(BEIJING_TZ)
    end = (current + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return end - datetime.timedelta(days=CONFIG_DAYS_AGO), end


def generate_daily_windows(now=None, stop_date_str=None):
    """按天倒序生成时间窗口，用于分天拉取。如果遇到 stop_date_str 则停止向更早的天数拉取。"""
    _, window_end = beijing_date_window(now)
    end_date = window_end.date()
    
    stop_date_dt = None
    if stop_date_str:
        try:
            stop_date_dt = datetime.datetime.fromisoformat(
                stop_date_str.replace('Z', '+00:00')
            ).astimezone(BEIJING_TZ)
        except Exception:
            pass
            
    # 倒序生成每天的区间：昨天0点-今天0点, 前天0点-昨天0点...
    for i in range(CONFIG_DAYS_AGO):
        day_end = end_date - datetime.timedelta(days=i)
        day_start = day_end - datetime.timedelta(days=1)
        
        start_dt = datetime.datetime.combine(
            day_start, datetime.time.min, tzinfo=BEIJING_TZ
        )
        end_dt = datetime.datetime.combine(
            day_end, datetime.time.min, tzinfo=BEIJING_TZ
        )
        
        if stop_date_dt and end_dt <= stop_date_dt:
            logging.info("遇到已缓存的时间截点 %s，停止向更早的天数拉取。", stop_date_dt)
            break
            
        yield start_dt, end_dt


def fetch_recent_alphas(client, now=None):
    """Read Beijing windows through versioned, query-aware Core checkpoints.

    Legacy daily JSON files are preserved untouched; without a completeness
    signature they cannot prove a whole day was fetched.
    """
    base_query = build_query_params()
    current = now or datetime.datetime.now(BEIJING_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING_TZ)
    today = current.astimezone(BEIJING_TZ).date()
    observed = {}
    for start, end in generate_daily_windows(now):
        result = fetch_alpha_window(
            client, start, end, query=base_query, page_size=100,
            dense_window_threshold=500,
            checkpoint_path=CACHE_DIR / "beijing_v2" / f"{start.date().isoformat()}.json",
            checkpoint_namespace="ppa_alpha_fetch",
            refresh_completed=start.date() == today,
        )
        if result.status != COMPLETE:
            raise RuntimeError(f"Alpha 结果未完整观测：{result.status}，{result.failures}")
        for alpha in result.records:
            observed[alpha["id"]] = alpha
    return list(observed.values())

def property_update_succeeded(response):
    return response is not None and response.status_code in (200, 201, 204)


def update_alpha_properties(client, alpha_id, **properties):
    response = set_alpha_properties(client, alpha_id, **properties)
    if property_update_succeeded(response):
        return True
    status = response.status_code if response is not None else "NO_RESPONSE"
    logging.error("Alpha %s 属性写回失败，状态=%s。", alpha_id, status)
    return False


def remove_ppa_tag_if_present(client, alpha, reason):
    if not has_alpha_tag(alpha, "PPA"):
        return False
    alpha_id = alpha.get("id")
    logging.info("移除 Alpha %s 的 PPA 标签：%s。", alpha_id, reason)
    tags = [tag for tag in alpha_tags(alpha) if tag != "PPA"]
    return update_alpha_properties(client, alpha_id, tags=tags)


def filter_candidates(client, alphas):
    """应用无需 PPAC 的前置过滤，返回候选及漏斗计数。"""
    valid_neut = normalize_neutralization_targets(TARGET_NEUTRALIZATION)
    valid_univ = (
        [str(item) for item in TARGET_UNIVERSE if item and str(item).lower() != "none"]
        if isinstance(TARGET_UNIVERSE, list)
        else []
    )
    valid_region = (
        [str(item) for item in TARGET_REGION if item and str(item).lower() != "none"]
        if isinstance(TARGET_REGION, list)
        else [TARGET_REGION] if TARGET_REGION and str(TARGET_REGION).lower() != "none" else []
    )
    warning_patterns = normalize_warning_patterns(PPC_EXCLUDED_WARNING_PATTERNS)
    need_univ_filter = len(valid_univ) > 0
    need_neut_filter = len(valid_neut) > 0
    need_region_filter = len(valid_region) > 0
    margin_threshold = get_margin_ratio(FILTER_MARGIN)
    counters = dict.fromkeys(
        ("universe", "region", "neutralization", "sharpe", "fitness", "margin", "high_tag", "warning", "ra_dropped", "ra_retained", "fail", "ppa_removed"),
        0,
    )
    candidates = []

    for alpha in alphas:
        alpha_id = alpha.get("id")
        checks = alpha.get("is", {}).get("checks", [])
        settings = alpha.get("settings", {})
        if has_alpha_tag(alpha, PPC_HIGH_TAG):
            counters["high_tag"] += 1
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, f"已有 {PPC_HIGH_TAG} 标签")
            continue
        if need_univ_filter and settings.get("universe") not in valid_univ:
            counters["universe"] += 1
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, "Universe 不匹配")
            continue
        if need_region_filter and settings.get("region") not in valid_region:
            counters["region"] += 1
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, "Region 不匹配")
            continue
        candidate_neut = normalize_neutralization_value(settings.get("neutralization"))
        if need_neut_filter and candidate_neut not in valid_neut:
            counters["neutralization"] += 1
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, "Neutralization 不匹配")
            continue

        metrics = alpha.get("is") or {}
        if not metric_meets_threshold(metrics.get("sharpe"), FILTER_SHARPE):
            counters["sharpe"] += 1
            continue
        if not metric_meets_threshold(metrics.get("fitness"), FILTER_FITNESS):
            counters["fitness"] += 1
            continue
        if margin_threshold > 0 and not metric_meets_threshold(
            metrics.get("margin"), margin_threshold, strict=True
        ):
            counters["margin"] += 1
            continue

        is_power_pool = any(check.get("name") == "POWER_POOL_CORRELATION" for check in checks)
        if not is_power_pool:
            if EXCLUDE_REGULAR_RA:
                counters["ra_dropped"] += 1
                counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, "普通 RA 已启用排除")
                continue
            counters["ra_retained"] += 1

        excluded_warning, detail = find_excluded_warning(checks, warning_patterns)
        if excluded_warning:
            counters["warning"] += 1
            logging.info("跳过 Alpha %s：WARNING 命中 %r。详情: %s", alpha_id, excluded_warning, detail)
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, f"WARNING 命中 {excluded_warning!r}")
            continue
        if any(
            check.get("name") != "POWER_POOL_CORRELATION" and check.get("result") == "FAIL"
            for check in checks
        ):
            counters["fail"] += 1
            counters["ppa_removed"] += remove_ppa_tag_if_present(client, alpha, "存在其他 FAIL 检查")
            continue
        candidates.append(alpha)
    return candidates, counters


def apply_ppac_result(client, alpha, ppac_value, lit_towers=None):
    """根据有效本地 PPAC 写回标签；不可判定时不修改任何属性。
       如果 alpha 所在 region 的点亮塔数为 0，且该 alpha 通过了测试，则追加 PPA_Submit 标签。
    """
    alpha_id = alpha.get("id")
    lit_towers = lit_towers or {}
    if isinstance(ppac_value, bool) or not isinstance(ppac_value, (int, float)) or not math.isfinite(float(ppac_value)):
        logging.warning("Alpha %s 本地 PPAC 不可判定，保持属性不变。", alpha_id)
        return "PENDING"
        
    value = float(ppac_value)
    name = f"PPC {value:.4f}"
    categories = get_expression_categories(client, alpha) if value < PPC_LIMIT else []
    
    if value > PPC_LIMIT:
        tags = high_ppc_tags(alpha)
    else:
        tags = list(dict.fromkeys([*add_alpha_tag(alpha, "PPA"), *categories]))
        
        region = str((alpha.get("settings") or {}).get("region") or "").strip().upper()
        # 塔数 < 3 = 未点亮，通过 PPAC 的候选追加 PPA_Submit 标签
        tower_count = lit_towers.get(region)
        if region and isinstance(tower_count, int) and not isinstance(tower_count, bool) and 0 <= tower_count < 3:
            if "PPA_Submit" not in tags:
                tags.append("PPA_Submit")
                
    if not update_alpha_properties(client, alpha_id, tags=tags, name=name):
        return "WRITE_FAILED"
    if categories:
        logging.info("Alpha %s PPAC=%.4f，已写入字段 Category 标签：%s (Tags: %s)", alpha_id, value, ", ".join(categories), tags)
    return "PPC_HIGH" if value > PPC_LIMIT else "PPA_PASS"


def build_output_row(alpha, ppac_value):
    alpha_id = alpha.get("id")
    is_stats = alpha.get("is", {})
    settings = alpha.get("settings", {})
    return {
        "alpha_id": f'=HYPERLINK("https://platform.worldquantbrain.com/alpha/{alpha_id}", "{alpha_id}")',
        "alpha_id_raw": alpha_id,
        "dateCreated": alpha.get("dateCreated", "")[:10],
        "region": settings.get("region", "UNKNOWN"),
        "universe": settings.get("universe", "UNKNOWN"),
        "delay": settings.get("delay", "UNKNOWN"),
        "neutralization": settings.get("neutralization", "UNKNOWN"),
        "sharpe": is_stats.get("sharpe"),
        "fitness": is_stats.get("fitness"),
        "turnover": is_stats.get("turnover"),
        "margin": is_stats.get("margin"),
        "ppc_value": float(ppac_value),
    }


def fetch_and_filter_ppa_alphas():
    """最近一个月候选 → 本地 PPAC → 平台标签写回。"""
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    today_str = datetime.datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    output_path = output_dir / f"filtered_PPAs_{today_str}.xlsx"
    log_path = configure_output_logging(output_dir, today_str)
    logging.info("运行日志写入: %s", log_path)

    config_path = base_dir.parent.parent.parent / "Password" / "config.yaml"
    try:
        client = login(str(config_path))
    except Exception as exc:
        logging.error("登录失败: %s", exc)
        return

    logging.info("启动时增量刷新 Core 本地 PPAC 参考缓存（本次仅刷新一次）。")
    try:
        ppac_ids, ppac_rets, refresh_report = refresh_ppac_data(
            client, flag_increment=True, return_report=True
        )
    except Exception as exc:
        logging.error("本地 PPAC 缓存刷新失败，停止处理且不修改 Alpha 属性: %s", exc)
        return
    logging.info(
        "Core PPAC 缓存刷新结果: 状态=%s，平台发现未缓存=%s，成功新增=%s，"
        "PnL失败=%s，本地缓存总数=%s。",
        refresh_report["status"],
        len(refresh_report["observed_new_os_alpha_ids"]),
        len(refresh_report["cached_new_os_alpha_ids"]),
        len(refresh_report["failed_pnl_alpha_ids"]),
        refresh_report["cached_os_count"],
    )
    if refresh_report["failed_pnl_alpha_ids"]:
        logging.warning(
            "以下 OS Alpha 因 PnL 未成功获取，尚未计入本地缓存: %s",
            ", ".join(refresh_report["failed_pnl_alpha_ids"]),
        )
    if not ppac_ids or not isinstance(ppac_rets, pd.DataFrame) or ppac_rets.empty:
        logging.error("本地 PPAC 参考缓存为空，停止处理且不修改 Alpha 属性。")
        return

    try:
        raw_alphas = fetch_recent_alphas(client)
    except Exception as exc:
        logging.error("候选列表不完整，停止处理且不修改 Alpha 属性: %s", exc)
        return
    logging.info("最近一个月共拉取基础候选: %s 个。", len(raw_alphas))
    if not raw_alphas:
        return
    candidates, counters = filter_candidates(client, raw_alphas)
    logging.info("前置过滤完成，候选=%s，漏斗=%s", len(candidates), counters)
    if not candidates:
        return
        
    lit_towers, category_counts = get_lit_tower_counts(client)
    logging.info("各区域已点亮塔数量: %s", lit_towers)

    # ==========================
    # 用户诉求两级优先级排序：
    # 第 1 级：还差 1-2 个即可点亮的黄金类别最高优先（差1个 > 差2个）
    # 第 2 级：所在区域未点亮塔数越少越优先（0 塔优先于 1 塔）
    # ==========================
    def get_candidate_priority(alpha):
        reg = str((alpha.get("settings") or {}).get("region") or "").strip().upper()
        d = int((alpha.get("settings") or {}).get("delay") or TARGET_DELAY)
        cats = extract_alpha_pyramid_categories(alpha)

        # gap 评级:
        # 1: 差 1 个即可点亮 (当前季度已有 2 个) -> 最高优先
        # 2: 差 2 个即可点亮 (当前季度已有 1 个) -> 次高优先
        # 3: 0 个未开始分类
        # 4: 已点亮分类 (当前季度已有 >= 3 个) -> 垫后
        best_gap = 3
        for r, delay_val, cat_name in cats:
            cnt = category_counts.get((r, delay_val, cat_name), 0)
            if cnt == 2:
                gap = 1
            elif cnt == 1:
                gap = 2
            elif cnt == 0:
                gap = 3
            else:
                gap = 4
            if gap < best_gap:
                best_gap = gap

        region_lit = lit_towers.get(reg, 0)
        return (best_gap, region_lit)

    def get_tower_count(alpha):
        r = str((alpha.get("settings") or {}).get("region") or "").strip().upper()
        return lit_towers.get(r, 0)

    if not CONFIG_PROCESS_LIT_TOWERS:
        # lit_towers < 3 的区域视为「未点亮」，需要优先处理并打 PPA_Submit
        # lit_towers >= 3 的区域视为「已点亮」，默认跳过
        unlit_candidates = [a for a in candidates if get_tower_count(a) < 3]
        if unlit_candidates:
            logging.info(
                "CONFIG_PROCESS_LIT_TOWERS=False：仅处理未点亮区域（塔数 < 3），"
                "候选从 %d 过滤至 %d 个。",
                len(candidates), len(unlit_candidates),
            )
            candidates = unlit_candidates
        else:
            logging.info(
                "CONFIG_PROCESS_LIT_TOWERS=False：所有候选区域塔数均 >= 3（已点亮），"
                "跳过本次 PPAC 计算。"
            )
            return
    else:
        logging.info("CONFIG_PROCESS_LIT_TOWERS=True（全量模式）：处理全部 %d 个候选。", len(candidates))

    # 执行优先级重排序
    candidates.sort(key=get_candidate_priority)

    # 统计并输出各优先级候选分布
    gap_stat = {1: 0, 2: 0, 3: 0, 4: 0}
    for a in candidates:
        g = get_candidate_priority(a)[0]
        gap_stat[g] = gap_stat.get(g, 0) + 1

    logging.info(
        "已完成两级优先级重排序！候选分布: [差1个即可点亮: %d 个 | 差2个即可点亮: %d 个 | 0个未开始: %d 个 | 已点亮分类: %d 个]",
        gap_stat.get(1, 0), gap_stat.get(2, 0), gap_stat.get(3, 0), gap_stat.get(4, 0),
    )
    logging.info("执行顺序：【差1个】最先判定，其次【差2个】，再次【0塔未点亮区域】，已满类别最后。")
    final_data = []
    result_counts = {"PPA_PASS": 0, "PPC_HIGH": 0, "PENDING": 0, "WRITE_FAILED": 0}
    for index, alpha in enumerate(candidates, start=1):
        alpha_id = alpha.get("id")
        logging.info("[%s/%s] 使用 Core 本地计算 PPAC: %s", index, len(candidates), alpha_id)
        try:
            # 单独拉取目标 Alpha 的 PnL 数据，增加强制成功重试逻辑
            alpha_pnls = None
            while True:
                _, pnl_result = get_alpha_pnls(client, [alpha])
                if pnl_result is not None and alpha_id in pnl_result.columns:
                    alpha_pnls = pnl_result
                    break
                    
                logging.warning(
                    f"Alpha {alpha_id} 的 PnL 下载失败（可能因网络或平台拥堵）。"
                    "已配置不可跳过，暂停 3 分钟后无限制重试..."
                )
                time.sleep(180)
            
            # PnL 数据拉取完成后，增加常规延时
            if CONFIG_PNL_DELAY > 0:
                time.sleep(CONFIG_PNL_DELAY)
                
            ppac_value = calc_ppac(
                client, alpha_id, ppac_rets, ppac_ids, 
                alpha_result=alpha, alpha_pnls=alpha_pnls
            )
        except Exception as exc:
            logging.error("Alpha %s 本地 PPAC 计算异常，保持属性不变: %s", alpha_id, exc)
            ppac_value = float("nan")
        result = apply_ppac_result(client, alpha, ppac_value, lit_towers)
        result_counts[result] += 1
        if result == "PPA_PASS":
            final_data.append(build_output_row(alpha, ppac_value))
        time.sleep(1.0)
        if index % CONFIG_BATCH_SIZE == 0 and index < len(candidates):
            time.sleep(CONFIG_REST_DURATION)

    logging.info("本地 PPAC 与标记完成: %s", result_counts)
    if not final_data:
        logging.info("没有完成本地 PPAC 且成功写回 PPA 标签的候选。")
        return
    pd.DataFrame(final_data).to_excel(output_path, index=False)
    logging.info("共输出 %s 个 PPA，结果保存至: %s", len(final_data), output_path)


if __name__ == "__main__":
    fetch_and_filter_ppa_alphas()
