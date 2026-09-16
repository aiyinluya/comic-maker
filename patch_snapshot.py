# -*- coding: utf-8 -*-
"""给 draw_bubbles 的 draw_from_storyboard 加快照抓取 + lint 联动。"""
import ast
from pathlib import Path

p = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\skills\comic-explainer\scripts\draw_bubbles.py")
src = p.read_text(encoding="utf-8")

# 在 draw_from_storyboard 的循环前抓灰度快照，存 npz
old = """        W, H = img.size
        d = ImageDraw.Draw(img)
        rb = []"""
new = """        W, H = img.size
        _snap_gray = np.asarray(img.convert("L")).copy()
        d = ImageDraw.Draw(img)
        rb = []"""
assert old in src
src = src.replace(old, new)

old2 = """        out = panel_dir / f"{key}.final.jpg"
        img.save(out, quality=95)"""
new2 = """        out = panel_dir / f"{key}.final.jpg"
        img.save(out, quality=95)
        try:
            import numpy as _np
            _np.savez_compressed(panel_dir / f"{key}.ink_snap.npz",
                                 gray=_np.asarray(img.convert("L")))
        except Exception:
            pass"""
assert old2 in src
src = src.replace(old2, new2)

# 头部 import numpy
if "import numpy" not in src:
    src = src.replace("from PIL import Image, ImageDraw, ImageFont",
                      "import numpy as np\nfrom PIL import Image, ImageDraw, ImageFont")

p.write_text(src, encoding="utf-8")
ast.parse(src)
print("snapshot capture injected + syntax OK")
