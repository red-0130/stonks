import React from 'react';
import { Skeleton } from './Skeleton';
import { DollarSign } from 'lucide-react';

export const EarningsSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-500/40" />
            <Skeleton className="h-6 w-64" />
          </div>
          <Skeleton className="h-3.5 w-80 mt-2" />
        </div>

        {/* Beat Ratio Badge */}
        <div className="flex items-center gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <Skeleton className="h-3 w-16 mb-1" />
            <Skeleton className="h-6 w-16" />
          </div>
          <Skeleton className="h-4 w-28" />
        </div>
      </div>

      {/* Upcoming Earnings Banner Skeleton */}
      <div className="p-4 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-8 h-8 rounded-lg" />
          <div>
            <Skeleton className="h-4 w-48 mb-1.5" />
            <Skeleton className="h-3 w-36" />
          </div>
        </div>
        <Skeleton className="h-4 w-20" />
      </div>

      {/* EPS Chart Placeholder */}
      <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-44" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>

        {/* Simulated Bar Graph */}
        <div className="h-48 flex items-end justify-around pt-6 pb-2 border-b border-slate-800">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-end gap-1.5 h-full">
              <Skeleton className="w-7 sm:w-10 rounded-t h-3/5" />
              <Skeleton className="w-7 sm:w-10 rounded-t h-4/5" />
            </div>
          ))}
        </div>
      </div>

      {/* Quarters Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 rounded-xl border border-slate-800 bg-slate-950 space-y-2">
            <div className="flex justify-between items-center">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-5 w-16 rounded" />
            </div>
            <div className="flex justify-between items-baseline pt-1">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-4 w-12" />
            </div>
            <div className="flex justify-between items-baseline">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
