#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_wechat20.py — 生成公众号可直接复制粘贴的第20话博客 HTML。

公众号编辑器约束：
- 粘贴时只保留内联 style，<style>/<class> 会被剥离 → 全文内联样式
- 本地/相对路径图片会被剥掉 → 图片先传 OSS，用公网 URL（粘贴时微信自动转存图床）
- 不用 <script>/<a> 外链按钮/id/伪类
输出：articles/20-zcode-incident-wechat.html
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
UP = r"C:\Users\liz-an\.openclaw-autoclaw\skills\autoglm-generate-image-seedream\upload-mix.py"
IMG_DIR = HERE / "articles/assets/20-zcode-incident"
CACHE = HERE / ".openclaw/tmp/oss_urls_20.json"
OUT = HERE / "articles/20-zcode-incident-wechat.html"


def upload(path):
    r = subprocess.run([sys.executable, UP, str(path)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"upload failed {path}: {r.stderr[-200:]}")
    return json.loads(r.stdout)["data"]["oss_info"][0]["oss_url"]


def upload_all():
    if CACHE.exists():
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        if len(cached) == 11:
            print("oss urls: cached")
            return cached
    urls = {}
    for i in range(1, 12):
        key = f"{i:02d}"
        f = IMG_DIR / f"{key}.jpg"
        urls[key] = upload(f)
        print(f"  uploaded {key} -> {urls[key][:60]}...", flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(urls, indent=2), encoding="utf-8")
    return urls


def img(urls, key, alt):
    u = urls[key]
    return (f'<img src="{u}" alt="{alt}" '
            f'style="width:100%;height:auto;display:block;border-radius:8px;" />')


def cap(text):
    return (f'<p style="text-align:center;font-size:12px;color:#8a857c;'
            f'margin:8px 0 24px;letter-spacing:0.05em;">{text}</p>')


def h2(text):
    return (f'<h2 style="font-size:20px;font-weight:700;color:#1a1a1a;'
            f'margin:42px 0 16px;line-height:1.4;">{text}</h2>')


def p(text):
    return (f'<p style="font-size:15px;line-height:1.85;color:#262421;'
            f'margin:0 0 18px;">{text}</p>')


def quote(text):
    return (f'<blockquote style="border-left:3px solid #b8553a;margin:22px 0;'
            f'padding:4px 0 4px 16px;font-size:15px;line-height:1.8;color:#8a857c;">{text}</blockquote>')


def orn():
    return ('<p style="text-align:center;color:#b8b4ac;font-size:14px;'
            'margin:34px 0;letter-spacing:6px;">· · ·</p>')


def build(urls):
    B = lambda t: f'<strong style="color:#1a1a1a;font-weight:700;">{t}</strong>'
    CODE = lambda t: (f'<code style="background:#f0ece5;color:#7a3d27;padding:2px 6px;'
                      f'border-radius:3px;font-size:13px;font-family:Consolas,monospace;">{t}</code>')
    parts = []
    # 头部
    parts.append('<p style="font-size:12px;color:#b8553a;letter-spacing:0.2em;'
                 'margin:0 0 14px;font-weight:600;">码事漫谈 · AI 科普第 20 话 · 2026-09-21</p>')
    parts.append('<h1 style="font-size:25px;font-weight:800;color:#1a1a1a;'
                 'line-height:1.35;margin:0 0 18px;">你的 Git 历史，是怎么'
                 '<span style="color:#b8553a;">「自己走出家门」</span>的</h1>')
    parts.append('<p style="font-size:15px;line-height:1.8;color:#6b6760;margin:0 0 26px;">'
                 '一个加密包裹，把 AI 编程工具的数据边界问题推上了台面。'
                 '三天，从曝光到开源——这篇用大白话把整件事讲清楚。</p>')
    parts.append('<hr style="border:none;border-top:1px solid #e7e5e0;margin:0 0 30px;" />')
    # 一
    parts.append(h2('9 月 18 日：从 700MB 开始的案中案'))
    parts.append(p('起因特别日常：一位开发者觉得磁盘吃紧，想弄明白 AI 编程工具 ZCode 的数据目录'
                   f'为什么占了 700MB。结果在 {CODE("~/.zcode/v2/checkpoints")} 底下，翻出一个 '
                   '313MB 的加密包。'))
    parts.append(p('顺着元数据往里查，事情大了：' +
                   B('只要账号登录着，这个工具就会把整个工作区——'
                     '代码、配置、甚至完整的 Git 提交历史——打包、加密、传到云上。') +
                   '默默地，不问你。'))
    parts.append(img(urls, "01", "小码举着手机惊呼"))
    parts.append(cap('9·18 那晚，开发者圈炸锅了'))
    parts.append(img(urls, "02", "挂锁图案的发光包裹"))
    parts.append(cap('清磁盘清出个 313MB 的加密包裹'))
    # 二
    parts.append(orn())
    parts.append(h2('包裹里装的是你的全部脚印'))
    parts.append(p(f'逆向分析的结论是：整个项目的快照。更扎心的是构成——上传量里 '
                   f'{B("86.6% 是 Git 历史")}。'))
    parts.append(p('Git 历史是什么？是这个项目从第一行代码到今天的全部脚印：每一版改动、每一条提交说明、'
                   '改过的文件名、删掉又没删干净的敏感信息。如果你曾经把 API 密钥提交进仓库、后来又删除——'
                   '那份密钥至今还躺在历史里。代码可以重写，历史没法伪造。'))
    parts.append(img(urls, "03", "包裹展开成发光的家谱树"))
    parts.append(cap('Git 历史像一棵家谱树，每个提交都是一圈年轮'))
    parts.append(quote('你的 Git 历史，比代码更懂你。'))
    parts.append(p(f'传到哪去了？云端对象存储，而且是{B("加密后上传")}——听起来是好事？坏在那把钥匙：'
                   '解密私钥只在服务端手里，你自己打不开自己代码的包裹。相当于把保险箱寄存在别人家，'
                   '锁是好的，但钥匙人家也有一把。'))
    parts.append(img(urls, "04", "传输线通向挂锁的云朵"))
    parts.append(cap('传输线通向云端，钥匙在服务端'))
    parts.append(p(f'删了不就完了？这才是最让人后背发凉的部分：{B("没用。")}'
                   '开发者第一次发现后直接删了待上传队列里的归档，半小时后客户端重新捕获、重新打包出一份'
                   '新的 313MB，重试计数器从 564 涨到 565。一个 10GB 的商业项目，剔除依赖后 345MB 的'
                   '核心资产，就这样被反复打包等待上传。这不是「功能」，这是一台永不停机的搬运机。'))
    parts.append(img(urls, "05", "撕碎又拼好的包裹和计数轮"))
    parts.append(cap('上传失败 564 次，还在锲而不舍地重试'))
    parts.append(p(f'把隐私开关关上呢？也关不掉。社区实测反馈，界面上的隐私开关关闭后，上传链路照样工作。'
                   f'{B("开关在界面上，腿长在后台")}——「默认开启」加上「关不彻底」，'
                   '才是这次事件真正刺痛人的地方。'))
    parts.append(img(urls, "06", "开关拨向关闭，背后还在爬线"))
    parts.append(cap('开关拨向关闭，后台的腿还在走'))
    # 三
    parts.append(orn())
    parts.append(h2('官方接招：致歉与三件套'))
    parts.append(p(f'9 月 18 日晚，官方回应来了：问题出在「代码库索引（Repo Wiki）」功能，上线初期'
                   f'{B("默认开启")}，生成 Wiki 页面时会触发仓库数据上传；云端生成后上传数据'
                   '「立即销毁、不会保存」；已修复，向受影响用户致歉。'))
    parts.append(img(urls, "07", "波普举着大报纸"))
    parts.append(cap('官方说明：索引功能默认开启闯的祸'))
    parts.append(p('补救是三件套：' +
                   B('承诺开源客户端代码、邀请第三方审查并公布进展、'
                     '全体用户补发一次周额度重置') +
                   '（当天就发了）。响应速度不算慢——当天曝光当天回应，三天后开源兑现。'))
    parts.append(img(urls, "08", "礼盒、放大镜、硬币三件套"))
    parts.append(cap('开源、第三方审计、补额度'))
    parts.append(p('但风波没有因为道歉结束，只是换了赛道。有企业正式发函，要求书面回应、'
                   '彻底删除数据及备份、提供完整数据处理清单——从舆论场进入合规场，追问还在继续。'))
    parts.append(img(urls, "09", "盖着红色印章的信函"))
    parts.append(cap('企业发函，期限十月十日'))
    # 四
    parts.append(orn())
    parts.append(h2('9 月 21 日：代码挂上了 GitHub'))
    parts.append(p('第三天，承诺兑现：ZCode 开源，代码放在 GitHub 上接受社区监督，'
                   '官方还专门感谢了发现问题的社区开发者。'))
    parts.append(img(urls, "10", "礼盒里升起发光的分支树"))
    parts.append(cap('三天后，代码真挂上了 GitHub'))
    parts.append(p('这事到这儿算是一个不错的落点。三个视角，各取一样东西带走：'))
    VP = lambda k, t: (f'<p style="border-top:1px solid #e7e5e0;margin:0;padding:13px 0;'
                       f'font-size:14px;line-height:1.8;color:#262421;">'
                       f'<span style="font-weight:700;color:#1a1a1a;">{k}</span>'
                       f'&nbsp;&nbsp;{t}</p>')
    parts.append(VP('如果你是用户', '「默认开启」的开关不等于你同意过；工具的每个数据出口，都值得亲手翻一翻。'))
    parts.append(VP('如果你是厂商', '信任修复的速度本身就是产品力：认错快、兑现快，损失才止得住。'))
    parts.append(VP('如果你看行业', 'AI 工具的数据边界需要行规：上传什么、存多久、钥匙在谁手里——默认答案应该是「本地」。'))
    parts.append('<p style="border-top:1px solid #e7e5e0;margin:0;"></p>')
    # 五
    parts.append(orn())
    parts.append(h2('给你的三步自查清单'))
    parts.append(p('如果你装过 ZCode 或任何同类 AI 编程工具，花两分钟做这三件事：'))
    STEP = lambda n, t: (f'<p style="margin:0 0 14px;font-size:15px;line-height:1.85;color:#262421;">'
                         f'<span style="font-family:Georgia,serif;font-weight:700;color:#b8553a;'
                         f'font-size:16px;margin-right:8px;">{n}</span>{t}</p>')
    parts.append(STEP('01', f'{B("看一眼数据目录")}：{CODE("~/.zcode/v2/checkpoints/")}（或同类目录）'
                            f'有没有异常大的 {CODE(".enc")} 文件——它的存在和大小，直接告诉你被打包过多少。'))
    parts.append(STEP('02', f'{B("翻一遍设置页")}：把所有带「上传 / 云端 / 索引 / 同步」字样的开关过一遍，'
                            '确认每一项都是你主动选择的默认值。'))
    parts.append(STEP('03', f'{B("评估敏感仓库的暴露面")}：轮换过期的密钥，清理 Git 历史里的旧凭证'
                            f'（{CODE("git filter-repo")} 或 BFG）。别把「曾经提交过」当成「没人看见过」。'))
    parts.append(img(urls, "11", "波普把分支树贴纸按在笔记本上"))
    parts.append(cap('把信任的年轮，贴回自己的机器上'))
    parts.append(quote('认错的速度，也是信任的一部分。<br/>工具会犯错，这难免；'
                       '真正拉开差距的，是犯错之后那张时间表。'))
    # 页脚
    parts.append('<p style="border-top:1px solid #e7e5e0;margin:34px 0 0;"></p>')
    parts.append('<p style="font-size:12px;line-height:1.8;color:#8a857c;margin:14px 0 0;">'
                 '事实依据：开发者 ferstar 的逆向复盘、OSCHINA、凤凰网科技、IT之家、华尔街见闻、'
                 '网易科技、DoNews 等公开报道（2026-09-18 至 09-21）；ZCode 已于 2026-09-21 开源'
                 '（github.com/zai-org/ZCode）。争议表述均采用「被曝 / 官方称」口径。</p>')
    parts.append('<p style="text-align:center;font-size:13px;font-weight:600;color:#1a1a1a;'
                 'margin:26px 0 6px;">出自公众号：码事漫谈</p>')
    return ('<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8" />'
            '<meta name="viewport" content="width=device-width, initial-scale=1" />'
            '<title>加密包裹：从曝光到开源的三天（公众号版）</title></head>'
            '<body style="margin:0;background:#ffffff;">'
            '<section style="max-width:578px;margin:0 auto;padding:36px 16px 40px;'
            'font-family:-apple-system-font,BlinkMacSystemFont,\'Helvetica Neue\','
            '\'PingFang SC\',\'Hiragino Sans GB\',\'Microsoft YaHei UI\',\'Microsoft YaHei\','
            'Arial,sans-serif;letter-spacing:0.5px;">'
            + "".join(parts) +
            '</section></body></html>')


def main():
    urls = upload_all()
    html = build(urls)
    OUT.write_text(html, encoding="utf-8")
    n_img = html.count("<img")
    bad = html.count("src=\"http") - n_img
    print(f"written {OUT.name}: {len(html)} bytes, {n_img} images (non-img http refs: {bad})")
    assert n_img == 11 and bad == 0, "image embedding check failed"
    print("OK")


if __name__ == "__main__":
    main()
