"""Data fetching module using yfinance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import yfinance as yf


@dataclass
class StockData:
    """Container for all stock data needed by the analysis modules."""

    ticker: str
    info: dict[str, Any] = field(default_factory=dict)
    history: pd.DataFrame = field(default_factory=pd.DataFrame)
    financials: pd.DataFrame = field(default_factory=pd.DataFrame)
    balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    recommendations: pd.DataFrame = field(default_factory=pd.DataFrame)
    calendar: dict[str, Any] = field(default_factory=dict)
    earnings_dates: pd.DataFrame = field(default_factory=pd.DataFrame)
    valid: bool = False
    error: str = ""

    @property
    def current_price(self) -> float | None:
        """Return the current stock price."""
        return self.info.get("currentPrice") or self.info.get(
            "regularMarketPrice"
        )

    @property
    def company_name(self) -> str:
        """Return the company's long name."""
        return self.info.get("longName", self.ticker.upper())

    @property
    def currency(self) -> str:
        """Return the currency the stock trades in."""
        return self.info.get("currency", "USD")

    @property
    def market_cap(self) -> float | None:
        """Return market capitalisation."""
        return self.info.get("marketCap")

    @property
    def shares_outstanding(self) -> float | None:
        """Return the number of shares outstanding."""
        return (
            self.info.get("sharesOutstanding")
            or self.info.get("impliedSharesOutstanding")
            or self.info.get("floatShares")
        )

    @property
    def dividend_yield(self) -> float | None:
        """Return dividend yield in percent (e.g. 1.5 for 1.5%)."""
        dy = self.info.get("dividendYield")
        if dy is not None:
            # If dy is a decimal fraction like 0.0031 instead of percentage 0.31%:
            if 0 < dy < 0.05 and self.info.get("dividendRate"):
                rate = self.info.get("dividendRate")
                cp = self.current_price
                if cp and cp > 0:
                    return (rate / cp) * 100.0
            return float(dy)
        # Fallback to dividendRate / current_price
        rate = self.info.get("dividendRate")
        cp = self.current_price
        if rate and cp and cp > 0:
            return (rate / cp) * 100.0
        if self.info.get("trailingAnnualDividendYield") is not None:
            tay = self.info.get("trailingAnnualDividendYield")
            if tay is not None:
                return float(tay) * 100.0 if tay < 0.2 else float(tay)
        return None

    @property
    def dividend_rate(self) -> float | None:
        """Return annual dividend rate per share."""
        return self.info.get("dividendRate") or self.info.get("trailingAnnualDividendRate")

    @property
    def sector(self) -> str:
        return self.info.get("sector", "N/A")

    @property
    def industry(self) -> str:
        return self.info.get("industry", "N/A")


def fetch_stock_data(ticker: str, period: str = "1y") -> StockData:
    """Fetch comprehensive stock data for the given ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        period: Historical data period (default "1y").

    Returns:
        A populated StockData instance.
    """
    data = StockData(ticker=ticker.upper())
    try:
        stock = yf.Ticker(ticker)
        data.info = stock.info or {}

        # Bail out early if the ticker doesn't resolve to a real security
        if not data.info or data.info.get("quoteType") is None:
            data.error = f"Ticker '{ticker.upper()}' not found."
            return data

        data.history = stock.history(period=period, auto_adjust=True)
        data.financials = stock.financials
        data.balance_sheet = stock.balance_sheet
        data.income_stmt = stock.income_stmt

        try:
            data.recommendations = stock.recommendations
        except Exception:
            data.recommendations = pd.DataFrame()

        try:
            data.calendar = stock.calendar or {}
        except Exception:
            data.calendar = {}

        try:
            ed = stock.get_earnings_dates(limit=12)
            data.earnings_dates = ed if ed is not None else pd.DataFrame()
        except Exception:
            data.earnings_dates = pd.DataFrame()

        data.valid = True
    except Exception as exc:  # noqa: BLE001
        data.error = str(exc)
    return data


def format_large_number(value: float | None) -> str:
    """Format a large number into a human-readable string (e.g. 2.4T)."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_000_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000_000:.2f}T"
    if abs_val >= 1_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000:.2f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val / 1_000:.2f}K"
    return f"{sign}{abs_val:.2f}"

