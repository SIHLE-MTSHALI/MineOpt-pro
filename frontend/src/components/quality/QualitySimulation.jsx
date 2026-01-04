/**
 * QualitySimulation.jsx - Monte Carlo simulation results display
 * 
 * Shows:
 * - Quality statistics with confidence intervals
 * - Probability of meeting specs (gauge/bar)
 * - Risk bands visualization
 * - Sensitivity analysis (which sources drive variance)
 */

import React, { useState } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Cell, Legend, ComposedChart, ErrorBar
} from 'recharts';
import {
    Activity, AlertTriangle, CheckCircle, TrendingUp,
    Percent, Play, RefreshCw, Sliders
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/**
 * Compliance gauge component
 */
const ComplianceGauge = ({ value, label }) => {
    const percentage = Math.round(value * 100);
    const color = percentage >= 95 ? '#22c55e' : percentage >= 80 ? '#f59e0b' : '#ef4444';

    return (
        <div className="flex flex-col items-center p-4 bg-slate-800 rounded-lg">
            <div
                className="relative w-24 h-24 rounded-full"
                style={{
                    background: `conic-gradient(${color} ${percentage}%, #334155 0%)`
                }}
            >
                <div className="absolute inset-2 bg-slate-900 rounded-full flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{percentage}%</span>
                </div>
            </div>
            <span className="mt-2 text-sm text-slate-400">{label}</span>
        </div>
    );
};

/**
 * Stat card with confidence interval
 */
const StatCard = ({ field, stats, color = 'blue' }) => {
    if (!stats) return null;

    const colors = {
        blue: 'from-blue-600 to-blue-800',
        green: 'from-green-600 to-green-800',
        amber: 'from-amber-600 to-amber-800',
        purple: 'from-purple-600 to-purple-800'
    };

    return (
        <div className={`bg-gradient-to-br ${colors[color]} p-4 rounded-lg`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white/80">{field}</span>
                <Activity size={16} className="text-white/60" />
            </div>
            <div className="text-2xl font-bold text-white">
                {stats.mean?.toFixed(2)}
            </div>
            <div className="text-xs text-white/60 mt-1">
                σ = {stats.std?.toFixed(3)}
            </div>
            <div className="flex justify-between text-xs text-white/80 mt-2 pt-2 border-t border-white/20">
                <span>P5: {stats.p5?.toFixed(2)}</span>
                <span>P95: {stats.p95?.toFixed(2)}</span>
            </div>
        </div>
    );
};

/**
 * Sensitivity bar chart
 */
const SensitivityChart = ({ data }) => {
    const chartData = Object.entries(data || {})
        .slice(0, 8)  // Top 8 contributors
        .map(([id, value]) => ({
            name: id.slice(0, 12),
            contribution: value
        }));

    if (chartData.length === 0) return null;

    return (
        <div className="bg-slate-800 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <TrendingUp size={16} className="text-purple-400" />
                Variance Contributors
            </h4>
            <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis type="number" stroke="#94a3b8" />
                        <YAxis dataKey="name" type="category" stroke="#94a3b8" width={80} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                            formatter={(val) => [`${val.toFixed(1)}%`, 'Contribution']}
                        />
                        <Bar dataKey="contribution" fill="#8b5cf6">
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={index}
                                    fill={`hsl(${270 - index * 20}, 70%, 50%)`}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

/**
 * Spec compliance chart
 */
const SpecComplianceChart = ({ data }) => {
    const chartData = Object.entries(data || {}).map(([field, prob]) => ({
        field,
        probability: prob * 100,
        compliant: prob >= 0.95
    }));

    if (chartData.length === 0) return null;

    return (
        <div className="bg-slate-800 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                <Percent size={16} className="text-green-400" />
                Specification Compliance Probability
            </h4>
            <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="field" stroke="#94a3b8" />
                        <YAxis domain={[0, 100]} stroke="#94a3b8" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                            formatter={(val) => [`${val.toFixed(1)}%`, 'Probability']}
                        />
                        <Bar dataKey="probability">
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={index}
                                    fill={entry.compliant ? '#22c55e' : '#f59e0b'}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

/**
 * Main Quality Simulation component
 */
const QualitySimulation = ({ sources = [], specs = [], onComplete }) => {
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [settings, setSettings] = useState({
        n_simulations: 1000,
        include_wash_plant: false,
        wash_plant_yield: 0.85
    });
    const [showSettings, setShowSettings] = useState(false);

    const runSimulation = async () => {
        if (sources.length === 0) {
            setError("No sources provided for simulation");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const res = await axios.post(`${API_BASE}/quality/simulate`, {
                sources: sources.map(s => ({
                    parcel_id: s.parcel_id || s.id || `source_${Math.random().toString(36).slice(2, 8)}`,
                    source_reference: s.source_reference || '',
                    quantity_tonnes: s.quantity_tonnes || s.tonnes || 0,
                    quality_vector: s.quality_vector || s.quality || {}
                })),
                specs: specs.map(s => ({
                    field_name: s.field_name || s.field,
                    min_value: s.min_value,
                    max_value: s.max_value,
                    is_hard_constraint: s.is_hard_constraint !== false
                })),
                n_simulations: settings.n_simulations,
                include_wash_plant: settings.include_wash_plant,
                wash_plant_yield: settings.wash_plant_yield
            });

            setResults(res.data);
            onComplete?.(res.data);

        } catch (e) {
            console.error("Simulation failed", e);
            setError(e.response?.data?.detail || "Simulation failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-slate-900 rounded-lg border border-slate-800">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity size={20} className="text-purple-400" />
                    <h3 className="text-lg font-semibold text-white">Quality Simulation</h3>
                    {results && (
                        <span className="text-xs text-slate-500 ml-2">
                            {results.n_simulations} runs in {results.simulation_time_ms?.toFixed(0)}ms
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="p-2 text-slate-400 hover:text-white rounded hover:bg-slate-800"
                    >
                        <Sliders size={18} />
                    </button>

                    <button
                        onClick={runSimulation}
                        disabled={loading || sources.length === 0}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
                    >
                        {loading ? (
                            <RefreshCw size={16} className="animate-spin" />
                        ) : (
                            <Play size={16} />
                        )}
                        Run Simulation
                    </button>
                </div>
            </div>

            {/* Settings Panel */}
            {showSettings && (
                <div className="p-4 bg-slate-800/50 border-b border-slate-800 grid grid-cols-3 gap-4">
                    <div>
                        <label className="text-xs text-slate-400">Simulations</label>
                        <input
                            type="number"
                            value={settings.n_simulations}
                            onChange={(e) => setSettings({ ...settings, n_simulations: parseInt(e.target.value) })}
                            className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                        />
                    </div>
                    <div>
                        <label className="text-xs text-slate-400 flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={settings.include_wash_plant}
                                onChange={(e) => setSettings({ ...settings, include_wash_plant: e.target.checked })}
                                className="rounded"
                            />
                            Include Wash Plant
                        </label>
                    </div>
                    {settings.include_wash_plant && (
                        <div>
                            <label className="text-xs text-slate-400">Expected Yield</label>
                            <input
                                type="number"
                                step="0.01"
                                value={settings.wash_plant_yield}
                                onChange={(e) => setSettings({ ...settings, wash_plant_yield: parseFloat(e.target.value) })}
                                className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm"
                            />
                        </div>
                    )}
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="p-4 bg-red-900/30 border-b border-red-800 flex items-center gap-2 text-red-300">
                    <AlertTriangle size={18} />
                    {error}
                </div>
            )}

            {/* Results */}
            {results && (
                <div className="p-4 space-y-4">
                    {/* Overall Compliance */}
                    <div className="flex justify-center gap-6">
                        <ComplianceGauge
                            value={results.overall_compliance || 0}
                            label="Overall Compliance"
                        />
                        {Object.entries(results.spec_compliance || {}).slice(0, 3).map(([field, prob]) => (
                            <ComplianceGauge key={field} value={prob} label={field} />
                        ))}
                    </div>

                    {/* Quality Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(results.quality_stats || {})
                            .filter(([k]) => !['yield', 'output_tonnes'].includes(k))
                            .slice(0, 8)
                            .map(([field, stats], i) => (
                                <StatCard
                                    key={field}
                                    field={field}
                                    stats={stats}
                                    color={['blue', 'green', 'amber', 'purple'][i % 4]}
                                />
                            ))
                        }
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <SpecComplianceChart data={results.spec_compliance} />
                        <SensitivityChart data={results.sensitivity} />
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!results && !loading && (
                <div className="p-8 text-center text-slate-500">
                    <Activity size={48} className="mx-auto mb-4 opacity-30" />
                    <p>Configure sources and click "Run Simulation"</p>
                    <p className="text-sm mt-1">{sources.length} sources loaded</p>
                </div>
            )}
        </div>
    );
};

export default QualitySimulation;
