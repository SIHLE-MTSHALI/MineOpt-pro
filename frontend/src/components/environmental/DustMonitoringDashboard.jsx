/**
 * DustMonitoringDashboard.jsx
 * 
 * Environmental dust monitoring visualization.
 */

import React, { useState, useMemo } from 'react';
import {
    Wind,
    AlertTriangle,
    RefreshCw,
    Calendar,
    TrendingUp
} from 'lucide-react';

const DustMonitoringDashboard = ({
    monitors = [],
    readings = [],
    exceedances = [],
    onRefresh,
    isLoading = false,
    className = ''
}) => {
    const [selectedMonitor, setSelectedMonitor] = useState(null);
    const [timeRange, setTimeRange] = useState('24h');

    // Current readings per monitor
    const currentReadings = useMemo(() => {
        const latest = new Map();
        readings.forEach(r => {
            const existing = latest.get(r.monitorId);
            if (!existing || new Date(r.measuredAt) > new Date(existing.measuredAt)) {
                latest.set(r.monitorId, r);
            }
        });
        return latest;
    }, [readings]);

    // Calculate stats
    const stats = useMemo(() => {
        const pm10Values = readings.map(r => r.pm10).filter(Boolean);
        const pm25Values = readings.map(r => r.pm25).filter(Boolean);

        return {
            avgPm10: pm10Values.length > 0 ? pm10Values.reduce((a, b) => a + b, 0) / pm10Values.length : 0,
            maxPm10: pm10Values.length > 0 ? Math.max(...pm10Values) : 0,
            avgPm25: pm25Values.length > 0 ? pm25Values.reduce((a, b) => a + b, 0) / pm25Values.length : 0,
            maxPm25: pm25Values.length > 0 ? Math.max(...pm25Values) : 0,
            exceedanceCount: exceedances.length
        };
    }, [readings, exceedances]);

    const getPm10Color = (value) => {
        if (value > 100) return '#ef4444';
        if (value > 50) return '#f97316';
        if (value > 25) return '#eab308';
        return '#22c55e';
    };

    const getPm25Color = (value) => {
        if (value > 50) return '#ef4444';
        if (value > 25) return '#f97316';
        if (value > 12) return '#eab308';
        return '#22c55e';
    };

    return (
        <div className={`dust-monitoring-dashboard ${className}`}>
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-left">
                    <Wind size={20} />
                    <h3>Dust Monitoring</h3>
                </div>
                <div className="header-right">
                    <select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value)}
                    >
                        <option value="1h">Last Hour</option>
                        <option value="24h">Last 24 Hours</option>
                        <option value="7d">Last 7 Days</option>
                    </select>
                    <button onClick={onRefresh} disabled={isLoading} className="refresh-btn">
                        <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="stats-row">
                <div className="stat-card">
                    <span className="stat-label">Avg PM10</span>
                    <span className="stat-value" style={{ color: getPm10Color(stats.avgPm10) }}>
                        {stats.avgPm10.toFixed(1)}
                    </span>
                    <span className="stat-unit">µg/m³</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Max PM10</span>
                    <span className="stat-value" style={{ color: getPm10Color(stats.maxPm10) }}>
                        {stats.maxPm10.toFixed(1)}
                    </span>
                    <span className="stat-unit">µg/m³</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Avg PM2.5</span>
                    <span className="stat-value" style={{ color: getPm25Color(stats.avgPm25) }}>
                        {stats.avgPm25.toFixed(1)}
                    </span>
                    <span className="stat-unit">µg/m³</span>
                </div>
                <div className="stat-card exceedances">
                    <AlertTriangle size={16} />
                    <span className="stat-value">{stats.exceedanceCount}</span>
                    <span className="stat-label">Exceedances</span>
                </div>
            </div>

            {/* Monitor Cards */}
            <div className="monitors-grid">
                {monitors.map(monitor => {
                    const reading = currentReadings.get(monitor.monitorId);
                    const hasExceedance = reading?.pm10Exceeded || reading?.pm25Exceeded;

                    return (
                        <div
                            key={monitor.monitorId}
                            className={`monitor-card ${hasExceedance ? 'exceeding' : ''} ${selectedMonitor === monitor.monitorId ? 'selected' : ''}`}
                            onClick={() => setSelectedMonitor(
                                selectedMonitor === monitor.monitorId ? null : monitor.monitorId
                            )}
                        >
                            <div className="monitor-header">
                                <span className="monitor-name">{monitor.name}</span>
                                {hasExceedance && <AlertTriangle size={14} className="alert-icon" />}
                            </div>

                            <div className="readings">
                                <div className="reading-item">
                                    <span className="reading-label">PM10</span>
                                    <div className="reading-gauge">
                                        <div
                                            className="gauge-fill"
                                            style={{
                                                width: `${Math.min((reading?.pm10 || 0) / 100 * 100, 100)}%`,
                                                backgroundColor: getPm10Color(reading?.pm10 || 0)
                                            }}
                                        />
                                    </div>
                                    <span
                                        className="reading-value"
                                        style={{ color: getPm10Color(reading?.pm10 || 0) }}
                                    >
                                        {reading?.pm10?.toFixed(1) || '--'}
                                    </span>
                                </div>

                                <div className="reading-item">
                                    <span className="reading-label">PM2.5</span>
                                    <div className="reading-gauge">
                                        <div
                                            className="gauge-fill"
                                            style={{
                                                width: `${Math.min((reading?.pm25 || 0) / 50 * 100, 100)}%`,
                                                backgroundColor: getPm25Color(reading?.pm25 || 0)
                                            }}
                                        />
                                    </div>
                                    <span
                                        className="reading-value"
                                        style={{ color: getPm25Color(reading?.pm25 || 0) }}
                                    >
                                        {reading?.pm25?.toFixed(1) || '--'}
                                    </span>
                                </div>
                            </div>

                            {reading && (
                                <div className="weather-info">
                                    <span>Wind: {reading.windSpeed?.toFixed(0) || '--'} km/h {reading.windDirection || ''}</span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Exceedance Log */}
            {exceedances.length > 0 && (
                <div className="exceedance-log">
                    <h4><AlertTriangle size={14} /> Recent Exceedances</h4>
                    <div className="log-list">
                        {exceedances.slice(0, 5).map((ex, i) => (
                            <div key={i} className="log-item">
                                <span className="log-time">{new Date(ex.measuredAt).toLocaleString()}</span>
                                <span className="log-type">
                                    {ex.pm10Exceeded && <span className="badge pm10">PM10: {ex.pm10?.toFixed(1)}</span>}
                                    {ex.pm25Exceeded && <span className="badge pm25">PM2.5: {ex.pm25?.toFixed(1)}</span>}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="legend">
                <span className="legend-title">Air Quality:</span>
                <div className="legend-item"><span className="dot good" />Good</div>
                <div className="legend-item"><span className="dot moderate" />Moderate</div>
                <div className="legend-item"><span className="dot unhealthy" />Unhealthy</div>
                <div className="legend-item"><span className="dot hazardous" />Hazardous</div>
            </div>

            <style jsx>{`
        .dust-monitoring-dashboard {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #fff;
        }
        
        .header-left h3 { margin: 0; font-size: 16px; }
        
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
        
        .stats-row {
          display: flex;
          gap: 12px;
          padding: 16px;
        }
        
        .stat-card {
          flex: 1;
          padding: 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          text-align: center;
        }
        
        .stat-label {
          display: block;
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
        }
        
        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 600;
        }
        
        .stat-unit {
          font-size: 10px;
          color: #666;
        }
        
        .stat-card.exceedances {
          background: rgba(239,68,68,0.1);
          border: 1px solid rgba(239,68,68,0.3);
          color: #ef4444;
        }
        
        .monitors-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 12px;
          padding: 0 16px 16px;
        }
        
        .monitor-card {
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          border: 1px solid transparent;
        }
        
        .monitor-card:hover { background: rgba(255,255,255,0.05); }
        .monitor-card.selected { border-color: #3b82f6; }
        .monitor-card.exceeding { border-color: rgba(239,68,68,0.5); }
        
        .monitor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        
        .monitor-name {
          font-weight: 600;
          color: #fff;
        }
        
        .alert-icon { color: #ef4444; }
        
        .reading-item {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .reading-label {
          width: 50px;
          font-size: 11px;
          color: #888;
        }
        
        .reading-gauge {
          flex: 1;
          height: 8px;
          background: rgba(255,255,255,0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .gauge-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }
        
        .reading-value {
          width: 40px;
          text-align: right;
          font-weight: 600;
          font-size: 13px;
        }
        
        .weather-info {
          font-size: 10px;
          color: #666;
          margin-top: 8px;
        }
        
        .exceedance-log {
          margin: 0 16px 16px;
          padding: 12px;
          background: rgba(239,68,68,0.1);
          border-radius: 8px;
        }
        
        .exceedance-log h4 {
          display: flex;
          align-items: center;
          gap: 6px;
          margin: 0 0 10px;
          font-size: 12px;
          color: #ef4444;
        }
        
        .log-item {
          display: flex;
          justify-content: space-between;
          padding: 6px 0;
          font-size: 11px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .log-time { color: #888; }
        
        .badge {
          padding: 2px 6px;
          border-radius: 3px;
          margin-left: 4px;
        }
        
        .badge.pm10 { background: rgba(239,68,68,0.2); color: #ef4444; }
        .badge.pm25 { background: rgba(249,115,22,0.2); color: #f97316; }
        
        .legend {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px 16px;
          background: rgba(0,0,0,0.2);
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .legend-title { font-size: 11px; color: #888; }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 10px;
          color: #aaa;
        }
        
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        
        .dot.good { background: #22c55e; }
        .dot.moderate { background: #eab308; }
        .dot.unhealthy { background: #f97316; }
        .dot.hazardous { background: #ef4444; }
      `}</style>
        </div>
    );
};

export default DustMonitoringDashboard;
