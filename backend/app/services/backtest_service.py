import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.services.data_service import get_historical_bars
from app.cache import get_cached, set_cached

def _compute_strategy_setup(strategy: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Compute an actionable trade setup using the selected strategy's own indicators."""
    last = df.iloc[-1]
    last_close = float(last["close"])
    last_atr = float(last["atr"]) if pd.notna(last["atr"]) and last["atr"] > 0 else (last_close * 0.02)

    if strategy == "ema_cross":
        ema20 = float(last["ema_20"])
        ema50 = float(last["ema_50"])
        bullish = ema20 > ema50
        # Entry at EMA 20 pullback level
        setup_entry = round(ema20, 2)
        # SL below EMA 50 (the slow average acts as dynamic support)
        setup_sl = round(min(ema50, last_close) - last_atr, 2)
        risk = max(0.01, setup_entry - setup_sl)
        setup_tp = round(setup_entry + (2.0 * risk), 2)
        condition = f"EMA 20 (${ema20:.2f}) {'above' if bullish else 'below'} EMA 50 (${ema50:.2f})"
        rationale = (
            f"Trend {'bullish' if bullish else 'bearish'}: {condition}. "
            f"Entry anchored at EMA 20 pullback (${setup_entry:.2f}), SL below EMA 50 support (${setup_sl:.2f}), "
            f"TP target at 1:2 R:R (${setup_tp:.2f})."
        )

    elif strategy == "rsi_reversal":
        rsi_val = float(last["rsi"])
        if rsi_val <= 40:
            # Oversold zone — anticipate bounce
            setup_entry = round(last_close, 2)
            recent_low = float(df["low"].iloc[-5:].min())
            setup_sl = round(recent_low - (0.5 * last_atr), 2)
            risk = max(0.01, setup_entry - setup_sl)
            setup_tp = round(setup_entry + (2.0 * risk), 2)
            condition = f"RSI at {rsi_val:.1f} (approaching oversold zone ≤30)"
            rationale = (
                f"RSI mean reversion: {condition}. "
                f"Entry on bounce (${setup_entry:.2f}), SL below 5-bar swing low (${setup_sl:.2f}), "
                f"TP target at 1:2 R:R (${setup_tp:.2f})."
            )
        else:
            # Neutral/overbought zone — awaiting oversold pullback
            setup_entry = round(last_close, 2)
            setup_sl = round(last_close - (1.5 * last_atr), 2)
            risk = max(0.01, setup_entry - setup_sl)
            setup_tp = round(setup_entry + (2.0 * risk), 2)
            condition = f"RSI at {rsi_val:.1f} (neutral zone — awaiting oversold dip below 30)"
            rationale = (
                f"RSI mean reversion: {condition}. "
                f"Anticipatory setup at current price (${setup_entry:.2f}), "
                f"SL at 1.5x ATR (${setup_sl:.2f}), TP at 1:2 R:R (${setup_tp:.2f}). "
                f"Best entry triggers when RSI drops below 30 and recovers."
            )

    elif strategy == "macd_cross":
        macd_val = float(last["macd_line"])
        macd_sig = float(last["macd_signal"])
        bullish = macd_val > macd_sig
        setup_entry = round(last_close, 2)
        recent_low = float(df["low"].iloc[-10:].min())
        setup_sl = round(recent_low - (0.5 * last_atr), 2)
        risk = max(0.01, setup_entry - setup_sl)
        setup_tp = round(setup_entry + (2.0 * risk), 2)
        condition = f"MACD ({macd_val:.2f}) {'above' if bullish else 'below'} Signal ({macd_sig:.2f})"
        rationale = (
            f"MACD momentum: {condition}. "
            f"Entry on crossover confirmation (${setup_entry:.2f}), "
            f"SL below 10-bar swing low (${setup_sl:.2f}), "
            f"TP target at 1:2 R:R (${setup_tp:.2f})."
        )

    elif strategy == "bollinger_breakout":
        bb_lower = float(last["bb_lower"]) if pd.notna(last["bb_lower"]) else last_close * 0.97
        bb_upper = float(last["bb_upper"]) if pd.notna(last["bb_upper"]) else last_close * 1.03
        bb_mid = float(last["bb_middle"]) if pd.notna(last["bb_middle"]) else last_close
        setup_entry = round(bb_lower, 2)
        setup_sl = round(bb_lower - last_atr, 2)
        setup_tp = round(bb_upper, 2)
        condition = f"Bollinger Lower: ${bb_lower:.2f}, Mid: ${bb_mid:.2f}, Upper: ${bb_upper:.2f}"
        rationale = (
            f"Bollinger band reversion: {condition}. "
            f"Entry at lower band touch (${setup_entry:.2f}), "
            f"SL below band by 1x ATR (${setup_sl:.2f}), "
            f"TP target near upper band (${setup_tp:.2f})."
        )

    else:  # smc_fvg_ob
        fvg_entry = None
        fvg_sl = None
        for i in range(len(df) - 1, max(1, len(df) - 30), -1):
            if i < 2:
                break
            c1_high = float(df.loc[i - 2, "high"])
            c3_low = float(df.loc[i, "low"])
            c2_close = float(df.loc[i - 1, "close"])
            c2_open = float(df.loc[i - 1, "open"])
            if c3_low > c1_high and c2_close > c2_open:
                fvg_entry = round(c3_low, 2)
                fvg_sl = round(c1_high - last_atr, 2)
                break

        if fvg_entry and fvg_sl:
            setup_entry = fvg_entry
            setup_sl = fvg_sl
            risk = max(0.01, setup_entry - setup_sl)
            setup_tp = round(setup_entry + (2.0 * risk), 2)
            condition = f"Active Bullish FVG zone ${fvg_sl:.2f} — ${fvg_entry:.2f}"
            rationale = (
                f"Smart Money Concepts: {condition}. "
                f"Entry on FVG retest (${setup_entry:.2f}), "
                f"SL below order block invalidation (${setup_sl:.2f}), "
                f"TP target at liquidity pool (${setup_tp:.2f}) offering 1:2 R:R."
            )
        else:
            setup_entry = round(last_close, 2)
            setup_sl = round(last_close - (1.5 * last_atr), 2)
            risk = max(0.01, setup_entry - setup_sl)
            setup_tp = round(setup_entry + (2.0 * risk), 2)
            condition = "No active FVG detected in recent 30 bars"
            rationale = (
                f"Smart Money Concepts: {condition}. "
                f"Fallback dynamic setup at current price (${setup_entry:.2f}), "
                f"SL at 1.5x ATR (${setup_sl:.2f}), TP at 1:2 R:R (${setup_tp:.2f}). "
                f"Awaiting new displacement candle to establish fresh FVG zone."
            )

    # Ensure SL is strictly less than entry
    if setup_sl >= setup_entry:
        setup_sl = round(setup_entry - last_atr, 2)
    risk = max(0.01, setup_entry - setup_sl)
    if setup_tp <= setup_entry:
        setup_tp = round(setup_entry + (2.0 * risk), 2)

    rr_ratio = round((setup_tp - setup_entry) / risk, 1)

    return {
        "entry_price": setup_entry,
        "stop_loss_price": setup_sl,
        "take_profit_price": setup_tp,
        "risk_reward_ratio": f"1:{rr_ratio:.1f}",
        "potential_gain_pct": round(((setup_tp - setup_entry) / setup_entry) * 100, 2),
        "potential_risk_pct": round(((setup_entry - setup_sl) / setup_entry) * 100, 2),
        "condition": condition,
        "rationale": rationale,
    }

def run_backtest(ticker: str, strategy: str = "ema_cross", lookback_days: int = 365) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"backtest:v2:{ticker}:{strategy}:{lookback_days}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    bars = get_historical_bars(ticker, timeframe="1D")
    if not bars or len(bars) < 50:
        return {"error": "Insufficient historical data for backtesting"}

    df = pd.DataFrame(bars)
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # Calculate basic indicators
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50.0)

    # MACD
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema_12 - ema_26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    rolling_mean = df["close"].rolling(window=20).mean()
    rolling_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = rolling_mean + (rolling_std * 2)
    df["bb_lower"] = rolling_mean - (rolling_std * 2)
    df["bb_middle"] = rolling_mean

    # ATR (14)
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=14).mean().fillna(tr)

    # Detect Buy / Exit signals according to strategy
    signals = pd.Series(0, index=df.index)

    if strategy == "ema_cross":
        # Buy when EMA 20 crosses above EMA 50
        bullish_cross = (df["ema_20"] > df["ema_50"]) & (df["ema_20"].shift(1) <= df["ema_50"].shift(1))
        bearish_cross = (df["ema_20"] < df["ema_50"]) & (df["ema_20"].shift(1) >= df["ema_50"].shift(1))
        signals[bullish_cross] = 1
        signals[bearish_cross] = -1

    elif strategy == "rsi_reversal":
        # Buy when RSI was oversold (<30) and climbs back above 30
        oversold_bounce = (df["rsi"] > 30) & (df["rsi"].shift(1) <= 30)
        overbought_exit = (df["rsi"] > 70) & (df["rsi"].shift(1) <= 70)
        signals[oversold_bounce] = 1
        signals[overbought_exit] = -1

    elif strategy == "macd_cross":
        # Buy when MACD crosses above signal line
        macd_buy = (df["macd_line"] > df["macd_signal"]) & (df["macd_line"].shift(1) <= df["macd_signal"].shift(1))
        macd_sell = (df["macd_line"] < df["macd_signal"]) & (df["macd_line"].shift(1) >= df["macd_signal"].shift(1))
        signals[macd_buy] = 1
        signals[macd_sell] = -1

    elif strategy == "bollinger_breakout":
        # Buy when price crosses above lower band from below or breaks 20 SMA with momentum
        bb_bounce = (df["close"] > df["bb_lower"]) & (df["close"].shift(1) <= df["bb_lower"].shift(1))
        bb_exit = df["close"] >= df["bb_upper"]
        signals[bb_bounce] = 1
        signals[bb_exit] = -1

    elif strategy == "smc_fvg_ob":
        # Smart Money Concepts: Fair Value Gap (FVG) and Order Block Retest
        # Bullish FVG: Candle i-2 High < Candle i Low (Gap between high of candle 1 and low of candle 3)
        fvg_zones = []
        for i in range(2, len(df)):
            c1_high = df.loc[i - 2, "high"]
            c3_low = df.loc[i, "low"]
            c2_close = df.loc[i - 1, "close"]
            c2_open = df.loc[i - 1, "open"]
            # Bullish displacement candle
            if c3_low > c1_high and c2_close > c2_open:
                fvg_zones.append((c1_high, c3_low, i))

        # Check retests of FVG zones
        for i in range(len(df)):
            curr_low = df.loc[i, "low"]
            curr_close = df.loc[i, "close"]
            for low_bound, high_bound, created_idx in fvg_zones:
                if 0 < (i - created_idx) <= 15: # Retest within 15 bars
                    if curr_low <= high_bound and curr_close >= low_bound:
                        signals.iloc[i] = 1
                        break

    # Simulate trades with 1:2 Risk/Reward using ATR
    trades = []
    in_trade = False
    entry_price = 0.0
    entry_time = None
    stop_loss = 0.0
    take_profit = 0.0

    for i in range(30, len(df)):
        row = df.iloc[i]
        curr_price = float(row["close"])
        curr_high = float(row["high"])
        curr_low = float(row["low"])
        curr_atr = float(row["atr"]) if pd.notna(row["atr"]) and row["atr"] > 0 else (curr_price * 0.02)
        curr_time = int(row["time"]) if isinstance(row["time"], (int, np.integer, float, np.floating)) else str(row["time"])

        sig = signals.iloc[i]

        if not in_trade:
            if sig == 1:
                in_trade = True
                entry_price = curr_price
                entry_time = curr_time
                risk = 1.5 * curr_atr
                stop_loss = round(entry_price - risk, 2)
                take_profit = round(entry_price + (2.0 * risk), 2)
        else:
            # Check exit conditions
            hit_tp = curr_high >= take_profit
            hit_sl = curr_low <= stop_loss
            strategy_exit = sig == -1

            if hit_tp or hit_sl or strategy_exit:
                if hit_tp:
                    exit_price = take_profit
                    outcome = "WIN"
                elif hit_sl:
                    exit_price = stop_loss
                    outcome = "LOSS"
                else:
                    exit_price = curr_price
                    outcome = "WIN" if exit_price > entry_price else "LOSS"

                pnl = exit_price - entry_price
                pnl_pct = (pnl / entry_price) * 100.0

                trades.append({
                    "entry_time": int(entry_time) if isinstance(entry_time, (int, np.integer, float, np.floating)) else str(entry_time),
                    "exit_time": int(curr_time) if isinstance(curr_time, (int, np.integer, float, np.floating)) else str(curr_time),
                    "entry_price": round(float(entry_price), 2),
                    "exit_price": round(float(exit_price), 2),
                    "stop_loss": round(float(stop_loss), 2),
                    "take_profit": round(float(take_profit), 2),
                    "outcome": outcome,
                    "pnl": round(float(pnl), 2),
                    "pnl_percent": round(float(pnl_pct), 2)
                })
                in_trade = False

    # Aggregate performance metrics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t["outcome"] == "WIN")
    losing_trades = total_trades - winning_trades
    success_rate = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0.0

    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 1.0)
    total_return_pct = round(sum(t["pnl_percent"] for t in trades), 2)

    # Strategy-Specific Actionable Setup Calculation
    strategy_display_names = {
        "ema_cross": "EMA 20 / 50 Trend Cross",
        "rsi_reversal": "RSI Mean Reversion (30/70)",
        "macd_cross": "MACD Signal Crossover",
        "bollinger_breakout": "Bollinger Bands Breakout",
        "smc_fvg_ob": "Smart Money Concepts (FVG & Order Block)",
    }
    strategy_display_name = strategy_display_names.get(strategy, strategy)
    setup_data = _compute_strategy_setup(strategy, df)

    result = {
        "symbol": ticker,
        "strategy": strategy,
        "strategy_name": strategy_display_name,
        "total_trades": total_trades,
        "successful_trades": winning_trades,
        "losing_trades": losing_trades,
        "success_rate": success_rate,
        "profit_factor": profit_factor,
        "total_return_percent": total_return_pct,
        "setup": setup_data,
        "recent_trades": trades[-10:] # last 10 trades for display
    }

    set_cached(cache_key, result, ttl_seconds=600)
    return result
