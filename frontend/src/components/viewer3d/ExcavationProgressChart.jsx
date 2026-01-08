/**
 * ExcavationProgressChart.jsx
 * 
 * Cumulative excavation volume progress chart.
 */

import React, { useState, useMemo } from 'react';
import {
    TrendingUp,
    Calendar,
    Target,
    RefreshCw
} from 'lucide-react';

const ExcavationProgressChart = ({
    progressData = [],
    targetVolume,
    onRefresh,
    isLoading = false,
    className = ''
}) => {
    const [timeRange, setTimeRange] = useState('all'); // all, 30d, 90d, ytd

    // Filter data by time range
    const filteredData = useMemo(() => {
        if (timeRange === 'all') return progressData;

        const now = new Date();
        let cutoff;

        switch (timeRange) {
            case '30d':
                cutoff = new Date(now.setDate(now.getDate() - 30));
                break;
            case '90d':
                cutoff = new Date(now.setDate(now.getDate() - 90));
                break;
            case 'ytd':
                cutoff = new Date(now.getFullYear(), 0, 1);
                break;
            default:
                return progressData;
        }

        return progressData.filter(d => new Date(d.period_date) >= cutoff);
    }, [progressData, timeRange]);

    // Calculate chart dimensions
    const chartWidth = 600;
    const chartHeight = 200;
    const padding = { top: 20, right: 60, bottom: 40, left: 60 };

    const innerWidth = chartWidth - padding.left - padding.right;
    const innerHeight = chartHeight - padding.top - padding.bottom;

    // Calculate scales
    const { xScale, yScale, maxVolume } = useMemo(() => {
        if (filteredData.length === 0) {
            return { xScale: () => 0, yScale: () => 0, maxVolume: 0 };
        }

        const dates = filteredData.map(d => new Date(d.period_date).getTime());
        const minDate = Math.min(...dates);
        const maxDate = Math.max(...dates);

        const volumes = filteredData.map(d => d.cumulative_cut_bcm || 0);
        const max = Math.max(...volumes, targetVolume || 0);

        return {
            xScale: (date) => {
                const time = new Date(date).getTime();
                return ((time - minDate) / (maxDate - minDate || 1)) * innerWidth;
            },
            yScale: (vol) => innerHeight - (vol / (max || 1)) * innerHeight,
            maxVolume: max
        };
    }, [filteredData, targetVolume, innerWidth, innerHeight]);

    // Generate path
    const linePath = useMemo(() => {
        if (filteredData.length === 0) return '';

        return filteredData.map((d, i) => {
            const x = xScale(d.period_date);
            const y = yScale(d.cumulative_cut_bcm || 0);
            return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
        }).join(' ');
    }, [filteredData, xScale, yScale]);

    // Area path
    const areaPath = useMemo(() => {
        if (!linePath) return '';
        return `${linePath} L ${xScale(filteredData[filteredData.length - 1]?.period_date)} ${innerHeight} L ${xScale(filteredData[0]?.period_date)} ${innerHeight} Z`;
    }, [linePath, filteredData, xScale, innerHeight]);

    // Summary stats
    const summary = useMemo(() => {
        if (filteredData.length === 0) {
            return { current: 0, percent: 0, remaining: targetVolume || 0, daily: 0 };
        }

        const latest = filteredData[filteredData.length - 1];
        const current = latest?.cumulative_cut_bcm || 0;
        const remaining = targetVolume ? targetVolume - current : 0;
        const percent = targetVolume ? (current / targetVolume) * 100 : 0;

        // Average daily rate
        const dayCount = filteredData.length;
        const daily = dayCount > 0 ? current / dayCount : 0;

        return { current, percent, remaining, daily };
    }, [filteredData, targetVolume]);

    const formatVolume = (val) => {
        if (val >= 1000000) return `${(val / 1000000).toFixed(2)}M`;
        if (val >= 1000) return `${(val / 1000).toFixed(0)}K`;
        return val.toFixed(0);
    };

    return (
        <div className={`excavation-progress-chart ${className}`}>
            {/* Header */}
            <div className="chart-header">
                <div className="header-left">
                    <TrendingUp size={18} />
                    <h4>Excavation Progress</h4>
                </div>
                <div className="header-right">
                    <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
                        <option value="all">All Time</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="90d">Last 90 Days</option>
                        <option value="ytd">Year to Date</option>
                    </select>
                    <button onClick={onRefresh} disabled={isLoading} className="refresh-btn">
                        <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="summary-cards">
                <div className="summary-card">
                    <span className="card-value">{formatVolume(summary.current)}</span>
                    <span className="card-label">Total Excavated (BCM)</span>
                </div>
                {targetVolume && (
                    <>
                        <div className="summary-card progress">
                            <span className="card-value">{summary.percent.toFixed(1)}%</span>
                            <span className="card-label">Complete</span>
                        </div>
                        <div className="summary-card remaining">
                            <span className="card-value">{formatVolume(summary.remaining)}</span>
                            <span className="card-label">Remaining (BCM)</span>
                        </div>
                    </>
                )}
                <div className="summary-card rate">
                    <span className="card-value">{formatVolume(summary.daily)}</span>
                    <span className="card-label">Avg Daily (BCM)</span>
                </div>
            </div>

            {/* Progress Bar */}
            {targetVolume && (
                <div className="progress-bar-container">
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${Math.min(summary.percent, 100)}%` }}
                        />
                    </div>
                    <div className="progress-labels">
                        <span>0</span>
                        <span className="target-label">
                            <Target size={10} /> {formatVolume(targetVolume)} BCM
                        </span>
                    </div>
                </div>
            )}

            {/* Chart */}
            <div className="chart-container">
                <svg width={chartWidth} height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`}>
                    <defs>
                        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#22c55e" stopOpacity="0.05" />
                        </linearGradient>
                    </defs>

                    <g transform={`translate(${padding.left}, ${padding.top})`}>
                        {/* Grid lines */}
                        {[0, 0.25, 0.5, 0.75, 1].map(pct => (
                            <g key={pct}>
                                <line
                                    x1={0}
                                    y1={pct * innerHeight}
                                    x2={innerWidth}
                                    y2={pct * innerHeight}
                                    stroke="rgba(255,255,255,0.05)"
                                />
                                <text
                                    x={-8}
                                    y={pct * innerHeight + 4}
                                    textAnchor="end"
                                    fill="#666"
                                    fontSize="10"
                                >
                                    {formatVolume(maxVolume * (1 - pct))}
                                </text>
                            </g>
                        ))}

                        {/* Target line */}
                        {targetVolume && (
                            <g>
                                <line
                                    x1={0}
                                    y1={yScale(targetVolume)}
                                    x2={innerWidth}
                                    y2={yScale(targetVolume)}
                                    stroke="#f97316"
                                    strokeDasharray="4,4"
                                    strokeWidth={2}
                                />
                                <text
                                    x={innerWidth + 4}
                                    y={yScale(targetVolume) + 4}
                                    fill="#f97316"
                                    fontSize="10"
                                >
                                    Target
                                </text>
                            </g>
                        )}

                        {/* Area */}
                        <path d={areaPath} fill="url(#areaGradient)" />

                        {/* Line */}
                        <path
                            d={linePath}
                            fill="none"
                            stroke="#22c55e"
                            strokeWidth={2}
                        />

                        {/* Data points */}
                        {filteredData.map((d, i) => (
                            <circle
                                key={i}
                                cx={xScale(d.period_date)}
                                cy={yScale(d.cumulative_cut_bcm || 0)}
                                r={3}
                                fill="#22c55e"
                                stroke="#fff"
                                strokeWidth={1}
                            >
                                <title>
                                    {new Date(d.period_date).toLocaleDateString()}: {formatVolume(d.cumulative_cut_bcm || 0)} BCM
                                </title>
                            </circle>
                        ))}
                    </g>
                </svg>
            </div>

            {/* Legend */}
            <div className="chart-legend">
                <div className="legend-item">
                    <span className="legend-line cumulative" />
                    <span>Cumulative Volume</span>
                </div>
                {targetVolume && (
                    <div className="legend-item">
                        <span className="legend-line target" />
                        <span>Target</span>
                    </div>
                )}
            </div>

            <style jsx>{`
        .excavation-progress-chart {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #fff;
        }
        
        .header-left h4 { margin: 0; font-size: 14px; }
        
        .header-right { display: flex; gap: 8px; }
        
        .header-right select {
          padding: 6px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
        }
        
        .refresh-btn {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        .summary-cards {
          display: flex;
          gap: 12px;
          padding: 12px 16px;
        }
        
        .summary-card {
          flex: 1;
          padding: 10px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          text-align: center;
        }
        
        .card-value {
          display: block;
          font-size: 20px;
          font-weight: 600;
          color: #fff;
        }
        
        .card-label {
          font-size: 10px;
          color: #888;
        }
        
        .summary-card.progress { border-left: 3px solid #22c55e; }
        .summary-card.remaining { border-left: 3px solid #f97316; }
        .summary-card.rate { border-left: 3px solid #3b82f6; }
        
        .progress-bar-container {
          padding: 0 16px 12px;
        }
        
        .progress-bar {
          height: 8px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          border-radius: 4px;
          transition: width 0.5s ease;
        }
        
        .progress-labels {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          color: #888;
          margin-top: 4px;
        }
        
        .target-label {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #f97316;
        }
        
        .chart-container {
          padding: 0 16px;
          overflow: hidden;
        }
        
        .chart-container svg {
          display: block;
          max-width: 100%;
          height: auto;
        }
        
        .chart-legend {
          display: flex;
          gap: 16px;
          padding: 12px 16px;
          justify-content: center;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #aaa;
        }
        
        .legend-line {
          width: 20px;
          height: 3px;
          border-radius: 2px;
        }
        
        .legend-line.cumulative { background: #22c55e; }
        .legend-line.target { 
          background: #f97316; 
          border-style: dashed;
        }
      `}</style>
        </div>
    );
};

export default ExcavationProgressChart;
