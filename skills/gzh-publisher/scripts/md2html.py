#!/usr/bin/env python3
"""稿件 md → 公众号注入材料。

用法：md2html.py <drafts/稿件.md> [输出目录，默认 /tmp/gzh_pub]

产出：
  article-text.html  纯文本富排版页（无图，供受信任复制粘贴）
  plan.json          标题、图片顺序 [{path, anchor}]、摘要候选、正文字数

转换规则：剥 frontmatter；首行非空文本=标题；剔模板签名行（> 开头）；
图片行记录顺序，锚点=其后第一个段落的前 12 字符（无后段则 anchor 为空=文末插入）。
"""
import json, re, sys, html, os
from pathlib import Path

src = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/gzh_pub")
out_dir.mkdir(parents=True, exist_ok=True)

text = src.read_text(encoding="utf-8")
text = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.S)
lines = [ln.rstrip() for ln in text.strip().split("\n")]

title = ""
paras, images, buf = [], [], []
IMG = re.compile(r"^!\[(.*?)\]\((.+?)\)\s*$")

def flush():
    global buf
    if buf:
        t = html.escape(" ".join(buf).strip())
        if t:
            paras.append(t)
        buf = []

for i, ln in enumerate(lines):
    s = ln.strip()
    if not s:
        flush(); continue
    if s.startswith(">"):  # 模板签名行，不发布
        continue
    if not title and not IMG.match(s) and not s.startswith("#"):
        title = s; continue
    m = IMG.match(s)
    if m:
        flush()
        img_path = m.group(2)
        # 相对路径按稿件所在目录解析为绝对路径
        p = Path(img_path)
        if not p.is_absolute():
            p = (src.parent / img_path).resolve()
        # 锚点：其后第一个段落
        anchor = ""
        for j in range(i + 1, len(lines)):
            ns = lines[j].strip()
            if ns and not ns.startswith(">") and not IMG.match(ns):
                anchor = ns[:12]; break
        images.append({"path": str(p), "alt": m.group(1), "anchor": anchor})
        continue
    if s.startswith("#"):  # 稿内一级标题（正常稿件没有，保底）
        flush(); paras.append("<b>" + html.escape(s.lstrip("# ")) + "</b>"); continue
    buf.append(s)
flush()

P_STYLE = ("margin:0 0 24px;font-size:15px;line-height:1.9;"
           "color:#3e3e3e;text-align:justify;letter-spacing:0.5px;")
body = "".join(f'<p style="{P_STYLE}">{p}</p>' for p in paras)
page = ('<!DOCTYPE html><html><head><meta charset="utf-8"><title>article</title></head>'
        f'<body style="max-width:677px;margin:40px auto;">{body}</body></html>')

(out_dir / "article-text.html").write_text(page, encoding="utf-8")
plan = {
    "title": title,
    "images": images,
    "body_chars": len(re.sub(r"<[^>]+>", "", body)),
    "digest_hint": paras[-2][:54] + "…" if len(paras) > 1 else "",
}
(out_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(plan, ensure_ascii=False, indent=1))
