#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 结构派：在无气泡空场景图上，用代码绘制气泡与文字。

几何确定性：
- 气泡位置/尺寸由本表固定（比例坐标），不依赖任何检测；
- 文字统一 44px 档（成品坐标系），换行按气泡宽，行数与块高在排入前验算，放不下自动降档 38/32/26；
- 圆角矩形气泡=小码（左），椭圆+锯齿尾=波普（右），描边加微抖动模拟手绘，尾尖朝向说话人。
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"
INK = (40, 44, 50)
PAPER = (252, 252, 249)
STROKE_W = 4
SIZE_TIERS = [44, 38, 32, 26]
LINE_H = 1.3
PAD = 26          # 文字距气泡边
JITTER = 2.2      # 手绘抖动幅度

# 每格：源图 + 气泡定义（比例坐标：x0,y0,x1,y1, 说话人, 文案, 尾巴指向比例点）
JOBS = {
    "v8-01": {"src": "panels/v8-01.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "波普，最近人人都在聊FDE，它到底是个什么岗位？", (0.40, 0.62)),
        (0.56, 0.05, 0.95, 0.28, "p", "前沿部署工程师——把AI模型送进客户现场的人。", (0.70, 0.42)),
    ]},
    "v8-02": {"src": "panels/v8-02.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "听起来就是搞实施部署的？和普通工程师有啥区别？", (0.38, 0.60)),
        (0.56, 0.05, 0.95, 0.28, "p", "普通工程师对代码负责，FDE对业务结果负责。", (0.72, 0.40)),
    ]},
    "v8-03": {"src": "panels/v8-03.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "客户现场没有标准答案，他们靠什么干活？", (0.40, 0.60)),
        (0.56, 0.05, 0.95, 0.28, "p", "四成时间写代码，六成时间泡在现场磨需求。", (0.70, 0.42)),
    ]},
    "v8-04": {"src": "panels/v8-04.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "听说这岗位最近火得一塌糊涂？", (0.38, 0.58)),
        (0.56, 0.05, 0.95, 0.28, "p", "招聘量一年涨了十倍不止，大厂都在抢人。", (0.70, 0.40)),
    ]},
    "v8-05": {"src": "panels/v8-05.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "为什么偏偏是现在爆发？", (0.40, 0.58)),
        (0.56, 0.05, 0.95, 0.28, "p", "模型已经很强，卡住AI落地的，是最后一公里。", (0.70, 0.40)),
    ]},
    "v8-06": {"src": "panels/v8-06.raw.jpg", "bubbles": [
        (0.06, 0.06, 0.46, 0.30, "m", "那什么样的人能干这行？", (0.38, 0.58)),
        (0.56, 0.05, 0.95, 0.28, "p", "懂技术、懂业务、还敢背结果——三样都要。", (0.70, 0.40)),
    ]},
    "v8-07": {"src": "panels/v8-07.raw.jpg", "bubbles": [
        (0.40, 0.06, 0.86, 0.32, "p", "AI价值不在论文里，在客户的现场里。", (0.66, 0.52)),
    ]},
}


def jitter_line(d, p0, p1, seed=[0]):
    """带轻微抖动的线段（分段小折线），模拟手绘笔触。"""
    seed[0] += 1
    x0, y0 = p0
    x1, y1 = p1
    n = max(3, int(math.hypot(x1 - x0, y1 - y0) / 26))
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        if 0 < i < n:
            x += math.sin(seed[0] * 12.9898 + i * 78.233) * JITTER
            y += math.cos(seed[0] * 45.164 + i * 12.731) * JITTER
        pts.append((x, y))
    d.line(pts, fill=INK, width=4, joint="curve")


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


def draw_m_bubble(d, box):
    """小码：圆角矩形气泡。"""
    x0, y0, x1, y1 = box
    r = 34
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=PAPER, outline=INK, width=4)
    # 手绘感：外沿再描一圈抖动线
    jitter_line(d, (x0 + r, y0), (x1 - r, y0))
    jitter_line(d, (x0 + r, y1), (x1 - r, y1))
    jitter_line(d, (x0, y0 + r), (x0, y1 - r))
    jitter_line(d, (x1, y0 + r), (x1, y1 - r))
    # 尾巴（朝左下说话人）
    jitter_line(d, (x0 + 46, y1 - 4), (x0 + 10, y1 + 52))
    jitter_line(d, (x0 + 10, y1 + 52), (x0 + 92, y1 - 4))


