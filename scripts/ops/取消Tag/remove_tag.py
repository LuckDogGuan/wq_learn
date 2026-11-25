#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码/优化代码/取消Tag/remove_tag.py

批量取消指定 Alpha 上的 Tag 标签小工具。
功能特性：
1. 支持交互式输入或命令行参数传入要取消的 Tag（例如 PPA_Submit）；
2. 复用「区分PPA并标记」中的强壮分页拉取逻辑（指数退避重试 + 500深度游标位移防超时）；
3. 遵循全局准则：提供修改前二次确认，防止误触导致全量标签误删；
4. 逐个写回平台并实时输出进度与日志。
"""

import sys
import time
import logging
import argparse
import urllib.parse
from pathlib import Path

# 添加 Core 所在路径
CURRENT_DIR = Path(__file__).resolve().parent
CORE_PARENT = CURRENT_DIR.parent
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.api import login, set_alpha_properties

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# 频率与安全控制参数
BATCH_REST_SIZE = 10     # 每处理多少个 Alpha 暂停一下
BATCH_REST_DURATION = 1.0 # 批次暂停秒数
REQUEST_INTERVAL = 0.3   # 单个请求基础间隔秒数


def alpha_tags(alpha):
    """提取 Alpha 的有效标签列表。"""
    tags = alpha.get("tags") if isinstance(alpha, dict) else None
    if not tags:
        return []
    if isinstance(tags, str):
        tags = [tags]
    return [tag for tag in tags if isinstance(tag, str) and tag]


def fetch_alphas_by_tag(client, target_tag):
    """
    使用「区分PPA并标记」相同的健壮分页机制拉取所有携带 target_tag 的因子。
    具备：
    1. 指数退避重试；
    2. offset >= 500 时自动使用 dateCreated 时间游标位移，彻底避免平台深分页超时。
    """
    logging.info("开始拉取带有标签 '%s' 的全部 Alpha...", target_tag)
    base_query = f"tag={urllib.parse.quote(target_tag, safe='')}&order=-dateCreated&limit=100"
    
    all_alphas = []
    seen_ids = set()
    offset = 0
    current_end_str = None

    while True:
        url = f"/users/self/alphas?{base_query}&offset={offset}"
        if current_end_str:
            date_param = urllib.parse.quote(f"dateCreated<={current_end_str}", safe="")
            url = f"{url}&{date_param}"

        response = None
        for attempt in range(10):
            response = client.get(url)
            if response and response.status_code == 200:
                break
            wait = 2 ** attempt
            logging.warning(
                "分页拉取警告 offset=%d 状态=%s，重试 (%d/10)，延时 %d 秒...",
                offset, response.status_code if response else "NO_RESPONSE", attempt + 1, wait,
            )
            time.sleep(wait)

        if not response or response.status_code != 200:
            logging.error("拉取彻底失败，offset=%d，停止继续拉取。", offset)
            break

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            logging.error("响应解析失败，offset=%d: %s", offset, exc)
            break

        results = payload.get("results", []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])
        if not isinstance(results, list) or not results:
            break

        valid_results = []
        for item in results:
            if isinstance(item, dict):
                alpha_id = item.get("id")
                if alpha_id and alpha_id not in seen_ids:
                    seen_ids.add(alpha_id)
                    valid_results.append(item)

        all_alphas.extend(valid_results)
        logging.info("成功拉取本批 offset=%d，获取 %d 条，累计已发现 %d 条。", offset, len(valid_results), len(all_alphas))

        if len(results) < 100:
            break

        offset += len(results)
        # 当偏移量达到 500 时，重置 offset 并移动时间游标，防止触发平台 500 限制
        if offset >= 500:
            last_date_str = results[-1].get("dateCreated")
            if last_date_str:
                logging.info("触发防超时时间游标移动，将查询截点更新为 %s，offset 清零继续拉取。", last_date_str)
                current_end_str = last_date_str
                offset = 0

    logging.info("全部拉取完成，共找到 %d 个带有标签 '%s' 的 Alpha。", len(all_alphas), target_tag)
    return all_alphas


def remove_tag_from_alphas(client, alphas, target_tag, auto_confirm=False):
    """执行批量取消 Tag 逻辑。"""
    if not alphas:
        logging.info("没有需要处理的 Alpha。")
        return

    print("\n" + "=" * 60)
    print("【准备执行批量取消标签】")
    print(f"目标标签: {target_tag}")
    print(f"受影响的 Alpha 数量: {len(alphas)}")
    print("前 3 个示例:")
    for a in alphas[:3]:
        print(f"  - ID: {a.get('id')} | 原标签: {alpha_tags(a)}")
    print("=" * 60)

    if not auto_confirm:
        try:
            confirm = input(f"确认要将以上 {len(alphas)} 个 Alpha 中的标签 '{target_tag}' 全部取消吗？(y/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n操作已取消。")
            return
        if confirm not in ("y", "yes"):
            logging.info("用户取消操作，未对任何 Alpha 进行修改。")
            return

    logging.info("开始批量移除标签...")
    success_count = 0
    fail_count = 0
    unchanged_count = 0

    for index, alpha in enumerate(alphas, start=1):
        alpha_id = alpha.get("id")
        current_tags = alpha_tags(alpha)

        if target_tag not in current_tags:
            unchanged_count += 1
            logging.info("[%d/%d] Alpha %s 原本就不含标签 '%s'，跳过。", index, len(alphas), alpha_id, target_tag)
            continue

        # 过滤掉目标标签
        new_tags = [t for t in current_tags if t != target_tag]

        # 写回平台
        try:
            resp = set_alpha_properties(client, alpha_id, tags=new_tags)
            if resp is not None and resp.status_code in (200, 201, 204):
                success_count += 1
                logging.info(
                    "[%d/%d] Alpha %s 成功取消标签 '%s'，剩余标签: %s",
                    index, len(alphas), alpha_id, target_tag, new_tags,
                )
            else:
                fail_count += 1
                status = resp.status_code if resp is not None else "NO_RESPONSE"
                logging.error("[%d/%d] Alpha %s 取消标签失败，HTTP 状态: %s", index, len(alphas), alpha_id, status)
        except Exception as exc:
            fail_count += 1
            logging.error("[%d/%d] Alpha %s 更新异常: %s", index, len(alphas), alpha_id, exc)

        time.sleep(REQUEST_INTERVAL)
        if index % BATCH_REST_SIZE == 0 and index < len(alphas):
            time.sleep(BATCH_REST_DURATION)

    print("\n" + "=" * 60)
    logging.info(
        "【处理完成】目标标签: '%s' | 总数: %d | 成功: %d | 失败: %d | 无需处理: %d",
        target_tag, len(alphas), success_count, fail_count, unchanged_count,
    )
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="WorldQuant BRAIN 批量取消指定 Tag 标签工具")
    parser.add_argument("--tag", "-t", type=str, default="", help="要取消的目标 Tag 名称（如 PPA_Submit）")
    parser.add_argument("--yes", "-y", action="store_true", help="跳过二次确认直接执行（用于自动化脚本）")
    args = parser.parse_args()

    target_tag = args.tag.strip()
    if not target_tag:
        try:
            target_tag = input("请输入要批量取消的 Tag 标签名称（例如 PPA_Submit）: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已退出。")
            return

    if not target_tag:
        print("错误：未输入任何 Tag 标签名称！")
        return

    # 登录平台
    client = login()

    # 1. 查询所有带有该 tag 的因子
    alphas = fetch_alphas_by_tag(client, target_tag)

    # 2. 批量移除
    remove_tag_from_alphas(client, alphas, target_tag, auto_confirm=args.yes)


if __name__ == "__main__":
    main()
