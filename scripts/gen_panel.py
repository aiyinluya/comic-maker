#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单格生成一条龙：调 seedream 文生图/图生图 -> 解析 image_url -> 下载原图 -> 缩放到 900px。
URL 不经过对话层，避免截断问题。在 workspace 根目录运行。
用法: python gen_panel.py "<提示词>" "<参考图URL或不填>" <输出raw路径> <输出900px路径>
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SEEDREAM = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\generate-image-seedream.py"


def main():
    prompt = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ("-", "") else None
    out_raw = Path(sys.argv[sys.argv.index("--raw") + 1]) if "--raw" in sys.argv else None
    out_fit = Path(sys.argv[sys.argv.index("--fit") + 1]) if "--fit" in sys.argv else None

    cmd = [sys.executable, SEEDREAM, prompt] + ([ref] if ref else [])
    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300, env=env)
    if proc.returncode != 0:
        sys.exit(f"generate failed: {proc.stderr[-500:]}")
    data = json.loads(proc.stdout)
    url = data.get("data", {}).get("image_url")
    if not url:
        sys.exit(f"no image_url: {json.dumps(data, ensure_ascii=False)[:500]}")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    blob = urllib.request.urlopen(req, timeout=120).read()
    if out_raw:
        out_raw.parent.mkdir(parents=True, exist_ok=True)
        out_raw.write_bytes(blob)
        print(json.dumps({"ok": True, "raw": str(out_raw), "bytes": len(blob), "size_url": url[:60]}, ensure_ascii=False))

    if out_fit:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(blob))
        w, h = img.size
        if w > 900:
            img = img.resize((900, round(h * 900 / w)), Image.LANCZOS)
        img = img.convert("RGB")
        out_fit.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_fit, quality=92)
        print(json.dumps({"ok": True, "fit": str(out_fit), "size": list(img.size)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
