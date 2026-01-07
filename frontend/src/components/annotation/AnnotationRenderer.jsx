/**
 * AnnotationRenderer.jsx - Phase 8
 * 
 * HTML overlay renderer for annotations.
 * 
 * Features:
 * - Render annotations as HTML elements
 * - Leader line drawing (SVG)
 * - Selection and hover states
 * - Drag to reposition
 * - Style application
 */

import React, { useState, useCallback, useMemo } from 'react';
import { X, GripVertical, Edit2 } from 'lucide-react';

// Single annotation component
const AnnotationItem = ({
    annotation,
    isSelected,
    isHovered,
    worldToScreen,
    onSelect,
    onHover,
    onMove,
    onEdit,
    onDelete
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

    // Get screen position
    const screenPos = worldToScreen
        ? worldToScreen(annotation.x, annotation.y, annotation.z)
        : { x: annotation.x, y: annotation.y };

    // Parse style from annotation or use defaults
    const style = annotation.style || {};
    const fontSize = style.fontSize || annotation.height * 5 || 12;
    const fontColor = annotation.color || style.fontColor || '#ffffff';
    const backgroundColor = style.backgroundColor;
    const backgroundOpacity = style.backgroundOpacity || 0.8;

    // Handle drag start
    const handleMouseDown = (e) => {
        if (e.button !== 0) return;
        e.stopPropagation();

        setIsDragging(true);
        setDragOffset({
            x: e.clientX - screenPos.x,
            y: e.clientY - screenPos.y
        });

        onSelect?.(annotation.annotation_id);
    };

    // Handle drag
    const handleMouseMove = useCallback((e) => {
        if (!isDragging) return;

        // Would need screenToWorld transform here
        // For now, just store screen coordinates
    }, [isDragging]);

    // Handle drag end
    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
    }, []);

    return (
        <div
            className={`annotation-item ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
            style={{
                left: screenPos.x,
                top: screenPos.y,
                transform: `translate(-50%, -50%) rotate(${annotation.rotation || 0}deg)`,
                fontSize: `${fontSize}px`,
                color: fontColor,
                backgroundColor: backgroundColor
                    ? `rgba(${parseInt(backgroundColor.slice(1, 3), 16)}, ${parseInt(backgroundColor.slice(3, 5), 16)}, ${parseInt(backgroundColor.slice(5, 7), 16)}, ${backgroundOpacity})`
                    : 'transparent',
                fontFamily: style.fontFamily || 'Arial'
            }}
            onMouseDown={handleMouseDown}
            onMouseEnter={() => onHover?.(annotation.annotation_id)}
            onMouseLeave={() => onHover?.(null)}
        >
            {/* Drag Handle */}
            {isSelected && (
                <div className="annotation-controls">
                    <button className="control-btn drag" title="Drag to move">
                        <GripVertical size={12} />
                    </button>
                    <button
                        className="control-btn edit"
                        onClick={(e) => { e.stopPropagation(); onEdit?.(annotation); }}
                        title="Edit"
                    >
                        <Edit2 size={12} />
                    </button>
                    <button
                        className="control-btn delete"
                        onClick={(e) => { e.stopPropagation(); onDelete?.(annotation.annotation_id); }}
                        title="Delete"
                    >
                        <X size={12} />
                    </button>
                </div>
            )}

            {/* Text Content */}
            <div className="annotation-text">
                {annotation.text.split('\n').map((line, i) => (
                    <div key={i}>{line}</div>
                ))}
            </div>

            <style jsx>{`
        .annotation-item {
          position: absolute;
          padding: 4px 8px;
          border-radius: 4px;
          white-space: nowrap;
          cursor: pointer;
          user-select: none;
          transition: box-shadow 0.15s ease;
          z-index: 10;
        }
        
        .annotation-item:hover {
          z-index: 20;
        }
        
        .annotation-item.selected {
          box-shadow: 0 0 0 2px #60a5fa, 0 4px 12px rgba(0,0,0,0.3);
          z-index: 30;
        }
        
        .annotation-item.hovered {
          box-shadow: 0 0 0 1px rgba(255,255,255,0.3);
        }
        
        .annotation-controls {
          position: absolute;
          top: -28px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          gap: 2px;
          background: rgba(30, 30, 46, 0.95);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 4px;
          padding: 2px;
        }
        
        .control-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 20px;
          height: 20px;
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          border-radius: 2px;
        }
        
        .control-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .control-btn.drag { cursor: grab; }
        .control-btn.drag:active { cursor: grabbing; }
        .control-btn.delete:hover { color: #f87171; }
        
        .annotation-text {
          line-height: 1.3;
        }
      `}</style>
        </div>
    );
};

// Leader line component (SVG)
const LeaderLines = ({ annotations, worldToScreen, leaderTargets }) => {
    const lines = useMemo(() => {
        return annotations
            .filter(a => a.style?.leaderStyle && a.style.leaderStyle !== 'none')
            .map(a => {
                const target = leaderTargets?.[a.annotation_id];
                if (!target) return null;

                const from = worldToScreen
                    ? worldToScreen(a.x, a.y, a.z)
                    : { x: a.x, y: a.y };
                const to = worldToScreen
                    ? worldToScreen(target.x, target.y, target.z)
                    : target;

                return {
                    id: a.annotation_id,
                    from,
                    to,
                    style: a.style?.leaderStyle || 'straight',
                    color: a.style?.leaderColor || '#666666',
                    width: a.style?.leaderWidth || 1
                };
            })
            .filter(Boolean);
    }, [annotations, worldToScreen, leaderTargets]);

    if (!lines.length) return null;

    return (
        <svg className="leader-lines" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
            {lines.map(line => {
                let pathD;

                switch (line.style) {
                    case 'bent':
                        // L-shaped line
                        const midY = (line.from.y + line.to.y) / 2;
                        pathD = `M ${line.from.x} ${line.from.y} L ${line.from.x} ${midY} L ${line.to.x} ${midY} L ${line.to.x} ${line.to.y}`;
                        break;
                    case 'curved':
                        // Bezier curve
                        const cx1 = line.from.x;
                        const cy1 = (line.from.y + line.to.y) / 2;
                        const cx2 = line.to.x;
                        const cy2 = cy1;
                        pathD = `M ${line.from.x} ${line.from.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${line.to.x} ${line.to.y}`;
                        break;
                    default:
                        // Straight line
                        pathD = `M ${line.from.x} ${line.from.y} L ${line.to.x} ${line.to.y}`;
                }

                return (
                    <g key={line.id}>
                        <path
                            d={pathD}
                            fill="none"
                            stroke={line.color}
                            strokeWidth={line.width}
                            strokeLinecap="round"
                        />
                        {/* Arrow at end */}
                        <circle
                            cx={line.to.x}
                            cy={line.to.y}
                            r={3}
                            fill={line.color}
                        />
                    </g>
                );
            })}
        </svg>
    );
};

// Main renderer component
const AnnotationRenderer = ({
    annotations = [],
    selectedId = null,
    hoveredId = null,
    leaderTargets = {},
    worldToScreen,
    onSelect,
    onHover,
    onMove,
    onEdit,
    onDelete,
    className = ''
}) => {
    // Group annotations by layer for z-ordering
    const layerGroups = useMemo(() => {
        const groups = {};
        annotations.forEach(a => {
            const layer = a.layer || 'DEFAULT';
            if (!groups[layer]) groups[layer] = [];
            groups[layer].push(a);
        });
        return groups;
    }, [annotations]);

    return (
        <div className={`annotation-renderer ${className}`}>
            {/* Leader Lines (rendered behind annotations) */}
            <LeaderLines
                annotations={annotations}
                worldToScreen={worldToScreen}
                leaderTargets={leaderTargets}
            />

            {/* Annotations by layer */}
            {Object.entries(layerGroups).map(([layer, layerAnnotations]) => (
                <div key={layer} className="annotation-layer" data-layer={layer}>
                    {layerAnnotations.map(annotation => (
                        <AnnotationItem
                            key={annotation.annotation_id}
                            annotation={annotation}
                            isSelected={selectedId === annotation.annotation_id}
                            isHovered={hoveredId === annotation.annotation_id}
                            worldToScreen={worldToScreen}
                            onSelect={onSelect}
                            onHover={onHover}
                            onMove={onMove}
                            onEdit={onEdit}
                            onDelete={onDelete}
                        />
                    ))}
                </div>
            ))}

            <style jsx>{`
        .annotation-renderer {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          overflow: hidden;
        }
        
        .annotation-layer {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        
        .annotation-layer :global(.annotation-item) {
          pointer-events: auto;
        }
      `}</style>
        </div>
    );
};

export default AnnotationRenderer;
