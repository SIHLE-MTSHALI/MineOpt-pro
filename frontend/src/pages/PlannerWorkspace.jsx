import React, { useState, useEffect } from 'react';
import Sidebar from '../components/ui/Sidebar';
import ErrorBoundary from '../components/ui/ErrorBoundary';
import Viewport3D from '../components/spatial/Viewport3D';
import GanttChart from '../components/scheduler/GanttChart';
import ScheduleControl from '../components/scheduler/ScheduleControl';
import Dashboard from '../components/reporting/Dashboard';
import ReportingModule from '../components/reporting/ReportingModule';
import Spatial3DToolbar from '../components/spatial/Spatial3DToolbar';
import FlowEditor from '../components/flow/FlowEditor';
import QualitySpecs from '../components/quality/QualitySpecs';
import StockpileManager from '../components/stockpile/StockpileManager';
import WashPlantConfig from '../components/washplant/WashPlantConfig';
import GeologyViewer from '../components/geology/GeologyViewer';
import SettingsPanel from '../components/settings/SettingsPanel';
// New module imports
import HaulCycleDashboard from '../components/fleet/HaulCycleDashboard';
import BlastPatternDesigner from '../components/drill-blast/BlastPatternDesigner';
import ShiftHandoverForm from '../components/operations/ShiftHandoverForm';
import SlopeMonitoringPanel from '../components/geotech/SlopeMonitoringPanel';
import DustMonitoringDashboard from '../components/environmental/DustMonitoringDashboard';
import TerrainImportPanel from '../components/import/TerrainImportPanel';
import ExternalIdMappingUI from '../components/integration/ExternalIdMappingUI';
import axios from 'axios';


