#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_blog.py — 从分镜成品一键生成漫画博客（三版：MD / 杂志 HTML / 公众号复制版）。

用法:
  python gen_blog.py --story stories/story-20-zcode --out-id 20-zcode-incident \
      --title "加密包裹：从曝光到开源的三天" \
      --kicker "码事漫谈 · AI 科普第 20 话 · 2026-09-21" \
      --format panels            # panels=单格图文交错 | long=长图单图版
  python gen_blog.py --story ... --wechat-only --title ... --kicker ...

三版产物（--out-dir 默认 articles/）:
  <out-id>.md              Markdown 图文版（配图拷入 articles/assets/<out-id>/）
  <out-id>.html            杂志风阅读版（delivery-artifact 杂志形态规范）
  <out-id>-wechat.html     公众号复制版（全内联样式 + OSS 图床，浏览器全选复制即用）

博客正文来源 --blog-md：Markdown 章节（## 小节 + ![图](NN) 占位）。
缺省时按 panels 模式从 storyboard.md 自动生成骨架文案（占位性质，发布前应人工润色）。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent   # 仓库根（本脚本位于 scripts/ 下）
_UP_DEFAULT = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\upload-mix.py"
UP = os.environ.get("COMIC_UPLOAD", _UP_DEFAULT)


# ──────────────────────────── 通用工具 ────────────────────────────

def parse_storyboard(story: Path):
    """解析 storyboard.md → [{key, q, a, scene}]（跳过过场格）。"""
    sb = story / "storyboard.md"
    rows = []
    for line in sb.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5 or cells[0] in ("#", "---") or set(cells[0]) <= set("-: "):
            continue
        if "提问" in "".join(cells):
            continue
        ref, q, a, scene = cells[1], cells[2], cells[3], cells[4]
        if "过场" in q:
            continue
        rows.append({"key": ref, "q": re.sub(r"[（(][^）)]*[)）]", "", q).strip(),
                     "a": a, "scene": scene})
    return rows


def count_panels(panels_dir: Path):
    return len(list(panels_dir.glob("v8-*.final.jpg")))


