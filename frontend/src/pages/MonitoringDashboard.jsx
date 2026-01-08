import React, { useState, useEffect } from 'react';
import SensorChart from '../components/monitoring/SensorChart';
import { monitoringAPI } from '../services/api';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';
import { AlertTriangle, Wind, Mountain, TrendingUp, Activity } from 'lucide-react';

const MonitoringDashboard = () => {
    const [activeTab, setActiveTab] = useState('slope');
    const [slopeAlerts, setSlopeAlerts] = useState([]);
    const [dustData, setDustData] = useState([]);
    const [loading, setLoading] = useState(true);
    const { currentSiteId, loading: siteLoading } = useSite();

    const loadSlopeAlerts = async () => {
        if (!currentSiteId) return;
        try {
            const response = await monitoringAPI.getSlopeAlerts(currentSiteId);
            setSlopeAlerts(response);
        } catch (error) {
            console.warn('Slope alerts API not available:', error);
            setSlopeAlerts([]);
        }
    };

    const loadDustData = async () => {
        if (!currentSiteId) return;
        try {
            const endDate = new Date().toISOString().split('T')[0];
            const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const response = await monitoringAPI.getDustExceedances(currentSiteId, startDate, endDate);

            // Transform data for chart
            if (Array.isArray(response) && response.length > 0) {
                setDustData(response.map(r => ({
                    time: new Date(r.measured_at).toLocaleDateString('en-US', { weekday: 'short' }),
                    pm10: r.pm10 || 0,
                    pm25: r.pm25 || 0
                })));
            } else {
                // Show empty state if no data
                setDustData([]);
            }
        } catch (error) {
            console.warn('Dust data API not available:', error);
            setDustData([]);
        }
    };

    useEffect(() => {
        if (currentSiteId) {
            setLoading(true);
            Promise.all([loadSlopeAlerts(), loadDustData()]).finally(() => setLoading(false));
        }
    }, [currentSiteId]);

    if (siteLoading) {
        return (
            <AppLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-slate-400">Loading site data...</div>
                </div>
            </AppLayout>
        );
    }

    return (
        <AppLayout>
            <div className="flex flex-col h-full">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <h2 className="text-xl font-bold text-white">Monitoring Dashboard</h2>
                    <p className="text-sm text-slate-400 mt-1">Geotechnical and environmental monitoring data</p>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'slope'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('slope')}
                        >
                            <Mountain size={16} />
                            Slope Stability
                        </button>
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'dust'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('dust')}
                        >
                            <Wind size={16} />
                            Dust Monitoring
                        </button>
                    </div>
                </div>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center h-64">
                            <div className="text-slate-400">Loading monitoring data...</div>
                        </div>
                    ) : activeTab === 'slope' ? (
                        <div className="space-y-6">
                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <AlertTriangle size={20} className="text-amber-400" />
                                    Active Slope Alerts
                                </h3>
                                {slopeAlerts.length === 0 ? (
                                    <div className="flex items-center justify-center py-12 text-slate-400">
                                        <div className="text-center">
                                            <Activity size={48} className="mx-auto mb-4 opacity-50" />
                                            <p>No active alerts. All prisms within thresholds.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {slopeAlerts.map((alert, idx) => (
                                            <div
                                                key={idx}
                                                className={`p-4 rounded-lg border ${alert.severity === 'critical'
                                                        ? 'bg-red-500/10 border-red-500/30 text-red-400'
                                                        : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                                                    }`}
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span className="font-medium">{alert.prism_name || `Prism ${idx + 1}`}</span>
                                                    <span className="text-sm uppercase">{alert.severity || 'warning'}</span>
                                                </div>
                                                <p className="text-sm mt-1 opacity-80">
                                                    Displacement: {alert.displacement_mm?.toFixed(1) || 'N/A'} mm
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                    <TrendingUp size={20} className="text-blue-400" />
                                    PM10 Levels (Last 7 Days)
                                </h3>
                                {dustData.length === 0 ? (
                                    <div className="flex items-center justify-center py-12 text-slate-400">
                                        <div className="text-center">
                                            <Wind size={48} className="mx-auto mb-4 opacity-50" />
                                            <p>No dust monitoring data available for this period.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <SensorChart
                                        title="PM10 Concentration"
                                        data={dustData}
                                        dataKey="pm10"
                                        color="#f59e0b"
                                        unit=" µg/m³"
                                    />
                                )}
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </AppLayout>
    );
};

export default MonitoringDashboard;
