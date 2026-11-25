# 广州服务器同账号安全隔离暂停与一键恢复回执

> [!IMPORTANT]
> **执行摘要（2026-11-25 用户决策 #1 落地）**：依据用户明确批准，已于 **`2026-11-25 14:36:50 CST`（`2026-11-25T06:36:50Z`）** 通过 `systemctl stop` 干净暂停广州主机（`ssh guangzhou`，主机名 `VM-0-3-ubuntu`）上的两项 WorldQuant systemd 服务：**`worldquant-hill-climbing.service`** 与 **`worldquant-ra-detection.service`**。
> - **零删除原则**：未删除、未修改任何远程代码、日志、数据库或配置单元文件。
> - **暂态单元完整留档**：因 `worldquant-hill-climbing.service` 属于 **transient（暂态）systemd 单元**（停止后 `/run/systemd/transient/worldquant-hill-climbing.service` 会被 systemd 自动清理），本次已在暂停前完整抓取其全部属性与原始单元文本，文末附**100% 等价一键恢复命令**。

---

## 1. 暂停前完整状态快照（抓拍于 `2026-11-25 14:34:44 CST` / `06:34:44Z`）

### 1.1 运行进程与资源占用总览

| 服务单元 | 单元类型 / 启用态 | 暂停前 Main PID | 进程状态 / 启动时间 | CPU 占用 / 累计 CPU | 内存占用 / 限额 | 暂停前末条活动摘要 |
| --- | --- | --- | --- | --- | --- | --- |
| `worldquant-hill-climbing.service` | **transient** (`/run/systemd/transient/...`) | `3382152` | `Rsl` · 自 `2026-11-18 16:17:33 CST`（运行 6 天） | **61.4%** · `4d 6h 14min 56.738s` (`368096769417000 ns`) | `762.0M` (`799068160 B`)；`High=768M / Max=1.125G / SwapMax=128M` | 断点续传 `Score=2.8368`, `Alpha ID=xAvjEopN`, 初始 `ID=1YWw2RRX`，循环搜索 `eur_top_signal_value_2`（本地缓存 32 候选），当日模拟 `used=0/3000` |
| `worldquant-ra-detection.service` | **永久单元** (`/etc/systemd/system/...`, `enabled`) | `3862476` | `Ssl` · 自 `2026-10-12 16:26:14 CST`（运行 1 个月 13 天） | **0.2%** · `3h 8min 10.732s`（停机终值 `3h 8min 10.818s`） | `231.0M` (`242290688 B`)；无硬内存限制 | 轮询 `/correlations/prod`：`2rG8ZR8Z`、`GrQ18610`、`XgNmlLm5`、`YPlLkmL6` 均连续 3 次返回 HTTP 200 空体，记 `PENDING_PC_RESULT` |

### 1.2 暂停前 `hill_climbing_budget/state.json` 完整快照

文件路径：`/root/worldquont/Core/runtime_data/hill_climbing_budget/state.json`（暂停前后逐字节核对完全一致）：

```json
{
  "window_started_at": "2026-11-25T12:00:00+08:00",
  "used": 0,
  "post_cooldown_count": 520,
  "last_rate_limit_at": "2026-09-09T07:56:13.545666+08:00",
  "limit": 3000,
  "remaining": 3000,
  "reset_hour": 12,
  "reset_at": "2026-11-26T12:00:00+08:00",
  "updated_at": "2026-11-25T14:32:33.716451+08:00"
}
```

### 1.3 原始 systemd 单元定义完整留档（`systemctl cat` 原文）

#### A. `worldquant-hill-climbing.service`（暂停前 `/run/systemd/transient/worldquant-hill-climbing.service`）

```ini
# /run/systemd/transient/worldquant-hill-climbing.service
# This is a transient unit file, created programmatically via the systemd API. Do not edit.
[Unit]
Description=WorldQuant hill climbing

[Service]
Type=exec
MemoryHigh=805306368
MemoryMax=1207959552
MemorySwapMax=134217728
WorkingDirectory=/root/worldquont/爬山代码
Environment="PYTHONUNBUFFERED=1"
ExecStart=
ExecStart="/root/miniconda3/bin/python" "/root/worldquont/\347\210\254\345\261\261\344\273\243\347\240\201/\345\205\250\350\207\252\345\212\250\347\210\254\345\261\261\347\256\227\346\263\225.py"
```

> 关键 `systemctl show` 补充字段：`Restart=no`、`StandardOutput=journal`、`StandardError=inherit`、`User=`（默认 `root`）、`ExecStart argv[]=/root/miniconda3/bin/python /root/worldquont/爬山代码/全自动爬山算法.py`。

#### B. `worldquant-ra-detection.service`（永久文件 `/etc/systemd/system/worldquant-ra-detection.service`）

