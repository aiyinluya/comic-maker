# 优化实施台账

> 首轮 12 项（2026-09-16「都做！」）+ 第二轮 P0-P2（同日「P0-P2全部都做！」，约束：12 部成品图不动，只优化项目本身）

## 第二轮（P0-P2 需求研究后全量）· 2026-09-16

- [x] **P0-1 复现包**：stories/ 12 部分镜入库（六话题从 MANIFEST 转换、夜话从脚本提取、幻觉/FDE 从旧 studio 抢救），parse_storyboard 12/12 解析通过
- [x] **P0-2 数据落点**：comic.py ROOT 从废弃的 comic-studio/ 改 data/（COMIC_DATA 可覆盖）；小码/波普档案迁移，refs 指向随仓库分发的定妆照
- [x] **P0-3 后端可配置**：gen_panel/fix_panel 的 5 个后端脚本路径全部环境变量化（COMIC_SEEDREAM/UPLOAD/RECOG/EDIT）
- [x] **P1-1 --style 接线**：draw_bubbles 消费 styles/manshi.yaml（PyYAML 优先 + 内置降级解析）；style=默认逐字节回归通过
- [x] **P1-2 npz 死代码**：ink_snap 快照写入移除，技能引擎同步（MD5 一致）
- [x] **P1-3 examples 清理**：5 个冒烟产物移出库 + gitignore（*_report.json / *.ink_snap.npz）
- [x] **P2-1 SKILL.md**：仓库版重写为 v2.8 九步流水线（原为 v2 七步 stack_fde 时代）
- [x] **P2-2 CONTRIBUTING + CHANGELOG**：新增（两条铁律 + v2.6-v2.8 日志）
- [x] **P2-3 CI 路径守护**：smoke.yml 增加硬编码扫描（上线即抓到 fix_panel 3 处漏网并修复）+ stories 全量解析步

## 第一轮（12 项）

### 1-4（原第一档）

- [x] **1. 单一事实源**：storyboard.md → 机器可读 → draw_bubbles 直读
  - 产出：scripts/parse_storyboard.py + draw_bubbles --bubbles 直读模式
  - 验证：RAG 分镜解析 7 格（键名/台词/站位全对）+ 重绘 13 气泡 44px 全档统一
- [x] **2. lint 内置质检**（v3 带宽阈值）
  - 产出：scripts/lint.py（BUBBLE-BOX / TIER-UNIFORM / PRESENCE 三检查）
  - 验证：夜话双篇 16/16 outside=0；RAG 重刷后 TIER-UNIFORM OK 44px ratio 1.00
- [x] **3. requirements.txt + GitHub Actions 冒烟**
  - 产出：requirements.txt、.github/workflows/smoke.yml（parse → draw → lint 三段）
  - 验证：本地全链路 PASS；已推送 b75b756
- [x] **4. 技能 v2.8 生效**（用户 15:35 批准 comic-explainer-20260915-5327f7ce07；apply 前先 revise 同步仓库现状：R1-R16、九步流程、44px 档位口径；技能版 draw_bubbles.py 与仓库版 MD5 一致）

### 5-8（原第二档）

- [x] **5. 表情/动作/转面三表**：assets/characters/sheet-{expressions,poses,turnaround}.jpg
  - 根因（R16）：seedream 直调不收本地参考图路径，必须经 upload-mix→OSS URL；scripts/gen_sheets.py 复用 gen_one 全通
  - 验证：三表目检双人造型全对（表情表 v2 重做：波普不再被画成趴肩道具）
- [x] **6. 文章 → 分镜自动转换**：scripts/article_to_storyboard.py
- [x] **7. 修字闭环**：scripts/fix_panel.py（OCR 比对 → 整句重写 → 2 轮失败转 patch_text）
- [x] **8. 定妆照本地化**：assets/characters/ + gen_panel --ref-local（base64 直传）

### 9-12（原第三档）

- [x] **9. README_en**：README.en.md（根因登记表为核心卖点）
- [x] **10. 12 部作品总索引页**：output/index.html（复用影廊 DNA）
- [x] **11. 并行出图**：gen_panel --parallel 3（线程池 + 逐格重试）
- [x] **12. 风格资产化**：styles/ 目录 + 风格 DNA 参数化（码事漫谈风为默认）

## 执行记录

- 2026-09-16（第二轮）：P0-P2 九项全部完成，验证见上；12 部成品图零接触
- 2026-09-16（第一轮）：#1/#2/#3 推送 b75b756；#6-#12 推送 509aa86；#5 三表 b799fbe；技能 v2.8 生效

- 2026-09-16：#1/#2/#3 完成并推送（b75b756）；#6-#12 完成并推送（509aa86）；#5 角色三表完成（gen_one 路径打通，R16 登记）
