# TMWebDriver SOP

- 直接用web_scan/web_execute_js工具。本文件只记录特性和坑。
- 底层：`../TMWebDriver.py`通过Chrome扩展接管用户浏览器（保留登录态/Cookie）
非Selenium/Playwright，保留登录态

## 通用特性
- ⚠`await`需**显式`return`**才拿返回值
- web_scan自动穿透同源iframe；跨域需CDP/postMessage

## 限制(isTrusted)
- `isTrusted=false`，敏感操作首选**CDP桥**
- ⚠JS点击开不了新tab→换CDP
- Vue3组件：⭐优先vnode实例→见**vue3_component_sop**；CDP仅适合少选项可见场景
- 文件上传：⭐首选**DataTransfer API**：`new File → DataTransfer.items.add → input.files=dt.files → dispatch input+change`；CDP `setFileInputFiles` nodeId跨调用失效；备选ljqCtrl
- 物理坐标：`physX = (screenX + rect.x) * dpr`，`physY = (screenY + chromeH + rect.y) * dpr`；`chromeH = outerHeight - innerHeight`

## 导航
- web_scan不导航，切站用 `location.href='url'`

## Google图搜
- 禁硬编码class，点击用 `[role=button]`
- 文本`document.body.innerText`，大图按`naturalWidth`最大取src
- "访问"链接：遍历a找`textContent.includes('访问')`的href
- 缩略图：`img[src^="data:image"]`直接提取

## Chrome下载PDF
```js
fetch('PDF_URL').then(r=>r.blob()).then(b=>{const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='f.pdf';a.click();});
```
⚠需同源或CORS，跨域先导航到目标域

## 后台标签节流
- `setTimeout`被throttle到≥1min/次，避免轮询
- SPA需CDP `Page.bringToFront`前台才加载数据

## CDP桥(tmwd_cdp_bridge) ⭐首选
路径：`assets/tmwd_cdp_bridge/`(需安装，含debugger权限)
⚠TID自动生成到`config.js`(已gitignore)
调用：`web_execute_js`传JSON字符串，工具层自动走WS→background.js
```
'{"cmd":"cookies"}' | '{"cmd":"tabs"}' | '{"cmd":"cdp","tabId":N,"method":"...","params":{...}}' | '{"cmd":"batch","commands":[...]}'
```
- management：`{cmd:'management',method:'list|reload|disable|enable',extId:'...'}`
- contentSettings：`{cmd:'contentSettings',type:'automaticDownloads',pattern:'https://*/*',setting:'allow'}` — 绕过Chrome下载阻塞对话框；⚠`Browser.setDownloadBehavior`扩展中不可用
- ⭐batch：`{cmd:'batch', commands:[...]}` → `{ok:true, results:[...]}`
  - `$N.path`引用第N个结果(0-indexed)；⚠前序失败则`$N`静默undefined，检查每项ok
  - 子命令继承外层tabId；CDP懒attach复用session
  - 典型上传：getDocument(**depth:1**)→querySelector(`input[type=file]`)→setFileInputFiles
  - nodeId来源一致不混用；上传后补发`input`/`change`；检查`input.accept`
  - 瞬态input：缩短发现→setFile时间窗，优先同batch；⚠tabId默认sender.tab，跨tab需显式指定
- ⭐跨tab无需前台：指定tabId即可

## CDP点击（✅已验证）
三事件序列：mouseMoved→mousePressed→mouseReleased(间隔50-100ms)，省略mouseMoved致hover组件失效
- ⭐坐标=`getBoundingClientRect()`，无需修正
- ⚠**首次attach陷阱**：infobar推下页面→坐标偏移。✅解决：attach后先`mouseMoved(0,0)`预热再测量
- 下拉框：1.rect→CDP点开 2.option rect→CDP选中；⚠超出视口→换vnode
- zoom修正：`realX = x * visualViewport.scale * getComputedStyle().zoom`
- iframe：`finalX = iframeRect.x + elRect.x`；跨域：`Page.getFrameTree→createIsolatedWorld({frameId})→Runtime.evaluate({contextId})`；batch引用`$0.frameTree.childFrames`

## CDP文本输入(未验证BBS#23)
- `insertText`快但无key事件，受控组件补`input`；完整键盘用`dispatchKeyEvent`

## Shadow DOM穿透(未验证BBS#24/#25)
- `DOM.getDocument({depth:-1, pierce:true})`穿透closed Shadow
- getBoxModel八值中心用**四点平均**(⚠非对角线，rotate/skew时非矩形)
- querySelector不能跨Shadow写组合选择器，分步：host→shadow内子元素
- ⚠nodeId变更失效→用`backendNodeId`或重刷getDocument

## autofill
检测：`data-autofilled="true"`，Chrome保护值需点击释放
- ⚠必须先`Page.bringToFront`前台
- ⭐一键：bringToFront→mousePressed点任一字段(无需Released)→500ms→补input/change→点登录

## 截图
- ⭐`Page.captureScreenshot`(png,base64)，无需前台
- canvas验证码：`canvas.toDataURL()`

## simphtml调试
- 必须`code_run`注入JS（Python端无法模拟DOM）
- `TMWebDriver().set_session('url_pattern').execute_js(code)` → `{'data':value}`
- `str(simphtml.optimize_html_for_tokens(html))` — BS4 Tag需str()

## 连不上排查
①浏览器进程在跑？→不在则启动(⚠about:blank不加载扩展)
②18766端口在监听？→不在→`from TMWebDriver import TMWebDriver; TMWebDriver()`后台起master
③扩展装了？→读`Secure Preferences`→`extensions.settings`找`tmwd_cdp_bridge`
④都正常→请求用户

---

## 附录A: Process Memory Scanner
Hex/字符串内存搜索，支持LLM上下文模式。
```python
import sys; sys.path.append('../memory')
from procmem_scanner import scan_memory
results = scan_memory(pid, "48 8b ?? ?? 00", mode="hex", llm_mode=True)
```
```powershell
python ../memory/procmem_scanner.py <PID> "pattern" --mode string
python ../memory/procmem_scanner.py <PID> "pattern" --llm  # JSON输出推荐
```

## 附录B: Vision API
规则：①先`pygetwindow`枚举窗口 ②🚫禁全屏截图 ③能用标题/OCR解决的不调Vision
```python
from vision_api import ask_vision
result = ask_vision(image, prompt="描述", backend="claude", timeout=60, max_pixels=1_440_000)
```
