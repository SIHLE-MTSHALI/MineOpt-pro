/**
 * MineOpt Pro - Application Layout Shell
 * ========================================
 * 
 * The main application layout providing:
 * - Collapsible sidebar navigation
 * - Top header bar with site/schedule context
 * - Main content area
 * - Optional right panel for properties
 */

import React, { useState, createContext, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
    Box, Layers, Calendar, Truck, Settings, Database,
    GitBranch, Package, Zap, BarChart2, LogOut, ChevronLeft,
    ChevronRight, User, Bell, Moon, Sun, HelpCircle,
    Home, Target, ClipboardList, Mountain, Wind, Upload, Link
} from 'lucide-react';
import { useSite } from '../../context/SiteContext';

// ============================================
// APP CONTEXT
// ============================================

const AppContext = createContext(null);

export function useApp() {
    return useContext(AppContext);
}

export function AppProvider({ children }) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [activeModule, setActiveModule] = useState('spatial');
    const [theme, setTheme] = useState('dark');

    const value = {
        sidebarCollapsed,
        setSidebarCollapsed,
        activeModule,
        setActiveModule,
        theme,
        setTheme,
        toggleSidebar: () => setSidebarCollapsed(!sidebarCollapsed),
        toggleTheme: () => setTheme(theme === 'dark' ? 'light' : 'dark'),
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}


// ============================================
// SIDEBAR NAVIGATION
// ============================================

const navSections = [
    {
        title: 'Home',
        items: [
            { id: 'dashboard', label: 'Dashboard', icon: Home, route: '/app/dashboard' },
        ],
    },
    {
        title: 'Planning',
        items: [
            { id: 'spatial', label: '3D Spatial View', icon: Box, route: '/app/planner' },
            { id: 'gantt', label: 'Gantt Schedule', icon: Calendar, route: '/app/planner' },
            { id: 'schedule-control', label: 'Schedule Control', icon: Zap, route: '/app/planner' },
            { id: 'reporting', label: 'Reports & Analytics', icon: BarChart2, route: '/app/planner' },
        ],
    },
    {
        title: 'Operations',
        items: [
            { id: 'fleet', label: 'Fleet Management', icon: Truck, route: '/app/fleet' },
            { id: 'drill-blast', label: 'Drill & Blast', icon: Target, route: '/app/drill-blast' },
            { id: 'shift-ops', label: 'Shift Operations', icon: ClipboardList, route: '/app/operations' },
        ],
    },
    {
        title: 'Monitoring',
        items: [
            { id: 'geotech', label: 'Slope Stability', icon: Mountain, route: '/app/monitoring' },
            { id: 'environment', label: 'Environment', icon: Wind, route: '/app/monitoring' },
        ],
    },
    {
        title: 'Configuration',
        items: [
            { id: 'flow-editor', label: 'Flow Network', icon: GitBranch, route: '/app/planner' },
            { id: 'product-specs', label: 'Product Specs', icon: Package, route: '/app/planner' },
            { id: 'resources', label: 'Resources', icon: Truck, route: '/app/planner' },
            { id: 'geology', label: 'Block Model', icon: Layers, route: '/app/planner' },
            { id: 'data', label: 'Data Model', icon: Database, route: '/app/planner' },
        ],
    },
    {
        title: 'Data & Integration',
        items: [
            { id: 'import', label: 'Import Data', icon: Upload, route: '/app/planner' },
            { id: 'integrations', label: 'Integrations', icon: Link, route: '/app/planner' },
            { id: 'seed-data', label: 'Seed Demo Data', icon: Database, route: '/app/seed-data', highlight: true },
            { id: 'settings', label: 'Settings', icon: Settings, route: '/app/planner' },
        ],
    },
];

