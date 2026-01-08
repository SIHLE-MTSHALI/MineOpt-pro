/**
 * QualitySpecs.jsx - Product Quality Specifications Screen
 * 
 * Allows configuration and monitoring of:
 * - Product quality specifications (CV, Ash, Moisture, Sulphur)
 * - Destination requirements and tolerances
 * - Quality compliance tracking
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Target, Plus, Save, Trash2, AlertTriangle, CheckCircle,
    Settings, ArrowRight, Package
} from 'lucide-react';

// Sample quality fields for coal
const QUALITY_FIELDS = [
    { id: 'CV', name: 'Calorific Value', unit: 'MJ/kg', typical: '22-26' },
    { id: 'Ash', name: 'Ash Content', unit: '%', typical: '8-15' },
    { id: 'Moisture', name: 'Total Moisture', unit: '%', typical: '6-12' },
    { id: 'Sulphur', name: 'Sulphur Content', unit: '%', typical: '0.4-1.2' },
    { id: 'Volatiles', name: 'Volatile Matter', unit: '%', typical: '22-35' },
];

// Product Spec Row Component
const ProductSpecRow = ({ spec, onUpdate, onDelete, qualityFields }) => {
    const [editing, setEditing] = useState(false);
    const [localSpec, setLocalSpec] = useState(spec);

    const handleSave = () => {
        onUpdate(localSpec);
        setEditing(false);
    };

    const getComplianceColor = (compliance) => {
        if (compliance >= 95) return 'text-green-400';
        if (compliance >= 80) return 'text-amber-400';
        return 'text-red-400';
    };

    return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-3">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                        <Package size={18} className="text-blue-400" />
                    </div>
                    <div>
                        <h4 className="text-white font-semibold">{spec.name}</h4>
                        <p className="text-xs text-slate-400">{spec.destination || 'Internal Use'}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${getComplianceColor(spec.compliance || 92)}`}>
                        {spec.compliance || 92}% Compliant
                    </span>
                    <button
                        onClick={() => setEditing(!editing)}
                        className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white"
                    >
                        <Settings size={16} />
                    </button>
                    <button
                        onClick={() => onDelete(spec.id)}
                        className="p-1.5 hover:bg-red-900/50 rounded text-slate-400 hover:text-red-400"
                    >
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>

            {/* Quality Limits */}
            <div className="grid grid-cols-5 gap-2">
                {qualityFields.map(field => {
                    const limit = spec.limits?.[field.id] || {};
                    const currentValue = spec.currentValues?.[field.id] || null;
                    const inSpec = currentValue !== null &&
                        (!limit.min || currentValue >= limit.min) &&
                        (!limit.max || currentValue <= limit.max);

                    return (
                        <div key={field.id} className="bg-slate-900 rounded p-2">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-slate-400">{field.id}</span>
                                {currentValue !== null && (
                                    inSpec
                                        ? <CheckCircle size={12} className="text-green-400" />
                                        : <AlertTriangle size={12} className="text-amber-400" />
                                )}
                            </div>
                            {editing ? (
                                <div className="flex gap-1">
                                    <input
                                        type="number"
                                        value={limit.min || ''}
                                        onChange={(e) => setLocalSpec({
                                            ...localSpec,
                                            limits: {
                                                ...localSpec.limits,
                                                [field.id]: { ...limit, min: parseFloat(e.target.value) || undefined }
                                            }
                                        })}
                                        placeholder="Min"
                                        className="w-12 text-xs bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-white"
                                    />
                                    <span className="text-slate-500">-</span>
                                    <input
                                        type="number"
                                        value={limit.max || ''}
                                        onChange={(e) => setLocalSpec({
                                            ...localSpec,
                                            limits: {
                                                ...localSpec.limits,
                                                [field.id]: { ...limit, max: parseFloat(e.target.value) || undefined }
                                            }
                                        })}
                                        placeholder="Max"
                                        className="w-12 text-xs bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-white"
                                    />
                                </div>
                            ) : (
                                <div className="text-sm text-white font-medium">
                                    {limit.min !== undefined && limit.max !== undefined
                                        ? `${limit.min}-${limit.max}`
                                        : limit.min !== undefined
                                            ? `≥${limit.min}`
                                            : limit.max !== undefined
                                                ? `≤${limit.max}`
                                                : '-'}
                                    <span className="text-xs text-slate-500 ml-1">{field.unit}</span>
                                </div>
                            )}
                            {currentValue !== null && (
                                <div className="text-xs text-slate-400 mt-1">
                                    Current: <span className="text-white">{currentValue}</span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {editing && (
                <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-slate-700">
                    <button
                        onClick={() => setEditing(false)}
                        className="px-3 py-1.5 text-sm text-slate-400 hover:text-white"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-500 flex items-center gap-1"
                    >
                        <Save size={14} /> Save
                    </button>
                </div>
            )}
        </div>
    );
};

// Main Quality Specs Component
const QualitySpecs = ({ siteId }) => {
    const [specs, setSpecs] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (siteId) {
            fetchSpecs();
        }
    }, [siteId]);

    const fetchSpecs = async () => {
        setLoading(true);
        try {
            // Try to fetch from API, fall back to mock data
            const res = await axios.get(`http://localhost:8000/quality/site/${siteId}/specs`);
            // API returns { specs: [...] } or an array directly
            const data = res.data?.specs || res.data || [];
            setSpecs(Array.isArray(data) ? data : []);
        } catch (e) {
            // Use sample data if API not available
            setSpecs([
                {
                    id: 'spec-1',
                    name: 'Export Grade A',
                    destination: 'Port Terminal',
                    compliance: 94,
                    limits: {
                        CV: { min: 23, max: 26 },
                        Ash: { max: 12 },
                        Moisture: { max: 10 },
                        Sulphur: { max: 0.8 },
                    },
                    currentValues: {
                        CV: 24.2,
                        Ash: 11.5,
                        Moisture: 8.3,
                        Sulphur: 0.65,
                    }
                },
                {
                    id: 'spec-2',
                    name: 'Domestic Power',
                    destination: 'Power Station',
                    compliance: 98,
                    limits: {
                        CV: { min: 20, max: 24 },
                        Ash: { max: 15 },
                        Moisture: { max: 12 },
                    },
                    currentValues: {
                        CV: 22.1,
                        Ash: 13.2,
                        Moisture: 9.8,
                    }
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleAddSpec = () => {
        const newSpec = {
            id: `spec-${Date.now()}`,
            name: 'New Product Spec',
            destination: '',
            compliance: 100,
            limits: {},
            currentValues: {},
        };
        setSpecs([...specs, newSpec]);
    };

    const handleUpdateSpec = (updatedSpec) => {
        setSpecs(specs.map(s => s.id === updatedSpec.id ? updatedSpec : s));
    };

    const handleDeleteSpec = (specId) => {
        setSpecs(specs.filter(s => s.id !== specId));
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400">
                Loading specifications...
            </div>
        );
    }

    return (
        <div className="h-full bg-slate-900 p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Target className="text-blue-400" />
                        Product Quality Specifications
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">
                        Configure quality requirements for each product destination
                    </p>
                </div>
                <button
                    onClick={handleAddSpec}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 flex items-center gap-2 font-medium"
                >
                    <Plus size={18} /> Add Product Spec
                </button>
            </div>

            {/* Quality Fields Legend */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Quality Parameters</h3>
                <div className="flex flex-wrap gap-4">
                    {QUALITY_FIELDS.map(field => (
                        <div key={field.id} className="flex items-center gap-2 text-sm">
                            <span className="font-medium text-white">{field.id}</span>
                            <span className="text-slate-400">({field.name})</span>
                            <span className="text-slate-500">Typical: {field.typical} {field.unit}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Product Specs List */}
            <div>
                {specs.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                        <Target size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No product specifications defined.</p>
                        <p className="text-sm">Click "Add Product Spec" to create one.</p>
                    </div>
                ) : (
                    specs.map(spec => (
                        <ProductSpecRow
                            key={spec.id}
                            spec={spec}
                            qualityFields={QUALITY_FIELDS}
                            onUpdate={handleUpdateSpec}
                            onDelete={handleDeleteSpec}
                        />
                    ))
                )}
            </div>

            {/* Blending Suggestion */}
            {specs.length > 0 && (
                <div className="mt-6 bg-gradient-to-r from-purple-900/30 to-slate-800 border border-purple-700/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg">
                            <ArrowRight size={18} className="text-purple-400" />
                        </div>
                        <div>
                            <h4 className="text-white font-medium">Blending Optimization Available</h4>
                            <p className="text-sm text-slate-400 mt-1">
                                The scheduler can automatically optimize material blending to meet all quality specifications while maximizing throughput.
                            </p>
                            <button className="mt-3 text-sm text-purple-400 hover:text-purple-300 font-medium">
                                Configure Auto-Blend →
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QualitySpecs;