def jitter_ellipse(d, box, seed):
    """沿椭圆轮廓采样的手绘抖动描边（R15：不许用直线连端点，会穿模成横线）。
    抖动幅度随接近长轴端点衰减到零，避免端点处溢出气泡包围盒。"""
    seed[0] += 1
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    a, b = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    n = max(28, int((a + b) / 5))
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        decay = abs(math.sin(t))  # 上下顶点=1，左右端点=0
        x = cx + a * math.cos(t) + math.sin(seed[0] * 12.9898 + i * 78.233) * JITTER * decay
        y = cy + b * math.sin(t) + math.cos(seed[0] * 45.164 + i * 12.731) * JITTER * decay
        pts.append((x, y))
    d.line(pts, fill=INK, width=STROKE_W, joint="curve")


def draw_p_bubble(d, box, seed=None):
    """波普：椭圆气泡 + 锯齿尾（描边沿椭圆轮廓，无穿模直线）。"""
    x0, y0, x1, y1 = box
    d.ellipse([x0, y0, x1, y1], fill=PAPER, outline=INK, width=STROKE_W)
    sd = seed if seed is not None else [0]
    jitter_ellipse(d, box, sd)
    cx = (x0 + x1) / 2
    # 锯齿尾（朝下方说话人）
    tip = (cx + 60, y1 + 58)
    for a, b in [((cx - 46, y1 - 6), (cx - 12, y1 + 26)),
                 ((cx - 12, y1 + 26), tip),
                 (tip, (cx + 26, y1 + 24)),
                 ((cx + 26, y1 + 24), (cx + 52, y1 - 6))]:
        jitter_line(d, a, b, sd)


def render(name, job):
    img = Image.open(HERE / job["src"]).convert("RGB")
    if img.size[0] != 1080:
        img = img.resize((1080, round(img.size[1] * 1080 / img.size[0])), Image.LANCZOS)
    W, H = img.size
    d = ImageDraw.Draw(img)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    report = []
    for bx in job["bubbles"]:
        x0, y0, x1 = int(bx[0] * W), int(bx[1] * H), int(bx[2] * W)
        text, sp = bx[5], bx[4]
        iw = (x1 - x0) - PAD * 2
        # 统一 44px：由文字需求推导气泡高度（上部留白区足够）
        size = 44
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap(text, font, iw, probe)
        lh = size * LINE_H
        needed = int(len(lines) * lh + PAD * 2)
        y1 = min(y0 + needed, int(0.50 * H))
        ih = (y1 - y0) - PAD * 2
        if len(lines) * lh > ih:
            # 允许底线到 0.55H；仍不够才降档
            y1 = y0 + needed
            ih = (y1 - y0) - PAD * 2
            if len(lines) * lh > ih:
                for F in SIZE_TIERS[1:]:
                    size = F
                    font = ImageFont.truetype(FONT_PATH, size)
                    lines = wrap(text, font, iw, probe)
                    lh = size * LINE_H
                    if len(lines) * lh <= ih:
                        break
        if sp == "m":
            draw_m_bubble(d, (x0, y0, x1, y1))
        else:
            draw_p_bubble(d, (x0, y0, x1, y1), [0])
        cy = y0 + PAD + ih / 2 - len(lines) * lh / 2 + lh / 2
        for ln in lines:
            d.text(((x0 + x1) / 2, cy), ln, font=font, fill=INK, anchor="mm")
            cy += lh
        report.append({"speaker": sp, "size": size, "lines": len(lines)})
    out = HERE / f"{name}.final.jpg"
    img.save(out, quality=95)
    return {"out": out.name, "bubbles": report}


def main():
    report = {}
    for name, job in JOBS.items():
        report[name] = render(name, job)
        print(name, json.dumps(report[name]["bubbles"], ensure_ascii=False))
    (HERE / "v8_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved v8_report.json")


if __name__ == "__main__":
    main()
