/**
 * AppLayout.jsx - Application Layout Shell
 * 
 * Enterprise-grade application layout providing:
 * - Unified sidebar navigation with route-based navigation
 * - Top header bar with site/schedule context
 * - Dynamic user profile display from auth context
 * - Collapsible sidebar with state persistence
 * - Theme support (dark/light)
 * - Notification system integration
 * 
 * @module components/layout/AppLayout
 */

import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
    Box, Layers, Calendar, Truck, Settings, Database,
    GitBranch, Package, Zap, BarChart2, LogOut, ChevronLeft,
    ChevronRight, Bell, Moon, Sun, HelpCircle,
    Home, Target, ClipboardList, Mountain, Wind, Upload, Link, Sparkles
} from 'lucide-react';
import { useSite } from '../../context/SiteContext';
import { authAPI } from '../../services/api';

// =============================================================================
// APP CONTEXT
// =============================================================================

const AppContext = createContext(null);

/**
 * Hook to access app context
 * @returns {Object} App context value
 */
export function useApp() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
}

/**
 * App Context Provider
 * Manages global app state: sidebar, theme, user
 */
export function AppProvider({ children }) {
    // ==========================================================================
    // PERSISTED STATE
    // ==========================================================================

    const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
        const stored = localStorage.getItem('mineopt_sidebar_collapsed');
        return stored === 'true';
    });

    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('mineopt_theme') || 'dark';
    });

    // ==========================================================================
    // USER STATE
    // ==========================================================================

    const [user, setUser] = useState({
        username: 'User',
        email: '',
        initials: 'U',
        roles: []
    });

    const [userLoading, setUserLoading] = useState(true);

    // Fetch user on mount
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const userData = await authAPI.getCurrentUser();
                setUser({
                    username: userData.username || userData.email?.split('@')[0] || 'User',
                    email: userData.email || '',
                    initials: getInitials(userData.username || userData.email),
                    roles: userData.roles || ['user']
                });
            } catch (err) {
                // User not authenticated or error - use defaults
                console.warn('[AppLayout] Failed to fetch user:', err.message);
            } finally {
                setUserLoading(false);
            }
        };

        const token = localStorage.getItem('token');
        if (token) {
            fetchUser();
        } else {
            setUserLoading(false);
        }
    }, []);

    // ==========================================================================
    // STATE HANDLERS
    // ==========================================================================

    const handleSetSidebarCollapsed = useCallback((collapsed) => {
        localStorage.setItem('mineopt_sidebar_collapsed', String(collapsed));
        setSidebarCollapsed(collapsed);
    }, []);

    const handleSetTheme = useCallback((newTheme) => {
        localStorage.setItem('mineopt_theme', newTheme);
        setTheme(newTheme);
        // Apply theme to document
        document.documentElement.classList.toggle('light-theme', newTheme === 'light');
    }, []);

    const toggleSidebar = useCallback(() => {
        handleSetSidebarCollapsed(!sidebarCollapsed);
    }, [sidebarCollapsed, handleSetSidebarCollapsed]);

    const toggleTheme = useCallback(() => {
        handleSetTheme(theme === 'dark' ? 'light' : 'dark');
    }, [theme, handleSetTheme]);

    // ==========================================================================
    // CONTEXT VALUE
    // ==========================================================================

    const value = {
        sidebarCollapsed,
        setSidebarCollapsed: handleSetSidebarCollapsed,
        theme,
        setTheme: handleSetTheme,
        toggleSidebar,
        toggleTheme,
        user,
        userLoading
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get initials from a name
 * @param {string} name - User name or email
 * @returns {string} 2 character initials
 */
function getInitials(name) {
    if (!name) return 'U';
    const parts = name.split(/[\s@._-]+/).filter(Boolean);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

// =============================================================================
// NAVIGATION CONFIGURATION
// =============================================================================

const navSections = [
    {
        title: 'Home',
        items: [
            { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/app/dashboard' }
        ]
    },
    {
        title: 'Planning',
        items: [
            { id: 'spatial', label: '3D Spatial View', icon: Box, plannerTab: 'spatial' },
            { id: 'gantt', label: 'Gantt Schedule', icon: Calendar, plannerTab: 'gantt' },
            { id: 'schedule-control', label: 'Schedule Control', icon: Zap, plannerTab: 'schedule-control' },
            { id: 'reporting', label: 'Reports & Analytics', icon: BarChart2, plannerTab: 'reporting' }
        ]
    },
    {
        title: 'Operations',
        items: [
            { id: 'fleet', label: 'Fleet Management', icon: Truck, path: '/app/fleet' },
            { id: 'drill-blast', label: 'Drill & Blast', icon: Target, path: '/app/drill-blast' },
            { id: 'shift-ops', label: 'Shift Operations', icon: ClipboardList, path: '/app/operations' }
        ]
    },
    {
        title: 'Monitoring',
        items: [
            { id: 'geotech', label: 'Slope Stability', icon: Mountain, path: '/app/monitoring' },
            { id: 'environment', label: 'Environment', icon: Wind, path: '/app/monitoring' }
        ]
    },
    {
        title: 'Configuration',
        items: [
            { id: 'flow-editor', label: 'Flow Network', icon: GitBranch, plannerTab: 'flow-editor' },
            { id: 'product-specs', label: 'Product Specs', icon: Package, plannerTab: 'product-specs' },
            { id: 'resources', label: 'Resources', icon: Truck, plannerTab: 'resources' },
            { id: 'geology', label: 'Block Model', icon: Layers, plannerTab: 'geology' },
            { id: 'data', label: 'Stockpiles', icon: Database, plannerTab: 'data' }
        ]
    },
    {
        title: 'Data & Integration',
        items: [
            { id: 'import', label: 'Import Data', icon: Upload, plannerTab: 'import' },
            { id: 'integrations', label: 'Integrations', icon: Link, plannerTab: 'integrations' },
            { id: 'seed-data', label: 'Seed Demo Data', icon: Sparkles, path: '/app/seed-data', highlight: true },
            { id: 'settings', label: 'Settings', icon: Settings, plannerTab: 'settings' }
        ]
    }
];

// =============================================================================
// NAV ITEM COMPONENT
// =============================================================================

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
                        ? 'text-blue-400 bg-blue-500/10'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            )}
        >
            {/* Active indicator */}
            {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-blue-400 rounded-r" />
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
                <span className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity shadow-lg">
                    {item.label}
                </span>
            )}
        </button>
    );
}

