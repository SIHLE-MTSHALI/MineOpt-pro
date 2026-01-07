/**
 * CADToolbar.jsx - Phase 6
 * 
 * Comprehensive CAD toolbar with tool groups for mining applications.
 * 
 * Features:
 * - Selection tools (single, multi, box, lasso)
 * - Draw tools (point, polyline, polygon, rectangle, circle, arc)
 * - Edit tools (vertex, extend, trim, offset, fillet)
 * - Snap settings panel
 * - Tool state management
 */

import React, { useState, useCallback } from 'react';
import {
    MousePointer2,
    SquareStack,
    Box,
    Lasso,
    Pencil,
    Route,
    Hexagon,
    Square,
    Circle,
    CornerDownRight,
    Move,
    GitBranch,
    Scissors,
    Copy,
    FlipHorizontal,
    Magnet,
    Grid3X3,
    Target,
    Crosshair,
    Minimize2,
    Maximize2,
    RotateCcw,
    RotateCw,
    Trash2,
    Settings,
    ChevronDown,
    Ruler,
    Hash,
    ArrowUpRight,
    Type
} from 'lucide-react';

// Tool definitions
const TOOL_GROUPS = {
    selection: {
        name: 'Selection',
        icon: MousePointer2,
        tools: [
            { id: 'select', name: 'Select', icon: MousePointer2, shortcut: 'V' },
            { id: 'select-multi', name: 'Multi Select', icon: SquareStack, shortcut: 'Shift+V' },
            { id: 'select-box', name: 'Box Select', icon: Box, shortcut: 'B' },
            { id: 'select-lasso', name: 'Lasso Select', icon: Lasso, shortcut: 'L' }
        ]
    },
    draw: {
        name: 'Draw',
        icon: Pencil,
        tools: [
            { id: 'draw-point', name: 'Point', icon: Target, shortcut: 'P' },
            { id: 'draw-polyline', name: 'Polyline', icon: Route, shortcut: 'PL' },
            { id: 'draw-polygon', name: 'Polygon', icon: Hexagon, shortcut: 'PG' },
            { id: 'draw-rectangle', name: 'Rectangle', icon: Square, shortcut: 'REC' },
            { id: 'draw-circle', name: 'Circle', icon: Circle, shortcut: 'C' },
            { id: 'draw-arc', name: 'Arc', icon: CornerDownRight, shortcut: 'A' }
        ]
    },
    edit: {
        name: 'Edit',
        icon: Move,
        tools: [
            { id: 'edit-vertex', name: 'Edit Vertices', icon: Crosshair, shortcut: 'E' },
            { id: 'edit-move', name: 'Move', icon: Move, shortcut: 'M' },
            { id: 'edit-copy', name: 'Copy', icon: Copy, shortcut: 'Ctrl+C' },
            { id: 'edit-mirror', name: 'Mirror', icon: FlipHorizontal, shortcut: 'MI' },
            { id: 'edit-split', name: 'Split', icon: GitBranch, shortcut: 'SP' },
            { id: 'edit-trim', name: 'Trim', icon: Scissors, shortcut: 'TR' },
            { id: 'edit-extend', name: 'Extend', icon: ArrowUpRight, shortcut: 'EX' },
            { id: 'edit-offset', name: 'Offset', icon: Maximize2, shortcut: 'O' }
        ]
    },
    measure: {
        name: 'Measure',
        icon: Ruler,
        tools: [
            { id: 'measure-distance', name: 'Distance', icon: Ruler, shortcut: 'DI' },
            { id: 'measure-area', name: 'Area', icon: Hexagon, shortcut: 'AR' },
            { id: 'measure-angle', name: 'Angle', icon: CornerDownRight, shortcut: 'AN' },
            { id: 'measure-coord', name: 'Coordinates', icon: Hash, shortcut: 'ID' }
        ]
    },
    annotate: {
        name: 'Annotate',
        icon: Type,
        tools: [
            { id: 'annotate-text', name: 'Text', icon: Type, shortcut: 'T' },
            { id: 'annotate-elevation', name: 'Elevation', icon: ArrowUpRight, shortcut: 'EL' },
            { id: 'annotate-dimension', name: 'Dimension', icon: Ruler, shortcut: 'DIM' }
        ]
    }
};

const SNAP_MODES = [
    { id: 'endpoint', name: 'Endpoint', icon: Target },
    { id: 'midpoint', name: 'Midpoint', icon: Minimize2 },
    { id: 'center', name: 'Center', icon: Circle },
    { id: 'intersection', name: 'Intersection', icon: Crosshair },
    { id: 'perpendicular', name: 'Perpendicular', icon: CornerDownRight },
    { id: 'nearest', name: 'Nearest', icon: Magnet },
    { id: 'grid', name: 'Grid', icon: Grid3X3 }
];

