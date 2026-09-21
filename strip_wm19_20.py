#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""strip_wm19_20.py v4 — 白色水印清除（跨图中值掩膜 + inpaint）。

关键修正：水印是白色半透明字（比纸面亮），不是灰字。
掩膜：紧凑条带窗内，对每张 raw 求 (roi - median51)（变亮量），
跨 19 张图逐像素取中值 → 纸纹噪声抵消，白色字形浮现。
修复：字形掩膜 inpaint（TELEA r=3，细笔画无痕）。
"""
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).parent
P20 = HERE / "stories/story-20-zcode/panels"
P19 = HERE / "stories/image-to-code/panels"
WIN = (1950, 1550, 2496, 1664)   # 水印条带（3x 放大目检定位）
DIFF_TH = 1.8


def build_mask():
    x0, y0, x1, y1 = WIN
    diffs = []
    for panels in (P20, P19):
        for f in sorted(panels.glob("v8-*.raw.jpg")):
            g = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            if g.shape != (1664, 2496):
                print(f"  skip {panels.name}/{f.name}")
                continue
            roi = g[y0:y1, x0:x1].astype(np.float64)
            med = cv2.medianBlur(roi.astype(np.uint8), 51).astype(np.float64)
            diffs.append(roi - med)          # 正号 = 变亮 = 白水印
    D = np.median(np.stack(diffs, 0), axis=0)
    print(f"median-brighten: p50={np.percentile(D,50):.2f} p90={np.percentile(D,90):.2f} "
          f"p99={np.percentile(D,99):.2f} max={D.max():.1f}")
    m = (D >= DIFF_TH).astype(np.uint8) * 255
    print(f"raw mask px={int((m>0).sum())}")
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            keep[lab == i] = 255
    keep = cv2.dilate(keep, np.ones((2, 2), np.uint8), iterations=2)
    tpl = cv2.imread(str(P20 / "v8-04.raw.jpg"))
    full = np.zeros(tpl.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = keep
    ov = tpl.copy()
    ov[full > 0] = (0, 0, 255)
    cv2.imwrite(str(HERE / ".openclaw/tmp/wm-mask-ov.png"), ov[1490:1664, 1900:2496])
    print(f"final mask px={int((full>0).sum())}")
    return full


def main():
    mask = build_mask()
    if "--mask-only" in sys.argv:
        print("MASK-ONLY: skip cleaning")
        return
    for panels in (P20, P19):
        outdir = panels / "cleaned"
        outdir.mkdir(exist_ok=True)
        for f in sorted(panels.glob("v8-*.raw.jpg")):
            img = cv2.imread(str(f))
            if img.shape[:2] != mask.shape:
                print(f"  SKIP {f.name}: size mismatch")
                continue
            out = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            cv2.imwrite(str(outdir / f.name), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"  cleaned {panels.name}/{f.name}")
    print("DONE")


if __name__ == "__main__":
    sys.exit(main())
