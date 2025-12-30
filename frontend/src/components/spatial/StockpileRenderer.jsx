import React from 'react';

const StockpileRenderer = ({ stockpiles = [] }) => {
    // Mock Data
    const dummyStockpiles = [
        { id: 'rom-1', position: [300, 0, 0], color: '#10b981', size: 80, label: 'ROM Pad A' },
        { id: 'rom-2', position: [300, 0, 150], color: '#f59e0b', size: 60, label: 'Product Stockpile' },
    ];

    return (
        <group>
            {dummyStockpiles.map((pile) => (
                <group key={pile.id} position={pile.position}>
                    {/* Cone shape for stockpile */}
                    <mesh castShadow receiveShadow>
                        <coneGeometry args={[pile.size / 2, pile.size / 2, 32]} />
                        <meshStandardMaterial color={pile.color} />
                    </mesh>
                    {/* Label Base */}
                    <mesh position={[0, 0, pile.size / 2 + 10]} rotation={[-Math.PI / 2, 0, 0]}>
                        <circleGeometry args={[10, 32]} />
                        <meshBasicMaterial color="white" opacity={0.5} transparent />
                    </mesh>
                </group>
            ))}
        </group>
    );
};

export default StockpileRenderer;
