import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from app.services.data_service import get_historical_bars
from app.cache import get_cached, set_cached

def _detect_swing_highs_lows(df: pd.DataFrame, window: int = 3) -> Tuple[List[dict], List[dict]]:
    """Detect local swing highs and swing lows using a rolling window."""
    swing_highs = []
    swing_lows = []
    n = len(df)
    if n < window * 2 + 1:
        return swing_highs, swing_lows

    for i in range(window, n - window):
        high_i = float(df.loc[i, "high"])
        low_i = float(df.loc[i, "low"])

        is_high = True
        for k in range(i - window, i + window + 1):
            if k != i and float(df.loc[k, "high"]) >= high_i:
                is_high = False
                break
        if is_high:
            swing_highs.append({"index": i, "price": high_i, "time": df.loc[i, "time"]})

        is_low = True
        for k in range(i - window, i + window + 1):
            if k != i and float(df.loc[k, "low"]) <= low_i:
                is_low = False
                break
        if is_low:
            swing_lows.append({"index": i, "price": low_i, "time": df.loc[i, "time"]})

    return swing_highs, swing_lows

def _classify_market_structure(df: pd.DataFrame, window: int = 3) -> Tuple[str, dict]:
    """
    Classify market structure into UPTREND (HH/HL), DOWNTREND (LH/LL), or CONSOLIDATION.
    Returns (regime, details_dict).
    """
    if len(df) < 12:
        return "CONSOLIDATION", {"reason": "Insufficient data"}

    swing_highs, swing_lows = _detect_swing_highs_lows(df, window=window)

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        close_series = df["close"]
        sma20 = float(close_series.rolling(min(20, len(df)), min_periods=5).mean().iloc[-1])
        last_close = float(close_series.iloc[-1])
        if last_close > sma20 * 1.015:
            return "UPTREND", {"type": "momentum_uptrend"}
        elif last_close < sma20 * 0.985:
            return "DOWNTREND", {"type": "momentum_downtrend"}
        else:
            return "CONSOLIDATION", {"type": "neutral_range"}

    sh1, sh2 = swing_highs[-2]["price"], swing_highs[-1]["price"]
    sl1, sl2 = swing_lows[-2]["price"], swing_lows[-1]["price"]

    higher_highs = sh2 > sh1
    higher_lows = sl2 > sl1
    lower_highs = sh2 < sh1
    lower_lows = sl2 < sl1

    if higher_highs and higher_lows:
        regime = "UPTREND"
    elif lower_highs and lower_lows:
        regime = "DOWNTREND"
    elif higher_highs and not lower_lows:
        regime = "UPTREND"
    elif lower_lows and not higher_highs:
        regime = "DOWNTREND"
    else:
        regime = "CONSOLIDATION"

    details = {
        "sh1": sh1,
        "sh2": sh2,
        "sl1": sl1,
        "sl2": sl2,
        "recent_high": sh2,
        "recent_low": sl2,
    }
    return regime, details

