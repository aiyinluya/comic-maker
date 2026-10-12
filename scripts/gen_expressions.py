#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_expressions.py — 角色表情库批量生产（gen_panel.py 链路复用）。

表情库理念：
  每个角色 × N 个基准表情，各存一张独立 JPG（身份已内嵌，单格生图时
  --ref-local 直指表情图即可，无需传两张参考）。
  提示词用「规范短语」（CANON），全流水线统一措辞，杜绝整话「惊讶看着」。

用法:
  python scripts/gen_expressions.py --char xiaoke --only neutral,surprised
  python scripts/gen_expressions.py --char popu                    # 全 8 表情
  python scripts/gen_expressions.py --char xiaoke --ref <定妆照路径>

产出:
  assets/characters/<char>/expressions/<expr>.raw.jpg   生成原图
  assets/characters/<char>/expressions/<expr>.jpg       900px 收幅成品
  assets/characters/<char>/expressions/meta.json        短语表 + 生成记录
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from gen_panel import gen_one, local_ref_to_url  # 复用同一条生图链路（seedream → 下载 → 收幅）

# ── 表情规范短语表（CANON）────────────────────────────────
# phrase: 注入生图提示词的标准描述（全流水线唯一口径）
# sanity: 质检时判断「画的是不是这个表情」的判据
EXPRESSIONS = {
    "neutral": {
        "phrase": "表情平静放松，嘴唇轻闭成平缓弧线，眼神平视，眉毛自然舒展",
        "sanity": "面部放松，嘴闭合，眉毛平，无夸张眉眼动作",
    },
    "surprised": {
        "phrase": "双眼瞪到最大，瞳孔缩成小点，眉毛高高挑起，嘴巴张成小圆形，一脸错愕",
        "sanity": "瞳孔缩小+眼白露出+眉毛高挑+圆形小嘴，四项至少三项",
    },
    "frown": {
        "phrase": "眉头拧成川字紧锁，眉毛斜压向眼，嘴角用力向下撇，眼睛微眯，满脸不满",
        "sanity": "川字眉或八字压眉+嘴角明显下撇，无笑容",
    },
    "smile": {
        "phrase": "嘴角大幅上扬的温和微笑，嘴唇闭合不张口，眼睛弯成月牙但保持睁开，神态友善愉悦",
        "sanity": "嘴角大幅上扬+眼睛弯起（弯月眼或笑纹）",
    },
    "laugh": {
        "phrase": "仰头开怀大笑，嘴巴大张露出上排牙齿，眼睛完全眯成两条缝，脸颊鼓起",
        "sanity": "眼眯成缝+嘴大张露齿，整体仰头开怀",
    },
    "think": {
        "phrase": "单手托腮，眉头轻皱，眼睛斜向上望，嘴巴抿成一条略歪的线，陷入沉思",
        "sanity": "托腮手+眼神斜向上+抿嘴",
    },
    "shock": {
        "phrase": "极度震惊：双眼圆凸瞪出，瞳孔震成小点，嘴巴张大成夸张的 O 形，脸颊下拉",
        "sanity": "夸张 O 形大嘴+圆凸瞪眼（比 surprised 更极端）",
    },
    "speechless": {
        "phrase": "无语：上眼睑下垂遮住半个瞳孔，嘴角平直略向下，眉毛放平，一脸无奈死鱼眼",
        "sanity": "半遮瞳的死鱼眼+嘴角平直",
    },
    "confused": {
        "phrase": "歪头，一边眉毛高高挑起一边眉毛压低，眼睛一大一小，嘴角下撇歪斜，满脸问号式困惑",
        "sanity": "头部倾斜+两眉不对称+嘴角歪斜",
    },
    "smug": {
        "phrase": "得意：下巴微抬，眼睛半眯上挑，嘴角咧开一边上扬的坏笑，一脸自信",
        "sanity": "半眯上挑眼+单侧上扬咧嘴坏笑",
    },
    "sad": {
        "phrase": "失落：眉毛内端上挑成八字泪眉，眼睛下垂湿润无神，嘴角明显向下瘪，肩膀低垂",
        "sanity": "八字泪眉+眼下垂+嘴角下瘪",
    },
    "worried": {
        "phrase": "担忧：眉头紧皱上挑，眼睛圆睁略颤，嘴角向下微张，额角一滴汗珠",
        "sanity": "皱眉上挑+眼圆睁+额角汗珠",
    },
    "angry": {
        "phrase": "愤怒：眉毛狠狠压成倒八字，眼睛瞪小怒视，咬牙切齿嘴紧抿，额头青筋或井字纹",
        "sanity": "倒八字压眉+咬牙怒视+井字纹任二",
    },
    "excited": {
        "phrase": "兴奋：双眼放光圆睁，瞳孔闪亮，嘴巴咧到最大露齿欢呼，脸颊泛红",
        "sanity": "双眼放光+露齿咧嘴欢呼+腮红",
    },
    "tired": {
        "phrase": "疲惫：上眼睑重重垂下遮眼过半，眼下有黑眼圈袋，嘴巴微张打哈欠，头略前倾",
        "sanity": "眼睑重垂+黑眼圈+哈欠",
    },
    "focus": {
        "phrase": "专注：眉头微聚，双眼锐利直视前方，瞳孔聚焦，嘴巴紧抿成直线",
        "sanity": "锐利直视+眉微聚+嘴紧抿",
    },
}

