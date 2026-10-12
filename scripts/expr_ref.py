#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""expr_ref.py — 表情库 → 分镜生成的接线层。

职责：
  1. 组装参考图：单角色直用该角色表情图；双角色 PIL 拼边成合成参考（左=小码右=波普，缓存）。
  2. 上传 OSS（按组合缓存 URL，同组合不重传）。
  3. 生成「表情条款」：把各角色 expressions/meta.json 的规范短语注入提示词，
     并声明合成参考图的左右对应关系。
  4. auto_annotate：关键词表扫场景文本自动标注表情键（兜底 neutral）；
     也支持显式 JSON（{"01": {"xiaoke":"frown","popu":"neutral"}, ...}）。

脚本内用法:
  from expr_ref import ExprRef
  er = ExprRef()
  pairs = [('xiaoke', 'frown'), ('popu', 'speechless')]
  ref = er.ref(pairs)          # OSS URL（合成图与 URL 均缓存）
  prompt = base + scene + er.clause(pairs) + BAN + DNA

命令行自检:
  python expr_ref.py --pairs xiaoke:frown,popu:speechless
  python expr_ref.py --auto "左侧男生小码指着乱线皱眉。右侧波普在旁解释。"
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
LIB = REPO / "assets" / "characters"
COMPOSITE_DIR = LIB / "_composite"
UPLOAD = REPO.parent / "skills" / "autoglm-generate-image-seedream" / "upload-mix.py"

CHARS = ("xiaoke", "popu")
DEFAULT_EXPR = "neutral"

# 关键词 → 表情键（按场景文本顺序首个命中生效；xiaoke 与 popu 分表）
KEYWORDS = {
    "xiaoke": [
        ("皱眉", "frown"), ("不满", "frown"), ("头疼", "sad"), ("失落", "sad"),
        ("眼花缭乱", "confused"), ("困惑", "confused"), ("疑问", "confused"), ("张望", "confused"),
        ("恍然大悟", "surprised"), ("惊讶", "surprised"), ("吃惊", "surprised"),
        ("好奇", "think"), ("思考", "think"), ("琢磨", "think"),
        ("认真", "focus"), ("仔细", "focus"), ("专注", "focus"),
        ("兴奋", "excited"), ("点赞", "excited"),
        ("点头", "smile"), ("满意", "smile"), ("大拇指", "smile"), ("欣赏", "smile"),
        ("无奈", "speechless"),
    ],
    "popu": [
        ("摊手", "speechless"), ("耸肩", "speechless"), ("扶额", "speechless"),
        ("惊讶", "surprised"),
        ("大笑", "laugh"),
        ("得意", "smug"),
    ],
}
NAME_CN = {"xiaoke": "男生小码", "popu": "机器人波普"}


def _canon(char: str, expr: str) -> str:
    """从角色 expressions/meta.json 取规范短语；缺库时回退 gen_expressions 表。"""
    meta_path = LIB / char / "expressions" / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ph = (meta.get("items") or {}).get(expr, {}).get("phrase")
        if ph:
            return ph
        ph = (meta.get("canon") or {}).get(expr)
        if ph:
            return ph
    sys.path.insert(0, str(HERE))
    from gen_expressions import EXPRESSIONS
    return EXPRESSIONS[expr]["phrase"]


def auto_annotate(scene: str) -> dict:
    """场景文本 → {char: expr}。各角色独立匹配第一个关键词，未命中给 neutral。"""
    out = {}
    for char in CHARS:
        hit = DEFAULT_EXPR
        for kw, expr in KEYWORDS[char]:
            if kw in scene:
                hit = expr
                break
        out[char] = hit
    return out


class ExprRef:
    def __init__(self):
        COMPOSITE_DIR.mkdir(parents=True, exist_ok=True)
        self._cache_path = COMPOSITE_DIR / "upload_cache.json"
        self._cache = {}
        if self._cache_path.exists():
            self._cache = json.loads(self._cache_path.read_text(encoding="utf-8"))

    # ---- 参考图 ----
    def _composite(self, pairs) -> Path:
        """双角色：900px 头像左右拼接，中缝细线。返回合成图路径。"""
        from PIL import Image
        key = "+".join(f"{c}-{e}" for c, e in pairs)
        out = COMPOSITE_DIR / f"{key}.jpg"
        if out.exists():
            return out
        tiles = []
        for c, e in pairs:
            f = LIB / c / "expressions" / f"{e}.jpg"
            if not f.exists():
                raise SystemExit(f"expression missing: {f}（先跑 gen_expressions.py）")
            tiles.append(Image.open(f).convert("RGB"))
        w = max(t.width for t in tiles)
        tiles = [t.resize((w, round(t.height * w / t.width))) for t in tiles]
        h = max(t.height for t in tiles)
        canvas = Image.new("RGB", (w * len(tiles) + 6 * (len(tiles) - 1), h), (216, 208, 192))
        x = 0
        for t in tiles:
            canvas.paste(t, (x, 0))
            x += w + 6
        canvas.save(out, quality=92)
        return out

    def ref(self, pairs) -> str:
        """pairs → 参考图 OSS URL（合成与上传均按内容缓存）。"""
        pairs = list(pairs)
        if len(pairs) == 1:
            c, e = pairs[0]
            local = LIB / c / "expressions" / f"{e}.jpg"
        else:
            local = self._composite(pairs)
        key = local.name
        hit = self._cache.get(key)
        if hit and hit.get("url"):
            return hit["url"]
        r = subprocess.run([sys.executable, str(UPLOAD), str(local)],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"upload failed: {r.stderr[-200:]}")
        url = json.loads(r.stdout)["data"]["oss_info"][0]["oss_url"]
        self._cache[key] = {"url": url, "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        self._cache_path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
        return url

    # ---- 提示词条款 ----
    def clause(self, pairs) -> str:
        pairs = list(pairs)
        if len(pairs) == 1:
            c, e = pairs[0]
            return (f"重要：参考图即{NAME_CN[c]}的表情头像特写，"
                    f"正图中该角色的面部表情必须与参考图完全一致（{_canon(c, e)}）。")
        left, right = pairs[0], pairs[1]
        return (
            f"重要：参考图由左右两格头像拼成——左格是{NAME_CN[left[0]]}的头像特写"
            f"（表情：{_canon(*left)}），右格是{NAME_CN[right[0]]}的头像特写"
            f"（表情：{_canon(*right)}）。"
            f"正图中{NAME_CN[left[0]]}的面部表情必须与左格一致，"
            f"{NAME_CN[right[0]]}的眼睛神态必须与右格一致；"
            f"两角色的造型（发型/眼镜/服装/面罩/徽章）严格保持参考图头像所示。"
        )


def _parse_pairs(s: str):
    out = []
    for part in s.split(","):
        c, e = part.strip().split(":")
        out.append((c.strip(), e.strip()))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default="", help="如 xiaoke:frown,popu:speechless")
    ap.add_argument("--auto", default="", help="场景文本，打印自动标注结果")
    args = ap.parse_args()
    er = ExprRef()
    if args.auto:
        print(json.dumps(auto_annotate(args.auto), ensure_ascii=False))
    if args.pairs:
        pairs = _parse_pairs(args.pairs)
        print(json.dumps({"ref": er.ref(pairs), "clause": er.clause(pairs)},
                         ensure_ascii=False, indent=2))
