import React, { useState } from 'react';
import { ForecastData } from '../types/stock';
import { TrendingUp, Users, Target, ShieldAlert, Award, Compass, ArrowUpRight, ArrowDownRight, Layers } from 'lucide-react';

interface ForecastChartProps {
  forecastData: ForecastData;
  daysAhead?: number;
  onChangeDaysAhead?: (days: number) => void;
  isLoading: boolean;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  forecastData,
  isLoading,
}) => {
  const {
    current_price,
    target_mean,
    target_median,
    target_high,
    target_low,
    implied_upside_percent,
    high_upside_percent,
    low_downside_percent,
    analyst_count,
    consensus_score,
    consensus_label,
    recommendation_key,
    ratings,
    milestones,
    historical,
    trajectories,
    provider,
  } = forecastData;

  const [selectedMilestone, setSelectedMilestone] = useState<string>('12M');
  const [activeTrajectory, setActiveTrajectory] = useState<'all' | 'mean' | 'high' | 'low'>('all');

  const isBullish = implied_upside_percent >= 0;

  // SVG Dimension & Coordinate Math
  const width = 860;
  const height = 360;
  const padding = { top: 25, right: 65, bottom: 45, left: 60 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Gather min/max price for scaling
  const histPrices = historical.map((h) => h.price);
  const trajHighs = trajectories.map((t) => t.high);
  const trajLows = trajectories.map((t) => t.low);
  const allValues = [...histPrices, ...trajHighs, ...trajLows, current_price].filter((v) => v > 0);

  const minPrice = Math.min(...allValues) * 0.95;
  const maxPrice = Math.max(...allValues) * 1.05;
  const priceRange = maxPrice - minPrice || 1;

  const totalPointsCount = (historical.length || 1) + trajectories.length - 1;
  const histEndIdx = Math.max(0, historical.length - 1);

  const getX = (idx: number) => padding.left + (idx / Math.max(1, totalPointsCount - 1)) * graphWidth;
  const getY = (val: number) => padding.top + graphHeight - ((val - minPrice) / priceRange) * graphHeight;

  // 1. Historical Path
  const histPoints = historical.map((h, i) => `${getX(i)},${getY(h.price)}`).join(' ');

  // 2. High Trajectory Path (Bull Case)
  const highPoints = trajectories.map((t, i) => `${getX(histEndIdx + i)},${getY(t.high)}`).join(' ');

  // 3. Mean Trajectory Path (Consensus)
  const meanPoints = trajectories.map((t, i) => `${getX(histEndIdx + i)},${getY(t.mean)}`).join(' ');

  // 4. Low Trajectory Path (Bear Case)
  const lowPoints = trajectories.map((t, i) => `${getX(histEndIdx + i)},${getY(t.low)}`).join(' ');

  // 5. Consensus Spread Cone Polygon (between Low and High)
  const forwardHighPoints = trajectories.map((t, i) => `${getX(histEndIdx + i)},${getY(t.high)}`);
  const forwardLowPoints = trajectories
    .slice()
    .reverse()
    .map((t, i) => `${getX(histEndIdx + trajectories.length - 1 - i)},${getY(t.low)}`);
  const conePolygonPoints = [...forwardHighPoints, ...forwardLowPoints].join(' ');

  // Consensus score color
  const getScoreColor = (score: number) => {
    if (score <= 1.8) return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/40';
    if (score <= 2.5) return 'text-teal-300 bg-teal-500/20 border-teal-500/40';
    if (score <= 3.2) return 'text-amber-400 bg-amber-500/20 border-amber-500/40';
    return 'text-rose-400 bg-rose-500/20 border-rose-500/40';
  };

  const totalRatings = ratings.total || 1;
  const pctSb = (ratings.strong_buy / totalRatings) * 100;
  const pctB = (ratings.buy / totalRatings) * 100;
  const pctH = (ratings.hold / totalRatings) * 100;
  const pctS = (ratings.sell / totalRatings) * 100;
  const pctSs = (ratings.strong_sell / totalRatings) * 100;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Target className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">FactSet Analyst Consensus Price Forecast</h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold uppercase">
              12M Horizon
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Wall Street institutional consensus price targets, high/low spread cone, and quarterly milestone fan trajectories.
          </p>
        </div>

        {/* FactSet Consensus Rating Badge */}
        <div className="flex items-center gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-medium">
              Consensus Score
            </span>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold text-white font-mono">
                {consensus_score.toFixed(1)} / 5.0
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${getScoreColor(consensus_score)}`}>
                {consensus_label}
              </span>
            </div>
          </div>
          <div className="text-right border-l border-slate-800 pl-3">
            <span className="text-[10px] text-slate-400 block font-medium">Coverage</span>
            <span className="text-xs font-bold text-slate-200 font-mono">
              {analyst_count} Analysts
            </span>
          </div>
        </div>
      </div>

      {/* 4 Summary Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Consensus 12M Mean Target */}
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 block mb-1">Consensus 12M Target</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              ${target_mean.toFixed(2)}
            </span>
            <span
              className={`text-xs font-bold font-mono ${
                isBullish ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isBullish ? '+' : ''}
              {implied_upside_percent.toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">
            Median: ${target_median.toFixed(2)}
          </span>
        </div>

        {/* Bull Case Target */}
        <div className="p-4 bg-slate-950 border border-emerald-500/20 rounded-xl">
          <span className="text-xs text-emerald-400/80 font-medium block mb-1">Bull Case (High Target)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-emerald-400 font-mono">
              ${target_high.toFixed(2)}
            </span>
            <span className="text-xs font-bold font-mono text-emerald-400">
              +{high_upside_percent.toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">Peak institutional target</span>
        </div>

        {/* Bear Case Target */}
        <div className="p-4 bg-slate-950 border border-rose-500/20 rounded-xl">
          <span className="text-xs text-rose-400/80 font-medium block mb-1">Bear Case (Low Target)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-rose-400 font-mono">
              ${target_low.toFixed(2)}
            </span>
            <span className="text-xs font-bold font-mono text-rose-400">
              {low_downside_percent.toFixed(1)}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">Conservative floor target</span>
        </div>

        {/* Current Price vs Spread */}
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 block mb-1">Current Trading Price</span>
          <span className="text-2xl font-extrabold text-slate-200 font-mono">
            ${current_price.toFixed(2)}
          </span>
          <span className="text-[10px] text-slate-400 block mt-1">
            12M Spread: ${(target_high - target_low).toFixed(0)} range
          </span>
        </div>
      </div>

      {/* Target Cone & Fan Chart */}
      <div className="relative bg-slate-950 border border-slate-800/90 rounded-xl p-4 overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm z-20 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs text-slate-400 mt-2 font-mono">Aggregating FactSet consensus data...</span>
          </div>
        )}

        {/* Chart View Controls Toolbar */}
        <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/80 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium">Trajectory Filter:</span>
            {(['all', 'mean', 'high', 'low'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setActiveTrajectory(mode)}
                className={`px-2.5 py-0.5 rounded text-[11px] font-medium uppercase transition ${
                  activeTrajectory === mode
                    ? 'bg-slate-800 text-emerald-400 border border-slate-700 shadow-sm'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
          <span className="text-[11px] text-slate-400 font-mono hidden sm:inline">
            180D Historical • 12M Forward Cone
          </span>
        </div>

        {/* SVG Fan Chart Canvas */}
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="consensusConeGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.22" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padding.top + pct * graphHeight;
            const priceVal = maxPrice - pct * priceRange;
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#1e293b"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="monospace"
                >
                  ${priceVal.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Forecast Transition Vertical Divider */}
          <line
            x1={getX(histEndIdx)}
            y1={padding.top}
            x2={getX(histEndIdx)}
            y2={padding.top + graphHeight}
            stroke="#475569"
            strokeDasharray="3 3"
          />
          <text
            x={getX(histEndIdx) + 6}
            y={padding.top + 12}
            fill="#94a3b8"
            fontSize="10"
            fontWeight="bold"
          >
            Today • 12M Consensus Start →
          </text>

          {/* Shaded Target Spread Cone */}
          {(activeTrajectory === 'all' || activeTrajectory === 'mean') && (
            <polygon points={conePolygonPoints} fill="url(#consensusConeGrad)" />
          )}

          {/* Historical Price Path */}
          <polyline
            points={histPoints}
            fill="none"
            stroke="#94a3b8"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Bull Case High Trajectory (Green dashed) */}
          {(activeTrajectory === 'all' || activeTrajectory === 'high') && (
            <polyline
              points={highPoints}
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              strokeDasharray="5 4"
              strokeLinecap="round"
            />
          )}

          {/* Bear Case Low Trajectory (Rose dashed) */}
          {(activeTrajectory === 'all' || activeTrajectory === 'low') && (
            <polyline
              points={lowPoints}
              fill="none"
              stroke="#ef4444"
              strokeWidth="2"
              strokeDasharray="5 4"
              strokeLinecap="round"
            />
          )}

          {/* Consensus Mean Trajectory (Solid Emerald) */}
          {(activeTrajectory === 'all' || activeTrajectory === 'mean') && (
            <polyline
              points={meanPoints}
              fill="none"
              stroke="#34d399"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          )}

          {/* Milestone Markers along the trajectory */}
          {milestones.map((ms, idx) => {
            const trajIdx = histEndIdx + ms.month;
            const x = getX(trajIdx);
            const yMean = getY(ms.target_mean);
            const yHigh = getY(ms.target_high);
            const yLow = getY(ms.target_low);

            return (
              <g key={idx} className="cursor-pointer" onClick={() => setSelectedMilestone(ms.period)}>
                {/* Milestone vertical line */}
                <line
                  x1={x}
                  y1={yHigh}
                  x2={x}
                  y2={yLow}
                  stroke="#334155"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />

                {/* Mean marker circle */}
                <circle
                  cx={x}
                  cy={yMean}
                  r="5"
                  fill="#10b981"
                  stroke="#0f172a"
                  strokeWidth="2"
                />

                {/* High marker circle */}
                <circle
                  cx={x}
                  cy={yHigh}
                  r="4"
                  fill="#34d399"
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />

                {/* Low marker circle */}
                <circle
                  cx={x}
                  cy={yLow}
                  r="4"
                  fill="#ef4444"
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />

                {/* Period label badge at bottom */}
                <text
                  x={x}
                  y={padding.top + graphHeight + 18}
                  fill={selectedMilestone === ms.period ? '#34d399' : '#94a3b8'}
                  fontSize="11"
                  fontWeight="bold"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {ms.period}
                </text>

                {/* Price label on top of mean target */}
                <text
                  x={x}
                  y={yMean - 8}
                  fill="#e2e8f0"
                  fontSize="10"
                  fontWeight="bold"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  ${ms.target_mean.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Today's price anchor dot */}
          <circle
            cx={getX(histEndIdx)}
            cy={getY(current_price)}
            r="5"
            fill="#3b82f6"
            stroke="#0f172a"
            strokeWidth="2"
          />
        </svg>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 mt-2 pt-2 border-t border-slate-800">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 bg-slate-400"></span> Historical (180D)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 bg-emerald-400"></span> Consensus Target (${target_mean.toFixed(2)})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 border-t border-emerald-400 border-dashed"></span> Bull Target (${target_high.toFixed(2)})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 border-t border-rose-400 border-dashed"></span> Bear Target (${target_low.toFixed(2)})
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-emerald-500/20 border border-emerald-500/40 rounded-sm"></span> Target Spread Cone
            </span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">{provider}</span>
        </div>
      </div>

      {/* FactSet Analyst Ratings Distribution Bar */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              FactSet Analyst Ratings Distribution ({analyst_count} Opinions)
            </h3>
          </div>
          <span className="text-xs font-mono text-emerald-400 font-bold">
            {ratings.strong_buy + ratings.buy} Buy Opinions ({((ratings.strong_buy + ratings.buy) / totalRatings * 100).toFixed(0)}%)
          </span>
        </div>

        {/* Multi-segment distribution progress bar */}
        <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
          {pctSb > 0 && <div style={{ width: `${pctSb}%` }} className="bg-emerald-600 h-full" title={`Strong Buy: ${ratings.strong_buy}`} />}
          {pctB > 0 && <div style={{ width: `${pctB}%` }} className="bg-emerald-400 h-full" title={`Buy: ${ratings.buy}`} />}
          {pctH > 0 && <div style={{ width: `${pctH}%` }} className="bg-amber-400 h-full" title={`Hold: ${ratings.hold}`} />}
          {pctS > 0 && <div style={{ width: `${pctS}%` }} className="bg-orange-500 h-full" title={`Sell: ${ratings.sell}`} />}
          {pctSs > 0 && <div style={{ width: `${pctSs}%` }} className="bg-rose-500 h-full" title={`Strong Sell: ${ratings.strong_sell}`} />}
        </div>

        {/* Legend counts */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono pt-1">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
            <span className="text-slate-400">Strong Buy:</span>
            <strong className="text-slate-100">{ratings.strong_buy}</strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-slate-400">Buy:</span>
            <strong className="text-slate-100">{ratings.buy}</strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            <span className="text-slate-400">Hold:</span>
            <strong className="text-slate-100">{ratings.hold}</strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
            <span className="text-slate-400">Sell:</span>
            <strong className="text-slate-100">{ratings.sell}</strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span className="text-slate-400">Strong Sell:</span>
            <strong className="text-slate-100">{ratings.strong_sell}</strong>
          </div>
        </div>
      </div>

      {/* Quarterly Milestones Grid (3M, 6M, 9M, 12M) */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Compass className="w-4 h-4 text-emerald-400" />
          Quarterly Consensus Milestone Targets
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {milestones.map((ms) => {
            const isSelected = selectedMilestone === ms.period;
            return (
              <div
                key={ms.period}
                onClick={() => setSelectedMilestone(ms.period)}
                className={`p-4 rounded-xl border transition cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-500/10 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    {ms.period} Milestone
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{ms.date}</span>
                </div>

                <div className="flex items-baseline justify-between">
                  <span className="text-xl font-extrabold text-white font-mono">
                    ${ms.target_mean.toFixed(2)}
                  </span>
                  <span
                    className={`text-xs font-bold font-mono ${
                      ms.implied_change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {ms.implied_change_percent >= 0 ? '+' : ''}
                    {ms.implied_change_percent.toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono mt-2 pt-2 border-t border-slate-800/80">
                  <span>Low: ${ms.target_low.toFixed(0)}</span>
                  <span>High: ${ms.target_high.toFixed(0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
