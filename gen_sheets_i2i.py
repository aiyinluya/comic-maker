#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五件套 i2i 生成：文生图故障绕行（用定妆照作参考图的图生图路径）。"""
import subprocess
import sys
import time
from pathlib import Path

GEN = r"C:\Users\liz-an\.openclaw-autoclaw\workspace\skills\autoglm-generate-image-seedream\generate-image-seedream.py"
REF = r"assets\characters\xiaoke-ref-manga.jpg"

SHEETS = {
    "sheet-expressions": "以参考图中的两个角色为主角，创作角色设定集表情表：网格排列六个表情头像（开心、惊讶、疑惑、思考、得意、无奈），每个头像下方留空白，不写任何文字",
    "sheet-poses": "以参考图中的两个角色为主角，创作角色设定集动作表：网格排列六个常用动作（走路、坐下打字、挥手、思考托腮、指着屏幕、竖大拇指），不写任何文字",
    "sheet-turnaround": "以参考图中的两个角色为主角，创作角色设定集转面图：每个角色的正面、侧面、背面三视图，两排展示，不写任何文字",
}

out_dir = Path("assets/characters")
out_dir.mkdir(parents=True, exist_ok=True)

failed = []
for name, prompt in SHEETS.items():
    ok = False
    for attempt in range(1, 4):
        r = subprocess.run(
            [sys.executable, GEN, prompt, REF,
             "--raw", str(out_dir / f"{name}.raw.jpg")],
            capture_output=True, text=True, encoding="utf-8", timeout=360)
        ok = r.returncode == 0 and '"image_url": ""' not in r.stdout
        print(name, f"attempt {attempt}:", "OK" if ok else "500")
        if ok:
            break
        time.sleep(15)
    if not ok:
        failed.append(name)

print("i2i sheets done, failed:", failed if failed else "none")
sys.exit(1 if failed else 0)
