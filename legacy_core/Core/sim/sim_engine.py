"""
sim/sim_engine.py
业务层：并发任务池调度。
所有 HTTP 通信完全委托给 Core.api.sim_api，本模块不含任何 requests 调用。
"""
from Core.api import login
from Core.api.sim_api import (
    post_simulation, post_multi_simulation, poll_simulation_progress
)
from Core.constants.global_ops import *

from time import sleep
import time
import re


_ALLOWED_SETTINGS_OVERRIDES = {
    'neutralization', 'truncation', 'pasteurization', 'testPeriod',
    'unitHandling', 'nanHandling', 'visualization', 'maxTrade',
}
_MAX_FILTERED_RETRIES = 2
_ERROR_INDEX_PATTERN = re.compile(r'\bindex\s*[:=]?\s*(\d+)\b', re.IGNORECASE)


def load_task_pool_single(alpha_list: list, limit: int) -> list:
    """
    将 Alpha 列表切分为单因子并发模拟的任务池。

    参数:
        alpha_list (list): (alpha_expr, decay) 元组列表。
        limit (int): 单次并发的最大模拟数量。

    返回:
        list: 分包后的任务池列表。
    """
    return [alpha_list[i:i + limit] for i in range(0, len(alpha_list), limit)]


def build_sim_payload(alpha: str, decay: int, region: str, universe: str,
                      neut: str, test_period: str = 'P0Y',
                      settings_overrides: dict = None) -> dict:
    """
    构建单条 simulation 的请求 payload。

    参数:
        alpha (str): Alpha 表达式。
        decay (int): Decay 参数。
        region (str): 地区。
        universe (str): 股票池。
        neut (str): 中性化设置。
        test_period (str): 回测周期（默认 P0Y）。
        settings_overrides (dict): 当前表达式允许覆盖的研究参数。

    返回:
        dict: simulation 请求体。
    """
    overrides = {} if settings_overrides is None else settings_overrides
    if not isinstance(overrides, dict):
        raise TypeError("settings_overrides 必须是 dict 或 None")
    invalid_keys = set(overrides) - _ALLOWED_SETTINGS_OVERRIDES
    if invalid_keys:
        raise ValueError(f"不允许覆盖 settings: {', '.join(sorted(invalid_keys))}")

    settings = {
        'instrumentType': 'EQUITY',
        'region': region,
        'universe': universe,
        'delay': 1,
        'decay': decay,
        'neutralization': neut,
        'truncation': 0.08,
        'pasteurization': 'ON',
        'testPeriod': test_period,
        'unitHandling': 'VERIFY',
        'nanHandling': 'ON',
        'maxTrade': 'OFF',
        'language': 'FASTEXPR',
        'visualization': False,
    }
    settings.update(overrides)

    return {
        'type': 'REGULAR',
        'settings': settings,
        'regular': alpha
    }


def _unpack_alpha_item(item):
    if len(item) == 2:
        alpha, decay = item
        return alpha, decay, None
    if len(item) == 3:
        alpha, decay, settings_overrides = item
        return alpha, decay, settings_overrides
    raise ValueError("Alpha 项必须是 (expression, decay) 或 (expression, decay, settings_overrides)")


