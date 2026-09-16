# 优化实施计划 · 12 项全量

> 授权：李卓 2026-09-16「都做！」——按 第一档(1-4) → 第二档(5-8) → 第三档(9-12) 顺序执行
> 每项完成即在本文件勾选并留证据链接

## 第一档：现在就该做

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

## 第二档：短期值得

- [x] **5. 表情/动作/转面三表**：assets/characters/sheet-{expressions,poses,turnaround}.jpg
  - 根因（R16）：seedream 直调不收本地参考图路径，必须经 upload-mix→OSS URL；scripts/gen_sheets.py 复用 gen_one 全通
  - 验证：三表目检双人造型全对（表情表 v2 重做：波普不再被画成趴肩道具）
- [x] **6. 文章 → 分镜自动转换**：scripts/article_to_storyboard.py
- [x] **7. 修字闭环**：scripts/fix_panel.py（OCR 比对 → 整句重写 → 2 轮失败转 patch_text）
- [x] **8. 定妆照本地化**：assets/characters/ + gen_panel --ref-local（base64 直传）

## 第三档：长期方向

- [x] **9. README_en**：README.en.md（根因登记表为核心卖点）
- [x] **10. 12 部作品总索引页**：output/index.html（复用影廊 DNA）
- [x] **11. 并行出图**：gen_panel --parallel 3（线程池 + 逐格重试）
- [x] **12. 风格资产化**：styles/ 目录 + 风格 DNA 参数化（码事漫谈风为默认）

## 执行记录

- 2026-09-16：#1/#2/#3 完成并推送（b75b756）；#6-#12 完成并推送（509aa86）；#5 角色三表完成（gen_one 路径打通，R16 登记）
