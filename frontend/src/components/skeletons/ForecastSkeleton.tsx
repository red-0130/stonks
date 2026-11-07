import React from 'react';
import { Skeleton } from './Skeleton';
import { Sparkles, Compass } from 'lucide-react';

export const ForecastSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-500/40" />
            <Skeleton className="h-6 w-72" />
          </div>
          <Skeleton className="h-3.5 w-80 mt-2" />
        </div>

        {/* Consensus Badge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <Skeleton className="h-3 w-28 mb-1" />
            <Skeleton className="h-5 w-24" />
          </div>
          <Skeleton className="h-7 w-20 rounded-lg" />
        </div>
      </div>

      {/* Target Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
            <Skeleton className="h-3 w-24 mb-2" />
            <Skeleton className="h-7 w-28 mb-1" />
            <Skeleton className="h-3 w-20" />
          </div>
        ))}
      </div>

      {/* Chart Canvas Area */}
      <div className="bg-slate-950 border border-slate-800/90 rounded-xl p-4">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800/80">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-6 w-48 rounded" />
        </div>

        {/* Shimmering chart canvas simulation */}
        <div className="h-72 w-full flex flex-col justify-between py-4 relative">
          <div className="border-b border-dashed border-slate-800 w-full" />
          <div className="border-b border-dashed border-slate-800 w-full" />
          <div className="border-b border-dashed border-slate-800 w-full" />
          <div className="border-b border-dashed border-slate-800 w-full" />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-3 border-emerald-500/50 border-t-transparent rounded-full animate-spin mb-2" />
            <span className="text-xs text-slate-400 font-mono">Aggregating forecast consensus & trajectory data...</span>
          </div>
        </div>
      </div>

      {/* Quarterly Milestones Grid */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Compass className="w-4 h-4 text-emerald-500/40" />
          <Skeleton className="h-4 w-60" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-xl border border-slate-800 bg-slate-950">
              <div className="flex items-center justify-between mb-2">
                <Skeleton className="h-3.5 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
              <Skeleton className="h-6 w-24 mb-2" />
              <div className="flex justify-between pt-2 border-t border-slate-800/80">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
