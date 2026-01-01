import React, { useState } from 'react';
import { Html } from '@react-three/drei';

const StockpileRenderer = ({ stockpiles = [] }) => {
    const [hovered, setHovered] = useState(null);

    return (
        <group>
            {stockpiles.map((pile, idx) => {
                // Calculate Scale based on Tonnage
                // Base size = 1, Max size = 5 (at 100k tons)
                const tons = pile.current_tonnage || 0;
                const scale = 1 + (Math.min(tons, 100000) / 25000);

                // Position: Hardcoded for now based on seed data layout
                // ROM Pad usually near (100, 0, -50). Offset them if multiple.
                const position = [120 + (idx * 50), 0, -50];

                return (
                    <group key={pile.node_id || idx} position={position}>
                        {/* Stockpile Cone */}
                        <mesh
                            position={[0, scale * 2.5, 0]}
                            scale={[scale, scale, scale]}
                            onPointerOver={() => setHovered(pile)}
                            onPointerOut={() => setHovered(null)}
                        >
                            <coneGeometry args={[5, 5, 32]} />
                            <meshStandardMaterial
                                color={tons > 0 ? "#22c55e" : "#334155"}
                                transparent
                                opacity={0.9}
                            />
                        </mesh>

                        {/* Base Indicator */}
                        <mesh rotation={[-Math.PI / 2, 0, 0]}>
                            <ringGeometry args={[scale * 5, scale * 5 + 1, 32]} />
                            <meshBasicMaterial color="#ffffff" opacity={0.3} transparent />
                        </mesh>

                        {/* Label */}
                        <Html position={[0, scale * 5 + 5, 0]} center>
                            <div className="bg-slate-900/80 backdrop-blur px-2 py-1 rounded text-xs text-white border border-slate-700 whitespace-nowrap">
                                <div className="font-bold">{pile.name}</div>
                                <div>{tons.toLocaleString()} t</div>
                                {tons > 0 && <div className="text-amber-400">{pile.current_grade.toFixed(2)} MJ/kg</div>}
                            </div>
                        </Html>
                    </group>
                );
            })}
        </group>
    );
};

export default StockpileRenderer;
