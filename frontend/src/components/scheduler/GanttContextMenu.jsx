/**
 * GanttContextMenu.jsx - Right-click context menu for Gantt tasks
 * 
 * Provides contextual actions for tasks:
 * - Edit Task Details
 * - Split Task across periods
 * - Change Resource
 * - View Decision Explanation
 * - Delete Task
 */

import React, { useState, useEffect, useRef } from 'react';
import {
    Edit3, Split, Users, HelpCircle, Trash2, X,
    ChevronRight, Copy, Scissors, Clock
} from 'lucide-react';

/**
 * Context Menu Component
 */
const GanttContextMenu = ({
    visible,
    x,
    y,
    task,
    resources = [],
    periods = [],
    onClose,
    onEditTask,
    onSplitTask,
    onChangeResource,
    onViewExplanation,
    onDeleteTask,
    onDuplicateTask
}) => {
    const menuRef = useRef(null);
    const [showResourceSubmenu, setShowResourceSubmenu] = useState(false);
    const [showSplitDialog, setShowSplitDialog] = useState(false);

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (menuRef.current && !menuRef.current.contains(e.target)) {
                onClose();
            }
        };
        if (visible) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [visible, onClose]);

    // Close on escape
    useEffect(() => {
        const handleEscape = (e) => {
            if (e.key === 'Escape') onClose();
        };
        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    if (!visible || !task) return null;

    // Adjust position to stay in viewport
    const adjustedX = Math.min(x, window.innerWidth - 220);
    const adjustedY = Math.min(y, window.innerHeight - 320);

    const menuItems = [
        {
            label: 'Edit Task',
            icon: Edit3,
            action: () => { onEditTask?.(task); onClose(); }
        },
        {
            label: 'Split Task',
            icon: Scissors,
            action: () => setShowSplitDialog(true),
            disabled: task.taskType === 'OptimiserDelay'
        },
        {
            label: 'Duplicate Task',
            icon: Copy,
            action: () => { onDuplicateTask?.(task); onClose(); },
            disabled: task.taskType === 'OptimiserDelay'
        },
        { divider: true },
        {
            label: 'Change Resource',
            icon: Users,
            submenu: true,
            action: () => setShowResourceSubmenu(!showResourceSubmenu),
            disabled: task.taskType === 'OptimiserDelay'
        },
        { divider: true },
        {
            label: 'View Decision Explanation',
            icon: HelpCircle,
            action: () => { onViewExplanation?.(task); onClose(); }
        },
        { divider: true },
        {
            label: 'Delete Task',
            icon: Trash2,
            action: () => { onDeleteTask?.(task.id); onClose(); },
            danger: true
        }
    ];

    return (
        <div
            ref={menuRef}
            className="fixed z-[100] bg-slate-900 border border-slate-700 rounded-lg shadow-2xl py-1 min-w-52"
            style={{ left: adjustedX, top: adjustedY }}
        >
            {/* Header */}
            <div className="px-3 py-2 border-b border-slate-700">
                <div className="text-sm font-medium text-white truncate">
                    {task.activityName || 'Task'}
                </div>
                <div className="text-xs text-slate-400 truncate">
                    {task.tonnes?.toLocaleString() || 0}t • {task.areaName || 'Unknown Area'}
                </div>
            </div>

            {/* Menu Items */}
            <div className="py-1">
                {menuItems.map((item, idx) => {
                    if (item.divider) {
                        return <div key={idx} className="border-t border-slate-700 my-1" />;
                    }

                    const Icon = item.icon;
                    return (
                        <button
                            key={idx}
                            onClick={item.action}
                            disabled={item.disabled}
                            className={`
                                w-full px-3 py-2 flex items-center justify-between text-sm
                                ${item.disabled
                                    ? 'text-slate-600 cursor-not-allowed'
                                    : item.danger
                                        ? 'text-red-400 hover:bg-red-500/10'
                                        : 'text-slate-300 hover:bg-slate-800'
                                }
                                transition-colors
                            `}
                        >
                            <span className="flex items-center">
                                <Icon size={14} className="mr-2" />
                                {item.label}
                            </span>
                            {item.submenu && <ChevronRight size={14} />}
                        </button>
                    );
                })}
            </div>

            {/* Resource Submenu */}
            {showResourceSubmenu && (
                <div className="absolute left-full top-24 ml-1 bg-slate-900 border border-slate-700 rounded-lg shadow-xl py-1 min-w-40">
                    <div className="px-3 py-1.5 text-xs text-slate-500 uppercase tracking-wider">
                        Select Resource
                    </div>
                    {resources.map(res => (
                        <button
                            key={res.resource_id}
                            onClick={() => {
                                onChangeResource?.(task.id, res.resource_id);
                                onClose();
                            }}
                            className={`
                                w-full px-3 py-2 text-left text-sm
                                ${res.resource_id === task.resourceId
                                    ? 'bg-blue-500/20 text-blue-400'
                                    : 'text-slate-300 hover:bg-slate-800'
                                }
                            `}
                        >
                            {res.name}
                            <span className="text-xs text-slate-500 ml-2">
                                ({res.resource_type})
                            </span>
                        </button>
                    ))}
                </div>
            )}

            {/* Split Task Dialog */}
            {showSplitDialog && (
                <SplitTaskDialog
                    task={task}
                    periods={periods}
                    onSplit={(splitConfig) => {
                        onSplitTask?.(task.id, splitConfig);
                        onClose();
                    }}
                    onCancel={() => setShowSplitDialog(false)}
                />
            )}
        </div>
    );
};

/**
 * Split Task Dialog Component
 */
const SplitTaskDialog = ({ task, periods, onSplit, onCancel }) => {
    const [splitPercent, setSplitPercent] = useState(50);
    const [targetPeriodId, setTargetPeriodId] = useState('');

    // Find available periods (after current)
    const currentPeriodIndex = periods.findIndex(p => p.period_id === task.periodId);
    const availablePeriods = periods.slice(currentPeriodIndex + 1, currentPeriodIndex + 5);

    useEffect(() => {
        if (availablePeriods.length > 0 && !targetPeriodId) {
            setTargetPeriodId(availablePeriods[0].period_id);
        }
    }, [availablePeriods, targetPeriodId]);

    const firstPartTonnes = Math.round(task.tonnes * (splitPercent / 100));
    const secondPartTonnes = task.tonnes - firstPartTonnes;

    return (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/50">
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-96 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Split Task</h3>
                    <button onClick={onCancel} className="text-slate-400 hover:text-white">
                        <X size={18} />
                    </button>
                </div>

                <div className="space-y-4">
                    {/* Original task info */}
                    <div className="p-3 bg-slate-800 rounded-lg">
                        <div className="text-sm text-slate-300">{task.activityName}</div>
                        <div className="text-xs text-slate-500">
                            Total: {task.tonnes.toLocaleString()} tonnes
                        </div>
                    </div>

                    {/* Split percentage */}
                    <div>
                        <label className="text-sm text-slate-400 block mb-2">
                            Split Ratio
                        </label>
                        <input
                            type="range"
                            min="10"
                            max="90"
                            step="5"
                            value={splitPercent}
                            onChange={(e) => setSplitPercent(parseInt(e.target.value))}
                            className="w-full"
                        />
                        <div className="flex justify-between text-xs text-slate-500 mt-1">
                            <span>Part 1: {firstPartTonnes.toLocaleString()}t ({splitPercent}%)</span>
                            <span>Part 2: {secondPartTonnes.toLocaleString()}t ({100 - splitPercent}%)</span>
                        </div>
                    </div>

                    {/* Target period for second part */}
                    <div>
                        <label className="text-sm text-slate-400 block mb-2">
                            Move Part 2 to Period
                        </label>
                        <select
                            value={targetPeriodId}
                            onChange={(e) => setTargetPeriodId(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300"
                        >
                            {availablePeriods.map(p => (
                                <option key={p.period_id} value={p.period_id}>
                                    {p.name || p.period_id}
                                </option>
                            ))}
                            {availablePeriods.length === 0 && (
                                <option value="">No available periods</option>
                            )}
                        </select>
                    </div>

                    {/* Preview */}
                    <div className="border border-slate-700 rounded-lg p-3">
                        <div className="text-xs text-slate-500 mb-2">Preview</div>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 h-8 bg-blue-600 rounded flex items-center justify-center text-xs text-white">
                                {firstPartTonnes.toLocaleString()}t
                            </div>
                            <Split size={16} className="text-slate-500" />
                            <div className="flex-1 h-8 bg-blue-500 rounded flex items-center justify-center text-xs text-white">
                                {secondPartTonnes.toLocaleString()}t
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 mt-6">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onSplit({
                            splitPercent,
                            targetPeriodId,
                            firstPartTonnes,
                            secondPartTonnes
                        })}
                        disabled={!targetPeriodId}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Split Task
                    </button>
                </div>
            </div>
        </div>
    );
};

export default GanttContextMenu;
