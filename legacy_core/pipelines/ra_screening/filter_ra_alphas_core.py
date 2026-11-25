"""V5 shared helpers for RA screening and platform labeling.

The operation script owns the pipeline order; this module owns reusable
category lookup, alias, and snapshot behavior.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import logging
import os
import pickle
import re
import runpy
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import urllib3
import yaml

CORE_PARENT = Path(__file__).resolve().parents[2]
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.api.alpha_retrieval import COMPLETE, fetch_alpha_window
from Core.api.client import BrainClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 是否进入每日 00:00 循环；False 表示启动后只执行一次。
CONFIG_RUN_DAILY = True
# PC 查询成功后的间隔，单位：秒；0 表示不做无条件休息，只在异常时由内部逻辑退避。
CONFIG_PC_SUCCESS_DELAY_SECONDS = 3
# 拉取最近多少个北京时间自然日创建的未提交 Alpha；可直接修改。
CONFIG_DAYS_AGO = 30
# Alpha 列表请求遇到网络错误、429 或 5xx 时的最大重试次数。
CONFIG_FETCH_MAX_RETRIES = 10
# Alpha 列表重试的初始退避时间，单位：秒，后续按指数增加。
CONFIG_FETCH_RETRY_BASE_SECONDS = 3
# 登录遇到 TLS/网络错误、429 或 5xx 时的最大尝试次数。
CONFIG_AUTH_MAX_RETRIES = 5
# 登录重试的初始退避时间，单位：秒。
CONFIG_AUTH_RETRY_BASE_SECONDS = 2
# SC 本地计算的并发线程数；平台不稳定时应适当降低。
CONFIG_SC_MAX_WORKERS = 6
# PC 单次重连或空响应的最大等待时间，单位：秒。
CONFIG_PC_MAX_WAIT_SECONDS = 60
# 单个 Alpha 的 PC 远程查询最大尝试次数；超限后保留 ID，交给下一次断点运行。
CONFIG_PC_MAX_RETRIES = 3
# 单次运行最多处理的 PC 数量。
CONFIG_PC_MAX_COUNT = 400
# SC/PC 高相关阈值；严格大于该值才判定为高相关，等于 0.7 仍算通过。
CORRELATION_HIGH_THRESHOLD = 0.7
# PC 低值停止阈值；只有严格小于该值才计数。
CONFIG_PC_LOW_STOP_THRESHOLD = 0.6
# 达到多少个低 PC Alpha 后停止；0 表示关闭该停止条件。
CONFIG_PC_LOW_TARGET_COUNT = 100
# 平台别名/标签更新失败时的最大尝试次数，包含首次请求。
CONFIG_PLATFORM_UPDATE_MAX_RETRIES = 10
# 连续进行平台属性更新前的固定间隔，单位：秒，降低连续 PATCH 触发限流的概率。
CONFIG_PLATFORM_UPDATE_DELAY_SECONDS = 1
# 平台返回 429 后的运行级熔断时间，单位：秒；熔断期间只记录待处理，不重复请求。
CONFIG_PLATFORM_429_COOLDOWN_SECONDS = 300
# 阶段1第一次运行后，后续每次回查水位前重叠的时间，单位：小时，防止平台数据延迟。
CONFIG_FETCH_OVERLAP_HOURS = 24
# 阶段1列表查询的时间切片大小，单位：小时；避免 offset 超过平台 1000 条分页上限。
CONFIG_FETCH_SLICE_HOURS = 24
# SC 结果缓存每累计多少个结果写入一次，降低中断后的重复计算量。
CONFIG_SC_RESULT_CHECKPOINT_INTERVAL = 25
# SC 高相关时写入平台的终态标签。
SC_HIGH_TAG = "SC_IS_HIGHT"
# PC 高相关时写入平台的终态标签。
PC_HIGH_TAG = "PC_IS_HIGHT"
# SC、PC 都通过后写入平台的最终候选标签；后续改名只需修改这里。
USEFUL_TAG = "Useful"
# Useful 且至少一个关联 Pyramid 未点亮时写入的平台候选标签。
SUBMIT_TAG = "Submit"
# 带有这些标签的 Alpha 下次运行时跳过 SC/PC 刷新。
TERMINAL_HIGH_TAGS = {SC_HIGH_TAG, PC_HIGH_TAG}
# 存在 POWER_POOL_CORRELATION 时，允许按 RA 特例放行的 WARNING 名称。
RA_EXCEPTION_WARNING_NAMES = {
    "MATCHES_THEMES", "OSMOSIS_ALLOCATION", "DAILY_OSMOSIS_RANK", "CLUSTER_TEST",
}
# 可扩展的 WARNING 排除规则；新增规则只需追加 code/contains/reason，不修改 V5 流程。
CONFIG_WARNING_EXCLUSION_RULES = (
    {
        "code": "CONCENTRATED_WEIGHT",
        "check_name": "CONCENTRATED_WEIGHT",
        "contains": "Weight is too strongly concentrated or too few instruments are assigned weight.",
        "reason": "Weight is too strongly concentrated or too few instruments are assigned weight.",
    },
    {
        "code": "SHARPE_BELOW_CUTOFF",
        "check_name": "LOW_2Y_SHARPE",
        "contains": "below cutoff of",
        "reason": "Sharpe is below the platform cutoff.",
    },
    {
        "code": "IS_LADDER_SHARPE",
        "check_name": "IS_LADDER_SHARPE",
        "contains": "IS ladder Sharpe of",
        "reason": "IS ladder Sharpe is below the platform cutoff.",
    },
)


def find_sc_skill():
    spec = importlib.util.find_spec("cnhkmcp")
    if not spec or not spec.submodule_search_locations:
        logging.warning("当前 Python 环境未找到 cnhkmcp，SC 将标记 PENDING_SC_LIBRARY")
        return None
    scripts = Path(next(iter(spec.submodule_search_locations))) / "untracked" / "skills" / "brain-calculate-alpha-selfcorrQuick" / "scripts"
    if not scripts.is_dir():
        return None
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        import skill
        return skill
    except ImportError:
        return None


sc_skill = find_sc_skill()
_RUN_LOG_PATH = None
_RUN_ID = ""
_PLATFORM_RATE_LIMITED_UNTIL = 0.0
_LAST_PLATFORM_UPDATE_STATUS = "IDLE"
_CORE_CLIENT = None


def configure_run_logging(log_path):
    """配置本地运行日志；同一日期文件用 run_id 分隔，避免重复 handler。"""
    global _RUN_LOG_PATH, _RUN_ID
    reset_platform_update_state()
    _RUN_LOG_PATH = Path(log_path)
    _RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")
    handler = logging.FileHandler(_RUN_LOG_PATH, encoding="utf-8")
    handler._v5_log_handler = True
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    root = logging.getLogger()
    for old_handler in list(root.handlers):
        root.removeHandler(old_handler)
        old_handler.close()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging.info("========== V5 运行开始 | run_id=%s ==========", _RUN_ID)


def reset_platform_update_state():
    """清除本次运行的平台 429 熔断状态。"""
    global _PLATFORM_RATE_LIMITED_UNTIL, _LAST_PLATFORM_UPDATE_STATUS
    _PLATFORM_RATE_LIMITED_UNTIL = 0.0
    _LAST_PLATFORM_UPDATE_STATUS = "IDLE"


def platform_update_status():
    """返回最近一次平台属性更新状态，供 Excel 写入可追溯状态。"""
    return _LAST_PLATFORM_UPDATE_STATUS


def is_platform_rate_limited():
    return _PLATFORM_RATE_LIMITED_UNTIL > time.monotonic()


def _atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
        return default


def progress(message):
    """输出不会被 logging 配置吞掉的简短阶段进度。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    logging.info(message)


def run_stage_file(file_name):
    """Load one sibling operation file and call its run_job without linking versions."""
    stage_path = Path(__file__).resolve().parent / file_name
    namespace = runpy.run_path(str(stage_path), run_name=f"_{stage_path.stem}_stage")
    entry = namespace.get("run_from_file_settings", namespace["run_job"])
    return entry()


