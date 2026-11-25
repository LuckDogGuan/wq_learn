"""
WorldQuant BRAIN Alpha 自动提交工具（论坛原文抓取）
"""

import datetime
import calendar
import json
import os
import random
import time
import logging
import argparse
from os.path import expanduser
from typing import Callable, Optional, List, Tuple


import pandas as pd
import requests
from requests.exceptions import (
    ConnectionError,
    Timeout,
    RequestException,
)
import wqb


# ============================================================
# 配置区 — 根据你的环境修改这里
# ============================================================


# 凭据文件路径（JSON 格式：["username", "password"]）
CREDENTIALS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Password", "config.yaml")
)


# API 基础地址
API_BASE = "https://api.worldquantbrain.com"


# 请求超时（秒），usappa 慢时可调大
REQUEST_TIMEOUT = 120


# 单次提交最大重试轮数（外层）
MAX_ATTEMPTS = 5


# POST 阶段遇到网络异常时等待秒数
POST_RETRY_SLEEP = 5


# POST 返回非预期状态码（如200）时等待秒数（usappa慢，建议10分钟）
POST_UNKNOWN_SLEEP = 600  # 10分钟


# GET 轮询的最大总等待时间（秒），超过视为超时
GET_POLL_TIMEOUT = 3600  # 1小时


# 日志输出到文件（None 则只输出到控制台）
LOG_FILE = "submit_alpha.log"


# ============ PPA 模式配置 ============
# 是否开启 PPA 提交模式（默认关，也可命令行 --ppa 临时开启）
PPA_MODE = False
# PPA 备注映射文件：两列 alpha_id, description（备注换行需用双引号包裹）
PPA_DESC_CSV = "ppaalpha_id_description.csv"
# PPA 备注格式校验：官方下限 100 字符，无上限
PPA_MIN_CHARS = 100
# PPA 备注必须包含的三段标题（英文备注分行格式）
PPA_REQUIRED_MARKERS = [
    "Idea:",
    "Rationale for data used:",
    "Rationale for operators used:",
]


# ============ 429 自适应退避配置 ============
# 基础退避延迟（秒），首次 429 等待
RATELIMIT_BASE_DELAY = 5
# 最大退避延迟（秒），连续 429 会指数增长但不超过此值
RATELIMIT_MAX_DELAY = 120
# 断路器阈值：连续 429 达到此次数后触发断路器，暂停全部请求
RATELIMIT_CIRCUIT_THRESHOLD = 5
# 断路器恢复时间（秒），触发后等待此时间再尝试
RATELIMIT_CIRCUIT_RECOVERY = 60
# 抖动比例（0~1），在退避延迟基础上加随机抖动避免雷鸣群体效应
RATELIMIT_JITTER_RATIO = 0.3


# ============================================================
# 日志配置
# ============================================================


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        *([logging.FileHandler(LOG_FILE, encoding="utf-8")] if LOG_FILE else []),
    ],
)
logger = logging.getLogger(__name__)


# pandas 显示设置
pd.set_option("expand_frame_repr", False)
pd.set_option("display.max_rows", 1000)
pd.set_option("display.max_colwidth", 100)



# ============================================================
# 429 自适应退避
# ============================================================


