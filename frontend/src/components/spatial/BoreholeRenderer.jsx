/**
 * BoreholeRenderer Component (Spatial) - Phase 4 Site Builder UI
 * 
 * 3D borehole visualization for the spatial viewer.
 * Per implementation plan WP-UI3: components/spatial/BoreholeRenderer.jsx
 * 
 * Features:
 * - 3D borehole traces in React Three Fiber
 * - Color by lithology or quality
 * - Selectable with info panel
 */

import React, { useMemo, useState, useCallback } from 'react';
import { Line, Html, Sphere } from '@react-three/drei';
import * as THREE from 'three';

// Color schemes
const LITHOLOGY_COLORS = {
    'COAL': '#1a1a1a',
    'SHALE': '#6b6b6b',
    'SANDSTONE': '#d4b483',
    'MUDSTONE': '#8b7355',
    'SILTSTONE': '#a0a0a0',
    'OVERBURDEN': '#8b4513',
    'default': '#888888'
};

const createQualityColor = (value, min = 0, max = 30, scheme = 'viridis') => {
    const t = Math.max(0, Math.min(1, (value - min) / (max - min || 1)));

    // Viridis-like color ramp
    const r = 0.267 + t * 0.726;
    const g = 0.004 + t * 0.902;
    const b = 0.329 + t * (-0.185);

    return new THREE.Color(r, g, b);
};

// Individual borehole component
const Borehole = ({
    collar,
    trace = [],
    intervals = [],
    colorBy = 'lithology', // 'lithology', 'quality', 'none'
    qualityField = 'CV_ARB',
    qualityRange = [0, 30],
    selected = false,
    onSelect,
    offset = { x: 0, y: 0, z: 0 },
    showLabel = true
}) => {
    const [hovered, setHovered] = useState(false);
    const [showInfoPanel, setShowInfoPanel] = useState(false);

    // Create trace line points
    const linePoints = useMemo(() => {
        if (!trace || trace.length === 0) {
            // Create vertical line from collar
            if (collar) {
                return [
                    [collar.easting - offset.x, collar.elevation - offset.z, collar.northing - offset.y],
                    [collar.easting - offset.x, collar.elevation - collar.total_depth - offset.z, collar.northing - offset.y]
                ];
            }
            return [];
        }

        return trace.map(point => [
            point.easting - offset.x,
            point.elevation - offset.z,
            point.northing - offset.y
        ]);
    }, [trace, collar, offset]);

    // Create colored interval segments
    const intervalSegments = useMemo(() => {
        if (!intervals || intervals.length === 0 || colorBy === 'none') return [];

        return intervals.map(interval => {
            let color;

            if (colorBy === 'lithology') {
                color = LITHOLOGY_COLORS[interval.lithology_code] || LITHOLOGY_COLORS.default;
            } else if (colorBy === 'quality' && interval.quality_vector) {
                const value = interval.quality_vector[qualityField] ?? 0;
                color = createQualityColor(value, qualityRange[0], qualityRange[1]);
            } else {
                color = LITHOLOGY_COLORS.default;
            }

            // Calculate segment positions
            const fromRatio = interval.from_depth / (collar?.total_depth || 100);
            const toRatio = interval.to_depth / (collar?.total_depth || 100);

            const collarPos = [
                collar.easting - offset.x,
                collar.elevation - offset.z,
                collar.northing - offset.y
            ];

            const bottomPos = [
                collar.easting - offset.x,
                collar.elevation - collar.total_depth - offset.z,
                collar.northing - offset.y
            ];

            // Interpolate
            const startPoint = [
                collarPos[0],
                collarPos[1] - (bottomPos[1] - collarPos[1]) * fromRatio - fromRatio * collar.total_depth,
                collarPos[2]
            ];

            const endPoint = [
                collarPos[0],
                collarPos[1] - (bottomPos[1] - collarPos[1]) * toRatio - toRatio * collar.total_depth,
                collarPos[2]
            ];

            return {
                points: [startPoint, endPoint],
                color: typeof color === 'string' ? new THREE.Color(color) : color,
                interval
            };
        }).filter(Boolean);
    }, [intervals, colorBy, qualityField, qualityRange, collar, offset]);

    // Collar position
    const collarPosition = useMemo(() => {
        if (!collar) return [0, 0, 0];
        return [
            collar.easting - offset.x,
            collar.elevation - offset.z,
            collar.northing - offset.y
        ];
    }, [collar, offset]);

    const handleClick = useCallback((e) => {
        e.stopPropagation();
        if (onSelect) {
            onSelect(collar);
        }
        setShowInfoPanel(!showInfoPanel);
    }, [collar, onSelect, showInfoPanel]);

    if (!collar) return null;

    return (
        <group>
            {/* Collar point */}
            <Sphere
                position={collarPosition}
                args={[2, 16, 16]}
                onClick={handleClick}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
            >
                <meshStandardMaterial
                    color={selected ? '#3B82F6' : hovered ? '#60A5FA' : '#10B981'}
                    emissive={selected || hovered ? '#3B82F6' : '#000000'}
                    emissiveIntensity={selected || hovered ? 0.4 : 0}
                />
            </Sphere>

            {/* Collar label */}
            {showLabel && (
                <Html
                    position={[collarPosition[0], collarPosition[1] + 8, collarPosition[2]]}
                    center
                    style={{ pointerEvents: 'none' }}
                >
                    <div style={{
                        backgroundColor: selected ? '#3B82F6' : 'rgba(0,0,0,0.75)',
                        color: 'white',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        whiteSpace: 'nowrap'
                    }}>
                        {collar.hole_id}
                    </div>
                </Html>
            )}

            {/* Info panel */}
            {showInfoPanel && (
                <Html
                    position={[collarPosition[0] + 15, collarPosition[1], collarPosition[2]]}
                    style={{ pointerEvents: 'auto' }}
                >
                    <div style={{
                        backgroundColor: 'white',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        fontSize: '12px',
                        minWidth: '180px'
                    }}>
                        <div style={{ fontWeight: 600, marginBottom: '8px', color: '#1F2937' }}>
                            {collar.hole_id}
                        </div>
                        <div style={{ color: '#4B5563', marginBottom: '4px' }}>
                            <strong>Easting:</strong> {collar.easting?.toFixed(2)}
                        </div>
                        <div style={{ color: '#4B5563', marginBottom: '4px' }}>
                            <strong>Northing:</strong> {collar.northing?.toFixed(2)}
                        </div>
                        <div style={{ color: '#4B5563', marginBottom: '4px' }}>
                            <strong>Elevation:</strong> {collar.elevation?.toFixed(2)}
                        </div>
                        <div style={{ color: '#4B5563', marginBottom: '4px' }}>
                            <strong>Total Depth:</strong> {collar.total_depth?.toFixed(1)} m
                        </div>
                        {intervals.length > 0 && (
                            <div style={{ color: '#4B5563' }}>
                                <strong>Intervals:</strong> {intervals.length}
                            </div>
                        )}
                        <button
                            onClick={() => setShowInfoPanel(false)}
                            style={{
                                marginTop: '8px',
                                padding: '4px 8px',
                                backgroundColor: '#F3F4F6',
                                border: 'none',
                                borderRadius: '4px',
                                fontSize: '11px',
                                cursor: 'pointer'
                            }}
                        >
                            Close
                        </button>
                    </div>
                </Html>
            )}

            {/* Trace line (base) */}
            {intervalSegments.length === 0 && linePoints.length > 0 && (
                <Line
                    points={linePoints}
                    color={selected ? '#3B82F6' : '#6B7280'}
                    lineWidth={selected ? 3 : 2}
                />
            )}

            {/* Colored interval segments */}
            {intervalSegments.map((segment, idx) => (
                <Line
                    key={idx}
                    points={segment.points}
                    color={segment.color}
                    lineWidth={4}
                />
            ))}
        </group>
    );
};