def resolve_config_path():
    """在脚本目录及向上最多三层中查找 Password/config.yaml。"""
    if os.environ.get("WQB_CONFIG"):
        configured = Path(os.environ["WQB_CONFIG"]).expanduser()
        if configured.is_file():
            return configured

    current_dir = Path(__file__).resolve().parent
    for level in range(4):
        config_path = current_dir / "Password" / "config.yaml"
        if config_path.is_file():
            return config_path
        current_dir = current_dir.parent
    raise FileNotFoundError("未找到凭据文件；请设置 WQB_CONFIG，或把配置放在仓库 Password/config.yaml。")


def get_session():
    try:
        with resolve_config_path().open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        if not isinstance(config, dict) or not config.get("username") or not config.get("password"):
            raise ValueError("配置必须包含非空 username 和 password")
        base_url = str(config.get("api_base_url", "https://api.worldquantbrain.com")).rstrip("/")
    except Exception as exc:
        logging.error("读取登录配置失败：%s", exc)
        return None

    for attempt in range(1, CONFIG_AUTH_MAX_RETRIES + 1):
        session = requests.Session()
        session.auth = (config["username"], config["password"])
        try:
            progress(f"[登录] 认证尝试 {attempt}/{CONFIG_AUTH_MAX_RETRIES}")
            response = session.post(f"{base_url}/authentication", timeout=30, verify=False)
            if response.status_code < 400:
                progress(f"[登录] 认证成功：尝试 {attempt}/{CONFIG_AUTH_MAX_RETRIES}")
                return session
            if response.status_code not in {429, 500, 502, 503, 504}:
                logging.error("登录不可重试：status=%s", response.status_code)
                session.close()
                return None
            error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            error = f"{type(exc).__name__}: {exc}"
        session.close()
        if attempt == CONFIG_AUTH_MAX_RETRIES:
            logging.error("登录重试耗尽：%s", error)
            return None
        delay = CONFIG_AUTH_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
        progress(f"[登录] 认证失败：{error}；{delay} 秒后重试")
        time.sleep(delay)
    return None


def get_core_client():
    """Return an authenticated project Core client without optional email packages."""
    global _CORE_CLIENT
    if _CORE_CLIENT is not None:
        return _CORE_CLIENT
    optimization_dir = Path(__file__).resolve().parent.parent
    if str(optimization_dir) not in sys.path:
        sys.path.insert(0, str(optimization_dir))
    from Core.api.client import BrainClient

    session = get_session()
    if session is None:
        raise RuntimeError("平台认证失败")
    _CORE_CLIENT = BrainClient(session)
    _CORE_CLIENT.mark_authenticated()
    return _CORE_CLIENT


def get_alpha_page_with_retry(session, url, context="AlphaPage"):
    """兼容V5的分页入口；传输重试继续复用Core BrainClient，不重写网络客户端。"""
    client = getattr(session, "_ra_alpha_page_client", None)
    if client is None:
        client = BrainClient(session)
        client.mark_authenticated()
        session._ra_alpha_page_client = client
    response = client.get(url, timeout=30)
    if response is None or response.status_code != 200:
        status = response.status_code if response is not None else "UNOBSERVED"
        progress(f"[RA][{context}] 分页=PENDING，HTTP={status}")
        return None
    return response


def get_platform_setting_options_core():
    """Read and normalize legal simulation settings through the project Core client."""
    response = get_core_client().options("/simulations")
    if response is None or response.status_code != 200:
        status = response.status_code if response is not None else "UNOBSERVED"
        raise RuntimeError(f"平台设置读取失败：HTTP {status}")
    data = response.json()
    settings = data.get("actions", {}).get("POST", {}).get("settings", {}).get("children", {})
    choices = {}
    for key, setting in settings.items():
        if setting.get("type") != "choice":
            continue
        label = str(setting.get("label") or key).strip().casefold()
        choices[label] = setting.get("choices", {})

    def by_label(*labels):
        for label in labels:
            if label.casefold() in choices:
                return choices[label.casefold()]
        return {}

    instrument_types = by_label("Instrument type", "instrumentType")
    regions = by_label("Region").get("instrumentType", {})
    delays = by_label("Delay").get("instrumentType", {})
    universes = by_label("Universe").get("instrumentType", {})
    neutralizations = by_label("Neutralization").get("instrumentType", {})
    rows = []
    for instrument in instrument_types:
        instrument_type = instrument.get("value")
        for region in regions.get(instrument_type, []):
            region_value = region.get("value")
            for delay in delays.get(instrument_type, {}).get("region", {}).get(region_value, []):
                rows.append({
                    "InstrumentType": instrument_type,
                    "Region": region_value,
                    "Delay": delay.get("value"),
                    "Universe": [
                        item.get("value") for item in
                        universes.get(instrument_type, {}).get("region", {}).get(region_value, [])
                        if item.get("value")
                    ],
                    "Neutralization": [
                        item.get("value") for item in
                        neutralizations.get(instrument_type, {}).get("region", {}).get(region_value, [])
                        if item.get("value")
                    ],
                })
    if not rows:
        raise RuntimeError("平台设置响应结构不完整，没有可用的 Region/Delay 组合")
    return {"instrument_options": rows, "total_combinations": len(rows)}


def create_multi_simulation_core(alpha_expressions, **settings):
    """Create one 2-8 expression multi-simulation and return observed child details."""
    if not 2 <= len(alpha_expressions) <= 8:
        return {"error": "Multi-simulation requires 2-8 expressions"}
    from Core.api.sim_api import post_multi_simulation, poll_simulation_progress

    client = get_core_client()
    payloads = []
    individual = settings.get("individual_settings")
    if individual is not None and (not isinstance(individual, list) or len(individual) != len(alpha_expressions)
                                   or any(not isinstance(item, dict) for item in individual)):
        return {"error": "LOCAL_INVALID_INDIVIDUAL_SETTINGS"}
    for index, expression in enumerate(alpha_expressions):
        payloads.append({
            "type": "REGULAR",
            "settings": {
                "instrumentType": settings.get("instrument_type", "EQUITY"),
                "region": settings.get("region", "USA"),
                "universe": settings.get("universe", "TOP3000"),
                "delay": settings.get("delay", 1),
                "decay": settings.get("decay", 0),
                "neutralization": settings.get("neutralization", "NONE"),
                "truncation": settings.get("truncation", 0),
                "pasteurization": settings.get("pasteurization", "ON"),
                "unitHandling": settings.get("unit_handling", "VERIFY"),
                "nanHandling": settings.get("nan_handling", "OFF"),
                "language": settings.get("language", "FASTEXPR"),
                "visualization": settings.get("visualization", False),
                "testPeriod": settings.get("test_period", "P0Y0M"),
                "maxTrade": settings.get("max_trade", "OFF"),
            },
            "regular": expression,
        })
        if individual is not None:
            keys = {"region", "universe", "delay", "decay", "neutralization"}
            if set(individual[index]) - keys:
                return {"error": "LOCAL_UNAPPROVED_INDIVIDUAL_SETTING"}
            payloads[-1]["settings"].update(individual[index])
    metadata = post_multi_simulation(client, payloads, return_metadata=True)
    if metadata.get("status_code") == 429:
        return {"error": "Failed to create multisimulation. Status: 429", "status_code": 429}
    location = metadata.get("location")
    if not location:
        status = metadata.get("status_code") or "UNOBSERVED"
        return {"error": f"Multi-simulation result unobserved: HTTP {status}"}

    if settings.get("defer_polling"):
        # 每个批次先持久化Location，由常驻RA流程冷却后只读恢复，避免长轮询卡死。
        return {"error": "PENDING_MULTI_SIMULATION", "multisimulation_location": location,
                "status_code": metadata.get("status_code")}

    children = []
    for _ in range(200):
        response = client.get(location)
        if response is not None and response.status_code == 200:
            parent = response.json()
            children = parent.get("children") or []
            if children:
                break
            retry_after = response.headers.get("Retry-After", 5)
        else:
            retry_after = 5
        try:
            time.sleep(max(0.0, float(retry_after)))
        except (TypeError, ValueError):
            time.sleep(5)
    if not children:
        return {"error": "Multi-simulation children remain unobserved; POST was not resent", "multisimulation_location": location}

    alpha_results = []
    for child in children:
        result = poll_simulation_progress(client, child, timeout=900)
        alpha_id = str(result.get("alpha") or "").strip() if isinstance(result, dict) else ""
        if not alpha_id:
            alpha_results.append({"location": str(child), "error": "Simulation result has no Alpha ID"})
            continue
        response = client.get(f"/alphas/{alpha_id}")
        if response is None or response.status_code != 200:
            status = response.status_code if response is not None else "UNOBSERVED"
            alpha_results.append({
                "alpha_id": alpha_id, "location": str(child),
                "error": f"Failed to get alpha details: {status}",
            })
            continue
        alpha_results.append({"alpha_id": alpha_id, "location": str(child), "details": response.json()})
    return {
        "success": True,
        "multisimulation_location": location,
        "total_requested": len(alpha_expressions),
        "total_created": len(alpha_results),
        "alpha_results": alpha_results,
    }


