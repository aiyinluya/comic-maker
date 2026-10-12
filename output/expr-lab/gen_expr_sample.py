#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_expr_sample.py - 表情库样张生成（表情库项目第一步）
复用 scripts/gen_panel.py 的 gen_one（已验证链路：本地图→upload-mix→OSS→seedream）。
产出: output/expr-lab/sheet-xiaoma-v2.{raw,fit}.jpg
用法: python output/expr-lab/gen_expr_sample.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # output/expr-lab/
ROOT = HERE.parent.parent                        # comic-maker 仓库根
sys.path.insert(0, str(ROOT / "scripts"))
from gen_panel import gen_one, local_ref_to_url  # noqa: E402

REF_LOCAL = ROOT / "assets/characters/xiaoke-ref-manga.jpg"

PROMPT = (
    "手绘漫画角色表情设定表，Q版大头比例。主角只有一个男生：黑色短发、圆框眼镜、"
    "深灰色连帽衫、蓝色牛仔裤（以参考图角色为准，造型完全一致）。白色背景，"
    "4列2行共8格，格与格之间留白分隔，均匀黑色描边，不写任何文字，无水印。"
    "8格表情依次为：1平静微笑、2惊讶（眉毛上挑、眼睛睁大、嘴微张）、"
    "3皱眉思考（手托下巴）、4开心大笑、5疑惑歪头、6得意挑眉、"
    "7生气鼓腮、8无奈叹气（闭眼）。"
    "每一格都必须清晰画出圆框眼镜，任何一格不得丢失眼镜或改变服装。"
)


def main():
    ref_url = local_ref_to_url(REF_LOCAL)
    print("ref uploaded:", ref_url[:60], "...")
    job = ("sheet-xiaoma-v2", PROMPT, ref_url,
           str(HERE / "sheet-xiaoma-v2.raw.jpg"),
           str(HERE / "sheet-xiaoma-v2.fit.jpg"), 3)
    idx, ok, msg = gen_one(job)
    print(("OK " if ok else "FAIL"), msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()