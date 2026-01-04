import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Play, Zap, Send, FileText, Clock, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const Dashboard = ({ scheduleVersionId, siteId, versionName, onRefresh }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState(null); // 'fastpass' | 'fullpass' | 'publish' | 'export'
    const [shiftTimeRemaining, setShiftTimeRemaining] = useState(null);
    const [lastRunStatus, setLastRunStatus] = useState(null);

    useEffect(() => {
        if (scheduleVersionId) {
            fetchStats();
            fetchLastRunStatus();
        }
    }, [scheduleVersionId]);

    // Shift countdown timer
    useEffect(() => {
        if (stats?.shift_end_time) {
            const updateCountdown = () => {
                const now = new Date();
                const end = new Date(stats.shift_end_time);
                const diff = end - now;
                if (diff > 0) {
                    const hours = Math.floor(diff / (1000 * 60 * 60));
                    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    setShiftTimeRemaining(`${hours}h ${minutes}m remaining`);
                } else {
                    setShiftTimeRemaining('Shift ended');
                }
            };
            updateCountdown();
            const interval = setInterval(updateCountdown, 60000); // Update every minute
            return () => clearInterval(interval);
        }
    }, [stats?.shift_end_time]);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/reporting/dashboard/${scheduleVersionId}`);

            // Also fetch Cycle Times
            let cycleTimes = [];
            try {
                const ctRes = await axios.get(`${API_BASE}/analytics/cycle-times/${scheduleVersionId}`);
                cycleTimes = ctRes.data;
            } catch (e) {
                console.warn("Cycle Times fetch failed");
            }

            setStats({
                ...res.data,
                cycle_times: cycleTimes
            });
        } catch (e) {
            console.error("Failed to fetch dashboard stats", e);
        } finally {
            setLoading(false);
        }
    };

    const fetchLastRunStatus = async () => {
        try {
            const res = await axios.get(`${API_BASE}/schedule/versions/${scheduleVersionId}/runs?limit=1`);
            if (res.data && res.data.length > 0) {
                setLastRunStatus(res.data[0]);
            }
        } catch (e) {
            // Run history may not be available
        }
    };

    // Quick Action Handlers
    const handleRunFastPass = async () => {
        setActionLoading('fastpass');
        try {
            await axios.post(`${API_BASE}/schedule/run/fast-pass`, {
                site_id: siteId,
                schedule_version_id: scheduleVersionId
            });
            fetchStats();
            fetchLastRunStatus();
            onRefresh?.();
        } catch (e) {
            console.error("Fast pass failed", e);
        } finally {
            setActionLoading(null);
        }
    };

    const handleRunFullPass = async () => {
        setActionLoading('fullpass');
        try {
            await axios.post(`${API_BASE}/schedule/run/full-pass`, {
                site_id: siteId,
                schedule_version_id: scheduleVersionId
            });
            fetchStats();
            fetchLastRunStatus();
            onRefresh?.();
        } catch (e) {
            console.error("Full pass failed", e);
        } finally {
            setActionLoading(null);
        }
    };

    const handlePublish = async () => {
        if (!window.confirm("Publish this schedule? It will become read-only.")) return;
        setActionLoading('publish');
        try {
            await axios.put(`${API_BASE}/schedule/versions/${scheduleVersionId}/publish`);
            fetchStats();
            onRefresh?.();
        } catch (e) {
            console.error("Publish failed", e);
        } finally {
            setActionLoading(null);
        }
    };

    const handleExportReportPack = async () => {
        setActionLoading('export');
        try {
            const res = await axios.post(`${API_BASE}/reporting/export/pdf/production`, {
                schedule_version_id: scheduleVersionId
            }, { responseType: 'blob' });

            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `schedule_report_${scheduleVersionId.slice(0, 8)}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (e) {
            console.error("Export failed", e);
            alert("PDF export failed. Ensure WeasyPrint is installed.");
        } finally {
            setActionLoading(null);
        }
    };

    if (loading) {
        return <div className="flex h-full items-center justify-center text-slate-400">Loading Dashboard...</div>;
    }

    if (!stats) {
        return <div className="flex h-full items-center justify-center text-slate-500">No Data Available. Generate a Schedule first.</div>;
    }

    return (
        <div className="h-full w-full bg-slate-900 p-6 overflow-y-auto">
            {/* Header with Title and Quick Actions */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white">Production Overview</h2>
                    {versionName && (
                        <p className="text-sm text-slate-400 mt-1">
                            Schedule: <span className="text-blue-400">{versionName}</span>
                        </p>
                    )}
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleRunFastPass}
                        disabled={actionLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {actionLoading === 'fastpass' ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <Zap size={16} />
                        )}
                        Fast Pass
                    </button>

                    <button
                        onClick={handleRunFullPass}
                        disabled={actionLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {actionLoading === 'fullpass' ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <Play size={16} />
                        )}
                        Full Pass
                    </button>

                    <button
                        onClick={handlePublish}
                        disabled={actionLoading || stats.status === 'Published'}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {actionLoading === 'publish' ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <Send size={16} />
                        )}
                        Publish
                    </button>

                    <button
                        onClick={handleExportReportPack}
                        disabled={actionLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {actionLoading === 'export' ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <FileText size={16} />
                        )}
                        Export PDF
                    </button>
                </div>
            </div>

            {/* Current Period & Status Bar */}
            <div className="bg-gradient-to-r from-blue-900 to-slate-800 p-4 rounded-lg border border-blue-700 mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <div>
                            <p className="text-sm text-blue-300 font-medium">Current Period</p>
                            <p className="text-xl font-bold text-white">{stats.current_period || 'Day Shift - Week 1'}</p>
                            {shiftTimeRemaining && (
                                <p className="text-sm text-blue-200 flex items-center gap-1 mt-1">
                                    <Clock size={14} />
                                    {shiftTimeRemaining}
                                </p>
                            )}
                        </div>

                        {lastRunStatus && (
                            <div className="border-l border-blue-700 pl-6">
                                <p className="text-sm text-slate-400">Last Schedule Run</p>
                                <p className="text-sm text-white font-medium flex items-center gap-2">
                                    {lastRunStatus.status === 'Completed' ? (
                                        <CheckCircle size={14} className="text-green-400" />
                                    ) : lastRunStatus.status === 'Failed' ? (
                                        <AlertTriangle size={14} className="text-red-400" />
                                    ) : (
                                        <RefreshCw size={14} className="text-yellow-400 animate-spin" />
                                    )}
                                    {lastRunStatus.schedule_type} - {lastRunStatus.status}
                                </p>
                                <p className="text-xs text-slate-400">
                                    {new Date(lastRunStatus.timestamp).toLocaleString()}
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="text-right">
                        <p className="text-sm text-slate-400">Schedule Status</p>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${stats.status === 'Published' ? 'bg-green-900 text-green-300' :
                            stats.status === 'Running' ? 'bg-yellow-900 text-yellow-300' :
                                'bg-slate-700 text-slate-300'
                            }`}>
                            {stats.status || 'Draft'}
                        </span>
                    </div>
                </div>
            </div>

            {/* KPI Cards - Primary Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Mined</p>
                    <p className="text-2xl font-bold text-white mt-1">{stats.total_tons?.toLocaleString() || 0} <span className="text-sm text-slate-500 font-normal">t</span></p>
                </div>

                <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Coal Production</p>
                    <p className="text-2xl font-bold text-blue-400 mt-1">{stats.coal_tons?.toLocaleString() || 0} <span className="text-sm text-slate-500 font-normal">t</span></p>
                </div>

                <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Stripping Ratio</p>
                    <p className="text-2xl font-bold text-amber-400 mt-1">{stats.stripping_ratio || '0:1'} <span className="text-sm text-slate-500 font-normal">W:C</span></p>
                </div>

                <div className="bg-slate-800 p-5 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Equipment Util.</p>
                    <p className="text-2xl font-bold text-green-400 mt-1">{stats.equipment_utilization || 85}%</p>
                </div>
            </div>

            {/* Quick KPIs - Actual vs Plan */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-slate-400 uppercase">Last Shift Actual vs Plan</p>
                        <span className={`text-xs font-medium ${(stats.actual_vs_plan || 98) >= 95 ? 'text-green-400' : 'text-red-400'}`}>
                            {stats.actual_vs_plan || 98}%
                        </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                            className={`h-2 rounded-full ${(stats.actual_vs_plan || 98) >= 95 ? 'bg-green-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(stats.actual_vs_plan || 98, 100)}%` }}
                        />
                    </div>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-slate-400 uppercase">Quality Compliance</p>
                        <span className={`text-xs font-medium ${(stats.quality_compliance || 92) >= 90 ? 'text-green-400' : 'text-amber-400'}`}>
                            {stats.quality_compliance || 92}%
                        </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                            className={`h-2 rounded-full ${(stats.quality_compliance || 92) >= 90 ? 'bg-green-500' : 'bg-amber-500'}`}
                            style={{ width: `${stats.quality_compliance || 92}%` }}
                        />
                    </div>
                </div>

                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-slate-400 uppercase">Plant Throughput</p>
                        <span className="text-xs font-medium text-blue-400">
                            {stats.plant_throughput || 450} t/h
                        </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                            className="h-2 rounded-full bg-blue-500"
                            style={{ width: `${Math.min((stats.plant_throughput || 450) / 500 * 100, 100)}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Alerts Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {/* Stockpile Level Alerts */}
                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></span>
                        Stockpile Alerts
                    </h4>
                    <div className="space-y-2 text-sm">
                        {(stats.stockpile_alerts || [
                            { name: 'ROM Stockpile 1', level: 85, status: 'high' },
                            { name: 'Product Stockpile A', level: 15, status: 'low' }
                        ]).map((alert, i) => (
                            <div key={i} className="flex items-center justify-between p-2 bg-slate-700/50 rounded">
                                <span className="text-slate-300">{alert.name}</span>
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${alert.status === 'high' ? 'bg-amber-900 text-amber-300' :
                                    alert.status === 'low' ? 'bg-red-900 text-red-300' :
                                        'bg-green-900 text-green-300'
                                    }`}>
                                    {alert.level}% {alert.status === 'high' ? '↑' : alert.status === 'low' ? '↓' : '✓'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Quality Compliance Status */}
                <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Quality Status
                    </h4>
                    <div className="space-y-2 text-sm">
                        {(stats.quality_status || [
                            { field: 'CV', value: 23.5, target: '22-25 MJ/kg', compliant: true },
                            { field: 'Ash', value: 12.8, target: '<14%', compliant: true },
                            { field: 'Moisture', value: 9.2, target: '<10%', compliant: true }
                        ]).map((q, i) => (
                            <div key={i} className="flex items-center justify-between p-2 bg-slate-700/50 rounded">
                                <span className="text-slate-300">{q.field}: <span className="text-white font-medium">{q.value}</span></span>
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${q.compliant ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                                    }`}>
                                    {q.target}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Charts Row 1 */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg h-96 mb-8">
                <h3 className="text-lg font-bold text-white mb-4">Production by Period</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={stats.chart_data}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                            itemStyle={{ color: '#f1f5f9' }}
                        />
                        <Legend />
                        <Bar dataKey="coal" name="Coal" stackId="a" fill="#3b82f6" />
                        <Bar dataKey="waste" name="Waste" stackId="a" fill="#ef4444" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Cycle Time Analytics */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-white">Truck Cycle Times vs Distance</h3>
                    <button
                        onClick={() => {
                            // Simple CSV Export Logic
                            if (!stats.cycle_times) return;
                            const headers = ["Task ID", "Block", "Destination", "Distance (m)", "Cycle Time (min)", "Throughput (t/h)"];
                            const rows = stats.cycle_times.map(r => [
                                r.task_id, r.block_name, r.destination, r.distance_m, r.cycle_time_min, r.potential_tph
                            ]);
                            const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
                            const encodedUri = encodeURI(csvContent);
                            const link = document.createElement("a");
                            link.setAttribute("href", encodedUri);
                            link.setAttribute("download", "schedule_cycles.csv");
                            document.body.appendChild(link);
                            link.click();
                        }}
                        className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded border border-slate-600"
                    >
                        Export CSV
                    </button>
                </div>

                <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" dataKey="distance_m" name="Distance" unit="m" stroke="#94a3b8" />
                            <YAxis type="number" dataKey="cycle_time_min" name="Cycle Time" unit="min" stroke="#94a3b8" />
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b' }} />
                            <Legend />
                            <Scatter name="Haul Routes" data={stats.cycle_times || []} fill="#f59e0b" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
