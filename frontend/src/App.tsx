import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { TickerSummary } from './components/TickerSummary';
import { PriceChart } from './components/PriceChart';
import { StockRatingCard } from './components/StockRatingCard';
import { TechnicalSummary } from './components/TechnicalSummary';
import { ForecastChart } from './components/ForecastChart';
import { BacktestStudio } from './components/BacktestStudio';
import { SentimentSection } from './components/SentimentSection';
import { EarningsSection } from './components/EarningsSection';
import {
  TickerSummarySkeleton,
  StockRatingSkeleton,
  TechnicalSummarySkeleton,
  ForecastSkeleton,
  SentimentSkeleton,
  EarningsSkeleton,
} from './components/skeletons';
import {
  fetchStockInfo,
  fetchChartBars,
  fetchStockRating,
  fetchTechnicals,
  fetchForecast,
  fetchBacktest,
  fetchSentiment,
  fetchEarnings,
} from './services/api';
import {
  StockInfo,
  ChartBar,
  StockRating,
  TechnicalData,
  ForecastData,
  BacktestResult,
  TradeSetup,
  MarketSentiment,
  EarningsData,
} from './types/stock';
import {
  BarChart2,
  Award,
  Sparkles,
  Crosshair,
  MessageSquare,
  DollarSign,
  AlertTriangle,
} from 'lucide-react';

const STRATEGIES = [
  {
    id: 'swing_structure',
    name: 'Multi-Timeframe Swing Structure',
    description: 'Top-down trend analysis (1W trend -> 1D POI / demand zones -> 4H confirmation) aiming for minimum 3:1 Risk/Reward.',
  },
  {
    id: 'liquidity_sweep',
    name: 'Liquidity Sweep (EQL/EQH Stop Hunt)',
    description:
      'Institutional stop-hunt framework: maps equal-highs/lows liquidity pools, confirms a sweep wick + LTF Market Structure Shift (BOS), then enters at the Demand/Supply POI. Targets 3:1–5:1 R:R.',
  },
  {
    id: 'smc_fvg_ob',
    name: 'Smart Money Concepts (SMC)',
    description: 'Fair Value Gap (FVG) liquidity imbalances & institutional Order Block demand retests.',
  },
  {
    id: 'ema_cross',
    name: 'EMA 20 / 50 Trend Cross',
    description: 'Classic trend continuation when fast EMA crosses above slow EMA.',
  },
  {
    id: 'rsi_reversal',
    name: 'RSI Mean Reversion (30/70)',
    description: 'Oversold bounce trigger with dynamic risk management.',
  },
  {
    id: 'macd_cross',
    name: 'MACD Signal Crossover',
    description: 'Momentum shift trigger with MACD line crossing over signal.',
  },
  {
    id: 'bollinger_breakout',
    name: 'Bollinger Bands Breakout',
    description: 'Volatility expansion and mean-reverting lower band re-entry.',
  },
];

