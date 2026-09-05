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

st.set_page_config(page_title="跨境电商创业决策工作台", page_icon="🧭", layout="wide")

# =====================================================================
# 共享数据（基于 B1 项目真实计算；采集 2026-09-06）
# =====================================================================
REFERRAL_PRESETS = {
    "工业品/工具/多数品类（约15%）": 15.0,
    "家居家具（约15%）": 15.0,
    "消费电子配件（约15%）": 15.0,
    "服饰（约17%）": 17.0,
    "珠宝（约20%）": 20.0,
    "自定义": None,
}
FBA_HINTS = {
    "小件标准 <1 lb（约$3.0-4.0）": 3.5,
    "标准件 1-2 lb（约$4.5-6.0）": 5.0,
    "大件/超重（约$8.0 起）": 8.0,
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


# =====================================================================
# 页面
# =====================================================================
def page_overview():
    st.title("🧭 跨境电商创业决策工作台")
    st.caption("基于 B1 项目：5 家中国跨境电商上市公司公开财报 + 海关宏观数据（2025 年报口径，采集 2026-09-06）")
    st.markdown("""
这是一套“先算清单件账，再选品类市场，最后持续体检”的决策工具：

| 页 | 回答 | 靠什么 |
|---|---|---|
| 🧮 P1 单位经济测算 | 这件货赚不赚钱 | 售价 - 佣金/FBA/广告/成本 |
| 🧭 P2 选品类助手 | 这个品类能不能做 | 单位经济 + 风险规则 |
| 🌍 P3 市场选择器 | 先做哪个市场 | 海关数据 + 致欧分地区毛利实证 |
| 🩺 P4 经营健康体检 | 走得长远吗？何时转型 | 对标 5 家上市公司基准 + 危险信号 |

**数据支持的边界（重要）**：公开数据能给你“基准、可行性、风险信号与转型阈值”；
“具体品类的需求热度、供应商报价”需要私有数据（卖家后台/选品工具/报价单），工具会提示你要补什么。
""")
    st.divider()
    st.markdown("**结论速记**：销售费用率是模式分水岭（品牌约22% vs 铺货约35%）；"
                "欧洲毛利高但增长慢；利润≠现金流（安克 2025 OCF/净利 0.19）；行业龙头集中度 <3%。")


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
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{name} · 单位净利 (USD)", f"{r['net']:.2f}", delta=f"{r['net_pct']:.1f}% 净利率")
    m2.metric("盈亏平衡 ACOS %", f"{max(r['be_acos'], 0):.1f}", help="超过该 ACOS 即亏损")
    m3.metric("平台+广告占售价", f"{r['fees']/r['price']*100:.1f}%",
              help=f"佣金 {r['referr']:.2f} + FBA {r['fba']:.2f} + 广告 {r['ad']:.2f}")
    m4.metric("广告前利润 (USD)", f"{r['gross_before_ad']:.2f}")


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
            fig = go.Figure(go.Scatter(x=acos_range, y=nets, mode="lines"))
            fig.add_hline(y=0, line_dash="dash", line_color="red")
            fig.update_layout(xaxis_title="广告 ACOS %", yaxis_title="单位净利 (USD)",
                              title="单位净利 vs ACOS", height=330, margin=dict(t=40, b=10))
            st.plotly_chart(fig, width="stretch", key="sens_a")
        with c2:
            st.subheader("售价拆解（USD，示意）")
            share = pd.DataFrame({
                "项目": ["采购成本(60%)", "头程+其他", "平台佣金", "FBA配送", "广告", "单位净利"],
                "金额": [pa[1]*0.6, pa[1]*0.4 + pa[2] + pa[3], r["referr"], r["fba"], r["ad"], r["net"]]})
            fig = go.Figure(go.Bar(x=share["项目"], y=share["金额"],
                                   marker_color=["#8ecae6"]*5 + ["#2a9d8f"]))
            fig.update_layout(height=330, margin=dict(t=10, b=10), showlegend=False, yaxis_title="USD")
            st.plotly_chart(fig, width="stretch", key="bar_a")
    with tab2:
        st.markdown("**用法**：A=零售散卖；B=整箱/Case Pack（单价改成 8 折、单件 FBA/广告调低）→ 看 ROI 是否成立。")
        ca1, cb1 = st.columns(2)
        with ca1:
            pa = _ui_calc_inputs("方案 A（散卖）", "a2")
        with cb1:
            pb = _ui_calc_inputs("方案 B（整箱/Case Pack）", "b2")
        ra, rb = calc(*pa), calc(*pb)
        cA, cB = st.columns(2)
        with cA:
            _show_result(ra, "方案 A")
        with cB:
            _show_result(rb, "方案 B")
        d = rb["net"] - ra["net"]
        st.metric("方案 B − 方案 A 单位净利差 (USD)", f"{d:+.2f}", help=">0 表示整箱更划算")
        if ra["net"] > 0 and abs(pa[0]-pb[0]) > 0.01:
            st.markdown(f"当前：单价从 ${pa[0]:.0f} 调到 ${pb[0]:.0f}，单件净利变化 {d:+.2f} USD —— "
                        "这就是判断“降单价、提 ROI”是否成立的入口。")
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
    m1, m2, m3 = st.columns(3)
    m1.metric("单位净利 (USD)", f"{r['net']:.2f}")
    m2.metric("净利率 %", f"{r['net_pct']:.1f}")
    m3.metric("盈亏平衡 ACOS %", f"{max(r['be_acos'],0):.1f}")

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
    st.caption("把六个维度按你的情况加权，看哪个市场最值得先做。分数来自公开数据+行业经验（1-5，分越高越有利）。")
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
                 color_continuous_scale="Blues")
    fig.update_layout(height=360, margin=dict(t=20, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(df.drop(columns=["加权得分", "一句话依据"]), width="stretch", hide_index=True)
    with st.expander("各市场的数据依据与打分说明"):
        for _, row in df.iterrows():
            st.markdown(f"**{row['市场']}**：{row['一句话依据']}")
    with st.expander("局限"):
        st.markdown("打分是公开数据+经验的估计，不是精确测算；关税/VAT 等政策变化需实时跟踪；"
                    "“单点突破、先跑通再复制”仍是最稳策略。")


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
        "🏠 概览与边界": page_overview,
        "🧮 P1 单位经济测算": page_calc,
        "🧭 P2 选品类助手": page_category,
        "🌍 P3 市场选择器": page_market,
        "🩺 P4 经营健康体检": page_health,
    }
    with st.sidebar:
        st.title("创业决策工作台")
        choice = st.radio("选择页面", list(pages), label_visibility="collapsed")
        st.divider()
        st.caption("数据：5 家上市公司 2025 年报（akshare）+ 海关宏观；个人学习用途，非投资建议。")
    pages[choice]()


if __name__ == "__main__":
    main()
