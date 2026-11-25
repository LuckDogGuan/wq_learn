"""
sim/alpha_manager.py
Alpha 结果管理、筛选、剪枝与批量提交前检查。
所有 HTTP 通信完全委托给 Core.api.sim_api，本模块不含任何 requests 调用。
"""
from Core.api import login, API_BASE_URL
from Core.api.sim_api import (
    locate_alpha, get_user_alphas, _get_user_alphas_page,
    get_alpha_check, get_ppc_value, set_alpha_properties
)

from time import sleep
import time
import datetime
import json
import re
import math
import pandas as pd
from collections import defaultdict


_NON_FIELD_IDENTIFIERS = {
    'true', 'false', 'nan', 'inf', 'none',
    'market', 'sector', 'industry', 'subindustry', 'country',
    'slow', 'fast', 'crowding', 'ram',
}


def extract_expression_field_ids(expression, operator_names=None) -> list[str]:
    """按出现顺序提取候选字段，并排除函数、关键字参数和分组常量。"""
    expression = str(expression or '')
    operators = {str(item).lower() for item in (operator_names or [])}
    fields = []
    for match in re.finditer(r'\b[A-Za-z_][A-Za-z0-9_]*\b', expression):
        token = match.group(0)
        lowered = token.lower()
        tail = expression[match.end():]
        if lowered in _NON_FIELD_IDENTIFIERS or lowered in operators:
            continue
        if re.match(r'\s*\(', tail) or re.match(r'\s*=', tail):
            continue
        if token not in fields:
            fields.append(token)
    return fields


def _record_expression(record):
    regular = record.get('regular')
    if isinstance(regular, dict):
        return regular.get('code') or ''
    return record.get('expression') or regular or ''


def _field_dataset_id(metadata):
    dataset = metadata.get('dataset') if isinstance(metadata, dict) else None
    if isinstance(dataset, dict):
        return str(dataset.get('id') or 'UNKNOWN')
    return str((metadata or {}).get('dataset_id') or (metadata or {}).get('dataset.id') or 'UNKNOWN')


def build_field_combination_key(record, field_metadata) -> tuple:
    """构造 Region/Universe/Delay + 有序字段角色 + 表达式方向组合键。"""
    settings = record.get('settings') or {}
    expression = _record_expression(record)
    field_ids = record.get('field_ids') or extract_expression_field_ids(
        expression, record.get('operator_names')
    )
    missing = [field_id for field_id in field_ids if field_id not in field_metadata]
    if not field_ids or missing:
        raise ValueError(f'PENDING_FIELD_METADATA: {missing or field_ids}')
    direction = record.get('direction')
    if not direction:
        sharpe = record.get('sharpe', (record.get('is') or {}).get('sharpe'))
        direction = 'negative' if (
            isinstance(sharpe, (int, float)) and not isinstance(sharpe, bool) and sharpe < 0
        ) or expression.lstrip().startswith('-') else 'positive'
    ordered_fields = tuple(
        (_field_dataset_id(field_metadata[field_id]), field_id) for field_id in field_ids
    )
    return (
        str(record.get('region') or settings.get('region') or 'UNKNOWN').upper(),
        str(record.get('universe') or settings.get('universe') or 'UNKNOWN').upper(),
        int(record.get('delay', settings.get('delay', 1))),
        ordered_fields,
        str(direction).lower(),
    )


def _candidate_rank_key(record):
    """Generic ordering; gate results and turnover preference come from callers."""
    metrics = record.get('is') or {}
    def number(name, default=-math.inf):
        value = record.get(name, metrics.get(name, default))
        return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else default
    return (
        str(record.get('status') or '').upper() not in {
            'PENDING', 'PENDING_FIELD_METADATA', 'PENDING_SC', 'RESULTS_UNOBSERVED'
        },
        number('hard_gate_pass_count', number('hard_pass_count', 0)),
        number('fitness'), number('sharpe'), number('margin'),
        str(record.get('date_created') or record.get('dateCreated') or ''),
        str(record.get('alpha_id') or record.get('id') or ''),
    )