def upload_oss(path: Path):
    r = subprocess.run([sys.executable, UP, str(path)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"upload failed: {r.stderr[-200:]}")
    return json.loads(r.stdout)["data"]["oss_info"][0]["oss_url"]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ──────────────────────────── 文案骨架 ────────────────────────────

def draft_panels_script(rows):
    """panels 模式缺省文案：按分镜问答生成骨架（人工润色前占位）。"""
    parts = []
    parts.append("## 引入\n\n（导语：两三句话交代这篇讲什么、为什么值得读。发布前润色。）\n")
    opened = False
    for r in rows:
        if r["q"]:
            if opened:
                parts.append("")
            parts.append(f"## 问：{r['q']}\n")
            opened = True
        parts.append(f"{r['a']}\n")
        parts.append(f"![{r['scene'][:20]}]({r['key'].replace('v8-', '')})\n")
    parts.append("## 收个尾\n\n（结语：一段话收束观点。发布前润色。）\n")
    return "\n".join(parts)


def draft_long_script(out_id, title, n):
    return (f"## 引入\n\n（导语：两三句话交代这篇讲什么。发布前润色。）\n\n"
            f"![{title}（完整长图，建议收藏）](LONG)\n\n"
            f"## 正文\n\n长图共 {n} 格，请横屏滑动阅读。要点速览：\n\n"
            f"（分点速览：把长图里的关键结论列成 3-5 条。发布前润色。）\n")


# ──────────────────────────── MD 版 ────────────────────────────

def gen_md(blog_md, out_id, title, kicker, story, out_dir, long_png):
    assets = out_dir / "assets" / out_id
    assets.mkdir(parents=True, exist_ok=True)
    body = blog_md
    if body.lstrip().startswith("# "):
        body = re.sub(r"^# .+?\n", "", body, count=1)
    if "(LONG)" in body:
        rel = f"../output/long-form/{out_id}/{out_id}.png"
        body = body.replace("(LONG)", f"({rel})")
    stem = long_png.stem if long_png else out_id
    out = [f"# {title}\n",
           f"> {kicker}\n",
           f"> 配套漫画《{title}》 · [完整长图]({rel if '(LONG)' in blog_md else '../output/long-form/' + out_id + '/' + out_id + '.png'})\n",
           body.rstrip(),
           "\n---\n",
           "\n**出自公众号：码事漫谈**\n"]
    text = "\n".join(out)
    # 把 ![xx](NN) 数字占位拷贝为资产图
    def copy_asset(m):
        alt, num = m.group(1), m.group(2)
        src = story / "panels" / f"v8-{num}.final.jpg"
        if src.exists():
            shutil.copy(src, assets / f"{num}.jpg")
            return f"![{alt}](assets/{out_id}/{num}.jpg)"
        return m.group(0)
    text = re.sub(r"!\[([^\]]*)\]\((\d{2})\)", copy_asset, text)
    path = out_dir / f"{out_id}.md"
    path.write_text(text, encoding="utf-8")
    print(f"  md  -> {path.name}")
    return path


# ──────────────────────────── 杂志 HTML 版 ────────────────────────────

def md_to_html_blocks(blog_md, story, out_dir, out_id, mode, offline=False):
    """极简 MD→HTML：## 标题 / 引用 / 段落 / 图片占位。图片按模式取本地图或 OSS。"""
    urls = load_oss_urls(out_id, story, blog_md, offline) if mode == "panels" else {}
    blocks = []
    for raw in blog_md.split("\n\n"):
        s = raw.strip()
        if not s:
            continue
        if s.startswith("## "):
            blocks.append(f"<h2>{esc(s[3:])}</h2>")
        elif s.startswith("> "):
            blocks.append("<blockquote>" + esc(s[2:].replace("\n", "<br/>")) + "</blockquote>")
        elif s.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
            if not m:
                continue
            alt, ref = m.group(1), m.group(2)
            if ref == "LONG":
                src = f"../output/long-form/{out_id}/{out_id}.png"
                blocks.append(f'<figure class="panel long"><img src="{src}" alt="{esc(alt)}" loading="lazy" /><figcaption>{esc(alt)}</figcaption></figure>')
            elif re.fullmatch(r"\d{2}", ref) and ref in urls:
                blocks.append(f'<figure class="panel"><img src="{urls[ref]}" alt="{esc(alt)}" /><figcaption>{esc(alt)}</figcaption></figure>')
            elif re.fullmatch(r"\d{2}", ref):
                shutil.copy(story / "panels" / f"v8-{ref}.final.jpg", out_dir / "assets" / out_id / f"{ref}.jpg")
                blocks.append(f'<figure class="panel"><img src="assets/{out_id}/{ref}.jpg" alt="{esc(alt)}" /><figcaption>{esc(alt)}</figcaption></figure>')
        elif s.startswith("- "):
            items = "".join(f"<li>{esc(li[2:])}</li>" for li in s.splitlines() if li.startswith("- "))
            blocks.append(f"<ul>{items}</ul>")
        else:
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(s).replace("\n", "<br/>"))
            body = re.sub(r"`(.+?)`", r"<code>\1</code>", body)
            blocks.append(f"<p>{body}</p>")
    return blocks


def load_oss_urls(out_id, story, blog_md, offline=False):
    if offline:
        print("offline mode: skip OSS upload, use asset paths in wechat html")
        return {}
    cache = HERE / ".openclaw/tmp" / f"oss_urls_{out_id}.json"
    refs = sorted(set(re.findall(r"!\[[^\]]*\]\((\d{2})\)", blog_md)))
    if cache.exists():
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if all(r in cached for r in refs):
            return {r: cached[r] for r in refs}
    urls = {}
    for r in refs:
        urls[r] = upload_oss(story / "panels" / f"v8-{r}.final.jpg")
        print(f"  oss {r}", flush=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(urls, indent=2), encoding="utf-8")
    return urls