# 各角色定妆照（缺省时用 --ref 指定）
DEFAULT_REFS = {
    "xiaoke": REPO / "assets" / "characters" / "xiaoke-ref-manga.jpg",
    "popu": REPO / "assets" / "characters" / "popu-ref-manga.jpg",
}

# 身份判据（与 vlm_qc.py DEFAULT_CHAR_SPEC 同口径）
IDENTITY = {
    "xiaoke": "黑色短发 + 圆框眼镜 + 深灰色连帽衫",
    "popu": "白色胶囊机器人 + 蓝色发光眼睛 + 橙色胸徽",
}


def build_prompt(char: str, expr: str, ref_hint: str) -> str:
    e = EXPRESSIONS[expr]
    return (
        f"以参考图中的角色为主角，绘制同一角色的头部大特写："
        f"正面微侧 3/4 视角，头部占据画面主体（头部+少量肩部），"
        f"纯色浅米白背景，正面柔光，漫画线稿风格，均匀描边，上色简洁。"
        f"严格保持参考图造型：{ref_hint}。"
        f"角色表情（漫画式夸张，特征必须明显）：{e['phrase']}。"
        f"画面只有这一个角色，不写任何文字。"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True, choices=sorted(set(DEFAULT_REFS) | {"custom"}))
    ap.add_argument("--only", default="", help="逗号分隔，如 neutral,surprised；缺省全部 8 个")
    ap.add_argument("--ref", default="", help="自定义定妆照路径（缺省用内置映射）")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--pause", type=float, default=2.0, help="每张间隔秒")
    ap.add_argument("--refit", action="store_true", help="不生图：从现有 raw 重出 900px 成品（清水印后用）")
    args = ap.parse_args()

    outdir = REPO / "assets" / "characters" / args.char / "expressions"
    if args.refit:
        from PIL import Image
        outdir.mkdir(parents=True, exist_ok=True)
        raws = sorted(outdir.glob("*.raw.jpg"))
        if not raws:
            sys.exit(f"no raws in {outdir}")
        for raw in raws:
            img = Image.open(raw)
            w, h = img.size
            if w > 900:
                img = img.resize((900, round(h * 900 / w)), Image.LANCZOS)
            img.convert("RGB").save(raw.with_name(raw.name[:-8] + ".jpg"), quality=92)
            print("refit", raw.name)
        print(f"DONE refit {len(raws)} finals")
        return
    ref = Path(args.ref) if args.ref else DEFAULT_REFS.get(args.char)
    if not ref or not ref.exists():
        sys.exit(f"ref not found: {ref}")
    ref_url = local_ref_to_url(str(ref))  # 本地定妆照 → OSS URL（API 只吃公网 URL）
    print(f"[ref] {ref_url}", flush=True)
    ref_hint = IDENTITY.get(args.char, "与参考图完全一致的角色造型")

    names = [n for n in (args.only.split(",") if args.only else EXPRESSIONS) if n]
    bad = [n for n in names if n not in EXPRESSIONS]
    if bad:
        sys.exit(f"unknown expressions: {bad}; valid: {list(EXPRESSIONS)}")

    meta_path = outdir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {
        "char": args.char, "identity": ref_hint, "canon": {}, "items": {}
    }
    meta["canon"] = {k: v["phrase"] for k, v in EXPRESSIONS.items()}

    results = []
    for i, name in enumerate(names):
        e = EXPRESSIONS[name]
        raw = outdir / f"{name}.raw.jpg"
        fit = outdir / f"{name}.jpg"
        prompt = build_prompt(args.char, name, ref_hint)
        idx, ok, msg = gen_one((i, prompt, ref_url, str(raw), str(fit), args.retries))
        results.append({"expr": name, "ok": ok, "msg": msg})
        print(json.dumps({"expr": name, "ok": ok, "msg": msg}, ensure_ascii=False), flush=True)
        if ok:
            meta["items"][name] = {
                "file": f"{name}.jpg",
                "raw": f"{name}.raw.jpg",
                "phrase": e["phrase"],
                "sanity": e["sanity"],
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "qc": "pending",
            }
        # 失败的旧条目保留原样（不覆盖已 QC 通过的记录）
        if i < len(names) - 1:
            time.sleep(args.pause)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_n = sum(1 for r in results if r["ok"])
    print(json.dumps({"summary": f"{ok_n}/{len(results)} generated",
                      "outdir": str(outdir), "meta": str(meta_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