export const App: React.FC = () => {
  const [ticker, setTicker] = useState<string>('AAPL');
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [activeTab, setActiveTab] = useState<'chart' | 'rating' | 'forecast' | 'backtest' | 'sentiment' | 'earnings'>('chart');

  // Data states
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [chartBars, setChartBars] = useState<ChartBar[]>([]);
  const [rating, setRating] = useState<StockRating | null>(null);
  const [technicals, setTechnicals] = useState<TechnicalData | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [forecastDays, setForecastDays] = useState<number>(60);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('smc_fvg_ob');
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [activeChartSetup, setActiveChartSetup] = useState<TradeSetup | null>(null);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [earnings, setEarnings] = useState<EarningsData | null>(null);

  // Loading states
  const [isLoadingMain, setIsLoadingMain] = useState<boolean>(true);
  const [isLoadingChart, setIsLoadingChart] = useState<boolean>(false);
  const [isLoadingForecast, setIsLoadingForecast] = useState<boolean>(false);
  const [isLoadingBacktest, setIsLoadingBacktest] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load all initial stock data
  const loadStockData = async (symbol: string) => {
    setIsLoadingMain(true);
    setErrorMsg(null);
    try {
      // Fire chart, backtest, and forecast concurrently for speed
      loadBars(symbol, timeframe);
      loadBacktest(symbol, selectedStrategy);
      loadForecastData(symbol, forecastDays);

      // Parallel fetch for core metadata
      const [infoRes, ratingRes, techRes, sentRes, earnRes] = await Promise.all([
        fetchStockInfo(symbol),
        fetchStockRating(symbol),
        fetchTechnicals(symbol),
        fetchSentiment(symbol),
        fetchEarnings(symbol),
      ]);

      setStockInfo(infoRes);
      setRating(ratingRes);
      setTechnicals(techRes);
      setSentiment(sentRes);
      setEarnings(earnRes);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Error fetching stock data');
    } finally {
      setIsLoadingMain(false);
    }
  };

  const loadBars = async (symbol: string, tf: string) => {
    setIsLoadingChart(true);
    try {
      const bars = await fetchChartBars(symbol, tf);
      setChartBars(bars);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingChart(false);
    }
  };

  const loadForecastData = async (symbol: string, days: number) => {
    setIsLoadingForecast(true);
    try {
      const data = await fetchForecast(symbol, days);
      setForecast(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingForecast(false);
    }
  };

  const loadBacktest = async (symbol: string, strat: string): Promise<BacktestResult | null> => {
    setIsLoadingBacktest(true);
    try {
      const data = await fetchBacktest(symbol, strat);
      setBacktestResult(data);
      return data;
    } catch (err) {
      console.error(err);
      return null;
    } finally {
      setIsLoadingBacktest(false);
    }
  };

  const handleSetStrategy = async () => {
    const data = await loadBacktest(ticker, selectedStrategy);
    if (data?.setup) {
      if (!data.setup.no_trade && data.setup.entry_price !== null) {
        setActiveChartSetup(data.setup);
        setActiveTab('chart');
      } else if (data.setup.liquidity_price) {
        setActiveChartSetup(data.setup);
        setActiveTab('chart');
      }
    }
  };

  useEffect(() => {
    loadStockData(ticker);
  }, [ticker]);

  const handleSelectTicker = (newTicker: string) => {
    if (newTicker !== ticker) {
      setActiveChartSetup(null);
      setTicker(newTicker);
      // Reset states so skeletons display immediately for new ticker
      setStockInfo(null);
      setChartBars([]);
      setRating(null);
      setTechnicals(null);
      setForecast(null);
      setBacktestResult(null);
      setSentiment(null);
      setEarnings(null);
    }
  };

  const handleSelectTimeframe = (newTf: string) => {
    setTimeframe(newTf);
    loadBars(ticker, newTf);
  };

  const handleChangeDaysAhead = (days: number) => {
    setForecastDays(days);
    loadForecastData(ticker, days);
  };

  const handleSelectStrategy = (strat: string) => {
    setSelectedStrategy(strat);
    loadBacktest(ticker, strat);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header
        currentTicker={ticker}
        onSelectTicker={handleSelectTicker}
        isLoading={isLoadingMain}
        onRefresh={() => loadStockData(ticker)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Error Notification */}
        {errorMsg && (
          <div className="p-4 bg-rose-950/40 border border-rose-500/50 rounded-xl text-rose-300 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-sm font-medium">{errorMsg}</span>
          </div>
        )}

        {/* Company Overview & Ticker Summary */}
        {stockInfo ? (
          <TickerSummary info={stockInfo} />
        ) : isLoadingMain ? (
          <TickerSummarySkeleton />
        ) : null}

        {/* Navigation Tabs Bar */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3 overflow-x-auto text-xs sm:text-sm font-semibold">
          <button
            onClick={() => setActiveTab('chart')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'chart'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            <span>Interactive Chart</span>
          </button>

          <button
            onClick={() => setActiveTab('rating')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'rating'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Award className="w-4 h-4" />
            <span>7-Factor Rating</span>
            {rating ? (
              <span className="px-1.5 py-0.2 bg-emerald-950 text-emerald-300 rounded text-[11px] font-mono">
                {rating.grade} ({rating.score}/7)
              </span>
            ) : isLoadingMain ? (
              <span className="inline-block w-12 h-4 bg-slate-800 rounded animate-pulse" />
            ) : null}
          </button>

          <button
            onClick={() => setActiveTab('forecast')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'forecast'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Forecast & Technicals</span>
          </button>

          <button
            onClick={() => setActiveTab('backtest')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'backtest'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Crosshair className="w-4 h-4" />
            <span>Backtest Studio & Setup</span>
            {backtestResult ? (
              <span className="px-1.5 py-0.2 bg-slate-800 text-slate-300 rounded text-[11px] font-mono">
                {backtestResult.success_rate}% Win
              </span>
            ) : isLoadingBacktest || isLoadingMain ? (
              <span className="inline-block w-14 h-4 bg-slate-800 rounded animate-pulse" />
            ) : null}
          </button>

          <button
            onClick={() => setActiveTab('sentiment')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'sentiment'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Market Sentiment</span>
          </button>

          <button
            onClick={() => setActiveTab('earnings')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              activeTab === 'earnings'
                ? 'bg-emerald-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <DollarSign className="w-4 h-4" />
            <span>Historical Earnings</span>
          </button>
        </div>

        {/* Tab Content Display */}
        <div>
          {/* TAB 1: INTERACTIVE CHART */}
          {activeTab === 'chart' && (
            <div className="space-y-6">
              <PriceChart
                bars={chartBars}
                symbol={ticker}
                currentTimeframe={timeframe}
                onSelectTimeframe={handleSelectTimeframe}
                activeSetup={activeChartSetup}
                onClearSetup={() => setActiveChartSetup(null)}
                isLoading={isLoadingChart}
              />

              {/* Quick glance at 7-factor and technical gauge */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {rating ? (
                  <StockRatingCard rating={rating} />
                ) : isLoadingMain ? (
                  <StockRatingSkeleton />
                ) : null}
                {technicals ? (
                  <TechnicalSummary technicals={technicals} />
                ) : isLoadingMain ? (
                  <TechnicalSummarySkeleton />
                ) : null}
              </div>
            </div>
          )}

          {/* TAB 2: 7-FACTOR RATING */}
          {activeTab === 'rating' && (
            <div className="space-y-6">
              {rating ? (
                <StockRatingCard rating={rating} />
              ) : isLoadingMain ? (
                <StockRatingSkeleton />
              ) : (
                <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-400 text-xs">
                  Rating data is unavailable for {ticker}.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: FORECAST & TECHNICALS */}
          {activeTab === 'forecast' && (
            <div className="space-y-6">
              {forecast ? (
                <ForecastChart
                  forecastData={forecast}
                  daysAhead={forecastDays}
                  onChangeDaysAhead={handleChangeDaysAhead}
                  isLoading={isLoadingForecast}
                />
              ) : (
                <ForecastSkeleton />
              )}
              {technicals ? (
                <TechnicalSummary technicals={technicals} />
              ) : isLoadingMain ? (
                <TechnicalSummarySkeleton />
              ) : null}
            </div>
          )}

          {/* TAB 4: BACKTEST STUDIO */}
          {activeTab === 'backtest' && (
            <div className="space-y-6">
              <BacktestStudio
                strategies={STRATEGIES}
                selectedStrategy={selectedStrategy}
                onSelectStrategy={handleSelectStrategy}
                backtestResult={backtestResult}
                onSetStrategy={handleSetStrategy}
                isLoading={isLoadingBacktest}
              />
            </div>
          )}

          {/* TAB 5: SENTIMENT & NEWS */}
          {activeTab === 'sentiment' && (
            <div className="space-y-6">
              {sentiment ? (
                <SentimentSection sentiment={sentiment} />
              ) : (
                <SentimentSkeleton />
              )}
            </div>
          )}

          {/* TAB 6: HISTORICAL EARNINGS */}
          {activeTab === 'earnings' && (
            <div className="space-y-6">
              {earnings ? (
                <EarningsSection earnings={earnings} />
              ) : (
                <EarningsSkeleton />
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-400 mt-auto">
        <div className="max-w-7xl mx-auto px-4">
          <p>© 2026 Stonks v2 — Algorithmic Market Analytics & Smart Money Quantitative Models.</p>
          <p className="mt-1 text-slate-400">
            Data provided by Yahoo Finance engine with local SQLite TTL caching. For educational & analytical purposes.
          </p>
        </div>
      </footer>
    </div>
  );
};
