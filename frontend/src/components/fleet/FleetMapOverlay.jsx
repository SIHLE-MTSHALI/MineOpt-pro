/**
 * FleetMapOverlay.jsx
 * 
 * Real-time equipment overlay on 2D/3D map showing fleet positions.
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
    Truck,
    HardHat,
    Fuel,
    Wrench,
    AlertTriangle,
    ChevronRight,
    RefreshCw,
    Filter,
    Layers
} from 'lucide-react';

const EQUIPMENT_ICONS = {
    haul_truck: Truck,
    excavator: HardHat,
    front_end_loader: HardHat,
    dozer: HardHat,
    grader: HardHat,
    drill_rig: HardHat,
    water_cart: Fuel,
    fuel_truck: Fuel,
    light_vehicle: Truck,
    other: Truck
};

const STATUS_COLORS = {
    operating: '#22c55e',  // Green
    standby: '#eab308',    // Yellow
    maintenance: '#3b82f6', // Blue
    breakdown: '#ef4444',   // Red
    refueling: '#f97316',   // Orange
    shift_change: '#8b5cf6', // Purple
    off_site: '#6b7280'     // Gray
};

const FleetMapOverlay = ({
    siteId,
    positions = [],
    selectedEquipmentId,
    onSelectEquipment,
    onRefresh,
    isLoading = false,
    mapBounds,
    showLabels = true,
    showTrails = false,
    filterTypes = [],
    filterStatuses = [],
    className = ''
}) => {
    const [hoveredId, setHoveredId] = useState(null);
    const [showFilters, setShowFilters] = useState(false);
    const [localFilterTypes, setLocalFilterTypes] = useState(filterTypes);
    const [localFilterStatuses, setLocalFilterStatuses] = useState(filterStatuses);

    // Filter positions
    const filteredPositions = useMemo(() => {
        return positions.filter(pos => {
            if (localFilterTypes.length > 0 && !localFilterTypes.includes(pos.equipment_type)) {
                return false;
            }
            if (localFilterStatuses.length > 0 && !localFilterStatuses.includes(pos.status)) {
                return false;
            }
            return true;
        });
    }, [positions, localFilterTypes, localFilterStatuses]);

    // Get unique types and statuses for filter options
    const availableTypes = useMemo(() => {
        const types = new Set(positions.map(p => p.equipment_type));
        return Array.from(types);
    }, [positions]);

    const availableStatuses = useMemo(() => {
        const statuses = new Set(positions.map(p => p.status).filter(Boolean));
        return Array.from(statuses);
    }, [positions]);

    // Convert geo coords to screen position (simplified)
    const getScreenPosition = useCallback((lat, lon) => {
        if (!mapBounds) {
            return { x: 50, y: 50 }; // Center fallback
        }

        const { minLat, maxLat, minLon, maxLon, width, height } = mapBounds;
        const x = ((lon - minLon) / (maxLon - minLon)) * width;
        const y = ((maxLat - lat) / (maxLat - minLat)) * height;

        return { x, y };
    }, [mapBounds]);

    return (
        <div className={`fleet-map-overlay ${className}`}>
            {/* Controls */}
            <div className="overlay-controls">
                <button
                    className="control-btn"
                    onClick={onRefresh}
                    disabled={isLoading}
                    title="Refresh positions"
                >
                    <RefreshCw size={16} className={isLoading ? 'spinning' : ''} />
                </button>

                <button
                    className={`control-btn ${showFilters ? 'active' : ''}`}
                    onClick={() => setShowFilters(!showFilters)}
                    title="Filter equipment"
                >
                    <Filter size={16} />
                </button>

                <div className="position-count">
                    {filteredPositions.length} / {positions.length}
                </div>
            </div>

            {/* Filter Panel */}
            {showFilters && (
                <div className="filter-panel">
                    <div className="filter-section">
                        <label>Equipment Type</label>
                        <div className="filter-options">
                            {availableTypes.map(type => (
                                <label key={type} className="filter-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={localFilterTypes.length === 0 || localFilterTypes.includes(type)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setLocalFilterTypes(prev =>
                                                    prev.length === 0 ? [] : [...prev, type]
                                                );
                                            } else {
                                                setLocalFilterTypes(prev => prev.filter(t => t !== type));
                                            }
                                        }}
                                    />
                                    <span>{type.replace(/_/g, ' ')}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="filter-section">
                        <label>Status</label>
                        <div className="filter-options">
                            {availableStatuses.map(status => (
                                <label key={status} className="filter-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={localFilterStatuses.length === 0 || localFilterStatuses.includes(status)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setLocalFilterStatuses(prev =>
                                                    prev.length === 0 ? [] : [...prev, status]
                                                );
                                            } else {
                                                setLocalFilterStatuses(prev => prev.filter(s => s !== status));
                                            }
                                        }}
                                    />
                                    <span style={{ color: STATUS_COLORS[status] }}>
                                        {status.replace(/_/g, ' ')}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Equipment Icons */}
            <svg className="equipment-layer" width="100%" height="100%">
                {filteredPositions.map(pos => {
                    const { x, y } = getScreenPosition(pos.latitude, pos.longitude);
                    const Icon = EQUIPMENT_ICONS[pos.equipment_type] || Truck;
                    const isSelected = selectedEquipmentId === pos.equipment_id;
                    const isHovered = hoveredId === pos.equipment_id;
                    const color = STATUS_COLORS[pos.status] || '#888';

                    return (
                        <g
                            key={pos.equipment_id}
                            transform={`translate(${x}, ${y})`}
                            onClick={() => onSelectEquipment?.(pos.equipment_id)}
                            onMouseEnter={() => setHoveredId(pos.equipment_id)}
                            onMouseLeave={() => setHoveredId(null)}
                            style={{ cursor: 'pointer' }}
                        >
                            {/* Selection ring */}
                            {isSelected && (
                                <circle
                                    r={20}
                                    fill="none"
                                    stroke={color}
                                    strokeWidth={2}
                                    className="pulse-ring"
                                />
                            )}

                            {/* Background circle */}
                            <circle
                                r={isSelected || isHovered ? 16 : 12}
                                fill={color}
                                opacity={0.9}
                            />

                            {/* Heading indicator */}
                            {pos.heading != null && (
                                <line
                                    x1={0}
                                    y1={0}
                                    x2={0}
                                    y2={-18}
                                    stroke={color}
                                    strokeWidth={2}
                                    transform={`rotate(${pos.heading})`}
                                />
                            )}

                            {/* Icon */}
                            <foreignObject x={-8} y={-8} width={16} height={16}>
                                <Icon size={16} color="#fff" />
                            </foreignObject>

                            {/* Label */}
                            {showLabels && (
                                <text
                                    y={24}
                                    textAnchor="middle"
                                    fill="#fff"
                                    fontSize={10}
                                    fontWeight={isSelected ? 'bold' : 'normal'}
                                >
                                    {pos.fleet_number}
                                </text>
                            )}
                        </g>
                    );
                })}
            </svg>

            {/* Legend */}
            <div className="status-legend">
                {Object.entries(STATUS_COLORS).map(([status, color]) => (
                    <div key={status} className="legend-item">
                        <span className="legend-dot" style={{ backgroundColor: color }} />
                        <span className="legend-label">{status.replace(/_/g, ' ')}</span>
                    </div>
                ))}
            </div>

            <style jsx>{`
        .fleet-map-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
        }
        
        .overlay-controls {
          position: absolute;
          top: 10px;
          right: 10px;
          display: flex;
          gap: 8px;
          align-items: center;
          background: rgba(0,0,0,0.7);
          padding: 8px;
          border-radius: 8px;
          pointer-events: auto;
        }
        
        .control-btn {
          padding: 6px;
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 4px;
          color: #fff;
          cursor: pointer;
        }
        
        .control-btn:hover, .control-btn.active {
          background: rgba(255,255,255,0.2);
        }
        
        .control-btn:disabled {
          opacity: 0.5;
        }
        
        .spinning {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .position-count {
          font-size: 12px;
          color: #aaa;
          padding: 0 8px;
        }
        
        .filter-panel {
          position: absolute;
          top: 50px;
          right: 10px;
          background: rgba(30,30,50,0.95);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          padding: 12px;
          pointer-events: auto;
          min-width: 180px;
        }
        
        .filter-section {
          margin-bottom: 12px;
        }
        
        .filter-section:last-child {
          margin-bottom: 0;
        }
        
        .filter-section label {
          display: block;
          font-size: 11px;
          color: #888;
          margin-bottom: 6px;
          text-transform: uppercase;
        }
        
        .filter-options {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .filter-checkbox {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #ccc;
          cursor: pointer;
        }
        
        .filter-checkbox input {
          margin: 0;
        }
        
        .equipment-layer {
          pointer-events: auto;
        }
        
        .pulse-ring {
          animation: pulse 1.5s ease-out infinite;
        }
        
        @keyframes pulse {
          0% { r: 16; opacity: 1; }
          100% { r: 30; opacity: 0; }
        }
        
        .status-legend {
          position: absolute;
          bottom: 10px;
          left: 10px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          background: rgba(0,0,0,0.7);
          padding: 8px 12px;
          border-radius: 8px;
          pointer-events: auto;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .legend-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        
        .legend-label {
          font-size: 10px;
          color: #aaa;
          text-transform: capitalize;
        }
      `}</style>
        </div>
    );
};

export default FleetMapOverlay;
