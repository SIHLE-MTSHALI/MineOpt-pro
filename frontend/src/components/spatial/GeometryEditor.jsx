/**
 * GeometryEditor.jsx - Polygon Geometry Editing Tools
 * 
 * Provides:
 * - Vertex editing mode (drag corners)
 * - Split polygon tool
 * - Merge areas tool
 * - Undo/redo for geometry changes
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
    Move, Scissors, Merge, Undo2, Redo2, Save, X,
    MousePointer, Edit3, Trash2
} from 'lucide-react';

/**
 * Geometry editing modes
 */
const EditMode = {
    SELECT: 'select',
    VERTEX: 'vertex',
    SPLIT: 'split',
    MERGE: 'merge'
};

/**
 * Geometry editing toolbar and controls
 */
const GeometryEditor = ({
    area,
    onSave,
    onCancel,
    onGeometryChange
}) => {
    const [mode, setMode] = useState(EditMode.SELECT);
    const [vertices, setVertices] = useState([]);
    const [selectedVertex, setSelectedVertex] = useState(null);
    const [history, setHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [isDragging, setIsDragging] = useState(false);
    const canvasRef = useRef(null);

    // Initialize vertices from area geometry
    useEffect(() => {
        if (area?.geometry?.coordinates) {
            const coords = area.geometry.coordinates[0] || [];
            setVertices(coords.map((c, i) => ({
                id: i,
                x: c[0],
                y: c[1]
            })));
            pushHistory(coords);
        }
    }, [area]);

    // History management
    const pushHistory = useCallback((newVertices) => {
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push(JSON.stringify(newVertices));
        setHistory(newHistory);
        setHistoryIndex(newHistory.length - 1);
    }, [history, historyIndex]);

    const undo = useCallback(() => {
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            setHistoryIndex(newIndex);
            const prevVertices = JSON.parse(history[newIndex]);
            setVertices(prevVertices.map((c, i) => ({
                id: i, x: c[0], y: c[1]
            })));
        }
    }, [history, historyIndex]);

    const redo = useCallback(() => {
        if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            setHistoryIndex(newIndex);
            const nextVertices = JSON.parse(history[newIndex]);
            setVertices(nextVertices.map((c, i) => ({
                id: i, x: c[0], y: c[1]
            })));
        }
    }, [history, historyIndex]);

    // Vertex drag handling
    const handleVertexMouseDown = useCallback((vertexId, e) => {
        if (mode === EditMode.VERTEX) {
            e.stopPropagation();
            setSelectedVertex(vertexId);
            setIsDragging(true);
        }
    }, [mode]);

    const handleMouseMove = useCallback((e) => {
        if (isDragging && selectedVertex !== null && canvasRef.current) {
            const rect = canvasRef.current.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width * 100;
            const y = (e.clientY - rect.top) / rect.height * 100;

            setVertices(prev => prev.map(v =>
                v.id === selectedVertex ? { ...v, x, y } : v
            ));
        }
    }, [isDragging, selectedVertex]);

    const handleMouseUp = useCallback(() => {
        if (isDragging) {
            setIsDragging(false);
            setSelectedVertex(null);
            pushHistory(vertices.map(v => [v.x, v.y]));
            onGeometryChange?.(vertices);
        }
    }, [isDragging, vertices, pushHistory, onGeometryChange]);

    // Split polygon at two selected vertices
    const handleSplit = useCallback((vertex1Id, vertex2Id) => {
        // Find indices
        const idx1 = vertices.findIndex(v => v.id === vertex1Id);
        const idx2 = vertices.findIndex(v => v.id === vertex2Id);

        if (idx1 === -1 || idx2 === -1 || idx1 === idx2) return;

        const [minIdx, maxIdx] = [Math.min(idx1, idx2), Math.max(idx1, idx2)];

        // Create two polygons
        const poly1 = vertices.slice(minIdx, maxIdx + 1);
        const poly2 = [...vertices.slice(maxIdx), ...vertices.slice(0, minIdx + 1)];

        console.log('Split into:', poly1.length, 'and', poly2.length, 'vertices');
        // In full implementation, would create two new areas

        pushHistory(vertices.map(v => [v.x, v.y]));
    }, [vertices, pushHistory]);

    // Merge with another area
    const handleMerge = useCallback((otherAreaId) => {
        console.log('Merge with area:', otherAreaId);
        // In full implementation, would combine vertices
    }, []);

    // Add vertex between two existing vertices
    const addVertex = useCallback((afterVertexId) => {
        const idx = vertices.findIndex(v => v.id === afterVertexId);
        if (idx === -1) return;

        const nextIdx = (idx + 1) % vertices.length;
        const curr = vertices[idx];
        const next = vertices[nextIdx];

        const newVertex = {
            id: Date.now(),
            x: (curr.x + next.x) / 2,
            y: (curr.y + next.y) / 2
        };

        const newVertices = [
            ...vertices.slice(0, idx + 1),
            newVertex,
            ...vertices.slice(idx + 1)
        ];

        setVertices(newVertices);
        pushHistory(newVertices.map(v => [v.x, v.y]));
    }, [vertices, pushHistory]);

    // Delete vertex
    const deleteVertex = useCallback((vertexId) => {
        if (vertices.length <= 3) return; // Minimum triangle

        const newVertices = vertices.filter(v => v.id !== vertexId);
        setVertices(newVertices);
        pushHistory(newVertices.map(v => [v.x, v.y]));
    }, [vertices, pushHistory]);

    // Save changes
    const handleSave = useCallback(() => {
        const coordinates = [vertices.map(v => [v.x, v.y])];
        // Close the polygon
        if (coordinates[0].length > 0) {
            coordinates[0].push(coordinates[0][0]);
        }
        onSave?.({
            ...area,
            geometry: {
                type: 'Polygon',
                coordinates
            }
        });
    }, [area, vertices, onSave]);

    return (
        <div className="geometry-editor">
            {/* Toolbar */}
            <div className="geometry-toolbar">
                <div className="tool-group">
                    <button
                        className={`tool-btn ${mode === EditMode.SELECT ? 'active' : ''}`}
                        onClick={() => setMode(EditMode.SELECT)}
                        title="Select Mode"
                    >
                        <MousePointer size={18} />
                    </button>
                    <button
                        className={`tool-btn ${mode === EditMode.VERTEX ? 'active' : ''}`}
                        onClick={() => setMode(EditMode.VERTEX)}
                        title="Edit Vertices"
                    >
                        <Edit3 size={18} />
                    </button>
                    <button
                        className={`tool-btn ${mode === EditMode.SPLIT ? 'active' : ''}`}
                        onClick={() => setMode(EditMode.SPLIT)}
                        title="Split Polygon"
                    >
                        <Scissors size={18} />
                    </button>
                    <button
                        className={`tool-btn ${mode === EditMode.MERGE ? 'active' : ''}`}
                        onClick={() => setMode(EditMode.MERGE)}
                        title="Merge Areas"
                    >
                        <Merge size={18} />
                    </button>
                </div>

                <div className="tool-group">
                    <button
                        className="tool-btn"
                        onClick={undo}
                        disabled={historyIndex <= 0}
                        title="Undo"
                    >
                        <Undo2 size={18} />
                    </button>
                    <button
                        className="tool-btn"
                        onClick={redo}
                        disabled={historyIndex >= history.length - 1}
                        title="Redo"
                    >
                        <Redo2 size={18} />
                    </button>
                </div>

                <div className="tool-group">
                    <button className="tool-btn save" onClick={handleSave} title="Save">
                        <Save size={18} />
                    </button>
                    <button className="tool-btn cancel" onClick={onCancel} title="Cancel">
                        <X size={18} />
                    </button>
                </div>
            </div>

            {/* Canvas */}
            <div
                ref={canvasRef}
                className="geometry-canvas"
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                {/* Polygon edges */}
                <svg className="polygon-svg" viewBox="0 0 100 100">
                    <polygon
                        points={vertices.map(v => `${v.x},${v.y}`).join(' ')}
                        fill="rgba(59, 130, 246, 0.3)"
                        stroke="#3b82f6"
                        strokeWidth="0.5"
                    />
                    {/* Edge lines for better visibility */}
                    {vertices.map((v, i) => {
                        const next = vertices[(i + 1) % vertices.length];
                        return (
                            <line
                                key={`edge-${i}`}
                                x1={v.x} y1={v.y}
                                x2={next.x} y2={next.y}
                                stroke="#3b82f6"
                                strokeWidth="0.3"
                            />
                        );
                    })}
                </svg>

                {/* Vertex handles */}
                {mode === EditMode.VERTEX && vertices.map((vertex, i) => (
                    <div
                        key={vertex.id}
                        className={`vertex-handle ${selectedVertex === vertex.id ? 'selected' : ''}`}
                        style={{
                            left: `${vertex.x}%`,
                            top: `${vertex.y}%`
                        }}
                        onMouseDown={(e) => handleVertexMouseDown(vertex.id, e)}
                        onDoubleClick={() => deleteVertex(vertex.id)}
                        title={`Vertex ${i + 1} (double-click to delete)`}
                    >
                        {i + 1}
                    </div>
                ))}

                {/* Add vertex button on edges */}
                {mode === EditMode.VERTEX && vertices.map((v, i) => {
                    const next = vertices[(i + 1) % vertices.length];
                    return (
                        <button
                            key={`add-${i}`}
                            className="add-vertex-btn"
                            style={{
                                left: `${(v.x + next.x) / 2}%`,
                                top: `${(v.y + next.y) / 2}%`
                            }}
                            onClick={() => addVertex(v.id)}
                            title="Add vertex here"
                        >
                            +
                        </button>
                    );
                })}
            </div>

            {/* Mode instructions */}
            <div className="mode-instructions">
                {mode === EditMode.SELECT && 'Click to select areas'}
                {mode === EditMode.VERTEX && 'Drag vertices to move. Double-click to delete. Click + to add vertex.'}
                {mode === EditMode.SPLIT && 'Click two vertices to split polygon'}
                {mode === EditMode.MERGE && 'Click another area to merge'}
            </div>

            <style jsx>{`
        .geometry-editor {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--bg-secondary, #1a1a2e);
          border-radius: 8px;
          overflow: hidden;
        }
        
        .geometry-toolbar {
          display: flex;
          gap: 16px;
          padding: 12px;
          background: var(--bg-primary, #0f0f1a);
          border-bottom: 1px solid var(--border-color, #2a2a4a);
        }
        
        .tool-group {
          display: flex;
          gap: 4px;
        }
        
        .tool-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border: 1px solid var(--border-color, #2a2a4a);
          background: transparent;
          color: var(--text-secondary, #a0a0b0);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .tool-btn:hover:not(:disabled) {
          background: var(--bg-hover, #2a2a4a);
          color: var(--text-primary, #fff);
        }
        
        .tool-btn.active {
          background: var(--accent-primary, #3b82f6);
          color: white;
          border-color: var(--accent-primary, #3b82f6);
        }
        
        .tool-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        
        .tool-btn.save {
          background: var(--success, #10b981);
          border-color: var(--success, #10b981);
          color: white;
        }
        
        .tool-btn.cancel {
          background: var(--danger, #ef4444);
          border-color: var(--danger, #ef4444);
          color: white;
        }
        
        .geometry-canvas {
          flex: 1;
          position: relative;
          background: var(--bg-tertiary, #141428);
          cursor: ${mode === EditMode.VERTEX ? 'crosshair' : 'default'};
        }
        
        .polygon-svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }
        
        .vertex-handle {
          position: absolute;
          transform: translate(-50%, -50%);
          width: 20px;
          height: 20px;
          background: var(--accent-primary, #3b82f6);
          border: 2px solid white;
          border-radius: 50%;
          cursor: move;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: bold;
          color: white;
          z-index: 10;
          transition: transform 0.1s;
        }
        
        .vertex-handle:hover {
          transform: translate(-50%, -50%) scale(1.2);
        }
        
        .vertex-handle.selected {
          background: var(--warning, #f59e0b);
          box-shadow: 0 0 12px var(--warning, #f59e0b);
        }
        
        .add-vertex-btn {
          position: absolute;
          transform: translate(-50%, -50%);
          width: 16px;
          height: 16px;
          background: var(--success, #10b981);
          border: none;
          border-radius: 50%;
          cursor: pointer;
          font-size: 12px;
          font-weight: bold;
          color: white;
          opacity: 0.6;
          transition: all 0.2s;
          z-index: 5;
        }
        
        .add-vertex-btn:hover {
          opacity: 1;
          transform: translate(-50%, -50%) scale(1.3);
        }
        
        .mode-instructions {
          padding: 8px 12px;
          background: var(--bg-primary, #0f0f1a);
          color: var(--text-secondary, #a0a0b0);
          font-size: 12px;
          text-align: center;
          border-top: 1px solid var(--border-color, #2a2a4a);
        }
      `}</style>
        </div>
    );
};

export default GeometryEditor;
