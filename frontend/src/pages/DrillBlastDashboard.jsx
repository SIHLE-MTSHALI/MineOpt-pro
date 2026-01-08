import React, { useState, useEffect } from 'react';
import PatternDesigner from '../components/drillblast/PatternDesigner';
import BlastEventLogger from '../components/drillblast/BlastEventLogger';
import { drillBlastAPI } from '../services/api';

const DrillBlastDashboard = () => {
    const [activeTab, setActiveTab] = useState('patterns');
    const [patterns, setPatterns] = useState([]);
    const [loading, setLoading] = useState(true);
    const siteId = "site-001"; // Hardcoded for now

    const loadPatterns = async () => {
        try {
            setLoading(true);
            const data = await drillBlastAPI.getPatterns(siteId);
            setPatterns(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'patterns') loadPatterns();
    }, [activeTab]);

    return (
        <div className="drill-blast-dashboard page-container">
            <header className="page-header">
                <h2>Drill & Blast</h2>
                <div className="tab-controls">
                    <button
                        className={activeTab === 'patterns' ? 'active' : ''}
                        onClick={() => setActiveTab('patterns')}
                    >
                        Patterns
                    </button>
                    <button
                        className={activeTab === 'new' ? 'active' : ''}
                        onClick={() => setActiveTab('new')}
                    >
                        New Design
                    </button>
                    <button
                        className={activeTab === 'log' ? 'active' : ''}
                        onClick={() => setActiveTab('log')}
                    >
                        Log Event
                    </button>
                </div>
            </header>

            <main className="dashboard-content">
                {activeTab === 'new' && (
                    <PatternDesigner siteId={siteId} onPatternCreated={() => setActiveTab('patterns')} />
                )}

                {activeTab === 'log' && (
                    <BlastEventLogger
                        siteId={siteId}
                        patterns={patterns}
                        onEventLogged={() => setActiveTab('patterns')}
                    />
                )}

                {activeTab === 'patterns' && (
                    <div className="patterns-list">
                        {loading ? <p>Loading patterns...</p> : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Bench</th>
                                        <th>Holes</th>
                                        <th>Depth (m)</th>
                                        <th>Status</th>
                                        <th>Created</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {patterns.map(p => (
                                        <tr key={p.pattern_id}>
                                            <td>{p.pattern_id.slice(0, 8)}...</td>
                                            <td>{p.bench_name}</td>
                                            <td>{p.num_rows * p.num_holes_per_row}</td>
                                            <td>{p.hole_depth_m}</td>
                                            <td>
                                                <span className={`status-badge ${p.status}`}>
                                                    {p.status}
                                                </span>
                                            </td>
                                            <td>{new Date(p.created_at).toLocaleDateString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default DrillBlastDashboard;
