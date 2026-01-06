/**
 * BlockModelRenderer Component - Phase 4 3D Visualization
 * 
 * React Three Fiber component for rendering block models in 3D.
 * 
 * Features:
 * - Instanced rendering for performance
 * - Quality-based color ramp
 * - Section/slice views
 * - Block selection
 * - Transparency for hidden blocks
 */

import React, { useMemo, useState, useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Box } from '@react-three/drei';
import * as THREE from 'three';

// Color ramp utilities
const colorRamps = {
    viridis: [
        [0.267, 0.004, 0.329],
        [0.282, 0.140, 0.458],
        [0.254, 0.265, 0.529],
        [0.163, 0.471, 0.558],
        [0.134, 0.658, 0.517],
        [0.477, 0.821, 0.318],
        [0.993, 0.906, 0.144]
    ],
    plasma: [
        [0.050, 0.030, 0.528],
        [0.417, 0.000, 0.658],
        [0.693, 0.165, 0.564],
        [0.881, 0.392, 0.383],
        [0.988, 0.652, 0.212],
        [0.940, 0.975, 0.131]
    ],
    coal: [
        [0.1, 0.1, 0.1],      // Low CV - dark
        [0.3, 0.2, 0.1],
        [0.5, 0.4, 0.2],
        [0.7, 0.6, 0.3],
        [0.9, 0.85, 0.5]      // High CV - bright
    ]
};

const interpolateColor = (value, min, max, rampName = 'viridis') => {
    const ramp = colorRamps[rampName] || colorRamps.viridis;
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

// Instanced block mesh for performance
const InstancedBlocks = ({
    blocks,
    blockSize,
    offset,
    valueRange,
    colorRamp,
    opacity = 1,
    selectedId = null
}) => {
    const meshRef = useRef();
    const tempObject = useMemo(() => new THREE.Object3D(), []);
    const tempColor = useMemo(() => new THREE.Color(), []);

    // Create color array
    const colors = useMemo(() => {
        const arr = new Float32Array(blocks.length * 3);

        blocks.forEach((block, i) => {
            const color = interpolateColor(
                block.value ?? 0,
                valueRange[0],
                valueRange[1],
                colorRamp
            );
            arr[i * 3] = color.r;
            arr[i * 3 + 1] = color.g;
            arr[i * 3 + 2] = color.b;
        });

        return arr;
    }, [blocks, valueRange, colorRamp]);

    // Update instance positions
    useEffect(() => {
        if (!meshRef.current) return;

        blocks.forEach((block, i) => {
            tempObject.position.set(
                block.x - offset.x,
                block.z - offset.z,
                block.y - offset.y
            );
            tempObject.updateMatrix();
            meshRef.current.setMatrixAt(i, tempObject.matrix);
        });

        meshRef.current.instanceMatrix.needsUpdate = true;
    }, [blocks, offset, tempObject]);

    // Update colors
    useEffect(() => {
        if (!meshRef.current) return;

        const colorAttribute = meshRef.current.geometry.getAttribute('color');
        if (colorAttribute) {
            colorAttribute.array.set(colors);
            colorAttribute.needsUpdate = true;
        }
    }, [colors]);

    if (blocks.length === 0) return null;

    return (
        <instancedMesh
            ref={meshRef}
            args={[null, null, blocks.length]}
            frustumCulled={true}
        >
            <boxGeometry args={[blockSize.x * 0.95, blockSize.z * 0.95, blockSize.y * 0.95]}>
                <instancedBufferAttribute
                    attach="attributes-color"
                    args={[colors, 3]}
                />
            </boxGeometry>
            <meshStandardMaterial
                vertexColors
                transparent={opacity < 1}
                opacity={opacity}
                roughness={0.7}
                metalness={0.1}
            />
        </instancedMesh>
    );
};

// Single block for selection highlight
const SelectedBlock = ({ block, blockSize, offset }) => {
    if (!block) return null;

    return (
        <group position={[
            block.x - offset.x,
            block.z - offset.z,
            block.y - offset.y
        ]}>
            <Box args={[blockSize.x, blockSize.z, blockSize.y]}>
                <meshBasicMaterial
                    color="#3B82F6"
                    transparent
                    opacity={0.3}
                    wireframe
                />
            </Box>
            <Html center>
                <div style={{
                    backgroundColor: 'rgba(59, 130, 246, 0.9)',
                    color: 'white',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none'
                }}>
                    <div><strong>Block ({block.i}, {block.j}, {block.k})</strong></div>
                    <div>Value: {block.value?.toFixed(2)}</div>
                    {block.variance && <div>Variance: {block.variance.toFixed(2)}</div>}
                </div>
            </Html>
        </group>
    );
};

// Main Block Model Renderer
const BlockModelRenderer = ({
    blocks = [],
    modelDefinition = null,
    qualityField = null,
    valueRange = [0, 100],
    colorRamp = 'viridis',
    sectionAxis = null,       // 'x', 'y', 'z', or null for all
    sectionLevel = 0,         // Which level to show
    sectionTolerance = 1,     // How many levels to include
    selectedBlockId = null,
    onBlockSelect,
    opacity = 1,
    showGrid = false,
    autoCenter = true
}) => {
    // Block size from model definition
    const blockSize = useMemo(() => {
        if (modelDefinition) {
            return {
                x: modelDefinition.block_size_x,
                y: modelDefinition.block_size_y,
                z: modelDefinition.block_size_z
            };
        }
        return { x: 10, y: 10, z: 5 };
    }, [modelDefinition]);

    // Calculate centering offset
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
            let coord;
            switch (sectionAxis) {
                case 'x':
                    coord = block.i;
                    break;
                case 'y':
                    coord = block.j;
                    break;
                case 'z':
                    coord = block.k;
                    break;
                default:
                    return true;
            }

            return Math.abs(coord - sectionLevel) <= sectionTolerance;
        });
    }, [blocks, sectionAxis, sectionLevel, sectionTolerance]);

    // Get selected block
    const selectedBlock = useMemo(() => {
        return blocks.find(b => b.block_id === selectedBlockId);
    }, [blocks, selectedBlockId]);

    return (
        <group>
            {/* Instanced blocks for performance */}
            <InstancedBlocks
                blocks={visibleBlocks}
                blockSize={blockSize}
                offset={offset}
                valueRange={valueRange}
                colorRamp={colorRamp}
                opacity={opacity}
                selectedId={selectedBlockId}
            />

            {/* Selected block highlight */}
            <SelectedBlock
                block={selectedBlock}
                blockSize={blockSize}
                offset={offset}
            />

            {/* Optional grid helper */}
            {showGrid && (
                <gridHelper
                    args={[
                        Math.max(blockSize.x * (modelDefinition?.count_x || 10), blockSize.y * (modelDefinition?.count_y || 10)),
                        Math.max(modelDefinition?.count_x || 10, modelDefinition?.count_y || 10),
                        '#888888',
                        '#444444'
                    ]}
                    position={[0, -blockSize.z * (modelDefinition?.count_z || 5) / 2, 0]}
                    rotation={[0, 0, 0]}
                />
            )}
        </group>
    );
};

export default BlockModelRenderer;
