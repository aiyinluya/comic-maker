#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comic-maker 助手脚本：角色档案、定妆照登记、页面记录、尺寸与拼接。

纯 Python 标准库；Pillow 仅在 fit-width / stack 时按需导入。
数据落在仓库内 data/ 目录（characters/ = 角色档案，posts/ = 台账）。
可用 COMIC_DATA 环境变量改数据根目录，默认当前工作目录下的 data/。
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(os.environ.get("COMIC_DATA", "data"))
CHARACTERS = ROOT / "characters"
POSTS = ROOT / "posts"


def _load(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_ensure_character(args):
    path = CHARACTERS / args.slug / "manifest.json"
    data = _load(path, {})
    data.update(
        {
            "name": args.name,
            "slug": args.slug,
            "role": args.role or data.get("role", ""),
            "identity_markers": args.markers or data.get("identity_markers", ""),
        }
    )
    data.setdefault("versions", ["base"])
    _save(path, data)
    print(json.dumps({"ok": True, "manifest": str(path)}, ensure_ascii=False))


def cmd_register_ref(args):
    cdir = CHARACTERS / args.slug
    src = Path(args.image)
    if not src.exists():
        sys.exit(f"image not found: {src}")
    dest_name = "ref.jpg" if args.version == "base" else f"ref-{args.version}.jpg"
    dest = cdir / dest_name
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    path = cdir / "manifest.json"
    data = _load(path, {"name": args.slug, "slug": args.slug})
    refs = data.get("refs", {})
    refs[args.version] = dest_name
    data["refs"] = refs
    versions = data.setdefault("versions", ["base"])
    if args.version not in versions:
        versions.append(args.version)
    _save(path, data)
    print(json.dumps({"ok": True, "ref": str(dest)}, ensure_ascii=False))


def cmd_record_panel(args):
    pdir = POSTS / args.slug
    pdir.mkdir(parents=True, exist_ok=True)
    entry = {
        "characters": [c.strip() for c in args.characters.split(",") if c.strip()],
        "image": args.image,
        "question": args.question,
        "answer": args.answer,
        "notes": args.notes or "",
    }
    _save(pdir / "panel.json", entry)
    print(json.dumps({"ok": True, "record": str(pdir / "panel.json")}, ensure_ascii=False))


def cmd_fit_width(args):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow 未安装：pip install pillow（或跳过缩放，手动处理）")
    src = Path(args.image)
    img = Image.open(src)
    w, h = img.size
    if w <= args.width:
        print(json.dumps({"ok": True, "skipped": True, "size": [w, h]}, ensure_ascii=False))
        return
    nh = round(h * args.width / w)
    out = Path(args.out) if args.out else src.with_name(src.stem + f"-{args.width}w" + src.suffix)
    img.resize((args.width, nh), Image.LANCZOS).save(out, quality=92)
    print(json.dumps({"ok": True, "out": str(out), "size": [args.width, nh]}, ensure_ascii=False))


def cmd_stack(args):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow 未安装：pip install pillow")
    imgs = [Image.open(p) for p in args.images]
    width = max(im.width for im in imgs)
    resized = []
    for im in imgs:
        if im.width != width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        resized.append(im.convert("RGB"))
    gap = args.gap
    total_h = sum(im.height for im in resized) + gap * (len(resized) - 1)
    canvas = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for im in resized:
        canvas.paste(im, (0, y))
        y += im.height + gap
    canvas.save(args.out, quality=92)
    print(json.dumps({"ok": True, "out": args.out, "size": [width, total_h]}, ensure_ascii=False))


def cmd_list(args):
    chars = []
    if CHARACTERS.exists():
        for d in sorted(CHARACTERS.iterdir()):
            m = d / "manifest.json"
            if m.exists():
                chars.append(_load(m, {}))
    panels = []
    if POSTS.exists():
        for d in sorted(POSTS.iterdir()):
            p = d / "panel.json"
            if p.exists():
                panels.append({"slug": d.name, **_load(p, {})})
    print(json.dumps({"characters": chars, "panels": panels}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="comic-maker 助手")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ensure-character")
    p.add_argument("--name", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--role")
    p.add_argument("--markers")
    p.set_defaults(fn=cmd_ensure_character)

    p = sub.add_parser("register-ref")
    p.add_argument("--slug", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--version", default="base")
    p.set_defaults(fn=cmd_register_ref)

    p = sub.add_parser("record-panel")
    p.add_argument("--slug", required=True)
    p.add_argument("--characters", required=True)
    p.add_argument("--image", required=True)
    p.add_argument("--question", default="")
    p.add_argument("--answer", default="")
    p.add_argument("--notes")
    p.set_defaults(fn=cmd_record_panel)

    p = sub.add_parser("fit-width")
    p.add_argument("--image", required=True)
    p.add_argument("--width", type=int, default=900)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_fit_width)

    p = sub.add_parser("stack")
    p.add_argument("--images", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--gap", type=int, default=24)
    p.set_defaults(fn=cmd_stack)

    p = sub.add_parser("list")
    p.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