// =============================================================================
// APP SIDEBAR COMPONENT
// =============================================================================

export function AppSidebar() {
    const { sidebarCollapsed, toggleSidebar, user, userLoading } = useApp();
    const navigate = useNavigate();
    const location = useLocation();

    /**
     * Handle navigation click
     */
    const handleNavClick = (item) => {
        if (item.path) {
            navigate(item.path);
        } else if (item.plannerTab) {
            navigate(`/app/planner?tab=${item.plannerTab}`);
        }
    };

    /**
     * Check if item is active
     */
    const isActiveItem = (item) => {
        if (item.path && location.pathname === item.path) {
            return true;
        }
        if (item.plannerTab && location.pathname === '/app/planner') {
            const params = new URLSearchParams(location.search);
            const tab = params.get('tab') || 'reporting';
            return tab === item.plannerTab;
        }
        return false;
    };

    /**
     * Handle logout
     */
    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <aside
            className={clsx(
                'h-full flex flex-col bg-slate-950 border-r border-slate-800 transition-all duration-300',
                sidebarCollapsed ? 'w-16' : 'w-64'
            )}
        >
            {/* Logo */}
            <div className={clsx(
                'h-14 flex items-center border-b border-slate-800 px-4',
                sidebarCollapsed ? 'justify-center' : 'justify-between'
            )}>
                {!sidebarCollapsed && (
                    <button onClick={() => navigate('/app/dashboard')} className="hover:opacity-80 transition-opacity">
                        <h1 className="text-lg font-bold text-white tracking-tight">
                            MineOpt<span className="text-blue-500">Pro</span>
                        </h1>
                        <p className="text-[10px] text-slate-500 -mt-0.5">Enterprise Edition</p>
                    </button>
                )}

                {sidebarCollapsed && (
                    <button onClick={() => navigate('/app/dashboard')} className="hover:opacity-80 transition-opacity">
                        <span className="text-lg font-bold text-blue-500">M</span>
                    </button>
                )}

                <button
                    onClick={toggleSidebar}
                    className="p-1.5 hover:bg-slate-800 rounded-md text-slate-400 hover:text-white transition-colors"
                >
                    {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-4 overflow-y-auto">
                {navSections.map((section) => (
                    <div key={section.title} className="mb-4">
                        {!sidebarCollapsed && (
                            <div className="px-4 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                                {section.title}
                            </div>
                        )}
                        {sidebarCollapsed && (
                            <div className="mb-2 border-b border-slate-800 mx-4" />
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

            {/* Footer - User Profile */}
            <div className="border-t border-slate-800 p-3 space-y-2">
                {/* User Profile */}
                <div
                    className={clsx(
                        'flex items-center gap-3 px-2 py-2 rounded-lg',
                        'text-sm text-slate-400',
                        sidebarCollapsed && 'justify-center'
                    )}
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                        {userLoading ? '...' : user.initials}
                    </div>
                    {!sidebarCollapsed && (
                        <div className="text-left flex-1 min-w-0">
                            <div className="text-slate-200 text-sm font-medium truncate">
                                {userLoading ? 'Loading...' : user.username}
                            </div>
                            <div className="text-slate-500 text-xs truncate">
                                {user.roles.includes('admin') ? 'Administrator' : 'User'}
                            </div>
                        </div>
                    )}
                </div>

                {/* Logout Button */}
                <button
                    onClick={handleLogout}
                    className={clsx(
                        'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                        'text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors',
                        sidebarCollapsed && 'justify-center'
                    )}
                    title="Logout"
                >
                    <LogOut size={18} />
                    {!sidebarCollapsed && <span>Logout</span>}
                </button>
            </div>
        </aside>
    );
}

// =============================================================================
// APP HEADER COMPONENT
// =============================================================================

export function AppHeader({
    siteName = 'Enterprise Coal Mine',
    scheduleVersion,
    scheduleVersions = [],
    onScheduleChange,
    onRunSchedule,
    loading = false
}) {
    const { toggleTheme, theme } = useApp();
    const navigate = useNavigate();

    return (
        <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-950/50 backdrop-blur-sm">
            {/* Left: Site & Schedule Selection */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Site:</span>
                    <span className="text-sm font-medium text-slate-200">{siteName}</span>
                </div>

                <div className="w-px h-6 bg-slate-800" />

                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Schedule:</span>
                    <select
                        value={scheduleVersion || ''}
                        onChange={(e) => onScheduleChange?.(e.target.value)}
                        className="bg-slate-800 border border-slate-700 text-white text-sm rounded-md px-3 py-1.5 focus:outline-none focus:border-blue-500 transition-colors"
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
                <button className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors relative">
                    <Bell size={18} />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                </button>

                {/* Theme Toggle */}
                <button
                    onClick={toggleTheme}
                    className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>

                {/* Help */}
                <button className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors">
                    <HelpCircle size={18} />
                </button>

                <div className="w-px h-6 bg-slate-800" />

                {/* Seed Data Button */}
                <button
                    onClick={() => navigate('/app/seed-data')}
                    className="px-3 py-1.5 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg transition-colors flex items-center gap-1.5"
                >
                    <Sparkles size={14} />
                    Seed Demo Data
                </button>

                {/* Run Schedule Button */}
                <button
                    onClick={onRunSchedule}
                    disabled={loading}
                    className={clsx(
                        'px-4 py-1.5 text-sm font-medium rounded-lg transition-all',
                        'bg-gradient-to-r from-purple-600 to-blue-600 text-white',
                        'hover:from-purple-500 hover:to-blue-500',
                        'shadow-lg shadow-purple-500/20 hover:shadow-purple-500/30',
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

// =============================================================================
// MAIN LAYOUT COMPONENT
// =============================================================================

export function AppLayout({ children }) {
    return (
        <AppProvider>
            <div className="h-screen w-screen flex overflow-hidden bg-slate-950">
                <AppSidebar />
                <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                    {children}
                </main>
            </div>
        </AppProvider>
    );
}

// =============================================================================
// CONTENT PANELS
// =============================================================================

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
            'w-80 border-l border-slate-800 bg-slate-950 flex flex-col',
            className
        )}>
            {title && (
                <div className="h-12 flex items-center justify-between px-4 border-b border-slate-800">
                    <h3 className="text-sm font-semibold text-white">{title}</h3>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
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

// =============================================================================
// MODULE PLACEHOLDER
// =============================================================================

export function ModulePlaceholder({ title, description }) {
    return (
        <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md mx-auto p-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                    <Settings size={24} className="text-slate-500" />
                </div>
                <h2 className="text-xl font-semibold text-slate-200 mb-2">
                    {title || 'Coming Soon'}
                </h2>
                <p className="text-sm text-slate-500">
                    {description || 'This module is under development.'}
                </p>
            </div>
        </div>
    );
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default {
    AppProvider,
    AppLayout,
    AppSidebar,
    AppHeader,
    ContentArea,
    PropertiesPanel,
    ModulePlaceholder,
    useApp
};
