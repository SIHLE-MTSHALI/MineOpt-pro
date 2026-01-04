/**
 * FlowEditor.jsx - Material Flow Diagram Editor
 * 
 * Canvas-based visual editor for mining flow networks:
 * - Drag and drop nodes (pits, stockpiles, plants, destinations)
 * - Connect nodes with arcs
 * - Configure node properties and arc quality objectives
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
    Mountain, Box, Factory, Target, Trash2, Plus, Save, Undo,
    ZoomIn, ZoomOut, Settings, Link, XCircle, ArrowRight
} from 'lucide-react';

// Node type definitions with icons and colors
const NODE_TYPES = {
    SourcePit: { icon: Mountain, color: '#f59e0b', label: 'Source Pit' },
    Stockpile: { icon: Box, color: '#3b82f6', label: 'Stockpile' },
    StagedStockpile: { icon: Box, color: '#8b5cf6', label: 'Staged Stockpile' },
    WashPlant: { icon: Factory, color: '#10b981', label: 'Wash Plant' },
    Destination: { icon: Target, color: '#ef4444', label: 'Destination' },
    Dump: { icon: Trash2, color: '#6b7280', label: 'Dump' }
};

// Flow Node Component
const FlowNode = ({ node, selected, onSelect, onDrag, onDragEnd }) => {
    const nodeType = NODE_TYPES[node.type] || NODE_TYPES.Stockpile;
    const Icon = nodeType.icon;

    const handleMouseDown = (e) => {
        e.stopPropagation();
        onSelect(node.id);
        const startX = e.clientX - node.x;
        const startY = e.clientY - node.y;

        const handleMouseMove = (e) => {
            onDrag(node.id, e.clientX - startX, e.clientY - startY);
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            onDragEnd(node.id);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    return (
        <g transform={`translate(${node.x}, ${node.y})`} onMouseDown={handleMouseDown}>
            <rect
                x="-50" y="-30"
                width="100" height="60"
                rx="8"
                fill={selected ? nodeType.color : `${nodeType.color}cc`}
                stroke={selected ? '#fff' : 'transparent'}
                strokeWidth="2"
                className="cursor-move transition-all"
            />
            <foreignObject x="-50" y="-30" width="100" height="60">
                <div className="flex flex-col items-center justify-center h-full text-white select-none">
                    <Icon size={20} />
                    <span className="text-xs mt-1 font-medium truncate w-20 text-center">{node.name}</span>
                </div>
            </foreignObject>
            {/* Connection points */}
            <circle cx="50" cy="0" r="6" fill="#374151" stroke="#fff" strokeWidth="1" className="cursor-crosshair" />
            <circle cx="-50" cy="0" r="6" fill="#374151" stroke="#fff" strokeWidth="1" className="cursor-crosshair" />
        </g>
    );
};

// Arc Component
const FlowArc = ({ arc, nodes, selected, onSelect }) => {
    const fromNode = nodes.find(n => n.id === arc.from);
    const toNode = nodes.find(n => n.id === arc.to);

    if (!fromNode || !toNode) return null;

    const startX = fromNode.x + 50;
    const startY = fromNode.y;
    const endX = toNode.x - 50;
    const endY = toNode.y;

    // Bezier control points
    const midX = (startX + endX) / 2;

    return (
        <g onClick={(e) => { e.stopPropagation(); onSelect(arc.id); }}>
            <path
                d={`M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`}
                stroke={selected ? '#3b82f6' : '#475569'}
                strokeWidth={selected ? 3 : 2}
                fill="none"
                markerEnd="url(#arrowhead)"
                className="cursor-pointer"
            />
            {/* Arc label */}
            <text
                x={midX}
                y={(startY + endY) / 2 - 10}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="10"
            >
                {arc.label || ''}
            </text>
        </g>
    );
};

