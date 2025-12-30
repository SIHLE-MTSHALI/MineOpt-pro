import React from 'react';
import { Box, Layers, Calendar, Truck, Settings, Database } from 'lucide-react';
import { clsx } from 'clsx';

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
    return (
        <div className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-full">
            <div className="p-4 border-b border-slate-800">
                <h1 className="text-xl font-bold text-white tracking-tight">MineOpt<span className="text-blue-500">Pro</span></h1>
                <p className="text-xs text-slate-500 mt-1">Enterprise Scheduling</p>
            </div>

            <nav className="flex-1 py-4 space-y-1">
                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Planning</div>
                <SidebarItem icon={Box} label="3D Spatial View" active={activeTab === 'spatial'} onClick={() => setActiveTab('spatial')} />
                <SidebarItem icon={Calendar} label="Gantt Schedule" active={activeTab === 'gantt'} onClick={() => setActiveTab('gantt')} />

                <div className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mt-6 mb-2">Configuration</div>
                <SidebarItem icon={Database} label="Data Model" active={activeTab === 'data'} onClick={() => setActiveTab('data')} />
                <SidebarItem icon={Truck} label="Resources" active={activeTab === 'resources'} onClick={() => setActiveTab('resources')} />
                <SidebarItem icon={Layers} label="Geology" active={activeTab === 'geology'} onClick={() => setActiveTab('geology')} />
                <SidebarItem icon={Settings} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
            </nav>

            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">SU</div>
                    <div className="text-sm">
                        <div className="text-white">Super User</div>
                        <div className="text-slate-500 text-xs">Admin Access</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