class AdaptiveRateLimiter:
    """自适应退避 + 断路器（同步版）。


    每次 429 指数退避 + 随机抖动避免雷鸣群体效应；
    连续 429 过多触发断路器，暂停全部请求后自动恢复。
    断路器恢复后自动重新认证 session（换新 token）。
    """


    def __init__(
        self,
        base_delay: float = RATELIMIT_BASE_DELAY,
        max_delay: float = RATELIMIT_MAX_DELAY,
        circuit_threshold: int = RATELIMIT_CIRCUIT_THRESHOLD,
        circuit_recovery: float = RATELIMIT_CIRCUIT_RECOVERY,
        jitter_ratio: float = RATELIMIT_JITTER_RATIO,
        on_circuit_recovery: Optional[Callable] = None,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit_threshold = circuit_threshold
        self.circuit_recovery = circuit_recovery
        self.jitter_ratio = jitter_ratio
        self.on_circuit_recovery = on_circuit_recovery
        self._consecutive_429 = 0
        self._circuit_open_until = 0.0


    def _jitter(self, delay: float) -> float:
        """在 [delay*(1-ratio), delay*(1+ratio)] 范围内随机抖动"""
        lo = max(0.5, delay * (1 - self.jitter_ratio))
        hi = delay * (1 + self.jitter_ratio)
        return random.uniform(lo, hi)


    def backoff(self, retry_count: int) -> float:
        """记录一次 429，返回应等待的秒数（已含抖动）。


        retry_count: 当前请求连续 429 的次数（1-based）。
        """
        self._consecutive_429 += 1
        if self._consecutive_429 >= self.circuit_threshold:
            self._circuit_open_until = time.time() + self.circuit_recovery
            logger.warning(
                "🔌 连续 %d 次 429，断路器触发！暂停 %d 秒",
                self._consecutive_429, self.circuit_recovery,
            )
        delay = min(self.base_delay * (2 ** (retry_count - 1)), self.max_delay)
        return self._jitter(delay)


    def is_circuit_open(self) -> bool:
        """断路器是否打开（应暂停所有请求）。"""
        if self._consecutive_429 >= self.circuit_threshold:
            if time.time() < self._circuit_open_until:
                return True
            self._consecutive_429 = 0  # 恢复时间到 → 半开
        return False


    def wait_if_circuit_open(self) -> None:
        """如果断路器打开，阻塞等待直到恢复。恢复后触发 on_circuit_recovery 回调。"""
        if self.is_circuit_open():
            remaining = self._circuit_open_until - time.time()
            if remaining > 0:
                logger.warning("🔌 断路器打开，等待 %.0f 秒后恢复...", remaining)
                time.sleep(remaining)
            # 恢复后触发回调（如刷新 session）
            if self.on_circuit_recovery:
                logger.info("🔄 断路器恢复，刷新 session...")
                self.on_circuit_recovery()


    def reset(self) -> None:
        """成功请求后重置 429 计数。"""
        self._consecutive_429 = 0



# ============================================================
# 核心函数
# ============================================================


def create_session(credentials_file: str = CREDENTIALS_FILE) -> requests.Session:
    """
    创建已认证的 wqb.WQBSession。
   
    凭据文件格式：JSON 数组 ["username", "password"]，或对象 {"email": "...", "password": "..."}
   
    返回：
        wqb.WQBSession — 已通过 /authentication 认证的会话对象
   
    异常：
        FileNotFoundError — 凭据文件不存在
        Exception — 认证失败
    """
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(
            f"凭据文件不存在: {credentials_file}\n"
            f"请创建该文件，内容格式: [\"你的邮箱\", \"你的密码\"]"
        )


    with open(credentials_file, encoding="utf-8") as f:
        if credentials_file.lower().endswith(('.yaml', '.yml')):
            credentials = {}
            for line in f:
                line = line.split('#', 1)[0].strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    credentials[key.strip()] = value.strip().strip('"\'')
        else:
            credentials = json.load(f)

    if isinstance(credentials, dict):
        username = credentials.get("email") or credentials.get("username")
        password = credentials.get("password")
    elif isinstance(credentials, (list, tuple)) and len(credentials) == 2:
        username, password = credentials
    else:
        raise ValueError("凭据文件必须是 [username, password] 或 {email, password}")
    if not username or not password:
        raise ValueError("凭据文件缺少账号或密码")
    try:
        sess = wqb.WQBSession((username, password), logger=logger)
        resp = sess.post_authentication(timeout=REQUEST_TIMEOUT)
    except (ConnectionError, Timeout) as e:
        raise ConnectionError(f"无法连接 BRAIN API（网络问题或 VPN 未开）: {e}")


    if resp.status_code not in (200, 201):
        raise Exception(
            f"认证失败 HTTP {resp.status_code}: {resp.text[:300]}"
        )


    logger.info("✅ BRAIN 认证成功")
    return sess



def _safe_checks_table(checks_list):
    """安全打印 checks 表格，兼容不同字段名（value/result/passed/status）。"""
    if not checks_list:
        return
    df = pd.DataFrame(checks_list)
    cols = [c for c in ("name", "value", "result", "passed", "status", "message") if c in df.columns]
    logger.error("\n" + (df[cols].to_string() if cols else df.to_string()))



def submit_alpha(
    sess: requests.Session,
    alpha_id: str,
    max_attempts: int = MAX_ATTEMPTS,
    ppa_mode: bool = False,
    ppa_desc: Optional[str] = None,
    limiter: Optional["AdaptiveRateLimiter"] = None,
) -> int:
    """
    提交单个 Alpha。


    两阶段提交：
      1) POST 触发提交，收到 201 进入第二阶段
      2) GET 轮询直到 Retry-After=0


    参数：
        sess: 已认证的 requests.Session
        alpha_id: Alpha 的 ID（如 "12345abc"）
        max_attempts: 最大外层重试次数
        limiter: 自适应退避实例（共享于批次内所有 alpha），为 None 则不启用


    返回：
        最终 HTTP 状态码（200=成功, 403=检查失败, 404=超时等）
    """
    submit_url = f"{API_BASE}/alphas/{alpha_id}/submit"


    for attempt in range(1, max_attempts + 1):
        logger.info(f"🔄 [{attempt}/{max_attempts}] 开始提交 Alpha {alpha_id}")


        # ========== PPA 模式：提交前校验/修复备注 ==========
        if ppa_mode and ppa_desc is not None:
            logger.info(f"📋 [{attempt}/{max_attempts}] PPA 备注校验: {alpha_id}")
            if not ensure_ppa_description(sess, alpha_id, ppa_desc, limiter=limiter):
                logger.error(f"❌ {alpha_id} 备注修复失败，放弃本轮")
                return 404


        # ========== 第一阶段：POST ==========
        post_success = False
        post_429_count = 0
        while True:
            try:
                res = sess.post(submit_url, timeout=REQUEST_TIMEOUT)
            except (ConnectionError, Timeout) as e:
                logger.warning(f"⚠️ POST 网络异常: {e}，{POST_RETRY_SLEEP}秒后重试...")
                time.sleep(POST_RETRY_SLEEP)
                continue
            except RequestException as e:
                logger.warning(f"⚠️ POST 请求异常: {e}，{POST_RETRY_SLEEP}秒后重试...")
                time.sleep(POST_RETRY_SLEEP)
                continue


            if res.status_code == 201:
                logger.info(f"  Alpha {alpha_id} POST 201 — 已触发提交，进入等待...")
                post_success = True
                break
            elif res.status_code == 400:
                logger.info(f"  Alpha {alpha_id} POST 400 — 已经提交过了，直接进入等待...")
                logger.debug(f"  Body: {res.content[:500]}")
                post_success = True  # 已在队列中，去GET轮询等结果
                break
            elif res.status_code == 403:
                # 区分：真正失败 vs 已提交过
                try:
                    checks = res.json().get("is", {}).get("checks", [])
                except Exception:
                    checks = []
                if checks:
                    only_already = all(c.get("name") == "ALREADY_SUBMITTED" for c in checks)
                    if only_already:
                        logger.info(f"  ✅ Alpha {alpha_id} 之前已提交成功（ALREADY_SUBMITTED）")
                        return 200
                    logger.error(f"  Alpha {alpha_id} POST 403 — 检查不通过！")
                    _safe_checks_table(checks)
                else:
                    logger.info(f"  Alpha {alpha_id} POST 403 — 可能已提交过，跳过")
                return res.status_code
            elif res.status_code == 429:
                post_429_count += 1
                delay = (
                    limiter.backoff(post_429_count) if limiter
                    else POST_RETRY_SLEEP
                )
                logger.warning(
                    f"  ⚠️ POST 429 限流（第{post_429_count}次），等待 {delay:.1f}s..."
                )
                time.sleep(delay)
                if limiter and limiter.is_circuit_open():
                    limiter.wait_if_circuit_open()
                continue
            else:
                logger.warning(
                    f"  Alpha {alpha_id} POST {res.status_code}，"
                    f"{POST_UNKNOWN_SLEEP}秒后重试..."
                )
                logger.debug(f"  Body: {res.content[:500]}")
                time.sleep(POST_UNKNOWN_SLEEP)


        if not post_success:
            # POST 没拿到 201，可能是 400（已提交），跳到下一轮
            continue


        # ========== 第二阶段：GET 轮询 ==========
        count = 0
        get_429_count = 0
        start_time = datetime.datetime.now()
        while True:
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            if elapsed > GET_POLL_TIMEOUT:
                logger.error(
                    f"  Alpha {alpha_id} GET 轮询超时（>{GET_POLL_TIMEOUT}秒），放弃本轮"
                )
                break  # 进入下一轮外层重试


            try:
                res = sess.get(submit_url, timeout=REQUEST_TIMEOUT)
            except (ConnectionError, Timeout) as e:
                logger.warning(f"  ⚠️ GET 网络异常: {e}，3秒后重试...")
                time.sleep(3)
                continue
            except RequestException as e:
                logger.warning(f"  ⚠️ GET 请求异常: {e}，3秒后重试...")
                time.sleep(3)
                continue


            if res.status_code == 200:
                retry_after = res.headers.get("Retry-After")
                if retry_after:
                    retry_sec = float(retry_after)
                    count += 1
                    time.sleep(retry_sec)
                    if count % 75 == 0:
                        logger.info(
                            f"  Alpha {alpha_id} 等待中... "
                            f"已等待 {datetime.datetime.now() - start_time}"
                        )
                else:
                    elapsed = datetime.datetime.now() - start_time
                    logger.info(
                        f"  ✅ Alpha {alpha_id} 提交成功！"
                        f" 总耗时 {elapsed}"
                    )
                    if limiter:
                        limiter.reset()
                    return res.status_code
            elif res.status_code == 403:
                try:
                    checks = res.json()["is"]["checks"]
                except Exception:
                    checks = []
                if checks and all(c.get("name") == "ALREADY_SUBMITTED" for c in checks):
                    logger.info(f"  ✅ Alpha {alpha_id} 之前已提交成功（ALREADY_SUBMITTED）")
                    return 200
                logger.error(f"  Alpha {alpha_id} GET 403 — 提交失败，需改进！")
                try:
                    _safe_checks_table(checks)
                except Exception:
                    logger.error(f"  Body: {res.content[:500]}")
                return res.status_code
            elif res.status_code == 404:
                logger.error(f"  Alpha {alpha_id} GET 404 — 提交超时失效")
                break
            elif res.status_code == 429:
                get_429_count += 1
                # 优先使用服务器给的 Retry-After，没有则走自适应退避
                retry_after = res.headers.get("Retry-After")
                server_delay = None
                if retry_after:
                    try:
                        server_delay = float(retry_after)
                    except (ValueError, TypeError):
                        pass
                if server_delay is not None:
                    delay = server_delay
                else:
                    delay = (
                        limiter.backoff(get_429_count) if limiter
                        else 3.0
                    )
                logger.warning(
                    f"  ⚠️ GET 429 限流（第{get_429_count}次），"
                    f"{'Retry-After: ' + str(server_delay) + 's' if server_delay else '退避: ' + str(round(delay, 1)) + 's'}"
                )
                time.sleep(delay)
                if limiter and limiter.is_circuit_open():
                    limiter.wait_if_circuit_open()
                continue
            else:
                logger.warning(
                    f"  Alpha {alpha_id} GET {res.status_code}，"
                    f"3秒后重试..."
                )
                logger.debug(f"  Headers: {dict(res.headers)}")
                logger.debug(f"  Body: {res.content[:500]}")
                time.sleep(3)


    logger.error(f"❌ Alpha {alpha_id} 经过 {max_attempts} 轮尝试仍未成功")
    return 404



def submit_batch(
    sess: requests.Session,
    alpha_ids: List[str],
    pause_between: int = 10,
    ppa_mode: bool = False,
    desc_map: Optional[dict] = None,
) -> Tuple[List[str], List[str]]:
    """
    批量提交多个 Alpha。


    参数：
        sess: 已认证的 session
        alpha_ids: Alpha ID 列表
        pause_between: 每个提交之间的间隔秒数（避免触发频率限制）


    返回：
        (成功的ID列表, 失败的ID列表)
    """
    successful = []
    failed = []
    # 批次内共享一个自适应退避实例，所有 alpha 的 429 共用一个断路器
    # 断路器恢复后强制重新认证（避免 token 过期被服务器当 429 打回）
    def _refresh_session():
        """强制重新认证当前 session，刷新 token cookie"""
        logger.info("🔄 断路器恢复，重新认证 session...")
        try:
            resp = sess.post(
                f"{API_BASE}/authentication",
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code in (200, 201):
                logger.info("✅ Session 认证刷新成功")
            else:
                logger.error(f"⚠️ Session 刷新返回 HTTP {resp.status_code}")
        except (ConnectionError, Timeout, RequestException) as e:
            logger.error(f"❌ Session 刷新失败: {e}")


    limiter = AdaptiveRateLimiter(on_circuit_recovery=_refresh_session)


    for i, alpha_id in enumerate(alpha_ids, 1):
        logger.info(f"{'='*50}")
        logger.info(f"[{i}/{len(alpha_ids)}] 提交 Alpha: {alpha_id}")
        logger.info(f"{'='*50}")


        ppa_desc = desc_map.get(alpha_id) if (ppa_mode and desc_map) else None
        status = submit_alpha(sess, alpha_id, ppa_mode=ppa_mode, ppa_desc=ppa_desc, limiter=limiter)
        if status == 200:
            successful.append(alpha_id)
        else:
            failed.append(alpha_id)


        if i < len(alpha_ids):
            logger.info(f"⏸ 等待 {pause_between} 秒后继续下一个...")
            time.sleep(pause_between)


    return successful, failed



# ============================================================
# PPA 模式：备注(Description)自动校验与修复
# 仅操作 Properties -> Description，不动其他属性（name/tags/color/category）
# PATCH body 格式：description 必须嵌套在 regular/combo/selection 子对象中（非顶层字段）
# ============================================================


def load_ppa_descriptions(csv_file: str = PPA_DESC_CSV) -> dict:
    """读取 PPA 备注映射文件，返回 {alpha_id: description}。"""
    if not os.path.exists(csv_file):
        logger.warning(f"⚠️ PPA 备注文件不存在: {csv_file}，跳过 PPA 校验")
        return {}
    df = pd.read_csv(csv_file)
    desc_map = {}
    for _, row in df.iterrows():
        aid = str(row.iloc[0]).strip()
        desc = str(row.iloc[1])
        desc_map[aid] = desc
    logger.info(f"📋 从 {csv_file} 读取到 {len(desc_map)} 条 PPA 备注")
    return desc_map


def load_ppa_scope(scope_file: str) -> dict:
    """读取并校验一个 PPA 范围 JSON。"""
    with open(scope_file, encoding="utf-8") as f:
        scope = json.load(f)
    required = ("duration", "core_requirements")
    if not all(key in scope for key in required):
        raise ValueError(f"PPA 范围缺少字段: {[key for key in required if key not in scope]}")
    requirements = scope["core_requirements"]
    for key in ("region", "delay", "universe"):
        if key not in requirements:
            raise ValueError(f"PPA 范围缺少 core_requirements.{key}")
    requirements.setdefault("forbidden_datasets", [])
    return scope


def load_alpha_standard(filename: str) -> dict:
    """读取不同阿尔法标准目录中的一个标准文件。"""
    standard_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "不同阿尔法标准", filename)
    )
    with open(standard_file, encoding="utf-8") as f:
        return json.load(f)


