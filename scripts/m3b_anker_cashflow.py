# -*- coding: utf-8 -*-
"""
m3b_anker_cashflow.py — 深挖安克创新 2025 现金流异常
====================================================
问题：2025 归母净利 25.5 亿，但经营现金流仅 ~4.8 亿（OCF/净利≈0.19，2024 约 1.3）。
方法：拉年报现金流量表（直接法 + 调节附表）与资产负债表，定位差异来源（营运资金变动/存货/应收/应付）。
输出：reports/03_安克现金流深挖.md + 原始表 data/raw、合并表 data/consolidated
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import akshare as ak

BASE = Path(__file__).resolve().parents[1]
RAW, CON, REP = BASE/"data"/"raw", BASE/"data"/"consolidated", BASE/"reports"
YI = 1e8

# ---------- 1) 现金流量表（年报） ----------
cf = ak.stock_cash_flow_sheet_by_yearly_em(symbol="SZ300866")
cf["REPORT_DATE"] = pd.to_datetime(cf["REPORT_DATE"])
cf = cf[(cf["REPORT_DATE"].dt.month == 12) & (cf["REPORT_DATE"].dt.day == 31)]
cf["年份"] = cf["REPORT_DATE"].dt.year
cf = cf[cf["年份"].between(2023, 2025)].sort_values("年份")
cf.to_csv(RAW/"anker_cashflow_annual.csv", index=False, encoding="utf-8-sig")

def pick(df, field):
    if field not in df.columns:
        return None
    s = df[field]
    return s

def yi(df, field):
    v = pick(df, field)
    if v is None:
        return None
    return v.apply(lambda x: round(x / YI, 2) if pd.notna(x) else None)

cols = {
    "销售商品收到现金": yi(cf, "SALES_SERVICES"),
    "经营活动现金流入小计": yi(cf, "TOTAL_OPERATE_INFLOW"),
    "购买商品支付现金": yi(cf, "BUY_SERVICES"),
    "支付给职工现金": yi(cf, "PAY_STAFF_CASH"),
    "支付的各项税费": yi(cf, "PAY_ALL_TAX"),
    "经营活动现金流出小计": yi(cf, "TOTAL_OPERATE_OUTFLOW"),
    "经营现金流净额(主表)": yi(cf, "NETCASH_OPERATE"),
    "投资现金流净额": yi(cf, "NETCASH_INVEST"),
    "筹资现金流净额": yi(cf, "NETCASH_FINANCE"),
    "期末现金余额": yi(cf, "END_CCE"),
}
direct = pd.DataFrame({k: v.values if v is not None else None for k, v in cols.items()},
                      index=[f"{y}年报" for y in cf["年份"]])
# 调节附表关键项
note_cols = {
    "净利润": yi(cf, "NETPROFIT"),
    "资产减值准备": yi(cf, "ASSET_IMPAIRMENT"),
    "折旧摊销(固资等)": yi(cf, "FA_IR_DEPR"),
    "无形资产摊销": yi(cf, "IA_AMORTIZE"),
    "财务费用": yi(cf, "FINANCE_EXPENSE"),
    "投资损失": yi(cf, "INVEST_LOSS"),
    "递延所得税": yi(cf, "DEFER_TAX"),
    "存货的减少(减:增加)": yi(cf, "INVENTORY_REDUCE"),
    "经营性应收减少(减:增加)": yi(cf, "OPERATE_RECE_REDUCE"),
    "经营性应付增加": yi(cf, "OPERATE_PAYABLE_ADD"),
    "其他": yi(cf, "OTHER"),
    "经营现金流净额(附表)": yi(cf, "NETCASH_OPERATENOTE"),
}
note = pd.DataFrame({k: v.values if v is not None else None for k, v in note_cols.items()},
                    index=[f"{y}年报" for y in cf["年份"]])
cf_out = direct.join(note, rsuffix="_附表")
cf_out.to_csv(CON/"anker_cashflow_annual_整理.csv", encoding="utf-8-sig")

# ---------- 2) 资产负债表：营运资金变动 ----------
bs = ak.stock_balance_sheet_by_yearly_em(symbol="SZ300866")
bs["REPORT_DATE"] = pd.to_datetime(bs["REPORT_DATE"])
bs = bs[(bs["REPORT_DATE"].dt.month == 12) & (bs["REPORT_DATE"].dt.day == 31)]
bs["年份"] = bs["REPORT_DATE"].dt.year
bs = bs[bs["年份"].between(2023, 2025)].sort_values("年份")
bs.to_csv(RAW/"anker_balance_sheet_annual.csv", index=False, encoding="utf-8-sig")

bs_cols = {
    "存货": "INVENTORY",
    "应收账款": "ACCOUNTS_RECE",
    "应收票据": "NOTE_RECE",
    "其他应收款": "OTHER_RECE",
    "合同资产": "CONTRACT_ASSET",
    "应付账款": "ACCOUNTS_PAYABLE",
    "应付票据": "NOTE_PAYABLE",
    "合同负债": "CONTRACT_LIAB",
}
bs_series = {zh: yi(bs, en) for zh, en in bs_cols.items()}
bs_df = pd.DataFrame({zh: (v.values if v is not None else None) for zh, v in bs_series.items()},
                     index=[f"{y}年报" for y in bs["年份"]])

# 营运资金变动 = Δ(存货+应收类) - Δ(应付类)（增加=占用现金）
def delta(zh):
    s = bs_df[zh]
    return None if s.isna().any() else round(s.iloc[-1] - s.iloc[-2], 2)

wc = pd.DataFrame({
    "2025较2024变动(亿)": [delta(zh) for zh in bs_cols],
    "2024较2023变动(亿)": [round((bs_df[zh].iloc[-2] - bs_df[zh].iloc[-3]), 2) if not bs_df[zh].isna().any() else None for zh in bs_cols],
}, index=list(bs_cols))
bs_df.to_csv(CON/"anker_balance_sheet_annual_整理.csv", encoding="utf-8-sig")

# 汇总到控制台
pd.set_option("display.width", 200)
print("===== 安克 现金流量表（直接法，亿元） =====")
print(direct.T.to_string())
print("\n===== 调节附表（亿元；正负号含义以年报为准，负值通常=占用现金） =====")
print(note.T.to_string())
print("\n===== 资产负债表主要科目（亿元） =====")
print(bs_df.T.to_string())
print("\n===== 营运资金变动 =====")
print(wc.to_string())
