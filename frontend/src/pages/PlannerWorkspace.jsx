/**
 * PlannerWorkspace.jsx - Unified Planning Workspace
 * 
 * Main planning interface providing:
 * - URL-based tab navigation with query parameters
 * - Centralized API integration
 * - Multi-module workspace with sidebar navigation
 * - Error boundaries for stability
 * - Real-time data updates
 * 
 * @module pages/PlannerWorkspace
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useSite } from '../context/SiteContext';
import { useToast } from '../context/ToastContext';

// API Service - Centralized
import {
    configAPI,
    calendarAPI,
    scheduleAPI,
    optimizationAPI
} from '../services/api';

// Layout Components
import { AppLayout } from '../components/layout/AppLayout';
import ErrorBoundary from '../components/ui/ErrorBoundary';
import Breadcrumb from '../components/ui/Breadcrumb';

// Planning Module Components
import Viewport3D from '../components/spatial/Viewport3D';
import GanttChart from '../components/scheduler/GanttChart';
import ScheduleControl from '../components/scheduler/ScheduleControl';
import ReportingModule from '../components/reporting/ReportingModule';
import Spatial3DToolbar from '../components/spatial/Spatial3DToolbar';
import FlowEditor from '../components/flow/FlowEditor';
import QualitySpecs from '../components/quality/QualitySpecs';
import StockpileManager from '../components/stockpile/StockpileManager';
import WashPlantConfig from '../components/washplant/WashPlantConfig';
import GeologyViewer from '../components/geology/GeologyViewer';
import SettingsPanel from '../components/settings/SettingsPanel';

// Operations Module Components
import HaulCycleDashboard from '../components/fleet/HaulCycleDashboard';
import BlastPatternDesigner from '../components/drill-blast/BlastPatternDesigner';
import ShiftHandoverForm from '../components/operations/ShiftHandoverForm';
import SlopeMonitoringPanel from '../components/geotech/SlopeMonitoringPanel';
import DustMonitoringDashboard from '../components/environmental/DustMonitoringDashboard';

// Data & Integration Components
import TerrainImportPanel from '../components/import/TerrainImportPanel';
import ExternalIdMappingUI from '../components/integration/ExternalIdMappingUI';

// Icons
import { RefreshCw, Zap, GitBranch, Save, AlertCircle } from 'lucide-react';

// =============================================================================
// CONSTANTS
// =============================================================================

/**
 * Valid tab identifiers for the workspace
 * Used for URL validation and navigation
 */
const VALID_TABS = [
    'spatial',
    'gantt',
    'schedule-control',
    'reporting',
    'flow-editor',
    'product-specs',
    'data',
    'resources',
    'geology',
    'settings',
    'fleet',
    'drill-blast',
    'shift-ops',
    'geotech',
    'environment',
    'import',
    'integrations'
];

/** Default tab when none specified */
const DEFAULT_TAB = 'reporting';

/** Tabs that require 3D rendering (slower to load) */
const HEAVY_TABS = ['spatial'];

// =============================================================================
// COMPONENT
// =============================================================================