def resolve_ppa_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    months: int = 2,
) -> tuple[datetime.datetime, datetime.datetime]:
    """解析查询日期；未指定时使用最近指定月数，默认两个月。"""
    if months < 1:
        raise ValueError("months 必须大于等于 1")
    today = datetime.date.today()
    if start_date is None and end_date is None:
        end = today
        month = end.month - months
        year = end.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        start = end.replace(day=min(end.day, calendar.monthrange(year, month)[1]))
        start = start.replace(year=year, month=month)
    elif start_date is not None and end_date is not None:
        start = datetime.date.fromisoformat(start_date)
        end = datetime.date.fromisoformat(end_date)
    elif start_date is not None:
        start = datetime.date.fromisoformat(start_date)
        end = today
    else:
        end = datetime.date.fromisoformat(end_date)
        month = end.month - months
        year = end.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        start = end.replace(day=min(end.day, calendar.monthrange(year, month)[1]))
        start = start.replace(year=year, month=month)
    if start > end:
        raise ValueError("start_date 不能晚于 end_date")
    return (
        datetime.datetime.combine(start, datetime.time.min, tzinfo=datetime.timezone.utc),
        datetime.datetime.combine(end, datetime.time(23, 59, 59), tzinfo=datetime.timezone.utc),
    )


