import React from 'react';
import { Skeleton } from './Skeleton';
import { Activity } from 'lucide-react';

export const TechnicalSummarySkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-500/40" />
            <Skeleton className="h-6 w-64" />
          </div>
          <Skeleton className="h-3.5 w-72 mt-2" />
        </div>

        {/* Consensus Badge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <Skeleton className="h-3 w-24 mb-1" />
            <Skeleton className="h-5 w-20" />
          </div>
          <div className="flex items-center gap-1.5">
            <Skeleton className="h-6 w-14 rounded" />
            <Skeleton className="h-6 w-16 rounded" />
            <Skeleton className="h-6 w-14 rounded" />
          </div>
        </div>
      </div>

      {/* Primary Key Indicators Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-lg">
            <Skeleton className="h-3 w-16 mb-2" />
            <div className="flex items-baseline justify-between">
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-4 w-14 rounded" />
            </div>
          </div>
        ))}
      </div>

      {/* Pivot Points & Moving Averages Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
          <Skeleton className="h-4 w-32 mb-3" />
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex justify-between items-center py-1">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-4 w-24" />
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
          <Skeleton className="h-4 w-36 mb-3" />
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex justify-between items-center py-1">
                <Skeleton className="h-3 w-28" />
                <Skeleton className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
