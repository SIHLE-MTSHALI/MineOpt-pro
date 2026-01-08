import React, { useState, useEffect } from 'react';
import ShiftLog from '../components/operations/ShiftLog';
import ShiftHandoverForm from '../components/operations/ShiftHandoverForm';
import { operationsAPI } from '../services/api';

const OperationsDashboard = () => {
    const [activeShift, setActiveShift] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showHandover, setShowHandover] = useState(false);
    const siteId = "site-001"; // Hardcoded for now

    const loadActiveShift = async () => {
        try {
            setLoading(true);
            const shift = await operationsAPI.getActiveShift(siteId);
            setActiveShift(shift);
        } catch (error) {
            console.error("No active shift or error:", error);
            setActiveShift(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadActiveShift();
    }, []);

    if (loading) return <div>Loading Operations...</div>;

    return (
        <div className="operations-dashboard page-container">
            <header className="page-header">
                <h2>Operations Control</h2>
            </header>

            <main className="dashboard-content">
                {showHandover && activeShift ? (
                    <div className="modal-overlay">
                        <ShiftHandoverForm
                            shiftId={activeShift.shift_id}
                            onComplete={() => {
                                setShowHandover(false);
                                loadActiveShift();
                            }}
                            onCancel={() => setShowHandover(false)}
                        />
                    </div>
                ) : (
                    <ShiftLog
                        siteId={siteId}
                        activeShift={activeShift}
                        onShiftUpdate={loadActiveShift}
                        onRequestHandover={() => setShowHandover(true)}
                    />
                )}
            </main>
        </div>
    );
};

export default OperationsDashboard;
