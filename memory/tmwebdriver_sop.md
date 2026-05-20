# TMWebDriver SOP

## 定位
- `web_scan`/`web_execute_js`；底层`TMWebDriver.py`+Chrome扩展保登录态，非Selenium。
- `web_execute_js` 内用 `await` 必须显式 `return`；`web_scan`穿透同源iframe，跨域iframe走CDP isolated world/postMessage。

## isTrusted / 上传
- JS事件`isTrusted=false`，敏感点击/上传可能拦截；优先CDP桥/组件实例法。
- Vue3 Select/Dropdown 先看`vue3_component_sop`；少量可见选项可CDP坐标点。
- 文件上传首选DataTransfer：`File→DataTransfer→input.files→input/change`；CDP`setFileInputFiles`仅同batch同链nodeId可靠。
- 物理坐标：`physX=(screenX+rect.cx)*dpr`，`physY=(screenY+outerHeight-innerHeight+rect.cy)*dpr`。

## CDP桥
- 扩展：`assets/tmwd_cdp_bridge/`；首次生成gitignore的`config.js`TID。
- `web_execute_js`的`script`可直接传JSON：
```js
{"cmd":"tabs"}
{"cmd":"cookies"}
{"cmd":"cdp","tabId":N,"method":"Page.bringToFront","params":{}}
{"cmd":"batch","tabId":N,"commands":[...]}
{"cmd":"management","method":"list|reload|disable|enable","extId":"..."}
{"cmd":"contentSettings","type":"automaticDownloads","pattern":"https://*/*","setting":"allow"}
```
- batch子命令继承外层`tabId`；`$N.path`引用第N个结果；须检查每项`ok`。
- 上传batch：`getDocument(depth:1)→querySelector(input[type=file])→setFileInputFiles`；不混nodeId，必要补`input/change`。
- 多 input 用 `accept`/父容器区分；瞬态 input 要同 batch；跨 tab 指定 `tabId`，无需前台。

## CDP点击/坐标
- 通用三事件：`mouseMoved→mousePressed→mouseReleased`，间隔50-100ms；省hover可能使MUI/AntD下拉失效。
- 稳定后CDP坐标=`getBoundingClientRect()`；首次attach可能有20px infobar，先`mouseMoved(0,0)`预热再测。
- 下拉：测 select rect 点开→出现后测 option rect 点选；大量/出视口优先 vnode。
- zoom/scale按`visualViewport.scale`/CSS zoom修正；iframe坐标`iframeRect+elRect`。
- 跨域iframe：`Page.getFrameTree→Page.createIsolatedWorld(frameId)→Runtime.evaluate(contextId)`；桥里`Target.attachToTarget`可能被拒。

## 文本/Shadow/autofill
- CDP`insertText`快但无key事件；受控组件补`input`，完整模拟用`dispatchKeyEvent`。
- closed Shadow：`DOM.getDocument({depth:-1,pierce:true})`；querySelector分段进shadow；DOM变更后nodeId失效，重取或用backendNodeId。
- `getBoxModel` 中心取 content 四点平均，别用对角线平均。
- autofill：必`Page.bringToFront`；`mousePressed`任一字段释放全页保护值；等500ms补`input/change`再提交。

## 常用/排障
- 导航：`web_scan`只读当前页，换站用`web_execute_js`设`location.href`。
- Google图搜：禁硬编码混淆class；用role/text；弹窗后从`body.innerText`、最大`naturalWidth`图、含"访问"的a提取。
- PDF下载：同源/CORS用`fetch(url).blob()`后a下载；跨域先导航到目标域。
- 后台页：Chrome后台`setTimeout`被节流；SPA加载先`Page.bringToFront`。
- 截图：`Page.captureScreenshot`前后台可用；验证码canvas/img优先`toDataURL()`。
- simphtml调试：`TMWebDriver().set_session(url).execute_js(code)`；`str(simphtml.optimize_html_for_tokens(html))`。
- 连不上：Chrome非内部页→18766 master/`TMWebDriver()`→扩展安装(Secure Preferences)→仍失败请求用户。

## 边界
- 只写TMWebDriver/CDP浏览器控制；Process Memory Scanner、Vision API等不得放入。
- 验收：`VERDICT: PASS` / `VERDICT: FAIL`。
