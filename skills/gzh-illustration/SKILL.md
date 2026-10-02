---
name: gzh-illustration
description: 为公众号文章生成配图的技能，双模式，AI 插画（agnes-ai 中转生图）与数据信息图（HTML 渲染截图）。当用户提到 生成配图、公众号配图、文章配图、头图、封面图、插画、生图、画一张图、给稿子/文章配图，或要求为 obsidian 库 drafts/ 稿件补充视觉素材时使用；即使用户只说「给这篇配几张图」「来个头图」也应触发。产物按库规存 drafts/images/ 并以 markdown 相对路径嵌入稿件。
---

# gzh-illustration — 公众号配图生成

为公众号文章产出配图。先判断用哪种模式，再按对应流程执行，产物统一落 obsidian 库 `drafts/images/`。

**选模式**：
- **AI 插画**（默认）——头图、氛围图、叙事意象图（如「凌晨四点的图书馆员」这类把文章比喻画出来的图）。
- **数据信息图**——图中出现数字、构成、流向、时间线的图。数字必须取自真实数据源（库内 log、manifest、git），一个都不许编；纯氛围图不要硬塞数据。

## 第 0 步，凭证（模式 A 用）

API key 在 `/home/johnson/.zcode/workspace/default/obsidian/raw/assets/agnes-ai.md`（git 忽略区）。读取方式：

```bash
KEY=$(grep -oP '(?<=API Key：)sk-\S+' "$KEY_FILE")
```

规则与原因：key 永不进 git、log、汇报正文；命令行只经变量引用，不在明文里重复它。凭证文件不存在时，先向库主人要 key，按库规 AGENTS.md 归档到 `raw/assets/`（先 `git check-ignore` 验证该目录确实被忽略，再写入），之后才能调用。

## 模式 A，AI 插画（agnes-ai 生图）

用技能自带的脚本，别手写 curl（脚本处理了 key 提取、JSON 拼装、b64 解码三件易错事）：

```bash
~/.agents/skills/gzh-illustration/scripts/gen.sh "prompt" 输出路径.png [size] [model]
```

- model 默认 `agnes-image-2.5-flash`（旧版 `agnes-image-2.1-flash`），size 默认 `1792x1024`。
- 已验证行为（2026-09-28 实测）：OpenAI 兼容 `/v1/images/generations`，中文 prompt 直接用，秒级返回 b64_json；size 参数收但执行宽松（要 1792x1024 实回 1312x736，恰为公众号 16:9 规格）。
- 若报 size 相关错误，去掉 size 重试；若返回里只有 url 没有 b64_json，脚本会自动按 url 下载。

**prompt 写法**（这是出图质量的最大变量）：
1. 先读稿件，找文章的核心意象和情绪（如「员工手册」「图书馆员」「凌晨四点」），prompt 围绕它写，不要泛泛的「科技感插画」。
2. 套路，内容主体 + 风格词 + 用途。风格词库，扁平插画 / 色彩克制 / 暖色点缀 / 主体居中 / 四周留白 / 横版构图；用途词写「公众号文章配图」。
3. **图内不要文字**。AI 生成中文必乱码，公众号的标题字后期在编辑器里排。

**验收**：生成后必须用 Read 工具打开 PNG 亲眼看，检查乱码文字、残肢、错误器官、无意义元素。不合格就改 prompt 重 roll（换措辞或换风格词，同一 prompt 原样重试没意义），最多 3 次，还不行就把已得结果给库主人并说明差距。

**成套图**：多张图保持同一串风格词不动，只换场景词，视觉才统一。

## 模式 B，数据信息图

1. 从真实数据源算好数字，列在草稿里先自查一遍。
2. 写自包含 HTML 到 `/tmp`，画布 1080px 宽（高度按内容 675-760），字体 `Noto Sans CJK SC`（先用 `fc-list :lang=zh` 确认存在），深色 GitHub 风（#0d1117 底、#e6edf3 字、绿 #3fb950/蓝 #58a6ff/橙 #f0883e 强调），图底标注数据源。
3. 本地服务 `python3 -m http.server <port> --bind 127.0.0.1`（后台），按 control-browser 技能的引导：`agent.browsers.getForUrl()` 选后端 → `tabs.list()` 绑定/新建标签 → `setViewportSize` 与画布一致 → `goto` → `waitForLoadState(domcontentloaded)` → 截图并在同一 cell 里 `nodeRepl.emitImage` + 写文件。
4. 已知坑：画布高度不够会裁掉底部内容（截图后看一眼脚注在不在）；HTML 改过必须 reload 再截。

## 落位与嵌入（两种模式相同）

- 存 `/home/johnson/.zcode/workspace/default/obsidian/drafts/images/`，命名 `AI生图-描述.png` 或 `配图N-描述.png`。
- 稿件嵌入用 markdown 相对路径 `![说明](images/文件名.png)`，这是「Obsidian ✓ + GitHub 网页 ✓」双兼容格式；**不要换成 `![[wiki嵌入]]`**（GitHub 不渲染）。稿件在 `drafts/` 下，所以相对路径是 `images/…`。
- 查看端兼容表（用户问「图怎么不显示」时先答这个）：Obsidian ✓，GitHub 网页（登录）✓，ZCode/网页预览 ✗（不解析相对路径本地图片，属查看端限制，不是稿件问题），GitHub 手机 App 支持差。
- 头图位在标题之下第一段之前；插图紧贴对应段落。

## 收尾（库内产物才需要）

向 log.md 追加一行（格式 `[YYYY-MM-DD HH:mm] 其他｜变化摘要｜遗留问题`，不含 key），`git add` 产物 + log 后 commit + push；push 被拒先 `git pull --rebase`，log.md 冲突按库惯例双侧保留。raw/assets/ 永不提交。

## 示例

```bash
~/.agents/skills/gzh-illustration/scripts/gen.sh \
  "扁平插画风格的公众号文章配图，深夜的图书馆，一个圆头圆脑发着柔光的可爱小机器人站在高大的深色书架前，把几本发光的书放回书架，窗外是凌晨四点泛着深蓝的城市天际线，一盏暖黄色台灯，画面安静温馨，色彩克制，主体居中，四周有留白，横版构图" \
  /home/johnson/.zcode/workspace/default/obsidian/drafts/images/AI生图-凌晨四点的图书馆员.png
```