def fetch_ppa_datasets(sess: requests.Session, scope_file: str) -> tuple[dict, list[dict]]:
    """按 PPA 范围读取数据集；主题查询为空时回退全量，再排除禁用数据集。"""
    scope = load_ppa_scope(scope_file)
    requirements = scope["core_requirements"]
    region = requirements["region"]
    delay = requirements["delay"]
    universe = requirements["universe"]
    themed = sess.search_datasets_limited(
        region, delay, universe, theme=True, limit=50, offset=0, log=None
    ).json()
    rows = themed.get("results") or []
    if not rows:
        rows = [
            row
            for response in sess.search_datasets(
                region, delay, universe, limit=50, log=None
            )
            for row in response.json().get("results", [])
        ]
    forbidden = {str(item).strip().lower() for item in requirements["forbidden_datasets"]}
    rows = [row for row in rows if str(row.get("id", "")).strip().lower() not in forbidden]
    return scope, rows


def fetch_ppa_regular_alphas(
    sess: requests.Session,
    scope_file: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    months: int = 2,
    query_requirements: Optional[dict] = None,
) -> tuple[dict, list[dict]]:
    """读取日期和 PPA 基础设置匹配的全部 REGULAR Alpha，不附加指标限制。"""
    scope = load_ppa_scope(scope_file)
    requirements = query_requirements or scope["core_requirements"]
    start, end = resolve_ppa_date_range(start_date, end_date, months)
    created = wqb.FilterRange(start, end, True, True)
    query = dict(
        type="REGULAR",
        date_created=created,
        region=requirements["region"],
        instrument_type="EQUITY",
        universe=requirements["universe"],
        delay=requirements["delay"],
        log=None,
    )
    first = sess.filter_alphas_limited(**query, limit=100, offset=0)
    payload = first.json()
    rows = payload.get("results", [])
    for offset in range(100, payload.get("count", len(rows)), 100):
        rows.extend(sess.filter_alphas_limited(**query, limit=100, offset=offset).json().get("results", []))
    return scope, rows


