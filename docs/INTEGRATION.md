# 图像后端 / 字体 / 平台适配指南

本仓库的核心脚本（`draw_bubbles.py` / `stack.py` / `comic.py`）只依赖 Pillow + numpy，
**不绑定任何图像生成服务**。生成环节（空场景出格）通过一个极薄的适配层对接你的后端。

## 一、图像生成后端

`scripts/gen_panel.py` 只要求你的后端满足一个契约：

```
输入：提示词字符串 + 可选的参考图公网 URL
输出：JSON，其中包含生成图片的 URL（本仓库默认解析 data.image_url 字段）
```

### 方案 A：AutoGLM Seedream（默认，国内网络友好）

本仓库默认脚本对接 [智谱 AutoGLM 技能接口](https://autoglm-api.zhipuai.cn)，
需要本地 token 服务（`http://127.0.0.1:18432/get_token`）。参考实现：

- [`autoglm-generate-image-seedream`](https://github.com/search?q=autoglm+generate-image-seedream)（generate-image-seedream.py / upload-mix.py）

### 方案 B：任何 OpenAI 兼容图像 API

写一个 10 行适配脚本，把 `generate-image-seedream.py` 的行为替换掉即可：

```python
# my_backend.py：输入提示词（和可选参考图 URL），stdout 输出 {"data": {"image_url": "..."}}
import base64, json, sys, urllib.request

prompt = sys.argv[1]
body = {"model": "gpt-image-1", "prompt": prompt, "size": "1536x1024"}
req = urllib.request.Request(
    "https://api.openai.com/v1/images/generations",
    data=json.dumps(body).encode(),
    headers={"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
)
url = json.load(urllib.request.urlopen(req))["data"][0]["url"]
print(json.dumps({"data": {"image_url": url}}))
```

然后把 `gen_panel.py` 顶部的 `SEEDREAM` 常量指向你的脚本即可。

### 方案 C：本地 ComfyUI / Stable Diffusion

同样只需满足契约：出图 → 存到可访问路径或临时 HTTP → 打印 `image_url`。
（本地文件路径也可：把 `gen_panel.py` 的下载环节替换为 `shutil.copy`。）

## 二、参考图（定妆照）上传

图生图需要参考图的**公网 URL**。可选：

- 对象存储（OSS/S3/R2）+ 预签名 URL
- 临时图床（如 `upload-mix.py` 这类上传脚本）
- 本地方案：`gen_panel.py` 支持把参考图直接以 base64 塞进 API 请求（改适配层）

## 三、字体配置

`draw_bubbles.py` / `stack.py` 顶部的 `FONT_PATH` 默认为 Windows 微软雅黑：

| 平台 | 推荐字体 | 路径示例 |
|---|---|---|
| Windows | 微软雅黑 Bold（默认） | `C:\Windows\Fonts\msyhbd.ttc` |
| macOS | 苹方 Bold | `/System/Library/Fonts/PingFang.ttc` |
| Linux | 思源黑体 Bold / Noto Sans CJK Bold | `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc` |

跨平台建议：把字体文件放进仓库 `assets/fonts/`（注意各字体的再分发许可），
或提供 `--font` 参数覆盖。

## 四、平台发布适配

| 平台 | 建议 |
|---|---|
| 微信公众号 | 1080px 宽 PNG；发布稿粘进 [doocs/md](https://github.com/doocs/md) 一键转格式 |
| 博客 | 直接用 `long-manga.png`，或 `panels/*.final.jpg` 按格插图 |
| 小红书 | 3:4 竖版：把 `stack.py` 的 `W` 改 1080、每格单独成图 |
| X / Twitter | 每格单独发或用长图；注意 PNG 体积（>5MB 建议用 JPG 分享版） |

## 五、合规提示

- 部分图像服务会在生成图上嵌入「AI 生成」标识（如中国的《AI 生成合成内容标识办法》要求），
  **请保留，不要抹除**；
- 若用于商业发布，确认所用水印政策与平台规则；
- 开源你自己的成品漫画时，注意生成内容的版权条款遵循你所使用服务的用户协议。
