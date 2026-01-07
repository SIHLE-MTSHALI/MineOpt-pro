/**
 * RasterLayerPanel.jsx - Phase 9
 * 
 * Panel for managing raster/DEM layers.
 * 
 * Features:
 * - Raster file upload/import
 * - Layer visibility and opacity controls
 * - Color scheme/rendering options
 * - Metadata display
 * - Transform to TIN option
 */

import React, { useState, useCallback } from 'react';
import {
    Image,
    Upload,
    Eye,
    EyeOff,
    Trash2,
    Info,
    Palette,
    Layers,
    Mountain,
    Grid3X3,
    ChevronDown,
    ChevronUp,
    Settings,
    Download,
    RefreshCw
} from 'lucide-react';

// Rendering modes
const RENDER_MODES = [
    { id: 'elevation', name: 'Elevation', description: 'Color by elevation' },
    { id: 'hillshade', name: 'Hillshade', description: 'Shaded relief' },
    { id: 'slope', name: 'Slope', description: 'Color by slope' },
    { id: 'aspect', name: 'Aspect', description: 'Color by aspect' },
    { id: 'rgb', name: 'RGB/Image', description: 'Show as image' }
];

// Color ramps
const COLOR_RAMPS = [
    { id: 'terrain', name: 'Terrain', colors: ['#00441b', '#1b7837', '#5aae61', '#a6dba0', '#d9f0d3', '#f7f7f7', '#e7d4e8', '#c2a5cf', '#9970ab', '#762a83', '#40004b'] },
    { id: 'viridis', name: 'Viridis', colors: ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'] },
    { id: 'grayscale', name: 'Grayscale', colors: ['#000000', '#333333', '#666666', '#999999', '#cccccc', '#ffffff'] },
    { id: 'hot', name: 'Hot', colors: ['#000000', '#e60000', '#ffc000', '#ffff00', '#ffffff'] }
];

// Raster layer item
const RasterLayerItem = ({
    layer,
    isExpanded,
    onToggle,
    onVisibilityChange,
    onOpacityChange,
    onRenderModeChange,
    onColorRampChange,
    onRemove,
    onConvertToTIN
}) => {
    return (
        <div className={`raster-layer-item ${isExpanded ? 'expanded' : ''}`}>
            {/* Header */}
            <div className="layer-header" onClick={() => onToggle?.(layer.id)}>
                <button
                    className={`visibility-btn ${layer.visible ? '' : 'off'}`}
                    onClick={(e) => { e.stopPropagation(); onVisibilityChange?.(layer.id, !layer.visible); }}
                >
                    {layer.visible ? <Eye size={14} /> : <EyeOff size={14} />}
                </button>

                <Image size={16} className="layer-icon" />

                <div className="layer-info">
                    <div className="layer-name">{layer.name}</div>
                    <div className="layer-size">{layer.width}×{layer.height}</div>
                </div>

                <span className="expand-icon">
                    {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </span>
            </div>

            {/* Expanded Controls */}
            {isExpanded && (
                <div className="layer-controls">
                    {/* Opacity */}
                    <div className="control-row">
                        <label>Opacity</label>
                        <input
                            type="range"
                            min={0}
                            max={1}
                            step={0.05}
                            value={layer.opacity || 1}
                            onChange={(e) => onOpacityChange?.(layer.id, parseFloat(e.target.value))}
                        />
                        <span className="value">{Math.round((layer.opacity || 1) * 100)}%</span>
                    </div>

                    {/* Render Mode */}
                    <div className="control-row">
                        <label>Display</label>
                        <select
                            value={layer.renderMode || 'elevation'}
                            onChange={(e) => onRenderModeChange?.(layer.id, e.target.value)}
                        >
                            {RENDER_MODES.map(mode => (
                                <option key={mode.id} value={mode.id}>{mode.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Color Ramp (for elevation-based modes) */}
                    {['elevation', 'slope'].includes(layer.renderMode || 'elevation') && (
                        <div className="control-row">
                            <label>Colors</label>
                            <div className="color-ramps">
                                {COLOR_RAMPS.map(ramp => (
                                    <button
                                        key={ramp.id}
                                        className={`ramp-btn ${layer.colorRamp === ramp.id ? 'active' : ''}`}
                                        onClick={() => onColorRampChange?.(layer.id, ramp.id)}
                                        title={ramp.name}
                                    >
                                        <div className="ramp-preview">
                                            {ramp.colors.slice(0, 5).map((c, i) => (
                                                <div key={i} style={{ background: c }} />
                                            ))}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Metadata */}
                    <div className="metadata">
                        <div className="meta-row">
                            <span>Format:</span>
                            <span>{layer.format || 'GeoTIFF'}</span>
                        </div>
                        <div className="meta-row">
                            <span>CRS:</span>
                            <span>{layer.crs || 'Unknown'}</span>
                        </div>
                        <div className="meta-row">
                            <span>Resolution:</span>
                            <span>{layer.resolution?.toFixed(2) || '-'} m</span>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="layer-actions">
                        <button className="action-btn" onClick={() => onConvertToTIN?.(layer.id)}>
                            <Mountain size={12} /> Convert to TIN
                        </button>
                        <button className="action-btn delete" onClick={() => onRemove?.(layer.id)}>
                            <Trash2 size={12} /> Remove
                        </button>
                    </div>
                </div>
            )}

            <style jsx>{`
        .raster-layer-item {
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          margin-bottom: 6px;
          overflow: hidden;
        }
        
        .layer-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 12px;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        
        .layer-header:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .visibility-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #4ade80;
          cursor: pointer;
        }
        
        .visibility-btn.off {
          color: #666;
        }
        
        .layer-icon {
          color: #60a5fa;
        }
        
        .layer-info {
          flex: 1;
          min-width: 0;
        }
        
        .layer-name {
          font-size: 12px;
          font-weight: 500;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .layer-size {
          font-size: 10px;
          color: #666;
        }
        
        .expand-icon {
          color: #666;
        }
        
        .layer-controls {
          padding: 0 12px 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .control-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 10px;
        }
        
        .control-row label {
          min-width: 50px;
          font-size: 11px;
          color: #888;
        }
        
        .control-row input[type="range"] {
          flex: 1;
        }
        
        .control-row select {
          flex: 1;
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
        
        .control-row .value {
          min-width: 35px;
          font-size: 10px;
          color: #888;
          text-align: right;
        }
        
        .color-ramps {
          display: flex;
          gap: 4px;
        }
        
        .ramp-btn {
          padding: 4px;
          background: transparent;
          border: 2px solid transparent;
          border-radius: 4px;
          cursor: pointer;
        }
        
        .ramp-btn.active {
          border-color: #60a5fa;
        }
        
        .ramp-preview {
          display: flex;
          width: 40px;
          height: 8px;
          border-radius: 2px;
          overflow: hidden;
        }
        
        .ramp-preview > div {
          flex: 1;
        }
        
        .metadata {
          margin-top: 10px;
          padding: 8px;
          background: rgba(0,0,0,0.2);
          border-radius: 4px;
        }
        
        .meta-row {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          margin-bottom: 4px;
        }
        
        .meta-row span:first-child { color: #666; }
        .meta-row span:last-child { color: #a0a0b0; }
        
        .layer-actions {
          display: flex;
          gap: 6px;
          margin-top: 10px;
        }
        
        .action-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 6px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #a0a0b0;
          font-size: 10px;
          cursor: pointer;
        }
        
        .action-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .action-btn.delete:hover { color: #f87171; border-color: rgba(239, 68, 68, 0.3); }
      `}</style>
        </div>
    );
};

// Main panel component
const RasterLayerPanel = ({
    layers = [],
    onUpload,
    onVisibilityChange,
    onOpacityChange,
    onRenderModeChange,
    onColorRampChange,
    onRemove,
    onConvertToTIN,
    className = ''
}) => {
    const [expandedId, setExpandedId] = useState(null);
    const [isUploading, setIsUploading] = useState(false);

    // Handle file drop
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer?.files || []);
        const rasterFiles = files.filter(f =>
            /\.(tif|tiff|ecw|jp2|sid|asc|png)$/i.test(f.name)
        );
        if (rasterFiles.length) {
            onUpload?.(rasterFiles);
        }
    }, [onUpload]);

    const handleDragOver = (e) => e.preventDefault();

    return (
        <div className={`raster-layer-panel ${className}`}>
            {/* Header */}
            <div className="panel-header">
                <div className="title">
                    <Image size={16} />
                    <span>Raster Layers</span>
                </div>
                <span className="count">{layers.length}</span>
            </div>

            {/* Upload Zone */}
            <div
                className={`upload-zone ${isUploading ? 'uploading' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
            >
                <Upload size={20} />
                <span>Drop raster files here</span>
                <span className="formats">GeoTIFF, ECW, JP2, PNG</span>
            </div>

            {/* Layer List */}
            <div className="layer-list">
                {layers.length === 0 ? (
                    <div className="empty-state">
                        <Grid3X3 size={24} />
                        <p>No raster layers</p>
                    </div>
                ) : (
                    layers.map(layer => (
                        <RasterLayerItem
                            key={layer.id}
                            layer={layer}
                            isExpanded={expandedId === layer.id}
                            onToggle={(id) => setExpandedId(expandedId === id ? null : id)}
                            onVisibilityChange={onVisibilityChange}
                            onOpacityChange={onOpacityChange}
                            onRenderModeChange={onRenderModeChange}
                            onColorRampChange={onColorRampChange}
                            onRemove={onRemove}
                            onConvertToTIN={onConvertToTIN}
                        />
                    ))
                )}
            </div>

            <style jsx>{`
        .raster-layer-panel {
          display: flex;
          flex-direction: column;
          background: #1e1e2e;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 600;
          color: #fff;
        }
        
        .count {
          padding: 2px 8px;
          background: rgba(59, 130, 246, 0.2);
          border-radius: 10px;
          font-size: 11px;
          color: #60a5fa;
        }
        
        .upload-zone {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 16px;
          margin: 12px;
          background: rgba(59, 130, 246, 0.05);
          border: 2px dashed rgba(59, 130, 246, 0.3);
          border-radius: 8px;
          color: #60a5fa;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .upload-zone:hover {
          background: rgba(59, 130, 246, 0.1);
          border-color: rgba(59, 130, 246, 0.5);
        }
        
        .upload-zone .formats {
          font-size: 10px;
          color: #666;
        }
        
        .layer-list {
          flex: 1;
          overflow-y: auto;
          padding: 0 12px 12px;
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 24px;
          color: #666;
          text-align: center;
        }
        
        .empty-state p {
          margin-top: 8px;
          font-size: 12px;
        }
      `}</style>
        </div>
    );
};

export default RasterLayerPanel;
