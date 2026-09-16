#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批三话量产驱动器（v2.8 流水线版）：
RAG 回忆杀 / Agent 审计员 / Token 失踪案 —— 复用 batch_parallel 的 gen_one 并行出格
+ draw_bubbles 引擎绘泡 + 夜话版拼装（1080px）。
分镜单一事实源：stories/trilogy-{a-rag,b-audit,c-token}/storyboard.md
用法: python gen_trilogy.py [a-rag|b-audit|c-token|all]
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
    "a-rag": ("RAG 回忆杀：", "AI 的笔记藏在哪", "小码 & 波普 · AI 科普"),
    "b-audit": ("Agent 审计员：", "谁动了我的上下文", "小码 & 波普 · AI 科普"),
    "c-token": ("Token 失踪案：", "你的钱包去哪了", "小码 & 波普 · AI 科普"),
}

SCENES = {
    "a-rag": [
        "场景：书房书桌前。{mk}趴在桌上翻一本厚书，越翻越快满脸焦急。{mp}漂浮在旁歪头看。",
        "场景：特写：一张白纸摊在桌上，纸上的笔迹正在快速变淡消失（回忆蒸发意象，不写任何文字）。{mk}双手按纸惊慌。",
        "场景：书架特写：每本书的书脊上都贴着发光的小标签书签（笔记卡片意象）。{mk}仰头惊讶，{mp}得意挥手。",
        "场景：书房。{mk}把一张便签纸递给{mp}，波普双手接过贴到自己胸口，胸口亮起一圈光。",
        "场景：特写：{mp}伸出天线，从书架方向拉出一条发光的细线连到自己头部，细线上串着几张小卡片在滑动。",
        "场景：书房。{mk}抱着手臂怀疑地看着{mp}，波普摊开双手，身旁漂浮几张翻开的卡片（自证清白意象）。",
        "场景：特写：两张并排的卡片，一张崭新发光，一张泛黄卷边（新旧资料对比意象）。{mk}与{mp}分立两旁注视。",
        "收尾格：书房全景。{mp}把最后一本书插回书架，拍拍手。{mk}靠在椅背上满意点头，竖起大拇指。",
    ],
    "b-audit": [
        "场景：书房。{mk}坐在电脑前挠头，屏幕发出困惑的蓝光。{mp}漂浮在旁举起一根手指似要发言。",
        "场景：特写：书桌上摊开一叠文件，每页内容各不相同且画满涂鸦线条（一团乱的任务清单意象）。{mk}扶额。",
        "场景：书房。三个迷你分身小机器人排成一排站在桌上，各自抱着一叠小文件。{mk}数手指清点。{mp}在旁指挥。",
        "场景：特写：两台迷你机器人隔着一堵小墙背对背工作，各自头顶冒出不同的想法气泡形状（空白无文字）。{mk}好奇围观。",
        "场景：书房。{mp}站在小讲台前，对三台迷你机器人比划分工手势，手里挥着一根指挥棒（发光细线）。{mk}在旁鼓掌。",
        "场景：特写：一台迷你机器人把一张完成的小卡片举过头顶，卡片上画着一个大大的对勾图案。{mk}惊喜。",
        "场景：书房全景。工作台整洁，文件按颜色分类码放整齐，三台迷你机器人排排坐休息。{mk}与{mp}满意环视。",
        "收尾格：{mk}与{mp}并肩站立，{mp}敬礼，{mk}竖大拇指。背后墙上挂着一幅分工流程图（只有图形和箭头，无文字）。",
    ],
    "c-token": [
        "场景：书房。{mk}拿着一张账单纸，瞪大眼睛张嘴惊呼。{mp}漂浮在旁歪头。",
        "场景：特写：一张大纸被裁刀切成整齐的小方块，方块排成长长一队。{mk}数方块数到手忙脚乱。",
        "场景：对比画面：左边一小队方块、右边一大队长队（中英等意句对比意象），中间立一个小天平。{mk}与{mp}分立两旁。",
        "场景：特写：两条传送带，一条向机器内输送方块（输入），另一条从机器输出更少但更大的方块（输出），输出端标价牌更高（只画符号不写字）。{mk}托腮。",
        "场景：书房。{mk}与{mp}对话多轮，两人之间的对话记忆画成越叠越高的方块塔。{mk}仰头看塔尖吃惊。",
        "场景：特写：{mp}把方块塔压缩整理，抽出一卷压紧的卷轴，塔变矮了一半。{mk}眼睛发亮。",
        "场景：书房。{mk}把一张写满涂鸦的长纸递给{mp}，波普摇手指，另一只手指向抽屉里分类整齐的卡片盒（该给机器人的才给意象）。",
        "收尾格：{mk}合上一本账本，露出轻松笑容；{mp}头顶天线闪着一个发光的小方块。两人击掌。",
    ],
}


def build_prompt(scene):
    return f"以参考图中的两个手绘漫画角色为主角，创作横向3:2构图的漫画单格。{scene}{BAN}{DNA}"


def generate(topic):
    out = HERE / "stories" / f"trilogy-{topic}"
    panels = out / "panels"
    panels.mkdir(parents=True, exist_ok=True)
    ref_url = local_ref_to_url(REF_LOCAL)
    jobs = []
    for i, tpl in enumerate(SCENES[topic], 1):
        scene = tpl.format(mk=MK, mp=MP)
        key = f"v8-{i:02d}"
        if (panels / f"{key}.raw.jpg").exists() and (panels / f"{key}.jpg").exists():
            continue  # 幂等续跑
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
    out = HERE / "stories" / f"trilogy-{topic}"
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
    base = HERE / "stories" / f"trilogy-{topic}"
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
    name = f"trilogy-{topic}.png"
    canvas.save(base / name, optimize=True)
    canvas.save(base / f"trilogy-{topic}-share.jpg", quality=90)
    img = Image.open(base / name)
    import numpy as np
    a = np.asarray(img.convert("L"))
    seg = img.size[1] // 12
    blanks = [i + 1 for i in range(12) if a[i * seg:(i + 1) * seg].std() < 8]
    assert img.size[0] == 1080 and not blanks, (img.size, blanks)
    print(f"[{topic}] long-manga {img.size} verified")


def run(topic):
    fails = generate(topic)
    if fails:
        return f"{topic}: generation failed {fails}"
    engine = load_engine()
    draw_bubbles(topic, engine)
    stack(topic)
    return f"{topic}: done"


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    topics = list(SCENES) if which == "all" else [which]
    for t in topics:
        print(run(t))
