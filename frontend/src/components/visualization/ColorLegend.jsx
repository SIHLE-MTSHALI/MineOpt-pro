/**
 * ColorLegend Component - Phase 4 3D Visualization
 * 
 * Displays a color ramp legend for interpreting visualization colors.
 * Used alongside BoreholeRenderer and BlockModelRenderer.
 */

import React, { useMemo } from 'react';

const COLOR_RAMPS = {
    viridis: [
        { pos: 0, color: '#440154' },
        { pos: 0.25, color: '#3B528B' },
        { pos: 0.5, color: '#21918C' },
        { pos: 0.75, color: '#5EC962' },
        { pos: 1, color: '#FDE725' }
    ],
    plasma: [
        { pos: 0, color: '#0D0887' },
        { pos: 0.25, color: '#7E03A8' },
        { pos: 0.5, color: '#CC4778' },
        { pos: 0.75, color: '#F89540' },
        { pos: 1, color: '#F0F921' }
    ],
    coal: [
        { pos: 0, color: '#1A1A1A' },
        { pos: 0.25, color: '#4D331A' },
        { pos: 0.5, color: '#806633' },
        { pos: 0.75, color: '#B3994D' },
        { pos: 1, color: '#E6D980' }
    ],
    redYellowGreen: [
        { pos: 0, color: '#D73027' },
        { pos: 0.25, color: '#FC8D59' },
        { pos: 0.5, color: '#FEE08B' },
        { pos: 0.75, color: '#91CF60' },
        { pos: 1, color: '#1A9850' }
    ]
};

const ColorLegend = ({
    title = 'Quality Value',
    minValue = 0,
    maxValue = 100,
    unit = '',
    colorRamp = 'viridis',
    orientation = 'vertical',
    width = 200,
    height = 20,
    showLabels = true,
    numTicks = 5,
    style = {}
}) => {
    // Generate gradient CSS
    const gradientStyle = useMemo(() => {
        const ramp = COLOR_RAMPS[colorRamp] || COLOR_RAMPS.viridis;
        const stops = ramp.map(s => `${s.color} ${s.pos * 100}%`).join(', ');

        if (orientation === 'vertical') {
            return `linear-gradient(to top, ${stops})`;
        }
        return `linear-gradient(to right, ${stops})`;
    }, [colorRamp, orientation]);

    // Generate tick values
    const ticks = useMemo(() => {
        const values = [];
        for (let i = 0; i < numTicks; i++) {
            const t = i / (numTicks - 1);
            const value = minValue + t * (maxValue - minValue);
            values.push({
                value,
                position: t * 100,
                label: value.toFixed(value < 10 ? 1 : 0)
            });
        }
        return values;
    }, [minValue, maxValue, numTicks]);

    const isVertical = orientation === 'vertical';

    return (
        <div
            style={{
                display: 'flex',
                flexDirection: isVertical ? 'row' : 'column',
                alignItems: 'center',
                padding: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                fontSize: '12px',
                ...style
            }}
        >
            {/* Title */}
            {title && (
                <div style={{
                    fontWeight: 600,
                    color: '#374151',
                    marginBottom: isVertical ? 0 : 8,
                    marginRight: isVertical ? 12 : 0,
                    writingMode: isVertical ? 'vertical-rl' : 'horizontal-tb',
                    transform: isVertical ? 'rotate(180deg)' : 'none'
                }}>
                    {title} {unit && `(${unit})`}
                </div>
            )}

            {/* Gradient bar with ticks */}
            <div style={{
                display: 'flex',
                flexDirection: isVertical ? 'row' : 'column',
                alignItems: 'stretch'
            }}>
                {/* Tick labels on left/top */}
                {showLabels && (
                    <div style={{
                        display: 'flex',
                        flexDirection: isVertical ? 'column' : 'row',
                        justifyContent: 'space-between',
                        [isVertical ? 'height' : 'width']: isVertical ? height : width,
                        [isVertical ? 'marginRight' : 'marginBottom']: 4,
                        [isVertical ? 'flexDirection' : '']: isVertical ? 'column-reverse' : ''
                    }}>
                        {ticks.map((tick, idx) => (
                            <span
                                key={idx}
                                style={{
                                    color: '#6B7280',
                                    fontSize: '10px',
                                    textAlign: isVertical ? 'right' : 'center'
                                }}
                            >
                                {tick.label}
                            </span>
                        ))}
                    </div>
                )}

                {/* Color bar */}
                <div
                    style={{
                        [isVertical ? 'width' : 'height']: 16,
                        [isVertical ? 'height' : 'width']: isVertical ? height : width,
                        background: gradientStyle,
                        borderRadius: '4px',
                        border: '1px solid #E5E7EB'
                    }}
                />
            </div>
        </div>
    );
};

export default ColorLegend;