def _detect_unswept_liquidity(df: pd.DataFrame, lookback: int = 60) -> Tuple[float, float, str]:
    """
    Identify the most prominent unswept liquidity pool on the chart that price is likely to target.
    Checks for Equal Lows (sell-side liquidity) or Equal Highs (buy-side liquidity) or major swing extremes.
    Returns (pool_low, pool_high, pool_type).
    """
    n = len(df)
    start_idx = max(0, n - lookback)
    sub = df.iloc[start_idx:].reset_index(drop=True)
    last_close = float(sub["close"].iloc[-1])
    last_atr = float(sub["atr"].iloc[-1]) if "atr" in sub.columns and pd.notna(sub["atr"].iloc[-1]) and sub["atr"].iloc[-1] > 0 else (last_close * 0.02)

    swing_highs, swing_lows = _detect_swing_highs_lows(sub, window=2)

    # 1. Look for Equal Lows (EQL) below last_close that haven't been swept
    lows_below = [s for s in swing_lows if s["price"] < last_close]
    tol = 0.0075  # 0.75% price tolerance for equal levels

    best_eql = None
    best_eql_cluster = None
    best_eql_count = 0
    for i in range(len(lows_below)):
        p1 = lows_below[i]["price"]
        cluster = [lows_below[i]]
        for j in range(i + 1, len(lows_below)):
            p2 = lows_below[j]["price"]
            if abs(p2 - p1) / max(p1, 0.01) <= tol:
                cluster.append(lows_below[j])
        if len(cluster) >= 2 and len(cluster) > best_eql_count:
            last_touch_idx = max(c["index"] for c in cluster)
            cluster_min = min(c["price"] for c in cluster)
            subsequent_lows = sub["low"].iloc[last_touch_idx + 1 :]
            if len(subsequent_lows) == 0 or subsequent_lows.min() >= cluster_min * 0.998:
                best_eql = round(float(cluster_min), 2)
                best_eql_cluster = cluster
                best_eql_count = len(cluster)

    if best_eql is not None and best_eql_cluster is not None:
        cluster_min = min(c["price"] for c in best_eql_cluster)
        cluster_max = max(c["price"] for c in best_eql_cluster)
        pool_high = round(float(cluster_max), 2)
        pool_low = round(float(cluster_min) - (0.35 * last_atr), 2)
        return pool_low, pool_high, f"Equal Lows (Sell-Side Liquidity Pool — {best_eql_count} touches)"

    # 2. Look for Equal Highs (EQH) above last_close if seeking buy-side liquidity
    highs_above = [s for s in swing_highs if s["price"] > last_close]
    best_eqh = None
    best_eqh_cluster = None
    best_eqh_count = 0
    for i in range(len(highs_above)):
        p1 = highs_above[i]["price"]
        cluster = [highs_above[i]]
        for j in range(i + 1, len(highs_above)):
            p2 = highs_above[j]["price"]
            if abs(p2 - p1) / max(p1, 0.01) <= tol:
                cluster.append(highs_above[j])
        if len(cluster) >= 2 and len(cluster) > best_eqh_count:
            last_touch_idx = max(c["index"] for c in cluster)
            cluster_max = max(c["price"] for c in cluster)
            subsequent_highs = sub["high"].iloc[last_touch_idx + 1 :]
            if len(subsequent_highs) == 0 or subsequent_highs.max() <= cluster_max * 1.002:
                best_eqh = round(float(cluster_max), 2)
                best_eqh_cluster = cluster
                best_eqh_count = len(cluster)

    # 3. Prefer Sell-Side Liquidity (Equal Lows or Swing Low below current price) for bullish liquidity sweep setup
    if lows_below:
        lowest_swing = min(lows_below, key=lambda s: s["price"])
        pool_high = round(float(lowest_swing["price"]), 2)
        pool_low = round(float(lowest_swing["price"]) - (0.4 * last_atr), 2)
        return pool_low, pool_high, "Major Swing Low (Sell-Side Liquidity Pool)"

    if best_eqh is not None and best_eqh_cluster is not None:
        cluster_min = min(c["price"] for c in best_eqh_cluster)
        cluster_max = max(c["price"] for c in best_eqh_cluster)
        pool_low = round(float(cluster_min), 2)
        pool_high = round(float(cluster_max) + (0.35 * last_atr), 2)
        return pool_low, pool_high, f"Equal Highs (Buy-Side Liquidity Pool — {best_eqh_count} touches)"

    if highs_above:
        highest_swing = max(highs_above, key=lambda s: s["price"])
        pool_low = round(float(highest_swing["price"]), 2)
        pool_high = round(float(highest_swing["price"]) + (0.4 * last_atr), 2)
        return pool_low, pool_high, "Major Swing High (Buy-Side Liquidity Pool)"

    lowest_recent = float(sub["low"].iloc[-min(20, len(sub)):].min())
    if lowest_recent < last_close:
        pool_high = round(lowest_recent, 2)
        pool_low = round(lowest_recent - (0.4 * last_atr), 2)
        return pool_low, pool_high, "Recent Low (Sell-Side Liquidity Pool)"

    highest_recent = float(sub["high"].iloc[-min(20, len(sub)):].max())
    pool_low = round(highest_recent, 2)
    pool_high = round(highest_recent + (0.4 * last_atr), 2)
    return pool_low, pool_high, "Recent High (Buy-Side Liquidity Pool)"

