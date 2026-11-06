import React from 'react';
import { MarketSentiment } from '../types/stock';
import { Newspaper, Users, ExternalLink, ThumbsUp, ThumbsDown, MessageSquare } from 'lucide-react';

interface SentimentSectionProps {
  sentiment: MarketSentiment;
}

export const SentimentSection: React.FC<SentimentSectionProps> = ({ sentiment }) => {
  const { sentiment_score, overall_sentiment, counts, analyst_consensus, news } = sentiment;

  // Normalized score: 0 to 100 for progress meter (score goes from -100 to +100)
  const normalizedMeter = Math.max(0, Math.min(100, (sentiment_score + 100) / 2));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Market Sentiment & News NLP</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time headline NLP sentiment analysis combined with Wall Street analyst consensus.
          </p>
        </div>

        {/* Overall Sentiment Badge */}
        <div className="flex items-center gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-medium">
              Sentiment Index
            </span>
            <span className="text-base font-extrabold text-white">{overall_sentiment}</span>
          </div>
          <span className="text-lg font-mono font-extrabold text-emerald-400">
            {sentiment_score >= 0 ? '+' : ''}
            {sentiment_score.toFixed(0)}
          </span>
        </div>
      </div>

      {/* Sentiment Gauge Bar */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
        <div className="flex justify-between items-center text-xs mb-2">
          <span className="text-rose-400 font-semibold flex items-center gap-1">
            <ThumbsDown className="w-3.5 h-3.5" /> Bearish (-100)
          </span>
          <span className="text-slate-400 font-mono">Neutral (0)</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            Bullish (+100) <ThumbsUp className="w-3.5 h-3.5" />
          </span>
        </div>
        <div className="relative w-full h-3 bg-slate-800 rounded-full overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-500 opacity-60" />
          <div
            className="absolute top-0 bottom-0 w-3 bg-white border border-slate-900 rounded-full shadow-lg -translate-x-1/2 transition-all duration-500"
            style={{ left: `${normalizedMeter}%` }}
          />
        </div>
        <div className="flex justify-between items-center text-[11px] text-slate-400 mt-2 font-mono">
          <span>{counts.bearish} Bearish Articles</span>
          <span>{counts.neutral} Neutral</span>
          <span>{counts.bullish} Bullish Articles</span>
        </div>
      </div>

      {/* Analyst Consensus Box */}
      {analyst_consensus && (
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Wall Street Analyst Consensus
              </h3>
            </div>
            <span className="text-xs text-slate-400">
              {analyst_consensus.analyst_count} Analyst Opinions
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-0.5">Recommendation</span>
              <span className="text-sm font-extrabold text-white">
                {analyst_consensus.recommendation}
              </span>
            </div>

            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-0.5">Average Target</span>
              <span className="text-sm font-extrabold text-emerald-300 font-mono">
                {analyst_consensus.target_mean ? `$${analyst_consensus.target_mean}` : 'N/A'}
              </span>
            </div>

            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-0.5">Implied Upside</span>
              <span className="text-sm font-extrabold text-emerald-400 font-mono">
                {analyst_consensus.implied_upside_percent
                  ? `${analyst_consensus.implied_upside_percent > 0 ? '+' : ''}${
                      analyst_consensus.implied_upside_percent
                    }%`
                  : 'N/A'}
              </span>
            </div>

            <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg">
              <span className="text-slate-400 block mb-0.5">Target Range</span>
              <span className="text-xs font-semibold text-slate-300 font-mono block truncate">
                {analyst_consensus.target_low ? `$${analyst_consensus.target_low} - $${analyst_consensus.target_high}` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tagged News Articles */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Newspaper className="w-4 h-4 text-slate-400" />
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Recent News Headlines & NLP Sentiment
          </h3>
        </div>

        <div className="space-y-2.5">
          {news.map((item, idx) => (
            <div
              key={idx}
              className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
            >
              <div className="flex-1">
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-slate-200 hover:text-emerald-400 transition flex items-center gap-1.5"
                >
                  <span>{item.title}</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 shrink-0" />
                </a>
                <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                  <span>{item.publisher}</span>
                  <span>•</span>
                  <span>{item.published}</span>
                </div>
              </div>

              {/* Sentiment Pill */}
              <div className="shrink-0 flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    item.sentiment === 'Bullish'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : item.sentiment === 'Bearish'
                      ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {item.sentiment}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {item.score >= 0 ? '+' : ''}
                  {item.score}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
