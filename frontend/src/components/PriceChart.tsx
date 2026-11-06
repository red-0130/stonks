import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, HistogramData, Time } from 'lightweight-charts';
import { ChartBar, TradeSetup } from '../types/stock';
import { Maximize2, BarChart, TrendingUp, Layers } from 'lucide-react';

interface PriceChartProps {
  bars: ChartBar[];
  symbol: string;
  currentTimeframe: string;
  onSelectTimeframe: (tf: string) => void;
  activeSetup?: TradeSetup | null;
  isLoading: boolean;
}

const TIMEFRAMES = ['1H', '4H', '1D', '1W'];

export const PriceChart: React.FC<PriceChartProps> = ({
  bars,
  symbol,
  currentTimeframe,
  onSelectTimeframe,
  activeSetup,
  isLoading,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const lineSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const priceLineRefs = useRef<any[]>([]);

  const [chartType, setChartType] = useState<'candlestick' | 'line'>('candlestick');
  const [showVolume, setShowVolume] = useState<boolean>(true);
  const [showSetupLines, setShowSetupLines] = useState<boolean>(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize Lightweight Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#090d16' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      width: chartContainerRef.current.clientWidth,
      height: 480,
    });

    chartRef.current = chart;

    // Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeriesRef.current = candleSeries;

    // Line Series
    const lineSeries = chart.addLineSeries({
      color: '#3b82f6',
      lineWidth: 2,
      visible: false,
    });
    lineSeriesRef.current = lineSeries;

    // Volume Series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Separate scale
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });
    volumeSeriesRef.current = volumeSeries;

    // Resize observer
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // Update chart data whenever bars or chartType changes
  useEffect(() => {
    if (!chartRef.current || !bars || bars.length === 0) return;

    // Clean & sort bars
    const sortedBars = [...bars].sort((a, b) => {
      const ta = typeof a.time === 'number' ? a.time : new Date(a.time).getTime() / 1000;
      const tb = typeof b.time === 'number' ? b.time : new Date(b.time).getTime() / 1000;
      return ta - tb;
    });

    const candleData: CandlestickData<Time>[] = [];
    const lineData: LineData<Time>[] = [];
    const volumeData: HistogramData<Time>[] = [];

    // Filter duplicates
    const seenTimes = new Set();

    sortedBars.forEach((b) => {
      const timeVal = (typeof b.time === 'number' ? b.time : b.time) as Time;
      if (seenTimes.has(timeVal)) return;
      seenTimes.add(timeVal);

      candleData.push({
        time: timeVal,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      });

      lineData.push({
        time: timeVal,
        value: b.close,
      });

      volumeData.push({
        time: timeVal,
        value: b.volume,
        color: b.close >= b.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)',
      });
    });

    if (candleSeriesRef.current) {
      candleSeriesRef.current.setData(candleData);
      candleSeriesRef.current.applyOptions({ visible: chartType === 'candlestick' });
    }

    if (lineSeriesRef.current) {
      lineSeriesRef.current.setData(lineData);
      lineSeriesRef.current.applyOptions({ visible: chartType === 'line' });
    }

    if (volumeSeriesRef.current) {
      volumeSeriesRef.current.setData(volumeData);
      volumeSeriesRef.current.applyOptions({ visible: showVolume });
    }

    chartRef.current.timeScale().fitContent();
  }, [bars, chartType, showVolume]);

  // Update Setup Price Lines (Entry, Stop Loss, Take Profit)
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Remove previous setup price lines before adding new ones
    priceLineRefs.current.forEach((line) => {
      try {
        candleSeriesRef.current?.removePriceLine(line);
      } catch (e) {
        // Safe fallback
      }
    });
    priceLineRefs.current = [];

    // Draw active setup price lines
    if (
      activeSetup &&
      showSetupLines &&
      !activeSetup.no_trade &&
      activeSetup.entry_price !== null &&
      activeSetup.take_profit_price !== null &&
      activeSetup.stop_loss_price !== null
    ) {
      try {
        const entryLine = candleSeriesRef.current.createPriceLine({
          price: activeSetup.entry_price,
          color: '#3b82f6',
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: true,
          title: `ENTRY: $${activeSetup.entry_price}`,
        });

        const tpLine = candleSeriesRef.current.createPriceLine({
          price: activeSetup.take_profit_price,
          color: '#10b981',
          lineWidth: 2,
          lineStyle: 1, // Dotted
          axisLabelVisible: true,
          title: `TP (+${activeSetup.potential_gain_pct}%): $${activeSetup.take_profit_price}`,
        });

        const slLine = candleSeriesRef.current.createPriceLine({
          price: activeSetup.stop_loss_price,
          color: '#ef4444',
          lineWidth: 2,
          lineStyle: 1, // Dotted
          axisLabelVisible: true,
          title: `SL (-${activeSetup.potential_risk_pct}%): $${activeSetup.stop_loss_price}`,
        });

        priceLineRefs.current = [entryLine, tpLine, slLine];
      } catch (e) {
        // Safe fallback
      }
    }
  }, [activeSetup, showSetupLines]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col">
      {/* Chart Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between p-3.5 border-b border-slate-800 bg-slate-950/60 gap-3">
        {/* Timeframe Buttons */}
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => onSelectTimeframe(tf)}
              disabled={isLoading}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition ${
                currentTimeframe === tf
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Chart View Controls */}
        <div className="flex items-center gap-2">
          {/* Candlestick / Line toggle */}
          <div className="flex items-center bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setChartType('candlestick')}
              className={`px-2.5 py-1 rounded transition ${
                chartType === 'candlestick' ? 'bg-slate-700 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Candles
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`px-2.5 py-1 rounded transition ${
                chartType === 'line' ? 'bg-slate-700 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Line
            </button>
          </div>

          {/* Volume Toggle */}
          <button
            onClick={() => setShowVolume(!showVolume)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium transition ${
              showVolume
                ? 'bg-slate-800 text-slate-200 border-slate-700'
                : 'bg-transparent text-slate-500 border-slate-800 hover:text-slate-400'
            }`}
          >
            Volume
          </button>

          {/* Setup Lines Toggle if setup exists */}
          {activeSetup && (
            <button
              onClick={() => setShowSetupLines(!showSetupLines)}
              className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium transition flex items-center gap-1.5 ${
                showSetupLines
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-transparent text-slate-500 border-slate-800 hover:text-slate-400'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Setup Overlay
            </button>
          )}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="relative w-full h-[480px]">
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm z-20 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs text-slate-400 mt-2 font-mono">Loading market bars for {symbol}...</span>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>

      {/* Footer info legend */}
      <div className="px-4 py-2 bg-slate-950 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-3">
          <span>
            Symbol: <strong className="text-slate-200 font-mono">{symbol}</strong>
          </span>
          <span>
            Timeframe: <strong className="text-slate-200 font-mono">{currentTimeframe}</strong>
          </span>
          <span>
            Bars: <strong className="text-slate-200 font-mono">{bars.length}</strong>
          </span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> Bullish Candle
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span> Bearish Candle
          </span>
          {activeSetup && showSetupLines && (
            <>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-blue-500"></span> Entry
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-emerald-500"></span> Take Profit
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-rose-500"></span> Stop Loss
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