def _compute_strategy_setup(strategy: str, df: pd.DataFrame, ticker: str = "") -> Dict[str, Any]:
    """Compute an actionable trade setup using the selected strategy's own indicators."""
    last = df.iloc[-1]
    last_close = float(last["close"])
    last_atr = float(last["atr"]) if pd.notna(last["atr"]) and last["atr"] > 0 else (last_close * 0.02)
    timeframe_status = None

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

    elif strategy == "swing_structure":
        # 1. Weekly Analysis (1W)
        weekly_regime = "UPTREND"
        weekly_status_str = "Bullish Uptrend (HH/HL)"
        if ticker:
            try:
                w_bars = get_historical_bars(ticker, timeframe="1W")
                if w_bars and len(w_bars) >= 10:
                    w_df = pd.DataFrame(w_bars)
                    for col in ["close", "open", "high", "low"]:
                        w_df[col] = w_df[col].astype(float)
                    w_regime, _ = _classify_market_structure(w_df, window=2)
                    weekly_regime = w_regime
                    if w_regime == "UPTREND":
                        weekly_status_str = "Bullish Uptrend (HH/HL)"
                    elif w_regime == "DOWNTREND":
                        weekly_status_str = "Bearish Downtrend (LH/LL)"
                    else:
                        weekly_status_str = "Consolidation (Sideways Range)"
            except Exception:
                pass

        # 2. Daily Analysis (1D)
        daily_regime, _ = _classify_market_structure(df, window=3)
        if daily_regime == "UPTREND":
            daily_status_str = "Impulse / Demand Retest"
        elif daily_regime == "DOWNTREND":
            daily_status_str = "Bearish Correction (LH/LL)"
        else:
            daily_status_str = "Consolidation Range"

        # Refined 1D POI / Demand Zone
        recent_15_low = float(df["low"].iloc[-15:].min())
        recent_15_high = float(df["high"].iloc[-15:].max())
        demand_zone_low = round(recent_15_low, 2)
        demand_zone_high = round(recent_15_low + (0.382 * max(0.01, recent_15_high - recent_15_low)), 2)

        # 3. 4H Execution & Confirmation
        h4_status_str = "4H Pullback into POI"
        if ticker:
            try:
                h4_bars = get_historical_bars(ticker, timeframe="4H")
                if h4_bars and len(h4_bars) >= 4:
                    h4_df = pd.DataFrame(h4_bars)
                    for col in ["close", "open", "high", "low"]:
                        h4_df[col] = h4_df[col].astype(float)
                    last_4h = h4_df.iloc[-1]
                    prev_4h = h4_df.iloc[-2]
                    if last_4h["close"] > last_4h["open"] and last_4h["close"] >= prev_4h["close"]:
                        h4_status_str = "Confirmed Bullish Displacement"
                    elif last_4h["close"] > last_4h["open"]:
                        h4_status_str = "Emerging 4H Rebound"
                    else:
                        h4_status_str = "Consolidating inside POI"
            except Exception:
                pass

        # Strict Long-Only Regime Filter: Weekly must be in UPTREND and Daily not in DOWNTREND
        is_bullish = (weekly_regime == "UPTREND" and daily_regime != "DOWNTREND")

        if is_bullish:
            # Active Pro-Trend Swing Setup
            if last_close <= demand_zone_high * 1.03:
                setup_entry = round(last_close, 2)
            else:
                setup_entry = round(demand_zone_high, 2)

            setup_sl = round(demand_zone_low - (0.5 * last_atr), 2)
            if setup_sl >= setup_entry:
                setup_sl = round(setup_entry - (1.5 * last_atr), 2)
            risk = max(0.01, setup_entry - setup_sl)

            # Minimum 3:1 R:R target (Exit Step 5)
            structural_target = max(recent_15_high, setup_entry + (3.0 * risk))
            setup_tp = round(max(structural_target, setup_entry + (3.0 * risk)), 2)
            condition = f"1W: {weekly_status_str} | 1D Demand POI: ${demand_zone_low:.2f}–${demand_zone_high:.2f} | 4H: {h4_status_str}"
            rationale = (
                f"Multi-Timeframe Swing Strategy: Weekly trend is {weekly_status_str}. "
                f"Daily structure identified key Demand POI at ${demand_zone_low:.2f}–${demand_zone_high:.2f}. "
                f"Entry anchored at ${setup_entry:.2f} with structural SL below swing low at ${setup_sl:.2f}. "
                f"Take-Profit targeted at ${setup_tp:.2f} enforcing a minimum 3:1 R:R pro-trend target."
            )
        else:
            # Regime Filter: NO TRADE
            condition = f"REGIME FILTER: NO TRADE — 1W {weekly_status_str}, 1D {daily_status_str}"
            rationale = (
                f"Market structure rules strictly prohibit buying during downtrends or consolidation. "
                f"Current Weekly regime is {weekly_status_str} and Daily regime is {daily_status_str}. "
                f"Capital preserved. Awaiting structural Break of Structure (BOS) into Higher Highs and Higher Lows."
            )
            timeframe_status = {
                "weekly": weekly_status_str,
                "daily": f"Structure: {daily_status_str}",
                "execution_4h": h4_status_str,
            }
            return {
                "no_trade": True,
                "entry_price": None,
                "stop_loss_price": None,
                "take_profit_price": None,
                "risk_reward_ratio": "N/A",
                "potential_gain_pct": 0,
                "potential_risk_pct": 0,
                "condition": condition,
                "rationale": rationale,
                "timeframe_status": timeframe_status,
            }

        timeframe_status = {
            "weekly": weekly_status_str,
            "daily": f"Demand POI ${demand_zone_low:.2f}–${demand_zone_high:.2f}",
            "execution_4h": h4_status_str,
        }

    elif strategy == "liquidity_sweep":
        # Scan last 60 bars for the most recent qualified Liquidity Sweep + BOS pattern
        eq_window = 5
        tol = 0.0025
        setup_found = False
        setup_data = None

        for i in range(len(df) - 1, max(49, len(df) - 60), -1):
            recent_lows = df["low"].iloc[max(0, i - eq_window) : i]
            if len(recent_lows) < 3:
                continue
            low_min = float(recent_lows.min())
            low_max = float(recent_lows.max())
            has_eql = (low_max - low_min) / max(low_min, 0.01) < tol

            if not has_eql:
                continue

            candle = df.iloc[i]
            sweep_low = low_min
            if not (float(candle["low"]) < sweep_low and float(candle["close"]) > sweep_low):
                continue

            swing_high_5 = float(df["high"].iloc[max(0, i - 5) : i].max())
            bos_found = False
            bos_bar = -1
            for j in range(i + 1, min(i + 6, len(df))):
                if float(df.iloc[j]["close"]) > swing_high_5:
                    bos_found = True
                    bos_bar = j
                    break
            if not bos_found:
                continue

            # Check if this setup is still active/qualified today (within 12 bars, SL not hit, TP not hit)
            bars_since_bos = (len(df) - 1) - bos_bar
            if bars_since_bos > 12:
                # Setup is outdated / expired
                continue

            # Compute POI
            impulse_base_low = float(df["low"].iloc[i : bos_bar + 1].min())
            impulse_base_high = float(df["high"].iloc[i : bos_bar + 1].max())
            setup_entry = round(impulse_base_low + 0.382 * max(0.01, impulse_base_high - impulse_base_low), 2)
            sl_anchor = float(candle["low"])
            setup_sl = round(sl_anchor - last_atr * 0.5, 2)
            risk = max(0.01, setup_entry - setup_sl)
            opp_high = float(df["high"].iloc[max(0, i - eq_window) : i].max())
            setup_tp = round(max(opp_high, setup_entry + 3.0 * risk), 2)
            swept_level = round(sweep_low, 2)

            subsequent = df.iloc[bos_bar:]
            lowest_since = float(subsequent["low"].min())
            highest_since = float(subsequent["high"].max())

            if lowest_since <= setup_sl or highest_since >= setup_tp:
                # Already hit SL or TP -> no longer an active setup
                continue

            if setup_sl >= setup_entry:
                setup_sl = round(setup_entry - last_atr, 2)
            risk = max(0.01, setup_entry - setup_sl)
            if setup_tp <= setup_entry:
                setup_tp = round(setup_entry + (2.0 * risk), 2)
            rr_ratio = round((setup_tp - setup_entry) / risk, 1)

            condition = (
                f"Equal Lows swept at ${swept_level:.2f} → BOS above ${swing_high_5:.2f} confirmed. "
                f"Demand POI: ${impulse_base_low:.2f}–${impulse_base_high:.2f}."
            )
            rationale = (
                f"Liquidity Sweep: Retail sell-stops below equal lows (${swept_level:.2f}) were swept. "
                f"Lower-timeframe BOS above ${swing_high_5:.2f} confirms institutional reversal. "
                f"Entry limit at demand POI (${setup_entry:.2f}), SL below sweep wick (${setup_sl:.2f}), "
                f"TP at opposing liquidity pool (${setup_tp:.2f}) — min 3:1 R:R."
            )

            setup_data = {
                "no_trade": False,
                "entry_price": setup_entry,
                "stop_loss_price": setup_sl,
                "take_profit_price": setup_tp,
                "risk_reward_ratio": f"1:{rr_ratio:.1f}",
                "potential_gain_pct": round(((setup_tp - setup_entry) / setup_entry) * 100, 2),
                "potential_risk_pct": round(((setup_entry - setup_sl) / setup_entry) * 100, 2),
                "condition": condition,
                "rationale": rationale,
                "liquidity_price": swept_level,
                "liquidity_price_low": round(float(candle["low"]), 2),
                "liquidity_price_high": swept_level,
                "liquidity_type": "Swept Equal Lows",
                "liquidity_status": "Swept",
            }
            setup_found = True
            break

        if setup_found and setup_data:
            return setup_data
        else:
            # If no qualified setup, do not use a fallback setup — indicate "No Trade" and show liquidity to be swept
            pool_low, pool_high, unswept_type = _detect_unswept_liquidity(df)
            unswept_mid = round((pool_low + pool_high) / 2, 2)
            condition = f"NO TRADE — Awaiting Liquidity Sweep at ${pool_low:.2f}–${pool_high:.2f} ({unswept_type})"
            rationale = (
                f"Liquidity Sweep Framework: No qualified trade setup active. "
                f"Institutional order flow requires price to first sweep retail stop-loss liquidity "
                f"resting in the pool at ${pool_low:.2f}–${pool_high:.2f} ({unswept_type}) and confirm a Market Structure Shift (BOS) "
                f"before entering. Capital preserved while monitoring for sweep."
            )
            return {
                "no_trade": True,
                "entry_price": None,
                "stop_loss_price": None,
                "take_profit_price": None,
                "risk_reward_ratio": "N/A",
                "potential_gain_pct": 0,
                "potential_risk_pct": 0,
                "condition": condition,
                "rationale": rationale,
                "liquidity_price": unswept_mid,
                "liquidity_price_low": pool_low,
                "liquidity_price_high": pool_high,
                "liquidity_type": unswept_type,
                "liquidity_status": "Awaiting Sweep",
            }

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

    res = {
        "entry_price": setup_entry,
        "stop_loss_price": setup_sl,
        "take_profit_price": setup_tp,
        "risk_reward_ratio": f"1:{rr_ratio:.1f}",
        "potential_gain_pct": round(((setup_tp - setup_entry) / setup_entry) * 100, 2),
        "potential_risk_pct": round(((setup_entry - setup_sl) / setup_entry) * 100, 2),
        "condition": condition,
        "rationale": rationale,
    }
    if timeframe_status:
        res["timeframe_status"] = timeframe_status
    return res

