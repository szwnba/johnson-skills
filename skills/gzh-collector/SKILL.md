---
name: gzh-collector
description: 公众号文章整站采集（微信读书路由）：把任意微信公众号的历史文章（列表 + 全文）批量落成本地 Markdown/JSON。当用户提到 采集公众号文章、导出公众号历史文章、公众号整站备份、抓公众号全部文章、微信读书采集、把某个公众号的文章存下来 时使用；哪怕只说「把这个公众号的文章都搞下来」也应触发。2026-11 全流程实战验证（601 篇）。
---

# gzh-collector — 公众号文章整站采集（微信读书路由）

微信公众号不提供公开的文章列表接口，搜索引擎也不收录，"整站采集"必须借助有完整存档的体系。本技能走**微信读书 Web API**：登录只需微信扫一次码，接口无公众平台那类限频，唯一前提是目标公众号能在**微信读书 App** 里搜到并关注。

## 路线对比（为何不走别路）

| 路线 | 结论 |
| --- | --- |
| mp.weixin.qq.com `appmsg?action=list_ex` | 接口真实存在，但限频（200013）一旦触发极难解除（实测 23h+，且限频期间继续探测会**续期惩罚窗口**）。仅作备用。 |
| wewe-rss 开源项目 | 已死：全版本依赖作者中转 `weread.111965.xyz`，2026-11 实测 502。 |
| **微信读书 Web API（本技能）** | ✅ 首选。三个接口即可全量落地，全程断点续传。 |

## 前置

- Node ≥ 18（跑 `scripts/cdp.js`）、Python 3.8+（**纯标准库**，无需 pip）；任意有 Chromium/Chrome 的机器；
- 手机微信（扫码登录网页版微信读书）+ 手机**微信读书 App**（同一微信登录）；
- 磁盘：正文原始 HTML ≈3.5MB/篇（仅作缓存，可删）。

脚本位置：本技能目录下 `scripts/cdp.js`（零依赖 CDP 控制器：nav / screenshot / shotclip / eval / info）与 `scripts/weread_mp_collect.py`（主采集器，`--book-id/--name/--list-only/--limit N/--all`，自动断点续传）。

## 流程

### 1. 起带 CDP 的浏览器并登录

```bash
DISPLAY=:1 chromium --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --remote-debugging-port=9222 --window-size=1280,900 \
  --user-data-dir=./chrome-profile "https://weread.qq.com/#login" &
```

二维码 2~3 分钟过期，点图上"点击刷新二维码"再扫。无头环境用 JS 抠码：

```bash
node scripts/cdp.js eval "const img=document.querySelector('img.wr_login_modal_qr_img');
return img && !img.className.includes('expired') ? img.src : 'EXPIRED_OR_MISSING'"
```

登录成功的标志：页面回到 `weread.qq.com` 首页（`node scripts/cdp.js info` 里无 `#login`）。

### 2. 手机 App 里关注目标公众号（只能手动，Web 搜不到公众号）

微信读书 App 搜索目标号 → 分类切到"公众号" → 进去**关注/加入书架**。
⚠️ Web 端搜索接口（`/api/store/search`、`/web/search/global`）实测均不含公众号结果，别在网页上找。

### 3. 书架拿 bookId

```bash
node scripts/cdp.js eval "const r = await fetch('/web/shelf/sync'); const d = await r.json();
return JSON.stringify((d.books||[]).filter(b => b.type === 3).map(b => ({bookId: b.bookId, title: b.title})))"
```

公众号在书架里是 `type:3`、`bookId` 形如 **`MP_WXS_3222754948`** 的"书"。

### 4. 跑采集器

```bash
python3 scripts/weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院" --list-only   # 列表, 600篇约40s
python3 scripts/weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院" --limit 20   # 最近20篇全文
python3 scripts/weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院" --all        # 全量, 约25-40min
```

## 三个接口（脚本内部语义）

| 接口 | 要点 |
| --- | --- |
| `GET /web/shelf/sync` | 书架 → 找 `MP_WXS_*` 的 bookId |
| `GET /web/mp/articles?bookId=...&offset=N` | 每页固定 20 条；**真正文章嵌在 `reviews[i].subReviews[]`**（reviewId + review.mpInfo 的 title/digest/time/readNum），直接按顶层解析会"有数据但存 0 条" |
| `GET /web/mp/content?reviewId=...` | 返回**原始微信文章 HTML**（≈3.5MB，Content-Type 还谎报 text/plain），正文在 `<div id="js_content">`，用标准库 html.parser 深度跟踪提取即可 |

## 输出物

`wr_out/` 下：`articles_list.json`（全量列表）、`content_raw/*.html`（缓存，可删）、`article_bodies.jsonl`（每行一篇含 bodyText）、`articles_fulltext.md`（可读合集）、`collect.log`。

## 排障速查

| 症状 | 处置 |
| --- | --- |
| `eval 无返回/undefined` | 浏览器没开 / CDP 端口不对 / 标签页不在 weread.qq.com → 重开浏览器，`curl 127.0.0.1:9222/json` 验证 |
| 接口返回登录页 HTML | 会话过期 → 重新扫码（同一 user-data-dir 重开浏览器可免扫码） |
| articles 404 | bookId 写错（少 `MP_WXS_` 前缀） |
| 书架无 MP_WXS_* 项 | App 没关注成功或同步延迟，等几秒重查 |
| 跑一半全挂 | 机器休眠杀了浏览器 → 重启浏览器 + 重跑（自动续传） |

节奏：脚本内置 1.2s/请求，**不要低于 1s**；被限频也绝不疯狂重试——微信系接口的惩罚窗口会被频繁探测续期。

## 已知坑

1. 公众号自己会重发旧文：同文异 ID 重复（标题相同时间不同），按标题/正文哈希二次去重；
2. App 关注后 Web 书架偶有几秒同步延迟；
3. 微信读书 App 搜不到的号（未收录），本路线不适用 → 兜底：手机 mitmproxy 抓 `profile_ext` 历史消息页（key 约 20 分钟有效）翻 `getappmsglist`；或公众平台管理员登录后单次 `list_ex`（fakeid 可从该号任一文章页 `var biz = "..."` 提取）；或新榜/西瓜数据付费导出。
