# -*- coding: utf-8 -*-
"""
m3_company_analysis.py — M3 中观：5 家公司财务对比
====================================================
基于 M1 数据底座 + 利润表明细，产出：
  data/consolidated/company_metrics_annual.csv  逐年核心指标（亿/率）
  data/consolidated/profit_sheet_annual.csv     销售/研发费用（年报口径）
  reports/figures/m3_*.png                      对比图（英文标签）
  reports/02_公司对比分析.md                      对比报告（中文）
"""

from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt
for fp in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
           "/System/Library/Fonts/Hiragino Sans GB.ttc"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception:
        pass
plt.rcParams["font.family"] = "PingFang SC, Hiragino Sans GB, STHeiti, sans-serif"
plt.rcParams["axes.unicode_minus"] = False
import numpy as np
import pandas as pd
import akshare as ak

BASE = Path(__file__).resolve().parents[1]
RAW, CON, REP = BASE/"data"/"raw", BASE/"data"/"consolidated", BASE/"reports"
FIG = REP/"figures"; FIG.mkdir(parents=True, exist_ok=True)

COMPANIES = [("安克创新","300866","SZ300866"),("致欧科技","301376","SZ301376"),
             ("赛维时代","301381","SZ301381"),("华凯易佰","300592","SZ300592"),
             ("吉宏股份","002803","SZ002803")]
YEARS = [2022, 2023, 2024, 2025]

# ---------- 读取年报关键指标（含毛利率/存货周转率等） ----------
ann = pd.read_csv(CON/"annual_key_metrics.csv")
ann = ann.drop_duplicates(subset=["公司名称","指标"])
period_cols = [str(c) for c in ann.columns if str(c).isdigit()]

def mval(company: str, metric: str, year: int):
    key = f"{year}1231"
    if key not in ann.columns:
        return None
    row = ann[(ann["公司名称"]==company)&(ann["指标"]==metric)]
    if row.empty:
        return None
    v = row[key].iloc[0]
    return None if pd.isna(v) else float(v)

# ---------- 利润表明细（销售/研发费用） ----------
profit_rows, profit_raw_all = [], []
for name, code, sym in COMPANIES:
    print(f"[{name}] 拉取利润表明细 ...", flush=True)
    df = ak.stock_profit_sheet_by_yearly_em(symbol=sym)
    keep = [c for c in df.columns if c in
            ("REPORT_DATE","TOTAL_OPERATE_INCOME","OPERATE_INCOME","SALE_EXPENSE",
             "MANAGE_EXPENSE","RESEARCH_EXPENSE","ME_RESEARCH_EXPENSE","FINANCE_EXPENSE")]
    df = df[keep].copy()
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"])
    df = df[(df["REPORT_DATE"].dt.month==12)&(df["REPORT_DATE"].dt.day==31)]
    df["year"] = df["REPORT_DATE"].dt.year
    df.insert(0, "公司名称", name); df.insert(1, "公司代码", code)
    df.to_csv(RAW/f"profit_sheet_{code}.csv", index=False, encoding="utf-8-sig")
    profit_raw_all.append(df)
    for _, r in df.iterrows():
        y = int(r["year"])
        rev = r.get("TOTAL_OPERATE_INCOME")
        sale = r.get("SALE_EXPENSE")
        rd = r.get("ME_RESEARCH_EXPENSE")
        if pd.isna(rd):
            rd = r.get("RESEARCH_EXPENSE")
        profit_rows.append({"公司名称":name,"年份":y,
            "营业收入": None if pd.isna(rev) else float(rev),
            "销售费用": None if pd.isna(sale) else float(sale),
            "研发费用": None if pd.isna(rd) else float(rd)})
profit_annual = pd.DataFrame(profit_rows).sort_values(["公司名称","年份"])
profit_annual.to_csv(CON/"profit_sheet_annual.csv", index=False, encoding="utf-8-sig")

def psale(name, year):
    r = profit_annual[(profit_annual["公司名称"]==name)&(profit_annual["年份"]==year)]
    if r.empty: return None, None, None
    row = r.iloc[0]
    rev = row["营业收入"]; sale = row["销售费用"]; rd = row["研发费用"]
    if rev is None or rev == 0: return None, None, None
    sale_rate = None if sale is None else sale/rev*100
    rd_rate = None if rd is None else rd/rev*100
    return sale_rate, rd_rate, (None if sale is None else sale/1e8)

