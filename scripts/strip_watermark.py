#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""strip_watermark.py — 清除 seedream 输出的白色网关水印（R19，通用版）。

原理（R19）：平台给所有 raw 同一像素位置盖白色半透明「AutoClaw AI生成」水印；
对每张 raw 求 (roi − median51)（变亮量），跨多张图逐像素取中值 →
随机内容噪声抵消、常量水印字形浮现；对字形掩膜 inpaint（TELEA）薄笔画填充，
网点/墨线无痕。掩膜可缓存到 assets/wm-mask-<W>x<H>.png 复用（图片数少时必须命中缓存）。

用法:
  python scripts/strip_watermark.py --dirs stories/story-20-zcode/panels stories/image-to-code/panels
  python scripts/strip_watermark.py --dirs ... --inplace        # 覆盖 raw（备份到 wm-original/）
  python scripts/strip_watermark.py --dirs ... --mask assets/wm-mask-2496x1664.png
"""
import argparse
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).parent.parent
WIN_DEFAULT = (1950, 1490, 2496, 1664)   # 2496×1664 raw 的水印条带（顶部余量放宽：R19b 批次间会漂移）
DIFF_TH = 1.8
MIN_IMGS_FOR_MEDIAN = 4


def build_mask(files, win, th):
    x0, y0, x1, y1 = win
    diffs = []
    for f in files:
        g = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
        if g.shape != (y1, x1):
            continue
        roi = g[y0:y1, x0:x1].astype(np.float64)
        med = cv2.medianBlur(roi.astype(np.uint8), 51).astype(np.float64)
        diffs.append(roi - med)
    if len(diffs) < MIN_IMGS_FOR_MEDIAN:
        raise SystemExit(f"need >= {MIN_IMGS_FOR_MEDIAN} same-size raws for cross-median "
                         f"(got {len(diffs)}); pass --mask instead")
    D = np.median(np.stack(diffs, 0), axis=0)
    m = (D >= th).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            keep[lab == i] = 255
    keep = cv2.dilate(keep, np.ones((2, 2), np.uint8), iterations=2)
    full = np.zeros((y1, x1), np.uint8)
    full[y0:y1, x0:x1] = keep
    print(f"mask built from {len(diffs)} imgs: px={int((full>0).sum())}")
    return full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True, help="含 v8-*.raw.jpg 的 panels 目录")
    ap.add_argument("--inplace", action="store_true", help="覆盖 raw（先备份到 wm-original/）")
    ap.add_argument("--mask", default=None, help="复用指定掩膜 PNG（跳过自动建模）")
    ap.add_argument("--th", type=float, default=DIFF_TH)
    a = ap.parse_args()

    dirs = [Path(d) if Path(d).is_absolute() else HERE / d for d in a.dirs]

    # R19b：水印位置会随批次漂移 → 掩膜按目录各自建模/缓存，不跨批次共用
    if a.mask:
        masks = None  # 单掩膜模式
        shared = cv2.imread(str(HERE / a.mask), cv2.IMREAD_GRAYSCALE)
        if shared is None:
            raise SystemExit(f"mask not found: {a.mask}")
        print(f"shared mask loaded: {a.mask} px={int((shared>0).sum())}")
    else:
        masks = {}
        for d in dirs:
            files_d = sorted(d.glob("v8-*.raw.jpg"))
            if not files_d:
                print(f"  no raws in {d.name}, skip mask")
                continue
            probe = cv2.imread(str(files_d[0]), cv2.IMREAD_GRAYSCALE)
            h, w = probe.shape
            key = d.parent.name or d.name   # 用话目录名做键，避免多个 <话>/panels 撞名
            cache = HERE / "assets" / f"wm-mask-{w}x{h}-{key}.png"
            if cache.exists():
                masks[str(d)] = cv2.imread(str(cache), cv2.IMREAD_GRAYSCALE)
                print(f"  mask cache hit: {cache.name} px={int((masks[str(d)]>0).sum())}")
                continue
            if (w, h) == (WIN_DEFAULT[2], WIN_DEFAULT[3]):
                win = WIN_DEFAULT
            else:
                sx, sy = w / WIN_DEFAULT[2], h / WIN_DEFAULT[3]
                win = (int(WIN_DEFAULT[0]*sx), int(WIN_DEFAULT[1]*sy), w, h)
            mask = build_mask(files_d, win, a.th)
            cache.parent.mkdir(exist_ok=True)
            cv2.imwrite(str(cache), mask)
            masks[str(d)] = mask
            print(f"  mask built+cached for {key} -> {cache.name}")

    n_clean = 0
    for d in dirs:
        for f in sorted(d.glob("v8-*.raw.jpg")):
            img = cv2.imread(str(f))
            mask = shared if a.mask else masks.get(str(d))
            if mask is None:
                print(f"  SKIP {f.name}: no mask")
                continue
            if img.shape[:2] != mask.shape:
                print(f"  SKIP {f.name}: size {img.shape[1]}x{img.shape[0]}")
                continue
            out = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            if a.inplace:
                bdir = f.parent / "wm-original"
                bdir.mkdir(exist_ok=True)
                if not (bdir / f.name).exists():
                    shutil.copy(f, bdir / f.name)
                cv2.imwrite(str(f), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
                print(f"  inplace {f.parent.parent.name}/{f.name}")
            else:
                cdir = f.parent / "cleaned"
                cdir.mkdir(exist_ok=True)
                cv2.imwrite(str(cdir / f.name), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
                print(f"  cleaned {f.parent.parent.name}/{f.name}")
            n_clean += 1
    print(f"DONE ({n_clean} panels)")


if __name__ == "__main__":
    main()
