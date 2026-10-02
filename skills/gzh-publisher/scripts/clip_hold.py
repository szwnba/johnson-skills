#!/usr/bin/env python3
"""GTK 系统剪贴板图片常驻进程（gzh-publisher 传图用）。

协议：向 /tmp/clip_request 写入 PNG 绝对路径 → 本进程把位图放入 CLIPBOARD
→ 把文件内容改写为 done。30 分钟无操作自退。

依赖：PyGObject（GTK3）。X11 会话下验证可用。
"""
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

REQ = os.environ.get("CLIP_REQ", "/tmp/clip_request")
clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
open(REQ, "w").write("")


def check():
    try:
        p = open(REQ).read().strip()
        if p and p != "done" and os.path.exists(p):
            clip.set_image(GdkPixbuf.Pixbuf.new_from_file(p))
            open(REQ, "w").write("done")
    except Exception:
        pass
    return True


GLib.timeout_add(300, check)
GLib.timeout_add(1800000, Gtk.main_quit)  # 30 分钟自退
Gtk.main()
