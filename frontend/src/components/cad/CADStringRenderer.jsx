/**
 * CADStringRenderer.jsx - Phase 6
 * 
 * Renders CAD strings with various styles and selection highlighting.
 * 
 * Features:
 * - Line styles (solid, dashed, dotted)
 * - Color by string type
 * - Selection highlighting
 * - Hover effects
 * - Vertex visualization
 */

import React, { useMemo } from 'react';

// Default colors by string type
const STRING_TYPE_COLORS = {
    pit_boundary: '#ef4444',      // Red
    bench_crest: '#f97316',       // Orange
    bench_toe: '#eab308',         // Yellow
    haul_road: '#a855f7',         // Purple
    ramp: '#8b5cf6',              // Violet
    contour: '#64748b',           // Gray
    drill_pattern: '#06b6d4',     // Cyan
    survey_traverse: '#22c55e',   // Green
    power_line: '#f43f5e',        // Rose
    water_line: '#3b82f6',        // Blue
    fence_line: '#78716c',        // Stone
    geological_contact: '#fb923c', // Orange
    fault: '#dc2626',             // Red dark
    boundary: '#6366f1',          // Indigo
    custom: '#60a5fa'             // Blue light
};

// Line dash patterns
const LINE_PATTERNS = {
    solid: '',
    dashed: '8 4',
    dotted: '2 4',
    dashdot: '8 4 2 4',
    phantom: '16 4 2 4 2 4'
};

