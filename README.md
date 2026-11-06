# Stonks v2 — Stock Analysis & Quantitative Trading Web App

A modern, high-performance financial intelligence web application built with **Bun**, **FastAPI**, **React**, and **TradingView Lightweight Charts**.

---

## 🌟 Key Features

1. **Ticker Search & Real-Time Price**: Instant search by ticker symbol with pre-configured popular stocks (`AAPL`, `NVDA`, `MSFT`, `TSLA`, `AMZN`, `GOOGL`, `META`, `SPY`).
2. **Key Financial Metrics**: Real-time price, day change, Market Cap, Shares Outstanding, Dividend Yield, P/E Ratio, and 52-Week Range.
3. **7-Factor Institutional Stock Rating**:
   - P/E Ratio (`< 20`)
   - ROIC (`> 15%`)
   - Debt/Equity Ratio (`< 1.0`)
   - EPS CAGR (`> 10%`)
   - ROE (`> 15%`)
   - EBIT Margin (`> 10%`)
   - Gross Margin (`> 40%`)
   - Visual checklist showing actual vs threshold values, pass/fail status, and tiered institutional grades (**A/B/C/D**).
4. **Interactable Price Chart (TradingView)**:
   - Timeframes: **1W**, **1D**, **4H**, **1H**.
   - Candlestick & Line views with volume histogram sub-chart.
   - Interactive panning, crosshairs, and setup price-line overlays.
5. **Technical Analysis Engine**:
   - RSI (14), MACD (12, 26, 9), Moving Averages (SMA 20, 50, 200; EMA 20, 50), Bollinger Bands, ATR (14), and Pivot Points (R1, R2, S1, S2, Pivot).
   - Composite Bullish / Bearish / Neutral consensus meter.
6. **Price Forecast Graph**:
   - Statistical ARIMA / Holt-Winters Exponential Smoothing projection.
   - 30, 60, and 90-day forecast horizons with **80% and 95% confidence interval uncertainty cones**.
7. **Algorithmic Strategy Backtesting Studio**:
   - **Smart Money Concepts (SMC)**: Fair Value Gap (FVG) imbalances & Order Block demand retests.
   - **EMA 20/50 Trend Cross**
   - **RSI Mean Reversion (30/70 bounce)**
   - **MACD Signal Crossover**
   - **Bollinger Bands Breakout**
   - Displays: **Win Rate (%)**, **Successful vs Total Trades Tested**, **Profit Factor**, **Total Return (%)**, and **Actionable Trade Setup** (**Entry Price**, **Stop-Loss Price**, **Take-Profit Price** with 1:2 Risk/Reward).
8. **Market Sentiment & News NLP**:
   - VADER sentiment scoring on live news headlines (-100 to +100 index).
   - Wall Street analyst consensus breakdown (Recommendation, Analyst Count, Target Price).
9. **Historical Earnings & Estimates**:
   - Interactive quarterly EPS actual vs estimated bar chart with beat/miss surprise % badges.
   - Upcoming earnings announcement schedule and consensus estimates.
10. **High-Performance Caching**:
    - Embedded SQLite + in-memory TTL caching (5-15 min quotes, 24h fundamentals).

---

## 🚀 Running the Application

### Option A: Unified Startup
Run the unified startup script:
```bash
./start.sh
```

### Option B: Run Services Separately

**1. Backend (Python FastAPI with `uv`):**
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**2. Frontend (React with `bun`):**
```bash
cd frontend
bun run dev --host 0.0.0.0 --port 5173
```

- **Frontend URL**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000` (API Docs at `http://localhost:8000/docs`)

---

## 🐳 Container Deployment

The application includes a production-ready, multi-stage `Dockerfile` and `docker-compose.yml` that bundles the compiled React frontend and FastAPI backend into a single self-contained container.

### Using Docker Compose (Recommended)

To build and run the unified container:
```bash
docker compose up --build -d
```
- **Application URL**: `http://localhost:8000`
- **API Health**: `http://localhost:8000/api/health`
- **API Docs**: `http://localhost:8000/docs`

To stop the container:
```bash
docker compose down
```

### Using Docker Directly

1. **Build the container image**:
```bash
docker build -t stonks-app .
```

2. **Run the container**:
```bash
docker run -d -p 8000:8000 --name stonks stonks-app
```

3. **Cloud Deployments (Cloud Run, ECS, Fly.io, K8s)**:
The container automatically binds to the `$PORT` environment variable (defaults to `8000`) and runs as an unprivileged user (`appuser`, UID `10001`):
```bash
docker run -d -e PORT=8080 -p 8080:8080 stonks-app
```

---

## 📦 GitHub Container Registry (GHCR)

The repository includes a GitHub Actions CI/CD workflow ([`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml)) that automatically builds and publishes the production image to **ghcr.io** on every push to the `main` branch.

### Pulling and Running the Pre-Built Image

```bash
# Pull the latest image from GHCR
docker pull ghcr.io/red-0130/stonks:latest

# Run the container
docker run -d -p 8000:8000 --name stonks ghcr.io/red-0130/stonks:latest
```
