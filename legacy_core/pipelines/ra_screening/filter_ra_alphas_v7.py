"""V7: run the daily V5 stage, then the V6 final stage."""

import filter_ra_alphas_core as core


# 只改“是/否”，然后直接运行本文件。
V7_RUN_V5 = True  # 是：先执行一次 V5；否：V6 使用 output/ 中最新 V5 文件
V7_RUN_V6 = True   # 是：继续执行 V6 最终阶段；否：只执行 V5
V7_DAILY_MIN_BATCHES = 10  # 只计8个不同Alpha ID且基础指标完整的已完成批次
V7_RETRY_SECONDS = 300
V7_SCAN_SECONDS = 1800


def run_job(run_v5=V7_RUN_V5, run_v6=V7_RUN_V6):
    if run_v5:
        core.run_stage_file("filter_ra_alphas_v5.py")
    if run_v6:
        result = core.run_stage_file("filter_ra_alphas_v6.py")
    else:
        result = None
    return result


def main():
    """仅持续RA检测和设置回测；模板轮动属于爬山程序。"""
    if core.CONFIG_RUN_DAILY:
        from pathlib import Path
        from ra_daily_runtime import keep_running
        keep_running(run_job, core, Path(__file__).resolve().parent / "output",
                     target=V7_DAILY_MIN_BATCHES, retry_seconds=V7_RETRY_SECONDS, scan_seconds=V7_SCAN_SECONDS)
    else:
        run_job()
    # run_job()


if __name__ == "__main__":
    main()
