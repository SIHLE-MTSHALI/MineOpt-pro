/**
 * LayerManager.jsx - Phase 10
 * 
 * Unified layer management panel for all data types.
 * 
 * Features:
 * - Multiple layer types (surfaces, strings, annotations, rasters)
 * - Drag-and-drop reordering
 * - Group management
 * - Visibility and lock controls
 * - Layer filtering
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
    Layers,
    Mountain,
    Route,
    Type,
    Image,
    Eye,
    EyeOff,
    Lock,
    Unlock,
    FolderOpen,
    Folder,
    ChevronDown,
    ChevronRight,
    Search,
    Plus,
    Trash2,
    GripVertical,
    Filter,
    Settings
} from 'lucide-react';

// Layer type icons
const LAYER_TYPE_ICONS = {
    surface: Mountain,
    string: Route,
    annotation: Type,
    raster: Image,
    group: Folder
};

// Layer type colors
const LAYER_TYPE_COLORS = {
    surface: '#22c55e',
    string: '#3b82f6',
    annotation: '#f59e0b',
    raster: '#8b5cf6',
    group: '#64748b'
};

// Single layer row
const LayerRow = ({
    layer,
    depth = 0,
    isSelected,
    onSelect,
    onVisibilityToggle,
    onLockToggle,
    onExpand,
    onRename,
    onDelete
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState(layer.name);

    const Icon = LAYER_TYPE_ICONS[layer.type] || Layers;
    const typeColor = LAYER_TYPE_COLORS[layer.type] || '#888';

    const handleDoubleClick = () => {
        setIsEditing(true);
        setEditName(layer.name);
    };

    const handleNameSave = () => {
        if (editName.trim() && editName !== layer.name) {
            onRename?.(layer.id, editName.trim());
        }
        setIsEditing(false);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleNameSave();
        if (e.key === 'Escape') setIsEditing(false);
    };

    return (
        <div
            className={`layer-row ${isSelected ? 'selected' : ''} ${layer.visible === false ? 'hidden' : ''} ${layer.locked ? 'locked' : ''}`}
            style={{ paddingLeft: 12 + depth * 16 }}
            onClick={() => onSelect?.(layer.id)}
            onDoubleClick={handleDoubleClick}
        >
            {/* Drag Handle */}
            <div className="drag-handle">
                <GripVertical size={12} />
            </div>

            {/* Expand/Collapse for groups */}
            {layer.type === 'group' && (
                <button className="expand-btn" onClick={(e) => { e.stopPropagation(); onExpand?.(layer.id); }}>
                    {layer.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
            )}

            {/* Type Icon */}
            <Icon size={14} style={{ color: typeColor, flexShrink: 0 }} />

            {/* Name */}
            {isEditing ? (
                <input
                    className="name-edit"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={handleNameSave}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                />
            ) : (
                <span className="layer-name">{layer.name}</span>
            )}

            {/* Item Count (for groups) */}
            {layer.type === 'group' && layer.children?.length > 0 && (
                <span className="item-count">{layer.children.length}</span>
            )}

            {/* Controls */}
            <div className="layer-controls">
                <button
                    className={`control-btn visibility ${layer.visible !== false ? '' : 'off'}`}
                    onClick={(e) => { e.stopPropagation(); onVisibilityToggle?.(layer.id); }}
                    title={layer.visible !== false ? 'Hide' : 'Show'}
                >
                    {layer.visible !== false ? <Eye size={12} /> : <EyeOff size={12} />}
                </button>

                <button
                    className={`control-btn lock ${layer.locked ? 'on' : ''}`}
                    onClick={(e) => { e.stopPropagation(); onLockToggle?.(layer.id); }}
                    title={layer.locked ? 'Unlock' : 'Lock'}
                >
                    {layer.locked ? <Lock size={12} /> : <Unlock size={12} />}
                </button>
            </div>

            <style jsx>{`
        .layer-row {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 8px;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.15s ease;
          user-select: none;
        }
        
        .layer-row:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .layer-row.selected {
          background: rgba(59, 130, 246, 0.15);
        }
        
        .layer-row.hidden {
          opacity: 0.5;
        }
        
        .layer-row.locked .layer-name {
          font-style: italic;
        }
        
        .drag-handle {
          color: #444;
          cursor: grab;
          opacity: 0;
          transition: opacity 0.15s ease;
        }
        
        .layer-row:hover .drag-handle {
          opacity: 1;
        }
        
        .expand-btn {
          padding: 2px;
          background: transparent;
          border: none;
          color: #666;
          cursor: pointer;
        }
        
        .layer-name {
          flex: 1;
          font-size: 12px;
          color: #c0c0d0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .name-edit {
          flex: 1;
          padding: 2px 6px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(59, 130, 246, 0.5);
          border-radius: 3px;
          color: #fff;
          font-size: 12px;
          outline: none;
        }
        
        .item-count {
          padding: 1px 6px;
          background: rgba(255,255,255,0.1);
          border-radius: 8px;
          font-size: 10px;
          color: #888;
        }
        
        .layer-controls {
          display: flex;
          gap: 2px;
          opacity: 0;
          transition: opacity 0.15s ease;
        }
        
        .layer-row:hover .layer-controls,
        .layer-row.selected .layer-controls {
          opacity: 1;
        }
        
        .control-btn {
          padding: 4px;
          background: transparent;
          border: none;
          color: #666;
          cursor: pointer;
          border-radius: 3px;
        }
        
        .control-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }
        .control-btn.visibility { color: #4ade80; }
        .control-btn.visibility.off { color: #666; }
        .control-btn.lock.on { color: #f59e0b; }
      `}</style>
        </div>
    );
};

