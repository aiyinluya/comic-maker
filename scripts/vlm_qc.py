# -*- coding: utf-8 -*-
"""vlm_qc.py — VLM 视觉质检（给流水线装上「看得见」的双眼）。

现有 lint.py 是像素/几何质检：墨迹越界、字号档位、final/raw 齐套。
它回答不了三个真实事故：
  1. 小码的圆框眼镜丢没丢（R1 · 角色变脸）
  2. 画面里有没有混进可读文字（R3 · 意外文字；空场景必须无文字）
  3. 网关水印有没有残留（R19 · 「AutoClaw AI生成」印进成品）

本脚本用多模态模型（Seed-2.1-pro-0915，火山方舟 OpenAI 兼容接口）
逐格看图，输出结构化 JSON，与 lint.py 形成「几何查墨迹 vs VLM 查语义」互补。

用法:
  python scripts/vlm_qc.py --dir stories/story-21-jev/panels
  python scripts/vlm_qc.py --dir posts/<slug>/panels --panels v8-01,v8-03

环境变量:
  ARK_API_KEY   火山方舟 API Key（必填）
  ARK_BASE_URL  默认 https://ark.cn-beijing.volces.com/api/v3
  ARK_MODEL     默认 seed-2.1-pro-0915

输出: <dir>/vlm_report.json（与 lint_report.json 并列，可进 CI）
退出码: 0=全部格完成质检；1=存在 API/IO 错误；2=用法错误（缺 Key/目录不存在）。
"""
import argparse
import base64
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "seed-2.1-pro-0915"
TIMEOUT = 60
RETRY = 2
RETRY_BACKOFF = 5.0

# 角色判定依据（来自定妆照 assets/characters/*-ref-manga.jpg）
DEFAULT_CHAR_SPEC = {
    "xiaoke": "小码（提问者，通常画面左侧）：黑色短发 + 圆框眼镜 + 深灰/灰色连帽衫（带波点）",
    "popu": "波普（解答者，通常画面右侧）：白色胶囊/圆润机器人 + 蓝色发光眼睛 + 橙色胸徽/圆形按钮",
}

SYSTEM_PROMPT = """你是一名漫画流水线的视觉质检员（VLM QC）。逐格检查漫画「空场景图」（无气泡、无文字、上部留白），输出严格 JSON。

角色判定依据（来自定妆照）：
- {xiaoke}
- {popu}

检查项：
1. xiaoke_glasses_ok：小码的圆框眼镜是否在位。没戴 / 戴歪 / 画没了 → false。
2. popu_ok：波普是否保持定妆要素。白色圆润机身 + 蓝色发光眼睛 + 橙色胸徽三者齐全 → true。
3. head_occluded：是否有物体/前景遮挡角色头部或脸。空场景无气泡，此值通常为 false。
4. stray_text：画面中是否混入可读文字/数字/乱码（表格字、卷轴字、面板刻度数字等）；OCR 无法辨认的疑似字符区也标 true，并在 notes 说明大致位置。
5. watermark：是否有平台/网关水印（如右下角「AI生成」类白色小字）。

只输出一个 JSON 对象，键固定为：
{{"panel":"<格名>","xiaoke_glasses_ok":bool,"popu_ok":bool,"head_occluded":bool,"stray_text":bool,"watermark":bool,"notes":"<中文说明>"}}
不要输出 JSON 以外的任何文字、代码块围栏或解释。"""

USER_PROMPT = "逐格检查这张漫画空场景图，按系统规则输出质检 JSON。"


def _data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() in (".png",) else "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _parse_json_content(text: str) -> dict:
    """优先 json_object 模式；失败则剥代码块围栏后取首个 {...}。"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"模型输出中未找到 JSON：{text[:200]!r}")
    return json.loads(m.group(0))


def _call_vision(api_key: str, base_url: str, model: str, panel: str, data_url: str,
                 char_spec: dict) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    system = SYSTEM_PROMPT.format(xiaoke=char_spec["xiaoke"], popu=char_spec["popu"])
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    last_err = None
    for attempt in range(1, RETRY + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            return _parse_json_content(content)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < RETRY:
                time.sleep(RETRY_BACKOFF)
    raise RuntimeError(f"调用视觉接口失败：{last_err}")


def main():
    ap = argparse.ArgumentParser(description="VLM 视觉质检：逐格查眼镜/角色要素/盖头/混进文字/水印")
    ap.add_argument("--dir", required=True, help="panels 目录（含 v8-NN.raw.jpg）")
    ap.add_argument("--panels", help="逗号分隔的格名，如 v8-01,v8-03；缺省扫描全部 *.raw.jpg")
    ap.add_argument("--out", help="输出 JSON 路径，缺省 <dir>/vlm_report.json")
    ap.add_argument("--api-key", help="火山方舟 API Key（缺省读 ARK_API_KEY）")
    ap.add_argument("--base-url", default=None, help="接口地址，缺省读 ARK_BASE_URL 或官方默认")
    ap.add_argument("--model", default=None, help="模型名，缺省读 ARK_MODEL 或 seed-2.1-pro-0915")
    ap.add_argument("--char-spec", help="可选：角色判定依据 JSON 文件 {\"xiaoke\":\"...\",\"popu\":\"...\"}")
    a = ap.parse_args()

    d = Path(a.dir)
    if not d.is_dir():
        print(f"ERROR: 目录不存在：{d}")
        sys.exit(2)
    if a.panels:
        keys = [k.strip() for k in a.panels.split(",") if k.strip()]
    else:
        keys = sorted(p.stem.removesuffix(".raw") for p in d.glob("*.raw.jpg"))
    if not keys:
        print(f"ERROR: {d} 下没有 raw 图，无可质检格")
        sys.exit(2)

    api_key = a.api_key or __import__("os").environ.get("ARK_API_KEY")
    if not api_key:
        print("ERROR: 缺少 API Key。请设置环境变量 ARK_API_KEY 或传 --api-key")
        sys.exit(2)
    base_url = a.base_url or __import__("os").environ.get("ARK_BASE_URL", DEFAULT_BASE_URL)
    model = a.model or __import__("os").environ.get("ARK_MODEL", DEFAULT_MODEL)
    char_spec = DEFAULT_CHAR_SPEC
    if a.char_spec:
        char_spec = json.loads(Path(a.char_spec).read_text(encoding="utf-8"))

    report, failed = {}, 0
    for key in keys:
        rawp = d / f"{key}.raw.jpg"
        if not rawp.exists():
            report[key] = {"error": "missing raw"}
            failed += 1
            continue
        try:
            res = _call_vision(api_key, base_url, model, key, _data_url(rawp), char_spec)
            if not isinstance(res, dict) or "panel" not in res:
                raise ValueError(f"JSON 缺 panel 键：{res!r}")
            report[key] = res
            print(f"{key}: glasses={res.get('xiaoke_glasses_ok')} popu={res.get('popu_ok')} "
                  f"head={res.get('head_occluded')} text={res.get('stray_text')} wm={res.get('watermark')}")
        except Exception as e:  # noqa: BLE001 —— 单格失败不中断整话
            report[key] = {"error": str(e)}
            failed += 1
            print(f"{key}: ERROR {e}", file=sys.stderr)

    report["_meta"] = {
        "engine": "ark-seed-vlm",
        "model": model,
        "base_url": base_url,
        "char_spec": char_spec,
        "checked": len(keys),
        "failed": failed,
    }
    out = Path(a.out) if a.out else d / "vlm_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out}")
    print("VLM-QC:", "FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