def get_alpha_details_core(client, alpha_id):
    """兼容广州旧 Core 的只读详情入口；保持现有 RA 客户端和错误状态。"""
    response = client.get(f"/alphas/{alpha_id}")
    if response is None or response.status_code != 200:
        return None
    data = response.json()
    return data if isinstance(data, dict) else None


def recover_multi_simulation_core(location):
    """一个已持久化父任务只读对账一次；不会POST或触发属性修改。"""
    client = get_core_client()
    response = client.get(location)
    parent = response.json() if response is not None and response.status_code == 200 else None
    children = parent.get("children") if isinstance(parent, dict) else None
    if not isinstance(children, list) or len(children) != 8 or any(not isinstance(child, str) for child in children) or len(set(children)) != 8:
        return {"error": "PENDING_CHILDREN", "multisimulation_location": location}
    results = []
    for child in children:
        child_url = child if child.startswith(("http://", "https://", "/")) else f"/simulations/{child}"
        response = client.get(child_url)
        progress = response.json() if response is not None and response.status_code == 200 else {}
        progress = progress if isinstance(progress, dict) else {}
        alpha_id = progress.get("alpha")
        details = get_alpha_details_core(client, alpha_id) if alpha_id else None
        results.append({"alpha_id": alpha_id, "details": details,
                        "error": None if details else "PENDING_ALPHA_DETAILS", "platform_status": progress.get("status")})
    return {"success": True, "alpha_results": results, "multisimulation_location": location}


def check_single_dataset_batch(expressions, region, universe, delay):
    """检测设置回测的真实字段范围；不能因来源Useful就忽略单数据集约束。"""
    from Core.sim.alpha_manager import extract_expression_field_ids
    from Core.api.data_api import get_datafield_metadata
    from Core.factor.templates.admin_distributed import operator_count
    import re

    if len(expressions) != 8:
        return {"status": "LOCAL_REJECTED", "reason": "不是完整八条"}
    fields = set()
    for expression in expressions:
        if operator_count(expression) >= 6 or re.search(r"\b(trade_when|add|multiply)\s*\(", expression):
            return {"status": "LOCAL_REJECTED", "reason": "总算子>=6或禁用算子"}
        variables = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)", expression))
        fields.update(set(extract_expression_field_ids(expression)) - variables)
    if not 1 <= len(fields) <= 2:
        return {"status": "LOCAL_REJECTED", "field_ids": sorted(fields), "reason": "真实字段并集不在1–2个范围"}
    response = get_datafield_metadata(get_core_client(), sorted(fields), "EQUITY", region, universe, delay, read_only=True)
    if response.get("status") != "OK":
        return {"status": "PENDING", "reason": "实时字段元数据不完整"}
    datasets = set()
    for field_id in fields:
        field = response.get("metadata", {}).get(field_id)
        if not isinstance(field, dict):
            return {"status": "PENDING", "reason": "字段详情缺失"}
        dataset = field.get("dataset")
        datasets.add(dataset.get("id") if isinstance(dataset, dict) else field.get("dataset_id"))
    if len(datasets) != 1 or next(iter(datasets)) in {None, "", "UNKNOWN"}:
        return {"status": "LOCAL_REJECTED" if len(datasets) > 1 else "PENDING", "reason": "跨数据集或无法确认数据集", "field_ids": sorted(fields)}
    registry = next((parent / "总结" / "优化复盘_20260802" / "操作符_字段黑名单登记表.md"
                     for parent in Path(__file__).resolve().parents
                     if (parent / "总结" / "优化复盘_20260802" / "操作符_字段黑名单登记表.md").is_file()), None)
    if registry is None:
        return {"status": "PENDING", "reason": "缺少唯一字段淘汰登记表"}
    for line in registry.read_text(encoding="utf-8-sig").splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not re.match(r"(?:DS|DATASET|FLD|FIELD)[-_]", cells[0]):
            continue
        if re.fullmatch(r"(?:FIELD_VERDICT\s*=\s*)?GARBAGE_CANDIDATE|(?:DATASET_VERDICT\s*=\s*)?STOP_DATASET", cells[2]):
            registered_ids = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", cells[1]))
            if registered_ids & (fields | datasets):
                return {"status": "LOCAL_REJECTED", "reason": f"正式淘汰登记 {cells[0]}：{cells[2]}", "evidence": cells[3]}
    return {"status": "PASS", "dataset_id": next(iter(datasets)), "field_ids": sorted(fields)}


def get_correlation_payload_core(alpha_id, correlation_type):
    """Read a correlation payload; missing/empty data remains observable as PENDING."""
    endpoint = "self" if correlation_type == "self" else "prod"
    response = get_core_client().get(f"/alphas/{alpha_id}/correlations/{endpoint}", timeout=30)
    if response is None or response.status_code != 200:
        return {}
    try:
        payload = response.json()
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def set_alpha_properties_core(alpha_id, name, tags):
    """Update V6 child properties through the existing bounded V5 updater."""
    ok = set_alpha_properties(get_core_client().session, alpha_id, name=name, tags=list(tags))
    status = platform_update_status()
    if ok:
        return {"id": alpha_id, "status": status}
    status_code = 429 if status in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"} else None
    return {"error": status, "status_code": status_code}


def _correlation_payload_value(payload, *keys):
    if not isinstance(payload, dict):
        return None
    for source in (payload, payload.get("schema")):
        if not isinstance(source, dict):
            continue
        for key in keys:
            try:
                value = source.get(key)
                if pd.notna(value):
                    return float(value)
            except (TypeError, ValueError):
                continue
    return None


def self_correlation_value(payload):
    return _correlation_payload_value(payload, "max", "selfCorrelation", "correlation", "value")


def production_correlation_values(payload):
    return (
        _correlation_payload_value(payload, "max", "prodCorrelationMax"),
        _correlation_payload_value(payload, "min", "prodCorrelationMin"),
    )


