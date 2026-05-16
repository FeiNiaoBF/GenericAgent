# LLM Proxy SOP · CC Switch + New API

> 版本: v1.0 | 创建: 2026-05-11
> 来源: 工具实测 + mykey.py + cc-switch.db + Docker确认

---

### 当前主链路

```text
Claude Code / GA
  ↓
CC Switch localhost:15721
  ↓
New API localhost:3000
  ↓
CLIProxyAPI localhost:8200(host 8200 → container 8317)
  ↓
Codex OAuth(auths/)
  ↓
gpt-5.5
```

用途分层：
- `CC Switch`: 本机入口、provider切换、给Claude Code/GA提供本地兼容API。
- `New API`: 渠道管理、统计、配额、中转到CLIProxyAPI。
- `CLIProxyAPI`: 直接对接CLI OAuth/上游凭据，暴露OpenAI兼容API。
- `Codex OAuth`: 当前`gpt-5.5`实际认证来源。

### 关键路径
- exe: `%LOCALAPPDATA%\Programs\CC Switch\cc-switch.exe`
- 数据: `~/.cc-switch/` (settings.json + cc-switch.db + auth文件)
- 日志: `~/.cc-switch/logs/cc-switch.log`

### 本地代理
- `settings.json` → `enableLocalProxy: true`
- 端口: **15721** (GA mykey.py中 `http://127.0.0.1:15721`)
- key校验: **不做** → 填 `sk-cc-switch-local` 即可

### DB结构 (SQLite: cc-switch.db)
核心表: `providers` / `provider_endpoints` / `proxy_config` / `proxy_request_logs` / `model_pricing` / `usage_daily_rollups`

providers表字段: id, app_type(claude/codex/gemini), name, settings_config(JSON), website_url, category, provider_type, is_current, cost_multiplier, limit_daily_usd, limit_monthly_usd

### 当前活跃配置
| 类型 | Provider | ID前缀 |
|------|----------|--------|
| Claude | xiaomimimo.com | dd9a91d1 |
| Codex | (见settings) | 96cee0b0 |
| Gemini | Google Official | 887caf02 |

### GA对接 (mykey.py)
```python
native_claude_config0 = {
    "name": "cc-switch-mimo",
    "apikey": "sk-cc-switch-local",
    "apibase": "http://127.0.0.1:15721",  # CC Switch本地端口
    "model": "mimo-v2.5-pro",
    "fake_cc_system_prompt": True,  # ★透传渠道必须开
    "thinking_type": "adaptive",
}
```

### 避坑
- `fake_cc_system_prompt: True` — 透传渠道(anyrouter/CC Switch/CRS)必开，否则上游收不到完整system prompt
- `enableClaudePluginIntegration: true` — 插件集成模式
- auth: codex_oauth(含refresh_token自动续期) + copilot_auth
- DB每天自动backup (backups/目录, 最多保留~10天)
- app_type区分: claude/codex/gemini三个独立provider链
- crash常见: `cannot move state from Destroyed` (tao框架窗口事件，无害)

---

## 2. New API (API管理平台)

**本质**: Docker部署的API中转管理面板(calciumion/new-api)

### 部署
- 容器: `new-api` (calciumion/new-api:latest)
- 端口: **0.0.0.0:3000** → 容器3000
- 管理面板: `http://localhost:3000`

### 用途
- 多模型API key统一管理
- 用量统计/配额控制
- 当前链路中作为 `CC Switch → New API → CLIProxyAPI` 的中转层
- 当前渠道名: `CLIProxyAPI-OpenAI`
- 上游目标: `http://localhost:8200`

### 排查要点
- New API负责渠道、统计、配额和转发，不负责Codex OAuth本身。
- 慢请求要先看New API请求统计，再下钻CLIProxyAPI日志。
- 如果CC Switch能通但`gpt-5.5`慢，优先确认是否命中正确New API渠道。

---

## 3. CLIProxyAPI (本地API代理)

**本质**: CLI工具→OpenAI/Gemini/Claude兼容API的代理服务端 (比New API更底层，直接对接CLI OAuth)