def rank_field_combination_candidates(records, field_metadata, *, rank_key=None) -> dict:
    """每个字段组合保留当前最佳一条，其余作为可顺序递补的历史记录。"""
    grouped = defaultdict(list)
    pending = []
    for original in records:
        record = dict(original)
        try:
            key = build_field_combination_key(record, field_metadata)
        except ValueError:
            record['status'] = 'PENDING_FIELD_METADATA'
            pending.append(record)
            continue
        record['field_combination_key'] = key
        grouped[key].append(record)

    winners = {}
    superseded = []
    ranked = {}
    for key, candidates in grouped.items():
        ordered = sorted(candidates, key=rank_key or _candidate_rank_key, reverse=True)
        for index, record in enumerate(ordered, 1):
            record['combination_rank'] = index
            if index > 1:
                record['pool_status'] = 'SUPERSEDED'
                superseded.append(record)
        winners[key] = ordered[0]
        ranked[key] = ordered
    return {
        'winners': winners,
        'ranked': ranked,
        'superseded': superseded,
        'pending_metadata': pending,
    }


def _record_towers(record):
    towers = record.get('covered_towers') or []
    if not towers:
        towers = [
            item.get('raw_scope') for item in (record.get('gap_scopes') or [])
            if isinstance(item, dict) and item.get('raw_scope')
        ]
    return list(dict.fromkeys(str(item) for item in towers if item))


def allocate_tower_candidate_pool(combination_winners, active_limit=12, *, rank_key=None) -> dict:
    """将多塔候选分配给最稀缺主塔；每条只占一个 ACTIVE 名额。"""
    if isinstance(active_limit, bool) or not isinstance(active_limit, int) or active_limit <= 0:
        raise ValueError('active_limit 必须是正整数')
    ranked_result = combination_winners if 'winners' in combination_winners else None
    winners = (ranked_result or {'winners': combination_winners})['winners']
    records = [dict(record) for record in winners.values()]
    availability = defaultdict(int)
    for record in records:
        for tower in _record_towers(record):
            availability[tower] += 1
    assigned = defaultdict(int)
    active, reserve, hold_pass = [], [], []
    for record in sorted(records, key=rank_key or _candidate_rank_key, reverse=True):
        towers = _record_towers(record)
        record['covered_towers'] = towers
        if not towers:
            record['pool_status'] = 'HOLD_PASS'
            hold_pass.append(record)
            continue
        primary = min(towers, key=lambda tower: (availability[tower], assigned[tower], tower))
        record['primary_tower'] = primary
        if assigned[primary] < active_limit:
            record['pool_status'] = 'ACTIVE'
            assigned[primary] += 1
            active.append(record)
        else:
            record['pool_status'] = 'RESERVE'
            reserve.append(record)
    all_towers = sorted(availability)
    return {
        'active': active,
        'reserve': reserve,
        'hold_pass': hold_pass,
        'superseded': list((ranked_result or {}).get('superseded', [])),
        'pending_metadata': list((ranked_result or {}).get('pending_metadata', [])),
        'tower_summary': {
            tower: {
                'combination_count': availability[tower],
                'active_count': assigned[tower],
            } for tower in all_towers
        },
    }


# ──────────────────────────────────────────────
# 对外重新暴露 set_alpha_properties / locate_alpha，
# 上层代码可直接从 sim.alpha_manager 导入（向前兼容）
# ──────────────────────────────────────────────


