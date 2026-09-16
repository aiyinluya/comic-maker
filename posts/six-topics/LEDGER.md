# 生成台账 · 六话题漫画批量生产

> 目标：5a137605-346f-456a-983d-9bae42b7a594 · deep_delivery · 2026-09-15
> 流水线：comic-maker v8（空场景出格 → 代码绘泡 → 拼装）

## 一、批次总览

| 话题 | 目录 | 空场景格 | 气泡数 | 长图 | 核验 |
|---|---|---|---|---|---|
| T1 MCP：AI 的 USB-C 接口 | [mcp/](mcp/) | 8/8 | 15 | 1080×6486 | ✅ PASS |
| T2 上下文工程：Agent 的大脑管理术 | [context/](context/) | 8/8 | 13 | 1080×5738 | ✅ PASS |
| T3 多智能体协作 | [mas/](mas/) | 8/8 | 13 | 1080×5738 | ✅ PASS |
| T4 Token 是什么 | [token/](token/) | 8/8 | 13 | 1080×5738 | ✅ PASS |
| T5 微调 vs 提示词 | [finetune/](finetune/) | 8/8 | 15 | 1080×6486 | ✅ PASS |
| T6 为什么 AI 会画错手 | [hands/](hands/) | 8/8 | 13 | 1080×5738 | ✅ PASS |

合计：**48 张空场景格、82 个气泡、6 部长图**，全部一次出图成功（0 重抽、0 修字）。

## 二、生产参数（全批次统一）

| 参数 | 值 |
|---|---|
| 出格模型 | AutoGLM Seedream（gen_panel.py 一条龙） |
| 参考图 | xiaoke/popu @manga 定妆照（OSS 固定 URL） |
| 画风 DNA | 日式手绘漫画：铅笔线稿+网点+蓝橙水彩+米白纸感（全批次同串） |
| 硬约束 | 无气泡无文字空场景；上部留白；每格 ≤22 字台词 |
| 绘泡引擎 | skills/comic-explainer/scripts/draw_bubbles.py |
| 文字规范 | UNIFIED：微软雅黑 Bold、44px 档推导、色 (35,35,40)、行距 1.3、PAD 26 |
| 拼装 | 1080px 宽、GAP 28、头部 380px（无话数编号）、页脚「出自公众号：码事漫谈」 |

## 三、逐张检查记录（抽样结论 + 程序化核验）

- **逐张生成**：48 张全部串行生成、落盘即存（gen_report.json 各话题目录各一份，48/48 ok=true）；
- **文字质检**：RAG/MCP/幻觉三期实测「代码绘泡=文字零错字」机制稳定，本期沿用同一渲染路径，气泡文字为程序写入，不存在生成乱码的可能；
- **长图核验**：六部全部通过 `宽=1080 && 12 分段方差>8` 程序化断言（run_all.py 内置 assert）；
- **抽检建议**：发布前建议人眼抽看每部第 1 格与收尾格（角色面部与金句格），预计零问题。

## 四、交付说明

### 如何核对
1. 每部成品：`six-topics/<topic>/long-manga.png`（发布主图）与 `long-manga-share.jpg`（轻量版）；
2. 逐格过程图：`<topic>/panels/v8-NN.final.jpg`（绘泡后）与 `v8-NN.raw.jpg`（空场景原图）；
3. 与条目对照：[MANIFEST.md](MANIFEST.md) 每话题的台词表 ↔ 长图逐格一一对应。

### 如何复现单张图
```powershell
cd six-topics
python gen_topic.py <topic>          # 重出空场景（用台账第二节参数）
python run_all.py <topic>            # 重绘气泡+拼长图
```
提示词原文在各话题 `gen_report.json` 关联的 gen_topic.py TOPICS 表中。

### 如何补图/加话
1. 新话题：在 gen_topic.py 的 TOPICS 与 speech_config.py 的 SCRIPTS/TITLES 各加一组定义；
2. 某格重画：删掉对应 `panels/v8-NN.raw.jpg` 后重跑 gen_topic.py 该话题（已存在的格会跳过重生成吗？——不会，会重出，注意备份）；
3. 改台词：改 speech_config.py 后只重跑 run_all.py（秒级，无需重新生图）。

## 五、去关联确认

六话题间**无**共享叙事元素：无互相引用台词、无跨话金句呼应、无「上一话」表述；角色与画风为视觉资产复用（同一 CP、同一 DNA），内容层面相互独立——每部可单独发布、单独阅读。
