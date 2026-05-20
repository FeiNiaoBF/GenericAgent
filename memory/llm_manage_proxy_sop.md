---
name: llm_manage_proxy
description: 管理本地 LLM 代理链路，检查 CC Switch、New API 与 CLIProxyAPI 状态
---
# LLM Proxy 管理 SOP

## 链路门禁
- 先探测再修复：`GA/Claude Code → CC Switch → New API → CLIProxyAPI → OAuth/provider`。
- 拓扑：`127.0.0.1:15721` CC Switch → `localhost:3000` New API → `localhost:8200` CLIProxyAPI（Docker `8200→8317`）。
- 位置：CC Switch `%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe`，数据/日志 `~/.cc-switch/`；New API容器 `new-api`；CLIProxyAPI `D:\Creative_Studio\WorkSpace\Project\CLIProxyAPI`。
- 透传渠道（anyrouter/CC Switch/CRS）配置必须 `fake_cc_system_prompt: True`；CLIProxyAPI 需 `Authorization: Bearer <key>` 或 `x-api-key`，密钥只引用配置位置。

## 排查顺序
1. CC Switch：进程+`15721`。
2. current provider：GUI / `settings.json` / `cc-switch.db`，禁凭记忆。
3. New API：`new-api`容器、`localhost:3000`面板、渠道转发到 `http://localhost:8200`。
4. CLIProxyAPI：`8200→8317`，认证key来自 `config.yaml`。
5. 慢请求：New API统计 → CLIProxyAPI日志/session-affinity/OAuth账号。

## 缓存命中低
- 触发：长会话缓存命中显著低于未命中，接近 `1:10`。
- 先查 `llmcore.py`：`cache_control`稳定基座是否在动态system前；user是否首尾断点；`_record_usage`是否记录`cache_read/cache_creation/input_tokens/压缩状态`；`compress_history_tags`默认开启。
- 验证：`py_compile`；构造OpenAI扁平、Anthropic嵌套、无缓存字段usage；长历史压缩后结构完整且保留关键事实。

## 症状速查
- 连不上：CC Switch进程/15721/current provider。
- 401：`fake_cc_system_prompt`；CLIProxyAPI key来源。
- crash：`~/.cc-switch/logs/cc-switch.log`；`cannot move state from Destroyed`多为窗口框架噪声。
- provider错：GUI/settings/DB核实。
- 用量异常：New API统计、`cc-switch.db` rollup/request logs。
- `gpt-5.5`慢尾：验证链路仍是CC Switch→New API→CLIProxyAPI→OAuth，再查坏会话粘滞；偶发长尾可缩短`session-affinity.ttl`，单OAuth仍可能上游慢。

## 禁止
禁写`config.yaml`的`api-keys`；禁未确认provider就断言来源；禁把New API当OAuth源；禁无新信息反复重启，三次失败后升级分析或问主人。

`VERDICT: PASS` / `VERDICT: FAIL`
