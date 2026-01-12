/**
 * Sidebar.jsx - Unified Navigation Sidebar
 * 
 * Professional-grade navigation component providing:
 * - Route-based navigation using React Router
 * - URL query params for PlannerWorkspace tabs
 * - Site selection with context integration
 * - Active state highlighting
 * - Collapsible design
 * - User authentication display
 * 
 * @module components/ui/Sidebar
 */

import React, { useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
    Box, Layers, Calendar, Truck, Settings, Database,
    GitBranch, Package, Zap, BarChart2, Target, Wind,
    Mountain, Upload, Link, ClipboardList, Home, LogOut,
    ChevronDown, ChevronLeft, ChevronRight, Sparkles
} from 'lucide-react';
import { useSite } from '../../context/SiteContext';

// =============================================================================
// NAVIGATION CONFIGURATION
// =============================================================================

/**
 * Navigation sections with items
 * Each item can either:
 * - Navigate to a dedicated route (path)
 * - Navigate to PlannerWorkspace with a tab param (plannerTab)
 */
const NAV_SECTIONS = [
    {
        title: 'Home',
        items: [
            {
                id: 'dashboard',
                label: 'Dashboard',
                icon: Home,
                path: '/app/dashboard'
            }
        ]
    },
    {
        title: 'Planning',
        items: [
            {
                id: 'spatial',
                label: '3D Spatial View',
                icon: Box,
                plannerTab: 'spatial'
            },
            {
                id: 'gantt',
                label: 'Gantt Schedule',
                icon: Calendar,
                plannerTab: 'gantt'
            },
            {
                id: 'schedule-control',
                label: 'Schedule Control',
                icon: Zap,
                plannerTab: 'schedule-control'
            },
            {
                id: 'reporting',
                label: 'Reports & Analytics',
                icon: BarChart2,
                plannerTab: 'reporting'
            }
        ]
    },
    {
        title: 'Operations',
        items: [
            {
                id: 'fleet',
                label: 'Fleet Management',
                icon: Truck,
                path: '/app/fleet'
            },
            {
                id: 'drill-blast',
                label: 'Drill & Blast',
                icon: Target,
                path: '/app/drill-blast'
            },
            {
                id: 'operations',
                label: 'Shift Operations',
                icon: ClipboardList,
                path: '/app/operations'
            }
        ]
    },
    {
        title: 'Monitoring',
        items: [
            {
                id: 'geotech',
                label: 'Slope Stability',
                icon: Mountain,
                path: '/app/monitoring',
                tabHint: 'geotech'
            },
            {
                id: 'environment',
                label: 'Environment',
                icon: Wind,
                path: '/app/monitoring',
                tabHint: 'environment'
            }
        ]
    },
    {
        title: 'Configuration',
        items: [
            {
                id: 'flow-editor',
                label: 'Flow Network',
                icon: GitBranch,
                plannerTab: 'flow-editor'
            },
            {
                id: 'product-specs',
                label: 'Product Specs',
                icon: Package,
                plannerTab: 'product-specs'
            },
            {
                id: 'data',
                label: 'Stockpiles',
                icon: Database,
                plannerTab: 'data'
            },
            {
                id: 'resources',
                label: 'Wash Plant',
                icon: Layers,
                plannerTab: 'resources'
            },
            {
                id: 'geology',
                label: 'Block Model',
                icon: Layers,
                plannerTab: 'geology'
            }
        ]
    },
    {
        title: 'Data & Integration',
        items: [
            {
                id: 'import',
                label: 'Import Data',
                icon: Upload,
                plannerTab: 'import'
            },
            {
                id: 'integrations',
                label: 'Integrations',
                icon: Link,
                plannerTab: 'integrations'
            },
            {
                id: 'seed-data',
                label: 'Seed Demo Data',
                icon: Sparkles,
                path: '/app/seed-data',
                highlight: true
            },
            {
                id: 'settings',
                label: 'Settings',
                icon: Settings,
                plannerTab: 'settings'
            }
        ]
    }
];

// =============================================================================
// SIDEBAR ITEM COMPONENT
// =============================================================================

/**
 * Individual navigation item
 */
const SidebarItem = ({ icon: Icon, label, active, onClick, highlight, collapsed }) => (
    <button
        onClick={onClick}
        className={clsx(
            'w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-all duration-200 relative group',
            highlight
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
                <span className="truncate">{label}</span>
                {highlight && (
                    <span className="ml-auto px-1.5 py-0.5 text-[10px] bg-emerald-500/20 text-emerald-400 rounded font-semibold">
                        NEW
                    </span>
                )}
            </>
        )}

        {/* Tooltip for collapsed state */}
        {collapsed && (
            <span className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity shadow-lg">
                {label}
            </span>
        )}
    </button>
);

