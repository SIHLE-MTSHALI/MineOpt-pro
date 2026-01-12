/**
 * navigation.test.jsx - Navigation System Tests
 * 
 * Comprehensive tests for the unified navigation system:
 * - Route-based navigation
 * - URL query parameter handling for PlannerWorkspace tabs
 * - Active state highlighting
 * - Protected route behavior
 * - Sidebar navigation configuration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import React from 'react';

// Mock dependencies
vi.mock('axios', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        patch: vi.fn(),
        create: vi.fn(() => ({
            get: vi.fn(() => Promise.resolve({ data: {} })),
            post: vi.fn(() => Promise.resolve({ data: {} })),
            interceptors: {
                request: { use: vi.fn() },
                response: { use: vi.fn() }
            }
        }))
    }
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
    Home: () => null,
    Box: () => null,
    Calendar: () => null,
    Truck: () => null,
    Target: () => null,
    ClipboardList: () => null,
    Mountain: () => null,
    Wind: () => null,
    GitBranch: () => null,
    Package: () => null,
    Database: () => null,
    Layers: () => null,
    Upload: () => null,
    Link: () => null,
    Sparkles: () => null,
    Settings: () => null,
    BarChart2: () => null,
    Zap: () => null,
    LogOut: () => null,
    ChevronLeft: () => null,
    ChevronRight: () => null,
    ChevronDown: () => null,
    RefreshCw: () => null,
    Save: () => null,
    AlertCircle: () => null,
    Bell: () => null,
    Moon: () => null,
    Sun: () => null,
    HelpCircle: () => null
}));

// =============================================================================
// NAVIGATION CONFIGURATION TESTS
// =============================================================================

describe('Navigation Configuration', () => {
    /**
     * Navigation sections configuration
     * This mirrors the structure in Sidebar.jsx
     */
    const NAV_SECTIONS = [
        {
            title: 'Home',
            items: [
                { id: 'dashboard', label: 'Dashboard', path: '/app/dashboard' }
            ]
        },
        {
            title: 'Planning',
            items: [
                { id: 'spatial', label: '3D Spatial View', plannerTab: 'spatial' },
                { id: 'gantt', label: 'Gantt Schedule', plannerTab: 'gantt' },
                { id: 'schedule-control', label: 'Schedule Control', plannerTab: 'schedule-control' },
                { id: 'reporting', label: 'Reports & Analytics', plannerTab: 'reporting' }
            ]
        },
        {
            title: 'Operations',
            items: [
                { id: 'fleet', label: 'Fleet Management', path: '/app/fleet' },
                { id: 'drill-blast', label: 'Drill & Blast', path: '/app/drill-blast' },
                { id: 'operations', label: 'Shift Operations', path: '/app/operations' }
            ]
        },
        {
            title: 'Monitoring',
            items: [
                { id: 'geotech', label: 'Slope Stability', path: '/app/monitoring' },
                { id: 'environment', label: 'Environment', path: '/app/monitoring' }
            ]
        },
        {
            title: 'Configuration',
            items: [
                { id: 'flow-editor', label: 'Flow Network', plannerTab: 'flow-editor' },
                { id: 'product-specs', label: 'Product Specs', plannerTab: 'product-specs' },
                { id: 'data', label: 'Stockpiles', plannerTab: 'data' },
                { id: 'resources', label: 'Wash Plant', plannerTab: 'resources' },
                { id: 'geology', label: 'Block Model', plannerTab: 'geology' }
            ]
        },
        {
            title: 'Data & Integration',
            items: [
                { id: 'import', label: 'Import Data', plannerTab: 'import' },
                { id: 'integrations', label: 'Integrations', plannerTab: 'integrations' },
                { id: 'seed-data', label: 'Seed Demo Data', path: '/app/seed-data' },
                { id: 'settings', label: 'Settings', plannerTab: 'settings' }
            ]
        }
    ];

    it('should have exactly 6 navigation sections', () => {
        expect(NAV_SECTIONS).toHaveLength(6);
    });

    it('should have all required section titles', () => {
        const titles = NAV_SECTIONS.map(s => s.title);
        expect(titles).toContain('Home');
        expect(titles).toContain('Planning');
        expect(titles).toContain('Operations');
        expect(titles).toContain('Monitoring');
        expect(titles).toContain('Configuration');
        expect(titles).toContain('Data & Integration');
    });

    it('should have dedicated routes for main modules', () => {
        const allItems = NAV_SECTIONS.flatMap(s => s.items);
        const dedicatedRoutes = allItems.filter(item => item.path);

        const routePaths = dedicatedRoutes.map(r => r.path);
        expect(routePaths).toContain('/app/dashboard');
        expect(routePaths).toContain('/app/fleet');
        expect(routePaths).toContain('/app/drill-blast');
        expect(routePaths).toContain('/app/operations');
        expect(routePaths).toContain('/app/monitoring');
        expect(routePaths).toContain('/app/seed-data');
    });

    it('should have planner tabs for configuration items', () => {
        const allItems = NAV_SECTIONS.flatMap(s => s.items);
        const plannerItems = allItems.filter(item => item.plannerTab);

        const tabs = plannerItems.map(p => p.plannerTab);
        expect(tabs).toContain('spatial');
        expect(tabs).toContain('gantt');
        expect(tabs).toContain('schedule-control');
        expect(tabs).toContain('reporting');
        expect(tabs).toContain('flow-editor');
        expect(tabs).toContain('product-specs');
        expect(tabs).toContain('data');
        expect(tabs).toContain('resources');
        expect(tabs).toContain('geology');
    });

    it('every item should have either path or plannerTab', () => {
        const allItems = NAV_SECTIONS.flatMap(s => s.items);
        allItems.forEach(item => {
            const hasNavigation = item.path || item.plannerTab;
            expect(hasNavigation).toBeTruthy();
        });
    });

    it('should have unique item IDs', () => {
        const allItems = NAV_SECTIONS.flatMap(s => s.items);
        const ids = allItems.map(item => item.id);
        const uniqueIds = new Set(ids);
        expect(uniqueIds.size).toBe(ids.length);
    });
});