const PlannerWorkspace = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const { currentSiteId, currentSite, loading: siteLoading } = useSite();
    const { showToast } = useToast();

    // ==========================================================================
    // URL-BASED TAB MANAGEMENT
    // ==========================================================================

    /**
     * Get active tab from URL query params with validation
     */
    const activeTab = useMemo(() => {
        const tabParam = searchParams.get('tab');
        if (tabParam && VALID_TABS.includes(tabParam)) {
            return tabParam;
        }
        return DEFAULT_TAB;
    }, [searchParams]);

    /**
     * Update URL when tab changes
     * @param {string} newTab - Tab identifier
     */
    const setActiveTab = useCallback((newTab) => {
        if (VALID_TABS.includes(newTab)) {
            setSearchParams({ tab: newTab }, { replace: true });
        }
    }, [setSearchParams]);

    // ==========================================================================
    // SITE DATA STATE
    // ==========================================================================

    const [siteData, setSiteData] = useState({
        activityAreas: [],
        flowNodes: [],
        resources: [],
        periods: [],
        versions: [],
        activeScheduleId: null,
        activeTasks: []
    });

    const [selectedBlock, setSelectedBlock] = useState(null);
    const [loading, setLoading] = useState(false);
    const [dataError, setDataError] = useState(null);
    const [lastRefresh, setLastRefresh] = useState(null);

    // ==========================================================================
    // DATA FETCHING
    // ==========================================================================

    /**
     * Fetch all site data in parallel for performance
     */
    const fetchSiteData = useCallback(async () => {
        if (!currentSiteId) {
            console.warn('[PlannerWorkspace] No site selected');
            return;
        }

        setLoading(true);
        setDataError(null);

        try {
            // Parallel fetch for better performance
            const [
                resources,
                activityAreas,
                flowNodes,
                calendars,
                versions
            ] = await Promise.allSettled([
                configAPI.getResources(currentSiteId),
                configAPI.getActivityAreas(currentSiteId),
                configAPI.getNetworkNodes(currentSiteId),
                calendarAPI.getCalendars(currentSiteId),
                scheduleAPI.getVersions(currentSiteId)
            ]);

            // Extract results, handling failures gracefully
            const resourcesData = resources.status === 'fulfilled' ? resources.value : [];
            const areasData = activityAreas.status === 'fulfilled' ? activityAreas.value : [];
            const nodesData = flowNodes.status === 'fulfilled' ? flowNodes.value : [];
            const calendarsData = calendars.status === 'fulfilled' ? calendars.value : [];
            const versionsData = versions.status === 'fulfilled' ? versions.value : [];

            // Get periods if calendar exists
            let periodsData = [];
            if (calendarsData.length > 0) {
                try {
                    periodsData = await calendarAPI.getPeriods(calendarsData[0].calendar_id);
                } catch (err) {
                    console.warn('[PlannerWorkspace] Failed to fetch periods:', err.message);
                }
            }

            // Determine active schedule
            const activeVersion = versionsData.find(v => v.status === 'active') || versionsData[0];
            const activeScheduleId = activeVersion?.version_id || null;

            // Fetch tasks for active schedule
            let tasksData = [];
            if (activeScheduleId) {
                try {
                    tasksData = await scheduleAPI.getTasks(activeScheduleId);
                } catch (err) {
                    console.warn('[PlannerWorkspace] Failed to fetch tasks:', err.message);
                }
            }

            // Update state
            setSiteData({
                resources: resourcesData,
                activityAreas: areasData,
                flowNodes: nodesData,
                periods: periodsData,
                versions: versionsData,
                activeScheduleId,
                activeTasks: tasksData
            });

            setLastRefresh(new Date());

            // Log any partial failures for debugging
            const failures = [resources, activityAreas, flowNodes, calendars, versions]
                .filter(r => r.status === 'rejected');
            if (failures.length > 0) {
                console.warn('[PlannerWorkspace] Some data fetch operations failed:', failures);
            }

        } catch (err) {
            console.error('[PlannerWorkspace] Critical error fetching site data:', err);
            setDataError(err.message || 'Failed to load site data');
            showToast({
                type: 'error',
                message: 'Failed to load workspace data. Some features may be unavailable.',
                duration: 5000
            });
        } finally {
            setLoading(false);
        }
    }, [currentSiteId, showToast]);

    // Fetch data when site changes
    useEffect(() => {
        if (currentSiteId) {
            fetchSiteData();
        }
    }, [currentSiteId, fetchSiteData]);

    // ==========================================================================
    // SCHEDULE MANAGEMENT
    // ==========================================================================

    /**
     * Change active schedule version
     * @param {string} versionId - Schedule version to activate
     */
    const handleScheduleChange = useCallback(async (versionId) => {
        if (versionId === siteData.activeScheduleId) return;

        setLoading(true);
        try {
            const tasks = await scheduleAPI.getTasks(versionId);
            setSiteData(prev => ({
                ...prev,
                activeScheduleId: versionId,
                activeTasks: tasks
            }));
            showToast({
                type: 'success',
                message: 'Schedule version changed successfully'
            });
        } catch (err) {
            console.error('[PlannerWorkspace] Failed to change schedule:', err);
            showToast({
                type: 'error',
                message: 'Failed to switch schedule version'
            });
        } finally {
            setLoading(false);
        }
    }, [siteData.activeScheduleId, showToast]);

    /**
     * Fork current schedule to create new scenario
     */
    const handleCreateScenario = useCallback(async () => {
        const name = window.prompt('Enter name for NEW Scenario (Fork):');
        if (!name?.trim()) return;

        if (!siteData.activeScheduleId) {
            showToast({
                type: 'warning',
                message: 'No base schedule to fork. Please seed data first.'
            });
            return;
        }

        setLoading(true);
        try {
            const result = await scheduleAPI.forkVersion(siteData.activeScheduleId, name.trim());

            // Refresh versions list
            const versions = await scheduleAPI.getVersions(currentSiteId);
            const tasks = await scheduleAPI.getTasks(result.version_id);

            setSiteData(prev => ({
                ...prev,
                versions,
                activeScheduleId: result.version_id,
                activeTasks: tasks
            }));

            showToast({
                type: 'success',
                message: `Scenario "${name}" created successfully!`
            });
        } catch (err) {
            console.error('[PlannerWorkspace] Failed to fork scenario:', err);
            showToast({
                type: 'error',
                message: 'Failed to create scenario. Please try again.'
            });
        } finally {
            setLoading(false);
        }
    }, [siteData.activeScheduleId, currentSiteId, showToast]);

    /**
     * Run schedule optimization
     */
    const handleRunOptimization = useCallback(async () => {
        if (!currentSiteId || !siteData.activeScheduleId) {
            showToast({
                type: 'warning',
                message: 'Please select a site and schedule first.'
            });
            return;
        }

        setLoading(true);
        try {
            const result = await optimizationAPI.runOptimization(
                currentSiteId,
                siteData.activeScheduleId
            );

            // Refresh tasks after optimization
            const tasks = await scheduleAPI.getTasks(siteData.activeScheduleId);
            setSiteData(prev => ({
                ...prev,
                activeTasks: tasks
            }));

            showToast({
                type: 'success',
                message: result.message || 'Optimization completed successfully!'
            });
        } catch (err) {
            console.error('[PlannerWorkspace] Optimization failed:', err);
            showToast({
                type: 'error',
                message: 'Optimization failed. Please check constraints and try again.'
            });
        } finally {
            setLoading(false);
        }
    }, [currentSiteId, siteData.activeScheduleId, showToast]);

    /**
     * Seed demo data
     */
    const handleSeedData = useCallback(async () => {
        setLoading(true);
        try {
            const result = await configAPI.seedDemoData();
            showToast({
                type: 'success',
                message: `Demo data seeded! ${result.sites_created || 0} sites, ${result.equipment_created || 0} equipment created.`
            });
            // Refresh page to load new data
            setTimeout(() => window.location.reload(), 1500);
        } catch (err) {
            console.error('[PlannerWorkspace] Failed to seed data:', err);
            showToast({
                type: 'error',
                message: 'Failed to seed demo data. Please try again.'
            });
            setLoading(false);
        }
    }, [showToast]);

    /**
     * Add task from selected block
     */
    const handleAddTask = useCallback(async () => {
        if (!selectedBlock || !siteData.activeScheduleId || siteData.periods.length === 0) {
            showToast({
                type: 'warning',
                message: 'Please select a block, schedule, and ensure periods exist.'
            });
            return;
        }

        try {
            const excavator = siteData.resources.find(r =>
                r.resource_type === 'Excavator' || r.resource_type === 'excavator'
            );
            const defaultResId = excavator?.resource_id || siteData.resources[0]?.resource_id;

            if (!defaultResId) {
                showToast({
                    type: 'warning',
                    message: 'No resources available. Please add equipment first.'
                });
                return;
            }

            await scheduleAPI.createTask(siteData.activeScheduleId, {
                resource_id: defaultResId,
                activity_id: selectedBlock.activity_id,
                period_id: siteData.periods[0].period_id,
                activity_area_id: selectedBlock.area_id,
                planned_quantity: 1000
            });

            // Refresh tasks
            const tasks = await scheduleAPI.getTasks(siteData.activeScheduleId);
            setSiteData(prev => ({
                ...prev,
                activeTasks: tasks
            }));

            showToast({
                type: 'success',
                message: 'Task added to schedule!'
            });
        } catch (err) {
            console.error('[PlannerWorkspace] Failed to add task:', err);
            showToast({
                type: 'error',
                message: 'Failed to add task. Please try again.'
            });
        }
    }, [selectedBlock, siteData, showToast]);

    // ==========================================================================
    // RENDER HELPERS
    // ==========================================================================

    /**
     * Get breadcrumb items based on active tab
     */
    const breadcrumbItems = useMemo(() => {
        const tabLabels = {
            'spatial': '3D Spatial View',
            'gantt': 'Gantt Schedule',
            'schedule-control': 'Schedule Control',
            'reporting': 'Reports & Analytics',
            'flow-editor': 'Flow Network',
            'product-specs': 'Product Specs',
            'data': 'Stockpiles',
            'resources': 'Wash Plant',
            'geology': 'Geology',
            'settings': 'Settings',
            'fleet': 'Fleet Management',
            'drill-blast': 'Drill & Blast',
            'shift-ops': 'Shift Operations',
            'geotech': 'Slope Stability',
            'environment': 'Environment',
            'import': 'Import Data',
            'integrations': 'Integrations'
        };

        return [
            { label: 'Planning', path: '/app/planner' },
            { label: tabLabels[activeTab] || activeTab }
        ];
    }, [activeTab]);

    /**
     * Render the active tab content
     */
    const renderTabContent = () => {
        const commonProps = {
            siteId: currentSiteId,
            scheduleVersionId: siteData.activeScheduleId
        };

        switch (activeTab) {
            case 'spatial':
                return (
                    <ErrorBoundary componentName="3D Spatial View">
                        <div className="h-full w-full relative">
                            <Spatial3DToolbar
                                siteId={currentSiteId}
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
                );

            case 'gantt':
                return (
                    <ErrorBoundary componentName="Gantt Chart">
                        <GanttChart
                            {...commonProps}
                            resources={siteData.resources}
                            periods={siteData.periods}
                        />
                    </ErrorBoundary>
                );

            case 'schedule-control':
                return <ScheduleControl {...commonProps} />;

            case 'reporting':
                return <ReportingModule {...commonProps} />;

            case 'flow-editor':
                return (
                    <FlowEditor
                        networkId={currentSiteId}
                        onSave={(data) => {
                            configAPI.saveFlowNetwork(currentSiteId, data)
                                .then(() => showToast({ type: 'success', message: 'Flow network saved!' }))
                                .catch(() => showToast({ type: 'error', message: 'Failed to save flow network' }));
                        }}
                    />
                );

            case 'product-specs':
                return <QualitySpecs siteId={currentSiteId} />;

            case 'data':
                return <StockpileManager siteId={currentSiteId} />;

            case 'resources':
                return <WashPlantConfig siteId={currentSiteId} />;

            case 'geology':
                return <GeologyViewer siteId={currentSiteId} />;

            case 'settings':
                return <SettingsPanel siteId={currentSiteId} />;

            case 'fleet':
                return (
                    <ErrorBoundary componentName="Fleet Management">
                        <HaulCycleDashboard siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'drill-blast':
                return (
                    <ErrorBoundary componentName="Drill & Blast">
                        <BlastPatternDesigner siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'shift-ops':
                return (
                    <ErrorBoundary componentName="Shift Operations">
                        <ShiftHandoverForm siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'geotech':
                return (
                    <ErrorBoundary componentName="Slope Monitoring">
                        <SlopeMonitoringPanel siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'environment':
                return (
                    <ErrorBoundary componentName="Environmental Monitoring">
                        <DustMonitoringDashboard siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'import':
                return (
                    <ErrorBoundary componentName="Data Import">
                        <TerrainImportPanel siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            case 'integrations':
                return (
                    <ErrorBoundary componentName="Integrations">
                        <ExternalIdMappingUI siteId={currentSiteId} />
                    </ErrorBoundary>
                );

            default:
                return (
                    <div className="flex items-center justify-center h-full text-slate-500">
                        <div className="text-center">
                            <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <h2 className="text-xl font-semibold mb-2">Module Not Found</h2>
                            <p>The requested module "{activeTab}" is not available.</p>
                        </div>
                    </div>
                );
        }
    };

    // ==========================================================================
    // LOADING STATE
    // ==========================================================================

    if (siteLoading) {
        return (
            <AppLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                        <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
                        <p className="text-slate-400">Loading site data...</p>
                    </div>
                </div>
            </AppLayout>
        );
    }

    // ==========================================================================
    // MAIN RENDER
    // ==========================================================================

    return (
        <AppLayout>
            <div className="flex flex-col h-full">
                {/* Top Header Bar */}
                <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-950/50 flex-shrink-0">
                    <div className="flex items-center space-x-4">
                        {/* Breadcrumb */}
                        <Breadcrumb items={breadcrumbItems} />

                        <div className="w-px h-6 bg-slate-700" />

                        {/* Scenario Selector */}
                        <div className="flex items-center space-x-2">
                            <span className="text-xs text-slate-500">Scenario:</span>
                            <select
                                value={siteData.activeScheduleId || ''}
                                onChange={(e) => handleScheduleChange(e.target.value)}
                                disabled={loading || siteData.versions.length === 0}
                                className="bg-slate-800 border border-slate-700 text-white text-sm rounded px-3 py-1 focus:outline-none focus:border-blue-500 disabled:opacity-50 min-w-[150px]"
                            >
                                {siteData.versions.length === 0 ? (
                                    <option value="">No schedules</option>
                                ) : (
                                    siteData.versions.map(v => (
                                        <option key={v.version_id} value={v.version_id}>
                                            {v.name} ({v.status})
                                        </option>
                                    ))
                                )}
                            </select>

                            <button
                                onClick={handleCreateScenario}
                                disabled={loading || !siteData.activeScheduleId}
                                className="p-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 transition-colors disabled:opacity-50 flex items-center gap-1"
                                title="Fork current scenario"
                            >
                                <GitBranch size={14} />
                                Fork
                            </button>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2">
                        {/* Refresh Button */}
                        <button
                            onClick={fetchSiteData}
                            disabled={loading}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors disabled:opacity-50"
                            title={lastRefresh ? `Last refresh: ${lastRefresh.toLocaleTimeString()}` : 'Refresh data'}
                        >
                            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        </button>

                        {/* Seed Data Button */}
                        <button
                            onClick={handleSeedData}
                            disabled={loading}
                            className="px-3 py-1.5 text-xs bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-600/30 rounded transition-colors disabled:opacity-50"
                        >
                            {loading ? 'Seeding...' : 'Seed Demo Data'}
                        </button>

                        {/* Save Changes */}
                        <button
                            disabled={loading}
                            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 text-white rounded font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
                        >
                            <Save size={14} />
                            Save
                        </button>

                        {/* Auto-Schedule */}
                        <button
                            onClick={handleRunOptimization}
                            disabled={loading || !siteData.activeScheduleId}
                            className="px-4 py-1.5 text-sm bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded font-medium transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50 flex items-center gap-1.5"
                        >
                            <Zap size={14} />
                            {loading ? 'Running...' : 'Auto-Schedule'}
                        </button>
                    </div>
                </header>

                {/* Error Banner */}
                {dataError && (
                    <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-2 flex items-center gap-2 text-red-400 text-sm">
                        <AlertCircle size={16} />
                        <span>{dataError}</span>
                        <button
                            onClick={fetchSiteData}
                            className="ml-auto text-red-300 hover:text-white underline"
                        >
                            Retry
                        </button>
                    </div>
                )}

                {/* Main Content Area */}
                <div className="flex-1 overflow-hidden relative">
                    {renderTabContent()}
                </div>

                {/* Properties Panel (for spatial view) */}
                {activeTab === 'spatial' && (
                    <aside className="w-80 border-l border-slate-800 bg-slate-950 p-4 absolute right-0 top-0 bottom-0 hidden xl:block overflow-y-auto">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
                            Properties
                        </h3>

                        <div className="space-y-4">
                            {/* Selected Object */}
                            <div className="p-3 bg-slate-900 rounded border border-slate-800">
                                <p className="text-xs text-slate-500 mb-1">Selected Object</p>
                                <p className="text-sm font-bold text-blue-400">
                                    {selectedBlock ? (selectedBlock.name || selectedBlock.id) : 'None'}
                                </p>
                                {selectedBlock && (
                                    <div className="mt-2 space-y-1 text-xs text-slate-400">
                                        <div>ID: {String(selectedBlock.area_id || selectedBlock.id).substring(0, 8)}...</div>
                                        <div>Material: {selectedBlock.slice_states?.[0]?.material || 'Unknown'}</div>
                                        <div>Quantity: {selectedBlock.slice_states?.[0]?.quantity?.toLocaleString() || 0}t</div>
                                    </div>
                                )}
                            </div>

                            {/* Add to Schedule Button */}
                            {selectedBlock?.area_id && (
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

                            {/* Stats */}
                            <div className="p-3 bg-slate-900 rounded border border-slate-800">
                                <p className="text-xs text-slate-500 mb-1">Total Blocks</p>
                                <p className="text-sm font-medium">{siteData.activityAreas.length} loaded</p>
                            </div>

                            <div className="p-3 bg-slate-900 rounded border border-slate-800">
                                <p className="text-xs text-slate-500 mb-1">Active Tasks</p>
                                <p className="text-sm font-medium">{siteData.activeTasks.length} scheduled</p>
                            </div>
                        </div>
                    </aside>
                )}
            </div>
        </AppLayout>
    );
};

export default PlannerWorkspace;
