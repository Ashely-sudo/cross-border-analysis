# -*- coding: utf-8 -*-
"""build_story_ppt.py — 生成《项目故事》图文 PPT（16:9）"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parents[1]
FIG = BASE / "reports" / "figures"
OUT = BASE / "presentation"
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY = RGBColor(0x26, 0x46, 0x53)
ACCENT = RGBColor(0x2A, 0x9D, 0x8F)
HOT = RGBColor(0xE7, 0x6F, 0x51)
GRAY = RGBColor(0x6C, 0x75, 0x7D)
LIGHT = RGBColor(0xF4, 0xF4, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def rect(slide, x, y, w, h, color, line=False):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if not line:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def textbox(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    return tb, tf


def set_run(r, size, color=PRIMARY, bold=False):
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold


def title(slide, kicker, text):
    rect(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.16), PRIMARY)
    _, tf = textbox(slide, Inches(0.7), Inches(0.45), Inches(12), Inches(1.0))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = kicker
    set_run(r, 13, ACCENT, True)
    p2 = tf.add_paragraph()
    r2 = p2.add_run(); r2.text = text
    set_run(r2, 30, PRIMARY, True)
    _, tf2 = textbox(slide, Inches(0.7), Inches(1.55), Inches(12), Inches(0.35))
    rect(slide, Inches(0.7), Inches(1.9), Inches(1.1), Inches(0.06), HOT)


def bullets(slide, items, x=0.7, y=2.15, w=6.6, h=5.0, size=16, gap=10):
    _, tf = textbox(slide, Inches(x), Inches(y), Inches(w), Inches(h))
    first = True
    for it in items:
        txt, lvl, bold = it[0], (it[1] if len(it) > 1 else 0), (it[2] if len(it) > 2 else False)
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = lvl
        p.space_after = Pt(gap)
        prefix = "" if lvl > 0 else ("• " if not txt.startswith("①") and not txt.startswith("②")
                                     and not txt.startswith("③") and not txt.startswith("④") else "")
        r = p.add_run(); r.text = prefix + txt
        set_run(r, size - lvl * 2, PRIMARY if lvl == 0 else GRAY, bold)
    return tf


def pic(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y),
                                    width=Inches(w) if w else None,
                                    height=Inches(h) if h else None)


def footer(slide, n):
    _, tf = textbox(slide, Inches(12.1), Inches(7.05), Inches(1.0), Inches(0.4))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = str(n)
    set_run(r, 12, GRAY)


# ---------------- S1 封面 ----------------
s = add_slide()
rect(s, Inches(0), Inches(0), prs.slide_width, prs.slide_height, PRIMARY)
rect(s, Inches(0.9), Inches(2.2), Inches(1.4), Inches(0.09), ACCENT)
_, tf = textbox(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(2.4))
p = tf.paragraphs[0]; r = p.add_run()
r.text = "中国跨境电商 / 出海赛道分析"
set_run(r, 46, WHITE, True)
p2 = tf.add_paragraph(); p2.space_before = Pt(12)
r2 = p2.add_run(); r2.text = "一个从亲身经历出发、用公开数据验证的行业研究"
set_run(r2, 20, LIGHT)
p3 = tf.add_paragraph(); p3.space_before = Pt(8)
r3 = p3.add_run(); r3.text = "5 家上市公司 · 现金流深挖 · 创业决策工作台"
set_run(r3, 15, RGBColor(0xA8, 0xDA, 0xDE))
_, tf2 = textbox(s, Inches(0.9), Inches(6.2), Inches(11), Inches(1.0))
for i, t in enumerate(["数据分析 / 商业分析 / 产品方向", "Xuefei Wang · 2026.09", "求职作品集（项目叙事版）"]):
    p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
    r = p.add_run(); r.text = t
    set_run(r, 14, RGBColor(0xCD, 0xD7, 0xDC))
footer(s, 1)

# ---------------- S2 我的起点 ----------------
s = add_slide()
title(s, "WHY · 起点", "我为什么做这个项目")
bullets(s, [
    ("上一份工作：亚马逊运营，卖 1000+ SKU 的工业阀门（品牌 U.S. Solid）", 0, False),
    ("职责覆盖：新品选品 / 定价 / 广告 / 库存，会为每个新品算 ROI", 1, False),
    ("一个让我困惑的现象：单 SKU 定价时 ROI 算得过来", 0, True),
    ("但公司整体却是“利润挺高、越来越不赚钱”", 1, False),
    ("我始终在想：钱到底被谁赚走了？", 0, True),
    ("是平台（佣金 / 仓储 / 广告）？还是我们自己的模式问题？", 1, False),
    ("于是决定：不套用现成数据集，用公开财报 + 官方数据，自己做一次“行业级”验证", 0, False),
], size=18)
footer(s, 2)

# ---------------- S3 我提出的问题 ----------------
s = add_slide()
title(s, "QUESTION · 问题", "我把困惑拆成四个可量化的问题")
qs = [
    ("① 赛道", "出海这门生意整体还有多大？还在涨吗？"),
    ("② 模式", "品牌 vs 铺货，谁更赚钱、更可持续？"),
    ("③ 市场/渠道", "北美 vs 欧洲怎么选？依赖平台是不是问题？"),
    ("④ 创业视角", "从活下来的公司反推：怎么起步才能活得久、何时该转型？"),
]
for i, (k, q) in enumerate(qs):
    col = i % 2
    row = i // 2
    x = 0.7 + col * 6.35
    y = 2.3 + row * 2.3
    rect(s, Inches(x), Inches(y), Inches(6.0), Inches(1.9), LIGHT)
    rect(s, Inches(x), Inches(y), Inches(0.12), Inches(1.9), ACCENT if i % 2 == 0 else HOT)
    _, tf = textbox(s, Inches(x + 0.45), Inches(y + 0.25), Inches(5.3), Inches(1.5))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = k
    set_run(r, 17, PRIMARY, True)
    p2 = tf.add_paragraph(); p2.space_before = Pt(6)
    r2 = p2.add_run(); r2.text = q
    set_run(r2, 15, GRAY)
footer(s, 3)

# ---------------- S4 我的方法 ----------------
s = add_slide()
title(s, "METHOD · 方法", "数据怎么来：全部公开、可核验")
bullets(s, [
    ("对象：5 家 A 股上市公司（安克创新 / 致欧科技 / 赛维时代 / 华凯易佰 / 吉宏股份）", 0, True),
    ("数据：多期财务摘要 + 主营构成 + 现金流量表/资产负债表（akshare 采集，与公开报道抽查核对）", 1, False),
    ("宏观：海关总署跨境电商进出口数据 + 行业公开统计", 1, False),
    ("三层框架：宏观(行业规模) → 中观(公司对比) → 微观(现金流验证)", 0, True),
    ("为什么是这 5 家：同属“跨境卖家”，覆盖 品牌×铺货 × 北美×欧洲×东南亚 × 平台×独立站", 0, False),
    ("合规：全部公开数据，无爬取；每个口径都记录在数据字典", 0, False),
], size=17)
footer(s, 4)

# ---------------- S5 宏观发现 ----------------
s = add_slide()
title(s, "FINDING ① · 赛道", "行业还在增长，但增速已换挡、格局极度分散")
bullets(s, [
    ("2025 终核 2.84 万亿元（出口 2.27 万亿），同比 +4.8%（前几年 +10~15%）", 0, True),
    ("美国仍是第一大出口目的国，占比约 36.2%", 0, False),
    ("5 家龙头 2025 营收合计 ≈ 668.8 亿 ≈ 出口额的 2.9%", 0, True),
    ("最大的安克 ≈ 1.3% —— 行业高度分散、长尾玩家众多", 1, False),
    ("含义：门槛低、进入多、竞争激烈，也解释了“起得快、倒得多”", 1, False),
], w=6.4, size=16)
pic(s, FIG / "m2_market_size.png", 7.3, 2.15, w=5.4)
pic(s, FIG / "m2_export_destination.png", 7.3, 4.6, w=5.4)
footer(s, 5)

# ---------------- S6 中观①模式 ----------------
s = add_slide()
title(s, "FINDING ② · 模式", "销售费用率是“模式”的分水岭")
bullets(s, [
    ("安克（品牌）：毛利 45% + 销售费用 22% → 净利 8.3%、营收 +23.5%", 0, True),
    ("赛维（铺货）：毛利 43% 不低，但销售费用 35% → 净利只剩 2.4%", 0, False),
    ("华凯易佰（铺货）：净利 1.6%、增速 +1.2% —— 增收不增利、增长见顶", 1, False),
    ("结论：毛利率高 ≠ 赚钱，费用结构才是模式分水岭", 0, True),
    ("品牌靠产品力与复购压低“流量税”，铺货靠买量，天然更重", 1, False),
], w=6.4, size=16)
pic(s, FIG / "m3_margin_2025.png", 7.3, 2.4, w=5.4)
footer(s, 6)

# ---------------- S7 中观②市场 ----------------
s = add_slide()
title(s, "FINDING ③ · 市场", "欧洲毛利更高，但天花板与本地化门槛并存")
bullets(s, [
    ("致欧是唯一披露欧美细分的公司：欧洲毛利率 36.4% > 美加 30.3%", 0, True),
    ("但致欧增速 +7.1%，明显慢于北美为主的安克（+23.5%）", 0, False),
    ("本地化门槛：VAT/EPR、多语言、产品标准", 1, False),
    ("我在阀门品类的亲历：美国 NPT 螺纹 vs 欧洲 G 螺纹 → 同一品类要重做产品线", 1, True),
    ("判断：美国走规模、欧洲赚毛利；先单点跑通再复制", 0, True),
], w=6.4, size=16)
pic(s, FIG / "m3_revenue.png", 7.3, 2.4, w=5.4)
footer(s, 7)

# ---------------- S8 中观③现金流 ----------------
s = add_slide()
title(s, "FINDING ④ · 现金流（我最意外的发现）", "利润 ≠ 现金：安克 2025 的“有利润没现金”")
bullets(s, [
    ("安克 2025：归母净利 25.5 亿，经营现金流仅 4.8 亿（OCF/净利 ≈ 0.19）", 0, True),
    ("追查现金流量表调节附表：存货增加占用约 20 亿、应收增加约 6.6 亿", 0, False),
    ("资产负债表交叉验证：存货余额 24 → 32 → 50 亿", 1, False),
    ("这就是我上一份工作的困惑的“上市公司版”：利润被货和应收占住了", 0, True),
    ("结论：规模扩张期，经营现金流才是生命线", 1, False),
], w=6.4, size=16)
pic(s, FIG / "m3b_anker_cashflow.png", 7.3, 2.4, w=5.4)
footer(s, 8)

# ---------------- S9 我怎么做验证 ----------------
s = add_slide()
title(s, "VALIDATION · 验证", "结论之前，我先做三件事")
bullets(s, [
    ("① 数据抽查：安克 2025 营收 305.1 亿 与公开报道核对一致", 0, False),
    ("② 交叉验证：调节表（存货 -20 亿）↔ 资产负债表（存货 +17.6 亿）互相印证", 0, False),
    ("③ 主动声明局限：上市公司是幸存者（幸存者偏差）；欧美细分只有致欧披露；吉宏含包装需看分部", 0, False),
    ("结论只到证据能到的地方：安克备货是主动还是被动？→ 标“待年报附注确认”，不下定论", 0, True),
], size=17)
footer(s, 9)

# ---------------- S10 结论 ----------------
s = add_slide()
title(s, "CONCLUSION · 结论", "四个可以带走、也能被追问的判断")
concl = [
    ("① 模式", "销售费用率是分水岭：品牌 22% vs 铺货 35%，毛利率高≠赚钱"),
    ("② 市场", "美国走规模、欧洲赚毛利；本地化是欧洲的隐形门槛"),
    ("③ 现金流", "利润≠现金：备货与回款是跨境电商的生死线"),
    ("④ 格局", "龙头集中度 <3%：细分做深（如长尾全品类）是中小卖家的路"),
]
for i, (k, v) in enumerate(concl):
    y = 2.3 + i * 1.15
    rect(s, Inches(0.7), Inches(y), Inches(0.9), Inches(0.95), PRIMARY)
    _, tf = textbox(s, Inches(0.7), Inches(y + 0.2), Inches(0.9), Inches(0.6))
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k
    set_run(r, 16, WHITE, True)
    _, tf2 = textbox(s, Inches(1.85), Inches(y + 0.12), Inches(10.8), Inches(0.85))
    p2 = tf2.paragraphs[0]; p2.anchor = MSO_ANCHOR.MIDDLE
    r2 = p2.add_run(); r2.text = v
    set_run(r2, 16, PRIMARY, False)
footer(s, 10)

# ---------------- S11 工具 ----------------
s = add_slide()
title(s, "PRODUCTIZE · 落地", "把结论做成能用的工具：创业决策工作台")
tools = [
    ("P1 单位经济测算", "单件赚不赚钱？盈亏平衡 ACOS；Case Pack 双方案对比"),
    ("P2 选品类助手", "单位经济可行性 + 风险规则 → 能不能做"),
    ("P3 市场选择器", "规模 / 毛利 / 竞争 / 本地化 加权 → 先做哪个市场"),
    ("P4 经营健康体检", "输入你的指标 → 对标 5 家上市公司 → 危险信号 + 阶段建议"),
]
for i, (k, v) in enumerate(tools):
    y = 2.3 + i * 1.15
    rect(s, Inches(0.7), Inches(y), Inches(5.2), Inches(0.95), LIGHT)
    _, tf = textbox(s, Inches(0.9), Inches(y + 0.1), Inches(4.8), Inches(0.8))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = k
    set_run(r, 16, ACCENT, True)
    _, tf2 = textbox(s, Inches(6.2), Inches(y + 0.08), Inches(6.5), Inches(0.9))
    p2 = tf2.paragraphs[0]; p2.anchor = MSO_ANCHOR.MIDDLE
    r2 = p2.add_run(); r2.text = v
    set_run(r2, 15, GRAY)
_, tfx = textbox(s, Inches(0.7), Inches(6.9), Inches(12), Inches(0.5))
px = tfx.paragraphs[0]; rx = px.add_run()
rx.text = "从“看报表”到“能决策”：每一页都基于 5 家公司的真实财务基准"
set_run(rx, 13, HOT, True)
footer(s, 11)

# ---------------- S12 复盘 ----------------
s = add_slide()
title(s, "REFLECTION · 复盘", "做得好的 & 下次能更好的")
bullets(s, [
    ("做得好的：从亲身困惑出发 / 三层框架 / 现金流深挖 / 把结论做成工具", 0, True),
    ("不足与边界：销售费用没拆“广告 vs 佣金”；缺 2026H1 与关税影响；供应商报价、需求热度这类私有数据只能给框架", 0, False),
    ("如果重来：会更早看现金流量表；先用少量行业访谈补“定性”，再用数据验证“定量”", 0, True),
    ("可迁移：这套“提问 → 取数 → 验证 → 结论 → 工具化”的流程，适用于任何行业研究 / 商业分析", 0, False),
], size=17)
footer(s, 12)

# ---------------- S13 收尾 ----------------
s = add_slide()
rect(s, Inches(0), Inches(0), prs.slide_width, prs.slide_height, PRIMARY)
_, tf = textbox(s, Inches(1.2), Inches(2.0), Inches(11), Inches(3.4))
lines = [
    ("数据之外，我更想让你看到的，是我的思考方式：", 22, LIGHT, True),
    ("会提问 —— 从一句“公司怎么不赚钱”出发", 18, WHITE, False),
    ("会验证 —— 公开数据也能做严谨的研究：口径、抽查、交叉验证、写清局限", 18, WHITE, False),
    ("会落地 —— 把结论做成能用的工具，而不只是报告", 18, WHITE, False),
    ("会复盘 —— 知道自己哪里好、哪里还能更好", 18, WHITE, False),
]
first = True
for t, sz, col, b in lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    p.space_after = Pt(10)
    r = p.add_run(); r.text = t
    set_run(r, sz, col, b)
_, tf2 = textbox(s, Inches(1.2), Inches(6.1), Inches(11), Inches(1.0))
p = tf2.paragraphs[0]; r = p.add_run()
r.text = "Xuefei Wang · 2026.09 · 联系与更多材料见简历"
set_run(r, 14, RGBColor(0xCD, 0xD7, 0xDC))
footer(s, 13)

out = OUT / "中国跨境电商出海赛道分析-项目故事.pptx"
prs.save(out)
print("已生成:", out, "| 页数:", len(prs.slides._sldIdLst))
