# -*- coding: utf-8 -*-
"""
fetch_financials.py — M1 数据底座
==================================
用 akshare 拉取 5 家跨境电商 A 股公司的：
  1) 财务摘要（多期关键指标）       ak.stock_financial_abstract   （新浪财经源）
  2) 主营构成（分产品/行业/地区）    ak.stock_zygc_em              （东方财富源）

输出：
  data/raw/            每家公司原始宽表
  data/consolidated/   合并后的长表 + 年报口径关键指标 + 主营构成汇总
  reports/00_数据字典.md / reports/01_年报关键指标预览.md

注意：
  - 接口数据仅作采集便利；年报 PDF（巨潮资讯）为权威口径，使用前抽查核对。
  - 主营构成接口的"按地区分类"目前粒度到境外/境内；北美/欧洲细分需从年报补。
  - 采集日期 2026-09-06；akshare 接口可能变动，若失败请重试或换源。
"""

from __future__ import annotations

import re
from pathlib import Path

import akshare as ak
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
CON = BASE / "data" / "consolidated"
REP = BASE / "reports"
RAW.mkdir(parents=True, exist_ok=True)
CON.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)

# 公司清单：名称, 股票代码, 东方财富符号
COMPANIES = [
    ("安克创新", "300866", "SZ300866"),
    ("致欧科技", "301376", "SZ301376"),
    ("赛维时代", "301381", "SZ301381"),
    ("华凯易佰", "300592", "SZ300592"),
    ("吉宏股份", "002803", "SZ002803"),
]

# 关注的关键指标（存在才保留；费用明细若缺失，标注需从年报/利润表补）
KEY_METRICS = [
    "营业总收入", "营业收入", "营业成本", "归母净利润", "净利润",
    "经营现金流量净额", "销售费用", "管理费用", "研发费用",
    "毛利率", "净利率", "销售费用率", "存货", "存货周转率",
]
PERIOD_RE = re.compile(r"^\d{8}$")


def period_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if PERIOD_RE.match(str(c))]


def fetch_company(name: str, code: str, sym: str) -> dict:
    print(f"[{name}] 拉取财务摘要与主营构成 ...", flush=True)
    abstract = ak.stock_financial_abstract(symbol=code)          # 新浪
    zygc = ak.stock_zygc_em(symbol=sym)                          # 东财
    zygc.insert(0, "公司名称", name)
    zygc.insert(1, "公司代码", code)

    abstract.to_csv(RAW / f"abstract_{code}.csv", index=False, encoding="utf-8-sig")
    zygc.to_csv(RAW / f"zygc_{sym}.csv", index=False, encoding="utf-8-sig")
    return {"name": name, "code": code, "abstract": abstract, "zygc": zygc}