def get_alphas(start_date=None, end_date=None, sharpe_th=1.25, fitness_th=1.0,
               region="USA", alpha_num=200, usage="submit", tag=None) -> list:
    """
    分页检索平台上尚未提交的 REGULAR Alpha，供后续研究或人工提交前检查使用。

    这只是读取与整理函数：它不会创建回测、不会修改 Alpha，也不会提交 Alpha。
    平台查询固定排除已提交 Alpha，并且排除 SUPER 类型；本地仅进一步做
    longCount + shortCount > 100 的最低可交易股票数检查。

    工作流程：
    1. 两个日期都留空时，自动使用最近 30 个自然日；两个日期必须同时填写。
    2. 以 100 条/页读取平台结果。alpha_num=None 时持续翻页直至平台返回末页。
    3. usage="submit" 仅读取正向候选；其他 usage（例如 "track"）还会读取负向候选，
       并在本地将其表达式加负号，使其成为可继续研究的正向表达式。
    4. 为每个保留候选给出基于 Turnover 的推荐 Decay；推荐值不是回测结论。
    5. 遇到任一分页失败时，停止继续翻页并打印 PARTIAL/PENDING，已读取结果仍会返回。

    参数:
        start_date (str, optional): 开始日期，格式为 'YYYY-MM-DD' 或 'MM-DD'。
            与 end_date 同时为 None 时自动回看最近 30 天；底层平台接口按自然日边界查询，
            不支持小时级筛选。
        end_date (str, optional): 结束日期，格式与 start_date 相同，必须与 start_date 成对提供。
        sharpe_th (float): 正向候选要求 Sharpe >= 此值；track 模式的反向候选要求
            Sharpe <= -此值。
        fitness_th (float): 正向候选要求 Fitness >= 此值；track 模式的反向候选要求
            Fitness <= -此值。
        region (str): 平台 Region 条件，例如 'GBR'；不会替代 Universe、字段或回测参数检查。
        alpha_num (int | None): 每个方向扫描的客户端上限。None 表示不设上限，按 100 条分页
            直至平台没有更多结果；这不改变平台返回的时间范围和筛选条件。
        usage (str): 'submit' 仅读取正向候选，适合建立人工提交前候选列表；任何其他值
            （通常为 'track'）都会同时读取正、负方向，适合继续构造高阶表达式。
            名字为 'submit' 不代表会执行提交。
        tag (str, optional): 精确匹配的平台 Tag；None、空字符串或纯空白表示不按 Tag 筛选。

    返回:
        list: 每项为 [alpha_id, expression, sharpe, turnover, fitness, margin,
        dateCreated, original_decay, recommended_decay]。返回非空不代表通过
        Submission Check、相关性或其他提交门槛。
    """
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

    # ── 日期解析 ──
    if bool(start_date) != bool(end_date):
        raise ValueError("start_date 和 end_date 必须同时填写或同时留空")
    if alpha_num is not None and (
        isinstance(alpha_num, bool) or not isinstance(alpha_num, int) or alpha_num <= 0
    ):
        raise ValueError("alpha_num 必须是正整数或 None")
    if tag is not None and not isinstance(tag, str):
        raise TypeError("tag 必须是字符串或 None")
    tag = tag.strip() if tag else None

    if not start_date:
        end_dt   = now
        start_dt = now - datetime.timedelta(days=29)
        start_str = start_dt.strftime("%Y-%m-%d")
        end_str   = end_dt.strftime("%Y-%m-%d")
    else:
        start_str = f"{now.year}-{start_date}" if len(start_date) == 5 else start_date
        end_str   = f"{now.year}-{end_date}"   if len(end_date)   == 5 else end_date

    client = login()
    output = []
    count  = 0
    partial = False
    from Core.api.pagination import iter_alpha_pages, AlphaPageUnavailable
    directions = [False] if usage == "submit" else [False, True]
    cursors = [
        iter_alpha_pages(
            lambda offset, negative=negative: _get_user_alphas_page(
                client, start_str, end_str, sharpe_th, fitness_th,
                region, offset, tag=tag, negative=negative,
            ),
            max_records=alpha_num,
        ) for negative in directions
    ]
    seen_ids = set()
    while cursors:
        alpha_list = []
        page_failed = False
        for cursor in list(cursors):
            try:
                alpha_list.extend(next(cursor)["results"])
            except StopIteration:
                cursors.remove(cursor)
            except AlphaPageUnavailable as exc:
                print(f"[get_alphas][PARTIAL/PENDING] {exc}")
                partial = page_failed = True
                break

        for item in alpha_list:
            if item['id'] in seen_ids:
                continue
            seen_ids.add(item['id'])
            alpha_id  = item["id"]
            sharpe    = item["is"]["sharpe"]
            fitness   = item["is"]["fitness"]
            turnover  = item["is"]["turnover"]
            margin    = item["is"]["margin"]
            long_cnt  = item["is"].get("longCount", 0)
            short_cnt = item["is"].get("shortCount", 0)
            decay     = item["settings"]["decay"]
            exp       = item["regular"]["code"]
            date_c    = item["dateCreated"]
            count    += 1

            if (long_cnt + short_cnt) > 100:
                if sharpe < -sharpe_th:
                    exp = f"-{exp}"
                rec = [alpha_id, exp, sharpe, turnover, fitness, margin, date_c, decay]
                # Turnover → 推荐 Decay
                rec.append(_recommend_decay(turnover, decay))
                print(rec)
                output.append(rec)

        if page_failed:
            break

    state = "部分完成" if partial else "检索完成"
    print(f"[get_alphas] {state}，读取 {count} 个，保留 {len(output)} 个")
    return output


