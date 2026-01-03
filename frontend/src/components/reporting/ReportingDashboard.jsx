/**
 * ReportingDashboard.jsx - Enhanced Reporting Dashboard
 * 
 * Comprehensive reporting dashboard with:
 * - Inventory over time chart
 * - Quality trend line charts
 * - Spec compliance gauges
 * - Material flow Sankey diagram
 * - Export buttons (PDF, CSV)
 */

import React, { useState, useEffect } from 'react';
import {
    Download, FileText, Table, RefreshCw,
    TrendingUp, TrendingDown, Activity, Package,
    AlertTriangle, CheckCircle, BarChart2
} from 'lucide-react';

// Mock data for charts
const generateMockData = () => ({
    inventoryTrend: [
        { period: 'D1 DS', rom1: 25000, rom2: 18000, product: 12000 },
        { period: 'D1 NS', rom1: 28000, rom2: 15000, product: 14000 },
        { period: 'D2 DS', rom1: 32000, rom2: 20000, product: 16000 },
        { period: 'D2 NS', rom1: 29000, rom2: 22000, product: 18000 },
        { period: 'D3 DS', rom1: 26000, rom2: 19000, product: 20000 },
        { period: 'D3 NS', rom1: 30000, rom2: 21000, product: 22000 }
    ],
    qualityTrend: [
        { period: 'D1 DS', cv: 22.5, ash: 13.2, moisture: 8.5 },
        { period: 'D1 NS', cv: 21.8, ash: 14.1, moisture: 9.0 },
        { period: 'D2 DS', cv: 23.1, ash: 12.8, moisture: 8.2 },
        { period: 'D2 NS', cv: 22.9, ash: 13.5, moisture: 8.8 },
        { period: 'D3 DS', cv: 23.5, ash: 12.5, moisture: 8.0 },
        { period: 'D3 NS', cv: 24.0, ash: 12.0, moisture: 7.8 }
    ],
    sankeyFlows: [
        { from: 'Pit A', to: 'ROM 1', value: 15000 },
        { from: 'Pit A', to: 'ROM 2', value: 8000 },
        { from: 'Pit B', to: 'ROM 1', value: 10000 },
        { from: 'Pit C', to: 'Waste', value: 12000 },
        { from: 'ROM 1', to: 'Plant', value: 20000 },
        { from: 'ROM 2', to: 'Plant', value: 8000 },
        { from: 'Plant', to: 'Product', value: 18000 },
        { from: 'Plant', to: 'Discard', value: 10000 }
    ]
});

// Gauge Component
const ComplianceGauge = ({ label, value, target, min = 0, max = 100, unit = '%' }) => {
    const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
    const targetPercentage = ((target - min) / (max - min)) * 100;
    const isCompliant = Math.abs(value - target) <= (target * 0.05);

    const getColor = () => {
        if (isCompliant) return '#10b981';
        if (Math.abs(value - target) <= (target * 0.1)) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">{label}</span>
                {isCompliant ? (
                    <CheckCircle size={16} className="text-green-400" />
                ) : (
                    <AlertTriangle size={16} className="text-yellow-400" />
                )}
            </div>

            <div className="text-2xl font-bold text-white mb-2">
                {value.toFixed(1)}{unit}
            </div>

            {/* Gauge bar */}
            <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                    className="absolute h-full rounded-full transition-all"
                    style={{
                        width: `${percentage}%`,
                        backgroundColor: getColor()
                    }}
                />
                {/* Target marker */}
                <div
                    className="absolute w-0.5 h-5 bg-white -top-1"
                    style={{ left: `${targetPercentage}%` }}
                />
            </div>

            <div className="flex justify-between mt-1 text-xs text-slate-500">
                <span>Min: {min}</span>
                <span>Target: {target}</span>
                <span>Max: {max}</span>
            </div>
        </div>
    );
};

