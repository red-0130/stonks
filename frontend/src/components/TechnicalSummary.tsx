import React from 'react';
import { TechnicalData } from '../types/stock';
import { Gauge, Activity, Compass, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface TechnicalSummaryProps {
  technicals: TechnicalData;
}

export const TechnicalSummary: React.FC<TechnicalSummaryProps> = ({ technicals }) => {
  const { summary, indicators, pivot_points, signals } = technicals;

  const getSignalBadge = (sig: 'BUY' | 'SELL' | 'NEUTRAL') => {
    switch (sig) {
      case 'BUY':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'SELL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header & Gauge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Technical Analysis & Indicators</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time trend, oscillator momentum, volatility, and key pivot levels.
          </p>
        </div>

        {/* Composite Summary Gauge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider block font-medium">
              Overall Consensus
            </span>
            <span className="text-base font-extrabold text-white">{summary.label}</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              {summary.buy} Buy
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              {summary.neutral} Neutral
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
              {summary.sell} Sell
            </span>
          </div>
        </div>
      </div>

      {/* Primary Key Indicators Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* RSI */}
        <div className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg">
          <span className="text-xs text-slate-400 block mb-1">RSI (14)</span>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-extrabold text-white font-mono">
              {indicators.rsi_14.toFixed(1)}
            </span>
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                indicators.rsi_14 > 70
                  ? 'bg-rose-500/20 text-rose-400'
                  : indicators.rsi_14 < 30
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {indicators.rsi_14 > 70 ? 'Overbought' : indicators.rsi_14 < 30 ? 'Oversold' : 'Neutral'}
            </span>
          </div>
        </div>

        {/* MACD */}
        <div className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg">
          <span className="text-xs text-slate-400 block mb-1">MACD (12, 26)</span>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-extrabold text-white font-mono">
              {indicators.macd.toFixed(2)}
            </span>
            <span className="text-xs font-mono text-slate-400">
              Sig: {indicators.macd_signal.toFixed(2)}
            </span>
          </div>
        </div>

        {/* ATR */}
        <div className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg">
          <span className="text-xs text-slate-400 block mb-1">ATR (14 Volatility)</span>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-extrabold text-emerald-400 font-mono">
              ${indicators.atr_14.toFixed(2)}
            </span>
            <span className="text-[10px] text-slate-400">Daily Risk Range</span>
          </div>
        </div>

        {/* Bollinger Band Middle */}
        <div className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg">
          <span className="text-xs text-slate-400 block mb-1">Bollinger Mid (20)</span>
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-extrabold text-white font-mono">
              {indicators.bb_middle ? `$${indicators.bb_middle.toFixed(2)}` : 'N/A'}
            </span>
            <span className="text-[10px] text-slate-400">SMA 20 Basis</span>
          </div>
        </div>
      </div>

      {/* Indicator Signals Table */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Signal Evaluator
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          {signals.map((s, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-slate-950/70 border border-slate-800 rounded-lg"
            >
              <div>
                <span className="font-semibold text-slate-200 block">{s.name}</span>
                <span className="text-[11px] text-slate-400">{s.action}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-slate-300">{s.value}</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getSignalBadge(
                    s.signal
                  )}`}
                >
                  {s.signal}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Support & Resistance Pivot Points */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Daily Support & Resistance Levels (Pivot Points)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono text-center">
          <div className="p-2.5 bg-rose-950/20 border border-rose-500/30 rounded-lg">
            <span className="text-[10px] text-rose-400 block mb-0.5 font-bold">R2 Resistance</span>
            <span className="text-sm font-extrabold text-slate-100">${pivot_points.r2}</span>
          </div>
          <div className="p-2.5 bg-rose-950/10 border border-rose-500/20 rounded-lg">
            <span className="text-[10px] text-rose-300 block mb-0.5 font-bold">R1 Resistance</span>
            <span className="text-sm font-extrabold text-slate-100">${pivot_points.r1}</span>
          </div>
          <div className="p-2.5 bg-slate-800/60 border border-slate-700 rounded-lg">
            <span className="text-[10px] text-slate-400 block mb-0.5 font-bold">Pivot Center</span>
            <span className="text-sm font-extrabold text-slate-100">${pivot_points.pivot}</span>
          </div>
          <div className="p-2.5 bg-emerald-950/10 border border-emerald-500/20 rounded-lg">
            <span className="text-[10px] text-emerald-300 block mb-0.5 font-bold">S1 Support</span>
            <span className="text-sm font-extrabold text-slate-100">${pivot_points.s1}</span>
          </div>
          <div className="p-2.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg">
            <span className="text-[10px] text-emerald-400 block mb-0.5 font-bold">S2 Support</span>
            <span className="text-sm font-extrabold text-slate-100">${pivot_points.s2}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
