---
name: gzh-publisher
description: 把 obsidian 库 drafts/ 稿件发布到微信公众号的完整管线：扫码登录、新建图文、受信任粘贴注入正文、GTK 剪贴板传图、填摘要、设封面、存草稿（可延伸群发/仅发布）。当用户提到 发公众号、发布文章、发到公众号后台、公众号草稿、群发、推送文章，或要求把某篇稿件（如 drafts/ 下的 md）发上公众号时使用；即使用户只说「把这篇发上去」「存个草稿到公众号」也应触发。
---

# gzh-publisher — 公众号发布管线

把 drafts/ 的 markdown 稿件送进公众号后台，默认终点是**草稿保存完成**（发表让库主人自己定）。2026-09-28 全流程实战验证。

前置：稿件在 obsidian 库 `drafts/`（图在 `drafts/images/`）；浏览器操作遵循 control-browser 技能的引导（bootstrap、tabs.list 绑定标签、快照优先）。本技能与 gzh-illustration 配套（缺配图先生成）。

## 流程总览

```
登录(用户扫码) → 新建图文(带token直连URL) → 注入标题 → 粘贴正文 → 逐张传图
→ 填摘要 → 设封面(从正文选择) → 保存草稿 → 汇报（终点）
```

**不包含 AI 声明步骤**（库主人 2026-09-28 指示）。若发表时平台弹出创作来源声明的拦截提示，停下来把选项报给库主人，由其当场决定，不代选。

## 1. 登录

1. `agent.browsers.getForUrl("https://mp.weixin.qq.com/")` → 新标签 → goto 首页。
2. 截图给用户扫码（`nodeRepl.emitImage`）。二维码 1-2 分钟过期，用户说「刷新了」就 reload 再截。
3. 轮询 `tab.url()`（每 5s，≤100s）：匹配 `cgi-bin/home` 即登录成功。
4. **从 URL 提取 token**（后续所有直连 URL 都要带）：`token=数字`。

登录态一次扫码全程有效；下次群发验证是另一码事（见第 9 节）。

## 2. 新建图文

首页「文章」按钮点击无效（事件挂在父级卡片），直接 goto：

```
https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token=<TOKEN>&lang=zh_CN
```

编辑器加载后先关「我知道了」引导弹窗（不关会挡住正文区，坐标点击全落空）：

```js
// 页面内点可见节点（playwright click 会卡在隐藏节点上）
const els = [...document.querySelectorAll('button, a, .weui-desktop-btn')]
  .filter(e => e.textContent.trim() === '我知道了' && e.offsetParent);
if (els.length) els[els.length-1].click();
```

编辑器结构：**两个 .ProseMirror，[0]=标题 [1]=正文**。

## 3. 标题

```js
const t = document.querySelectorAll('.ProseMirror')[0];
t.focus();
document.execCommand('insertText', false, '标题文本');
```

## 4. 正文注入（最大的坑在此）

**合成 ClipboardEvent('paste') 会被编辑器直接丢弃**，必须走受信任键盘事件：

1. 跑 `scripts/md2html.py <稿件.md> /tmp/gzh_pub/`，产出：
   - `article-text.html` — 纯文本富排版页（无图，图片单独走第 5 步）
   - `plan.json` — 标题、图片顺序、每张图的锚点段落前缀
   - 转换规则已内置：剥 frontmatter、剔模板签名行（`>` 开头）、段落套公众号排版样式。
2. `cd /tmp/gzh_pub && python3 -m http.server <port> --bind 127.0.0.1`（后台）。
3. 新开标签 goto `http://127.0.0.1:<port>/article-text.html`，`cua` Ctrl+A → Ctrl+C（受信任复制）。
4. 回编辑器标签：`cua` 点击正文区（约 x=800,y=450）→ Ctrl+A → Delete（清残留）→ Ctrl+V。
5. 校验：`pm[1].textContent.length` 与稿件正文字数一致。

**禁止**把 `<img src="http://127.0.0.1:...">` 混进粘贴内容——编辑器会报「N 个内容插入失败」，本站图片 src 一律被拒，图片只能走第 5 步。

## 5. 传图（GTK 剪贴板，唯一可行路径）

启动常驻进程（本机无 xclip/PyQt5，PyGObject 可用）：

```bash
python3 ~/.agents/skills/gzh-publisher/scripts/clip_hold.py   # 后台，30 分钟自退
```

对 `plan.json` 里的每张图（按文中顺序）：

```bash
echo "<图片绝对路径>" > /tmp/clip_request && sleep 1.2 && cat /tmp/clip_request
# 输出 done 即剪贴板已装好位图
```

然后编辑器内：定位锚点段落（图在 md 中位于该段落之前）→ 段落起点真实粘贴：

```js
// 锚点定位 + 滚动 + 取坐标
const el = [...pm.children].find(e => e.textContent.startsWith('锚点前缀'));
el.scrollIntoView({block:'center'});
const r = el.getBoundingClientRect();
// cua.click({x: r.x+3, y: r.y+8}) → Ctrl+V → 轮询
```

每张粘贴后轮询（≤15s）直到 `mmbiz.qpic.cn` 计数 +1（编辑器自动把剪贴板位图转存到公众号 CDN，这就是发布可用的图）。全部传完后核对：**总图数、每图 mmbiz、图文交错顺序**与稿件一致。

## 6. 摘要

```js
const box = tab.playwright.locator('textarea[placeholder^="选填"], input[placeholder^="选填"]');
```

点击后 fill（≤120 字）。摘要建议从稿件结论句提炼。

## 7. 封面

路径：点左侧封面卡（「+ 拖拽或选择封面」）→ 菜单「从正文选择」→ 选第一张图 → 下一步 → 看裁剪预览（2.35:1 与 1:1）→ 完成。

**坑**：下拉菜单 JS click 不触发事件代理，必须用可见节点的坐标 `cua.click`；选项渲染有延迟，点开后等 400ms 以上再找。

## 8. 保存草稿（默认终点）

点底部「保存为草稿」，等左下角出现保存时间即成功。汇报：草稿名、字数、图数、封面、摘要，发表方式（群发/仅发布）待库主人定。

## 9. 发表规则速查（如库主人要求继续）

- **群发**（开群发通知，推送给订阅用户）：每次都要管理员微信扫码验证，1-2 分钟过期，过期重点「发表」即可，草稿不丢。每天 1 次额度。
- **仅发布**（关群发通知）：免扫码、不占额度、不推送粉丝，文章上主页可分享。发表设置面板里把「群发通知」开关关掉再点发表。
- 发表遇平台合规拦截（如创作来源声明）：**停下来报选项，库主人当场拍板**，不代选。

## 10. 通用避坑

- 标签页 id 必须每次 `tabs.list()` 拿完整值，别截断复用。
- playwright 文本定位常命中隐藏 DOM 卡 actionability，一律改 `evaluate` 过滤 `offsetParent` 或直接 `cua` 坐标点。
- 每步操作后用 `evaluate` 读编辑器真实状态（字数/图数/mmbiz 数）做验收，别信点击返回值。
