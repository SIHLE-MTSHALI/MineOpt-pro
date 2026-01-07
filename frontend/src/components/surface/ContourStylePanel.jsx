/**
 * ContourStylePanel.jsx - Phase 7
 * 
 * Panel for configuring contour display styles.
 * 
 * Features:
 * - Contour interval settings
 * - Color scheme selection
 * - Index/intermediate contour styling
 * - Label settings
 * - Layer visibility
 */

import React, { useState, useCallback } from 'react';
import {
    Mountain,
    Palette,
    Type,
    Eye,
    EyeOff,
    Settings,
    RefreshCw
} from 'lucide-react';

// Preset color schemes
const COLOR_SCHEMES = [
    {
        id: 'terrain',
        name: 'Terrain',
        colors: ['#1a472a', '#2d5a3f', '#4a7c59', '#6b9b7a', '#8fb89c', '#b5d5bf', '#daf2e4']
    },
    {
        id: 'elevation',
        name: 'Elevation',
        colors: ['#440154', '#482878', '#3e4989', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725']
    },
    {
        id: 'grayscale',
        name: 'Grayscale',
        colors: ['#333', '#555', '#777', '#999', '#bbb', '#ddd']
    },
    {
        id: 'mining',
        name: 'Mining',
        colors: ['#8b4513', '#a0522d', '#cd853f', '#daa520', '#ffd700']
    },
    {
        id: 'custom',
        name: 'Custom',
        colors: ['#3b82f6']
    }
];

const ContourStylePanel = ({
    settings,
    onSettingsChange,
    contourStats,
    onRegenerate,
    className = ''
}) => {
    const [localSettings, setLocalSettings] = useState(settings || {
        interval: 5,
        indexInterval: 25,
        minElevation: null,
        maxElevation: null,
        colorScheme: 'terrain',
        indexColor: '#ffffff',
        indexWeight: 2,
        intermediateWeight: 1,
        showLabels: true,
        labelInterval: 25,
        labelSize: 10,
        visible: true
    });

    // Handle setting change
    const handleChange = useCallback((key, value) => {
        const newSettings = { ...localSettings, [key]: value };
        setLocalSettings(newSettings);
        onSettingsChange?.(newSettings);
    }, [localSettings, onSettingsChange]);

    // Get color for elevation
    const getColorForElevation = useCallback((elevation) => {
        const scheme = COLOR_SCHEMES.find(s => s.id === localSettings.colorScheme);
        if (!scheme || !contourStats) return scheme?.colors[0] || '#60a5fa';

        const range = contourStats.maxElevation - contourStats.minElevation;
        if (range === 0) return scheme.colors[0];

        const t = (elevation - contourStats.minElevation) / range;
        const idx = Math.floor(t * (scheme.colors.length - 1));
        return scheme.colors[Math.min(idx, scheme.colors.length - 1)];
    }, [localSettings.colorScheme, contourStats]);

    return (
        <div className={`contour-style-panel ${className}`}>
            {/* Header */}
            <div className="panel-header">
                <div className="title">
                    <Mountain size={16} />
                    <span>Contour Styles</span>
                </div>
                <button
                    className={`toggle-btn ${localSettings.visible ? '' : 'off'}`}
                    onClick={() => handleChange('visible', !localSettings.visible)}
                    title={localSettings.visible ? 'Hide Contours' : 'Show Contours'}
                >
                    {localSettings.visible ? <Eye size={16} /> : <EyeOff size={16} />}
                </button>
            </div>

            {/* Interval Settings */}
            <div className="panel-section">
                <div className="section-title">Intervals</div>

                <div className="setting-row">
                    <label>Contour Interval:</label>
                    <div className="input-group">
                        <input
                            type="number"
                            value={localSettings.interval}
                            onChange={(e) => handleChange('interval', parseFloat(e.target.value) || 5)}
                            min={0.5}
                            step={0.5}
                        />
                        <span className="unit">m</span>
                    </div>
                </div>

                <div className="setting-row">
                    <label>Index Interval:</label>
                    <div className="input-group">
                        <input
                            type="number"
                            value={localSettings.indexInterval}
                            onChange={(e) => handleChange('indexInterval', parseFloat(e.target.value) || 25)}
                            min={1}
                        />
                        <span className="unit">m</span>
                    </div>
                </div>

                <div className="setting-row">
                    <label>Min Elevation:</label>
                    <div className="input-group">
                        <input
                            type="number"
                            value={localSettings.minElevation ?? ''}
                            onChange={(e) => handleChange('minElevation', e.target.value ? parseFloat(e.target.value) : null)}
                            placeholder="Auto"
                        />
                    </div>
                </div>

                <div className="setting-row">
                    <label>Max Elevation:</label>
                    <div className="input-group">
                        <input
                            type="number"
                            value={localSettings.maxElevation ?? ''}
                            onChange={(e) => handleChange('maxElevation', e.target.value ? parseFloat(e.target.value) : null)}
                            placeholder="Auto"
                        />
                    </div>
                </div>
            </div>

            {/* Color Scheme */}
            <div className="panel-section">
                <div className="section-title">
                    <Palette size={14} />
                    <span>Colors</span>
                </div>

                <div className="color-schemes">
                    {COLOR_SCHEMES.map(scheme => (
                        <button
                            key={scheme.id}
                            className={`scheme-btn ${localSettings.colorScheme === scheme.id ? 'active' : ''}`}
                            onClick={() => handleChange('colorScheme', scheme.id)}
                            title={scheme.name}
                        >
                            <div className="scheme-preview">
                                {scheme.colors.slice(0, 5).map((color, i) => (
                                    <div key={i} className="color-chip" style={{ background: color }} />
                                ))}
                            </div>
                            <span>{scheme.name}</span>
                        </button>
                    ))}
                </div>

                <div className="setting-row">
                    <label>Index Color:</label>
                    <input
                        type="color"
                        value={localSettings.indexColor}
                        onChange={(e) => handleChange('indexColor', e.target.value)}
                        className="color-input"
                    />
                </div>
            </div>

            {/* Line Weights */}
            <div className="panel-section">
                <div className="section-title">
                    <Settings size={14} />
                    <span>Line Weights</span>
                </div>

                <div className="setting-row">
                    <label>Index Lines:</label>
                    <input
                        type="range"
                        min={1}
                        max={5}
                        step={0.5}
                        value={localSettings.indexWeight}
                        onChange={(e) => handleChange('indexWeight', parseFloat(e.target.value))}
                    />
                    <span className="range-value">{localSettings.indexWeight}</span>
                </div>

                <div className="setting-row">
                    <label>Intermediate:</label>
                    <input
                        type="range"
                        min={0.5}
                        max={3}
                        step={0.25}
                        value={localSettings.intermediateWeight}
                        onChange={(e) => handleChange('intermediateWeight', parseFloat(e.target.value))}
                    />
                    <span className="range-value">{localSettings.intermediateWeight}</span>
                </div>
            </div>

            {/* Labels */}
            <div className="panel-section">
                <div className="section-title">
                    <Type size={14} />
                    <span>Labels</span>
                </div>

                <div className="setting-row">
                    <label>Show Labels:</label>
                    <input
                        type="checkbox"
                        checked={localSettings.showLabels}
                        onChange={(e) => handleChange('showLabels', e.target.checked)}
                    />
                </div>

                {localSettings.showLabels && (
                    <>
                        <div className="setting-row">
                            <label>Label Interval:</label>
                            <div className="input-group">
                                <input
                                    type="number"
                                    value={localSettings.labelInterval}
                                    onChange={(e) => handleChange('labelInterval', parseFloat(e.target.value) || 25)}
                                    min={1}
                                />
                                <span className="unit">m</span>
                            </div>
                        </div>

                        <div className="setting-row">
                            <label>Label Size:</label>
                            <input
                                type="range"
                                min={8}
                                max={16}
                                value={localSettings.labelSize}
                                onChange={(e) => handleChange('labelSize', parseInt(e.target.value))}
                            />
                            <span className="range-value">{localSettings.labelSize}px</span>
                        </div>
                    </>
                )}
            </div>

            {/* Stats */}
            {contourStats && (
                <div className="panel-section stats-section">
                    <div className="stat-row">
                        <span>Contours:</span>
                        <span>{contourStats.count}</span>
                    </div>
                    <div className="stat-row">
                        <span>Range:</span>
                        <span>{contourStats.minElevation?.toFixed(0)} - {contourStats.maxElevation?.toFixed(0)} m</span>
                    </div>
                </div>
            )}

            {/* Regenerate Button */}
            <div className="panel-footer">
                <button className="regenerate-btn" onClick={onRegenerate}>
                    <RefreshCw size={14} /> Regenerate Contours
                </button>
            </div>

            <style jsx>{`
        .contour-style-panel {
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
        
        .toggle-btn {
          padding: 6px;
          background: rgba(34, 197, 94, 0.15);
          border: none;
          border-radius: 4px;
          color: #4ade80;
          cursor: pointer;
        }
        
        .toggle-btn.off {
          background: rgba(255,255,255,0.05);
          color: #888;
        }
        
        .panel-section {
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .section-title {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #888;
          margin-bottom: 10px;
        }
        
        .setting-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          font-size: 12px;
        }
        
        .setting-row label {
          flex: 0 0 100px;
          color: #a0a0b0;
        }
        
        .input-group {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .setting-row input[type="number"] {
          width: 60px;
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 12px;
        }
        
        .setting-row input[type="range"] {
          flex: 1;
          cursor: pointer;
        }
        
        .setting-row input[type="checkbox"] {
          cursor: pointer;
        }
        
        .color-input {
          width: 32px;
          height: 24px;
          border: none;
          cursor: pointer;
        }
        
        .unit, .range-value {
          font-size: 11px;
          color: #666;
          min-width: 30px;
        }
        
        .color-schemes {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px;
          margin-bottom: 12px;
        }
        
        .scheme-btn {
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding: 8px;
          background: rgba(0,0,0,0.2);
          border: 1px solid transparent;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .scheme-btn:hover {
          background: rgba(0,0,0,0.3);
        }
        
        .scheme-btn.active {
          border-color: rgba(59, 130, 246, 0.5);
          background: rgba(59, 130, 246, 0.1);
        }
        
        .scheme-preview {
          display: flex;
          height: 8px;
          border-radius: 2px;
          overflow: hidden;
        }
        
        .color-chip {
          flex: 1;
        }
        
        .scheme-btn span {
          font-size: 10px;
          color: #a0a0b0;
          text-align: center;
        }
        
        .stats-section {
          background: rgba(0,0,0,0.2);
        }
        
        .stat-row {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          margin-bottom: 4px;
        }
        
        .stat-row span:first-child { color: #888; }
        .stat-row span:last-child { color: #fff; font-family: 'SF Mono', monospace; }
        
        .panel-footer {
          padding: 12px 16px;
        }
        
        .regenerate-btn {
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
        
        .regenerate-btn:hover {
          background: rgba(59, 130, 246, 0.25);
        }
      `}</style>
        </div>
    );
};

export default ContourStylePanel;
