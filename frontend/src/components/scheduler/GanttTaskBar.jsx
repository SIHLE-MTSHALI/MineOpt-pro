/**
 * GanttTaskBar.jsx - Enhanced Gantt Task Bar Component
 * 
 * Provides enhanced task visualization with:
 * - Rich task labels (activity + area + destination)
 * - Rate factor inline editing slider
 * - Maintenance/availability overlays
 * - Task status icons
 * - Quality risk indicators
 */

import React, { useState, useRef } from 'react';
import {
    AlertTriangle, CheckCircle, Clock, Pause, Play,
    Target, Truck, Settings, ChevronDown
} from 'lucide-react';

// Rate Factor Slider
const RateFactorSlider = ({ value, onChange, onClose }) => {
    const [localValue, setLocalValue] = useState(value);

    return (
        <div className="absolute z-50 top-full left-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl min-w-48">
            <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400">Rate Factor</span>
                <span className="text-xs font-medium text-white">{(localValue * 100).toFixed(0)}%</span>
            </div>
            <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.05"
                value={localValue}
                onChange={(e) => setLocalValue(parseFloat(e.target.value))}
                className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>50%</span>
                <span>100%</span>
                <span>150%</span>
            </div>
            <div className="flex space-x-2 mt-3">
                <button
                    onClick={onClose}
                    className="flex-1 px-2 py-1 bg-slate-700 rounded text-xs text-slate-300"
                >
                    Cancel
                </button>
                <button
                    onClick={() => { onChange(localValue); onClose(); }}
                    className="flex-1 px-2 py-1 bg-blue-600 rounded text-xs text-white"
                >
                    Apply
                </button>
            </div>
        </div>
    );
};

// Task Status Icon
const TaskStatusIcon = ({ status }) => {
    switch (status) {
        case 'complete':
            return <CheckCircle size={12} className="text-green-400" />;
        case 'in-progress':
            return <Play size={12} className="text-blue-400" />;
        case 'delayed':
            return <AlertTriangle size={12} className="text-yellow-400" />;
        case 'paused':
            return <Pause size={12} className="text-orange-400" />;
        default:
            return <Clock size={12} className="text-slate-400" />;
    }
};

