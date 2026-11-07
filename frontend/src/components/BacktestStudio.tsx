import React from 'react';
import { BacktestResult } from '../types/stock';
import { Play, CheckCircle, Crosshair, Target, Shield, Percent, History, Layers, MapPin, Compass, TrendingUp, Clock, AlertTriangle, Loader2 } from 'lucide-react';
import { BacktestResultsSkeleton } from './skeletons';

interface BacktestStudioProps {
  strategies: { id: string; name: string; description: string }[];
  selectedStrategy: string;
  onSelectStrategy: (strat: string) => void;
  backtestResult: BacktestResult | null;
  onSetStrategy: () => void;
  isLoading: boolean;
}

export const BacktestStudio: React.FC<BacktestStudioProps> = ({
  strategies,
  selectedStrategy,
  onSelectStrategy,
  backtestResult,
  onSetStrategy,
  isLoading,
}) => {
  const isNoTrade = Boolean(
    backtestResult?.setup?.no_trade ||
    backtestResult?.setup?.condition?.toUpperCase().includes('NO TRADE') ||
    !backtestResult?.setup?.entry_price
  );
  const hasLiquidity = Boolean(backtestResult?.setup?.liquidity_price);
  const canSetStrategy = !isLoading && (!isNoTrade || hasLiquidity);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Crosshair className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Trading Strategy Backtesting Studio</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Backtest algorithmic trading models on historical data and generate institutional Entry, Stop-Loss, and Take-Profit setups.
          </p>
        </div>

        <button
          onClick={onSetStrategy}
          disabled={!canSetStrategy}
          className={`flex items-center gap-2 px-4 py-2 text-white rounded-lg text-sm font-bold shadow-lg transition ${
            canSetStrategy
              ? isNoTrade && hasLiquidity
                ? 'bg-amber-600 hover:bg-amber-500 shadow-amber-900/20'
                : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-900/20'
              : 'bg-emerald-600 opacity-40 cursor-not-allowed'
          }`}
          title={
            isNoTrade
              ? hasLiquidity
                ? 'Mark liquidity to be swept on chart'
                : 'No trade setup available in current market regime'
              : 'Apply trade setup to chart'
          }
        >
          <MapPin className={`w-4 h-4 ${isLoading ? 'animate-pulse' : ''}`} />
          <span>
            {isLoading
              ? 'Calculating Strategy...'
              : isNoTrade
              ? hasLiquidity
                ? 'Set Strategy (Mark Liquidity)'
                : 'No Trade Available'
              : 'Set Strategy'}
          </span>
        </button>
      </div>

      {/* Strategy Selection Pills */}
      <div>
        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2.5">
          Select Strategy Model
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {strategies.map((strat) => {
            const isSelected = selectedStrategy === strat.id;
            return (
              <button
                key={strat.id}
                onClick={() => onSelectStrategy(strat.id)}
                disabled={isLoading}
                className={`p-3.5 rounded-lg border text-left transition-all ${
                  isSelected
                    ? 'bg-emerald-500/10 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                    : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 hover:bg-slate-950'
                } ${isLoading ? 'cursor-not-allowed opacity-90' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-bold ${isSelected ? 'text-emerald-300' : 'text-slate-200'}`}>
                    {strat.name}
                  </span>
                  {isSelected && (
                    isLoading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    )
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{strat.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Backtest Results Area */}
      {backtestResult ? (
        <div className="space-y-6 relative">
          {/* Recalculating Overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-[2px] z-20 rounded-xl flex flex-col items-center justify-center p-6">
              <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-2" />
              <span className="text-xs font-mono text-slate-300">Recalculating quantitative backtest model...</span>
            </div>
          )}
          {/* Performance Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400 block mb-1">Win Rate (Success Rate)</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-extrabold text-emerald-400 font-mono">
                  {backtestResult.success_rate.toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400 block mb-1">Trades Won / Tested</span>
              <span className="text-xl font-extrabold text-white font-mono">
                {backtestResult.successful_trades} / {backtestResult.total_trades}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {backtestResult.losing_trades} losing trades
              </span>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400 block mb-1">Profit Factor</span>
              <span className="text-xl font-extrabold text-slate-200 font-mono">
                {backtestResult.profit_factor.toFixed(2)}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Gross Win / Gross Loss</span>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400 block mb-1">Total Return</span>
              <span
                className={`text-xl font-extrabold font-mono ${
                  backtestResult.total_return_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {backtestResult.total_return_percent >= 0 ? '+' : ''}
                {backtestResult.total_return_percent.toFixed(2)}%
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Unleveraged cumulative</span>
            </div>
          </div>

          {/* Actionable Trade Setup or No-Trade Regime Notification */}
          {isNoTrade ? (
            <div className="bg-gradient-to-r from-amber-950/20 via-slate-950 to-slate-950 border border-amber-500/30 rounded-xl p-5 shadow-lg space-y-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  {backtestResult.strategy_name} — Market Regime Filter
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold ml-auto border border-amber-500/30">
                  NO TRADE AVAILABLE
                </span>
              </div>

              {/* Strategy Condition Indicator */}
              {backtestResult.setup?.condition && (
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-900/90 rounded-lg border border-slate-800">
                  <Compass className="w-4 h-4 text-amber-400 shrink-0" />
                  <span className="text-xs text-slate-300">
                    <strong className="text-amber-300">Regime Status:</strong>{' '}
                    {backtestResult.setup.condition}
                  </span>
                </div>
              )}

              {/* Multi-Timeframe Structure Status Badges */}
              {backtestResult.setup?.timeframe_status && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      1W Trend Bias
                    </span>
                    <span className="text-xs font-semibold text-amber-300 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                      {backtestResult.setup.timeframe_status.weekly}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      1D Structure
                    </span>
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                      {backtestResult.setup.timeframe_status.daily}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      4H Confirmation
                    </span>
                    <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                      {backtestResult.setup.timeframe_status.execution_4h}
                    </span>
                  </div>
                </div>
              )}

              {/* Liquidity to be Swept Card */}
              {backtestResult.setup?.liquidity_price && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div className="bg-slate-900/90 border border-amber-500/40 p-3.5 rounded-lg flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block mb-0.5">
                        Liquidity Pool Area to Sweep
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {backtestResult.setup.liquidity_type || 'Equal Lows Pool'}
                      </span>
                      {backtestResult.setup.liquidity_price_low && backtestResult.setup.liquidity_price_high && (
                        <span className="text-[10px] text-slate-400 block mt-1">
                          Spread: ${(backtestResult.setup.liquidity_price_high - backtestResult.setup.liquidity_price_low).toFixed(2)} (
                          {(
                            ((backtestResult.setup.liquidity_price_high - backtestResult.setup.liquidity_price_low) /
                              backtestResult.setup.liquidity_price_low) *
                            100
                          ).toFixed(2)}
                          %)
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      {backtestResult.setup.liquidity_price_low && backtestResult.setup.liquidity_price_high ? (
                        <div>
                          <span className="text-lg sm:text-xl font-mono font-extrabold text-amber-300 block">
                            ${backtestResult.setup.liquidity_price_low.toFixed(2)} – ${backtestResult.setup.liquidity_price_high.toFixed(2)}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            Mid: ${backtestResult.setup.liquidity_price.toFixed(2)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-2xl font-mono font-extrabold text-amber-300">
                          ${backtestResult.setup.liquidity_price.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-lg flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-0.5">
                        Execution Prerequisite
                      </span>
                      <span className="text-xs text-slate-300">
                        Sweep penetration into area + LTF BOS
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {backtestResult.setup.liquidity_status || 'AWAITING SWEEP'}
                    </span>
                  </div>
                </div>
              )}

              {backtestResult.setup?.rationale && (
                <p className="text-xs text-slate-400 bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  💡 {backtestResult.setup.rationale}
                </p>
              )}
            </div>
          ) : backtestResult.setup && backtestResult.setup.entry_price !== null ? (
            <div className="bg-gradient-to-r from-emerald-950/30 via-slate-950 to-slate-950 border border-emerald-500/40 rounded-xl p-5 shadow-lg">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  {backtestResult.strategy_name} — Trade Setup
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold ml-auto">
                  R:R {backtestResult.setup.risk_reward_ratio}
                </span>
              </div>

              {/* Strategy Condition Indicator */}
              {backtestResult.setup.condition && (
                <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-slate-900/90 rounded-lg border border-slate-800">
                  <Compass className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="text-xs text-slate-300">
                    <strong className="text-emerald-300">Market Condition:</strong>{' '}
                    {backtestResult.setup.condition}
                  </span>
                </div>
              )}

              {/* Multi-Timeframe Structure Status Badges */}
              {backtestResult.setup.timeframe_status && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-3">
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      1W Trend Bias
                    </span>
                    <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
                      {backtestResult.setup.timeframe_status.weekly}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      1D Zone / POI
                    </span>
                    <span className="text-xs font-semibold text-blue-400 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 shrink-0 text-blue-400" />
                      {backtestResult.setup.timeframe_status.daily}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                      4H Confirmation
                    </span>
                    <span className="text-xs font-semibold text-purple-400 flex items-center gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0 text-purple-400" />
                      {backtestResult.setup.timeframe_status.execution_4h}
                    </span>
                  </div>
                </div>
              )}

              {backtestResult.setup.liquidity_price && (
                <div className="flex items-center justify-between mb-3 px-3.5 py-2.5 bg-amber-500/10 rounded-lg border border-amber-500/30">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-amber-400 shrink-0" />
                    <span className="text-xs text-amber-200">
                      <strong>Swept Liquidity Pool Area:</strong> {backtestResult.setup.liquidity_type || 'Equal Lows Pool'}
                    </span>
                  </div>
                  <span className="text-sm sm:text-base font-mono font-bold text-amber-300">
                    {backtestResult.setup.liquidity_price_low && backtestResult.setup.liquidity_price_high
                      ? `$${backtestResult.setup.liquidity_price_low.toFixed(2)} – $${backtestResult.setup.liquidity_price_high.toFixed(2)}`
                      : `$${backtestResult.setup.liquidity_price.toFixed(2)}`}
                  </span>
                </div>
              )}

              <p className="text-xs text-slate-300 mb-4 bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                💡 {backtestResult.setup.rationale}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
                {/* Entry Price */}
                <div className="p-3.5 bg-blue-950/20 border border-blue-500/30 rounded-lg">
                  <span className="text-xs text-blue-300 font-semibold block mb-1">Entry Price</span>
                  <span className="text-xl font-extrabold text-blue-400 font-mono">
                    ${backtestResult.setup.entry_price.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-1">Current Trigger Level</span>
                </div>

                {/* Stop Loss */}
                <div className="p-3.5 bg-rose-950/20 border border-rose-500/30 rounded-lg">
                  <span className="text-xs text-rose-300 font-semibold block mb-1">Stop-Loss Price</span>
                  <span className="text-xl font-extrabold text-rose-400 font-mono">
                    ${backtestResult.setup.stop_loss_price?.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-rose-400/80 block mt-1 font-mono">
                    -{backtestResult.setup.potential_risk_pct}% Risk
                  </span>
                </div>

                {/* Take Profit */}
                <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg">
                  <span className="text-xs text-emerald-300 font-semibold block mb-1">Take-Profit Price</span>
                  <span className="text-xl font-extrabold text-emerald-400 font-mono">
                    ${backtestResult.setup.take_profit_price?.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-emerald-400/80 block mt-1 font-mono">
                    +{backtestResult.setup.potential_gain_pct}% Target
                  </span>
                </div>
              </div>
            </div>
          ) : null}

          {/* Recent Backtest Trades Table */}
          {backtestResult.recent_trades && backtestResult.recent_trades.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <History className="w-4 h-4 text-slate-400" />
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Recent Backtest Trades Log
                </h3>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-2.5">Entry Price</th>
                      <th className="px-4 py-2.5">Exit Price</th>
                      <th className="px-4 py-2.5">Stop-Loss</th>
                      <th className="px-4 py-2.5">Take-Profit</th>
                      <th className="px-4 py-2.5">PnL (%)</th>
                      <th className="px-4 py-2.5 text-right">Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {backtestResult.recent_trades.map((t, idx) => {
                      const isWin = t.outcome === 'WIN';
                      return (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="px-4 py-2 text-slate-200">${t.entry_price}</td>
                          <td className="px-4 py-2 text-slate-200">${t.exit_price}</td>
                          <td className="px-4 py-2 text-rose-400">${t.stop_loss}</td>
                          <td className="px-4 py-2 text-emerald-400">${t.take_profit}</td>
                          <td className={`px-4 py-2 font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isWin ? '+' : ''}
                            {t.pnl_percent}%
                          </td>
                          <td className="px-4 py-2 text-right">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isWin
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              }`}
                            >
                              {t.outcome}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : isLoading ? (
        <BacktestResultsSkeleton />
      ) : (
        <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-400 text-xs">
          No backtest results available for this strategy.
        </div>
      )}
    </div>
  );
};
