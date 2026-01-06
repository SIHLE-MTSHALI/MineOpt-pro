/**
 * BlockModelRenderer Component (Spatial) - Phase 4 Site Builder UI
 * 
 * 3D block model visualization for the spatial viewer.
 * Per implementation plan WP-UI4: components/spatial/BlockModelRenderer.jsx
 * 
 * Features:
 * - 3D block visualization
 * - Color ramp by quality field
 * - Section views (XY, XZ, YZ planes)
 */

import React, { useMemo, useState, useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Box } from '@react-three/drei';
import * as THREE from 'three';

// Color ramps
const COLOR_RAMPS = {
    viridis: [
        [0.267, 0.004, 0.329],
        [0.282, 0.140, 0.458],
        [0.254, 0.265, 0.529],
        [0.163, 0.471, 0.558],
        [0.134, 0.658, 0.517],
        [0.477, 0.821, 0.318],
        [0.993, 0.906, 0.144]
    ],
    coal: [
        [0.1, 0.1, 0.1],
        [0.3, 0.2, 0.15],
        [0.5, 0.4, 0.25],
        [0.7, 0.55, 0.35],
        [0.9, 0.8, 0.5]
    ],
    thermal: [
        [0.1, 0.1, 0.5],
        [0.2, 0.2, 0.8],
        [0.5, 0.3, 0.8],
        [0.8, 0.3, 0.3],
        [1.0, 0.8, 0.2]
    ]
};

const getColorFromRamp = (value, min, max, rampName = 'viridis') => {
    const ramp = COLOR_RAMPS[rampName] || COLOR_RAMPS.viridis;
    const t = Math.max(0, Math.min(1, (value - min) / (max - min || 1)));

    const segment = t * (ramp.length - 1);
    const i = Math.floor(segment);
    const f = segment - i;

    if (i >= ramp.length - 1) {
        return new THREE.Color(...ramp[ramp.length - 1]);
    }

    const c1 = ramp[i];
    const c2 = ramp[i + 1];

    return new THREE.Color(
        c1[0] + (c2[0] - c1[0]) * f,
        c1[1] + (c2[1] - c1[1]) * f,
        c1[2] + (c2[2] - c1[2]) * f
    );
};

// Individual block component
const BlockMesh = ({
    block,
    blockSize,
    offset,
    color,
    selected = false,
    onSelect
}) => {
    const [hovered, setHovered] = useState(false);

    const position = useMemo(() => [
        block.x - offset.x,
        block.z - offset.z,
        block.y - offset.y
    ], [block, offset]);

    return (
        <group position={position}>
            <Box
                args={[blockSize.x * 0.92, blockSize.z * 0.92, blockSize.y * 0.92]}
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect?.(block);
                }}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
            >
                <meshStandardMaterial
                    color={color}
                    transparent={true}
                    opacity={selected ? 1 : hovered ? 0.9 : 0.8}
                    roughness={0.6}
                    metalness={0.1}
                />
            </Box>

            {/* Selection highlight */}
            {selected && (
                <Box args={[blockSize.x, blockSize.z, blockSize.y]}>
                    <meshBasicMaterial
                        color="#3B82F6"
                        transparent
                        opacity={0.3}
                        wireframe
                    />
                </Box>
            )}
        </group>
    );
};

// Section view controls
const SectionControls = ({
    sectionAxis,
    sectionLevel,
    maxLevels,
    onAxisChange,
    onLevelChange
}) => {
    return (
        <div style={{
            position: 'absolute',
            bottom: 20,
            left: 20,
            backgroundColor: 'rgba(255,255,255,0.95)',
            padding: '12px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            zIndex: 100
        }}>
            <div style={{ marginBottom: '8px', fontWeight: 500, fontSize: '12px' }}>
                Section View
            </div>

            <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
                {['all', 'x', 'y', 'z'].map(axis => (
                    <button
                        key={axis}
                        onClick={() => onAxisChange(axis === 'all' ? null : axis)}
                        style={{
                            padding: '4px 10px',
                            border: sectionAxis === (axis === 'all' ? null : axis)
                                ? '2px solid #3B82F6'
                                : '1px solid #D1D5DB',
                            borderRadius: '4px',
                            backgroundColor: sectionAxis === (axis === 'all' ? null : axis)
                                ? '#EFF6FF'
                                : 'white',
                            fontSize: '11px',
                            cursor: 'pointer',
                            textTransform: 'uppercase'
                        }}
                    >
                        {axis === 'all' ? 'All' : axis.toUpperCase()}
                    </button>
                ))}
            </div>

            {sectionAxis && (
                <div>
                    <input
                        type="range"
                        min={0}
                        max={maxLevels[sectionAxis] - 1}
                        value={sectionLevel}
                        onChange={(e) => onLevelChange(parseInt(e.target.value))}
                        style={{ width: '100%' }}
                    />
                    <div style={{ fontSize: '10px', color: '#6B7280', textAlign: 'center' }}>
                        Level {sectionLevel + 1} / {maxLevels[sectionAxis]}
                    </div>
                </div>
            )}
        </div>
    );
};

