# 角色表情库使用说明

> **v2（2026-10-12）**：小码 + 波普 × **16 表情全量入库**（QC 通过 + OCR 复核）。
> v2 变化：头部大特写构图（脸部信号更强）、16 表情规范短语漫画式夸张化、
> 统一 3/4 视角+浅米白背景模板（16 张互相同源）。
> 实战 demo：frown 喂真实分镜，表情落地 8/10、身份保持 9.5/10。

## 这是什么

每个角色 × N 个基准表情，各存一张独立 JPG（身份特征已内嵌）。
单格生图时 `--ref-local` 直指**表情图**即可，不用再靠一句「惊讶看着」碰运气；
提示词同步引用 meta.json 里的**规范短语**（canon phrase），全流水线统一口径。

```
assets/characters/<char>/expressions/
├── neutral.jpg / neutral.raw.jpg     成品 900px / 生成原图 2048px
├── surprised.jpg …
└── meta.json                          规范短语 + sanity 判据 + QC 状态
```

## 三条命令

```powershell
# 1) 批量生成（复用 gen_panel 链路：定妆照→OSS→seedream→900px）
python scripts/gen_expressions.py --char xiaoke --only neutral,surprised
python scripts/gen_expressions.py --char popu            # 全 8 表情

# 2) 清水印（R19 管线；方图务必加宽窗 + 低阈值）
python scripts/strip_watermark.py --dirs assets/characters/xiaoke/expressions `
    --pattern '*.raw.jpg' --inplace --win '1400,1700,2048,2048' --th 1.2

# 3) 从干净 raw 重出成品（清完水印后必须重出，成品不是裁剪而是重采样）
python scripts/gen_expressions.py --char xiaoke --refit

# 登记 / 补登记（含 QC 状态与规范短语；幂等）
python ..\skills\comic-explainer\scripts\comic.py register-expression `
    --slug xiaoke --expression frown --image assets/characters/xiaoke/expressions/frown.jpg `
    --phrase "眉头紧锁下压，嘴角向下" --qc "pass: ..."
```

## 在单格生图里用

```powershell
python scripts/gen_panel.py "……小码（参考图表情：皱眉，眉头紧锁下压，嘴角向下）指着屏幕……" `
    --ref-local assets/characters/xiaoke/expressions/frown.jpg `
    --raw posts/<slug>/panels/v8-01.raw.jpg --fit posts/<slug>/panels/v8-01.jpg
```

要点：
- **参考图就是表情图**——身份已内嵌，无需再叠定妆照；
- 提示词里引用 meta.json 的 phrase，别自由发挥措辞；
- 分镜阶段就给每格标表情键，治「整话惊讶」的单调病。

## 8 个基准表情

| 键 | 一句话 | 适用场景 |
|---|---|---|
| neutral | 平静正视 | 旁白、过渡格 |
| surprised | 瞪眼瞳孔缩小 | 听到新信息 |
| frown | 川字眉压嘴角 | 质疑、看到问题 |
| smile | 闭嘴月牙眼微笑 | 认可、收尾 |
| laugh | 仰头大笑露齿 | 梗的爆点 |
| think | 托腮斜上看 | 思考、铺垫 |
| shock | O 形嘴圆凸眼 | 反转、震惊 |
| speechless | 死鱼眼无奈 | 吐槽、无语 |
| confused | 歪头不对称眉 | 困惑、没听懂 |
| smug | 单侧坏笑半眯眼 | 得意、小聪明 |
| sad | 八字泪眉下瘪嘴 | 失落、认错 |
| worried | 皱眉圆眼汗珠 | 担忧、忐忑 |
| angry | 倒八字咬牙怒视 | 愤怒、爆发 |
| excited | 放光圆眼露齿 | 兴奋、种草 |
| tired | 垂眼黑眼圈哈欠 | 疲惫、加班 |
| focus | 锐利直视抿嘴 | 专注、动手 |

## 已知坑（都踩过，别再踩）

1. **gen_one 不转本地路径**：参考图必须是 OSS URL，gen_expressions 已内置 `local_ref_to_url`；直接调 gen_panel 走 `--ref-local`。
2. **方图水印窗口更宽**：`strip_watermark` 默认窗口按 2496×1664 横版缩放，2048 方图上「f」会漏——方图必须 `--win '1400,1700,2048,2048' --th 1.2`。
3. **掩膜缓存键**：改窗口后如不生效，删 `assets/wm-mask-*.png` 缓存（现版本 --win 已纳入缓存键）。
4. **清完水印必须 --refit**：成品 900px 是从 raw 重采样的，直接改成品会二次压缩。
5. **QC 双检**：身份特征（眼镜/面罩）+ 目标表情，先视觉后 OCR 复核角落；VLM 看到提示词里的「水印」二字会有偏置虚警，以放大裁片 + OCR 为准。

## 扩库

加新角色：`comic.py ensure-character` → `register-ref` 登记定妆照 → 在 `gen_expressions.py` 的 `DEFAULT_REFS`/`IDENTITY` 补两行 → 批量生成 → QC → 登记。
加新表情：`EXPRESSIONS` 表加一项（phrase + sanity）→ `--only` 生成该键 → QC → 登记。
