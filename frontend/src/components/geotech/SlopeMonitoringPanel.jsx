/**
 * SlopeMonitoringPanel.jsx
 * 
 * Geotechnical slope monitoring dashboard.
 */

import React, { useState, useMemo } from 'react';
import {
    Mountain,
    AlertTriangle,
    Activity,
    TrendingUp,
    RefreshCw,
    Filter,
    ChevronRight
} from 'lucide-react';

const SlopeMonitoringPanel = ({
    prisms = [],
    domains = [],
    selectedPrismId,
    onSelectPrism,
    onRefresh,
    isLoading = false,
    className = ''
}) => {
    const [filterStatus, setFilterStatus] = useState('all');
    const [selectedDomain, setSelectedDomain] = useState(null);

    // Filter prisms
    const filteredPrisms = useMemo(() => {
        return prisms.filter(p => {
            if (filterStatus !== 'all' && p.alertStatus !== filterStatus) return false;
            if (selectedDomain && p.domainId !== selectedDomain) return false;
            return true;
        });
    }, [prisms, filterStatus, selectedDomain]);

    // Count by status
    const statusCounts = useMemo(() => {
        return {
            normal: prisms.filter(p => p.alertStatus === 'normal').length,
            warning: prisms.filter(p => p.alertStatus === 'warning').length,
            critical: prisms.filter(p => p.alertStatus === 'critical').length
        };
    }, [prisms]);

    const getStatusColor = (status) => {
        return {
            normal: '#22c55e',
            warning: '#eab308',
            critical: '#ef4444'
        }[status] || '#6b7280';
    };

    return (
        <div className={`slope-monitoring-panel ${className}`}>
            {/* Header */}
            <div className="panel-header">
                <div className="header-left">
                    <Mountain size={20} />
                    <h3>Slope Monitoring</h3>
                </div>
                <button
                    className="refresh-btn"
                    onClick={onRefresh}
                    disabled={isLoading}
                >
                    <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                </button>
            </div>

            {/* Status Summary */}
            <div className="status-summary">
                <div
                    className={`status-card ${filterStatus === 'all' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('all')}
                >
                    <span className="count">{prisms.length}</span>
                    <span className="label">Total</span>
                </div>
                <div
                    className={`status-card normal ${filterStatus === 'normal' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('normal')}
                >
                    <span className="count">{statusCounts.normal}</span>
                    <span className="label">Normal</span>
                </div>
                <div
                    className={`status-card warning ${filterStatus === 'warning' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('warning')}
                >
                    <span className="count">{statusCounts.warning}</span>
                    <span className="label">Warning</span>
                </div>
                <div
                    className={`status-card critical ${filterStatus === 'critical' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('critical')}
                >
                    <span className="count">{statusCounts.critical}</span>
                    <span className="label">Critical</span>
                </div>
            </div>

            {/* Critical Alerts */}
            {statusCounts.critical > 0 && (
                <div className="critical-alerts">
                    <div className="alert-header">
                        <AlertTriangle size={16} />
                        Critical Alerts
                    </div>
                    {prisms
                        .filter(p => p.alertStatus === 'critical')
                        .map(prism => (
                            <div
                                key={prism.prismId}
                                className="alert-item"
                                onClick={() => onSelectPrism?.(prism.prismId)}
                            >
                                <span className="prism-name">{prism.prismName}</span>
                                <span className="displacement">
                                    {prism.totalDisplacementMm?.toFixed(1)} mm
                                </span>
                                <ChevronRight size={14} />
                            </div>
                        ))
                    }
                </div>
            )}

            {/* Prism List */}
            <div className="prism-list">
                <div className="list-header">
                    <span>Prism</span>
                    <span>Displacement</span>
                    <span>Rate</span>
                    <span>Status</span>
                </div>

                {filteredPrisms.map(prism => (
                    <div
                        key={prism.prismId}
                        className={`prism-row ${selectedPrismId === prism.prismId ? 'selected' : ''}`}
                        onClick={() => onSelectPrism?.(prism.prismId)}
                    >
                        <span className="prism-name">{prism.prismName}</span>
                        <span className="displacement">
                            {prism.totalDisplacementMm?.toFixed(1)} mm
                        </span>
                        <span className="rate">
                            {prism.displacementRateMmDay?.toFixed(2)} mm/day
                        </span>
                        <span
                            className="status-dot"
                            style={{ backgroundColor: getStatusColor(prism.alertStatus) }}
                        />
                    </div>
                ))}

                {filteredPrisms.length === 0 && (
                    <div className="no-data">No prisms matching filter</div>
                )}
            </div>

            {/* Selected Prism Detail */}
            {selectedPrismId && (
                <div className="prism-detail">
                    {(() => {
                        const prism = prisms.find(p => p.prismId === selectedPrismId);
                        if (!prism) return null;

                        return (
                            <>
                                <h4>{prism.prismName}</h4>
                                <div className="detail-grid">
                                    <div className="detail-item">
                                        <label>Total Displacement</label>
                                        <span className="value">{prism.totalDisplacementMm?.toFixed(2)} mm</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Velocity</label>
                                        <span className="value">{prism.displacementRateMmDay?.toFixed(3)} mm/day</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Warning Threshold</label>
                                        <span className="value">{prism.warningThresholdMm} mm</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Critical Threshold</label>
                                        <span className="value">{prism.criticalThresholdMm} mm</span>
                                    </div>
                                    <div className="detail-item">
                                        <label>Last Reading</label>
                                        <span className="value">{prism.lastReadingAt || 'Unknown'}</span>
                                    </div>
                                </div>

                                {/* Mini displacement chart would go here */}
                                <div className="displacement-chart-placeholder">
                                    <Activity size={20} />
                                    <span>Displacement History</span>
                                </div>
                            </>
                        );
                    })()}
                </div>
            )}

            <style jsx>{`
        .slope-monitoring-panel {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .panel-header {
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
        
        .header-left h3 {
          margin: 0;
          font-size: 16px;
        }
        
        .refresh-btn {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .spinning {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .status-summary {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          padding: 12px;
        }
        
        .status-card {
          text-align: center;
          padding: 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          cursor: pointer;
          border: 1px solid transparent;
        }
        
        .status-card.active {
          border-color: rgba(255,255,255,0.2);
        }
        
        .status-card .count {
          display: block;
          font-size: 20px;
          font-weight: 600;
          color: #fff;
        }
        
        .status-card .label {
          font-size: 11px;
          color: #888;
        }
        
        .status-card.normal { border-left: 3px solid #22c55e; }
        .status-card.warning { border-left: 3px solid #eab308; }
        .status-card.critical { border-left: 3px solid #ef4444; }
        
        .critical-alerts {
          margin: 0 12px 12px;
          background: rgba(239,68,68,0.1);
          border: 1px solid rgba(239,68,68,0.3);
          border-radius: 8px;
          overflow: hidden;
        }
        
        .alert-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          background: rgba(239,68,68,0.2);
          color: #ef4444;
          font-size: 12px;
          font-weight: 600;
        }
        
        .alert-item {
          display: flex;
          align-items: center;
          padding: 10px 12px;
          border-top: 1px solid rgba(239,68,68,0.2);
          cursor: pointer;
        }
        
        .alert-item:hover {
          background: rgba(255,255,255,0.03);
        }
        
        .alert-item .prism-name {
          flex: 1;
          color: #fff;
          font-size: 13px;
        }
        
        .alert-item .displacement {
          color: #ef4444;
          font-size: 12px;
          margin-right: 8px;
        }
        
        .prism-list {
          padding: 0 12px 12px;
        }
        
        .list-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 40px;
          padding: 8px 12px;
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
        }
        
        .prism-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 40px;
          align-items: center;
          padding: 10px 12px;
          background: rgba(255,255,255,0.02);
          border-radius: 6px;
          margin-bottom: 4px;
          cursor: pointer;
        }
        
        .prism-row:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .prism-row.selected {
          background: rgba(59,130,246,0.15);
          border: 1px solid rgba(59,130,246,0.3);
        }
        
        .prism-row .prism-name {
          color: #fff;
          font-size: 13px;
        }
        
        .prism-row .displacement,
        .prism-row .rate {
          color: #aaa;
          font-size: 12px;
        }
        
        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          justify-self: center;
        }
        
        .no-data {
          text-align: center;
          padding: 20px;
          color: #666;
          font-style: italic;
        }
        
        .prism-detail {
          padding: 16px;
          margin: 0 12px 12px;
          background: rgba(0,0,0,0.3);
          border-radius: 8px;
        }
        
        .prism-detail h4 {
          margin: 0 0 12px;
          color: #fff;
          font-size: 14px;
        }
        
        .detail-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .detail-item label {
          display: block;
          font-size: 10px;
          color: #888;
          margin-bottom: 2px;
        }
        
        .detail-item .value {
          font-size: 13px;
          color: #ddd;
        }
        
        .displacement-chart-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 30px;
          background: rgba(255,255,255,0.02);
          border-radius: 6px;
          color: #666;
          font-size: 12px;
        }
      `}</style>
        </div>
    );
};

export default SlopeMonitoringPanel;
