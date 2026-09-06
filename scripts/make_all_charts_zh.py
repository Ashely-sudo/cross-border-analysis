# -*- coding: utf-8 -*-
"""
make_all_charts_zh.py — 用已落盘的 CSV 重画全部中文图表
========================================================
读入：
  data/consolidated/m2_macro_source.csv           宏观（手工整理的海关官方口径）
  data/consolidated/company_metrics_annual.csv    M3 公司指标（脚本生成）
  data/consolidated/anker_cashflow_annual_整理.csv 安克现金流（脚本生成）
输出（中文标签）：
  reports/figures/m2_market_size.png / m2_export_destination.png
  reports/figures/m3_revenue.png / m3_margin_2025.png / m3_sale_expense_rate.png
  reports/figures/m3b_anker_cashflow.png
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt

for fp in ["/System/Library/Fonts/Hiragino Sans GB.ttc",
           "/Library/Fonts/Arial Unicode.ttf",
           "/System/Library/Fonts/Supplemental/Songti.ttc"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception as e:
        print("font fail", fp, e)
plt.rcParams["font.family"] = ["Hiragino Sans GB", "Arial Unicode MS", "Songti SC", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
print("font resolved:", font_manager.findfont("Hiragino Sans GB"))

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CON, FIG = BASE / "data" / "consolidated", BASE / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, GREEN, RED = "#2F5AA8", "#C97B1E", "#2a9d8f", "#e76f51"
GRAY = "#8a93a3"
ORDER = ["安克创新", "致欧科技", "赛维时代", "华凯易佰", "吉宏股份"]

# ---------- 1) 宏观源表（手工整理：海关总署/商务部官方口径，可复核） ----------
macro_src = """年份,口径,进出口万亿,同比pct
2023,终核,2.38,15.6
2024,修订口径,2.71,14.0
2025,终核,2.84,4.8
"""
(CON / "m2_macro_source.csv").write_text(macro_src, encoding="utf-8-sig")

# ---------- 图1：行业规模 ----------
m2 = pd.read_csv(CON / "m2_macro_source.csv", encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
bars = ax.bar(m2["年份"].astype(str), m2["进出口万亿"], color=[BLUE, "#7d9ad1", GREEN], width=0.5)
for b, (_, r) in zip(bars, m2.iterrows()):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.04, f"{r['进出口万亿']:.2f}\n同比 +{r['同比pct']:.1f}%",
            ha="center", va="bottom", fontsize=10)
ax.set_ylim(0, 3.6)
ax.set_ylabel("跨境电商进出口规模（万亿元）")
ax.set_title("中国跨境电商进出口规模（海关口径，修订后）")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m2_market_size.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图2：出口目的国 ----------
dest = pd.DataFrame({"地区": ["美国", "英国", "德国", "其他"], "占比pct": [36.2, 11.7, 5.7, 46.4]})
fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=160)
cols = [BLUE, ORANGE, GREEN, "#b9c2cf"]
wedges, _, autotexts = ax.pie(dest["占比pct"], labels=dest["地区"], autopct="%1.1f%%",
                               colors=cols, startangle=90, counterclock=False,
                               textprops={"fontsize": 10})
for a in autotexts:
    a.set_color("white"); a.set_fontweight("bold")
ax.set_title("中国跨境电商出口目的国占比（2024）")
fig.tight_layout(); fig.savefig(FIG / "m2_export_destination.png", bbox_inches="tight"); plt.close(fig)

# ---------- 读 M3 指标表 ----------
m3 = pd.read_csv(CON / "company_metrics_annual.csv", encoding="utf-8-sig")

# ---------- 图3：营收对比 ----------
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
x = np.arange(len(ORDER)); w = 0.26
for i, y in enumerate([2023, 2024, 2025]):
    vals = [m3[(m3["公司名称"] == n) & (m3["年份"] == y)]["营业收入亿"].iloc[0]
            if len(m3[(m3["公司名称"] == n) & (m3["年份"] == y)]) else np.nan for n in ORDER]
    ax.bar(x + (i-1)*w, vals, w, label=str(y), color=[BLUE, ORANGE, GREEN][i])
ax.set_xticks(x); ax.set_xticklabels(ORDER, rotation=15)
ax.set_ylabel("营业收入（亿元）"); ax.set_title("2023–2025 营业收入对比（5 家上市公司）")
ax.legend(title="年份"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m3_revenue.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图4：2025 毛利 vs 净利 ----------
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
gm = [m3[(m3["公司名称"] == n) & (m3["年份"] == 2025)]["毛利率%"].iloc[0] for n in ORDER]
npm = [m3[(m3["公司名称"] == n) & (m3["年份"] == 2025)]["归母净利率%"].iloc[0] for n in ORDER]
ax.bar(x - w/2, gm, w, label="毛利率", color=GREEN)
ax.bar(x + w/2, npm, w, label="归母净利率", color=RED)
for i, (g, n) in enumerate(zip(gm, npm)):
    ax.text(i - w/2, g + 0.6, f"{g:.1f}", ha="center", fontsize=8.5)
    ax.text(i + w/2, n + 0.6, f"{n:.1f}", ha="center", fontsize=8.5)
ax.set_xticks(x); ax.set_xticklabels(ORDER, rotation=15)
ax.set_ylim(0, 55)
ax.set_ylabel("比率（%）"); ax.set_title("2025 毛利率 vs 归母净利率：中间差的是费用")
ax.legend(); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m3_margin_2025.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图5：销售费用率趋势 ----------
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
palette = [BLUE, ORANGE, GREEN, RED, GRAY]
for n, c in zip(ORDER, palette):
    sub = m3[m3["公司名称"] == n].sort_values("年份")
    ax.plot(sub["年份"], sub["销售费用率%"], marker="o", label=n, color=c)
ax.set_xlabel("年份"); ax.set_ylabel("销售费用率（%）"); ax.set_title("销售费用率趋势（2022–2025）")
ax.legend(ncol=2, fontsize=9); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m3_sale_expense_rate.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图6：安克现金流 ----------
cf = pd.read_csv(CON / "anker_cashflow_annual_整理.csv", index_col=0, encoding="utf-8-sig")
years = ["2023", "2024", "2025"]
np_ = [cf.loc[f"{y}年报", "净利润"] for y in years]
ocf = [cf.loc[f"{y}年报", "经营现金流净额(主表)"] for y in years]
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
b1 = ax.bar(np.arange(3) - 0.2, np_, 0.4, label="净利润", color=BLUE)
b2 = ax.bar(np.arange(3) + 0.2, ocf, 0.4, label="经营现金流净额", color=ORANGE)
for i, (n, o) in enumerate(zip(np_, ocf)):
    ax.text(i - 0.2, n + 0.5, f"{n:.1f}", ha="center", fontsize=9)
    ax.text(i + 0.2, o + (1.0 if o >= 0 else -2.5), f"{o:.1f}", ha="center", fontsize=9)
ax.axhline(0, color=GRAY, lw=0.8)
ax.set_xticks(np.arange(3)); ax.set_xticklabels(years)
ax.set_ylabel("金额（亿元）"); ax.set_title("安克创新：净利润 vs 经营现金流（2023–2025）")
ax.legend(); ax.spines[["top", "right"]].set_visible(False)
ax.text(1.6, max(np_)*0.75, "2025 OCF/净利≈0.19\n钱被存货/应收占住", fontsize=9, color=RED)
fig.tight_layout(); fig.savefig(FIG / "m3b_anker_cashflow.png", bbox_inches="tight"); plt.close(fig)

print("6 张中文图已生成到 reports/figures/")
