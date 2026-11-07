import React from 'react';
import { Skeleton } from './Skeleton';
import { Award } from 'lucide-react';

export const StockRatingSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-emerald-500/40" />
            <Skeleton className="h-6 w-64" />
          </div>
          <Skeleton className="h-3.5 w-80 sm:w-96 mt-2" />
        </div>

        {/* Grade Badge Skeleton */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <Skeleton className="h-3 w-20 mb-1.5 ml-auto" />
            <Skeleton className="h-6 w-28 ml-auto" />
          </div>
          <Skeleton className="w-14 h-14 rounded-xl" />
        </div>
      </div>

      {/* Progress Bar Skeleton */}
      <div className="my-5">
        <div className="flex justify-between items-center text-xs mb-1.5">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="w-full h-2.5 rounded-full" />
      </div>

      {/* Criteria Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        {Array.from({ length: 7 }).map((_, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg border border-slate-800/80 bg-slate-950/40 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Skeleton className="w-5 h-5 rounded-full shrink-0" />
                  <Skeleton className="h-4 w-36" />
                </div>
                <Skeleton className="h-5 w-16 rounded" />
              </div>
              <Skeleton className="h-3 w-4/5 mt-1" />
            </div>

            <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-800/60 text-xs">
              <Skeleton className="h-3 w-28" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