def main() -> None:
    results = []
    for name, code, sym in COMPANIES:
        results.append(fetch_company(name, code, sym))

    # ---------- 合并 1：财务摘要长表 ----------
    frames = []
    for r in results:
        df = r["abstract"].copy()
        cols = period_columns(df)
        long = df.melt(id_vars=["选项", "指标"], value_vars=cols,
                       var_name="报告期", value_name="数值")
        long.insert(0, "公司代码", r["code"])
        long.insert(1, "公司名称", r["name"])
        frames.append(long)
    abstract_long = pd.concat(frames, ignore_index=True)
    abstract_long["数值"] = pd.to_numeric(abstract_long["数值"], errors="coerce")
    abstract_long.to_csv(CON / "financial_abstract_long.csv", index=False, encoding="utf-8-sig")

    # ---------- 合并 2：年报口径关键指标（报告期以 1231 结尾） ----------
    rows = []
    for r in results:
        df = r["abstract"].copy()
        ann_cols = [c for c in period_columns(df) if c.endswith("1231")]
        sub = df[df["指标"].isin(KEY_METRICS)][["指标"] + ann_cols].copy()
        sub.insert(0, "公司名称", r["name"])
        sub.insert(1, "公司代码", r["code"])
        rows.append(sub)
    annual = pd.concat(rows, ignore_index=True)
    annual.to_csv(CON / "annual_key_metrics.csv", index=False, encoding="utf-8-sig")

    # ---------- 合并 3：主营构成汇总 ----------
    zygc_all = pd.concat([r["zygc"] for r in results], ignore_index=True)
    zygc_all.to_csv(CON / "zygc_all.csv", index=False, encoding="utf-8-sig")

    # ---------- 公司清单 ----------
    pd.DataFrame(COMPANIES, columns=["公司名称", "代码", "东财符号"]).to_csv(
        CON / "companies.csv", index=False, encoding="utf-8-sig")

    # ---------- 抽查：安克创新 2025 年报营收 ----------
    anker = annual[(annual["公司名称"] == "安克创新") & (annual["指标"] == "营业总收入")]
    anker_2025 = anker["20251231"].iloc[0] if not anker.empty and "20251231" in anker.columns else None
    reported = 30514403376.92  # 公开报道的 2025 全年营收（元），用于核对
    check = "一致 ✅" if anker_2025 is not None and abs(float(anker_2025) - reported) < 1e6 else f"不一致（接口值 {anker_2025} vs 报道 {reported}）"

    # ---------- 数据字典 ----------
    dict_lines = [
        "# 00 · 数据字典（M1）", "",
        "> 采集日期：2026-09-06 ｜ 数据源：新浪财经（财务摘要）、东方财富（主营构成）｜ 权威口径：年报 PDF（巨潮资讯）",
        "",
        "## 文件清单", "",
        "### data/raw/（每家公司原始表）", "",
        "| 文件 | 内容 | 关键列 |",
        "|---|---|---|",
        "| abstract_代码.csv | 财务摘要（宽表：指标 × 报告期） | 选项、指标、YYYYMMDD… |",
        "| zygc_符号.csv | 主营构成（分产品/行业/地区，多期） | 公司名称、报告日期、分类类型、主营构成、主营收入、收入比例、毛利率 |",
        "",
        "### data/consolidated/（合并表）", "",
        "| 文件 | 内容 |",
        "|---|---|",
        "| companies.csv | 5 家公司清单 |",
        "| financial_abstract_long.csv | 财务摘要长表（公司 × 报告期 × 指标 × 数值），便于过滤/透视 |",
        "| annual_key_metrics.csv | 年报口径（报告期=12/31）关键指标，用于跨公司年度对比 |",
        "| zygc_all.csv | 5 家主营构成合并（含公司名称列） |",
        "",
        "## 口径与注意", "",
        "- 半年报/季报为**累计值**，跨期对比要对齐期间（同比用同期间）；",
        "- 主营构成接口的按地区分类目前到**境外/境内**；北美/欧洲细分需从年报 PDF 提取；",
        "- 财务摘要未覆盖的指标（如销售费用明细、存货明细等）需从**利润表/年报**补充；",
        "- akshare 接口返回上限可能截断早期报告期（如主营构成约 200 行），近期数据完整；",
        "- **抽查**：安克创新 2025 全年营业总收入 接口值 ≈ 305.1 亿元，" + check,
        "",
        "## 下一步（M2/M3）", "",
        "- M2 宏观层：海关跨境电商进出口数据 + 行业报告；",
        "- M3 中观：用 annual_key_metrics + zygc_all 做 5 家财务对比与三维分析。",
    ]
    (REP / "00_数据字典.md").write_text("\n".join(dict_lines), encoding="utf-8")

    # ---------- 预览：年报营收/归母净利（手写 markdown，避免依赖 tabulate） ----------
    def annual_pivot(metric: str) -> pd.DataFrame:
        sub = annual[annual["指标"] == metric][["公司名称"] +
                                               [c for c in annual.columns if c.endswith("1231")]]
        sub = sub.drop_duplicates(subset=["公司名称"]).reset_index(drop=True)
        return sub

    def to_md_table(df: pd.DataFrame, title: str) -> str:
        keep = sorted([c for c in df.columns if c.endswith("1231")], reverse=True)[:3]
        d2 = df[["公司名称"] + keep].copy()
        d2.columns = ["公司名称"] + [c[:4] + "年报" for c in keep]
        lines = [f"### {title}", "", "| " + " | ".join(d2.columns) + " |",
                 "|" + "|".join(["---"] * len(d2.columns)) + "|"]
        for _, row in d2.iterrows():
            cells = []
            for v in row.values:
                try:
                    cells.append(f"{float(v)/1e8:.1f}" if pd.notna(v) else "-")
                except Exception:
                    cells.append(str(v))
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    preview_md = ("# 01 · 年报关键指标预览（单位：人民币亿元）\n\n"
                  + to_md_table(annual_pivot("营业总收入"), "营业总收入")
                  + "\n\n" + to_md_table(annual_pivot("归母净利润"), "归母净利润") + "\n")
    (REP / "01_年报关键指标预览.md").write_text(preview_md, encoding="utf-8")

    # ---------- 控制台摘要 ----------
    print("\n========== M1 完成 ==========")
    print("抽查 安克创新 2025 全年营收：", check)
    print("\n各公司数据规模：")
    for r in results:
        print(f"  {r['name']}: 摘要 {r['abstract'].shape}，主营构成 {r['zygc'].shape}")
    print("\n合并表：")
    for f in sorted(CON.glob("*.csv")):
        print(f"  {f.name}  ({sum(1 for _ in f.open())} 行)")
    print("\n报告：", REP / "00_数据字典.md", "|", REP / "01_年报关键指标预览.md")


if __name__ == "__main__":
    main()
