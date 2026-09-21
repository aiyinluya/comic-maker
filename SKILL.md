---
name: "comic-maker"
description: "生成公众号手绘长漫画 v2.8：分镜单一事实源 → 空场景出格（定妆照锁角色）→ 代码绘气泡（构造上根除溢出与乱码）→ lint 质检 → 并行出图 → 长图拼装。画漫画时用。"
---

# Comic Maker — 手绘长漫画流水线（v2.8 · 结构派）

把「一个知识点」变成「一部 8 格手绘长漫画」：分镜先行 → 角色档案 → 分镜解析 → 空场景出格 → 质检 → 代码绘气泡 → 修字闭环 → 拼装交付。常驻角色：**小码**（提问者，原名小柯，形象不变）× **波普**（解答者）。

**核心架构**：生成模型只画**无气泡、无文字的空场景**；气泡与文字全部由代码绘制（`draw_bubbles.py`）——几何确定性，溢出与字号漂移从构造上不可能发生。

**铁律**：
1. **没有定妆照，不许出格。**
2. **没有用户确认的文案，不许开画。**
3. **气泡与文字一律代码绘制**：出格提示词含「画面中绝对不出现任何对话气泡，不出现任何文字、字母、数字、符号」。
4. **文字 UNIFIED**：44px 优先档位（1080 宽成品坐标系，极端兜底 38/32/26）、微软雅黑 Bold、色 (35,35,40)、行距 1.3、边距 26px；说话人区分只靠气泡形状。
5. **品牌规范**：页脚唯一「出自公众号：码事漫谈」；无话数编号。
6. **表情逐格指定（R18）**：定妆照只锁造型，i2i 会把表情也锁死；分镜画面列必须为每个露脸角色逐格写明眉眼嘴形态，禁止全话同一张脸；面罩机器人用「蓝眼弯成月牙=笑、蓝眼明亮=自信」表达情绪。

## 目录结构（仓库相对路径）

```
stories/<作品>/storyboard.md      # 每话单一事实源（19 部已入库，可直接复现）
data/characters/<slug>/manifest.json  # 角色档案（COMIC_DATA 可改数据根）
assets/characters/                # 定妆照 + 表情/动作/转面三表
styles/manshi.yaml                # 画风 DNA / 气泡参数资产化（--style 消费）
output/long-form/                 # 19 部成品（发布即用，勿重刷）
scripts/                          # 全部工具脚本（见下）
```

## 流水线九步

1. **文案先行**：调研 → draft.md → 用户确认
2. **分镜锁定**：storyboard.md；每句 ≤22 字、无嵌套引号；画面列逐格写明露脸角色表情（铁律 6 / R18）
3. **定妆照**：新画风先 image-edit 转风 + 复核入库（register-ref --version manga）；出格提示词内联完整身份标记（R1）
4. **分镜→气泡配置**：`python scripts/parse_storyboard.py --storyboard stories/<作品>/storyboard.md --out bubbles.json`
5. **空场景出格**：`python scripts/gen_panel.py "<提示词>" --ref-local assets/characters/xiaoke-ref-manga.jpg --raw ... --fit ...`（本地图自动上传 OSS，R16：禁止直传本地路径）；批量用 `batch_parallel.py`（线程池+幂等跳过+逐格重试）
6. **质检**：识别接口查角色要素/水印/意外文字；出图后 `python scripts/lint.py --dir panels/ --bubbles bubbles.json`（越界/字号档位/要素三检查）
7. **代码绘气泡与文字**：`python scripts/draw_bubbles.py --bubbles bubbles.json --dir panels/ --style styles/manshi.yaml`（重采样 1080 宽 R12 → 画气泡 R15 → 文字推导高度 R14）
8. **修字闭环**（v8 下罕见）：`fix_panel.py` OCR 比对 → 整句重写 → 2 轮失败转 `patch_text.py`
9. **拼装交付**：`stack.py`（1080px PNG+JPG）+ verify 核验
10. **漫画博客**（可选）：`python scripts/gen_blog.py --story stories/<作品> --out-id <编号> --title "标题" --format panels|long`
    - 产出三版：`<out-id>.md`（MD 图文版）+ `<out-id>.html`（杂志风阅读版）+ `<out-id>-wechat.html`（公众号复制版：浏览器打开全选复制即用）
    - `--format panels` 单格图文交错（默认）｜ `--format long` 长图单图版
    - 正文用 `--blog-md` 传自己写的 Markdown（`## 小节` + `![配图说明](NN)` 数字占位，收尾格 99 除外的两位序号），缺省自动生成分镜问答骨架（发布前人工润色）
    - 出格后先跑 `scripts/strip_watermark.py --dirs stories/<作品>/panels --inplace` 清网关水印（R19）再入库

## 角色与定妆照

- 登记：`comic.py ensure-character --name 小码 --slug xiaoke --role 提问者 --markers "黑色短发，圆框眼镜，深灰连帽衫"`
- 出格提示词**内联完整身份标记**（只写"保持参考图造型"会丢眼镜/变色，R1）
- 角色持久变化 → register-ref 新建版本，绝不覆盖 base
- 角色三表（表情/动作/转面）用 `gen_sheets.py` 一键生成

## 画风 DNA（styles/manshi.yaml，--style 消费）

```
日式手绘漫画风格，铅笔质感利落手绘线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，米白纸感背景
```
空场景约束：无气泡无文字、上部留白（由调用方拼接，不写入 DNA）

## 构图与拼装

- 问答格 3:2、过场条格 21:9；小码恒左、波普恒右；气泡：小码=圆角矩形左下尾，波普=椭圆锯齿尾
- 长图 1080px 宽、GAP 28、页脚「出自公众号：码事漫谈」（唯一页脚内容，R11）
- 色彩：PAPER #fafaf7 / INK #1a1a1a / ACCENT #b8553a

## 根因登记表

见 [docs/ROOT-CAUSES.md](docs/ROOT-CAUSES.md)（R1-R18）。**新版本必须继承全部已修复行为；每次翻车必须新增条目。**

## 依赖与后端

- Pillow、numpy（requirements.txt）；微软雅黑（Windows 自带；Linux fonts-noto-cjk）
- 图像生成：`COMIC_SEEDREAM` / `COMIC_UPLOAD` 环境变量指向后端脚本，默认 AutoGLM Seedream；OpenAI 兼容 API / ComfyUI 适配见 [docs/INTEGRATION.md](docs/INTEGRATION.md)
- autoglm-image-edit（修字/转风）、autoglm-image-recognition（质检兜底）
