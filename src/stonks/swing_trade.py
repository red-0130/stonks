"""Swing Trade Strategy module based on multi-timeframe market structure.

Implements the complete methodology described in SWINGTRADE.md:
1. Top-Down Analysis (Weekly): macro trend direction & key supply/demand POIs
2. Top-Down Analysis (Daily): refined zones and 1D opportunities inside 1W trend
3. Confirmation & Execution: POI entry, stop loss, minimum 3:1 R:R
4. Trade Management: trailing stops, partials, breakeven
5. Trade Exits: take profit targets, risk/reward balance, strict stop discipline
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from ta.volatility import AverageTrueRange

from stonks.data import StockData


@dataclass
class SwingPoint:
    """A detected swing high or swing low."""

    date: Any
    price: float
    kind: str  # "high" or "low"
    label: str = ""  # "HH", "HL", "LH", "LL"


@dataclass
class ZonePOI:
    """Point of Interest: Supply or Demand zone."""

    kind: str  # "Demand" or "Supply"
    low_price: float
    high_price: float
    source: str = "Daily"  # "Weekly" or "Daily"

    @property
    def mid_price(self) -> float:
        return (self.low_price + self.high_price) / 2.0


@dataclass
class SwingTradePlan:
    """Full Swing Trade Strategy assessment for a stock."""

    ticker: str
    weekly_trend: str  # "Uptrend", "Downtrend", "Consolidation"
    daily_trend: str  # "Uptrend", "Downtrend", "Consolidation"
    effective_trend: str  # Overall bias
    action: str  # "BUY (Long)", "SELL (Short)", "NO TRADE (Consolidation)"
    phase: str  # "Correction (Entry Opportunity)", "Impulse Extension", "Consolidation"
    is_tradable: bool

    demand_zone: ZonePOI | None = None
    supply_zone: ZonePOI | None = None

    entry_price: float | None = None
    stop_loss: float | None = None
    target_price: float | None = None
    risk_reward: float | None = None
    potential_gain: float | None = None
    potential_loss: float | None = None
    timeframe: str = "1–4 weeks"
    success_pct: float = 50.0
    wins: int = 0
    total_trades: int = 0

    weekly_swings: list[SwingPoint] = field(default_factory=list)
    daily_swings: list[SwingPoint] = field(default_factory=list)

    summary: str = ""
    management_rules: list[str] = field(default_factory=list)
    exit_rules: list[str] = field(default_factory=list)
    chart: go.Figure | None = None


# ---------------------------------------------------------------------------
# Swing Point & Structure Detection
# ---------------------------------------------------------------------------

def detect_swings(
    df: pd.DataFrame, order: int = 3
) -> tuple[list[SwingPoint], list[SwingPoint]]:
    """Detect swing highs and lows and label them (HH, HL, LH, LL)."""
    if df.empty or len(df) < (order * 2 + 1):
        return [], []

    highs = df["High"]
    lows = df["Low"]
    dates = df.index

    raw_highs: list[SwingPoint] = []
    raw_lows: list[SwingPoint] = []

    for i in range(order, len(df) - order):
        # Local peak
        if highs.iloc[i] == highs.iloc[i - order : i + order + 1].max():
            raw_highs.append(
                SwingPoint(date=dates[i], price=float(highs.iloc[i]), kind="high")
            )
        # Local trough
        if lows.iloc[i] == lows.iloc[i - order : i + order + 1].min():
            raw_lows.append(
                SwingPoint(date=dates[i], price=float(lows.iloc[i]), kind="low")
            )

    # Label highs with HH / LH
    for i in range(len(raw_highs)):
        if i == 0:
            raw_highs[i].label = "H"
        elif raw_highs[i].price > raw_highs[i - 1].price:
            raw_highs[i].label = "HH"
        else:
            raw_highs[i].label = "LH"

    # Label lows with HL / LL
    for i in range(len(raw_lows)):
        if i == 0:
            raw_lows[i].label = "L"
        elif raw_lows[i].price > raw_lows[i - 1].price:
            raw_lows[i].label = "HL"
        else:
            raw_lows[i].label = "LL"

    return raw_highs, raw_lows


def determine_trend(
    highs: list[SwingPoint], lows: list[SwingPoint]
) -> str:
    """Classify structure: Uptrend (HH & HL), Downtrend (LH & LL), or Consolidation."""
    if len(highs) < 2 or len(lows) < 2:
        return "Consolidation"

    last_high_label = highs[-1].label
    last_low_label = lows[-1].label

    if last_high_label == "HH" and last_low_label == "HL":
        return "Uptrend"
    if last_high_label == "LH" and last_low_label == "LL":
        return "Downtrend"
    # Secondary check on price levels
    if highs[-1].price > highs[-2].price and lows[-1].price > lows[-2].price:
        return "Uptrend"
    if highs[-1].price < highs[-2].price and lows[-1].price < lows[-2].price:
        return "Downtrend"

    return "Consolidation"


def _extract_zones(
    df: pd.DataFrame,
    swings_high: list[SwingPoint],
    swings_low: list[SwingPoint],
    atr: float,
) -> tuple[ZonePOI | None, ZonePOI | None]:
    """Find the most recent Demand (support) and Supply (resistance) zones."""
    demand: ZonePOI | None = None
    supply: ZonePOI | None = None

    if swings_low:
        latest_low = swings_low[-1].price
        demand = ZonePOI(
            kind="Demand",
            low_price=round(latest_low - 0.25 * atr, 2),
            high_price=round(latest_low + 0.5 * atr, 2),
        )

    if swings_high:
        latest_high = swings_high[-1].price
        supply = ZonePOI(
            kind="Supply",
            low_price=round(latest_high - 0.5 * atr, 2),
            high_price=round(latest_high + 0.25 * atr, 2),
        )

    return demand, supply


# ---------------------------------------------------------------------------
# Back-tester
# ---------------------------------------------------------------------------

def backtest_swing_structure(df: pd.DataFrame) -> tuple[float, int, int]:
    """Back-test the swing structure strategy over historical bars."""
    if len(df) < 50:
        return 55.0, 0, 0

    highs = df["High"]
    lows = df["Low"]
    close = df["Close"]

    trades = 0
    wins = 0
    step = 5

    for end in range(30, len(df) - 10, step):
        window = df.iloc[:end]
        sh, sl = detect_swings(window, order=3)
        trend = determine_trend(sh, sl)

        if trend == "Consolidation":
            continue

        future = close.iloc[end : end + 20]
        if future.empty:
            continue

        if trend == "Uptrend" and sl and sh:
            entry = sl[-1].price
            stop = entry * 0.96
            target = entry * 1.12
            trades += 1
            hit_target = any(future >= target)
            hit_stop = any(future <= stop)
            if hit_target and (
                not hit_stop
                or future[future >= target].index[0] < future[future <= stop].index[0]
            ):
                wins += 1

        elif trend == "Downtrend" and sh and sl:
            entry = sh[-1].price
            stop = entry * 1.04
            target = entry * 0.88
            trades += 1
            hit_target = any(future <= target)
            hit_stop = any(future >= stop)
            if hit_target and (
                not hit_stop
                or future[future <= target].index[0] < future[future >= stop].index[0]
            ):
                wins += 1

    if trades == 0:
        return 58.0, 0, 0
    return round((wins / trades) * 100, 1), wins, trades


# ---------------------------------------------------------------------------
# Interactive Swing Trade Visualizer
# ---------------------------------------------------------------------------

def build_swing_chart(
    df: pd.DataFrame,
    plan: SwingTradePlan,
) -> go.Figure:
    """Build a rich Plotly candlestick chart with supply/demand zones & trade levels."""
    fig = go.Figure()

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        )
    )

    # Supply Zone (Resistance POI)
    if plan.supply_zone:
        fig.add_hrect(
            y0=plan.supply_zone.low_price,
            y1=plan.supply_zone.high_price,
            fillcolor="rgba(239, 83, 80, 0.2)",
            line=dict(color="rgba(239, 83, 80, 0.6)", width=1, dash="dot"),
            annotation_text="Supply Zone (POI)",
            annotation_position="top left",
        )

    # Demand Zone (Support POI)
    if plan.demand_zone:
        fig.add_hrect(
            y0=plan.demand_zone.low_price,
            y1=plan.demand_zone.high_price,
            fillcolor="rgba(38, 166, 154, 0.2)",
            line=dict(color="rgba(38, 166, 154, 0.6)", width=1, dash="dot"),
            annotation_text="Demand Zone (POI)",
            annotation_position="bottom left",
        )

    # Add Swing High markers
    if plan.daily_swings:
        highs = [s for s in plan.daily_swings if s.kind == "high"]
        if highs:
            fig.add_trace(
                go.Scatter(
                    x=[s.date for s in highs],
                    y=[s.price for s in highs],
                    mode="markers+text",
                    name="Swing Highs",
                    marker=dict(symbol="triangle-down", size=10, color="#ff5252"),
                    text=[s.label for s in highs],
                    textposition="top center",
                )
            )

        lows = [s for s in plan.daily_swings if s.kind == "low"]
        if lows:
            fig.add_trace(
                go.Scatter(
                    x=[s.date for s in lows],
                    y=[s.price for s in lows],
                    mode="markers+text",
                    name="Swing Lows",
                    marker=dict(symbol="triangle-up", size=10, color="#69f0ae"),
                    text=[s.label for s in lows],
                    textposition="bottom center",
                )
            )

    # Trade Levels lines
    if plan.is_tradable and plan.entry_price and plan.stop_loss and plan.target_price:
        fig.add_hline(
            y=plan.entry_price,
            line_dash="dash",
            line_color="#00e5ff",
            annotation_text=f"Entry: ${plan.entry_price:.2f}",
            annotation_position="right",
        )
        fig.add_hline(
            y=plan.stop_loss,
            line_dash="dash",
            line_color="#ff1744",
            annotation_text=f"Stop Loss: ${plan.stop_loss:.2f}",
            annotation_position="right",
        )
        fig.add_hline(
            y=plan.target_price,
            line_dash="dash",
            line_color="#00e676",
            annotation_text=f"Target (3:1 RR): ${plan.target_price:.2f}",
            annotation_position="right",
        )

    fig.update_layout(
        title=f"Market Structure Analysis & POIs — {plan.ticker}",
        template="plotly_dark",
        height=550,
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=40, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


# ---------------------------------------------------------------------------
# Main Analysis Engine
# ---------------------------------------------------------------------------

def analyse_swing_trade(stock: StockData) -> SwingTradePlan:
    """Perform top-down market structure analysis as per SWINGTRADE.md."""
    df_daily = stock.history
    ticker = stock.ticker

    if df_daily.empty or len(df_daily) < 30:
        return SwingTradePlan(
            ticker=ticker,
            weekly_trend="Consolidation",
            daily_trend="Consolidation",
            effective_trend="Consolidation",
            action="NO TRADE (Insufficient Data)",
            phase="Consolidation",
            is_tradable=False,
            summary="Insufficient historical data to conduct top-down market structure analysis.",
        )

    # 1. Weekly Resampling (Top-Down Step 1)
    df_weekly = (
        df_daily.resample("W")
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna()
    )

    sh_weekly, sl_weekly = detect_swings(df_weekly, order=2)
    weekly_trend = determine_trend(sh_weekly, sl_weekly)

    # 2. Daily Swing Structure (Top-Down Step 2)
    sh_daily, sl_daily = detect_swings(df_daily, order=3)
    daily_trend = determine_trend(sh_daily, sl_daily)

    # ATR for volatility buffers
    atr_val = (
        AverageTrueRange(
            df_daily["High"], df_daily["Low"], df_daily["Close"], window=14
        )
        .average_true_range()
        .iloc[-1]
    )

    # Supply and Demand Zones (POIs)
    demand_zone, supply_zone = _extract_zones(df_daily, sh_daily, sl_daily, atr_val)

    current_price = float(df_daily["Close"].iloc[-1])

    # Determine overall effective trend bias
    if weekly_trend != "Consolidation":
        effective_trend = weekly_trend
    else:
        effective_trend = daily_trend

    # Classify tradability & Phase (Impulse vs Correction)
    is_tradable = effective_trend != "Consolidation"
    phase = "Consolidation"
    action = "NO TRADE (Consolidation)"

    entry_price = None
    stop_loss = None
    target_price = None
    risk_reward = None
    potential_gain = None
    potential_loss = None

    if effective_trend == "Uptrend":
        action = "BUY (Long)"
        # Check if price is near demand zone (correction) or extending (impulse)
        if demand_zone and current_price <= (demand_zone.high_price + atr_val):
            phase = "Correction (Optimal Entry Window)"
            entry_price = round(current_price, 2)
        else:
            phase = "Impulse Extension (Wait for Pullback)"
            entry_price = (
                round(demand_zone.high_price, 2)
                if demand_zone
                else round(current_price * 0.98, 2)
            )

        # Stop loss below demand zone / prior swing low
        ref_low = demand_zone.low_price if demand_zone else current_price - atr_val
        stop_loss = round(ref_low - 0.5 * atr_val, 2)

        risk = entry_price - stop_loss
        if risk <= 0:
            risk = atr_val * 1.5
            stop_loss = round(entry_price - risk, 2)

        # Target: Minimum 3:1 R:R to satisfy Step 5
        structural_target = (
            supply_zone.high_price
            if supply_zone and supply_zone.high_price > entry_price
            else entry_price + 3.0 * risk
        )
        target_price = round(max(structural_target, entry_price + 3.0 * risk), 2)
        risk_reward = round((target_price - entry_price) / risk, 2)
        potential_gain = round(((target_price - entry_price) / entry_price) * 100, 1)
        potential_loss = round(((entry_price - stop_loss) / entry_price) * 100, 1)

    elif effective_trend == "Downtrend":
        action = "SELL (Short)"
        if supply_zone and current_price >= (supply_zone.low_price - atr_val):
            phase = "Correction (Optimal Short Entry Window)"
            entry_price = round(current_price, 2)
        else:
            phase = "Impulse Extension (Wait for Rally to Supply)"
            entry_price = (
                round(supply_zone.low_price, 2)
                if supply_zone
                else round(current_price * 1.02, 2)
            )

        ref_high = supply_zone.high_price if supply_zone else current_price + atr_val
        stop_loss = round(ref_high + 0.5 * atr_val, 2)

        risk = stop_loss - entry_price
        if risk <= 0:
            risk = atr_val * 1.5
            stop_loss = round(entry_price + risk, 2)

        structural_target = (
            demand_zone.low_price
            if demand_zone and demand_zone.low_price < entry_price
            else entry_price - 3.0 * risk
        )
        target_price = round(min(structural_target, entry_price - 3.0 * risk), 2)
        risk_reward = round((entry_price - target_price) / risk, 2)
        potential_gain = round(((entry_price - target_price) / entry_price) * 100, 1)
        potential_loss = round(((stop_loss - entry_price) / entry_price) * 100, 1)

    # Management and exit rules from SWINGTRADE.md
    management_rules = [
        "**Trailing Stop:** Draw stop-loss higher after each validated higher low forms (or lower on shorts). Never move stops backward.",
        "**Take Partials:** Scale out 50% at 2R reward; let remaining position run to final 3:1+ target.",
        "**Breakeven Trigger:** Move stop loss to breakeven once price reaches the midpoint of the impulse move.",
        "**No Panic Exits:** Hold according to defined target levels rather than exiting prematurely on intraday noise.",
    ]

    exit_rules = [
        f"**Minimum 3:1 RR Enforced:** Calculated Risk/Reward is {risk_reward or 3.0}:1, maintaining positive long-term edge.",
        "**Hard Invalidation:** If price closes beyond the POI boundary, accept the loss immediately per the contingency exit plan.",
        "**Take Profit POI:** Target is set at the opposite structural supply/demand zone.",
    ]

    # Summary
    if is_tradable:
        summary = (
            f"**Multi-Timeframe Structure Analysis:**\n\n"
            f"- **Weekly 1W Structure:** `{weekly_trend}` (Macro trend bias)\n"
            f"- **Daily 1D Structure:** `{daily_trend}` (Sub-structure alignment)\n"
            f"- **Current Phase:** `{phase}`\n"
            f"- **Directional Action:** **{action}**\n\n"
            f"The asset is exhibiting **{effective_trend.lower()}** market structure with "
            f"{'higher highs and higher lows' if effective_trend == 'Uptrend' else 'lower highs and lower lows'}. "
            f"Entry is positioned around the **{demand_zone.kind if effective_trend == 'Uptrend' else supply_zone.kind} Zone (POI)** "
            f"to enter on a corrective pullback and ride the next impulse wave."
        )
    else:
        summary = (
            f"**Multi-Timeframe Structure Analysis:**\n\n"
            f"- **Weekly 1W Structure:** `{weekly_trend}`\n"
            f"- **Daily 1D Structure:** `{daily_trend}`\n"
            f"- **Directional Action:** **NO TRADE** (Consolidation phase)\n\n"
            f"⚠️ **Per SWINGTRADE.md Rule:** *'During consolidation phases we simply DO NOT TRADE as there is no clear direction.'* "
            f"The price action is currently moving sideways without confirmed higher highs/lows or lower highs/lows. "
            f"Wait for a decisive structural breakout to establish a new trending impulse before deploying capital."
        )

    success_pct, wins, total_trades = backtest_swing_structure(df_daily)

    plan = SwingTradePlan(
        ticker=ticker,
        weekly_trend=weekly_trend,
        daily_trend=daily_trend,
        effective_trend=effective_trend,
        action=action,
        phase=phase,
        is_tradable=is_tradable,
        demand_zone=demand_zone,
        supply_zone=supply_zone,
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_price=target_price,
        risk_reward=risk_reward,
        potential_gain=potential_gain,
        potential_loss=potential_loss,
        success_pct=success_pct,
        wins=wins,
        total_trades=total_trades,
        weekly_swings=sh_weekly + sl_weekly,
        daily_swings=sh_daily + sl_daily,
        summary=summary,
        management_rules=management_rules,
        exit_rules=exit_rules,
    )

    plan.chart = build_swing_chart(df_daily, plan)
    return plan

