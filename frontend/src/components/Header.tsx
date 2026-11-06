import React, { useState } from 'react';
import { Search, TrendingUp, RefreshCw } from 'lucide-react';

interface HeaderProps {
  currentTicker: string;
  onSelectTicker: (ticker: string) => void;
  isLoading: boolean;
  onRefresh: () => void;
}

const POPULAR_TICKERS = ['AAPL', 'NVDA', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META', 'SPY'];

export const Header: React.FC<HeaderProps> = ({
  currentTicker,
  onSelectTicker,
  isLoading,
  onRefresh,
}) => {
  const [searchInput, setSearchInput] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = searchInput.trim().toUpperCase();
    if (clean) {
      onSelectTicker(clean);
      setSearchInput('');
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-black tracking-tight text-white">STONKS</span>
                <span className="text-xs px-2 py-0.5 font-bold uppercase rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  v2.0
                </span>
              </div>
              <p className="text-xs text-slate-400">Next-Gen Quantitative Stock Intelligence</p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="w-full md:w-auto flex-1 max-w-md">
            <form onSubmit={handleSearch} className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search symbol (e.g. AAPL, NVDA)..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-10 pr-24 py-2 bg-slate-950/80 border border-slate-700/80 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500 uppercase font-mono transition-all"
              />
              <button
                type="submit"
                disabled={!searchInput.trim()}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white rounded text-xs font-semibold transition"
              >
                Analyze
              </button>
            </form>
          </div>

          {/* Refresh Action */}
          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh live data"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-300 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Popular Tickers Quick Bar */}
        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-800/60 overflow-x-auto text-xs">
          <span className="text-slate-400 shrink-0 font-medium">Quick Tickers:</span>
          {POPULAR_TICKERS.map((t) => (
            <button
              key={t}
              onClick={() => onSelectTicker(t)}
              className={`px-2.5 py-1 rounded font-mono font-medium transition ${
                currentTicker === t
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-700/40'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};
