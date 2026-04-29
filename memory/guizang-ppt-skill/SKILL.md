# Guizang Magazine PPT Skill

## 概述
杂志风PPT单文件生成器。基于HTML/CSS，通过主题变量+布局骨架快速生成演示文稿，在浏览器中直接阅览。

## 工作流
1. **选主题**：从 `references/themes.md` 选一套，复制 `:root{}` 块
2. **拷模板**：复制 `assets/template.html` 到工作目录
3. **替换:root**：用选中主题的 `:root` 替换模板中的默认主题
4. **选布局**：从 `references/layouts.md` 选10种布局骨架
5. **填内容**：替换 `{PLACEHOLDER}` 为实际内容
6. **拼幻灯片**：按顺序组合 `<section>` 元素
7. **P0自检**：对照 `references/checklist.md` P0 清单自检
8. **阅览**：双击HTML打开/用 `python -m http.server` serve

## 核心约束
- 只能从5套主题中选择，不可自定义 hex
- 主题节奏：禁止连续3页同 theme
- >=8页时必须有 hero dark + hero light
- 大标题用衬线体（h-hero/h-xl），正文用非衬线体（body-zh）
- 无 emoji，用 Lucide 图标
- 图片高度用 `height:Nvh`，不用 `aspect-ratio`
- 禁止 `align-self: end`

## 文件结构
```
guizang-ppt-skill/
├── SKILL.md              # 本文件
├── assets/
│   └── template.html     # 单文件模板（含全部CSS类+示例slides）
└── references/
    ├── themes.md         # 5套主题色 :root{} 块
    ├── layouts.md        # 10种布局骨架
    ├── checklist.md      # P0/P1/P2/P3 质量清单
    └── components.md     # CSS类名速查
```

## 版本
v1.1 | 2026-04-30 | 新增表格(.data-table) + 图片占位(.img-placeholder) + L11/L12布局
