/**
 * SurfaceToolPanel.jsx - Phase 7
 * 
 * Comprehensive tool panel for surface operations.
 * 
 * Features:
 * - Information tab (metadata, stats)
 * - Edit operations tab (transform, refine)
 * - Analysis tab (slope, profiles, isopach)
 * - Comparison tab (volumes, cut/fill)
 */

import React, { useState, useCallback } from 'react';
import {
    Info,
    Pencil,
    BarChart3,
    GitCompareArrows,
    Ruler,
    Move,
    RotateCw,
    Maximize2,
    FlipHorizontal,
    Scissors,
    Merge,
    Wand2,
    Grid3X3,
    Plus,
    Mountain,
    TrendingUp,
    Layers,
    MapPin,
    Download,
    ChevronDown,
    ChevronUp,
    Play,
    LoaderCircle
} from 'lucide-react';

// Tab definitions
const TABS = [
    { id: 'info', label: 'Info', icon: Info },
    { id: 'edit', label: 'Edit', icon: Pencil },
    { id: 'analysis', label: 'Analysis', icon: BarChart3 },
    { id: 'compare', label: 'Compare', icon: GitCompareArrows }
];

// Collapsible section
const ToolSection = ({ title, children, defaultOpen = true }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="tool-section">
            <button className="section-header" onClick={() => setIsOpen(!isOpen)}>
                <span>{title}</span>
                {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            {isOpen && <div className="section-content">{children}</div>}

            <style jsx>{`
        .tool-section {
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
          padding: 10px 16px;
          border: none;
          background: transparent;
          color: #fff;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          text-align: left;
        }
        .section-header:hover {
          background: rgba(255,255,255,0.05);
        }
        .section-content {
          padding: 0 16px 12px;
        }
      `}</style>
        </div>
    );
};

// Tool button
const ToolButton = ({ icon: Icon, label, onClick, disabled, loading }) => (
    <button
        className={`tool-button ${disabled ? 'disabled' : ''}`}
        onClick={onClick}
        disabled={disabled || loading}
    >
        {loading ? <LoaderCircle size={14} className="spin" /> : <Icon size={14} />}
        <span>{label}</span>

        <style jsx>{`
      .tool-button {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 8px 12px;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        background: rgba(255,255,255,0.05);
        color: #c0c0d0;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.15s ease;
        margin-bottom: 6px;
      }
      .tool-button:hover:not(:disabled) {
        background: rgba(255,255,255,0.1);
        color: #fff;
        border-color: rgba(255,255,255,0.2);
      }
      .tool-button.disabled, .tool-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .spin {
        animation: spin 1s linear infinite;
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `}</style>
    </button>
);

// Info Tab Content
const InfoTab = ({ surface }) => {
    if (!surface) return <div className="empty">No surface selected</div>;

    return (
        <>
            <ToolSection title="Properties">
                <div className="info-row">
                    <span className="label">Name:</span>
                    <span className="value">{surface.name}</span>
                </div>
                <div className="info-row">
                    <span className="label">Type:</span>
                    <span className="value">{surface.surface_type}</span>
                </div>
                <div className="info-row">
                    <span className="label">Seam:</span>
                    <span className="value">{surface.seam_name || '-'}</span>
                </div>
            </ToolSection>

            <ToolSection title="Geometry">
                <div className="info-row">
                    <span className="label">Vertices:</span>
                    <span className="value">{surface.vertex_count?.toLocaleString()}</span>
                </div>
                <div className="info-row">
                    <span className="label">Triangles:</span>
                    <span className="value">{surface.triangle_count?.toLocaleString()}</span>
                </div>
                <div className="info-row">
                    <span className="label">Area:</span>
                    <span className="value">{surface.area_m2?.toLocaleString()} m²</span>
                </div>
            </ToolSection>

            <ToolSection title="Extent" defaultOpen={false}>
                <div className="info-row">
                    <span className="label">Min X:</span>
                    <span className="value">{surface.min_x?.toFixed(2)}</span>
                </div>
                <div className="info-row">
                    <span className="label">Max X:</span>
                    <span className="value">{surface.max_x?.toFixed(2)}</span>
                </div>
                <div className="info-row">
                    <span className="label">Min Y:</span>
                    <span className="value">{surface.min_y?.toFixed(2)}</span>
                </div>
                <div className="info-row">
                    <span className="label">Max Y:</span>
                    <span className="value">{surface.max_y?.toFixed(2)}</span>
                </div>
                <div className="info-row">
                    <span className="label">Min Z:</span>
                    <span className="value">{surface.min_z?.toFixed(2)}</span>
                </div>
                <div className="info-row">
                    <span className="label">Max Z:</span>
                    <span className="value">{surface.max_z?.toFixed(2)}</span>
                </div>
            </ToolSection>

            <style jsx>{`
        .info-row {
          display: flex;
          justify-content: space-between;
          padding: 4px 0;
          font-size: 12px;
        }
        .label { color: #888; }
        .value { color: #fff; font-family: 'SF Mono', monospace; }
        .empty { padding: 20px; text-align: center; color: #666; }
      `}</style>
        </>
    );
};

