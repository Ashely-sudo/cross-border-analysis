# -*- coding: utf-8 -*-
"""build_story_ppt.py — 生成《项目故事》图文 PPT v2（16:9，清爽国际咨询风）"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parents[1]
FIG = BASE / "reports" / "figures"
OUT = BASE / "presentation"
OUT.mkdir(parents=True, exist_ok=True)

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1B, 0x24, 0x30)
SUB = RGBColor(0x5B, 0x64, 0x70)
ACCENT = RGBColor(0x2F, 0x5A, 0xA8)
AMBER = RGBColor(0xC9, 0x7B, 0x1E)
PANEL = RGBColor(0xF3, 0xF5, 0xF8)
LINE = RGBColor(0xD9, 0xDE, 0xE6)
FONT = "微软雅黑"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def rect(slide, x, y, w, h, color=WHITE, line_color=None, line_w=0.75):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def tb(slide, x, y, w, h):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    return box, tf


def set_run(r, size, color=INK, bold=False):
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold


def header(slide, kicker, title, title_size=27):
    rect(slide, Inches(0.7), Inches(0.55), Inches(0.09), Inches(0.62), ACCENT)
    _, tf = tb(slide, Inches(0.98), Inches(0.5), Inches(11.6), Inches(1.2))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = kicker
    set_run(r, 11.5, ACCENT, True)
    p2 = tf.add_paragraph(); p2.space_before = Pt(4)
    r2 = p2.add_run(); r2.text = title
    set_run(r2, title_size, INK, True)


def bullets(slide, items, x=0.7, y=2.05, w=6.6, h=5.0, size=15.5, gap=12):
    _, tf = tb(slide, Inches(x), Inches(y), Inches(w), Inches(h))
    first = True
    for it in items:
        txt = it[0]
        lvl = it[1] if len(it) > 1 else 0
        bold = it[2] if len(it) > 2 else False
        col = it[3] if len(it) > 3 else None
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = lvl
        p.space_after = Pt(gap)
        mark = "— " if lvl > 0 else ("▪ " if not txt.startswith(("①", "②", "③", "④")) else "")
        r = p.add_run(); r.text = mark + txt
        set_run(r, size - lvl * 1.5, col or (SUB if lvl > 0 else INK), bold)
    return tf


def pic(slide, path, x, y, w):
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w))


def footer(slide, n, total=16):
    _, tf = tb(slide, Inches(0.7), Inches(7.05), Inches(4), Inches(0.35))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "Xuefei Wang · 2026"
    set_run(r, 9.5, SUB)
    _, tf2 = tb(slide, Inches(12.0), Inches(7.05), Inches(0.7), Inches(0.35))
    p2 = tf2.paragraphs[0]; p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run(); r2.text = f"{n:02d} / {total}"
    set_run(r2, 9.5, SUB)


def card(slide, x, y, w, h, title_txt, body_txt, accent=ACCENT, t_size=14, b_size=11.5):
    rect(slide, Inches(x), Inches(y), Inches(w), Inches(h), PANEL)
    rect(slide, Inches(x), Inches(y), Inches(0.07), Inches(h), accent)
    _, tf = tb(slide, Inches(x + 0.25), Inches(y + 0.16), Inches(w - 0.45), Inches(h - 0.3))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = title_txt
    set_run(r, t_size, INK, True)
    p2 = tf.add_paragraph(); p2.space_before = Pt(5)
    r2 = p2.add_run(); r2.text = body_txt
    set_run(r2, b_size, SUB)


# ---------------- S1 封面 ----------------
s = add_slide()
rect(s, Inches(0), Inches(0), Inches(0.22), prs.slide_height, ACCENT)
_, tf = tb(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(3.2))
p = tf.paragraphs[0]; r = p.add_run(); r.text = "中国跨境电商 / 出海赛道分析"
set_run(r, 44, INK, True)
p2 = tf.add_paragraph(); p2.space_before = Pt(14)
r2 = p2.add_run(); r2.text = "一个从亲身经历出发、用公开数据验证的行业研究"
set_run(r2, 19, SUB)
p3 = tf.add_paragraph(); p3.space_before = Pt(10)
r3 = p3.add_run(); r3.text = "5 家上市公司 · 精品 vs 铺货 · 现金流深挖 · 创业决策工作台"
set_run(r3, 13.5, ACCENT)
rect(s, Inches(1.0), Inches(4.05), Inches(1.5), Inches(0.045), AMBER)
_, tf4 = tb(s, Inches(1.0), Inches(6.1), Inches(11), Inches(1.0))
for i, t in enumerate(["Xuefei Wang  ·  数据分析 / 商业分析 / 产品方向", "2026 秋招  ·  项目叙事版"]):
    pp = tf4.paragraphs[0] if i == 0 else tf4.add_paragraph()
    pp.space_after = Pt(4)
    rr = pp.add_run(); rr.text = t
    set_run(rr, 13, SUB)

# ---------------- S2 我的起点 ----------------
s = add_slide()
header(s, "WHY · 起点", "我为什么做这个项目")
bullets(s, [
    ('我上一份工作在一家做自有品牌出海的公司做亚马逊运营，卖阀门/管件、实验室仪器、封口机这类偏专业的产品，在售 SKU 超过 1000 个。', 0, False),
    ('经营上我们把品类做深做全：同一类阀门按通径、材质和螺纹标准展开，两通/三通、1/2 到 2 英寸、不锈钢/黄铜/PVC 都会配齐。客户多是工程师、实验室或做自动化改造的人，下单前会核对型号参数。', 0, False),
    ('我负责日常运营，也参与新品选品。给新品定价前先算单件 ROI，再决定广告投入和备货节奏。', 0, False),
    ('让我一直没想通的是：单个 SKU 怎么算都能盈利，公司整体却没以前那么赚钱了。这只是我听来的说法，未必准确，可能也和广告投放的调整有关。', 0, False),
    ('我怀疑问题出在两处：平台拿走的佣金、仓储和广告费用，或是我们这种把 SKU 铺得很开的打法本身有问题。', 0, False),
    ('为了解决自己的疑惑，我决定用数据验证：不用现成数据集，用上市公司财报和海关官方数据，从行业层面重新分析。', 0, False),
], w=11.7, size=16, gap=15)
footer(s, 2)

# ---------------- S3 问题 ----------------
s = add_slide()
header(s, "QUESTION · 问题", "我把困惑拆成四个可量化的问题")
qs = [
    ("① 赛道", "出海这门生意整体还有多大？还在涨吗？"),
    ("② 模式", "精品 vs 铺货，谁更赚钱、更可持续？"),
    ("③ 市场/渠道", "北美 vs 欧洲怎么选？依赖平台是不是问题？"),
    ("④ 创业视角", "从活下来的公司反推：怎么起步才能活得久、何时该转型？"),
]
for i, (k, q) in enumerate(qs):
    x = 0.7 + (i % 2) * 6.15
    y = 2.15 + (i // 2) * 2.2
    card(s, x, y, 5.85, 1.85, k, q, ACCENT if i % 2 == 0 else AMBER, t_size=15, b_size=12.5)
footer(s, 3)

# ---------------- S4 方法 ----------------
s = add_slide()
header(s, "METHOD · 方法", "数据怎么来：全部公开、可核验")
bullets(s, [
    ("对象：5 家 A 股上市公司（安克创新 / 致欧科技 / 赛维时代 / 华凯易佰 / 吉宏股份）", 0, True),
    ("数据：多期财务摘要 + 主营构成 + 现金流量表/资产负债表（akshare 采集，与公开报道抽查核对）", 1, False),
    ("宏观：海关总署跨境电商进出口数据 + 行业公开统计", 1, False),
    ("三层框架：宏观（行业规模）→ 中观（公司对比）→ 微观（现金流验证）", 0, True),
    ("为什么是这 5 家：同属“跨境卖家”，覆盖 精品/铺货/长尾 × 北美/欧洲/东南亚 × 平台/独立站", 0, False),
    ("合规：全部公开数据，无爬取；每个口径都记录在数据字典", 0, False),
], size=16)
footer(s, 4)

# ---------------- S5 宏观 ----------------
s = add_slide()
header(s, "FINDING ① · 赛道", "行业还在增长，但增速换挡、格局极度分散")
bullets(s, [
    ("2025 终核 2.84 万亿元（出口 2.27 万亿），同比 +4.8%（前几年 +10~15%）", 0, True),
    ("美国仍是第一大出口目的国，占比约 36.2%", 0, False),
    ("5 家龙头 2025 营收合计 ≈ 668.8 亿 ≈ 出口额的 2.9%", 0, True),
    ("最大的安克 ≈ 1.3% —— 行业高度分散、长尾玩家众多", 1, False),
    ("含义：门槛低、进入多、竞争激烈，也解释“起得快、倒得多”", 1, False),
], w=6.2, size=15)
pic(s, FIG / "m2_market_size.png", 7.1, 2.0, 5.6)
pic(s, FIG / "m2_export_destination.png", 7.1, 4.55, 5.6)
footer(s, 5)

# ---------------- S6 进入与退出 ----------------
s = add_slide()
header(s, "FINDING ① · 赛道", "支撑数据：这个行业进得有多快、洗牌有多快")
blk6 = [
    ("体量 · 官方口径", "跨境电商主体超 12 万家（约占近 70 万家有进出口记录经营主体的 1/6）；2024 进出口 2.63 万亿、+10.8%。来源：商务部 / 经济日报 2025-02", ACCENT),
    ("新增进入 ① · 企查查", "2023 注册 5,818 家（+44%）→ 2024 注册 8,598 家（+47%）→ 2025 前 4 月 5,080 家（+173%）；现存 2.89 万家（2025-05）", ACCENT),
    ("新增进入 ② · 天眼查", "现存超 3.4 万家（2025-09）；2024 新增 7,000+（较 2023 约 +50%）；2025 已新增 1.3 万+；成立不足 1 年的企业占 46.7%", AMBER),
    ("退出 · 可见案例", "网经社“死亡名单”：2022 年 31 家 → 2023 年 11 家 → 2024 年 50 家（+354.5%）。仅统计有知名度的倒闭/关停，不是退出总数", AMBER),
]
for i, (k, v, ac) in enumerate(blk6):
    x = 0.7 + (i % 2) * 6.15
    y = 2.05 + (i // 2) * 2.25
    card(s, x, y, 5.85, 2.0, k, v, ac, t_size=14.5, b_size=11.5)
_, tf = tb(s, Inches(0.7), Inches(6.55), Inches(12), Inches(0.6))
p = tf.paragraphs[0]; r = p.add_run()
r.text = "口径提醒：官方“主体 12 万”≠工商注册“2.9~3.4 万家”（多数卖家经营范围不含“跨境电商”字样）；企查查/天眼查不能混比；退出无官方逐年统计，故只做定性判断。"
set_run(r, 11.5, SUB)
footer(s, 6)

# ---------------- S7 模式发现 ----------------
s = add_slide()
header(s, "FINDING ② · 模式", "精品 vs 铺货：销售费用率是分水岭")
bullets(s, [
    ("安克（精品品牌）：毛利 45% + 销售费用 22% → 净利 8.3%、营收 +23.5%", 0, True),
    ("赛维（铺货）：毛利 43% 不低，但销售费用 35% → 净利只剩 2.4%", 0, False),
    ("华凯易佰（铺货）：净利 1.6%、增速 +1.2% —— 增收不增利、增长见顶", 1, False),
    ("结论：毛利率高 ≠ 赚钱，费用结构才是模式分水岭", 0, True),
    ("精品靠产品力与复购压低“流量税”，铺货靠买量，天然更重", 1, False),
], w=6.2, size=15)
pic(s, FIG / "m3_margin_2025.png", 7.1, 2.3, 5.6)
footer(s, 7)

# ---------------- S8 分类方法 ----------------
s = add_slide()
header(s, "METHOD · 分类", "我怎么定义“精品 vs 铺货”：四个可核对的信号")
blk = [
    ("研发 / 产品投入", "精品高（私模、自研、专利）；铺货低（贴牌、公模、跟随选品）"),
    ("SKU 广度与打法", "精品少而聚焦、靠爆款+系列；铺货海量 SKU、上架测款跑概率"),
    ("收入集中度", "精品头部品类占比高（安克充电储能 50.5%）；铺货分散在无数 SKU"),
    ("销售费用率与流量", "精品较低（品牌词/复购）；铺货高（广告买量，靠流量吃饭）"),
]
for i, (k, v) in enumerate(blk):
    x = 0.7 + (i % 2) * 6.15
    y = 2.15 + (i // 2) * 2.15
    card(s, x, y, 5.85, 1.85, k, v, ACCENT, t_size=14, b_size=12)
_, tf = tb(s, Inches(0.7), Inches(6.55), Inches(12), Inches(0.6))
p = tf.paragraphs[0]; r = p.add_run()
r.text = "说明：这是“谱带”不是“开关”——判断看经营结构，而非有没有品牌名。"
set_run(r, 12, SUB, False)
footer(s, 8)

# ---------------- S9 5家定位 ----------------
s = add_slide()
header(s, "METHOD · 定位", "5 家上市公司落在哪里 + 三种原型")
rows = [
    ("安克创新", "精品品牌", "研发 9.5% 全场最高；充电储能占 50.5%；品牌+私模"),
    ("致欧科技", "目录式长尾品牌", "自有品牌矩阵、SKU 大而全；重产品设计而非铺货"),
    ("赛维时代", "铺货（泛品）", "数十万 SKU；研发 <1%；销售费用 35.4%"),
    ("华凯易佰", "铺货（泛品）", "海量 SKU + 综合服务；净利率 1.6%、增速 +1.2%"),
    ("吉宏股份", "流量驱动（非典型）", "社交电商/独立站投放为主；另含包装需分部看"),
]
y = 2.0
for name, kind, why in rows:
    rect(s, Inches(0.7), Inches(y), Inches(11.9), Inches(0.78), PANEL)
    _, tf = tb(s, Inches(0.95), Inches(y + 0.08), Inches(2.1), Inches(0.6))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = name
    set_run(r, 13.5, INK, True)
    _, tf2 = tb(s, Inches(3.1), Inches(y + 0.08), Inches(2.6), Inches(0.6))
    p2 = tf2.paragraphs[0]; r2 = p2.add_run(); r2.text = kind
    set_run(r2, 13, ACCENT, True)
    _, tf3 = tb(s, Inches(5.8), Inches(y + 0.08), Inches(6.6), Inches(0.6))
    p3 = tf3.paragraphs[0]; r3 = p3.add_run(); r3.text = why
    set_run(r3, 11.5, SUB)
    y += 0.88
_, tf4 = tb(s, Inches(0.7), Inches(6.6), Inches(12), Inches(0.7))
p4 = tf4.paragraphs[0]; r4 = p4.add_run()
r4.text = "我的经历：上一家公司 1000+ SKU 按规格矩阵做全 —— 第三种路径“目录式长尾品牌”。"
set_run(r4, 12.5, AMBER, True)
footer(s, 9)

# ---------------- S10 市场 ----------------
s = add_slide()
header(s, "FINDING ③ · 市场", "欧洲毛利更高，但天花板与本地化门槛并存")
bullets(s, [
    ("致欧是唯一披露欧美细分的公司：欧洲毛利率 36.4% > 美加 30.3%", 0, True),
    ("但致欧增速 +7.1%，明显慢于北美为主的安克（+23.5%）", 0, False),
    ("本地化门槛：VAT/EPR、多语言、产品标准", 1, False),
    ("我的亲历：美国 NPT 螺纹 vs 欧洲 G 螺纹 → 同一品类要重做产品线", 1, True),
    ("判断：美国走规模、欧洲赚毛利；先单点跑通再复制", 0, True),
], w=6.2, size=15)
pic(s, FIG / "m3_revenue.png", 7.1, 2.3, 5.6)
footer(s, 10)

# ---------------- S11 现金流 ----------------
s = add_slide()
header(s, "FINDING ④ · 现金流", "利润 ≠ 现金：安克 2025 的“有利润没现金”")
bullets(s, [
    ("安克 2025：归母净利 25.5 亿，经营现金流仅 4.8 亿（OCF/净利 ≈ 0.19）", 0, True),
    ("追查调节附表：存货增加占用约 20 亿、应收增加约 6.6 亿", 0, False),
    ("资产负债表交叉验证：存货余额 24 → 32 → 50 亿", 1, False),
    ("这就是我上一份工作困惑的“上市公司版”：利润被货和应收占住了", 0, True),
    ("结论：规模扩张期，经营现金流才是生命线", 1, False),
], w=6.2, size=15)
pic(s, FIG / "m3b_anker_cashflow.png", 7.1, 2.3, 5.6)
footer(s, 11)

# ---------------- S12 验证 ----------------
s = add_slide()
header(s, "VALIDATION · 验证", "结论之前，我先做三件事")
bullets(s, [
    ("① 数据抽查：安克 2025 营收 305.1 亿 与公开报道核对一致", 0, False),
    ("② 交叉验证：调节表（存货 -20 亿）↔ 资产负债表（存货 +17.6 亿）互相印证", 0, False),
    ("③ 主动声明局限：上市公司是幸存者（幸存者偏差）；欧美细分只有致欧披露；吉宏含包装需看分部", 0, False),
    ("结论只到证据能到的地方：安克备货是主动还是被动？→ 标“待年报附注确认”，不下定论", 0, True),
], size=16)
footer(s, 12)

# ---------------- S13 结论 ----------------
s = add_slide()
header(s, "CONCLUSION · 结论", "四个可以带走、也能被追问的判断")
concl = [
    ("① 模式", "销售费用率是分水岭：精品 22% vs 铺货 35%，毛利率高≠赚钱"),
    ("② 市场", "美国走规模、欧洲赚毛利；本地化是欧洲的隐形门槛"),
    ("③ 现金流", "利润≠现金：备货与回款是跨境电商的生死线"),
    ("④ 格局", "龙头集中度 <3%：细分做深（如目录式长尾品牌）是中小卖家的路"),
]
y = 2.2
for k, v in concl:
    rect(s, Inches(0.7), Inches(y), Inches(0.72), Inches(0.92), ACCENT)
    _, tf = tb(s, Inches(0.7), Inches(y + 0.22), Inches(0.72), Inches(0.5))
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k
    set_run(r, 15, WHITE, True)
    _, tf2 = tb(s, Inches(1.7), Inches(y + 0.1), Inches(10.9), Inches(0.75))
    p2 = tf2.paragraphs[0]; p2.anchor = MSO_ANCHOR.MIDDLE
    r2 = p2.add_run(); r2.text = v
    set_run(r2, 15.5, INK, False)
    y += 1.13
footer(s, 13)

# ---------------- S14 工具 ----------------
s = add_slide()
header(s, "PRODUCTIZE · 落地", "把结论做成能用的工具：创业决策工作台")
tools = [
    ("P1 单位经济测算", "单件赚不赚钱？盈亏平衡 ACOS；Case Pack 双方案对比"),
    ("P2 选品类助手", "单位经济可行性 + 风险规则 → 能不能做"),
    ("P3 市场选择器", "规模 / 毛利 / 竞争 / 本地化 加权 → 先做哪个市场"),
    ("P4 经营健康体检", "输入你的指标 → 对标 5 家上市公司 → 危险信号 + 阶段建议"),
]
y = 2.25
for k, v in tools:
    rect(s, Inches(0.7), Inches(y), Inches(5.0), Inches(0.9), PANEL)
    _, tf = tb(s, Inches(0.95), Inches(y + 0.12), Inches(4.6), Inches(0.7))
    p = tf.paragraphs[0]; r = p.add_run(); r.text = k
    set_run(r, 15.5, ACCENT, True)
    _, tf2 = tb(s, Inches(6.0), Inches(y + 0.1), Inches(6.7), Inches(0.75))
    p2 = tf2.paragraphs[0]; p2.anchor = MSO_ANCHOR.MIDDLE
    r2 = p2.add_run(); r2.text = v
    set_run(r2, 14, SUB)
    y += 1.05
_, tfx = tb(s, Inches(0.7), Inches(6.7), Inches(12), Inches(0.5))
px = tfx.paragraphs[0]; rx = px.add_run()
rx.text = "从“看报表”到“能决策”：每一页都基于 5 家公司的真实财务基准"
set_run(rx, 12.5, AMBER, True)
footer(s, 14)

# ---------------- S15 复盘 ----------------
s = add_slide()
header(s, "REFLECTION · 复盘", "做得好的 & 下次能更好的")
bullets(s, [
    ("做得好的：从亲身困惑出发 / 三层框架 / 现金流深挖 / 把结论做成工具", 0, True),
    ("不足与边界：销售费用没拆“广告 vs 佣金”；缺 2026H1 与关税影响；供应商报价、需求热度这类私有数据只能给框架", 0, False),
    ("如果重来：会更早看现金流量表；先用少量行业访谈补定性，再用数据验证定量", 0, True),
    ("可迁移：这套“提问 → 取数 → 验证 → 结论 → 工具化”的流程，适用于任何行业研究 / 商业分析", 0, False),
], size=16)
footer(s, 15)

# ---------------- S16 收尾 ----------------
s = add_slide()
rect(s, Inches(0), Inches(0), Inches(0.22), prs.slide_height, ACCENT)
_, tf = tb(s, Inches(1.2), Inches(2.2), Inches(11), Inches(3.4))
lines = [
    ("数据之外，我更想让你看到的，是我的思考方式：", 21, INK, True),
    ("会提问 —— 从一句“公司怎么不赚钱”出发", 16.5, SUB, False),
    ("会验证 —— 公开数据也能做严谨的研究：口径、抽查、交叉验证、写清局限", 16.5, SUB, False),
    ("会落地 —— 把结论做成能用的工具，而不只是报告", 16.5, SUB, False),
    ("会复盘 —— 知道自己哪里好、哪里还能更好", 16.5, SUB, False),
]
first = True
for t, sz, col, b in lines:
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    first = False
    p.space_after = Pt(10)
    r = p.add_run(); r.text = t
    set_run(r, sz, col, b)
_, tf2 = tb(s, Inches(1.2), Inches(6.3), Inches(11), Inches(0.8))
p2 = tf2.paragraphs[0]; r2 = p2.add_run()
r2.text = "Xuefei Wang · 2026.09 · 联系与更多材料见简历"
set_run(r2, 13, SUB)

out = OUT / "中国跨境电商出海赛道分析-项目故事-v2.pptx"
prs.save(out)
print("已生成:", out, "| 页数:", len(prs.slides._sldIdLst))
