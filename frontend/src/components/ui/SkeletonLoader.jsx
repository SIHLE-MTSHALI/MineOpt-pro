/**
 * SkeletonLoader.jsx - Loading Skeleton Components
 * 
 * Provides skeleton placeholders for loading states.
 */

import React from 'react';
import { clsx } from 'clsx';

const Skeleton = ({ variant = 'text', width, height, className, count = 1 }) => {
    const baseClasses = "animate-pulse bg-slate-700/50 rounded";

    const getVariantStyles = () => {
        switch (variant) {
            case 'text':
                return 'h-4 w-full';
            case 'title':
                return 'h-6 w-3/4';
            case 'circle':
                return 'rounded-full';
            case 'card':
                return 'h-32 w-full rounded-xl';
            case 'avatar':
                return 'h-10 w-10 rounded-full';
            case 'button':
                return 'h-10 w-24 rounded-lg';
            case 'table-row':
                return 'h-12 w-full';
            default:
                return '';
        }
    };

    const style = {
        ...(width && { width }),
        ...(height && { height })
    };

    if (count > 1) {
        return (
            <div className="space-y-2">
                {Array.from({ length: count }).map((_, i) => (
                    <div
                        key={i}
                        className={clsx(baseClasses, getVariantStyles(), className)}
                        style={style}
                    />
                ))}
            </div>
        );
    }

    return (
        <div
            className={clsx(baseClasses, getVariantStyles(), className)}
            style={style}
        />
    );
};

export const SkeletonCard = ({ className }) => (
    <div className={clsx("bg-slate-800/50 border border-slate-700 rounded-xl p-6", className)}>
        <Skeleton variant="title" className="mb-4" />
        <Skeleton variant="text" count={3} />
    </div>
);

export const SkeletonTable = ({ rows = 5 }) => (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
        <div className="bg-slate-900/50 px-4 py-3 border-b border-slate-700">
            <div className="flex gap-4">
                <Skeleton width="100px" />
                <Skeleton width="150px" />
                <Skeleton width="80px" />
                <Skeleton width="120px" />
            </div>
        </div>
        {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="px-4 py-3 border-b border-slate-700/50 flex gap-4">
                <Skeleton width="100px" />
                <Skeleton width="150px" />
                <Skeleton width="80px" />
                <Skeleton width="120px" />
            </div>
        ))}
    </div>
);

export const SkeletonDashboard = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
        {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                <Skeleton variant="text" width="60%" className="mb-2" />
                <Skeleton variant="title" width="40%" className="mb-4" />
                <Skeleton variant="text" width="80%" />
            </div>
        ))}
    </div>
);

export const SkeletonChart = ({ height = 200 }) => (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <Skeleton variant="title" width="30%" className="mb-4" />
        <Skeleton height={height} className="rounded-lg" />
    </div>
);

export default Skeleton;
