#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""气泡重排 v7：几何测量派。
R12：字号在成品坐标系（1080 宽）定义，按各格源图分辨率换算绘制 → 成品字号严格一致。
R13：排版区 = 从内腔质心贪心扩张的最大内接矩形（每一步整行/整列必须全为内腔），文字块必在其内。
内腔 = 最大白色连通域（先对描边做形态学闭运算封 4px 缺口防漏）∪ 被包围的文字暗域。
渲染后像素审计：新增暗像素必须全部落在内腔掩码内（0 容差），否则该格判 FAIL。
全话字号求解：44 → 38 → 32 → 26 逐档试算，取全话通用最大档；禁止混排。
"""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FINAL_W = 1080
TIERS = [44, 38, 32, 26]
FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"
TEXT_COLOR = (35, 35, 40)
LINE_H = 1.3
MARGIN_FINAL = 10  # 成品坐标系下的排版边距

JOBS = {
    "panel-01": {"src": "panels/panel-01.fixed.raw.jpg", "bubbles": [
        (0.08, 0.07, 0.47, 0.28, "波普，最近人人都在聊FDE，它到底是个什么岗位？"),
        (0.41, 0.42, 0.74, 0.68, "前沿部署工程师——把AI模型送进客户现场的人。")]},
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


def dilate(m, k):
    for _ in range(k):
        p = np.pad(m, 1, constant_values=False)
        m = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | p[1:-1, 1:-1])
    return m


def erode(m, k):
    for _ in range(k):
        p = np.pad(m, 1, constant_values=True)
        m = (p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:] & p[1:-1, 1:-1])
    return m


def label_components(mask):
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    comps = []
    cur = 0
    for sy in range(h):
        row = mask[sy]
        for sx in range(w):
            if row[sx] and labels[sy, sx] == 0:
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


def largest_light(ink, k=4):
    """内腔 = 不接触裁剪边缘的最大浅色连通域（背景必触边被排除；闭运算先封 4px 描边缺口）。"""
    closed = erode(dilate(ink, k), k)
    light = ~closed
    _, comps = label_components(light)
    h, w = ink.shape
    cands = [c for c in comps if not any(y in (0, h - 1) or x in (0, w - 1) for y, x in c)]
    if not cands:
        return None, None
    biggest = max(cands, key=len)
    m = np.zeros_like(ink)
    for y, x in biggest:
        m[y, x] = True
    iy, ix = np.where(m)
    return m, (int(ix.min()), int(iy.min()), int(ix.max()), int(iy.max()))


def text_components(ink, light_mask, lb):
    """被内腔包围的暗色连通域（不接触裁剪边，主体落在内腔 bbox 内）。"""
    _, comps = label_components(ink)
    out = []
    for comp in comps:
        if len(comp) < 6:
            continue
        if any(y in (0, ink.shape[0] - 1) or x in (0, ink.shape[1] - 1) for y, x in comp):
            continue
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        inside = sum(1 for y, x in comp if lb[0] <= x <= lb[2] and lb[1] <= y <= lb[3]) / len(comp)
        if inside >= 0.6:
            out.append(comp)
    return out


def greedy_rect(interior_full, cy, cx):
    """从 (cy,cx) 贪心扩张：每一步新行/列必须整行/整列全为内腔。返回 (l,t,r,b)。"""
    ch, cw = interior_full.shape
    top = bot = cy
    left = right = cx
    while True:
        grew = False
        if top - 1 >= 0 and interior_full[top - 1, left:right + 1].all():
            top -= 1
            grew = True
        if bot + 1 < ch and interior_full[bot + 1, left:right + 1].all():
            bot += 1
            grew = True
        if left - 1 >= 0 and interior_full[top:bot + 1, left - 1].all():
            left -= 1
            grew = True
        if right + 1 < cw and interior_full[top:bot + 1, right + 1].all():
            right += 1
            grew = True
        if not grew:
            return left, top, right, bot


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


def measure_all():
    meas = {}
    for name, job in JOBS.items():
        img = Image.open(HERE / job["src"]).convert("RGB")
        W, H = img.size
        items = []
        for bx_t in job["bubbles"]:
            bx, text = bx_t[:4], bx_t[4]
            x0, y0, x1, y1 = int(bx[0] * W), int(bx[1] * H), int(bx[2] * W), int(bx[3] * H)
            crop = img.crop((x0, y0, x1, y1))
            g = np.asarray(crop.convert("L"))
            ink = g < 150
            light_mask, lb = largest_light(ink)
            if light_mask is None:
                items.append({"err": "no light region"})
                continue
            tcomps = text_components(ink, light_mask, lb)
            interior_full = light_mask.copy()
            for comp in tcomps:
                for y, x in comp:
                    interior_full[y, x] = True
            iy, ix = np.where(interior_full)
            cy, cx = int(iy.mean()), int(ix.mean())
            if not interior_full[cy, cx]:
                pts = np.argwhere(interior_full)
                d = ((pts[:, 0] - cy) ** 2 + (pts[:, 1] - cx) ** 2)
                cy, cx = pts[int(np.argmin(d))]
                cy, cx = int(cy), int(cx)
            # 种子点必须在内腔内（质心可能落在非凸区域外）
            if not interior_full[cy, cx]:
                sys.exit(f"seed not in interior for {name}")
            l, t, r, b = greedy_rect(interior_full, cy, cx)
            m = round(MARGIN_FINAL * W / FINAL_W)
            rect = (l + m, t + m, r - m, b - m)
            items.append({"rect": rect, "pw": W, "text": text,
                          "cavity_bbox": list(lb), "n_text_comp": len(tcomps)})
        meas[name] = {"pw": W, "bubbles": items}
    return meas


def solve_global(meas):
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for F in TIERS:
        ok = True
        detail = []
        for name, m in meas.items():
            for it in m["bubbles"]:
                if "err" in it:
                    ok = False
                    detail.append((name, "ERR"))
                    continue
                l, t, r, b = it["rect"]
                rw, rh = r - l, b - t
                if rw < 60 or rh < 40:
                    ok = False
                    detail.append((name, f"small {rw}x{rh}"))
                    continue
                size = max(round(F * it["pw"] / FINAL_W), 12)
                font = ImageFont.truetype(FONT_PATH, size)
                lines = wrap(it["text"], font, rw, probe)
                lh = size * LINE_H
                if len(lines) * lh > rh:
                    ok = False
                    detail.append((name, f"{F} needs {len(lines)}L>{rh}px"))
                else:
                    detail.append((name, f"{F} ok {len(lines)}L"))
        if ok:
            return F, detail
    return TIERS[-1], detail


def render_all(meas, F):
    report = {}
    for name, m in meas.items():
        img = Image.open(HERE / JOBS[name]["src"]).convert("RGB")
        panel_report = []
        for (bx_t, it) in zip(JOBS[name]["bubbles"], m["bubbles"]):
            bx, text = bx_t[:4], bx_t[4]
            if "err" in it:
                panel_report.append({"skipped": it["err"]})
                continue
            x0, y0, x1, y1 = int(bx[0] * m["pw"]), int(bx[1] * img.size[1]), int(bx[2] * m["pw"]), int(bx[3] * img.size[1])
            crop = img.crop((x0, y0, x1, y1))
            g = np.asarray(crop.convert("L"))
            ink_before = g < 150
            light_mask, lb = largest_light(ink_before)
            tcomps = text_components(ink_before, light_mask, lb)
            draw = ImageDraw.Draw(crop)
            flat = np.asarray(crop).reshape(-1, 3)
            lmask = flat.mean(axis=1) > 175
            bg = tuple(int(v) for v in (np.median(flat[lmask], axis=0) if lmask.any() else [253, 253, 251]))
            for comp in tcomps:
                ys = [p[0] for p in comp]
                xs = [p[1] for p in comp]
                draw.rectangle([max(min(xs) - 3, 0), max(min(ys) - 3, 0),
                                min(max(xs) + 3, crop.size[0] - 1), min(max(ys) + 3, crop.size[1] - 1)], fill=bg)
            l, t, r, b = it["rect"]
            size = max(round(F * it["pw"] / FINAL_W), 12)
            font = ImageFont.truetype(FONT_PATH, size)
            lines = wrap(text, font, r - l, draw)
            lh = size * LINE_H
            cy = t + (b - t) / 2 - len(lines) * lh / 2 + lh / 2
            for ln in lines:
                draw.text(((l + r) / 2, cy), ln, font=font, fill=TEXT_COLOR, anchor="mm")
                cy += lh
            # 像素审计：新增暗像素必须全部落在内腔掩码内
            g2 = np.asarray(crop.convert("L"))
            dark_after = g2 < 150
            stray = int((dark_after & ~light_mask & ~ink_before).sum())
            panel_report.append({"F": F, "size_px": size, "lines": len(lines),
                                 "erased": len(tcomps), "stray_dark_px": stray,
                                 "audit": "PASS" if stray == 0 else "FAIL"})
            if stray:
                print(f"  !! {name} stray dark pixels outside cavity: {stray}")
            img.paste(crop, (x0, y0))
        out = HERE / f"panels/{name}.retyped7.jpg"
        img.save(out, quality=95)
        report[name] = {"src": JOBS[name]["src"], "out": out.name, "bubbles": panel_report}
        print(name, json.dumps(panel_report, ensure_ascii=False))
    (HERE / "retyped7_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved retyped7_report.json")


def main():
    meas = measure_all()
    for name, m in meas.items():
        print(name, "measured", len(m["bubbles"]), "bubbles")
    F, detail = solve_global(meas)
    print(f"GLOBAL FONT = {F}px (final-1080 space)")
    print(json.dumps(detail, ensure_ascii=False))
    render_all(meas, F)


if __name__ == "__main__":
    main()
