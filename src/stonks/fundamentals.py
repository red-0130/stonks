"""Fundamental analysis rating engine.

Evaluates a stock against seven criteria and produces a score + summary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stonks.data import StockData


@dataclass
class CriterionResult:
    """Result of evaluating a single fundamental criterion."""

    name: str
    description: str
    threshold: str
    actual_value: float | None
    passed: bool

    @property
    def display_value(self) -> str:
        if self.actual_value is None:
            return "N/A"
        # Format as percentage for ratio-like metrics
        if "%" in self.threshold or "Margin" in self.name or self.name in (
            "ROE", "ROIC"
        ):
            return f"{self.actual_value:.2f}%"
        return f"{self.actual_value:.2f}"


@dataclass
class FundamentalRating:
    """Overall fundamental rating for a stock."""

    criteria: list[CriterionResult]

    @property
    def score(self) -> int:
        return sum(1 for c in self.criteria if c.passed)

    @property
    def max_score(self) -> int:
        return len(self.criteria)

    @property
    def grade(self) -> str:
        ratio = self.score / self.max_score if self.max_score else 0
        if ratio >= 0.85:
            return "A"
        if ratio >= 0.70:
            return "B"
        if ratio >= 0.55:
            return "C"
        if ratio >= 0.40:
            return "D"
        return "F"

    @property
    def summary(self) -> str:
        passed = [c for c in self.criteria if c.passed]
        failed = [c for c in self.criteria if not c.passed]
        parts: list[str] = []
        parts.append(
            f"**Overall Grade: {self.grade}** ({self.score}/{self.max_score} criteria met)"
        )
        if passed:
            strengths = ", ".join(c.name for c in passed)
            parts.append(f"✅ **Strengths:** {strengths}")
        if failed:
            weaknesses = ", ".join(c.name for c in failed)
            parts.append(f"⚠️ **Weaknesses:** {weaknesses}")

        if self.grade in ("A", "B"):
            parts.append(
                "📊 The stock shows **strong fundamentals** and meets most "
                "quality criteria. It may be a solid long-term holding."
            )
        elif self.grade == "C":
            parts.append(
                "📊 The stock has **mixed fundamentals**. Some metrics are "
                "promising but others need improvement. Exercise caution."
            )
        else:
            parts.append(
                "📊 The stock shows **weak fundamentals** and fails to meet "
                "several key quality criteria. Higher risk — proceed with care."
            )
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_get(info: dict, key: str) -> float | None:
    val = info.get(key)
    if val is None:
        return None
    try:
        result = float(val)
        if np.isnan(result) or np.isinf(result):
            return None
        return result
    except (ValueError, TypeError):
        return None


def _compute_pe(stock: StockData) -> float | None:
    """Compute trailing P/E ratio: Current Price / Trailing 12-month EPS.

    Tries three approaches in order:
    1. Manual: current price / trailing EPS from info
    2. Manual: current price / (net income TTM / shares outstanding)
    3. Fallback: yfinance pre-computed trailingPE
    """
    info = stock.info
    price = stock.current_price
    if price is None or price <= 0:
        return None

    # Approach 1: price / trailingEps (most reliable)
    trailing_eps = _safe_get(info, "trailingEps")
    if trailing_eps is not None and trailing_eps > 0:
        return price / trailing_eps

    # Approach 2: compute EPS from income statement and shares outstanding
    try:
        inc = stock.income_stmt
        if not inc.empty and "Net Income" in inc.index:
            net_income = float(inc.loc["Net Income"].iloc[0])
            shares = _safe_get(info, "sharesOutstanding")
            if shares is None and not stock.balance_sheet.empty:
                for key in ("Ordinary Shares Number", "Share Issued"):
                    if key in stock.balance_sheet.index:
                        shares = float(stock.balance_sheet.loc[key].iloc[0])
                        break
            if shares is not None and shares > 0 and net_income > 0:
                eps = net_income / shares
                return price / eps
    except Exception:  # noqa: BLE001
        pass

    # Approach 3: fallback to yfinance pre-computed value
    pe = _safe_get(info, "trailingPE")
    if pe is not None and pe > 0:
        return pe

    return None


def _compute_eps_cagr(stock: StockData) -> float | None:
    """Compute EPS compound annual growth rate from income statements."""
    try:
        inc = stock.income_stmt
        if inc.empty:
            return None

        # income_stmt columns are dates, most recent first
        eps_values: list[float] = []
        shares_values: list[float] = []

        bs = stock.balance_sheet
        for col in inc.columns:
            net_income = inc.at["Net Income", col] if "Net Income" in inc.index else None
            # Try to get shares from balance sheet or info
            shares = None
            if not bs.empty and col in bs.columns:
                for key in ("Ordinary Shares Number", "Share Issued"):
                    if key in bs.index:
                        shares = bs.at[key, col]
                        break
            if shares is None:
                shares = stock.info.get("sharesOutstanding")

            if net_income is not None and shares is not None and float(shares) > 0:
                eps_values.append(float(net_income) / float(shares))
                shares_values.append(float(shares))

        if len(eps_values) < 2:
            return None

        # Most recent is first, oldest is last — reverse for CAGR
        eps_start = eps_values[-1]
        eps_end = eps_values[0]
        n_years = len(eps_values) - 1

        if eps_start <= 0 or eps_end <= 0:
            return None

        cagr = (eps_end / eps_start) ** (1 / n_years) - 1
        return cagr * 100  # as percentage
    except Exception:  # noqa: BLE001
        return None


def _compute_roic(stock: StockData) -> float | None:
    """Compute Return on Invested Capital."""
    try:
        info = stock.info
        inc = stock.income_stmt
        bs = stock.balance_sheet

        # NOPAT = EBIT × (1 − tax_rate)
        ebit = None
        if not inc.empty and "EBIT" in inc.index:
            ebit = float(inc.iloc[0]["EBIT"] if isinstance(inc.iloc[0], dict) else inc["EBIT"].iloc[0] if "EBIT" in inc else inc.loc["EBIT"].iloc[0])

        if ebit is None:
            ebit = _safe_get(info, "ebitda")
            if ebit is not None:
                # Approximate EBIT from EBITDA (rough)
                da = _safe_get(info, "totalCashFromDepreciationAndAmortization")
                if da:
                    ebit -= da

        if ebit is None:
            return None

        tax_rate = _safe_get(info, "effectiveTaxRate") or 0.21
        if tax_rate > 1:
            tax_rate = tax_rate / 100
        nopat = ebit * (1 - tax_rate)

        # Invested Capital = Total Equity + Total Debt - Cash
        total_equity = _safe_get(info, "totalStockholderEquity")
        total_debt = _safe_get(info, "totalDebt")
        cash = _safe_get(info, "totalCash")

        if total_equity is None and not bs.empty:
            for key in ("Stockholders Equity", "Total Stockholder Equity", "Stockholders' Equity"):
                if key in bs.index:
                    total_equity = float(bs.loc[key].iloc[0])
                    break

        if total_equity is None:
            return None

        total_debt = total_debt or 0
        cash = cash or 0
        invested_capital = total_equity + total_debt - cash

        if invested_capital <= 0:
            return None

        return (nopat / invested_capital) * 100
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Main rating function
# ---------------------------------------------------------------------------

def rate_stock(stock: StockData) -> FundamentalRating:
    """Rate a stock against the seven fundamental criteria.

    Criteria:
        1. P/E Ratio < 20
        2. ROIC > 15%
        3. Debt/Equity < 1
        4. EPS CAGR > 10%
        5. ROE > 15%
        6. EBIT Margin > 10%
        7. Gross Margin > 40%
    """
    info = stock.info
    criteria: list[CriterionResult] = []

    # 1. P/E Ratio < 20
    # Compute trailing P/E manually: current price / trailing 12-month EPS
    pe = _compute_pe(stock)
    criteria.append(CriterionResult(
        name="P/E Ratio",
        description="Price-to-Earnings ratio measures valuation relative to earnings (trailing 12-month)",
        threshold="< 20",
        actual_value=pe,
        passed=pe is not None and pe > 0 and pe < 20,
    ))

    # 2. ROIC > 15%
    roic = _compute_roic(stock)
    criteria.append(CriterionResult(
        name="ROIC",
        description="Return on Invested Capital measures how efficiently the company uses its capital",
        threshold="> 15%",
        actual_value=roic,
        passed=roic is not None and roic > 15,
    ))

    # 3. Debt/Equity < 1
    de = _safe_get(info, "debtToEquity")
    if de is not None and de > 10:
        # yfinance sometimes returns D/E as a percentage
        de = de / 100
    criteria.append(CriterionResult(
        name="Debt/Equity",
        description="Debt-to-Equity ratio measures financial leverage",
        threshold="< 1",
        actual_value=de,
        passed=de is not None and de < 1,
    ))

    # 4. EPS CAGR > 10%
    eps_cagr = _compute_eps_cagr(stock)
    criteria.append(CriterionResult(
        name="EPS CAGR",
        description="Earnings Per Share compound annual growth rate",
        threshold="> 10%",
        actual_value=eps_cagr,
        passed=eps_cagr is not None and eps_cagr > 10,
    ))

    # 5. ROE > 15%
    roe = _safe_get(info, "returnOnEquity")
    if roe is not None and abs(roe) < 5:
        # yfinance returns ROE as a decimal ratio (e.g. 0.25 = 25%)
        roe = roe * 100
    criteria.append(CriterionResult(
        name="ROE",
        description="Return on Equity measures profitability relative to shareholders' equity",
        threshold="> 15%",
        actual_value=roe,
        passed=roe is not None and roe > 15,
    ))

    # 6. EBIT Margin > 10%
    operating_margin = _safe_get(info, "operatingMargins")
    if operating_margin is not None and abs(operating_margin) <= 1:
        operating_margin = operating_margin * 100
    criteria.append(CriterionResult(
        name="EBIT Margin",
        description="EBIT Margin (operating margin) measures operational efficiency",
        threshold="> 10%",
        actual_value=operating_margin,
        passed=operating_margin is not None and operating_margin > 10,
    ))

    # 7. Gross Margin > 40%
    gross_margin = _safe_get(info, "grossMargins")
    if gross_margin is not None and abs(gross_margin) <= 1:
        gross_margin = gross_margin * 100
    criteria.append(CriterionResult(
        name="Gross Margin",
        description="Gross Margin measures production efficiency",
        threshold="> 40%",
        actual_value=gross_margin,
        passed=gross_margin is not None and gross_margin > 40,
    ))

    return FundamentalRating(criteria=criteria)