def _extract_error_indices(value) -> list:
    """从 ERROR 响应的结构化 index 或错误文本中提取零基索引。"""
    indices = set()

    def visit(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if str(key).lower() == 'index':
                    if isinstance(child, int) and not isinstance(child, bool):
                        indices.add(child)
                    elif isinstance(child, str) and child.isdigit():
                        indices.add(int(child))
                visit(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)
        elif isinstance(node, str):
            indices.update(int(match) for match in _ERROR_INDEX_PATTERN.findall(node))

    visit(value)
    return sorted(indices)


def single_simulate(alpha_pool: list, neut: str, region: str, universe: str, start: int = 0):
    """
    逐批提交单 Alpha 模拟任务，并轮询监控直到所有模拟完成。
    遇到超时或平台异常时自适应等待并重新登录。

    参数:
        alpha_pool (list): 任务池列表（每项为 [(alpha, decay), ...] 的小批次）。
        neut (str): 中性化方式。
        region (str): 地区。
        universe (str): 股票池。
        start (int): 起始批次索引，用于断点续传。
    """
    client = login()

    for x, task in enumerate(alpha_pool):
        if x < start:
            continue
        progress_urls = []

        for item in task:
            alpha, decay, settings_overrides = _unpack_alpha_item(item)
            payload = build_sim_payload(
                alpha, decay, region, universe, neut, 'P0Y', settings_overrides
            )
            url = post_simulation(client, payload)
            if url:
                progress_urls.append(url)
            else:
                print(f"[批次 {x}] 提交失败，等待 10 分钟后重新登录...")
                sleep(600)
                client = login()

        print(f"[批次 {x}] POST 提交完成，共 {len(progress_urls)} 个任务")

        for j, progress_url in enumerate(progress_urls):
            result = poll_simulation_progress(client, progress_url, timeout=600)
            status = result.get("status", "UNKNOWN")
            if status not in ("COMPLETE", "WARNING"):
                print(f"  [任务 {j}] 回测未成功: status={status}, url={progress_url}")

        print(f"[批次 {x}] 全部模拟完成")

    print("所有单 Alpha 模拟任务已完成")


def generate_sim_data(alpha_list: list, region: str, universe: str, neut: str) -> list:
    """
    构造 Multi-simulation 回测所需的 payload 列表。

    参数:
        alpha_list (list): (alpha, decay) 或 (alpha, decay, settings_overrides) 列表。
        region (str): 交易地区。
        universe (str): 股票池。
        neut (str): 中性化模式。

    返回:
        list: Multi-simulation 的 payload 列表。
    """
    payloads = []
    for item in alpha_list:
        alpha, decay, settings_overrides = _unpack_alpha_item(item)
        payloads.append(build_sim_payload(
            alpha, decay, region, universe, neut, 'P2Y', settings_overrides
        ))
    return payloads


def load_task_pool(alpha_list: list, limit_children: int, limit_multi: int) -> list:
    """
    多因子批量模拟三层任务池切分结构函数 (Pools → Tasks → Alphas)。

    参数:
        alpha_list (list): Alpha 元组列表。
        limit_children (int): 单个 Multi-simulation 包含的子 Alpha 数量（2–8）。
        limit_multi (int): 同时并发的多因子组合数。

    返回:
        list: 三层嵌套的任务池 pools。
    """
    if isinstance(limit_children, bool) or not isinstance(limit_children, int) or not 2 <= limit_children <= 8:
        raise ValueError("limit_children 必须在 2 到 8 之间")
    if isinstance(limit_multi, bool) or not isinstance(limit_multi, int) or limit_multi <= 0:
        raise ValueError("limit_multi 必须是正整数")
    if len(alpha_list) == 1:
        raise ValueError("仅一个 Alpha，不能创建多模拟任务；请保留待补批")
    tasks = [
        alpha_list[i:i + limit_children]
        for i in range(0, len(alpha_list), limit_children)
    ]
    if len(tasks) > 1 and len(tasks[-1]) == 1:
        if len(tasks[-2]) > 2:
            tasks[-1].insert(0, tasks[-2].pop())
        else:
            tasks[-2].extend(tasks.pop())
    return [tasks[i:i + limit_multi] for i in range(0, len(tasks), limit_multi)]


def multi_simulate(alpha_pools: list, neut: str, region: str, universe: str, start: int = 0):
    """
    Consultant 级别的多因子组合 (Multi-simulation) 批量并发提交与轮询监控。

    参数:
        alpha_pools (list): 任务池嵌套列表。
        neut (str): 中性化设置。
        region (str): 地区。
        universe (str): 股票池。
        start (int): 断点恢复起始池索引。
    """
    client = login()
    total_success = 0
    total_error = 0
    total_unobserved = 0

    for x, pool in enumerate(alpha_pools):
        if x < start:
            continue
        submitted = []
        pool_success = 0
        pool_error = 0
        pool_unobserved = 0

        for y, task in enumerate(pool):
            try:
                sim_data_list = generate_sim_data(task, region, universe, neut)
                url = post_multi_simulation(client, sim_data_list)
            except (TypeError, ValueError) as exc:
                print(f"[池 {x} 批次 {y}] ERROR_STOP: {exc}")
                pool_error += 1
                continue
            if url:
                submitted.append((y, list(enumerate(task)), url))
            else:
                print(f"[池 {x} 批次 {y}] RESULTS_UNOBSERVED: 提交失败或缺少 Location，停止该任务")
                pool_unobserved += 1

        print(f"[池 {x}] POST 提交完成，共 {len(submitted)} 个 multi-sim")

        for y, entries, progress_url in submitted:
            retries_used = 0
            while True:
                result = poll_simulation_progress(client, progress_url, timeout=900)
                status = result.get("status", "UNKNOWN") if result else "UNKNOWN"

                if status in ("COMPLETE", "WARNING"):
                    print(f"  [池 {x} 批次 {y}] 成功完成: status={status}")
                    pool_success += 1
                    break

                if status != "ERROR":
                    print(
                        f"  [池 {x} 批次 {y}] RESULTS_UNOBSERVED: "
                        f"status={status}, url={progress_url}"
                    )
                    pool_unobserved += 1
                    break

                error_indices = _extract_error_indices(result)
                if not error_indices or any(index < 0 or index >= len(entries) for index in error_indices):
                    print(
                        f"  [池 {x} 批次 {y}] RESULTS_UNOBSERVED: 无法定位有效错误索引，"
                        f"不重试，url={progress_url}"
                    )
                    pool_unobserved += 1
                    break

                if retries_used >= _MAX_FILTERED_RETRIES:
                    print(f"  [池 {x} 批次 {y}] ERROR_STOP: 已达到额外重试上限 {_MAX_FILTERED_RETRIES}")
                    pool_error += 1
                    break

                bad_indices = set(error_indices)
                for index in error_indices:
                    original_index, item = entries[index]
                    alpha, _, _ = _unpack_alpha_item(item)
                    print(
                        f"  [池 {x} 批次 {y}] 筛除错误表达式: "
                        f"当前索引={index}, 原索引={original_index}, expression={alpha}"
                    )
                entries = [entry for index, entry in enumerate(entries) if index not in bad_indices]
                if not entries:
                    print(f"  [池 {x} 批次 {y}] ERROR_STOP: 筛除后没有可重试表达式")
                    pool_error += 1
                    break

                retries_used += 1
                print(
                    f"  [池 {x} 批次 {y}] 筛除后重试 {retries_used}/{_MAX_FILTERED_RETRIES}，"
                    f"剩余 {len(entries)} 个表达式"
                )
                try:
                    sim_data_list = generate_sim_data(
                        [item for _, item in entries], region, universe, neut
                    )
                    progress_url = post_multi_simulation(client, sim_data_list)
                except (TypeError, ValueError) as exc:
                    print(f"  [池 {x} 批次 {y}] ERROR_STOP: {exc}")
                    pool_error += 1
                    break
                if not progress_url:
                    print(
                        f"  [池 {x} 批次 {y}] RESULTS_UNOBSERVED: "
                        "筛除后提交失败或缺少 Location，停止该任务"
                    )
                    pool_unobserved += 1
                    break

        total_success += pool_success
        total_error += pool_error
        total_unobserved += pool_unobserved
        print(
            f"[池 {x}] 处理结束: 成功={pool_success}, "
            f"错误停止={pool_error}, 结果未观察={pool_unobserved}"
        )

    print(
        f"Multi-simulation 调度结束: 成功={total_success}, "
        f"错误停止={total_error}, 结果未观察={total_unobserved}"
    )
