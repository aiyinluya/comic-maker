#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_expr_single.py - 表情库正式形态：单角色单表情立绘
表情库每个表情 = 一张独立图（定妆照参考 + 表情提示词），QC 过关后入 assets/characters/<role>/expr/
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from gen_panel import gen_one, local_ref_to_url  # noqa: E402

REF_LOCAL = ROOT / "assets/characters/xiaoke-ref-manga.jpg"

BASE = ("手绘漫画风格单人立绘，Q版大头比例，白色背景，黑色描边，不写任何文字，无水印。"
        "主角：黑色短发男生，圆框眼镜（必须清晰戴在脸上，镜片完整可见），深灰色连帽衫，蓝色牛仔裤，"
        "造型与参考图完全一致。表情：")

EXPRS = {
    "laugh":  "开心大笑，眼睛弯成月牙但眼镜仍清晰戴在脸上，嘴巴大张，身体微微后仰。",
    "think":  "皱眉思考，手托下巴，眉头紧锁，眼镜清晰，眼神向上。",
    "sigh":   "无奈叹气，眉毛下垂，嘴角向下撇，眼皮半垂但眼镜清晰戴在脸上，肩膀下垂。",
}


def main():
    ref_url = local_ref_to_url(REF_LOCAL)
    print("ref uploaded:", ref_url[:60], "...")
    outdir = HERE / "single"
    failed = []
    for name, expr in EXPRS.items():
        job = (name, BASE + expr, ref_url,
               str(outdir / f"{name}.raw.jpg"), str(outdir / f"{name}.jpg"), 3)
        idx, ok, msg = gen_one(job)
        print(("OK " if ok else "FAIL"), name, msg[:100])
        if not ok:
            failed.append(name)
    print("done, failed:", failed if failed else "none")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()