/**
 * ExternalIdMappingUI.jsx - External ID Mapping Management
 * 
 * Provides UI for mapping between external system IDs and internal MineOpt IDs:
 * - View all mappings by entity type
 * - Add/edit/delete mappings
 * - Import mappings from CSV
 * - Validate mappings
 */

import React, { useState, useEffect } from 'react';
import {
    Link2, Plus, Trash2, Upload, Download, Search,
    CheckCircle, AlertCircle, RefreshCw, Edit3, Save, X
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Entity type tabs
const ENTITY_TYPES = [
    { id: 'parcel', label: 'Parcels', icon: '📦' },
    { id: 'resource', label: 'Resources', icon: '🚜' },
    { id: 'location', label: 'Locations', icon: '📍' },
    { id: 'product', label: 'Products', icon: '⚫' }
];

// Mapping row component
const MappingRow = ({ mapping, onEdit, onDelete, isEditing, onSave, onCancel }) => {
    const [externalId, setExternalId] = useState(mapping.external_id);
    const [internalId, setInternalId] = useState(mapping.internal_id);
    const [description, setDescription] = useState(mapping.description || '');

    if (isEditing) {
        return (
            <tr className="bg-slate-800/50">
                <td className="px-4 py-2">
                    <input
                        type="text"
                        value={externalId}
                        onChange={(e) => setExternalId(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        placeholder="External ID"
                    />
                </td>
                <td className="px-4 py-2">
                    <input
                        type="text"
                        value={internalId}
                        onChange={(e) => setInternalId(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        placeholder="Internal ID"
                    />
                </td>
                <td className="px-4 py-2">
                    <input
                        type="text"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                        placeholder="Description (optional)"
                    />
                </td>
                <td className="px-4 py-2">
                    <span className="text-xs text-slate-500">-</span>
                </td>
                <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => onSave({ ...mapping, external_id: externalId, internal_id: internalId, description })}
                            className="p-1 hover:bg-emerald-500/20 rounded text-emerald-400"
                        >
                            <Save size={14} />
                        </button>
                        <button
                            onClick={onCancel}
                            className="p-1 hover:bg-slate-600 rounded text-slate-400"
                        >
                            <X size={14} />
                        </button>
                    </div>
                </td>
            </tr>
        );
    }

    return (
        <tr className="border-b border-slate-700/50 hover:bg-slate-800/30">
            <td className="px-4 py-3">
                <span className="font-mono text-sm text-slate-300">{mapping.external_id}</span>
            </td>
            <td className="px-4 py-3">
                <span className="font-mono text-sm text-blue-400">{mapping.internal_id}</span>
            </td>
            <td className="px-4 py-3">
                <span className="text-sm text-slate-400">{mapping.description || '-'}</span>
            </td>
            <td className="px-4 py-3">
                {mapping.validated ? (
                    <span className="flex items-center gap-1 text-xs text-emerald-400">
                        <CheckCircle size={12} /> Valid
                    </span>
                ) : (
                    <span className="flex items-center gap-1 text-xs text-amber-400">
                        <AlertCircle size={12} /> Unverified
                    </span>
                )}
            </td>
            <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onEdit(mapping)}
                        className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-white"
                    >
                        <Edit3 size={14} />
                    </button>
                    <button
                        onClick={() => onDelete(mapping.id)}
                        className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400"
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </td>
        </tr>
    );
};

const ExternalIdMappingUI = () => {
    const [activeTab, setActiveTab] = useState('parcel');
    const [mappings, setMappings] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [showAddNew, setShowAddNew] = useState(false);

    useEffect(() => {
        fetchMappings();
    }, [activeTab]);

    const fetchMappings = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/integration/mappings?entity_type=${activeTab}`);
            setMappings(res.data);
        } catch (error) {
            console.error('Failed to fetch mappings:', error);
            // Mock data for demo
            setMappings([
                { id: '1', external_id: 'PIT-A-15', internal_id: 'parcel-abc123', description: 'Block A15', validated: true },
                { id: '2', external_id: 'PIT-B-22', internal_id: 'parcel-def456', description: 'Block B22', validated: true },
                { id: '3', external_id: 'LAB-SAMPLE-001', internal_id: 'parcel-ghi789', description: 'Lab reference', validated: false },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (mapping) => {
        try {
            if (mapping.id) {
                await axios.put(`${API_BASE}/integration/mappings/${mapping.id}`, mapping);
            } else {
                await axios.post(`${API_BASE}/integration/mappings`, { ...mapping, entity_type: activeTab });
            }
            setEditingId(null);
            setShowAddNew(false);
            fetchMappings();
        } catch (error) {
            console.error('Failed to save mapping:', error);
            // Optimistic update for demo
            if (mapping.id) {
                setMappings(mappings.map(m => m.id === mapping.id ? mapping : m));
            } else {
                setMappings([...mappings, { ...mapping, id: Date.now().toString() }]);
            }
            setEditingId(null);
            setShowAddNew(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this mapping?')) return;
        try {
            await axios.delete(`${API_BASE}/integration/mappings/${id}`);
            fetchMappings();
        } catch (error) {
            console.error('Failed to delete mapping:', error);
            // Optimistic update for demo
            setMappings(mappings.filter(m => m.id !== id));
        }
    };

    const handleImportCSV = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('entity_type', activeTab);

        try {
            await axios.post(`${API_BASE}/integration/mappings/import`, formData);
            fetchMappings();
        } catch (error) {
            console.error('Failed to import CSV:', error);
            alert('Import failed. Please check CSV format.');
        }
    };

    const handleExportCSV = () => {
        const headers = 'external_id,internal_id,description';
        const rows = mappings.map(m => `${m.external_id},${m.internal_id},${m.description || ''}`);
        const csv = [headers, ...rows].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${activeTab}_mappings.csv`;
        a.click();
    };

    const filteredMappings = mappings.filter(m =>
        m.external_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.internal_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (m.description || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link2 size={20} className="text-blue-400" />
                    <div>
                        <h2 className="text-lg font-semibold text-white">External ID Mappings</h2>
                        <p className="text-xs text-slate-400">Map external system IDs to MineOpt entities</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <label className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300 cursor-pointer">
                        <Upload size={14} className="inline mr-2" />
                        Import CSV
                        <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
                    </label>
                    <button
                        onClick={handleExportCSV}
                        className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300"
                    >
                        <Download size={14} className="inline mr-2" />
                        Export
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-700">
                {ENTITY_TYPES.map(type => (
                    <button
                        key={type.id}
                        onClick={() => setActiveTab(type.id)}
                        className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === type.id
                                ? 'text-blue-400 border-b-2 border-blue-400 bg-slate-800/50'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800/30'
                            }`}
                    >
                        <span>{type.icon}</span>
                        {type.label}
                    </button>
                ))}
            </div>

            {/* Toolbar */}
            <div className="px-4 py-3 bg-slate-800/30 flex items-center justify-between">
                <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search mappings..."
                        className="bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 w-64"
                    />
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchMappings}
                        className="p-2 hover:bg-slate-700 rounded-lg text-slate-400"
                    >
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                    </button>
                    <button
                        onClick={() => { setShowAddNew(true); setEditingId(null); }}
                        className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm text-white"
                    >
                        <Plus size={14} />
                        Add Mapping
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="text-xs text-slate-500 uppercase tracking-wider border-b border-slate-700">
                            <th className="px-4 py-3 text-left">External ID</th>
                            <th className="px-4 py-3 text-left">Internal ID</th>
                            <th className="px-4 py-3 text-left">Description</th>
                            <th className="px-4 py-3 text-left">Status</th>
                            <th className="px-4 py-3 text-left">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {showAddNew && (
                            <MappingRow
                                mapping={{ external_id: '', internal_id: '', description: '' }}
                                isEditing={true}
                                onSave={handleSave}
                                onCancel={() => setShowAddNew(false)}
                            />
                        )}
                        {filteredMappings.map(mapping => (
                            <MappingRow
                                key={mapping.id}
                                mapping={mapping}
                                isEditing={editingId === mapping.id}
                                onEdit={(m) => setEditingId(m.id)}
                                onDelete={handleDelete}
                                onSave={handleSave}
                                onCancel={() => setEditingId(null)}
                            />
                        ))}
                    </tbody>
                </table>

                {/* Empty state */}
                {filteredMappings.length === 0 && !showAddNew && !loading && (
                    <div className="text-center py-12 text-slate-500">
                        <Link2 size={32} className="mx-auto mb-3 opacity-50" />
                        <p>No mappings found for {ENTITY_TYPES.find(t => t.id === activeTab)?.label}</p>
                        <button
                            onClick={() => setShowAddNew(true)}
                            className="mt-3 text-blue-400 hover:text-blue-300 text-sm"
                        >
                            Add your first mapping
                        </button>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
                {mappings.length} mappings • {mappings.filter(m => m.validated).length} validated
            </div>
        </div>
    );
};

export default ExternalIdMappingUI;
