/**
 * BoreholeRenderer Component - Phase 4 3D Visualization
 * 
 * React Three Fiber component for rendering borehole traces in 3D.
 * 
 * Features:
 * - Collar points with labels
 * - 3D trace lines with depth coloring
 * - Interval segments colored by quality
 * - Click selection and info display
 * - LOD for large datasets
 */

import React, { useMemo, useState, useRef, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Line, Html, Sphere, Text } from '@react-three/drei';
import * as THREE from 'three';

// Color ramp for quality values
const createColorRamp = (value, min, max, colorScheme = 'viridis') => {
    const t = Math.max(0, Math.min(1, (value - min) / (max - min || 1)));

    const schemes = {
        viridis: [
            [0.267, 0.004, 0.329],
            [0.282, 0.140, 0.458],
            [0.254, 0.265, 0.529],
            [0.163, 0.471, 0.558],
            [0.134, 0.658, 0.517],
            [0.477, 0.821, 0.318],
            [0.993, 0.906, 0.144]
        ],
        redYellowGreen: [
            [0.843, 0.188, 0.121],
            [0.992, 0.682, 0.38],
            [0.996, 0.996, 0.596],
            [0.651, 0.851, 0.416],
            [0.102, 0.596, 0.314]
        ]
    };

    const colors = schemes[colorScheme] || schemes.viridis;
    const segment = t * (colors.length - 1);
    const i = Math.floor(segment);
    const f = segment - i;

    if (i >= colors.length - 1) {
        return new THREE.Color(...colors[colors.length - 1]);
    }

    const c1 = colors[i];
    const c2 = colors[i + 1];

    return new THREE.Color(
        c1[0] + (c2[0] - c1[0]) * f,
        c1[1] + (c2[1] - c1[1]) * f,
        c1[2] + (c2[2] - c1[2]) * f
    );
};

// Single borehole trace component
const BoreholeTrace = ({
    borehole,
    trace,
    intervals = [],
    qualityField,
    qualityRange,
    colorScheme = 'viridis',
    selected,
    onSelect,
    showLabel = true,
    offset = { x: 0, y: 0, z: 0 }
}) => {
    const [hovered, setHovered] = useState(false);

    // Create trace line points
    const linePoints = useMemo(() => {
        if (!trace || trace.length === 0) return [];

        return trace.map(point => [
            point.easting - offset.x,
            point.elevation - offset.z,
            point.northing - offset.y
        ]);
    }, [trace, offset]);

    // Create interval segments with colors
    const intervalSegments = useMemo(() => {
        if (!intervals || intervals.length === 0 || !qualityField) return [];

        return intervals.map(interval => {
            const value = interval.quality_vector?.[qualityField] ?? 0;
            const color = createColorRamp(
                value,
                qualityRange?.[0] ?? 0,
                qualityRange?.[1] ?? 100,
                colorScheme
            );

            // Find trace points within interval depth range
            const fromDepth = interval.from_depth;
            const toDepth = interval.to_depth;

            const startPoint = trace?.find(p => p.depth >= fromDepth);
            const endPoint = trace?.find(p => p.depth >= toDepth);

            if (startPoint && endPoint) {
                return {
                    points: [
                        [startPoint.easting - offset.x, startPoint.elevation - offset.z, startPoint.northing - offset.y],
                        [endPoint.easting - offset.x, endPoint.elevation - offset.z, endPoint.northing - offset.y]
                    ],
                    color,
                    value,
                    interval
                };
            }
            return null;
        }).filter(Boolean);
    }, [intervals, trace, qualityField, qualityRange, colorScheme, offset]);

    // Collar position
    const collarPosition = useMemo(() => {
        if (!borehole) return [0, 0, 0];
        return [
            borehole.easting - offset.x,
            borehole.elevation - offset.z,
            borehole.northing - offset.y
        ];
    }, [borehole, offset]);

    if (linePoints.length === 0) return null;

    return (
        <group>
            {/* Collar point */}
            <Sphere
                position={collarPosition}
                args={[2, 16, 16]}
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect?.(borehole);
                }}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
            >
                <meshStandardMaterial
                    color={selected ? '#3B82F6' : hovered ? '#60A5FA' : '#10B981'}
                    emissive={selected ? '#3B82F6' : hovered ? '#60A5FA' : '#000000'}
                    emissiveIntensity={selected || hovered ? 0.3 : 0}
                />
            </Sphere>

            {/* Collar label */}
            {showLabel && (
                <Html
                    position={[collarPosition[0], collarPosition[1] + 5, collarPosition[2]]}
                    center
                    style={{
                        pointerEvents: 'none',
                        userSelect: 'none'
                    }}
                >
                    <div style={{
                        backgroundColor: selected ? '#3B82F6' : 'rgba(0,0,0,0.7)',
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 500,
                        whiteSpace: 'nowrap'
                    }}>
                        {borehole.hole_id}
                    </div>
                </Html>
            )}

            {/* Trace line (when no quality coloring) */}
            {intervalSegments.length === 0 && (
                <Line
                    points={linePoints}
                    color={selected ? '#3B82F6' : '#6B7280'}
                    lineWidth={selected ? 3 : 2}
                />
            )}

            {/* Interval segments with quality colors */}
            {intervalSegments.map((segment, idx) => (
                <Line
                    key={idx}
                    points={segment.points}
                    color={segment.color}
                    lineWidth={3}
                />
            ))}
        </group>
    );
};

// Main Borehole Renderer
const BoreholeRenderer = ({
    boreholes = [],
    traces = {},
    intervals = {},
    qualityField = null,
    qualityRange = [0, 100],
    colorScheme = 'viridis',
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
            {boreholes.map(borehole => (
                <BoreholeTrace
                    key={borehole.collar_id}
                    borehole={borehole}
                    trace={traces[borehole.collar_id] || []}
                    intervals={intervals[borehole.collar_id] || []}
                    qualityField={qualityField}
                    qualityRange={qualityRange}
                    colorScheme={colorScheme}
                    selected={selectedId === borehole.collar_id}
                    onSelect={onSelect}
                    showLabel={showLabels}
                    offset={offset}
                />
            ))}
        </group>
    );
};

export default BoreholeRenderer;
