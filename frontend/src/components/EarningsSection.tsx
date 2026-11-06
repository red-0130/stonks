import React from 'react';
import { EarningsData } from '../types/stock';
import { Calendar, CheckCircle2, XCircle, TrendingUp, DollarSign } from 'lucide-react';

interface EarningsSectionProps {
  earnings: EarningsData;
}

export const EarningsSection: React.FC<EarningsSectionProps> = ({ earnings }) => {
  const { history, beats_count, misses_count, beat_ratio_percent, upcoming } = earnings;

  // Find scale for EPS Chart
  const allEps = history.flatMap((h) => [h.eps_actual ?? 0, h.eps_estimate ?? 0]);
  const maxEps = Math.max(1, ...allEps) * 1.25;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Historical Earnings & Estimates</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Quarterly EPS actual results vs consensus estimates and surprise performance.
          </p>
        </div>

        {/* Beat Ratio Badge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-medium">
              Beat Ratio
            </span>
            <span className="text-base font-extrabold text-emerald-400 font-mono">
              {beat_ratio_percent.toFixed(0)}%
            </span>
          </div>
          <div className="text-xs text-slate-400">
            <span className="text-emerald-400 font-bold">{beats_count} Beats</span> •{' '}
            <span className="text-rose-400 font-bold">{misses_count} Misses</span>
          </div>
        </div>
      </div>

      {/* Upcoming Earnings Banner */}
      {upcoming && (upcoming.date || upcoming.Earnings_Date) && (
        <div className="p-4 bg-emerald-950/20 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
              <Calendar className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-slate-100 block">Upcoming Earnings Announcement</span>
              <span className="text-slate-400">
                Scheduled Date: <strong className="text-emerald-300 font-mono">{upcoming.date || upcoming.Earnings_Date}</strong>
              </span>
            </div>
          </div>
          {upcoming.eps_estimate_avg && (
            <div className="text-right">
              <span className="text-slate-400 block text-[11px]">Consensus EPS Est.</span>
              <span className="text-sm font-extrabold text-white font-mono">
                ${Number(upcoming.eps_estimate_avg).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Interactive EPS Beat/Miss Bar Chart */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
          Quarterly EPS: Actual vs Consensus Estimate
        </h3>

        <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
          <div className="flex items-end justify-between gap-4 h-44 pb-2 border-b border-slate-800">
            {history.map((q, idx) => {
              const actHeight = q.eps_actual ? Math.max(10, (q.eps_actual / maxEps) * 100) : 0;
              const estHeight = q.eps_estimate ? Math.max(10, (q.eps_estimate / maxEps) * 100) : 0;
              const isBeat = q.status === 'BEAT';

              return (
                <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group">
                  {/* Tooltip Surprise Badge on top */}
                  <div className="mb-2 text-center">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        isBeat
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {q.surprise_percent ? `${q.surprise_percent > 0 ? '+' : ''}${q.surprise_percent}%` : 'N/A'}
                    </span>
                  </div>

                  {/* Dual Bars: Actual (left) & Estimate (right) */}
                  <div className="flex items-end gap-1.5 w-full max-w-[50px] h-32 justify-center">
                    {/* Actual EPS Bar */}
                    <div
                      className={`w-1/2 rounded-t transition-all ${
                        isBeat ? 'bg-emerald-500' : 'bg-rose-500'
                      } hover:brightness-110`}
                      style={{ height: `${actHeight}%` }}
                      title={`Actual EPS: $${q.eps_actual}`}
                    />
                    {/* Estimate EPS Bar */}
                    <div
                      className="w-1/2 bg-slate-700 rounded-t hover:brightness-110"
                      style={{ height: `${estHeight}%` }}
                      title={`Estimated EPS: $${q.eps_estimate}`}
                    />
                  </div>

                  {/* Quarter Date Label */}
                  <span className="text-[10px] font-mono text-slate-400 mt-2 block truncate max-w-[65px] text-center">
                    {q.quarter}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Chart Legend */}
          <div className="flex items-center justify-center gap-6 mt-3 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-emerald-500 rounded-sm"></span> Actual EPS (Beat)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-rose-500 rounded-sm"></span> Actual EPS (Miss)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-slate-700 rounded-sm"></span> Consensus Estimate
            </span>
          </div>
        </div>
      </div>

      {/* Historical Earnings Table */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Earnings History Breakdown
        </h3>

        <div className="overflow-x-auto border border-slate-800 rounded-lg">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-2.5">Quarter</th>
                <th className="px-4 py-2.5">EPS Actual</th>
                <th className="px-4 py-2.5">EPS Estimate</th>
                <th className="px-4 py-2.5">Difference</th>
                <th className="px-4 py-2.5">Surprise %</th>
                <th className="px-4 py-2.5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {history.map((q, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="px-4 py-2 text-slate-200">{q.quarter}</td>
                  <td className="px-4 py-2 font-bold text-white">
                    {q.eps_actual ? `$${q.eps_actual.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-4 py-2 text-slate-400">
                    {q.eps_estimate ? `$${q.eps_estimate.toFixed(2)}` : 'N/A'}
                  </td>
                  <td className="px-4 py-2 text-slate-300">
                    {q.eps_difference ? `${q.eps_difference > 0 ? '+' : ''}$${q.eps_difference.toFixed(2)}` : 'N/A'}
                  </td>
                  <td
                    className={`px-4 py-2 font-bold ${
                      q.status === 'BEAT' ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {q.surprise_percent ? `${q.surprise_percent > 0 ? '+' : ''}${q.surprise_percent}%` : 'N/A'}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        q.status === 'BEAT'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : q.status === 'MISS'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {q.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
