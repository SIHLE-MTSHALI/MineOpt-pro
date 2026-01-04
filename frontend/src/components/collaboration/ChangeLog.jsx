/**
 * ChangeLog.jsx - Real-time change log panel
 * 
 * Displays recent edits with:
 * - Timestamp and user
 * - Entity type and action
 * - Click to navigate to changed entity
 */

import React, { useState } from 'react';
import {
    History, User, Clock, Plus, Edit2, Trash2,
    Filter, ChevronDown, ArrowUpRight
} from 'lucide-react';

const ACTION_ICONS = {
    create: Plus,
    update: Edit2,
    delete: Trash2
};

const ACTION_COLORS = {
    create: 'text-green-400 bg-green-400/10',
    update: 'text-blue-400 bg-blue-400/10',
    delete: 'text-red-400 bg-red-400/10'
};

const ENTITY_LABELS = {
    task: 'Task',
    flow: 'Flow',
    stockpile: 'Stockpile',
    resource: 'Resource',
    schedule: 'Schedule'
};

/**
 * Individual change entry
 */
const ChangeEntry = ({ change, onNavigate }) => {
    const ActionIcon = ACTION_ICONS[change.action] || Edit2;
    const actionColor = ACTION_COLORS[change.action] || ACTION_COLORS.update;

    const timeAgo = getTimeAgo(new Date(change.timestamp));

    return (
        <div
            className="p-3 border-b border-slate-800 hover:bg-slate-800/50 transition-colors cursor-pointer group"
            onClick={() => onNavigate?.(change.entity_type, change.entity_id)}
        >
            <div className="flex items-start gap-3">
                {/* Action Icon */}
                <div className={`p-1.5 rounded ${actionColor}`}>
                    <ActionIcon size={14} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 truncate">
                        {change.summary}
                    </p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                        <User size={10} />
                        <span>{change.username}</span>
                        <span>•</span>
                        <Clock size={10} />
                        <span>{timeAgo}</span>
                    </div>
                </div>

                {/* Navigate arrow */}
                <ArrowUpRight
                    size={14}
                    className="text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity"
                />
            </div>
        </div>
    );
};

/**
 * Time ago formatter
 */
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

/**
 * Main Change Log Panel
 */
const ChangeLog = ({
    changes = [],
    onNavigate,
    className = ''
}) => {
    const [filterType, setFilterType] = useState('all');
    const [showFilters, setShowFilters] = useState(false);

    // Filter changes
    const filteredChanges = filterType === 'all'
        ? changes
        : changes.filter(c => c.entity_type === filterType);

    // Get unique entity types for filter
    const entityTypes = [...new Set(changes.map(c => c.entity_type))];

    return (
        <div className={`bg-slate-900 rounded-lg border border-slate-800 ${className}`}>
            {/* Header */}
            <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium text-white">
                    <History size={16} className="text-slate-400" />
                    Recent Changes
                    {changes.length > 0 && (
                        <span className="px-1.5 py-0.5 bg-slate-800 rounded text-xs text-slate-400">
                            {changes.length}
                        </span>
                    )}
                </div>

                {/* Filter dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-white rounded hover:bg-slate-800"
                    >
                        <Filter size={12} />
                        {filterType === 'all' ? 'All' : ENTITY_LABELS[filterType] || filterType}
                        <ChevronDown size={12} />
                    </button>

                    {showFilters && (
                        <div className="absolute right-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded shadow-lg z-10 min-w-[120px]">
                            <button
                                onClick={() => { setFilterType('all'); setShowFilters(false); }}
                                className={`w-full px-3 py-2 text-left text-xs hover:bg-slate-700 ${filterType === 'all' ? 'text-blue-400' : 'text-slate-300'}`}
                            >
                                All Types
                            </button>
                            {entityTypes.map(type => (
                                <button
                                    key={type}
                                    onClick={() => { setFilterType(type); setShowFilters(false); }}
                                    className={`w-full px-3 py-2 text-left text-xs hover:bg-slate-700 ${filterType === type ? 'text-blue-400' : 'text-slate-300'}`}
                                >
                                    {ENTITY_LABELS[type] || type}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Changes list */}
            <div className="max-h-80 overflow-y-auto">
                {filteredChanges.length === 0 ? (
                    <div className="p-6 text-center text-slate-500 text-sm">
                        No recent changes
                    </div>
                ) : (
                    filteredChanges.map((change, idx) => (
                        <ChangeEntry
                            key={`${change.timestamp}-${idx}`}
                            change={change}
                            onNavigate={onNavigate}
                        />
                    ))
                )}
            </div>
        </div>
    );
};

export default ChangeLog;
