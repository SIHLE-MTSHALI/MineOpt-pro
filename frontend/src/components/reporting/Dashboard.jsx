import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard = ({ scheduleVersionId }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (scheduleVersionId) {
            fetchStats();
        }
    }, [scheduleVersionId]);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/reporting/dashboard/${scheduleVersionId}`);
            setStats(res.data);
        } catch (e) {
            console.error("Failed to fetch dashboard stats", e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="flex h-full items-center justify-center text-slate-400">Loading Dashboard...</div>;
    }

    if (!stats) {
        return <div className="flex h-full items-center justify-center text-slate-500">No Data Available. Generate a Schedule first.</div>;
    }

    return (
        <div className="h-full w-full bg-slate-900 p-6 overflow-y-auto">
            <h2 className="text-2xl font-bold text-white mb-6">Production Overview</h2>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">Total Mined</p>
                    <p className="text-3xl font-bold text-white mt-1">{stats.total_tons.toLocaleString()} <span className="text-lg text-slate-500 font-normal">tons</span></p>
                </div>

                <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">Coal Production</p>
                    <p className="text-3xl font-bold text-blue-400 mt-1">{stats.coal_tons.toLocaleString()} <span className="text-lg text-slate-500 font-normal">tons</span></p>
                </div>

                <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg">
                    <p className="text-sm text-slate-400 font-medium uppercase tracking-wider">Stripping Ratio</p>
                    <p className="text-3xl font-bold text-amber-400 mt-1">{stats.stripping_ratio} <span className="text-lg text-slate-500 font-normal">W:C</span></p>
                </div>
            </div>

            {/* Charts */}
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 shadow-lg h-96">
                <h3 className="text-lg font-bold text-white mb-4">Production by Period</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={stats.chart_data}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                            itemStyle={{ color: '#f1f5f9' }}
                        />
                        <Legend />
                        <Bar dataKey="coal" name="Coal" stackId="a" fill="#3b82f6" />
                        <Bar dataKey="waste" name="Waste" stackId="a" fill="#ef4444" />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default Dashboard;
