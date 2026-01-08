import React, { useState, useEffect } from 'react';
import PatternDesigner from '../components/drillblast/PatternDesigner';
import BlastEventLogger from '../components/drillblast/BlastEventLogger';
import { drillBlastAPI } from '../services/api';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';

const DrillBlastDashboard = () => {
    const [activeTab, setActiveTab] = useState('patterns');
    const [patterns, setPatterns] = useState([]);
    const [loading, setLoading] = useState(true);
    const { currentSiteId, loading: siteLoading } = useSite();

    const loadPatterns = async () => {
        if (!currentSiteId) return;
        try {
            setLoading(true);
            const data = await drillBlastAPI.getPatterns(currentSiteId);
            setPatterns(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'patterns' && currentSiteId) loadPatterns();
    }, [activeTab, currentSiteId]);

    if (siteLoading) {
        return (
            <AppLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-slate-400">Loading site data...</div>
                </div>
            </AppLayout>
        );
    }

    return (
        <AppLayout>
            <div className="flex flex-col h-full">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <h2 className="text-xl font-bold text-white">Drill & Blast</h2>
                    <p className="text-sm text-slate-400 mt-1">Design patterns, manage drilling, and log blast events</p>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'patterns'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('patterns')}
                        >
                            Patterns
                        </button>
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'new'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('new')}
                        >
                            New Design
                        </button>
                        <button
                            className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'log'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                            onClick={() => setActiveTab('log')}
                        >
                            Log Event
                        </button>
                    </div>
                </div>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {activeTab === 'new' && (
                        <PatternDesigner siteId={currentSiteId} onPatternCreated={() => setActiveTab('patterns')} />
                    )}

                    {activeTab === 'log' && (
                        <BlastEventLogger
                            siteId={currentSiteId}
                            patterns={patterns}
                            onEventLogged={() => setActiveTab('patterns')}
                        />
                    )}

                    {activeTab === 'patterns' && (
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                            {loading ? (
                                <div className="p-8 text-center text-slate-400">Loading patterns...</div>
                            ) : patterns.length === 0 ? (
                                <div className="p-8 text-center text-slate-400">
                                    No patterns found. Create a new design to get started.
                                </div>
                            ) : (
                                <table className="w-full">
                                    <thead className="bg-slate-900/50">
                                        <tr>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">ID</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">Bench</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">Holes</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">Depth (m)</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">Status</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase">Created</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700">
                                        {patterns.map(p => (
                                            <tr key={p.pattern_id} className="hover:bg-slate-800/50 transition-colors">
                                                <td className="px-4 py-3 text-sm text-slate-300">{p.pattern_id.slice(0, 8)}...</td>
                                                <td className="px-4 py-3 text-sm text-slate-300">{p.bench_name}</td>
                                                <td className="px-4 py-3 text-sm text-slate-300">{p.num_rows * p.num_holes_per_row}</td>
                                                <td className="px-4 py-3 text-sm text-slate-300">{p.hole_depth_m}</td>
                                                <td className="px-4 py-3">
                                                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${p.status === 'approved'
                                                            ? 'bg-emerald-500/20 text-emerald-400'
                                                            : p.status === 'drilled'
                                                                ? 'bg-blue-500/20 text-blue-400'
                                                                : 'bg-amber-500/20 text-amber-400'
                                                        }`}>
                                                        {p.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-sm text-slate-400">
                                                    {new Date(p.created_at).toLocaleDateString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}
                </main>
            </div>
        </AppLayout>
    );
};

export default DrillBlastDashboard;
