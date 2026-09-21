#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第20话《加密包裹：从曝光到开源的三天》量产驱动器（11格）。
复用 gen_trilogy2 流水线：并行出格 → 绘泡 → 拼装 → lint → 双轨落盘。
用法: python gen_work20.py [gen|finish|all]
"""
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "scripts"))
from gen_panel import gen_one, local_ref_to_url  # noqa: E402

REF_LOCAL = HERE / "assets/characters/xiaoke-ref-manga.jpg"
DNA = ("日式手绘漫画风格，铅笔质感的利落手绘线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，"
       "米白纸感背景，画面干净无水印")
BAN = ("重要：画面中绝对不出现任何对话气泡，不出现任何文字、字母、数字、符号；"
       "构图上部留出较多空白。")
MK = "左侧男生小码（严格保持参考图造型：黑色短发、脸上必须戴圆框眼镜、深灰色连帽衫、蓝色牛仔裤）"
MP = "右侧白色胶囊机器人波普（严格保持参考图造型：白色胶囊形身体、黑色面罩上有两只蓝色发光圆眼、头顶细天线顶端蓝色圆点、胸口橙色圆形徽章）"

STORY = "story-20-zcode"
OUT_ID = "20-zcode-incident"
TITLE = ("加密包裹：", "从曝光到开源的三天", "小码 & 波普 · AI 科普")
N_PANELS = 11

SCENES = [
    "场景：书房。{mk}举着手机满脸惊呼，手机屏幕发光。{mp}从旁边漂浮过来，看向手机。",
    "场景：特写：桌角放着一个挂着挂锁图案的发光包裹，旁边散落着几个文件袋。{mk}与{mp}俯身查看。",
    "场景：特写：包裹展开成一幅层叠的树状分支图案，像一棵发光的家谱树。{mp}指着树杈讲解，{mk}凑近细看。",
    "场景：特写：一条发光的传输线从一台笔记本电脑通向天空中的云朵，云朵上挂着一把巨大的锁。{mk}仰头望。",
    "场景：特写：一个被撕碎又重新拼好的包裹，旁边一个不停转动的机械计数转轮。{mk}震惊摊手，{mp}耸肩。",
    "场景：特写：一块开关面板的拨杆被拨向关闭位置，面板背后却伸出几条还在爬动的小细线。{mk}瞪大眼睛指给{mp}看。",
    "场景：书房。{mp}双手举着一张巨大的报纸，版面只有抽象色块图形。{mk}凑近查看。",
    "场景：特写：三样东西并排摆在桌上——一个系丝带的礼盒、一把大放大镜、一枚闪亮的硬币。{mk}与{mp}从两侧探头看。",
    "场景：特写：一封厚厚的信函立在桌上，封口盖着红色抽象印章图案，旁边立着一个小沙漏。{mk}表情严肃。",
    "场景：特写：一只打开的礼盒里升起一棵发光的分支树图案，光芒四射。{mk}与{mp}仰头惊喜观看。",
    "收尾格：{mp}把一枚发光的分支树贴纸轻轻按在笔记本电脑外壳上，{mk}在旁竖起大拇指，两人相视一笑。",
]


def build_prompt(scene):
    return f"以参考图中的两个手绘漫画角色为主角，创作横向3:2构图的漫画单格。{scene}{BAN}{DNA}"


def panels_dir():
    return HERE / "stories" / STORY / "panels"


def generate():
    panels = panels_dir()
    panels.mkdir(parents=True, exist_ok=True)
    ref_url = local_ref_to_url(REF_LOCAL)
    jobs = []
    for i, tpl in enumerate(SCENES, 1):
        scene = tpl.format(mk=MK, mp=MP)
        key = f"v8-{i:02d}"
        if (panels / f"{key}.raw.jpg").exists() and (panels / f"{key}.jpg").exists():
            continue
        jobs.append((key, build_prompt(scene), ref_url,
                     str(panels / f"{key}.raw.jpg"), str(panels / f"{key}.jpg"), 3))
    if not jobs:
        print(f"[{STORY}] panels already complete")
        return 0
    fails = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(gen_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            key, ok, msg = fut.result()
            print(f"[{STORY}] {'OK ' if ok else 'FAIL'} {key} {msg[:80]}", flush=True)
            if not ok:
                fails.append(key)
    return fails


def load_engine():
    engine_path = HERE / "scripts" / "draw_bubbles.py"
    esrc = engine_path.read_text(encoding="utf-8").replace(
        'if __name__ == "__main__":\n    main_cli()', "")
    engine = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location("engine", engine_path))
    exec(compile(esrc, str(engine_path), "exec"), engine.__dict__)
    return engine


def draw_bubbles(engine):
    base = HERE / "stories" / STORY
    panels = base / "panels"
    cfg_path = base / "bubbles.json"
    if not cfg_path.exists():
        r = subprocess.run([sys.executable, str(HERE / "scripts/parse_storyboard.py"),
                            "--storyboard", str(base / "storyboard.md"),
                            "--out", str(cfg_path)],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"parse failed: {r.stderr[-200:]}")
    engine.HERE = panels
    engine.draw_from_storyboard(str(cfg_path), str(panels),
                                str(HERE / "styles/manshi.yaml"))


def stack():
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    base = HERE / "stories" / STORY
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
    for n in [f"{i:02d}" for i in range(1, N_PANELS + 1)]:
        im = Image.open(panels / f"v8-{n}.final.jpg").convert("RGB")
        imgs.append(im.resize((W, round(im.height * W / im.width)), Image.LANCZOS))
    total_h = HEAD_H + sum(im.height for im in imgs) + GAP * (len(imgs) - 1) + FOOT_H
    canvas = Image.new("RGB", (W, total_h), PAPER)
    d = ImageDraw.Draw(canvas)
    d.rectangle([72, 84, 128, 92], fill=ACCENT)
    d.text((72, 106), TITLE[0], font=load_font(74), fill=INK)
    d.text((72, 196), TITLE[1], font=load_font(74), fill=INK)
    d.ellipse([72, 316, 88, 332], fill=BLUE)
    d.ellipse([98, 316, 114, 332], fill=ORANGE)
    d.ellipse([124, 316, 140, 332], fill=ACCENT)
    d.text((156, 312), TITLE[2], font=load_font(26, bold=False), fill=MUTE)
    y = HEAD_H
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height + GAP
    fy = total_h - FOOT_H
    d.rectangle([72, fy + 34, W - 72, fy + 38], fill=(231, 229, 224))
    d.text((72, fy + 56), "出自公众号：码事漫谈", font=load_font(34), fill=INK)
    canvas.save(base / f"{STORY}.png", optimize=True)
    canvas.save(base / f"{STORY}-share.jpg", quality=90)
    img = Image.open(base / f"{STORY}.png")
    a = np.asarray(img.convert("L"))
    seg = img.size[1] // 12
    blanks = [i + 1 for i in range(12) if a[i * seg:(i + 1) * seg].std() < 8]
    assert img.size[0] == 1080 and not blanks, (img.size, blanks)
    print(f"[{STORY}] long-manga {img.size} verified")


def lint():
    base = HERE / "stories" / STORY
    r = subprocess.run([sys.executable, str(HERE / "scripts/lint.py"),
                        "--dir", str(base / "panels"),
                        "--bubbles", str(base / "bubbles.json")],
                       capture_output=True, text=True, encoding="utf-8")
    print(f"[{STORY}] lint rc={r.returncode}: {(r.stdout or r.stderr).strip().splitlines()[-1]}")
    return r.returncode == 0


def publish():
    src = HERE / "stories" / STORY
    lf = HERE / "output/long-form" / OUT_ID
    pl = HERE / "output/panels" / OUT_ID
    lf.mkdir(parents=True, exist_ok=True)
    pl.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(src / f"{STORY}.png", lf / f"{OUT_ID}.png")
    shutil.copy(src / f"{STORY}-share.jpg", lf / f"{OUT_ID}-share.jpg")
    n = 0
    for f in sorted((src / "panels").glob("v8-*.final.jpg")):
        shutil.copy(f, pl / (f.name.replace("v8-", "").replace(".final.jpg", "") + ".jpg"))
        n += 1
    print(f"[{STORY}] published -> {lf.name} + panels({n})")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("gen", "all"):
        fails = generate()
        if fails:
            print(f"GENERATION FAILED: {fails}")
            sys.exit(1)
    if which in ("finish", "all"):
        engine = load_engine()
        draw_bubbles(engine)
        stack()
        if not lint():
            print("LINT FAILED")
            sys.exit(1)
        publish()
    if which == "publish":
        publish()
    print(f"[{STORY}] {which} done")
