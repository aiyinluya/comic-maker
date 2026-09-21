#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rebuild19_20.py — 用 cleaned raw（已去水印）重建两话成品链。

工作19（image-to-code, 8格）：cleaned/v8-XX.raw.jpg → fit 900px → draw_bubbles(manshi) → stack → lint → publish
工作20（story-20-zcode, 11格）：cleaned/v8-XX.raw.jpg → fit 900px → draw_bubbles(manshi) → stack → lint → publish

fit 与 gen_panel 完全同规格（>900 才缩放，LANCZOS，q92）。
"""
import importlib.util
import subprocess
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "scripts"))
from PIL import Image  # noqa: E402

WORKS = [
    ("stories/image-to-code", "19-image-to-code",
     ("豆包 2.1 Pro：", "0915 新版强在哪？", "小码 & 波普 · AI 科普"), 8),
    ("stories/story-20-zcode", "20-zcode-incident",
     ("加密包裹：", "从曝光到开源的三天", "小码 & 波普 · AI 科普"), 11),
]


def load_engine():
    engine_path = HERE / "scripts" / "draw_bubbles.py"
    esrc = engine_path.read_text(encoding="utf-8").replace(
        'if __name__ == "__main__":\n    main_cli()', "")
    engine = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location("engine", engine_path))
    exec(compile(esrc, str(engine_path), "exec"), engine.__dict__)
    return engine


def refit_from_cleaned(base):
    """cleaned/v8-XX.raw.jpg → v8-XX.final.jpg（900px fit，规格同 gen_panel）。"""
    panels = base / "panels"
    cleaned = panels / "cleaned"
    for f in sorted(cleaned.glob("v8-*.raw.jpg")):
        key = f.name.replace(".raw.jpg", "")
        img = Image.open(f)
        w, h = img.size
        if w > 900:
            img = img.resize((900, round(h * 900 / w)), Image.LANCZOS)
        img.convert("RGB").save(panels / f"{key}.final.jpg", quality=92)
    n = len(list(cleaned.glob("v8-*.raw.jpg")))
    print(f"  refit {n} finals <- cleaned")


def draw_bubbles(base):
    panels = base / "panels"
    cfg_path = base / "bubbles.json"
    r = subprocess.run([sys.executable, str(HERE / "scripts/parse_storyboard.py"),
                        "--storyboard", str(base / "storyboard.md"),
                        "--out", str(cfg_path)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"parse failed: {r.stderr[-200:]}")
    return cfg_path


def stack(base, title, n_panels):
    from PIL import ImageDraw, ImageFont
    import numpy as np
    panels = base / "panels"
    W, GAP, HEAD_H, FOOT_H = 1080, 28, 380, 150
    PAPER, INK, MUTE = (250, 250, 247), (26, 26, 26), (107, 103, 96)
    ACCENT, BLUE, ORANGE = (184, 85, 58), (58, 110, 165), (224, 122, 40)

    def load_font(size, bold=True):
        for p in ([r"C:\Windows\Fonts\msyhbd.ttc"] if bold else []) + [
                r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\Dengb.ttf"]:
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
        raise SystemExit("no font")

    imgs = []
    for i in range(1, n_panels + 1):
        im = Image.open(panels / f"v8-{i:02d}.final.jpg").convert("RGB")
        imgs.append(im.resize((W, round(im.height * W / im.width)), Image.LANCZOS))
    total_h = HEAD_H + sum(im.height for im in imgs) + GAP * (len(imgs) - 1) + FOOT_H
    canvas = Image.new("RGB", (W, total_h), PAPER)
    d = ImageDraw.Draw(canvas)
    d.rectangle([72, 84, 128, 92], fill=ACCENT)
    d.text((72, 106), title[0], font=load_font(74), fill=INK)
    d.text((72, 196), title[1], font=load_font(74), fill=INK)
    d.ellipse([72, 316, 88, 332], fill=BLUE)
    d.ellipse([98, 316, 114, 332], fill=ORANGE)
    d.ellipse([124, 316, 140, 332], fill=ACCENT)
    d.text((156, 312), title[2], font=load_font(26, bold=False), fill=MUTE)
    y = HEAD_H
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height + GAP
    fy = total_h - FOOT_H
    d.rectangle([72, fy + 34, W - 72, fy + 38], fill=(231, 229, 224))
    d.text((72, fy + 56), "出自公众号：码事漫谈", font=load_font(34), fill=INK)
    stem = base.name
    canvas.save(base / f"{stem}.png", optimize=True)
    canvas.save(base / f"{stem}-share.jpg", quality=90)
    a = np.asarray(Image.open(base / f"{stem}.png").convert("L"))
    seg = canvas.size[1] // 12
    blanks = [i + 1 for i in range(12) if a[i * seg:(i + 1) * seg].std() < 8]
    assert canvas.size[0] == 1080 and not blanks, (canvas.size, blanks)
    print(f"  stack {canvas.size} verified")


def lint(base):
    r = subprocess.run([sys.executable, str(HERE / "scripts/lint.py"),
                        "--dir", str(base / "panels"),
                        "--bubbles", str(base / "bubbles.json")],
                       capture_output=True, text=True, encoding="utf-8")
    last = (r.stdout or r.stderr).strip().splitlines()[-1]
    print(f"  lint rc={r.returncode}: {last}")
    return r.returncode == 0


def publish(base, out_id, n_panels):
    lf = HERE / "output/long-form" / out_id
    pl = HERE / "output/panels" / out_id
    lf.mkdir(parents=True, exist_ok=True)
    pl.mkdir(parents=True, exist_ok=True)
    stem = base.name
    shutil.copy(base / f"{stem}.png", lf / f"{out_id}.png")
    shutil.copy(base / f"{stem}-share.jpg", lf / f"{out_id}-share.jpg")
    for i in range(1, n_panels + 1):
        shutil.copy(base / "panels" / f"v8-{i:02d}.final.jpg", pl / f"{i:02d}.jpg")
    print(f"  published -> {out_id} (long-form + panels)")


def main():
    engine = load_engine()
    for rel, out_id, title, n in WORKS:
        base = HERE / rel
        print(f"[{out_id}]")
        refit_from_cleaned(base)
        cfg = draw_bubbles(base)
        engine.HERE = base / "panels"
        engine.draw_from_storyboard(str(cfg), str(base / "panels"),
                                    str(HERE / "styles/manshi.yaml"))
        stack(base, title, n)
        if not lint(base):
            print(f"[{out_id}] LINT FAILED")
            sys.exit(1)
        publish(base, out_id, n)
    print("ALL DONE")


if __name__ == "__main__":
    main()