def set_alpha_properties(session, alpha_id, name=None, tags=None):
    global _PLATFORM_RATE_LIMITED_UNTIL, _LAST_PLATFORM_UPDATE_STATUS
    payload = {key: value for key, value in {"name": name, "tags": tags}.items() if value is not None}
    if not payload:
        _LAST_PLATFORM_UPDATE_STATUS = "SKIPPED_EMPTY"
        return True
    if is_platform_rate_limited():
        _LAST_PLATFORM_UPDATE_STATUS = "SKIPPED_RATE_LIMIT"
        progress(f"[平台] {alpha_id} 处于 429 熔断期，跳过请求并保留待处理")
        return False
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
    progress(f"[平台] {alpha_id} 更新前等待 {CONFIG_PLATFORM_UPDATE_DELAY_SECONDS:.1f} 秒")
    time.sleep(CONFIG_PLATFORM_UPDATE_DELAY_SECONDS)
    for attempt in range(1, CONFIG_PLATFORM_UPDATE_MAX_RETRIES + 1):
        try:
            progress(f"[平台] {alpha_id} 属性更新尝试 {attempt}/{CONFIG_PLATFORM_UPDATE_MAX_RETRIES}")
            response = session.patch(url, json=payload, timeout=30, verify=False)
            if response.status_code < 400:
                _LAST_PLATFORM_UPDATE_STATUS = "SYNCED"
                return True
            logging.warning("Alpha %s 平台属性更新失败：status=%s，第 %s/%s 次", alpha_id, response.status_code, attempt, CONFIG_PLATFORM_UPDATE_MAX_RETRIES)
            if attempt == CONFIG_PLATFORM_UPDATE_MAX_RETRIES:
                if response.status_code == 429:
                    _PLATFORM_RATE_LIMITED_UNTIL = time.monotonic() + CONFIG_PLATFORM_429_COOLDOWN_SECONDS
                    _LAST_PLATFORM_UPDATE_STATUS = "RATE_LIMITED"
                    progress(f"[平台] {alpha_id} 触发 429，开启 {CONFIG_PLATFORM_429_COOLDOWN_SECONDS} 秒运行级熔断")
                else:
                    _LAST_PLATFORM_UPDATE_STATUS = "FAILED"
                return False
        except requests.RequestException as exc:
            logging.warning("Alpha %s 平台属性更新网络异常，第 %s/%s 次：%s", alpha_id, attempt, CONFIG_PLATFORM_UPDATE_MAX_RETRIES, exc)
            if attempt == CONFIG_PLATFORM_UPDATE_MAX_RETRIES:
                logging.error("Alpha %s 平台属性更新重试耗尽", alpha_id)
                _LAST_PLATFORM_UPDATE_STATUS = "FAILED"
                return False
        time.sleep(min(2 ** (attempt - 1), 10))
    return False


def save_excel(df, output_path):
    df.to_excel(output_path, index=False, engine="openpyxl")


def classify_ra_alpha(alpha):
    checks = alpha.get("is", {}).get("checks", []) or []
    power_pool = any(str(check.get("name", "")).strip().upper() == "POWER_POOL_CORRELATION" for check in checks)
    if not power_pool:
        return True, "无 POWER_POOL_CORRELATION 检查"
    warnings = [check for check in checks if str(check.get("result", "")).strip().upper() == "WARNING"]
    names = {str(check.get("name", "")).strip().upper() for check in warnings}
    return (True, "RA WARNING 特例") if 1 <= len(warnings) <= 3 and names.issubset(RA_EXCEPTION_WARNING_NAMES) else (False, "PPA")


def tag_names(tags):
    names = []
    for tag in tags or []:
        name = tag if isinstance(tag, str) else (tag.get("name") or tag.get("id") if isinstance(tag, dict) else None)
        if name and str(name).strip():
            names.append(str(name).strip())
    return names


def merge_tag(tags, new_tag, remove_tags=None):
    removed = {str(tag).casefold() for tag in (remove_tags or [])}
    return list(dict.fromkeys([tag for tag in tag_names(tags) if tag.casefold() not in removed] + [new_tag]))


def terminal_high_tag(tags):
    names = set(tag_names(tags))
    return SC_HIGH_TAG if SC_HIGH_TAG in names else PC_HIGH_TAG if PC_HIGH_TAG in names else None


def find_warning_exclusions(alpha):
    """返回命中的可配置 WARNING 排除规则，未命中时返回空列表。"""
    checks = alpha.get("is", {}).get("checks", []) or {}
    if not isinstance(checks, list):
        return []
    matches = []
    for check in checks:
        if not isinstance(check, dict) or str(check.get("result", "")).strip().upper() != "WARNING":
            continue
        searchable = json.dumps(check, ensure_ascii=False, sort_keys=True).casefold()
        check_name = str(check.get("name", "")).strip().casefold()
        named_matches = []
        text_matches = []
        for rule in CONFIG_WARNING_EXCLUSION_RULES:
            contains = str(rule.get("contains", "")).strip().casefold()
            configured_name = rule.get("check_name") or rule.get("name")
            names = configured_name if isinstance(configured_name, (list, tuple, set)) else [configured_name]
            name_matches = any(
                check_name == str(name).strip().casefold()
                for name in names
                if str(name or "").strip()
            )
            if name_matches or (contains and contains in searchable):
                match = {
                    "code": rule.get("code", "UNNAMED_WARNING_RULE"),
                    "reason": rule.get("reason", rule.get("contains", "")),
                    "check": check,
                }
                (named_matches if name_matches else text_matches).append(match)
        matches.extend(named_matches or text_matches)
    return matches


def remove_useful_tag_if_present(session, alpha, reason):
    """排除 Alpha 时移除 Useful/Submit，保留其它标签。"""
    alpha_id = str(alpha.get("id") or "").strip()
    tags = tag_names(alpha.get("tags"))
    useful_present = any(tag.casefold() == USEFUL_TAG.casefold() for tag in tags)
    if not alpha_id:
        progress(f"[V5][ExcludedTag] 无有效 Alpha ID：原因={reason}，Useful={'YES' if useful_present else 'NO'}")
        return False
    if not useful_present:
        progress(f"[V5][ExcludedTag] {alpha_id}：原因={reason}，Useful=NO，无需更新")
        return True
    removed = {USEFUL_TAG.casefold(), SUBMIT_TAG.casefold()}
    new_tags = [tag for tag in tags if tag.casefold() not in removed]
    progress(f"[V5][ExcludedTag] {alpha_id}：原因={reason}，Useful=YES，开始移除")
    updated = set_alpha_properties(session, alpha_id, tags=new_tags)
    progress(
        f"[V5][ExcludedTag] {alpha_id}：Useful 移除{'成功' if updated else '失败，保留待重试'}"
    )
    return updated


def is_high_correlation(value):
    return pd.notna(value) and abs(float(value)) > CORRELATION_HIGH_THRESHOLD


def is_high_pc(max_value, min_value):
    """PC 有两个值；任一绝对值超过阈值即可确认高 PC。"""
    return is_high_correlation(max_value) or is_high_correlation(min_value)


def is_complete_low_pc(max_value, min_value):
    """只有两个 PC 值都存在且都未超过绝对值阈值，才算低 PC 完成。"""
    return (
        pd.notna(max_value)
        and pd.notna(min_value)
        and is_correlation_pass(max_value)
        and is_correlation_pass(min_value)
    )


def high_alias(kind, value):
    if kind not in {"SC", "PC"}:
        raise ValueError(f"未知相关性类型: {kind}")
    formatted = abs(float(value)) if kind == "PC" else float(value)
    return f"{kind} {formatted:.3f}"


def pc_alias_value(max_value, min_value):
    """PC 原始值保留在 Excel；别名只保存两个值中的最大绝对值。"""
    values = [
        abs(float(value))
        for value in (max_value, min_value)
        if pd.notna(value)
    ]
    return max(values) if values else None


def partial_alias(existing_name, kind, value):
    """只更新一个相关性值，保留别名中已经存在的另一项。"""
    if kind not in {"SC", "PC"}:
        raise ValueError(f"未知相关性类型: {kind}")
    values = {
        "SC": parse_alias_value(existing_name, "SC"),
        "PC": parse_alias_value(existing_name, "PC"),
    }
    values[kind] = float(value)
    return " ".join(
        f"{name} {(abs(values[name]) if name == 'PC' else values[name]):.3f}"
        for name in ("SC", "PC")
        if values[name] is not None
    )


def normal_alias(sc_value, pc_value):
    return f"SC {float(sc_value):.3f} PC {abs(float(pc_value)):.3f}"


def parse_alias_value(name, kind):
    if not name:
        return None
    match = re.search(rf"(?:^|\s){re.escape(kind)}\s*=?\s*(-?\d+(?:\.\d+)?)", str(name), re.IGNORECASE)
    return float(match.group(1)) if match else None


def raw_alpha_id(value):
    if isinstance(value, str) and value.startswith("=HYPERLINK"):
        match = re.search(r'/alpha/([^"/]+)', value)
        return match.group(1) if match else value
    return value


