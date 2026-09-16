#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_storyboard.py — 把分镜脚本（Markdown 表格）解析为绘泡配置（单一事实源）。

分镜表格式约定（storyboard.md）：
| # | 提问（小码） | 解答（波普） | 画面 |
每行一个问答格；提问列为空 → 该格无气泡（过场/收尾由解答列或「（收尾）」标记）。
输出：JSON {panel_key: [(x0,y0,x1,y1,speaker,text), ...]}，气泡框按左右站位模板生成。

用法:
  python parse_storyboard.py --storyboard sb.md --layout left-right --out bubbles.json
  python draw_bubbles.py --config bubbles.json   # 无缝衔接现有引擎
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 左右站位模板（比例坐标）：小码左（圆角矩形）、波普右（椭圆锯齿尾）
LAYOUTS = {
    "left-right": {
        "m": (0.06, 0.05, 0.50, None),   # y1 由 draw_bubbles 按文字高度推导
        "p": (0.56, 0.05, 0.95, None),
    },
    "closing-p": {  # 收尾格：仅波普居中大泡
        "p": (0.40, 0.05, 0.88, None),
    },
}


def parse_markdown_table(md: str):
    """提取首个含「提问」与「解答」表头的 Markdown 表格行。
    若行内引用了图片文件名（v8-XX / panel-XX），则从该列提取格号；
    台词列含文件名时自动跳过该标记取真实台词。"""
    rows = []
    in_table = False
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_table:
                joined = "".join(cells)
                if "提问" in joined and "解答" in joined:
                    in_table = True
                continue
            if set("".join(cells)) <= set("-: "):  # 分隔行
                continue
            rows.append(cells)
        elif in_table and not s:
            break
    return rows


def strip_ref(cell: str) -> str:
    """台词列若误以文件名开头（v8-XX / panel-XX），剥掉。"""
    return re.sub(r"^(v8-\d{2}|panel-\d{2})\s*", "", cell)


def clean(text: str) -> str:
    """去掉 （收尾）（过场）等舞台指示与 markdown 粗体标记。"""
    t = re.sub(r"[（(][^）)]*[)）]", "", text)
    t = t.replace("**", "")
    return t.strip()


def build_bubbles(rows, layout="left-right"):
    """按行生成气泡配置。列结构容错：
    - 4 列（#|提问|解答|画面）：台词在 1/2 列；
    - 5 列（#|文件|提问|解答|画面）：台词在 2/3 列；
    - 提问列含「过场」→ 整格无气泡；含「收尾」→ 仅保留波普居中收尾泡。
    气泡框 y1=None（由 draw_bubbles 按文字推导高度）。
    """
    out = {}
    idx = 0
    for cells in rows:
        if len(cells) >= 5:
            ref, q, a = cells[1], cells[2], cells[3]
        elif len(cells) == 4:
            ref, q, a = "", cells[1], cells[2]
        else:
            continue
        ref_m = re.search(r"(v8-\d{2}|panel-\d{2}|v8-strip)", ref)
        key = ref_m.group(1) if ref_m else f"panel-{idx+1:02d}"
        idx += 1
        if "过场" in q:
            continue
        bubbles = []
        closing = ("收尾" in q) or (q == "" and bool(clean(a)))
        if not closing and strip_ref(q):
            x0, y0, x1, _ = LAYOUTS[layout]["m"]
            bubbles.append([x0, y0, x1, None, "m", strip_ref(q)])
        if strip_ref(a):
            lay = LAYOUTS["closing-p"] if closing else LAYOUTS[layout]
            x0, y0, x1, _ = lay["p"]
            bubbles.append([x0, y0, x1, None, "p", strip_ref(a)])
        if bubbles:
            out[key] = bubbles
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--layout", default="left-right", choices=list(LAYOUTS))
    ap.add_argument("--out", default="bubbles.json")
    a = ap.parse_args()
    md = Path(a.storyboard).read_text(encoding="utf-8")
    rows = parse_markdown_table(md)
    if not rows:
        sys.exit("no Q/A table found in storyboard")
    bubbles = build_bubbles(rows, a.layout)
    Path(a.out).write_text(json.dumps(bubbles, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"parsed {len(rows)} rows -> {len(bubbles)} bubble panels -> {a.out}")


if __name__ == "__main__":
    main()
