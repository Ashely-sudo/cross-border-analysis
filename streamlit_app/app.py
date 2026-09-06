# -*- coding: utf-8 -*-
"""
跨境电商创业决策工作台（多页）
================================
基于 B1 项目（5 家上市公司公开财报 + 海关宏观数据）构建的交互决策工具：

  P1 单位经济测算    —— 这件货赚不赚钱
  P2 选品类助手      —— 这个品类能不能做
  P3 市场选择器      —— 先做哪个市场
  P4 经营健康体检    —— 我走得长远吗？该转型吗？（对标 5 家上市公司基准）

口径与诚实边界：工具用公开数据给“基准/可行性/风险信号”；具体需求热度、
供应商报价等需要私有数据，工具会提示“需补充什么数据”。

运行：streamlit run streamlit_app/app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="跨境电商创业决策工作台", page_icon="🧭", layout="wide")

# ---------- 主题：暖色高级工作台（彩色、避开蓝色） ----------
TEAL = "#0F6B5C"; AMBER = "#B45309"; VIOLET = "#6D28D9"; RUST = "#C2410C"; ROSE = "#9F1239"
INK = "#23272E"; MUTED = "#8A8178"; PAPER = "#F7F5F0"; CARD_LINE = "#EAE2D3"
MOD_COLORS = {
    "🧮 P1 单位经济测算": AMBER,
    "🧭 P2 选品类助手": VIOLET,
    "🌍 P3 市场选择器": RUST,
    "🩺 P4 经营健康体检": TEAL,
}
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [TEAL, AMBER, VIOLET, RUST, ROSE]
GLOBAL_CSS = """
<style>
.stApp { background-color: #F7F5F0; }
[data-testid="stSidebar"] { background-color: #EFE9DC; }
html, body, [class*="css"] { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }
h1, h2, h3, h4 { color: #23272E; }
[data-testid="stCaptionContainer"] p { color: #8A8178; }
[data-testid="stHeader"] { background: transparent; }
div[data-testid="stLinkButton"] a { background: linear-gradient(135deg, #0F6B5C, #0E5A4F); color: #FFFFFF !important; border: none; border-radius: 10px; font-weight: 600; }
div[data-testid="stLinkButton"] a:hover { color: #FFFFFF !important; opacity: .92; }
.stButton > button { background: linear-gradient(135deg, #23272E, #3A414B); color: #FFFFFF; border: none; border-radius: 10px; font-weight: 600; }
.stButton > button:hover { color: #FFFFFF; opacity: .92; }
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BASE = Path(__file__).resolve().parents[1]
PPT_URL = "https://docs.qq.com/slide/DWnFSTVpNdVRucUxs"

# =====================================================================
# 共享数据（基于 B1 项目真实计算；采集 2026-09-06）
# =====================================================================
REFERRAL_PRESETS = {
    "工业品 & 科研用品（Business, Industrial & Scientific，12%）": 12.0,
    "工具 & 家装（Tools & Home Improvement，15%）": 15.0,
    "家居厨房（Home & Kitchen，15%）": 15.0,
    "消费电子（Consumer Electronics，8%）": 8.0,
    "电子配件（Electronics Accessories，15% ≤$100）": 15.0,
    "服饰（Clothing，>$20 为 17%）": 17.0,
    "珠宝（Jewelry，≤$250 为 20%）": 20.0,
    "自定义": None,
}
FBA_HINTS = {
    "小号标准 ≤1 lb（约$3.3–4.0）": 3.7,
    "大号标准 1–2 lb（约$4.6–5.8）": 5.2,
    "大号标准 2–3 lb（约$5.8–6.7）": 6.3,
    "大号标准 >3 lb（$6.97 起，每 4oz +$0.08）": 7.2,
    "自定义": None,
}

BENCH = [
    {"公司": "安克创新", "模式": "品牌精品·北美", "毛利率": 45.1, "销售费用率": 22.4,
     "净利率": 8.3, "增速": 23.5, "OCF/净利": 0.19, "存货周转": 4.1},
    {"公司": "致欧科技", "模式": "品牌精品·欧洲", "毛利率": 34.5, "销售费用率": 25.2,
     "净利率": 3.9, "增速": 7.1, "OCF/净利": 7.40, "存货周转": 4.4},
    {"公司": "赛维时代", "模式": "泛品铺货", "毛利率": 42.7, "销售费用率": 35.4,
     "净利率": 2.4, "增速": 15.0, "OCF/净利": 4.42, "存货周转": 4.4},
    {"公司": "华凯易佰", "模式": "泛品铺货", "毛利率": 33.4, "销售费用率": 25.4,
     "净利率": 1.6, "增速": 1.2, "OCF/净利": 6.62, "存货周转": 4.4},
    {"公司": "吉宏股份", "模式": "社交电商(含包装)", "毛利率": 46.9, "销售费用率": 35.3,
     "净利率": 4.1, "增速": 21.6, "OCF/净利": 0.94, "存货周转": 7.4},
]
BENCH_DF = pd.DataFrame(BENCH)
BENCH_MED = {k: float(BENCH_DF[k].median())
             for k in ["毛利率", "销售费用率", "净利率", "增速", "OCF/净利"]}

MARKETS = {
    "美国": {"规模": 5.0, "竞争": 2.0, "毛利": 3.0, "本地化难度": 2.0, "资金需求": 4.0, "增长": 3.0,
             "依据": "出口占 36.2% 最大；最卷但基础设施最成熟；毛利参考致欧美加 30.3%"},
    "欧洲": {"规模": 4.0, "竞争": 3.0, "毛利": 5.0, "本地化难度": 4.5, "资金需求": 3.0, "增长": 2.0,
             "依据": "致欧欧洲毛利率 36.4%>美加 30.3%；但标准/合规、多语言、增长更慢(+7.1%)"},
    "日本": {"规模": 2.5, "竞争": 3.0, "毛利": 4.0, "本地化难度": 4.5, "资金需求": 3.0, "增长": 2.0,
             "依据": "客单价高、退货低；语言与习惯门槛高"},
    "东南亚": {"规模": 2.5, "竞争": 4.0, "毛利": 2.5, "本地化难度": 2.5, "资金需求": 2.0, "增长": 5.0,
               "依据": "增速快竞争小；但客单价低、基建不成熟（吉宏社交电商样本）"},
}
CRITERIA = ["规模", "竞争", "毛利", "本地化难度", "资金需求", "增长"]
MARKET_NOTES = {
    "美国": "走规模的基本盘：先单点跑通单位经济与现金流，再考虑扩张。",
    "欧洲": "赚毛利的市场：适合有本地化能力（认证/标准/合规/语言）的差异化细分。",
    "日本": "高客单低退货：适合愿意投入语言与本土化运营的团队。",
    "东南亚": "赌增长的市场：适合能忍受低客单价、愿意长期培育的团队。",
}


def calc(price, unit_cost, freight, other, referral_pct, fba, acos):
    referr = price * referral_pct / 100.0
    ad = price * acos / 100.0
    total_cost = unit_cost + freight + other
    fees = referr + fba + ad
    net = price - total_cost - fees
    net_pct = net / price * 100 if price else 0.0
    be_acos = (price - total_cost - referr - fba) / price * 100 if price else 0.0
    gross_before_ad = price - total_cost - referr - fba
    return {"price": price, "referr": referr, "fba": fba, "ad": ad,
            "total_cost": total_cost, "fees": fees, "net": net, "net_pct": net_pct,
            "be_acos": be_acos, "gross_before_ad": gross_before_ad}


def metric_row(label, user_val, median):
    d = user_val - median
    arrow = "▲ 高于基准" if d > 0.05 else ("▼ 低于基准" if d < -0.05 else "≈ 持平")
    return {"指标": label, "你的值": round(user_val, 1), "5家基准(中位数)": round(median, 1), "对比": arrow}


# ---------- 卡片辅助（单行 HTML，浅底/白底 + 彩色侧条；单行避免被 Markdown 当成代码块） ----------
def info_card(title, body, accent=TEAL, value=None):
    value_html = ""
    if value is not None:
        value_html = "<div style='font-size:26px;font-weight:800;color:#23272E;margin:6px 0 2px;'>" + value + "</div>"
    html = ("<div style='background:linear-gradient(180deg,#FFFFFF,#FBF7EF);border:1px solid #EAE2D3;"
            "border-left:5px solid " + accent + ";border-radius:14px;padding:14px 18px;"
            "box-shadow:0 2px 6px rgba(35,39,46,.05);'>"
            "<div style='font-weight:800;color:#23272E;font-size:16px;'>" + title + "</div>" + value_html +
            "<div style='color:#8A8178;font-size:13.5px;margin-top:4px;line-height:1.6;'>" + body + "</div></div>")
    return html


def metric_block(label, value, delta=None, help=None, accent=AMBER):
    delta_html = ""
    if delta is not None:
        dcolor = "#2E7D5B" if str(delta).startswith("+") else ("#C2410C" if str(delta).startswith("-") else "#8A8178")
        delta_html = "<div style='font-size:13px;color:" + dcolor + ";margin-top:2px;'>" + str(delta) + "</div>"
    help_html = ""
    if help:
        help_html = "<div style='font-size:12px;color:#A69E93;margin-top:4px;line-height:1.4;'>" + help + "</div>"
    html = ("<div style='background:linear-gradient(180deg,#FFFFFF,#FBF7EF);border:1px solid #EAE2D3;"
            "border-top:4px solid " + accent + ";border-radius:14px;padding:14px 16px;"
            "box-shadow:0 1px 3px rgba(35,39,46,.05);'>"
            "<div style='color:#8A8178;font-size:13px;'>" + label + "</div>"
            "<div style='font-size:26px;font-weight:800;color:#23272E;margin:4px 0 2px;'>" + value + "</div>"
            + delta_html + help_html + "</div>")
    return html


PAGES = [
    "🧮 P1 单位经济测算",
    "🧭 P2 选品类助手",
    "🌍 P3 市场选择器",
    "🩺 P4 经营健康体检",
]
PAGE_DESC = {
    "🧮 P1 单位经济测算": "这件货到底赚不赚钱：定价 / ACOS 盈亏平衡 / Case Pack 整箱对比。",
    "🧭 P2 选品类助手": "按单位经济 + 风险清单判断：这个品类能不能做、要不要先小批量验证。",
    "🌍 P3 市场选择器": "把六个维度按你的盘子加权，选先做美国 / 欧洲 / 日本 / 东南亚。",
    "🩺 P4 经营健康体检": "输入你的指标，对标 5 家上市公司基准，输出危险信号与转型建议。",
}


def page_overview():
    hero = """<div style="background:linear-gradient(135deg,#FFFFFF 0%,#F4EFE4 100%);border:1px solid #EAE2D3;border-radius:18px;padding:26px 30px;margin-bottom:16px;box-shadow:0 4px 14px rgba(35,39,46,.06);">
      <div style="font-size:12px;color:#8A8178;font-weight:700;letter-spacing:1.5px;">XUEFEI WANG · 2026 · DATA / BUSINESS ANALYSIS</div>
      <div style="font-size:32px;font-weight:900;color:#23272E;margin-top:8px;">跨境电商创业决策工作台</div>
      <div style="color:#6E675E;font-size:15px;margin-top:10px;max-width:840px;line-height:1.75;">从一线运营的困惑出发，用 5 家上市公司公开财报把“单品盈利却整体不赚钱”拆成可验证的问题，再落成 <b>4 个可直接上手用的决策工具</b>。完整论证与结论在 PPT。</div>
      <div style="margin-top:16px;">
        <span style="background:#E7F0EC;color:#0F6B5C;font-size:12px;font-weight:600;border-radius:20px;padding:4px 12px;margin-right:6px;">公开财报 · 可复核</span>
        <span style="background:#F7E9DA;color:#B45309;font-size:12px;font-weight:600;border-radius:20px;padding:4px 12px;margin-right:6px;">5 家上市公司基准</span>
        <span style="background:#EFE8F6;color:#6D28D9;font-size:12px;font-weight:600;border-radius:20px;padding:4px 12px;margin-right:6px;">海关官方宏观</span>
        <span style="background:#FBEAE2;color:#C2410C;font-size:12px;font-weight:600;border-radius:20px;padding:4px 12px;">结论见 13 页 PPT</span>
      </div>
    </div>"""
    st.markdown(hero, unsafe_allow_html=True)

    st.markdown("### 工作台模块")
    st.caption("点下方任一模块进入，或用左侧导航切换。")
    cols = st.columns(2)
    mod_accent = [AMBER, VIOLET, RUST, TEAL]
    for i, key in enumerate(PAGES):
        with cols[i % 2]:
            st.markdown(info_card(key, PAGE_DESC[key], mod_accent[i]), unsafe_allow_html=True)
            if st.button("进入模块 →", key="go_" + key, width="stretch"):
                st.session_state["nav"] = key
                st.rerun()
    st.markdown("---")
    st.caption("📄 完整论证与结论见 [13 页项目故事 PPT](%s) ｜ 数据版本：2026-09 · 5 家上市公司 2025 年报 + 海关官方统计，口径与局限见 PPT。" % PPT_URL)

def _ui_calc_inputs(title, key):
    st.subheader(title)
    c = st.columns(2)
    with c[0]:
        price = st.number_input("售价 USD/件", 0.0, 10000.0, 25.0, step=1.0, key=f"{key}_price")
        unit_cost = st.number_input("采购成本 USD/件", 0.0, 10000.0, 8.0, step=0.5, key=f"{key}_cost")
        freight = st.number_input("头程+入库 USD/件", 0.0, 10000.0, 1.0, step=0.1, key=f"{key}_freight")
        other = st.number_input("其他(仓储/退货分摊) USD/件", 0.0, 1000.0, 0.5, step=0.1, key=f"{key}_other")
    with c[1]:
        ref_choice = st.selectbox("平台佣金率（按品类近似）", list(REFERRAL_PRESETS), index=0, key=f"{key}_refsel")
        referral_pct = REFERRAL_PRESETS[ref_choice] if REFERRAL_PRESETS[ref_choice] is not None else st.number_input(
            "自定义佣金率 %", 0.0, 50.0, 15.0, key=f"{key}_refcust")
        fba_choice = st.selectbox("FBA 配送费（按体积重量近似）", list(FBA_HINTS), index=1, key=f"{key}_fbasel")
        fba = FBA_HINTS[fba_choice] if FBA_HINTS[fba_choice] is not None else st.number_input(
            "自定义 FBA 配送费 USD", 0.0, 100.0, 5.0, key=f"{key}_fbacust")
        acos = st.slider("广告 ACOS %", 0, 80, 30, key=f"{key}_acos")
    return price, unit_cost, freight, other, referral_pct, fba, acos


def _show_result(r, name):
    cards = [
        (f"{name} · 单位净利 (USD)", f"{r['net']:.2f}",
         f"{r['net_pct']:.1f}%", "净利率"),
        ("盈亏平衡 ACOS %", f"{max(r['be_acos'], 0):.1f}", None, "超过该 ACOS 即亏损"),
        ("平台+广告占售价", f"{r['fees']/r['price']*100:.1f}%", None,
         f"佣金 {r['referr']:.2f} + FBA {r['fba']:.2f} + 广告 {r['ad']:.2f}"),
        ("广告前利润 (USD)", f"{r['gross_before_ad']:.2f}", None, "扣佣金/FBA、未扣广告"),
    ]
    cols = st.columns(4)
    for col, (lab, val, delta, help_) in zip(cols, cards):
        col.markdown(metric_block(lab, val, delta, help_), unsafe_allow_html=True)


# ---------- 2026 美国 FBA 运费引擎（非服装·标准件；口径：2026-07，非旺季 $10–$50 主表 + 价档调整） ----------
_FBA_SMALL = [(2, 3.32), (4, 3.42), (6, 3.45), (8, 3.54), (10, 3.68), (12, 3.78), (14, 3.91), (16, 3.96)]
_FBA_LARGE = [(4, 3.73), (8, 3.95), (12, 4.20), (16, 4.60), (20, 5.04), (24, 5.42), (28, 5.57), (32, 5.82),
              (36, 5.92), (40, 6.10), (44, 6.26), (48, 6.67)]
_FBA_SMALL_LOW = [(2, 2.43), (4, 2.49), (6, 2.56), (8, 2.66), (10, 2.77), (12, 2.82), (14, 2.92), (16, 2.95)]
_FBA_LARGE_LOW = [(4, 2.91), (8, 3.13), (12, 3.38), (16, 3.78), (20, 4.22), (24, 4.60), (28, 4.75), (32, 5.00),
                  (36, 5.10), (40, 5.28), (44, 5.44), (48, 5.85)]


def _band_fee(table_oz, weight_oz, over3_base):
    for max_oz, fee in table_oz:
        if weight_oz <= max_oz:
            return fee
    # 超过 3 lb（48 oz）：按每多 4 oz +0.08 递增
    extra = max(0.0, weight_oz - 48.0)
    return over3_base + (extra / 4.0) * 0.08


def fba_fee_2026(dims_in, wt_lb, price_band="10_50"):
    """dims_in=(L,W,H) 英寸; wt_lb=实际重量; 返回 (tier, 计费重量lb, 运费USD 或 None)"""
    L, W, H = dims_in
    d = sorted([L, W, H], reverse=True)  # 长>=宽>=高
    dim_wt = L * W * H / 139.0
    ship = max(wt_lb, dim_wt)
    oz = ship * 16.0
    # 尺寸带
    if wt_lb <= 1.0 and L <= 15.0 and W <= 12.0 and H <= 0.75:
        tier = "小号标准"
    elif wt_lb <= 20.0 and d[0] <= 18.0 and d[1] <= 14.0 and d[2] <= 8.0:
        tier = "大号标准"
    else:
        return ("超规/大件（超出标准，请用亚马逊官方计算器精算）", ship, None)
    low = price_band == "lt10"
    if tier == "小号标准":
        fee = _band_fee(_FBA_SMALL_LOW if low else _FBA_SMALL, min(oz, 16.0), None)
    else:
        fee = _band_fee(_FBA_LARGE_LOW if low else _FBA_LARGE, min(oz, 48.0) if ship <= 3.0 else oz,
                        2.43 if False else (6.15 if low else 6.97))
        if low:
            pass
    if price_band == "gt50":
        fee = None if fee is None else fee + 0.26
    return (tier, round(ship, 2), round(fee, 2) if fee is not None else None)


def abs_discount(n_units):
    """Amazon Bulk Services 佣金折扣：2-9:15% off, 10-23:20% off, 24+:25% off"""
    if n_units >= 24:
        return 0.25
    if n_units >= 10:
        return 0.20
    if n_units >= 2:
        return 0.15
    return 0.0


def page_calc():
    st.title("🧮 P1 · 单位经济测算")
    tab1, tab2 = st.tabs(["单方案测算", "双方案对比"])
    with tab1:
        pa = _ui_calc_inputs("基础参数", "a")
        r = calc(*pa)
        _show_result(r, "当前方案")
        c1, c2 = st.columns([1.1, 1])
        with c1:
            acos_range = np.arange(0, 81, 1)
            nets = [calc(*pa[:6], ac)["net"] for ac in acos_range]
            fig = go.Figure(go.Scatter(x=acos_range, y=nets, mode="lines", line=dict(color=AMBER, width=3)))
            fig.add_hline(y=0, line_dash="dash", line_color="#C2410C")
            fig.update_layout(xaxis_title="广告 ACOS %", yaxis_title="单位净利 (USD)",
                              title="单位净利 vs 广告 ACOS",
                              title_font_size=15, height=340,
                              margin=dict(t=52, b=10, l=8, r=8), font=dict(color=INK))
            st.plotly_chart(fig, width="stretch", key="sens_a")
        with c2:
            share = pd.DataFrame({
                "项目": ["采购成本(60%)", "头程+其他", "平台佣金", "FBA配送", "广告", "单位净利"],
                "金额": [pa[1]*0.6, pa[1]*0.4 + pa[2] + pa[3], r["referr"], r["fba"], r["ad"], r["net"]]})
            palette2 = ["#C7B299", "#B29A7C", "#9A8161", "#C05746", "#7A6A8F", "#0F6B5C"]
            fig = go.Figure(go.Bar(x=share["项目"], y=share["金额"], marker_color=palette2))
            fig.update_layout(title="售价拆解（USD）", title_font_size=15, height=340,
                              margin=dict(t=52, b=10, l=8, r=8), showlegend=False,
                              yaxis_title="USD", font=dict(color=INK))
            st.plotly_chart(fig, width="stretch", key="bar_a")
    with tab2:
        st.markdown("**Case Pack 整箱 vs 散卖**：输入单件成本/售价与箱数，工具自动算整箱总账；"
                    "运费按 2026 美国 FBA 费率自动判断尺寸带，广告按售价 15% 计，佣金按品类并可叠加批量佣金折扣。")
        top = st.columns([1, 1, 1.1])
        with top[0]:
            unit_cost_rmb = st.number_input("单件采购成本（人民币）", 0.0, 1e6, 60.0, step=1.0, key="cp_cost")
            unit_price_usd = st.number_input("单件售价（美元）", 0.0, 1e6, 25.0, step=0.5, key="cp_price")
            n_units = st.number_input("每箱件数", 1, 500, 10, step=1, key="cp_n")
            fx = st.number_input("汇率（CNY/USD）", 1.0, 20.0, 7.2, step=0.1, key="cp_fx")
        with top[1]:
            ref_choice = st.selectbox("品类佣金率", list(REFERRAL_PRESETS), index=0, key="cp_ref")
            ref_pct = REFERRAL_PRESETS[ref_choice] if REFERRAL_PRESETS[ref_choice] else st.number_input(
                "自定义佣金率 %", 0.0, 50.0, 15.0, key="cp_refc")
            use_abs = st.checkbox("参与批量销售佣金折扣（Amazon Bulk Services）", value=True, key="cp_abs",
                                  help="官方口径：2-9件减15%、10-23件减20%、24件+减25%。还需同时满足：整箱售价>$20，且（件数≥10 或 体积≥1400 in³ 或 重量≥35 lb）；卖家须为品牌注册授权方。工具会按下方的整箱尺寸自动判断是否达标。")
            price_band = st.selectbox("FBA 价档", ["lt10", "10_50", "gt50"], index=1, key="cp_band",
                                      format_func=lambda x: {"lt10": "<$10", "10_50": "$10–50", "gt50": ">$50"}[x])
        with top[2]:
            st.markdown("**整箱售价调整**")
            case_disc = st.slider("整箱再打折（%）", 0, 50, 20, key="cp_disc",
                                  help="例如 20 = 整箱总价打 8 折")
            rounding = st.selectbox("取整方式", ["不取整", "取整到整数美元", "取整到 .99"], index=0, key="cp_round")

        st.markdown("#### 尺寸与重量（inch / lb）")
        dims = st.columns(4)
        with dims[0]:
            sL = st.number_input("单件 长(in)", 0.1, 60.0, 8.0, key="cp_sL")
            sW = st.number_input("单件 宽(in)", 0.1, 60.0, 6.0, key="cp_sW")
            sH = st.number_input("单件 高(in)", 0.1, 60.0, 4.0, key="cp_sH")
            sWt = st.number_input("单件 重(lb)", 0.01, 200.0, 1.2, key="cp_sWt")
        with dims[1]:
            cL = st.number_input("整箱 长(in)", 0.1, 120.0, 12.0, key="cp_cL")
            cW = st.number_input("整箱 宽(in)", 0.1, 120.0, 10.0, key="cp_cW")
            cH = st.number_input("整箱 高(in)", 0.1, 120.0, 8.0, key="cp_cH")
            cWt = st.number_input("整箱 重(lb)", 0.1, 300.0, 13.0, key="cp_cWt")
        with dims[2]:
            st.caption("单件运费由【单件尺寸/重量】判断；整箱运费由【整箱尺寸/重量】判断。")
            st.caption("计费重量 = max(实际重量, 长×宽×高 ÷ 139)。")
        with dims[3]:
            pass

        n = int(n_units)
        gross_case = unit_price_usd * n * (1 - case_disc / 100.0)
        if rounding == "取整到整数美元":
            gross_case = float(round(gross_case))
        elif rounding == "取整到 .99":
            gross_case = float(int(gross_case)) + 0.99

        # 批量折扣资格：整箱售价>$20 且（件数≥10 或 体积≥1400in³ 或 重量≥35lb）
        case_vol = cL * cW * cH
        abs_ok = (gross_case > 20.0) and (n >= 10 or case_vol >= 1400.0 or cWt >= 35.0)
        abs_eligible_note = ""
        if use_abs and n >= 2 and not abs_ok:
            abs_eligible_note = ("｜ ⚠️ 本箱不满足官方批量折扣条件（需整箱售价>$20，且件数≥10 "
                                 "或体积≥1400 in³ 或重量≥35 lb），故未应用折扣，请核对。")

        # 散卖
        tier_s, ship_s, fba_s = fba_fee_2026((sL, sW, sH), sWt, price_band)
        ref_s = unit_price_usd * ref_pct / 100.0
        ad_s = unit_price_usd * 0.15
        fee_s = (0 if fba_s is None else fba_s) + ref_s + ad_s
        net_s_usd = unit_price_usd - fee_s
        profit_s_rmb = net_s_usd * fx - unit_cost_rmb
        roi_s = profit_s_rmb / unit_cost_rmb * 100 if unit_cost_rmb else 0

        # 整箱
        tier_c, ship_c, fba_c = fba_fee_2026((cL, cW, cH), cWt, price_band)
        abs_d = abs_discount(n) if (use_abs and n >= 2 and abs_ok) else 0.0
        ref_c_total = gross_case * ref_pct / 100.0 * (1 - abs_d)
        ad_c_total = gross_case * 0.15
        fba_c_total = 0 if fba_c is None else fba_c
        fee_c_total = ref_c_total + ad_c_total + fba_c_total
        net_c_usd = gross_case - fee_c_total
        profit_c_rmb = net_c_usd * fx - unit_cost_rmb * n
        roi_c = profit_c_rmb / (unit_cost_rmb * n) * 100 if (unit_cost_rmb * n) else 0
        per_c = net_c_usd / n

        st.markdown("#### 对比结果")
        colA, colB, colC = st.columns(3)
        colA.markdown(metric_block("散卖 · 单件 ROI", f"{roi_s:.1f}%",
                                   f"净利 {profit_s_rmb:+.2f} RMB", f"单件净利 ${net_s_usd:.2f} USD"), unsafe_allow_html=True)
        colB.markdown(metric_block("Case Pack · 整箱 ROI", f"{roi_c:.1f}%",
                                   f"净利 {profit_c_rmb:+.2f} RMB", f"整箱净利 ${net_c_usd:.2f} USD"), unsafe_allow_html=True)
        colC.markdown(metric_block("Case Pack 每件净利", f"${per_c:.2f}",
                                   f"vs 散卖单件 {net_s_usd:.2f}",
                                   f"整箱总售价 ${gross_case:.2f}（{n}件，每件${gross_case/n:.2f}）｜ "
                                   f"整箱总成本 ¥{unit_cost_rmb * n:.0f}（{n}件 × ¥{unit_cost_rmb:.0f}）"), unsafe_allow_html=True)

        st.markdown("#### 费用拆解（USD）")
        detail = pd.DataFrame({
            "项目": ["售价（总）", "平台佣金（总）", "广告 15%（总）", "FBA 配送费（整包）", "费用合计", "净利（总）"],
            "散卖（每件）": [round(unit_price_usd, 2), round(ref_s, 2), round(ad_s, 2), round(0 if fba_s is None else fba_s, 2),
                          round(fee_s, 2), round(net_s_usd, 2)],
            "Case Pack（整箱）": [round(gross_case, 2), round(ref_c_total, 2), round(ad_c_total, 2), round(0 if fba_c is None else fba_c, 2),
                               round(fee_c_total, 2), round(net_c_usd, 2)],
        })
        st.dataframe(detail, width="stretch", hide_index=True)
        st.caption(f"散卖运费：{tier_s}，计费重量 {ship_s} lb，FBA ${0 if fba_s is None else fba_s} ｜ "
                   f"整箱运费：{tier_c}，计费重量 {ship_c} lb，FBA ${0 if fba_c is None else fba_c} ｜ "
                   f"整箱佣金按箱数 {n} 件应用批量折扣 -{abs_d*100:.0f}%。{abs_eligible_note}")
        st.caption("费率口径：佣金与批量折扣取亚马逊官方费率表（2026，美国站）；FBA 取 2026 非旺季费率、不含燃油附加费；"
                   "品类归属与最终费用以卖家后台及亚马逊官方 FBA Revenue Calculator 为准。")
    st.info("未含退货损失、仓储超期费、汇率波动与税务；落地以亚马逊当期官方费率表为准。")


def page_category():
    st.title("🧭 P2 · 选品类助手")
    st.caption("先用单位经济判断“这类品还能不能做出利润”，再叠加风险规则；需求热度/竞争密度需私有数据补充。")
    c = st.columns(2)
    with c[0]:
        price = st.number_input("预期售价 USD/件", 5.0, 500.0, 25.0, step=1.0, key="cat_price")
        unit_cost = st.number_input("采购+头程到仓 USD/件", 1.0, 300.0, 9.0, step=0.5, key="cat_cost")
        ref_choice = st.selectbox("品类佣金率", list(REFERRAL_PRESETS), index=0, key="cat_ref")
        referral_pct = REFERRAL_PRESETS[ref_choice] if REFERRAL_PRESETS[ref_choice] else st.number_input(
            "自定义佣金率 %", 0.0, 50.0, 15.0, key="cat_refc")
        fba_choice = st.selectbox("FBA 配送费档位", list(FBA_HINTS), index=1, key="cat_fba")
        fba = FBA_HINTS[fba_choice] if FBA_HINTS[fba_choice] else st.number_input(
            "自定义 FBA USD", 0.0, 100.0, 5.0, key="cat_fbac")
        acos = st.slider("假设广告 ACOS %", 0, 80, 30, key="cat_acos")
    with c[1]:
        st.markdown("#### 风险特征（勾选，命中越多越谨慎）")
        r_high_return = st.checkbox("高退货（服装鞋码/尺寸敏感）", key="cat_ret")
        r_big = st.checkbox("大件/超重（运费与仓储贵）", key="cat_big")
        r_electric = st.checkbox("带电/易碎/需认证", key="cat_elec")
        r_seasonal = st.checkbox("强季节性（一年只卖几个月）", key="cat_sea")
        r_brand = st.checkbox("强品牌垄断/大牌低价品", key="cat_brand")
        r_diff = st.checkbox("你能做出差异（规格/材质/组合/私模）", key="cat_diff")

    r = calc(price, unit_cost, 0.0, 0.0, referral_pct, fba, acos)
    cards = [
        ("单位净利 (USD)", f"{r['net']:.2f}", (f"{r['net_pct']:.1f}%" + (" 净利率" if r["net_pct"] >= 0 else " 净亏损率")), None),
        ("净利率 %", f"{r['net_pct']:.1f}", None, "单位净利 ÷ 售价"),
        ("盈亏平衡 ACOS %", f"{max(r['be_acos'],0):.1f}", None, "广告 ACOS 超过该值即亏损"),
    ]
    cols = st.columns(3)
    for col, (lab, val, delta, note) in zip(cols, cards):
        col.markdown(metric_block(lab, val, delta, note, VIOLET), unsafe_allow_html=True)

    risks = []
    if r_high_return:
        risks.append("高退货：售后与折价吃掉利润")
    if r_big:
        risks.append("大件/超重：FBA 与头程成本高")
    if r_electric:
        risks.append("带电/认证：合规与测款周期长")
    if r_seasonal:
        risks.append("强季节性：现金流波动大")
    if r_brand:
        risks.append("品牌垄断/标品价格战：只能拼价")
    if not r_diff:
        risks.append("无差异化：谁都能卖 = 注定价格战")

    if r["net"] <= 0:
        st.error("🔴 单位经济不成立：先改定价/降成本，别铺量")
    elif r["net_pct"] < 5:
        st.warning("🟠 单位经济勉强：净利率<5%，抗风险能力弱")
    else:
        st.success("🟢 单位经济可行")
    if len(risks) >= 3:
        st.error("🔴 风险命中过多，建议换方向或先小批量验证")
    elif risks:
        st.warning(f"🟠 命中 {len(risks)} 项风险，需逐条给对策")
    if risks:
        with st.expander("命中的风险与对策建议"):
            for x in risks:
                st.markdown(f"- {x}")
    with st.expander("还需要补什么数据（诚实边界）"):
        st.markdown("""本工具只能判断成本/费率结构上能不能做。上线前还须补：
- 类目需求热度、搜索量、Top100 集中度与 review 分布（卖家后台/选品工具）；
- 竞品定价与你的差异化证据；
- 真实 FBA 费率与头程报价（按重量尺寸精算）。""")


def page_market():
    st.title("🌍 P3 · 市场选择器")
    st.caption("把六个维度按你的情况加权，看哪个市场最值得先做。口径：规模/毛利/增长 分数越高越有利；竞争压力/本地化难度/资金需求 分数越高越不利（按原始分直接加权，用于排序方向，非精确测算）。")
    weights = {}
    c = st.columns(3)
    for i, cr in enumerate(CRITERIA):
        with c[i % 3]:
            weights[cr] = st.slider(f"{cr} 权重", 0, 5, 3, key=f"w_{cr}")

    rows = []
    for mk, attrs in MARKETS.items():
        score = sum(attrs[cr] * weights[cr] for cr in CRITERIA)
        rows.append({"市场": mk, **{cr: attrs[cr] for cr in CRITERIA},
                     "加权得分": round(score, 1), "一句话依据": attrs["依据"]})
    df = pd.DataFrame(rows).sort_values("加权得分", ascending=False).reset_index(drop=True)

    top = df.iloc[0]
    st.success(f"🏆 加权后最推荐先做：**{top['市场']}**（得分 {top['加权得分']}）。{MARKET_NOTES[top['市场']]}")

    fig = px.bar(df, x="市场", y="加权得分", text="加权得分", color="加权得分",
                 color_continuous_scale=["#F3E3BE", "#C89B3C", "#B45309"])
    fig.update_layout(height=360, margin=dict(t=20, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(df.drop(columns=["加权得分", "一句话依据"]), width="stretch", hide_index=True)
    with st.expander("各市场的数据依据与打分说明"):
        for _, row in df.iterrows():
            st.markdown(f"**{row['市场']}**：{row['一句话依据']}")
    with st.expander("局限"):
        st.markdown("""打分是公开数据+经验的估计，不是精确测算；关税/VAT 等政策变化需实时跟踪。
- 三个负向维度（竞争压力、本地化难度、资金需求）数值越大代表对你越不利，工具按原始分直接加权；
- 建议把它当“排序方向”用，别当精确分数；换权重看结论是否稳健；
- “单点突破、先跑通再复制”仍是最稳策略。""")


def page_health():
    st.title("🩺 P4 · 经营健康体检（对标 5 家上市公司）")
    st.caption("输入你（或你假设的公司）的真实经营指标，与 5 家上市公司 2025 年基准对比，输出危险信号与阶段建议。")
    c = st.columns(3)
    with c[0]:
        gross = st.number_input("毛利率 %", -20.0, 90.0, 35.0, key="h_gross")
        sale = st.number_input("销售费用率 %", 0.0, 90.0, 28.0, key="h_sale")
    with c[1]:
        net = st.number_input("净利率 %", -30.0, 50.0, 3.0, key="h_net")
        growth = st.number_input("营收同比增速 %", -30.0, 100.0, 10.0, key="h_growth")
    with c[2]:
        ocf = st.number_input("OCF/归母净利（如 0.5）", -5.0, 15.0, 0.8, step=0.1, key="h_ocf")
        inv = st.number_input("存货周转率（次/年，可留默认）", 0.0, 20.0, 4.0, key="h_inv")
    scale = st.selectbox("你现在的营收规模（人民币）",
                         ["验证期 <100万", "复制期 100万-1000万", "放大期 1000万-1亿", "升级期 >1亿"],
                         key="h_scale")
    model = st.selectbox("你的模式（用于建议措辞）",
                         ["品牌精品", "泛品铺货", "长尾全品类品牌", "平台+独立站混合"], key="h_model")

    user = {"毛利率": gross, "销售费用率": sale, "净利率": net, "增速": growth, "OCF/净利": ocf}
    rows = [metric_row(k, user[k], BENCH_MED[k]) for k in BENCH_MED]
    st.markdown("#### 你 vs 5 家上市公司基准（中位数）")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    feats = ["毛利率", "销售费用率", "净利率", "增速", "OCF/净利"]
    tmp = BENCH_DF.copy()
    tmp["_dist"] = np.sqrt(sum(((user[g] - tmp[g]) / ((tmp[g].max() - tmp[g].min()) or 1.0)) ** 2 for g in feats))
    near = tmp.loc[tmp["_dist"].idxmin()]
    st.info(f"🧬 你的财务结构最接近：**{near['公司']}（{near['模式']}）**——仅代表结构近似，不代表经营水平相同。")

    flags = []
    if net < 2:
        flags.append(("盈利警报", f"净利率 {net:.1f}% < 2%（华凯易佰 1.6% 同区）——增收不增利/亏损边缘",
                      "砍低效 SKU、提价或降广告依赖，先让单件账为正"))
    if sale > 35:
        flags.append(("平台税过重", f"销售费用率 {sale:.1f}% > 35%（接近赛维/吉宏）——你在给平台和流量打工",
                      "提高自然单占比、复购与品牌词占比，压 ACOS"))
    if ocf < 0.3:
        flags.append(("现金流警报", f"OCF/净利 {ocf:.1f} < 0.3（安克 2025 = 0.19 即警讯）——利润被存货/应收占住",
                      "控库存、加快回款，把经营现金流当第一生命线"))
    if growth < 5:
        flags.append(("增长停滞", f"增速 {growth:.1f}% < 5%（华凯易佰 +1.2% 同区）——旧打法见顶",
                      "找第二增长曲线：新市场/新渠道/新品类/品牌升级"))
    if gross < 35:
        flags.append(("毛利偏低", f"毛利率 {gross:.1f}% < 35%（低于致欧/华凯）——产品缺差异化或成本无优势",
                      "做私模/改款/垂直供应链，别在纯标品里拼价"))

    st.markdown("#### 🚦 转型/健康信号")
    if not flags:
        st.success("✅ 各项指标都在样本基准合理区间——现阶段重点是：把单点跑通后复制，别盲目扩张。")
    else:
        for name, why, action in flags:
            with st.expander(f"⚠️ {name}"):
                st.markdown(f"- **现象**：{why}\n- **动作**：{action}")

    st.markdown("#### 🪜 你现在大致处于哪个阶段")
    stage_txt = scale.split(" ")[0]
    if flags and net < 2 and ocf < 0.3:
        stage_txt += "（⚠️ 建议先回到“单位经济为正 + 现金流为正”，再谈规模）"
    st.markdown(f"**{scale} → 定位：{stage_txt}**")
    advice = {
        "验证期": "少量 SKU 试销，验证单件单位经济与自然单占比；不铺量、不压货。",
        "复制期": "把验证过的 SKU 矩阵化/规格化，稳定补货与现金流后，复制到相邻品类或站点。",
        "放大期": "加广告与多平台/多站点，但每扩张一步都要回查 OCF/净利 与存货周转。",
        "升级期": "向品牌、私模、独立站与供应链垂直整合升级，降低对单一平台的依赖。",
    }
    st.info(advice[stage_txt.split("（")[0]])

    with st.expander("基准怎么来的（数据边界）"):
        st.markdown("对标值来自 5 家上市公司 2025 年报（B1 M3 计算）。危险阈值是按样本分布划的参考线，不是铁律；"
                    "上市公司有幸存者偏差，小公司费用结构可能差异更大。建议每季度体检，看趋势而非单点。")


def main():
    pages = {
        "🏠 概览与入口": page_overview,
        "🧮 P1 单位经济测算": page_calc,
        "🧭 P2 选品类助手": page_category,
        "🌍 P3 市场选择器": page_market,
        "🩺 P4 经营健康体检": page_health,
    }
    order = list(pages)
    if "nav" not in st.session_state or st.session_state["nav"] not in pages:
        st.session_state["nav"] = order[0]
    with st.sidebar:
        st.title("创业决策工作台")
        sel = st.radio("选择页面", order,
                       index=order.index(st.session_state["nav"]),
                       label_visibility="collapsed")
        st.session_state["nav"] = sel
        st.divider()
        st.caption("数据：5 家上市公司 2025 年报（akshare）+ 海关宏观；个人学习用途，非投资建议。")
    pages[st.session_state["nav"]]()


if __name__ == "__main__":
    main()