def _get_user_alphas_negative(client, start_str, end_str, sharpe_th, fitness_th,
                              region, offset, tag=None):
    """拉取空头 Alpha（Sharpe < -sharpe_th）。"""
    page = _get_user_alphas_page(
        client, start_str, end_str, sharpe_th, fitness_th,
        region, offset, tag=tag, negative=True,
    )
    return [] if page is None else page["results"]


def _recommend_decay(turnover: float, decay: int) -> int:
    """根据换手率推荐增大的 Decay 参数。"""
    if   turnover > 0.7:  return decay * 4
    elif turnover > 0.6:  return decay * 3 + 3
    elif turnover > 0.5:  return decay * 3
    elif turnover > 0.4:  return decay * 2
    elif turnover > 0.35: return decay + 4
    elif turnover > 0.3:  return decay + 2
    else:                 return decay


def prune(next_alpha_recs: list, prefix: str = "", keep_num: int = 5,
          field_ids: list[str] | None = None) -> list:
    """
    按基础字段组合削减同质化表达式，为下一阶保留每组最强的少量候选。

    推荐传入 field_ids：函数会在表达式中找出出现的字段，并按出现顺序形成分组键。
    因此，单字段 ``A`` 与双字段 ``A -> B`` 是不同组；``A -> B`` 与 ``B -> A``
    也不同组，因为字段在表达式中的角色和经济方向可能相反。每个“字段组合 +
    Alpha 正负方向”独立保留 |Sharpe| 最大的前 keep_num 个表达式。

    不传 field_ids 时保留旧兼容行为：prefix 非空则按旧 prefix 规则分组；prefix 为空
    则按完整表达式分组。这种情况下几乎只会删除完全重复的公式，不适合多 Category
    Notebook 的真正字段剪枝。

    参数:
        next_alpha_recs (list): get_alphas 返回的记录列表。
        prefix (str): 旧代码兼容用的字段前缀（如 'fnd6'）。field_ids 存在时不使用它。
        keep_num (int): 每个字段组合及方向保留的 Top N，必须为正整数。
        field_ids (list[str] | None): 当前研究批次允许的字段 ID，例如 Notebook 的
            selected_ids。多字段公式会按字段出现顺序组成一个组合，而不是被错误并入
            任一单字段组。

    返回:
        list: 剪枝后的 [expression, recommended_decay] 列表；不表示平台提交资格。
    """
    if isinstance(keep_num, bool) or not isinstance(keep_num, int) or keep_num <= 0:
        raise ValueError("keep_num 必须是正整数")

    def group_key(expression: str, sharpe: float) -> tuple[str, ...] | str:
        if field_ids:
            matched = []
            for field_id in field_ids:
                pattern = rf"(?<![A-Za-z0-9_]){re.escape(field_id)}(?![A-Za-z0-9_])"
                match = re.search(pattern, expression)
                if match:
                    matched.append((match.start(), field_id))
            if matched:
                source = tuple(field_id for _, field_id in sorted(matched))
            else:
                # 未识别字段不与其它公式合并，避免错误删除非本批字段或复杂组合。
                source = (expression,)
        elif prefix and prefix in expression:
            source = (expression.split(prefix)[-1].split(",")[0].split(")")[0].strip(),)
        else:
            source = (expression,)

        direction = "negative" if sharpe < 0 else "positive"
        return (direction, *source)

    grouped = defaultdict(list)
    for rec in next_alpha_recs:
        grouped[group_key(rec[1], rec[2])].append(rec)

    output = []
    for records in grouped.values():
        # get_alphas(track) 会混合正、负方向；用 |Sharpe| 才能在各自方向内比较强弱。
        for rec in sorted(records, key=lambda item: abs(item[2]), reverse=True)[:keep_num]:
            output.append([rec[1], rec[-1]])

    return output


