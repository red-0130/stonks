import React from 'react';
import { Skeleton } from './Skeleton';
import { MessageSquare } from 'lucide-react';

export const SentimentSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-emerald-500/40" />
            <Skeleton className="h-6 w-64" />
          </div>
          <Skeleton className="h-3.5 w-80 mt-2" />
        </div>

        {/* Sentiment Index Badge */}
        <div className="flex items-center gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <Skeleton className="h-3 w-20 mb-1" />
            <Skeleton className="h-5 w-24" />
          </div>
          <Skeleton className="h-7 w-14 rounded" />
        </div>
      </div>

      {/* Sentiment Gauge Bar */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
        <div className="flex justify-between items-center text-xs mb-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-28" />
        </div>
        <Skeleton className="h-3 w-full rounded-full" />
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
            <Skeleton className="h-3 w-28 mb-2" />
            <Skeleton className="h-7 w-20" />
          </div>
        ))}
      </div>

      {/* News Articles List Skeleton */}
      <div className="space-y-3 pt-2">
        <Skeleton className="h-4 w-44 mb-3" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="p-4 rounded-xl border border-slate-800 bg-slate-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <Skeleton className="h-4 w-20 rounded" />
                <Skeleton className="h-3 w-28" />
              </div>
              <Skeleton className="h-4 w-5/6" />
            </div>
            <Skeleton className="h-6 w-20 rounded-full shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
};
