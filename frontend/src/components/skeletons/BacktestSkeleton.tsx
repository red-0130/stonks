import React from 'react';
import { Skeleton } from './Skeleton';

export const BacktestResultsSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* 4 Performance Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
            <Skeleton className="h-3 w-28 mb-2" />
            <Skeleton className="h-8 w-24 mb-1.5" />
            <Skeleton className="h-3 w-20" />
          </div>
        ))}
      </div>

      {/* Trade Setup Card Skeleton */}
      <div className="p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-3 bg-slate-900 border border-slate-800/80 rounded-lg">
              <Skeleton className="h-3 w-16 mb-2" />
              <Skeleton className="h-6 w-20" />
            </div>
          ))}
        </div>
      </div>

      {/* Trade Log Table Skeleton */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
        <div className="flex justify-between items-center mb-2">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex justify-between items-center py-2 px-3 bg-slate-900/60 rounded">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
