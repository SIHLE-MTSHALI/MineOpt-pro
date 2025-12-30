import React, { useState, useEffect } from 'react';
import Sidebar from '../components/ui/Sidebar';
import Viewport3D from '../components/spatial/Viewport3D';
import GanttChart from '../components/scheduler/GanttChart';
import axios from 'axios';

const PlannerWorkspace = () => {
    const [activeTab, setActiveTab] = useState('spatial');

    // Site Data State
    const [siteData, setSiteData] = useState({
        activityAreas: [],
        siteId: null,
        resources: [],
        activeScheduleId: null
    });

    const [loading, setLoading] = useState(false);
    const [notification, setNotification] = useState(null);

    // Fetch Data on Load
    useEffect(() => {
        fetchSiteData();
    }, []);

    const fetchSiteData = async () => {
        try {
            // 1. Get Sites
            const sitesRes = await axios.get('http://localhost:8000/config/sites');
            if (sitesRes.data.length > 0) {
                const site = sitesRes.data[0];
                const siteId = site.site_id;

                // 2. Get Resources for Site
                const resRes = await axios.get(`http://localhost:8000/config/resources?site_id=${siteId}`);

                // 3. Get Schedules for Site
                const schedRes = await axios.get(`http://localhost:8000/schedule/site/${siteId}/versions`);
                const activeScheduleId = schedRes.data.length > 0 ? schedRes.data[0].version_id : null;

                // 4. Get Calendar & Periods
                let sitePeriods = [];
                const calRes = await axios.get(`http://localhost:8000/calendar/site/${siteId}`);
                if (calRes.data.length > 0) {
                    const calId = calRes.data[0].calendar_id;
                    const perRes = await axios.get(`http://localhost:8000/calendar/${calId}/periods`);
                    sitePeriods = perRes.data;
                }

                console.log("DEBUG: SiteData Loaded", { siteId, resources: resRes.data, activeScheduleId, periods: sitePeriods });

                setSiteData({
                    siteId,
                    activityAreas: [], // Mocked for now (WP3)
                    stockpiles: [],
                    resources: resRes.data,
                    activeScheduleId,
                    periods: sitePeriods
                });
            } else {
                console.warn("DEBUG: No sites found.");
            }
        } catch (e) {
            console.error("Failed to fetch site data", e);
        }
    };

    const handleSeedData = async () => {
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/config/seed-demo-data');
            setNotification({ type: 'success', message: 'Demo Project Seeded! Reloading...' });
            setTimeout(() => window.location.reload(), 1500);
        } catch (e) {
            setNotification({ type: 'error', message: 'Failed to seed data.' });
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

            <main className="flex-1 flex flex-col min-w-0">
                {/* Top Bar */}
                <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-950/50">
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-slate-400">Project:</span>
                        <span className="font-medium text-white">MineOpt Demo</span>
                        <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-500 border border-blue-500/30">ENTERPRISE</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        {/* Seed Button for Verification */}
                        <button
                            onClick={handleSeedData}
                            disabled={loading}
                            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded transition-colors mr-2"
                        >
                            {loading ? 'Seeding...' : 'Initialize Demo Data'}
                        </button>

                        <button className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded font-medium transition-colors">
                            Save Changes
                        </button>
                    </div>
                </header>

                {/* Workspace Content */}
                <div className="flex-1 relative">
                    {/* Notification Toast */}
                    {notification && (
                        <div className={`absolute top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded shadow-lg z-50 text-sm font-medium ${notification.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                            {notification.message}
                        </div>
                    )}

                    {activeTab === 'spatial' && (
                        <div className="h-full w-full">
                            <Viewport3D siteData={siteData} />
                        </div>
                    )}

                    {activeTab === 'gantt' && (
                        <GanttChart
                            siteId={siteData.siteId}
                            resources={siteData.resources}
                            scheduleVersionId={siteData.activeScheduleId}
                            periods={siteData.periods}
                        />
                    )}

                    {activeTab !== 'spatial' && activeTab !== 'gantt' && (
                        <div className="flex items-center justify-center h-full text-slate-500">
                            <div className="text-center">
                                <h2 className="text-xl font-semibold mb-2">Module Under Construction</h2>
                                <p>Work Package for {activeTab} is pending.</p>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            {/* Properties Panel (Right Side) - Placeholder for now */}
            {activeTab === 'spatial' && (
                <aside className="w-80 border-l border-slate-800 bg-slate-950 p-4 hidden xl:block">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Properties</h3>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-900 rounded border border-slate-800">
                            <p className="text-xs text-slate-500 mb-1">Selected Object</p>
                            <p className="text-sm font-medium">None</p>
                        </div>
                        <div className="p-3 bg-slate-900 rounded border border-slate-800">
                            <p className="text-xs text-slate-500 mb-1">Total Blocks</p>
                            <p className="text-sm font-medium">0 (Database Empty)</p>
                            <p className="text-xs text-slate-500 mt-2">Click "Initialize Demo Data" above to load.</p>
                        </div>
                    </div>
                </aside>
            )}
        </div>
    );
};

export default PlannerWorkspace;
