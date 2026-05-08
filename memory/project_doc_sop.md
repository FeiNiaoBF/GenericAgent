# project_doc_sop · 项目文档生成与维护 SOP (v1.0)
> 知识融合: README三步法 | Diátaxis四象限 | C4四层 | OpenAPI 3.1
> 复用工具: file_read(代码探索) | code_run(分析) | git(变更追踪)

## 执行摘要（≥1步执行前必读）
① 决策树选文档类型(README/架构/API/Onboarding)→② 收集上下文(代码+git变更)→③ 按模板生成→④ code_run验证代码示例 → 🛑 过验证门禁

## §0 触发
用户说: "写文档/README/架构文档/API文档/新人入职/更新文档/changelog"

## §1 文档类型决策树

```
用户需求
├─ "README" / "项目主页" ────────→ §2 README（三阶段）
├─ "架构" / "系统设计" ────────→ §3 C4（四层自底向上）
├─ "API文档" ───────────────────→ §4 API（OpenAPI 3.1优先）
├─ "新人入职" / "理解代码" ────→ §5 双文档
├─ "技术手册" / "详细文档" ────→ §6 十章结构
└─ 未明确 → Diátaxis选型: Tutorial(学习)/How-to(任务)/Reference(信息)/Explanation(理解)
```

> 铁律: 一个文档只承担一种角色，禁止混写。

## §2 README 生成（三阶段）

**阶段一: 代码探索** → 按顺序查: 根结构→入口点→配置→数据库→依赖→脚本→部署→测试（缺失跳过）
**阶段二: 识别发布目标** → Dockerfile > k8s > fly.toml > vercel.json > CI > Procfile
**阶段三: 模板写作**:

```markdown
# 项目名 (2-3句: 做什么/谁用)
## ✨ 核心特性 (5-8条)
## 🛠 技术栈 (语言/框架/DB/部署)
## 📋 前置条件 (必须安装的软件+版本)
## 🚀 快速开始 (克隆→安装→配置→初始化→启动 5步)
## ⚙️ 配置 (所有环境变量+默认值，从.env.example提取)
## 🏗 架构 (Mermaid C4 Container + 目录结构)
## 🗄 数据库 (类型/表数量/关键表)
## 🧪 测试 (运行命令/框架/覆盖率)
## 🚢 部署 (具体平台步骤)
## 🤝 贡献 (3-5步)
## 📄 许可证
```

## §3 C4 架构文档（四层自底向上: Code→Component→Container→Context）
- Code: 函数签名/类结构 | Component: 边界+接口+Mermaid | Container: 部署单元+API Spec | Context: 用户角色+外部系统(面向非技术)
- 输出目录: `docs/C4-Documentation/`

## §4 API 文档
- 优先 OpenAPI 3.1 YAML；备选 AsyncAPI / GraphQL Schema
- 每端点: Method+Path+Summary+Params+Req/Res(200/400/401/500)
- 每模型: 字段名+类型+必填+说明+示例值

## §5 入职双文档 → `docs/onboarding/`
- Principal级: 架构决策/设计哲学/关键权衡（3000-5000字）
- Newcomer级: 环境搭建/目录结构/开发流程/常见坑（1500-3000字）

## §6 技术手册 → 十章结构
简介→快速开始→核心概念→详细指南→API参考→配置→部署→故障排除→FAQ→Changelog

## §7 文档维护
- 增量更新: `git diff` 识别变更 → 只更新受影响章节
- 发布同步: 版本发布前执行 `docs/release-checklist.md`
- 写完后必须 code_run 验证代码示例可运行

## §8 模板速查
- README: `../memory/templates/readme-template.md`
- C4: `../memory/templates/c4-*.md`
- API: `../memory/templates/api-template.yaml`
- Onboarding: `../memory/templates/onboarding-*.md`

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 文档类型正确(README/架构/API/Onboarding)？ | |
| 代码示例已code_run验证可运行？ | |
| 模板格式完整(符合Diátaxis/C4)？ | |
| 交叉引用路径有效？ | |
| changelog已更新？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
