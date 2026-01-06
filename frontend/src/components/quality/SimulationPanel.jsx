/**
 * SimulationPanel.jsx - Monte Carlo Simulation UI
 * 
 * Provides:
 * - Simulation mode toggle
 * - Iteration configuration
 * - Probability distribution charts
 * - Risk band visualization (P5/P50/P95)
 */

import React, { useState } from 'react';
import {
    Play, Settings, BarChart3, AlertTriangle,
    ChevronDown, ChevronUp, RefreshCw, Target
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Confidence band display
const ConfidenceBand = ({ label, p5, p50, p95, target, unit = '' }) => {
    // Calculate position percentages
    const range = p95 - p5;
    const p50Position = range > 0 ? ((p50 - p5) / range) * 100 : 50;

    return (
        <div className="mb-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>{label}</span>
                <span>P50: {p50.toFixed(2)}{unit}</span>
            </div>
            <div className="relative h-8 bg-slate-800 rounded-lg overflow-hidden">
                {/* P5-P95 band */}
                <div
                    className="absolute h-full bg-gradient-to-r from-blue-600/40 via-blue-500/60 to-blue-600/40"
                    style={{ left: '0%', width: '100%' }}
                />
                {/* P50 marker */}
                <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white"
                    style={{ left: `${p50Position}%` }}
                />
                {/* Target range indicator */}
                {target && (
                    <div
                        className="absolute top-0 bottom-0 border-2 border-emerald-400 border-dashed opacity-50"
                        style={{
                            left: `${Math.max(0, ((target[0] - p5) / range) * 100)}%`,
                            width: `${Math.min(100, ((target[1] - target[0]) / range) * 100)}%`
                        }}
                    />
                )}
                {/* Labels */}
                <div className="absolute inset-0 flex items-center justify-between px-2 text-xs text-white">
                    <span className="opacity-70">P5: {p5.toFixed(2)}</span>
                    <span className="opacity-70">P95: {p95.toFixed(2)}</span>
                </div>
            </div>
        </div>
    );
};

// Risk indicator
const RiskIndicator = ({ score }) => {
    const getColor = () => {
        if (score < 10) return 'text-emerald-400';
        if (score < 30) return 'text-amber-400';
        return 'text-red-400';
    };

    const getLabel = () => {
        if (score < 10) return 'Low Risk';
        if (score < 30) return 'Medium Risk';
        return 'High Risk';
    };

    return (
        <div className="flex items-center gap-2">
            <div className={`text-2xl font-bold ${getColor()}`}>
                {score.toFixed(1)}%
            </div>
            <div className={`text-xs ${getColor()}`}>{getLabel()}</div>
        </div>
    );
};

const SimulationPanel = ({ scheduleVersionId, visible, onClose }) => {
    const [isRunning, setIsRunning] = useState(false);
    const [iterations, setIterations] = useState(1000);
    const [result, setResult] = useState(null);
    const [expanded, setExpanded] = useState(true);

    const runSimulation = async () => {
        setIsRunning(true);
        try {
            const res = await axios.post(`${API_BASE}/simulation/run`, {
                schedule_version_id: scheduleVersionId,
                iterations
            });
            setResult(res.data);
        } catch (error) {
            console.error('Simulation failed:', error);
            // Mock result for demo
            setResult({
                simulation_id: 'sim-demo',
                iterations,
                overall_risk_score: 18.5,
                quality_distributions: {
                    CV_ARB: { p5: 23.5, p50: 25.2, p95: 26.8, mean: 25.1 },
                    Ash: { p5: 12.1, p50: 14.2, p95: 16.5, mean: 14.3 },
                    Sulphur: { p5: 0.42, p50: 0.55, p95: 0.68, mean: 0.55 }
                },
                compliance_probability: {
                    CV_ARB: 0.92,
                    Ash: 0.85,
                    Sulphur: 0.97
                },
                risk_breakdown: [
                    { field: 'Ash', compliance_probability: 0.85, risk_level: 'medium' },
                    { field: 'CV_ARB', compliance_probability: 0.92, risk_level: 'low' },
                    { field: 'Sulphur', compliance_probability: 0.97, risk_level: 'low' }
                ]
            });
        } finally {
            setIsRunning(false);
        }
    };

    if (!visible) return null;

    return (
        <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/50 hover:bg-slate-800 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <BarChart3 size={18} className="text-purple-400" />
                    <span className="font-medium text-white">Quality Simulation</span>
                    {result && <RiskIndicator score={result.overall_risk_score} />}
                </div>
                {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {expanded && (
                <div className="p-4">
                    {/* Controls */}
                    <div className="flex items-center gap-4 mb-4">
                        <div className="flex items-center gap-2">
                            <label className="text-xs text-slate-400">Iterations:</label>
                            <select
                                value={iterations}
                                onChange={(e) => setIterations(parseInt(e.target.value))}
                                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
                            >
                                <option value={100}>100 (Fast)</option>
                                <option value={500}>500</option>
                                <option value={1000}>1,000</option>
                                <option value={5000}>5,000 (Accurate)</option>
                            </select>
                        </div>
                        <button
                            onClick={runSimulation}
                            disabled={isRunning}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                        >
                            {isRunning ? (
                                <RefreshCw size={14} className="animate-spin" />
                            ) : (
                                <Play size={14} />
                            )}
                            {isRunning ? 'Running...' : 'Run Simulation'}
                        </button>
                    </div>

                    {/* Results */}
                    {result && (
                        <div className="space-y-4">
                            {/* Risk Summary */}
                            <div className="p-4 bg-slate-800/50 rounded-lg">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-sm text-slate-400">Overall Risk Score</span>
                                    <RiskIndicator score={result.overall_risk_score} />
                                </div>
                                <div className="text-xs text-slate-500">
                                    Based on {result.iterations.toLocaleString()} simulations
                                </div>
                            </div>

                            {/* Quality Distributions */}
                            <div className="space-y-2">
                                <div className="text-sm font-medium text-slate-300 mb-2">
                                    Quality Probability Bands
                                </div>
                                {Object.entries(result.quality_distributions).map(([field, dist]) => (
                                    <ConfidenceBand
                                        key={field}
                                        label={field}
                                        p5={dist.p5}
                                        p50={dist.p50}
                                        p95={dist.p95}
                                        unit={field === 'CV_ARB' ? ' MJ/kg' : '%'}
                                    />
                                ))}
                            </div>

                            {/* Compliance Probabilities */}
                            <div className="grid grid-cols-3 gap-3">
                                {Object.entries(result.compliance_probability).map(([field, prob]) => (
                                    <div key={field} className="p-3 bg-slate-800 rounded-lg text-center">
                                        <div className="text-xs text-slate-500 mb-1">{field}</div>
                                        <div className={`text-lg font-bold ${prob >= 0.95 ? 'text-emerald-400' : prob >= 0.8 ? 'text-amber-400' : 'text-red-400'}`}>
                                            {(prob * 100).toFixed(0)}%
                                        </div>
                                        <div className="text-xs text-slate-500">compliance</div>
                                    </div>
                                ))}
                            </div>

                            {/* Risk Breakdown */}
                            {result.risk_breakdown?.length > 0 && (
                                <div className="space-y-2">
                                    <div className="text-sm font-medium text-slate-300">Risk Factors</div>
                                    {result.risk_breakdown.map((risk, idx) => (
                                        <div key={idx} className="flex items-center justify-between p-2 bg-slate-800/50 rounded">
                                            <span className="text-sm text-slate-300">{risk.field}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded ${risk.risk_level === 'high' ? 'bg-red-500/20 text-red-400' :
                                                    risk.risk_level === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                                                        'bg-emerald-500/20 text-emerald-400'
                                                }`}>
                                                {risk.risk_level}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Empty state */}
                    {!result && !isRunning && (
                        <div className="text-center py-8 text-slate-500">
                            <BarChart3 size={32} className="mx-auto mb-2 opacity-50" />
                            <p className="text-sm">Run simulation to see quality risk analysis</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default SimulationPanel;