const CADToolbar = ({
    activeTool,
    onToolChange,
    snapSettings,
    onSnapChange,
    onUndo,
    onRedo,
    canUndo = false,
    canRedo = false,
    selectedCount = 0,
    onDelete,
    className = ''
}) => {
    const [expandedGroup, setExpandedGroup] = useState(null);
    const [showSnapPanel, setShowSnapPanel] = useState(false);

    // Handle tool selection
    const handleToolSelect = useCallback((toolId) => {
        onToolChange?.(toolId);
        setExpandedGroup(null);
    }, [onToolChange]);

    // Toggle group expansion
    const toggleGroup = useCallback((groupId, e) => {
        e.stopPropagation();
        setExpandedGroup(expandedGroup === groupId ? null : groupId);
        setShowSnapPanel(false);
    }, [expandedGroup]);

    // Toggle snap mode
    const toggleSnap = useCallback((snapId) => {
        if (!snapSettings || !onSnapChange) return;

        const currentModes = snapSettings.modes || [];
        const newModes = currentModes.includes(snapId)
            ? currentModes.filter(m => m !== snapId)
            : [...currentModes, snapId];

        onSnapChange({ ...snapSettings, modes: newModes });
    }, [snapSettings, onSnapChange]);

    // Find active tool info
    const getActiveToolInfo = () => {
        for (const group of Object.values(TOOL_GROUPS)) {
            const tool = group.tools.find(t => t.id === activeTool);
            if (tool) return tool;
        }
        return null;
    };

    const activeToolInfo = getActiveToolInfo();

    return (
        <div className={`cad-toolbar ${className}`}>
            {/* Tool Groups */}
            <div className="toolbar-section tool-groups">
                {Object.entries(TOOL_GROUPS).map(([groupId, group]) => {
                    const GroupIcon = group.icon;
                    const isExpanded = expandedGroup === groupId;
                    const hasActiveTool = group.tools.some(t => t.id === activeTool);

                    return (
                        <div key={groupId} className="tool-group">
                            <button
                                className={`tool-group-btn ${hasActiveTool ? 'active' : ''}`}
                                onClick={(e) => toggleGroup(groupId, e)}
                                title={group.name}
                            >
                                <GroupIcon size={18} />
                                <ChevronDown size={12} className={`chevron ${isExpanded ? 'expanded' : ''}`} />
                            </button>

                            {isExpanded && (
                                <div className="tool-dropdown">
                                    <div className="dropdown-header">{group.name}</div>
                                    {group.tools.map(tool => {
                                        const ToolIcon = tool.icon;
                                        return (
                                            <button
                                                key={tool.id}
                                                className={`tool-item ${activeTool === tool.id ? 'active' : ''}`}
                                                onClick={() => handleToolSelect(tool.id)}
                                                title={`${tool.name} (${tool.shortcut})`}
                                            >
                                                <ToolIcon size={16} />
                                                <span className="tool-name">{tool.name}</span>
                                                <span className="tool-shortcut">{tool.shortcut}</span>
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Separator */}
            <div className="toolbar-separator" />

            {/* Active Tool Display */}
            {activeToolInfo && (
                <div className="active-tool-display">
                    <activeToolInfo.icon size={16} />
                    <span>{activeToolInfo.name}</span>
                </div>
            )}

            {/* Separator */}
            <div className="toolbar-separator" />

            {/* Snap Settings */}
            <div className="toolbar-section snap-section">
                <button
                    className={`snap-toggle ${snapSettings?.enabled ? 'active' : ''}`}
                    onClick={() => onSnapChange?.({ ...snapSettings, enabled: !snapSettings?.enabled })}
                    title="Toggle Snapping (F3)"
                >
                    <Magnet size={18} />
                </button>

                <button
                    className="snap-settings-btn"
                    onClick={() => {
                        setShowSnapPanel(!showSnapPanel);
                        setExpandedGroup(null);
                    }}
                    title="Snap Settings"
                >
                    <Settings size={14} />
                </button>

                {showSnapPanel && (
                    <div className="snap-panel">
                        <div className="snap-panel-header">Snap Settings</div>

                        <div className="snap-modes">
                            {SNAP_MODES.map(snap => {
                                const SnapIcon = snap.icon;
                                const isActive = snapSettings?.modes?.includes(snap.id);

                                return (
                                    <button
                                        key={snap.id}
                                        className={`snap-mode-btn ${isActive ? 'active' : ''}`}
                                        onClick={() => toggleSnap(snap.id)}
                                        title={snap.name}
                                    >
                                        <SnapIcon size={14} />
                                        <span>{snap.name}</span>
                                    </button>
                                );
                            })}
                        </div>

                        <div className="snap-options">
                            <label className="snap-option">
                                <span>Grid Size:</span>
                                <input
                                    type="number"
                                    value={snapSettings?.gridSize || 1}
                                    onChange={(e) => onSnapChange?.({
                                        ...snapSettings,
                                        gridSize: parseFloat(e.target.value)
                                    })}
                                    min={0.1}
                                    step={0.5}
                                />
                                <span>m</span>
                            </label>

                            <label className="snap-option">
                                <span>Tolerance:</span>
                                <input
                                    type="number"
                                    value={snapSettings?.tolerance || 10}
                                    onChange={(e) => onSnapChange?.({
                                        ...snapSettings,
                                        tolerance: parseFloat(e.target.value)
                                    })}
                                    min={1}
                                    max={50}
                                />
                                <span>px</span>
                            </label>
                        </div>
                    </div>
                )}
            </div>

            {/* Separator */}
            <div className="toolbar-separator" />

            {/* Undo/Redo */}
            <div className="toolbar-section undo-redo">
                <button
                    className="toolbar-btn"
                    onClick={onUndo}
                    disabled={!canUndo}
                    title="Undo (Ctrl+Z)"
                >
                    <RotateCcw size={18} />
                </button>
                <button
                    className="toolbar-btn"
                    onClick={onRedo}
                    disabled={!canRedo}
                    title="Redo (Ctrl+Y)"
                >
                    <RotateCw size={18} />
                </button>
            </div>

            {/* Delete (if selection) */}
            {selectedCount > 0 && (
                <>
                    <div className="toolbar-separator" />
                    <div className="toolbar-section">
                        <button
                            className="toolbar-btn delete-btn"
                            onClick={onDelete}
                            title={`Delete ${selectedCount} selected (Del)`}
                        >
                            <Trash2 size={18} />
                            <span className="selection-count">{selectedCount}</span>
                        </button>
                    </div>
                </>
            )}

            <style jsx>{`
        .cad-toolbar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: linear-gradient(180deg, #2a2a3e 0%, #1e1e2e 100%);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          user-select: none;
        }
        
        .toolbar-section {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .toolbar-separator {
          width: 1px;
          height: 24px;
          background: rgba(255,255,255,0.15);
          margin: 0 4px;
        }
        
        .tool-groups {
          display: flex;
          gap: 2px;
        }
        
        .tool-group {
          position: relative;
        }
        
        .tool-group-btn {
          display: flex;
          align-items: center;
          gap: 2px;
          padding: 6px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 6px;
          color: #a0a0b0;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .tool-group-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .tool-group-btn.active {
          background: rgba(59, 130, 246, 0.2);
          border-color: rgba(59, 130, 246, 0.5);
          color: #60a5fa;
        }
        
        .chevron {
          transition: transform 0.2s ease;
        }
        
        .chevron.expanded {
          transform: rotate(180deg);
        }
        
        .tool-dropdown {
          position: absolute;
          top: calc(100% + 4px);
          left: 0;
          min-width: 180px;
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          z-index: 100;
          overflow: hidden;
        }
        
        .dropdown-header {
          padding: 8px 12px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #888;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .tool-item {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          padding: 8px 12px;
          border: none;
          background: transparent;
          color: #c0c0d0;
          cursor: pointer;
          text-align: left;
          transition: all 0.15s ease;
        }
        
        .tool-item:hover {
          background: rgba(255,255,255,0.08);
          color: #fff;
        }
        
        .tool-item.active {
          background: rgba(59, 130, 246, 0.15);
          color: #60a5fa;
        }
        
        .tool-name {
          flex: 1;
          font-size: 13px;
        }
        
        .tool-shortcut {
          font-size: 11px;
          color: #666;
          font-family: 'SF Mono', monospace;
        }
        
        .active-tool-display {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: rgba(59, 130, 246, 0.15);
          border-radius: 4px;
          color: #60a5fa;
          font-size: 12px;
          font-weight: 500;
        }
        
        .snap-section {
          position: relative;
        }
        
        .snap-toggle {
          padding: 6px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 6px;
          color: #a0a0b0;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .snap-toggle:hover {
          background: rgba(255,255,255,0.1);
        }
        
        .snap-toggle.active {
          background: rgba(34, 197, 94, 0.2);
          border-color: rgba(34, 197, 94, 0.5);
          color: #4ade80;
        }
        
        .snap-settings-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
        }
        
        .snap-settings-btn:hover {
          color: #fff;
        }
        
        .snap-panel {
          position: absolute;
          top: calc(100% + 4px);
          right: 0;
          width: 220px;
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          z-index: 100;
          padding: 12px;
        }
        
        .snap-panel-header {
          font-size: 12px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 12px;
        }
        
        .snap-modes {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 4px;
          margin-bottom: 12px;
        }
        
        .snap-mode-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 4px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .snap-mode-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .snap-mode-btn.active {
          background: rgba(34, 197, 94, 0.15);
          border-color: rgba(34, 197, 94, 0.3);
          color: #4ade80;
        }
        
        .snap-options {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding-top: 8px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .snap-option {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: #a0a0b0;
        }
        
        .snap-option input {
          width: 60px;
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 12px;
        }
        
        .toolbar-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 6px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 6px;
          color: #a0a0b0;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .toolbar-btn:hover:not(:disabled) {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .toolbar-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        
        .delete-btn {
          background: rgba(239, 68, 68, 0.1);
          color: #f87171;
          gap: 4px;
        }
        
        .delete-btn:hover {
          background: rgba(239, 68, 68, 0.2);
          color: #fca5a5;
        }
        
        .selection-count {
          font-size: 11px;
          font-weight: 600;
        }
      `}</style>
        </div>
    );
};

export default CADToolbar;