def fetch_unsubmitted_regular_alphas(
    sess: requests.Session,
    requirements: dict,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    months: int = 2,
) -> list[dict]:
    """直接读取平台未提交 REGULAR Alpha，不依赖本地范围文件。"""
    start, end = resolve_ppa_date_range(start_date, end_date, months)
    query = dict(
        type="REGULAR",
        status="UNSUBMITTED",
        date_created=wqb.FilterRange(start, end, True, True),
        region=requirements.get("region"),
        instrument_type=requirements.get("instrument_type", "EQUITY"),
        delay=requirements.get("delay"),
        log=None,
    )
    if requirements.get("universe"):
        query["universe"] = requirements["universe"]
    if requirements.get("sharpe_min") is not None:
        query["sharpe"] = wqb.FilterRange(requirements["sharpe_min"], float("inf"), True, False)
    if requirements.get("fitness_min") is not None:
        query["fitness"] = wqb.FilterRange(requirements["fitness_min"], float("inf"), True, False)
    if requirements.get("turnover_min") is not None and requirements.get("turnover_max") is not None:
        query["turnover"] = wqb.FilterRange(
            requirements["turnover_min"], requirements["turnover_max"], False, False
        )
    first = sess.filter_alphas_limited(**query, limit=100, offset=0)
    payload = first.json()
    if isinstance(payload, list):
        payload = {"results": payload, "count": len(payload)}
    rows = [row for row in payload.get("results", []) if isinstance(row, dict)]
    for offset in range(100, payload.get("count", len(rows)), 100):
        page = sess.filter_alphas_limited(**query, limit=100, offset=offset).json()
        page_rows = page if isinstance(page, list) else page.get("results", [])
        rows.extend(row for row in page_rows if isinstance(row, dict))
    return rows



