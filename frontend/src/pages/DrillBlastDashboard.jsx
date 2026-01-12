/**
 * DrillBlastDashboard.jsx - Drill & Blast Management Dashboard
 * 
 * Features:
 * - Blast pattern list with status badges
 * - Pattern designer
 * - Blast event logging
 * - Breadcrumb navigation
 * - Page animations
 */

import React, { useState, useEffect } from 'react';
import { Zap, Target, Calendar, Plus, RefreshCw } from 'lucide-react';
import PatternDesigner from '../components/drillblast/PatternDesigner';
import BlastEventLogger from '../components/drillblast/BlastEventLogger';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';
import { drillBlastAPI } from '../services/api';
import Breadcrumb from '../components/ui/Breadcrumb';
import AnimatedCard from '../components/ui/AnimatedCard';

// Status badge component
const PatternStatusBadge = ({ status }) => {
    const statusConfig = {
        designed: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Designed' },
        drilled: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Drilled' },
        loaded: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Loaded' },
        blasted: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Blasted' },
        pending: { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'Pending' }
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
            {config.label}
        </span>
    );
};

const DrillBlastDashboard = () => {
    const [activeTab, setActiveTab] = useState('patterns');
    const [patterns, setPatterns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedPattern, setSelectedPattern] = useState(null);
    const { currentSiteId, loading: siteLoading } = useSite();

    useEffect(() => {
        if (currentSiteId) {
            loadPatterns();
        }
    }, [currentSiteId]);

    const loadPatterns = async () => {
        if (!currentSiteId) return;
        try {
            setLoading(true);
            const data = await drillBlastAPI.getPatterns(currentSiteId);
            setPatterns(data || []);
        } catch (error) {
            console.error('Failed to load patterns:', error);
            setPatterns([]);
        } finally {
            setLoading(false);
        }
    };

    if (siteLoading) {
        return (
            <AppLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-slate-400 animate-pulse">Loading site data...</div>
                </div>
            </AppLayout>
        );
    }

    const tabs = [
        { id: 'patterns', label: 'Patterns', icon: Target },
        { id: 'design', label: 'New Design', icon: Plus },
        { id: 'events', label: 'Log Event', icon: Calendar }
    ];

    return (
        <AppLayout>
            <div className="flex flex-col h-full page-enter">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <Breadcrumb className="mb-3" />
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <Zap className="text-amber-400" size={24} />
                                Drill & Blast
                            </h2>
                            <p className="text-sm text-slate-400 mt-1">Design blast patterns, track drilling, and log blast events</p>
                        </div>
                        <button
                            onClick={loadPatterns}
                            disabled={loading}
                            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2 disabled:opacity-50"
                        >
                            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            Refresh
                        </button>
                    </div>
                </header>

                {/* Tab Controls */}
                <div className="border-b border-slate-800 bg-slate-900/50 px-6">
                    <div className="flex gap-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all relative ${activeTab === tab.id
                                        ? 'text-amber-400'
                                        : 'text-slate-400 hover:text-slate-200'
                                    }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <tab.icon size={16} />
                                {tab.label}
                                {activeTab === tab.id && (
                                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-t-full" />
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {activeTab === 'patterns' && (
                        <div className="space-y-4">
                            {loading ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {[1, 2, 3, 4, 5, 6].map(i => (
                                        <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 animate-pulse">
                                            <div className="h-5 w-32 bg-slate-700 rounded mb-3"></div>
                                            <div className="h-4 w-48 bg-slate-700 rounded mb-4"></div>
                                            <div className="h-6 w-20 bg-slate-700 rounded-full"></div>
                                        </div>
                                    ))}
                                </div>
                            ) : patterns.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {patterns.map((pattern, idx) => (
                                        <AnimatedCard
                                            key={pattern.pattern_id}
                                            delay={idx * 50}
                                            onClick={() => setSelectedPattern(pattern)}
                                            className="cursor-pointer"
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div>
                                                    <h3 className="font-medium text-white">{pattern.name || `Pattern ${idx + 1}`}</h3>
                                                    <p className="text-xs text-slate-400 mt-1">
                                                        {pattern.hole_count || 0} holes • {pattern.total_explosives_kg?.toFixed(0) || 0} kg
                                                    </p>
                                                </div>
                                                <Target size={18} className="text-amber-400" />
                                            </div>

                                            <div className="flex items-center justify-between">
                                                <PatternStatusBadge status={pattern.status} />
                                                <span className="text-xs text-slate-500">
                                                    {pattern.created_at ? new Date(pattern.created_at).toLocaleDateString() : '-'}
                                                </span>
                                            </div>
                                        </AnimatedCard>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-slate-400">
                                    <Target size={48} className="mx-auto mb-4 opacity-50" />
                                    <p>No blast patterns found</p>
                                    <button
                                        onClick={() => setActiveTab('design')}
                                        className="mt-4 px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-white text-sm font-medium transition-colors"
                                    >
                                        Create First Pattern
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'design' && (
                        <PatternDesigner
                            siteId={currentSiteId}
                            onSave={() => {
                                loadPatterns();
                                setActiveTab('patterns');
                            }}
                        />
                    )}

                    {activeTab === 'events' && (
                        <BlastEventLogger
                            siteId={currentSiteId}
                            patterns={patterns}
                            onEventLogged={loadPatterns}
                        />
                    )}
                </main>
            </div>
        </AppLayout>
    );
};

export default DrillBlastDashboard;
