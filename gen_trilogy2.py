#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二批三话（16-18）量产驱动器：复用 gen_trilogy 的流水线组件。
R16 后 i2i 路径稳定，含单格成品双轨落盘（long-form + panels）。
用法: python gen_trilogy2.py [temperature|embedding|reasoning|all]
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

TITLES = {
    "temperature": ("AI 的骰子：", "为什么每次回答都不一样", "小码 & 波普 · AI 科普"),
    "embedding": ("意思的地图：", "AI 怎么听懂言外之意", "小码 & 波普 · AI 科普"),
    "reasoning": ("AI 打草稿：", "推理模型的思考过程", "小码 & 波普 · AI 科普"),
}
OUT_IDS = {"temperature": "16-temperature", "embedding": "17-embedding", "reasoning": "18-reasoning"}

SCENES = {
    "temperature": [
        "场景：书房。{mk}举着手机满脸疑惑，屏幕发出两种不同颜色的光。{mp}漂浮在旁摊手。",
        "场景：特写：一枚巨大的骰子悬在半空旋转，骰子各面画着不同的图形符号。{mp}指着骰子讲解。",
        "场景：特写：一枚骰子被封在透明冰块里冻住。{mk}对着冰块哈气搓手，{mp}在旁点头。",
        "场景：对比画面：左边机器吐出整齐划一的灰色方块，右边机器吐出五颜六色的雪花图案。{mk}站在中间观看。",
        "场景：书房。{mp}面前摆着一块带两个旋钮的面板，一个旋钮画尺子图案，另一个画羽毛图案。{mk}伸手选择。",
        "场景：特写：面板旋钮拧到最大，机器头顶冒烟，吐出一团乱糟糟的缠线。{mk}目瞪口呆。",
        "场景：书房。{mp}举起一根平衡秤，两端分别是尺子和羽毛。{mk}托腮思考。",
        "收尾格：{mp}把一枚发光的小骰子轻轻放到{mk}摊开的手心，两人相视一笑。",
    ],
    "embedding": [
        "场景：书房。{mk}竖起大拇指夸奖，{mp}得意地挺起圆肚子。桌上立着一本厚字典。",
        "场景：特写：一片星点组成的街区，几个星点聚成小群落，之间有淡淡的连线。{mp}指着星群讲解。",
        "场景：书架前。两颗小星点从两侧滑向同一个星群，星群微微发光。{mk}与{mp}仰头观看。",
        "场景：对比画面：两幅小场景分屏——一边画一个圆形果实图案的街区，一边画一台笔记本电脑图案的街区，同一颗星点分处两地。{mk}恍然大悟。",
        "场景：特写：一条由浅到深的色带，一颗星点落在中间偏左位置，色带两端各有一个表情圆脸（微笑/面无表情）。{mp}指着星点。",
        "场景：书房全景。{mp}手持画笔站在一幅巨大星图前，星图延展到画面外。{mk}震惊仰望。",
        "场景：特写：星图一角有几颗星点被一个虚线圈错误地框在一起，{mp}用橡皮轻轻擦那道框线。{mk}点头。",
        "收尾格：{mp}把一颗新星点轻轻放在星图上，星点亮起；{mk}竖大拇指。",
    ],
    "reasoning": [
        "场景：书房。{mk}指着手表一脸着急。{mp}闭眼冥想，头顶漂浮几颗小星点。",
        "场景：特写：一张大草稿纸铺开，上面画着分步骤的图形链条（圆圈连圆圈），末端是一个对勾。{mp}指着链条讲解。",
        "场景：对比画面：左边一台机器从嘴直接飞出一个闪光答案方块，右边一台机器铺开草稿纸写画。{mk}站中间两边看。",
        "场景：特写：草稿纸上有一条步骤链被大叉划掉，箭头绕回起点重新出发。{mk}凑近看，{mp}耸肩。",
        "场景：书房。一台迷你机器人被自己画的一团乱线缠住，草稿纸堆成山。{mk}扶额，{mp}举着一把剪刀。",
        "场景：书房。{mp}面前摆三张卡片（分别画算盘/拼图/日历图案），逐一点过。{mk}认真记。",
        "场景：特写：{mp}头顶天线挂着一张小账单图形（画着硬币符号），旁边草稿纸与硬币等重悬在天平上。{mk}捂住口袋。",
        "收尾格：{mp}把一张画满步骤链的草稿纸递给{mk}，{mk}接过竖大拇指，两人身后一台迷你机器安静工作。",
    ],
}


def build_prompt(scene):
    return f"以参考图中的两个手绘漫画角色为主角，创作横向3:2构图的漫画单格。{scene}{BAN}{DNA}"


