/**
 * StringPropertiesPanel.jsx - Phase 6
 * 
 * Properties panel for viewing and editing CAD string properties.
 * 
 * Features:
 * - String metadata display
 * - Color picker
 * - Line style selector
 * - Calculated values (length, area, gradient)
 * - String type selector
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Palette,
    Ruler,
    Square,
    TrendingUp,
    Layers,
    Type,
    Hash,
    X,
    ChevronDown,
    ChevronUp,
    RotateCcw,
    Save
} from 'lucide-react';

import { STRING_TYPE_COLORS } from './CADStringRenderer';

// String type options
const STRING_TYPES = [
    { value: 'pit_boundary', label: 'Pit Boundary' },
    { value: 'bench_crest', label: 'Bench Crest' },
    { value: 'bench_toe', label: 'Bench Toe' },
    { value: 'haul_road', label: 'Haul Road' },
    { value: 'ramp', label: 'Ramp' },
    { value: 'contour', label: 'Contour' },
    { value: 'drill_pattern', label: 'Drill Pattern' },
    { value: 'survey_traverse', label: 'Survey Traverse' },
    { value: 'power_line', label: 'Power Line' },
    { value: 'water_line', label: 'Water Line' },
    { value: 'fence_line', label: 'Fence Line' },
    { value: 'geological_contact', label: 'Geological Contact' },
    { value: 'fault', label: 'Fault' },
    { value: 'boundary', label: 'Boundary' },
    { value: 'custom', label: 'Custom' }
];

// Line weight options
const LINE_WEIGHTS = [0.5, 1, 1.5, 2, 3, 4, 5];

// Preset colors
const PRESET_COLORS = [
    '#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981',
    '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7',
    '#ec4899', '#f43f5e', '#64748b', '#78716c', '#ffffff'
];

// Property Section Component
const PropertySection = ({ title, icon: Icon, children, defaultOpen = true }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="property-section">
            <button
                className="section-header"
                onClick={() => setIsOpen(!isOpen)}
            >
                {Icon && <Icon size={14} />}
                <span>{title}</span>
                {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {isOpen && (
                <div className="section-content">
                    {children}
                </div>
            )}

            <style jsx>{`
        .property-section {
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .section-header {
          display: flex;
          align-items: center;
          gap: 8px;
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
        
        .section-header span {
          flex: 1;
        }
        
        .section-content {
          padding: 0 16px 12px;
        }
      `}</style>
        </div>
    );
};

// Main Component
const StringPropertiesPanel = ({
    string,
    calculatedValues,
    onUpdate,
    onClose,
    className = ''
}) => {
    const [localValues, setLocalValues] = useState({});
    const [hasChanges, setHasChanges] = useState(false);

    // Initialize local values when string changes
    useEffect(() => {
        if (string) {
            setLocalValues({
                name: string.name || '',
                description: string.description || '',
                layer: string.layer || 'DEFAULT',
                string_type: string.string_type || 'custom',
                color: string.color || STRING_TYPE_COLORS[string.string_type] || '#60a5fa',
                line_weight: string.line_weight || 1,
                elevation: string.elevation || 0
            });
            setHasChanges(false);
        }
    }, [string?.string_id]);

    // Handle value change
    const handleChange = useCallback((key, value) => {
        setLocalValues(prev => ({ ...prev, [key]: value }));
        setHasChanges(true);
    }, []);

    // Save changes
    const handleSave = useCallback(() => {
        onUpdate?.(localValues);
        setHasChanges(false);
    }, [localValues, onUpdate]);

    // Reset changes
    const handleReset = useCallback(() => {
        if (string) {
            setLocalValues({
                name: string.name || '',
                description: string.description || '',
                layer: string.layer || 'DEFAULT',
                string_type: string.string_type || 'custom',
                color: string.color || STRING_TYPE_COLORS[string.string_type] || '#60a5fa',
                line_weight: string.line_weight || 1,
                elevation: string.elevation || 0
            });
            setHasChanges(false);
        }
    }, [string]);

    if (!string) {
        return (
            <div className={`string-properties-panel empty ${className}`}>
                <div className="empty-state">
                    <Type size={32} />
                    <p>No string selected</p>
                </div>

                <style jsx>{`
          .string-properties-panel.empty {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 200px;
            color: #666;
          }
          
          .empty-state {
            text-align: center;
          }
          
          .empty-state p {
            margin-top: 8px;
            font-size: 13px;
          }
        `}</style>
            </div>
        );
    }

    return (
        <div className={`string-properties-panel ${className}`}>
            {/* Header */}
            <div className="panel-header">
                <h3>Properties</h3>
                <button className="close-btn" onClick={onClose}>
                    <X size={18} />
                </button>
            </div>

            {/* General Section */}
            <PropertySection title="General" icon={Type}>
                <div className="property-row">
                    <label>Name</label>
                    <input
                        type="text"
                        value={localValues.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                    />
                </div>

                <div className="property-row">
                    <label>Type</label>
                    <select
                        value={localValues.string_type}
                        onChange={(e) => handleChange('string_type', e.target.value)}
                    >
                        {STRING_TYPES.map(type => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                        ))}
                    </select>
                </div>

                <div className="property-row">
                    <label>Layer</label>
                    <input
                        type="text"
                        value={localValues.layer}
                        onChange={(e) => handleChange('layer', e.target.value)}
                    />
                </div>

                <div className="property-row full">
                    <label>Description</label>
                    <textarea
                        value={localValues.description}
                        onChange={(e) => handleChange('description', e.target.value)}
                        rows={2}
                    />
                </div>
            </PropertySection>

            {/* Style Section */}
            <PropertySection title="Style" icon={Palette}>
                <div className="property-row">
                    <label>Color</label>
                    <div className="color-picker">
                        <input
                            type="color"
                            value={localValues.color}
                            onChange={(e) => handleChange('color', e.target.value)}
                        />
                        <span className="color-hex">{localValues.color}</span>
                    </div>
                </div>

                <div className="color-presets">
                    {PRESET_COLORS.map(color => (
                        <button
                            key={color}
                            className={`color-preset ${localValues.color === color ? 'active' : ''}`}
                            style={{ background: color }}
                            onClick={() => handleChange('color', color)}
                        />
                    ))}
                </div>

                <div className="property-row">
                    <label>Line Weight</label>
                    <div className="weight-selector">
                        {LINE_WEIGHTS.map(weight => (
                            <button
                                key={weight}
                                className={`weight-option ${localValues.line_weight === weight ? 'active' : ''}`}
                                onClick={() => handleChange('line_weight', weight)}
                            >
                                <div className="weight-preview" style={{ height: weight }} />
                                <span>{weight}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </PropertySection>

            {/* Geometry Section */}
            <PropertySection title="Geometry" icon={Hash}>
                <div className="property-row readonly">
                    <label>Vertices</label>
                    <span>{string.vertex_count || string.vertices?.length || 0}</span>
                </div>

                <div className="property-row readonly">
                    <label>Closed</label>
                    <span>{string.is_closed ? 'Yes' : 'No'}</span>
                </div>

                <div className="property-row">
                    <label>Elevation</label>
                    <input
                        type="number"
                        value={localValues.elevation || ''}
                        onChange={(e) => handleChange('elevation', parseFloat(e.target.value) || 0)}
                        placeholder="Auto"
                    />
                </div>
            </PropertySection>

            {/* Calculated Values Section */}
            {calculatedValues && (
                <PropertySection title="Calculated" icon={Ruler} defaultOpen={false}>
                    {calculatedValues.length !== undefined && (
                        <div className="property-row readonly">
                            <label>Length</label>
                            <span>{calculatedValues.length.toFixed(2)} m</span>
                        </div>
                    )}

                    {calculatedValues.area !== undefined && (
                        <div className="property-row readonly">
                            <label>Area</label>
                            <span>{calculatedValues.area.toFixed(2)} m²</span>
                        </div>
                    )}

                    {calculatedValues.gradient && (
                        <>
                            <div className="property-row readonly">
                                <label>Min Gradient</label>
                                <span>{calculatedValues.gradient.min_gradient.toFixed(1)}%</span>
                            </div>
                            <div className="property-row readonly">
                                <label>Max Gradient</label>
                                <span>{calculatedValues.gradient.max_gradient.toFixed(1)}%</span>
                            </div>
                            <div className="property-row readonly">
                                <label>Avg Gradient</label>
                                <span>{calculatedValues.gradient.avg_gradient.toFixed(1)}%</span>
                            </div>
                        </>
                    )}
                </PropertySection>
            )}

            {/* Actions */}
            {hasChanges && (
                <div className="panel-actions">
                    <button className="reset-btn" onClick={handleReset}>
                        <RotateCcw size={14} /> Reset
                    </button>
                    <button className="save-btn" onClick={handleSave}>
                        <Save size={14} /> Save
                    </button>
                </div>
            )}

            <style jsx>{`
        .string-properties-panel {
          background: #1e1e2e;
          border-left: 1px solid rgba(255,255,255,0.1);
          width: 280px;
          display: flex;
          flex-direction: column;
          overflow-y: auto;
        }
        
        .panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel-header h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: #fff;
        }
        
        .close-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
        }
        
        .close-btn:hover {
          color: #fff;
        }
        
        .property-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .property-row.full {
          flex-direction: column;
          align-items: stretch;
        }
        
        .property-row.full label {
          margin-bottom: 4px;
        }
        
        .property-row label {
          min-width: 80px;
          font-size: 12px;
          color: #888;
        }
        
        .property-row input,
        .property-row select,
        .property-row textarea {
          flex: 1;
          padding: 6px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 12px;
        }
        
        .property-row select {
          cursor: pointer;
        }
        
        .property-row textarea {
          resize: none;
        }
        
        .property-row input:focus,
        .property-row select:focus,
        .property-row textarea:focus {
          border-color: rgba(59, 130, 246, 0.5);
          outline: none;
        }
        
        .property-row.readonly span {
          flex: 1;
          font-size: 12px;
          color: #c0c0d0;
          font-family: 'SF Mono', monospace;
        }
        
        .color-picker {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
        }
        
        .color-picker input[type="color"] {
          width: 32px;
          height: 32px;
          padding: 0;
          border: none;
          cursor: pointer;
        }
        
        .color-hex {
          font-size: 11px;
          color: #888;
          font-family: 'SF Mono', monospace;
          text-transform: uppercase;
        }
        
        .color-presets {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 12px;
        }
        
        .color-preset {
          width: 20px;
          height: 20px;
          border: 2px solid transparent;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .color-preset:hover {
          transform: scale(1.1);
        }
        
        .color-preset.active {
          border-color: #fff;
        }
        
        .weight-selector {
          display: flex;
          gap: 4px;
          flex: 1;
        }
        
        .weight-option {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 6px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid transparent;
          border-radius: 4px;
          cursor: pointer;
        }
        
        .weight-option:hover {
          background: rgba(255,255,255,0.1);
        }
        
        .weight-option.active {
          border-color: rgba(59, 130, 246, 0.5);
          background: rgba(59, 130, 246, 0.15);
        }
        
        .weight-preview {
          width: 20px;
          background: #fff;
          border-radius: 1px;
        }
        
        .weight-option span {
          font-size: 9px;
          color: #888;
        }
        
        .panel-actions {
          display: flex;
          gap: 8px;
          padding: 12px 16px;
          border-top: 1px solid rgba(255,255,255,0.1);
          margin-top: auto;
        }
        
        .panel-actions button {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 8px 12px;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .reset-btn {
          background: rgba(255,255,255,0.1);
          color: #a0a0b0;
        }
        
        .reset-btn:hover {
          background: rgba(255,255,255,0.15);
          color: #fff;
        }
        
        .save-btn {
          background: rgba(34, 197, 94, 0.2);
          color: #4ade80;
        }
        
        .save-btn:hover {
          background: rgba(34, 197, 94, 0.3);
        }
      `}</style>
        </div>
    );
};

export default StringPropertiesPanel;
