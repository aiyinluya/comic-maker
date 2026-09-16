# 优化实施计划 · 12 项全量

> 授权：李卓 2026-09-16「都做！」——按 第一档(1-4) → 第二档(5-8) → 第三档(9-12) 顺序执行
> 每项完成即在本文件勾选并留证据链接

## 第一档：现在就该做

- [ ] **1. 单一事实源**：storyboard.md → 机器可读 → draw_bubbles 直接读取
  - 产出：scripts/parse_storyboard.py + 改造 draw_bubbles.py 支持 --storyboard
  - 验收：任一话从 storyboard.md 一键重绘，无需手工抄台词
- [ ] **2. comic.py lint 内置质检**：台词比对 + 气泡边界 + 字号统一三合一
  - 产出：scripts/lint.py（OCR 接口可选，默认几何断言）
  - 验收：对已完成 12 部跑 lint，输出台账
- [ ] **3. requirements.txt + GitHub Actions 冒烟**
  - 产出：requirements.txt、.github/workflows/smoke.yml（跑 examples）
- [ ] **4. 技能 v2.7 批准**（用户动作：回复「批准 comic-explainer-20260915-5327f7ce07」）
  - 本文件只能提醒，无法代批

## 第二档：短期值得

- [ ] **5. 表情/姿态表**：小码 & 波普五件套（正面/侧面/背面/表情表/动作表）生成 + 入库 v2 版本
- [ ] **6. 文章 → 分镜自动转换**：scripts/article_to_storyboard.py（LLM 或规则模板产出分镜草稿）
- [ ] **7. fix_panel.py 修字闭环**：OCR 比对 → 整句重写 → 2 轮失败转 patch_text，全程落台账
- [ ] **8. 参考图本地化**：定妆照入库仓库 assets/characters/，gen_panel 支持 --ref-local（base64 直传）

## 第三档：长期方向

- [ ] **9. README_en**：英文版 README（根因登记表为核心卖点）
- [ ] **10. 12 部作品总索引页**：GitHub Pages 风格 index（复用夜话影廊 DNA）
- [ ] **11. 并行出图**：gen_panel 并发 3-4 路（线程池 + 重试）
- [ ] **12. 风格资产化**：styles/ 目录 + 风格 DNA 参数化（码事漫谈风为默认）

## 执行记录

（每完成一项在此追加：日期、改动文件、验证结果）
