import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Loader2, CheckCircle, XCircle, ArrowLeft, Factory, Truck, Crosshair, Users, Wind, Mountain } from 'lucide-react';
import axios from 'axios';
import { AppLayout } from '../components/layout/AppLayout';

const API_BASE = 'http://localhost:8000';

const SeedDataPage = () => {
    const navigate = useNavigate();
    const [status, setStatus] = useState('idle'); // idle, seeding, success, error
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const steps = [
        { icon: Factory, label: 'Creating Sites', percent: 5 },
        { icon: Database, label: 'Materials & Calendars', percent: 15 },
        { icon: Truck, label: 'Equipment Fleet', percent: 30 },
        { icon: Crosshair, label: 'GPS Readings', percent: 45 },
        { icon: Truck, label: 'Haul Cycles', percent: 55 },
        { icon: Mountain, label: 'Blast Patterns', percent: 65 },
        { icon: Users, label: 'Shifts & Tickets', percent: 75 },
        { icon: Crosshair, label: 'Geotechnical Data', percent: 85 },
        { icon: Wind, label: 'Environmental Data', percent: 95 },
        { icon: CheckCircle, label: 'Finalizing', percent: 100 },
    ];

    const simulateProgress = () => {
        let stepIndex = 0;
        const interval = setInterval(() => {
            if (stepIndex < steps.length) {
                setProgress(steps[stepIndex].percent);
                setCurrentStep(steps[stepIndex].label);
                stepIndex++;
            } else {
                clearInterval(interval);
            }
        }, 2500); // Advance every 2.5 seconds
        return interval;
    };

    const handleSeedData = async () => {
        setStatus('seeding');
        setProgress(0);
        setCurrentStep('Initializing...');
        setError(null);
        setResults(null);

        // Start simulated progress
        const progressInterval = simulateProgress();

        try {
            const response = await axios.post(`${API_BASE}/config/seed-comprehensive-demo`);
            clearInterval(progressInterval);
            setProgress(100);
            setCurrentStep('Complete!');
            setResults(response.data);
            setStatus('success');
        } catch (err) {
            clearInterval(progressInterval);
            setError(err.response?.data?.detail || err.message || 'Seeding failed');
            setStatus('error');
        }
    };

    return (
        <AppLayout>
            <div className="flex-1 overflow-auto bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
                <div className="max-w-2xl mx-auto">
                    {/* Header */}
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
                    >
                        <ArrowLeft size={20} />
                        Back
                    </button>

                    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur-sm">
                        <div className="text-center mb-8">
                            <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Database size={32} className="text-blue-400" />
                            </div>
                            <h1 className="text-2xl font-bold text-white mb-2">Seed Demo Data</h1>
                            <p className="text-slate-400">
                                Generate comprehensive demo data for testing and demonstration
                            </p>
                        </div>

                        {/* Data Preview */}
                        <div className="bg-slate-900/50 rounded-xl p-4 mb-6">
                            <h3 className="text-sm font-medium text-slate-300 mb-3">Data to be generated:</h3>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex justify-between text-slate-400">
                                    <span>Coal Mining Sites</span>
                                    <span className="text-white font-medium">3</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Equipment Pieces</span>
                                    <span className="text-white font-medium">~130</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Days of History</span>
                                    <span className="text-white font-medium">90</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Shifts</span>
                                    <span className="text-white font-medium">~540</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Blast Patterns</span>
                                    <span className="text-white font-medium">~50</span>
                                </div>
                                <div className="flex justify-between text-slate-400">
                                    <span>Load Tickets</span>
                                    <span className="text-white font-medium">~50,000+</span>
                                </div>
                            </div>
                        </div>

                        {/* Progress */}
                        {status === 'seeding' && (
                            <div className="mb-6">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm text-slate-400">{currentStep}</span>
                                    <span className="text-sm text-blue-400 font-medium">{progress}%</span>
                                </div>
                                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500 ease-out"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <p className="text-xs text-slate-500 mt-2 text-center">
                                    This may take 30-60 seconds...
                                </p>
                            </div>
                        )}

                        {/* Success */}
                        {status === 'success' && results && (
                            <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                                <div className="flex items-center gap-2 text-emerald-400 mb-3">
                                    <CheckCircle size={20} />
                                    <span className="font-medium">Seeding Complete!</span>
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="text-slate-400">Sites: <span className="text-white">{results.sites?.length || 0}</span></div>
                                    <div className="text-slate-400">Equipment: <span className="text-white">{results.equipment_count?.toLocaleString()}</span></div>
                                    <div className="text-slate-400">GPS Readings: <span className="text-white">{results.gps_readings?.toLocaleString()}</span></div>
                                    <div className="text-slate-400">Haul Cycles: <span className="text-white">{results.haul_cycles?.toLocaleString()}</span></div>
                                    <div className="text-slate-400">Blast Patterns: <span className="text-white">{results.blast_patterns}</span></div>
                                    <div className="text-slate-400">Shifts: <span className="text-white">{results.shifts}</span></div>
                                    <div className="text-slate-400">Load Tickets: <span className="text-white">{results.load_tickets?.toLocaleString()}</span></div>
                                    <div className="text-slate-400">Prism Readings: <span className="text-white">{results.prism_readings?.toLocaleString()}</span></div>
                                </div>
                            </div>
                        )}

                        {/* Error */}
                        {status === 'error' && (
                            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
                                <div className="flex items-center gap-2 text-red-400">
                                    <XCircle size={20} />
                                    <span className="font-medium">Error: {error}</span>
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3">
                            <button
                                onClick={handleSeedData}
                                disabled={status === 'seeding'}
                                className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl font-medium transition-all ${status === 'seeding'
                                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                                    }`}
                            >
                                {status === 'seeding' ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Seeding Data...
                                    </>
                                ) : status === 'success' ? (
                                    <>
                                        <Database size={20} />
                                        Seed Again
                                    </>
                                ) : (
                                    <>
                                        <Database size={20} />
                                        Start Seeding
                                    </>
                                )}
                            </button>

                            {status === 'success' && (
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="flex items-center gap-2 py-3 px-6 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-medium transition-all"
                                >
                                    View Dashboard
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Warning */}
                    <p className="text-center text-slate-500 text-sm mt-4">
                        ⚠️ This will add data to the existing database. Run only once for demo purposes.
                    </p>
                </div>
            </div>
        </AppLayout>
    );
};

export default SeedDataPage;

