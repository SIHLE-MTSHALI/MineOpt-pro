/**
 * SiteDashboard.jsx - Site Dashboard Launchpad
 * 
 * Main entry point for planners showing:
 * - Current period/shift info
 * - Active schedule summary
 * - Quick KPIs (planned vs actual, quality compliance)
 * - Stockpile alerts
 * - Quick action buttons
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Calendar, Clock, TrendingUp, AlertTriangle,
    Play, FileText, Settings, BarChart3, Package,
    Truck, Factory, ChevronRight, RefreshCw
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// KPI Card component
const KPICard = ({ title, value, unit, trend, trendLabel, icon: Icon, color = 'blue' }) => {
    const colorClasses = {
        blue: 'from-blue-500 to-blue-600',
        emerald: 'from-emerald-500 to-emerald-600',
        amber: 'from-amber-500 to-amber-600',
        purple: 'from-purple-500 to-purple-600',
        rose: 'from-rose-500 to-rose-600'
    };

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors">
            <div className="flex items-start justify-between">
                <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{title}</div>
                    <div className="text-3xl font-bold text-white">
                        {value}
                        {unit && <span className="text-lg text-slate-400 ml-1">{unit}</span>}
                    </div>
                    {trend !== undefined && (
                        <div className={`text-xs mt-2 ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% {trendLabel || 'vs plan'}
                        </div>
                    )}
                </div>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center shadow-lg`}>
                    <Icon size={24} className="text-white" />
                </div>
            </div>
        </div>
    );
};

// Alert card component
const AlertCard = ({ type, title, message, severity }) => {
    const severityConfig = {
        warning: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', icon: AlertTriangle },
        error: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', icon: AlertTriangle },
        info: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', icon: AlertTriangle }
    };
    const config = severityConfig[severity] || severityConfig.info;
    const Icon = config.icon;

    return (
        <div className={`p-4 rounded-lg ${config.bg} ${config.border} border`}>
            <div className="flex items-start gap-3">
                <Icon size={18} className={config.text} />
                <div>
                    <div className={`font-medium ${config.text}`}>{title}</div>
                    <div className="text-xs text-slate-400 mt-1">{message}</div>
                </div>
            </div>
        </div>
    );
};

// Quick action button
const ActionButton = ({ icon: Icon, label, description, onClick, primary = false }) => (
    <button
        onClick={onClick}
        className={`
            w-full p-4 rounded-xl border text-left transition-all
            ${primary
                ? 'bg-gradient-to-r from-blue-600 to-emerald-600 border-transparent hover:from-blue-500 hover:to-emerald-500 shadow-lg shadow-blue-500/20'
                : 'bg-slate-800/50 border-slate-700 hover:bg-slate-700/50 hover:border-slate-600'
            }
        `}
    >
        <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${primary ? 'bg-white/20' : 'bg-slate-700'}`}>
                <Icon size={20} className={primary ? 'text-white' : 'text-slate-300'} />
            </div>
            <div className="flex-1">
                <div className={`font-medium ${primary ? 'text-white' : 'text-slate-200'}`}>{label}</div>
                <div className={`text-xs ${primary ? 'text-white/70' : 'text-slate-400'}`}>{description}</div>
            </div>
            <ChevronRight size={18} className={primary ? 'text-white/50' : 'text-slate-500'} />
        </div>
    </button>
);

const SiteDashboard = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [dashboardData, setDashboardData] = useState(null);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            // Fetch site data
            const siteRes = await axios.get(`${API_BASE}/config/site`);
            const site = siteRes.data;

            // Fetch current schedule
            const schedulesRes = await axios.get(`${API_BASE}/schedule/site/${site.site_id}/versions`);
            const schedules = schedulesRes.data || [];
            const activeSchedule = schedules.find(s => s.status === 'Published') || schedules[0];

            // Fetch analytics
            let analytics = null;
            try {
                const analyticsRes = await axios.get(`${API_BASE}/analytics/summary?site_id=${site.site_id}`);
                analytics = analyticsRes.data;
            } catch (e) {
                // Analytics may not be available
            }

            setDashboardData({
                site,
                activeSchedule,
                scheduleCount: schedules.length,
                analytics
            });
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
            // Set mock data for demo
            setDashboardData({
                site: { name: 'Demo Mine Site', site_id: 'demo-site' },
                activeSchedule: { name: 'Week 1 Schedule', status: 'Draft' },
                scheduleCount: 3,
                analytics: null
            });
        } finally {
            setLoading(false);
        }
    };

    // Get current shift info
    const now = new Date();
    const hour = now.getHours();
    const currentShift = hour >= 6 && hour < 18 ? 'Day Shift' : 'Night Shift';
    const currentDate = now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {/* Header */}
            <div className="border-b border-slate-800 bg-slate-900/50">
                <div className="max-w-7xl mx-auto px-6 py-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">
                                {loading ? 'Loading...' : dashboardData?.site?.name || 'Site Dashboard'}
                            </h1>
                            <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                                <span className="flex items-center gap-1">
                                    <Calendar size={14} />
                                    {currentDate}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Clock size={14} />
                                    {currentShift}
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={fetchDashboardData}
                            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                            title="Refresh"
                        >
                            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* KPI Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <KPICard
                        title="Planned Tonnes Today"
                        value="45,200"
                        unit="t"
                        trend={2.5}
                        icon={Truck}
                        color="blue"
                    />
                    <KPICard
                        title="Actual vs Plan"
                        value="92"
                        unit="%"
                        trend={-3}
                        trendLabel="vs yesterday"
                        icon={TrendingUp}
                        color="emerald"
                    />
                    <KPICard
                        title="Quality Compliance"
                        value="96"
                        unit="%"
                        trend={1.2}
                        icon={BarChart3}
                        color="purple"
                    />
                    <KPICard
                        title="Active Resources"
                        value="12"
                        unit="/15"
                        icon={Factory}
                        color="amber"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left column - Schedule & Actions */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Active Schedule Card */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <FileText size={20} className="text-blue-400" />
                                Active Schedule
                            </h2>
                            {dashboardData?.activeSchedule ? (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-xl font-medium">{dashboardData.activeSchedule.name}</div>
                                            <div className="text-sm text-slate-400">
                                                Status: <span className={dashboardData.activeSchedule.status === 'Published' ? 'text-emerald-400' : 'text-amber-400'}>
                                                    {dashboardData.activeSchedule.status}
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => navigate('/app/planner')}
                                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            Open Planner
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700">
                                        <div>
                                            <div className="text-xs text-slate-500">Tasks</div>
                                            <div className="text-lg font-medium">45</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-slate-500">Horizon</div>
                                            <div className="text-lg font-medium">14 days</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-slate-500">Last Updated</div>
                                            <div className="text-lg font-medium">2h ago</div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-8 text-slate-500">
                                    No active schedule. Create one to get started.
                                </div>
                            )}
                        </div>

                        {/* Quick Actions */}
                        <div className="space-y-3">
                            <h2 className="text-lg font-semibold">Quick Actions</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <ActionButton
                                    icon={Play}
                                    label="Run Fast Pass"
                                    description="Quick optimization check"
                                    onClick={() => navigate('/app')}
                                    primary
                                />
                                <ActionButton
                                    icon={FileText}
                                    label="Create Scenario"
                                    description="Fork current schedule"
                                    onClick={() => navigate('/app')}
                                />
                                <ActionButton
                                    icon={BarChart3}
                                    label="View Reports"
                                    description="Production analytics"
                                    onClick={() => navigate('/app')}
                                />
                                <ActionButton
                                    icon={Settings}
                                    label="Site Settings"
                                    description="Configure resources"
                                    onClick={() => navigate('/app')}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Right column - Alerts & Status */}
                    <div className="space-y-6">
                        {/* Alerts */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <AlertTriangle size={20} className="text-amber-400" />
                                Alerts
                            </h2>
                            <div className="space-y-3">
                                <AlertCard
                                    severity="warning"
                                    title="ROM Stockpile High"
                                    message="Approaching 90% capacity. Consider increasing reclaim rate."
                                />
                                <AlertCard
                                    severity="info"
                                    title="Maintenance Window"
                                    message="EX-03 scheduled for maintenance tomorrow 06:00-14:00"
                                />
                            </div>
                        </div>

                        {/* Stockpile Summary */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Package size={20} className="text-emerald-400" />
                                Stockpiles
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-slate-400">ROM Stockpile</span>
                                        <span className="text-amber-400">85%</span>
                                    </div>
                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full" style={{ width: '85%' }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-slate-400">Product Coal</span>
                                        <span className="text-emerald-400">45%</span>
                                    </div>
                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" style={{ width: '45%' }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-slate-400">Reject</span>
                                        <span className="text-blue-400">30%</span>
                                    </div>
                                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full" style={{ width: '30%' }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SiteDashboard;
