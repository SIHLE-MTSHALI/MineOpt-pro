/**
 * MonitoringDashboard.jsx - Geotechnical & Environmental Monitoring
 * 
 * Features:
 * - Slope stability alerts
 * - Dust monitoring charts
 * - Threshold configuration
 * - Breadcrumb navigation
 * - Page animations
 */

import React, { useState, useEffect } from 'react';
import { Mountain, Wind, AlertTriangle, Settings, RefreshCw, Bell, Activity } from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';
import { monitoringAPI } from '../services/api';
import Breadcrumb from '../components/ui/Breadcrumb';
import AnimatedCard from '../components/ui/AnimatedCard';

// Alert severity badge
const SeverityBadge = ({ severity }) => {
    const config = {
        critical: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Critical' },
        warning: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Warning' },
        normal: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Normal' },
        ok: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'OK' }
    };

    const c = config[severity] || config.normal;
    return (
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
            {c.label}
        </span>
    );
};

// Simple chart component for dust data
const DustChart = ({ data }) => {
    if (!data || data.length === 0) {
        return (
            <div className="text-center py-8 text-slate-400">
                <Wind size={32} className="mx-auto mb-2 opacity-50" />
                <p>No dust data available</p>
            </div>
        );
    }

    const maxValue = Math.max(...data.map(d => d.value || 0), 100);

    return (
        <div className="h-48 flex items-end gap-1">
            {data.slice(-24).map((point, idx) => (
                <div
                    key={idx}
                    className="flex-1 bg-blue-500/50 rounded-t-sm transition-all hover:bg-blue-400/70"
                    style={{
                        height: `${Math.max(4, (point.value / maxValue) * 100)}%`,
                        animationDelay: `${idx * 20}ms`
                    }}
                    title={`${point.time || 'Time'}: ${point.value?.toFixed(1) || 0} µg/m³`}
                ></div>
            ))}
        </div>
    );
};

