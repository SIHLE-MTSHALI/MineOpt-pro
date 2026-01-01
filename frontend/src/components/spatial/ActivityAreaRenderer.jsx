import React, { useMemo } from 'react';
import * as THREE from 'three';

const ActivityAreaRenderer = ({ areas = [], onSelect, selectedBlock }) => {
    // Mock Data if empty
    const dummyAreas = useMemo(() => {
        if (areas.length > 0) return areas;
        const items = [];
        // Generate a simple pit layout
        for (let x = 0; x < 10; x++) {
            for (let z = 0; z < 5; z++) {
                items.push({
                    id: `block-${x}-${z}`,
                    position: [x * 50 - 250, 0, z * 50 - 125],
                    color: x % 2 === 0 ? '#3b82f6' : '#ef4444', // Blue (Coal) vs Red (Waste)
                    height: 10 + Math.random() * 5
                });
            }
        }
        return items;
    }, [areas]);

    return (
        <group>
            {dummyAreas.map((area) => {
                const isSelected = selectedBlock && (
                    (area.area_id && area.area_id === selectedBlock.area_id) ||
                    (area.id && area.id === selectedBlock.id)
                );

                return (
                    <mesh
                        key={area.id || area.area_id}
                        position={area.position || area.geometry?.position}
                        castShadow
                        receiveShadow
                        onClick={(e) => {
                            e.stopPropagation();
                            console.log('Clicked Area:', area);
                            if (onSelect) onSelect(area);
                        }}
                    >
                        <boxGeometry args={[48, area.height || 10, 48]} />
                        <meshStandardMaterial
                            color={isSelected ? "#fbbf24" : (area.color || (area.slice_states?.[0]?.material_name === 'Thermal Coal' ? '#0f172a' : '#ef4444'))}
                            roughness={0.7}
                            metalness={0.1}
                            emissive={isSelected ? "#fbbf24" : "black"}
                            emissiveIntensity={isSelected ? 0.5 : 0}
                        />
                        {/* Wireframe overlay for technical look */}
                        <lineSegments>
                            <edgesGeometry args={[new THREE.BoxGeometry(48, area.height || 10, 48)]} />
                            <lineBasicMaterial color={isSelected ? "white" : "black"} linewidth={2} opacity={0.2} transparent />
                        </lineSegments>
                    </mesh>
                );
            })}
        </group>
    );
};

export default ActivityAreaRenderer;
