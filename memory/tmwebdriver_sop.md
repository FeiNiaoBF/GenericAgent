# TMWebDriver SOP
> 直接用 web_scan/web_execute_js 工具。文件仅记录特性和坑。
> 底层: `../TMWebDriver.py` 通过Chrome扩展接管用户浏览器(保留登录态/Cookie)

## 通用特性
- ⚠ `await` 需**显式`return`** 才能拿到返回值
- ✅ web_scan 自动穿透同源 iframe

## 导航
- `web_scan` 仅读当前页，切换用 `web_execute_js` + `location.href='url'`
- 新tab打开: 优先CDP点击；JS点击可能被弹窗拦截

## Google图搜
- class混淆禁硬编码；点击结果用 `[role=button]` div
- 大图: 遍历img按`naturalWidth`最大取src；缩略图: `img[src^="data:image"]`

## 限制(isTrusted)
- JS事件`isTrusted=false`，敏感操作(文件上传/部分按钮)可能被拦截→首选**CDP桥**
- 物理坐标: `physX=(screenX+rect中心x)*dpr`，`physY=(screenY+chromeH+rect中心y)*dpr`，`chromeH=outerHeight-innerHeight`

## CDP桥(tmwd_cdp_bridge扩展) ⭐首选
扩展: `assets/tmwd_cdp_bridge/` | TID: `config.js`(gitignore,首次自动生成)
调用: `web_execute_js` 传JSON字符串(工具层自动识别WS路由):
```js
web_execute_js script='{"cmd": "cookies"}'
web_execute_js script='{"cmd": "tabs"}'
web_execute_js script='{"cmd": "cdp", "tabId": N, "method": "...", "params": {...}}'
web_execute_js script='{"cmd": "batch", "commands": [...]}'
web_execute_js script='{"cmd": "management", "method": "list|reload|disable|enable", "extId": "..."}'
```
⭐batch: `{cmd:'batch', commands:[...]}` → `{ok:true, results:[...]}`
- `$N.path` 引用第N个结果字段(0-indexed)
- ⚠前序失败时后续`$N`引用静默undefined→检查results每项ok
- 典型文件上传: getDocument(depth:1)→querySelector→setFileInputFiles
- 瞬态input: 缩短发现→setFileInputFiles时间窗，优先同batch完成
- ⚠tabId: CDP默认sender.tab.id，跨tab需显式或batch内先tabs查
⭐跨tab操作无需前台: 指定tabId即可操作后台标签

## CDP点击
三事件序列: mouseMoved→mousePressed→mouseReleased(间隔50-100ms)
坐标修正(page有transform:scale/zoom): `realX=x*zoom; realY=y*zoom`
iframe合成: `finalX=iframeRect.x+elRect.x`
跨域iframe: `Page.getFrameTree`→`Page.createIsolatedWorld`→`Runtime.evaluate({contextId})`
batch链式: `$0.frameTree.childFrames` 匹配url，`$1.executionContextId` 传evaluate

## CDP文本输入
- insertText快但无key事件；受控组件补dispatch `input`事件
- 完整键盘: `dispatchKeyEvent`逐键

## CDP DOM穿透Shadow
- `DOM.getDocument({depth:-1, pierce:true})` 穿透closed Shadow
- querySelector不能跨Shadow组合选择器→分步: host→shadow内找子元素
- nodeId DOM变更后失效→用`backendNodeId`或重新getDocument
- getBoxModel中心: 四点平均(非对角) centerX=sum(x)/4

## autofill获取与登录
前置: 必须先`Page.bringToFront`(后台tab不释放)
一键释放: bringToFront→mousePressed点任一字段→等500ms→补input/change→点登录

## 截图/验证码
- CDP: `Page.captureScreenshot`(format:'png')→base64，全页高清
- 验证码: JS `canvas.toDataURL()` 拿base64

## 连不上排查
① 浏览器进程?→tasklist查，无则启动正常URL(⚠about:blank不加载扩展)
② WS 18766端口?→死则手动起 `from TMWebDriver import TMWebDriver; TMWebDriver()`
③ 扩展已装?→读Chrome Secure Preferences→extensions.settings搜tmwd_cdp_bridge
④ 以上正常→请求用户
