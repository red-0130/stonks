import {
  StockInfo,
  ChartBar,
  StockRating,
  TechnicalData,
  ForecastData,
  BacktestResult,
  MarketSentiment,
  EarningsData
} from '../types/stock';

const API_BASE = '/api';

export async function fetchStockInfo(ticker: string): Promise<StockInfo> {
  const res = await fetch(`${API_BASE}/stock/${ticker}`);
  if (!res.ok) throw new Error(`Failed to load ticker: ${ticker}`);
  return res.json();
}

export async function fetchChartBars(ticker: string, timeframe: string = '1D'): Promise<ChartBar[]> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/chart?timeframe=${timeframe}`);
  if (!res.ok) throw new Error(`Failed to load chart bars`);
  const data = await res.json();
  return data.bars || [];
}

export async function fetchStockRating(ticker: string): Promise<StockRating> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/rating`);
  if (!res.ok) throw new Error(`Failed to load stock rating`);
  return res.json();
}

export async function fetchTechnicals(ticker: string): Promise<TechnicalData> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/technicals`);
  if (!res.ok) throw new Error(`Failed to load technical analysis`);
  return res.json();
}

export async function fetchForecast(ticker: string, days: number = 60): Promise<ForecastData> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/forecast?days=${days}`);
  if (!res.ok) throw new Error(`Failed to load price forecast`);
  return res.json();
}

export async function fetchBacktest(ticker: string, strategy: string = 'ema_cross'): Promise<BacktestResult> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/backtest?strategy=${strategy}`);
  if (!res.ok) throw new Error(`Failed to run backtest`);
  return res.json();
}

export async function fetchSentiment(ticker: string): Promise<MarketSentiment> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/sentiment`);
  if (!res.ok) throw new Error(`Failed to load sentiment`);
  return res.json();
}

export async function fetchEarnings(ticker: string): Promise<EarningsData> {
  const res = await fetch(`${API_BASE}/stock/${ticker}/earnings`);
  if (!res.ok) throw new Error(`Failed to load earnings history`);
  return res.json();
}
