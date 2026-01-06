/**
 * GanttChart.jsx - Enhanced Gantt Chart Component
 * 
 * Provides comprehensive task visualization and editing:
 * - Drag-drop task assignment (resource & period)
 * - Rate factor inline editing
 * - Task splitting across periods
 * - Maintenance/availability overlays
 * - Rich filtering controls
 * - Real-time API updates
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { clsx } from 'clsx';
import {
    Calendar, ChevronRight, ChevronLeft, RefreshCw,
    ZoomIn, ZoomOut, Filter, Plus, Save, Undo,
    Split, Trash2, Settings
} from 'lucide-react';
import axios from 'axios';
import GanttTaskBar, { MaintenanceOverlay, GanttFilters } from './GanttTaskBar';
import GanttContextMenu from './GanttContextMenu';

const API_BASE = 'http://localhost:8000';

const GanttChart = ({ siteId, resources = [], scheduleVersionId, periods = [], onTaskUpdate }) => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedTaskId, setSelectedTaskId] = useState(null);
    const [filters, setFilters] = useState({
        coalOnly: false,
        qualityRisk: false,
        delayed: false,
        resource: 'all'
    });
    const [zoomLevel, setZoomLevel] = useState(1); // 0.5=compact, 1=normal, 2=expanded
    const [viewMode, setViewMode] = useState('shift'); // shift, day, week
    const [dragOverCell, setDragOverCell] = useState(null);
    const [editHistory, setEditHistory] = useState([]);
    const [saving, setSaving] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [maintenanceWindows, setMaintenanceWindows] = useState([]);
    const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0, task: null });

    const gridRef = useRef(null);

    // Fetch tasks when schedule version changes
    useEffect(() => {
        if (scheduleVersionId) {
            fetchTasks();
            fetchMaintenanceWindows();
        }
    }, [scheduleVersionId]);

    // Filter visible periods based on view mode
    const visiblePeriods = React.useMemo(() => {
        if (!periods.length) return [];

        // For now, show all periods - could add pagination
        const maxPeriods = Math.floor(12 * zoomLevel);
        return periods.slice(0, maxPeriods);
    }, [periods, zoomLevel, viewMode]);

    // Filter tasks based on current filters
    const filteredTasks = React.useMemo(() => {
        return tasks.filter(task => {
            if (filters.coalOnly && task.materialType !== 'Coal') return false;
            if (filters.qualityRisk && !task.qualityRisk) return false;
            if (filters.delayed && task.status !== 'delayed') return false;
            if (filters.resource !== 'all' && task.resourceId !== filters.resource) return false;
            return true;
        });
    }, [tasks, filters]);

    /**
     * Fetch tasks from the backend
     */
    const fetchTasks = async () => {
        setLoading(true);
        console.log("Gantt: Fetching tasks for version:", scheduleVersionId);
        try {
            const res = await axios.get(`${API_BASE}/schedule/versions/${scheduleVersionId}`);
            const backendTasks = res.data.tasks.map(t => ({
                id: t.task_id,
                resourceId: t.resource_id,
                periodId: t.period_id,
                activityId: t.activity_id,
                activityAreaId: t.activity_area_id,
                activityName: t.task_type || 'Mining',
                areaName: t.activity_area_id?.slice(0, 8) || 'Unknown',
                destinationName: t.destination_node_id || 'ROM',
                tonnes: t.planned_quantity || 0,
                durationHours: t.duration_hours || 12,
                materialType: t.material_type_id || 'Coal',
                quality: t.quality_vector || {},
                qualityRisk: t.quality_vector?.Ash > 16,
                rateFactor: t.rate_factor_applied || 1,
                status: t.status || 'scheduled',
                taskType: t.task_type,
                notes: t.notes,
                delayReasonCode: t.delay_reason_code
            }));
            setTasks(backendTasks);
        } catch (e) {
            console.error("Failed to fetch tasks", e);
        } finally {
            setLoading(false);
        }
    };

    /**
     * Fetch maintenance windows for overlay
     */
    const fetchMaintenanceWindows = async () => {
        try {
            const res = await axios.get(`${API_BASE}/resources/maintenance?site_id=${siteId}`);
            setMaintenanceWindows(res.data || []);
        } catch (e) {
            // No maintenance data - that's fine
            setMaintenanceWindows([]);
        }
    };

    /**
     * Handle drag start for task
     */
    const handleDragStart = (e, taskId) => {
        e.dataTransfer.setData("taskId", taskId);
        e.dataTransfer.effectAllowed = 'move';
        // Add visual feedback
        e.target.style.opacity = '0.5';
    };

    const handleDragEnd = (e) => {
        e.target.style.opacity = '1';
        setDragOverCell(null);
    };

    const handleDragOver = (e, resourceId, periodId) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        setDragOverCell({ resourceId, periodId });
    };

    const handleDragLeave = () => {
        setDragOverCell(null);
    };

    /**
     * Handle drop - move task to new cell
     */
    const handleDrop = async (e, targetResourceId, targetPeriodId) => {
        e.preventDefault();
        setDragOverCell(null);

        const taskId = e.dataTransfer.getData("taskId");
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;

        // Save to undo history
        setEditHistory(prev => [...prev, {
            type: 'move', taskId,
            oldResourceId: task.resourceId, oldPeriodId: task.periodId,
            newResourceId: targetResourceId, newPeriodId: targetPeriodId
        }]);

        // Optimistic update
        const updatedTasks = tasks.map(t => {
            if (t.id === taskId) {
                return { ...t, resourceId: targetResourceId, periodId: targetPeriodId };
            }
            return t;
        });
        setTasks(updatedTasks);

        // API update
        try {
            setSaving(true);
            await axios.put(`${API_BASE}/schedule/tasks/${taskId}`, {
                resource_id: targetResourceId,
                period_id: targetPeriodId
            });
            onTaskUpdate?.();
        } catch (error) {
            console.error("Failed to update task", error);
            // Revert on failure
            fetchTasks();
        } finally {
            setSaving(false);
        }
    };

    /**
     * Handle rate factor update
     */
    const handleUpdateRateFactor = async (taskId, newFactor) => {
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;

        // Save to undo history
        setEditHistory(prev => [...prev, {
            type: 'rateFactor', taskId,
            oldValue: task.rateFactor, newValue: newFactor
        }]);

        // Optimistic update
        const updatedTasks = tasks.map(t => {
            if (t.id === taskId) {
                // Adjust tonnes based on rate factor change
                const tonnageAdjustment = newFactor / (task.rateFactor || 1);
                return { ...t, rateFactor: newFactor, tonnes: t.tonnes * tonnageAdjustment };
            }
            return t;
        });
        setTasks(updatedTasks);

        // API update
        try {
            setSaving(true);
            await axios.put(`${API_BASE}/schedule/tasks/${taskId}`, {
                rate_factor_applied: newFactor
            });
            onTaskUpdate?.();
        } catch (error) {
            console.error("Failed to update rate factor", error);
            fetchTasks();
        } finally {
            setSaving(false);
        }
    };

    /**
     * Handle task deletion
     */
    const handleDeleteTask = async (taskId) => {
        if (!window.confirm("Delete this task? This action cannot be undone.")) return;

        try {
            setSaving(true);
            await axios.delete(`${API_BASE}/schedule/tasks/${taskId}`);
            setTasks(tasks.filter(t => t.id !== taskId));
            setSelectedTaskId(null);
            onTaskUpdate?.();
        } catch (error) {
            console.error("Failed to delete task", error);
        } finally {
            setSaving(false);
        }
    };

    /**
     * Handle right-click context menu
     */
    const handleContextMenu = (e, task) => {
        e.preventDefault();
        setContextMenu({
            visible: true,
            x: e.clientX,
            y: e.clientY,
            task
        });
    };

    /**
     * Close context menu
     */
    const closeContextMenu = () => {
        setContextMenu({ visible: false, x: 0, y: 0, task: null });
    };

    /**
     * Handle task split
     */
    const handleSplitTask = async (taskId, splitConfig) => {
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;

        try {
            setSaving(true);

            // Update the original task with reduced tonnes
            const updatedOriginal = {
                ...task,
                tonnes: splitConfig.firstPartTonnes
            };

            // Create a new task for the second part
            const newTaskResponse = await axios.post(`${API_BASE}/schedule/tasks`, {
                schedule_version_id: scheduleVersionId,
                resource_id: task.resourceId,
                period_id: splitConfig.targetPeriodId,
                activity_id: task.activityId,
                activity_area_id: task.activityAreaId,
                planned_quantity: splitConfig.secondPartTonnes,
                material_type_id: task.materialType,
                task_type: task.taskType,
                notes: `Split from task ${taskId}`
            });

            // Update original task
            await axios.put(`${API_BASE}/schedule/tasks/${taskId}`, {
                planned_quantity: splitConfig.firstPartTonnes
            });

            // Update local state
            const newTask = {
                ...task,
                id: newTaskResponse.data.task_id || `split-${Date.now()}`,
                periodId: splitConfig.targetPeriodId,
                tonnes: splitConfig.secondPartTonnes
            };

            setTasks(prev => [
                ...prev.map(t => t.id === taskId ? updatedOriginal : t),
                newTask
            ]);

            // Add to undo history
            setEditHistory(prev => [...prev, {
                type: 'split',
                originalTaskId: taskId,
                newTaskId: newTask.id,
                originalTonnes: task.tonnes
            }]);

            onTaskUpdate?.();
        } catch (error) {
            console.error("Failed to split task", error);
            fetchTasks();
        } finally {
            setSaving(false);
        }
    };

    /**
     * Handle resource change from context menu
     */
    const handleChangeResource = async (taskId, newResourceId) => {
        const task = tasks.find(t => t.id === taskId);
        if (!task || task.resourceId === newResourceId) return;

        // Save to undo history
        setEditHistory(prev => [...prev, {
            type: 'move', taskId,
            oldResourceId: task.resourceId, oldPeriodId: task.periodId,
            newResourceId: newResourceId, newPeriodId: task.periodId
        }]);

        // Optimistic update
        setTasks(tasks.map(t =>
            t.id === taskId ? { ...t, resourceId: newResourceId } : t
        ));

        try {
            setSaving(true);
            await axios.put(`${API_BASE}/schedule/tasks/${taskId}`, {
                resource_id: newResourceId
            });
            onTaskUpdate?.();
        } catch (error) {
            console.error("Failed to change resource", error);
            fetchTasks();
        } finally {
            setSaving(false);
        }
    };

    /**
     * Undo last action
     */
    const handleUndo = async () => {
        if (editHistory.length === 0) return;

        const lastAction = editHistory[editHistory.length - 1];
        setEditHistory(prev => prev.slice(0, -1));

        if (lastAction.type === 'move') {
            // Revert movement
            const updatedTasks = tasks.map(t => {
                if (t.id === lastAction.taskId) {
                    return { ...t, resourceId: lastAction.oldResourceId, periodId: lastAction.oldPeriodId };
                }
                return t;
            });
            setTasks(updatedTasks);

            try {
                await axios.put(`${API_BASE}/schedule/tasks/${lastAction.taskId}`, {
                    resource_id: lastAction.oldResourceId,
                    period_id: lastAction.oldPeriodId
                });
            } catch (e) {
                fetchTasks();
            }
        } else if (lastAction.type === 'rateFactor') {
            // Revert rate factor
            const updatedTasks = tasks.map(t => {
                if (t.id === lastAction.taskId) {
                    return { ...t, rateFactor: lastAction.oldValue };
                }
                return t;
            });
            setTasks(updatedTasks);

            try {
                await axios.put(`${API_BASE}/schedule/tasks/${lastAction.taskId}`, {
                    rate_factor_applied: lastAction.oldValue
                });
            } catch (e) {
                fetchTasks();
            }
        }
    };

    /**
     * Format period label
     */
    const formatPeriod = (p) => {
        if (!p.start_datetime) return p.name;
        const date = new Date(p.start_datetime);
        const day = date.getDate();
        const month = date.toLocaleString('default', { month: 'short' });
        const shift = p.group_shift || '';
        return `${day} ${month} ${shift}`;
    };

    /**
     * Get tasks for a specific cell
     */
    const getTasksForCell = (resourceId, periodId) => {
        return filteredTasks.filter(t => t.resourceId === resourceId && t.periodId === periodId);
    };

    /**
     * Calculate period width based on zoom
     */
    const periodWidth = Math.max(80, 120 * zoomLevel);
    const rowHeight = 56 + (16 * (zoomLevel - 1));

    // Calculate total width for summary stats
    const totalTonnes = filteredTasks.reduce((sum, t) => sum + (t.tonnes || 0), 0);
    const taskCount = filteredTasks.length;

    return (
        <div className="flex flex-col h-full bg-slate-900 text-slate-100">
            {/* Toolbar */}
            <div className="h-12 border-b border-slate-800 flex items-center px-4 justify-between bg-slate-950">
                {/* Left: Navigation */}
                <div className="flex items-center space-x-2">
                    <button className="p-1 hover:bg-slate-800 rounded" title="Previous">
                        <ChevronLeft size={18} />
                    </button>
                    <span className="font-medium text-sm flex items-center">
                        {visiblePeriods.length > 0
                            ? `${formatPeriod(visiblePeriods[0])} - ${formatPeriod(visiblePeriods[visiblePeriods.length - 1])}`
                            : "No Calendar Loaded"}
                    </span>
                    <button className="p-1 hover:bg-slate-800 rounded" title="Next">
                        <ChevronRight size={18} />
                    </button>
                </div>

                {/* Center: View controls */}
                <div className="flex items-center space-x-2">
                    <button
                        onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.25))}
                        className="p-1 hover:bg-slate-800 rounded"
                        title="Zoom Out"
                    >
                        <ZoomOut size={16} />
                    </button>
                    <span className="text-xs text-slate-400 w-12 text-center">{(zoomLevel * 100).toFixed(0)}%</span>
                    <button
                        onClick={() => setZoomLevel(Math.min(2, zoomLevel + 0.25))}
                        className="p-1 hover:bg-slate-800 rounded"
                        title="Zoom In"
                    >
                        <ZoomIn size={16} />
                    </button>

                    <div className="h-4 w-px bg-slate-700 mx-2" />

                    {/* View mode selector */}
                    <select
                        value={viewMode}
                        onChange={(e) => setViewMode(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
                    >
                        <option value="shift">Shift View</option>
                        <option value="day">Day View</option>
                        <option value="week">Week View</option>
                    </select>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center space-x-4 text-xs">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={clsx(
                            "flex items-center px-2 py-1 rounded",
                            showFilters ? "bg-blue-600 text-white" : "hover:bg-slate-800"
                        )}
                    >
                        <Filter size={14} className="mr-1" />
                        Filters
                    </button>

                    <button
                        onClick={handleUndo}
                        disabled={editHistory.length === 0}
                        className={clsx(
                            "flex items-center px-2 py-1 rounded",
                            editHistory.length > 0 ? "hover:bg-slate-800" : "text-slate-600 cursor-not-allowed"
                        )}
                        title="Undo last action"
                    >
                        <Undo size={14} className="mr-1" />
                        Undo ({editHistory.length})
                    </button>

                    <button
                        onClick={fetchTasks}
                        className="flex items-center hover:text-blue-400"
                    >
                        <RefreshCw size={14} className={clsx("mr-1", loading && "animate-spin")} />
                        Refresh
                    </button>

                    {saving && (
                        <span className="text-yellow-400 flex items-center">
                            <Save size={14} className="mr-1 animate-pulse" />
                            Saving...
                        </span>
                    )}
                </div>
            </div>

            {/* Filter bar (collapsible) */}
            {showFilters && (
                <GanttFilters filters={filters} onChange={setFilters} />
            )}

            {/* Summary bar */}
            <div className="h-8 bg-slate-850 border-b border-slate-800 flex items-center px-4 text-xs text-slate-400">
                <span className="mr-4">
                    <strong className="text-slate-300">{taskCount}</strong> tasks
                </span>
                <span className="mr-4">
                    <strong className="text-slate-300">{totalTonnes.toLocaleString()}</strong>t total
                </span>
                <span className="flex items-center">
                    <span className="w-3 h-3 bg-blue-600 rounded-sm mr-1"></span>
                    Coal
                    <span className="w-3 h-3 bg-slate-600 rounded-sm mr-1 ml-3"></span>
                    Waste
                    <span className="w-3 h-3 bg-amber-600 rounded-sm mr-1 ml-3"></span>
                    At Risk
                    <span className="w-3 h-3 bg-purple-600 rounded-sm mr-1 ml-3" style={{
                        backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(255,255,255,0.3) 2px, rgba(255,255,255,0.3) 4px)'
                    }}></span>
                    Delay
                </span>
            </div>

            {/* Gantt Grid */}
            <div ref={gridRef} className="flex-1 overflow-auto relative">
                <div style={{ minWidth: `${200 + visiblePeriods.length * periodWidth}px` }}>
                    {/* Header Row */}
                    <div className="flex border-b border-slate-800 bg-slate-900 sticky top-0 z-10 text-xs">
                        <div
                            className="w-48 min-w-48 p-2 border-r border-slate-800 font-bold uppercase tracking-wider text-slate-500 sticky left-0 bg-slate-900 z-20"
                        >
                            Resource
                        </div>
                        {visiblePeriods.map(p => (
                            <div
                                key={p.period_id}
                                className="p-2 border-r border-slate-800 text-center text-slate-400 font-medium"
                                style={{ width: periodWidth, minWidth: periodWidth }}
                            >
                                {formatPeriod(p)}
                            </div>
                        ))}
                    </div>

                    {/* Resource Rows */}
                    {resources.map(res => (
                        <div
                            key={res.resource_id}
                            className="flex border-b border-slate-800 hover:bg-slate-800/20 transition-colors"
                            style={{ height: rowHeight }}
                        >
                            {/* Resource Name (sticky) */}
                            <div className="w-48 min-w-48 p-3 border-r border-slate-800 flex items-center text-sm font-medium text-slate-300 sticky left-0 bg-slate-900 z-10">
                                <div>
                                    {res.name}
                                    <span className="block text-xs text-slate-500">{res.resource_type}</span>
                                </div>
                            </div>

                            {/* Time Slots */}
                            {visiblePeriods.map((p) => {
                                const cellTasks = getTasksForCell(res.resource_id, p.period_id);
                                const isDragOver = dragOverCell?.resourceId === res.resource_id &&
                                    dragOverCell?.periodId === p.period_id;

                                // Check for maintenance
                                const hasMaintenance = maintenanceWindows.some(
                                    mw => mw.resource_id === res.resource_id && mw.period_id === p.period_id
                                );

                                return (
                                    <div
                                        key={p.period_id}
                                        className={clsx(
                                            "border-r border-slate-800 relative p-1 transition-colors",
                                            isDragOver && "bg-blue-500/20 ring-2 ring-blue-500 ring-inset",
                                            !p.is_working_period && "bg-slate-800/50",
                                            hasMaintenance && "bg-red-500/10"
                                        )}
                                        style={{ width: periodWidth, minWidth: periodWidth }}
                                        onDragOver={(e) => handleDragOver(e, res.resource_id, p.period_id)}
                                        onDragLeave={handleDragLeave}
                                        onDrop={(e) => handleDrop(e, res.resource_id, p.period_id)}
                                    >
                                        {/* Maintenance overlay indicator */}
                                        {hasMaintenance && (
                                            <div className="absolute top-0 left-0 right-0 h-1 bg-red-500" />
                                        )}

                                        {/* Tasks in this cell */}
                                        <div className="flex flex-col gap-1 h-full">
                                            {cellTasks.map(task => (
                                                <div
                                                    key={task.id}
                                                    draggable={task.taskType !== 'OptimiserDelay'}
                                                    onDragStart={(e) => handleDragStart(e, task.id)}
                                                    onDragEnd={handleDragEnd}
                                                    onClick={() => setSelectedTaskId(task.id)}
                                                    onContextMenu={(e) => handleContextMenu(e, task)}
                                                    className={clsx(
                                                        "flex-1 min-h-6 rounded text-xs flex items-center justify-center px-2",
                                                        "font-medium text-white shadow transition-all",
                                                        task.taskType !== 'OptimiserDelay' && "cursor-grab active:cursor-grabbing hover:brightness-110",
                                                        task.taskType === 'OptimiserDelay' && "cursor-default",
                                                        task.materialType === 'Coal' && !task.qualityRisk && task.taskType !== 'OptimiserDelay' && "bg-gradient-to-r from-blue-600 to-blue-500",
                                                        task.materialType === 'Coal' && task.qualityRisk && task.taskType !== 'OptimiserDelay' && "bg-gradient-to-r from-amber-600 to-amber-500",
                                                        task.materialType === 'Waste' && task.taskType !== 'OptimiserDelay' && "bg-gradient-to-r from-slate-600 to-slate-500",
                                                        task.taskType === 'OptimiserDelay' && "bg-purple-600",
                                                        selectedTaskId === task.id && "ring-2 ring-white ring-offset-1 ring-offset-slate-900"
                                                    )}
                                                    style={task.taskType === 'OptimiserDelay' ? {
                                                        backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(255,255,255,0.2) 3px, rgba(255,255,255,0.2) 6px)'
                                                    } : undefined}
                                                    title={task.taskType === 'OptimiserDelay'
                                                        ? `Optimizer Delay: ${task.notes || 'Rate reduction applied'}`
                                                        : `${task.activityName}: ${task.tonnes.toLocaleString()}t${task.rateFactor !== 1 ? ` (${(task.rateFactor * 100).toFixed(0)}%)` : ''}`
                                                    }
                                                >
                                                    {task.taskType === 'OptimiserDelay' ? (
                                                        <span className="truncate text-purple-200 italic">
                                                            ⚡ Delay
                                                        </span>
                                                    ) : (
                                                        <>
                                                            <span className="truncate">
                                                                {task.tonnes >= 1000
                                                                    ? `${(task.tonnes / 1000).toFixed(1)}kt`
                                                                    : `${task.tonnes.toFixed(0)}t`
                                                                }
                                                            </span>
                                                            {task.rateFactor !== 1 && (
                                                                <span className="ml-1 opacity-70">
                                                                    {(task.rateFactor * 100).toFixed(0)}%
                                                                </span>
                                                            )}
                                                        </>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))}

                    {/* Empty state */}
                    {resources.length === 0 && (
                        <div className="p-8 text-center text-slate-500">
                            No resources found. Initialize Demo Data to see fleet.
                        </div>
                    )}
                </div>
            </div>

            {/* Selected Task Panel */}
            {selectedTaskId && (
                <div className="h-24 border-t border-slate-800 bg-slate-850 p-4 flex items-center justify-between">
                    {(() => {
                        const task = tasks.find(t => t.id === selectedTaskId);
                        if (!task) return null;

                        return (
                            <>
                                <div className="flex items-center space-x-6">
                                    <div>
                                        <div className="text-sm font-medium text-white">{task.activityName}</div>
                                        <div className="text-xs text-slate-400">{task.areaName}</div>
                                    </div>
                                    <div className="text-sm">
                                        <span className="text-slate-400">Tonnes:</span>
                                        <span className="ml-2 text-white font-medium">{task.tonnes.toLocaleString()}</span>
                                    </div>
                                    <div className="text-sm">
                                        <span className="text-slate-400">Rate Factor:</span>
                                        <input
                                            type="range"
                                            min="0.5"
                                            max="1.5"
                                            step="0.05"
                                            value={task.rateFactor}
                                            onChange={(e) => handleUpdateRateFactor(task.id, parseFloat(e.target.value))}
                                            className="ml-2 w-24 align-middle"
                                        />
                                        <span className="ml-2 text-white">{(task.rateFactor * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => handleDeleteTask(task.id)}
                                        className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs rounded flex items-center"
                                    >
                                        <Trash2 size={14} className="mr-1" />
                                        Delete
                                    </button>
                                    <button
                                        onClick={() => setSelectedTaskId(null)}
                                        className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded"
                                    >
                                        Close
                                    </button>
                                </div>
                            </>
                        );
                    })()}
                </div>
            )}

            {/* Context Menu */}
            <GanttContextMenu
                visible={contextMenu.visible}
                x={contextMenu.x}
                y={contextMenu.y}
                task={contextMenu.task}
                resources={resources}
                periods={periods}
                onClose={closeContextMenu}
                onEditTask={(task) => setSelectedTaskId(task.id)}
                onSplitTask={handleSplitTask}
                onChangeResource={handleChangeResource}
                onDeleteTask={handleDeleteTask}
                onViewExplanation={(task) => {
                    console.log("View explanation for task:", task.id);
                    // TODO: Open decision explanation modal
                }}
                onDuplicateTask={(task) => {
                    console.log("Duplicate task:", task.id);
                    // TODO: Implement duplicate
                }}
            />
        </div>
    );
};

export default GanttChart;
