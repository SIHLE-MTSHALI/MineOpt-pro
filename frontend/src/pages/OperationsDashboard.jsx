import React, { useState, useEffect } from 'react';
import ShiftLog from '../components/operations/ShiftLog';
import ShiftHandoverForm from '../components/operations/ShiftHandoverForm';
import { operationsAPI } from '../services/api';
import { AppLayout } from '../components/layout/AppLayout';
import { useSite } from '../context/SiteContext';

const OperationsDashboard = () => {
    const [activeShift, setActiveShift] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showHandover, setShowHandover] = useState(false);
    const { currentSiteId, loading: siteLoading } = useSite();

    const loadActiveShift = async () => {
        if (!currentSiteId) return;
        try {
            setLoading(true);
            const shift = await operationsAPI.getActiveShift(currentSiteId);
            setActiveShift(shift);
        } catch (error) {
            console.error("No active shift or error:", error);
            setActiveShift(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (currentSiteId) {
            loadActiveShift();
        }
    }, [currentSiteId]);

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
                    <h2 className="text-xl font-bold text-white">Operations Control</h2>
                    <p className="text-sm text-slate-400 mt-1">Manage shifts, load tickets, and handover operations</p>
                </header>

                {/* Content */}
                <main className="flex-1 overflow-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center h-64">
                            <div className="text-slate-400">Loading operations data...</div>
                        </div>
                    ) : showHandover && activeShift ? (
                        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                            <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
                                <ShiftHandoverForm
                                    shiftId={activeShift.shift_id}
                                    onComplete={() => {
                                        setShowHandover(false);
                                        loadActiveShift();
                                    }}
                                    onCancel={() => setShowHandover(false)}
                                />
                            </div>
                        </div>
                    ) : (
                        <ShiftLog
                            siteId={currentSiteId}
                            activeShift={activeShift}
                            onShiftUpdate={loadActiveShift}
                            onRequestHandover={() => setShowHandover(true)}
                        />
                    )}
                </main>
            </div>
        </AppLayout>
    );
};

export default OperationsDashboard;
