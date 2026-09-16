# stories/ — 12 部作品的复现分镜包

每部作品一个目录，`storyboard.md` 是该话的**单一事实源**：台词、画面描述、构图规范全部在此。

| 目录 | 作品 | 对应成品 |
|---|---|---|
| six-01-mcp | MCP：AI 的 USB-C 接口 | output/long-form/01-mcp |
| six-02-context | 上下文工程 | output/long-form/02-context-engineering |
| six-03-mas | 多智能体协作 | output/long-form/03-multi-agent |
| six-04-token | Token | output/long-form/04-token |
| six-05-finetune | 微调 vs 提示词 | output/long-form/05-finetune-vs-prompt |
| six-06-hands | 为什么 AI 会画错手 | output/long-form/06-hands |
| coder-rider | 从码农到骑手 | output/long-form/07-coder-rider |
| rag | RAG | output/long-form/08-rag |
| a-backup-life | 备份人生（原创短篇） | output/long-form/09-backup-life |
| b-missing-comments | 消失的注释（原创短篇） | output/long-form/10-missing-comments |
| hallucination | 幻觉 | output/long-form/11-hallucination |
| fde | FDE | output/long-form/12-fde |

## 从分镜复现一话

```bash
# 1. 分镜 → 气泡配置（单一事实源）
python scripts/parse_storyboard.py \
  --storyboard stories/six-01-mcp/storyboard.md --out bubbles.json

# 2. 逐格出空场景（提示词由分镜"画面"列 + 角色 DNA 组装）
python scripts/batch_parallel.py --topics mcp   # 六话题内置场景表

# 3. 画气泡与台词
python scripts/draw_bubbles.py --bubbles bubbles.json --dir panels/

# 4. 质检 + 拼装
python scripts/lint.py --dir panels/ --bubbles bubbles.json
python scripts/stack.py --config stack.json
```

注意：六话题的逐格气泡坐标另有精调版 `posts/six-topics/speech_config.py`
（含 y1 精调值）；storyboard.md 是无坐标版，坐标由引擎按文字推导（R14）。
