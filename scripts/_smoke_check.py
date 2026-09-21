# -*- coding: utf-8 -*-
"""_smoke_check.py — gen_blog 冒烟产物断言（CI / 本地通用）。

用法: python scripts/_smoke_check.py <blog-out-dir> [--offline]
"""
import re
import sys
from pathlib import Path

d = Path(sys.argv[1] if len(sys.argv) > 1 else ".openclaw/tmp/blog-smoke")
offline = "--offline" in sys.argv

h = (d / "20-zcode-incident-wechat.html").read_text(encoding="utf-8")
assert h.count("<img") == 11, f"wechat imgs {h.count('<img')}"
assert h.count("<script") == 0
srcs = re.findall(r'src="([^"]+)"', h)
if offline:
    assert all(s.startswith("assets/") for s in srcs), srcs[:3]
else:
    assert all(s.startswith("https://") for s in srcs), srcs[:3]
assert h.count("<h2") >= 6
assert "出自公众号：码事漫谈" in h

m = (d / "20-zcode-incident.md").read_text(encoding="utf-8")
assert m.count("](assets/20-zcode-incident/") == 11, "md asset refs"
assert m.startswith("# ")
assert "出自公众号：码事漫谈" in m

z = (d / "20-zcode-incident.html").read_text(encoding="utf-8")
assert z.count("<figure") == 11, f"magazine figures {z.count('<figure')}"
assert "grain" in z and "--accent:#b8553a" in z

mode = "offline(asset-path)" if offline else "oss"
print(f"SMOKE OK: wechat 11 img inline ({mode}) / md 11 assets / magazine 11 figures")
