/**
 * EquipmentHealthDashboard.jsx
 * 
 * Fleet-wide equipment health overview with ML predictions.
 */

import React, { useState, useMemo } from 'react';
import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Wrench,
    TrendingUp,
    RefreshCw,
    Filter
} from 'lucide-react';

const EquipmentHealthDashboard = ({
    equipment = [],
    healthScores = [],
    maintenanceAlerts = [],
    onRefresh,
    onEquipmentSelect,
    isLoading = false,
    className = ''
}) => {
    const [filterType, setFilterType] = useState('all');
    const [sortBy, setSortBy] = useState('risk'); // risk, name, hours

    // Combine equipment with health scores
    const equipmentWithHealth = useMemo(() => {
        return equipment.map(eq => {
            const health = healthScores.find(h => h.equipmentId === eq.equipmentId);
            return {
                ...eq,
                riskScore: health?.riskScore ?? 0,
                riskStatus: health?.status ?? 'unknown',
                recommendation: health?.recommendation ?? 'No data',
                componentIssues: health?.featureContributions ?? []
            };
        });
    }, [equipment, healthScores]);

    // Filter and sort
    const filteredEquipment = useMemo(() => {
        let filtered = equipmentWithHealth;

        if (filterType !== 'all') {
            filtered = filtered.filter(eq => eq.equipmentType === filterType);
        }

        return filtered.sort((a, b) => {
            if (sortBy === 'risk') return b.riskScore - a.riskScore;
            if (sortBy === 'name') return a.fleetNumber.localeCompare(b.fleetNumber);
            if (sortBy === 'hours') return b.engineHours - a.engineHours;
            return 0;
        });
    }, [equipmentWithHealth, filterType, sortBy]);

    // Summary stats
    const stats = useMemo(() => {
        const total = equipmentWithHealth.length;
        const critical = equipmentWithHealth.filter(e => e.riskStatus === 'critical').length;
        const high = equipmentWithHealth.filter(e => e.riskStatus === 'high').length;
        const healthy = equipmentWithHealth.filter(e => e.riskScore < 40).length;
        const avgScore = total > 0
            ? equipmentWithHealth.reduce((sum, e) => sum + e.riskScore, 0) / total
            : 0;

        return { total, critical, high, healthy, avgScore };
    }, [equipmentWithHealth]);

    const getRiskColor = (status) => {
        return {
            critical: '#ef4444',
            high: '#f97316',
            medium: '#eab308',
            low: '#22c55e',
            unknown: '#6b7280'
        }[status] || '#6b7280';
    };

    const equipmentTypes = useMemo(() => {
        const types = new Set(equipment.map(e => e.equipmentType));
        return Array.from(types);
    }, [equipment]);

    return (
        <div className={`equipment-health-dashboard ${className}`}>
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-left">
                    <Activity size={20} />
                    <h3>Equipment Health</h3>
                </div>
                <div className="header-right">
                    <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                        <option value="all">All Types</option>
                        {equipmentTypes.map(type => (
                            <option key={type} value={type}>{type}</option>
                        ))}
                    </select>
                    <button onClick={onRefresh} disabled={isLoading} className="refresh-btn">
                        <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="health-summary">
                <div className="summary-card">
                    <span className="count">{stats.total}</span>
                    <span className="label">Total Units</span>
                </div>
                <div className="summary-card healthy">
                    <CheckCircle size={16} />
                    <span className="count">{stats.healthy}</span>
                    <span className="label">Healthy</span>
                </div>
                <div className="summary-card warning">
                    <AlertTriangle size={16} />
                    <span className="count">{stats.high}</span>
                    <span className="label">High Risk</span>
                </div>
                <div className="summary-card critical">
                    <Wrench size={16} />
                    <span className="count">{stats.critical}</span>
                    <span className="label">Critical</span>
                </div>
                <div className="summary-card score">
                    <TrendingUp size={16} />
                    <span className="count">{stats.avgScore.toFixed(0)}</span>
                    <span className="label">Avg Risk Score</span>
                </div>
            </div>

            {/* Sort Options */}
            <div className="sort-bar">
                <span>Sort by:</span>
                {['risk', 'name', 'hours'].map(option => (
                    <button
                        key={option}
                        className={sortBy === option ? 'active' : ''}
                        onClick={() => setSortBy(option)}
                    >
                        {option === 'risk' ? 'Risk' : option === 'name' ? 'Name' : 'Engine Hours'}
                    </button>
                ))}
            </div>

            {/* Equipment Grid */}
            <div className="equipment-grid">
                {filteredEquipment.map(eq => (
                    <div
                        key={eq.equipmentId}
                        className={`equipment-card ${eq.riskStatus}`}
                        onClick={() => onEquipmentSelect?.(eq.equipmentId)}
                    >
                        <div className="card-header">
                            <span className="fleet-number">{eq.fleetNumber}</span>
                            <span
                                className="risk-badge"
                                style={{ backgroundColor: getRiskColor(eq.riskStatus) }}
                            >
                                {eq.riskScore}%
                            </span>
                        </div>
                        <div className="card-body">
                            <div className="info-row">
                                <span className="label">Type:</span>
                                <span className="value">{eq.equipmentType}</span>
                            </div>
                            <div className="info-row">
                                <span className="label">Hours:</span>
                                <span className="value">{eq.engineHours?.toLocaleString() || 'N/A'}</span>
                            </div>
                            <div className="info-row">
                                <span className="label">Status:</span>
                                <span className={`status ${eq.status}`}>{eq.status}</span>
                            </div>
                        </div>

                        {/* Risk meter */}
                        <div className="risk-meter">
                            <div
                                className="risk-fill"
                                style={{
                                    width: `${eq.riskScore}%`,
                                    backgroundColor: getRiskColor(eq.riskStatus)
                                }}
                            />
                        </div>

                        {/* Issues */}
                        {eq.componentIssues.length > 0 && (
                            <div className="issues">
                                {eq.componentIssues.slice(0, 2).map((issue, i) => (
                                    <div key={i} className="issue-tag">{issue.message}</div>
                                ))}
                            </div>
                        )}

                        {/* Recommendation */}
                        <div className="recommendation">{eq.recommendation}</div>
                    </div>
                ))}
            </div>

            {/* Maintenance Alerts */}
            {maintenanceAlerts.length > 0 && (
                <div className="maintenance-alerts">
                    <h4><Wrench size={14} /> Upcoming Maintenance</h4>
                    {maintenanceAlerts.slice(0, 3).map((alert, i) => (
                        <div key={i} className="alert-item">
                            <span className="fleet">{alert.fleetNumber}</span>
                            <span className="type">{alert.maintenanceType}</span>
                            <span className="due">{alert.dueDate}</span>
                        </div>
                    ))}
                </div>
            )}

            <style jsx>{`
        .equipment-health-dashboard {
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
        
        .header-right {
          display: flex;
          gap: 8px;
        }
        
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
        
        .health-summary {
          display: flex;
          gap: 12px;
          padding: 16px;
          overflow-x: auto;
        }
        
        .summary-card {
          flex: 1;
          min-width: 100px;
          padding: 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          text-align: center;
        }
        
        .summary-card .count {
          display: block;
          font-size: 24px;
          font-weight: 600;
          color: #fff;
        }
        
        .summary-card .label {
          font-size: 11px;
          color: #888;
        }
        
        .summary-card.healthy { border-left: 3px solid #22c55e; }
        .summary-card.warning { border-left: 3px solid #f97316; }
        .summary-card.critical { border-left: 3px solid #ef4444; }
        .summary-card.score { border-left: 3px solid #3b82f6; }
        
        .sort-bar {
          display: flex;
          gap: 8px;
          padding: 8px 16px;
          align-items: center;
        }
        
        .sort-bar span { font-size: 11px; color: #888; }
        
        .sort-bar button {
          padding: 4px 10px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
        }
        
        .sort-bar button.active {
          background: rgba(59,130,246,0.2);
          color: #3b82f6;
        }
        
        .equipment-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 12px;
          padding: 0 16px 16px;
        }
        
        .equipment-card {
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          border-left: 3px solid #6b7280;
          transition: background 0.2s;
        }
        
        .equipment-card:hover { background: rgba(255,255,255,0.06); }
        .equipment-card.critical { border-color: #ef4444; }
        .equipment-card.high { border-color: #f97316; }
        .equipment-card.medium { border-color: #eab308; }
        .equipment-card.low { border-color: #22c55e; }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
        }
        
        .fleet-number {
          font-weight: 600;
          font-size: 14px;
          color: #fff;
        }
        
        .risk-badge {
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 600;
          color: #fff;
        }
        
        .card-body .info-row {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          margin-bottom: 4px;
        }
        
        .info-row .label { color: #888; }
        .info-row .value { color: #ccc; }
        .info-row .status { text-transform: capitalize; }
        .info-row .status.operating { color: #22c55e; }
        .info-row .status.maintenance { color: #3b82f6; }
        .info-row .status.breakdown { color: #ef4444; }
        
        .risk-meter {
          height: 4px;
          background: rgba(255,255,255,0.1);
          border-radius: 2px;
          margin: 10px 0;
          overflow: hidden;
        }
        
        .risk-fill {
          height: 100%;
          transition: width 0.3s;
        }
        
        .issues {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 8px;
        }
        
        .issue-tag {
          font-size: 9px;
          padding: 2px 6px;
          background: rgba(239,68,68,0.2);
          color: #ef4444;
          border-radius: 3px;
        }
        
        .recommendation {
          font-size: 10px;
          color: #888;
          font-style: italic;
        }
        
        .maintenance-alerts {
          padding: 16px;
          background: rgba(59,130,246,0.1);
          border-top: 1px solid rgba(59,130,246,0.2);
        }
        
        .maintenance-alerts h4 {
          display: flex;
          align-items: center;
          gap: 6px;
          margin: 0 0 12px;
          font-size: 12px;
          color: #3b82f6;
        }
        
        .alert-item {
          display: flex;
          justify-content: space-between;
          padding: 8px;
          background: rgba(0,0,0,0.2);
          border-radius: 4px;
          margin-bottom: 4px;
          font-size: 11px;
        }
        
        .alert-item .fleet { color: #fff; font-weight: 500; }
        .alert-item .type { color: #aaa; }
        .alert-item .due { color: #3b82f6; }
      `}</style>
        </div>
    );
};

export default EquipmentHealthDashboard;
