#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整泡重排：擦除气泡内部文字并用本机圆体黑体重新渲染目标句。
用法: python patch_text.py <src> <out> <x0,y0,x1,y1 气泡外接框比例> <行1> [行2...]
"""
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\Dengb.ttf",
    r"C:\Windows\Fonts\Deng.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    sys.exit("no CJK font found")


def main():
    src, out = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = [float(v) for v in sys.argv[3].split(",")]
    lines = [a for a in sys.argv[4:] if a.strip()]

    img = Image.open(src).convert("RGB")
    W, H = img.size
    bx0, by0, bx1, by1 = int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)
    crop = img.crop((bx0, by0, bx1, by1))
    cw, ch = crop.size
    g = np.asarray(crop.convert("L"))
    ink = g < 150

    ys, xs = np.where(ink)
    if len(xs) == 0:
        sys.exit("no ink in bubble crop")
    ix0, ix1, iy0, iy1 = xs.min(), xs.max(), ys.min(), ys.max()
    print(f"ink bbox in crop: x {ix0}-{ix1}, y {iy0}-{iy1}, crop {cw}x{ch}")

    # 内部区域：从墨迹外接框向内收（避开气泡描边）
    inset_x = max(int((ix1 - ix0) * 0.07), 14)
    inset_y = max(int((iy1 - iy0) * 0.10), 12)
    tx0, tx1 = ix0 + inset_x, ix1 - inset_x
    ty0, ty1 = iy0 + inset_y, iy1 - inset_y

    region = np.asarray(crop.crop((tx0, ty0, tx1, ty1))).reshape(-1, 3)
    light = region[region.mean(axis=1) > 175]
    dark = region[region.mean(axis=1) <= 110]
    bg = tuple(int(v) for v in (np.median(light, axis=0) if len(light) else [252, 252, 250]))
    fg = tuple(int(v) for v in (np.median(dark, axis=0) if len(dark) else [45, 45, 50]))
    print(f"bg={bg} fg={fg} interior=({tx0},{ty0})-({tx1},{ty1})")

    # 擦除内部（稍扩 2px 确保残迹清零）
    draw = ImageDraw.Draw(crop)
    draw.rectangle([max(tx0 - 2, 0), max(ty0 - 2, 0), min(tx1 + 2, cw), min(ty1 + 2, ch)], fill=bg)

    # 排版：字号自适应
    iw, ih = tx1 - tx0, ty1 - ty0
    n = len(lines)
    longest = max(lines, key=len)
    size = int(min(ih / (n * 1.45), iw / len(longest) * 1.02))
    size = max(size, 18)
    font = load_font(size)
    while True:
        ok = True
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            if bb[2] - bb[0] > iw or bb[3] - bb[1] > ih / n * 1.25:
                ok = False
                break
        if ok or size <= 18:
            break
        size -= 2
        font = load_font(size)
    print(f"font size={size}")

    cy = ty0 + ih / (2 * n)
    for ln in lines:
        draw.text(((tx0 + tx1) / 2, cy), ln, font=font, fill=fg, anchor="mm")
        cy += ih / n

    img.paste(crop, (bx0, by0))
    img.save(out, quality=95)
    print(f"saved {out} font={font.getname()}")


if __name__ == "__main__":
    main()
