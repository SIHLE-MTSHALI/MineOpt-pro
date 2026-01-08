import React from 'react';
import {
    Box, Layers, Calendar, Truck, Settings, Database,
    GitBranch, Package, Zap, BarChart2, Target, Wind,
    Mountain, Upload, Link, ClipboardList, Home, LogOut
} from 'lucide-react';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';

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
