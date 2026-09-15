#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长图拼装：标题区 + 8 格竖向拼接 -> long-manga.jpg"""
from PIL import Image, ImageDraw, ImageFont

PANELS = [
    "panels/panel-01.jpg",
    "panels/panel-02.jpg",
    "panels/strip-01.jpg",
    "panels/panel-03.jpg",
    "panels/panel-04.jpg",
    "panels/panel-05.jpg",
    "panels/panel-06.jpg",
    "panels/panel-07.jpg",
]
W, GAP, TH = 900, 26, 300
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
f_title = load_font(60)
f_sub = load_font(26, bold=False)
d.rectangle([60, 70, 100, 76], fill=ACCENT)
d.text((60, 92), "为什么 AI 会一本正经地", font=f_title, fill=INK)
d.text((60, 170), "胡说八道？", font=f_title, fill=INK)
d.text((60, 248), "小柯 & 波普 · 手绘长漫画 第 1 话 · 一问一答讲透「AI 幻觉」", font=f_sub, fill=MUTE)

total_h = TH + sum(im.height for im in imgs) + GAP * (len(imgs) - 1)
canvas = Image.new("RGB", (W, total_h), PAPER)
canvas.paste(header, (0, 0))
y = TH
for im in imgs:
    canvas.paste(im, (0, y))
    y += im.height + GAP
canvas.save("long-manga.jpg", quality=92)
print("long-manga.jpg", canvas.size)