// Edit Tab Content
const EditTab = ({ surface, onOperation, loadingOp }) => {
    const [params, setParams] = useState({
        translate: { dx: 0, dy: 0, dz: 0 },
        rotate: { angle: 0, centerX: 0, centerY: 0 },
        scale: { factorXY: 1, factorZ: 1 },
        smooth: { iterations: 1, factor: 0.5 },
        simplify: { targetCount: 1000 },
        densify: { maxArea: 100 },
        resample: { gridSpacing: 10 }
    });

    if (!surface) return <div className="empty">No surface selected</div>;

    return (
        <>
            <ToolSection title="Transform">
                <ToolButton
                    icon={Move}
                    label="Translate"
                    onClick={() => onOperation?.('translate', params.translate)}
                    loading={loadingOp === 'translate'}
                />
                <div className="param-grid">
                    <input type="number" placeholder="dX" value={params.translate.dx}
                        onChange={e => setParams({ ...params, translate: { ...params.translate, dx: parseFloat(e.target.value) || 0 } })} />
                    <input type="number" placeholder="dY" value={params.translate.dy}
                        onChange={e => setParams({ ...params, translate: { ...params.translate, dy: parseFloat(e.target.value) || 0 } })} />
                    <input type="number" placeholder="dZ" value={params.translate.dz}
                        onChange={e => setParams({ ...params, translate: { ...params.translate, dz: parseFloat(e.target.value) || 0 } })} />
                </div>

                <ToolButton
                    icon={RotateCw}
                    label="Rotate"
                    onClick={() => onOperation?.('rotate', params.rotate)}
                    loading={loadingOp === 'rotate'}
                />

                <ToolButton
                    icon={Maximize2}
                    label="Scale"
                    onClick={() => onOperation?.('scale', params.scale)}
                    loading={loadingOp === 'scale'}
                />

                <ToolButton
                    icon={FlipHorizontal}
                    label="Mirror"
                    onClick={() => onOperation?.('mirror')}
                    loading={loadingOp === 'mirror'}
                />
            </ToolSection>

            <ToolSection title="Refine">
                <ToolButton
                    icon={Wand2}
                    label={`Smooth (${params.smooth.iterations}x)`}
                    onClick={() => onOperation?.('smooth', params.smooth)}
                    loading={loadingOp === 'smooth'}
                />

                <ToolButton
                    icon={Grid3X3}
                    label={`Simplify (→${params.simplify.targetCount})`}
                    onClick={() => onOperation?.('simplify', params.simplify)}
                    loading={loadingOp === 'simplify'}
                />

                <ToolButton
                    icon={Plus}
                    label="Densify"
                    onClick={() => onOperation?.('densify', params.densify)}
                    loading={loadingOp === 'densify'}
                />

                <ToolButton
                    icon={Grid3X3}
                    label={`Resample (${params.resample.gridSpacing}m)`}
                    onClick={() => onOperation?.('resample', params.resample)}
                    loading={loadingOp === 'resample'}
                />
            </ToolSection>

            <ToolSection title="Geometry">
                <ToolButton
                    icon={Scissors}
                    label="Clip to Boundary"
                    onClick={() => onOperation?.('clip')}
                    loading={loadingOp === 'clip'}
                />

                <ToolButton
                    icon={Merge}
                    label="Merge Surfaces"
                    onClick={() => onOperation?.('merge')}
                    loading={loadingOp === 'merge'}
                />
            </ToolSection>

            <style jsx>{`
        .empty { padding: 20px; text-align: center; color: #666; }
        .param-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 4px;
          margin-bottom: 8px;
        }
        .param-grid input {
          padding: 6px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
      `}</style>
        </>
    );
};

