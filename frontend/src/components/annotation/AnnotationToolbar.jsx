/**
 * AnnotationToolbar.jsx - Phase 8
 * 
 * Toolbar for annotation creation and editing.
 * 
 * Features:
 * - Annotation type selection
 * - Text input
 * - Style controls
 * - Leader line options
 */

import React, { useState } from 'react';
import {
    Type,
    ArrowUpRight,
    Ruler,
    Square,
    Box,
    TrendingUp,
    Hash,
    Compass,
    Tag,
    MapPin,
    Thermometer,
    Settings,
    Palette,
    X,
    Check
} from 'lucide-react';

// Annotation types with icons
const ANNOTATION_TYPES = [
    { id: 'text', name: 'Text', icon: Type, description: 'Simple text label' },
    { id: 'elevation', name: 'Elevation', icon: ArrowUpRight, description: 'Show elevation value' },
    { id: 'distance', name: 'Distance', icon: Ruler, description: 'Measure between points' },
    { id: 'area', name: 'Area', icon: Square, description: 'Display area measurement' },
    { id: 'volume', name: 'Volume', icon: Box, description: 'Display volume value' },
    { id: 'gradient', name: 'Gradient', icon: TrendingUp, description: 'Show slope/gradient' },
    { id: 'coordinate', name: 'Coordinate', icon: Hash, description: 'Display XYZ coordinates' },
    { id: 'bearing', name: 'Bearing', icon: Compass, description: 'Show bearing/azimuth' },
    { id: 'borehole_id', name: 'Borehole ID', icon: MapPin, description: 'Borehole identifier' },
    { id: 'seam_thickness', name: 'Seam Thickness', icon: Thermometer, description: 'Seam thickness value' },
    { id: 'quality', name: 'Quality', icon: Tag, description: 'Quality parameter' }
];

// Leader line styles
const LEADER_STYLES = [
    { id: 'none', name: 'None' },
    { id: 'straight', name: 'Straight' },
    { id: 'bent', name: 'Bent' },
    { id: 'curved', name: 'Curved' }
];

