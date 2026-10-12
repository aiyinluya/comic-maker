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
        "phrase": "表情平静自然，嘴唇轻闭，眼神正视前方",
        "sanity": "面部放松，嘴闭合，无夸张眉眼动作",
    },
    "surprised": {
        "phrase": "眼睛睁大，眉毛上挑，嘴巴微张，表情惊讶",
        "sanity": "双眼明显睁大，眉上挑，嘴微张",
    },
    "frown": {
        "phrase": "眉头紧锁下压，嘴角向下，神情不满或严肃审视",
        "sanity": "眉间皱起，嘴角下弯，无笑容",
    },
    "smile": {
        "phrase": "嘴角上扬的温和微笑，眼睛柔和",
        "sanity": "嘴角明显上扬，眼神柔和，无露齿大笑",
    },
    "laugh": {
        "phrase": "开怀大笑，眼睛弯成缝，嘴巴大张露出大笑的神态",
        "sanity": "眼睛眯起，嘴大张，整体开怀",
    },
    "think": {
        "phrase": "一手托腮或手指抵下巴，目光斜向上，若有所思",
        "sanity": "托腮/抵下巴动作 + 眼神向上或斜向",
    },
    "shock": {
        "phrase": "极度震惊：双眼圆睁，嘴巴大张成 O 形，身体后仰",
        "sanity": "O 形嘴 + 圆睁眼（比 surprised 更夸张）",
    },
    "speechless": {
        "phrase": "无语：半眯眼平视，嘴角平直，一脸无奈",
        "sanity": "眼睑下垂半眯，嘴平直，无奈神态",
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
        f"以参考图中的角色为主角，绘制单张漫画角色头像特写，"
        f"腰部以上构图，纯色浅米白背景，漫画线稿风格，均匀描边，上色简洁。"
        f"严格保持参考图造型：{ref_hint}。"
        f"角色表情：{e['phrase']}。"
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