// Simple Bar Chart Component
const BarChart = ({ data, bars, height = 200 }) => {
    const maxValue = Math.max(...data.flatMap(d => bars.map(b => d[b.key] || 0)));

    return (
        <div className="space-y-2">
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mb-2">
                {bars.map(bar => (
                    <div key={bar.key} className="flex items-center space-x-2">
                        <div className="w-3 h-3 rounded" style={{ backgroundColor: bar.color }} />
                        <span className="text-xs text-slate-400">{bar.label}</span>
                    </div>
                ))}
            </div>

            {/* Chart */}
            <div className="flex items-end justify-between space-x-1" style={{ height }}>
                {data.map((item, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                        <div className="w-full flex items-end justify-center space-x-0.5" style={{ height: height - 20 }}>
                            {bars.map(bar => (
                                <div
                                    key={bar.key}
                                    className="flex-1 rounded-t transition-all hover:opacity-80"
                                    style={{
                                        height: `${(item[bar.key] / maxValue) * 100}%`,
                                        backgroundColor: bar.color,
                                        minWidth: '8px',
                                        maxWidth: '24px'
                                    }}
                                    title={`${bar.label}: ${item[bar.key]?.toLocaleString()}`}
                                />
                            ))}
                        </div>
                        <span className="text-xs text-slate-500 mt-1 truncate w-full text-center">{item.period}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// Line Chart Component
const LineChart = ({ data, lines, height = 200 }) => {
    const allValues = data.flatMap(d => lines.map(l => d[l.key] || 0));
    const maxValue = Math.max(...allValues);
    const minValue = Math.min(...allValues);
    const range = maxValue - minValue || 1;

    const getY = (value) => height - 20 - ((value - minValue) / range) * (height - 40);
    const getX = (index) => (index / (data.length - 1)) * 100;

    return (
        <div className="space-y-2">
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mb-2">
                {lines.map(line => (
                    <div key={line.key} className="flex items-center space-x-2">
                        <div className="w-3 h-0.5" style={{ backgroundColor: line.color }} />
                        <span className="text-xs text-slate-400">{line.label}</span>
                    </div>
                ))}
            </div>

            {/* SVG Chart */}
            <svg width="100%" height={height} className="overflow-visible">
                {/* Grid lines */}
                {[0, 25, 50, 75, 100].map(pct => (
                    <line
                        key={pct}
                        x1="0"
                        y1={height - 20 - (pct / 100) * (height - 40)}
                        x2="100%"
                        y2={height - 20 - (pct / 100) * (height - 40)}
                        stroke="#334155"
                        strokeWidth="1"
                        strokeDasharray="4"
                    />
                ))}

                {/* Lines */}
                {lines.map(line => (
                    <polyline
                        key={line.key}
                        fill="none"
                        stroke={line.color}
                        strokeWidth="2"
                        points={data.map((d, i) => `${getX(i)}%,${getY(d[line.key])}`).join(' ')}
                    />
                ))}

                {/* Data points */}
                {lines.map(line =>
                    data.map((d, i) => (
                        <circle
                            key={`${line.key}-${i}`}
                            cx={`${getX(i)}%`}
                            cy={getY(d[line.key])}
                            r="4"
                            fill={line.color}
                        >
                            <title>{`${line.label}: ${d[line.key]?.toFixed(2)}`}</title>
                        </circle>
                    ))
                )}

                {/* X-axis labels */}
                {data.map((d, i) => (
                    <text
                        key={i}
                        x={`${getX(i)}%`}
                        y={height - 5}
                        textAnchor="middle"
                        className="text-xs fill-slate-500"
                    >
                        {d.period}
                    </text>
                ))}
            </svg>
        </div>
    );
};

// Sankey Diagram (Simplified)
const SankeyDiagram = ({ flows }) => {
    // Group flows by source and destination
    const sources = [...new Set(flows.map(f => f.from))];
    const destinations = [...new Set(flows.map(f => f.to))];
    const allNodes = [...new Set([...sources, ...destinations])];

    const getNodeColor = (node) => {
        if (node.includes('Pit')) return '#f59e0b';
        if (node.includes('ROM')) return '#3b82f6';
        if (node.includes('Plant')) return '#10b981';
        if (node.includes('Product')) return '#8b5cf6';
        if (node.includes('Waste') || node.includes('Discard')) return '#6b7280';
        return '#64748b';
    };

    const totalFlow = flows.reduce((sum, f) => sum + f.value, 0);

    return (
        <div className="space-y-4">
            <div className="text-sm text-slate-400">
                Total Flow: {totalFlow.toLocaleString()} tonnes
            </div>

            {/* Simplified flow display */}
            <div className="space-y-2">
                {flows.map((flow, idx) => (
                    <div key={idx} className="flex items-center space-x-3">
                        <span
                            className="px-2 py-1 rounded text-xs text-white min-w-20 text-center"
                            style={{ backgroundColor: getNodeColor(flow.from) }}
                        >
                            {flow.from}
                        </span>

                        <div className="flex-1 relative">
                            <div
                                className="h-4 rounded bg-gradient-to-r opacity-60"
                                style={{
                                    width: `${(flow.value / totalFlow) * 100 * 2}%`,
                                    background: `linear-gradient(to right, ${getNodeColor(flow.from)}, ${getNodeColor(flow.to)})`
                                }}
                            />
                            <span className="absolute inset-0 flex items-center justify-center text-xs text-white font-medium">
                                {flow.value.toLocaleString()} t
                            </span>
                        </div>

                        <span
                            className="px-2 py-1 rounded text-xs text-white min-w-20 text-center"
                            style={{ backgroundColor: getNodeColor(flow.to) }}
                        >
                            {flow.to}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// Export Buttons
const ExportButtons = ({ onExport }) => (
    <div className="flex space-x-2">
        <button
            onClick={() => onExport('pdf')}
            className="flex items-center space-x-2 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-sm"
        >
            <FileText size={16} />
            <span>Export PDF</span>
        </button>
        <button
            onClick={() => onExport('csv')}
            className="flex items-center space-x-2 px-3 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-400 rounded-lg text-sm"
        >
            <Table size={16} />
            <span>Export CSV</span>
        </button>
    </div>
);

// Main Reporting Dashboard
const ReportingDashboard = ({ scheduleVersionId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        // Load mock data
        setData(generateMockData());
    }, [scheduleVersionId]);

    const handleRefresh = () => {
        setLoading(true);
        setTimeout(() => {
            setData(generateMockData());
            setLoading(false);
        }, 1000);
    };

    const handleExport = (format) => {
        console.log(`Exporting as ${format}...`);
        // API call would go here
    };

    if (!data) {
        return <div className="flex items-center justify-center h-full text-slate-400">Loading...</div>;
    }

    return (
        <div className="h-full flex flex-col bg-slate-950">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-white">Reporting Dashboard</h2>
                    <p className="text-sm text-slate-400">Schedule performance metrics</p>
                </div>
                <div className="flex items-center space-x-3">
                    <button
                        onClick={handleRefresh}
                        className={`p-2 rounded-lg hover:bg-slate-800 text-slate-400 ${loading ? 'animate-spin' : ''}`}
                    >
                        <RefreshCw size={18} />
                    </button>
                    <ExportButtons onExport={handleExport} />
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-800">
                {['overview', 'inventory', 'quality', 'flow'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm font-medium capitalize ${activeTab === tab
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-slate-300'
                            }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* KPI Gauges */}
                        <div className="grid grid-cols-4 gap-4">
                            <ComplianceGauge label="CV (ARB)" value={23.2} target={22.0} min={18} max={28} unit=" MJ/kg" />
                            <ComplianceGauge label="Ash (ADB)" value={12.8} target={14.0} min={8} max={20} unit="%" />
                            <ComplianceGauge label="Production" value={85} target={90} unit="%" />
                            <ComplianceGauge label="Utilisation" value={78} target={85} unit="%" />
                        </div>

                        {/* Summary Charts */}
                        <div className="grid grid-cols-2 gap-6">
                            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                                <h3 className="text-sm font-medium text-white mb-4">Inventory Levels</h3>
                                <BarChart
                                    data={data.inventoryTrend}
                                    bars={[
                                        { key: 'rom1', label: 'ROM 1', color: '#3b82f6' },
                                        { key: 'rom2', label: 'ROM 2', color: '#8b5cf6' },
                                        { key: 'product', label: 'Product', color: '#10b981' }
                                    ]}
                                    height={180}
                                />
                            </div>

                            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                                <h3 className="text-sm font-medium text-white mb-4">Quality Trends</h3>
                                <LineChart
                                    data={data.qualityTrend}
                                    lines={[
                                        { key: 'cv', label: 'CV', color: '#f59e0b' },
                                        { key: 'ash', label: 'Ash', color: '#ef4444' }
                                    ]}
                                    height={180}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'inventory' && (
                    <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                        <h3 className="text-sm font-medium text-white mb-4">Inventory Over Time</h3>
                        <BarChart
                            data={data.inventoryTrend}
                            bars={[
                                { key: 'rom1', label: 'ROM Stockpile 1', color: '#3b82f6' },
                                { key: 'rom2', label: 'ROM Stockpile 2', color: '#8b5cf6' },
                                { key: 'product', label: 'Product Stock', color: '#10b981' }
                            ]}
                            height={300}
                        />
                    </div>
                )}

                {activeTab === 'quality' && (
                    <div className="space-y-6">
                        <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                            <h3 className="text-sm font-medium text-white mb-4">Quality Trend Lines</h3>
                            <LineChart
                                data={data.qualityTrend}
                                lines={[
                                    { key: 'cv', label: 'CV (MJ/kg)', color: '#f59e0b' },
                                    { key: 'ash', label: 'Ash (%)', color: '#ef4444' },
                                    { key: 'moisture', label: 'Moisture (%)', color: '#3b82f6' }
                                ]}
                                height={300}
                            />
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            <ComplianceGauge label="CV (ARB)" value={23.2} target={22.0} min={18} max={28} unit=" MJ/kg" />
                            <ComplianceGauge label="Ash (ADB)" value={12.8} target={14.0} min={8} max={20} unit="%" />
                            <ComplianceGauge label="Moisture" value={8.3} target={10.0} min={5} max={15} unit="%" />
                        </div>
                    </div>
                )}

                {activeTab === 'flow' && (
                    <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                        <h3 className="text-sm font-medium text-white mb-4">Material Flow (Sankey)</h3>
                        <SankeyDiagram flows={data.sankeyFlows} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportingDashboard;
