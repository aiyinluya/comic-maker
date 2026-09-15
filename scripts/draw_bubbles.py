#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""draw_bubbles.py — 在无气泡空场景漫画格上绘制气泡与文字（v8 结构派核心）。

设计原则（见 docs/ROOT-CAUSES.md R12-R14）：
- 全部源图先重采样到成品宽度坐标系（config.width），字号档位只在成品坐标系定义
- 由文字需求推导气泡高度（统一档位放不下才按档位表降档）
- UNIFIED 常量表是唯一样式出处；说话人区分只靠气泡形状

用法：
  python draw_bubbles.py --config bubbles.json

config 示例见 examples/bubbles.example.json
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── UNIFIED 文字规范（唯一出处；禁止在调用方覆盖）──
TEXT_COLOR = (35, 35, 40)
PAPER = (252, 252, 249)
INK = (40, 44, 50)
LINE_H = 1.3
PAD = 26            # 文字距气泡内边（px，成品坐标系）
JITTER = 2.2        # 手绘抖动幅度
STROKE_W = 4
SIZE_TIERS = [44, 38, 32, 26]   # 全局统一档位：44 优先，放不下才逐级降档
BLOCK_MAX_FRAC = 0.92           # 文字块高 ≤ 气泡内高 × 0.92

# ── 跨平台字体探测 ──
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",                       # Windows 微软雅黑 Bold
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/PINGFANG.ttc",                 # macOS 苹方
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Linux Noto
    "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Bold.otf",
]


def load_font(size, font_path=None):
    candidates = [font_path] if font_path else []
    candidates += FONT_CANDIDATES
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    raise SystemExit(
        "No CJK font found. Set \"font\" in config (see docs/INTEGRATION.md).")


def jitter_line(d, p0, p1, seed):
    """带轻微抖动的手绘感线段。"""
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
    d.line(pts, fill=INK, width=STROKE_W, joint="curve")


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


def draw_m_bubble(d, box, seed):
    """提问者：圆角矩形气泡 + 左下尾巴。"""
    x0, y0, x1, y1 = box
    r = 34
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=PAPER, outline=INK, width=STROKE_W)
    jitter_line(d, (x0 + r, y0), (x1 - r, y0), seed)
    jitter_line(d, (x0 + r, y1), (x1 - r, y1), seed)
    jitter_line(d, (x0, y0 + r), (x0, y1 - r), seed)
    jitter_line(d, (x1, y0 + r), (x1, y1 - r), seed)
    jitter_line(d, (x0 + 46, y1 - 4), (x0 + 10, y1 + 52), seed)
    jitter_line(d, (x0 + 10, y1 + 52), (x0 + 92, y1 - 4), seed)


def draw_p_bubble(d, box, seed):
    """解答者：椭圆气泡 + 锯齿尾。"""
    x0, y0, x1, y1 = box
    d.ellipse([x0, y0, x1, y1], fill=PAPER, outline=INK, width=STROKE_W)
    jitter_line(d, (x0, y0), (x1, y0), seed)
    jitter_line(d, (x0, y1), (x1, y1), seed)
    cx = (x0 + x1) / 2
    tip = (cx + 60, y1 + 58)
    for a, b in [((cx - 46, y1 - 6), (cx - 12, y1 + 26)),
                 ((cx - 12, y1 + 26), tip),
                 (tip, (cx + 26, y1 + 24)),
                 ((cx + 26, y1 + 24), (cx + 52, y1 - 6))]:
        jitter_line(d, a, b, seed)


def render_panel(name, panel, cfg, probe, seed):
    img = Image.open(panel["src"]).convert("RGB")
    width = cfg.get("width", 1080)
    if img.size[0] != width:
        img = img.resize((width, round(img.size[1] * width / img.size[0])), Image.LANCZOS)
    W, H = img.size
    d = ImageDraw.Draw(img)
    report = []
    for b in panel["bubbles"]:
        x0, y0, x1 = int(b["x0"] * W), int(b["y0"] * H), int(b["x1"] * W)
        text, sp = b["text"], b["speaker"]
        iw = (x1 - x0) - PAD * 2
        # 统一档位求解：44 优先；气泡高度由文字需求推导（R13）
        size = None
        for F in cfg.get("size_tiers", SIZE_TIERS):
            fnt = load_font(F, cfg.get("font"))
            lines = wrap(text, fnt, iw, probe)
            lh = F * LINE_H
            needed = int(len(lines) * lh + PAD * 2)
            y1 = min(y0 + needed, int(cfg.get("max_bubble_bottom", 0.55) * H))
            ih = (y1 - y0) - PAD * 2
            if len(lines) * lh <= ih:
                size, font = F, fnt
                break
        if size is None:
            F = cfg.get("size_tiers", SIZE_TIERS)[-1]
            size, font = F, load_font(F, cfg.get("font"))
            lines = wrap(text, font, iw, probe)
            lh = size * LINE_H
            needed = int(len(lines) * lh + PAD * 2)
            y1 = y0 + needed
            ih = (y1 - y0) - PAD * 2
        box = (x0, y0, x1, y1)
        if sp == "m":
            draw_m_bubble(d, box, seed)
        else:
            draw_p_bubble(d, box, seed)
        cy = y0 + PAD + ih / 2 - len(lines) * lh / 2 + lh / 2
        for ln in lines:
            d.text(((x0 + x1) / 2, cy), ln, font=font, fill=TEXT_COLOR, anchor="mm")
            cy += lh
        report.append({"speaker": sp, "size": size, "lines": len(lines)})
    out = panel.get("out") or Path(panel["src"]).with_name(
        Path(panel["src"]).stem + cfg.get("output_suffix", ".final.jpg"))
    img.save(out, quality=95)
    return {"out": str(out), "bubbles": report}


def main():
    ap = argparse.ArgumentParser(description="Draw speech bubbles & text on bubble-free panels.")
    ap.add_argument("--config", required=True, help="JSON config (see examples/bubbles.example.json)")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    base = Path(args.config).parent
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    seed = [0]
    report = {}
    for name, panel in cfg["panels"].items():
        panel = dict(panel)
        panel["src"] = str((base / panel["src"]).resolve()) if not Path(panel["src"]).is_absolute() else panel["src"]
        if "out" in panel:
            panel["out"] = str((base / panel["out"]).resolve()) if not Path(panel["out"]).is_absolute() else panel["out"]
        report[name] = render_panel(name, panel, cfg, probe, seed)
        print(name, json.dumps(report[name]["bubbles"], ensure_ascii=False))
    out_json = cfg.get("report", "draw_report.json")
    (base / out_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out_json}")


if __name__ == "__main__":
    main()
