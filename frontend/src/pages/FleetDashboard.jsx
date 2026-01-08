import React, { useState } from 'react';
import EquipmentList from '../components/fleet/EquipmentList';
import MaintenancePanel from '../components/fleet/MaintenancePanel';

const FleetDashboard = () => {
    const [activeTab, setActiveTab] = useState('list');
    // Hardcoded site ID for now, should come from context/selector
    const currentSiteId = "site-001";

    return (
        <div className="fleet-dashboard page-container">
            <header className="page-header">
                <h2>Fleet Management</h2>
                <div className="tab-controls">
                    <button
                        className={activeTab === 'list' ? 'active' : ''}
                        onClick={() => setActiveTab('list')}
                    >
                        Equipment List
                    </button>
                    <button
                        className={activeTab === 'map' ? 'active' : ''}
                        onClick={() => setActiveTab('map')}
                    >
                        Live Map
                    </button>
                    <button
                        className={activeTab === 'maintenance' ? 'active' : ''}
                        onClick={() => setActiveTab('maintenance')}
                    >
                        Maintenance
                    </button>
                </div>
            </header>

            <main className="dashboard-content">
                {activeTab === 'list' && <EquipmentList siteId={currentSiteId} />}

                {activeTab === 'map' && (
                    <div className="map-placeholder card">
                        <h3>Live Fleet Map</h3>
                        <p>Map visualization would go here (requires map integration)</p>
                        <p>Coordinates would be plotted from <code>/fleet/sites/{currentSiteId}/positions</code></p>
                    </div>
                )}

                {activeTab === 'maintenance' && <MaintenancePanel siteId={currentSiteId} />}
            </main>
        </div>
    );
};

export default FleetDashboard;