// Analysis Tab Content
const AnalysisTab = ({ surface, onAnalysis, loadingOp }) => {
    const [profileLine, setProfileLine] = useState({ startX: 0, startY: 0, endX: 100, endY: 0, interval: 5 });
    const [slopeGridSize, setSlopeGridSize] = useState(10);

    if (!surface) return <div className="empty">No surface selected</div>;

    return (
        <>
            <ToolSection title="Terrain Analysis">
                <ToolButton
                    icon={Mountain}
                    label="Calculate Slope Map"
                    onClick={() => onAnalysis?.('slope-map', { gridSpacing: slopeGridSize })}
                    loading={loadingOp === 'slope-map'}
                />
                <div className="param-row">
                    <label>Grid Size:</label>
                    <input type="number" value={slopeGridSize} onChange={e => setSlopeGridSize(parseFloat(e.target.value) || 10)} />
                    <span>m</span>
                </div>

                <ToolButton
                    icon={TrendingUp}
                    label="Aspect Map"
                    onClick={() => onAnalysis?.('aspect-map', { gridSpacing: slopeGridSize })}
                    loading={loadingOp === 'aspect-map'}
                />
            </ToolSection>

            <ToolSection title="Profiles">
                <ToolButton
                    icon={Ruler}
                    label="Generate Profile"
                    onClick={() => onAnalysis?.('profile', profileLine)}
                    loading={loadingOp === 'profile'}
                />
                <div className="param-grid-2">
                    <div className="param-row">
                        <label>Start:</label>
                        <input type="number" placeholder="X" value={profileLine.startX}
                            onChange={e => setProfileLine({ ...profileLine, startX: parseFloat(e.target.value) || 0 })} />
                        <input type="number" placeholder="Y" value={profileLine.startY}
                            onChange={e => setProfileLine({ ...profileLine, startY: parseFloat(e.target.value) || 0 })} />
                    </div>
                    <div className="param-row">
                        <label>End:</label>
                        <input type="number" placeholder="X" value={profileLine.endX}
                            onChange={e => setProfileLine({ ...profileLine, endX: parseFloat(e.target.value) || 0 })} />
                        <input type="number" placeholder="Y" value={profileLine.endY}
                            onChange={e => setProfileLine({ ...profileLine, endY: parseFloat(e.target.value) || 0 })} />
                    </div>
                </div>
            </ToolSection>

            <ToolSection title="Sampling">
                <ToolButton
                    icon={MapPin}
                    label="Sample Point"
                    onClick={() => onAnalysis?.('sample-point')}
                    loading={loadingOp === 'sample-point'}
                />

                <ToolButton
                    icon={Ruler}
                    label="Sample Along Line"
                    onClick={() => onAnalysis?.('sample-line', profileLine)}
                    loading={loadingOp === 'sample-line'}
                />
            </ToolSection>

            <style jsx>{`
        .empty { padding: 20px; text-align: center; color: #666; }
        .param-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          font-size: 11px;
          color: #888;
        }
        .param-row input {
          width: 60px;
          padding: 4px 6px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
        .param-grid-2 {
          margin-bottom: 8px;
        }
      `}</style>
        </>
    );
};