const AnnotationToolbar = ({
    activeType,
    onTypeChange,
    textValue,
    onTextChange,
    style,
    onStyleChange,
    onPlace,
    onCancel,
    isPlacing = false,
    className = ''
}) => {
    const [showStylePanel, setShowStylePanel] = useState(false);
    const [localStyle, setLocalStyle] = useState(style || {
        fontFamily: 'Arial',
        fontSize: 12,
        fontColor: '#ffffff',
        backgroundColor: null,
        backgroundOpacity: 0.8,
        leaderStyle: 'straight',
        leaderColor: '#666666',
        leaderWidth: 1
    });

    // Handle style change
    const handleStyleChange = (key, value) => {
        const newStyle = { ...localStyle, [key]: value };
        setLocalStyle(newStyle);
        onStyleChange?.(newStyle);
    };

    return (
        <div className={`annotation-toolbar ${className}`}>
            {/* Type Selection */}
            <div className="toolbar-section type-section">
                <div className="section-label">Type</div>
                <div className="type-grid">
                    {ANNOTATION_TYPES.map(type => {
                        const Icon = type.icon;
                        return (
                            <button
                                key={type.id}
                                className={`type-btn ${activeType === type.id ? 'active' : ''}`}
                                onClick={() => onTypeChange?.(type.id)}
                                title={type.description}
                            >
                                <Icon size={14} />
                                <span>{type.name}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Text Input */}
            <div className="toolbar-section text-section">
                <div className="section-label">Text</div>
                <textarea
                    value={textValue || ''}
                    onChange={(e) => onTextChange?.(e.target.value)}
                    placeholder={activeType === 'text' ? 'Enter annotation text...' : 'Auto-generated from type'}
                    rows={2}
                    disabled={activeType !== 'text' && activeType !== 'custom'}
                />
            </div>

            {/* Quick Styles */}
            <div className="toolbar-section quick-styles">
                <button
                    className="style-toggle"
                    onClick={() => setShowStylePanel(!showStylePanel)}
                >
                    <Palette size={14} />
                    <span>Style</span>
                    <Settings size={12} />
                </button>

                {/* Color Quick Select */}
                <div className="color-row">
                    <input
                        type="color"
                        value={localStyle.fontColor}
                        onChange={(e) => handleStyleChange('fontColor', e.target.value)}
                        title="Text Color"
                    />
                    <span className="color-label">Color</span>
                </div>

                {/* Font Size */}
                <div className="size-row">
                    <button onClick={() => handleStyleChange('fontSize', Math.max(8, localStyle.fontSize - 1))}>−</button>
                    <span>{localStyle.fontSize}px</span>
                    <button onClick={() => handleStyleChange('fontSize', Math.min(32, localStyle.fontSize + 1))}>+</button>
                </div>
            </div>

            {/* Style Panel */}
            {showStylePanel && (
                <div className="style-panel">
                    <div className="panel-header">
                        <span>Annotation Style</span>
                        <button onClick={() => setShowStylePanel(false)}><X size={14} /></button>
                    </div>

                    <div className="style-group">
                        <div className="group-title">Font</div>
                        <div className="style-row">
                            <label>Family:</label>
                            <select
                                value={localStyle.fontFamily}
                                onChange={(e) => handleStyleChange('fontFamily', e.target.value)}
                            >
                                <option value="Arial">Arial</option>
                                <option value="Helvetica">Helvetica</option>
                                <option value="Courier New">Courier New</option>
                                <option value="Times New Roman">Times New Roman</option>
                            </select>
                        </div>
                        <div className="style-row">
                            <label>Size:</label>
                            <input
                                type="number"
                                value={localStyle.fontSize}
                                onChange={(e) => handleStyleChange('fontSize', parseInt(e.target.value) || 12)}
                                min={6}
                                max={48}
                            />
                        </div>
                        <div className="style-row">
                            <label>Color:</label>
                            <input
                                type="color"
                                value={localStyle.fontColor}
                                onChange={(e) => handleStyleChange('fontColor', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="style-group">
                        <div className="group-title">Background</div>
                        <div className="style-row">
                            <label>Color:</label>
                            <input
                                type="color"
                                value={localStyle.backgroundColor || '#000000'}
                                onChange={(e) => handleStyleChange('backgroundColor', e.target.value)}
                            />
                            <button
                                className="clear-btn"
                                onClick={() => handleStyleChange('backgroundColor', null)}
                            >
                                Clear
                            </button>
                        </div>
                        <div className="style-row">
                            <label>Opacity:</label>
                            <input
                                type="range"
                                min={0}
                                max={1}
                                step={0.1}
                                value={localStyle.backgroundOpacity}
                                onChange={(e) => handleStyleChange('backgroundOpacity', parseFloat(e.target.value))}
                            />
                            <span>{Math.round(localStyle.backgroundOpacity * 100)}%</span>
                        </div>
                    </div>

                    <div className="style-group">
                        <div className="group-title">Leader Line</div>
                        <div className="style-row">
                            <label>Style:</label>
                            <select
                                value={localStyle.leaderStyle}
                                onChange={(e) => handleStyleChange('leaderStyle', e.target.value)}
                            >
                                {LEADER_STYLES.map(s => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="style-row">
                            <label>Color:</label>
                            <input
                                type="color"
                                value={localStyle.leaderColor}
                                onChange={(e) => handleStyleChange('leaderColor', e.target.value)}
                            />
                        </div>
                        <div className="style-row">
                            <label>Width:</label>
                            <input
                                type="number"
                                value={localStyle.leaderWidth}
                                onChange={(e) => handleStyleChange('leaderWidth', parseFloat(e.target.value) || 1)}
                                min={0.5}
                                max={5}
                                step={0.5}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="toolbar-section actions">
                {isPlacing ? (
                    <>
                        <span className="placing-hint">Click to place annotation...</span>
                        <button className="cancel-btn" onClick={onCancel}>
                            <X size={14} /> Cancel
                        </button>
                    </>
                ) : (
                    <button className="place-btn" onClick={onPlace}>
                        <Check size={14} /> Place Annotation
                    </button>
                )}
            </div>

            <style jsx>{`
        .annotation-toolbar {
          display: flex;
          flex-direction: column;
          gap: 12px;
          padding: 12px;
          background: #1e1e2e;
          border-radius: 8px;
        }
        
        .toolbar-section {
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .toolbar-section:last-child {
          padding-bottom: 0;
          border-bottom: none;
        }
        
        .section-label {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #888;
          margin-bottom: 8px;
        }
        
        .type-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 4px;
        }
        
        .type-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 8px 4px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 6px;
          color: #888;
          font-size: 9px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .type-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .type-btn.active {
          background: rgba(59, 130, 246, 0.15);
          border-color: rgba(59, 130, 246, 0.3);
          color: #60a5fa;
        }
        
        .text-section textarea {
          width: 100%;
          padding: 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
          resize: none;
        }
        
        .text-section textarea:focus {
          border-color: rgba(59, 130, 246, 0.5);
          outline: none;
        }
        
        .text-section textarea:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .quick-styles {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .style-toggle {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 10px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #a0a0b0;
          font-size: 11px;
          cursor: pointer;
        }
        
        .style-toggle:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .color-row {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        
        .color-row input[type="color"] {
          width: 24px;
          height: 24px;
          border: none;
          cursor: pointer;
        }
        
        .color-label {
          font-size: 11px;
          color: #888;
        }
        
        .size-row {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .size-row button {
          width: 24px;
          height: 24px;
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 4px;
          color: #fff;
          cursor: pointer;
        }
        
        .size-row span {
          min-width: 40px;
          text-align: center;
          font-size: 11px;
          color: #fff;
        }
        
        .style-panel {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          z-index: 100;
          padding: 12px;
          margin-top: 8px;
        }
        
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel-header span {
          font-size: 12px;
          font-weight: 600;
          color: #fff;
        }
        
        .panel-header button {
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
        }
        
        .style-group {
          margin-bottom: 12px;
        }
        
        .group-title {
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          color: #666;
          margin-bottom: 8px;
        }
        
        .style-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
          font-size: 11px;
        }
        
        .style-row label {
          min-width: 50px;
          color: #888;
        }
        
        .style-row input, .style-row select {
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
        
        .style-row input[type="color"] {
          width: 24px;
          height: 24px;
          padding: 0;
          border: none;
        }
        
        .style-row input[type="range"] {
          flex: 1;
        }
        
        .clear-btn {
          padding: 2px 6px;
          background: rgba(239, 68, 68, 0.1);
          border: none;
          border-radius: 4px;
          color: #f87171;
          font-size: 10px;
          cursor: pointer;
        }
        
        .actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .placing-hint {
          flex: 1;
          font-size: 12px;
          color: #60a5fa;
          font-style: italic;
        }
        
        .place-btn, .cancel-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .place-btn {
          flex: 1;
          justify-content: center;
          background: rgba(34, 197, 94, 0.2);
          color: #4ade80;
        }
        
        .place-btn:hover {
          background: rgba(34, 197, 94, 0.3);
        }
        
        .cancel-btn {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
        }
        
        .cancel-btn:hover {
          background: rgba(239, 68, 68, 0.2);
        }
      `}</style>
        </div>
    );
};

export default AnnotationToolbar;
