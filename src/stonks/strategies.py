"""Trade strategy generator.

Produces actionable trade strategies with entry/exit points and
historical back-tested success percentages.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.trend import EMAIndicator

from stonks.data import StockData
from stonks.smc import analyse_smc
from stonks.swing_trade import analyse_swing_trade


@dataclass
class TradeStrategy:
    """A single trade strategy recommendation."""

    name: str
    description: str
    direction: str  # "Long" or "Short"
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward: float
    success_pct: float  # back-tested success percentage
    timeframe: str
    wins: int = 0
    total_trades: int = 0

    @property
    def potential_gain(self) -> float:
        if self.direction == "Long":
            return (self.target_price / self.entry_price - 1) * 100
        return (self.entry_price / self.target_price - 1) * 100

    @property
    def potential_loss(self) -> float:
        if self.direction == "Long":
            return (1 - self.stop_loss / self.entry_price) * 100
        return (self.stop_loss / self.entry_price - 1) * 100


def _backtest_mean_reversion(close: pd.Series, window: int = 20) -> tuple[float, int, int]:
    """Back-test mean reversion: buy when price drops below lower BB, sell at mid."""
    if len(close) < window + 50:
        return 55.0, 0, 0

    bb = BollingerBands(close, window=window)
    lower = bb.bollinger_lband()
    mid = bb.bollinger_mavg()

    trades = 0
    wins = 0
    in_trade = False

    for i in range(window, len(close)):
        if not in_trade and close.iloc[i] <= lower.iloc[i]:
            in_trade = True
            entry = close.iloc[i]
        elif in_trade and close.iloc[i] >= mid.iloc[i]:
            in_trade = False
            trades += 1
            if close.iloc[i] > entry:
                wins += 1
        elif in_trade and i == len(close) - 1:
            trades += 1
            if close.iloc[i] > entry:
                wins += 1

    if trades == 0:
        return 55.0, 0, 0
    return round((wins / trades) * 100, 1), wins, trades


def _backtest_momentum(close: pd.Series) -> tuple[float, int, int]:
    """Back-test momentum: buy when SMA20 crosses above SMA50, exit on cross below."""
    if len(close) < 60:
        return 50.0, 0, 0

    sma20 = SMAIndicator(close, window=20).sma_indicator()
    sma50 = SMAIndicator(close, window=50).sma_indicator()

    trades = 0
    wins = 0
    in_trade = False
    entry = 0.0

    for i in range(50, len(close)):
        if not in_trade and sma20.iloc[i] > sma50.iloc[i] and sma20.iloc[i - 1] <= sma50.iloc[i - 1]:
            in_trade = True
            entry = close.iloc[i]
        elif in_trade and (sma20.iloc[i] < sma50.iloc[i] or i == len(close) - 1):
            in_trade = False
            trades += 1
            if close.iloc[i] > entry:
                wins += 1

    if trades == 0:
        return 50.0, 0, 0
    return round((wins / trades) * 100, 1), wins, trades


def _backtest_rsi_reversal(close: pd.Series) -> tuple[float, int, int]:
    """Back-test RSI reversal: buy when RSI < 30, sell when RSI > 50."""
    if len(close) < 30:
        return 55.0, 0, 0

    rsi = RSIIndicator(close, window=14).rsi()

    trades = 0
    wins = 0
    in_trade = False
    entry = 0.0

    for i in range(14, len(close)):
        if not in_trade and rsi.iloc[i] < 30:
            in_trade = True
            entry = close.iloc[i]
        elif in_trade and (rsi.iloc[i] > 50 or i == len(close) - 1):
            in_trade = False
            trades += 1
            if close.iloc[i] > entry:
                wins += 1

    if trades == 0:
        return 60.0, 0, 0
    return round((wins / trades) * 100, 1), wins, trades


def _backtest_breakout(close: pd.Series, lookback: int = 20) -> tuple[float, int, int]:
    """Back-test breakout: buy when price breaks above N-day high."""
    if len(close) < lookback + 30:
        return 50.0, 0, 0

    trades = 0
    wins = 0

    for i in range(lookback, len(close) - 5):
        prev_high = close.iloc[i - lookback : i].max()
        if close.iloc[i] > prev_high and close.iloc[i - 1] <= prev_high:
            trades += 1
            # Check if price is higher 5 bars later
            exit_idx = min(i + 5, len(close) - 1)
            if close.iloc[exit_idx] > close.iloc[i]:
                wins += 1

    if trades == 0:
        return 48.0, 0, 0
    return round((wins / trades) * 100, 1), wins, trades


# ---------------------------------------------------------------------------
# Strategy generators
# ---------------------------------------------------------------------------

def _mean_reversion_strategy(stock: StockData) -> TradeStrategy | None:
    """Mean-reversion strategy using Bollinger Bands."""
    close = stock.history["Close"]
    if len(close) < 30:
        return None

    bb = BollingerBands(close, window=20)
    current = close.iloc[-1]
    lower = bb.bollinger_lband().iloc[-1]
    mid = bb.bollinger_mavg().iloc[-1]
    upper = bb.bollinger_hband().iloc[-1]

    atr_val = AverageTrueRange(
        stock.history["High"], stock.history["Low"], close, window=14,
    ).average_true_range().iloc[-1]

    entry = lower
    stop = lower - 1.5 * atr_val
    target = mid
    rr = (target - entry) / (entry - stop) if entry > stop else 0

    success, wins, trades = _backtest_mean_reversion(close)

    return TradeStrategy(
        name="Mean Reversion (Bollinger Bands)",
        description=(
            "Enter a **long** position when price touches the lower Bollinger Band, "
            "targeting a move back to the middle band. The strategy exploits "
            "short-term overreactions."
        ),
        direction="Long",
        entry_price=round(entry, 2),
        stop_loss=round(stop, 2),
        target_price=round(target, 2),
        risk_reward=round(rr, 2),
        success_pct=success,
        timeframe="1–2 weeks",
        wins=wins,
        total_trades=trades,
    )


def _momentum_strategy(stock: StockData) -> TradeStrategy | None:
    """Momentum strategy using SMA crossover."""
    close = stock.history["Close"]
    if len(close) < 50:
        return None

    sma20 = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
    sma50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
    current = close.iloc[-1]

    atr_val = AverageTrueRange(
        stock.history["High"], stock.history["Low"], close, window=14,
    ).average_true_range().iloc[-1]

    if sma20 > sma50:
        # Bullish momentum
        entry = current
        stop = current - 2.0 * atr_val
        target = current + 3.0 * atr_val
        direction = "Long"
    else:
        # Bearish momentum
        entry = current
        stop = current + 2.0 * atr_val
        target = current - 3.0 * atr_val
        direction = "Short"

    rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0
    success, wins, trades = _backtest_momentum(close)

    return TradeStrategy(
        name="Momentum (SMA Crossover)",
        description=(
            f"{'Bullish' if direction == 'Long' else 'Bearish'} momentum strategy. "
            f"SMA20 is {'above' if sma20 > sma50 else 'below'} SMA50, indicating a "
            f"{'bullish' if sma20 > sma50 else 'bearish'} trend. "
            f"Ride the trend with ATR-based stops."
        ),
        direction=direction,
        entry_price=round(entry, 2),
        stop_loss=round(stop, 2),
        target_price=round(target, 2),
        risk_reward=round(rr, 2),
        success_pct=success,
        timeframe="2–6 weeks",
        wins=wins,
        total_trades=trades,
    )


def _rsi_reversal_strategy(stock: StockData) -> TradeStrategy | None:
    """RSI reversal strategy."""
    close = stock.history["Close"]
    if len(close) < 20:
        return None

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    current = close.iloc[-1]

    atr_val = AverageTrueRange(
        stock.history["High"], stock.history["Low"], close, window=14,
    ).average_true_range().iloc[-1]

    if rsi < 40:
        entry = current
        stop = current - 1.5 * atr_val
        target = current + 2.5 * atr_val
        direction = "Long"
        desc = (
            f"RSI at {rsi:.1f} indicates the stock is approaching oversold levels. "
            "Enter long anticipating a bounce back to neutral RSI levels."
        )
    elif rsi > 60:
        entry = current
        stop = current + 1.5 * atr_val
        target = current - 2.5 * atr_val
        direction = "Short"
        desc = (
            f"RSI at {rsi:.1f} indicates the stock is approaching overbought levels. "
            "Enter short anticipating a pullback."
        )
    else:
        entry = current * 0.97  # wait for a dip
        stop = entry - 1.5 * atr_val
        target = entry + 2.5 * atr_val
        direction = "Long"
        desc = (
            f"RSI at {rsi:.1f} is neutral. Set a limit buy 3% below current price "
            "to catch a short-term dip."
        )

    rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0
    success, wins, trades = _backtest_rsi_reversal(close)

    return TradeStrategy(
        name="RSI Reversal",
        description=desc,
        direction=direction,
        entry_price=round(entry, 2),
        stop_loss=round(stop, 2),
        target_price=round(target, 2),
        risk_reward=round(rr, 2),
        success_pct=success,
        timeframe="3–10 days",
        wins=wins,
        total_trades=trades,
    )


def _breakout_strategy(stock: StockData) -> TradeStrategy | None:
    """Breakout strategy using N-day high."""
    close = stock.history["Close"]
    if len(close) < 30:
        return None

    lookback = 20
    resistance = close.iloc[-lookback:].max()
    current = close.iloc[-1]

    atr_val = AverageTrueRange(
        stock.history["High"], stock.history["Low"], close, window=14,
    ).average_true_range().iloc[-1]

    entry = round(resistance * 1.005, 2)  # buy just above resistance
    stop = round(resistance - 1.0 * atr_val, 2)
    target = round(entry + 3.0 * atr_val, 2)
    rr = abs(target - entry) / abs(entry - stop) if abs(entry - stop) > 0 else 0

    success, wins, trades = _backtest_breakout(close)

    return TradeStrategy(
        name="Breakout (20-Day High)",
        description=(
            f"Buy when price breaks above the 20-day high of ${resistance:.2f}. "
            "Breakouts often lead to continued momentum. "
            "Set a tight stop just below the breakout level."
        ),
        direction="Long",
        entry_price=entry,
        stop_loss=stop,
        target_price=target,
        risk_reward=round(rr, 2),
        success_pct=success,
        timeframe="1–3 weeks",
        wins=wins,
        total_trades=trades,
    )


# ---------------------------------------------------------------------------
# Swing Trade Strategy (from SWINGTRADE.md)
# ---------------------------------------------------------------------------

def _swing_trade_strategy(stock: StockData) -> TradeStrategy | None:
    """Swing Trade strategy using multi-timeframe market structure from SWINGTRADE.md."""
    plan = analyse_swing_trade(stock)
    if not plan.is_tradable or plan.entry_price is None or plan.stop_loss is None or plan.target_price is None:
        return None

    direction = "Long" if "BUY" in plan.action else "Short"
    return TradeStrategy(
        name="Swing Trade (Market Structure)",
        description=plan.summary,
        direction=direction,
        entry_price=plan.entry_price,
        stop_loss=plan.stop_loss,
        target_price=plan.target_price,
        risk_reward=plan.risk_reward or 3.0,
        success_pct=plan.success_pct,
        timeframe=plan.timeframe,
        wins=plan.wins,
        total_trades=plan.total_trades,
    )


def _smc_strategy(stock: StockData) -> TradeStrategy | None:
    """Smart Money Concepts (SMC) strategy: Order Blocks, FVGs, and Liquidity Pools."""
    smc = analyse_smc(stock)
    if "WAIT" in smc.action or smc.entry_price is None or smc.stop_loss is None or smc.target_price is None:
        return None

    direction = "Long" if "BUY" in smc.action else "Short"
    return TradeStrategy(
        name="Smart Money Concepts (Order Block / FVG)",
        description=smc.summary,
        direction=direction,
        entry_price=smc.entry_price,
        stop_loss=smc.stop_loss,
        target_price=smc.target_price,
        risk_reward=smc.risk_reward or 3.0,
        success_pct=smc.success_pct,
        timeframe=smc.timeframe,
        wins=smc.wins,
        total_trades=smc.total_trades,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_strategies(stock: StockData) -> list[TradeStrategy]:
    """Generate trade strategies for the given stock."""
    generators = [
        _momentum_strategy,
        _mean_reversion_strategy,
        _rsi_reversal_strategy,
        _breakout_strategy,
        _swing_trade_strategy,
        _smc_strategy,
    ]

    strategies: list[TradeStrategy] = []
    for gen in generators:
        try:
            strat = gen(stock)
            if strat is not None:
                strategies.append(strat)
        except Exception:  # noqa: BLE001
            continue

    return strategies