// Compare Tab Content
const CompareTab = ({ surfaces, selectedSurface, onCompare, loadingOp }) => {
    const [compareSurfaceId, setCompareSurfaceId] = useState('');
    const [volumeParams, setVolumeParams] = useState({ gridSpacing: 5, density: 1.4 });

    const otherSurfaces = surfaces?.filter(s => s.surface_id !== selectedSurface?.surface_id) || [];

    if (!selectedSurface) return <div className="empty">No surface selected</div>;

    return (
        <>
            <ToolSection title="Compare With">
                <select
                    value={compareSurfaceId}
                    onChange={e => setCompareSurfaceId(e.target.value)}
                    className="surface-select"
                >
                    <option value="">Select surface...</option>
                    {otherSurfaces.map(s => (
                        <option key={s.surface_id} value={s.surface_id}>{s.name}</option>
                    ))}
                </select>
            </ToolSection>

            <ToolSection title="Volume Calculations">
                <ToolButton
                    icon={Layers}
                    label="Calculate Volume Between"
                    onClick={() => onCompare?.('volume', { compareSurfaceId, ...volumeParams })}
                    disabled={!compareSurfaceId}
                    loading={loadingOp === 'volume'}
                />

                <ToolButton
                    icon={GitCompareArrows}
                    label="Cut/Fill Analysis"
                    onClick={() => onCompare?.('cut-fill', { compareSurfaceId, ...volumeParams })}
                    disabled={!compareSurfaceId}
                    loading={loadingOp === 'cut-fill'}
                />

                <div className="param-row">
                    <label>Grid:</label>
                    <input type="number" value={volumeParams.gridSpacing}
                        onChange={e => setVolumeParams({ ...volumeParams, gridSpacing: parseFloat(e.target.value) || 5 })} />
                    <span>m</span>
                </div>

                <div className="param-row">
                    <label>Density:</label>
                    <input type="number" value={volumeParams.density} step="0.1"
                        onChange={e => setVolumeParams({ ...volumeParams, density: parseFloat(e.target.value) || 1.4 })} />
                    <span>t/m³</span>
                </div>
            </ToolSection>

            <ToolSection title="Thickness">
                <ToolButton
                    icon={Layers}
                    label="Isopach Map"
                    onClick={() => onCompare?.('isopach', { compareSurfaceId, ...volumeParams })}
                    disabled={!compareSurfaceId}
                    loading={loadingOp === 'isopach'}
                />
            </ToolSection>

            <style jsx>{`
        .empty { padding: 20px; text-align: center; color: #666; }
        .surface-select {
          width: 100%;
          padding: 8px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
          cursor: pointer;
          margin-bottom: 8px;
        }
        .param-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          font-size: 11px;
          color: #888;
        }
        .param-row input {
          width: 60px;
          padding: 4px 6px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
      `}</style>
        </>
    );
};

// Main Component
const SurfaceToolPanel = ({
    surface,
    surfaces = [],
    onOperation,
    onAnalysis,
    onCompare,
    onExport,
    loadingOp,
    className = ''
}) => {
    const [activeTab, setActiveTab] = useState('info');

    return (
        <div className={`surface-tool-panel ${className}`}>
            {/* Tabs */}
            <div className="tab-bar">
                {TABS.map(tab => {
                    const TabIcon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <TabIcon size={14} />
                            <span>{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Tab Content */}
            <div className="tab-content">
                {activeTab === 'info' && <InfoTab surface={surface} />}
                {activeTab === 'edit' && <EditTab surface={surface} onOperation={onOperation} loadingOp={loadingOp} />}
                {activeTab === 'analysis' && <AnalysisTab surface={surface} onAnalysis={onAnalysis} loadingOp={loadingOp} />}
                {activeTab === 'compare' && <CompareTab surfaces={surfaces} selectedSurface={surface} onCompare={onCompare} loadingOp={loadingOp} />}
            </div>

            {/* Export */}
            <div className="export-section">
                <button className="export-btn" onClick={onExport}>
                    <Download size={14} /> Export Surface
                </button>
            </div>

            <style jsx>{`
        .surface-tool-panel {
          display: flex;
          flex-direction: column;
          background: #1e1e2e;
          border-left: 1px solid rgba(255,255,255,0.1);
          width: 280px;
          height: 100%;
          overflow: hidden;
        }
        
        .tab-bar {
          display: flex;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .tab {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 12px 8px;
          border: none;
          background: transparent;
          color: #888;
          font-size: 10px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .tab:hover {
          background: rgba(255,255,255,0.05);
          color: #fff;
        }
        
        .tab.active {
          color: #60a5fa;
          background: rgba(59, 130, 246, 0.1);
          border-bottom: 2px solid #60a5fa;
        }
        
        .tab-content {
          flex: 1;
          overflow-y: auto;
        }
        
        .export-section {
          padding: 12px 16px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .export-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 10px;
          background: rgba(59, 130, 246, 0.15);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 6px;
          color: #60a5fa;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .export-btn:hover {
          background: rgba(59, 130, 246, 0.25);
        }
      `}</style>
        </div>
    );
};

export default SurfaceToolPanel;
