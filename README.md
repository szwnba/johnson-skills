<div align="center">

# 🧰 Johnson Skills

#### 我自己收藏和在用的 AI Skill / MCP / Prompt 个人工具箱

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-13-10B981?style=for-the-badge)](#-skills-收藏)
[![Prompts](https://img.shields.io/badge/Prompts-1-F59E0B?style=for-the-badge)](#-prompts-自研)
[![MCP](https://img.shields.io/badge/MCP-记录中-8B5CF6?style=for-the-badge)](./mcp)

![Agent Skills](https://img.shields.io/badge/Agent_Skills-Standard-D97706?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-10B981?style=flat-square&logo=anthropic&logoColor=white)
![ZCode](https://img.shields.io/badge/ZCode-Compatible-3B82F6?style=flat-square)

</div>

个人仓库，只干三件事：

1. **备份** — 收藏的 skill 存本体，上游删库/跑路也不影响我重装
2. **自研** — 自己写的 skill、prompt、MCP 配方沉淀在这里
3. **一键恢复** — 换机器/重装环境时，从这里一条命令装回来

所有 skill 遵循 [Agent Skills](https://agentskills.io) 开放标准，Claude Code、ZCode、Codex 等 40+ Agent 通用。

---

## 📋 目录

| 分类 | 数量 | 说明 |
|---|---|---|
| [Skills（收藏）](#-skills-收藏) | 13 | 第三方开源 skill，均标注上游来源 |
| [Prompts（自研）](#-prompts-自研) | 1 | 自己写的深度研究命令 |
| [MCP](./mcp) | 记录中 | MCP 服务器配置与使用笔记 |

---

## 📦 安装方式

**方式一：让 Agent 自己装**（推荐）

在支持 Agent Skills 的工具里直接说：

```
帮我安装这个 skill：https://github.com/szwnba/johnson-skills/tree/main/skills/<skill-name>
```

例如 `skills/leader`、`skills/defuddle`。Agent 会自己 clone 到对应目录。

**方式二：命令行手动装**

```bash
git clone https://github.com/szwnba/johnson-skills /tmp/johnson-skills
cp -r /tmp/johnson-skills/skills/<skill-name> ~/.agents/skills/
```

**方式三：新机器整库恢复**

```bash
cp -r /tmp/johnson-skills/skills/* ~/.agents/skills/
```

> [!NOTE]
> 仓库地址：https://github.com/szwnba/johnson-skills

---

## 🗂 Skills（收藏）

| 名字 | 一句话 | 来源 |
|---|---|---|
| 🧭 [**leader**](./skills/leader) | 把一句话的想法拆成 agent 能独立跑完的目标任务书（先实测调研，再一次性提问 ≤5 个） | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) |
| 🧹 [**defuddle**](./skills/defuddle) | 网页 HTML 抽取为干净 Markdown（Defuddle CLI） | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) |
| 🗃 [**obsidian-markdown**](./skills/obsidian-markdown) | Obsidian 风格 Markdown：wikilink、callout、frontmatter、嵌入语法 | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) |
| ⌨️ [**obsidian-cli**](./skills/obsidian-cli) | 用 Obsidian CLI 读写 vault：笔记、任务、属性、插件开发 | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) |
| 📊 [**obsidian-bases**](./skills/obsidian-bases) | 创建/编辑 Obsidian Bases（.base 数据库视图：过滤、公式、汇总） | [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) |
| 🎨 [**frontend-design**](./skills/frontend-design) | 前端视觉设计审美指引，避免模板味的默认设计 | [anthropics/skills](https://github.com/anthropics/skills) |
| ⚛️ [**vercel-react-best-practices**](./skills/vercel-react-best-practices) | Vercel 官方 React/Next.js 性能优化规则库（90+ 条规则） | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) |
| 🔍 [**web-design-guidelines**](./skills/web-design-guidelines) | 按 Web Interface Guidelines 审查 UI 代码与可访问性 | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) |
| 🔎 [**find-skills**](./skills/find-skills) | 让 agent 帮你发现和安装新 skill | [vercel-labs/skills](https://github.com/vercel-labs/skills) |
| 🔥 [**grill-me**](./skills/grill-me) | 用连环追问打磨一个方案或设计 | [mattpocock/skills](https://github.com/mattpocock/skills) |
| 🔥 [**grilling**](./skills/grilling) | 同上的持续拷问模式（触发词驱动） | [mattpocock/skills](https://github.com/mattpocock/skills) |
| ⚡ [**using-superpowers**](./skills/using-superpowers) | superpowers 生态入口：会话开始先查 skill 再动手 | [obra/superpowers](https://github.com/obra/superpowers) |
| 🧠 [**typesafe-ai**](./skills/typesafe-ai) | 用 TypeSafe System One（Jev）把自然语言/应用状态变成代码可用的类型化判断 | [typesafe-ai/skills](https://github.com/typesafe-ai/skills) |

> 收藏的 skill 版权归原作者所有，各自目录内保留了上游的 LICENSE（如有）。
> 本仓库仅作个人备份与快速重装用途，如原作者有异议可联系移除。

---

## ✍️ Prompts（自研）

| 名字 | 一句话 |
|---|---|
| 📜 [**deep-research**](./prompts/deep-research.md) | 横纵分析法深度研究报告：纵向追发展史、横向比竞品，1~3 万字长文。原本是 ZCode 的 `/deep-research` 命令 |

---

## 🔌 MCP

见 [./mcp](./mcp)。目前记录了在用的 MCP/插件清单和收录格式模板，后续逐个补配置与使用笔记。

---

## 📝 如何新增内容

**新增一个收藏 skill：**

```bash
cp -r ~/.agents/skills/<skill-name> skills/<skill-name>
```

然后在本文件 Skills 表格加一行（名字/一句话/来源链接），commit。

**新增一个自研 prompt：**

把文件放进 `prompts/`，在本文件 Prompts 表格加一行。

**新增一个 MCP：**

在 `mcp/` 下建 `<名称>.md`，按 [mcp/README.md](./mcp/README.md) 里的模板写。

---

## 📄 许可证

本仓库的自研内容（prompts、后续自研 skill、文档）以 [MIT](./LICENSE) 开源。
第三方 skill 的许可与版权见各自目录。
