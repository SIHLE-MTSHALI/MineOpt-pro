/**
 * Viewport3D.jsx - Enhanced 3D Mine Visualization
 * 
 * Main 3D canvas component providing:
 * - Interactive mining block selection
 * - Multi-select support (Ctrl+click)
 * - Stockpile visualization
 * - Haulage route animation
 * - Measurement tools
 * - Screenshot capability
 */

import React, { Suspense, useState, useCallback, useRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Environment, ContactShadows, PerspectiveCamera, Stats } from '@react-three/drei';
import {
    Camera, ZoomIn, ZoomOut, RotateCcw, Maximize2,
    Layers, Eye, EyeOff, Grid as GridIcon
} from 'lucide-react';
import ActivityAreaRenderer from './ActivityAreaRenderer';
import StockpileRenderer from './StockpileRenderer';
import HaulageRenderer from './HaulageRenderer';

/**
 * Camera controller for zoom and reset
 */
const CameraController = ({ zoom, onZoomChange }) => {
    const { camera } = useThree();

    React.useEffect(() => {
        if (camera) {
            const distance = 500 / zoom;
            camera.position.set(distance, distance, distance);
            camera.updateProjectionMatrix();
        }
    }, [zoom, camera]);

    return null;
};

/**
 * Main Viewport component
 */
