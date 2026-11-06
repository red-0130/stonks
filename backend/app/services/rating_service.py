import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.services.data_service import get_financial_statements, get_ticker_info
from app.cache import get_cached, set_cached

def calculate_stock_rating(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"rating:{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    info_data = get_ticker_info(ticker)
    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info or {}

    # 1. P/E Ratio (< 20)
    pe_val = info_data.get("pe_ratio")
    if pe_val is None:
        pe_val = info.get("trailingPE") or info.get("forwardPE")
    pe_passed = (pe_val is not None) and (pe_val > 0) and (pe_val < 20.0)

    # 2. Debt to Equity (< 1.0)
    de_val = info_data.get("debt_to_equity")
    if de_val is None and info.get("debtToEquity") is not None:
        de_val = float(info.get("debtToEquity")) / 100.0
    de_passed = (de_val is not None) and (de_val < 1.0)

    # 3. ROE (> 15%)
    roe_val = info.get("returnOnEquity")
    if roe_val is not None:
        roe_pct = round(float(roe_val) * 100, 2)
    else:
        roe_pct = None
    roe_passed = (roe_pct is not None) and (roe_pct > 15.0)

    # 4. EBIT / Operating Margin (> 10%)
    ebit_margin_val = info.get("operatingMargins")
    if ebit_margin_val is not None:
        ebit_margin_pct = round(float(ebit_margin_val) * 100, 2)
    else:
        ebit_margin_pct = None
    ebit_margin_passed = (ebit_margin_pct is not None) and (ebit_margin_pct > 10.0)

    # 5. Gross Margin (> 40%)
    gross_margin_val = info.get("grossMargins")
    if gross_margin_val is not None:
        gross_margin_pct = round(float(gross_margin_val) * 100, 2)
    else:
        gross_margin_pct = None
    gross_margin_passed = (gross_margin_pct is not None) and (gross_margin_pct > 40.0)

    # 6. ROIC (> 15%)
    # NOPAT / Invested Capital or Operating Income / (Total Assets - Current Liabilities)
    roic_pct = None
    try:
        bs = yf_ticker.balance_sheet
        inc = yf_ticker.income_stmt
        if bs is not None and not bs.empty and inc is not None and not inc.empty:
            recent_date = inc.columns[0]
            ebit = inc.loc["Operating Income", recent_date] if "Operating Income" in inc.index else (inc.loc["EBIT", recent_date] if "EBIT" in inc.index else None)
            tax_exp = inc.loc["Tax Provision", recent_date] if "Tax Provision" in inc.index else 0
            pretax_inc = inc.loc["Pretax Income", recent_date] if "Pretax Income" in inc.index else None

            tax_rate = (tax_exp / pretax_inc) if pretax_inc and pretax_inc > 0 else 0.21
            if tax_rate < 0 or tax_rate > 0.5:
                tax_rate = 0.21

            nopat = ebit * (1 - tax_rate) if ebit is not None else None

            # Invested capital
            total_equity = bs.loc["Stockholders Equity", bs.columns[0]] if "Stockholders Equity" in bs.index else (bs.loc["Total Equity Gross Minority Interest", bs.columns[0]] if "Total Equity Gross Minority Interest" in bs.index else None)
            total_debt = bs.loc["Total Debt", bs.columns[0]] if "Total Debt" in bs.index else 0
            cash = bs.loc["Cash And Cash Equivalents", bs.columns[0]] if "Cash And Cash Equivalents" in bs.index else 0

            if total_equity is not None and nopat is not None:
                invested_capital = float(total_equity) + float(total_debt or 0) - float(cash or 0)
                if invested_capital > 0:
                    roic_pct = round((float(nopat) / invested_capital) * 100, 2)
    except Exception:
        pass

    if roic_pct is None:
        # Fallback approximation from ROA / ROE
        roa = info.get("returnOnAssets")
        if roa and roe_val:
            roic_pct = round(((float(roa) + float(roe_val)) / 2.0) * 100, 2)

    roic_passed = (roic_pct is not None) and (roic_pct > 15.0)

    # 7. EPS CAGR (> 10%)
    eps_cagr_pct = None
    try:
        inc = yf_ticker.income_stmt
        if inc is not None and not inc.empty and len(inc.columns) >= 2:
            eps_rows = [r for r in inc.index if "Diluted EPS" in str(r) or "Basic EPS" in str(r)]
            if eps_rows:
                row_key = eps_rows[0]
                cols = list(inc.columns)
                cols.sort() # chronological
                recent_eps = inc.loc[row_key, cols[-1]]
                initial_eps = inc.loc[row_key, cols[0]]
                n_years = len(cols) - 1
                if pd.notna(recent_eps) and pd.notna(initial_eps) and initial_eps > 0 and recent_eps > 0 and n_years > 0:
                    cagr = ((float(recent_eps) / float(initial_eps)) ** (1.0 / n_years)) - 1.0
                    eps_cagr_pct = round(cagr * 100, 2)
    except Exception:
        pass

    if eps_cagr_pct is None:
        # Fallback approximation from earningsGrowth
        eg = info.get("earningsGrowth")
        if eg is not None:
            eps_cagr_pct = round(float(eg) * 100, 2)

    eps_cagr_passed = (eps_cagr_pct is not None) and (eps_cagr_pct > 10.0)

    checklist = [
        {
            "id": "pe_ratio",
            "name": "P/E Ratio",
            "condition": "Less than 20",
            "threshold": 20.0,
            "operator": "<",
            "actual_value": pe_val,
            "display_value": f"{pe_val:.2f}x" if pe_val is not None else "N/A",
            "passed": pe_passed,
            "description": "Price to Earnings ratio measures valuation; lower values suggest attractive valuation."
        },
        {
            "id": "roic",
            "name": "ROIC",
            "condition": "Above 15%",
            "threshold": 15.0,
            "operator": ">",
            "actual_value": roic_pct,
            "display_value": f"{roic_pct:.1f}%" if roic_pct is not None else "N/A",
            "passed": roic_passed,
            "description": "Return on Invested Capital measures how efficiently capital is allocated to generate profits."
        },
        {
            "id": "debt_to_equity",
            "name": "Debt / Equity Ratio",
            "condition": "Less than 1.0",
            "threshold": 1.0,
            "operator": "<",
            "actual_value": de_val,
            "display_value": f"{de_val:.2f}" if de_val is not None else "N/A",
            "passed": de_passed,
            "description": "Financial leverage; debt should not exceed stockholder equity to ensure safety."
        },
        {
            "id": "eps_cagr",
            "name": "EPS CAGR",
            "condition": "Above 10%",
            "threshold": 10.0,
            "operator": ">",
            "actual_value": eps_cagr_pct,
            "display_value": f"{eps_cagr_pct:.1f}%" if eps_cagr_pct is not None else "N/A",
            "passed": eps_cagr_passed,
            "description": "Compound Annual Growth Rate of earnings per share indicates sustained profit expansion."
        },
        {
            "id": "roe",
            "name": "ROE",
            "condition": "Greater than 15%",
            "threshold": 15.0,
            "operator": ">",
            "actual_value": roe_pct,
            "display_value": f"{roe_pct:.1f}%" if roe_pct is not None else "N/A",
            "passed": roe_passed,
            "description": "Return on Equity measures profitability generated with shareholders' money."
        },
        {
            "id": "ebit_margin",
            "name": "EBIT Margin",
            "condition": "Greater than 10%",
            "threshold": 10.0,
            "operator": ">",
            "actual_value": ebit_margin_pct,
            "display_value": f"{ebit_margin_pct:.1f}%" if ebit_margin_pct is not None else "N/A",
            "passed": ebit_margin_passed,
            "description": "Operating profit margin indicates strong operational efficiency and pricing power."
        },
        {
            "id": "gross_margin",
            "name": "Gross Margin",
            "condition": "Greater than 40%",
            "threshold": 40.0,
            "operator": ">",
            "actual_value": gross_margin_pct,
            "display_value": f"{gross_margin_pct:.1f}%" if gross_margin_pct is not None else "N/A",
            "passed": gross_margin_passed,
            "description": "High gross margin provides a strong moat and buffer against inflation or price wars."
        }
    ]

    passed_count = sum(1 for item in checklist if item["passed"])
    total_criteria = len(checklist)

    if passed_count >= 6:
        grade = "A"
        rating_label = "Strong Buy"
        rating_color = "emerald"
    elif passed_count >= 4:
        grade = "B"
        rating_label = "Moderate Buy"
        rating_color = "blue"
    elif passed_count >= 3:
        grade = "C"
        rating_label = "Hold / Neutral"
        rating_color = "amber"
    else:
        grade = "D"
        rating_label = "Weak / Avoid"
        rating_color = "rose"

    result = {
        "symbol": ticker,
        "score": passed_count,
        "total": total_criteria,
        "percentage": round((passed_count / total_criteria) * 100, 1),
        "grade": grade,
        "label": rating_label,
        "color": rating_color,
        "checklist": checklist
    }

    set_cached(cache_key, result, ttl_seconds=86400)
    return result
