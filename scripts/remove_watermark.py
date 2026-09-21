#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""remove_watermark.py — 清除 seedream 输出右下角「AutoClaw AI生成」半透明水印。

方法：在固定锚定区域做自动掩膜（亮灰半透明笔画 = 比周围纸面暗、
又远暗于纯黑线稿的中间调、低饱和），OpenCV inpaint(TELEA) 填充。
区域锚定：右下角 w×h 比例窗（默认 x0=0.50,y0=0.88 → 1.0,1.0），
可用 --inspect 输出掩膜叠加图人工核验。

用法:
  python remove_watermark.py --panel panels/v8-01.raw.jpg --out panels/v8-01.nowm.jpg
  python remove_watermark.py --panel a.jpg --mask-overlay ov.png   # 调参目检
"""
import argparse
import cv2
import numpy as np
from pathlib import Path


def build_mask(img_bgr, x0=0.50, y0=0.88):
    h, w = img_bgr.shape[:2]
    ax0, ay0 = int(w * x0), int(h * y0)
    roi = img_bgr[ay0:, ax0:]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    # 水印笔画：中间调（水印灰 ~200-242），低饱和（彩色线稿/水彩排除）
    wm = ((gray > 180) & (gray < 244) & (s < 40)).astype(np.uint8) * 255
    # 连通域过滤：只要较大的团块（笔画碎片），去噪点
    n, lab, stats, _ = cv2.connectedComponentsWithStats(wm, 8)
    keep = np.zeros_like(wm)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            keep[lab == i] = 255
    # 轻微膨胀盖住抗锯齿边缘
    keep = cv2.dilate(keep, np.ones((3, 3), np.uint8), iterations=2)
    full = np.zeros((h, w), np.uint8)
    full[ay0:, ax0:] = keep
    return full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--mask-overlay", default=None, help="输出掩膜红叠加目检图")
    ap.add_argument("--x0", type=float, default=0.50)
    ap.add_argument("--y0", type=float, default=0.88)
    a = ap.parse_args()
    src = Path(a.panel)
    img = cv2.imread(str(src))
    mask = build_mask(img, a.x0, a.y0)
    if a.mask_overlay:
        ov = img.copy()
        ov[mask > 0] = (0, 0, 255)
        cv2.imwrite(a.mask_overlay, ov)
        print(f"overlay -> {a.mask_overlay} mask_px={int((mask>0).sum())}")
    if a.out:
        bgr = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
        cv2.imwrite(a.out, bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"cleaned -> {a.out} mask_px={int((mask>0).sum())}")


if __name__ == "__main__":
    main()
