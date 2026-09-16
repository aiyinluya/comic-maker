#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_panel.py — 漫画格修字闭环：OCR 比对 → image-edit 整句重写 → 2 轮失败转 patch_text。

用法:
  python fix_panel.py --panel panels/v8-01.raw.jpg --bubbles bubbles.json --key v8-01 \
      --expect "气泡1台词|气泡2台词"
流程:
  1) OCR 转录（autoglm-image-recognition）并与期望逐字比对
  2) 有错 → image-edit 定点修字（整句重写失败气泡）
  3) 重 OCR 复验；同一气泡 2 轮仍错 → 转 patch_text.py 程序化重排（退出码 2 提示人工/脚本接力）
结果: fix_report.json 落台账。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REC = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-image-recognition\image-recognition.py"
UP = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\upload-mix.py"
EDIT = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-image-edit\image-edit.py"
MAX_ROUNDS = 2


def ocr(url, goal):
    q = (f"逐字转录这幅漫画里所有白色对话气泡的文字（用竖线分隔多个气泡），"
         f"与目标逐字比对——目标：{goal}。只回答三点：1)实际转录 2)不一致的每个字 3)结论：汉字全对或有错")
    r = subprocess.run([sys.executable, REC, url, q],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    return r.stdout if r.returncode == 0 else f"OCR_FAIL: {r.stderr[-150:]}"


def upload(path):
    r = subprocess.run([sys.executable, UP, str(path)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    return json.loads(r.stdout)["data"]["oss_info"][0]["oss_url"]


def edit_bubble(url, texts):
    """texts: ['台词1','台词2'] 按左右气泡顺序整句重写。"""
    if len(texts) == 1:
        inst = f"只把画面中白色对话气泡里的文字全部擦除，重新逐字精确写成：{texts[0]}"
    else:
        inst = (f"只把画面中两个白色对话气泡里的文字全部擦除，重新逐字精确书写："
                f"左侧男生的气泡写成：{texts[0]}，右侧机器人的气泡写成：{texts[1]}")
    inst += ("。字体保持圆润黑体，清晰无错别字。画面其他所有内容保持完全不变，"
             "不要添加任何新元素或新文字")
    r = subprocess.run([sys.executable, EDIT, url, inst],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)["data"]["image_url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True, help="当前格图片（raw 或上一轮 fixed）")
    ap.add_argument("--bubbles", required=True, help="bubbles.json")
    ap.add_argument("--key", required=True, help="panel key（如 v8-01）")
    ap.add_argument("--expect", required=True, help="期望台词，竖线分隔多气泡")
    ap.add_argument("--max-rounds", type=int, default=MAX_ROUNDS)
    a = ap.parse_args()

    panel = Path(a.panel)
    goal = a.expect
    cur = panel
    log = {"panel": a.key, "expect": goal, "rounds": []}

    for rnd in range(1, a.max_rounds + 1):
        url = upload(cur)
        verdict = ocr(url, goal)
        log["rounds"].append({"round": rnd, "verdict": verdict[:500]})
        print(f"--- round {rnd} OCR ---")
        print(verdict[:400])
        if "汉字全对" in verdict or "全部正确" in verdict:
            (panel.parent / "fix_report.json").write_text(
                json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"FIX-PASS after {rnd-1} edit(s)")
            sys.exit(0)
        # 仍有错 → 整句重写
        out_url = edit_bubble(url, goal.split("|"))
        if not out_url:
            print("edit failed")
            break
        import urllib.request
        data = urllib.request.urlopen(
            urllib.request.Request(out_url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=120).read()
        cur = panel.parent / f"{panel.stem}.fix{rnd}.jpg"
        cur.write_bytes(data)
        print(f"round {rnd} edited -> {cur.name}")

    print("FIX-ESCALATE: 2 轮未过，转 patch_text.py 程序化重排（退出码 2）")
    (panel.parent / "fix_report.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(2)


if __name__ == "__main__":
    main()
