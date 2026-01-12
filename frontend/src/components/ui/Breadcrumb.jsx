/**
 * Breadcrumb.jsx - Breadcrumb navigation component
 * 
 * Features:
 * - Auto-generates from current route
 * - Clickable navigation links
 * - Animated transitions
 * - Custom labels for routes
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { clsx } from 'clsx';

// Custom labels for routes
const routeLabels = {
    'app': 'App',
    'dashboard': 'Dashboard',
    'planner': 'Planner Workspace',
    'fleet': 'Fleet Management',
    'drill-blast': 'Drill & Blast',
    'operations': 'Operations',
    'monitoring': 'Monitoring',
    'seed-data': 'Seed Data'
};

const Breadcrumb = ({
    className,
    showHome = true,
    maxItems = 4
}) => {
    const location = useLocation();
    const pathnames = location.pathname.split('/').filter(x => x);

    // Don't show breadcrumb on root
    if (pathnames.length === 0) return null;

    // If too many items, collapse middle ones
    let displayPaths = pathnames;
    if (pathnames.length > maxItems) {
        displayPaths = [
            pathnames[0],
            '...',
            ...pathnames.slice(-2)
        ];
    }

    return (
        <nav
            className={clsx(
                'flex items-center text-sm animate-fade-in',
                className
            )}
            aria-label="Breadcrumb"
        >
            <ol className="flex items-center gap-1">
                {/* Home link */}
                {showHome && (
                    <li className="flex items-center">
                        <Link
                            to="/app/dashboard"
                            className="breadcrumb-item flex items-center gap-1 text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-slate-800/50"
                        >
                            <Home size={14} />
                        </Link>
                        <ChevronRight size={14} className="breadcrumb-separator text-slate-600 mx-1" />
                    </li>
                )}

                {/* Path segments */}
                {displayPaths.map((segment, index) => {
                    const isLast = index === displayPaths.length - 1;
                    const isEllipsis = segment === '...';

                    // Build the route path for this segment
                    const routeTo = '/' + pathnames.slice(0, pathnames.indexOf(segment) + 1).join('/');

                    // Get display label
                    const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');

                    if (isEllipsis) {
                        return (
                            <li key="ellipsis" className="flex items-center">
                                <span className="text-slate-500 px-1">...</span>
                                <ChevronRight size={14} className="breadcrumb-separator text-slate-600 mx-1" />
                            </li>
                        );
                    }

                    return (
                        <li key={segment} className="flex items-center">
                            {isLast ? (
                                <span className="breadcrumb-item text-white font-medium px-2 py-1">
                                    {label}
                                </span>
                            ) : (
                                <>
                                    <Link
                                        to={routeTo}
                                        className="breadcrumb-item text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800/50"
                                    >
                                        {label}
                                    </Link>
                                    <ChevronRight size={14} className="breadcrumb-separator text-slate-600 mx-1" />
                                </>
                            )}
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};

// Static breadcrumb for custom items
Breadcrumb.Static = ({ items, className }) => (
    <nav
        className={clsx('flex items-center text-sm', className)}
        aria-label="Breadcrumb"
    >
        <ol className="flex items-center gap-1">
            {items.map((item, index) => {
                const isLast = index === items.length - 1;
                return (
                    <li key={item.label} className="flex items-center">
                        {isLast ? (
                            <span className="text-white font-medium px-2 py-1">
                                {item.icon && <item.icon size={14} className="mr-1.5 inline" />}
                                {item.label}
                            </span>
                        ) : (
                            <>
                                {item.href ? (
                                    <Link
                                        to={item.href}
                                        className="text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800/50"
                                    >
                                        {item.icon && <item.icon size={14} className="mr-1.5 inline" />}
                                        {item.label}
                                    </Link>
                                ) : (
                                    <span className="text-slate-400 px-2 py-1">
                                        {item.icon && <item.icon size={14} className="mr-1.5 inline" />}
                                        {item.label}
                                    </span>
                                )}
                                <ChevronRight size={14} className="text-slate-600 mx-1" />
                            </>
                        )}
                    </li>
                );
            })}
        </ol>
    </nav>
);

export default Breadcrumb;
