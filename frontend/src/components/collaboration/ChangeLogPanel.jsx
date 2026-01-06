/**
 * ChangeLogPanel Component - Phase 5 Collaboration
 * 
 * Real-time feed showing recent changes to site data.
 * Integrates with WebSocket for live updates.
 * 
 * Features:
 * - Chronological change history
 * - User attribution
 * - Entity type filtering
 * - Click to view changed item
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
    Clock,
    User,
    Edit,
    Plus,
    Trash2,
    Filter,
    RefreshCw,
    ChevronDown,
    MapPin,
    Grid3X3,
    Calendar,
    Layers
} from 'lucide-react';

// Entity type icons
const ENTITY_ICONS = {
    activity_area: MapPin,
    block_model: Grid3X3,
    schedule: Calendar,
    borehole: Layers,
    default: Edit
};

// Action type styles
const ACTION_STYLES = {
    created: { color: '#10B981', bgColor: '#ECFDF5', label: 'Created' },
    updated: { color: '#3B82F6', bgColor: '#EFF6FF', label: 'Updated' },
    deleted: { color: '#EF4444', bgColor: '#FEE2E2', label: 'Deleted' }
};

const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    return date.toLocaleDateString();
};

const ChangeLogEntry = ({ change, onItemClick }) => {
    const [expanded, setExpanded] = useState(false);

    const Icon = ENTITY_ICONS[change.entity_type] || ENTITY_ICONS.default;
    const actionStyle = ACTION_STYLES[change.action] || ACTION_STYLES.updated;

    return (
        <div
            style={{
                padding: '12px 16px',
                borderBottom: '1px solid #F3F4F6',
                cursor: 'pointer',
                transition: 'background-color 0.15s'
            }}
            onClick={() => setExpanded(!expanded)}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                {/* Icon */}
                <div style={{
                    padding: '8px',
                    borderRadius: '8px',
                    backgroundColor: actionStyle.bgColor
                }}>
                    <Icon size={16} color={actionStyle.color} />
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    {/* Header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{
                            fontSize: '11px',
                            fontWeight: 500,
                            color: actionStyle.color,
                            backgroundColor: actionStyle.bgColor,
                            padding: '2px 6px',
                            borderRadius: '4px'
                        }}>
                            {actionStyle.label}
                        </span>
                        <span style={{ fontSize: '13px', fontWeight: 500, color: '#1F2937' }}>
                            {change.entity_name || change.entity_id.slice(0, 8)}
                        </span>
                    </div>

                    {/* Description */}
                    <div style={{ fontSize: '12px', color: '#6B7280', marginBottom: '4px' }}>
                        {change.description || `${change.entity_type} ${change.action}`}
                    </div>

                    {/* Meta */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        fontSize: '11px',
                        color: '#9CA3AF'
                    }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <User size={12} />
                            {change.user_name || 'System'}
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={12} />
                            {formatTimeAgo(change.timestamp)}
                        </span>
                    </div>

                    {/* Expanded details */}
                    {expanded && change.changes && (
                        <div style={{
                            marginTop: '8px',
                            padding: '8px',
                            backgroundColor: '#F3F4F6',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontFamily: 'monospace'
                        }}>
                            {Object.entries(change.changes).map(([key, value]) => (
                                <div key={key} style={{ marginBottom: '2px' }}>
                                    <span style={{ color: '#6B7280' }}>{key}:</span>{' '}
                                    <span style={{ color: '#1F2937' }}>{JSON.stringify(value)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Expand indicator */}
                {change.changes && (
                    <ChevronDown
                        size={14}
                        color="#9CA3AF"
                        style={{
                            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s'
                        }}
                    />
                )}
            </div>
        </div>
    );
};

const ChangeLogPanel = ({
    siteId,
    changes = [],
    onRefresh,
    onItemClick,
    isLoading = false,
    maxHeight = 400,
    style = {}
}) => {
    const [filter, setFilter] = useState('all');
    const [showFilters, setShowFilters] = useState(false);
    const listRef = useRef(null);

    // Available entity types from changes
    const entityTypes = useMemo(() => {
        const types = new Set(changes.map(c => c.entity_type));
        return ['all', ...Array.from(types)];
    }, [changes]);

    // Filtered changes
    const filteredChanges = useMemo(() => {
        if (filter === 'all') return changes;
        return changes.filter(c => c.entity_type === filter);
    }, [changes, filter]);

    return (
        <div
            style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                overflow: 'hidden',
                ...style
            }}
        >
            {/* Header */}
            <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid #E5E7EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={18} color="#3B82F6" />
                    <span style={{ fontWeight: 600, fontSize: '14px', color: '#1F2937' }}>
                        Change Log
                    </span>
                    <span style={{
                        fontSize: '11px',
                        backgroundColor: '#F3F4F6',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        color: '#6B7280'
                    }}>
                        {filteredChanges.length}
                    </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {/* Filter button */}
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '4px 8px',
                            backgroundColor: showFilters ? '#EFF6FF' : 'transparent',
                            border: '1px solid #E5E7EB',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            color: '#6B7280'
                        }}
                    >
                        <Filter size={14} />
                    </button>

                    {/* Refresh button */}
                    <button
                        onClick={onRefresh}
                        disabled={isLoading}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '4px 8px',
                            backgroundColor: 'transparent',
                            border: '1px solid #E5E7EB',
                            borderRadius: '6px',
                            cursor: isLoading ? 'not-allowed' : 'pointer'
                        }}
                    >
                        <RefreshCw
                            size={14}
                            color="#6B7280"
                            style={{
                                animation: isLoading ? 'spin 1s linear infinite' : 'none'
                            }}
                        />
                    </button>
                </div>
            </div>

            {/* Filter bar */}
            {showFilters && (
                <div style={{
                    padding: '8px 16px',
                    borderBottom: '1px solid #F3F4F6',
                    display: 'flex',
                    gap: '6px',
                    flexWrap: 'wrap'
                }}>
                    {entityTypes.map(type => (
                        <button
                            key={type}
                            onClick={() => setFilter(type)}
                            style={{
                                padding: '4px 10px',
                                borderRadius: '14px',
                                border: filter === type ? '1px solid #3B82F6' : '1px solid #E5E7EB',
                                backgroundColor: filter === type ? '#EFF6FF' : '#FFFFFF',
                                color: filter === type ? '#1D4ED8' : '#6B7280',
                                fontSize: '11px',
                                cursor: 'pointer',
                                textTransform: 'capitalize'
                            }}
                        >
                            {type.replace('_', ' ')}
                        </button>
                    ))}
                </div>
            )}

            {/* Change list */}
            <div
                ref={listRef}
                style={{
                    maxHeight,
                    overflowY: 'auto'
                }}
            >
                {filteredChanges.length === 0 ? (
                    <div style={{
                        padding: '40px 20px',
                        textAlign: 'center',
                        color: '#9CA3AF'
                    }}>
                        <Clock size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
                        <div style={{ fontSize: '13px' }}>No changes yet</div>
                    </div>
                ) : (
                    filteredChanges.map((change, idx) => (
                        <ChangeLogEntry
                            key={change.id || idx}
                            change={change}
                            onItemClick={onItemClick}
                        />
                    ))
                )}
            </div>

            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

export default ChangeLogPanel;
