import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Environment, ContactShadows } from '@react-three/drei';
import ActivityAreaRenderer from './ActivityAreaRenderer';
import StockpileRenderer from './StockpileRenderer';

import HaulageRenderer from './HaulageRenderer';

const Viewport3D = ({ siteData, onBlockSelect, selectedBlock }) => {
    return (
        <div className="h-full w-full bg-slate-900">
            <Canvas camera={{ position: [500, 500, 500], fov: 45 }}>
                <Suspense fallback={null}>
                    <Environment preset="city" />
                    <ambientLight intensity={0.5} />
                    <directionalLight position={[100, 100, 50]} intensity={1} castShadow />

                    <group position={[0, -10, 0]}>
                        <Grid infiniteGrid fadeDistance={2000} sectionSize={100} cellSize={10} sectionColor="#475569" cellColor="#334155" />
                        <ContactShadows opacity={0.5} scale={1000} blur={2} far={100} resolution={256} color="#000000" />
                    </group>

                    {/* Render Activity Areas (Mining Blocks) */}
                    <ActivityAreaRenderer
                        areas={siteData.activityAreas}
                        onSelect={onBlockSelect}
                        selectedBlock={selectedBlock}
                    />

                    {/* Render Stockpiles */}
                    <StockpileRenderer stockpiles={siteData.stockpiles} />

                    {/* Render Simulation (Active Tasks) */}
                    <HaulageRenderer
                        activeTasks={siteData.activeTasks}
                        activityAreas={siteData.activityAreas}
                        stockpiles={siteData.stockpiles}
                    />

                    <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2.1} />
                </Suspense>
            </Canvas>

            {/* Overlay UI for Tooltips/Controls could go here */}
            <div className="absolute top-4 right-4 bg-black/50 p-2 rounded text-xs text-white">
                MineOpt Pro 3D Engine
            </div>
        </div>
    );
};

export default Viewport3D;