# ---------- 逐年指标表 ----------
rows = []
for name, code, sym in COMPANIES:
    for y in YEARS:
        rev = mval(name,"营业总收入",y)
        np_ = mval(name,"归母净利润",y)
        ocf = mval(name,"经营现金流量净额",y)
        inv = mval(name,"存货周转率",y)
        gm = mval(name,"毛利率",y)   # 摘要自带毛利率，单位 %
        if rev is None:
            continue
        rev_y, np_y, ocf_y = rev/1e8, (np_/1e8 if np_ is not None else None), (ocf/1e8 if ocf is not None else None)
        prev = mval(name,"营业总收入",y-1)
        growth = None if prev in (None,0) else (rev/prev-1)*100
        npm = None if np_ is None else np_/rev*100
        ocf2np = None if (np_ in (None,0) or ocf is None) else ocf/np_
        sale_rate, rd_rate, sale_yi = psale(name, y)
        rows.append({"公司名称":name,"年份":y,"营业收入亿":round(rev_y,1),
            "营收同比%": None if growth is None else round(growth,1),
            "毛利率%": None if gm is None else round(gm,1),
            "归母净利率%": None if npm is None else round(npm,1),
            "销售费用率%": None if sale_rate is None else round(sale_rate,1),
            "研发费用率%": None if rd_rate is None else round(rd_rate,1),
            "归母净利润亿": np_y, "经营现金流亿": ocf_y,
            "OCF/归母净利": None if ocf2np is None else round(ocf2np,2),
            "存货周转率": inv})
metrics = pd.DataFrame(rows)
metrics.to_csv(CON/"company_metrics_annual.csv", index=False, encoding="utf-8-sig")
print("company_metrics_annual.csv 已生成", metrics.shape)

# ---------- 图 1：营收 ----------
fig, ax = plt.subplots(figsize=(9,4.5))
names = [c[0] for c in COMPANIES]
NAMES_EN = {"安克创新":"Anker","致欧科技":"ZOYO","赛维时代":"Sailvan","华凯易佰":"Huakai","吉宏股份":"Jihong"}
names_en = [NAMES_EN[n] for n in names]
x = np.arange(len(names)); w=0.26
for i,y in enumerate([2023,2024,2025]):
    vals=[metrics[(metrics.公司名称==n)&(metrics.年份==y)]["营业收入亿"].iloc[0] if len(metrics[(metrics.公司名称==n)&(metrics.年份==y)]) else None for n in names]
    ax.bar(x+(i-1)*w, vals, w, label=str(y))
