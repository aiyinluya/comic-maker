# -*- coding: utf-8 -*-
"""lint 终验：快照(720高) vs final(720高？) —— 先确认 final 尺寸再对比。
关键：final 是 img（resize 后 1080 宽）保存的，快照也是 resize 后抓的 → 两者应同尺寸。
"""
from pathlib import Path
from PIL import Image
import numpy as np
import json

d = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\comic-maker\posts\rag\panels")
bubbles = json.loads((HERE if False else Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\comic-maker\posts\rag\bubbles.json")).read_text(encoding="utf-8"))

for key, bl in bubbles.items():
    fin = d / f"{key}.final.jpg"
    npz = d / f"{key}.ink_snap.npz"
    snap = np.load(npz)["gray"]
    a = np.asarray(Image.open(fin).convert("L"))
    new = (a < 150) & (snap >= 150)
    ys, xs = np.where(new)
    bad_total = 0
    for b in bl:
        x0, y0, x1 = int(b[0] * a.shape[1]), int(b[1] * a.shape[0]), int(b[2] * a.shape[1])
        # y1 由 draw_report 反查：气泡实际高度 = lines*lh+PAD*2；这里用宽松外扩 8/70
        inside = ((xs >= x0 - 8) & (xs <= x1 + 8) &
                  (ys >= max(y0 - 8, 0)) & (ys <= min(y0 + int(0.60 * a.shape[0]), a.shape[0])))
        bad_total += int((~inside).sum())
    print(key, "snap shape", snap.shape, "final", a.shape, "| outside-ink:", bad_total)
