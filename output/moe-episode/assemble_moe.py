#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble_moe.py — 临时驱动器：把 6 格 final 拼成 MoE 话长图（标题区 + 竖拼 + 页脚）。
仿 scripts/stack.py 逻辑，标题/面板参数化；仅用于 output/moe-episode 本次演示。"""
from PIL import Image, ImageDraw, ImageFont

PANELS = [f"panels/v8-0{i}.final.jpg" for i in range(1, 7)]
W, GAP, TH = 1080, 26, 320
PAPER = (250, 250, 247)
INK = (26, 26, 26)
MUTE = (107, 103, 96)
ACCENT = (184, 85, 58)


def load_font(size, bold=True):
    for p in ([r"C:\Windows\Fonts\msyhbd.ttc"] if bold else []) + [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\Dengb.ttf",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    raise SystemExit("no font")


imgs = [Image.open(p).convert("RGB") for p in PANELS]
for im in imgs:
    assert im.width == W, im.size

header = Image.new("RGB", (W, TH), PAPER)
d = ImageDraw.Draw(header)
f_title = load_font(56)
f_sub = load_font(26, bold=False)
d.rectangle([60, 70, 100, 76], fill=ACCENT)
d.text((60, 88), "MoE：为什么大模型里", font=f_title, fill=INK)
d.text((60, 168), "住着一群专家？", font=f_title, fill=INK)
d.text((60, 250), "小码 & 波普 · 手绘长漫画 · 一问一答讲透「混合专家」", font=f_sub, fill=MUTE)

footer_h = 140
total_h = TH + sum(im.height for im in imgs) + GAP * (len(imgs) - 1) + footer_h
canvas = Image.new("RGB", (W, total_h), PAPER)
canvas.paste(header, (0, 0))
y = TH
for im in imgs:
    canvas.paste(im, (0, y))
    y += im.height + GAP
df = ImageDraw.Draw(canvas)
df.text((60, y + 40), "出自「码事漫谈」· comic-maker 开源流水线 · Seed-2.1-pro-0915 出图", font=f_sub, fill=MUTE)
canvas.save("long-manga.jpg", quality=92)
print("long-manga.jpg", canvas.size)
