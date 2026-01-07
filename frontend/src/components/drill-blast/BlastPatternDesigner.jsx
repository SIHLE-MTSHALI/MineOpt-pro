/**
 * BlastPatternDesigner.jsx
 * 
 * Interactive drill and blast pattern design tool.
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
    Grid,
    Circle,
    RotateCw,
    Settings,
    Save,
    Download,
    Play,
    Zap,
    AlertTriangle
} from 'lucide-react';

const BlastPatternDesigner = ({
    pattern,
    holes = [],
    onPatternChange,
    onHoleSelect,
    onSave,
    onPreviewFragmentation,
    selectedHoleId,
    className = ''
}) => {
    const [viewMode, setViewMode] = useState('plan'); // plan, section, 3d
    const [showGrid, setShowGrid] = useState(true);
    const [showDelays, setShowDelays] = useState(true);
    const [zoom, setZoom] = useState(1);

    // Calculate SVG dimensions based on pattern
    const dimensions = useMemo(() => {
        if (!pattern) return { width: 600, height: 400, scale: 10 };

        const patternWidth = pattern.num_holes_per_row * pattern.spacing;
        const patternHeight = pattern.num_rows * pattern.burden;
        const scale = Math.min(500 / patternWidth, 350 / patternHeight);

        return {
            width: patternWidth * scale + 100,
            height: patternHeight * scale + 100,
            scale
        };
    }, [pattern]);

    // Get delay color
    const getDelayColor = (delay_ms) => {
        const hue = (delay_ms / 10) % 360;
        return `hsl(${hue}, 70%, 50%)`;
    };

    // Get hole status color
    const getStatusColor = (status) => {
        const colors = {
            planned: '#6b7280',
            drilled: '#3b82f6',
            loaded: '#f97316',
            detonated: '#22c55e'
        };
        return colors[status] || '#6b7280';
    };

    return (
        <div className={`blast-pattern-designer ${className}`}>
            {/* Toolbar */}
            <div className="designer-toolbar">
                <div className="toolbar-left">
                    <div className="view-mode-selector">
                        <button
                            className={viewMode === 'plan' ? 'active' : ''}
                            onClick={() => setViewMode('plan')}
                        >
                            Plan
                        </button>
                        <button
                            className={viewMode === 'section' ? 'active' : ''}
                            onClick={() => setViewMode('section')}
                        >
                            Section
                        </button>
                    </div>

                    <button
                        className={`toggle-btn ${showGrid ? 'active' : ''}`}
                        onClick={() => setShowGrid(!showGrid)}
                        title="Toggle Grid"
                    >
                        <Grid size={16} />
                    </button>

                    <button
                        className={`toggle-btn ${showDelays ? 'active' : ''}`}
                        onClick={() => setShowDelays(!showDelays)}
                        title="Toggle Delay Colors"
                    >
                        <Zap size={16} />
                    </button>
                </div>

                <div className="toolbar-right">
                    <button className="action-btn" onClick={onPreviewFragmentation}>
                        <Play size={14} />
                        Fragmentation
                    </button>
                    <button className="action-btn primary" onClick={onSave}>
                        <Save size={14} />
                        Save
                    </button>
                </div>
            </div>

            {/* Pattern Parameters */}
            {pattern && (
                <div className="pattern-params">
                    <div className="param-group">
                        <label>Burden</label>
                        <div className="param-value">{pattern.burden} m</div>
                    </div>
                    <div className="param-group">
                        <label>Spacing</label>
                        <div className="param-value">{pattern.spacing} m</div>
                    </div>
                    <div className="param-group">
                        <label>Depth</label>
                        <div className="param-value">{pattern.hole_depth_m} m</div>
                    </div>
                    <div className="param-group">
                        <label>Diameter</label>
                        <div className="param-value">{pattern.hole_diameter_mm} mm</div>
                    </div>
                    <div className="param-group">
                        <label>Powder Factor</label>
                        <div className="param-value">{pattern.powder_factor_kg_bcm?.toFixed(2)} kg/BCM</div>
                    </div>
                    <div className="param-group">
                        <label>Total Holes</label>
                        <div className="param-value">{holes.length}</div>
                    </div>
                </div>
            )}

            {/* Canvas */}
            <div className="pattern-canvas">
                <svg
                    width={dimensions.width}
                    height={dimensions.height}
                    viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
                >
                    {/* Grid */}
                    {showGrid && (
                        <g className="grid-layer">
                            {Array.from({ length: 20 }).map((_, i) => (
                                <React.Fragment key={i}>
                                    <line
                                        x1={50 + i * 30}
                                        y1={0}
                                        x2={50 + i * 30}
                                        y2={dimensions.height}
                                        stroke="rgba(255,255,255,0.1)"
                                        strokeWidth={1}
                                    />
                                    <line
                                        x1={0}
                                        y1={50 + i * 30}
                                        x2={dimensions.width}
                                        y2={50 + i * 30}
                                        stroke="rgba(255,255,255,0.1)"
                                        strokeWidth={1}
                                    />
                                </React.Fragment>
                            ))}
                        </g>
                    )}

                    {/* Free Face */}
                    <line
                        x1={50}
                        y1={50}
                        x2={dimensions.width - 50}
                        y2={50}
                        stroke="#22c55e"
                        strokeWidth={3}
                        strokeDasharray="10,5"
                    />
                    <text x={55} y={40} fill="#22c55e" fontSize={10}>FREE FACE</text>

                    {/* Holes */}
                    {holes.map((hole, i) => {
                        const x = 50 + (hole.design_x - (pattern?.origin_x || 0)) * dimensions.scale;
                        const y = 50 + (hole.design_y - (pattern?.origin_y || 0)) * dimensions.scale;
                        const isSelected = selectedHoleId === hole.hole_id;
                        const color = showDelays && hole.detonator_delay_ms
                            ? getDelayColor(hole.detonator_delay_ms)
                            : getStatusColor(hole.status);

                        return (
                            <g
                                key={hole.hole_id}
                                transform={`translate(${x}, ${y})`}
                                onClick={() => onHoleSelect?.(hole)}
                                style={{ cursor: 'pointer' }}
                            >
                                {/* Selection ring */}
                                {isSelected && (
                                    <circle r={16} fill="none" stroke="#fff" strokeWidth={2} />
                                )}

                                {/* Hole circle */}
                                <circle r={10} fill={color} stroke="#fff" strokeWidth={1} />

                                {/* Hole number */}
                                <text
                                    textAnchor="middle"
                                    dy={3}
                                    fill="#fff"
                                    fontSize={8}
                                    fontWeight="bold"
                                >
                                    {hole.hole_number}
                                </text>

                                {/* Delay label */}
                                {showDelays && hole.detonator_delay_ms && (
                                    <text
                                        textAnchor="middle"
                                        dy={22}
                                        fill="#aaa"
                                        fontSize={8}
                                    >
                                        {hole.detonator_delay_ms}ms
                                    </text>
                                )}
                            </g>
                        );
                    })}
                </svg>
            </div>

            {/* Legend */}
            <div className="pattern-legend">
                <div className="legend-title">Status</div>
                <div className="legend-items">
                    {['planned', 'drilled', 'loaded', 'detonated'].map(status => (
                        <div key={status} className="legend-item">
                            <span className="legend-dot" style={{ backgroundColor: getStatusColor(status) }} />
                            <span>{status}</span>
                        </div>
                    ))}
                </div>
            </div>

            <style jsx>{`
        .blast-pattern-designer {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .designer-toolbar {
          display: flex;
          justify-content: space-between;
          padding: 12px 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .toolbar-left, .toolbar-right {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        
        .view-mode-selector {
          display: flex;
          background: rgba(255,255,255,0.05);
          border-radius: 6px;
          overflow: hidden;
        }
        
        .view-mode-selector button {
          padding: 6px 12px;
          background: transparent;
          border: none;
          color: #888;
          font-size: 12px;
          cursor: pointer;
        }
        
        .view-mode-selector button.active {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .toggle-btn {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .toggle-btn.active {
          background: rgba(59, 130, 246, 0.2);
          color: #3b82f6;
        }
        
        .action-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #ccc;
          font-size: 12px;
          cursor: pointer;
        }
        
        .action-btn.primary {
          background: rgba(34, 197, 94, 0.2);
          border-color: #22c55e;
          color: #22c55e;
        }
        
        .pattern-params {
          display: flex;
          gap: 24px;
          padding: 12px 16px;
          background: rgba(255,255,255,0.02);
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .param-group {
          text-align: center;
        }
        
        .param-group label {
          display: block;
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 4px;
        }
        
        .param-value {
          font-size: 14px;
          font-weight: 600;
          color: #fff;
        }
        
        .pattern-canvas {
          padding: 16px;
          overflow: auto;
          background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
        }
        
        .pattern-canvas svg {
          display: block;
          margin: 0 auto;
        }
        
        .pattern-legend {
          display: flex;
          gap: 16px;
          padding: 12px 16px;
          background: rgba(0,0,0,0.2);
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .legend-title {
          font-size: 11px;
          color: #888;
          text-transform: uppercase;
        }
        
        .legend-items {
          display: flex;
          gap: 16px;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #aaa;
          text-transform: capitalize;
        }
        
        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }
      `}</style>
        </div>
    );
};

export default BlastPatternDesigner;
