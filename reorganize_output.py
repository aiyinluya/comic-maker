# -*- coding: utf-8 -*-
"""开源仓库输出目录重组：过程与成品分离。
目标结构：
  output/               ← 全部最终成品（发布即用）
    long-form/          ← 12 部竖版长图（PNG 主图 + JPG 分享版）
    panels/             ← 单格成品图（按作品分子目录，供按格发布/博客用）
  process/              ← 全部过程图（空场景 raw / 修字轮次 fixed / 重排 retyped），不进发布
  archive/              ← 既有 archive 兼容（历史方案脚本仍在）
原 posts/、comic-studio/ 保留为过程工场，不删除（可追溯）。
"""
import shutil
from pathlib import Path

WS = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace")
CM = WS / "comic-maker"
OUT = CM / "output"
LF = OUT / "long-form"
PN = OUT / "panels"
LF.mkdir(parents=True, exist_ok=True)
PN.mkdir(parents=True, exist_ok=True)

# 作品清单：目录名（现位置）→ 输出目录名
WORKS = [
    # (posts_base, work_dir, output_name)
    (CM / "posts", "mcp", "01-mcp"),
    (CM / "posts/six-topics", "context", "02-context-engineering"),
    (CM / "posts/six-topics", "mas", "03-multi-agent"),
    (CM / "posts/six-topics", "token", "04-token"),
    (CM / "posts/six-topics", "finetune", "05-finetune-vs-prompt"),
    (CM / "posts/six-topics", "hands", "06-hands"),
    (CM / "posts", "coder-rider", "07-coder-rider"),
    (CM / "posts", "rag", "08-rag"),
    (CM / "posts", "a-backup-life", "09-backup-life"),
    (CM / "posts", "b-missing-comments", "10-missing-comments"),
    (WS / "comic-studio/posts", "2026-09-14-hallucination-manga", "11-hallucination"),
    (WS / "comic-studio/posts", "2026-09-15-fde", "12-fde"),
]

copied_long = 0
copied_panels = 0
for base, work, name in WORKS:
    src = base / work
    # 1) 长图 → output/long-form/<name>/
    lfd = LF / name
    lfd.mkdir(parents=True, exist_ok=True)
    for f in src.glob("long-manga*.png"):
        shutil.copy2(f, lfd / f"{name}.png")
        copied_long += 1
    for f in src.glob("long-manga-share.jpg"):
        shutil.copy2(f, lfd / f"{name}-share.jpg")
        copied_long += 1
    for f in src.glob("long-manga.jpg"):  # 幻觉篇早期 jpg 分享版
        shutil.copy2(f, lfd / f"{name}-legacy.jpg")
        copied_long += 1
    # 2) 单格 final → output/panels/<name>/
    pd = PN / name
    pd.mkdir(parents=True, exist_ok=True)
    finals = sorted(src.glob("*.final.jpg")) + sorted(src.glob("panels/*.final.jpg"))
    for i, f in enumerate(finals, 1):
        shutil.copy2(f, pd / f"{i:02d}.jpg")
        copied_panels += 1

print(f"long-form files: {copied_long} | panel files: {copied_panels}")
print("works:", len(WORKS))
