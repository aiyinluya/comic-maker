# -*- coding: utf-8 -*-
"""_smoke_fallback.py — 模拟 CI 无过程 panels：gen_blog 应回退 output/panels。"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent
story = HERE / "stories/story-20-zcode/panels"
bak = story / "_bak"
bak.mkdir(exist_ok=True)
moved = []
for f in story.glob("v8-*.final.jpg"):
    shutil.move(str(f), str(bak / f.name))
    moved.append(f.name)
try:
    r = subprocess.run(
        [sys.executable, str(HERE / "scripts/gen_blog.py"),
         "--story", "stories/story-20-zcode", "--out-id", "20-zcode-incident",
         "--title", "T", "--kicker", "K", "--format", "panels",
         "--offline", "--out-dir", ".openclaw/tmp/blog-fallback"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(HERE))
    assert r.returncode == 0, r.stderr[-400:]
    n = len(list((HERE / ".openclaw/tmp/blog-fallback/assets/20-zcode-incident").glob("*.jpg")))
    assert n == 11, f"fallback assets {n}"
    print(f"FALLBACK OK: {n} assets from output/panels when story panels absent")
finally:
    for f in bak.glob("v8-*.final.jpg"):
        shutil.move(str(f), str(story / f.name))
    bak.rmdir()
