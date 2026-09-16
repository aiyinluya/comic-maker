# -*- coding: utf-8 -*-
"""给技能版 draw_bubbles.py 加 --bubbles 单一事实源直读模式，并同步 comic-maker 副本。"""
import ast
from pathlib import Path

ENGINE = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\skills\comic-explainer\scripts\draw_bubbles.py")

src = ENGINE.read_text(encoding="utf-8")

if "draw_from_storyboard" in src:
    print("already patched")
else:
    # 1) 插入 draw_from_storyboard（放在 render 之后、main 之前）
    func = '''

def draw_from_storyboard(bubbles_path, panel_dir):
    """单一事实源直读：parse_storyboard.py 产出的 bubbles.json → 绘制 → final。
    y1=None 时按文字需求推导气泡高度（44px 档优先，放不下逐级降档）。
    过场格不在 bubbles.json 中，调用方自行把 raw 拷为 final 占位。"""
    import json as _json
    cfg = _json.loads(Path(bubbles_path).read_text(encoding="utf-8"))
    panel_dir = Path(panel_dir)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    seed = [0]
    report = {}
    for key, bubbles in cfg.items():
        src_img = panel_dir / f"{key}.raw.jpg"
        if not src_img.exists():
            alt = panel_dir.parent / f"{key}.raw.jpg"
            if alt.exists():
                src_img = alt
        img = Image.open(src_img).convert("RGB")
        if img.size[0] != 1080:
            img = img.resize((1080, round(img.size[1] * 1080 / img.size[0])), Image.LANCZOS)
        W, H = img.size
        d = ImageDraw.Draw(img)
        rb = []
        for b in bubbles:
            x0, y0, x1 = int(b[0] * W), int(b[1] * H), int(b[2] * W)
            sp, text = b[4], b[5]
            iw = (x1 - x0) - PAD * 2
            size = None
            for F in SIZE_TIERS:
                fnt = load_font(F)
                lines = wrap(text, fnt, iw, probe)
                lh = F * LINE_H
                needed = int(len(lines) * lh + PAD * 2)
                yy1 = min(y0 + needed, int(0.55 * H))
                if len(lines) * lh <= (yy1 - y0) - PAD * 2:
                    size, font = F, fnt
                    break
            if size is None:
                F = SIZE_TIERS[-1]
                size, font = F, load_font(F)
                lines = wrap(text, font, iw, probe)
                lh = size * LINE_H
                yy1 = y0 + int(len(lines) * lh + PAD * 2)
            ih = (yy1 - y0) - PAD * 2
            box = (x0, y0, x1, yy1)
            if sp == "m":
                draw_m_bubble(d, box, seed)
            else:
                draw_p_bubble(d, box, seed)
            cy = y0 + PAD + ih / 2 - len(lines) * lh / 2 + lh / 2
            for ln in lines:
                d.text(((x0 + x1) / 2, cy), ln, font=font, fill=TEXT_COLOR, anchor="mm")
                cy += lh
            rb.append({"speaker": sp, "size": size, "lines": len(lines)})
        out = panel_dir / f"{key}.final.jpg"
        img.save(out, quality=95)
        report[key] = {"out": str(out), "bubbles": rb}
        print(key, _json.dumps(rb, ensure_ascii=False))
    (panel_dir / "draw_report.json").write_text(
        _json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"single-source draw complete -> {panel_dir}")


def main_cli():
    import argparse
    ap = argparse.ArgumentParser(description="Draw speech bubbles & text on bubble-free panels.")
    ap.add_argument("--bubbles", help="bubbles.json from parse_storyboard.py")
    ap.add_argument("--dir", help="directory containing <key>.raw.jpg")
    ap.add_argument("--legacy", action="store_true", help="run built-in JOBS demo")
    a = ap.parse_args()
    if a.bubbles:
        if not a.dir:
            ap.error("--dir is required with --bubbles")
        draw_from_storyboard(a.bubbles, a.dir)
    else:
        main()

'''
    marker = "\nif __name__ == \"__main__\":"
    assert marker in src, "main guard not found"
    src = src.replace(marker, func + marker, 1)
    src = src.replace('if __name__ == "__main__":\n    main()',
                      'if __name__ == "__main__":\n    main_cli()')
    ENGINE.write_text(src, encoding="utf-8")
    ast.parse(src)
    print("engine patched + syntax OK")

# 2) 同步到 comic-maker/scripts（开源副本）
import shutil
dst = Path(r"C:\Users\liz-an\.openclaw-autoclaw\workspace\comic-maker\scripts\draw_bubbles.py")
shutil.copy2(ENGINE, dst)
ast.parse(dst.read_text(encoding="utf-8"))
print("synced ->", dst)
