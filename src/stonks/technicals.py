"""Technical analysis module.

Computes RSI, MACD, Bollinger Bands, and Moving Averages, then produces
actionable buy/sell/hold signals.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands

from stonks.data import StockData


@dataclass
class TechnicalSignal:
    """A single technical indicator signal."""

    indicator: str
    value: float | None
    signal: str  # "Buy", "Sell", "Hold"
    detail: str


@dataclass
class TechnicalReport:
    """Full technical analysis report."""

    signals: list[TechnicalSignal]
    overall: str  # "Buy", "Sell", "Hold"
    summary: str
    chart: go.Figure | None = None


def _compute_rsi(close: pd.Series, window: int = 14) -> TechnicalSignal:
    """RSI signal."""
    if len(close) < window + 1:
        return TechnicalSignal("RSI (14)", None, "Hold", "Insufficient data")

    rsi = RSIIndicator(close, window=window).rsi().iloc[-1]

    if rsi > 70:
        return TechnicalSignal(
            "RSI (14)", rsi, "Sell",
            f"RSI at {rsi:.1f} — **overbought** territory (>70). Potential pullback ahead.",
        )
    if rsi < 30:
        return TechnicalSignal(
            "RSI (14)", rsi, "Buy",
            f"RSI at {rsi:.1f} — **oversold** territory (<30). Potential bounce ahead.",
        )
    return TechnicalSignal(
        "RSI (14)", rsi, "Hold",
        f"RSI at {rsi:.1f} — neutral range (30-70).",
    )


def _compute_macd(close: pd.Series) -> TechnicalSignal:
    """MACD signal."""
    if len(close) < 26:
        return TechnicalSignal("MACD", None, "Hold", "Insufficient data")

    macd_ind = MACD(close)
    macd_line = macd_ind.macd().iloc[-1]
    signal_line = macd_ind.macd_signal().iloc[-1]
    histogram = macd_ind.macd_diff().iloc[-1]

    if macd_line > signal_line and histogram > 0:
        return TechnicalSignal(
            "MACD", histogram, "Buy",
            f"MACD ({macd_line:.2f}) above signal ({signal_line:.2f}) — **bullish crossover**.",
        )
    if macd_line < signal_line and histogram < 0:
        return TechnicalSignal(
            "MACD", histogram, "Sell",
            f"MACD ({macd_line:.2f}) below signal ({signal_line:.2f}) — **bearish crossover**.",
        )
    return TechnicalSignal(
        "MACD", histogram, "Hold",
        f"MACD ({macd_line:.2f}) near signal ({signal_line:.2f}) — converging.",
    )


def _compute_bollinger(close: pd.Series, window: int = 20) -> TechnicalSignal:
    """Bollinger Bands signal."""
    if len(close) < window:
        return TechnicalSignal("Bollinger Bands", None, "Hold", "Insufficient data")

    bb = BollingerBands(close, window=window)
    upper = bb.bollinger_hband().iloc[-1]
    lower = bb.bollinger_lband().iloc[-1]
    price = close.iloc[-1]
    mid = bb.bollinger_mavg().iloc[-1]
    width = (upper - lower) / mid * 100 if mid else 0

    if price >= upper:
        return TechnicalSignal(
            "Bollinger Bands", price, "Sell",
            f"Price (${price:.2f}) at/above upper band (${upper:.2f}) — **overbought**. "
            f"Band width: {width:.1f}%.",
        )
    if price <= lower:
        return TechnicalSignal(
            "Bollinger Bands", price, "Buy",
            f"Price (${price:.2f}) at/below lower band (${lower:.2f}) — **oversold**. "
            f"Band width: {width:.1f}%.",
        )
    return TechnicalSignal(
        "Bollinger Bands", price, "Hold",
        f"Price (${price:.2f}) within bands (${lower:.2f}–${upper:.2f}). "
        f"Band width: {width:.1f}%.",
    )


def _compute_ma_crossover(close: pd.Series) -> TechnicalSignal:
    """SMA 20/50 crossover signal."""
    if len(close) < 50:
        return TechnicalSignal("MA Crossover (20/50)", None, "Hold", "Insufficient data")

    sma20 = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
    sma50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
    price = close.iloc[-1]

    if sma20 > sma50 and price > sma20:
        return TechnicalSignal(
            "MA Crossover (20/50)", sma20, "Buy",
            f"SMA20 (${sma20:.2f}) > SMA50 (${sma50:.2f}) with price above both — **uptrend**.",
        )
    if sma20 < sma50 and price < sma20:
        return TechnicalSignal(
            "MA Crossover (20/50)", sma20, "Sell",
            f"SMA20 (${sma20:.2f}) < SMA50 (${sma50:.2f}) with price below both — **downtrend**.",
        )
    return TechnicalSignal(
        "MA Crossover (20/50)", sma20, "Hold",
        f"SMA20 (${sma20:.2f}), SMA50 (${sma50:.2f}) — mixed signals.",
    )


def _build_chart(stock: StockData) -> go.Figure | None:
    """Build a Plotly chart with candlesticks, Bollinger Bands, volume, RSI, and MACD."""
    hist = stock.history
    if hist.empty or len(hist) < 26:
        return None

    close = hist["Close"]
    bb = BollingerBands(close, window=20)
    rsi_series = RSIIndicator(close, window=14).rsi()
    macd_ind = MACD(close)

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=("Price & Bollinger Bands", "Volume", "RSI (14)", "MACD"),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name="Price",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=hist.index, y=bb.bollinger_hband(), name="BB Upper",
        line=dict(color="rgba(173,216,230,0.6)", width=1),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=hist.index, y=bb.bollinger_lband(), name="BB Lower",
        line=dict(color="rgba(173,216,230,0.6)", width=1),
        fill="tonexty", fillcolor="rgba(173,216,230,0.1)",
    ), row=1, col=1)

    # SMA 20 / 50
    sma20 = SMAIndicator(close, window=20).sma_indicator()
    sma50 = SMAIndicator(close, window=50).sma_indicator()
    fig.add_trace(go.Scatter(
        x=hist.index, y=sma20, name="SMA 20",
        line=dict(color="#ff9800", width=1, dash="dot"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=hist.index, y=sma50, name="SMA 50",
        line=dict(color="#2196f3", width=1, dash="dot"),
    ), row=1, col=1)

    # Volume
    colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"], name="Volume",
        marker_color=colors, opacity=0.7,
    ), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=hist.index, y=rsi_series, name="RSI",
        line=dict(color="#ab47bc", width=1.5),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

    # MACD
    fig.add_trace(go.Scatter(
        x=hist.index, y=macd_ind.macd(), name="MACD",
        line=dict(color="#2196f3", width=1.5),
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=hist.index, y=macd_ind.macd_signal(), name="Signal",
        line=dict(color="#ff9800", width=1.5),
    ), row=4, col=1)
    macd_hist = macd_ind.macd_diff()
    hist_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in macd_hist]
    fig.add_trace(go.Bar(
        x=hist.index, y=macd_hist, name="Histogram",
        marker_color=hist_colors, opacity=0.6,
    ), row=4, col=1)

    fig.update_layout(
        height=900,
        template="plotly_dark",
        showlegend=False,
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=20, t=40, b=30),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Vol", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_technicals(stock: StockData) -> TechnicalReport:
    """Run full technical analysis on the stock."""
    if stock.history.empty:
        return TechnicalReport(
            signals=[], overall="Hold",
            summary="No historical data available for technical analysis.",
        )

    close = stock.history["Close"]

    signals = [
        _compute_rsi(close),
        _compute_macd(close),
        _compute_bollinger(close),
        _compute_ma_crossover(close),
    ]

    buy_count = sum(1 for s in signals if s.signal == "Buy")
    sell_count = sum(1 for s in signals if s.signal == "Sell")

    if buy_count > sell_count:
        overall = "Buy"
    elif sell_count > buy_count:
        overall = "Sell"
    else:
        overall = "Hold"

    emoji = {"Buy": "🟢", "Sell": "🔴", "Hold": "🟡"}[overall]
    summary_parts = [f"{emoji} **Technical Outlook: {overall}**", ""]
    for sig in signals:
        icon = {"Buy": "🟢", "Sell": "🔴", "Hold": "🟡"}[sig.signal]
        summary_parts.append(f"- {icon} **{sig.indicator}**: {sig.detail}")

    chart = _build_chart(stock)

    return TechnicalReport(
        signals=signals,
        overall=overall,
        summary="\n".join(summary_parts),
        chart=chart,
    )

