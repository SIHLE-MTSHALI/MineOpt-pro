import React from 'react';
import {
    Box, Layers, Calendar, Truck, Settings, Database,
    GitBranch, Package, Zap, BarChart2, Target, Wind,
    Mountain, Upload, Link, ClipboardList, Home, LogOut, ChevronDown
} from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useSite } from '../../context/SiteContext';

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={clsx(
            "w-full flex items-center space-x-3 px-4 py-3 text-sm font-medium transition-colors",
            active ? "bg-slate-800 text-blue-400 border-r-2 border-blue-400" : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
        )}
    >
        <Icon size={18} />
        <span>{label}</span>
    </button>
);

const Sidebar = ({ activeTab, setActiveTab }) => {
    const navigate = useNavigate();
    const { sites, currentSiteId, currentSite, selectSite, loading } = useSite();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-full">
            <div className="p-4 border-b border-slate-800">
                <h1 className="text-xl font-bold text-white tracking-tight">MineOpt<span className="text-blue-500">Pro</span></h1>
                <p className="text-xs text-slate-500 mt-1">Enterprise Scheduling</p>
            </div>

            {/* Site Selector */}
            <div className="px-4 py-3 border-b border-slate-800">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 block">
                    Active Site
                </label>
                <div className="relative">
                    <select
                        value={currentSiteId || ''}
                        onChange={(e) => selectSite(e.target.value)}
                        disabled={loading || sites.length === 0}
                        className="w-full bg-slate-900 border border-slate-700 text-white text-sm rounded-lg px-3 py-2 pr-8 appearance-none cursor-pointer hover:border-slate-600 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
                    >
                        {loading ? (
                            <option value="">Loading sites...</option>
                        ) : sites.length === 0 ? (
                            <option value="">No sites available</option>
                        ) : (
                            sites.map((site) => (
                                <option key={site.site_id} value={site.site_id}>
                                    {site.name}
                                </option>
                            ))
                        )}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
                {currentSite && (
                    <p className="text-xs text-slate-600 mt-1 truncate" title={currentSite.timezone}>
                        {currentSite.timezone || 'UTC'}
                    </p>
                )}
            </div>


            <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
                {/* Dashboard */}
                <SidebarItem icon={Home} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => navigate('/app/dashboard')} />

                {/* Planning Section */}
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-4 mb-2">Planning</div>
                <SidebarItem icon={Box} label="3D Spatial View" active={activeTab === 'spatial'} onClick={() => setActiveTab('spatial')} />
                <SidebarItem icon={Calendar} label="Gantt Schedule" active={activeTab === 'gantt'} onClick={() => setActiveTab('gantt')} />
                <SidebarItem icon={Zap} label="Schedule Control" active={activeTab === 'schedule-control'} onClick={() => setActiveTab('schedule-control')} />
                <SidebarItem icon={BarChart2} label="Reports" active={activeTab === 'reporting'} onClick={() => setActiveTab('reporting')} />

                {/* Operations Section */}
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-4 mb-2">Operations</div>
                <SidebarItem icon={Truck} label="Fleet Management" active={activeTab === 'fleet'} onClick={() => setActiveTab('fleet')} />
                <SidebarItem icon={Target} label="Drill & Blast" active={activeTab === 'drill-blast'} onClick={() => setActiveTab('drill-blast')} />
                <SidebarItem icon={ClipboardList} label="Shift Operations" active={activeTab === 'shift-ops'} onClick={() => setActiveTab('shift-ops')} />

                {/* Monitoring Section */}
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-4 mb-2">Monitoring</div>
                <SidebarItem icon={Mountain} label="Slope Stability" active={activeTab === 'geotech'} onClick={() => setActiveTab('geotech')} />
                <SidebarItem icon={Wind} label="Environment" active={activeTab === 'environment'} onClick={() => setActiveTab('environment')} />

                {/* Configuration Section */}
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-4 mb-2">Configuration</div>
                <SidebarItem icon={GitBranch} label="Flow Network" active={activeTab === 'flow-editor'} onClick={() => setActiveTab('flow-editor')} />
                <SidebarItem icon={Package} label="Product Specs" active={activeTab === 'product-specs'} onClick={() => setActiveTab('product-specs')} />
                <SidebarItem icon={Database} label="Stockpiles" active={activeTab === 'data'} onClick={() => setActiveTab('data')} />
                <SidebarItem icon={Layers} label="Wash Plant" active={activeTab === 'resources'} onClick={() => setActiveTab('resources')} />
                <SidebarItem icon={Layers} label="Geology" active={activeTab === 'geology'} onClick={() => setActiveTab('geology')} />

                {/* Data & Integration Section */}
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-4 mb-2">Data & Integration</div>
                <SidebarItem icon={Upload} label="Import Data" active={activeTab === 'import'} onClick={() => setActiveTab('import')} />
                <SidebarItem icon={Link} label="Integrations" active={activeTab === 'integrations'} onClick={() => setActiveTab('integrations')} />
                <SidebarItem icon={Settings} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
            </nav>

            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">SU</div>
                        <div className="text-sm">
                            <div className="text-white">Super User</div>
                            <div className="text-slate-500 text-xs">Admin Access</div>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
                        title="Logout"
                    >
                        <LogOut size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