const MonitoringDashboard = () => {
    const [activeTab, setActiveTab] = useState('slope');
    const [slopeAlerts, setSlopeAlerts] = useState([]);
    const [dustData, setDustData] = useState([]);
    const [loading, setLoading] = useState(true);
    const { currentSiteId, loading: siteLoading } = useSite();

    useEffect(() => {
        if (currentSiteId) {
            loadMonitoringData();
        }
    }, [currentSiteId]);

    const loadMonitoringData = async () => {
        if (!currentSiteId) return;

        setLoading(true);
        try {
            // Load slope alerts
            try {
                const alerts = await monitoringAPI.getSlopeAlerts(currentSiteId);
                setSlopeAlerts(alerts || []);
            } catch (e) {
                console.warn('Could not load slope alerts:', e);
                setSlopeAlerts([]);
            }

            // Load dust data
            try {
                const endDate = new Date().toISOString();
                const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
                const dust = await monitoringAPI.getDustExceedances(currentSiteId, startDate, endDate);
                setDustData(dust || []);
            } catch (e) {
                console.warn('Could not load dust data:', e);
                setDustData([]);
            }
        } catch (error) {
            console.error('Failed to load monitoring data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (siteLoading) {
        return (
            <AppLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-slate-400 animate-pulse">Loading site data...</div>
                </div>
            </AppLayout>
        );
    }

    const tabs = [
        { id: 'slope', label: 'Slope Stability', icon: Mountain },
        { id: 'dust', label: 'Dust Monitoring', icon: Wind },
        { id: 'settings', label: 'Thresholds', icon: Settings }
    ];

    return (
        <AppLayout>
            <div className="flex flex-col h-full page-enter">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <Breadcrumb className="mb-3" />
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Activity className="text-purple-400" size={24} />
                                Monitoring
                            </h2>
                            <p className="text-sm text-slate-400 mt-1">Geotechnical stability and environmental monitoring</p>
                        </div>
                        <div className="flex items-center gap-3">
                            {slopeAlerts.filter(a => a.alert_status === 'critical' || a.alert_status === 'warning').length > 0 && (
                                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/20 border border-amber-500/30 rounded-lg">
                                    <Bell size={14} className="text-amber-400" />
                                    <span className="text-xs text-amber-400 font-medium">
                                        {slopeAlerts.filter(a => a.alert_status === 'critical' || a.alert_status === 'warning').length} Active Alerts
                                    </span>
                                </div>
                            )}
                            <button
                                onClick={loadMonitoringData}
                                disabled={loading}
                                className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2 disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                Refresh
                            </button>
                        </div>
                    </div>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all relative ${activeTab === tab.id
                                        ? 'text-purple-400'
                                        : 'text-slate-400 hover:text-slate-200'
                                    }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <tab.icon size={16} />
                                {tab.label}
                                {activeTab === tab.id && (
                                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400 rounded-t-full" />
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {activeTab === 'slope' && (
                        <div className="space-y-4">
                            <AnimatedCard delay={0}>
                                <AnimatedCard.Header>
                                    <AnimatedCard.Title icon={AlertTriangle}>Slope Stability Alerts</AnimatedCard.Title>
                                    <span className="text-xs text-slate-500">
                                        {slopeAlerts.length} prisms monitored
                                    </span>
                                </AnimatedCard.Header>

                                {loading ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="animate-pulse flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
                                                <div className="w-10 h-10 bg-slate-700 rounded-lg"></div>
                                                <div className="flex-1">
                                                    <div className="h-4 w-48 bg-slate-700 rounded mb-2"></div>
                                                    <div className="h-3 w-32 bg-slate-700 rounded"></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : slopeAlerts.length > 0 ? (
                                    <div className="space-y-3">
                                        {slopeAlerts.map((alert, idx) => (
                                            <div
                                                key={alert.prism_id || idx}
                                                className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
                                                style={{
                                                    animation: `slideUp 0.3s ease-out forwards`,
                                                    animationDelay: `${idx * 50}ms`,
                                                    opacity: 0
                                                }}
                                            >
                                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${alert.alert_status === 'critical' ? 'bg-red-500/20' :
                                                        alert.alert_status === 'warning' ? 'bg-amber-500/20' : 'bg-emerald-500/20'
                                                    }`}>
                                                    <Mountain size={18} className={
                                                        alert.alert_status === 'critical' ? 'text-red-400' :
                                                            alert.alert_status === 'warning' ? 'text-amber-400' : 'text-emerald-400'
                                                    } />
                                                </div>
                                                <div className="flex-1">
                                                    <div className="font-medium text-white">{alert.prism_name || `Prism ${idx + 1}`}</div>
                                                    <div className="text-xs text-slate-400 mt-1">
                                                        Displacement: {alert.total_displacement_mm?.toFixed(1) || 0} mm
                                                        {alert.velocity_mm_day && ` • Velocity: ${alert.velocity_mm_day.toFixed(2)} mm/day`}
                                                    </div>
                                                </div>
                                                <SeverityBadge severity={alert.alert_status} />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-slate-400">
                                        <Mountain size={48} className="mx-auto mb-4 opacity-50" />
                                        <p>No slope alerts at this time</p>
                                        <p className="text-xs text-slate-500 mt-1">All monitoring prisms are within normal parameters</p>
                                    </div>
                                )}
                            </AnimatedCard>
                        </div>
                    )}

                    {activeTab === 'dust' && (
                        <div className="space-y-4">
                            <AnimatedCard delay={0}>
                                <AnimatedCard.Header>
                                    <AnimatedCard.Title icon={Wind}>Dust Levels (24h)</AnimatedCard.Title>
                                    <span className="text-xs text-slate-500">PM10 concentrations</span>
                                </AnimatedCard.Header>

                                {loading ? (
                                    <div className="h-48 bg-slate-800/50 rounded-lg animate-pulse"></div>
                                ) : (
                                    <DustChart data={dustData} />
                                )}

                                <div className="mt-4 grid grid-cols-3 gap-4">
                                    <div className="bg-slate-800/50 rounded-lg p-3">
                                        <div className="text-xs text-slate-500">Current</div>
                                        <div className="text-lg font-medium text-white mt-1">
                                            {dustData.length > 0 ? `${dustData[dustData.length - 1]?.value?.toFixed(1) || 0} µg/m³` : '-'}
                                        </div>
                                    </div>
                                    <div className="bg-slate-800/50 rounded-lg p-3">
                                        <div className="text-xs text-slate-500">24h Average</div>
                                        <div className="text-lg font-medium text-white mt-1">
                                            {dustData.length > 0
                                                ? `${(dustData.reduce((sum, d) => sum + (d.value || 0), 0) / dustData.length).toFixed(1)} µg/m³`
                                                : '-'
                                            }
                                        </div>
                                    </div>
                                    <div className="bg-slate-800/50 rounded-lg p-3">
                                        <div className="text-xs text-slate-500">Exceedances</div>
                                        <div className="text-lg font-medium text-amber-400 mt-1">
                                            {dustData.filter(d => d.value > 50).length}
                                        </div>
                                    </div>
                                </div>
                            </AnimatedCard>
                        </div>
                    )}

                    {activeTab === 'settings' && (
                        <div className="space-y-4">
                            <AnimatedCard delay={0}>
                                <AnimatedCard.Header>
                                    <AnimatedCard.Title icon={Settings}>Alert Thresholds</AnimatedCard.Title>
                                </AnimatedCard.Header>

                                <div className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <label className="block text-sm text-slate-400 mb-2">Slope Displacement Warning (mm)</label>
                                            <input
                                                type="number"
                                                defaultValue={10}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <label className="block text-sm text-slate-400 mb-2">Slope Displacement Critical (mm)</label>
                                            <input
                                                type="number"
                                                defaultValue={25}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <label className="block text-sm text-slate-400 mb-2">Dust PM10 Warning (µg/m³)</label>
                                            <input
                                                type="number"
                                                defaultValue={50}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <label className="block text-sm text-slate-400 mb-2">Dust PM10 Critical (µg/m³)</label>
                                            <input
                                                type="number"
                                                defaultValue={100}
                                                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex justify-end pt-4">
                                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm font-medium transition-colors">
                                            Save Thresholds
                                        </button>
                                    </div>
                                </div>
                            </AnimatedCard>
                        </div>
                    )}
                </main>
            </div>
        </AppLayout>
    );
};

export default MonitoringDashboard;
