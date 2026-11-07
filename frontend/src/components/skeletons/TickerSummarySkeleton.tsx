import React from 'react';
import { Skeleton } from './Skeleton';

export const TickerSummarySkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-24 rounded-lg" />
            <Skeleton className="h-5 w-40 rounded-full" />
          </div>
          <Skeleton className="h-4 w-48 mt-2" />
        </div>

        {/* Live Price Display Skeleton */}
        <div className="flex items-baseline gap-3">
          <Skeleton className="h-9 w-32 rounded-lg" />
          <Skeleton className="h-8 w-28 rounded-lg" />
        </div>
      </div>

      {/* Metrics Grid Skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4 text-xs">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-lg">
            <Skeleton className="h-3 w-16 mb-2" />
            <Skeleton className="h-5 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
};