### 关键路径
- 项目: `D:\Creative_Studio\WorkSpace\Project\CLIProxyAPI`
- 配置: 同目录下 `config.yaml` (386行)
- 本地: **http://127.0.0.1:8200** (Docker host 8200 → container 8317；容器内仍监听8317)

### API Key认证
- Key: 见项目配置文件 `config.yaml` 的 `api-keys`，不要写入记忆或SOP明文。
- 请求头: `Authorization: Bearer <key>` 或 `x-api-key: <key>`
- **会校验key** (不像CC Switch本地模式跳过)

### 核心配置速查
| 配置项 | 值 | 说明 |
|--------|-----|------|
| port | 8317 | 本地代理端口 |
| request-retry | 3 | 失败自动重试(403/408/5xx) |
| max-retry-credentials | 0 | 0=试所有credential |
| disable-cooling | false | 启用冷却调度 |
| quota-exceeded.switch-project | true | 配额耗尽自动切项目 |
| quota-exceeded.antigravity-credits | true | Claude用credits兜底 |

### 支持的Provider类型
- **gemini-api-key**: Gemini OAuth key，支持prefix/excluded-models
- **codex-api-key**: Codex OAuth key，支持proxy-url
- **claude-api-key**: Claude OAuth key，支持prefix
- **openai-compatibility**: 第三方OpenAI兼容API(如openrouter)，支持自定义header/模型别名/round-robin池
- **vertex-api-key**: Vertex AI key，支持base-url覆盖
- **ampcode**: Amp CLI集成，支持上游key映射/model-mappings

### 高级特性
- **模型别名**: 同一alias可映射多个上游模型→round-robin负载均衡
- **prefix路由**: provider设prefix后请求格式 `prefix/model-name`
- **per-key proxy**: 每个key可单独设socks5/http代理或"direct"
- **TLS**: 可配cert+key启用HTTPS
- **内置管理面板**: `disable-control-panel: false` 可下载Web面板

### GA对接 (待配置)
mykey.py中暂无CLIProxyAPI配置。如需接入:
```python
native_claude_config_cliproxy = {
    "name": "cli-proxy-api",
    "apikey": "<从CLIProxyAPI config.yaml 的 api-keys 读取，不写入记忆>",
    "apibase": "http://127.0.0.1:8200",
    "model": "待确认",  # 取决于CLIProxyAPI接入的provider
}
```

### 避坑
- key必须配，不填key会401
- host="" 监听所有接口，生产环境建议改为 `127.0.0.1`
- openai-compatibility的models字段必填(即使只用alias映射)
- quota-exceeded联动: switch-project + switch-preview-model 双重兜底
- `force-model-prefix: false`(默认) → 无前缀请求只用无前缀credential

---

## 4. 三工具关系图

```
GA (GenericAgent)
  ├─ mixin_config (故障转移链)
  │    ├─ [1] cc-switch-mimo → localhost:15721 (CC Switch)
  │    │                          ├─ xiaomimimo.com → Claude API
  │    │                          ├─ DeepSeek (备选)
  │    │                          └─ 其他provider...
  │    ├─ [2] cc-deepseek → api.deepseek.com/anthropic (直连)
  │    └─ [3] gemini-pro → generativelanguage.googleapis.com
  │
  └─ New API (localhost:3000)
       └─ 可作为独立上游接入CC Switch或GA
```

## 5. 排障速查
| 症状 | 检查 |
|------|------|
| GA连不上LLM | CC Switch进程在否？端口15721能curl？ |
| 401错误 | fake_cc_system_prompt开了没？CLIProxyAPI key是否来自配置文件？ |
| CC Switch crash | 看logs/cc-switch.log，tao框架窗口crash通常无害重启即可 |
| provider切换 | CC Switch GUI切换或改settings.json的currentProviderClaude |
| 用量异常 | 查DB的usage_daily_rollups表 |
| `gpt-5.5`慢尾 | 先确认完整链路是否仍是`CC Switch→NewAPI→CLIProxyAPI→Codex OAuth`；再查New API请求统计；最后查CLIProxyAPI session-affinity与OAuth账号状态 |
| 偶发长尾但成功 | 已实测把CLIProxyAPI `session-affinity.ttl` 从1小时改到5分钟可降低粘滞坏会话影响，但单OAuth账号仍可能有上游长尾 |
