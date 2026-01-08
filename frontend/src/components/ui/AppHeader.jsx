/**
 * AppHeader.jsx - Shared Navigation Header
 * 
 * Provides consistent navigation across all app pages:
 * - Logo/branding
 * - Site selector dropdown
 * - Current page indicator
 * - User menu with logout
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, ChevronDown, LogOut, User, Settings, Menu } from 'lucide-react';
import { useSite } from '../../context/SiteContext';

const AppHeader = ({ onToggleSidebar, showSidebarToggle = false }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { sites, currentSite, selectSite, loading } = useSite();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    // Get current page name from route
    const getPageName = () => {
        const path = location.pathname;
        const pageNames = {
            '/app/dashboard': 'Dashboard',
            '/app/planner': 'Planner Workspace',
            '/app/fleet': 'Fleet Management',
            '/app/drill-blast': 'Drill & Blast',
            '/app/operations': 'Operations',
            '/app/monitoring': 'Monitoring'
        };
        return pageNames[path] || 'Dashboard';
    };

    return (
        <header className="h-14 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-4 sticky top-0 z-50">
            {/* Left section - Logo and breadcrumb */}
            <div className="flex items-center gap-4">
                {showSidebarToggle && (
                    <button
                        onClick={onToggleSidebar}
                        className="p-2 hover:bg-slate-800 rounded-lg transition-colors lg:hidden"
                    >
                        <Menu size={20} className="text-slate-400" />
                    </button>
                )}

                <button
                    onClick={() => navigate('/app/dashboard')}
                    className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                    <span className="text-xl font-bold text-white tracking-tight">
                        MineOpt<span className="text-blue-500">Pro</span>
                    </span>
                </button>

                {/* Breadcrumb */}
                <div className="hidden sm:flex items-center gap-2 text-sm text-slate-400">
                    <ChevronDown size={14} className="rotate-[-90deg]" />
                    <span className="text-slate-200">{getPageName()}</span>
                </div>
            </div>

            {/* Center section - Site selector */}
            <div className="flex items-center">
                <div className="relative">
                    <select
                        value={currentSite?.site_id || ''}
                        onChange={(e) => selectSite(e.target.value)}
                        disabled={loading}
                        className="appearance-none bg-slate-800 border border-slate-700 text-white text-sm rounded-lg px-4 py-2 pr-8 focus:outline-none focus:border-blue-500 cursor-pointer min-w-[200px]"
                    >
                        {sites.map(site => (
                            <option key={site.site_id} value={site.site_id}>
                                {site.name}
                            </option>
                        ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
            </div>

            {/* Right section - User menu */}
            <div className="flex items-center gap-2">
                <button
                    onClick={() => navigate('/app/dashboard')}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                    title="Dashboard"
                >
                    <Home size={18} />
                </button>

                <button
                    onClick={() => navigate('/app/planner')}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                    title="Settings"
                >
                    <Settings size={18} />
                </button>

                <div className="w-px h-6 bg-slate-700 mx-2" />

                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">
                        <User size={16} />
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-400"
                        title="Logout"
                    >
                        <LogOut size={18} />
                    </button>
                </div>
            </div>
        </header>
    );
};

export default AppHeader;
