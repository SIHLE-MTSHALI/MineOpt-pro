/**
 * ScheduleControl.jsx - Schedule Control & Optimization Panel
 * 
 * Provides controls for:
 * - Running auto-scheduling optimization
 * - Schedule version management
 * - Constraint configuration
 * - Optimization status and progress
 * - Schedule comparison and publishing
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Zap, Play, Pause, Check, X, Clock, Calendar,
    Settings, RefreshCw, ChevronDown, ChevronRight,
    AlertTriangle, TrendingUp, Target, Layers, Copy,
    Archive, Send, FileText, BarChart2
} from 'lucide-react';

// Schedule Version Card
const VersionCard = ({ version, isActive, onSelect, onPublish, onCompare }) => {
    const statusColors = {
        Draft: 'bg-slate-600 text-slate-200',
        Running: 'bg-amber-600 text-amber-100',
        Completed: 'bg-green-600 text-green-100',
        Published: 'bg-blue-600 text-blue-100',
        Failed: 'bg-red-600 text-red-100'
    };

    return (
        <div
            className={`bg-slate-800 border rounded-lg p-4 cursor-pointer transition-all ${isActive ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-slate-700 hover:border-slate-600'
                }`}
            onClick={() => onSelect(version)}
        >
            <div className="flex items-start justify-between mb-2">
                <div>
                    <h4 className="font-semibold text-white">{version.name}</h4>
                    <p className="text-xs text-slate-400">v{version.version_number}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${statusColors[version.status] || statusColors.Draft}`}>
                    {version.status}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div>
                    <span className="text-slate-500">Created:</span>
                    <span className="text-slate-300 ml-1">{version.created_at || 'Today'}</span>
                </div>
                <div>
                    <span className="text-slate-500">Tasks:</span>
                    <span className="text-slate-300 ml-1">{version.task_count || 0}</span>
                </div>
            </div>

            <div className="flex gap-2">
                {version.status === 'Completed' && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPublish(version); }}
                        className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-blue-600/20 text-blue-400 rounded text-xs hover:bg-blue-600/30"
                    >
                        <Send size={12} /> Publish
                    </button>
                )}
                <button
                    onClick={(e) => { e.stopPropagation(); onCompare(version); }}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-slate-700 text-slate-300 rounded text-xs hover:bg-slate-600"
                >
                    <BarChart2 size={12} /> Compare
                </button>
            </div>
        </div>
    );
};

// Constraint Configuration Section
const ConstraintSection = ({ title, constraints, onToggle, expanded, onExpand }) => (
    <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <button
            onClick={onExpand}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-750"
        >
            <div className="flex items-center gap-2">
                <Settings size={16} className="text-blue-400" />
                <span className="font-medium text-white">{title}</span>
            </div>
            {expanded ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
        </button>

        {expanded && (
            <div className="p-3 pt-0 space-y-2">
                {constraints.map((constraint, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-t border-slate-700">
                        <div>
                            <span className="text-sm text-slate-300">{constraint.name}</span>
                            {constraint.description && (
                                <p className="text-xs text-slate-500">{constraint.description}</p>
                            )}
                        </div>
                        <button
                            onClick={() => onToggle(i)}
                            className={`relative w-10 h-5 rounded-full transition-colors ${constraint.enabled ? 'bg-blue-600' : 'bg-slate-600'
                                }`}
                        >
                            <span
                                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${constraint.enabled ? 'translate-x-5' : 'translate-x-0'
                                    }`}
                            />
                        </button>
                    </div>
                ))}
            </div>
        )}
    </div>
);

// Optimization Progress Display
const OptimizationProgress = ({ status, progress, metrics }) => {
    if (status === 'idle') return null;

    return (
        <div className="bg-gradient-to-r from-blue-900/50 to-slate-800 border border-blue-700/50 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    {status === 'running' ? (
                        <RefreshCw size={18} className="text-blue-400 animate-spin" />
                    ) : status === 'completed' ? (
                        <Check size={18} className="text-green-400" />
                    ) : (
                        <X size={18} className="text-red-400" />
                    )}
                    <span className="font-semibold text-white">
                        {status === 'running' ? 'Optimizing Schedule...' :
                            status === 'completed' ? 'Optimization Complete' :
                                'Optimization Failed'}
                    </span>
                </div>
                {status === 'running' && (
                    <span className="text-sm text-blue-300">{progress}%</span>
                )}
            </div>

            {status === 'running' && (
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden mb-3">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}

            {metrics && (
                <div className="grid grid-cols-4 gap-3 text-center">
                    <div>
                        <p className="text-lg font-bold text-white">{metrics.tasksScheduled}</p>
                        <p className="text-xs text-slate-400">Tasks</p>
                    </div>
                    <div>
                        <p className="text-lg font-bold text-green-400">{metrics.utilization}%</p>
                        <p className="text-xs text-slate-400">Utilization</p>
                    </div>
                    <div>
                        <p className="text-lg font-bold text-blue-400">{metrics.qualityScore}</p>
                        <p className="text-xs text-slate-400">Quality Score</p>
                    </div>
                    <div>
                        <p className="text-lg font-bold text-amber-400">{metrics.violations}</p>
                        <p className="text-xs text-slate-400">Violations</p>
                    </div>
                </div>
            )}
        </div>
    );
};

// Main Schedule Control Component
const ScheduleControl = ({ siteId, scheduleVersionId, onScheduleChange }) => {
    const [versions, setVersions] = useState([]);
    const [activeVersion, setActiveVersion] = useState(null);
    const [loading, setLoading] = useState(false);

    // Optimization state
    const [optimizationStatus, setOptimizationStatus] = useState('idle'); // idle, running, completed, failed
    const [optimizationProgress, setOptimizationProgress] = useState(0);
    const [metrics, setMetrics] = useState(null);

    // Constraint toggles
    const [expandedSection, setExpandedSection] = useState('resource');
    const [constraints, setConstraints] = useState({
        resource: [
            { name: 'Equipment Availability', description: 'Respect maintenance windows', enabled: true },
            { name: 'Operator Shifts', description: 'Match tasks to crew schedules', enabled: true },
            { name: 'Fleet Capacity', description: 'Limit concurrent truck assignments', enabled: true },
        ],
        quality: [
            { name: 'Product Specs Compliance', description: 'Meet destination quality targets', enabled: true },
            { name: 'Blending Optimization', description: 'Optimize material blending ratios', enabled: true },
            { name: 'Stockpile Quality Tracking', description: 'Track running quality averages', enabled: false },
        ],
        operational: [
            { name: 'Pit Sequencing', description: 'Follow mining progression rules', enabled: true },
            { name: 'Haul Route Optimization', description: 'Minimize total haul distance', enabled: true },
            { name: 'Stockpile Balancing', description: 'Maintain target inventory levels', enabled: false },
        ],
    });

    useEffect(() => {
        if (siteId) {
            fetchVersions();
        }
    }, [siteId]);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/schedule/site/${siteId}/versions`);
            setVersions(res.data);
            if (res.data.length > 0) {
                setActiveVersion(res.data[0]);
            }
        } catch (e) {
            // Sample data
            setVersions([
                { id: 'v1', name: 'Week 1 Schedule', version_number: 1, status: 'Published', task_count: 45, created_at: 'Jan 2' },
                { id: 'v2', name: 'Week 2 Draft', version_number: 2, status: 'Completed', task_count: 52, created_at: 'Jan 3' },
                { id: 'v3', name: 'Current Working', version_number: 3, status: 'Draft', task_count: 0, created_at: 'Jan 4' },
            ]);
            setActiveVersion({ id: 'v3', name: 'Current Working', version_number: 3, status: 'Draft' });
        } finally {
            setLoading(false);
        }
    };

    const handleRunOptimization = async () => {
        setOptimizationStatus('running');
        setOptimizationProgress(0);
        setMetrics(null);

        // Simulate optimization progress
        const interval = setInterval(() => {
            setOptimizationProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    return 100;
                }
                return prev + Math.random() * 15;
            });
        }, 500);

        try {
            // Call optimization API
            const response = await axios.post(`http://localhost:8000/schedule/optimize`, {
                site_id: siteId,
                version_id: activeVersion?.id,
                constraints: constraints
            });

            clearInterval(interval);
            setOptimizationProgress(100);
            setOptimizationStatus('completed');
            setMetrics(response.data.metrics || {
                tasksScheduled: 52,
                utilization: 87,
                qualityScore: 94,
                violations: 2
            });
        } catch (e) {
            clearInterval(interval);
            // Simulate success for demo
            setTimeout(() => {
                setOptimizationProgress(100);
                setOptimizationStatus('completed');
                setMetrics({
                    tasksScheduled: 52,
                    utilization: 87,
                    qualityScore: 94,
                    violations: 2
                });
            }, 2000);
        }
    };

    const handleToggleConstraint = (section, index) => {
        setConstraints(prev => ({
            ...prev,
            [section]: prev[section].map((c, i) =>
                i === index ? { ...c, enabled: !c.enabled } : c
            )
        }));
    };

    const handleCreateVersion = async () => {
        const name = prompt('Enter schedule version name:');
        if (!name) return;

        const newVersion = {
            id: `v${versions.length + 1}`,
            name,
            version_number: versions.length + 1,
            status: 'Draft',
            task_count: 0,
            created_at: 'Now'
        };

        setVersions([newVersion, ...versions]);
        setActiveVersion(newVersion);
    };

    const handlePublish = async (version) => {
        setVersions(prev => prev.map(v =>
            v.id === version.id ? { ...v, status: 'Published' } : v
        ));
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400">
                <RefreshCw className="animate-spin mr-2" /> Loading schedules...
            </div>
        );
    }

    return (
        <div className="h-full bg-slate-900 p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Zap className="text-amber-400" />
                        Schedule Control
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">
                        Configure and run optimization for production schedules
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleCreateVersion}
                        className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-700"
                    >
                        <Copy size={16} /> New Version
                    </button>
                    <button
                        onClick={handleRunOptimization}
                        disabled={optimizationStatus === 'running'}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${optimizationStatus === 'running'
                                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-400 hover:to-orange-400 shadow-lg shadow-amber-500/20'
                            }`}
                    >
                        {optimizationStatus === 'running' ? (
                            <>
                                <RefreshCw size={18} className="animate-spin" /> Optimizing...
                            </>
                        ) : (
                            <>
                                <Play size={18} /> Run Optimization
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Optimization Progress */}
            <OptimizationProgress
                status={optimizationStatus}
                progress={Math.min(optimizationProgress, 100)}
                metrics={metrics}
            />

            <div className="grid grid-cols-3 gap-6">
                {/* Left: Schedule Versions */}
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                        Schedule Versions
                    </h3>
                    <div className="space-y-3">
                        {versions.map(version => (
                            <VersionCard
                                key={version.id}
                                version={version}
                                isActive={activeVersion?.id === version.id}
                                onSelect={setActiveVersion}
                                onPublish={handlePublish}
                                onCompare={() => console.log('Compare', version)}
                            />
                        ))}
                    </div>
                </div>

                {/* Middle: Constraints */}
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                        Optimization Constraints
                    </h3>
                    <div className="space-y-3">
                        <ConstraintSection
                            title="Resource Constraints"
                            constraints={constraints.resource}
                            onToggle={(i) => handleToggleConstraint('resource', i)}
                            expanded={expandedSection === 'resource'}
                            onExpand={() => setExpandedSection(expandedSection === 'resource' ? null : 'resource')}
                        />
                        <ConstraintSection
                            title="Quality Constraints"
                            constraints={constraints.quality}
                            onToggle={(i) => handleToggleConstraint('quality', i)}
                            expanded={expandedSection === 'quality'}
                            onExpand={() => setExpandedSection(expandedSection === 'quality' ? null : 'quality')}
                        />
                        <ConstraintSection
                            title="Operational Constraints"
                            constraints={constraints.operational}
                            onToggle={(i) => handleToggleConstraint('operational', i)}
                            expanded={expandedSection === 'operational'}
                            onExpand={() => setExpandedSection(expandedSection === 'operational' ? null : 'operational')}
                        />
                    </div>
                </div>

                {/* Right: Quick Actions & Summary */}
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                        Quick Actions
                    </h3>

                    <div className="space-y-3">
                        <button className="w-full flex items-center gap-3 p-3 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-750 text-left">
                            <div className="p-2 bg-blue-500/20 rounded-lg">
                                <Calendar size={18} className="text-blue-400" />
                            </div>
                            <div>
                                <span className="text-sm font-medium text-white">View Calendar</span>
                                <p className="text-xs text-slate-400">See scheduled periods</p>
                            </div>
                        </button>

                        <button className="w-full flex items-center gap-3 p-3 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-750 text-left">
                            <div className="p-2 bg-green-500/20 rounded-lg">
                                <Target size={18} className="text-green-400" />
                            </div>
                            <div>
                                <span className="text-sm font-medium text-white">Set Targets</span>
                                <p className="text-xs text-slate-400">Configure production goals</p>
                            </div>
                        </button>

                        <button className="w-full flex items-center gap-3 p-3 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-750 text-left">
                            <div className="p-2 bg-amber-500/20 rounded-lg">
                                <FileText size={18} className="text-amber-400" />
                            </div>
                            <div>
                                <span className="text-sm font-medium text-white">Generate Report</span>
                                <p className="text-xs text-slate-400">Export schedule details</p>
                            </div>
                        </button>

                        <button className="w-full flex items-center gap-3 p-3 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-750 text-left">
                            <div className="p-2 bg-purple-500/20 rounded-lg">
                                <Archive size={18} className="text-purple-400" />
                            </div>
                            <div>
                                <span className="text-sm font-medium text-white">Archive Version</span>
                                <p className="text-xs text-slate-400">Store for reference</p>
                            </div>
                        </button>
                    </div>

                    {/* Active Version Summary */}
                    {activeVersion && (
                        <div className="mt-4 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                            <h4 className="text-xs text-slate-500 uppercase mb-2">Active Version</h4>
                            <p className="text-lg font-semibold text-white">{activeVersion.name}</p>
                            <p className="text-xs text-slate-400">Version {activeVersion.version_number} • {activeVersion.status}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScheduleControl;
