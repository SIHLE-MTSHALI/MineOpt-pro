/**
 * SurfaceComparisonOverlay.jsx
 * 
 * Side-by-side or overlay comparison of two surface versions.
 */

import React, { useState } from 'react';
import {
    Layers,
    SplitSquareHorizontal,
    Maximize2,
    Eye,
    EyeOff,
    Settings,
    Download
} from 'lucide-react';

const SurfaceComparisonOverlay = ({
    baseVersion,
    compareVersion,
    comparisonResult,
    viewMode = 'overlay',
    onViewModeChange,
    onOpacityChange,
    overlayOpacity = 0.5,
    onExport,
    className = ''
}) => {
    const [showDifference, setShowDifference] = useState(true);
    const [colorScale, setColorScale] = useState('diverging'); // diverging, sequential
    const [cutColor, setCutColor] = useState('#ef4444');
    const [fillColor, setFillColor] = useState('#3b82f6');

    const formatVolume = (bcm) => {
        if (!bcm) return '0';
        if (Math.abs(bcm) >= 1000000) {
            return `${(bcm / 1000000).toFixed(2)}M`;
        } else if (Math.abs(bcm) >= 1000) {
            return `${(bcm / 1000).toFixed(1)}K`;
        }
        return bcm.toFixed(0);
    };

    return (
        <div className={`surface-comparison-overlay ${className}`}>
            {/* Header */}
            <div className="comparison-header">
                <div className="header-left">
                    <Layers size={18} />
                    <h4>Surface Comparison</h4>
                </div>
                <div className="view-mode-toggle">
                    <button
                        className={viewMode === 'overlay' ? 'active' : ''}
                        onClick={() => onViewModeChange?.('overlay')}
                        title="Overlay view"
                    >
                        <Layers size={14} />
                    </button>
                    <button
                        className={viewMode === 'split' ? 'active' : ''}
                        onClick={() => onViewModeChange?.('split')}
                        title="Split view"
                    >
                        <SplitSquareHorizontal size={14} />
                    </button>
                </div>
            </div>

            {/* Version Info */}
            <div className="version-panels">
                <div className="version-panel base">
                    <div className="panel-label">Base</div>
                    <div className="version-name">{baseVersion?.version_name || 'None'}</div>
                    <div className="version-date">
                        {baseVersion?.version_date ? new Date(baseVersion.version_date).toLocaleDateString() : '--'}
                    </div>
                </div>
                <div className="vs-divider">vs</div>
                <div className="version-panel compare">
                    <div className="panel-label">Compare</div>
                    <div className="version-name">{compareVersion?.version_name || 'None'}</div>
                    <div className="version-date">
                        {compareVersion?.version_date ? new Date(compareVersion.version_date).toLocaleDateString() : '--'}
                    </div>
                </div>
            </div>

            {/* Volume Results */}
            {comparisonResult && (
                <div className="volume-results">
                    <div className="result-row total">
                        <span className="result-label">Net Volume</span>
                        <span className={`result-value ${comparisonResult.net_volume_bcm > 0 ? 'cut' : 'fill'}`}>
                            {comparisonResult.net_volume_bcm > 0 ? '+' : ''}{formatVolume(comparisonResult.net_volume_bcm)} BCM
                        </span>
                    </div>
                    <div className="result-breakdown">
                        <div className="result-row cut">
                            <span className="result-dot" style={{ backgroundColor: cutColor }} />
                            <span className="result-label">Cut</span>
                            <span className="result-value">{formatVolume(comparisonResult.cut_volume_bcm)} BCM</span>
                        </div>
                        <div className="result-row fill">
                            <span className="result-dot" style={{ backgroundColor: fillColor }} />
                            <span className="result-label">Fill</span>
                            <span className="result-value">{formatVolume(comparisonResult.fill_volume_bcm)} BCM</span>
                        </div>
                    </div>

                    {/* Max differences */}
                    <div className="max-diff">
                        <div className="diff-item">
                            <span className="diff-label">Max Cut</span>
                            <span className="diff-value">{comparisonResult.max_cut_m?.toFixed(2) || '--'} m</span>
                        </div>
                        <div className="diff-item">
                            <span className="diff-label">Max Fill</span>
                            <span className="diff-value">{comparisonResult.max_fill_m?.toFixed(2) || '--'} m</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Display Controls */}
            <div className="display-controls">
                <div className="control-row">
                    <label className="toggle-label">
                        <input
                            type="checkbox"
                            checked={showDifference}
                            onChange={(e) => setShowDifference(e.target.checked)}
                        />
                        Show difference
                    </label>
                </div>

                {viewMode === 'overlay' && (
                    <div className="control-row">
                        <label>Opacity</label>
                        <input
                            type="range"
                            min={0}
                            max={1}
                            step={0.1}
                            value={overlayOpacity}
                            onChange={(e) => onOpacityChange?.(parseFloat(e.target.value))}
                        />
                        <span>{Math.round(overlayOpacity * 100)}%</span>
                    </div>
                )}

                <div className="control-row">
                    <label>Color Scale</label>
                    <select value={colorScale} onChange={(e) => setColorScale(e.target.value)}>
                        <option value="diverging">Diverging (Cut/Fill)</option>
                        <option value="sequential">Sequential</option>
                        <option value="thermal">Thermal</option>
                    </select>
                </div>
            </div>

            {/* Color Legend */}
            <div className="color-legend">
                <div className="legend-gradient">
                    <div className="gradient-bar" style={{
                        background: `linear-gradient(to right, ${fillColor}, #888, ${cutColor})`
                    }} />
                    <div className="legend-labels">
                        <span>Fill</span>
                        <span>0</span>
                        <span>Cut</span>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="comparison-actions">
                <button className="export-btn" onClick={onExport}>
                    <Download size={14} />
                    Export Report
                </button>
            </div>

            <style jsx>{`
        .surface-comparison-overlay {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .comparison-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #fff;
        }
        
        .header-left h4 { margin: 0; font-size: 14px; }
        
        .view-mode-toggle {
          display: flex;
          gap: 4px;
        }
        
        .view-mode-toggle button {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .view-mode-toggle button.active {
          background: rgba(59,130,246,0.2);
          border-color: #3b82f6;
          color: #3b82f6;
        }
        
        .version-panels {
          display: flex;
          align-items: center;
          padding: 12px;
          gap: 8px;
        }
        
        .version-panel {
          flex: 1;
          padding: 10px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          text-align: center;
        }
        
        .version-panel.base { border-left: 3px solid #f97316; }
        .version-panel.compare { border-left: 3px solid #3b82f6; }
        
        .panel-label {
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 4px;
        }
        
        .version-name {
          font-weight: 600;
          color: #fff;
          font-size: 13px;
        }
        
        .version-date {
          font-size: 11px;
          color: #666;
        }
        
        .vs-divider {
          color: #666;
          font-size: 11px;
        }
        
        .volume-results {
          padding: 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .result-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
        }
        
        .result-row.total {
          border-bottom: 1px solid rgba(255,255,255,0.05);
          margin-bottom: 8px;
        }
        
        .result-label {
          font-size: 12px;
          color: #aaa;
        }
        
        .result-value {
          font-weight: 600;
          font-size: 14px;
        }
        
        .result-value.cut { color: #ef4444; }
        .result-value.fill { color: #3b82f6; }
        
        .result-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 8px;
        }
        
        .result-breakdown .result-row {
          padding: 4px 0;
        }
        
        .result-breakdown .result-label {
          display: flex;
          align-items: center;
        }
        
        .result-breakdown .result-value {
          font-size: 12px;
          color: #ccc;
        }
        
        .max-diff {
          display: flex;
          gap: 16px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .diff-item {
          flex: 1;
          text-align: center;
        }
        
        .diff-label {
          display: block;
          font-size: 10px;
          color: #888;
          margin-bottom: 2px;
        }
        
        .diff-value {
          font-size: 14px;
          color: #fff;
        }
        
        .display-controls {
          padding: 12px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        
        .control-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          font-size: 12px;
          color: #aaa;
        }
        
        .toggle-label {
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
        }
        
        .control-row input[type="range"] {
          flex: 1;
          height: 4px;
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
        
        .color-legend {
          padding: 0 12px 12px;
        }
        
        .gradient-bar {
          height: 8px;
          border-radius: 4px;
          margin-bottom: 4px;
        }
        
        .legend-labels {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          color: #888;
        }
        
        .comparison-actions {
          padding: 12px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .export-btn {
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 6px;
          padding: 10px;
          background: rgba(59,130,246,0.2);
          border: 1px solid #3b82f6;
          border-radius: 6px;
          color: #3b82f6;
          font-size: 12px;
          cursor: pointer;
        }
      `}</style>
        </div>
    );
};

export default SurfaceComparisonOverlay;
