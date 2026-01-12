/**
 * AnimatedNumber.jsx - Animated counting number display
 * 
 * Features:
 * - Smooth counting animation from 0 to target value
 * - Configurable duration and format
 * - Supports decimals and custom formatting
 */

import React, { useState, useEffect, useRef } from 'react';
import { clsx } from 'clsx';

const AnimatedNumber = ({
    value,
    duration = 1000,
    decimals = 0,
    prefix = '',
    suffix = '',
    className,
    formatFn = null // Custom format function
}) => {
    const [displayValue, setDisplayValue] = useState(0);
    const previousValue = useRef(0);
    const animationRef = useRef(null);

    useEffect(() => {
        const startValue = previousValue.current;
        const endValue = typeof value === 'number' ? value : parseFloat(value) || 0;
        const startTime = Date.now();

        const animate = () => {
            const now = Date.now();
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = startValue + (endValue - startValue) * easeOut;

            setDisplayValue(currentValue);

            if (progress < 1) {
                animationRef.current = requestAnimationFrame(animate);
            } else {
                setDisplayValue(endValue);
                previousValue.current = endValue;
            }
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [value, duration]);

    const formattedValue = formatFn
        ? formatFn(displayValue)
        : displayValue.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });

    return (
        <span className={clsx('tabular-nums', className)}>
            {prefix}{formattedValue}{suffix}
        </span>
    );
};

// Preset formatters for common use cases
AnimatedNumber.formatTonnes = (value) => {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
    }
    return Math.round(value).toLocaleString();
};

AnimatedNumber.formatPercent = (value) => {
    return value.toFixed(1) + '%';
};

AnimatedNumber.formatCurrency = (value) => {
    return '$' + value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

export default AnimatedNumber;
