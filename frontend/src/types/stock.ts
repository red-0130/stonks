export interface StockInfo {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  description: string;
  currency: string;
  current_price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  market_cap?: number;
  shares_outstanding?: number;
  dividend_yield?: number;
  pe_ratio?: number | null;
  forward_pe?: number | null;
  debt_to_equity?: number | null;
  fifty_two_week_high?: number | null;
  fifty_two_week_low?: number | null;
  day_high?: number | null;
  day_low?: number | null;
  volume?: number | null;
  average_volume?: number | null;
}

export interface ChartBar {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RatingChecklistItem {
  id: string;
  name: string;
  condition: string;
  threshold: number;
  operator: string;
  actual_value: number | null;
  display_value: string;
  passed: boolean;
  description: string;
}

export interface StockRating {
  symbol: string;
  score: number;
  total: number;
  percentage: number;
  grade: string;
  label: string;
  color: string;
  checklist: RatingChecklistItem[];
}

export interface TechnicalSignal {
  name: string;
  value: string;
  signal: 'BUY' | 'SELL' | 'NEUTRAL';
  action: string;
}

export interface TechnicalData {
  symbol: string;
  current_price: number;
  summary: {
    label: string;
    color: string;
    buy: number;
    sell: number;
    neutral: number;
  };
  indicators: {
    rsi_14: number;
    macd: number;
    macd_signal: number;
    macd_hist: number;
    sma_20: number | null;
    sma_50: number | null;
    sma_200: number | null;
    ema_20: number;
    ema_50: number;
    bb_upper: number | null;
    bb_middle: number | null;
    bb_lower: number | null;
    atr_14: number;
  };
  pivot_points: {
    pivot: number;
    r1: number;
    r2: number;
    s1: number;
    s2: number;
  };
  signals: TechnicalSignal[];
}

export interface ConsensusMilestone {
  period: string;
  month: number;
  date: string;
  target_mean: number;
  target_high: number;
  target_low: number;
  implied_change_percent: number;
}

export interface RatingsBreakdown {
  strong_buy: number;
  buy: number;
  hold: number;
  sell: number;
  strong_sell: number;
  total: number;
}

export interface ForecastTrajectoryPoint {
  month: number;
  date: string;
  mean: number;
  median: number;
  high: number;
  low: number;
}

export interface ForecastData {
  symbol: string;
  current_price: number;
  target_mean: number;
  target_median: number;
  target_high: number;
  target_low: number;
  implied_upside_percent: number;
  high_upside_percent: number;
  low_downside_percent: number;
  analyst_count: number;
  consensus_score: number;
  consensus_label: string;
  recommendation_key: string;
  ratings: RatingsBreakdown;
  milestones: ConsensusMilestone[];
  historical: { date: string; price: number }[];
  trajectories: ForecastTrajectoryPoint[];
  provider: string;
}

export interface TradeSetup {
  entry_price: number | null;
  stop_loss_price: number | null;
  take_profit_price: number | null;
  risk_reward_ratio: string;
  potential_gain_pct: number;
  potential_risk_pct: number;
  condition: string;
  rationale: string;
  no_trade?: boolean;
  timeframe_status?: {
    weekly: string;
    daily: string;
    execution_4h: string;
  };
}

export interface BacktestTrade {
  entry_time: number | string;
  exit_time: number | string;
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  take_profit: number;
  outcome: 'WIN' | 'LOSS';
  pnl: number;
  pnl_percent: number;
}

export interface BacktestResult {
  symbol: string;
  strategy: string;
  strategy_name: string;
  total_trades: number;
  successful_trades: number;
  losing_trades: number;
  success_rate: number;
  profit_factor: number;
  total_return_percent: number;
  setup: TradeSetup | null;
  recent_trades: BacktestTrade[];
}

export interface NewsArticle {
  title: string;
  publisher: string;
  link: string;
  published: string;
  sentiment: 'Bullish' | 'Bearish' | 'Neutral';
  color: string;
  score: number;
}

export interface MarketSentiment {
  symbol: string;
  sentiment_score: number;
  overall_sentiment: string;
  color: string;
  counts: {
    bullish: number;
    neutral: number;
    bearish: number;
    total_articles: number;
  };
  analyst_consensus: {
    recommendation: string;
    analyst_count: number;
    target_mean: number | null;
    target_high: number | null;
    target_low: number | null;
    target_median: number | null;
    implied_upside_percent: number | null;
  };
  news: NewsArticle[];
}

export interface EarningsQuarter {
  quarter: string;
  eps_actual: number | null;
  eps_estimate: number | null;
  eps_difference: number | null;
  surprise_percent: number | null;
  status: 'BEAT' | 'MISS' | 'N/A';
}

export interface EarningsData {
  symbol: string;
  history: EarningsQuarter[];
  beats_count: number;
  misses_count: number;
  beat_ratio_percent: number;
  upcoming: Record<string, any>;
}