ax.set_xticks(x); ax.set_xticklabels(names_en, rotation=15)
ax.set_ylabel("Revenue (RMB 100M)"); ax.set_title("Revenue by company, 2023-2025")
ax.legend(); fig.tight_layout(); fig.savefig(FIG/"m3_revenue.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图 2：2025 毛利 vs 净利 ----------
fig, ax = plt.subplots(figsize=(9,4.5))
gm=[metrics[(metrics.公司名称==n)&(metrics.年份==2025)]["毛利率%"].iloc[0] if len(metrics[(metrics.公司名称==n)&(metrics.年份==2025)]) else None for n in names]
npm=[metrics[(metrics.公司名称==n)&(metrics.年份==2025)]["归母净利率%"].iloc[0] if len(metrics[(metrics.公司名称==n)&(metrics.年份==2025)]) else None for n in names]
ax.bar(x-w/2, gm, w, label="Gross margin %", color="#2a9d8f")
ax.bar(x+w/2, npm, w, label="Net margin %", color="#e76f51")
for i,(g,n) in enumerate(zip(gm,npm)):
    if g is not None: ax.text(i-w/2, g+0.5, f"{g:.1f}", ha="center", fontsize=8)
    if n is not None: ax.text(i+w/2, n+0.5, f"{n:.1f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(names_en, rotation=15)
ax.set_ylabel("%"); ax.set_title("2025 gross vs net margin (gap = expense burden)")
ax.legend(); fig.tight_layout(); fig.savefig(FIG/"m3_margin_2025.png", bbox_inches="tight"); plt.close(fig)

# ---------- 图 3：销售费用率趋势 ----------
fig, ax = plt.subplots(figsize=(9,4.5))
for n, ne in zip(names, names_en):
    sub = metrics[(metrics.公司名称==n)].sort_values("年份")
    yy = sub["年份"]; sr = sub["销售费用率%"]
    ax.plot(yy, sr, marker="o", label=ne)
ax.set_xlabel("Year"); ax.set_ylabel("Selling expense rate %")
ax.set_title("Selling expense ratio trend")
ax.legend(); fig.tight_layout(); fig.savefig(FIG/"m3_sale_expense_rate.png", bbox_inches="tight"); plt.close(fig)

# ---------- 结构表：地区 & 产品（最新年报） ----------
zygc = pd.read_csv(CON/"zygc_all.csv")
zygc = zygc[zygc["报告日期"].astype(str).str.contains("12-31")].copy()
zygc["报告年份"] = zygc["报告日期"].astype(str).str[:4].astype(int)

def latest_annual_structure(company, cat):
    sub = zygc[(zygc["公司名称"]==company)&(zygc["分类类型"]==cat)]
    if sub.empty: return pd.DataFrame()
    y = sub["报告年份"].max()
    s = sub[sub["报告年份"]==y].copy()
    s["收入比例%"] = (s["收入比例"]*100).round(1)
    s["毛利率%"] = (s["毛利率"]*100).round(1)
    rev_yi = metrics[(metrics.公司名称==company)&(metrics.年份==y)]["营业收入亿"]
    rev_yi = rev_yi.iloc[0] if len(rev_yi) else None
    s["约收入亿"] = (s["收入比例"]* (rev_yi or 0)).round(1)
    return s, y

md = ["# 02 · M3 公司对比分析（初版）", "",
      "> 数据：akshare（新浪/东财），年报口径（12-31）；金额单位：人民币亿元。采集 2026-09-06。",
      "", "## 一、2025 年概览（关键比率）", ""]

m25 = metrics[metrics["年份"]==2025].set_index("公司名称")
cols = ["营业收入亿","营收同比%","毛利率%","归母净利率%","销售费用率%","研发费用率%","OCF/归母净利","存货周转率"]
def to_md_table(df):
    d = df.copy()
    for c in d.columns:
        if d[c].dtype == float:
            d[c] = d[c].round(1)
    lines=["| "+" | ".join(map(str,d.columns))+" |","|"+"|".join(["---"]*len(d.columns))+"|"]
    for _,r in d.iterrows():
        lines.append("| "+" | ".join("-" if pd.isna(v) else str(v) for v in r.values)+" |")
    return "\n".join(lines)
md.append(to_md_table(m25[cols].reset_index()))
md.append("")

# 增长
g = metrics[metrics["年份"].isin([2023,2024,2025])].pivot(index="公司名称",columns="年份",values="营业收入亿").reset_index()
g["23→24 同比%"] = ((g[2024]/g[2023]-1)*100).round(1) if 2023 in g else "-"
g["24→25 同比%"] = ((g[2025]/g[2024]-1)*100).round(1)
md += ["## 二、营收规模与增速（亿元）", "", to_md_table(g), ""]

# 地区与产品
md.append("## 三、地区结构（最新年报，收入占比与约收入）")
for name,code,sym in COMPANIES:
    s, y = latest_annual_structure(name,"按地区分类")
    if s.empty:
        md.append(f"\n### {name}（{y}）：暂无地区分类数据\n"); continue
    md.append(f"\n### {name}（{y} 年报）\n")
    md.append(to_md_table(s[["主营构成","收入比例%","毛利率%","约收入亿"]]))
md.append("\n## 四、产品结构 Top3（最新年报）")
for name,code,sym in COMPANIES:
    s, y = latest_annual_structure(name,"按产品分类")
    if s.empty:
        md.append(f"\n### {name}（{y}）：暂无产品分类数据\n"); continue
    s = s.sort_values("收入比例%", ascending=False).head(3)
    md.append(f"\n### {name}（{y} 年报）\n")
    md.append(to_md_table(s[["主营构成","收入比例%","毛利率%","约收入亿"]]))
md.append("")

md += ["## 五、图表", "",
       "![revenue](figures/m3_revenue.png)", "",
       "![margin](figures/m3_margin_2025.png)", "",
       "![sale_expense](figures/m3_sale_expense_rate.png)", "",
       "## 六、初步发现（待结合数字精修）", "",
       "- （M3 首版由脚本生成数据表与图，业务解读将在下一步结合真实数字补全。）", ""]

(REP/"02_公司对比分析.md").write_text("\n".join(md), encoding="utf-8")
print("报告已生成：", REP/"02_公司对比分析.md")
print("\n=== 2025 概览 ===")
print(m25[cols].reset_index().to_string(index=False))
