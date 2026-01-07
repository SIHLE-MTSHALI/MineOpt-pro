/**
 * CADStringEditor.jsx - Phase 6
 * 
 * Interactive CAD string editor with vertex manipulation.
 * 
 * Features:
 * - Real-time vertex handles for editing
 * - Insert/delete/move vertices
 * - Keyboard shortcuts
 * - Undo/redo integration
 * - Visual feedback during editing
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
    Plus,
    Minus,
    Move,
    X,
    Save,
    RotateCcw,
    Check,
    Trash2,
    Copy,
    CircleDot,
    GitBranch,
    Merge,
    ArrowRightLeft
} from 'lucide-react';

// Vertex handle component
const VertexHandle = ({
    index,
    x,
    y,
    z,
    isSelected,
    isFirst,
    isLast,
    onSelect,
    onMove,
    onInsertBefore,
    onInsertAfter,
    onDelete,
    worldToScreen
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [showMenu, setShowMenu] = useState(false);

    const screenPos = worldToScreen ? worldToScreen(x, y, z) : { x, y };

    const handleMouseDown = (e) => {
        e.stopPropagation();
        if (e.button === 0) {
            setIsDragging(true);
            onSelect?.(index);
        } else if (e.button === 2) {
            setShowMenu(!showMenu);
        }
    };

    const handleContextMenu = (e) => {
        e.preventDefault();
        setShowMenu(!showMenu);
    };

    return (
        <div
            className={`vertex-handle ${isSelected ? 'selected' : ''} ${isFirst ? 'first' : ''} ${isLast ? 'last' : ''}`}
            style={{
                left: screenPos.x,
                top: screenPos.y,
                transform: 'translate(-50%, -50%)'
            }}
            onMouseDown={handleMouseDown}
            onContextMenu={handleContextMenu}
        >
            <div className="handle-dot" />
            <div className="handle-index">{index}</div>

            {showMenu && (
                <div className="vertex-menu" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => { onInsertBefore?.(index); setShowMenu(false); }}>
                        <Plus size={12} /> Insert Before
                    </button>
                    <button onClick={() => { onInsertAfter?.(index); setShowMenu(false); }}>
                        <Plus size={12} /> Insert After
                    </button>
                    <div className="menu-separator" />
                    <button
                        onClick={() => { onDelete?.(index); setShowMenu(false); }}
                        className="delete-btn"
                    >
                        <Trash2 size={12} /> Delete
                    </button>
                </div>
            )}

            <style jsx>{`
        .vertex-handle {
          position: absolute;
          z-index: 10;
          cursor: pointer;
        }
        
        .handle-dot {
          width: 10px;
          height: 10px;
          background: #3b82f6;
          border: 2px solid #fff;
          border-radius: 50%;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          transition: all 0.15s ease;
        }
        
        .vertex-handle:hover .handle-dot {
          width: 14px;
          height: 14px;
          margin: -2px;
        }
        
        .vertex-handle.selected .handle-dot {
          background: #f59e0b;
          width: 14px;
          height: 14px;
          margin: -2px;
        }
        
        .vertex-handle.first .handle-dot {
          background: #22c55e;
        }
        
        .vertex-handle.last .handle-dot {
          background: #ef4444;
        }
        
        .handle-index {
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 10px;
          color: #fff;
          background: rgba(0,0,0,0.7);
          padding: 2px 6px;
          border-radius: 3px;
          pointer-events: none;
          opacity: 0;
          transition: opacity 0.15s ease;
        }
        
        .vertex-handle:hover .handle-index {
          opacity: 1;
        }
        
        .vertex-menu {
          position: absolute;
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 6px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4);
          min-width: 140px;
          padding: 4px;
          z-index: 100;
        }
        
        .vertex-menu button {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 6px 10px;
          border: none;
          background: transparent;
          color: #c0c0d0;
          font-size: 12px;
          cursor: pointer;
          border-radius: 4px;
          text-align: left;
        }
        
        .vertex-menu button:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .vertex-menu .delete-btn:hover {
          background: rgba(239, 68, 68, 0.15);
          color: #f87171;
        }
        
        .menu-separator {
          height: 1px;
          background: rgba(255,255,255,0.1);
          margin: 4px 0;
        }
      `}</style>
        </div>
    );
};

// Main Editor Component
const CADStringEditor = ({
    string,
    isEditing,
    onStartEdit,
    onEndEdit,
    onSave,
    onCancel,
    onVertexInsert,
    onVertexDelete,
    onVertexMove,
    onSplit,
    onReverse,
    onClose,
    onOpen,
    worldToScreen,
    screenToWorld,
    className = ''
}) => {
    const [selectedVertex, setSelectedVertex] = useState(null);
    const [editHistory, setEditHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [localVertices, setLocalVertices] = useState([]);

    // Initialize local vertices when string changes
    useEffect(() => {
        if (string?.vertices) {
            setLocalVertices([...string.vertices]);
            setEditHistory([string.vertices]);
            setHistoryIndex(0);
        }
    }, [string?.string_id]);

    // Keyboard shortcuts
    useEffect(() => {
        if (!isEditing) return;

        const handleKeyDown = (e) => {
            // Escape to cancel
            if (e.key === 'Escape') {
                onCancel?.();
                return;
            }

            // Enter to save
            if (e.key === 'Enter') {
                handleSave();
                return;
            }

            // Delete selected vertex
            if ((e.key === 'Delete' || e.key === 'Backspace') && selectedVertex !== null) {
                handleDeleteVertex(selectedVertex);
                return;
            }

            // Undo/Redo
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                handleUndo();
                return;
            }

            if (e.ctrlKey && e.key === 'y') {
                e.preventDefault();
                handleRedo();
                return;
            }

            // Arrow keys to move selected vertex
            if (selectedVertex !== null && e.key.startsWith('Arrow')) {
                e.preventDefault();
                const delta = e.shiftKey ? 10 : 1;
                const vertex = localVertices[selectedVertex];
                let newX = vertex[0];
                let newY = vertex[1];

                switch (e.key) {
                    case 'ArrowUp': newY += delta; break;
                    case 'ArrowDown': newY -= delta; break;
                    case 'ArrowLeft': newX -= delta; break;
                    case 'ArrowRight': newX += delta; break;
                }

                handleMoveVertex(selectedVertex, newX, newY, vertex[2]);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isEditing, selectedVertex, localVertices, historyIndex]);

    // Add to history
    const addToHistory = useCallback((vertices) => {
        const newHistory = editHistory.slice(0, historyIndex + 1);
        newHistory.push([...vertices]);
        setEditHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    }, [editHistory, historyIndex]);

    // Undo
    const handleUndo = useCallback(() => {
        if (historyIndex > 0) {
            setHistoryIndex(historyIndex - 1);
            setLocalVertices([...editHistory[historyIndex - 1]]);
        }
    }, [historyIndex, editHistory]);

    // Redo
    const handleRedo = useCallback(() => {
        if (historyIndex < editHistory.length - 1) {
            setHistoryIndex(historyIndex + 1);
            setLocalVertices([...editHistory[historyIndex + 1]]);
        }
    }, [historyIndex, editHistory]);

    // Insert vertex
    const handleInsertVertex = useCallback((index, before = false) => {
        if (localVertices.length < 2) return;

        const refIndex = before ? index : index + 1;
        const prevIndex = before ? index - 1 : index;
        const nextIndex = before ? index : index + 1;

        // Calculate midpoint
        let newVertex;
        if (prevIndex >= 0 && nextIndex < localVertices.length) {
            const prev = localVertices[prevIndex];
            const next = localVertices[nextIndex % localVertices.length];
            newVertex = [
                (prev[0] + next[0]) / 2,
                (prev[1] + next[1]) / 2,
                (prev[2] + next[2]) / 2
            ];
        } else {
            // Edge case - add at start or end
            const ref = localVertices[index];
            newVertex = [ref[0] + 10, ref[1] + 10, ref[2]];
        }

        const newVertices = [...localVertices];
        newVertices.splice(before ? index : index + 1, 0, newVertex);
        setLocalVertices(newVertices);
        addToHistory(newVertices);

        onVertexInsert?.(before ? index : index + 1, newVertex);
    }, [localVertices, addToHistory, onVertexInsert]);

    // Delete vertex
    const handleDeleteVertex = useCallback((index) => {
        if (localVertices.length <= 2) return; // Need at least 2 vertices

        const newVertices = localVertices.filter((_, i) => i !== index);
        setLocalVertices(newVertices);
        addToHistory(newVertices);
        setSelectedVertex(null);

        onVertexDelete?.(index);
    }, [localVertices, addToHistory, onVertexDelete]);

    // Move vertex
    const handleMoveVertex = useCallback((index, x, y, z) => {
        const newVertices = [...localVertices];
        newVertices[index] = [x, y, z];
        setLocalVertices(newVertices);

        onVertexMove?.(index, x, y, z);
    }, [localVertices, onVertexMove]);

    // Complete move (add to history)
    const handleMoveComplete = useCallback(() => {
        addToHistory(localVertices);
    }, [localVertices, addToHistory]);

    // Save changes
    const handleSave = useCallback(() => {
        onSave?.(localVertices);
        onEndEdit?.();
    }, [localVertices, onSave, onEndEdit]);

    // Calculate stats
    const stats = useMemo(() => {
        if (!localVertices?.length) return null;

        let length = 0;
        for (let i = 1; i < localVertices.length; i++) {
            const dx = localVertices[i][0] - localVertices[i - 1][0];
            const dy = localVertices[i][1] - localVertices[i - 1][1];
            const dz = localVertices[i][2] - localVertices[i - 1][2];
            length += Math.sqrt(dx * dx + dy * dy + dz * dz);
        }

        return {
            vertexCount: localVertices.length,
            length: length.toFixed(2),
            canUndo: historyIndex > 0,
            canRedo: historyIndex < editHistory.length - 1
        };
    }, [localVertices, historyIndex, editHistory]);

    if (!string) return null;

    return (
        <div className={`cad-string-editor ${className}`}>
            {/* Info Bar */}
            <div className="editor-info">
                <div className="string-name">{string.name}</div>
                <div className="string-type">{string.string_type}</div>
                <div className="vertex-count">{stats?.vertexCount || 0} vertices</div>
                <div className="string-length">{stats?.length || 0}m</div>
            </div>

            {/* Toolbar */}
            {isEditing && (
                <div className="editor-toolbar">
                    <button
                        onClick={handleUndo}
                        disabled={!stats?.canUndo}
                        title="Undo (Ctrl+Z)"
                    >
                        <RotateCcw size={14} />
                    </button>

                    <button
                        onClick={handleRedo}
                        disabled={!stats?.canRedo}
                        title="Redo (Ctrl+Y)"
                    >
                        <RotateCcw size={14} style={{ transform: 'scaleX(-1)' }} />
                    </button>

                    <div className="toolbar-sep" />

                    <button onClick={onReverse} title="Reverse Direction">
                        <ArrowRightLeft size={14} />
                    </button>

                    <button onClick={string.is_closed ? onOpen : onClose} title={string.is_closed ? 'Open String' : 'Close String'}>
                        {string.is_closed ? <GitBranch size={14} /> : <CircleDot size={14} />}
                    </button>

                    <div className="toolbar-sep" />

                    <button className="save-btn" onClick={handleSave} title="Save (Enter)">
                        <Check size={14} /> Save
                    </button>

                    <button className="cancel-btn" onClick={onCancel} title="Cancel (Esc)">
                        <X size={14} />
                    </button>
                </div>
            )}

            {/* Vertex Handles */}
            {isEditing && localVertices.map((vertex, index) => (
                <VertexHandle
                    key={index}
                    index={index}
                    x={vertex[0]}
                    y={vertex[1]}
                    z={vertex[2]}
                    isSelected={selectedVertex === index}
                    isFirst={index === 0}
                    isLast={index === localVertices.length - 1}
                    onSelect={setSelectedVertex}
                    onMove={(x, y, z) => handleMoveVertex(index, x, y, z)}
                    onInsertBefore={() => handleInsertVertex(index, true)}
                    onInsertAfter={() => handleInsertVertex(index, false)}
                    onDelete={() => handleDeleteVertex(index)}
                    worldToScreen={worldToScreen}
                />
            ))}

            {/* Selected Vertex Info */}
            {isEditing && selectedVertex !== null && localVertices[selectedVertex] && (
                <div className="vertex-info">
                    <div className="info-header">Vertex {selectedVertex}</div>
                    <div className="coord-row">
                        <label>X:</label>
                        <input
                            type="number"
                            value={localVertices[selectedVertex][0].toFixed(3)}
                            onChange={(e) => handleMoveVertex(
                                selectedVertex,
                                parseFloat(e.target.value) || 0,
                                localVertices[selectedVertex][1],
                                localVertices[selectedVertex][2]
                            )}
                            onBlur={handleMoveComplete}
                        />
                    </div>
                    <div className="coord-row">
                        <label>Y:</label>
                        <input
                            type="number"
                            value={localVertices[selectedVertex][1].toFixed(3)}
                            onChange={(e) => handleMoveVertex(
                                selectedVertex,
                                localVertices[selectedVertex][0],
                                parseFloat(e.target.value) || 0,
                                localVertices[selectedVertex][2]
                            )}
                            onBlur={handleMoveComplete}
                        />
                    </div>
                    <div className="coord-row">
                        <label>Z:</label>
                        <input
                            type="number"
                            value={localVertices[selectedVertex][2].toFixed(3)}
                            onChange={(e) => handleMoveVertex(
                                selectedVertex,
                                localVertices[selectedVertex][0],
                                localVertices[selectedVertex][1],
                                parseFloat(e.target.value) || 0
                            )}
                            onBlur={handleMoveComplete}
                        />
                    </div>
                </div>
            )}

            <style jsx>{`
        .cad-string-editor {
          position: relative;
        }
        
        .editor-info {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 8px 16px;
          background: rgba(30, 30, 46, 0.95);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          font-size: 12px;
        }
        
        .string-name {
          font-weight: 600;
          color: #fff;
        }
        
        .string-type {
          padding: 2px 8px;
          background: rgba(59, 130, 246, 0.2);
          border-radius: 4px;
          color: #60a5fa;
          text-transform: capitalize;
        }
        
        .vertex-count, .string-length {
          color: #888;
        }
        
        .editor-toolbar {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 8px 16px;
          background: rgba(30, 30, 46, 0.9);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .editor-toolbar button {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 6px 10px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 4px;
          color: #a0a0b0;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .editor-toolbar button:hover:not(:disabled) {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .editor-toolbar button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        
        .save-btn {
          background: rgba(34, 197, 94, 0.15) !important;
          border-color: rgba(34, 197, 94, 0.3) !important;
          color: #4ade80 !important;
        }
        
        .save-btn:hover {
          background: rgba(34, 197, 94, 0.25) !important;
        }
        
        .cancel-btn {
          background: rgba(239, 68, 68, 0.1) !important;
          color: #f87171 !important;
        }
        
        .toolbar-sep {
          width: 1px;
          height: 20px;
          background: rgba(255,255,255,0.15);
          margin: 0 4px;
        }
        
        .vertex-info {
          position: absolute;
          bottom: 20px;
          right: 20px;
          padding: 12px;
          background: rgba(30, 30, 46, 0.95);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          min-width: 180px;
        }
        
        .info-header {
          font-size: 12px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 10px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .coord-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }
        
        .coord-row label {
          width: 20px;
          font-size: 12px;
          color: #888;
          font-weight: 500;
        }
        
        .coord-row input {
          flex: 1;
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 12px;
          font-family: 'SF Mono', monospace;
        }
        
        .coord-row input:focus {
          border-color: rgba(59, 130, 246, 0.5);
          outline: none;
        }
      `}</style>
        </div>
    );
};

export default CADStringEditor;