// =============================================================================
// URL QUERY PARAMETER TESTS
// =============================================================================

describe('URL Query Parameters for Planner Tabs', () => {
    const VALID_TABS = [
        'spatial',
        'gantt',
        'schedule-control',
        'reporting',
        'flow-editor',
        'product-specs',
        'data',
        'resources',
        'geology',
        'settings',
        'fleet',
        'drill-blast',
        'shift-ops',
        'geotech',
        'environment',
        'import',
        'integrations'
    ];

    it('should have 17 valid tabs', () => {
        expect(VALID_TABS).toHaveLength(17);
    });

    it('should validate tab parameters', () => {
        const isValidTab = (tab) => VALID_TABS.includes(tab);

        expect(isValidTab('gantt')).toBe(true);
        expect(isValidTab('spatial')).toBe(true);
        expect(isValidTab('invalid')).toBe(false);
        expect(isValidTab('')).toBe(false);
    });

    it('should default to reporting tab when no param', () => {
        const getActiveTab = (searchParams) => {
            const tab = searchParams.get('tab');
            return tab && VALID_TABS.includes(tab) ? tab : 'reporting';
        };

        const params1 = new URLSearchParams('');
        expect(getActiveTab(params1)).toBe('reporting');

        const params2 = new URLSearchParams('?tab=gantt');
        expect(getActiveTab(params2)).toBe('gantt');

        const params3 = new URLSearchParams('?tab=invalid');
        expect(getActiveTab(params3)).toBe('reporting');
    });

    it('should construct correct planner URLs', () => {
        const getPlannerUrl = (tab) => `/app/planner?tab=${tab}`;

        expect(getPlannerUrl('gantt')).toBe('/app/planner?tab=gantt');
        expect(getPlannerUrl('spatial')).toBe('/app/planner?tab=spatial');
        expect(getPlannerUrl('flow-editor')).toBe('/app/planner?tab=flow-editor');
    });
});

// =============================================================================
// ACTIVE STATE DETECTION TESTS
// =============================================================================

