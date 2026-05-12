# project_doc_manage_sop · 项目文档生成与维护 (v1.0)
> 知识融合: README三步法 | Diátaxis四象限 | C4四层 | OpenAPI 3.1

## 执行摘要
① 决策树选类型→② 收集上下文(代码+git)→③ 按模板生成→④ code_run验证 → 🛑

## 文档类型决策树
```
README/主页→§2 | 架构/系统设计→§3 C4 | API文档→§4 OpenAPI
新人入职→§5 双文档 | 技术手册→§6 十章 | 未明确→Diátaxis(Tutorial/How-to/Reference/Explanation)
```
铁律：一个文档只承担一种角色，禁止混写。

## §2 README(三阶段)
**一代码探索**：根→入口→配置→DB→依赖→脚本→部署→测试(缺失跳过)
**二发布目标**：Dockerfile>k8s>fly.toml>vercel.json>CI>Procfile
**三模板**：项目简介→核心特性(5-8)→技术栈→前置条件→快速开始(5步)→配置→架构(Mermaid C4)→数据库→测试→部署→贡献→许可证

## §3 C4架构文档
Code→Component→Container→Context | 输出`docs/C4-Documentation/`

## §4 API文档
OpenAPI 3.1 YAML优先 | 每端点: Method+Path+Summary+Params+Res(200/400/401/500)

## §5 入职双文档
`docs/onboarding/` | Principal级(3-5k字:决策/哲学/权衡) | Newcomer级(1.5-3k字:搭建/结构/流程/坑)

## §6 技术手册
简介→快速开始→核心概念→详细指南→API→配置→部署→故障排除→FAQ→Changelog

## §7 维护
增量更新: `git diff`识别变更→只更新受影响章节 | 发布前执行`docs/release-checklist.md`

## §8 模板路径
README: `templates/readme-template.md` | C4: `templates/c4-*.md` | API: `templates/api-template.yaml`

## 🛑 验证门禁
文档类型正确 | 代码示例已code_run验证 | 模板格式完整 | 交叉引用有效 | changelog已更新

`VERDICT: PASS` / `VERDICT: FAIL`
