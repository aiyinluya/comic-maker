#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 19 话量产驱动器（v2.8 流水线版）：《豆包 2.1 Pro：0915 新版强在哪？》
v2：主角是 0915 版本本身的优点（Agent 交付 / 多模态编程 / 多模态理解 / Token 效率）。
复用 gen_panel 的 gen_one 并行出格 + draw_bubbles 引擎绘泡 + 1080px 拼装 + 双轨落盘。
分镜单一事实源：stories/image-to-code/storyboard.md
用法: python gen_episode19.py [gen|draw|stack|lint|publish|all]
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

TOPIC = "image-to-code"
OUT_ID = "19-image-to-code"
REF_LOCAL = HERE / "assets/characters/xiaoke-ref-manga.jpg"
DNA = ("日式手绘漫画风格，铅笔质感的利落手绘线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，"
       "米白纸感背景，画面干净无水印")
BAN = ("重要：画面中绝对不出现任何对话气泡，不出现任何文字、字母、数字、符号，时钟表盘只用刻度圆点；"
       "构图上部留出较多空白。")
MK = "左侧男生小码（严格保持参考图造型：黑色短发、脸上必须戴圆框眼镜、深灰色连帽衫、蓝色牛仔裤）"
MP = "右侧白色胶囊机器人波普（严格保持参考图造型：白色胶囊形身体、黑色面罩上有两只蓝色发光圆眼、头顶细天线顶端蓝色圆点、胸口橙色圆形徽章）"
MINI = ("一群比波普小很多的迷你胶囊机器人，造型和波普一致：白色小胶囊身体、黑色面罩蓝色圆眼、"
        "细天线、胸口橙色小圆徽章")

TITLE = ("豆包 2.1 Pro：", "0915 新版强在哪？", "小码 & 波普 · AI 科普")

SCENES = [
    # v8-01 重出（R18 表情）：四大件总览，小码期待脸
    "场景：书房，画面上方三分之一必须完全留白，两个角色都位于画面下半部。{mk}位于画面左下角、半身入镜，"
    "【表情：眉毛高高扬起、眼睛发亮睁大、嘴角微张，是满脸期待和好奇的神情】，"
    "举起一部手机，手机屏幕上只有一个系丝带的礼物盒图形；{mp}位于画面右下角，蓝色圆眼睛明亮、微微弯起显得胸有成竹，"
    "身侧悬浮着四个图形图标（扳手、眼睛、胶片条、硬币，全是纯图形），波普抬手指向这四个图标。",
    # v8-02 重出（R18 表情）：桌面草图，小码半信半疑
    "场景：桌面特写。白纸上是{mk}画的歪歪扭扭网页草图，只有方框、线条和圆形按钮，全是图形没有任何文字；"
    "{mp}俯身认真看图、眼神笃定；{mk}在旁【表情：歪着头、单手挠头、一边眉毛挑起、嘴角一撇，一脸半信半疑】。",
    # v8-03 保留：纸卷代码山 + 录屏（中景走路，惊讶担心脸合理）
    "场景：纹理纸卷堆成的一座大山，纸卷表面只有等高线纹理、没有任何字符，代表代码仓库，山前立着一台老式终端机柜；"
    "{mp}举着录屏手机沿山路往前走，{mk}紧跟在后。",
    # v8-04 重出（R18 表情）：四张设计稿 → 立体小院，小码惊喜赞叹
    "场景：特写。四张设计稿卡片排成弧形，箭头汇入一个立体小院模型，院里有小亭、水池、落叶，天空飘着雨丝；"
    "{mk}和{mp}仰头观看，小码【表情：惊喜地睁大眼睛、张开嘴露出赞叹的笑容、眉毛上扬】，波普蓝眼睛弯起、一脸自豪。",
    # v8-05 重出（R18 表情）：子 Agent 调研，小码怀疑脸
    "场景：画面上方三分之一留白，角色集中在下半部。{mp}站在画面右下方居中调度、蓝眼睛认真专注，周围环绕着{mini}，"
    "迷你机器人分别举着放大镜、文件夹、小卫星和小船图案，每个迷你机器人牵出一根细线，"
    "所有线汇到波普手中一张盖着对勾图标的证书上；{mk}在左下方【表情：眯起眼睛、单边眉毛高高挑起、嘴角下撇，一脸怀疑】。",
    # v8-06 保留：36 小时长任务（小码脸部被气泡区遮挡，中性等待即可）
    "场景：画面上方三分之一留白。一只巨大的圆形时钟占据画面下半部，表盘上只有刻度圆点、绝对没有数字和指针数字；"
    "{mp}带着{mini2}沿时钟外圈的刻度轨道接力奔跑，沿途一个个纸卷被修好并亮起对勾标记，"
    "大约五分之四的路段已经亮起灯，剩余路段还是灰的；{mk}抱着水杯站在左下角。",
    # v8-07 重出（R18 表情）：长视频 + 省钱，小码心疼试探、波普从容
    "场景：画面上方三分之一留白，两个角色都在下半部。左侧一卷超长电影胶片展开、弯弯曲曲拖得很长，{mp}在右侧俯身看胶片、"
    "蓝眼睛弯成月牙一脸从容；波普另一只手旁是一张账单纸条图形，纸条明显缩短了一截，旁边一枚硬币上画着向下箭头、表示退回省钱；"
    "{mk}站在左侧胶片旁【表情：皱着眉头、撇嘴、一只手摊开，是心疼钱又试探的神情】。",
    # v8-08 重出（R18 表情）：收尾，小码必须是赞许的笑
    "收尾格：半身构图。{mk}把一张手绘草图递给{mp}，草图一角发光浮现出一个小网页窗口图案；"
    "{mk}竖起大拇指，【表情：真心赞许的灿烂笑容、眼睛弯成两道月牙、嘴角大大上扬，绝不是皱眉或担忧】；"
    "{mp}胸口橙色徽章发亮、蓝色圆眼睛也弯成月牙像在开心地笑。",
]


