---
name: "comic-maker"
description: "生成公众号手绘长漫画：7+1 格问答流水线，定妆照一致性、逐字质检、修字与整泡重排、长图拼装。画漫画时用。"
---

# Comic Maker — 手绘长漫画流水线（v2）

把「一个知识点」变成「一部 7+1 格手绘长漫画」：分镜问答 → 角色一致性出格 → 逐字质检 → 修字/整泡重排 → 长图拼装 → 公众号交付。固定常驻角色 CP：小柯（提问者）× 波普（解答者），也可登记新角色。

**核心纪律**（借鉴 agent-mangaka-forge，MIT）：**没有定妆照，不许出格。**

## 目录结构（workspace 相对路径）

```
comic-studio/
  characters/<slug>/manifest.json   # 角色档案：name/slug/role/identity_markers/versions/refs
  characters/<slug>/ref.jpg         # 定妆照扁平版（base 版本）
  characters/<slug>/ref-manga.jpg   # 手绘漫画版（manga 版本）
  posts/<yyyy-mm-dd>-<slug>/
    storyboard.md                   # 分镜脚本（先行锁定）
    panels/panel-NN.raw.jpg         # 1600px 出格原图（按轮存档 *.fixed*.raw.jpg）
    panels/panel-NN.jpg             # 900px 终版
    long-manga.jpg                  # 拼装长图（标题区 + 全格）
    post.md / preview.html          # 公众号稿 / 阅读页
    panel.json                      # 页面登记
```

## 1. 流水线七步（长漫画标准流程）

1. **分镜先行**：拆 7 组一问一答（过场条格按需），写 `storyboard.md`。气泡文案纪律：每句 ≤22 字、不用嵌套引号、不用长句（引号嵌套是乱码重灾区）
2. **定妆照**：新画风先经 image-edit 转风 + 视觉复核后入库（register-ref --version manga）；已有版本直接复用
3. **出格**：`scripts/gen_panel.py "<提示词>" "<参考图URL>" --raw panels\panel-NN.raw.jpg --fit panels\panel-NN.jpg`（生成→解析→下载→900px 一条龙，URL 不经过对话层防截断）
4. **质检**：逐格视觉/识别复核——气泡逐字转录 vs 分镜目标句、角色要素（眼镜/卫衣/天线/徽章）、有无水印；多格可拼批发
5. **修字**：错字先走 image-edit 定点修字（只改气泡、其他不变）；**同一气泡连续 2 轮失败 → 立即转 `patch_text.py` 程序化整泡重排**（擦除气泡内文字 + 微软雅黑重排正确句，文字零错误）
6. **拼装**：`scripts/stack.py`（标题区 + 8 格竖拼 → long-manga.jpg）；程序化校验：分段方差 >8 无空白段、尺寸 900 宽
7. **交付**：post.md（分节导览+知识胶囊+互动）+ preview.html（阅读页）+ 台账（LEDGER.md）

## 2. 角色与定妆照

- 登记：`comic.py ensure-character --name 小柯 --slug xiaoke --role 提问者 --markers "..."`
- 出格提示词必须**内联完整身份标记**（不能只写"保持参考图造型"——实测会丢眼镜/变色）
- 角色任何持久变化（换装/进化）→ register-ref 新建版本，绝不覆盖 base
- 参考图上传：upload-mix.py 取公网 URL（OSS 链接长期有效，可复用）

## 3. 画风 DNA（提示词尾部必拼）

```
日式手绘漫画风格，铅笔质感的利落手绘线稿，灰色网点纸阴影，少量蓝色和橙色水彩淡彩点缀，米白纸感背景，中文对话气泡文字清晰锐利无错别字，除气泡外画面中不出现任何其他文字，画面干净无水印
```

## 4. 文字质检与修字决策表（实战校准）

| 情形 | 动作 |
|---|---|
| 出格后气泡错字/乱码 | image-edit 修字：整句重写失败气泡（成功率 > 单字微调）；禁用嵌套引号目标句 |
| 同一气泡修字 2 轮仍失败 | patch_text.py 整泡重排：气泡位置由识别接口口述定位，字体 msyhbd.ttc 自适应字号 |
| 视觉模型 500/超时 | 降级 autoglm-image-recognition（本地图先 upload-mix） |
| 衍字/标点风格项（半角？、省略句号） | 汉字全对即判通过；标点不阻塞交付 |
| 「AI 生成」水印 | 服务商合规标识，保留不抹除；发布文案注明"AI 辅助生成，人类逐字终审" |

## 5. 构图规范

- 问答格 3:2（900×~582）、过场条格 21:9（900×~386）、收尾格可 3:2 半身
- 小柯恒左、波普恒右；圆角矩形气泡=小柯，锯齿尾=波普
- 长图 900px 宽、GAP 26、标题区 300px（PAPER #fafaf7 / INK #1a1a1a / ACCENT #b8553a）

## 6. 发布链路

post.md → doocs/md 或 mdnice → 一键复制公众号（粘贴自动传图）。博客直接按格插图或用 long-manga.jpg。系列长图跨话复用 manga 版定妆照。

## 7. 依赖与工具

- autoglm-generate-image-seedream（文生图/图生图）、autoglm-image-edit（修字/转风）、autoglm-image-recognition（文字终验兜底）、upload-mix.py（参考图上传）
- scripts/：comic.py（档案/登记/台账）、gen_panel.py（出格一条龙）、patch_text.py（整泡重排）、stack.py（长图拼装）
- Pillow（必需）、numpy（patch_text.py）、微软雅黑字体（Windows 自带）