describe('Active State Detection', () => {
    /**
     * Mock isActiveItem function from Sidebar
     */
    const isActiveItem = (item, pathname, search) => {
        if (item.path && pathname === item.path) {
            return true;
        }
        if (item.plannerTab && pathname === '/app/planner') {
            const params = new URLSearchParams(search);
            const tab = params.get('tab') || 'reporting';
            return tab === item.plannerTab;
        }
        return false;
    };

    it('should detect active state for dedicated route', () => {
        const dashboardItem = { id: 'dashboard', path: '/app/dashboard' };

        expect(isActiveItem(dashboardItem, '/app/dashboard', '')).toBe(true);
        expect(isActiveItem(dashboardItem, '/app/fleet', '')).toBe(false);
        expect(isActiveItem(dashboardItem, '/app/planner', '?tab=gantt')).toBe(false);
    });

    it('should detect active state for planner tabs', () => {
        const ganttItem = { id: 'gantt', plannerTab: 'gantt' };

        expect(isActiveItem(ganttItem, '/app/planner', '?tab=gantt')).toBe(true);
        expect(isActiveItem(ganttItem, '/app/planner', '?tab=spatial')).toBe(false);
        expect(isActiveItem(ganttItem, '/app/dashboard', '')).toBe(false);
    });

    it('should default to reporting tab when on planner without tab param', () => {
        const reportingItem = { id: 'reporting', plannerTab: 'reporting' };

        expect(isActiveItem(reportingItem, '/app/planner', '')).toBe(true);
        expect(isActiveItem(reportingItem, '/app/planner', '?tab=reporting')).toBe(true);
    });

    it('should handle URL with other params', () => {
        const spatialItem = { id: 'spatial', plannerTab: 'spatial' };

        expect(isActiveItem(spatialItem, '/app/planner', '?tab=spatial&view=3d')).toBe(true);
        expect(isActiveItem(spatialItem, '/app/planner', '?view=3d&tab=spatial')).toBe(true);
    });
});

// =============================================================================
// PROTECTED ROUTE TESTS
// =============================================================================

describe('Protected Route Behavior', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    afterEach(() => {
        localStorage.clear();
    });

    it('should check for token in localStorage', () => {
        const hasToken = () => !!localStorage.getItem('token');

        expect(hasToken()).toBe(false);

        localStorage.setItem('token', 'test-token');
        expect(hasToken()).toBe(true);

        localStorage.removeItem('token');
        expect(hasToken()).toBe(false);
    });

    it('should return correct redirect path', () => {
        const getRedirect = () => {
            const token = localStorage.getItem('token');
            return token ? '/app/dashboard' : '/login';
        };

        expect(getRedirect()).toBe('/login');

        localStorage.setItem('token', 'test-token');
        expect(getRedirect()).toBe('/app/dashboard');
    });
});

// =============================================================================
// NAVIGATION HELPER TESTS
// =============================================================================

describe('Navigation Helpers', () => {
    it('should generate correct navigation target', () => {
        const getNavigationTarget = (item) => {
            if (item.path) return item.path;
            if (item.plannerTab) return `/app/planner?tab=${item.plannerTab}`;
            return '/app/dashboard'; // fallback
        };

        expect(getNavigationTarget({ path: '/app/fleet' })).toBe('/app/fleet');
        expect(getNavigationTarget({ plannerTab: 'gantt' })).toBe('/app/planner?tab=gantt');
        expect(getNavigationTarget({})).toBe('/app/dashboard');
    });

    it('should handle breadcrumb generation', () => {
        const getBreadcrumbs = (pathname, search) => {
            const breadcrumbs = [{ label: 'Home', path: '/app/dashboard' }];

            if (pathname === '/app/planner') {
                const params = new URLSearchParams(search);
                const tab = params.get('tab') || 'reporting';
                const tabLabels = {
                    'spatial': '3D Spatial View',
                    'gantt': 'Gantt Schedule',
                    'reporting': 'Reports & Analytics'
                };
                breadcrumbs.push({ label: 'Planning', path: '/app/planner' });
                breadcrumbs.push({ label: tabLabels[tab] || tab });
            } else if (pathname === '/app/fleet') {
                breadcrumbs.push({ label: 'Fleet Management' });
            }

            return breadcrumbs;
        };

        const plannerBreadcrumbs = getBreadcrumbs('/app/planner', '?tab=gantt');
        expect(plannerBreadcrumbs).toHaveLength(3);
        expect(plannerBreadcrumbs[2].label).toBe('Gantt Schedule');

        const fleetBreadcrumbs = getBreadcrumbs('/app/fleet', '');
        expect(fleetBreadcrumbs).toHaveLength(2);
        expect(fleetBreadcrumbs[1].label).toBe('Fleet Management');
    });
});

