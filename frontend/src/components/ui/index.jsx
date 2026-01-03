/**
 * MineOpt Pro - UI Component Library
 * ====================================
 * 
 * Reusable React components using the design system.
 * All components use CSS classes from design-system.css
 */

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility function for combining class names
export function cn(...inputs) {
    return twMerge(clsx(inputs));
}

// ============================================
// BUTTON COMPONENT
// ============================================

export const Button = React.forwardRef(({
    children,
    variant = 'primary',
    size = 'default',
    className,
    disabled,
    loading,
    leftIcon,
    rightIcon,
    ...props
}, ref) => {
    const variants = {
        primary: 'btn-primary',
        secondary: 'btn-secondary',
        accent: 'btn-accent',
        ghost: 'btn-ghost',
        danger: 'btn-danger',
    };

    const sizes = {
        sm: 'btn-sm',
        default: '',
        lg: 'btn-lg',
        icon: 'btn-icon',
        'icon-sm': 'btn-icon-sm',
    };

    return (
        <button
            ref={ref}
            className={cn(
                'btn',
                variants[variant],
                sizes[size],
                loading && 'opacity-75',
                className
            )}
            disabled={disabled || loading}
            {...props}
        >
            {loading ? (
                <span className="animate-spin">⟳</span>
            ) : (
                <>
                    {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
                    {children}
                    {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
                </>
            )}
        </button>
    );
});

Button.displayName = 'Button';


// ============================================
// INPUT COMPONENT
// ============================================

export const Input = React.forwardRef(({
    type = 'text',
    label,
    error,
    className,
    containerClassName,
    ...props
}, ref) => {
    return (
        <div className={cn('flex flex-col gap-1', containerClassName)}>
            {label && (
                <label className="text-xs font-medium text-neutral-400">
                    {label}
                </label>
            )}
            <input
                ref={ref}
                type={type}
                className={cn(
                    'input',
                    error && 'border-danger-500 focus:border-danger-500',
                    className
                )}
                {...props}
            />
            {error && (
                <span className="text-xs text-danger-400">{error}</span>
            )}
        </div>
    );
});

Input.displayName = 'Input';


// ============================================
// SELECT COMPONENT
// ============================================

export const Select = React.forwardRef(({
    options,
    label,
    placeholder,
    error,
    className,
    containerClassName,
    ...props
}, ref) => {
    return (
        <div className={cn('flex flex-col gap-1', containerClassName)}>
            {label && (
                <label className="text-xs font-medium text-neutral-400">
                    {label}
                </label>
            )}
            <select
                ref={ref}
                className={cn(
                    'input select',
                    error && 'border-danger-500',
                    className
                )}
                {...props}
            >
                {placeholder && (
                    <option value="" disabled>
                        {placeholder}
                    </option>
                )}
                {options?.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
            {error && (
                <span className="text-xs text-danger-400">{error}</span>
            )}
        </div>
    );
});

Select.displayName = 'Select';


// ============================================
// CARD COMPONENT
// ============================================

export function Card({
    children,
    variant = 'default',
    interactive = false,
    className,
    ...props
}) {
    const variants = {
        default: 'card',
        elevated: 'card-elevated',
        glass: 'glass-panel',
    };

    return (
        <div
            className={cn(
                variants[variant],
                interactive && 'card-interactive',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ children, className, ...props }) {
    return (
        <div className={cn('pb-3 border-b border-neutral-800 mb-4', className)} {...props}>
            {children}
        </div>
    );
}

export function CardTitle({ children, className, ...props }) {
    return (
        <h3 className={cn('text-sm font-semibold text-white', className)} {...props}>
            {children}
        </h3>
    );
}

export function CardDescription({ children, className, ...props }) {
    return (
        <p className={cn('text-xs text-neutral-400 mt-1', className)} {...props}>
            {children}
        </p>
    );
}

export function CardContent({ children, className, ...props }) {
    return (
        <div className={cn('', className)} {...props}>
            {children}
        </div>
    );
}


// ============================================
// BADGE COMPONENT
// ============================================

export function Badge({
    children,
    variant = 'neutral',
    className,
    ...props
}) {
    const variants = {
        primary: 'badge-primary',
        success: 'badge-success',
        warning: 'badge-warning',
        danger: 'badge-danger',
        neutral: 'badge-neutral',
    };

    return (
        <span
            className={cn('badge', variants[variant], className)}
            {...props}
        >
            {children}
        </span>
    );
}


// ============================================
// STATUS INDICATOR
// ============================================

export function StatusDot({
    status = 'inactive',
    className,
    ...props
}) {
    const statuses = {
        active: 'status-active',
        pending: 'status-pending',
        error: 'status-error',
        inactive: 'status-inactive',
    };

    return (
        <span
            className={cn('status-dot', statuses[status], className)}
            {...props}
        />
    );
}


// ============================================
// LOADING SPINNER
// ============================================

export function Spinner({ size = 'default', className }) {
    const sizes = {
        sm: 'w-4 h-4',
        default: 'w-6 h-6',
        lg: 'w-8 h-8',
    };

    return (
        <svg
            className={cn('animate-spin', sizes[size], className)}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
        >
            <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
            />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
        </svg>
    );
}


// ============================================
// TOOLTIP
// ============================================

export function Tooltip({ children, content, className }) {
    return (
        <span
            className={cn('tooltip', className)}
            data-tooltip={content}
        >
            {children}
        </span>
    );
}


// ============================================
// PROGRESS BAR
// ============================================

export function Progress({
    value = 0,
    max = 100,
    variant = 'primary',
    showLabel = false,
    className,
}) {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    const variants = {
        primary: 'bg-gradient-to-r from-primary-500 to-primary-400',
        success: 'bg-gradient-to-r from-success-500 to-success-400',
        warning: 'bg-gradient-to-r from-warning-500 to-warning-400',
        danger: 'bg-gradient-to-r from-danger-500 to-danger-400',
    };

    return (
        <div className={cn('w-full', className)}>
            <div className="quality-bar">
                <div
                    className={cn('quality-bar-fill', variants[variant])}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            {showLabel && (
                <span className="text-xs text-neutral-400 mt-1">
                    {Math.round(percentage)}%
                </span>
            )}
        </div>
    );
}


// ============================================
// NOTIFICATION TOAST
// ============================================

export function Toast({
    message,
    type = 'info',
    onClose,
    className,
}) {
    const types = {
        info: 'bg-primary-600',
        success: 'bg-success-600',
        warning: 'bg-warning-600',
        error: 'bg-danger-600',
    };

    return (
        <div
            className={cn(
                'fixed top-4 left-1/2 -translate-x-1/2 z-50',
                'px-4 py-3 rounded-lg shadow-xl',
                'text-sm font-medium text-white',
                'animate-slide-down',
                types[type],
                className
            )}
        >
            <div className="flex items-center gap-3">
                <span>{message}</span>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-white/80 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                )}
            </div>
        </div>
    );
}


// ============================================
// SKELETON LOADER
// ============================================

export function Skeleton({ className, ...props }) {
    return (
        <div
            className={cn(
                'bg-neutral-800 rounded animate-pulse',
                className
            )}
            {...props}
        />
    );
}

export function SkeletonText({ lines = 3, className }) {
    return (
        <div className={cn('space-y-2', className)}>
            {Array.from({ length: lines }).map((_, i) => (
                <Skeleton
                    key={i}
                    className="h-4"
                    style={{
                        width: i === lines - 1 ? '60%' : '100%',
                    }}
                />
            ))}
        </div>
    );
}


// ============================================
// DIVIDER
// ============================================

export function Divider({ className, ...props }) {
    return (
        <hr
            className={cn('border-t border-neutral-800 my-4', className)}
            {...props}
        />
    );
}


// ============================================
// KPI CARD (Mining Dashboard Specific)
// ============================================

export function KpiCard({
    title,
    value,
    unit,
    trend,
    trendValue,
    icon,
    variant = 'default',
    className,
}) {
    const trendColors = {
        up: 'text-success-400',
        down: 'text-danger-400',
        neutral: 'text-neutral-400',
    };

    return (
        <Card variant="elevated" className={cn('p-4', className)}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs text-neutral-400 uppercase tracking-wider mb-1">
                        {title}
                    </p>
                    <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold text-white">{value}</span>
                        {unit && (
                            <span className="text-sm text-neutral-400">{unit}</span>
                        )}
                    </div>
                    {trend && (
                        <div className={cn('flex items-center gap-1 mt-2 text-xs', trendColors[trend])}>
                            {trend === 'up' && '↑'}
                            {trend === 'down' && '↓'}
                            {trend === 'neutral' && '→'}
                            <span>{trendValue}</span>
                        </div>
                    )}
                </div>
                {icon && (
                    <div className="p-2 bg-primary-500/10 rounded-lg text-primary-400">
                        {icon}
                    </div>
                )}
            </div>
        </Card>
    );
}


// ============================================
// EXPORTS
// ============================================

export default {
    Button,
    Input,
    Select,
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    Badge,
    StatusDot,
    Spinner,
    Tooltip,
    Progress,
    Toast,
    Skeleton,
    SkeletonText,
    Divider,
    KpiCard,
    cn,
};
