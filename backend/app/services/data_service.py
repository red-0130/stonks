import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.cache import get_cached, set_cached

def get_ticker_info(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"info:{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info or {}

    # Extract price safely
    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
        or 0.0
    )
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose") or current_price
    change = current_price - prev_close if prev_close else 0.0
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    result = {
        "symbol": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "description": info.get("longBusinessSummary", ""),
        "currency": info.get("currency", "USD"),
        "current_price": round(float(current_price), 2),
        "previous_close": round(float(prev_close), 2),
        "change": round(float(change), 2),
        "change_percent": round(float(change_pct), 2),
        "market_cap": info.get("marketCap"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "dividend_yield": round(float(info.get("dividendYield") or 0.0) * 100, 2) if info.get("dividendYield") else 0.0,
        "pe_ratio": round(float(info.get("trailingPE")), 2) if info.get("trailingPE") else None,
        "forward_pe": round(float(info.get("forwardPE")), 2) if info.get("forwardPE") else None,
        "debt_to_equity": round(float(info.get("debtToEquity") or 0.0) / 100.0, 2) if info.get("debtToEquity") else None,
        "fifty_two_week_high": round(float(info.get("fiftyTwoWeekHigh") or 0.0), 2) if info.get("fiftyTwoWeekHigh") else None,
        "fifty_two_week_low": round(float(info.get("fiftyTwoWeekLow") or 0.0), 2) if info.get("fiftyTwoWeekLow") else None,
        "day_high": round(float(info.get("dayHigh") or 0.0), 2) if info.get("dayHigh") else None,
        "day_low": round(float(info.get("dayLow") or 0.0), 2) if info.get("dayLow") else None,
        "volume": info.get("regularMarketVolume") or info.get("volume"),
        "average_volume": info.get("averageVolume"),
    }

    set_cached(cache_key, result, ttl_seconds=300) # 5 min cache
    return result

def get_historical_bars(ticker: str, timeframe: str = "1D") -> List[Dict[str, Any]]:
    ticker = ticker.upper().strip()
    cache_key = f"bars:{ticker}:{timeframe}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    yf_ticker = yf.Ticker(ticker)

    # Timeframe mapping
    # 1W -> period='5y', interval='1wk'
    # 1D -> period='2y', interval='1d'
    # 4H -> period='730d', interval='1h' resampled to 4H
    # 1H -> period='730d', interval='1h'
    timeframe_upper = timeframe.upper()
    if timeframe_upper == "1W":
        df = yf_ticker.history(period="5y", interval="1wk")
    elif timeframe_upper == "4H":
        df_1h = yf_ticker.history(period="730d", interval="1h")
        if not df_1h.empty:
            df = df_1h.resample("4h").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum"
            }).dropna()
        else:
            df = df_1h
    elif timeframe_upper == "1H":
        df = yf_ticker.history(period="730d", interval="1h")
    else: # Default 1D
        df = yf_ticker.history(period="2y", interval="1d")

    bars = []
    if not df.empty:
        # Reset index to access datetime
        df = df.reset_index()
        date_col = "Date" if "Date" in df.columns else "Datetime"
        for _, row in df.iterrows():
            ts = row[date_col]
            if hasattr(ts, "timestamp"):
                time_val = int(ts.timestamp())
            else:
                time_val = str(ts)[:10]

            open_val = row.get("Open")
            high_val = row.get("High")
            low_val = row.get("Low")
            close_val = row.get("Close")
            volume_val = row.get("Volume", 0)

            if pd.isna(close_val):
                continue

            bars.append({
                "time": time_val,
                "open": round(float(open_val), 2),
                "high": round(float(high_val), 2),
                "low": round(float(low_val), 2),
                "close": round(float(close_val), 2),
                "volume": int(volume_val) if not pd.isna(volume_val) else 0,
            })

    ttl = 300 if timeframe_upper in ["1H", "4H"] else 900
    set_cached(cache_key, bars, ttl_seconds=ttl)
    return bars

def get_financial_statements(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"financials:{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    yf_ticker = yf.Ticker(ticker)

    income_stmt = yf_ticker.income_stmt
    balance_sheet = yf_ticker.balance_sheet
    cashflow = yf_ticker.cashflow

    def df_to_dict(df):
        if df is None or df.empty:
            return {}
        # Convert Timestamp columns to string
        res = {}
        for col in df.columns:
            date_str = str(col)[:10]
            res[date_str] = {idx: (None if pd.isna(val) else float(val)) for idx, val in df[col].items()}
        return res

    result = {
        "income_stmt": df_to_dict(income_stmt),
        "balance_sheet": df_to_dict(balance_sheet),
        "cashflow": df_to_dict(cashflow)
    }

    set_cached(cache_key, result, ttl_seconds=86400) # 24h
    return result
