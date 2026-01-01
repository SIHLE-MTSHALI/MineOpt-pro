import React, { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { Calendar, ChevronRight, ChevronLeft, RefreshCw } from 'lucide-react';
import axios from 'axios';

const GanttChart = ({ siteId, resources = [], scheduleVersionId, periods = [] }) => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (scheduleVersionId) {
            fetchTasks();
        }
    }, [scheduleVersionId]);

    const fetchTasks = async () => {
        setLoading(true);
        console.log("DEBUG: Gantt Fetching Tasks for Version:", scheduleVersionId);
        try {
            const res = await axios.get(`http://localhost:8000/schedule/versions/${scheduleVersionId}`);
            console.log("DEBUG: Gantt Raw Tasks:", res.data.tasks);
            const backendTasks = res.data.tasks.map(t => ({
                id: t.task_id,
                resourceId: t.resource_id,
                startPeriod: t.period_id,
                label: `${t.planned_quantity}t`, // Todo: Resolve Block Name via ID if available
                color: 'bg-blue-600',
                activityAreaId: t.activity_area_id
            }));
            setTasks(backendTasks);
        } catch (e) {
            console.error("Failed to fetch tasks", e);
        } finally {
            setLoading(false);
        }
    };

    // Drag and Drop Handlers
    const handleDragStart = (e, taskId) => {
        e.dataTransfer.setData("taskId", taskId);
    };

    const handleDrop = async (e, targetResourceId, targetPeriodId) => {
        e.preventDefault();
        const taskId = e.dataTransfer.getData("taskId");

        // Optimistic Update
        const updatedTasks = tasks.map(t => {
            if (t.id === taskId) {
                return { ...t, resourceId: targetResourceId, startPeriod: targetPeriodId };
            }
            return t;
        });
        setTasks(updatedTasks);

        // API Update
        try {
            await axios.put(`http://localhost:8000/schedule/tasks/${taskId}`, {
                resource_id: targetResourceId,
                period_id: targetPeriodId
            });
        } catch (error) {
            console.error("Failed to update task", error);
            // TODO: Revert on failure
            fetchTasks();
        }
    };

    // Helper to format period label nicely
    const formatPeriod = (p) => {
        if (!p.start_datetime) return p.name;
        const date = new Date(p.start_datetime);
        const day = date.getDate();
        const month = date.toLocaleString('default', { month: 'short' });
        // Show "31 Dec Day"
        return `${day} ${month} ${p.group_shift}`;
    };

    return (
        <div className="flex flex-col h-full bg-slate-900 text-slate-100">
            {/* Toolbar */}
            <div className="h-12 border-b border-slate-800 flex items-center px-4 justify-between bg-slate-950">
                <div className="flex items-center space-x-2">
                    <button className="p-1 hover:bg-slate-800 rounded"><ChevronLeft size={18} /></button>
                    <span className="font-medium text-sm flex items-center">
                        {periods.length > 0
                            ? `${new Date(periods[0].start_datetime).toDateString()} - ${new Date(periods[periods.length - 1].end_datetime).toDateString()}`
                            : "No Calendar Loaded"}
                    </span>
                    <button className="p-1 hover:bg-slate-800 rounded"><ChevronRight size={18} /></button>
                </div>
                <div className="flex items-center space-x-4 text-xs">
                    <button onClick={fetchTasks} className="flex items-center hover:text-blue-400">
                        <RefreshCw size={14} className={clsx("mr-1", loading && "animate-spin")} />
                        Refresh
                    </button>
                    <div className="flex items-center space-x-2">
                        <span className="flex items-center"><span className="w-3 h-3 bg-blue-600 rounded-sm mr-1"></span> Coal</span>
                    </div>
                </div>
            </div>

            {/* Gantt Grid */}
            <div className="flex-1 overflow-auto relative">
                <div className="min-w-[800px]">
                    {/* Header Row */}
                    <div className="flex border-b border-slate-800 bg-slate-900 sticky top-0 z-10 text-xs">
                        <div className="w-48 p-2 border-r border-slate-800 font-bold uppercase tracking-wider text-slate-500">Resource</div>
                        {periods.map(p => (
                            <div key={p.period_id} className="flex-1 min-w-[100px] p-2 border-r border-slate-800 text-center text-slate-400 font-medium">
                                {formatPeriod(p)}
                            </div>
                        ))}
                    </div>

                    {/* Resource Rows */}
                    {resources.map(res => (
                        <div key={res.resource_id} className="flex border-b border-slate-800 hover:bg-slate-800/30 transition-colors h-16">
                            {/* Resource Name */}
                            <div className="w-48 p-3 border-r border-slate-800 flex items-center text-sm font-medium text-slate-300">
                                {res.name}
                                <span className="ml-2 text-xs text-slate-500">({res.resource_type})</span>
                            </div>

                            {/* Time Slots */}
                            {periods.map((p, idx) => {
                                // Find tasks in this cell
                                const cellTasks = tasks.filter(t => t.resourceId === res.resource_id && t.startPeriod === p.period_id);

                                return (
                                    <div
                                        key={p.period_id}
                                        className="flex-1 min-w-[100px] border-r border-slate-800 relative p-1 group hover:bg-slate-800/50 transition-colors"
                                        onDragOver={(e) => e.preventDefault()}
                                        onDrop={(e) => handleDrop(e, res.resource_id, p.period_id)}
                                    >
                                        {cellTasks.map(task => (
                                            <div
                                                key={task.id}
                                                className={clsx(
                                                    "h-full rounded text-xs flex items-center justify-center font-bold text-white shadow cursor-grab active:cursor-grabbing hover:opacity-90",
                                                    task.color
                                                )}
                                                draggable
                                                onDragStart={(e) => handleDragStart(e, task.id)}
                                                title={task.label}
                                            >
                                                {task.label}
                                            </div>
                                        ))}
                                    </div>
                                );
                            })}
                        </div>
                    ))}

                    {resources.length === 0 && (
                        <div className="p-8 text-center text-slate-500">No resources found. Initialize Demo Data to see fleet.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GanttChart;
