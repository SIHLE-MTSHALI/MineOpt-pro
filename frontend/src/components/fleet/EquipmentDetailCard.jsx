/**
 * EquipmentDetailCard.jsx
 * 
 * Equipment detail popup showing status, location, and actions.
 */

import React, { useState } from 'react';
import {
    X,
    MapPin,
    Gauge,
    Clock,
    User,
    Wrench,
    Activity,
    Navigation,
    ChevronDown,
    AlertTriangle
} from 'lucide-react';

const STATUS_CONFIGS = {
    operating: { color: '#22c55e', label: 'Operating', icon: Activity },
    standby: { color: '#eab308', label: 'Standby', icon: Clock },
    maintenance: { color: '#3b82f6', label: 'Maintenance', icon: Wrench },
    breakdown: { color: '#ef4444', label: 'Breakdown', icon: AlertTriangle },
    refueling: { color: '#f97316', label: 'Refueling', icon: Gauge },
    shift_change: { color: '#8b5cf6', label: 'Shift Change', icon: User },
    off_site: { color: '#6b7280', label: 'Off Site', icon: MapPin }
};

const EquipmentDetailCard = ({
    equipment,
    position,
    onClose,
    onStatusChange,
    onViewTrail,
    onScheduleMaintenance,
    className = ''
}) => {
    const [showStatusMenu, setShowStatusMenu] = useState(false);

    if (!equipment) return null;

    const statusConfig = STATUS_CONFIGS[equipment.status] || STATUS_CONFIGS.standby;
    const StatusIcon = statusConfig.icon;

    return (
        <div className={`equipment-detail-card ${className}`}>
            {/* Header */}
            <div className="card-header">
                <div className="equipment-id">
                    <span className="fleet-number">{equipment.fleet_number}</span>
                    <span className="equipment-type">{equipment.equipment_type?.replace(/_/g, ' ')}</span>
                </div>
                <button className="close-btn" onClick={onClose}>
                    <X size={18} />
                </button>
            </div>

            {/* Status Badge */}
            <div className="status-section">
                <button
                    className="status-badge"
                    style={{ backgroundColor: `${statusConfig.color}20`, borderColor: statusConfig.color }}
                    onClick={() => setShowStatusMenu(!showStatusMenu)}
                >
                    <StatusIcon size={14} style={{ color: statusConfig.color }} />
                    <span style={{ color: statusConfig.color }}>{statusConfig.label}</span>
                    <ChevronDown size={14} style={{ color: statusConfig.color }} />
                </button>

                {showStatusMenu && (
                    <div className="status-menu">
                        {Object.entries(STATUS_CONFIGS).map(([key, config]) => (
                            <button
                                key={key}
                                className={`status-option ${equipment.status === key ? 'active' : ''}`}
                                onClick={() => {
                                    onStatusChange?.(key);
                                    setShowStatusMenu(false);
                                }}
                            >
                                <config.icon size={14} style={{ color: config.color }} />
                                <span>{config.label}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Position Info */}
            {position && (
                <div className="info-section">
                    <div className="section-title">
                        <MapPin size={14} />
                        <span>Position</span>
                    </div>
                    <div className="info-grid">
                        <div className="info-item">
                            <span className="label">Coordinates</span>
                            <span className="value">
                                {position.latitude?.toFixed(6)}, {position.longitude?.toFixed(6)}
                            </span>
                        </div>
                        <div className="info-item">
                            <span className="label">Speed</span>
                            <span className="value">{position.speed_kmh?.toFixed(1) || 0} km/h</span>
                        </div>
                        <div className="info-item">
                            <span className="label">Heading</span>
                            <span className="value">{position.heading?.toFixed(0) || 0}°</span>
                        </div>
                        <div className="info-item">
                            <span className="label">Last Update</span>
                            <span className="value">{position.last_update || 'Unknown'}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Equipment Info */}
            <div className="info-section">
                <div className="section-title">
                    <Gauge size={14} />
                    <span>Equipment Info</span>
                </div>
                <div className="info-grid">
                    {equipment.manufacturer && (
                        <div className="info-item">
                            <span className="label">Make/Model</span>
                            <span className="value">{equipment.manufacturer} {equipment.model}</span>
                        </div>
                    )}
                    {equipment.payload_tonnes && (
                        <div className="info-item">
                            <span className="label">Payload</span>
                            <span className="value">{equipment.payload_tonnes} t</span>
                        </div>
                    )}
                    {equipment.engine_hours != null && (
                        <div className="info-item">
                            <span className="label">Engine Hours</span>
                            <span className="value">{equipment.engine_hours?.toFixed(0)} hrs</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            <div className="actions-section">
                <button className="action-btn" onClick={onViewTrail}>
                    <Navigation size={14} />
                    View Trail
                </button>
                <button className="action-btn" onClick={onScheduleMaintenance}>
                    <Wrench size={14} />
                    Schedule Maintenance
                </button>
            </div>

            <style jsx>{`
        .equipment-detail-card {
          width: 320px;
          background: linear-gradient(145deg, #1e1e2e, #252538);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 16px;
          background: rgba(0,0,0,0.2);
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .equipment-id {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        
        .fleet-number {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }
        
        .equipment-type {
          font-size: 12px;
          color: #888;
          text-transform: capitalize;
        }
        
        .close-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #666;
          cursor: pointer;
        }
        
        .close-btn:hover {
          color: #fff;
        }
        
        .status-section {
          padding: 12px 16px;
          position: relative;
        }
        
        .status-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: transparent;
          border: 1px solid;
          border-radius: 8px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
        }
        
        .status-menu {
          position: absolute;
          top: 100%;
          left: 16px;
          right: 16px;
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          margin-top: 4px;
          z-index: 10;
          overflow: hidden;
        }
        
        .status-option {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 10px 12px;
          background: transparent;
          border: none;
          color: #ccc;
          font-size: 13px;
          cursor: pointer;
          text-align: left;
        }
        
        .status-option:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .status-option.active {
          background: rgba(255,255,255,0.1);
        }
        
        .info-section {
          padding: 12px 16px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .section-title {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 10px;
        }
        
        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        
        .info-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        
        .info-item .label {
          font-size: 10px;
          color: #666;
        }
        
        .info-item .value {
          font-size: 13px;
          color: #ddd;
        }
        
        .actions-section {
          display: flex;
          gap: 8px;
          padding: 12px 16px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .action-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 10px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          color: #ccc;
          font-size: 12px;
          cursor: pointer;
        }
        
        .action-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
      `}</style>
        </div>
    );
};

export default EquipmentDetailCard;
