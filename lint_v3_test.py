# -*- coding: utf-8 -*-
"""lint v3：阈值带宽判定，消除 JPEG 灰度边界噪音。
新增墨迹判定：final < 130 且 snapshot >= 180（强墨迹 vs 确定非墨迹），边界带不参与。
"""
from pathlib import Path
from PIL import Image
import numpy as np
import json

HERE = Path(__file__).parent
SCRIPTS = {
    "v8-01": [(0.06, 0.05, 0.50, 0.32, "m", "波普！我的硬盘它、它烧了！"),
              (0.56, 0.05, 0.95, 0.32, "p", "别慌。先告诉我：最后一次备份是什么时候？")],
    "v8-02": [(0.06, 0.05, 0.50, 0.32, "m", "备份……我总觉得自己会记得。"),
              (0.56, 0.05, 0.95, 0.34, "p", "现在你知道了：记忆是最不可靠的硬盘。")],
    "v8-03": [(0.06, 0.05, 0.50, 0.34, "m", "可那里有我三年代码、照片、还有日记。"),
              (0.56, 0.05, 0.95, 0.32, "p", "在某个平行世界，它们都还在。")],
    "v8-04": [(0.06, 0.05, 0.50, 0.32, "m", "什么意思？我们进去了？"),
              (0.56, 0.05, 0.95, 0.32, "p", "这是没备份的人生：所有数据都还活着的世界。")],
    "v8-05": [(0.06, 0.05, 0.50, 0.32, "m", "那扇发光的门是什么？"),
              (0.56, 0.05, 0.95, 0.34, "p", "找回数据的唯一出口——但它需要现实里的钥匙。")],
    "v8-06": [(0.06, 0.05, 0.50, 0.32, "m", "钥匙是什么？"),
              (0.56, 0.05, 0.95, 0.34, "p", "我在云端还留着一份你三个月前的同步快照。")],
    "v8-07": [(0.06, 0.05, 0.50, 0.32, "m", "所以丢失的只是……这三个月？"),
              (0.56, 0.05, 0.95, 0.32, "p", "对。人生找回来了，学费也交了。")],
    "v8-08": [(0.40, 0.05, 0.88, 0.34, "p", "没备份的人生，连后悔都是并行的。")],
}

d = Path("posts/a-backup-life/panels")
bubbles = {"v8-%02d" % i: b for i, b in zip(range(1, 9), [
    SCRIPTS[k] for k in ["v8-01", "v8-02", "v8-03", "v8-04", "v8-05", "v8-06", "v8-07", "v8-08"]])}
bubbles = {f"v8-{i:02d}": b for i, b in zip(range(1, 9),
           [SCRIPTS[f"v8-{i:02d}"] for i in range(1, 9)])}

allok = True
for key, bl in bubbles.items():
    fin = np.asarray(Image.open(d / f"{key}.final.jpg").convert("L"))
    snap = np.load(d / f"{key}.ink_snap.npz")["gray"]
    strong_new = (fin < 130) & (snap >= 180)
    ys, xs = np.where(strong_new)
    bad_total = 0
    for b in bl:
        x0, y0, x1 = int(b[0] * 1080), int(b[1] * 720), int(b[2] * 1080)
        needed_lines = b[5]
        # 气泡底 = y0 + needed；用宽松外扩 8/70
        # 从 draw_report 拿不到 yy1，这里用 0.60H 作为下界（气泡必在上半部）
        inside = ((xs >= x0 - 8) & (xs <= x1 + 8) &
                  (ys >= max(y0 - 8, 0)) & (ys <= min(y0 + int(0.60 * 720), 720)))
        bad_total += int((~inside).sum())
    status = "PASS" if bad_total < 50 else "FAIL"
    allok &= status == "PASS"
    print(key, "strong_new:", len(xs), "outside:", bad_total, status)

print("LINT v3:", "PASS" if allok else "FAIL")
