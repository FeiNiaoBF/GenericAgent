# Web 工具链初始化执行 SOP (v1.0)

若 web_scan 和 web_execute_js 已测试可用，无需执行此 SOP。
仅供初始安装时，code_run 可用但 web 工具尚未配置的场景。

## 执行摘要（≥1步执行前必读）
1. 仅首次安装时执行；若 `web_scan` 已可用 → 跳过本 SOP
2. 打开 `chrome://extensions` → 加载 `../assets/tmwd_cdp_bridge/` 扩展
3. 用 `start "" "https://www.baidu.com"` 打开正常页面 → `web_scan` 验证 → 🛑 过验证门禁

## 目标
在仅具备系统级权限（code_run）时，建立 Web 交互能力（web_scan / web_execute_js）。

## 前置：检测浏览器

## 安装 tmwd_cdp_bridge 扩展
扩展路径: `../assets/tmwd_cdp_bridge/`（MV3 Chrome 扩展，含 CDP debugger + scripting + cookie 能力）

### 自动打开扩展管理页
`chrome://extensions` 无法通过命令行或 JS 打开，需用剪贴板+地址栏方案

### 安装步骤（chrome扩展页难以自动化）
1. 打开扩展管理页，开启「开发者模式」
2. 点击「加载已解压的扩展程序」，选择 `assets/tmwd_cdp_bridge/` 目录，或让用户直接拖入
3. 显示"错误"不用管，一般只是因为还没连上GA

## 验证
⚠ web_scan 显示「没有可用标签页」不一定是扩展没装好，可能是浏览器未打开或只有 blank 页。
此时禁止乱试，先用 `start "" "https://www.baidu.com"` 打开一个正常页面，再 `web_scan` 确认。
若仍不可用，无法自动探测默认浏览器是哪个、插件装在了哪个浏览器、或是否已安装——此时请求用户协助。

## 🛑 验证门禁（必须执行，否则流程未完成）

| # | 验证动作 | 工具 | 预期结果 | PASS/FAIL |
|---|----------|------|----------|-----------|
| 1 | 浏览器页面打开 | `start "" "https://www.baidu.com"` | 浏览器有新标签页加载正常网页 | |
| 2 | web_scan可读 | web_scan | 返回页面HTML/文本内容，非"没有可用标签页" | |
| 3 | web_execute_js可用 | web_execute_js | `document.title` 返回页面标题，非空/非error | |
| 4 | 扩展连接 | web_execute_js | CDP命令可执行（如截图），无超时 | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`