const PlannerWorkspace = () => {
    // Default to 'reporting' tab to avoid Three.js/WebGL crash on initial load
    const [activeTab, setActiveTab] = useState('reporting');

    // Site Data State
    const [siteData, setSiteData] = useState({
        activityAreas: [],
        siteId: null,
        resources: [],
        activeScheduleId: null,
        periods: [],
        versions: [],
        activeTasks: []
    });

    const [selectedBlock, setSelectedBlock] = useState(null);
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

                // 2b. Get Activity Areas (Blocks)
                let areas = [];
                try {
                    const areasRes = await axios.get(`http://localhost:8000/config/activity-areas?site_id=${siteId}`);
                    areas = areasRes.data;
                } catch (e) { console.warn("Activity Areas endpoint missing"); }

                // 3. Get Schedules for Site (Versions)
                let versions = [];
                let activeScheduleId = null;
                try {
                    const schedRes = await axios.get(`http://localhost:8000/schedule/site/${siteId}/versions`);
                    versions = schedRes.data;
                    activeScheduleId = versions.length > 0 ? versions[0].version_id : null;
                } catch (e) { console.warn("Schedule versions endpoint missing"); }

                // 3b. Get Flow Network Nodes (Stockpiles, Plants, Dumps)
                let flowNodes = [];
                try {
                    const nodesRes = await axios.get(`http://localhost:8000/config/network-nodes?site_id=${siteId}`);
                    flowNodes = nodesRes.data;
                } catch (e) { console.warn("Network Nodes fetch failed"); }

                // 4. Get Calendar & Periods
                let sitePeriods = [];
                try {
                    const calRes = await axios.get(`http://localhost:8000/calendar/site/${siteId}`);
                    if (calRes.data.length > 0) {
                        const calId = calRes.data[0].calendar_id;
                        const perRes = await axios.get(`http://localhost:8000/calendar/${calId}/periods`);
                        sitePeriods = perRes.data;
                    }
                } catch (e) { console.warn("Calendar/Periods endpoint missing"); }

                // 5. Get Tasks for Simulation (active schedule)
                let tasks = [];
                if (activeScheduleId) {
                    try {
                        const tasksRes = await axios.get(`http://localhost:8000/schedule/versions/${activeScheduleId}/tasks`);
                        tasks = tasksRes.data;
                    } catch (e) { console.warn("Tasks fetch failed"); }
                }

                console.log("DEBUG: SiteData Loaded", { siteId, resources: resRes.data, activeScheduleId, periods: sitePeriods, versions, tasks });

                setSiteData({
                    siteId,
                    activityAreas: areas,
                    flowNodes: flowNodes,
                    resources: resRes.data,
                    activeScheduleId,
                    periods: sitePeriods,
                    versions: versions,
                    activeTasks: tasks
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

    const handleAddTask = async () => {
        if (!selectedBlock || !siteData.activeScheduleId || siteData.periods.length === 0) return;

        try {
            // Find a resource (Excavator)
            const excavator = siteData.resources.find(r => r.resource_type === 'Excavator');
            const defaultResId = excavator ? excavator.resource_id : siteData.resources[0]?.resource_id;

            await axios.post(`http://localhost:8000/schedule/versions/${siteData.activeScheduleId}/tasks`, {
                schedule_version_id: siteData.activeScheduleId,
                resource_id: defaultResId,
                activity_id: selectedBlock.activity_id, // Assuming block has activity_id
                period_id: siteData.periods[0].period_id, // Default to first period
                activity_area_id: selectedBlock.area_id,
                planned_quantity: 1000 // Default quantity
            });
            setNotification({ type: 'success', message: 'Task Added to Schedule!' });
        } catch (e) {
            console.error("Add Task Failed", e);
            setNotification({ type: 'error', message: 'Failed to add task.' });
        }
    };

    const handleCreateScenario = async () => {
        const name = window.prompt("Enter name for NEW Scenario (Fork):");
        if (!name) return;

        setLoading(true);
        try {
            // Call Fork Endpoint
            // We fork the CURRENT active schedule
            if (!siteData.activeScheduleId) {
                alert("No base schedule to fork. Please seed data first.");
                setLoading(false);
                return;
            }

            const res = await axios.post(`http://localhost:8000/schedule/versions/${siteData.activeScheduleId}/fork?new_name=${encodeURIComponent(name)}`);

            // Refresh Versions
            const schedRes = await axios.get(`http://localhost:8000/schedule/site/${siteData.siteId}/versions`);

            setSiteData(prev => ({
                ...prev,
                versions: schedRes.data,
                // Switch to new fork
                activeScheduleId: res.data.version_id
            }));

            setNotification({ type: 'success', message: `Scenario '${name}' Created!` });
            // Reload to fetch the tasks for this new version
            // For MVP reload is easiest to ensure state consistency
            setTimeout(() => window.location.reload(), 1000);

        } catch (e) {
            console.error(e);
            setNotification({ type: 'error', message: 'Failed to fork scenario.' });
        } finally {
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
                        <span className="text-sm text-slate-400">Scenario:</span>

                        <select
                            value={siteData.activeScheduleId || ""}
                            onChange={(e) => setSiteData(prev => ({ ...prev, activeScheduleId: e.target.value }))}
                            className="bg-slate-800 border border-slate-700 text-white text-sm rounded px-3 py-1 focus:outline-none focus:border-blue-500"
                        >
                            {siteData.versions?.map(v => (
                                <option key={v.version_id} value={v.version_id}>{v.name} ({v.status})</option>
                            ))}
                        </select>

                        <button
                            onClick={handleCreateScenario}
                            className="p-1 px-2 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 transition-colors"
                        >
                            Fork / Copy
                        </button>
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

                        <button
                            onClick={async () => {
                                if (!siteData.activeScheduleId) return;
                                setLoading(true);
                                try {
                                    const res = await axios.post('http://localhost:8000/optimization/run', {
                                        site_id: siteData.siteId,
                                        schedule_version_id: siteData.activeScheduleId
                                    });
                                    setNotification({ type: 'success', message: res.data.message });
                                    // Refresh Gantt if active
                                    // Note: GanttChart component fetches its own data, we might need to trigger a refresh via key or context.
                                    // For now, reloading page is nuclear but safe for MVP.
                                    setTimeout(() => window.location.reload(), 1500);
                                } catch (e) {
                                    setNotification({ type: 'error', message: 'Optimization Failed' });
                                } finally {
                                    setLoading(false);
                                }
                            }}
                            className="px-3 py-1.5 text-sm bg-purple-600 hover:bg-purple-500 text-white rounded font-medium transition-colors flex items-center"
                        >
                            <span className="mr-1">⚡</span> Auto-Schedule
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
                        <ErrorBoundary componentName="3D Spatial View">
                            <div className="h-full w-full relative">
                                <Spatial3DToolbar
                                    siteId={siteData.siteId}
                                    surfaceVersions={[]}
                                    currentSurfaceId={null}
                                    onSurfaceChange={() => { }}
                                    onCompare={() => { }}
                                />
                                <Viewport3D
                                    siteData={siteData}
                                    onBlockSelect={setSelectedBlock}
                                    selectedBlock={selectedBlock}
                                    flowNodes={siteData.flowNodes}
                                />
                            </div>
                        </ErrorBoundary>
                    )}

                    {activeTab === 'gantt' && (
                        <ErrorBoundary componentName="Gantt Chart">
                            <GanttChart
                                siteId={siteData.siteId}
                                resources={siteData.resources || []}
                                scheduleVersionId={siteData.activeScheduleId}
                                periods={siteData.periods || []}
                            />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'schedule-control' && (
                        <ScheduleControl
                            siteId={siteData.siteId}
                            scheduleVersionId={siteData.activeScheduleId}
                        />
                    )}

                    {activeTab === 'reporting' && (
                        <ReportingModule
                            scheduleVersionId={siteData.activeScheduleId}
                            siteId={siteData.siteId}
                        />
                    )}

                    {activeTab === 'flow-editor' && (
                        <FlowEditor
                            networkId={siteData.siteId}
                            onSave={(data) => console.log('Saving flow network:', data)}
                        />
                    )}

                    {activeTab === 'product-specs' && (
                        <QualitySpecs siteId={siteData.siteId} />
                    )}

                    {activeTab === 'data' && (
                        <StockpileManager siteId={siteData.siteId} />
                    )}

                    {activeTab === 'resources' && (
                        <WashPlantConfig siteId={siteData.siteId} />
                    )}

                    {activeTab === 'geology' && (
                        <GeologyViewer siteId={siteData.siteId} />
                    )}

                    {activeTab === 'settings' && (
                        <SettingsPanel siteId={siteData.siteId} />
                    )}

                    {/* New Module Tabs */}
                    {activeTab === 'fleet' && (
                        <ErrorBoundary componentName="Fleet Management">
                            <HaulCycleDashboard siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'drill-blast' && (
                        <ErrorBoundary componentName="Drill & Blast">
                            <BlastPatternDesigner siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'shift-ops' && (
                        <ErrorBoundary componentName="Shift Operations">
                            <ShiftHandoverForm siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'geotech' && (
                        <ErrorBoundary componentName="Slope Monitoring">
                            <SlopeMonitoringPanel siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'environment' && (
                        <ErrorBoundary componentName="Environmental Monitoring">
                            <DustMonitoringDashboard siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'import' && (
                        <ErrorBoundary componentName="Data Import">
                            <TerrainImportPanel siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {activeTab === 'integrations' && (
                        <ErrorBoundary componentName="Integrations">
                            <ExternalIdMappingUI siteId={siteData.siteId} />
                        </ErrorBoundary>
                    )}

                    {!['spatial', 'gantt', 'reporting', 'flow-editor', 'product-specs', 'data', 'resources', 'geology', 'settings', 'schedule-control', 'fleet', 'drill-blast', 'shift-ops', 'geotech', 'environment', 'import', 'integrations'].includes(activeTab) && (
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
                            <p className="text-sm font-bold text-blue-400">
                                {selectedBlock ? (selectedBlock.name || selectedBlock.id) : "None"}
                            </p>
                            {selectedBlock && (
                                <div className="mt-2 space-y-1 text-xs text-slate-400">
                                    <div>ID: {(selectedBlock.area_id || selectedBlock.id).toString().substring(0, 8)}...</div>
                                    <div>Material: {selectedBlock.slice_states?.[0]?.material || "Unknown"}</div>
                                    <div>Quantity: {selectedBlock.slice_states?.[0]?.quantity || 0}t</div>
                                </div>
                            )}
                        </div>

                        {selectedBlock && selectedBlock.area_id && (
                            <button
                                onClick={handleAddTask}
                                className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-sm transition-colors"
                            >
                                + Add to Schedule
                            </button>
                        )}

                        {selectedBlock && !selectedBlock.area_id && (
                            <div className="text-xs text-amber-500 p-2 bg-amber-500/10 border border-amber-500/20 rounded">
                                This is a preview block. Initialize Demo Data to create real scheduleable blocks.
                            </div>
                        )}

                        <div className="p-3 bg-slate-900 rounded border border-slate-800">
                            <p className="text-xs text-slate-500 mb-1">Total Blocks</p>
                            <p className="text-sm font-medium">{siteData.activityAreas.length} (Loaded)</p>
                        </div>
                    </div>
                </aside>
            )}
        </div>
    );
};

export default PlannerWorkspace;