```ini
# /etc/systemd/system/worldquant-ra-detection.service
[Unit]
Description=WorldQuant RA detection and setting backtests
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=/root/worldquont/Ra_reach
ExecStart=/root/miniconda3/bin/python -u /root/worldquont/Ra_reach/filter_ra_alphas_v7.py
Restart=always
RestartSec=60
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 1.4 定时任务与自动拉起审计（暂停前实测）

- **`systemctl list-timers --all`**：仅存在 `v2ray-sub-refresh.timer` 与 `apt-daily-upgrade.timer`，**无任何 WorldQuant 相关 timer**。
- **`crontab -l`**：仅存在腾讯云监控 `*/5 * * * * flock -xn /tmp/stargate.lock -c '/usr/local/qcloud/stargate/admin/start.sh > /dev/null 2>&1 &'`，**无任何自动拉起 WorldQuant 服务的 cron**。

---

## 2. 暂停执行与暂停后实测核验

- **执行命令**：`ssh guangzhou "systemctl stop worldquant-hill-climbing.service worldquant-ra-detection.service"`
- **暂停起止时间戳**：`2026-11-25 14:36:50 CST`（`2026-11-25T06:36:50Z`）→ `2026-11-25 14:36:50 CST`（同秒完成优雅退出）
- **核验结果汇总**：

| 核验项 | 实测输出 | 结论 |
| --- | --- | --- |
| `systemctl is-active worldquant-hill-climbing.service` | `inactive`（暂态单元已干净卸载） | **PASS（已暂停）** |
| `systemctl is-active worldquant-ra-detection.service` | `inactive`（`Active: inactive (dead)`，`code=killed, signal=TERM`，`Deactivated successfully.`） | **PASS（已暂停）** |
| `systemctl is-enabled worldquant-ra-detection.service` | `enabled`（按“仅暂停不改单元文件”要求保留原启用状态） | **已记录（注意下方重启提示）** |
| `ps aux \| grep -iE 'python\|hill\|ra_reach\|worldquont'` | 仅余系统进程 PID `788`（`networkd-dispatcher`）与 PID `966`（`unattended-upgrade-shutdown`），**`0` 个 WorldQuant 进程** | **PASS（零残留进程）** |
| 远程文件完整性校验（`ls -la`） | `/etc/systemd/system/worldquant-ra-detection.service` (`444 B`)、`/root/worldquont/爬山代码/全自动爬山算法.py` (`475 B`)、`/root/worldquont/Ra_reach/filter_ra_alphas_v7.py` (`1191 B`)、`/root/worldquont/Core/runtime_data/hill_climbing_budget/state.json` (`311 B`, `used=0/3000`) 全部完好 | **PASS（零删除、零篡改）** |

> [!NOTE]
> **主机重启提示**：因本次严格遵守“仅 `stop`、不改动任何远程文件与配置”边界，`worldquant-ra-detection.service` 仍保持 `enabled`。若隔离期间广州主机发生重启，`worldquant-ra-detection.service` 会随开机自启（`worldquant-hill-climbing.service` 为暂态单元，不会自启）。如需跨重启彻底保持暂停，可另行执行 `ssh guangzhou "systemctl disable worldquant-ra-detection.service"`（恢复时配 `enable --now`）。

---

## 3. 一键精准恢复命令（随时可原样还原）

### 3.1 分别恢复单个服务

#### 恢复 1：`worldquant-hill-climbing.service`（按原暂态单元参数 100% 精准重建）

```bash
ssh guangzhou 'systemd-run \
  --unit=worldquant-hill-climbing \
  --description="WorldQuant hill climbing" \
  --working-directory="/root/worldquont/爬山代码" \
  --property=Type=exec \
  --property=MemoryHigh=805306368 \
  --property=MemoryMax=1207959552 \
  --property=MemorySwapMax=134217728 \
  --setenv=PYTHONUNBUFFERED=1 \
  /root/miniconda3/bin/python "/root/worldquont/爬山代码/全自动爬山算法.py"'
```

#### 恢复 2：`worldquant-ra-detection.service`（直接拉起永久单元）

```bash
ssh guangzhou 'systemctl start worldquant-ra-detection.service'
```

### 3.2 一键同时恢复两项服务并核验状态

```bash
ssh guangzhou 'systemd-run --unit=worldquant-hill-climbing --description="WorldQuant hill climbing" --working-directory="/root/worldquont/爬山代码" --property=Type=exec --property=MemoryHigh=805306368 --property=MemoryMax=1207959552 --property=MemorySwapMax=134217728 --setenv=PYTHONUNBUFFERED=1 /root/miniconda3/bin/python "/root/worldquont/爬山代码/全自动爬山算法.py" && systemctl start worldquant-ra-detection.service && systemctl is-active worldquant-hill-climbing.service worldquant-ra-detection.service'
```

### 3.3 隔离期间随时复查（确认仍保持暂停）

```bash
ssh guangzhou 'systemctl is-active worldquant-hill-climbing.service worldquant-ra-detection.service; ps aux | grep -iE "hill|ra_reach|worldquont" | grep -v grep'
```
