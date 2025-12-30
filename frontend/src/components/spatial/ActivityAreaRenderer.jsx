import React, { useMemo } from 'react';
import * as THREE from 'three';

const ActivityAreaRenderer = ({ areas = [] }) => {
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
            {dummyAreas.map((area) => (
                <mesh key={area.id} position={area.position} castShadow receiveShadow onClick={(e) => {
                    e.stopPropagation();
                    console.log('Clicked Area:', area.id);
                }}>
                    <boxGeometry args={[48, area.height, 48]} />
                    <meshStandardMaterial color={area.color} roughness={0.7} metalness={0.1} />
                    {/* Wireframe overlay for technical look */}
                    <lineSegments>
                        <edgesGeometry args={[new THREE.BoxGeometry(48, area.height, 48)]} />
                        <lineBasicMaterial color="black" linewidth={1} opacity={0.2} transparent />
                    </lineSegments>
                </mesh>
            ))}
        </group>
    );
};

export default ActivityAreaRenderer;
