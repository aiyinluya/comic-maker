#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article_to_storyboard.py — 把科普文章（Markdown）自动转换为分镜脚本草稿。

规则模板（结构映射）：
  引入段   → 格 1（抛出问题）
  正文节 1 → 格 2（给核心定义/答案）
  正文节 2 → 格 3（过场条格，无气泡）
  正文节 3-4 → 格 4-5（展开细节，一节一格）
  正文节 5 → 格 6（边界/误区）
  要点小结 → 格 7（三件事口诀）
  金句（引用块）→ 格 8（收尾）

台词从各节首句/小结句自动提取并压缩到 ≤22 字；画面列填占位说明供人工润色。
用法: python article_to_storyboard.py --article articles/01-mcp.md --title "MCP：AI 的 USB-C 接口" --out sb.md
"""
import argparse
import re
from pathlib import Path


def split_sections(md: str):
    """返回 [(heading, body_first_sentence)] 列表；跳过标题前内容。"""
    sections = []
    cur_h, cur_body = None, []
    for line in md.splitlines():
        if line.startswith("## "):
            if cur_h:
                sections.append((cur_h, " ".join(cur_body)))
            cur_h, cur_body = line[3:].strip(), []
        elif cur_h and line.strip() and not line.startswith(">") and not line.startswith("|") \
                and not re.match(r"^\d+\.", line.strip()) and not line.startswith("- "):
            cur_body.append(line.strip())
        elif cur_h and line.startswith(">"):
            cur_body.append(line[1:].strip())
    if cur_h:
        sections.append((cur_h, " ".join(cur_body)))
    return sections


def first_sentence(text: str, limit=22):
    text = re.sub(r"\*\*|`|#", "", text)
    text = re.sub(r"\s+", "", text)
    m = re.split(r"[。！？；]", text)
    s = m[0] if m and m[0] else text
    return s[:limit]


def shorten(text: str, limit=22):
    """压缩到 limit 字内：优先取冒号前段，再截断。"""
    text = re.sub(r"\*\*|`", "", text)
    text = text.split("——")[0] if "——" in text else text
    s = first_sentence(text, limit)
    return s[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", default="storyboard-auto.md")
    a = ap.parse_args()
    md = Path(a.article).read_text(encoding="utf-8")

    # 金句：blockquote 中最长的陈述句（排除标题/署名行）
    quotes = [l[1:].strip() for l in md.splitlines()
              if l.startswith(">") and len(l) > 12
              and "码事漫谈" not in l and "AI 科普系列" not in l
              and a.title not in l]
    if not quotes:
        # 无金句 blockquote 时：从「要点小结」节取含加粗的最长句
        in_sum = False
        for l in md.splitlines():
            if l.startswith('## '):
                in_sum = '要点' in l
                continue
            if in_sum and '**' in l and len(l) > 20:
                quotes.append(re.sub(r'[*>-]', '', l).strip())
        quotes = [q for q in quotes if len(q) >= 12]
    quote = max(quotes, key=len) if quotes else a.title

    sections = split_sections(md)
    body = [(h, b) for h, b in sections if "引入" not in h and "要点" not in h and "延伸" not in h]
    summary = next((b for h, b in sections if "要点" in h), "")

    # 台词生成
    q1 = f"波普，{a.title.split('：')[0]}到底是什么？"
    a1 = shorten(body[0][1]) if body else "让 AI 一次接遍所有工具。"
    q2 = f"{a1[:6]}？具体怎么做到的？"
    a2 = shorten(body[1][1]) if len(body) > 1 else "大家约定同一个标准。"
    q4 = f"那实际用起来是什么样？"
    a4 = shorten(body[2][1]) if len(body) > 2 else "插上就会用，工具随手可及。"
    q5 = f"它有什么局限吗？"
    a5 = shorten(body[3][1]) if len(body) > 3 else "有边界——标准之外仍有功课。"
    q6 = f"那我们该怎么用好它？"
    a6 = shorten(body[4][1]) if len(body) > 4 else "先懂原理，再动手实践。"
    q7 = f"所以关键是什么？"
    a7 = "记住口诀，剩下的交给实践。"
    a8 = shorten(quote, 24)

    rows = [
        ("1", "panel-01", q1, a1, "（画面占位：场景+角色动作）"),
        ("2", "panel-02", q2, a2, "（画面占位：概念可视化）"),
        ("S", "v8-strip", "（过场，无气泡）", "（无气泡）", "（画面占位：过场条格）"),
        ("3", "panel-04", q4, a4, "（画面占位：展开意象）"),
        ("4", "panel-05", q5, a5, "（画面占位：边界意象）"),
        ("5", "panel-06", q6, a6, "（画面占位：深化意象）"),
        ("6", "panel-07", q7, a7, "（画面占位：口诀呈现）"),
        ("7", "panel-08", "（收尾）", a8, "（画面占位：金句收尾）"),
    ]

    out = [f"# 分镜（自动草稿）· {a.title}", "",
           "> 由 article_to_storyboard.py 自动生成——台词为压缩草稿，画面列需人工润色后锁定。", "",
           "| # | 文件 | 提问（小码） | 解答（波普） | 画面 |",
           "|---|---|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    out.append("")
    out.append("### 自动提取的金句候选")
    out.append(f"> {quote}")
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print(f"storyboard draft -> {a.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
