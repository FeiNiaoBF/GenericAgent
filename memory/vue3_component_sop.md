# Vue3 组件操作 SOP

## 触发
- 适用：Vue3中`click/dispatchEvent/focus`失效，或DOM变了但提交值没变。
- 验证看`payload`/store/组件实例值，别看DOM表象。
- 路线：表单→`nativeSetter+input/change`；Select/Dropdown/Autocomplete→`vnode→component→proxy`；富文本→实例API。

## 找实例
```javascript
const rootVnode = document.getElementById('app')._vnode;
function compByEl(v, el, d=0){
  if(!v||d>50) return null;
  const c=v.component;
  if(c){
    if(c.vnode?.el===el||c.subTree?.el===el) return c;
    if(c.vnode?.el?.contains?.(el)) return compByEl(c.subTree,el,d+1)||c;
    const r=compByEl(c.subTree,el,d+1); if(r) return r;
  }
  const kids=Array.isArray(v.children)?v.children:(v.dynamicChildren||[]);
  for(const k of kids){const r=compByEl(k,el,d+1); if(r) return r;}
  return null;
}
```

## Select/Dropdown
- 从目标DOM向上≤8层找proxy：有`onSelect/handleSelect/select/setValue`且有`computedOptions/options/items`；逻辑常在父级。
```javascript
function findSelect(el){for(let x=el,n=0;x&&n<8;x=x.parentElement,n++){
  const p=compByEl(rootVnode,x)?.proxy;
  if(p&&(p.onSelect||p.handleSelect||p.select||p.setValue)&&(p.computedOptions||p.options||p.items)) return p;
}}
const p=findSelect(targetElement), opts=p.computedOptions||p.options||p.items;
(p.onSelect||p.handleSelect||p.select||p.setValue).call(p, opts.find(o=>(o.label||o.text||o.value||String(o)).toString().includes('USD')));
```
- 选项必须取组件现有完整对象，可能是`{id,label}`/`{value,text}`/字符串；探测`$options.methods/setupState/exposed`。

## 普通字段/上传
```javascript
const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
s.call(inputEl,'新值');
inputEl.dispatchEvent(new Event('input',{bubbles:true}));
inputEl.dispatchEvent(new Event('change',{bubbles:true}));
```
- `textarea`换`HTMLTextAreaElement.prototype.value`；Date走`focus→setter→input/change→blur`；Button可`.click()`。
- File Upload按`tmwebdriver_sop`：定位`input[type=file]`后用DataTransfer/CDP，再派发`input+change`。

## 富文本
- 优先实例API：Quill `__quill.setText()/dangerouslyPasteHTML()/Quill.find`；Tiptap `__tiptap.commands.setContent()` / ref `.editor.commands.setContent()`；TinyMCE `tinymce.get(id).setContent()` / `activeEditor`；WangEditor `__wangEditor.setHtml()`；CKEditor `editor.setData()`。
- 查找：DOM私有字段→Vue `setupState/exposed`→全局变量→编辑器静态查找。
- 识别：`.ql-editor` Quill；`.ProseMirror` Tiptap；`.tox-edit-area`/iframe TinyMCE；`.w-e-text-container` WangEditor；`.ck-editor__editable` CKEditor5；`.cm-editor` CodeMirror6。
- 次选 `innerHTML+InputEvent` 只适合简单 wrapper；复杂用 CDP `Input.insertText`。

## 坑点
- Element Plus下拉可能Teleport到body，全局查`.el-select-dropdown__item`。
- TinyMCE在iframe内，操作`iframe.contentDocument.body`。
- 提交值可能来自editor实例/Pinia/Vuex store，非DOM。
- debounce后等300-500ms再验；prod minify会改方法名，结合行为+数据结构判断。
- 验证过：OrangeHRM Vue3+OXD；本地Vue3+Element Plus+Quill/Tiptap靶场（2026-05-09）。