// Main Enhanced Task Bar Component
const GanttTaskBar = ({
    task,
    width,
    left,
    height = 28,
    onSelect,
    onUpdateRateFactor,
    selected = false
}) => {
    const [showRateSlider, setShowRateSlider] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);
    const barRef = useRef(null);

    // Determine colors based on material/status
    const getBarColor = () => {
        if (task.materialType === 'Coal') {
            if (task.qualityRisk) return 'bg-gradient-to-r from-amber-600 to-amber-500';
            return 'bg-gradient-to-r from-blue-600 to-blue-500';
        }
        if (task.materialType === 'Waste') {
            return 'bg-gradient-to-r from-slate-600 to-slate-500';
        }
        return 'bg-gradient-to-r from-gray-600 to-gray-500';
    };

    // Quality risk indicator
    const hasQualityRisk = task.qualityRisk || (task.quality?.ash > 16);

    return (
        <div
            ref={barRef}
            className={`
                absolute rounded cursor-pointer transition-all
                ${getBarColor()}
                ${selected ? 'ring-2 ring-white ring-offset-1 ring-offset-slate-900' : ''}
                hover:brightness-110
            `}
            style={{
                left: `${left}%`,
                width: `${Math.max(width, 2)}%`,
                height: `${height}px`,
                minWidth: '20px'
            }}
            onClick={() => onSelect(task.id)}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            {/* Task content */}
            <div className="h-full px-2 flex items-center justify-between overflow-hidden">
                {/* Left: Status icon and label */}
                <div className="flex items-center space-x-1 min-w-0">
                    <TaskStatusIcon status={task.status} />
                    {width > 8 && (
                        <span className="text-xs text-white truncate">
                            {task.activityName}
                        </span>
                    )}
                </div>

                {/* Right: Quick actions */}
                {width > 10 && (
                    <div className="flex items-center space-x-1">
                        {hasQualityRisk && (
                            <AlertTriangle size={12} className="text-yellow-300" />
                        )}
                        <button
                            onClick={(e) => { e.stopPropagation(); setShowRateSlider(!showRateSlider); }}
                            className="p-0.5 hover:bg-white/20 rounded"
                        >
                            <Settings size={10} className="text-white/70" />
                        </button>
                    </div>
                )}
            </div>

            {/* Rate adjustment pattern overlay */}
            {task.rateFactor && task.rateFactor !== 1 && (
                <div
                    className="absolute inset-0 pointer-events-none opacity-20"
                    style={{
                        background: task.rateFactor < 1
                            ? 'repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(255,255,255,0.3) 3px, rgba(255,255,255,0.3) 6px)'
                            : 'repeating-linear-gradient(-45deg, transparent, transparent 3px, rgba(0,255,0,0.3) 3px, rgba(0,255,0,0.3) 6px)'
                    }}
                />
            )}

            {/* Rate Factor Slider */}
            {showRateSlider && (
                <RateFactorSlider
                    value={task.rateFactor || 1}
                    onChange={(val) => onUpdateRateFactor(task.id, val)}
                    onClose={() => setShowRateSlider(false)}
                />
            )}

            {/* Enhanced Tooltip */}
            {showTooltip && (
                <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl min-w-56">
                    <div className="space-y-2">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <span className="font-medium text-white text-sm">{task.activityName}</span>
                            <TaskStatusIcon status={task.status} />
                        </div>

                        {/* Details grid */}
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="bg-slate-800 rounded p-1.5">
                                <span className="text-slate-500">Area:</span>
                                <span className="text-slate-300 ml-1">{task.areaName || 'N/A'}</span>
                            </div>
                            <div className="bg-slate-800 rounded p-1.5">
                                <span className="text-slate-500">Dest:</span>
                                <span className="text-slate-300 ml-1">{task.destinationName || 'N/A'}</span>
                            </div>
                            <div className="bg-slate-800 rounded p-1.5">
                                <span className="text-slate-500">Tonnes:</span>
                                <span className="text-slate-300 ml-1">{task.tonnes?.toLocaleString() || 0}</span>
                            </div>
                            <div className="bg-slate-800 rounded p-1.5">
                                <span className="text-slate-500">Duration:</span>
                                <span className="text-slate-300 ml-1">{task.durationHours?.toFixed(1) || 0}h</span>
                            </div>
                        </div>

                        {/* Quality info */}
                        {task.quality && (
                            <div className="border-t border-slate-700 pt-2">
                                <div className="text-xs text-slate-500 mb-1">Quality</div>
                                <div className="flex space-x-2 text-xs">
                                    {task.quality.cv && (
                                        <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                                            CV: {task.quality.cv.toFixed(1)}
                                        </span>
                                    )}
                                    {task.quality.ash && (
                                        <span className={`px-1.5 py-0.5 rounded ${task.quality.ash > 16
                                                ? 'bg-red-500/20 text-red-400'
                                                : 'bg-green-500/20 text-green-400'
                                            }`}>
                                            Ash: {task.quality.ash.toFixed(1)}%
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Rate factor */}
                        {task.rateFactor && task.rateFactor !== 1 && (
                            <div className="text-xs">
                                <span className="text-slate-500">Rate Factor:</span>
                                <span className={`ml-1 ${task.rateFactor < 1 ? 'text-yellow-400' : 'text-green-400'}`}>
                                    {(task.rateFactor * 100).toFixed(0)}%
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Tooltip arrow */}
                    <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-900 border-r border-b border-slate-700 rotate-45" />
                </div>
            )}
        </div>
    );
};

// Maintenance Overlay Component
export const MaintenanceOverlay = ({ start, end, periodWidth }) => (
    <div
        className="absolute top-0 bottom-0 bg-red-500/10 border-l border-r border-red-500/30"
        style={{
            left: `${start}%`,
            width: `${end - start}%`
        }}
    >
        <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs text-red-400 bg-slate-900/80 px-2 py-0.5 rounded">
                Maintenance
            </span>
        </div>
    </div>
);

// Filter Controls Component
export const GanttFilters = ({ filters, onChange }) => {
    return (
        <div className="flex items-center space-x-4 px-4 py-2 bg-slate-900 border-b border-slate-800">
            <span className="text-xs text-slate-500">Filters:</span>

            <label className="flex items-center space-x-2 text-xs">
                <input
                    type="checkbox"
                    checked={filters.coalOnly}
                    onChange={(e) => onChange({ ...filters, coalOnly: e.target.checked })}
                    className="rounded bg-slate-700 border-slate-600"
                />
                <span className="text-slate-400">Coal Only</span>
            </label>

            <label className="flex items-center space-x-2 text-xs">
                <input
                    type="checkbox"
                    checked={filters.qualityRisk}
                    onChange={(e) => onChange({ ...filters, qualityRisk: e.target.checked })}
                    className="rounded bg-slate-700 border-slate-600"
                />
                <span className="text-slate-400">Quality Risk</span>
            </label>

            <label className="flex items-center space-x-2 text-xs">
                <input
                    type="checkbox"
                    checked={filters.delayed}
                    onChange={(e) => onChange({ ...filters, delayed: e.target.checked })}
                    className="rounded bg-slate-700 border-slate-600"
                />
                <span className="text-slate-400">Delayed</span>
            </label>

            <div className="flex items-center space-x-2 ml-auto">
                <select
                    value={filters.resource || 'all'}
                    onChange={(e) => onChange({ ...filters, resource: e.target.value })}
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
                >
                    <option value="all">All Resources</option>
                    <option value="ex-01">EX-01</option>
                    <option value="ex-02">EX-02</option>
                    <option value="truck-fleet">Truck Fleet</option>
                </select>
            </div>
        </div>
    );
};

export default GanttTaskBar;
