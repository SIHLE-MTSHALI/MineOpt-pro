/**
 * FleetDashboard.jsx - Fleet Management Dashboard
 * 
 * Features:
 * - Equipment list with status updates
 * - Live fleet map
 * - Maintenance tracking
 * - Breadcrumb navigation
 * - Page animations
 */

import React, { useState } from 'react';
import { Truck, Map, Wrench } from 'lucide-react';
import EquipmentList from '../components/fleet/EquipmentList';
import MaintenancePanel from '../components/fleet/MaintenancePanel';
import FleetMapContainer from '../components/fleet/FleetMapContainer';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';
import Breadcrumb from '../components/ui/Breadcrumb';

const FleetDashboard = () => {
    const [activeTab, setActiveTab] = useState('list');
    const { currentSiteId, loading: siteLoading } = useSite();

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
        { id: 'list', label: 'Equipment List', icon: Truck },
        { id: 'map', label: 'Live Map', icon: Map },
        { id: 'maintenance', label: 'Maintenance', icon: Wrench }
    ];

    return (
        <AppLayout>
            <div className="flex flex-col h-full page-enter">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <Breadcrumb className="mb-3" />
                    <h2 className="text-xl font-bold text-white">Fleet Management</h2>
                    <p className="text-sm text-slate-400 mt-1">Track equipment status, locations, and maintenance</p>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all relative ${activeTab === tab.id
                                        ? 'text-blue-400'
                                        : 'text-slate-400 hover:text-slate-200'
                                    }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <tab.icon size={16} />
                                {tab.label}
                                {activeTab === tab.id && (
                                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400 rounded-t-full" />
                                )}
                            </button>
                        ))}
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
