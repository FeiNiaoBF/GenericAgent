---
name: gcal_manage_schedule
description: Google Calendar日程创建、查询、修改与删除
---

# Google Calendar SOP (v1.0)

## 执行摘要（≥1步执行前必读）
1. 账号验证：切到`u/1`（主账号pai Yang），`web_scan`确认日视图
2. 操作：创建(URL方式⭐首选) / 查看 / 删除 → JS补填标题
3. 回验证：`saved≠verified`，导航回日视图`web_scan`确认 → 🛑 过验证门禁

## 0. 前置：账号与URL体系
- **URL格式**: `https://calendar.google.com/calendar/u/{N}/r/{view}`
  - `u/0`: 默认账号 | `u/1`: yeekox.pai (pai Yang, **主账号**)
  - views: `day`(日) | `week`(周) | `month`(月) | `eventedit`(新建/编辑)
- **账号验证**: 日视图 `web_scan` → 右上角头像alt/下拉账户名匹配 `pai Yang` → u/1
- ⚠**第一步必做**: 创建前切到 `u/1`，切前先 `web_scan` 扫日视图确认现有日程

## 1. 事件创建（URL方式 ⭐首选）
### 1.1 直接导航
```js
location.href = 'https://calendar.google.com/calendar/u/1/r/eventedit' +
  '?text=' + encodeURIComponent('📖 标题') +
  '&dates=YYYYMMDDTHHMMSSZ/YYYYMMDDTHHMMSSZ' +
  '&details=' + encodeURIComponent('描述') +
  '&ctz=Asia/Shanghai';
```
- 时区转换: 北京时间 → UTC = 减8小时 (如 10:15 → T021500Z)
- ⚠**URL参数中text可能不生效** → 导航后用JS填充: `document.querySelector('#xTiIn').value = title; dispatchEvent('input')`
### 1.2 保存
```js
var saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === '保存');
saveBtn.click();
```

## 2. 冲突检测（创建前必做）
- 导航到当日视图 → `web_scan text_only=true`
- 读取已存在事件列表，检测时间段重叠
- 存在冲突 → 报告用户决策（替换/调整/跳过）
- 同功能事件已存在 → 直接跳过

## 3. 事件删除
点击目标事件 → 弹出详情 → 删除按钮 → 二次确认

## 4. 典型坑
- ⚠**u/0≠u/1**: 默认导航到u/0，主账号是u/1，每次新开URL必须显式指定
- ⚠**URL params标题不可靠**: text参数有时被GCal忽略，必须JS补填
- ⚠**saved≠verified**: 保存后必须导航回日视图web_scan确认

## 5. 工具脚本
- `../memory/gcal_helper.py`: Python自动化 (add_gcal_event支持account_index)

## 🛑 验证门禁
|检查项|PASS条件|FAIL处理|状态|
|--------|---------|---------|------|
|账号正确|`web_scan`确认右上角为`pai Yang` (u/1)|切到u/1重来|
|日视图已确认|新建前`web_scan`扫日视图无冲突|调整时间避免冲突|
|保存后已验证|导航回日视图`web_scan`确认日程出现|重建事件|

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
