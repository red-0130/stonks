from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.data_service import get_ticker_info, get_historical_bars
from app.services.rating_service import calculate_stock_rating
from app.services.technical_service import calculate_technicals
from app.services.forecast_service import generate_price_forecast
from app.services.backtest_service import run_backtest
from app.services.sentiment_service import get_market_sentiment
from app.services.earnings_service import get_earnings_history

router = APIRouter(prefix="/api")

@router.get("/health")
def health_check():
    return {"status": "ok", "app": "Stonks v2 API"}

@router.get("/stock/{ticker}")
def get_stock(ticker: str):
    try:
        info = get_ticker_info(ticker)
        if not info or not info.get("symbol"):
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/chart")
def get_chart(ticker: str, timeframe: str = Query("1D", pattern="^(1W|1D|4H|1H)$")):
    try:
        bars = get_historical_bars(ticker, timeframe=timeframe)
        return {"symbol": ticker.upper(), "timeframe": timeframe, "bars": bars}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/rating")
def get_rating(ticker: str):
    try:
        return calculate_stock_rating(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/technicals")
def get_technicals(ticker: str):
    try:
        data = calculate_technicals(ticker)
        if not data:
            raise HTTPException(status_code=404, detail=f"No technical data for '{ticker}'")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/forecast")
def get_forecast(ticker: str, days: Optional[int] = Query(365)):
    try:
        data = generate_price_forecast(ticker, days_ahead=days or 365)
        if not data:
            raise HTTPException(status_code=404, detail=f"Could not compute consensus forecast for '{ticker}'")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/backtest")
def get_backtest(
    ticker: str,
    strategy: str = Query("ema_cross", pattern="^(ema_cross|rsi_reversal|macd_cross|bollinger_breakout|smc_fvg_ob)$"),
    lookback_days: int = Query(365, ge=60, le=1825)
):
    try:
        data = run_backtest(ticker, strategy=strategy, lookback_days=lookback_days)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/sentiment")
def get_sentiment(ticker: str):
    try:
        return get_market_sentiment(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{ticker}/earnings")
def get_earnings(ticker: str):
    try:
        return get_earnings_history(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