// Main Block Model Renderer
const BlockModelRenderer = ({
    blocks = [],
    modelDefinition = null,
    qualityField = null,
    valueRange = [0, 30],
    colorRamp = 'viridis',
    selectedBlockId = null,
    onBlockSelect,
    showSectionControls = true,
    autoCenter = true
}) => {
    const [sectionAxis, setSectionAxis] = useState(null);
    const [sectionLevel, setSectionLevel] = useState(0);

    // Block size from model
    const blockSize = useMemo(() => {
        if (modelDefinition) {
            return {
                x: modelDefinition.block_size_x || 10,
                y: modelDefinition.block_size_y || 10,
                z: modelDefinition.block_size_z || 5
            };
        }
        return { x: 10, y: 10, z: 5 };
    }, [modelDefinition]);

    // Max levels for section controls
    const maxLevels = useMemo(() => {
        if (modelDefinition) {
            return {
                x: modelDefinition.count_x || 10,
                y: modelDefinition.count_y || 10,
                z: modelDefinition.count_z || 5
            };
        }
        // Calculate from blocks
        const maxI = Math.max(...blocks.map(b => b.i), 0) + 1;
        const maxJ = Math.max(...blocks.map(b => b.j), 0) + 1;
        const maxK = Math.max(...blocks.map(b => b.k), 0) + 1;
        return { x: maxI, y: maxJ, z: maxK };
    }, [blocks, modelDefinition]);

    // Center offset
    const offset = useMemo(() => {
        if (!autoCenter || blocks.length === 0) {
            return { x: 0, y: 0, z: 0 };
        }

        const xs = blocks.map(b => b.x);
        const ys = blocks.map(b => b.y);
        const zs = blocks.map(b => b.z);

        return {
            x: (Math.min(...xs) + Math.max(...xs)) / 2,
            y: (Math.min(...ys) + Math.max(...ys)) / 2,
            z: (Math.min(...zs) + Math.max(...zs)) / 2
        };
    }, [blocks, autoCenter]);

    // Filter blocks by section
    const visibleBlocks = useMemo(() => {
        if (!sectionAxis) return blocks;

        return blocks.filter(block => {
            const indexMap = { x: block.i, y: block.j, z: block.k };
            return indexMap[sectionAxis] === sectionLevel;
        });
    }, [blocks, sectionAxis, sectionLevel]);

    // Block colors
    const blockColors = useMemo(() => {
        const colors = {};
        blocks.forEach(block => {
            const value = qualityField && block.quality_vector
                ? block.quality_vector[qualityField]
                : block.value ?? 0;
            colors[block.block_id] = getColorFromRamp(value, valueRange[0], valueRange[1], colorRamp);
        });
        return colors;
    }, [blocks, qualityField, valueRange, colorRamp]);

    return (
        <>
            <group>
                {visibleBlocks.map(block => (
                    <BlockMesh
                        key={block.block_id}
                        block={block}
                        blockSize={blockSize}
                        offset={offset}
                        color={blockColors[block.block_id]}
                        selected={selectedBlockId === block.block_id}
                        onSelect={onBlockSelect}
                    />
                ))}
            </group>

            {/* Section controls rendered via HTML portal */}
            {showSectionControls && (
                <Html fullscreen>
                    <SectionControls
                        sectionAxis={sectionAxis}
                        sectionLevel={sectionLevel}
                        maxLevels={maxLevels}
                        onAxisChange={(axis) => {
                            setSectionAxis(axis);
                            setSectionLevel(0);
                        }}
                        onLevelChange={setSectionLevel}
                    />
                </Html>
            )}
        </>
    );
};

export default BlockModelRenderer;