def generate(topic):
    out = HERE / "stories" / f"trilogy-2-{topic}"
    panels = out / "panels"
    panels.mkdir(parents=True, exist_ok=True)
    ref_url = local_ref_to_url(REF_LOCAL)
    jobs = []
    for i, tpl in enumerate(SCENES[topic], 1):
        scene = tpl.format(mk=MK, mp=MP)
        key = f"v8-{i:02d}"
        if (panels / f"{key}.raw.jpg").exists() and (panels / f"{key}.jpg").exists():
            continue
        jobs.append((key, build_prompt(scene), ref_url,
                     str(panels / f"{key}.raw.jpg"), str(panels / f"{key}.jpg"), 3))
    if not jobs:
        print(f"[{topic}] panels already complete")
        return 0
    fails = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(gen_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            key, ok, msg = fut.result()
            print(f"[{topic}] {'OK ' if ok else 'FAIL'} {key} {msg[:80]}")
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


def draw_bubbles(topic, engine):
    out = HERE / "stories" / f"trilogy-2-{topic}"
    panels = out / "panels"
    cfg_path = out / "bubbles.json"
    if not cfg_path.exists():
        r = subprocess.run([sys.executable, str(HERE / "scripts/parse_storyboard.py"),
                            "--storyboard", str(out / "storyboard.md"),
                            "--out", str(cfg_path)],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"parse failed: {r.stderr[-200:]}")
    engine.HERE = panels
    engine.draw_from_storyboard(str(cfg_path), str(panels))


def stack(topic):
    from PIL import Image, ImageDraw, ImageFont
    base = HERE / "stories" / f"trilogy-2-{topic}"
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
    for n in ["01", "02", "03", "04", "05", "06", "07", "08"]:
        im = Image.open(panels / f"v8-{n}.final.jpg").convert("RGB")
        imgs.append(im.resize((W, round(im.height * W / im.width)), Image.LANCZOS))
    total_h = HEAD_H + sum(im.height for im in imgs) + GAP * (len(imgs) - 1) + FOOT_H
    canvas = Image.new("RGB", (W, total_h), PAPER)
    d = ImageDraw.Draw(canvas)
    t = TITLES[topic]
    d.rectangle([72, 84, 128, 92], fill=ACCENT)
    d.text((72, 106), t[0], font=load_font(74), fill=INK)
    d.text((72, 196), t[1], font=load_font(74), fill=INK)
    d.ellipse([72, 316, 88, 332], fill=BLUE)
    d.ellipse([98, 316, 114, 332], fill=ORANGE)
    d.ellipse([124, 316, 140, 332], fill=ACCENT)
    d.text((156, 312), t[2], font=load_font(26, bold=False), fill=MUTE)
    y = HEAD_H
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height + GAP
    fy = total_h - FOOT_H
    d.rectangle([72, fy + 34, W - 72, fy + 38], fill=(231, 229, 224))
    d.text((72, fy + 56), "出自公众号：码事漫谈", font=load_font(34), fill=INK)
    name = f"trilogy-2-{topic}.png"
    canvas.save(base / name, optimize=True)
    canvas.save(base / f"trilogy-2-{topic}-share.jpg", quality=90)
    img = Image.open(base / name)
    import numpy as np
    a = np.asarray(img.convert("L"))
    seg = img.size[1] // 12
    blanks = [i + 1 for i in range(12) if a[i * seg:(i + 1) * seg].std() < 8]
    assert img.size[0] == 1080 and not blanks, (img.size, blanks)
    print(f"[{topic}] long-manga {img.size} verified")


def publish(topic):
    """双轨落盘：long-form 长图 + panels 单格（上一话教训，验收单固定项）。"""
    out_id = OUT_IDS[topic]
    src = HERE / "stories" / f"trilogy-2-{topic}"
    lf = HERE / "output/long-form" / out_id
    pl = HERE / "output/panels" / out_id
    lf.mkdir(parents=True, exist_ok=True)
    pl.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(src / f"trilogy-2-{topic}.png", lf / f"{out_id}.png")
    shutil.copy(src / f"trilogy-2-{topic}-share.jpg", lf / f"{out_id}-share.jpg")
    for f in (src / "panels").glob("v8-*.final.jpg"):
        n = f.name.replace("v8-", "").replace(".final.jpg", "")
        shutil.copy(f, pl / f"{n}.jpg")
    print(f"[{topic}] published -> {lf.name} + panels({out_id})")


def lint(topic):
    out = HERE / "stories" / f"trilogy-2-{topic}"
    r = subprocess.run([sys.executable, str(HERE / "scripts/lint.py"),
                        "--dir", str(out / "panels"),
                        "--bubbles", str(out / "bubbles.json")],
                       capture_output=True, text=True, encoding="utf-8")
    print(f"[{topic}] lint rc={r.returncode}: {(r.stdout or r.stderr).strip().splitlines()[-1]}")
    return r.returncode == 0


def run(topic):
    fails = generate(topic)
    if fails:
        return f"{topic}: generation failed {fails}"
    engine = load_engine()
    draw_bubbles(topic, engine)
    stack(topic)
    if not lint(topic):
        return f"{topic}: lint FAILED"
    publish(topic)
    return f"{topic}: done (strip + panels + lint)"


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    topics = list(SCENES) if which == "all" else [which]
    for t in topics:
        print(run(t))