def base_dir():
    return HERE / "stories" / TOPIC


def build_prompt(scene):
    return f"以参考图中的两个手绘漫画角色为主角，创作横向3:2构图的漫画单格。{scene}{BAN}{DNA}"


def generate():
    out = base_dir()
    panels = out / "panels"
    panels.mkdir(parents=True, exist_ok=True)
    ref_url = local_ref_to_url(REF_LOCAL)
    jobs = []
    for i, tpl in enumerate(SCENES, 1):
        scene = tpl.format(mk=MK, mp=MP, mini=MINI, mini2=MINI)
        key = f"v8-{i:02d}"
        if (panels / f"{key}.raw.jpg").exists() and (panels / f"{key}.jpg").exists():
            continue
        jobs.append((key, build_prompt(scene), ref_url,
                     str(panels / f"{key}.raw.jpg"), str(panels / f"{key}.jpg"), 3))
    if not jobs:
        print("[19] panels already complete")
        return []
    print(f"[19] generating {len(jobs)} panels ...")
    fails = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(gen_one, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            key, ok, msg = fut.result()
            print(f"[19] {'OK ' if ok else 'FAIL'} {key} {msg[:100]}")
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
    out = base_dir()
    panels = out / "panels"
    cfg_path = out / "bubbles.json"
    r = subprocess.run([sys.executable, str(HERE / "scripts/parse_storyboard.py"),
                        "--storyboard", str(out / "storyboard.md"),
                        "--out", str(cfg_path)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"parse failed: {r.stderr[-200:]}")
    engine.HERE = panels
    engine.draw_from_storyboard(str(cfg_path), str(panels),
                                str(HERE / "styles/manshi.yaml"))


def stack():
    from PIL import Image, ImageDraw, ImageFont
    panels = base_dir() / "panels"
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
    base = base_dir()
    canvas.save(base / f"{TOPIC}.png", optimize=True)
    canvas.save(base / f"{TOPIC}-share.jpg", quality=90)
    img = Image.open(base / f"{TOPIC}.png")
    import numpy as np
    a = np.asarray(img.convert("L"))
    seg = img.size[1] // 12
    blanks = [i + 1 for i in range(12) if a[i * seg:(i + 1) * seg].std() < 8]
    assert img.size[0] == 1080 and not blanks, (img.size, blanks)
    print(f"[19] long-manga {img.size} verified")


def lint():
    out = base_dir()
    r = subprocess.run([sys.executable, str(HERE / "scripts/lint.py"),
                        "--dir", str(out / "panels"),
                        "--bubbles", str(out / "bubbles.json")],
                       capture_output=True, text=True, encoding="utf-8")
    print(f"[19] lint rc={r.returncode}: {(r.stdout or r.stderr).strip().splitlines()[-1]}")
    return r.returncode == 0


def publish():
    src = base_dir()
    lf = HERE / "output/long-form" / OUT_ID
    pl = HERE / "output/panels" / OUT_ID
    lf.mkdir(parents=True, exist_ok=True)
    pl.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(src / f"{TOPIC}.png", lf / f"{OUT_ID}.png")
    shutil.copy(src / f"{TOPIC}-share.jpg", lf / f"{OUT_ID}-share.jpg")
    for f in (src / "panels").glob("v8-*.final.jpg"):
        n = f.name.replace("v8-", "").replace(".final.jpg", "")
        shutil.copy(f, pl / f"{n}.jpg")
    print(f"[19] published -> {lf.name} + panels({OUT_ID})")


def run(step):
    if step in ("gen", "all"):
        fails = generate()
        if fails:
            sys.exit(f"[19] generation failed {fails}")
    if step in ("draw", "all"):
        draw_bubbles(load_engine())
    if step in ("stack", "all"):
        stack()
    if step in ("lint", "all"):
        if not lint():
            sys.exit("[19] lint FAILED")
    if step in ("publish", "all"):
        publish()
    print(f"[19] step '{step}' done")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "all")