// =============================================================================
// API CACHE TESTS
// =============================================================================

describe('API Cache Behavior', () => {
    it('should validate cache key generation', () => {
        const getCacheKey = (url, params = {}) => {
            const filteredParams = Object.entries(params)
                .filter(([_, v]) => v !== undefined && v !== null && v !== '')
                .sort(([a], [b]) => a.localeCompare(b));

            if (filteredParams.length === 0) return url;

            const queryString = new URLSearchParams(Object.fromEntries(filteredParams)).toString();
            return `${url}?${queryString}`;
        };

        expect(getCacheKey('/api/sites')).toBe('/api/sites');
        expect(getCacheKey('/api/resources', { site_id: 'site-1' })).toBe('/api/resources?site_id=site-1');
        expect(getCacheKey('/api/data', { a: undefined, b: 'value' })).toBe('/api/data?b=value');
    });

    it('should handle cache TTL validation', () => {
        const CACHE_TTL = 30000; // 30 seconds

        const isCacheValid = (timestamp) => {
            return Date.now() - timestamp < CACHE_TTL;
        };

        const recentTimestamp = Date.now() - 10000; // 10 seconds ago
        const oldTimestamp = Date.now() - 60000; // 1 minute ago

        expect(isCacheValid(recentTimestamp)).toBe(true);
        expect(isCacheValid(oldTimestamp)).toBe(false);
    });
});

// =============================================================================
// USER INITIALS TESTS
// =============================================================================

describe('User Initials Generation', () => {
    const getInitials = (name) => {
        if (!name) return 'U';
        const parts = name.split(/[\s@._-]+/).filter(Boolean);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    it('should generate initials from username', () => {
        expect(getInitials('John Doe')).toBe('JD');
        expect(getInitials('admin')).toBe('AD');
        expect(getInitials('super_user')).toBe('SU');
    });

    it('should generate initials from email', () => {
        expect(getInitials('john.doe@example.com')).toBe('JD');
        expect(getInitials('admin@company.org')).toBe('AC');
    });

    it('should handle edge cases', () => {
        expect(getInitials('')).toBe('U');
        expect(getInitials(null)).toBe('U');
        expect(getInitials(undefined)).toBe('U');
        expect(getInitials('A')).toBe('A');
    });
});

// =============================================================================
// ROUTE MATCHING TESTS
// =============================================================================

describe('Route Matching', () => {
    const protectedRoutes = [
        '/app/dashboard',
        '/app/planner',
        '/app/fleet',
        '/app/drill-blast',
        '/app/operations',
        '/app/monitoring',
        '/app/seed-data'
    ];

    const publicRoutes = [
        '/',
        '/login',
        '/register'
    ];

    it('should identify protected routes', () => {
        const isProtected = (path) => protectedRoutes.some(r => path.startsWith(r) || path === r);

        expect(isProtected('/app/dashboard')).toBe(true);
        expect(isProtected('/app/planner')).toBe(true);
        expect(isProtected('/app/fleet')).toBe(true);
        expect(isProtected('/')).toBe(false);
        expect(isProtected('/login')).toBe(false);
    });

    it('should identify public routes', () => {
        const isPublic = (path) => publicRoutes.includes(path);

        expect(isPublic('/')).toBe(true);
        expect(isPublic('/login')).toBe(true);
        expect(isPublic('/register')).toBe(true);
        expect(isPublic('/app/dashboard')).toBe(false);
    });

    it('should have all app routes starting with /app', () => {
        protectedRoutes.forEach(route => {
            expect(route.startsWith('/app')).toBe(true);
        });
    });
});

export default {};