function NavItem({ item, active, collapsed, onClick }) {
    const Icon = item.icon;

    return (
        <button
            onClick={onClick}
            className={clsx(
                'w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-all duration-200',
                'relative group',
                item.highlight
                    ? 'text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20'
                    : active
                        ? 'text-primary-400 bg-primary-500/10'
                        : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
            )}
        >
            {/* Active indicator */}
            {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-primary-400 rounded-r" />
            )}

            <Icon size={18} className="flex-shrink-0" />

            {!collapsed && (
                <>
                    <span className="truncate">{item.label}</span>
                    {item.highlight && (
                        <span className="ml-auto px-1.5 py-0.5 text-[10px] bg-emerald-500/20 text-emerald-400 rounded font-semibold">
                            NEW
                        </span>
                    )}
                </>
            )}

            {/* Tooltip for collapsed state */}
            {collapsed && (
                <span className="absolute left-full ml-2 px-2 py-1 bg-neutral-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
                    {item.label}
                </span>
            )}
        </button>
    );
}

export function AppSidebar() {
    const { sidebarCollapsed, toggleSidebar, activeModule, setActiveModule } = useApp();
    const navigate = useNavigate();
    const location = useLocation();

    const handleNavClick = (item) => {
        setActiveModule(item.id);
        if (item.route) {
            navigate(item.route);
        }
    };

    const isActiveItem = (item) => {
        // Check if current route matches this item's route
        if (item.route && location.pathname === item.route) {
            return true;
        }
        return activeModule === item.id;
    };

    return (
        <aside
            className={clsx(
                'h-full flex flex-col bg-neutral-950 border-r border-neutral-800 transition-all duration-300',
                sidebarCollapsed ? 'w-16' : 'w-64'
            )}
        >
            {/* Logo */}
            <div className={clsx(
                'h-14 flex items-center border-b border-neutral-800 px-4',
                sidebarCollapsed ? 'justify-center' : 'justify-between'
            )}>
                {!sidebarCollapsed && (
                    <button onClick={() => navigate('/app/dashboard')} className="hover:opacity-80 transition-opacity">
                        <h1 className="text-lg font-bold text-white tracking-tight">
                            MineOpt<span className="text-blue-500">Pro</span>
                        </h1>
                        <p className="text-[10px] text-neutral-500 -mt-0.5">Enterprise Edition</p>
                    </button>
                )}

                {sidebarCollapsed && (
                    <button onClick={() => navigate('/app/dashboard')} className="hover:opacity-80 transition-opacity">
                        <span className="text-lg font-bold text-blue-500">M</span>
                    </button>
                )}

                <button
                    onClick={toggleSidebar}
                    className="p-1.5 hover:bg-neutral-800 rounded-md text-neutral-400 hover:text-white transition-colors"
                >
                    {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-4 overflow-y-auto">
                {navSections.map((section) => (
                    <div key={section.title} className="mb-4">
                        {!sidebarCollapsed && (
                            <div className="px-4 mb-2 text-[10px] font-semibold text-neutral-600 uppercase tracking-wider">
                                {section.title}
                            </div>
                        )}
                        {sidebarCollapsed && (
                            <div className="mb-2 border-b border-neutral-800 mx-4" />
                        )}
                        {section.items.map((item) => (
                            <NavItem
                                key={item.id}
                                item={item}
                                active={isActiveItem(item)}
                                collapsed={sidebarCollapsed}
                                onClick={() => handleNavClick(item)}
                            />
                        ))}
                    </div>
                ))}
            </nav>

            {/* Footer */}
            <div className="border-t border-neutral-800 p-3">
                <button
                    className={clsx(
                        'w-full flex items-center gap-3 px-2 py-2 rounded-lg',
                        'text-sm text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition-colors',
                        sidebarCollapsed && 'justify-center'
                    )}
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                        SU
                    </div>
                    {!sidebarCollapsed && (
                        <div className="text-left">
                            <div className="text-neutral-200 text-sm font-medium">Super User</div>
                            <div className="text-neutral-500 text-xs">Administrator</div>
                        </div>
                    )}
                </button>
            </div>
        </aside>
    );
}


// ============================================
// TOP HEADER BAR
// ============================================

export function AppHeader({
    siteName = 'Enterprise Coal Mine',
    scheduleVersion,
    scheduleVersions = [],
    onScheduleChange,
    onRunSchedule,
    loading = false,
}) {
    const { toggleTheme, theme } = useApp();
    const navigate = useNavigate();

    return (
        <header className="h-14 border-b border-neutral-800 flex items-center justify-between px-6 bg-neutral-950/50 backdrop-blur-sm">
            {/* Left: Site & Schedule Selection */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <span className="text-xs text-neutral-500">Site:</span>
                    <span className="text-sm font-medium text-neutral-200">{siteName}</span>
                </div>

                <div className="w-px h-6 bg-neutral-800" />

                <div className="flex items-center gap-2">
                    <span className="text-xs text-neutral-500">Schedule:</span>
                    <select
                        value={scheduleVersion || ''}
                        onChange={(e) => onScheduleChange?.(e.target.value)}
                        className="bg-neutral-800 border border-neutral-700 text-white text-sm rounded-md px-3 py-1.5 focus:outline-none focus:border-primary-500 transition-colors"
                    >
                        {scheduleVersions.map((v) => (
                            <option key={v.version_id} value={v.version_id}>
                                {v.name} ({v.status})
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-3">
                {/* Notifications */}
                <button className="p-2 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition-colors relative">
                    <Bell size={18} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger-500 rounded-full" />
                </button>

                {/* Theme Toggle */}
                <button
                    onClick={toggleTheme}
                    className="p-2 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition-colors"
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>

                {/* Help */}
                <button className="p-2 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition-colors">
                    <HelpCircle size={18} />
                </button>

                <div className="w-px h-6 bg-neutral-800" />

                {/* Seed Data Button */}
                <button
                    onClick={() => navigate('/app/seed-data')}
                    className="px-3 py-1.5 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg transition-colors flex items-center gap-1.5"
                >
                    <Database size={14} />
                    Seed Demo Data
                </button>

                {/* Run Schedule Button */}
                <button
                    onClick={onRunSchedule}
                    disabled={loading}
                    className={clsx(
                        'px-4 py-1.5 text-sm font-medium rounded-lg transition-all',
                        'bg-gradient-to-r from-accent-500 to-accent-600 text-white',
                        'hover:from-accent-400 hover:to-accent-500',
                        'shadow-lg shadow-accent-500/20 hover:shadow-accent-500/30',
                        'disabled:opacity-50 disabled:cursor-not-allowed',
                        'flex items-center gap-2'
                    )}
                >
                    <Zap size={14} />
                    {loading ? 'Running...' : 'Auto-Schedule'}
                </button>
            </div>
        </header>
    );
}


// ============================================
// MAIN LAYOUT
// ============================================

export function AppLayout({ children }) {
    return (
        <AppProvider>
            <div className="h-screen w-screen flex overflow-hidden bg-neutral-950">
                <AppSidebar />
                <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                    {children}
                </main>
            </div>
        </AppProvider>
    );
}


// ============================================
// CONTENT PANELS
// ============================================

export function ContentArea({ children, className }) {
    return (
        <div className={clsx('flex-1 overflow-hidden', className)}>
            {children}
        </div>
    );
}

export function PropertiesPanel({ children, title, onClose, className }) {
    return (
        <aside className={clsx(
            'w-80 border-l border-neutral-800 bg-neutral-950 flex flex-col',
            className
        )}>
            {title && (
                <div className="h-12 flex items-center justify-between px-4 border-b border-neutral-800">
                    <h3 className="text-sm font-semibold text-white">{title}</h3>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
                        >
                            ✕
                        </button>
                    )}
                </div>
            )}
            <div className="flex-1 overflow-y-auto p-4">
                {children}
            </div>
        </aside>
    );
}


// ============================================
// MODULE PLACEHOLDER
// ============================================

export function ModulePlaceholder({ title, description }) {
    return (
        <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md mx-auto p-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-neutral-800 to-neutral-900 flex items-center justify-center">
                    <Settings size={24} className="text-neutral-500" />
                </div>
                <h2 className="text-xl font-semibold text-neutral-200 mb-2">
                    {title || 'Coming Soon'}
                </h2>
                <p className="text-sm text-neutral-500">
                    {description || 'This module is under development.'}
                </p>
            </div>
        </div>
    );
}


export default {
    AppProvider,
    AppLayout,
    AppSidebar,
    AppHeader,
    ContentArea,
    PropertiesPanel,
    ModulePlaceholder,
    useApp,
};
