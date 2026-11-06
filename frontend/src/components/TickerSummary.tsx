import React from 'react';
import { StockInfo } from '../types/stock';
import { TrendingUp, TrendingDown, DollarSign, Layers, PieChart, BarChart2 } from 'lucide-react';

interface TickerSummaryProps {
  info: StockInfo;
}

function formatCurrency(val?: number | null): string {
  if (val === undefined || val === null) return 'N/A';
  return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatLargeNumber(val?: number | null): string {
  if (val === undefined || val === null) return 'N/A';
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return val.toLocaleString();
}

function formatShares(val?: number | null): string {
  if (val === undefined || val === null) return 'N/A';
  if (val >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(2)}M`;
  return val.toLocaleString();
}

export const TickerSummary: React.FC<TickerSummaryProps> = ({ info }) => {
  const isPositive = info.change >= 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">
              {info.symbol}
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {info.sector} • {info.industry}
            </span>
          </div>
          <p className="text-sm font-medium text-slate-400 mt-1">{info.name}</p>
        </div>

        {/* Live Price Display */}
        <div className="flex items-baseline gap-3">
          <div className="text-3xl sm:text-4xl font-extrabold text-white font-mono">
            {formatCurrency(info.current_price)}
          </div>
          <div
            className={`flex items-center gap-1 text-sm sm:text-base font-semibold px-2.5 py-1 rounded-lg ${
              isPositive
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>
              {isPositive ? '+' : ''}
              {info.change.toFixed(2)} ({isPositive ? '+' : ''}
              {info.change_percent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>

      {/* Basic Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4 text-xs">
        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">Market Cap</span>
          <span className="text-sm font-semibold text-slate-200 font-mono">
            {formatLargeNumber(info.market_cap)}
          </span>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">Outstanding Shares</span>
          <span className="text-sm font-semibold text-slate-200 font-mono">
            {formatShares(info.shares_outstanding)}
          </span>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">Dividend Yield</span>
          <span className="text-sm font-semibold text-emerald-400 font-mono">
            {info.dividend_yield ? `${info.dividend_yield.toFixed(2)}%` : '0.00%'}
          </span>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">P/E Ratio</span>
          <span className="text-sm font-semibold text-slate-200 font-mono">
            {info.pe_ratio ? `${info.pe_ratio.toFixed(2)}x` : 'N/A'}
          </span>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">Day Range</span>
          <span className="text-xs font-semibold text-slate-300 font-mono block truncate">
            {info.day_low ? `$${info.day_low.toFixed(2)} - $${info.day_high?.toFixed(2)}` : 'N/A'}
          </span>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
          <span className="text-slate-400 block mb-1">52-Week Range</span>
          <span className="text-xs font-semibold text-slate-300 font-mono block truncate">
            {info.fifty_two_week_low ? `$${info.fifty_two_week_low.toFixed(2)} - $${info.fifty_two_week_high?.toFixed(2)}` : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};