def get_alpha_description(sess: requests.Session, alpha_id: str) -> str:
    """GET /alphas/{id} 读取当前 description。失败/不存在返回空串。"""
    url = f"{API_BASE}/alphas/{alpha_id}"
    try:
        res = sess.get(url, timeout=REQUEST_TIMEOUT)
    except (ConnectionError, Timeout, RequestException) as e:
        logger.warning(f"⚠️ 读取 {alpha_id} 备注失败: {e}")
        return ""
    if res.status_code == 200:
        data = res.json()
        # description 嵌套在 regular/combo/selection 之一，非顶层字段
        for key in ("regular", "combo", "selection"):
            sub = data.get(key)
            if isinstance(sub, dict) and sub.get("description") is not None:
                return (sub.get("description") or "").strip()
        return ""
    logger.warning(f"⚠️ 读取 {alpha_id} 备注返回 HTTP {res.status_code}")
    return ""



def set_alpha_description(sess: requests.Session, alpha_id: str, description: str) -> bool:
    """PATCH /alphas/{id} 覆盖 description（=删除旧+写新）。
    description 必须嵌套在 regular/combo/selection 子对象(视 alpha 类型而定)，
    禁止顶层 "description" 字段(否则 HTTP 400 {"description":["Unexpected property."]})。
    成功返回 True。"""
    url = f"{API_BASE}/alphas/{alpha_id}"
    # 先 GET 判断 alpha 类型，确定 description 的嵌套键
    sub_key = "regular"
    try:
        r = sess.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            d = r.json()
            for k in ("regular", "combo", "selection"):
                if isinstance(d.get(k), dict):
                    sub_key = k
                    break
    except (ConnectionError, Timeout, RequestException):
        pass  # 拿不到类型就默认 regular（PPA alpha 普通类型）
    try:
        res = sess.patch(url, json={sub_key: {"description": description}}, timeout=REQUEST_TIMEOUT)
    except (ConnectionError, Timeout, RequestException) as e:
        logger.error(f"❌ 更新 {alpha_id} 备注失败: {e}")
        return False
    if res.status_code in (200, 201):
        logger.info(f"  ✅ {alpha_id} 备注已更新（{len(description)} 字符）")
        return True
    logger.error(f"❌ 更新 {alpha_id} 备注返回 HTTP {res.status_code}: {res.text[:300]}")
    return False



