/**
 * SectionViewer.jsx - Phase 7
 * 
 * Interactive cross-section/profile viewer.
 * 
 * Features:
 * - Display elevation profiles
 * - Interactive zoom/pan
 * - Measurement tools
 * - Multiple profile overlay
 * - Export options
 */

import React, { useMemo, useState, useRef, useCallback } from 'react';
import {
    ZoomIn,
    ZoomOut,
    Home,
    Ruler,
    Download,
    Eye,
    Grid3X3,
    Info
} from 'lucide-react';

const SectionViewer = ({
    profiles = [],
    title = 'Section View',
    width = 600,
    height = 300,
    showGrid = true,
    showStats = true,
    onExport,
    className = ''
}) => {
    const [zoom, setZoom] = useState(1);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [showRuler, setShowRuler] = useState(false);
    const [hoveredPoint, setHoveredPoint] = useState(null);
    const svgRef = useRef(null);

    // Calculate view bounds from all profiles
    const viewBounds = useMemo(() => {
        if (!profiles.length) return null;

        let minDist = Infinity, maxDist = -Infinity;
        let minZ = Infinity, maxZ = -Infinity;

        profiles.forEach(profile => {
            profile.points?.forEach(pt => {
                minDist = Math.min(minDist, pt.distance);
                maxDist = Math.max(maxDist, pt.distance);
                minZ = Math.min(minZ, pt.z);
                maxZ = Math.max(maxZ, pt.z);
            });
        });

        // Add padding
        const distPadding = (maxDist - minDist) * 0.05 || 10;
        const zPadding = (maxZ - minZ) * 0.1 || 5;

        return {
            minDist: minDist - distPadding,
            maxDist: maxDist + distPadding,
            minZ: minZ - zPadding,
            maxZ: maxZ + zPadding
        };
    }, [profiles]);

    // Transform functions
    const transform = useMemo(() => {
        if (!viewBounds) return null;

        const padding = 50;
        const plotWidth = width - 2 * padding;
        const plotHeight = height - 2 * padding;

        const distRange = viewBounds.maxDist - viewBounds.minDist;
        const zRange = viewBounds.maxZ - viewBounds.minZ;

        const scaleX = plotWidth / (distRange * zoom);
        const scaleY = plotHeight / (zRange * zoom);

        return {
            toScreen: (dist, z) => ({
                x: padding + (dist - viewBounds.minDist) * scaleX * zoom + offset.x,
                y: height - padding - (z - viewBounds.minZ) * scaleY * zoom + offset.y
            }),
            fromScreen: (x, y) => ({
                distance: (x - padding - offset.x) / (scaleX * zoom) + viewBounds.minDist,
                z: viewBounds.minZ + (height - padding - y - offset.y) / (scaleY * zoom)
            }),
            plotWidth,
            plotHeight,
            padding
        };
    }, [viewBounds, width, height, zoom, offset]);

    // Generate grid lines
    const gridLines = useMemo(() => {
        if (!viewBounds || !transform || !showGrid) return { x: [], y: [] };

        const lines = { x: [], y: [] };

        // Calculate nice intervals
        const distRange = viewBounds.maxDist - viewBounds.minDist;
        const zRange = viewBounds.maxZ - viewBounds.minZ;

        const distInterval = Math.pow(10, Math.floor(Math.log10(distRange / 5)));
        const zInterval = Math.pow(10, Math.floor(Math.log10(zRange / 5)));

        // Vertical lines (distance)
        for (let d = Math.ceil(viewBounds.minDist / distInterval) * distInterval; d <= viewBounds.maxDist; d += distInterval) {
            const { x } = transform.toScreen(d, 0);
            if (x >= transform.padding && x <= width - transform.padding) {
                lines.x.push({ value: d, x, major: d % (distInterval * 5) === 0 });
            }
        }

        // Horizontal lines (elevation)
        for (let z = Math.ceil(viewBounds.minZ / zInterval) * zInterval; z <= viewBounds.maxZ; z += zInterval) {
            const { y } = transform.toScreen(0, z);
            if (y >= transform.padding && y <= height - transform.padding) {
                lines.y.push({ value: z, y, major: z % (zInterval * 5) === 0 });
            }
        }

        return lines;
    }, [viewBounds, transform, showGrid, width, height]);

    // Profile colors
    const profileColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

    // Handle mouse move for tooltip
    const handleMouseMove = useCallback((e) => {
        if (!transform || !profiles.length) return;

        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) return;

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Find nearest point
        const { distance } = transform.fromScreen(x, y);

        let nearest = null;
        let minDistToPoint = Infinity;

        profiles.forEach((profile, profileIdx) => {
            profile.points?.forEach((pt) => {
                const dist = Math.abs(pt.distance - distance);
                if (dist < minDistToPoint) {
                    minDistToPoint = dist;
                    nearest = { ...pt, profileIndex: profileIdx, profileName: profile.name };
                }
            });
        });

        if (nearest && minDistToPoint < (viewBounds.maxDist - viewBounds.minDist) * 0.05) {
            setHoveredPoint(nearest);
        } else {
            setHoveredPoint(null);
        }
    }, [transform, profiles, viewBounds]);

    // Zoom controls
    const handleZoomIn = () => setZoom(z => Math.min(z * 1.5, 10));
    const handleZoomOut = () => setZoom(z => Math.max(z / 1.5, 0.5));
    const handleReset = () => { setZoom(1); setOffset({ x: 0, y: 0 }); };

    if (!profiles.length || !viewBounds) {
        return (
            <div className={`section-viewer empty ${className}`}>
                <div className="empty-state">
                    <Grid3X3 size={32} />
                    <p>No profile data</p>
                </div>

                <style jsx>{`
          .section-viewer.empty {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 200px;
            background: #1a1a2e;
            border-radius: 8px;
            color: #666;
          }
          .empty-state { text-align: center; }
          .empty-state p { margin-top: 8px; font-size: 13px; }
        `}</style>
            </div>
        );
    }

    return (
        <div className={`section-viewer ${className}`}>
            {/* Header */}
            <div className="viewer-header">
                <h3>{title}</h3>
                <div className="controls">
                    <button onClick={handleZoomIn} title="Zoom In"><ZoomIn size={16} /></button>
                    <button onClick={handleZoomOut} title="Zoom Out"><ZoomOut size={16} /></button>
                    <button onClick={handleReset} title="Reset View"><Home size={16} /></button>
                    <button
                        onClick={() => setShowRuler(!showRuler)}
                        className={showRuler ? 'active' : ''}
                        title="Toggle Ruler"
                    >
                        <Ruler size={16} />
                    </button>
                    <button onClick={onExport} title="Export"><Download size={16} /></button>
                </div>
            </div>

            {/* SVG Canvas */}
            <svg
                ref={svgRef}
                width={width}
                height={height}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoveredPoint(null)}
                style={{ background: '#1a1a2e' }}
            >
                {/* Grid Lines */}
                {showGrid && (
                    <g className="grid">
                        {gridLines.x.map((line, i) => (
                            <g key={`x-${i}`}>
                                <line
                                    x1={line.x} y1={transform.padding}
                                    x2={line.x} y2={height - transform.padding}
                                    stroke={line.major ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)'}
                                    strokeWidth={line.major ? 1 : 0.5}
                                />
                                <text
                                    x={line.x}
                                    y={height - transform.padding + 15}
                                    fill="#666"
                                    fontSize={9}
                                    textAnchor="middle"
                                >
                                    {line.value.toFixed(0)}
                                </text>
                            </g>
                        ))}
                        {gridLines.y.map((line, i) => (
                            <g key={`y-${i}`}>
                                <line
                                    x1={transform.padding} y1={line.y}
                                    x2={width - transform.padding} y2={line.y}
                                    stroke={line.major ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)'}
                                    strokeWidth={line.major ? 1 : 0.5}
                                />
                                <text
                                    x={transform.padding - 8}
                                    y={line.y + 3}
                                    fill="#666"
                                    fontSize={9}
                                    textAnchor="end"
                                >
                                    {line.value.toFixed(0)}
                                </text>
                            </g>
                        ))}
                    </g>
                )}

                {/* Profile Lines */}
                {profiles.map((profile, idx) => {
                    if (!profile.points?.length) return null;

                    const pathD = profile.points
                        .map((pt, i) => {
                            const { x, y } = transform.toScreen(pt.distance, pt.z);
                            return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
                        })
                        .join(' ');

                    return (
                        <path
                            key={idx}
                            d={pathD}
                            fill="none"
                            stroke={profileColors[idx % profileColors.length]}
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    );
                })}

                {/* Hovered Point */}
                {hoveredPoint && transform && (
                    <g className="hover-indicator">
                        <circle
                            cx={transform.toScreen(hoveredPoint.distance, hoveredPoint.z).x}
                            cy={transform.toScreen(hoveredPoint.distance, hoveredPoint.z).y}
                            r={6}
                            fill={profileColors[hoveredPoint.profileIndex % profileColors.length]}
                            stroke="#fff"
                            strokeWidth={2}
                        />
                    </g>
                )}

                {/* Axis Labels */}
                <text x={width / 2} y={height - 10} fill="#888" fontSize={11} textAnchor="middle">
                    Distance (m)
                </text>
                <text
                    x={15}
                    y={height / 2}
                    fill="#888"
                    fontSize={11}
                    textAnchor="middle"
                    transform={`rotate(-90, 15, ${height / 2})`}
                >
                    Elevation (m)
                </text>
            </svg>

            {/* Tooltip */}
            {hoveredPoint && (
                <div className="tooltip">
                    <div className="tooltip-header">{hoveredPoint.profileName || 'Profile'}</div>
                    <div className="tooltip-row">
                        <span>Distance:</span>
                        <span>{hoveredPoint.distance.toFixed(2)} m</span>
                    </div>
                    <div className="tooltip-row">
                        <span>Elevation:</span>
                        <span>{hoveredPoint.z.toFixed(2)} m</span>
                    </div>
                    {hoveredPoint.slope_to_next !== undefined && (
                        <div className="tooltip-row">
                            <span>Slope:</span>
                            <span>{hoveredPoint.slope_to_next.toFixed(1)}°</span>
                        </div>
                    )}
                </div>
            )}

            {/* Legend */}
            {profiles.length > 1 && (
                <div className="legend">
                    {profiles.map((profile, idx) => (
                        <div key={idx} className="legend-item">
                            <span
                                className="legend-color"
                                style={{ background: profileColors[idx % profileColors.length] }}
                            />
                            <span>{profile.name || `Profile ${idx + 1}`}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Stats */}
            {showStats && profiles[0] && (
                <div className="stats">
                    <div className="stat">
                        <span className="label">Length:</span>
                        <span className="value">{profiles[0].total_distance?.toFixed(1)} m</span>
                    </div>
                    <div className="stat">
                        <span className="label">Min:</span>
                        <span className="value">{profiles[0].min_elevation?.toFixed(1)} m</span>
                    </div>
                    <div className="stat">
                        <span className="label">Max:</span>
                        <span className="value">{profiles[0].max_elevation?.toFixed(1)} m</span>
                    </div>
                </div>
            )}

            <style jsx>{`
        .section-viewer {
          position: relative;
          background: #1e1e2e;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .viewer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .viewer-header h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: #fff;
        }
        
        .controls {
          display: flex;
          gap: 4px;
        }
        
        .controls button {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .controls button:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .controls button.active { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        
        .tooltip {
          position: absolute;
          top: 60px;
          right: 16px;
          background: rgba(30, 30, 46, 0.95);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 6px;
          padding: 10px;
          min-width: 140px;
        }
        
        .tooltip-header {
          font-size: 11px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 8px;
          padding-bottom: 6px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .tooltip-row {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          margin-bottom: 4px;
        }
        
        .tooltip-row span:first-child { color: #888; }
        .tooltip-row span:last-child { color: #fff; font-family: 'SF Mono', monospace; }
        
        .legend {
          display: flex;
          gap: 16px;
          padding: 8px 16px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #a0a0b0;
        }
        
        .legend-color {
          width: 12px;
          height: 3px;
          border-radius: 1px;
        }
        
        .stats {
          display: flex;
          gap: 16px;
          padding: 8px 16px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .stat {
          font-size: 11px;
        }
        
        .stat .label { color: #888; margin-right: 4px; }
        .stat .value { color: #fff; font-family: 'SF Mono', monospace; }
      `}</style>
        </div>
    );
};

export default SectionViewer;
