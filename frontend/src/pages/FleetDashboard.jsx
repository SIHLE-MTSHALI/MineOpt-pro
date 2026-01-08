import React, { useState } from 'react';
import EquipmentList from '../components/fleet/EquipmentList';
import MaintenancePanel from '../components/fleet/MaintenancePanel';
import FleetMapContainer from '../components/fleet/FleetMapContainer';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';

const FleetDashboard = () => {
    const [activeTab, setActiveTab] = useState('list');
    const { currentSiteId, loading: siteLoading } = useSite();

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
                    <h2 className="text-xl font-bold text-white">Fleet Management</h2>
                    <p className="text-sm text-slate-400 mt-1">Track equipment status, locations, and maintenance</p>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'list'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('list')}
                        >
                            Equipment List
                        </button>
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'map'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('map')}
                        >
                            Live Map
                        </button>
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'maintenance'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('maintenance')}
                        >
                            Maintenance
                        </button>
                    </div>
                </div>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {activeTab === 'list' && <EquipmentList siteId={currentSiteId} />}
                    {activeTab === 'map' && <FleetMapContainer siteId={currentSiteId} />}
                    {activeTab === 'maintenance' && <MaintenancePanel siteId={currentSiteId} />}
                </main>
            </div>
        </AppLayout>
    );
};

export default FleetDashboard;
