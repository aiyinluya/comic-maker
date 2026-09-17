# Contributing to comic-maker

感谢有兴趣改进这个项目。先读 [README](README.md) 和 [docs/ROOT-CAUSES.md](docs/ROOT-CAUSES.md)——后者是这个仓库最重要的一份文件。

## 两条铁律（违反的 PR 会被直接关闭）

1. **文字样式只在一处定义**。气泡的字体、字号、颜色、行距只出现在 `scripts/draw_bubbles.py` 的常量区（或 `styles/*.yaml`，经 `--style` 加载）。任何绕过常量表私设样式的改动都会被拒绝（R14 教训）。
2. **翻车必须登记**。你的修复如果源自一次真实事故，请在 ROOT-CAUSES.md 加一条：症状 / 根因 / 解法 / 代码落点。改代码不登记等于没修。

## 本地开发

```bash
pip install -r requirements.txt
# Windows 需要 CJK 字体（微软雅黑自带）；Linux 安装 fonts-noto-cjk

# 全链路冒烟（解析 → 绘制 → 质检）
python scripts/parse_storyboard.py --storyboard examples/example-storyboard.md --out examples/bubbles.parsed.json
python scripts/draw_bubbles.py --bubbles examples/bubbles.parsed.json --dir examples/assets
python scripts/lint.py --dir examples/assets --bubbles examples/bubbles.parsed.json
```

GitHub Actions 在每次 push/PR 时跑同一套冒烟（`.github/workflows/smoke.yml`）。

## 约定

- **成品不重刷**：`output/long-form/` 下的成品是发布物，改动只影响未来作品。不要提交重刷成品图的 PR。
- **表情逐格指定（R18）**：定妆照只锁造型，i2i 会把表情也锁死；分镜画面列必须为每个露脸角色逐格写明眉眼嘴形态，禁止全话同一张脸。面罩机器人用「蓝眼弯成月牙=笑、蓝眼明亮=自信」表达情绪。
- **风格参数化**：改风格先改 `styles/manshi.yaml`，确认 `--style` 加载后的输出与预期一致再动代码。
- **后端无关**：图像生成相关的路径一律走环境变量（`COMIC_SEEDREAM` / `COMIC_UPLOAD`），不许硬编码。
- **提交信息**：一行主题，说清「改了什么、为什么」；涉及根因的引用编号（如 `R16`）。

## 提交 PR 前自检

- [ ] 全链路冒烟本地通过
- [ ] 没有引入新的硬编码绝对路径（CI 会扫描）
- [ ] 分镜画面列逐格写了露脸角色的表情（R18），没有全话同一张脸
- [ ] 如果修了一个 bug：ROOT-CAUSES.md 有对应条目
- [ ] 如果改了绘制逻辑：示例输出（examples/）重新生成且 lint PASS

## License

提交即表示同意代码以 [MIT](LICENSE) 发布。
