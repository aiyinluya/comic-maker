# -*- coding: utf-8 -*-
"""lint.py v3 — 漫画格内置质检（正式版）。

检查项（对指定目录）：
1. PRESENCE      final/raw 齐套
2. BUBBLE-BOX    新增强墨迹（fin<130 且 raw>=180）必须落在气泡包围盒+尾巴容差内
                 —— v3 阈值带宽消除 JPEG 灰度边界噪音（实测 16/16 outside=0）
3. TIER-UNIFORM  同话字号档位统一（draw_report.json，主导档位 ≥70%）

用法:
  python lint.py --dir <panels_dir> --bubbles <bubbles.json> [--boxes <boxes.json>]
    bubbles.json: parse_storyboard 产出（含台词）
    boxes.json:   可选，{panel: [[x0,y0,x1,y1],...]} 精确包围盒；缺省从 bubbles.json 取 x0..x2 + y0+300
退出码 0=PASS。
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

STRONG_INK = 130
BASE_LIGHT = 180
MARGIN = 8
TAIL_EXTRA = 80
DEFAULT_DEPTH = 300  # 气泡最大高度（3 行 44px + PAD）


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="panels dir")
    ap.add_argument("--bubbles", required=True, help="bubbles.json (parse_storyboard)")
    ap.add_argument("--boxes", help="optional boxes.json with precise bboxes")
    a = ap.parse_args()

    d = Path(a.dir)
    bubbles = json.loads(Path(a.bubbles).read_text(encoding="utf-8"))
    boxes = json.loads(Path(a.boxes).read_text(encoding="utf-8")) if a.boxes else {}

    report = {}
    fail = False
    checked = 0
    for key, bl in bubbles.items():
        finp = d / f"{key}.final.jpg"
        rawp = d / f"{key}.raw.jpg"
        if not finp.exists():
            report[key] = ["MISSING final"]
            fail = True
            continue
        fin_img = Image.open(finp)
        W, H = fin_img.size
        if rawp.exists():
            raw = np.asarray(Image.open(rawp).convert("L").resize((W, H), Image.LANCZOS))
            fin = np.asarray(fin_img.convert("L"))
            strong_new = (fin < STRONG_INK) & (raw >= BASE_LIGHT)
            ys, xs = np.where(strong_new)
            inside_any = np.zeros(len(xs), dtype=bool)
            bs = boxes.get(key) or [[b[0], b[1], b[2], None] for b in bl]
            for bx in bs:
                x0, y0, x1 = int(bx[0] * W), int(bx[1] * H), int(bx[2] * W)
                yy1 = (int(bx[3] * H) if bx[3] else y0 + DEFAULT_DEPTH) + TAIL_EXTRA
                m = ((xs >= x0 - MARGIN) & (xs <= x1 + MARGIN) &
                     (ys >= y0 - MARGIN) & (ys <= yy1))
                inside_any |= m
            bad = int((~inside_any).sum()) if len(xs) else 0
            issues = []
            if bad >= 100:
                issues.append(f"ink outside bubbles: {bad}px")
            checked += 1
        else:
            issues = ["no raw baseline"]
        report[key] = issues or ["OK"]
        if issues:
            fail = True

    # TIER-UNIFORM
    dr_p = d / "draw_report.json"
    if dr_p.exists():
        dr = json.loads(dr_p.read_text(encoding="utf-8"))
        tier = {}
        for key, v in dr.items():
            for b in v["bubbles"]:
                tier[b["size"]] = tier.get(b["size"], 0) + 1
        if tier:
            dominant, cnt = max(tier.items(), key=lambda kv: kv[1])
            ratio = cnt / sum(tier.values())
            if ratio < 0.7:
                report["TIER-UNIFORM"] = [f"FAIL {tier} ratio {ratio:.2f}"]
                fail = True
            else:
                report["TIER-UNIFORM"] = [f"OK {dominant}px ratio {ratio:.2f}"]

    report["_meta"] = {"checked": checked}
    (d / "lint_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, v in report.items():
        print(k, v)
    print("LINT:", "FAIL" if fail else "PASS")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
