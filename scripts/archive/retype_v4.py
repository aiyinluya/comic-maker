#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""气泡重排 v4：统一文字规范（全气泡同一字体/字重/颜色/行距/字号公式）。

根因修复：v2/v3 中波普=粗体、小码=常规体，且不同轮次脚本字号策略不一 → 样式漂移。
v4 起所有气泡使用同一标准（UNIFIED），说话人区分只靠气泡形状（圆角矩形 vs 锯齿尾）。

UNIFIED 规范（唯一可调参数表，禁止逐格特调）：
  FONT   = msyhbd.ttc（微软雅黑 Bold，所有气泡统一）
  COLOR  = (35,35,40)
  LINE_H = 1.3
  MARGIN = 10px
  SIZE   = clamp(min(可用高/2.3, 可用宽/7.0), 18, 无上限) —— 确定性公式
"""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent

# ── UNIFIED 文字规范（唯一出处）──
FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"
TEXT_COLOR = (35, 35, 40)
LINE_H = 1.3
MARGIN = 10
MIN_SIZE = 18

JOBS = {
    "panel-01": {"src": "panels/panel-01.fixed.raw.jpg", "bubbles": [
        (0.08, 0.07, 0.47, 0.28, "波普，最近人人都在聊FDE，它到底是个什么岗位？"),
        (0.42, 0.45, 0.73, 0.65, "前沿部署工程师——把AI模型送进客户现场的人。")]},
    "panel-02": {"src": "panels/panel-02.fixed.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.49, 0.32, "听起来就是搞实施部署的？和普通工程师有啥区别？"),
        (0.58, 0.04, 0.98, 0.32, "普通工程师对代码负责，FDE对业务结果负责。")]},
    "panel-03": {"src": "panels/panel-03.fixed2.raw.jpg", "bubbles": [
        (0.05, 0.06, 0.36, 0.43, "客户现场没有标准答案，他们靠什么干活？"),
        (0.67, 0.55, 0.99, 0.85, "四成时间写代码，六成时间泡在现场磨需求。")]},
    "panel-04": {"src": "panels/panel-04.fixed2.raw.jpg", "bubbles": [
        (0.05, 0.03, 0.34, 0.27, "听说这岗位最近火得一塌糊涂？"),
        (0.59, 0.02, 0.98, 0.33, "招聘量一年涨了十倍不止，大厂都在抢人。")]},
    "panel-05": {"src": "panels/panel-05.raw.jpg", "bubbles": [
        (0.03, 0.04, 0.42, 0.30, "为什么偏偏是现在爆发？"),
        (0.61, 0.04, 0.94, 0.26, "模型已经很强，卡住AI落地的，是最后一公里。")]},
    "panel-06": {"src": "panels/panel-06.fixed.raw.jpg", "bubbles": [
        (0.05, 0.04, 0.33, 0.29, "那什么样的人能干这行？"),
        (0.64, 0.04, 0.96, 0.32, "懂技术、懂业务、还敢背结果——三样都要。")]},
    "panel-07": {"src": "panels/panel-07.fixed.raw.jpg", "bubbles": [
        (0.24, 0.04, 0.70, 0.51, "AI价值不在论文里，在客户的现场里。")]},
}


def label_components(mask):
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    comps = []
    cur = 0
    for sy in range(h):
        for sx in range(w):
            if mask[sy, sx] and labels[sy, sx] == 0:
                cur += 1
                q = deque([(sy, sx)])
                labels[sy, sx] = cur
                px = []
                while q:
                    y, x = q.popleft()
                    px.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                                labels[ny, nx] = cur
                                q.append((ny, nx))
                comps.append(px)
    return labels, comps


def largest_light_region(ink):
    """白色内腔 = 最大的浅色连通域（确定性，不依赖泛洪起点）。"""
    labels, comps = label_components(~ink)
    if not comps:
        return None
    biggest = max(comps, key=len)
    m = np.zeros_like(ink)
    for y, x in biggest:
        m[y, x] = True
    iy, ix = np.where(m)
    return m, (int(ix.min()), int(iy.min()), int(ix.max()), int(iy.max()))


def wrap(text, font, max_w, probe):
    lines, cur = [], ""
    for c in text:
        t = cur + c
        if probe.textlength(t, font=font) > max_w and cur:
            lines.append(cur)
            cur = c
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def retype_bubble(img, bx, text):
    W, H = img.size
    x0, y0, x1, y1 = int(bx[0] * W), int(bx[1] * H), int(bx[2] * W), int(bx[3] * H)
    crop = img.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    g = np.asarray(crop.convert("L"))
    ink = g < 150

    lr = largest_light_region(ink)
    if lr is None:
        return {"skipped": "no light region"}
    interior, cav = lr

    draw = ImageDraw.Draw(crop)
    _, comps = label_components(ink)
    n_erased = 0
    for comp in comps:
        if len(comp) < 6:
            continue
        if any(y in (0, ch - 1) or x in (0, cw - 1) for y, x in comp):
            continue  # 接触裁剪边缘 = 气泡边框/画面，不碰
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        # 组件大部分位于内腔内 = 文字；擦完整 bbox 防残字
        inside_frac = sum(1 for y, x in comp if cav[0] <= x <= cav[2] and cav[1] <= y <= cav[3]) / len(comp)
        if inside_frac >= 0.6:
            draw.rectangle([max(min(xs) - 3, 0), max(min(ys) - 3, 0),
                            min(max(xs) + 3, cw - 1), min(max(ys) + 3, ch - 1)], fill=(253, 253, 251))
            n_erased += 1

    lx0, ly0 = cav[0] + MARGIN, cav[1] + MARGIN
    lx1, ly1 = cav[2] - MARGIN, cav[3] - MARGIN
    iw, ih = lx1 - lx0, ly1 - ly0
    if iw < 60 or ih < 40:
        return {"skipped": f"region {iw}x{ih}"}

    # UNIFIED 字号公式（确定性）
    size = max(int(min(ih / 2.3, iw / 7.0)), MIN_SIZE)
    font = ImageFont.truetype(FONT_PATH, size)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    while size >= MIN_SIZE:
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap(text, font, iw, probe)
        lh = size * LINE_H
        if len(lines) * lh <= ih and all(probe.textlength(l, font=font) <= iw for l in lines):
            break
        size -= 2
    lh = size * LINE_H
    cy = ly0 + ih / 2 - len(lines) * lh / 2 + lh / 2
    for ln in lines:
        draw.text(((lx0 + lx1) / 2, cy), ln, font=font, fill=TEXT_COLOR, anchor="mm")
        cy += lh

    img.paste(crop, (x0, y0))
    return {"font_size": size, "lines": len(lines), "erased": n_erased, "cavity": list(cav)}


def main():
    only = sys.argv[1:] or None
    report_p = HERE / "retyped4_report.json"
    report = json.loads(report_p.read_text(encoding="utf-8")) if report_p.exists() else {}
    for name, job in JOBS.items():
        if only and name not in only:
            continue
        img = Image.open(HERE / job["src"]).convert("RGB")
        infos = [retype_bubble(img, b[:4], b[4]) for b in job["bubbles"]]
        out = HERE / f"panels/{name}.retyped4.jpg"
        img.save(out, quality=95)
        report[name] = {"src": job["src"], "out": out.name, "bubbles": infos}
        print(name, json.dumps(infos, ensure_ascii=False))
    report_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved retyped4_report.json")


if __name__ == "__main__":
    main()
