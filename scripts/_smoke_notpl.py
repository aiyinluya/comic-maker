# -*- coding: utf-8 -*-
"""_smoke_notpl.py — 模拟 CI 无模板环境：COMIC_MAGAZINE_TPL 指向不存在路径。"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent
env = dict(os.environ)
env["COMIC_MAGAZINE_TPL"] = str(HERE / "assets/__no_such_template__.html")
r = subprocess.run(
    [sys.executable, str(HERE / "scripts/gen_blog.py"),
     "--story", "stories/story-20-zcode", "--out-id", "20-zcode-incident",
     "--title", "T", "--kicker", "K", "--format", "panels",
     "--offline", "--out-dir", ".openclaw/tmp/blog-notpl"],
    capture_output=True, text=True, encoding="utf-8", cwd=str(HERE), env=env)
assert r.returncode == 0, r.stderr[-400:]
z = (HERE / ".openclaw/tmp/blog-notpl/20-zcode-incident.html").read_text(encoding="utf-8")
assert "--accent:#b8553a" in z and "grain" in z, "fallback CSS missing"
assert z.count("<figure") == 11
assert "max-w-[720px]" not in z, "tailwind utility leaked (no CDN in CI)"
print("NO-TPL OK: fallback design-system CSS applied, no tailwind dependency")