def load_excel_history(output_path):
    if not output_path.is_file():
        return {}
    try:
        old_df = pd.read_excel(output_path, engine="openpyxl")
    except Exception as exc:
        logging.warning("读取当天 Excel 断点失败：%s", exc)
        return {}
    history = {}
    for _, row in old_df.iterrows():
        alpha_id = row.get("alpha_id_raw") if pd.notna(row.get("alpha_id_raw")) else raw_alpha_id(row.get("alpha_id"))
        if alpha_id and alpha_id not in history:
            history[alpha_id] = {
                "self_correlation": row.get("self_correlation"),
                "prod_correlation_max": row.get("prod_correlation_max"),
                "prod_correlation_min": row.get("prod_correlation_min"),
                "Platform_Name": row.get("Platform_Name"),
                "Processing_Status": row.get("Processing_Status"),
                "PC_Status": row.get("PC_Status"),
                "Platform_Update_Status": row.get("Platform_Update_Status"),
            }
    return history


def save_snapshot(df, output_path):
    snapshot = df.copy()
    # 空结果/分页失败占位行也必须包含下一阶段依赖的表头；标签未知保持空。
    for column in ("Expression", "Region", "Universe", "Delay", "Sharpe", "Fitness", "Margin", "Platform_Tags"):
        if column not in snapshot:
            snapshot[column] = "" if column == "Platform_Tags" else None
    internal = [column for column in snapshot.columns if str(column).startswith("_")]
    if internal:
        snapshot = snapshot.drop(columns=internal)
    if "alpha_id" in snapshot.columns:
        if "alpha_id_raw" not in snapshot.columns:
            snapshot.insert(1, "alpha_id_raw", snapshot["alpha_id"])
        snapshot["alpha_id"] = snapshot["alpha_id"].apply(
            lambda value: f'=HYPERLINK("https://platform.worldquantbrain.com/alpha/{value}", "{value}")'
        )
    save_excel(snapshot, output_path)


def _parse_utc(value):
    if not value:
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    return None if pd.isna(parsed) else parsed.to_pydatetime()


def beijing_date_window_utc(now=None, days=None):
    """返回最近 N 个北京时间自然日对应的 UTC 半开区间。"""
    beijing = ZoneInfo("Asia/Shanghai")
    current = now or datetime.now(beijing)
    if current.tzinfo is None:
        current = current.replace(tzinfo=beijing)
    current = current.astimezone(beijing)
    end = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days or CONFIG_DAYS_AGO)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def _keep_recent_alpha_records(records, lower_bound):
    kept = {}
    for alpha in records:
        if not isinstance(alpha, dict) or not alpha.get("id"):
            continue
        created = _parse_utc(alpha.get("dateCreated"))
        if created is None or created >= lower_bound:
            kept[str(alpha["id"])] = alpha
    return kept


def _build_fetch_slices(query_start, query_end):
    slices = []
    cursor = query_start
    step = timedelta(hours=CONFIG_FETCH_SLICE_HOURS)
    while cursor < query_end:
        slice_end = min(cursor + step, query_end)
        slices.append((cursor, slice_end))
        cursor = slice_end
    return slices


def fetch_recent_alphas(session, checkpoint_path=None):
    """按水位增量读取 Alpha；分页、切片和断点由 Core 统一处理。"""
    checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
    filters = ["is.sharpe>=1.6", "is.fitness>=1.0", "is.margin>0.0005"]
    signature = {
        "days": CONFIG_DAYS_AGO,
        "filters": filters,
        "status": "UNSUBMITTED",
        "hidden": False,
        "overlap_hours": CONFIG_FETCH_OVERLAP_HOURS,
    }
    state = _load_json(checkpoint_path, {}) if checkpoint_path else {}
    if state.get("version") != 3 or state.get("signature") != signature:
        previous_records = state.get("records", {}) if isinstance(state.get("records"), dict) else {}
        state = {
            "version": 3,
            "signature": signature,
            "records": previous_records,
            "watermark_utc": state.get("watermark_utc") if state.get("signature") == signature else None,
        }

    cached_records = state.get("records", {})
    if not isinstance(cached_records, dict):
        cached_records = {}
    lower_bound, window_end = beijing_date_window_utc()
    watermark = _parse_utc(state.get("watermark_utc"))
    query_start = (
        max(lower_bound, watermark - timedelta(hours=CONFIG_FETCH_OVERLAP_HOURS))
        if watermark else lower_bound
    )
    query_end = window_end
    if query_start >= query_end:
        query_start = lower_bound
    progress(
        f"[Core][阶段1] 增量区间：{query_start.isoformat()} -> {query_end.isoformat()}，"
        f"已有缓存 {len(cached_records)} 条"
    )
    state.pop("active_query", None)
    if checkpoint_path:
        _atomic_write_json(checkpoint_path, state)

    client = session if isinstance(session, BrainClient) else BrainClient(session)
    client.mark_authenticated()
    result = fetch_alpha_window(
        client,
        query_start,
        query_end,
        query=["status=UNSUBMITTED", *filters, "hidden=false"],
        page_size=100,
        slice_size=timedelta(hours=CONFIG_FETCH_SLICE_HOURS),
        dense_window_threshold=500,
        checkpoint_path=checkpoint_path,
        checkpoint_namespace="ra_alpha_fetch",
        refresh_completed=True,
    )
    failures = [item["context"] for item in result.failures]
    merged = dict(cached_records)
    merged.update(_keep_recent_alpha_records(result.records, lower_bound))
    merged = _keep_recent_alpha_records(merged.values(), lower_bound)
    if checkpoint_path:
        saved = _load_json(checkpoint_path, {})
        if isinstance(saved, dict):
            state = saved
    state["records"] = merged
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    if result.status == COMPLETE:
        state["watermark_utc"] = query_end.isoformat()
        progress(f"[Core][阶段1] 增量读取完成：本地保留 {len(merged)} 条 Alpha")
    else:
        progress(f"[Core][阶段1] 部分完成：本地保留 {len(merged)} 条，待重试分页 {len(failures)} 个")
    if checkpoint_path:
        _atomic_write_json(checkpoint_path, state)
    progress(f"[Core][阶段1] 拉取完成：{len(merged)} 条，失败分页 {len(failures)} 个")
    return list(merged.values()), failures


def _load_sc_result_cache(cache_path, alpha_df):
    raw_sc_cache = _load_json(cache_path, {})
    cached_sc = raw_sc_cache.get("results", {}) if raw_sc_cache.get("version") == 1 else {}
    if not isinstance(cached_sc, dict):
        return {}
    results = {}
    for row in alpha_df[["alpha_id", "Region"]].itertuples(index=False):
        cached = cached_sc.get(row.alpha_id)
        if not isinstance(cached, dict) or str(cached.get("region")) != str(row.Region):
            continue
        try:
            results[row.alpha_id] = float(cached["value"])
        except (KeyError, TypeError, ValueError):
            continue
    return results


def _cached_sc_alpha_ids(data_path):
    """读取基础 OS Alpha 缓存的 ID，用于判断增量下载是否真的带来新数据。"""
    try:
        with (Path(data_path) / "os_alpha_ids.pickle").open("rb") as cache_file:
            grouped_ids = pickle.load(cache_file)
    except (FileNotFoundError, EOFError, pickle.PickleError, TypeError, ValueError):
        return set()
    if not isinstance(grouped_ids, dict):
        return set()
    return {
        str(alpha_id)
        for alpha_ids in grouped_ids.values()
        for alpha_id in (alpha_ids if isinstance(alpha_ids, (list, tuple, set)) else [])
        if alpha_id
    }