def get_sc_value(client, alpha_id: str) -> float | str:
    """
    从 get_alpha_check 的结果中提取自相关性 (SELF_CORRELATION) 值。

    返回:
        float  — 通过时的 SC 值
        "fail" — 存在 FAIL 检查项
        "sleep"— Session 已过期
        "error"— 解析异常
    """
    check = get_alpha_check(client, alpha_id)
    if not check:
        return "error"
    if check.get("is", 0) == 0:
        return "sleep"
    try:
        checks_df = pd.DataFrame(check["is"]["checks"])
        sc = checks_df[checks_df.name == "SELF_CORRELATION"]["value"].values[0]
        if any(checks_df["result"] == "FAIL"):
            return "fail"
        return sc
    except Exception:
        return "error"


def get_pc_value(client, alpha_id: str) -> float | str:
    """
    获取生产相关性 (PROD_CORRELATION)。

    复用 validator 的专用 /correlations/prod 查询；仅在专用接口没有数值时
    使用 /check 降级一次。Power Pool Correlation 与 PC 含义不同，不再混用。

    返回:
        float  — PC 值
        "sleep"— Session 已过期
        "error"— 解析异常
    """
    from Core.sim.validator import get_pc_check
    return get_pc_check(client, alpha_id)


def check_submission(alpha_bag: list, gold_bag: list, start: int = 0) -> list:
    """
    批量进行 Alpha 提交前完整性校验（SC + 全部 checks 通过 → 进入 gold_bag）。

    参数:
        alpha_bag (list): 待检查 Alpha ID 列表。
        gold_bag  (list): 已通过的优质因子库列表 (out param，追加写入)。
        start     (int): 起始索引（断点续传）。

    返回:
        list: 更新后的 gold_bag。
    """
    depot  = []
    client = login()

    for idx, alpha_id in enumerate(alpha_bag):
        if idx < start:
            continue
        if idx % 5 == 0:
            print(f"[check_submission] 进度: {idx}/{len(alpha_bag)}")
        if idx % 200 == 0 and idx > 0:
            client = login()

        sc = get_sc_value(client, alpha_id)

        if sc == "sleep":
            sleep(100)
            client = login()
            alpha_bag.append(alpha_id)       # 延迟重试
        elif sc == "fail":
            continue
        elif sc == "error":
            depot.append(alpha_id)
        elif sc != sc:                        # NaN check
            print(f"[check_submission] NaN SC: {alpha_id}")
            sleep(100)
            alpha_bag.append(alpha_id)
        else:
            print(f"[check_submission] 通过: {alpha_id}  SC={sc:.4f}")
            gold_bag.append((alpha_id, sc))

    print(f"[check_submission] 待定 depot: {depot}")
    return gold_bag


def view_alphas(gold_bag: list):
    """
    格式化打印金子因子库中的 Alpha 信息（按 Sharpe 降序）。

    参数:
        gold_bag (list): (alpha_id, self_correlation) 元组列表。
    """
    client     = login()
    sharp_list = []

    for alpha_id, pc in gold_bag:
        triple = locate_alpha(client, alpha_id)
        if triple:
            info = [triple[0], triple[2], triple[3], triple[4], triple[5], triple[6], triple[1], pc]
            sharp_list.append(info)

    sharp_list.sort(reverse=True, key=lambda x: x[1])
    for row in sharp_list:
        print(row)
