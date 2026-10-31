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