def calculate_self_correlation_for_alphas_optimized(
    session, data_path, alpha_df, tag="SelfCorr", max_workers=10, known_sc_results=None
):
    """使用调用方已有的 Region，避免逐个请求 Alpha 详情确认区域。"""
    if sc_skill is None or alpha_df.empty:
        return alpha_df.copy()

    started = time.monotonic()
    sc_result_cache_path = Path(data_path) / "sc_results.json"
    cached_input_results = _load_sc_result_cache(sc_result_cache_path, alpha_df)
    progress("[SC] 开始准备自相关性基础数据")
    cached_base_ids = _cached_sc_alpha_ids(data_path)
    downloaded = sc_skill.download_data(session, data_path, flag_increment=True)
    downloaded_base_ids = downloaded[0] if isinstance(downloaded, tuple) and downloaded else None
    if isinstance(downloaded_base_ids, dict):
        current_base_ids = {
            str(alpha_id)
            for alpha_ids in downloaded_base_ids.values()
            for alpha_id in (alpha_ids if isinstance(alpha_ids, (list, tuple, set)) else [])
            if alpha_id
        }
    else:
        current_base_ids = _cached_sc_alpha_ids(data_path)
    new_base_ids = current_base_ids - cached_base_ids
    base_data_changed = bool(new_base_ids)
    if base_data_changed:
        progress(f"[SC] 基础数据检测到新增 Alpha：{len(new_base_ids)} 个，仅强制重算本批 SC；PC 缓存保留")
        cached_input_results = {}
    else:
        progress("[SC] 基础数据没有新增 Alpha，可复用已有 SC 结果")
    progress(f"[SC] 基础数据下载/缓存完成，耗时 {format_duration(time.monotonic() - started)}")

    if not base_data_changed and isinstance(known_sc_results, dict):
        valid_ids = set(alpha_df["alpha_id"].astype(str))
        for alpha_id, value in known_sc_results.items():
            if str(alpha_id) not in valid_ids or pd.isna(value):
                continue
            try:
                cached_input_results[str(alpha_id)] = float(value)
            except (TypeError, ValueError):
                continue

    if not base_data_changed and len(cached_input_results) == len(alpha_df):
        output = alpha_df.copy()
        output["self_correlation"] = output["alpha_id"].map(cached_input_results)
        output.attrs["base_data_changed"] = False
        progress(f"[SC] 结果缓存全部命中 {len(output)} 个，跳过 SC 计算和目标 PnL 加载")
        return output

    load_started = time.monotonic()
    os_alpha_ids, os_alpha_rets = sc_skill.load_data(data_path, tag=tag)
    progress(f"[SC] 本地缓存加载完成，耗时 {format_duration(time.monotonic() - load_started)}")
    if os_alpha_rets.empty:
        progress("[SC] 缓存没有足够的 OS Alpha 数据，结果保留为 PENDING")
        output = alpha_df.copy()
        output.attrs["base_data_changed"] = base_data_changed
        return output

    regions = {str(region) for region in alpha_df["Region"].dropna().unique()}
    missing_regions = sorted(regions - set(os_alpha_ids))
    if missing_regions:
        progress(f"[SC] 缓存缺少区域 {missing_regions}，结果保留为 PENDING")
        output = alpha_df.copy()
        output.attrs["base_data_changed"] = base_data_changed
        return output

    alpha_records = [
        {"id": row.alpha_id, "settings": {"region": row.Region}}
        for row in alpha_df[["alpha_id", "Region"]].itertuples(index=False)
    ]
    pnl_started = time.monotonic()
    target_pnl_cache = Path(data_path) / "target_alpha_pnls.pickle"
    try:
        with target_pnl_cache.open("rb") as cache_file:
            target_pnls = pickle.load(cache_file)
        if not isinstance(target_pnls, pd.DataFrame):
            raise ValueError("目标 PnL 缓存不是 DataFrame")
        progress(f"[SC] 已加载本地目标 PnL 缓存：{len(target_pnls.columns)} 个 Alpha")
    except (FileNotFoundError, EOFError, pickle.PickleError, ValueError, TypeError):
        target_pnls = pd.DataFrame()
        progress("[SC] 没有可用的目标 PnL 缓存")

    missing_records = [record for record in alpha_records if record["id"] not in target_pnls.columns]
    progress(f"[SC] 目标 PnL：缓存命中 {len(alpha_records) - len(missing_records)} 个，需远程获取 {len(missing_records)} 个")
    try:
        if missing_records:
            _, target_pnls = sc_skill.get_alpha_pnls(
                # 传 None 让技能内部创建 defaultdict(list)，否则 GLB/EUR 等新 Region
                # 会在空 dict 上 append 时触发 KeyError。
                session, missing_records, alpha_pnls=target_pnls, alpha_ids=None
            )
            with target_pnl_cache.open("wb") as cache_file:
                pickle.dump(target_pnls, cache_file, pickle.HIGHEST_PROTOCOL)
            progress(f"[SC] 目标 PnL 已保存到本地：{target_pnl_cache.name}")
    except Exception as exc:
        logging.exception("[SC] 目标 Alpha PnL 加载失败：%s", exc)
        progress(f"[SC] 目标 Alpha PnL 加载失败：{str(exc)[:120]}")
        progress("[SC] 目标 Alpha PnL 加载失败，结果保留为 PENDING")
        output = alpha_df.copy()
        output.attrs["base_data_changed"] = base_data_changed
        return output
    progress(f"[SC] 目标 Alpha PnL 准备完成，耗时 {format_duration(time.monotonic() - pnl_started)}")

    raw_sc_cache = _load_json(sc_result_cache_path, {})
    cached_sc = (
        raw_sc_cache.get("results", {})
        if not base_data_changed and raw_sc_cache.get("version") == 1
        else {}
    )
    if not isinstance(cached_sc, dict):
        cached_sc = {}
    results = dict(cached_input_results)
    record_by_id = {record["id"]: record for record in alpha_records}
    for alpha_id, cached in cached_sc.items():
        record = record_by_id.get(alpha_id)
        if not record or not isinstance(cached, dict):
            continue
        if str(cached.get("region")) != str(record["settings"].get("region")):
            continue
        try:
            results[alpha_id] = float(cached["value"])
        except (KeyError, TypeError, ValueError):
            continue
    missing_records = [record for record in alpha_records if record["id"] not in results]
    progress(f"[SC] 结果缓存命中 {len(results)} 个，需本地计算 {len(missing_records)} 个")

    def calculate(record):
        alpha_id = record["id"]
        try:
            value = sc_skill.calc_self_corr(
                session=session,
                alpha_id=alpha_id,
                os_alpha_rets=os_alpha_rets,
                os_alpha_ids=os_alpha_ids,
                alpha_result=record,
                alpha_pnls=target_pnls,
            )
            return alpha_id, value, None
        except Exception as exc:
            return alpha_id, None, exc

    progress(f"[SC] 开始计算 {len(missing_records)} 个 Alpha，线程数 {max_workers}")
    completed = 0
    total = len(missing_records)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(calculate, record) for record in missing_records]
        for future in as_completed(futures):
            alpha_id, value, error = future.result()
            completed += 1
            if error is not None:
                logging.warning("[SC] Alpha %s 计算失败：%s", alpha_id, error)
                progress(f"[SC] {completed}/{total} {alpha_id} 完成：FAILED，{str(error)[:120]}")
            elif value is not None:
                results[alpha_id] = value
                cached_sc[alpha_id] = {
                    "value": float(value),
                    "region": record_by_id[alpha_id]["settings"].get("region"),
                }
                progress(f"[SC] {completed}/{total} {alpha_id} 完成：SC={float(value):.6f}")
            else:
                progress(f"[SC] {completed}/{total} {alpha_id} 完成：PENDING")
            if sc_result_cache_path and completed % CONFIG_SC_RESULT_CHECKPOINT_INTERVAL == 0:
                _atomic_write_json(sc_result_cache_path, {"version": 1, "results": cached_sc})
                progress(f"[SC] 已保存结果中间文件：{sc_result_cache_path.name}，累计 {len(cached_sc)} 个")

    _atomic_write_json(sc_result_cache_path, {"version": 1, "results": cached_sc})
    progress(f"[SC] 结果缓存已保存：{sc_result_cache_path.name}，共 {len(cached_sc)} 个")

    output = alpha_df.copy()
    output["self_correlation"] = output["alpha_id"].map(results)
    output.attrs["base_data_changed"] = base_data_changed
    progress(f"[SC] 计算完成：成功 {len(results)}/{len(alpha_records)}，总耗时 {format_duration(time.monotonic() - started)}")
    return output


