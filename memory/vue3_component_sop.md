# Vue 3 组件 JS 操作 SOP

## 核心问题
Vue3自定义组件`isTrusted:false`事件不响应。解法：直接操作Vue组件实例。

## vnode遍历找组件
```javascript
const rootVnode = document.getElementById('app')._vnode;
function findCompByEl(vnode, targetEl, depth = 0) {
    if (depth > 50 || !vnode) return null;
    const comp = vnode.component;
    if (comp) {
        if (comp.vnode?.el === targetEl || comp.subTree?.el === targetEl) return comp;
        if (comp.vnode?.el?.contains?.(targetEl)) { const r = findCompByEl(comp.subTree, targetEl, depth+1); return r || comp; }
        const r = findCompByEl(comp.subTree, targetEl, depth+1); if (r) return r;
    }
    for (const arr of [vnode.children, vnode.dynamicChildren].filter(a => Array.isArray(a)))
        for (const child of arr) { const r = findCompByEl(child, targetEl, depth+1); if (r) return r; }
    return null;
}
```

## Select/Dropdown
⚠区分展示层(无效果) vs 逻辑层(有onSelect)，用`parentElement`找逻辑层
```javascript
// 循环向上查找(推荐)
function findSelectComp(el) {
  for (let up = 0; el && up < 8; el = el.parentElement, up++) {
    const comp = findCompByEl(rootVnode, el);
    if (comp?.proxy?.onSelect && comp.proxy.computedOptions?.length) return comp;
  }
  return null; // 找不到→CDP兜底
}
const comp = findSelectComp(targetElement);
comp.proxy.onSelect({id: 'USD', label: 'United States Dollar'});
```

## Input/Textarea(nativeSetter)
`el.value=x`不触发v-model，用原型setter：
```javascript
const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
setter.call(inputEl, '新值');
inputEl.dispatchEvent(new Event('input', {bubbles: true}));
inputEl.dispatchEvent(new Event('change', {bubbles: true}));
```
- Date：focus→setter→input→change→blur
- Button：`.click()`即可(Vue不检查button isTrusted)

## File Upload
```javascript
const dt = new DataTransfer();
dt.items.add(new File([content], 'name.txt', {type:'text/plain'}));
fileInput.files = dt.files;
fileInput.dispatchEvent(new Event('change', {bubbles: true}));
```
⚠CDP `setFileInputFiles`不触发事件，DataTransfer+dispatch是唯一纯JS方案

## 泛化探测(陌生Vue3站点)
1. `document.getElementById('app')?.__vue_app__`确认Vue3
2. findCompByEl从DOM反查组件
3. 探测能力：`comp.proxy.$options.methods` | `comp.setupState` | `comp.exposed`
4. 试调onSelect/handleSelect/select/setValue，传入选项对象
- ⚠Composition API逻辑在setupState；minify后需猜测；选项可能`{id,label}`或`{value,text}`

## 富文本编辑器
🚫禁只改innerHTML(不触发model，提交丢失)。优先找实例API：
| 类型 | 识别 | API |
|------|------|-----|
| Quill | `.ql-editor` | `el.__quill.setText()` / `.clipboard.dangerouslyPasteHTML()` |
| Tiptap | `.ProseMirror` | `el.__tiptap.commands.setContent()` |
| TinyMCE | `.tox-edit-area` | `tinymce.get(id).setContent()` |
| WangEditor | `.w-e-text-container` | `el.__wangEditor.setHtml()` |
| CKEditor | `.ck-editor__editable` | `editor.setData()` |
| CodeMirror | `.cm-editor` | `el.cmView` |

查找：DOM私有字段→Vue setupState/exposed→全局变量→Quill.find()
验证：拦截fetch/XHR看payload或`editor.getHTML()`(⚠看到≠提交对)

## 避坑
- Element Plus Select→Teleport到body，全局`.el-select-dropdown__item`
- TinyMCE在iframe→`iframe.contentDocument.body`
- debounce wrapper→改后等300-500ms
- Pinia/Vuex→store直接赋值

验证于：OrangeHRM(Vue3+OXD) + 本地Vue3+Element Plus+Quill/Tiptap靶场
