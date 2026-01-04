import React, { useState } from 'react';
import { Html } from '@react-three/drei';

const StockpileRenderer = ({ stockpiles = [] }) => {
    const [hovered, setHovered] = useState(null);

    return (
        <group>
            {stockpiles.map((node, idx) => {
                // Enterprise Model: node.node_type = "Stockpile" | "Dump" | "WashPlant"
                // Config is nested in node.stockpile_config or similar (if joined)
                // But simplified for now: logic based on node_type

                if (node.node_type !== 'Stockpile' && node.node_type !== 'Dump') return null;

                const isStockpile = node.node_type === 'Stockpile';

                // Safe Access to nested config (FastAPI might flatten or nest)
                // Assuming standard Pydantic/ORM serialization where relationships are included if eager loaded
                // If not, fallbacks to 0.
                const config = node.stockpile_config || {};
                const tons = config.current_inventory_tonnes || 0;

                // Scale
                const scale = 1 + (Math.min(tons, 100000) / 25000);

                // Position: from node.location_geometry.position
                const posData = node.location_geometry?.position || [120 + (idx * 50), 0, -50];
                const position = [posData[0], posData[1], posData[2]];

                return (
                    <group key={node.node_id || idx} position={position}>
                        {/* Stockpile Cone */}
                        <mesh
                            position={[0, scale * 2.5, 0]}
                            scale={[scale, scale, scale]}
                            onPointerOver={() => setHovered(node)}
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
                                <div className="font-bold">{node.name}</div>
                                <div>{tons.toLocaleString()} t</div>
                                {tons > 0 && <div className="text-amber-400">{(node.current_grade || 0).toFixed(2)} MJ/kg</div>}
                            </div>
                        </Html>
                    </group>
                );
            })}
        </group>
    );
};

export default StockpileRenderer;
