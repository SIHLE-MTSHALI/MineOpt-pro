import React, { useState, useEffect } from 'react';
import SensorChart from '../components/monitoring/SensorChart';
import { monitoringAPI } from '../services/api';

const MonitoringDashboard = () => {
    const [view, setView] = useState('summary');
    const [alerts, setAlerts] = useState([]);
    const [dustData, setDustData] = useState([]);

    // Hardcoded site ID
    const siteId = "site-001";

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const alertData = await monitoringAPI.getSlopeAlerts(siteId);
            setAlerts(alertData);

            // Mocking dust data request for the last 7 days
            const end = new Date();
            const start = new Date();
            start.setDate(start.getDate() - 7);

            // In a real scenario, we'd fetch this. pushing mock data for visualization if empty
            // const dust = await monitoringAPI.getDustExceedances(siteId, start.toISOString(), end.toISOString());
            const mockDust = [
                { time: 'Mon', pm10: 45 },
                { time: 'Tue', pm10: 52 },
                { time: 'Wed', pm10: 38 },
                { time: 'Thu', pm10: 65 },
                { time: 'Fri', pm10: 42 },
                { time: 'Sat', pm10: 30 },
                { time: 'Sun', pm10: 35 },
            ];
            setDustData(mockDust);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="monitoring-dashboard page-container">
            <header className="page-header">
                <h2>Environmental & Geotech Monitoring</h2>
            </header>

            <main className="dashboard-content grid-layout">
                <div className="alerts-section card">
                    <h3>Active Alerts</h3>
                    {alerts.length === 0 ? (
                        <p className="ok-status">No active geotechnical alerts.</p>
                    ) : (
                        <ul className="alert-list">
                            {alerts.map(a => (
                                <li key={a.prism_id} className="alert-item high">
                                    <strong>{a.prism_name}</strong>: {a.rate_mm_day} mm/day movement
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="charts-section">
                    <SensorChart
                        title="PM10 Dust Levels"
                        data={dustData}
                        dataKey="pm10"
                        color="#82ca9d"
                        unit=" ug/m3"
                    />
                </div>
            </main>
        </div>
    );
};

export default MonitoringDashboard;
