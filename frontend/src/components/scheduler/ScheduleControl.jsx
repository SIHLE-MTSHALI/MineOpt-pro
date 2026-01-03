/**
 * ScheduleControl.jsx - Scheduling Control & Diagnostics Panel
 * 
 * Controls for schedule generation and troubleshooting:
 * - Fast Pass / Full Pass execution buttons
 * - Run progress indicator
 * - Diagnostic list panel
 * - Infeasibility explanations
 * - Decision "why" drill-down
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Play, Zap, RefreshCw, AlertTriangle, CheckCircle, XCircle,
    Info, ChevronDown, ChevronRight, Clock, Settings,
    Activity, HelpCircle, Loader2
} from 'lucide-react';

// Status indicator component
const StatusBadge = ({ status }) => {
    const config = {
        idle: { bg: 'bg-slate-700', text: 'text-slate-400', icon: Clock },
        running: { bg: 'bg-blue-600', text: 'text-white', icon: Loader2, spin: true },
        success: { bg: 'bg-green-600', text: 'text-white', icon: CheckCircle },
        warning: { bg: 'bg-yellow-600', text: 'text-white', icon: AlertTriangle },
        error: { bg: 'bg-red-600', text: 'text-white', icon: XCircle }
    };

    const { bg, text, icon: Icon, spin } = config[status] || config.idle;

    return (
        <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded text-xs ${bg} ${text}`}>
            <Icon size={12} className={spin ? 'animate-spin' : ''} />
            <span className="capitalize">{status}</span>
        </span>
    );
};

// Progress Bar Component
const ProgressBar = ({ progress, stage }) => (
    <div className="w-full">
        <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{stage}</span>
            <span>{progress}%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
            />
        </div>
    </div>
);

// Diagnostic Item Component
const DiagnosticItem = ({ diagnostic, expanded, onToggle }) => {
    const severityColors = {
        info: 'border-blue-500 bg-blue-500/10',
        warning: 'border-yellow-500 bg-yellow-500/10',
        error: 'border-red-500 bg-red-500/10'
    };

    const severityIcons = {
        info: Info,
        warning: AlertTriangle,
        error: XCircle
    };

    const Icon = severityIcons[diagnostic.severity] || Info;

    return (
        <div className={`border-l-2 ${severityColors[diagnostic.severity]} rounded-r-lg p-3 mb-2`}>
            <div
                className="flex items-start justify-between cursor-pointer"
                onClick={onToggle}
            >
                <div className="flex items-start space-x-2">
                    <Icon size={16} className={`mt-0.5 ${diagnostic.severity === 'error' ? 'text-red-400' :
                            diagnostic.severity === 'warning' ? 'text-yellow-400' : 'text-blue-400'
                        }`} />
                    <div>
                        <div className="text-sm text-white">{diagnostic.message}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{diagnostic.category}</div>
                    </div>
                </div>
                {diagnostic.details && (
                    expanded ? <ChevronDown size={16} className="text-slate-500" /> :
                        <ChevronRight size={16} className="text-slate-500" />
                )}
            </div>

            {expanded && diagnostic.details && (
                <div className="mt-3 pt-3 border-t border-slate-700 text-xs text-slate-400">
                    {diagnostic.details}
                </div>
            )}
        </div>
    );
};

// Decision Explanation Component
const DecisionExplainer = ({ decision }) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="bg-slate-800/50 rounded-lg p-3 mb-2">
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center space-x-2">
                    <HelpCircle size={16} className="text-blue-400" />
                    <span className="text-sm text-white">{decision.question}</span>
                </div>
                {expanded ? <ChevronDown size={16} className="text-slate-500" /> :
                    <ChevronRight size={16} className="text-slate-500" />}
            </div>

            {expanded && (
                <div className="mt-3 space-y-2">
                    <div className="text-sm text-slate-300">{decision.answer}</div>

                    {decision.factors && (
                        <div className="space-y-1">
                            <div className="text-xs text-slate-500 font-medium">Contributing Factors:</div>
                            {decision.factors.map((factor, i) => (
                                <div key={i} className="flex items-center space-x-2 text-xs">
                                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                                    <span className="text-slate-400">{factor}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Main Schedule Control Component
const ScheduleControl = ({ scheduleVersionId }) => {
    const [status, setStatus] = useState('idle');
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState('Ready');
    const [lastRun, setLastRun] = useState(null);
    const [diagnostics, setDiagnostics] = useState([]);
    const [expandedDiagnostic, setExpandedDiagnostic] = useState(null);
    const [decisions, setDecisions] = useState([]);
    const [runMode, setRunMode] = useState('fast');

    // Simulated optimization stages
    const stages = [
        'Validating inputs...',
        'Building candidates...',
        'Assigning resources...',
        'Optimizing flow...',
        'Calculating quality...',
        'Checking constraints...',
        'Finalizing schedule...'
    ];

    // Run Fast Pass
    const handleFastPass = useCallback(async () => {
        setStatus('running');
        setProgress(0);
        setRunMode('fast');
        setDiagnostics([]);

        // Simulate progress
        for (let i = 0; i < stages.length; i++) {
            setStage(stages[i]);
            setProgress(Math.round((i + 1) / stages.length * 100));
            await new Promise(r => setTimeout(r, 500));
        }

        // Simulate result
        setStatus('success');
        setLastRun(new Date().toISOString());
        setDiagnostics([
            { id: 1, severity: 'info', category: 'Scheduling', message: 'Fast pass completed in 3.2s', details: '142 tasks scheduled across 12 periods' },
            { id: 2, severity: 'warning', category: 'Capacity', message: 'Stockpile ROM-01 near capacity in period 5', details: 'Current: 45,000t / Max: 50,000t. Consider increasing reclaim rate.' }
        ]);
        setDecisions([
            { question: 'Why was Block A sent to ROM Stockpile instead of Direct Feed?', answer: 'Block A has Ash content of 18% which exceeds plant direct feed limit of 15%. Sent to ROM for blending.', factors: ['Ash_ADB: 18% > limit 15%', 'Stockpile capacity available', 'Blending opportunity exists'] },
            { question: 'Why is Excavator EX-01 idle in period 3?', answer: 'No accessible coal blocks in EX-01 working area during this period.', factors: ['Block B not yet exposed', 'Block C reserved for EX-02', 'Maintenance window scheduled'] }
        ]);
    }, []);

    // Run Full Pass
    const handleFullPass = useCallback(async () => {
        setStatus('running');
        setProgress(0);
        setRunMode('full');
        setDiagnostics([]);

        // Simulate longer optimization
        for (let i = 0; i < stages.length; i++) {
            setStage(stages[i]);
            setProgress(Math.round((i + 1) / stages.length * 100));
            await new Promise(r => setTimeout(r, 1000)); // Slower for full pass
        }

        setStatus('success');
        setLastRun(new Date().toISOString());
        setDiagnostics([
            { id: 1, severity: 'info', category: 'Optimization', message: 'Full pass completed in 8.4s', details: '142 tasks scheduled, 3 iterations performed' },
            { id: 2, severity: 'info', category: 'Quality', message: 'Product quality targets achieved', details: 'All products within spec. Blending optimization reduced variance by 12%.' }
        ]);
    }, []);

    // Cancel run
    const handleCancel = () => {
        setStatus('idle');
        setProgress(0);
        setStage('Cancelled');
    };

    return (
        <div className="h-full flex flex-col bg-slate-950">
            {/* Header */}
            <div className="p-4 border-b border-slate-800">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-white">Schedule Control</h2>
                        <p className="text-sm text-slate-400">Run optimization and review decisions</p>
                    </div>
                    <StatusBadge status={status} />
                </div>
            </div>

            {/* Run Controls */}
            <div className="p-4 border-b border-slate-800">
                <div className="flex space-x-3">
                    <button
                        onClick={handleFastPass}
                        disabled={status === 'running'}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
                    >
                        <Zap size={18} />
                        <span>Fast Pass</span>
                    </button>

                    <button
                        onClick={handleFullPass}
                        disabled={status === 'running'}
                        className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
                    >
                        <Play size={18} />
                        <span>Full Pass</span>
                    </button>

                    {status === 'running' && (
                        <button
                            onClick={handleCancel}
                            className="flex items-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white"
                        >
                            <XCircle size={18} />
                            <span>Cancel</span>
                        </button>
                    )}
                </div>

                {/* Progress */}
                {status === 'running' && (
                    <div className="mt-4">
                        <ProgressBar progress={progress} stage={stage} />
                    </div>
                )}

                {/* Last Run Info */}
                {lastRun && status !== 'running' && (
                    <div className="mt-4 flex items-center space-x-4 text-sm text-slate-400">
                        <span>Last run: {new Date(lastRun).toLocaleTimeString()}</span>
                        <span>•</span>
                        <span className="capitalize">{runMode} pass</span>
                    </div>
                )}
            </div>

            {/* Tabs */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <div className="flex border-b border-slate-800">
                    <button className="px-4 py-2 text-sm font-medium text-blue-400 border-b-2 border-blue-400">
                        Diagnostics ({diagnostics.length})
                    </button>
                    <button className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-300">
                        Decisions ({decisions.length})
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4">
                    {/* Diagnostics Tab */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium text-slate-400 mb-3">Diagnostic Messages</h3>

                        {diagnostics.length === 0 ? (
                            <div className="text-center py-8 text-slate-500">
                                <Activity size={24} className="mx-auto mb-2 opacity-50" />
                                <p>Run optimization to see diagnostics</p>
                            </div>
                        ) : (
                            diagnostics.map(diag => (
                                <DiagnosticItem
                                    key={diag.id}
                                    diagnostic={diag}
                                    expanded={expandedDiagnostic === diag.id}
                                    onToggle={() => setExpandedDiagnostic(
                                        expandedDiagnostic === diag.id ? null : diag.id
                                    )}
                                />
                            ))
                        )}
                    </div>

                    {/* Decision Explanations */}
                    {decisions.length > 0 && (
                        <div className="mt-6">
                            <h3 className="text-sm font-medium text-slate-400 mb-3">Decision Explanations</h3>
                            {decisions.map((decision, i) => (
                                <DecisionExplainer key={i} decision={decision} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScheduleControl;
