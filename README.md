# 📈 Stonks — Stock Analysis Dashboard

A comprehensive stock analysis app built with Streamlit that provides fundamental ratings, market sentiment, technical analysis, and trade strategies.

## Features

- **Stock Lookup** — Enter any ticker symbol to get instant analysis
- **Current Price** — Live price with change percentage, market cap, and 52-week range
- **Fundamental Rating** — Grades stocks on 7 quality criteria:
  - P/E Ratio < 20
  - ROIC > 15%
  - Debt/Equity < 1
  - EPS CAGR > 10%
  - ROE > 15%
  - EBIT Margin > 10%
  - Gross Margin > 40%
- **Market Sentiment** — Analyses price momentum, volume trends, moving averages, analyst consensus, and 52-week positioning
- **Technical Analysis** — RSI, MACD, Bollinger Bands, and MA crossover signals with interactive Plotly charts
- **Swing Trade Strategy** — Top-down multi-timeframe structure (Weekly/Daily), supply/demand POIs, impulses vs corrections, trailing stop rules, and minimum 3:1 R:R
- **Smart Money Concepts (SMC)** — Institutional footprints including Order Blocks (OB), Fair Value Gaps (FVG), Market Structure Shifts (BOS & CHoCH), Liquidity Pools (BSL/SSL), and mitigation entries
- **Trade Strategies** — Momentum, mean reversion, RSI reversal, breakout, swing trade, and SMC setups with entry/exit prices, risk/reward ratios, and back-tested success percentages

## Quick Start

```bash
# Install dependencies
uv sync

# Launch the dashboard
uv run stonks
```

The app will open in your browser at `http://localhost:8501`.

## Docker Deployment

### Using Docker

```bash
# Build the container image locally
docker build -t stonks:latest .

# Run the container
docker run -d --name stonks-dashboard -p 8501:8501 stonks:latest
```

Or run the image directly from GitHub Container Registry (after CI publishes):

```bash
docker run -d --name stonks-dashboard -p 8501:8501 ghcr.io/<owner>/stonks:latest
```

### Using Docker Compose

```bash
docker compose up -d --build
```

Access the dashboard at `http://localhost:8501`.

## Tech Stack

- **[Streamlit](https://streamlit.io/)** — Interactive web UI
- **[yfinance](https://github.com/ranaroussi/yfinance)** — Yahoo Finance market data
- **[Plotly](https://plotly.com/)** — Interactive charts
- **[ta](https://github.com/bukosabino/ta)** — Technical analysis indicators
- **[Pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/)** — Data processing

## Disclaimer

This tool is for **educational purposes only**. It is not financial advice. Always do your own research before making investment decisions.