// Single string rendering
const CADStringPath = ({
    string,
    isSelected,
    isHovered,
    scale = 1,
    offset = { x: 0, y: 0 },
    showVertices = true,
    lineStyle = 'solid',
    customColor,
    customWeight,
    onClick,
    onHover
}) => {
    const { vertices, is_closed, string_type, color, line_weight } = string;

    // Calculate path
    const pathData = useMemo(() => {
        if (!vertices || vertices.length < 2) return '';

        const points = vertices.map(v => `${(v[0] + offset.x) * scale},${(v[1] + offset.y) * scale}`);

        const d = `M ${points[0]} L ${points.slice(1).join(' L ')}${is_closed ? ' Z' : ''}`;
        return d;
    }, [vertices, is_closed, scale, offset]);

    // Determine colors
    const strokeColor = customColor || color || STRING_TYPE_COLORS[string_type] || '#60a5fa';
    const strokeWidth = (customWeight || line_weight || 1) * (isSelected ? 2 : 1);
    const dashArray = LINE_PATTERNS[lineStyle] || '';

    return (
        <g className={`cad-string ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}>
            {/* Selection/hover glow */}
            {(isSelected || isHovered) && (
                <path
                    d={pathData}
                    fill="none"
                    stroke={isSelected ? '#fbbf24' : strokeColor}
                    strokeWidth={strokeWidth + 4}
                    strokeOpacity={0.3}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            )}

            {/* Main path */}
            <path
                d={pathData}
                fill="none"
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                strokeDasharray={dashArray}
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ cursor: 'pointer' }}
                onClick={(e) => {
                    e.stopPropagation();
                    onClick?.(string.string_id);
                }}
                onMouseEnter={() => onHover?.(string.string_id)}
                onMouseLeave={() => onHover?.(null)}
            />

            {/* Vertices */}
            {showVertices && vertices.map((v, i) => (
                <circle
                    key={i}
                    cx={(v[0] + offset.x) * scale}
                    cy={(v[1] + offset.y) * scale}
                    r={isSelected ? 5 : 3}
                    fill={i === 0 ? '#22c55e' : i === vertices.length - 1 ? '#ef4444' : '#fff'}
                    stroke={strokeColor}
                    strokeWidth={1}
                    opacity={isSelected || isHovered ? 1 : 0.7}
                />
            ))}
        </g>
    );
};

// Main renderer component
const CADStringRenderer = ({
    strings = [],
    selectedIds = [],
    hoveredId = null,
    bounds,
    width = 800,
    height = 600,
    showGrid = true,
    gridSpacing = 100,
    showVertices = true,
    lineStyle = 'solid',
    onSelect,
    onHover,
    onBackgroundClick,
    className = ''
}) => {
    // Calculate view transform
    const viewTransform = useMemo(() => {
        if (!bounds || !strings.length) {
            return { scale: 1, offset: { x: 0, y: 0 } };
        }

        const { minX, minY, maxX, maxY } = bounds;
        const padding = 50;

        const dataWidth = maxX - minX || 1;
        const dataHeight = maxY - minY || 1;

        const scaleX = (width - 2 * padding) / dataWidth;
        const scaleY = (height - 2 * padding) / dataHeight;
        const scale = Math.min(scaleX, scaleY);

        return {
            scale,
            offset: {
                x: -minX + padding / scale,
                y: -minY + padding / scale
            }
        };
    }, [bounds, strings, width, height]);

    // Generate grid lines
    const gridLines = useMemo(() => {
        if (!showGrid || !bounds) return [];

        const { minX, minY, maxX, maxY } = bounds;
        const lines = [];

        // Vertical lines
        for (let x = Math.floor(minX / gridSpacing) * gridSpacing; x <= maxX; x += gridSpacing) {
            lines.push({
                x1: (x + viewTransform.offset.x) * viewTransform.scale,
                y1: (minY + viewTransform.offset.y) * viewTransform.scale,
                x2: (x + viewTransform.offset.x) * viewTransform.scale,
                y2: (maxY + viewTransform.offset.y) * viewTransform.scale,
                major: x % (gridSpacing * 5) === 0
            });
        }

        // Horizontal lines
        for (let y = Math.floor(minY / gridSpacing) * gridSpacing; y <= maxY; y += gridSpacing) {
            lines.push({
                x1: (minX + viewTransform.offset.x) * viewTransform.scale,
                y1: (y + viewTransform.offset.y) * viewTransform.scale,
                x2: (maxX + viewTransform.offset.x) * viewTransform.scale,
                y2: (y + viewTransform.offset.y) * viewTransform.scale,
                major: y % (gridSpacing * 5) === 0
            });
        }

        return lines;
    }, [showGrid, bounds, gridSpacing, viewTransform]);

    return (
        <svg
            className={`cad-string-renderer ${className}`}
            width={width}
            height={height}
            onClick={onBackgroundClick}
            style={{ background: '#1a1a2e' }}
        >
            {/* Grid */}
            {showGrid && (
                <g className="grid">
                    {gridLines.map((line, i) => (
                        <line
                            key={i}
                            x1={line.x1}
                            y1={line.y1}
                            x2={line.x2}
                            y2={line.y2}
                            stroke={line.major ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)'}
                            strokeWidth={line.major ? 1 : 0.5}
                        />
                    ))}
                </g>
            )}

            {/* Strings (render non-selected first, then selected on top) */}
            <g className="strings">
                {strings
                    .filter(s => !selectedIds.includes(s.string_id))
                    .map(string => (
                        <CADStringPath
                            key={string.string_id}
                            string={string}
                            isSelected={false}
                            isHovered={hoveredId === string.string_id}
                            scale={viewTransform.scale}
                            offset={viewTransform.offset}
                            showVertices={showVertices}
                            lineStyle={lineStyle}
                            onClick={onSelect}
                            onHover={onHover}
                        />
                    ))}

                {strings
                    .filter(s => selectedIds.includes(s.string_id))
                    .map(string => (
                        <CADStringPath
                            key={string.string_id}
                            string={string}
                            isSelected={true}
                            isHovered={hoveredId === string.string_id}
                            scale={viewTransform.scale}
                            offset={viewTransform.offset}
                            showVertices={showVertices}
                            lineStyle={lineStyle}
                            onClick={onSelect}
                            onHover={onHover}
                        />
                    ))}
            </g>

            <style>{`
        .cad-string-renderer {
          display: block;
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          overflow: hidden;
        }
        
        .cad-string path {
          transition: stroke-width 0.15s ease, stroke-opacity 0.15s ease;
        }
        
        .cad-string.hovered path {
          stroke-opacity: 1;
        }
        
        .cad-string circle {
          transition: r 0.15s ease, opacity 0.15s ease;
        }
      `}</style>
        </svg>
    );
};

export default CADStringRenderer;
export { STRING_TYPE_COLORS, LINE_PATTERNS };