// Node Palette Component
const NodePalette = ({ onAddNode }) => {
    return (
        <div className="absolute left-4 top-4 bg-slate-900/95 border border-slate-700 rounded-lg p-3 space-y-2">
            <div className="text-xs text-slate-400 font-semibold uppercase mb-2">Add Node</div>
            {Object.entries(NODE_TYPES).map(([type, config]) => {
                const Icon = config.icon;
                return (
                    <button
                        key={type}
                        onClick={() => onAddNode(type)}
                        className="flex items-center space-x-2 w-full p-2 rounded hover:bg-slate-800 transition-colors text-slate-300 hover:text-white"
                    >
                        <Icon size={16} style={{ color: config.color }} />
                        <span className="text-xs">{config.label}</span>
                    </button>
                );
            })}
        </div>
    );
};

// Properties Panel Component
const PropertiesPanel = ({ selectedNode, selectedArc, nodes, arcs, onUpdateNode, onUpdateArc, onDeleteNode, onDeleteArc }) => {
    if (!selectedNode && !selectedArc) {
        return (
            <div className="absolute right-4 top-4 bg-slate-900/95 border border-slate-700 rounded-lg p-4 w-64">
                <div className="text-slate-400 text-sm">Select a node or arc to edit properties</div>
            </div>
        );
    }

    if (selectedNode) {
        const node = nodes.find(n => n.id === selectedNode);
        if (!node) return null;

        return (
            <div className="absolute right-4 top-4 bg-slate-900/95 border border-slate-700 rounded-lg p-4 w-64">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-white font-semibold">Node Properties</h3>
                    <button onClick={() => onDeleteNode(node.id)} className="text-red-400 hover:text-red-300">
                        <Trash2 size={16} />
                    </button>
                </div>

                <div className="space-y-3">
                    <div>
                        <label className="text-xs text-slate-400">Name</label>
                        <input
                            type="text"
                            value={node.name}
                            onChange={(e) => onUpdateNode(node.id, { name: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        />
                    </div>

                    <div>
                        <label className="text-xs text-slate-400">Type</label>
                        <select
                            value={node.type}
                            onChange={(e) => onUpdateNode(node.id, { type: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        >
                            {Object.entries(NODE_TYPES).map(([type, config]) => (
                                <option key={type} value={type}>{config.label}</option>
                            ))}
                        </select>
                    </div>

                    {(node.type === 'Stockpile' || node.type === 'StagedStockpile') && (
                        <div>
                            <label className="text-xs text-slate-400">Capacity (tonnes)</label>
                            <input
                                type="number"
                                value={node.capacity || ''}
                                onChange={(e) => onUpdateNode(node.id, { capacity: parseFloat(e.target.value) || 0 })}
                                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                            />
                        </div>
                    )}

                    {node.type === 'WashPlant' && (
                        <div>
                            <label className="text-xs text-slate-400">Feed Capacity (tph)</label>
                            <input
                                type="number"
                                value={node.feedCapacity || ''}
                                onChange={(e) => onUpdateNode(node.id, { feedCapacity: parseFloat(e.target.value) || 0 })}
                                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                            />
                        </div>
                    )}
                </div>
            </div>
        );
    }

    if (selectedArc) {
        const arc = arcs.find(a => a.id === selectedArc);
        if (!arc) return null;

        const fromNode = nodes.find(n => n.id === arc.from);
        const toNode = nodes.find(n => n.id === arc.to);

        return (
            <div className="absolute right-4 top-4 bg-slate-900/95 border border-slate-700 rounded-lg p-4 w-64">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-white font-semibold">Arc Properties</h3>
                    <button onClick={() => onDeleteArc(arc.id)} className="text-red-400 hover:text-red-300">
                        <Trash2 size={16} />
                    </button>
                </div>

                <div className="space-y-3">
                    <div className="text-xs text-slate-400">
                        <span className="text-blue-400">{fromNode?.name}</span>
                        <ArrowRight size={12} className="inline mx-1" />
                        <span className="text-green-400">{toNode?.name}</span>
                    </div>

                    <div>
                        <label className="text-xs text-slate-400">Max Throughput (tph)</label>
                        <input
                            type="number"
                            value={arc.maxThroughput || ''}
                            onChange={(e) => onUpdateArc(arc.id, { maxThroughput: parseFloat(e.target.value) || 0 })}
                            className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        />
                    </div>

                    <div>
                        <label className="text-xs text-slate-400">Priority</label>
                        <input
                            type="number"
                            value={arc.priority || 0}
                            onChange={(e) => onUpdateArc(arc.id, { priority: parseInt(e.target.value) || 0 })}
                            className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        />
                    </div>

                    <div>
                        <label className="text-xs text-slate-400 block mb-1">Material Filter</label>
                        <select
                            value={arc.materialFilter || 'All'}
                            onChange={(e) => onUpdateArc(arc.id, { materialFilter: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        >
                            <option value="All">All Materials</option>
                            <option value="Coal">Coal Only</option>
                            <option value="Waste">Waste Only</option>
                        </select>
                    </div>

                    {/* Quality Objectives Section */}
                    <div className="border-t border-slate-700 pt-3 mt-3">
                        <div className="flex justify-between items-center mb-2">
                            <label className="text-xs text-slate-400 font-medium">Quality Objectives</label>
                            <button
                                onClick={() => {
                                    const objectives = arc.qualityObjectives || [];
                                    onUpdateArc(arc.id, {
                                        qualityObjectives: [...objectives, {
                                            id: `obj-${Date.now()}`,
                                            field: 'CV',
                                            min: null,
                                            max: null,
                                            target: null,
                                            softness: 'Medium'
                                        }]
                                    });
                                }}
                                className="text-xs text-blue-400 hover:text-blue-300"
                            >
                                + Add
                            </button>
                        </div>

                        {(arc.qualityObjectives || []).map((obj, idx) => (
                            <div key={obj.id} className="bg-slate-800 rounded p-2 mb-2 text-xs">
                                <div className="flex justify-between items-center mb-2">
                                    <select
                                        value={obj.field}
                                        onChange={(e) => {
                                            const updated = [...arc.qualityObjectives];
                                            updated[idx].field = e.target.value;
                                            onUpdateArc(arc.id, { qualityObjectives: updated });
                                        }}
                                        className="bg-slate-700 border border-slate-600 rounded px-1 py-0.5 text-white"
                                    >
                                        <option value="CV">CV (MJ/kg)</option>
                                        <option value="Ash">Ash (%)</option>
                                        <option value="Moisture">Moisture (%)</option>
                                        <option value="Sulphur">Sulphur (%)</option>
                                        <option value="Volatile">Volatile (%)</option>
                                    </select>
                                    <button
                                        onClick={() => {
                                            const updated = arc.qualityObjectives.filter((_, i) => i !== idx);
                                            onUpdateArc(arc.id, { qualityObjectives: updated });
                                        }}
                                        className="text-red-400 hover:text-red-300 p-1"
                                    >
                                        ×
                                    </button>
                                </div>
                                <div className="grid grid-cols-3 gap-1">
                                    <div>
                                        <label className="text-slate-500">Min</label>
                                        <input
                                            type="number"
                                            value={obj.min ?? ''}
                                            onChange={(e) => {
                                                const updated = [...arc.qualityObjectives];
                                                updated[idx].min = e.target.value ? parseFloat(e.target.value) : null;
                                                onUpdateArc(arc.id, { qualityObjectives: updated });
                                            }}
                                            className="w-full bg-slate-700 border border-slate-600 rounded px-1 py-0.5 text-white"
                                            placeholder="-"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-500">Target</label>
                                        <input
                                            type="number"
                                            value={obj.target ?? ''}
                                            onChange={(e) => {
                                                const updated = [...arc.qualityObjectives];
                                                updated[idx].target = e.target.value ? parseFloat(e.target.value) : null;
                                                onUpdateArc(arc.id, { qualityObjectives: updated });
                                            }}
                                            className="w-full bg-slate-700 border border-slate-600 rounded px-1 py-0.5 text-white"
                                            placeholder="-"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-slate-500">Max</label>
                                        <input
                                            type="number"
                                            value={obj.max ?? ''}
                                            onChange={(e) => {
                                                const updated = [...arc.qualityObjectives];
                                                updated[idx].max = e.target.value ? parseFloat(e.target.value) : null;
                                                onUpdateArc(arc.id, { qualityObjectives: updated });
                                            }}
                                            className="w-full bg-slate-700 border border-slate-600 rounded px-1 py-0.5 text-white"
                                            placeholder="-"
                                        />
                                    </div>
                                </div>
                                <div className="mt-1">
                                    <select
                                        value={obj.softness}
                                        onChange={(e) => {
                                            const updated = [...arc.qualityObjectives];
                                            updated[idx].softness = e.target.value;
                                            onUpdateArc(arc.id, { qualityObjectives: updated });
                                        }}
                                        className="w-full bg-slate-700 border border-slate-600 rounded px-1 py-0.5 text-white"
                                    >
                                        <option value="Hard">Hard (must meet)</option>
                                        <option value="Medium">Medium (penalty)</option>
                                        <option value="Soft">Soft (prefer)</option>
                                    </select>
                                </div>
                            </div>
                        ))}

                        {(!arc.qualityObjectives || arc.qualityObjectives.length === 0) && (
                            <div className="text-slate-500 text-xs italic">No quality objectives defined</div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return null;
};

// Toolbar Component
const Toolbar = ({ onSave, onUndo, zoom, onZoomIn, onZoomOut, nodeCount, arcCount }) => {
    return (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-slate-900/95 border border-slate-700 rounded-lg p-2 flex items-center space-x-2">
            <button onClick={onSave} className="p-2 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Save Network">
                <Save size={18} />
            </button>
            <button onClick={onUndo} className="p-2 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Undo">
                <Undo size={18} />
            </button>
            <div className="w-px h-6 bg-slate-700" />
            <button onClick={onZoomOut} className="p-2 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom Out">
                <ZoomOut size={18} />
            </button>
            <span className="text-xs text-slate-400 w-12 text-center">{Math.round(zoom * 100)}%</span>
            <button onClick={onZoomIn} className="p-2 rounded hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom In">
                <ZoomIn size={18} />
            </button>
            <div className="w-px h-6 bg-slate-700" />
            <div className="text-xs text-slate-400 px-2">
                {nodeCount} nodes • {arcCount} arcs
            </div>
        </div>
    );
};

// Main Flow Editor Component
const FlowEditor = ({ networkId, onSave: onExternalSave }) => {
    const svgRef = useRef(null);
    const [nodes, setNodes] = useState([]);
    const [arcs, setArcs] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [selectedArc, setSelectedArc] = useState(null);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [connectingFrom, setConnectingFrom] = useState(null);
    const [history, setHistory] = useState([]);

    // Generate unique ID
    const generateId = () => `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Add new node
    const handleAddNode = useCallback((type) => {
        const newNode = {
            id: generateId(),
            type,
            name: `${NODE_TYPES[type].label} ${nodes.length + 1}`,
            x: 150 + Math.random() * 400,
            y: 100 + Math.random() * 300
        };
        setNodes(prev => [...prev, newNode]);
        setSelectedNode(newNode.id);
        setSelectedArc(null);
    }, [nodes.length]);

    // Update node
    const handleUpdateNode = useCallback((nodeId, updates) => {
        setNodes(prev => prev.map(n => n.id === nodeId ? { ...n, ...updates } : n));
    }, []);

    // Delete node
    const handleDeleteNode = useCallback((nodeId) => {
        setNodes(prev => prev.filter(n => n.id !== nodeId));
        setArcs(prev => prev.filter(a => a.from !== nodeId && a.to !== nodeId));
        setSelectedNode(null);
    }, []);

    // Update arc
    const handleUpdateArc = useCallback((arcId, updates) => {
        setArcs(prev => prev.map(a => a.id === arcId ? { ...a, ...updates } : a));
    }, []);

    // Delete arc
    const handleDeleteArc = useCallback((arcId) => {
        setArcs(prev => prev.filter(a => a.id !== arcId));
        setSelectedArc(null);
    }, []);

    // Drag node
    const handleDragNode = useCallback((nodeId, x, y) => {
        setNodes(prev => prev.map(n => n.id === nodeId ? { ...n, x, y } : n));
    }, []);

    // Create arc between nodes
    const handleCreateArc = useCallback((fromId, toId) => {
        // Prevent duplicate arcs
        const exists = arcs.some(a => a.from === fromId && a.to === toId);
        if (exists || fromId === toId) return;

        const newArc = {
            id: `arc-${Date.now()}`,
            from: fromId,
            to: toId,
            maxThroughput: 500,
            priority: 0,
            materialFilter: 'All'
        };
        setArcs(prev => [...prev, newArc]);
    }, [arcs]);

    // Handle canvas click for arc creation
    const handleNodeSelect = useCallback((nodeId) => {
        if (connectingFrom && connectingFrom !== nodeId) {
            handleCreateArc(connectingFrom, nodeId);
            setConnectingFrom(null);
        } else {
            setSelectedNode(nodeId);
            setSelectedArc(null);
        }
    }, [connectingFrom, handleCreateArc]);

    // Handle arc selection
    const handleArcSelect = useCallback((arcId) => {
        setSelectedArc(arcId);
        setSelectedNode(null);
    }, []);

    // Clear selection on canvas click
    const handleCanvasClick = useCallback(() => {
        setSelectedNode(null);
        setSelectedArc(null);
        setConnectingFrom(null);
    }, []);

    // Zoom controls
    const handleZoomIn = () => setZoom(z => Math.min(z + 0.1, 2));
    const handleZoomOut = () => setZoom(z => Math.max(z - 0.1, 0.5));

    // Save network
    const handleSave = async () => {
        const networkData = { nodes, arcs };
        console.log('Saving network:', networkData);
        if (onExternalSave) {
            await onExternalSave(networkData);
        }
    };

    // Undo
    const handleUndo = () => {
        if (history.length > 0) {
            const prevState = history[history.length - 1];
            setNodes(prevState.nodes);
            setArcs(prevState.arcs);
            setHistory(prev => prev.slice(0, -1));
        }
    };

    // Double-click to start connecting
    const handleNodeDoubleClick = useCallback((nodeId) => {
        setConnectingFrom(nodeId);
    }, []);

    return (
        <div className="relative w-full h-full bg-slate-950 overflow-hidden">
            {/* SVG Canvas */}
            <svg
                ref={svgRef}
                className="w-full h-full"
                onClick={handleCanvasClick}
            >
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#475569" />
                    </marker>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                    </pattern>
                </defs>

                {/* Grid background */}
                <rect width="100%" height="100%" fill="url(#grid)" />

                <g transform={`scale(${zoom}) translate(${pan.x}, ${pan.y})`}>
                    {/* Arcs */}
                    {arcs.map(arc => (
                        <FlowArc
                            key={arc.id}
                            arc={arc}
                            nodes={nodes}
                            selected={selectedArc === arc.id}
                            onSelect={handleArcSelect}
                        />
                    ))}

                    {/* Nodes */}
                    {nodes.map(node => (
                        <FlowNode
                            key={node.id}
                            node={node}
                            selected={selectedNode === node.id || connectingFrom === node.id}
                            onSelect={handleNodeSelect}
                            onDrag={handleDragNode}
                            onDragEnd={() => { }}
                        />
                    ))}
                </g>
            </svg>

            {/* Node Palette */}
            <NodePalette onAddNode={handleAddNode} />

            {/* Properties Panel */}
            <PropertiesPanel
                selectedNode={selectedNode}
                selectedArc={selectedArc}
                nodes={nodes}
                arcs={arcs}
                onUpdateNode={handleUpdateNode}
                onUpdateArc={handleUpdateArc}
                onDeleteNode={handleDeleteNode}
                onDeleteArc={handleDeleteArc}
            />

            {/* Toolbar */}
            <Toolbar
                onSave={handleSave}
                onUndo={handleUndo}
                zoom={zoom}
                onZoomIn={handleZoomIn}
                onZoomOut={handleZoomOut}
                nodeCount={nodes.length}
                arcCount={arcs.length}
            />

            {/* Connection Mode Indicator */}
            {connectingFrom && (
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
                    Click another node to create connection
                    <button onClick={() => setConnectingFrom(null)} className="ml-2">
                        <XCircle size={16} className="inline" />
                    </button>
                </div>
            )}
        </div>
    );
};

export default FlowEditor;