// Main renderer component
const BoreholeRenderer = ({
    boreholes = [],
    traces = {},
    intervals = {},
    colorBy = 'none',
    qualityField = 'CV_ARB',
    qualityRange = [0, 30],
    selectedId = null,
    onSelect,
    showLabels = true,
    autoCenter = true
}) => {
    // Calculate offset for centering
    const offset = useMemo(() => {
        if (!autoCenter || boreholes.length === 0) {
            return { x: 0, y: 0, z: 0 };
        }

        const xs = boreholes.map(b => b.easting);
        const ys = boreholes.map(b => b.northing);
        const zs = boreholes.map(b => b.elevation);

        return {
            x: (Math.min(...xs) + Math.max(...xs)) / 2,
            y: (Math.min(...ys) + Math.max(...ys)) / 2,
            z: (Math.min(...zs) + Math.max(...zs)) / 2
        };
    }, [boreholes, autoCenter]);

    return (
        <group>
            {boreholes.map(collar => (
                <Borehole
                    key={collar.collar_id || collar.hole_id}
                    collar={collar}
                    trace={traces[collar.collar_id] || []}
                    intervals={intervals[collar.collar_id] || []}
                    colorBy={colorBy}
                    qualityField={qualityField}
                    qualityRange={qualityRange}
                    selected={selectedId === collar.collar_id}
                    onSelect={onSelect}
                    offset={offset}
                    showLabel={showLabels}
                />
            ))}
        </group>
    );
};

export default BoreholeRenderer;
