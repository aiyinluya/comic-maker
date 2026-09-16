# -*- coding: utf-8 -*-
"""修 lint 的快照路径 bug：--snapshot 只传了一个格子的快照，却用于所有格。
改为 --snapshot 传目录，lint 自动加载 <key>.ink_snap.npz。
"""
import ast
from pathlib import Path

p = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\comic-maker\scripts\lint.py")
src = p.read_text(encoding="utf-8")

old = """    snap = None
    if a.snapshot and Path(a.snapshot).exists():
        snap = np.load(a.snapshot)["gray"]

    tier = Counter()
    for key, bl in bubbles.items():
        issues = []
        fin = d / f"{key}.final.jpg"
        if not fin.exists():
            report[key] = ["MISSING final"]
            fail = True
            continue
        W, H = Image.open(fin).size
        if snap is not None:
            a = np.asarray(Image.open(fin).convert("L"))
            new_ink = (a < 150) & (snap >= 150)"""

new = """    snap_dir = Path(a.snapshot) if a.snapshot else None

    tier = Counter()
    for key, bl in bubbles.items():
        issues = []
        fin = d / f"{key}.final.jpg"
        if not fin.exists():
            report[key] = ["MISSING final"]
            fail = True
            continue
        W, H = Image.open(fin).size
        snap = None
        if snap_dir:
            npz = Path(snap_dir) / f"{key}.ink_snap.npz"
            if npz.exists():
                snap = np.load(npz)["gray"]
        if snap is not None:
            a = np.asarray(Image.open(fin).convert("L"))
            new_ink = (a < 150) & (snap >= 150)"""

assert old in src, "pattern not found"
src = src.replace(old, new)
p.write_text(src, encoding="utf-8")
ast.parse(src)
print("lint snapshot-per-panel fixed")
