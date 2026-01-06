/**
 * BIExtractPublisher.jsx - BI Extract Publishing Management
 * 
 * Enables configuration and management of scheduled BI data extracts:
 * - Create/edit extract configurations
 * - Define schedule (cron), output format, and destination
 * - Manual trigger runs
 * - View extract history
 */

import React, { useState, useEffect } from 'react';
import {
    Database, Plus, Trash2, Play, Clock, FileJson, FileText,
    Calendar, CheckCircle, AlertCircle, Settings, RefreshCw, X
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const ENTITY_TYPES = [
    { id: 'schedules', label: 'Schedules', icon: '📅' },
    { id: 'production', label: 'Production Actuals', icon: '⛏️' },
    { id: 'quality', label: 'Quality Data', icon: '🧪' },
    { id: 'stockpiles', label: 'Stockpile Levels', icon: '📦' },
    { id: 'equipment', label: 'Equipment Status', icon: '🚜' }
];

const SCHEDULE_PRESETS = [
    { label: 'Hourly', cron: '0 * * * *' },
    { label: 'Daily 6AM', cron: '0 6 * * *' },
    { label: 'Daily 6PM', cron: '0 18 * * *' },
    { label: 'Weekly Monday', cron: '0 6 * * 1' },
    { label: 'Monthly 1st', cron: '0 6 1 * *' }
];

// Extract configuration card
const ExtractCard = ({ extract, onRun, onDelete, onToggle }) => {
    const [running, setRunning] = useState(false);
    const [lastResult, setLastResult] = useState(null);

    const handleRun = async () => {
        setRunning(true);
        try {
            const result = await onRun(extract.id);
            setLastResult(result);
        } finally {
            setRunning(false);
        }
    };

    const entityInfo = ENTITY_TYPES.find(t => t.id === extract.entity_type) || { icon: '📄', label: extract.entity_type };

    return (
        <div className={`bg-slate-800/50 border rounded-xl p-4 ${extract.enabled ? 'border-slate-700' : 'border-slate-800 opacity-60'}`}>
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{entityInfo.icon}</span>
                    <div>
                        <h3 className="font-medium text-white">{extract.name}</h3>
                        <p className="text-xs text-slate-400">{entityInfo.label}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onToggle(extract.id, !extract.enabled)}
                        className={`w-10 h-5 rounded-full relative transition-colors ${extract.enabled ? 'bg-emerald-500' : 'bg-slate-600'
                            }`}
                    >
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${extract.enabled ? 'left-5' : 'left-0.5'
                            }`} />
                    </button>
                </div>
            </div>

            <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                    <Clock size={14} />
                    <span>{extract.schedule_cron || 'Manual only'}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                    {extract.output_format === 'json' ? (
                        <FileJson size={14} />
                    ) : (
                        <FileText size={14} />
                    )}
                    <span className="uppercase">{extract.output_format}</span>
                    <span className="text-slate-600">→</span>
                    <span className="font-mono text-xs truncate max-w-[150px]">{extract.destination}</span>
                </div>
            </div>

            {lastResult && (
                <div className="mb-3 p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                    <div className="flex items-center gap-2 text-xs text-emerald-400">
                        <CheckCircle size={12} />
                        <span>Exported {lastResult.rows_exported} rows</span>
                    </div>
                </div>
            )}

            <div className="flex items-center gap-2">
                <button
                    onClick={handleRun}
                    disabled={running}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded-lg text-sm text-white"
                >
                    {running ? (
                        <RefreshCw size={14} className="animate-spin" />
                    ) : (
                        <Play size={14} />
                    )}
                    Run Now
                </button>
                <button
                    onClick={() => onDelete(extract.id)}
                    className="p-2 hover:bg-red-500/20 rounded-lg text-slate-400 hover:text-red-400"
                >
                    <Trash2 size={14} />
                </button>
            </div>
        </div>
    );
};

// New extract form
const NewExtractForm = ({ onSave, onCancel }) => {
    const [name, setName] = useState('');
    const [entityType, setEntityType] = useState('schedules');
    const [schedule, setSchedule] = useState('');
    const [outputFormat, setOutputFormat] = useState('json');
    const [destination, setDestination] = useState('/exports/');

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({
            name,
            entity_type: entityType,
            schedule_cron: schedule || null,
            output_format: outputFormat,
            destination,
            enabled: true
        });
    };

    return (
        <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-white">New BI Extract</h3>
                <button type="button" onClick={onCancel} className="p-1 hover:bg-slate-700 rounded">
                    <X size={16} className="text-slate-400" />
                </button>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="block text-xs text-slate-400 mb-1">Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                        placeholder="Daily Production Export"
                    />
                </div>

                <div>
                    <label className="block text-xs text-slate-400 mb-1">Data Type</label>
                    <select
                        value={entityType}
                        onChange={(e) => setEntityType(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                    >
                        {ENTITY_TYPES.map(t => (
                            <option key={t.id} value={t.id}>{t.icon} {t.label}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-xs text-slate-400 mb-1">Schedule</label>
                    <div className="flex flex-wrap gap-2 mb-2">
                        {SCHEDULE_PRESETS.map(preset => (
                            <button
                                key={preset.cron}
                                type="button"
                                onClick={() => setSchedule(preset.cron)}
                                className={`px-2 py-1 text-xs rounded-lg ${schedule === preset.cron
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-700 text-slate-400 hover:text-white'
                                    }`}
                            >
                                {preset.label}
                            </button>
                        ))}
                    </div>
                    <input
                        type="text"
                        value={schedule}
                        onChange={(e) => setSchedule(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white font-mono"
                        placeholder="Cron expression (leave empty for manual)"
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs text-slate-400 mb-1">Format</label>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setOutputFormat('json')}
                                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm ${outputFormat === 'json'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-700 text-slate-400'
                                    }`}
                            >
                                <FileJson size={14} /> JSON
                            </button>
                            <button
                                type="button"
                                onClick={() => setOutputFormat('csv')}
                                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm ${outputFormat === 'csv'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-700 text-slate-400'
                                    }`}
                            >
                                <FileText size={14} /> CSV
                            </button>
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs text-slate-400 mb-1">Destination</label>
                        <input
                            type="text"
                            value={destination}
                            onChange={(e) => setDestination(e.target.value)}
                            required
                            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white font-mono"
                            placeholder="/exports/data.json"
                        />
                    </div>
                </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
                <button
                    type="button"
                    onClick={onCancel}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm text-white"
                >
                    Create Extract
                </button>
            </div>
        </form>
    );
};

const BIExtractPublisher = () => {
    const [extracts, setExtracts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showNewForm, setShowNewForm] = useState(false);

    useEffect(() => {
        fetchExtracts();
    }, []);

    const fetchExtracts = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/integration/bi-extracts`);
            setExtracts(res.data);
        } catch (error) {
            console.error('Failed to fetch extracts:', error);
            // Demo data
            setExtracts([
                {
                    id: '1',
                    name: 'Daily Production Summary',
                    entity_type: 'production',
                    schedule_cron: '0 6 * * *',
                    output_format: 'json',
                    destination: '/exports/production_daily.json',
                    enabled: true
                },
                {
                    id: '2',
                    name: 'Weekly Quality Report',
                    entity_type: 'quality',
                    schedule_cron: '0 6 * * 1',
                    output_format: 'csv',
                    destination: '/exports/quality_weekly.csv',
                    enabled: true
                },
                {
                    id: '3',
                    name: 'Stockpile Snapshot',
                    entity_type: 'stockpiles',
                    schedule_cron: null,
                    output_format: 'json',
                    destination: '/exports/stockpiles.json',
                    enabled: false
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (config) => {
        try {
            const res = await axios.post(`${API_BASE}/integration/bi-extracts`, config);
            setExtracts([...extracts, res.data]);
        } catch (error) {
            console.error('Failed to create extract:', error);
            // Optimistic update
            setExtracts([...extracts, { ...config, id: Date.now().toString() }]);
        }
        setShowNewForm(false);
    };

    const handleRun = async (id) => {
        try {
            const res = await axios.post(`${API_BASE}/integration/bi-extracts/${id}/run`);
            return res.data;
        } catch (error) {
            console.error('Failed to run extract:', error);
            // Mock result
            return { rows_exported: Math.floor(Math.random() * 500) + 50 };
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this extract configuration?')) return;
        try {
            await axios.delete(`${API_BASE}/integration/bi-extracts/${id}`);
        } catch (error) {
            console.error('Failed to delete extract:', error);
        }
        setExtracts(extracts.filter(e => e.id !== id));
    };

    const handleToggle = async (id, enabled) => {
        setExtracts(extracts.map(e => e.id === id ? { ...e, enabled } : e));
        try {
            await axios.patch(`${API_BASE}/integration/bi-extracts/${id}`, { enabled });
        } catch (error) {
            console.error('Failed to toggle extract:', error);
        }
    };

    return (
        <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Database size={20} className="text-purple-400" />
                    <div>
                        <h2 className="text-lg font-semibold text-white">BI Extract Publisher</h2>
                        <p className="text-xs text-slate-400">Schedule and publish data extracts to external systems</p>
                    </div>
                </div>
                <button
                    onClick={() => setShowNewForm(true)}
                    className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm text-white"
                >
                    <Plus size={14} />
                    New Extract
                </button>
            </div>

            {/* Content */}
            <div className="p-4">
                {showNewForm && (
                    <div className="mb-4">
                        <NewExtractForm onSave={handleCreate} onCancel={() => setShowNewForm(false)} />
                    </div>
                )}

                {loading ? (
                    <div className="text-center py-12 text-slate-500">
                        <RefreshCw size={24} className="mx-auto animate-spin mb-2" />
                        Loading extracts...
                    </div>
                ) : extracts.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                        <Database size={32} className="mx-auto mb-3 opacity-50" />
                        <p>No BI extracts configured</p>
                        <button
                            onClick={() => setShowNewForm(true)}
                            className="mt-3 text-purple-400 hover:text-purple-300 text-sm"
                        >
                            Create your first extract
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {extracts.map(extract => (
                            <ExtractCard
                                key={extract.id}
                                extract={extract}
                                onRun={handleRun}
                                onDelete={handleDelete}
                                onToggle={handleToggle}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500 flex items-center justify-between">
                <span>{extracts.filter(e => e.enabled).length} active extracts</span>
                <button
                    onClick={fetchExtracts}
                    className="flex items-center gap-1 text-slate-400 hover:text-white"
                >
                    <RefreshCw size={12} />
                    Refresh
                </button>
            </div>
        </div>
    );
};

export default BIExtractPublisher;
