# 指引：环境与认证

## 用途
首次使用 / 认证失败 / 换环境时，让 MCP 可用。

## 最少路径
1. 安装依赖：运行 `cnhkmcp/untracked/配置前运行我_安装必要依赖包.py`。
2. 填凭据：`cnhkmcp/untracked/user_config.json`（或环境变量 `MCP_CONFIG_FILE`）。
3. 注册 MCP：按 `cnhkmcp/untracked/sample_mcp_config.json` 注册，启动 `platform_functions.py`。
4. 认证：调用 `authenticate`（参数留空则读配置）。

## 限制
- 未认证禁止调用任何平台数据工具。
- 凭据为明文，禁止写入日志 / 在对话中传播。
- 生物识别认证需图形界面 + Chromium（Playwright）。
- 本机 numpy 若损坏需先修复（`pip install --force-reinstall numpy`）。

## 相关
- 认证后查询字段：`evaluate/guide.md`。