def validate_ppa_description(text: str) -> Tuple[bool, str]:
    """校验 PPA 备注格式：≥100 字符 且 含三段标题。返回 (是否合格, 原因)。"""
    text = text or ""
    if len(text.strip()) < PPA_MIN_CHARS:
        return False, f"字符数 {len(text.strip())} < 下限 {PPA_MIN_CHARS}"
    missing = [m for m in PPA_REQUIRED_MARKERS if m not in text]
    if missing:
        return False, f"缺少必要段落: {missing}"
    return True, "OK"



def _auto_fix_ppa_format(text: str) -> str:
    """自动修复常见 PPA 备注格式问题（仅修复明确可自动纠正的）。


    当前支持：
      - 三段标题(Idea:/Rationale for data used:/Rationale for operators used:)冒号后缺空格 → 自动补空格
    返回修复后的文本；无需修复则返回原文本。
    """
    import re


    fixed = text
    for marker in PPA_REQUIRED_MARKERS:
        # 冒号后紧跟非空白非换行字符 → 补空格
        pattern = rf"({re.escape(marker)})([^\s\n])"
        fixed = re.sub(pattern, r"\1 \2", fixed)
    return fixed



def ensure_ppa_description(
    sess: requests.Session, alpha_id: str, expected_desc: str,
    limiter: Optional["AdaptiveRateLimiter"] = None,
) -> bool:
    """
    PPA 提交前的备注校验与修复。
    逻辑：
      1) 断路器检查：如果 limiter 断路器打开，先等待恢复
      2) 预检 CSV 备注本身格式，不合格仅 warn（仍以 CSV 为准覆盖）
      3) GET 读取 alpha 当前 description
      4) 与 CSV 备注一致 → 跳过，返回 True
      5) 不一致/为空/被顶掉 → PATCH 用 CSV 备注覆盖，返回 True
    """
    if limiter:
        limiter.wait_if_circuit_open()


    ok, reason = validate_ppa_description(expected_desc)
    if not ok:
        # 尝试自动修复常见格式问题（如 Idea: 后缺空格）
        fixed = _auto_fix_ppa_format(expected_desc)
        if fixed != expected_desc:
            ok2, reason2 = validate_ppa_description(fixed)
            if ok2:
                logger.warning(
                    "🔧 %s 备注格式自动修复成功（标题冒号后补空格），已用修复版提交，请同步修改 CSV",
                    alpha_id,
                )
                expected_desc = fixed
            else:
                logger.warning(
                    "⚠️ %s CSV 备注格式不达标（自动修复也失败）: %s",
                    alpha_id, reason2,
                )
        else:
            logger.warning(
                "⚠️ %s CSV 备注格式不达标（无法自动修复）: %s",
                alpha_id, reason,
            )


    current = get_alpha_description(sess, alpha_id)


    # 归一化比对（容忍首尾空白 + Windows/Unix 换行差异）
    def _norm(s):
        return (s or "").strip().replace("\r\n", "\n").replace("\r", "\n")


    if _norm(current) == _norm(expected_desc):
        logger.info(f"  ✔ {alpha_id} 备注已存在且与文件对应，跳过")
        return True


    if not current:
        logger.info(f"  📝 {alpha_id} 当前无备注，写入 PPA 备注")
    else:
        logger.info(f"  🔧 {alpha_id} 当前备注({len(current)}字符)与文件不符(可能已被顶掉)，覆盖修复")
    return set_alpha_description(sess, alpha_id, expected_desc)