def build_dataframe(alphas, history):
    records = []
    for alpha in alphas:
        alpha_id = alpha.get("id")
        old = history.get(alpha_id, {})
        history_name = old.get("Platform_Name")
        name = (
            history_name
            if pd.notna(history_name) and str(history_name).strip()
            else alpha.get("name") or ""
        )
        tags = tag_names(alpha.get("tags"))
        sc_value = old.get("self_correlation")
        pc_max = old.get("prod_correlation_max")
        pc_min = old.get("prod_correlation_min")
        alias_sc = parse_alias_value(name, "SC")
        alias_pc = parse_alias_value(name, "PC")
        sc_from_alias = pd.isna(sc_value) and alias_sc is not None
        pc_from_alias = pd.isna(pc_max) and alias_pc is not None
        if sc_from_alias:
            sc_value = alias_sc
        if pc_from_alias:
            pc_max = alias_pc
        records.append({
            "alpha_id": alpha_id, "Expression": alpha.get("regular", {}).get("code"),
            "Region": alpha.get("settings", {}).get("region"), "Universe": alpha.get("settings", {}).get("universe"),
            "Delay": alpha.get("settings", {}).get("delay"), "Sharpe": alpha.get("is", {}).get("sharpe"),
            "Fitness": alpha.get("is", {}).get("fitness"), "Margin": alpha.get("is", {}).get("margin"),
            "Date Created": alpha.get("dateCreated"), "Platform_Name": name, "Platform_Tags": ", ".join(tags),
            "Platform_Update_Status": old.get("Platform_Update_Status") or "NOT_ATTEMPTED",
            "self_correlation": sc_value, "prod_correlation_max": pc_max, "prod_correlation_min": pc_min,
            "SC_Status": None, "PC_Status": None, "Processing_Status": None,
            "_sc_cached": pd.notna(sc_value),
            # A high PC value is already terminal; low PC needs both values.
            "_pc_cached": is_high_pc(pc_max, pc_min) or (
                pd.notna(pc_max) and pd.notna(pc_min)
            ),
            "_sc_from_alias": sc_from_alias, "_pc_from_alias": pc_from_alias,
            "_history_processing_status": old.get("Processing_Status"), "_history_pc_status": old.get("PC_Status"),
            "_tags": tags,
        })
    # 无候选时仍保留 V5/V6 的数据契约，不能导出无表头工作簿。
    columns = ["alpha_id", "Expression", "Region", "Universe", "Delay", "Sharpe", "Fitness", "Margin",
               "Date Created", "Platform_Name", "Platform_Tags", "Platform_Update_Status",
               "self_correlation", "prod_correlation_max", "prod_correlation_min", "SC_Status", "PC_Status", "Processing_Status",
               "_sc_cached", "_pc_cached", "_sc_from_alias", "_pc_from_alias", "_history_processing_status", "_history_pc_status", "_tags"]
    return pd.DataFrame(records, columns=columns)


def mark_platform(session, df, index, tag, alias=None):
    tag_values = [tag] if isinstance(tag, str) else list(tag)
    remove_tags = {USEFUL_TAG, SUBMIT_TAG} if any(value in TERMINAL_HIGH_TAGS for value in tag_values) else set()
    tags = list(df.at[index, "_tags"] or [])
    for value in tag_values:
        tags = merge_tag(tags, value, remove_tags=remove_tags)
    progress(
        f"[平台] {df.at[index, 'alpha_id']} 准备更新："
        f"原name={df.at[index, 'Platform_Name']!r}，"
        f"原tags={','.join(tag_names(df.at[index, '_tags']))}，"
        f"目标name={alias!r}，目标tags={','.join(tags)}"
    )
    if set_alpha_properties(session, df.at[index, "alpha_id"], name=alias, tags=tags):
        df.at[index, "Platform_Update_Status"] = "SYNCED"
        df.at[index, "_tags"] = tags
        df.at[index, "Platform_Tags"] = ", ".join(tags)
        if alias is not None:
            df.at[index, "Platform_Name"] = alias
        progress(
            f"[平台] {df.at[index, 'alpha_id']} 属性更新成功："
            f"name={alias!r}，tags={','.join(tags)}，status=SYNCED"
        )
        return True
    df.at[index, "Platform_Update_Status"] = (
        "PENDING_PLATFORM_RATE_LIMIT"
        if platform_update_status() in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"}
        else "PENDING_PLATFORM_UPDATE"
    )
    progress(
        f"[平台] {df.at[index, 'alpha_id']} 属性更新失败："
        f"name={alias!r}，目标tags={','.join(tags)}，"
        f"status={df.at[index, 'Platform_Update_Status']}"
    )
    return False


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def pc_retry_wait(failure_count, initial_seconds=2):
    return min(initial_seconds * (2 ** min(max(0, failure_count - 1), 7)), CONFIG_PC_MAX_WAIT_SECONDS)


def get_prod_correlation_stats_resilient(session, alpha_id):
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/correlations/prod"
    attempt = 0
    while attempt < CONFIG_PC_MAX_RETRIES:
        attempt += 1
        attempt_started = time.monotonic()
        try:
            invalid_payload = False
            response = session.get(url, timeout=CONFIG_PC_MAX_WAIT_SECONDS, verify=False)
            if response.status_code == 200 and response.content:
                try:
                    payload = response.json()
                    if not isinstance(payload, dict):
                        raise TypeError("PC 响应不是对象")
                    max_pc = payload.get("max")
                    min_pc = payload.get("min")
                    max_pc = float(max_pc) if max_pc is not None else None
                    min_pc = float(min_pc) if min_pc is not None else None
                    if max_pc is None and min_pc is None:
                        raise ValueError("缺少 max/min")
                    return max_pc, min_pc, session
                except (KeyError, TypeError, ValueError, requests.exceptions.JSONDecodeError):
                    invalid_payload = True
            if response.status_code == 200:
                wait_seconds = max(0, CONFIG_PC_MAX_WAIT_SECONDS - (time.monotonic() - attempt_started))
                progress(
                    f"[PC] {alpha_id} 平台返回 200 但结果{('无效' if invalid_payload else '为空')}："
                    f"尝试 {attempt}/{CONFIG_PC_MAX_RETRIES}，等待 {wait_seconds} 秒"
                )
            else:
                if response.status_code not in {401, 403, 429} and response.status_code < 500:
                    progress(f"[PC] {alpha_id} 不可重试 HTTP 状态：{response.status_code}")
                    return None, None, session
                wait_seconds = max(0, CONFIG_PC_MAX_WAIT_SECONDS - (time.monotonic() - attempt_started))
                progress(
                    f"[PC] {alpha_id} HTTP {response.status_code}："
                    f"尝试 {attempt}/{CONFIG_PC_MAX_RETRIES}，等待 {wait_seconds} 秒"
                )
            if attempt >= CONFIG_PC_MAX_RETRIES:
                break
            time.sleep(wait_seconds)
        except requests.RequestException as exc:
            # 登录交给下一轮客户端重建，避免PC失败又进入额外登录重试拖长超时。
            wait_seconds = max(0, CONFIG_PC_MAX_WAIT_SECONDS - (time.monotonic() - attempt_started))
            progress(
                f"[PC] {alpha_id} 网络异常：{exc.__class__.__name__}，"
                f"尝试 {attempt}/{CONFIG_PC_MAX_RETRIES}，等待 {wait_seconds} 秒"
            )
            if attempt >= CONFIG_PC_MAX_RETRIES:
                break
            time.sleep(wait_seconds)
    progress(f"[PC] {alpha_id} 已尝试{CONFIG_PC_MAX_RETRIES}次（每次最多60秒），跳过当前Alpha，保留 PENDING_PC_RESULT")
    return None, None, session


def get_pc_stop_reason(processed_count, low_count):
    if CONFIG_PC_LOW_TARGET_COUNT > 0 and low_count >= CONFIG_PC_LOW_TARGET_COUNT:
        return f"PC < {CONFIG_PC_LOW_STOP_THRESHOLD:.3f} 已达到目标 {CONFIG_PC_LOW_TARGET_COUNT} 个"
    if processed_count >= CONFIG_PC_MAX_COUNT:
        return f"达到 PC 上限 {CONFIG_PC_MAX_COUNT} 个"
    return None


def wait_until_midnight():
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time.sleep((midnight - now).total_seconds())


USER_DIVERSITY_URL = "https://api.worldquantbrain.com/users/self/activities/diversity"