// =============================================================================
// MAIN SIDEBAR COMPONENT
// =============================================================================

/**
 * Main Sidebar Navigation Component
 * 
 * Features:
 * - Unified route-based navigation
 * - Site selector
 * - Collapsible design
 * - User profile display
 */
const Sidebar = ({ collapsed = false, onToggleCollapse }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { sites, currentSiteId, currentSite, selectSite, loading } = useSite();

    // ==========================================================================
    // NAVIGATION LOGIC
    // ==========================================================================

    /**
     * Handle navigation item click
     * Routes to path or PlannerWorkspace with tab param
     */
    const handleNavClick = (item) => {
        if (item.path) {
            navigate(item.path);
        } else if (item.plannerTab) {
            navigate(`/app/planner?tab=${item.plannerTab}`);
        }
    };

    /**
     * Determine if an item is active based on current location
     */
    const isItemActive = useMemo(() => {
        return (item) => {
            // Check direct path match
            if (item.path && location.pathname === item.path) {
                return true;
            }

            // Check planner tab match
            if (item.plannerTab && location.pathname === '/app/planner') {
                const searchParams = new URLSearchParams(location.search);
                const currentTab = searchParams.get('tab') || 'reporting';
                return currentTab === item.plannerTab;
            }

            return false;
        };
    }, [location.pathname, location.search]);

    /**
     * Handle logout
     */
    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    // ==========================================================================
    // RENDER
    // ==========================================================================

    return (
        <aside
            className={clsx(
                'h-full flex flex-col bg-slate-950 border-r border-slate-800 transition-all duration-300',
                collapsed ? 'w-16' : 'w-64'
            )}
        >
            {/* Logo & Collapse Toggle */}
            <div className={clsx(
                'h-14 flex items-center border-b border-slate-800 px-4',
                collapsed ? 'justify-center' : 'justify-between'
            )}>
                {!collapsed && (
                    <button
                        onClick={() => navigate('/app/dashboard')}
                        className="hover:opacity-80 transition-opacity"
                    >
                        <h1 className="text-lg font-bold text-white tracking-tight">
                            MineOpt<span className="text-blue-500">Pro</span>
                        </h1>
                        <p className="text-[10px] text-slate-500 -mt-0.5">Enterprise Edition</p>
                    </button>
                )}

                {collapsed && (
                    <button
                        onClick={() => navigate('/app/dashboard')}
                        className="hover:opacity-80 transition-opacity"
                    >
                        <span className="text-lg font-bold text-blue-500">M</span>
                    </button>
                )}

                {onToggleCollapse && (
                    <button
                        onClick={onToggleCollapse}
                        className="p-1.5 hover:bg-slate-800 rounded-md text-slate-400 hover:text-white transition-colors"
                    >
                        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </button>
                )}
            </div>

            {/* Site Selector */}
            {!collapsed && (
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
                        <ChevronDown
                            size={14}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                        />
                    </div>
                    {currentSite && (
                        <p className="text-xs text-slate-600 mt-1 truncate" title={currentSite.timezone}>
                            {currentSite.timezone || 'UTC'}
                        </p>
                    )}
                </div>
            )}

            {/* Navigation Items */}
            <nav className="flex-1 py-4 overflow-y-auto">
                {NAV_SECTIONS.map((section) => (
                    <div key={section.title} className="mb-4">
                        {!collapsed && (
                            <div className="px-4 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                                {section.title}
                            </div>
                        )}
                        {collapsed && (
                            <div className="mb-2 border-b border-slate-800 mx-4" />
                        )}
                        {section.items.map((item) => (
                            <SidebarItem
                                key={item.id}
                                icon={item.icon}
                                label={item.label}
                                active={isItemActive(item)}
                                highlight={item.highlight}
                                collapsed={collapsed}
                                onClick={() => handleNavClick(item)}
                            />
                        ))}
                    </div>
                ))}
            </nav>

            {/* User Profile & Logout */}
            <div className="border-t border-slate-800 p-3 space-y-2">
                {/* User Profile */}
                <div
                    className={clsx(
                        'flex items-center gap-3 px-2 py-2 rounded-lg',
                        'text-sm text-slate-400',
                        collapsed && 'justify-center'
                    )}
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                        SU
                    </div>
                    {!collapsed && (
                        <div className="text-left flex-1 min-w-0">
                            <div className="text-slate-200 text-sm font-medium truncate">Super User</div>
                            <div className="text-slate-500 text-xs">Administrator</div>
                        </div>
                    )}
                </div>

                {/* Logout Button */}
                <button
                    onClick={handleLogout}
                    className={clsx(
                        'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                        'text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors',
                        collapsed && 'justify-center'
                    )}
                    title="Logout"
                >
                    <LogOut size={18} />
                    {!collapsed && <span>Logout</span>}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
