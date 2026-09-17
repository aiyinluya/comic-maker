#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch_parallel.py — 六话题 48 格并行出图（3 路并发 × 逐格重试）。
复用 gen_panel v2 的 gen_one 原子函数。并行组=每话题内 8 格，话题间串行（限流友好）。
用法: python batch_parallel.py [--topics mcp,context,...] [--workers 3]
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gen_panel  # noqa: E402  # gen_one / local_ref_to_url

DNA = ("日式手绘漫画风格，铅笔质感的利落手绘线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，"
       "米白纸感背景，画面干净无水印")
BAN = ("重要：画面中绝对不出现任何对话气泡，不出现任何文字、字母、数字、符号；"
       "构图上部留出较多空白。")
MK = ("左侧男生小码（严格保持参考图造型：黑色短发、脸上必须戴圆框眼镜、"
      "深灰色连帽衫、蓝色牛仔裤）")
MP = ("右侧白色胶囊机器人波普（严格保持参考图造型：白色胶囊形身体、黑色面罩上有两只蓝色发光圆眼、"
      "头顶细天线顶端蓝色圆点、胸口橙色圆形徽章）")

# 话题级画面定义（与 gen_topic.py 同源；此处为并行版汇总）
SCENES = {
    "mcp": [
        "场景：书房书桌前。{mk}好奇发问。{mp}手里举着一根两头发光的粗连接线。",
        "场景：书房。AI拟物机器背后拖着七八根颜色各异的乱线缠成一团，{mk}指着乱线皱眉。{mp}在旁解释。",
        "场景：特写标准插线板，插着三种不同形状的插头（键盘/方块/日历形状）。{mk}与{mp}在旁观看。",
        "场景：特写。{mp}举着一根USB-C连接线，旁边漂浮几种老式接口的轮廓对比。{mk}恍然大悟。",
        "场景：书房。{mp}身后一排工具图标（信封、日历、齿轮、地图钉）依次发光亮起。{mk}惊讶看着。",
        "场景：书房全景。各式形状不同的机器人角色围拢在{mp}身旁伸手。{mk}在旁观看。",
        "场景：房间全景。AI拟物机器与家具之间只剩一根干净发光线缆。{mk}与{mp}在旁欣赏。",
        "收尾格：{mp}把转接头轻轻插上，四周工具图标全部亮起。{mk}竖起大拇指。",
    ],
    "context": [
        "场景：书房。{mk}发问。{mp}指着自己的头部，头顶画一个半满的容器图案。",
        "场景：书房特写。一架大天平：一侧文件堆积如山，另一侧空空如也。{mk}与{mp}分立两旁。",
        "过场条格（超宽横向21:9）：图书馆书架前，{mp}只抽出一本发光的书，其余书灰暗。{mk}仰头观看。",
        "场景：书房。{mp}把一摞厚文件压成一张小卡片。{mk}惊讶看着。",
        "场景：书房全景。三个独立小隔间，各坐一个迷你机器人。{mk}与{mp}在隔间外观看。",
        "场景：书房。{mp}把一张卡片放进带抽屉的柜子。{mk}在旁点头。",
        "场景：书房。{mp}连续演示三个动作的连环剪影。{mk}认真看。",
        "收尾格：{mk}把一份整理好的文件递给{mp}，波普双眼发光亮起。",
    ],
    "mas": [
        "场景：书桌前。文件堆积成山，一个迷你小机器人被埋住半截。{mk}惊讶。{mp}在旁摊手。",
        "场景：全景。四个工位各坐一个迷你机器人（放大镜/笔/齿轮/对勾图案）。{mk}与{mp}介绍。",
        "过场条格（超宽横向21:9）：俯瞰四工位传送带连接，卡片传递。全景构图。",
        "场景：三扇独立的门（放大镜/笔/对勾图案）。{mk}打开一扇张望。{mp}在旁讲解。",
        "场景：传送带上标准卡片在工位间传递，机器人们专注工作。{mk}观看点头。",
        "场景：审查工位机器人盖红色不合格章，卡片被送回。{mk}与{mp}在旁观察。",
        "场景：{mk}面前摊开分阶段流程图（节点与箭头）。{mp}指着讲解。",
        "收尾格：{mp}举一枚天平：一端一个迷你机器人，另一端四个。{mk}竖大拇指。",
    ],
    "token": [
        "场景：特写：一张写着笔画图案的纸条被裁刀切成整齐小方块。{mk}凑近看。{mp}拿着裁刀。",
        "场景：对比图：中文纸条切出更多块，英文纸条切出较少块（只画图案线条）。{mk}与{mp}分立两旁。",
        "过场条格（超宽横向21:9）：传送带上方块流进机器，另一端流出长账单卷轴（只画线条）。",
        "场景：大天平：一侧大量方块（输入），另一侧较少但更重的方块（输出）。{mk}惊讶。{mp}解释。",
        "场景：一个雪球越滚越大，裹着层层旧方块。{mk}目瞪口呆。{mp}指着雪球。",
        "场景：特写大玻璃容器装满方块，顶部警戒线闪烁。{mk}与{mp}仰头看。",
        "场景：{mp}展示三张卡片（裁刀/压缩泵/隔板图案）。{mk}接过卡片。",
        "收尾格：{mk}把一大摞方块精简成一小叠，旁边账单卷轴变短。{mp}竖大拇指。",
    ],
    "finetune": [
        "场景：书房。{mk}发问。{mp}左右手各举：一张说明书、一顶学士帽。",
        "场景：书房。{mk}递出一张画满线条图案的说明书，AI拟物机器看完立即工作。{mp}点头。",
        "场景：训练教室，AI拟物机器坐课桌前，墙上挂满课程图表。{mk}与{mp}在后门张望。",
        "场景：三扇门并排（方块堆/闪电/时钟图案）。{mp}依次指着。{mk}看着。",
        "场景：两条进料管道：一条流出干净方块，一条流出混杂垃圾。{mk}捏鼻。{mp}摇头。",
        "场景：三级台阶图（说明书/资料库/教室图案），从低到高。{mk}登第一级。{mp}指引。",
        "场景：AI拟物机器身穿定制制服，手拿当天任务卡。{mk}与{mp}赞许。",
        "收尾格：{mp}把一枚巨大的锤子轻轻放回武器架。{mk}竖大拇指。",
    ],
    "hands": [
        "场景：分屏：左半噪点雪花，右半雪花中浮现一只写实的猫。{mk}惊讶指着。{mp}解释。",
        "场景：三联过程图横排：雪花屏、模糊猫轮廓、清晰的猫（箭头连接）。{mk}与{mp}在下方观看。",
        "过场条格（超宽横向21:9）：去噪波纹扫过画布，噪点变清晰图案。全景构图。",
        "场景：一只手的三种姿态简笔画并排，指节数量有细微差异。{mk}拿放大镜细看。{mp}扶额。",
        "场景：五只一模一样的猫排排站。{mk}数得眼花头顶螺旋线。{mp}耸肩。",
        "场景：特写一张纸写满似字非字的伪汉字图案。{mk}看得头疼。{mp}解释。",
        "场景：{mp}用尺子和圆规在纸上画精确的方格。{mk}在旁看着。",
        "收尾格：{mp}一手握画笔一手举放大镜，拼合成对勾。{mk}竖大拇指。",
    ],
}
STRIP = {"context": "07", "mas": "03", "token": "03", "hands": "03"}  # 过场条格所在格序号


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics", default="mcp,context,mas,token,finetune,hands")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--ref", default="https://autoglm-agent.aminer.cn/auto_fly/"
                                      "7742f6da-cf32-489f-a000-7a425d54d667/ref-manga.jpg")
    ap.add_argument("--out-root", default="posts/six-topics")
    a = ap.parse_args()

    total_jobs = []
    for topic in a.topics.split(","):
        base = Path(a.out_root) / topic
        base.mkdir(parents=True, exist_ok=True)
        for i, scene_tpl in enumerate(SCENES[topic], 1):
            scene = scene_tpl.format(mk=MK, mp=MP)
            prompt = f"以参考图中的两个手绘漫画角色为主角，创作横向3:2构图的漫画单格。{scene}{BAN}{DNA}"
            out_raw = base / f"v8-{i:02d}.raw.jpg"
            out_fit = base / f"v8-{i:02d}.jpg"
            # 已存在则跳过（幂等，支持断点续跑）
            if out_raw.exists() and out_fit.exists():
                continue
            total_jobs.append((f"{topic}-{i:02d}", prompt, a.ref,
                               str(out_raw), str(out_fit), a.retries))

    print(f"jobs to run: {len(total_jobs)} (workers={a.workers})")
    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futures = {ex.submit(gen_panel.gen_one, j): j[0] for j in total_jobs}
        for fut in as_completed(futures):
            key = futures[fut]
            idx, ok, msg = fut.result()
            results.append({"job": key, "ok": ok, "msg": msg[:200]})
            print(("OK " if ok else "FAIL"), key, msg[:120])

    report_path = Path(a.out_root) / "parallel_report.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    fails = [r for r in results if not r["ok"]]
    print(f"done: {len(results) - len(fails)}/{len(results)} | report: {report_path}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
