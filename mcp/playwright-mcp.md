# Playwright MCP

- **来源**: npm 包 [`@playwright/mcp`](https://www.npmjs.com/package/@playwright/mcp) / [GitHub: microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)（微软官方，Apache-2.0，37k+ stars）
- **用途**: Playwright 官方 MCP 服务器。让 LLM 通过**无障碍树快照**（非截图）操作网页：导航、点击、填表、拖拽、tab 管理等，无需视觉模型
- **状态**: 收藏备选（未接入日常环境；日常浏览器自动化优先用仓库里的 [playwright-cli skill](../skills/playwright-cli)）
- **要求**: Node.js 18+

## 配置

各 MCP 客户端通用的标准配置：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

Claude Code 一条命令接入：`claude mcp add playwright npx @playwright/mcp@latest`

### 常用启动参数（加在 args 里）

| 参数 | 说明 |
|---|---|
| `--browser <chrome\|firefox\|webkit\|msedge>` | 指定浏览器（默认 chrome） |
| `--headless` | 无头模式（默认有头） |
| `--caps <vision,pdf,devtools>` | 附加能力：截图视觉/PDF/devtools |
| `--user-data-dir <path>` | 浏览器 profile 目录，**复用登录态**（不指定则临时目录） |
| `--storage-state <path>` | 从 storage state 文件恢复会话（isolated 模式下的登录态复用） |
| `--cdp-endpoint <endpoint>` | 连接已运行的浏览器 CDP 端点（预登录浏览器直接接管） |
| `--isolated` | profile 只存内存不落盘 |
| `--device "iPhone 15"` / `--viewport-size "1280x720"` | 设备模拟 / 视口尺寸 |
| `--proxy-server <url>` | 走代理 |
| `--save-session` | 保存会话到输出目录 |
| `--timeout-action 5000` / `--timeout-navigation 60000` | 动作/导航超时（ms） |

每个参数都有对应环境变量形式（如 `PLAYWRIGHT_MCP_BROWSER`）。完整参数表见[官方 README](https://github.com/microsoft/playwright-mcp#configuration)。

## 使用笔记

- **MCP 还是 CLI？官方自己给了判断标准**：coding agent 场景优先用 [playwright-cli + skill](https://github.com/microsoft/playwright-cli)——CLI 调用更省 token，不用往上下文里塞大工具 schema 和完整无障碍树；MCP 适合需要**持续浏览器状态**的场景（探索式自动化、长程自治任务、自愈测试），维持浏览器上下文比 token 成本更重要时选它。两个我仓库里都收了：skill 见 `skills/playwright-cli`，本文件是 MCP 配方。
- 核心卖点是确定性：基于结构化的无障碍树定位元素，规避截图方案的坐标歧义问题。
- 登录态复用三条路：`--user-data-dir`（整 profile）、`--storage-state`（cookie/storage 快照）、`--cdp-endpoint`（直接连手工预登录好的浏览器实例）。
- 安全相关：`--allowed-origins` / `--blocked-origins` 可控访问范围，但官方明确说明**不构成安全边界**、不影响重定向。
