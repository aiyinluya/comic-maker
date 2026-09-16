# -*- coding: utf-8 -*-
"""给 scripts/draw_bubbles.py 增加 --bubbles 单一事实源直读模式。"""
from pathlib import Path

p = Path("scripts/draw_bubbles.py")
src = p.read_text(encoding="utf-8")

old = '''def main():
    ap = argparse.ArgumentParser(description="Draw speech bubbles & text on bubble-free panels.")
    ap.add_argument("--config", required=True, help="JSON config (see examples/bubbles.example.json)")
    args = ap.parse_args()'''

new = '''def draw_from_storyboard(bubbles_path: Path, panel_dir: Path):
    """单一事实源直读：bubbles.json（parse_storyboard 产出）→ 绘制 → final。
    y1=None 时按文字需求推导气泡高度（44px 档位，放不下逐级降档）。"""
    cfg = json.loads(bubbles_path.read_text(encoding="utf-8"))
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    seed = [0]
    report = {}
    for key, bubbles in cfg.items():
        src_img = panel_dir / f"{key}.raw.jpg"
        if not src_img.exists():
            # 兼容早期 raw 在上级目录的布局
            alt = panel_dir.parent / f"{key}.raw.jpg"
            src_img = alt if alt.exists() else src_img
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
        print(key, json.dumps(rb, ensure_ascii=False))
    (panel_dir / "draw_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"single-source draw complete -> {panel_dir}")


def main():
    ap = argparse.ArgumentParser(description="Draw speech bubbles & text on bubble-free panels.")
    ap.add_argument("--config", help="JSON config (see examples/bubbles.example.json)")
    ap.add_argument("--bubbles", help="bubbles.json from parse_storyboard.py (single source of truth)")
    ap.add_argument("--dir", help="panel directory containing <key>.raw.jpg (with --bubbles)")
    args = ap.parse_args()
    if args.bubbles:
        if not args.dir:
            ap.error("--dir is required with --bubbles")
        draw_from_storyboard(Path(args.bubbles), Path(args.dir))
        return'''

assert old in src, "main() pattern not found"
src = src.replace(old, new)
p.write_text(src, encoding="utf-8")
print("draw_bubbles.py patched with --bubbles mode")
