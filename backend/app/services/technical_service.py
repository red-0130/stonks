import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.services.data_service import get_historical_bars
from app.cache import get_cached, set_cached

def calculate_technicals(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"technicals:{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    bars = get_historical_bars(ticker, timeframe="1D")
    if not bars or len(bars) < 30:
        return {}

    df = pd.DataFrame(bars)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)

    # 1. Moving Averages
    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()
    df["sma_200"] = df["close"].rolling(window=200).mean()

    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

    # 2. RSI (14)
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50.0)

    # 3. MACD (12, 26, 9)
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema_12 - ema_26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]

    # 4. Bollinger Bands (20, 2)
    rolling_mean_20 = df["close"].rolling(window=20).mean()
    rolling_std_20 = df["close"].rolling(window=20).std()
    df["bb_upper"] = rolling_mean_20 + (rolling_std_20 * 2)
    df["bb_lower"] = rolling_mean_20 - (rolling_std_20 * 2)
    df["bb_middle"] = rolling_mean_20

    # 5. ATR (14)
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=14).mean().fillna(tr)

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    curr_price = float(last["close"])

    # Pivot Points (Standard Daily)
    h = float(last["high"])
    l = float(last["low"])
    c = float(last["close"])
    pivot = (h + l + c) / 3.0
    r1 = (2 * pivot) - l
    s1 = (2 * pivot) - h
    r2 = pivot + (h - l)
    s2 = pivot - (h - l)

    # Evaluate indicator signals
    signals = []

    # RSI
    rsi_val = float(last["rsi"])
    if rsi_val < 30:
        signals.append({"name": "RSI (14)", "value": f"{rsi_val:.1f}", "signal": "BUY", "action": "Oversold"})
    elif rsi_val > 70:
        signals.append({"name": "RSI (14)", "value": f"{rsi_val:.1f}", "signal": "SELL", "action": "Overbought"})
    else:
        signals.append({"name": "RSI (14)", "value": f"{rsi_val:.1f}", "signal": "NEUTRAL", "action": "Neutral"})

    # MACD
    macd_val = float(last["macd_line"])
    macd_sig = float(last["macd_signal"])
    macd_hist = float(last["macd_hist"])
    if macd_val > macd_sig and macd_hist > 0:
        signals.append({"name": "MACD (12,26,9)", "value": f"{macd_val:.2f}", "signal": "BUY", "action": "Bullish Crossover"})
    elif macd_val < macd_sig and macd_hist < 0:
        signals.append({"name": "MACD (12,26,9)", "value": f"{macd_val:.2f}", "signal": "SELL", "action": "Bearish Crossover"})
    else:
        signals.append({"name": "MACD (12,26,9)", "value": f"{macd_val:.2f}", "signal": "NEUTRAL", "action": "Consolidating"})

    # Moving Average 20
    sma20 = float(last["sma_20"]) if pd.notna(last["sma_20"]) else None
    if sma20:
        sig = "BUY" if curr_price > sma20 else "SELL"
        signals.append({"name": "SMA (20)", "value": f"${sma20:.2f}", "signal": sig, "action": f"Price {'above' if sig == 'BUY' else 'below'} SMA 20"})

    # Moving Average 50
    sma50 = float(last["sma_50"]) if pd.notna(last["sma_50"]) else None
    if sma50:
        sig = "BUY" if curr_price > sma50 else "SELL"
        signals.append({"name": "SMA (50)", "value": f"${sma50:.2f}", "signal": sig, "action": f"Price {'above' if sig == 'BUY' else 'below'} SMA 50"})

    # Moving Average 200
    sma200 = float(last["sma_200"]) if pd.notna(last["sma_200"]) else None
    if sma200:
        sig = "BUY" if curr_price > sma200 else "SELL"
        signals.append({"name": "SMA (200)", "value": f"${sma200:.2f}", "signal": sig, "action": f"Long-term {'Bullish' if sig == 'BUY' else 'Bearish'}"})

    # Bollinger Bands
    bbu = float(last["bb_upper"]) if pd.notna(last["bb_upper"]) else None
    bbl = float(last["bb_lower"]) if pd.notna(last["bb_lower"]) else None
    if bbu and bbl:
        if curr_price >= bbu:
            signals.append({"name": "Bollinger Bands", "value": f"${bbu:.2f}", "signal": "SELL", "action": "Upper band touch (Overextended)"})
        elif curr_price <= bbl:
            signals.append({"name": "Bollinger Bands", "value": f"${bbl:.2f}", "signal": "BUY", "action": "Lower band touch (Oversold bounce)"})
        else:
            signals.append({"name": "Bollinger Bands", "value": "Within Bands", "signal": "NEUTRAL", "action": "Normal volatility"})

    buy_count = sum(1 for s in signals if s["signal"] == "BUY")
    sell_count = sum(1 for s in signals if s["signal"] == "SELL")
    neutral_count = sum(1 for s in signals if s["signal"] == "NEUTRAL")

    if buy_count >= sell_count + 3:
        summary_label = "Strong Buy"
        summary_color = "emerald"
    elif buy_count > sell_count:
        summary_label = "Buy"
        summary_color = "teal"
    elif sell_count >= buy_count + 3:
        summary_label = "Strong Sell"
        summary_color = "rose"
    elif sell_count > buy_count:
        summary_label = "Sell"
        summary_color = "orange"
    else:
        summary_label = "Neutral"
        summary_color = "amber"

    result = {
        "symbol": ticker,
        "current_price": round(curr_price, 2),
        "summary": {
            "label": summary_label,
            "color": summary_color,
            "buy": buy_count,
            "sell": sell_count,
            "neutral": neutral_count
        },
        "indicators": {
            "rsi_14": round(rsi_val, 2),
            "macd": round(macd_val, 2),
            "macd_signal": round(macd_sig, 2),
            "macd_hist": round(macd_hist, 2),
            "sma_20": round(sma20, 2) if sma20 else None,
            "sma_50": round(sma50, 2) if sma50 else None,
            "sma_200": round(sma200, 2) if sma200 else None,
            "ema_20": round(float(last["ema_20"]), 2),
            "ema_50": round(float(last["ema_50"]), 2),
            "bb_upper": round(bbu, 2) if bbu else None,
            "bb_middle": round(float(last["bb_middle"]), 2) if pd.notna(last["bb_middle"]) else None,
            "bb_lower": round(bbl, 2) if bbl else None,
            "atr_14": round(float(last["atr"]), 2)
        },
        "pivot_points": {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
        },
        "signals": signals
    }

    set_cached(cache_key, result, ttl_seconds=600)
    return result