def run_backtest(ticker: str, strategy: str = "ema_cross", lookback_days: int = 365) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"backtest:v6:{ticker}:{strategy}:{lookback_days}"
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

    elif strategy == "swing_structure":
        # Swing Structure: Detect trend regime (HH/HL) and buy pullbacks into demand zones
        for i in range(25, len(df)):
            sub_df = df.iloc[max(0, i - 40) : i + 1].reset_index(drop=True)
            regime, _ = _classify_market_structure(sub_df, window=2)
            curr_c = float(df.loc[i, "close"])
            curr_l = float(df.loc[i, "low"])
            curr_o = float(df.loc[i, "open"])

            if regime == "UPTREND":
                # Find demand POI (origin of recent expansion in 15 bars)
                low_15 = float(df["low"].iloc[max(0, i - 15) : i].min())
                high_15 = float(df["high"].iloc[max(0, i - 15) : i].max())
                demand_threshold = low_15 + (0.42 * max(0.01, high_15 - low_15))
                # Pullback into demand zone followed by bullish defense (close > open)
                if curr_l <= demand_threshold and curr_c > curr_o:
                    signals.iloc[i] = 1
            elif regime == "DOWNTREND":
                signals.iloc[i] = -1

    elif strategy == "liquidity_sweep":
        # Liquidity Sweep: Institutional stop-hunt framework
        # Phase 1 – Detect Equal Highs / Equal Lows liquidity pools
        # Phase 2 – Identify sweep candle (wick past level, body closes back inside)
        # Phase 3 – Confirm LTF Market Structure Shift (BOS) using 5-bar swing high break
        # Phase 4 – Entry at Demand/Supply POI (origin of BOS impulse candle)
        # Phase 5 – Target opposing liquidity pool at 3:1 R:R minimum
        eq_window = 5       # bars to look back for equal highs/lows matching
        tol = 0.0025        # 0.25% tolerance for "equal"

        for i in range(50, len(df)):
            # --- Pool Detection: Equal Lows (bullish sweep setup) ---
            recent_lows = df["low"].iloc[max(0, i - eq_window) : i]
            if len(recent_lows) < 3:
                continue
            low_min = float(recent_lows.min())
            low_max = float(recent_lows.max())
            has_eql = (low_max - low_min) / max(low_min, 0.01) < tol

            if not has_eql:
                continue

            # --- Phase 2: Sweep candle — wick below EQL, body closes back above ---
            candle = df.iloc[i]
            sweep_low = low_min
            swept_below = float(candle["low"]) < sweep_low
            body_above = float(candle["close"]) > sweep_low
            if not (swept_below and body_above):
                continue

            # --- Phase 3: BOS on next bar(s) — close above 5-bar swing high ---
            swing_high_5 = float(df["high"].iloc[max(0, i - 5) : i].max())
            bos_found = False
            bos_bar = -1
            for j in range(i + 1, min(i + 6, len(df))):
                if float(df.iloc[j]["close"]) > swing_high_5:
                    bos_found = True
                    bos_bar = j
                    break
            if not bos_found:
                continue

            # Only emit signal on bos_bar
            if bos_bar < len(signals):
                signals.iloc[bos_bar] = 1

    # Simulate trades with Risk/Reward management
    trades = []
    in_trade = False
    entry_price = 0.0
    entry_time = None
    stop_loss = 0.0
    take_profit = 0.0
    risk = 0.0
    breakeven_reached = False

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
                if strategy in ("swing_structure", "liquidity_sweep"):
                    recent_low = float(df["low"].iloc[max(0, i - 10) : i].min())
                    risk = max(curr_atr * 1.2, entry_price - recent_low)
                    stop_loss = round(entry_price - risk, 2)
                    take_profit = round(entry_price + (3.0 * risk), 2)
                    breakeven_reached = False
                else:
                    risk = 1.5 * curr_atr
                    stop_loss = round(entry_price - risk, 2)
                    take_profit = round(entry_price + (2.0 * risk), 2)
        else:
            # Trailing stop management for swing_structure / liquidity_sweep
            if strategy in ("swing_structure", "liquidity_sweep"):
                if not breakeven_reached and curr_high >= entry_price + (1.5 * risk):
                    stop_loss = max(stop_loss, entry_price)
                    breakeven_reached = True
                elif breakeven_reached:
                    local_low = float(df["low"].iloc[max(0, i - 5) : i].min())
                    if local_low > stop_loss and local_low < curr_price:
                        stop_loss = round(local_low, 2)

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
                    outcome = "WIN" if exit_price >= entry_price else "LOSS"
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
        "swing_structure": "Multi-Timeframe Swing Structure",
        "liquidity_sweep": "Liquidity Sweep (EQL/EQH Stop Hunt)",
    }
    strategy_display_name = strategy_display_names.get(strategy, strategy)
    setup_data = _compute_strategy_setup(strategy, df, ticker=ticker)

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
