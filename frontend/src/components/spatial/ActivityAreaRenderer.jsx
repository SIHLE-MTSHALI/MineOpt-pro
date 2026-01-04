/**
 * ActivityAreaRenderer.jsx - Enhanced Mining Area 3D Visualization
 * 
 * Provides rich visualization of mining activity areas with:
 * - Click selection with highlight
 * - Slice state visualization (Available/Mining/Complete)
 * - Priority indicators
 * - Hover tooltips
 * - Multi-select support (Ctrl+click)
 * - Status-based coloring and hatching patterns
 */

import React, { useMemo, useState, useRef } from 'react';
import * as THREE from 'three';
import { Text, Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';

/**
 * Status colors for mining areas
 */
const STATUS_COLORS = {
    Available: '#3b82f6',    // Blue - ready to mine
    Released: '#22c55e',     // Green - released for mining
    Mining: '#f59e0b',       // Amber - currently being mined
    Complete: '#6b7280',     // Gray - completed
    Locked: '#ef4444',       // Red - locked/exclusion
    Waste: '#64748b'         // Slate - waste material
};

/**
 * Material type colors
 */
const MATERIAL_COLORS = {
    'Thermal Coal': '#1e3a5f',
    'Coal': '#0f172a',
    'Waste': '#78716c',
    'Overburden': '#92400e',
    'Interburden': '#7c2d12'
};

/**
 * Single Activity Area Mesh with interaction
 */
const ActivityAreaMesh = ({
    area,
    isSelected,
    isHovered,
    onSelect,
    onHover,
    multiSelect = false
}) => {
    const meshRef = useRef();
    const [localHover, setLocalHover] = useState(false);

    // Calculate position from geometry or default
    const position = useMemo(() => {
        if (area.geometry?.position) return area.geometry.position;
        if (area.position) return area.position;
        // Calculate from centroid if available
        if (area.geometry_centroid) {
            return [area.geometry_centroid.x || 0, 0, area.geometry_centroid.y || 0];
        }
        return [0, 0, 0];
    }, [area]);

    // Determine slice info
    const sliceStates = area.slice_states || [];
    const activeSlice = sliceStates.find(s => s.status === 'Mining') || sliceStates[0] || {};
    const completedSlices = sliceStates.filter(s => s.status === 'Complete').length;
    const totalSlices = sliceStates.length || 1;
    const progress = totalSlices > 0 ? (completedSlices / totalSlices) : 0;

    // Get status-based color
    const baseColor = useMemo(() => {
        if (area.is_locked) return STATUS_COLORS.Locked;
        if (activeSlice.status === 'Mining') return STATUS_COLORS.Mining;
        if (activeSlice.status === 'Complete') return STATUS_COLORS.Complete;
        if (activeSlice.status === 'Released') return STATUS_COLORS.Released;

        // Material-based default
        const materialName = activeSlice.material_name || area.material_type || 'Coal';
        return MATERIAL_COLORS[materialName] || STATUS_COLORS.Available;
    }, [area, activeSlice]);

    // Calculate height based on remaining quantity
    const height = useMemo(() => {
        const totalQty = sliceStates.reduce((sum, s) => sum + (s.quantity || 0), 0);
        const remainingQty = sliceStates
            .filter(s => s.status !== 'Complete')
            .reduce((sum, s) => sum + (s.quantity || 0), 0);

        const maxHeight = area.height || 15;
        if (totalQty === 0) return maxHeight;
        return Math.max(2, maxHeight * (remainingQty / totalQty));
    }, [area, sliceStates]);

    // Animation for selected/hovered state
    useFrame((state) => {
        if (meshRef.current) {
            if (isSelected) {
                meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.5;
            } else if (localHover) {
                meshRef.current.scale.setScalar(1.02);
            } else {
                meshRef.current.scale.setScalar(1);
                meshRef.current.position.y = position[1];
            }
        }
    });

    const handleClick = (e) => {
        e.stopPropagation();
        const isMulti = e.nativeEvent?.ctrlKey || e.nativeEvent?.metaKey;
        onSelect?.(area, isMulti);
    };

    const handlePointerOver = (e) => {
        e.stopPropagation();
        setLocalHover(true);
        onHover?.(area);
        document.body.style.cursor = 'pointer';
    };

    const handlePointerOut = () => {
        setLocalHover(false);
        onHover?.(null);
        document.body.style.cursor = 'auto';
    };

    // Priority indicator
    const priorityColor = area.priority >= 3 ? '#ef4444' :
        area.priority === 2 ? '#f59e0b' : '#22c55e';

    return (
        <group>
            {/* Main mesh */}
            <mesh
                ref={meshRef}
                position={position}
                castShadow
                receiveShadow
                onClick={handleClick}
                onPointerOver={handlePointerOver}
                onPointerOut={handlePointerOut}
            >
                <boxGeometry args={[46, height, 46]} />
                <meshStandardMaterial
                    color={isSelected ? '#fbbf24' : (localHover ? '#60a5fa' : baseColor)}
                    roughness={0.7}
                    metalness={0.1}
                    emissive={isSelected ? '#fbbf24' : (localHover ? '#3b82f6' : 'black')}
                    emissiveIntensity={isSelected ? 0.4 : (localHover ? 0.2 : 0)}
                />

                {/* Wireframe overlay */}
                <lineSegments>
                    <edgesGeometry args={[new THREE.BoxGeometry(46, height, 46)]} />
                    <lineBasicMaterial
                        color={isSelected ? 'white' : (localHover ? '#93c5fd' : '#1e293b')}
                        linewidth={2}
                        opacity={0.5}
                        transparent
                    />
                </lineSegments>
            </mesh>

            {/* Progress bar (completion indicator) */}
            {progress > 0 && progress < 1 && (
                <mesh position={[position[0], position[1] + height / 2 + 1, position[2]]}>
                    <boxGeometry args={[46 * progress, 1, 2]} />
                    <meshBasicMaterial color="#22c55e" transparent opacity={0.8} />
                </mesh>
            )}

            {/* Priority indicator (top corner) */}
            {area.priority >= 2 && (
                <mesh position={[position[0] + 20, position[1] + height / 2 + 3, position[2] + 20]}>
                    <sphereGeometry args={[2, 8, 8]} />
                    <meshBasicMaterial color={priorityColor} />
                </mesh>
            )}

            {/* Area name label (visible when selected or hovered) */}
            {(isSelected || localHover) && (
                <Text
                    position={[position[0], position[1] + height / 2 + 5, position[2]]}
                    fontSize={5}
                    color="white"
                    anchorX="center"
                    anchorY="bottom"
                    outlineWidth={0.3}
                    outlineColor="black"
                >
                    {area.name || area.area_id?.slice(0, 8) || 'Area'}
                </Text>
            )}

            {/* Hover tooltip */}
            {localHover && !isSelected && (
                <Html
                    position={[position[0] + 30, position[1] + height / 2 + 10, position[2]]}
                    style={{ pointerEvents: 'none' }}
                >
                    <div className="bg-slate-900/95 text-white text-xs p-2 rounded-lg shadow-xl min-w-32">
                        <div className="font-medium">{area.name || 'Mining Area'}</div>
                        <div className="text-slate-400 mt-1">
                            Status: <span className="text-white">{activeSlice.status || 'Available'}</span>
                        </div>
                        {activeSlice.quantity && (
                            <div className="text-slate-400">
                                Qty: <span className="text-white">{activeSlice.quantity.toLocaleString()}t</span>
                            </div>
                        )}
                        <div className="text-slate-400">
                            Priority: <span className="text-white">{area.priority || 1}</span>
                        </div>
                    </div>
                </Html>
            )}

            {/* Locked indicator overlay */}
            {area.is_locked && (
                <mesh position={position} rotation={[0, Math.PI / 4, 0]}>
                    <planeGeometry args={[48, 48]} />
                    <meshBasicMaterial
                        color="#ef4444"
                        transparent
                        opacity={0.3}
                        side={THREE.DoubleSide}
                    />
                </mesh>
            )}
        </group>
    );
};

/**
 * Main Activity Area Renderer Component
 */
const ActivityAreaRenderer = ({
    areas = [],
    onSelect,
    selectedBlock,
    selectedBlocks = [],
    onHover
}) => {
    const [hoveredArea, setHoveredArea] = useState(null);

    // Generate dummy data if no areas provided
    const displayAreas = useMemo(() => {
        if (areas.length > 0) return areas;

        // Generate demo pit layout
        const items = [];
        for (let x = 0; x < 8; x++) {
            for (let z = 0; z < 4; z++) {
                const isCoal = (x + z) % 3 !== 0;
                const status = Math.random() > 0.7 ? 'Complete' :
                    Math.random() > 0.5 ? 'Mining' : 'Available';

                items.push({
                    id: `demo-block-${x}-${z}`,
                    area_id: `demo-block-${x}-${z}`,
                    name: `Block ${String.fromCharCode(65 + x)}${z + 1}`,
                    position: [x * 52 - 200, 0, z * 52 - 100],
                    height: 8 + Math.random() * 12,
                    material_type: isCoal ? 'Thermal Coal' : 'Waste',
                    priority: Math.floor(Math.random() * 3) + 1,
                    is_locked: Math.random() > 0.95,
                    slice_states: [{
                        status: status,
                        quantity: Math.round(2000 + Math.random() * 8000),
                        material_name: isCoal ? 'Thermal Coal' : 'Waste'
                    }]
                });
            }
        }
        return items;
    }, [areas]);

    // Check if an area is selected
    const isSelected = (area) => {
        const areaId = area.area_id || area.id;
        if (selectedBlocks.length > 0) {
            return selectedBlocks.some(b => (b.area_id || b.id) === areaId);
        }
        if (selectedBlock) {
            return (selectedBlock.area_id || selectedBlock.id) === areaId;
        }
        return false;
    };

    const handleHover = (area) => {
        setHoveredArea(area);
        onHover?.(area);
    };

    return (
        <group>
            {displayAreas.map((area) => (
                <ActivityAreaMesh
                    key={area.area_id || area.id}
                    area={area}
                    isSelected={isSelected(area)}
                    isHovered={hoveredArea?.id === area.id || hoveredArea?.area_id === area.area_id}
                    onSelect={onSelect}
                    onHover={handleHover}
                />
            ))}
        </group>
    );
};

export default ActivityAreaRenderer;
