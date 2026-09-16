# -*- coding: utf-8 -*-
"""修 snapshot 注入的 np 引用 + ast 导入。"""
import ast
from pathlib import Path

p = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\skills\comic-explainer\scripts\draw_bubbles.py")
src = p.read_text(encoding="utf-8")

old = """        try:
            import numpy as _np
            _np.savez_compressed(panel_dir / f"{key}.ink_snap.npz",
                                 gray=_np.asarray(img.convert("L")))
        except Exception:
            pass"""
new = """        try:
            np.savez_compressed(panel_dir / f"{key}.ink_snap.npz",
                                gray=_snap_gray)
        except Exception:
            pass"""
assert old in src, "pattern not found"
src = src.replace(old, new)
p.write_text(src, encoding="utf-8")
ast.parse(src)
print("np reference fixed + syntax OK")