def gen_magazine(blog_md, out_id, title, kicker, story, out_dir, mode, offline=False):
    blocks = md_to_html_blocks(blog_md, story, out_dir, out_id, mode, offline)
    _TPL_DEFAULT = r"C:\Users\liz-an\.openclaw-autoclaw\skills\delivery-artifact\assets\magazine-template.html"
    tpl = Path(os.environ.get("COMIC_MAGAZINE_TPL", _TPL_DEFAULT))
    css = ""
    if tpl.exists():
        t = tpl.read_text(encoding="utf-8")
        m = re.search(r"<style>(.*?)</style>", t, re.S)
        css = m.group(1) if m else ""
    css += """
  figure.panel { margin:2em 0; }
  figure.panel img { width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:10px; }
  figure.panel.long img { border:none; }
  figure.panel figcaption { font-size:12px; color:var(--mute); text-align:center; margin-top:10px; letter-spacing:0.04em; }
"""
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Noto+Sans+SC:wght@300;400;500;600&family=Noto+Serif+SC:wght@500;700;900&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body class="grain">
<article class="article max-w-[720px] mx-auto px-6 pt-20 pb-32">
<div class="text-[11px] font-medium tracking-[0.22em] uppercase text-[var(--accent)] mb-5">{esc(kicker)}</div>
<h1 class="serif text-[3rem] leading-[1.08] font-black tracking-tight mb-5">{esc(title)}</h1>
<div class="flex items-center gap-3 text-[12px] text-[var(--mute)] pb-12 border-b border-[var(--line)]">
<div class="w-8 h-8 rounded-full" style="background:var(--accent)"></div>
<span class="font-medium text-[var(--ink)]">码事漫谈</span>
<span>·</span><span>小码 &amp; 波普 漫画配套图文</span>
</div>
{chr(10).join(blocks)}
<p class="text-center text-[12px] text-[var(--mute)] mt-14 tracking-[0.1em]">出自公众号：码事漫谈</p>
</article>
</body>
</html>
"""
    path = out_dir / f"{out_id}.html"
    path.write_text(html, encoding="utf-8")
    print(f"  html -> {path.name}")
    return path


# ──────────────────────────── 公众号复制版 ────────────────────────────

def gen_wechat(blog_md, out_id, title, kicker, story, out_dir, mode, offline=False):
    urls = load_oss_urls(out_id, story, blog_md, offline) if mode == "panels" else {}
    B = lambda t: f'<strong style="color:#1a1a1a;font-weight:700;">{t}</strong>'
    P = lambda t: (f'<p style="font-size:15px;line-height:1.85;color:#262421;margin:0 0 18px;">{t}</p>')
    H2 = lambda t: (f'<h2 style="font-size:20px;font-weight:700;color:#1a1a1a;'
                    f'margin:42px 0 16px;line-height:1.4;">{t}</h2>')
    QUOTE = lambda t: (f'<blockquote style="border-left:3px solid #b8553a;margin:22px 0;'
                       f'padding:4px 0 4px 16px;font-size:15px;line-height:1.8;color:#8a857c;">{t}</blockquote>')
    ORN = ('<p style="text-align:center;color:#b8b4ac;font-size:14px;'
           'margin:34px 0;letter-spacing:6px;">· · ·</p>')
    CAP = lambda t: (f'<p style="text-align:center;font-size:12px;color:#8a857c;'
                     f'margin:8px 0 24px;letter-spacing:0.05em;">{t}</p>')
    IMG = (lambda key, alt: f'<img src="{urls[key]}" alt="{esc(alt)}" '
           'style="width:100%;height:auto;display:block;border-radius:8px;" />')

    parts = ['<p style="font-size:12px;color:#b8553a;letter-spacing:0.2em;'
             'margin:0 0 14px;font-weight:600;">' + esc(kicker) + '</p>']
    parts.append('<h1 style="font-size:25px;font-weight:800;color:#1a1a1a;'
                 'line-height:1.35;margin:0 0 18px;">' + esc(title) + '</h1>')
    parts.append('<hr style="border:none;border-top:1px solid #e7e5e0;margin:0 0 30px;" />')

    for raw in blog_md.split("\n\n"):
        s = raw.strip()
        if not s:
            continue
        if s.startswith("## "):
            parts.append(ORN)
            parts.append(H2(esc(s[3:])))
        elif s.startswith("> "):
            parts.append(QUOTE(esc(s[2:]).replace("\n", "<br/>")))
        elif s.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
            if not m:
                continue
            alt, ref = m.group(1), m.group(2)
            if ref == "LONG":
                if offline:
                    u = f"../output/long-form/{out_id}/{out_id}.png"
                else:
                    u = upload_oss(HERE / "output/long-form" / out_id / f"{out_id}.png")
                parts.append(f'<img src="{u}" alt="{esc(alt)}" '
                             'style="width:100%;height:auto;display:block;" />')
            elif re.fullmatch(r"\d{2}", ref) and ref in urls:
                parts.append(IMG(ref, alt))
                parts.append(CAP(esc(alt)))
            elif re.fullmatch(r"\d{2}", ref):
                shutil.copy(story / "panels" / f"v8-{ref}.final.jpg",
                            out_dir / "assets" / out_id / f"{ref}.jpg")
                parts.append(f'<img src="assets/{out_id}/{ref}.jpg" alt="{esc(alt)}" '
                             'style="width:100%;height:auto;display:block;border-radius:8px;" />')
                parts.append(CAP(esc(alt)))
        elif s.startswith("- "):
            for li in s.splitlines():
                if li.startswith("- "):
                    parts.append(P("· " + re.sub(r"\*\*(.+?)\*\*",
                                 lambda mm: B(mm.group(1)), esc(li[2:]))))
        else:
            body = re.sub(r"\*\*(.+?)\*\*", lambda mm: B(mm.group(1)),
                          re.sub(r"`(.+?)`",
                                 lambda mm: f'<code style="background:#f0ece5;color:#7a3d27;'
                                            f'padding:2px 6px;border-radius:3px;font-size:13px;'
                                            f'font-family:Consolas,monospace;">{esc(mm.group(1))}</code>',
                                 esc(s)))
            parts.append(P(body.replace("\n", "<br/>")))

    parts.append('<p style="border-top:1px solid #e7e5e0;margin:34px 0 0;"></p>')
    parts.append('<p style="text-align:center;font-size:13px;font-weight:600;color:#1a1a1a;'
                 'margin:26px 0 6px;">出自公众号：码事漫谈</p>')
    html = ('<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8" />'
            '<meta name="viewport" content="width=device-width, initial-scale=1" />'
            f'<title>{esc(title)}（公众号版）</title></head>'
            '<body style="margin:0;background:#ffffff;">'
            '<section style="max-width:578px;margin:0 auto;padding:36px 16px 40px;'
            'font-family:-apple-system-font,BlinkMacSystemFont,\'Helvetica Neue\','
            '\'PingFang SC\',\'Hiragino Sans GB\',\'Microsoft YaHei UI\','
            '\'Microsoft YaHei\',Arial,sans-serif;letter-spacing:0.5px;">'
            + "".join(parts) + '</section></body></html>')
    path = out_dir / f"{out_id}-wechat.html"
    path.write_text(html, encoding="utf-8")
    print(f"  wechat -> {path.name}")
    return path


# ──────────────────────────── 主流程 ────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", required=True, help="stories/<作品>/ 目录")
    ap.add_argument("--out-id", required=True, help="output 编号（如 20-zcode-incident）")
    ap.add_argument("--title", required=True)
    ap.add_argument("--kicker", default="码事漫谈 · AI 科普 · 漫画配套图文")
    ap.add_argument("--format", choices=["panels", "long"], default="panels",
                    help="panels=单格图文交错（默认）| long=长图单图版")
    ap.add_argument("--blog-md", default=None, help="博客正文 Markdown（缺省自动生成骨架）")
    ap.add_argument("--out-dir", default=str(HERE / "articles"))
    ap.add_argument("--wechat-only", action="store_true", help="只更新公众号复制版")
    ap.add_argument("--offline", action="store_true", help="不上传 OSS（CI 冒烟用，公众号版退化为本地路径）")
    a = ap.parse_args()

    story = Path(a.story)
    if not story.is_absolute():
        story = HERE / a.story  # HERE = 仓库根（gen_blog.py 位于 scripts/ 下）
    out_dir = Path(a.out_dir)
    long_png = HERE / "output/long-form" / a.out_id / f"{a.out_id}.png"

    blog_md = Path(a.blog_md).read_text(encoding="utf-8") if a.blog_md else None
    if blog_md is None:
        rows = parse_storyboard(story)
        blog_md = (draft_long_script(a.out_id, a.title, count_panels(story / "panels"))
                   if a.format == "long" else draft_panels_script(rows))
        print("blog copy: auto-draft (skeleton, polish before publishing)")

    if a.wechat_only:
        mode = "long" if "(LONG)" in blog_md else "panels"
        gen_wechat(blog_md, a.out_id, a.title, a.kicker, story, out_dir, mode, a.offline)
        return

    gen_md(blog_md, a.out_id, a.title, a.kicker, story, out_dir, long_png)
    mode = "long" if "(LONG)" in blog_md else "panels"
    gen_magazine(blog_md, a.out_id, a.title, a.kicker, story, out_dir, mode, a.offline)
    gen_wechat(blog_md, a.out_id, a.title, a.kicker, story, out_dir, mode, a.offline)
    print("blog trio done")


if __name__ == "__main__":
    main()
