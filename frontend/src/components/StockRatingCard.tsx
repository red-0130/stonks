import React from 'react';
import { StockRating } from '../types/stock';
import { CheckCircle2, XCircle, Award, ShieldAlert, Info } from 'lucide-react';

interface StockRatingCardProps {
  rating: StockRating;
}

export const StockRatingCard: React.FC<StockRatingCardProps> = ({ rating }) => {
  const getBadgeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'B':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
      case 'C':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      default:
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      {/* Header with Grade & Score */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">7-Factor Fundamental Rating</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Institutional investment criteria scorecard evaluating valuation, profitability, balance sheet health, and moat.
          </p>
        </div>

        {/* Grade Badge */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-xs text-slate-400 block font-medium">Rating Score</span>
            <span className="text-lg font-extrabold text-white font-mono">
              {rating.score} / {rating.total} Criteria
            </span>
          </div>
          <div
            className={`w-14 h-14 rounded-xl border flex flex-col items-center justify-center font-extrabold text-2xl shadow-lg ${getBadgeColor(
              rating.grade
            )}`}
          >
            {rating.grade}
          </div>
        </div>
      </div>

      {/* Progress Bar & Status Pill */}
      <div className="my-5">
        <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
          <span className="text-slate-300">
            Rating Status: <strong className="text-emerald-400">{rating.label}</strong>
          </span>
          <span className="text-slate-400 font-mono">{rating.percentage}% Met</span>
        </div>
        <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
            style={{ width: `${rating.percentage}%` }}
          />
        </div>
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        {rating.checklist.map((item) => (
          <div
            key={item.id}
            className={`p-4 rounded-lg border transition-all ${
              item.passed
                ? 'bg-emerald-950/20 border-emerald-500/30'
                : 'bg-rose-950/20 border-rose-500/30'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                {item.passed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-100">{item.name}</h3>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      Rule: {item.condition}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{item.description}</p>
                </div>
              </div>

              {/* Metric Value */}
              <div className="text-right shrink-0">
                <span className="text-xs text-slate-400 block">Actual</span>
                <span
                  className={`text-sm font-extrabold font-mono ${
                    item.passed ? 'text-emerald-300' : 'text-rose-300'
                  }`}
                >
                  {item.display_value}
                </span>
                <span
                  className={`block text-[10px] font-bold uppercase mt-1 px-1.5 py-0.5 rounded text-center ${
                    item.passed
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {item.passed ? 'Pass' : 'Fail'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