const Viewport3D = ({
    siteData,
    onBlockSelect,
    selectedBlock,
    selectedBlocks = [],
    onMultiSelect,
    showStats = false
}) => {
    const [hoveredBlock, setHoveredBlock] = useState(null);
    const [showGrid, setShowGrid] = useState(true);
    const [showStockpiles, setShowStockpiles] = useState(true);
    const [showHaulage, setShowHaulage] = useState(true);
    const [zoom, setZoom] = useState(1);
    const canvasRef = useRef();

    /**
     * Handle block selection (single or multi)
     */
    const handleBlockSelect = useCallback((block, isMulti) => {
        if (isMulti && onMultiSelect) {
            onMultiSelect(block);
        } else if (onBlockSelect) {
            onBlockSelect(block);
        }
    }, [onBlockSelect, onMultiSelect]);

    /**
     * Handle screenshot
     */
    const handleScreenshot = useCallback(() => {
        if (canvasRef.current) {
            const canvas = canvasRef.current.querySelector('canvas');
            if (canvas) {
                const link = document.createElement('a');
                link.download = `mineopt-3d-${Date.now()}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            }
        }
    }, []);

    /**
     * Reset camera position
     */
    const handleResetCamera = useCallback(() => {
        setZoom(1);
    }, []);

    return (
        <div ref={canvasRef} className="h-full w-full bg-slate-900 relative">
            <Canvas
                shadows
                gl={{ preserveDrawingBuffer: true }}
                camera={{ position: [500, 500, 500], fov: 45 }}
            >
                <Suspense fallback={null}>
                    <Environment preset="city" />
                    <ambientLight intensity={0.4} />
                    <directionalLight
                        position={[200, 300, 100]}
                        intensity={1.2}
                        castShadow
                        shadow-mapSize={[2048, 2048]}
                    />
                    <directionalLight position={[-100, 100, -100]} intensity={0.3} />

                    {/* Camera controller */}
                    <CameraController zoom={zoom} />

                    {/* Base grid and ground plane */}
                    {showGrid && (
                        <group position={[0, -10, 0]}>
                            <Grid
                                infiniteGrid
                                fadeDistance={1500}
                                sectionSize={100}
                                cellSize={20}
                                sectionColor="#475569"
                                cellColor="#334155"
                            />
                            <ContactShadows
                                opacity={0.4}
                                scale={1500}
                                blur={2}
                                far={150}
                                resolution={512}
                                color="#000000"
                            />
                        </group>
                    )}

                    {/* Render Activity Areas (Mining Blocks) */}
                    <ActivityAreaRenderer
                        areas={siteData?.activityAreas || []}
                        onSelect={handleBlockSelect}
                        selectedBlock={selectedBlock}
                        selectedBlocks={selectedBlocks}
                        onHover={setHoveredBlock}
                    />

                    {/* Render Stockpiles */}
                    {showStockpiles && (
                        <StockpileRenderer stockpiles={siteData?.flowNodes || []} />
                    )}

                    {/* Render Haulage Routes */}
                    {showHaulage && (
                        <HaulageRenderer
                            activeTasks={siteData?.activeTasks || []}
                            activityAreas={siteData?.activityAreas || []}
                            stockpiles={siteData?.flowNodes || []}
                        />
                    )}

                    <OrbitControls
                        makeDefault
                        minPolarAngle={0.1}
                        maxPolarAngle={Math.PI / 2.1}
                        minDistance={100}
                        maxDistance={2000}
                        enableDamping
                        dampingFactor={0.05}
                    />

                    {showStats && <Stats />}
                </Suspense>
            </Canvas>

            {/* Toolbar overlay */}
            <div className="absolute top-4 left-4 flex flex-col space-y-2">
                {/* Layer toggles */}
                <div className="bg-slate-900/90 rounded-lg p-2 flex flex-col space-y-1">
                    <button
                        onClick={() => setShowGrid(!showGrid)}
                        className={`p-2 rounded transition-colors ${showGrid ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                        title="Toggle Grid"
                    >
                        <GridIcon size={16} />
                    </button>
                    <button
                        onClick={() => setShowStockpiles(!showStockpiles)}
                        className={`p-2 rounded transition-colors ${showStockpiles ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                        title="Toggle Stockpiles"
                    >
                        <Layers size={16} />
                    </button>
                    <button
                        onClick={() => setShowHaulage(!showHaulage)}
                        className={`p-2 rounded transition-colors ${showHaulage ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                        title="Toggle Haulage"
                    >
                        {showHaulage ? <Eye size={16} /> : <EyeOff size={16} />}
                    </button>
                </div>

                {/* Zoom controls */}
                <div className="bg-slate-900/90 rounded-lg p-2 flex flex-col space-y-1">
                    <button
                        onClick={() => setZoom(Math.min(zoom + 0.2, 3))}
                        className="p-2 rounded bg-slate-800 text-slate-400 hover:bg-slate-700"
                        title="Zoom In"
                    >
                        <ZoomIn size={16} />
                    </button>
                    <button
                        onClick={() => setZoom(Math.max(zoom - 0.2, 0.3))}
                        className="p-2 rounded bg-slate-800 text-slate-400 hover:bg-slate-700"
                        title="Zoom Out"
                    >
                        <ZoomOut size={16} />
                    </button>
                    <button
                        onClick={handleResetCamera}
                        className="p-2 rounded bg-slate-800 text-slate-400 hover:bg-slate-700"
                        title="Reset View"
                    >
                        <RotateCcw size={16} />
                    </button>
                </div>

                {/* Screenshot */}
                <div className="bg-slate-900/90 rounded-lg p-2">
                    <button
                        onClick={handleScreenshot}
                        className="p-2 rounded bg-slate-800 text-slate-400 hover:bg-slate-700"
                        title="Screenshot"
                    >
                        <Camera size={16} />
                    </button>
                </div>
            </div>

            {/* Info overlay */}
            <div className="absolute top-4 right-4 bg-slate-900/90 p-3 rounded-lg text-xs text-white min-w-40">
                <div className="font-medium mb-2 text-slate-300">MineOpt Pro 3D</div>
                <div className="space-y-1 text-slate-400">
                    <div>Areas: <span className="text-white">{siteData?.activityAreas?.length || 'Demo'}</span></div>
                    <div>Stockpiles: <span className="text-white">{siteData?.flowNodes?.filter(n => n.node_type === 'Stockpile').length || 0}</span></div>
                    {selectedBlock && (
                        <div className="mt-2 pt-2 border-t border-slate-700">
                            <div className="text-blue-400">Selected:</div>
                            <div className="text-white">{selectedBlock.name || selectedBlock.area_id?.slice(0, 8)}</div>
                        </div>
                    )}
                    {selectedBlocks.length > 1 && (
                        <div className="text-amber-400">{selectedBlocks.length} blocks selected</div>
                    )}
                </div>
            </div>

            {/* Hovered block tooltip */}
            {hoveredBlock && !selectedBlock && (
                <div className="absolute bottom-4 left-4 bg-slate-900/95 p-3 rounded-lg text-xs text-white">
                    <div className="font-medium">{hoveredBlock.name || 'Mining Block'}</div>
                    <div className="text-slate-400 mt-1">Click to select, Ctrl+Click for multi-select</div>
                </div>
            )}

            {/* Legend */}
            <div className="absolute bottom-4 right-4 bg-slate-900/90 p-3 rounded-lg text-xs text-white">
                <div className="font-medium mb-2 text-slate-300">Legend</div>
                <div className="space-y-1">
                    <div className="flex items-center">
                        <span className="w-3 h-3 bg-blue-500 rounded mr-2"></span>
                        <span className="text-slate-400">Available</span>
                    </div>
                    <div className="flex items-center">
                        <span className="w-3 h-3 bg-green-500 rounded mr-2"></span>
                        <span className="text-slate-400">Released</span>
                    </div>
                    <div className="flex items-center">
                        <span className="w-3 h-3 bg-amber-500 rounded mr-2"></span>
                        <span className="text-slate-400">Mining</span>
                    </div>
                    <div className="flex items-center">
                        <span className="w-3 h-3 bg-gray-500 rounded mr-2"></span>
                        <span className="text-slate-400">Complete</span>
                    </div>
                    <div className="flex items-center">
                        <span className="w-3 h-3 bg-red-500 rounded mr-2"></span>
                        <span className="text-slate-400">Locked</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Viewport3D;
