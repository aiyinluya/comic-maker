#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五件套生成器（重试版）：表情表 + 动作表，服务恢复后执行。
用法: python gen_sheets.py
"""
import subprocess
import sys
import time
from pathlib import Path

GEN = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\generate-image-seedream.py"
DNA = ("日式手绘漫画风格，铅笔质感线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，"
       "米白纸感背景，均匀描边，无任何文字")
CHAR = ("戴圆框眼镜穿深灰连帽衫的男生，和白色胶囊形小机器人（蓝色眼睛、头顶天线、胸口橙色徽章）")

SHEETS = {
    "sheet-expressions": f"角色设定集表情表插画：{CHAR}，网格排列六个表情头像：开心、惊讶、疑惑、思考、得意、无奈。{DNA}",
    "sheet-poses": f"角色设定集动作表插画：{CHAR}，网格排列六个常用动作：走路、坐下打字、挥手、思考托腮、指着屏幕、竖大拇指。{DNA}",
    "sheet-turnaround": f"角色设定集转面图插画：{CHAR}，三视图排列：正面、侧面、背面，两排展示。{DNA}",
}

out_dir = Path("assets/characters")
out_dir.mkdir(parents=True, exist_ok=True)

failed = []
for name, prompt in SHEETS.items():
    ok = False
    for attempt in range(1, 4):
        r = subprocess.run(
            [sys.executable, GEN, prompt, "--raw", str(out_dir / f"{name}.raw.jpg")],
            capture_output=True, text=True, encoding="utf-8", timeout=360)
        ok = r.returncode == 0 and '"image_url": ""' not in r.stdout
        print(name, f"attempt {attempt}:", "OK" if ok else "500")
        if ok:
            break
        time.sleep(20)
    if not ok:
        failed.append(name)

print("sheets done, failed:", failed if failed else "none")
sys.exit(1 if failed else 0)