def _read_activity_json(session, url, context):
    """读取 Activity/Pyramid JSON；429 冷却五分钟后只对账一次。"""
    for attempt in range(2):
        try:
            response = session.get(url, timeout=30, verify=False)
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    return payload
                logging.warning("%s 响应不是对象", context)
                return None
            if response.status_code == 429 and attempt == 0:
                progress(f"[Pyramid] {context} 返回 429，300 秒后只读对账一次")
                time.sleep(300)
                continue
            logging.warning("%s 查询失败：status=%s", context, response.status_code)
            return None
        except (requests.RequestException, ValueError, TypeError) as exc:
            logging.warning("%s 查询异常：%s", context, exc)
            return None
    return None


def get_user_diversity(session):
    """直接返回平台账户 Pyramid 状态；不可观测时返回空对象。"""
    return _read_activity_json(session, USER_DIVERSITY_URL, "账户塔状态") or {}


def get_alpha_pyramid_pass_info(session, alpha_id):
    """直接读取 MATCHES_PYRAMID，不再从表达式字段推断 Category。"""
    alpha_id = str(alpha_id or "").strip()
    pending = {"status": "PENDING", "alpha_id": alpha_id, "categories": []}
    if not alpha_id:
        return pending
    payload = _read_activity_json(
        session,
        f"https://api.worldquantbrain.com/alphas/{alpha_id}",
        f"Alpha {alpha_id} Pyramid",
    )
    checks = (payload.get("is") or {}).get("checks") if isinstance(payload, dict) else None
    if not isinstance(checks, list):
        return pending
    check = next(
        (item for item in checks if isinstance(item, dict) and item.get("name") == "MATCHES_PYRAMID"),
        None,
    )
    if check is None:
        return pending
    pyramids = check.get("pyramids")
    valid = [
        {"name": item.get("name"), "multiplier": item.get("multiplier")}
        for item in pyramids or []
        if isinstance(item, dict) and item.get("name")
    ] if isinstance(pyramids, list) else []
    if check.get("result") == "PASS" and not valid:
        return pending
    return {
        "status": "PASS" if check.get("result") == "PASS" else "NO_PASS",
        "alpha_id": alpha_id,
        "categories": [item["name"] for item in valid],
        "pyramids": valid,
        "effective": check.get("effective"),
        "multiplier": check.get("multiplier"),
    }


_CATEGORY_ALIASES = {"pricevolume": "pv", "pricevol": "pv"}


def _canonical_category(value):
    token = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    return _CATEGORY_ALIASES.get(token, token)


def evaluate_pyramid_coverage(diversity_payload, pyramid_info):
    """按 Region + Delay + Category 判断关联塔是否存在缺口。"""
    rows = diversity_payload.get("alphas") if isinstance(diversity_payload, dict) else None
    categories = pyramid_info.get("categories") if isinstance(pyramid_info, dict) else None
    if not isinstance(rows, list):
        return {"status": "PENDING", "scopes": [], "gap_scopes": [], "reason": "diversity响应不可用"}
    if (not isinstance(pyramid_info, dict) or pyramid_info.get("status") == "PENDING"
            or not isinstance(categories, list) or not categories):
        return {"status": "PENDING", "scopes": [], "gap_scopes": [], "reason": "Alpha Pyramid分类不可用"}

    index = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        category = row.get("dataCategory") or {}
        key = _canonical_category(category.get("id") or category.get("name"))
        region = str(row.get("region") or "").strip().upper()
        try:
            delay = int(row.get("delay"))
        except (TypeError, ValueError):
            continue
        if not region or not key:
            continue
        diversity = row.get("dataDiversity") or {}
        index[(region, delay, key)] = {
            "check": str(diversity.get("check") or "").strip().upper() or "MISSING",
            "limit": diversity.get("limit"),
            "alpha_count": row.get("alphaCount"),
            "category_id": category.get("id"),
            "category_name": category.get("name"),
        }

    scopes = []
    for raw_scope in categories:
        match = re.fullmatch(r"([^/]+)/D(\d+)/(.+)", str(raw_scope or "").strip(), re.IGNORECASE)
        if not match:
            return {"status": "PENDING", "scopes": scopes, "gap_scopes": [],
                    "reason": f"无法解析平台塔名称: {raw_scope!r}"}
        region, delay = match.group(1).upper(), int(match.group(2))
        category = _canonical_category(match.group(3))
        row = index.get((region, delay, category))
        scopes.append({
            "raw_scope": raw_scope,
            "region": region,
            "delay": delay,
            "category": category,
            "check": row["check"] if row else "MISSING",
            "limit": row.get("limit") if row else None,
            "alpha_count": row.get("alpha_count") if row else None,
            "matched_category_id": row.get("category_id") if row else None,
            "matched_category_name": row.get("category_name") if row else None,
        })
    gaps = [scope for scope in scopes if scope["check"] != "PASS"]
    return {
        "status": "HAS_GAP" if gaps else "ALL_PASS",
        "scopes": scopes,
        "gap_scopes": gaps,
        "reason": "存在未PASS或未返回的关联塔" if gaps else "所有关联塔均PASS",
    }


def is_correlation_pass(value):
    """高相关采用严格大于 0.7，因此边界值 0.700 属于通过。"""
    return pd.notna(value) and abs(float(value)) <= CORRELATION_HIGH_THRESHOLD


def is_strictly_low(value):
    """保留旧的严格小于判断；最终通过请使用 is_correlation_pass。"""
    return pd.notna(value) and abs(float(value)) < CORRELATION_HIGH_THRESHOLD


def pc_priority_key(df, index):
    created = pd.to_datetime(df.at[index, "Date Created"], errors="coerce", utc=True)
    if pd.isna(created):
        return (1, 0, str(df.at[index, "alpha_id"]))
    return (0, -created.value, str(df.at[index, "alpha_id"]))


def apply_low_correlation_categories(session, df, index, alpha):
    """双低后写 Useful；Pyramid Category 在最终全量审计中直接查询。"""
    alpha_id = df.at[index, "alpha_id"]
    sc = df.at[index, "self_correlation"]
    pc_max = df.at[index, "prod_correlation_max"]
    pc_min = df.at[index, "prod_correlation_min"] if "prod_correlation_min" in df.columns else None
    if not is_correlation_pass(sc) or not is_complete_low_pc(pc_max, pc_min):
        progress(
            f"[V5][Useful] {alpha_id} 未满足双低：SC={sc}，PC={pc_max}/{pc_min}，"
            f"不写 {USEFUL_TAG}"
        )
        return False
    pc = pc_alias_value(pc_max, pc_min)
    alias = normal_alias(sc, pc)
    terminal_names = {tag.casefold() for tag in TERMINAL_HIGH_TAGS}
    nonterminal_tags = [
        tag for tag in tag_names(df.at[index, "_tags"])
        if tag.casefold() not in terminal_names
    ]
    tags = list(dict.fromkeys([USEFUL_TAG, *nonterminal_tags]))
    df.at[index, "Matched_Categories"] = ""
    df.at[index, "Category_Status"] = "PENDING_PYRAMID_AUDIT"
    df.at[index, "Category_Evidence"] = ""
    df.at[index, "PC_Status"] = "PASS"
    df.at[index, "Processing_Status"] = "COMPLETE"
    progress(
        f"[V5][Useful] {alpha_id} 双低确认：SC={sc}，"
        f"PC={pc_max}/{pc_min}，准备写入 {USEFUL_TAG}；Pyramid Category 在最终审计查询"
    )
    updated = set_alpha_properties(session, alpha_id, name=alias, tags=tags)

    if not updated:
        df.at[index, "Platform_Update_Status"] = (
            "PENDING_PLATFORM_RATE_LIMIT"
            if platform_update_status() in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"}
            else "PENDING_PLATFORM_UPDATE"
        )
        df.at[index, "Processing_Status"] = "PENDING_PLATFORM_UPDATE"
        return False

    df.at[index, "Platform_Name"] = alias
    df.at[index, "Platform_Update_Status"] = "SYNCED"
    df.at[index, "_tags"] = tags
    df.at[index, "Platform_Tags"] = ", ".join(tags)
    progress(
        f"[V5][Useful] {alpha_id} 更新成功：name={alias!r}，"
        f"tags={','.join(tags)}"
    )
    return True
