#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五件套生成 v2：复用 gen_panel.gen_one（已验证调用路径：本地图→upload-mix→OSS URL→生成）。
用法: python gen_sheets_i2i.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from gen_panel import gen_one, local_ref_to_url  # noqa: E402

REF_LOCAL = Path("assets/characters/xiaoke-ref-manga.jpg")

SHEETS = {
    "sheet-expressions": "以参考图中的两个手绘漫画角色为主角，创作角色设定集表情表：网格排列六个表情头像（开心、惊讶、疑惑、思考、得意、无奈），白底，均匀描边，不写任何文字",
    "sheet-poses": "以参考图中的两个手绘漫画角色为主角，创作角色设定集动作表：网格排列六个常用动作（走路、坐下打字、挥手、思考托腮、指着屏幕、竖大拇指），白底，不写任何文字",
    "sheet-turnaround": "以参考图中的两个手绘漫画角色为主角，创作角色设定集转面图：每个角色的正面、侧面、背面三视图，两排展示，白底，不写任何文字",
}


def main():
    ref_url = local_ref_to_url(REF_LOCAL)
    print("ref uploaded:", ref_url[:60], "...")

    jobs = []
    for name, prompt in SHEETS.items():
        out = Path("assets/characters")
        jobs.append((name, prompt, ref_url, str(out / f"{name}.raw.jpg"),
                     str(out / f"{name}.jpg"), 3))

    failed = []
    for job in jobs:
        idx, ok, msg = gen_one(job)
        print(("OK " if ok else "FAIL"), job[0], msg[:120])
        if not ok:
            failed.append(job[0])

    print("sheets done, failed:", failed if failed else "none")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
