/**
 * DiagnosticsPanel.jsx - Schedule Diagnostics & Explanations
 * 
 * Displays after schedule optimization:
 * - Infeasibilities (constraints that couldn't be satisfied)
 * - Blocked routes (arcs at capacity)
 * - Unmet demands (product shortfalls)
 * - Binding constraints (what limited the solution)
 * - Decision explanations (why specific choices were made)
 */

import React, { useState, useEffect } from 'react';
import {
    AlertTriangle, AlertCircle, CheckCircle, Info,
    ChevronDown, ChevronRight, Route, Package,
    Gauge, HelpCircle, X, ExternalLink
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Severity badge component
const SeverityBadge = ({ level }) => {
    const config = {
        error: { bg: 'bg-red-500/20', text: 'text-red-400', icon: AlertCircle },
        warning: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: AlertTriangle },
        info: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: Info },
        success: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle }
    };
    const c = config[level] || config.info;
    const Icon = c.icon;
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>
            <Icon size={12} />
            {level.toUpperCase()}
        </span>
    );
};

// Collapsible section
const DiagnosticSection = ({ title, icon: Icon, count, severity, children, defaultOpen = false }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="border border-slate-700 rounded-lg overflow-hidden mb-3">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-800/50 hover:bg-slate-800 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <Icon size={18} className="text-slate-400" />
                    <span className="font-medium text-slate-200">{title}</span>
                    {count > 0 && (
                        <span className="px-2 py-0.5 bg-slate-700 rounded-full text-xs text-slate-300">
                            {count}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {severity && <SeverityBadge level={severity} />}
                    {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </div>
            </button>
            {isOpen && (
                <div className="p-4 bg-slate-900/50">
                    {children}
                </div>
            )}
        </div>
    );
};

// Individual diagnostic item
const DiagnosticItem = ({ item, onViewDetails }) => (
    <div className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg mb-2 hover:bg-slate-800/50 transition-colors">
        <SeverityBadge level={item.severity || 'info'} />
        <div className="flex-1 min-w-0">
            <div className="font-medium text-slate-200 text-sm">{item.message}</div>
            {item.details && (
                <div className="text-xs text-slate-400 mt-1">{item.details}</div>
            )}
            {item.affectedEntities && (
                <div className="flex flex-wrap gap-1 mt-2">
                    {item.affectedEntities.map((entity, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-slate-700 rounded text-xs text-slate-300">
                            {entity}
                        </span>
                    ))}
                </div>
            )}
        </div>
        {onViewDetails && (
            <button
                onClick={() => onViewDetails(item)}
                className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                title="View Details"
            >
                <ExternalLink size={14} />
            </button>
        )}
    </div>
);

// Decision explanation modal
const DecisionExplanationModal = ({ decision, onClose }) => {
    if (!decision) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                        <HelpCircle size={20} className="text-blue-400" />
                        <h3 className="text-lg font-semibold text-white">Decision Explanation</h3>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-slate-700 rounded">
                        <X size={18} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[60vh]">
                    {/* Decision Type */}
                    <div className="mb-6">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Decision Type</div>
                        <div className="text-lg font-medium text-white">{decision.decisionType || 'Unknown'}</div>
                    </div>

                    {/* Main explanation */}
                    <div className="mb-6">
                        <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Explanation</div>
                        <p className="text-slate-300">{decision.explanation || 'No explanation available'}</p>
                    </div>

                    {/* Binding Constraints */}
                    {decision.bindingConstraints?.length > 0 && (
                        <div className="mb-6">
                            <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Binding Constraints</div>
                            <div className="space-y-2">
                                {decision.bindingConstraints.map((constraint, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-800 rounded-lg">
                                        <span className="text-slate-300">{constraint.name}</span>
                                        <span className="text-amber-400 font-mono text-sm">
                                            {constraint.value} / {constraint.limit} {constraint.units}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Penalty Breakdown */}
                    {decision.penaltyBreakdown?.length > 0 && (
                        <div className="mb-6">
                            <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Penalty Breakdown</div>
                            <div className="space-y-2">
                                {decision.penaltyBreakdown.map((penalty, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-800 rounded-lg">
                                        <div>
                                            <span className="text-slate-300">{penalty.qualityField}</span>
                                            <span className="text-xs text-slate-500 ml-2">
                                                ({penalty.deviation > 0 ? '+' : ''}{penalty.deviation.toFixed(2)} from target)
                                            </span>
                                        </div>
                                        <span className="text-red-400 font-mono text-sm">
                                            ${penalty.penaltyValue?.toFixed(2) || '0.00'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Alternatives Considered */}
                    {decision.alternativesConsidered?.length > 0 && (
                        <div>
                            <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Alternatives Considered</div>
                            <div className="space-y-2">
                                {decision.alternativesConsidered.map((alt, idx) => (
                                    <div key={idx} className="p-3 bg-slate-800 rounded-lg">
                                        <div className="flex items-center justify-between">
                                            <span className="text-slate-300">{alt.description}</span>
                                            <span className={alt.selected ? 'text-emerald-400' : 'text-slate-500'}>
                                                {alt.selected ? '✓ Selected' : 'Rejected'}
                                            </span>
                                        </div>
                                        {alt.reason && (
                                            <div className="text-xs text-slate-400 mt-1">{alt.reason}</div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-slate-700 bg-slate-800/50">
                    <button
                        onClick={onClose}
                        className="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

// Main DiagnosticsPanel component
const DiagnosticsPanel = ({ scheduleVersionId, visible, onClose }) => {
    const [diagnostics, setDiagnostics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [selectedDecision, setSelectedDecision] = useState(null);

    useEffect(() => {
        if (visible && scheduleVersionId) {
            fetchDiagnostics();
        }
    }, [visible, scheduleVersionId]);

    const fetchDiagnostics = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/schedule/versions/${scheduleVersionId}/diagnostics`);
            setDiagnostics(res.data);
        } catch (error) {
            console.error('Failed to fetch diagnostics:', error);
            // Set mock data for demo
            setDiagnostics({
                summary: {
                    status: 'completed_with_warnings',
                    totalTasks: 45,
                    feasibilityScore: 0.95,
                    qualityCompliance: 0.88
                },
                infeasibilities: [],
                blockedRoutes: [
                    {
                        id: '1',
                        severity: 'warning',
                        message: 'ROM Stockpile at 95% capacity',
                        details: 'Consider increasing reclaim rate or diverting to alternate destination',
                        affectedEntities: ['ROM-SP-001', 'EX-02']
                    }
                ],
                unmetDemands: [],
                bindingConstraints: [
                    {
                        id: '2',
                        severity: 'info',
                        message: 'Ash constraint binding on Product Coal',
                        details: 'Blend composition limited by ash specification max 15%',
                        affectedEntities: ['Product Coal', 'Blending Point']
                    }
                ],
                decisions: [
                    {
                        id: 'd1',
                        decisionType: 'Routing Decision',
                        explanation: 'Material from Block A-15 routed to ROM Stockpile instead of direct to plant due to quality variance.',
                        bindingConstraints: [
                            { name: 'CV Minimum', value: 24.5, limit: 25.0, units: 'MJ/kg' }
                        ],
                        penaltyBreakdown: [
                            { qualityField: 'CV_ARB', deviation: -0.5, penaltyValue: 125.00 }
                        ],
                        alternativesConsidered: [
                            { description: 'Direct to Plant', selected: false, reason: 'CV below minimum spec' },
                            { description: 'ROM Stockpile for blending', selected: true, reason: 'Allows quality adjustment' }
                        ]
                    }
                ]
            });
        } finally {
            setLoading(false);
        }
    };

    if (!visible) return null;

    return (
        <div className="fixed inset-y-0 right-0 w-[480px] bg-slate-900 border-l border-slate-700 shadow-2xl z-40 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
                <div>
                    <h2 className="text-lg font-semibold text-white">Schedule Diagnostics</h2>
                    <p className="text-xs text-slate-400">Optimization results and explanations</p>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg">
                    <X size={18} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="flex items-center justify-center h-32">
                        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                    </div>
                ) : diagnostics ? (
                    <>
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 gap-3 mb-6">
                            <div className="p-4 bg-slate-800 rounded-lg">
                                <div className="text-xs text-slate-500 mb-1">Feasibility</div>
                                <div className="text-2xl font-bold text-emerald-400">
                                    {((diagnostics.summary?.feasibilityScore || 0) * 100).toFixed(0)}%
                                </div>
                            </div>
                            <div className="p-4 bg-slate-800 rounded-lg">
                                <div className="text-xs text-slate-500 mb-1">Quality Compliance</div>
                                <div className="text-2xl font-bold text-blue-400">
                                    {((diagnostics.summary?.qualityCompliance || 0) * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>

                        {/* Infeasibilities */}
                        <DiagnosticSection
                            title="Infeasibilities"
                            icon={AlertCircle}
                            count={diagnostics.infeasibilities?.length || 0}
                            severity={diagnostics.infeasibilities?.length > 0 ? 'error' : null}
                            defaultOpen={diagnostics.infeasibilities?.length > 0}
                        >
                            {diagnostics.infeasibilities?.length > 0 ? (
                                diagnostics.infeasibilities.map((item, idx) => (
                                    <DiagnosticItem key={idx} item={item} />
                                ))
                            ) : (
                                <p className="text-slate-500 text-sm text-center py-4">No infeasibilities detected</p>
                            )}
                        </DiagnosticSection>

                        {/* Blocked Routes */}
                        <DiagnosticSection
                            title="Blocked Routes / Capacity"
                            icon={Route}
                            count={diagnostics.blockedRoutes?.length || 0}
                            severity={diagnostics.blockedRoutes?.length > 0 ? 'warning' : null}
                        >
                            {diagnostics.blockedRoutes?.length > 0 ? (
                                diagnostics.blockedRoutes.map((item, idx) => (
                                    <DiagnosticItem key={idx} item={item} />
                                ))
                            ) : (
                                <p className="text-slate-500 text-sm text-center py-4">No route capacity issues</p>
                            )}
                        </DiagnosticSection>

                        {/* Binding Constraints */}
                        <DiagnosticSection
                            title="Binding Constraints"
                            icon={Gauge}
                            count={diagnostics.bindingConstraints?.length || 0}
                        >
                            {diagnostics.bindingConstraints?.length > 0 ? (
                                diagnostics.bindingConstraints.map((item, idx) => (
                                    <DiagnosticItem key={idx} item={item} />
                                ))
                            ) : (
                                <p className="text-slate-500 text-sm text-center py-4">No binding constraints</p>
                            )}
                        </DiagnosticSection>

                        {/* Decision Explanations */}
                        <DiagnosticSection
                            title="Decision Explanations"
                            icon={HelpCircle}
                            count={diagnostics.decisions?.length || 0}
                            defaultOpen={true}
                        >
                            {diagnostics.decisions?.length > 0 ? (
                                diagnostics.decisions.map((decision, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => setSelectedDecision(decision)}
                                        className="p-3 bg-slate-800/30 rounded-lg mb-2 hover:bg-slate-800/50 cursor-pointer transition-colors"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium text-slate-200 text-sm">{decision.decisionType}</span>
                                            <ChevronRight size={16} className="text-slate-500" />
                                        </div>
                                        <p className="text-xs text-slate-400 mt-1 line-clamp-2">{decision.explanation}</p>
                                    </div>
                                ))
                            ) : (
                                <p className="text-slate-500 text-sm text-center py-4">No decision explanations available</p>
                            )}
                        </DiagnosticSection>
                    </>
                ) : (
                    <div className="text-center text-slate-500 py-8">
                        No diagnostics available. Run a schedule optimization first.
                    </div>
                )}
            </div>

            {/* Decision Modal */}
            <DecisionExplanationModal
                decision={selectedDecision}
                onClose={() => setSelectedDecision(null)}
            />
        </div>
    );
};

export default DiagnosticsPanel;
