# 🔌 MCP 收录

这个目录存放 MCP（Model Context Protocol）服务器的**配置配方和使用笔记**。

MCP 服务器本体通常是 npx 包或本地服务，不往仓库里塞代码，只记录：是什么、怎么配、怎么用、踩过什么坑。

---

## 收录格式

每个 MCP 一个 `<名称>.md`，按这个模板写：

```markdown
# <MCP 名称>

- **来源**: npm 包名 / GitHub 仓库 / 本地服务
- **用途**: 一句话说明它干什么
- **状态**: 在用 / 备选 / 已弃用

## 配置

（JSON 配置片段。注意：API key 用 <REDACTED> 占位，真实 key 永远不入库）

## 使用笔记

- 典型调用场景
- 踩过的坑和 workaround
```

---

## 当前在用（ZCode 宿主内置/插件，备忘）

以下是当前 ZCode 环境里开箱即用的，不属于本仓库管理，仅作备忘清单：

| 名称 | 类型 | 用途 |
|---|---|---|
| web_reader | 内置 | 网页抓取转 Markdown（大模型友好输入） |
| node_repl | 内置 | 浏览器/计算机控制的 JS 内核 |
| 4_5v_mcp · analyze_image | 内置 | 远程 URL 图像的视觉分析 |
| image-search | 插件 | 联网图片搜索 |
| browser-use | 插件 | 浏览器自动化（导航/点击/截图/表单） |
| computer-use | 插件 | 原生桌面应用与 OS 级操作 |
| android-emulator | 插件 | 安卓模拟器构建/安装/UI 自动化全家桶 |

> 后续接入的外部 MCP（自建或第三方）逐个建 `.md` 收录到这里。
