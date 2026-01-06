/**
 * GanttTaskEditor.jsx - Enhanced Task Manipulation for Gantt Chart
 * 
 * Provides:
 * - Split task across period boundary
 * - Merge adjacent tasks
 * - Quantity adjustment
 * - Notes/comments
 * - Precedence validation
 * - Breakdown/downtime indicators
 */

import React, { useState, useCallback } from 'react';
import {
    Scissors, Merge, FileText, AlertTriangle, Clock,
    ChevronDown, ChevronUp, X, Save, RotateCcw
} from 'lucide-react';

/**
 * Task split dialog
 */
export const TaskSplitDialog = ({ task, periods, onSplit, onClose }) => {
    const [splitPoint, setSplitPoint] = useState(50); // Percentage
    const [splitPeriod, setSplitPeriod] = useState(task?.period_id || '');

    const handleSplit = useCallback(() => {
        if (!task) return;

        const quantity = task.scheduled_quantity || 0;
        const part1Qty = Math.round(quantity * splitPoint / 100);
        const part2Qty = quantity - part1Qty;

        onSplit?.({
            originalTask: task,
            part1: {
                ...task,
                task_id: `${task.task_id}_a`,
                scheduled_quantity: part1Qty
            },
            part2: {
                ...task,
                task_id: `${task.task_id}_b`,
                scheduled_quantity: part2Qty,
                period_id: splitPeriod
            }
        });
    }, [task, splitPoint, splitPeriod, onSplit]);

    if (!task) return null;

    return (
        <div className="task-dialog-overlay">
            <div className="task-dialog">
                <div className="dialog-header">
                    <Scissors size={20} />
                    <h3>Split Task</h3>
                    <button onClick={onClose}><X size={18} /></button>
                </div>

                <div className="dialog-content">
                    <div className="task-info">
                        <span className="label">Task:</span>
                        <span>{task.activity_name || task.task_id}</span>
                    </div>
                    <div className="task-info">
                        <span className="label">Total Quantity:</span>
                        <span>{task.scheduled_quantity?.toLocaleString()} t</span>
                    </div>

                    <div className="split-slider">
                        <label>Split Point: {splitPoint}%</label>
                        <input
                            type="range"
                            min="10"
                            max="90"
                            value={splitPoint}
                            onChange={(e) => setSplitPoint(Number(e.target.value))}
                        />
                        <div className="split-preview">
                            <div className="part" style={{ flex: splitPoint }}>
                                Part 1: {Math.round(task.scheduled_quantity * splitPoint / 100)} t
                            </div>
                            <div className="part" style={{ flex: 100 - splitPoint }}>
                                Part 2: {Math.round(task.scheduled_quantity * (100 - splitPoint) / 100)} t
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Move Part 2 to Period:</label>
                        <select value={splitPeriod} onChange={(e) => setSplitPeriod(e.target.value)}>
                            {periods?.map(p => (
                                <option key={p.period_id} value={p.period_id}>{p.name || p.period_id}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="dialog-actions">
                    <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button className="btn-primary" onClick={handleSplit}>Split Task</button>
                </div>
            </div>
        </div>
    );
};

/**
 * Task merge dialog
 */
export const TaskMergeDialog = ({ tasks, onMerge, onClose }) => {
    if (!tasks || tasks.length < 2) return null;

    const handleMerge = useCallback(() => {
        const totalQty = tasks.reduce((sum, t) => sum + (t.scheduled_quantity || 0), 0);

        onMerge?.({
            mergedTask: {
                ...tasks[0],
                scheduled_quantity: totalQty,
                notes: `Merged from ${tasks.length} tasks`
            },
            removedTaskIds: tasks.slice(1).map(t => t.task_id)
        });
    }, [tasks, onMerge]);

    return (
        <div className="task-dialog-overlay">
            <div className="task-dialog">
                <div className="dialog-header">
                    <Merge size={20} />
                    <h3>Merge Tasks</h3>
                    <button onClick={onClose}><X size={18} /></button>
                </div>

                <div className="dialog-content">
                    <p>Merge {tasks.length} selected tasks:</p>
                    <ul className="task-list">
                        {tasks.map(t => (
                            <li key={t.task_id}>
                                {t.activity_name || t.task_id} - {t.scheduled_quantity?.toLocaleString()} t
                            </li>
                        ))}
                    </ul>
                    <div className="merge-result">
                        <strong>Result:</strong>{' '}
                        {tasks.reduce((sum, t) => sum + (t.scheduled_quantity || 0), 0).toLocaleString()} t
                    </div>
                </div>

                <div className="dialog-actions">
                    <button className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button className="btn-primary" onClick={handleMerge}>Merge Tasks</button>
                </div>
            </div>
        </div>
    );
};

/**
 * Task quantity editor
 */
export const QuantityEditor = ({ task, onUpdate, onCancel }) => {
    const [quantity, setQuantity] = useState(task?.scheduled_quantity || 0);
    const [notes, setNotes] = useState(task?.notes || '');

    const handleSave = useCallback(() => {
        onUpdate?.({
            ...task,
            scheduled_quantity: quantity,
            notes
        });
    }, [task, quantity, notes, onUpdate]);

    if (!task) return null;

    return (
        <div className="quantity-editor">
            <div className="form-row">
                <label>Quantity (tonnes):</label>
                <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    min="0"
                    step="100"
                />
            </div>
            <div className="form-row">
                <label>Notes:</label>
                <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add notes or comments..."
                    rows={3}
                />
            </div>
            <div className="editor-actions">
                <button className="btn-secondary" onClick={onCancel}>
                    <X size={14} /> Cancel
                </button>
                <button className="btn-primary" onClick={handleSave}>
                    <Save size={14} /> Save
                </button>
            </div>
        </div>
    );
};

/**
 * Precedence validation helper
 */
export const validatePrecedence = (task, newPosition, allTasks, constraints) => {
    const errors = [];

    // Check predecessors
    const predecessors = constraints?.filter(c => c.successor_id === task.task_id) || [];
    for (const pred of predecessors) {
        const predTask = allTasks.find(t => t.task_id === pred.predecessor_id);
        if (predTask && predTask.end_time > newPosition.start_time) {
            errors.push({
                type: 'precedence',
                message: `Cannot start before ${predTask.activity_name || predTask.task_id} finishes`,
                conflictTask: predTask
            });
        }
    }

    // Check successors
    const successors = constraints?.filter(c => c.predecessor_id === task.task_id) || [];
    for (const succ of successors) {
        const succTask = allTasks.find(t => t.task_id === succ.successor_id);
        if (succTask && newPosition.end_time > succTask.start_time) {
            errors.push({
                type: 'precedence',
                message: `Must finish before ${succTask.activity_name || succTask.task_id} starts`,
                conflictTask: succTask
            });
        }
    }

    return {
        valid: errors.length === 0,
        errors
    };
};

/**
 * Breakdown/Downtime indicator component
 */
export const DowntimeIndicator = ({ downtimes, periodStart, periodEnd, height = 40 }) => {
    if (!downtimes || downtimes.length === 0) return null;

    const periodDuration = periodEnd - periodStart;

    return (
        <div className="downtime-container" style={{ height }}>
            {downtimes.map((dt, i) => {
                const left = ((dt.start_time - periodStart) / periodDuration) * 100;
                const width = ((dt.end_time - dt.start_time) / periodDuration) * 100;

                return (
                    <div
                        key={i}
                        className={`downtime-block ${dt.type}`}
                        style={{ left: `${left}%`, width: `${width}%` }}
                        title={`${dt.type}: ${dt.reason}`}
                    >
                        <AlertTriangle size={12} />
                    </div>
                );
            })}
        </div>
    );
};

/**
 * Filter controls including destination filter
 */
export const GanttFilters = ({
    filters,
    onFilterChange,
    destinations = [],
    activityTypes = [],
    materialTypes = []
}) => {
    return (
        <div className="gantt-filters">
            <div className="filter-group">
                <label>Activity Type:</label>
                <select
                    value={filters.activityType || ''}
                    onChange={(e) => onFilterChange({ ...filters, activityType: e.target.value })}
                >
                    <option value="">All Types</option>
                    {activityTypes.map(t => (
                        <option key={t} value={t}>{t}</option>
                    ))}
                </select>
            </div>

            <div className="filter-group">
                <label>Material:</label>
                <select
                    value={filters.materialType || ''}
                    onChange={(e) => onFilterChange({ ...filters, materialType: e.target.value })}
                >
                    <option value="">All Materials</option>
                    {materialTypes.map(m => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>
            </div>

            <div className="filter-group">
                <label>Destination:</label>
                <select
                    value={filters.destination || ''}
                    onChange={(e) => onFilterChange({ ...filters, destination: e.target.value })}
                >
                    <option value="">All Destinations</option>
                    {destinations.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                </select>
            </div>

            <button
                className="btn-text"
                onClick={() => onFilterChange({})}
            >
                <RotateCcw size={14} /> Reset
            </button>
        </div>
    );
};

/**
 * Scroll to current period button
 */
export const ScrollToCurrentButton = ({ periods, currentPeriodId, scrollContainerRef }) => {
    const handleScrollToCurrent = useCallback(() => {
        if (!scrollContainerRef?.current || !currentPeriodId) return;

        const periodElement = scrollContainerRef.current.querySelector(
            `[data-period-id="${currentPeriodId}"]`
        );

        if (periodElement) {
            periodElement.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    }, [currentPeriodId, scrollContainerRef]);

    return (
        <button
            className="scroll-to-current"
            onClick={handleScrollToCurrent}
            title="Scroll to current period"
        >
            <Clock size={16} />
            <span>Go to Today</span>
        </button>
    );
};

// Export all components
export default {
    TaskSplitDialog,
    TaskMergeDialog,
    QuantityEditor,
    validatePrecedence,
    DowntimeIndicator,
    GanttFilters,
    ScrollToCurrentButton
};
