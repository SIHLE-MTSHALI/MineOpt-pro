/**
 * MaterialFlowSankey.jsx
 * 
 * Sankey diagram visualization for material flow between locations.
 */

import React, { useState, useMemo } from 'react';
import {
    Boxes,
    RefreshCw,
    Calendar,
    Filter
} from 'lucide-react';

const MaterialFlowSankey = ({
    flowData,
    onRefresh,
    onDateRangeChange,
    dateRange,
    isLoading = false,
    className = ''
}) => {
    const [selectedNode, setSelectedNode] = useState(null);
    const [filterMaterial, setFilterMaterial] = useState('all');

    // Process flow data for visualization
    const processedData = useMemo(() => {
        if (!flowData?.links) return { nodes: [], links: [], maxTonnes: 0 };

        const nodesMap = new Map();
        let maxTonnes = 0;

        // Collect unique nodes and calculate positions
        flowData.nodes?.forEach((node, i) => {
            nodesMap.set(node, {
                name: node,
                x: node.includes('Pit') || node.includes('Block') ? 0 :
                    node.includes('Stock') ? 1 : 2,
                inflow: 0,
                outflow: 0
            });
        });

        // Calculate flows
        flowData.links?.forEach(link => {
            if (filterMaterial !== 'all' && link.material !== filterMaterial) return;

            const source = nodesMap.get(link.source);
            const target = nodesMap.get(link.target);

            if (source) source.outflow += link.tonnes;
            if (target) target.inflow += link.tonnes;

            if (link.tonnes > maxTonnes) maxTonnes = link.tonnes;
        });

        return {
            nodes: Array.from(nodesMap.values()),
            links: flowData.links?.filter(l =>
                filterMaterial === 'all' || l.material === filterMaterial
            ) || [],
            maxTonnes
        };
    }, [flowData, filterMaterial]);

    // Get material types
    const materialTypes = useMemo(() => {
        if (!flowData?.links) return [];
        const types = new Set(flowData.links.map(l => l.material));
        return Array.from(types);
    }, [flowData]);

    // Calculate node positions for SVG
    const getNodePositions = () => {
        const columns = [[], [], []];
        processedData.nodes.forEach(node => {
            columns[node.x].push(node);
        });

        const positions = new Map();
        columns.forEach((col, x) => {
            col.forEach((node, i) => {
                positions.set(node.name, {
                    x: 100 + x * 200,
                    y: 60 + i * 80,
                    flow: Math.max(node.inflow, node.outflow)
                });
            });
        });

        return positions;
    };

    const nodePositions = getNodePositions();

    // Get link color based on material
    const getLinkColor = (material) => {
        const colors = {
            'ore_high_grade': 'rgba(34, 197, 94, 0.5)',
            'ore_low_grade': 'rgba(132, 204, 22, 0.5)',
            'marginal': 'rgba(234, 179, 8, 0.5)',
            'waste': 'rgba(107, 114, 128, 0.5)',
            'overburden': 'rgba(75, 85, 99, 0.5)'
        };
        return colors[material] || 'rgba(100, 100, 100, 0.5)';
    };

    return (
        <div className={`material-flow-sankey ${className}`}>
            {/* Header */}
            <div className="sankey-header">
                <div className="header-left">
                    <Boxes size={20} />
                    <h3>Material Flow</h3>
                </div>
                <div className="header-right">
                    <select
                        value={filterMaterial}
                        onChange={(e) => setFilterMaterial(e.target.value)}
                    >
                        <option value="all">All Materials</option>
                        {materialTypes.map(type => (
                            <option key={type} value={type}>
                                {type.replace('_', ' ').toUpperCase()}
                            </option>
                        ))}
                    </select>
                    <button
                        className="refresh-btn"
                        onClick={onRefresh}
                        disabled={isLoading}
                    >
                        <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="flow-summary">
                <div className="summary-item">
                    <span className="label">Total Links</span>
                    <span className="value">{processedData.links.length}</span>
                </div>
                <div className="summary-item">
                    <span className="label">Total Tonnes</span>
                    <span className="value">
                        {processedData.links.reduce((sum, l) => sum + l.tonnes, 0).toLocaleString()}
                    </span>
                </div>
                <div className="summary-item">
                    <span className="label">Total Loads</span>
                    <span className="value">
                        {processedData.links.reduce((sum, l) => sum + l.loads, 0).toLocaleString()}
                    </span>
                </div>
            </div>

            {/* Sankey Diagram */}
            <div className="sankey-canvas">
                <svg width="600" height="400" viewBox="0 0 600 400">
                    {/* Column labels */}
                    <text x="100" y="30" textAnchor="middle" fill="#888" fontSize="12">Source</text>
                    <text x="300" y="30" textAnchor="middle" fill="#888" fontSize="12">Stockpile</text>
                    <text x="500" y="30" textAnchor="middle" fill="#888" fontSize="12">Destination</text>

                    {/* Links */}
                    {processedData.links.map((link, i) => {
                        const source = nodePositions.get(link.source);
                        const target = nodePositions.get(link.target);
                        if (!source || !target) return null;

                        const thickness = Math.max(4, (link.tonnes / processedData.maxTonnes) * 30);

                        return (
                            <g key={i} className="link-group">
                                <path
                                    d={`M ${source.x + 60} ${source.y}
                      C ${source.x + 100} ${source.y},
                        ${target.x - 100} ${target.y},
                        ${target.x - 60} ${target.y}`}
                                    fill="none"
                                    stroke={getLinkColor(link.material)}
                                    strokeWidth={thickness}
                                    opacity={selectedNode ? (selectedNode === link.source || selectedNode === link.target ? 1 : 0.2) : 0.7}
                                />
                                {/* Tooltip on hover */}
                                <title>{`${link.source} → ${link.target}: ${link.tonnes.toLocaleString()} t (${link.loads} loads)`}</title>
                            </g>
                        );
                    })}

                    {/* Nodes */}
                    {processedData.nodes.map((node, i) => {
                        const pos = nodePositions.get(node.name);
                        if (!pos) return null;

                        const height = Math.max(30, Math.min(60, (pos.flow / processedData.maxTonnes) * 60));

                        return (
                            <g
                                key={node.name}
                                className="node-group"
                                onClick={() => setSelectedNode(selectedNode === node.name ? null : node.name)}
                                style={{ cursor: 'pointer' }}
                            >
                                <rect
                                    x={pos.x - 50}
                                    y={pos.y - height / 2}
                                    width={100}
                                    height={height}
                                    rx={4}
                                    fill={selectedNode === node.name ? '#3b82f6' : '#374151'}
                                    stroke={selectedNode === node.name ? '#60a5fa' : '#4b5563'}
                                    strokeWidth={2}
                                />
                                <text
                                    x={pos.x}
                                    y={pos.y + 4}
                                    textAnchor="middle"
                                    fill="#fff"
                                    fontSize="11"
                                    fontWeight="500"
                                >
                                    {node.name.length > 12 ? node.name.slice(0, 12) + '...' : node.name}
                                </text>
                            </g>
                        );
                    })}
                </svg>
            </div>

            {/* Legend */}
            <div className="sankey-legend">
                <span className="legend-title">Material Type:</span>
                {materialTypes.map(type => (
                    <div key={type} className="legend-item">
                        <span
                            className="legend-color"
                            style={{ backgroundColor: getLinkColor(type).replace('0.5', '1') }}
                        />
                        <span>{type.replace('_', ' ')}</span>
                    </div>
                ))}
            </div>

            <style jsx>{`
        .material-flow-sankey {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .sankey-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #fff;
        }
        
        .header-left h3 { margin: 0; font-size: 16px; }
        
        .header-right {
          display: flex;
          gap: 8px;
        }
        
        .header-right select {
          padding: 6px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
        }
        
        .refresh-btn {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #888;
          cursor: pointer;
        }
        
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        .flow-summary {
          display: flex;
          gap: 24px;
          padding: 12px 16px;
          background: rgba(255,255,255,0.02);
        }
        
        .summary-item .label {
          font-size: 10px;
          color: #888;
          text-transform: uppercase;
          display: block;
        }
        
        .summary-item .value {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }
        
        .sankey-canvas {
          padding: 16px;
        }
        
        .sankey-canvas svg {
          display: block;
          margin: 0 auto;
        }
        
        .sankey-legend {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px 16px;
          background: rgba(0,0,0,0.2);
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .legend-title {
          font-size: 11px;
          color: #888;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #aaa;
          text-transform: capitalize;
        }
        
        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }
      `}</style>
        </div>
    );
};

export default MaterialFlowSankey;
