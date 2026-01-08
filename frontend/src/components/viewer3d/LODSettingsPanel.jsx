/**
 * LODSettingsPanel.jsx
 * 
 * Level of Detail settings for 3D rendering performance.
 */

import React, { useState } from 'react';
import {
    Settings,
    Eye,
    Cpu,
    Gauge,
    Triangle,
    Mountain
} from 'lucide-react';

const LODSettingsPanel = ({
    settings,
    onSettingsChange,
    performanceStats,
    presets = ['low', 'medium', 'high', 'ultra'],
    className = ''
}) => {
    const [activePreset, setActivePreset] = useState('medium');

    const defaultSettings = {
        maxTriangles: 500000,
        renderDistance: 5000,
        lodBias: 1.0,
        wireframeDistance: 200,
        shadowQuality: 'medium',
        antialias: true,
        showStats: false,
        ...settings
    };

    const presetConfigs = {
        low: {
            maxTriangles: 100000,
            renderDistance: 2000,
            lodBias: 0.5,
            wireframeDistance: 100,
            shadowQuality: 'off',
            antialias: false
        },
        medium: {
            maxTriangles: 500000,
            renderDistance: 5000,
            lodBias: 1.0,
            wireframeDistance: 200,
            shadowQuality: 'medium',
            antialias: true
        },
        high: {
            maxTriangles: 1000000,
            renderDistance: 10000,
            lodBias: 1.5,
            wireframeDistance: 500,
            shadowQuality: 'high',
            antialias: true
        },
        ultra: {
            maxTriangles: 2000000,
            renderDistance: 20000,
            lodBias: 2.0,
            wireframeDistance: 1000,
            shadowQuality: 'ultra',
            antialias: true
        }
    };

    const handlePresetChange = (preset) => {
        setActivePreset(preset);
        onSettingsChange?.({ ...defaultSettings, ...presetConfigs[preset] });
    };

    const handleSettingChange = (key, value) => {
        setActivePreset('custom');
        onSettingsChange?.({ ...defaultSettings, [key]: value });
    };

    const formatNumber = (num) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
        return num.toString();
    };

    return (
        <div className={`lod-settings-panel ${className}`}>
            {/* Header */}
            <div className="panel-header">
                <Settings size={16} />
                <h4>Render Settings</h4>
            </div>

            {/* Performance Stats */}
            {performanceStats && (
                <div className="performance-stats">
                    <div className="stat-item">
                        <Gauge size={12} />
                        <span className="stat-value">{performanceStats.fps || '--'}</span>
                        <span className="stat-label">FPS</span>
                    </div>
                    <div className="stat-item">
                        <Triangle size={12} />
                        <span className="stat-value">{formatNumber(performanceStats.triangles || 0)}</span>
                        <span className="stat-label">Triangles</span>
                    </div>
                    <div className="stat-item">
                        <Cpu size={12} />
                        <span className="stat-value">{performanceStats.drawCalls || '--'}</span>
                        <span className="stat-label">Draw Calls</span>
                    </div>
                </div>
            )}

            {/* Presets */}
            <div className="presets-section">
                <label>Quality Preset</label>
                <div className="preset-buttons">
                    {presets.map(preset => (
                        <button
                            key={preset}
                            className={`preset-btn ${activePreset === preset ? 'active' : ''}`}
                            onClick={() => handlePresetChange(preset)}
                        >
                            {preset.charAt(0).toUpperCase() + preset.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Detailed Settings */}
            <div className="settings-section">
                <div className="setting-row">
                    <label>
                        <Triangle size={12} />
                        Max Triangles
                    </label>
                    <div className="slider-group">
                        <input
                            type="range"
                            min={50000}
                            max={2000000}
                            step={50000}
                            value={defaultSettings.maxTriangles}
                            onChange={(e) => handleSettingChange('maxTriangles', parseInt(e.target.value))}
                        />
                        <span className="value">{formatNumber(defaultSettings.maxTriangles)}</span>
                    </div>
                </div>

                <div className="setting-row">
                    <label>
                        <Eye size={12} />
                        Render Distance
                    </label>
                    <div className="slider-group">
                        <input
                            type="range"
                            min={1000}
                            max={20000}
                            step={500}
                            value={defaultSettings.renderDistance}
                            onChange={(e) => handleSettingChange('renderDistance', parseInt(e.target.value))}
                        />
                        <span className="value">{defaultSettings.renderDistance}m</span>
                    </div>
                </div>

                <div className="setting-row">
                    <label>
                        <Mountain size={12} />
                        LOD Bias
                    </label>
                    <div className="slider-group">
                        <input
                            type="range"
                            min={0.5}
                            max={2}
                            step={0.1}
                            value={defaultSettings.lodBias}
                            onChange={(e) => handleSettingChange('lodBias', parseFloat(e.target.value))}
                        />
                        <span className="value">{defaultSettings.lodBias.toFixed(1)}</span>
                    </div>
                    <div className="setting-hint">
                        Higher = more detail at distance
                    </div>
                </div>

                <div className="setting-row">
                    <label>Wireframe Distance</label>
                    <div className="slider-group">
                        <input
                            type="range"
                            min={50}
                            max={1000}
                            step={50}
                            value={defaultSettings.wireframeDistance}
                            onChange={(e) => handleSettingChange('wireframeDistance', parseInt(e.target.value))}
                        />
                        <span className="value">{defaultSettings.wireframeDistance}m</span>
                    </div>
                </div>

                <div className="setting-row">
                    <label>Shadow Quality</label>
                    <select
                        value={defaultSettings.shadowQuality}
                        onChange={(e) => handleSettingChange('shadowQuality', e.target.value)}
                    >
                        <option value="off">Off</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="ultra">Ultra</option>
                    </select>
                </div>

                <div className="setting-row toggle">
                    <label>
                        <input
                            type="checkbox"
                            checked={defaultSettings.antialias}
                            onChange={(e) => handleSettingChange('antialias', e.target.checked)}
                        />
                        Anti-aliasing
                    </label>
                </div>

                <div className="setting-row toggle">
                    <label>
                        <input
                            type="checkbox"
                            checked={defaultSettings.showStats}
                            onChange={(e) => handleSettingChange('showStats', e.target.checked)}
                        />
                        Show Performance Stats
                    </label>
                </div>
            </div>

            {/* Memory Usage */}
            {performanceStats?.memoryUsage && (
                <div className="memory-section">
                    <label>GPU Memory</label>
                    <div className="memory-bar">
                        <div
                            className="memory-fill"
                            style={{
                                width: `${(performanceStats.memoryUsage / performanceStats.memoryLimit) * 100}%`
                            }}
                        />
                    </div>
                    <span className="memory-text">
                        {formatNumber(performanceStats.memoryUsage)} / {formatNumber(performanceStats.memoryLimit)} MB
                    </span>
                </div>
            )}

            <style jsx>{`
        .lod-settings-panel {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
          width: 280px;
        }
        
        .panel-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .panel-header h4 {
          margin: 0;
          font-size: 14px;
        }
        
        .performance-stats {
          display: flex;
          gap: 8px;
          padding: 12px;
          background: rgba(0,0,0,0.2);
        }
        
        .stat-item {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          padding: 8px;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
        }
        
        .stat-item svg { color: #888; }
        
        .stat-value {
          font-size: 16px;
          font-weight: 600;
          color: #fff;
        }
        
        .stat-label {
          font-size: 9px;
          color: #888;
          text-transform: uppercase;
        }
        
        .presets-section {
          padding: 12px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .presets-section > label {
          display: block;
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        
        .preset-buttons {
          display: flex;
          gap: 6px;
        }
        
        .preset-btn {
          flex: 1;
          padding: 8px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
        }
        
        .preset-btn:hover {
          background: rgba(255,255,255,0.06);
        }
        
        .preset-btn.active {
          background: rgba(59,130,246,0.2);
          border-color: #3b82f6;
          color: #3b82f6;
        }
        
        .settings-section {
          padding: 12px;
        }
        
        .setting-row {
          margin-bottom: 12px;
        }
        
        .setting-row > label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #aaa;
          margin-bottom: 6px;
        }
        
        .setting-row.toggle > label {
          cursor: pointer;
        }
        
        .slider-group {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .slider-group input[type="range"] {
          flex: 1;
          height: 4px;
          -webkit-appearance: none;
          background: rgba(255,255,255,0.1);
          border-radius: 2px;
        }
        
        .slider-group input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 14px;
          height: 14px;
          background: #3b82f6;
          border-radius: 50%;
          cursor: pointer;
        }
        
        .slider-group .value {
          min-width: 50px;
          text-align: right;
          font-size: 11px;
          color: #fff;
        }
        
        .setting-hint {
          font-size: 9px;
          color: #666;
          margin-top: 2px;
        }
        
        .setting-row select {
          width: 100%;
          padding: 6px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 11px;
        }
        
        .memory-section {
          padding: 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .memory-section > label {
          display: block;
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 6px;
        }
        
        .memory-bar {
          height: 6px;
          background: rgba(255,255,255,0.1);
          border-radius: 3px;
          overflow: hidden;
          margin-bottom: 4px;
        }
        
        .memory-fill {
          height: 100%;
          background: linear-gradient(90deg, #22c55e, #eab308, #ef4444);
          border-radius: 3px;
        }
        
        .memory-text {
          font-size: 10px;
          color: #888;
        }
      `}</style>
        </div>
    );
};

export default LODSettingsPanel;
