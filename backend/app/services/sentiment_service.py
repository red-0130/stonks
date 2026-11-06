import yfinance as yf
from datetime import datetime
from typing import Dict, Any, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.cache import get_cached, set_cached

analyzer = SentimentIntensityAnalyzer()

def get_market_sentiment(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper().strip()
    cache_key = f"sentiment:{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info or {}

    # 1. Analyst Recommendations & Price Targets
    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    target_median = info.get("targetMedianPrice")
    curr_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0

    upside_pct = None
    if target_mean and curr_price:
        upside_pct = round(((target_mean - curr_price) / curr_price) * 100, 2)

    rec_key = info.get("recommendationKey", "none").replace("_", " ").title()
    number_of_analysts = info.get("numberOfAnalystOpinions", 0)

    # 2. News sentiment with VADER
    news_items = []
    try:
        raw_news = yf_ticker.news or []
    except Exception:
        raw_news = []

    compound_scores = []
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0

    for item in raw_news[:15]:
        title = item.get("title", "")
        summary = item.get("summary") or item.get("description") or ""
        text_to_score = f"{title}. {summary}"

        vs = analyzer.polarity_scores(text_to_score)
        compound = vs["compound"]
        compound_scores.append(compound)

        if compound >= 0.15:
            sentiment_tag = "Bullish"
            tag_color = "emerald"
            bullish_count += 1
        elif compound <= -0.15:
            sentiment_tag = "Bearish"
            tag_color = "rose"
            bearish_count += 1
        else:
            sentiment_tag = "Neutral"
            tag_color = "slate"
            neutral_count += 1

        pub_time = item.get("providerPublishTime")
        if pub_time:
            time_str = datetime.utcfromtimestamp(pub_time).strftime("%b %d, %Y %H:%M")
        else:
            time_str = "Recent"

        news_items.append({
            "title": title,
            "publisher": item.get("publisher", "Financial News"),
            "link": item.get("link", "#"),
            "published": time_str,
            "sentiment": sentiment_tag,
            "color": tag_color,
            "score": round(compound, 2)
        })

    if compound_scores:
        avg_score = sum(compound_scores) / len(compound_scores)
        scaled_score = round(avg_score * 100, 1) # -100 to +100
    else:
        scaled_score = 15.0 # default mild positive if no news
        bullish_count = 1

    if scaled_score >= 20:
        overall_sentiment = "Strongly Bullish"
        overall_color = "emerald"
    elif scaled_score >= 5:
        overall_sentiment = "Mildly Bullish"
        overall_color = "teal"
    elif scaled_score <= -20:
        overall_sentiment = "Strongly Bearish"
        overall_color = "rose"
    elif scaled_score <= -5:
        overall_sentiment = "Mildly Bearish"
        overall_color = "orange"
    else:
        overall_sentiment = "Neutral"
        overall_color = "amber"

    result = {
        "symbol": ticker,
        "sentiment_score": scaled_score, # -100 to +100
        "overall_sentiment": overall_sentiment,
        "color": overall_color,
        "counts": {
            "bullish": bullish_count,
            "neutral": neutral_count,
            "bearish": bearish_count,
            "total_articles": len(news_items)
        },
        "analyst_consensus": {
            "recommendation": rec_key,
            "analyst_count": number_of_analysts,
            "target_mean": round(target_mean, 2) if target_mean else None,
            "target_high": round(target_high, 2) if target_high else None,
            "target_low": round(target_low, 2) if target_low else None,
            "target_median": round(target_median, 2) if target_median else None,
            "implied_upside_percent": upside_pct
        },
        "news": news_items
    }

    set_cached(cache_key, result, ttl_seconds=900) # 15 min cache
    return result
