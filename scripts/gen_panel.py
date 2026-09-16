#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_panel.py — 单格出图一条龙（v2）：
调 seedream 文生图/图生图 → 下载 → 缩放到 900px。
URL 不经过对话层。支持：
  --ref-local <文件>   本地定妆照自动上传 OSS 取 URL（优先于位置参数 ref）
  --retries N          生成失败重试次数（默认 2）
  gen_one()            供并行调度复用的原子函数

用法:
  python gen_panel.py "<提示词>" ["<参考图URL>" | --ref-local <本地文件>] \
      --raw out.raw.jpg --fit out.jpg [--retries 3]
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

# 后端脚本可经环境变量覆盖（OpenAI 兼容 API / ComfyUI 适配见 docs/INTEGRATION.md）
# default: 本机 AutoGLM 技能脚本；CI 允许默认值存在，但不许新增裸路径
_SEEDREAM_DEFAULT = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\generate-image-seedream.py"
_UPLOAD_DEFAULT = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\upload-mix.py"
SEEDREAM = os.environ.get("COMIC_SEEDREAM", _SEEDREAM_DEFAULT)
UPLOAD = os.environ.get("COMIC_UPLOAD", _UPLOAD_DEFAULT)


def local_ref_to_url(local_path):
    """本地参考图 → OSS 公网 URL（经 upload-mix）。失败抛异常。"""
    r = subprocess.run([sys.executable, UPLOAD, str(local_path)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"upload failed: {r.stderr[-200:]}")
    return json.loads(r.stdout)["data"]["oss_info"][0]["oss_url"]


def gen_one(args_tuple):
    """单格生成原子函数（并行安全）。args: (idx, prompt, ref, out_raw, out_fit, retries)
    返回 (idx, ok, message)。"""
    idx, prompt, ref, out_raw, out_fit, retries = args_tuple
    import io
    import os
    last_err = ""
    for attempt in range(1, retries + 1):
        try:
            cmd = [sys.executable, SEEDREAM, prompt] + ([ref] if ref else [])
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", timeout=300, env=env)
            if proc.returncode != 0:
                last_err = proc.stderr[-300:]
                continue
            data = json.loads(proc.stdout)
            url = (data.get("data") or {}).get("image_url")
            if not url:
                last_err = "no image_url: " + json.dumps(data, ensure_ascii=False)[:200]
                continue
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            blob = urllib.request.urlopen(req, timeout=120).read()
            if out_raw:
                out_raw = Path(out_raw)
                out_raw.parent.mkdir(parents=True, exist_ok=True)
                out_raw.write_bytes(blob)
            if out_fit:
                from PIL import Image
                img = Image.open(io.BytesIO(blob))
                w, h = img.size
                if w > 900:
                    img = img.resize((900, round(h * 900 / w)), Image.LANCZOS)
                out_fit = Path(out_fit)
                out_fit.parent.mkdir(parents=True, exist_ok=True)
                img.convert("RGB").save(out_fit, quality=92)
            return (idx, True, f"attempt {attempt}, {len(blob)} bytes")
        except Exception as exc:  # noqa
            last_err = str(exc)[:300]
    return (idx, False, last_err)


def main():
    prompt = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ("-", "") and not sys.argv[2].startswith("--") else None
    if "--ref-local" in sys.argv:
        ref = local_ref_to_url(sys.argv[sys.argv.index("--ref-local") + 1])
        print(f"[ref-local] uploaded")
    out_raw = Path(sys.argv[sys.argv.index("--raw") + 1]) if "--raw" in sys.argv else None
    out_fit = Path(sys.argv[sys.argv.index("--fit") + 1]) if "--fit" in sys.argv else None
    retries = int(sys.argv[sys.argv.index("--retries") + 1]) if "--retries" in sys.argv else 2

    idx, ok, msg = gen_one((0, prompt, ref,
                            str(out_raw) if out_raw else None,
                            str(out_fit) if out_fit else None, retries))
    print(json.dumps({"ok": ok, "msg": msg}, ensure_ascii=False))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
