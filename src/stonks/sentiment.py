"""Market sentiment analysis module.

Derives sentiment from price action, volume trends, analyst recommendations,
and key market indicators available through yfinance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from stonks.data import StockData


@dataclass
class SentimentSignal:
    """A single sentiment signal."""

    name: str
    signal: str  # "Bullish", "Bearish", "Neutral"
    detail: str
    weight: float = 1.0


@dataclass
class SentimentReport:
    """Aggregated market sentiment report."""

    signals: list[SentimentSignal]
    overall: str  # "Bullish", "Bearish", "Neutral"
    confidence: float  # 0-100
    summary: str


def _price_momentum_signal(history: pd.DataFrame) -> SentimentSignal:
    """Analyse recent price momentum."""
    if history.empty or len(history) < 20:
        return SentimentSignal("Price Momentum", "Neutral", "Insufficient data")

    close = history["Close"]
    pct_1m = (close.iloc[-1] / close.iloc[-min(21, len(close))] - 1) * 100
    pct_3m = (
        (close.iloc[-1] / close.iloc[-min(63, len(close))] - 1) * 100
        if len(close) >= 63
        else pct_1m
    )

    if pct_1m > 5 and pct_3m > 10:
        return SentimentSignal(
            "Price Momentum", "Bullish",
            f"Strong upward momentum: +{pct_1m:.1f}% (1M), +{pct_3m:.1f}% (3M)",
            weight=1.5,
        )
    if pct_1m > 0:
        return SentimentSignal(
            "Price Momentum", "Bullish",
            f"Positive trend: +{pct_1m:.1f}% (1M)",
        )
    if pct_1m < -5 and pct_3m < -10:
        return SentimentSignal(
            "Price Momentum", "Bearish",
            f"Strong downward momentum: {pct_1m:.1f}% (1M), {pct_3m:.1f}% (3M)",
            weight=1.5,
        )
    if pct_1m < 0:
        return SentimentSignal(
            "Price Momentum", "Bearish",
            f"Negative trend: {pct_1m:.1f}% (1M)",
        )
    return SentimentSignal("Price Momentum", "Neutral", "Flat price action")


def _volume_signal(history: pd.DataFrame) -> SentimentSignal:
    """Analyse volume trends."""
    if history.empty or len(history) < 20:
        return SentimentSignal("Volume Trend", "Neutral", "Insufficient data")

    vol = history["Volume"]
    avg_recent = vol.iloc[-5:].mean()
    avg_prior = vol.iloc[-20:-5].mean()

    if avg_prior == 0:
        return SentimentSignal("Volume Trend", "Neutral", "No volume data")

    vol_change = (avg_recent / avg_prior - 1) * 100
    price_up = history["Close"].iloc[-1] > history["Close"].iloc[-5]

    if vol_change > 20 and price_up:
        return SentimentSignal(
            "Volume Trend", "Bullish",
            f"Volume surging +{vol_change:.0f}% with rising prices — accumulation",
        )
    if vol_change > 20 and not price_up:
        return SentimentSignal(
            "Volume Trend", "Bearish",
            f"Volume surging +{vol_change:.0f}% with falling prices — distribution",
        )
    if vol_change < -20:
        return SentimentSignal(
            "Volume Trend", "Neutral",
            f"Volume declining {vol_change:.0f}% — low conviction",
        )
    return SentimentSignal(
        "Volume Trend", "Neutral",
        f"Volume stable ({vol_change:+.0f}%)",
    )


def _moving_average_signal(history: pd.DataFrame) -> SentimentSignal:
    """50/200 day MA crossover signal (Golden/Death cross)."""
    if history.empty or len(history) < 200:
        if len(history) >= 50:
            close = history["Close"]
            ma50 = close.rolling(50).mean().iloc[-1]
            current = close.iloc[-1]
            if current > ma50:
                return SentimentSignal(
                    "Moving Averages", "Bullish",
                    f"Price (${current:.2f}) above 50-day MA (${ma50:.2f})",
                )
            return SentimentSignal(
                "Moving Averages", "Bearish",
                f"Price (${current:.2f}) below 50-day MA (${ma50:.2f})",
            )
        return SentimentSignal("Moving Averages", "Neutral", "Insufficient history")

    close = history["Close"]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    current = close.iloc[-1]

    if ma50 > ma200 and current > ma50:
        return SentimentSignal(
            "Moving Averages", "Bullish",
            f"Golden cross: 50-day MA (${ma50:.2f}) above 200-day MA (${ma200:.2f})",
            weight=1.5,
        )
    if ma50 < ma200 and current < ma50:
        return SentimentSignal(
            "Moving Averages", "Bearish",
            f"Death cross: 50-day MA (${ma50:.2f}) below 200-day MA (${ma200:.2f})",
            weight=1.5,
        )
    return SentimentSignal(
        "Moving Averages", "Neutral",
        f"50-day MA (${ma50:.2f}), 200-day MA (${ma200:.2f}) — mixed signal",
    )


def _analyst_signal(stock: StockData) -> SentimentSignal:
    """Sentiment from analyst recommendations."""
    rec = stock.info.get("recommendationKey", "")
    rec_mean = stock.info.get("recommendationMean")
    target = stock.info.get("targetMeanPrice")
    current = stock.current_price

    if not rec:
        return SentimentSignal("Analyst Consensus", "Neutral", "No analyst data available")

    detail_parts = [f"Consensus: **{rec.replace('_', ' ').title()}**"]
    if rec_mean is not None:
        detail_parts.append(f"(score: {rec_mean:.1f}/5)")
    if target and current:
        upside = (target / current - 1) * 100
        detail_parts.append(f"| Target: ${target:.2f} ({upside:+.1f}%)")

    detail = " ".join(detail_parts)

    if rec in ("strong_buy", "buy"):
        return SentimentSignal("Analyst Consensus", "Bullish", detail, weight=1.2)
    if rec in ("sell", "strong_sell"):
        return SentimentSignal("Analyst Consensus", "Bearish", detail, weight=1.2)
    return SentimentSignal("Analyst Consensus", "Neutral", detail)


def _52w_range_signal(stock: StockData) -> SentimentSignal:
    """Where the price sits in its 52-week range."""
    high = stock.info.get("fiftyTwoWeekHigh")
    low = stock.info.get("fiftyTwoWeekLow")
    current = stock.current_price

    if not all((high, low, current)) or high == low:
        return SentimentSignal("52-Week Range", "Neutral", "Insufficient data")

    position = (current - low) / (high - low) * 100

    if position > 80:
        return SentimentSignal(
            "52-Week Range", "Bullish",
            f"Trading near 52-week high ({position:.0f}th percentile) — ${low:.2f} to ${high:.2f}",
        )
    if position < 20:
        return SentimentSignal(
            "52-Week Range", "Bearish",
            f"Trading near 52-week low ({position:.0f}th percentile) — ${low:.2f} to ${high:.2f}",
        )
    return SentimentSignal(
        "52-Week Range", "Neutral",
        f"Mid-range ({position:.0f}th percentile) — ${low:.2f} to ${high:.2f}",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_sentiment(stock: StockData) -> SentimentReport:
    """Produce a market sentiment report for the given stock."""
    signals = [
        _price_momentum_signal(stock.history),
        _volume_signal(stock.history),
        _moving_average_signal(stock.history),
        _analyst_signal(stock),
        _52w_range_signal(stock),
    ]

    bullish_w = sum(s.weight for s in signals if s.signal == "Bullish")
    bearish_w = sum(s.weight for s in signals if s.signal == "Bearish")
    total_w = sum(s.weight for s in signals) or 1

    if bullish_w > bearish_w:
        overall = "Bullish"
        confidence = (bullish_w / total_w) * 100
    elif bearish_w > bullish_w:
        overall = "Bearish"
        confidence = (bearish_w / total_w) * 100
    else:
        overall = "Neutral"
        confidence = 50.0

    # Build summary
    emoji = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}[overall]
    summary_parts = [
        f"{emoji} **Overall Sentiment: {overall}** (confidence: {confidence:.0f}%)",
        "",
    ]
    for sig in signals:
        icon = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}[sig.signal]
        summary_parts.append(f"- {icon} **{sig.name}**: {sig.detail}")

    return SentimentReport(
        signals=signals,
        overall=overall,
        confidence=confidence,
        summary="\n".join(summary_parts),
    )

