/**
 * OperationsDashboard.jsx - Shift & Operations Dashboard
 * 
 * Features:
 * - Active shift display with status
 * - Shift log with ticket creation
 * - Shift handover workflow
 * - Breadcrumb navigation
 * - Page animations
 */

import React, { useState, useEffect } from 'react';
import { Clock, ClipboardList, Users, Plus, RefreshCw, Play, Pause } from 'lucide-react';
import ShiftLog from '../components/operations/ShiftLog';
import ShiftHandoverForm from '../components/operations/ShiftHandoverForm';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';
import { operationsAPI } from '../services/api';
import Breadcrumb from '../components/ui/Breadcrumb';
import AnimatedCard from '../components/ui/AnimatedCard';
import AnimatedNumber from '../components/ui/AnimatedNumber';

const OperationsDashboard = () => {
    const { currentSiteId, loading: siteLoading } = useSite();
    const [activeShift, setActiveShift] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showHandover, setShowHandover] = useState(false);

    useEffect(() => {
        if (currentSiteId) {
            loadActiveShift();
        }
    }, [currentSiteId]);

    const loadActiveShift = async () => {
        if (!currentSiteId) return;
        try {
            setLoading(true);
            const data = await operationsAPI.getActiveShift(currentSiteId);
            setActiveShift(data);
        } catch (error) {
            console.error('Failed to load active shift:', error);
            setActiveShift(null);
        } finally {
            setLoading(false);
        }
    };

    const handleStartShift = async () => {
        if (!currentSiteId) return;
        try {
            const now = new Date();
            const hour = now.getHours();
            const shiftType = hour >= 6 && hour < 18 ? 'day' : 'night';

            await operationsAPI.startShift(currentSiteId, shiftType);
            await loadActiveShift();
        } catch (error) {
            console.error('Failed to start shift:', error);
        }
    };

    const handleEndShift = async () => {
        if (!activeShift?.shift_id) return;
        try {
            await operationsAPI.endShift(activeShift.shift_id);
            await loadActiveShift();
        } catch (error) {
            console.error('Failed to end shift:', error);
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

    // Determine current shift type based on time
    const now = new Date();
    const hour = now.getHours();
    const shiftName = hour >= 6 && hour < 18 ? 'Day Shift' : 'Night Shift';
    const shiftTime = hour >= 6 && hour < 18 ? '06:00 - 18:00' : '18:00 - 06:00';

    return (
        <AppLayout>
            <div className="flex flex-col h-full page-enter">
                {/* Page Header */}
                <header className="border-b border-slate-800 bg-slate-950/50 px-6 py-4">
                    <Breadcrumb className="mb-3" />
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <ClipboardList className="text-emerald-400" size={24} />
                                Operations
                            </h2>
                            <p className="text-sm text-slate-400 mt-1">Manage shifts, track production, and log events</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={loadActiveShift}
                                disabled={loading}
                                className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2 disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                Refresh
                            </button>
                        </div>
                    </div>
                </header>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    <div className="max-w-6xl mx-auto space-y-6">
                        {/* Active Shift Card */}
                        <AnimatedCard delay={0}>
                            <div className="flex items-center justify-between mb-4">
                                <AnimatedCard.Title icon={Clock}>Current Shift</AnimatedCard.Title>
                                <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <Clock size={14} />
                                    {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                            </div>

                            {loading ? (
                                <div className="animate-pulse space-y-4">
                                    <div className="h-8 w-48 bg-slate-700 rounded"></div>
                                    <div className="flex gap-4">
                                        <div className="h-20 w-40 bg-slate-700 rounded-lg"></div>
                                        <div className="h-20 w-40 bg-slate-700 rounded-lg"></div>
                                    </div>
                                </div>
                            ) : activeShift ? (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-2">
                                            <span className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span>
                                            <span className="text-xl font-semibold text-white">{shiftName}</span>
                                        </div>
                                        <span className="text-slate-400">({shiftTime})</span>
                                        <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-xs font-medium">
                                            Active
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500">Tickets</div>
                                            <div className="text-2xl font-bold text-white mt-1">
                                                <AnimatedNumber value={activeShift.ticket_count || 0} />
                                            </div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500">Tonnes Hauled</div>
                                            <div className="text-2xl font-bold text-white mt-1">
                                                <AnimatedNumber value={activeShift.total_tonnes || 0} formatFn={AnimatedNumber.formatTonnes} />
                                            </div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500">Started</div>
                                            <div className="text-lg font-medium text-white mt-1">
                                                {activeShift.start_time ? new Date(activeShift.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                                            </div>
                                        </div>
                                        <div className="bg-slate-800/50 rounded-lg p-4">
                                            <div className="text-xs text-slate-500">Supervisor</div>
                                            <div className="text-lg font-medium text-white mt-1 truncate">
                                                {activeShift.supervisor_name || 'Not assigned'}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-3 pt-4">
                                        <button
                                            onClick={() => setShowHandover(true)}
                                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm font-medium transition-colors flex items-center gap-2"
                                        >
                                            <Users size={16} />
                                            Handover
                                        </button>
                                        <button
                                            onClick={handleEndShift}
                                            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg text-red-400 text-sm font-medium transition-colors flex items-center gap-2"
                                        >
                                            <Pause size={16} />
                                            End Shift
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <div className="text-slate-400 mb-4">No active shift</div>
                                    <button
                                        onClick={handleStartShift}
                                        className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-medium transition-colors flex items-center gap-2 mx-auto"
                                    >
                                        <Play size={18} />
                                        Start {shiftName}
                                    </button>
                                </div>
                            )}
                        </AnimatedCard>

                        {/* Shift Log */}
                        {activeShift && (
                            <AnimatedCard delay={100}>
                                <AnimatedCard.Header>
                                    <AnimatedCard.Title icon={ClipboardList}>Shift Log</AnimatedCard.Title>
                                </AnimatedCard.Header>
                                <ShiftLog siteId={currentSiteId} shiftId={activeShift?.shift_id} />
                            </AnimatedCard>
                        )}
                    </div>
                </main>

                {/* Handover Modal */}
                {showHandover && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
                        <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-scale-in">
                            <div className="p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">Shift Handover</h3>
                                <ShiftHandoverForm
                                    shiftId={activeShift?.shift_id}
                                    onComplete={() => {
                                        setShowHandover(false);
                                        loadActiveShift();
                                    }}
                                    onCancel={() => setShowHandover(false)}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </AppLayout>
    );
};

export default OperationsDashboard;
