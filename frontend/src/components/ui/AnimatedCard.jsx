/**
 * AnimatedCard.jsx - Reusable animated card component
 * 
 * Features:
 * - Entrance animation on mount
 * - Hover lift effect
 * - Consistent styling with design system
 * - Optional click handler for interactive cards
 */

import React from 'react';
import { clsx } from 'clsx';

const AnimatedCard = ({
    children,
    className,
    onClick,
    delay = 0,
    variant = 'default', // default, elevated, glass
    hover = true,
    padding = true,
    animate = true
}) => {
    const baseStyles = 'rounded-xl border transition-all duration-200';

    const variantStyles = {
        default: 'bg-slate-800/50 border-slate-700',
        elevated: 'bg-slate-800 border-slate-700 shadow-lg',
        glass: 'bg-slate-800/30 backdrop-blur-sm border-slate-700/50'
    };

    const hoverStyles = hover
        ? 'hover:border-slate-600 hover:shadow-lg hover:-translate-y-0.5'
        : '';

    const interactiveStyles = onClick
        ? 'cursor-pointer active:scale-[0.99]'
        : '';

    const animationStyle = animate
        ? {
            animation: 'slideUp 0.3s ease-out forwards',
            animationDelay: `${delay}ms`,
            opacity: 0
        }
        : {};

    return (
        <div
            className={clsx(
                baseStyles,
                variantStyles[variant],
                hoverStyles,
                interactiveStyles,
                padding && 'p-5',
                className
            )}
            style={animationStyle}
            onClick={onClick}
        >
            {children}
        </div>
    );
};

// Subcomponents for consistent card structure
AnimatedCard.Header = ({ children, className }) => (
    <div className={clsx('flex items-center justify-between mb-4', className)}>
        {children}
    </div>
);

AnimatedCard.Title = ({ children, icon: Icon, className }) => (
    <h3 className={clsx('text-sm font-semibold text-white flex items-center gap-2', className)}>
        {Icon && <Icon size={18} className="text-blue-400" />}
        {children}
    </h3>
);

AnimatedCard.Content = ({ children, className }) => (
    <div className={clsx('', className)}>
        {children}
    </div>
);

AnimatedCard.Footer = ({ children, className }) => (
    <div className={clsx('mt-4 pt-4 border-t border-slate-700', className)}>
        {children}
    </div>
);

export default AnimatedCard;
