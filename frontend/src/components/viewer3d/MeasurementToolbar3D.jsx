/**
 * MeasurementToolbar3D.jsx
 * 
 * 3D measurement tools for point-to-point, polyline, and area measurements.
 */

import React, { useState } from 'react';
import {
    Ruler,
    Move,
    Triangle,
    Square,
    Trash2,
    Copy,
    Download,
    RotateCcw
} from 'lucide-react';

const MeasurementToolbar3D = ({
    activeTool,
    onToolChange,
    measurements = [],
    onMeasurementClear,
    onMeasurementDelete,
    onMeasurementExport,
    onUndo,
    units = 'meters',
    onUnitsChange,
    snapEnabled = true,
    onSnapToggle,
    className = ''
}) => {
    const [showMeasurements, setShowMeasurements] = useState(true);

    const tools = [
        { id: 'point', icon: Move, label: 'Point', description: 'Measure coordinates' },
        { id: 'distance', icon: Ruler, label: 'Distance', description: 'Point-to-point distance' },
        { id: 'polyline', icon: Triangle, label: 'Polyline', description: 'Multi-segment distance' },
        { id: 'area', icon: Square, label: 'Area', description: 'Polygon area & perimeter' }
    ];

    const formatValue = (value, type) => {
        if (type === 'area') {
            if (units === 'meters') {
                if (value >= 10000) return `${(value / 10000).toFixed(2)} ha`;
                return `${value.toFixed(2)} m²`;
            }
            return `${value.toFixed(2)} ft²`;
        }

        if (units === 'meters') {
            if (value >= 1000) return `${(value / 1000).toFixed(3)} km`;
            return `${value.toFixed(2)} m`;
        }
        return `${value.toFixed(2)} ft`;
    };

    const getTotalByType = (type) => {
        return measurements
            .filter(m => m.type === type)
            .reduce((sum, m) => sum + (m.value || 0), 0);
    };

    return (
        <div className={`measurement-toolbar ${className}`}>
            {/* Tool Selection */}
            <div className="tools-row">
                {tools.map(tool => (
                    <button
                        key={tool.id}
                        className={`tool-btn ${activeTool === tool.id ? 'active' : ''}`}
                        onClick={() => onToolChange?.(tool.id)}
                        title={tool.description}
                    >
                        <tool.icon size={18} />
                        <span className="tool-label">{tool.label}</span>
                    </button>
                ))}
            </div>

            {/* Options */}
            <div className="options-row">
                <div className="option-group">
                    <label>Units:</label>
                    <select
                        value={units}
                        onChange={(e) => onUnitsChange?.(e.target.value)}
                    >
                        <option value="meters">Metric (m)</option>
                        <option value="feet">Imperial (ft)</option>
                    </select>
                </div>

                <label className="snap-toggle">
                    <input
                        type="checkbox"
                        checked={snapEnabled}
                        onChange={(e) => onSnapToggle?.(e.target.checked)}
                    />
                    Snap to surface
                </label>

                <button className="icon-btn" onClick={onUndo} title="Undo last point">
                    <RotateCcw size={14} />
                </button>
            </div>

            {/* Active Measurement Display */}
            {activeTool && measurements.length > 0 && (
                <div className="active-measurement">
                    <div className="measurement-display">
                        {activeTool === 'point' && measurements[measurements.length - 1] && (
                            <>
                                <span className="coord">X: {measurements[measurements.length - 1].x?.toFixed(2)}</span>
                                <span className="coord">Y: {measurements[measurements.length - 1].y?.toFixed(2)}</span>
                                <span className="coord">Z: {measurements[measurements.length - 1].z?.toFixed(2)}</span>
                            </>
                        )}
                        {activeTool === 'distance' && (
                            <span className="value">
                                {formatValue(measurements[measurements.length - 1]?.value || 0, 'distance')}
                            </span>
                        )}
                        {activeTool === 'polyline' && (
                            <span className="value">
                                Total: {formatValue(getTotalByType('polyline'), 'distance')}
                            </span>
                        )}
                        {activeTool === 'area' && (
                            <>
                                <span className="value">
                                    Area: {formatValue(measurements[measurements.length - 1]?.area || 0, 'area')}
                                </span>
                                <span className="value secondary">
                                    Perimeter: {formatValue(measurements[measurements.length - 1]?.perimeter || 0, 'distance')}
                                </span>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Measurements List */}
            <div className="measurements-section">
                <div
                    className="section-header"
                    onClick={() => setShowMeasurements(!showMeasurements)}
                >
                    <span>Measurements ({measurements.length})</span>
                    <span className="toggle-icon">{showMeasurements ? '▼' : '▶'}</span>
                </div>

                {showMeasurements && (
                    <div className="measurements-list">
                        {measurements.length === 0 ? (
                            <div className="no-measurements">
                                Click on the 3D view to start measuring
                            </div>
                        ) : (
                            measurements.map((m, i) => (
                                <div key={i} className={`measurement-item ${m.type}`}>
                                    <div className="item-icon">
                                        {m.type === 'point' && <Move size={12} />}
                                        {m.type === 'distance' && <Ruler size={12} />}
                                        {m.type === 'polyline' && <Triangle size={12} />}
                                        {m.type === 'area' && <Square size={12} />}
                                    </div>
                                    <div className="item-value">
                                        {m.type === 'point' && (
                                            <span>({m.x?.toFixed(1)}, {m.y?.toFixed(1)}, {m.z?.toFixed(1)})</span>
                                        )}
                                        {m.type === 'distance' && formatValue(m.value, 'distance')}
                                        {m.type === 'polyline' && formatValue(m.value, 'distance')}
                                        {m.type === 'area' && formatValue(m.area, 'area')}
                                    </div>
                                    <button
                                        className="delete-btn"
                                        onClick={() => onMeasurementDelete?.(i)}
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="actions-row">
                <button
                    className="action-btn"
                    onClick={onMeasurementClear}
                    disabled={measurements.length === 0}
                >
                    <Trash2 size={12} />
                    Clear All
                </button>
                <button
                    className="action-btn"
                    onClick={onMeasurementExport}
                    disabled={measurements.length === 0}
                >
                    <Download size={12} />
                    Export
                </button>
            </div>

            <style jsx>{`
        .measurement-toolbar {
          background: linear-gradient(145deg, #1a1a2e, #252538);
          border-radius: 12px;
          padding: 12px;
          width: 280px;
        }
        
        .tools-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 6px;
          margin-bottom: 12px;
        }
        
        .tool-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 10px 6px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          color: #888;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .tool-btn:hover {
          background: rgba(255,255,255,0.06);
          color: #aaa;
        }
        
        .tool-btn.active {
          background: rgba(59,130,246,0.2);
          border-color: #3b82f6;
          color: #3b82f6;
        }
        
        .tool-label {
          font-size: 10px;
        }
        
        .options-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .option-group {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          color: #888;
        }
        
        .option-group select {
          padding: 4px 6px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 10px;
        }
        
        .snap-toggle {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 10px;
          color: #888;
          cursor: pointer;
        }
        
        .icon-btn {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .active-measurement {
          background: rgba(59,130,246,0.1);
          border: 1px solid rgba(59,130,246,0.3);
          border-radius: 8px;
          padding: 10px;
          margin-bottom: 12px;
        }
        
        .measurement-display {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }
        
        .coord {
          font-size: 12px;
          color: #aaa;
        }
        
        .value {
          font-size: 16px;
          font-weight: 600;
          color: #fff;
        }
        
        .value.secondary {
          font-size: 12px;
          font-weight: normal;
          color: #aaa;
        }
        
        .measurements-section {
          background: rgba(0,0,0,0.2);
          border-radius: 8px;
          overflow: hidden;
          margin-bottom: 12px;
        }
        
        .section-header {
          display: flex;
          justify-content: space-between;
          padding: 10px 12px;
          font-size: 12px;
          color: #aaa;
          cursor: pointer;
          background: rgba(0,0,0,0.2);
        }
        
        .measurements-list {
          max-height: 150px;
          overflow-y: auto;
        }
        
        .no-measurements {
          padding: 16px;
          text-align: center;
          font-size: 11px;
          color: #666;
          font-style: italic;
        }
        
        .measurement-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .item-icon {
          color: #888;
        }
        
        .measurement-item.point .item-icon { color: #3b82f6; }
        .measurement-item.distance .item-icon { color: #22c55e; }
        .measurement-item.polyline .item-icon { color: #f97316; }
        .measurement-item.area .item-icon { color: #a855f7; }
        
        .item-value {
          flex: 1;
          font-size: 12px;
          color: #ccc;
        }
        
        .delete-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #666;
          cursor: pointer;
        }
        
        .delete-btn:hover {
          color: #ef4444;
        }
        
        .actions-row {
          display: flex;
          gap: 8px;
        }
        
        .action-btn {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 6px;
          padding: 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #aaa;
          font-size: 11px;
          cursor: pointer;
        }
        
        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
        </div>
    );
};

export default MeasurementToolbar3D;