# ============================================================
# 主入口
# ============================================================


if __name__ == "__main__":
    # ===== 命令行参数 =====
    parser = argparse.ArgumentParser(description="WorldQuant BRAIN Alpha 自动提交")
    parser.add_argument("--ppa", action="store_true",
                        help="开启 PPA 模式（自动校验/修复 alpha 备注）")
    parser.add_argument("--credentials", default=CREDENTIALS_FILE,
                        help="凭据 JSON 路径，默认读取 ~/brain.txt")
    args = parser.parse_args()
    ppa_mode = PPA_MODE or args.ppa


    # 1. 创建认证 session
    try:
        sess = create_session(args.credentials)
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        exit(1)


    # 2. 选择提交模式
    # 方式A：从 CSV 文件读取 alpha ID 列表
    CSV_FILE = "alpha_id.csv"
    if os.path.exists(CSV_FILE):
        alpha_ids = pd.read_csv(CSV_FILE, header=None)[0].tolist()
        logger.info(f"从 {CSV_FILE} 读取到 {len(alpha_ids)} 个 Alpha")
    else:
        # 方式B：手动指定（替换成你自己的 alpha_id）
        alpha_ids = [
            # "你的alpha_id_1",
            # "你的alpha_id_2",
        ]
        if not alpha_ids:
            logger.warning(
                "⚠️ 未找到 alpha_id.csv 且未手动指定 alpha_ids。\n"
                "请以下两种方式之一提供 Alpha ID：\n"
                "  1) 创建 alpha_id.csv 文件，每行一个 Alpha ID\n"
                "  2) 在代码中直接填入 alpha_ids 列表"
            )
            exit(0)


    # 2.5 读取 PPA 备注映射（仅 PPA 模式）
    desc_map = {}
    if ppa_mode:
        desc_map = load_ppa_descriptions(PPA_DESC_CSV)
        if not desc_map:
            logger.warning("⚠️ PPA 备注映射为空，将以普通模式提交")


    # 3. 批量提交
    successful, failed = submit_batch(
        sess, alpha_ids, pause_between=10,
        ppa_mode=ppa_mode, desc_map=desc_map,
    )


    # 4. 输出结果
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 提交结果汇总")
    logger.info(f"{'='*50}")
    logger.info(f"✅ 成功: {len(successful)} 个 → {successful}")
    logger.info(f"❌ 失败: {len(failed)} 个 → {failed}")
 
