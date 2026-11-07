#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weread_mp_collect.py — 微信读书路由的公众号文章采集器（无第三方依赖）

依赖: python3 (纯标准库) + node (跑 cdp.js) + 一个带 CDP 的 Chromium/Chrome
      (登录态已在浏览器里, 详见配套 SOP 文档)

用法:
  # 1. 只拉全量文章列表(标题/日期/摘要/阅读数, 通常 1-2 分钟)
  python3 weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院"

  # 2. 列表 + 最近 20 篇正文
  python3 weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院" --limit 20

  # 3. 列表 + 全部正文(601 篇约 25-40 分钟, 可中断续跑)
  python3 weread_mp_collect.py --book-id MP_WXS_3222754948 --name "鼎汇出海研究院" --all

断点续传: 列表缓存于 <out>/articles_list.json, 正文缓存于 <out>/content_raw/*.html,
重复执行会跳过已完成的部分。
"""
import argparse, datetime, json, os, re, subprocess, sys, time
from html.parser import HTMLParser

PAGE = 20                      # /web/mp/articles 每页条数(实测固定 20)
PACE = 1.2                     # 每次请求间隔秒数(实测 1.2s 无限频, 勿低于 1s)


def log(msg, logfile=None):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if logfile:
        with open(logfile, "a") as f:
            f.write(line + "\n")


# ---------------- CDP 控制层 ----------------

def cdp_eval(cdp_js, port, expr, timeout=120):
    """在浏览器当前标签页里执行 async JS 并返回其 return 值(字符串)。"""
    out = subprocess.run(["node", cdp_js, "eval", expr],
                         capture_output=True, text=True, timeout=timeout)
    s = out.stdout.strip()
    if not s or s == "undefined":
        raise RuntimeError(
            "eval 无返回(浏览器没开/CDP 端口不对/标签页不在 weread.qq.com)。"
            f"stderr: {out.stderr[:200]}")
    return s


def fetch_json(cdp_js, port, path):
    js = ("const r = await fetch('%s', {headers: {Accept: 'application/json'}});"
          " return JSON.stringify({s: r.status, t: await r.text()})" % path)
    d = json.loads(cdp_eval(cdp_js, port, js))
    if d["s"] != 200:
        raise IOError(f"HTTP {d['s']} for {path}")
    return json.loads(d["t"])


def fetch_text(cdp_js, port, path):
    js = ("const r = await fetch('%s'); return await r.text()" % path)
    return cdp_eval(cdp_js, port, js)


# ---------------- 正文提取 ----------------

class ContentExtractor(HTMLParser):
    """抓取 <div id="js_content"> 内的纯文本; h1 作为文内标题; 块级标签转换行。"""

    BLOCKS = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "section")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active = False
        self.parts = []
        self.title = None
        self._in_h1 = False
        self._h1 = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            if self.active:
                self.depth += 1
            elif a.get("id") == "js_content":
                self.active, self.depth = True, 1
        elif self.active and tag in self.BLOCKS:
            if tag == "h1" and self.title is None and not self._h1:
                self._in_h1 = True
        elif self.active and tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if not self.active:
            return
        if tag == "div":
            self.depth -= 1
            if self.depth <= 0:
                self.active = False
        elif tag in self.BLOCKS:
            self.parts.append("\n")
            if tag == "h1":
                self._in_h1 = False
                if self._h1 and self.title is None:
                    t = "".join(self._h1).strip()
                    if t:
                        self.title = t
                    self._h1 = []

    def handle_data(self, data):
        if not self.active:
            return
        self.parts.append(data)
        if self._in_h1:
            self._h1.append(data)


def extract_body(html: str):
    """返回 (文内标题, 正文纯文本)。"""
    p = ContentExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    text = "".join(p.parts)
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return p.title, text.strip()


# ---------------- 阶段 1: 文章列表 ----------------

def collect_list(cdp_js, port, book_id, out_dir, name, logfile):
    list_path = os.path.join(out_dir, "articles_list.json")
    articles = {}
    if os.path.exists(list_path):
        cached = json.load(open(list_path))
        articles = {a["reviewId"]: a for a in cached["articles"]}
        log(f"列表已有缓存: {len(articles)} 篇, 跳过采集", logfile)
        return cached

    offset, empty = 0, 0
    while True:
        d = fetch_json(cdp_js, port, f"/web/mp/articles?bookId={book_id}&offset={offset}")
        rs = d.get("reviews") or []
        log(f"offset={offset} -> {len(rs)} reviews", logfile)
        if not rs:
            empty += 1
            if empty >= 2:
                break
            offset += PAGE
            continue
        empty = 0
        for r in rs:
            # 关键: 真正的文章嵌在 reviews[i].subReviews[] 里
            for e in (r.get("subReviews") or [r]):
                rev = e.get("review") or e
                mp = rev.get("mpInfo") or {}
                rid = e.get("reviewId") or rev.get("reviewId")
                if not rid:
                    continue
                articles[rid] = {
                    "reviewId": rid,
                    "title": mp.get("title") or rev.get("content") or "(无标题)",
                    "digest": mp.get("content", ""),
                    "time": mp.get("time") or rev.get("createTime") or r.get("createTime"),
                    "readNum": mp.get("readNum"),
                    "likeNum": mp.get("likeNum"),
                    "pic_url": mp.get("pic_url", ""),
                }
        offset += PAGE
        time.sleep(PACE)
        if offset > 6000:          # 安全上限(300 篇页)
            log("达到安全上限, 停止翻页", logfile)
            break

    items = sorted(articles.values(), key=lambda a: -(a.get("time") or 0))
    payload = {"bookId": book_id, "mp_name": name, "count": len(items), "articles": items}
    json.dump(payload, open(list_path, "w"), ensure_ascii=False, indent=1)
    log(f"阶段1完成: {len(items)} 篇 -> {list_path}", logfile)
    return payload


# ---------------- 阶段 2: 正文 ----------------

def collect_content(cdp_js, port, items, out_dir, logfile, limit=None):
    raw_dir = os.path.join(out_dir, "content_raw")
    os.makedirs(raw_dir, exist_ok=True)
    targets = items if limit is None else items[:limit]
    bodies_path = os.path.join(out_dir, "article_bodies.jsonl")
    done_before = 0
    if os.path.exists(bodies_path):
        done_before = sum(1 for _ in open(bodies_path))
        log(f"正文已有 {done_before} 篇, 继续补齐", logfile)

    with open(bodies_path, "a") as out:
        for i, a in enumerate(targets, 1):
            rid = a["reviewId"]
            safe = re.sub(r"[^A-Za-z0-9_-]", "_", rid)[:120]
            raw_path = os.path.join(raw_dir, safe + ".html")
            if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                html = open(raw_path, encoding="utf-8", errors="ignore").read()
            else:
                for attempt in range(4):
                    try:
                        html = fetch_text(cdp_js, port,
                                          "/web/mp/content?reviewId=" + rid)
                        with open(raw_path, "w", encoding="utf-8") as f:
                            f.write(html)
                        break
                    except Exception as e:
                        log(f"  重试{attempt+1} #{i}: {e}", logfile)
                        time.sleep(15 * (attempt + 1))
                else:
                    log(f"  #{i} 彻底失败, 跳过: {rid}", logfile)
                    continue
            in_title, text = extract_body(html)
            rec = {**a, "date": (datetime.datetime.fromtimestamp(a["time"]).strftime("%Y-%m-%d")
                                 if a.get("time") else ""),
                   "titleInHtml": in_title, "bodyText": text}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            log(f"[{i}/{len(targets)}] {rec['date']} {rec['title'][:34]} "
                f"| {len(text)} 字", logfile)
            time.sleep(PACE)


# ---------------- 阶段 3: 导出 ----------------

def export(out_dir, name, bodies_jsonl, md_path):
    recs = [json.loads(l) for l in open(bodies_jsonl)]
    md = [f"# {name} · 文章全文合集（{len(recs)} 篇）\n",
          f"> 采集时间 {time.strftime('%Y-%m-%d %H:%M')}，来源：微信读书公众号库\n"]
    for i, r in enumerate(recs, 1):
        md.append(f"\n---\n\n## {i}. {r['title']}\n")
        md.append(f"**日期**：{r['date']}")
        if r.get("digest"):
            md.append(f"  \n**摘要**：{r['digest']}")
        md.append("\n\n" + (r["bodyText"] or "（正文提取为空）") + "\n")
    open(md_path, "w", encoding="utf-8").write("\n".join(md))
    log(f"导出完成: {md_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-id", required=True, help="书架里查到的公众号 bookId, 形如 MP_WXS_3222754948")
    ap.add_argument("--name", default="公众号", help="公众号名称(用于标题)")
    ap.add_argument("--limit", type=int, default=None, help="只抓最近 N 篇正文")
    ap.add_argument("--all", action="store_true", help="抓全部正文")
    ap.add_argument("--list-only", action="store_true", help="只拉文章列表, 不抓正文")
    ap.add_argument("--out-dir", default="wr_out", help="输出目录")
    ap.add_argument("--cdp-js", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdp.js"))
    ap.add_argument("--cdp-port", default="9222", help="浏览器远程调试端口(仅用于报错提示)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    logfile = os.path.join(args.out_dir, "collect.log")
    payload = collect_list(args.cdp_js, args.cdp_port, args.book_id,
                           args.out_dir, args.name, logfile)
    if args.list_only:
        return
    items = payload["articles"]
    limit = None if args.all else (args.limit or 20)
    collect_content(args.cdp_js, args.cdp_port, items, args.out_dir, logfile, limit)
    bodies = os.path.join(args.out_dir, "article_bodies.jsonl")
    export(args.out_dir, args.name, bodies,
           os.path.join(args.out_dir, "articles_fulltext.md"))


if __name__ == "__main__":
    main()
