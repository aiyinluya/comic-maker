# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 精神，版本号对应 SKILL.md 的流水线版本。

## [Unreleased]

### 新增
- **第 19 部作品**《豆包 2.1 Pro：0915 新版强在哪？》（`stories/image-to-code/`，output 编号 19）：盘点 Doubao-Seed-2.1-pro 0915 新版四大升级（Agent 可信交付、多模态编程、多模态理解、图像/视频 Token 降 30%+）；8 格，其中 4 格空场景复用自该话 v1 草稿，复现驱动器 `gen_episode19.py`

### 修复
- **R17**（2026-09-17 登记）：气泡长句换行时句号/顿号被甩到行首（缺中文避头尾规则）→ `wrap()` 新增 `NO_LINE_START` 避头标点集，断行命中时换行点提前一个字；第 19 话重绘与 examples 全链路冒烟均 lint PASS
- **R18**（2026-09-17 登记）：i2i 定妆照把角色表情连同造型一起锁死，全话同一张担忧脸（收尾点赞仍皱眉）→ 分镜画面列逐格写明眉眼嘴表情、机器人用蓝眼弯月表达笑；第 19 话据此重出 6 格（01/02/04/05/07/08），03/06 保留，lint PASS

## [v2.8] · 2026-09-16

### 新增
- **stories/ 复现分镜包**：12 部已发布作品的 storyboard.md 全部入库（此前散落在 gitignore 区与仓库外目录），每份均可被 `parse_storyboard.py` 解析（12/12 通过）
- **风格资产化接线**：`draw_bubbles.py --style styles/manshi.yaml` ——文字色/行距/边距/字号档位/描边宽度可从 YAML 覆盖；无 PyYAML 时内置降级解析；参数与内置默认逐字节一致（回归验证）
- **数据目录可配置**：`comic.py` 数据落点从废弃的 `comic-studio/` 改为仓库内 `data/`，支持 `COMIC_DATA` 环境变量；小码/波普档案迁移完成（refs 指向随仓库分发的定妆照）
- **生成后端可配置**：`gen_panel.py` 的 seedream/upload 脚本路径支持 `COMIC_SEEDREAM` / `COMIC_UPLOAD` 环境变量覆盖
- **CONTRIBUTING.md**：两条铁律 + 本地冒烟步骤 + PR 自检清单
- **CI 防回归**：smoke.yml 增加硬编码绝对路径扫描（`C:\Users` / `/home/`）

### 修复
- **R15**（2026-09-16 登记）：椭圆气泡手绘感描边沿直线连接端点导致穿模 → `jitter_ellipse` 参数方程采样，抖动幅度 `decay=abs(sin(t))` 端点衰减到零
- **R16**（2026-09-16 登记）：seedream 直调传本地参考图路径全报 500（错误无区分度，误判为服务端故障半天）→ 本地图一律先经 upload-mix→OSS URL，`gen_one` 内固化该路径

### 清理
- `draw_bubbles.py` 移除 `ink_snap.npz` 快照写入（lint v3 已不消费的死代码）；examples 内 5 个冒烟产物移出库并 gitignore
- assets/characters/ 移除冒烟残留图与 .raw.jpg 过程图（gitignore 防回归）
- 文件名大小写规整：`optimizations.md`→`OPTIMIZATIONS.md`、articles 三件套大写（GitHub 链接大小写敏感）
- output/index.html 相对路径修复（36 引用零缺失）；posts 台账三件入库

## [v2.7] · 2026-09-15（b75b756 → 509aa86）

### 新增
- 单一事实源：`parse_storyboard.py`（分镜 md → 气泡配置）+ `draw_bubbles --bubbles` 直读，气泡高度由文字需求推导（44px 档统一）
- lint v3：BUBBLE-BOX（带宽阈值判强墨迹）/ TIER-UNIFORM / PRESENCE 三检查
- requirements.txt + GitHub Actions 冒烟（parse → draw → lint）
- `article_to_storyboard.py`：科普文章 → 分镜草稿
- `fix_panel.py`：修字闭环（OCR 比对 → 整句重写 → 2 轮失败转 patch_text）
- `gen_panel.py --ref-local`：本地定妆照自动上传 OSS；`gen_one` 并行安全原子函数
- `batch_parallel.py`：线程池并行出图（幂等跳过 + 逐格重试）
- `styles/manshi.yaml`：风格 DNA / 角色标记 / 气泡 / 拼装参数资产化
- 角色设定集三表（表情/动作/转面）入库 assets/characters/
- README.en.md 英文版；output/index.html 作品总索引页

### 变更
- output/process 分离：成品 output/long-form（12 部编号）+ panels/；过程图移出库

## [v2.6] · 2026-09-15（9785be4 及之前）

- 初始发布：v8 结构派架构（空场景出格 + 代码绘气泡）、R1-R14 根因登记表、12 部作品产出