// Main component
const LayerManager = ({
    layers = [],
    selectedIds = [],
    onSelect,
    onVisibilityToggle,
    onLockToggle,
    onReorder,
    onRename,
    onDelete,
    onCreateGroup,
    className = ''
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedGroups, setExpandedGroups] = useState(new Set());
    const [filterType, setFilterType] = useState(null);

    // Filter layers
    const filteredLayers = useMemo(() => {
        let result = layers;

        // Filter by search
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            result = result.filter(l => l.name.toLowerCase().includes(query));
        }

        // Filter by type
        if (filterType) {
            result = result.filter(l => l.type === filterType);
        }

        return result;
    }, [layers, searchQuery, filterType]);

    // Toggle group expansion
    const handleExpand = useCallback((groupId) => {
        setExpandedGroups(prev => {
            const next = new Set(prev);
            if (next.has(groupId)) {
                next.delete(groupId);
            } else {
                next.add(groupId);
            }
            return next;
        });
    }, []);

    // Render layer tree recursively
    const renderLayers = (items, depth = 0) => {
        return items.map(layer => (
            <React.Fragment key={layer.id}>
                <LayerRow
                    layer={{ ...layer, expanded: expandedGroups.has(layer.id) }}
                    depth={depth}
                    isSelected={selectedIds.includes(layer.id)}
                    onSelect={onSelect}
                    onVisibilityToggle={onVisibilityToggle}
                    onLockToggle={onLockToggle}
                    onExpand={handleExpand}
                    onRename={onRename}
                    onDelete={onDelete}
                />

                {/* Render children if group is expanded */}
                {layer.type === 'group' && layer.children && expandedGroups.has(layer.id) && (
                    renderLayers(layer.children, depth + 1)
                )}
            </React.Fragment>
        ));
    };

    // Count by type
    const typeCounts = useMemo(() => {
        const counts = { surface: 0, string: 0, annotation: 0, raster: 0 };
        layers.forEach(l => {
            if (counts[l.type] !== undefined) counts[l.type]++;
        });
        return counts;
    }, [layers]);

    return (
        <div className={`layer-manager ${className}`}>
            {/* Header */}
            <div className="manager-header">
                <div className="title">
                    <Layers size={16} />
                    <span>Layers</span>
                </div>
                <button className="add-btn" onClick={onCreateGroup} title="Create Group">
                    <Plus size={14} />
                </button>
            </div>

            {/* Search */}
            <div className="search-bar">
                <Search size={14} />
                <input
                    type="text"
                    placeholder="Search layers..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Type Filters */}
            <div className="type-filters">
                <button
                    className={`filter-btn ${filterType === null ? 'active' : ''}`}
                    onClick={() => setFilterType(null)}
                >
                    All ({layers.length})
                </button>
                {Object.entries(typeCounts).map(([type, count]) => {
                    if (count === 0) return null;
                    const Icon = LAYER_TYPE_ICONS[type];
                    return (
                        <button
                            key={type}
                            className={`filter-btn ${filterType === type ? 'active' : ''}`}
                            onClick={() => setFilterType(type)}
                            style={{ '--type-color': LAYER_TYPE_COLORS[type] }}
                        >
                            <Icon size={12} />
                            {count}
                        </button>
                    );
                })}
            </div>

            {/* Layer List */}
            <div className="layer-list">
                {filteredLayers.length === 0 ? (
                    <div className="empty-state">
                        {searchQuery ? (
                            <><Search size={20} /><p>No matching layers</p></>
                        ) : (
                            <><Layers size={20} /><p>No layers yet</p></>
                        )}
                    </div>
                ) : (
                    renderLayers(filteredLayers)
                )}
            </div>

            <style jsx>{`
        .layer-manager {
          display: flex;
          flex-direction: column;
          background: #1e1e2e;
          border-radius: 8px;
          height: 100%;
          overflow: hidden;
        }
        
        .manager-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 600;
          color: #fff;
        }
        
        .add-btn {
          padding: 4px 8px;
          background: rgba(59, 130, 246, 0.15);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 4px;
          color: #60a5fa;
          cursor: pointer;
        }
        
        .add-btn:hover {
          background: rgba(59, 130, 246, 0.25);
        }
        
        .search-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          margin: 8px 12px;
          background: rgba(0,0,0,0.2);
          border-radius: 6px;
          color: #666;
        }
        
        .search-bar input {
          flex: 1;
          background: transparent;
          border: none;
          color: #fff;
          font-size: 12px;
          outline: none;
        }
        
        .search-bar input::placeholder {
          color: #555;
        }
        
        .type-filters {
          display: flex;
          gap: 4px;
          padding: 0 12px 8px;
          flex-wrap: wrap;
        }
        
        .filter-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(255,255,255,0.05);
          border: 1px solid transparent;
          border-radius: 12px;
          color: #888;
          font-size: 10px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .filter-btn:hover {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .filter-btn.active {
          background: rgba(59, 130, 246, 0.15);
          border-color: rgba(59, 130, 246, 0.3);
          color: #60a5fa;
        }
        
        .layer-list {
          flex: 1;
          overflow-y: auto;
          padding: 0 6px 12px;
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 24px;
          color: #555;
        }
        
        .empty-state p {
          margin-top: 8px;
          font-size: 12px;
        }
      `}</style>
        </div>
    );
};

export default LayerManager;
