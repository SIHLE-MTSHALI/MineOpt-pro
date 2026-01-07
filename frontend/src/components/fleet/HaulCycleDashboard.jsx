/**
 * HaulCycleDashboard.jsx
 * 
 * Dashboard for haul cycle analytics with KPIs and charts.
 */

import React, { useState, useMemo } from 'react';
import {
    Truck,
    Clock,
    TrendingUp,
    BarChart2,
    RefreshCw,
    Calendar,
    Download,
    ChevronDown
} from 'lucide-react';

const HaulCycleDashboard = ({
    statistics,
    cyclesByEquipment = [],
    dateRange,
    onDateRangeChange,
    onRefresh,
    isLoading = false,
    className = ''
}) => {
    const [selectedView, setSelectedView] = useState('overview');

    // Calculate cycle breakdown percentages
    const cycleBreakdown = useMemo(() => {
        if (!statistics) return null;

        const total = statistics.avg_cycle_time_min || 1;
        return {
            loading: (statistics.avg_loading_min / total) * 100,
            travel_loaded: (statistics.avg_travel_loaded_min / total) * 100,
            dumping: (statistics.avg_dumping_min / total) * 100,
            travel_empty: (statistics.avg_travel_empty_min / total) * 100
        };
    }, [statistics]);

    const formatTime = (minutes) => {
        if (minutes < 60) return `${minutes.toFixed(1)} min`;
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return `${hours}h ${mins}m`;
    };

    return (
        <div className={`haul-cycle-dashboard ${className}`}>
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-left">
                    <h2>
                        <Truck size={20} />
                        Haul Cycle Analytics
                    </h2>
                </div>

                <div className="header-right">
                    <div className="date-selector">
                        <Calendar size={14} />
                        <select
                            value={dateRange}
                            onChange={(e) => onDateRangeChange?.(e.target.value)}
                        >
                            <option value="today">Today</option>
                            <option value="yesterday">Yesterday</option>
                            <option value="7days">Last 7 Days</option>
                            <option value="30days">Last 30 Days</option>
                        </select>
                    </div>

                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                        disabled={isLoading}
                    >
                        <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <div className="kpi-icon" style={{ background: 'rgba(34, 197, 94, 0.15)' }}>
                        <TrendingUp size={20} color="#22c55e" />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-value">{statistics?.total_cycles || 0}</span>
                        <span className="kpi-label">Total Cycles</span>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon" style={{ background: 'rgba(59, 130, 246, 0.15)' }}>
                        <Truck size={20} color="#3b82f6" />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-value">
                            {(statistics?.total_tonnes || 0).toLocaleString()}
                        </span>
                        <span className="kpi-label">Total Tonnes</span>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon" style={{ background: 'rgba(168, 85, 247, 0.15)' }}>
                        <Clock size={20} color="#a855f7" />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-value">
                            {formatTime(statistics?.avg_cycle_time_min || 0)}
                        </span>
                        <span className="kpi-label">Avg Cycle Time</span>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="kpi-icon" style={{ background: 'rgba(249, 115, 22, 0.15)' }}>
                        <BarChart2 size={20} color="#f97316" />
                    </div>
                    <div className="kpi-content">
                        <span className="kpi-value">
                            {(statistics?.productivity_tph || 0).toFixed(0)}
                        </span>
                        <span className="kpi-label">Productivity (t/hr)</span>
                    </div>
                </div>
            </div>

            {/* Cycle Breakdown */}
            {cycleBreakdown && (
                <div className="breakdown-section">
                    <h3>Average Cycle Breakdown</h3>

                    <div className="breakdown-bar">
                        <div
                            className="breakdown-segment loading"
                            style={{ width: `${cycleBreakdown.loading}%` }}
                            title={`Loading: ${statistics?.avg_loading_min?.toFixed(1)} min`}
                        />
                        <div
                            className="breakdown-segment travel-loaded"
                            style={{ width: `${cycleBreakdown.travel_loaded}%` }}
                            title={`Travel Loaded: ${statistics?.avg_travel_loaded_min?.toFixed(1)} min`}
                        />
                        <div
                            className="breakdown-segment dumping"
                            style={{ width: `${cycleBreakdown.dumping}%` }}
                            title={`Dumping: ${statistics?.avg_dumping_min?.toFixed(1)} min`}
                        />
                        <div
                            className="breakdown-segment travel-empty"
                            style={{ width: `${cycleBreakdown.travel_empty}%` }}
                            title={`Travel Empty: ${statistics?.avg_travel_empty_min?.toFixed(1)} min`}
                        />
                    </div>

                    <div className="breakdown-legend">
                        <div className="legend-item">
                            <span className="dot loading" />
                            <span>Loading ({statistics?.avg_loading_min?.toFixed(1)} min)</span>
                        </div>
                        <div className="legend-item">
                            <span className="dot travel-loaded" />
                            <span>Travel Loaded ({statistics?.avg_travel_loaded_min?.toFixed(1)} min)</span>
                        </div>
                        <div className="legend-item">
                            <span className="dot dumping" />
                            <span>Dumping ({statistics?.avg_dumping_min?.toFixed(1)} min)</span>
                        </div>
                        <div className="legend-item">
                            <span className="dot travel-empty" />
                            <span>Travel Empty ({statistics?.avg_travel_empty_min?.toFixed(1)} min)</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Equipment Performance Table */}
            <div className="performance-section">
                <h3>Equipment Performance</h3>

                <table className="performance-table">
                    <thead>
                        <tr>
                            <th>Fleet #</th>
                            <th>Cycles</th>
                            <th>Tonnes</th>
                            <th>Avg Cycle</th>
                            <th>Utilization</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cyclesByEquipment.map((eq) => (
                            <tr key={eq.equipment_id}>
                                <td className="fleet-cell">{eq.fleet_number}</td>
                                <td>{eq.cycle_count}</td>
                                <td>{eq.total_tonnes?.toLocaleString()}</td>
                                <td>{formatTime(eq.avg_cycle_min)}</td>
                                <td>
                                    <div className="utilization-bar">
                                        <div
                                            className="utilization-fill"
                                            style={{ width: `${eq.utilization || 0}%` }}
                                        />
                                        <span>{eq.utilization?.toFixed(0)}%</span>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {cyclesByEquipment.length === 0 && (
                            <tr>
                                <td colSpan={5} className="empty-row">
                                    No cycle data available
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style jsx>{`
        .haul-cycle-dashboard {
          background: linear-gradient(145deg, #1a1a2e, #1e1e30);
          border-radius: 12px;
          padding: 20px;
        }
        
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .dashboard-header h2 {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 18px;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }
        
        .header-right {
          display: flex;
          gap: 10px;
        }
        
        .date-selector {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #aaa;
        }
        
        .date-selector select {
          background: transparent;
          border: none;
          color: #fff;
          font-size: 13px;
          cursor: pointer;
        }
        
        .refresh-btn {
          padding: 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #aaa;
          cursor: pointer;
        }
        
        .refresh-btn:hover {
          background: rgba(255,255,255,0.1);
        }
        
        .spinning {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .kpi-card {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 16px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 10px;
        }
        
        .kpi-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 10px;
        }
        
        .kpi-content {
          display: flex;
          flex-direction: column;
        }
        
        .kpi-value {
          font-size: 22px;
          font-weight: 600;
          color: #fff;
        }
        
        .kpi-label {
          font-size: 12px;
          color: #888;
        }
        
        .breakdown-section {
          background: rgba(0,0,0,0.2);
          border-radius: 10px;
          padding: 16px;
          margin-bottom: 20px;
        }
        
        .breakdown-section h3 {
          font-size: 14px;
          font-weight: 500;
          color: #ccc;
          margin: 0 0 14px 0;
        }
        
        .breakdown-bar {
          display: flex;
          height: 24px;
          border-radius: 6px;
          overflow: hidden;
          margin-bottom: 12px;
        }
        
        .breakdown-segment {
          height: 100%;
          transition: width 0.3s ease;
        }
        
        .breakdown-segment.loading { background: #22c55e; }
        .breakdown-segment.travel-loaded { background: #3b82f6; }
        .breakdown-segment.dumping { background: #f97316; }
        .breakdown-segment.travel-empty { background: #a855f7; }
        
        .breakdown-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #aaa;
        }
        
        .dot {
          width: 10px;
          height: 10px;
          border-radius: 2px;
        }
        
        .dot.loading { background: #22c55e; }
        .dot.travel-loaded { background: #3b82f6; }
        .dot.dumping { background: #f97316; }
        .dot.travel-empty { background: #a855f7; }
        
        .performance-section h3 {
          font-size: 14px;
          font-weight: 500;
          color: #ccc;
          margin: 0 0 12px 0;
        }
        
        .performance-table {
          width: 100%;
          border-collapse: collapse;
        }
        
        .performance-table th {
          text-align: left;
          padding: 10px 12px;
          font-size: 11px;
          font-weight: 500;
          color: #888;
          text-transform: uppercase;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .performance-table td {
          padding: 12px;
          font-size: 13px;
          color: #ccc;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .fleet-cell {
          font-weight: 600;
          color: #fff;
        }
        
        .utilization-bar {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .utilization-fill {
          height: 6px;
          background: linear-gradient(90deg, #22c55e, #3b82f6);
          border-radius: 3px;
          min-width: 4px;
        }
        
        .utilization-bar span {
          font-size: 12px;
          color: #888;
        }
        
        .empty-row {
          text-align: center;
          color: #666;
          padding: 24px !important;
        }
        
        @media (max-width: 768px) {
          .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
        </div>
    );
};

export default HaulCycleDashboard;
