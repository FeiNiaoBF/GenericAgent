---
name: resume
description: 修改简历内容、结构与项目表达
---
# 简历/CV优化 · resume_sop

## 触发与输入
触发：`改简历` / `优化简历` / `写CV` / `投XX公司` / `简历适配`。
必须先拿到：简历源文件（Word/PDF/LaTeX/Markdown）+ 目标岗位JD；没有JD时只做通用版。

## 流程
1. 解析简历：读取源文件；PDF优先结构化解析，乱码则转Markdown手工重建。
2. 重建结构树：基本信息 / 教育 / 工作经历 / 项目 / 技能 / 证书等。
3. JD匹配：提取硬技能、软技能、行业术语、工具/证书、高频动词名词。
4. 差距清单：已有需突出 / 可重述补齐 / 完全缺失需问主人。
5. 内容优化：统一时态、日期`YYYY.MM`、列表风格；删除弱词、重复、过时技术。
6. ATS注入：关键词自然放入技能与经历，单条bullet关键词密度≤15%。
7. 量化强化：优先使用 `动作 + 对象 + 方法 + 量化结果`，当前工作用现在时，过往用过去时。
8. 输出版本：通用版或定向版；文件名含日期+目标公司；交付Markdown+PDF。

## 写作标准
- 使用 CAR/STAR：情境 → 行动 → 结果 → 量化。
- 每条bullet尽量带数字：增长%、节省时间、交付周期、用户数、收入、团队规模。
- 中文简历通常1页；英文简历严格1页，Times New Roman/Calibri，10–12pt。
- ATS友好：禁止表格、文本框、分栏、图片图标；标题用纯文字+粗体。
- LaTeX需求可用 `resume-cv-builder` 模板渲染。

## 自研项目写法
写主人项目或进行中项目前，必须查真实仓库与文档，不凭记忆编造。
提取维度：定位 / 技术栈 / 架构 / 已实现能力 / 可量化结果 / 与JD匹配点。

AgentDock默认素材：
- 路径：`D:\Creative_Studio\WorkSpace\Project\AgentDock`
- 定位：桌面AI工作台 / Agent客户端
- 技术栈：Tauri2 + React19 + TypeScript + Vite7 + Markdown渲染
- 架构：Workbench Modular Core + ACP + GA扩展
- MVP：Tauri/WebView、Python bridge、JSON-RPC stdio、ACP session、多Tab、流式消息、turn折叠、ask_user、abort
- 原则：GA core不改；进行中项目只写已验证事实；未知指标问主人，不捏造。

## 交付门禁
- 自查：ATS友好、语法、格式一致性、关键词自然度。
- 朗读检查：避免ATS过度优化导致别扭。
- 超页处理：压缩次要经历、合并短段、缩减技能到JD相关Top 8–10。
- 最终定稿前给主人过目确认。

`VERDICT: PASS` / `VERDICT: FAIL`
