/**
 * Spatial3DToolbar.jsx
 * 
 * Floating toolbar for 3D visualization tools including:
 * - Surface timeline player
 * - Measurement tools
 * - LOD settings
 * - Surface comparison
 */

import React, { useState } from 'react';
import {
    Clock, Ruler, Settings, Layers, GitCompare,
    ChevronDown, ChevronUp, X
} from 'lucide-react';
import SurfaceTimelinePlayer from '../viewer3d/SurfaceTimelinePlayer';
import MeasurementToolbar3D from '../viewer3d/MeasurementToolbar3D';
import LODSettingsPanel from '../viewer3d/LODSettingsPanel';
import SurfaceComparisonOverlay from '../viewer3d/SurfaceComparisonOverlay';

const ToolButton = ({ icon: Icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all
            ${active
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }
        `}
        title={label}
    >
        <Icon size={16} />
        <span className="hidden lg:inline">{label}</span>
    </button>
);

const Spatial3DToolbar = ({
    siteId,
    surfaceVersions = [],
    currentSurfaceId,
    onSurfaceChange,
    onCompare,
    measurementMode,
    onMeasurementModeChange,
    lodSettings,
    onLODChange,
    className = ''
}) => {
    const [activePanel, setActivePanel] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [playbackSpeed, setPlaybackSpeed] = useState(1);

    const togglePanel = (panel) => {
        setActivePanel(activePanel === panel ? null : panel);
    };

    return (
        <div className={`spatial-3d-toolbar ${className}`}>
            {/* Tool Buttons */}
            <div className="toolbar-buttons">
                <ToolButton
                    icon={Clock}
                    label="Timeline"
                    active={activePanel === 'timeline'}
                    onClick={() => togglePanel('timeline')}
                />
                <ToolButton
                    icon={Ruler}
                    label="Measure"
                    active={activePanel === 'measure'}
                    onClick={() => togglePanel('measure')}
                />
                <ToolButton
                    icon={GitCompare}
                    label="Compare"
                    active={activePanel === 'compare'}
                    onClick={() => togglePanel('compare')}
                />
                <ToolButton
                    icon={Settings}
                    label="Quality"
                    active={activePanel === 'lod'}
                    onClick={() => togglePanel('lod')}
                />
            </div>

            {/* Active Panel */}
            {activePanel && (
                <div className="toolbar-panel">
                    <div className="panel-header">
                        <span className="panel-title">
                            {activePanel === 'timeline' && 'Surface Timeline'}
                            {activePanel === 'measure' && 'Measurement Tools'}
                            {activePanel === 'compare' && 'Surface Comparison'}
                            {activePanel === 'lod' && 'Quality Settings'}
                        </span>
                        <button onClick={() => setActivePanel(null)} className="close-btn">
                            <X size={16} />
                        </button>
                    </div>
                    <div className="panel-content">
                        {activePanel === 'timeline' && (
                            <SurfaceTimelinePlayer
                                versions={surfaceVersions}
                                currentVersionId={currentSurfaceId}
                                onVersionChange={onSurfaceChange}
                                isPlaying={isPlaying}
                                onPlayPause={setIsPlaying}
                                playbackSpeed={playbackSpeed}
                                onSpeedChange={setPlaybackSpeed}
                                onCompare={onCompare}
                            />
                        )}
                        {activePanel === 'measure' && (
                            <MeasurementToolbar3D
                                activeTool={measurementMode}
                                onToolChange={onMeasurementModeChange}
                            />
                        )}
                        {activePanel === 'compare' && (
                            <SurfaceComparisonOverlay
                                versions={surfaceVersions}
                                currentVersionId={currentSurfaceId}
                                onCompare={onCompare}
                            />
                        )}
                        {activePanel === 'lod' && (
                            <LODSettingsPanel
                                settings={lodSettings}
                                onChange={onLODChange}
                            />
                        )}
                    </div>
                </div>
            )}

            <style jsx>{`
                .spatial-3d-toolbar {
                    position: absolute;
                    top: 16px;
                    left: 16px;
                    z-index: 100;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .toolbar-buttons {
                    display: flex;
                    gap: 4px;
                    padding: 4px;
                    background: rgba(15, 23, 42, 0.9);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(8px);
                }

                .toolbar-panel {
                    background: rgba(15, 23, 42, 0.95);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(8px);
                    min-width: 320px;
                    max-width: 400px;
                    overflow: hidden;
                }

                .panel-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background: rgba(0, 0, 0, 0.3);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .panel-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #fff;
                }

                .close-btn {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 28px;
                    height: 28px;
                    background: rgba(255, 255, 255, 0.05);
                    border: none;
                    border-radius: 6px;
                    color: #888;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .close-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    color: #fff;
                }

                .panel-content {
                    max-height: 400px;
                    overflow-y: auto;
                }
            `}</style>
        </div>
    );
};

export default Spatial3DToolbar;
