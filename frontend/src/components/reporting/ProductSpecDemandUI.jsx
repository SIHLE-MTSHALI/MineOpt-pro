/**
 * ProductSpecDemandUI.jsx - Product Specification & Demand Schedule
 * 
 * Displays and manages:
 * - Product specifications (quality targets)
 * - Demand schedules by product
 * - Delivery commitments
 */

import React, { useState, useEffect } from 'react';
import {
    Package, Plus, Trash2, Edit3, Save, X, Calendar,
    Target, TrendingUp, AlertTriangle, Check, ChevronDown, ChevronUp
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Quality field definitions
const QUALITY_FIELDS = [
    { id: 'cv', label: 'CV (MJ/kg)', min: 20, max: 30, unit: 'MJ/kg' },
    { id: 'ash', label: 'Ash (%)', min: 0, max: 20, unit: '%' },
    { id: 'moisture', label: 'Moisture (%)', min: 0, max: 15, unit: '%' },
    { id: 'sulphur', label: 'Sulphur (%)', min: 0, max: 2, unit: '%' },
    { id: 'volatiles', label: 'Volatiles (%)', min: 20, max: 40, unit: '%' }
];

// Product card component
const ProductCard = ({ product, onEdit, onDelete, expanded, onToggle }) => {
    const complianceColor = product.compliance_rate >= 95 ? 'emerald' :
        product.compliance_rate >= 80 ? 'amber' : 'red';

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div
                className="p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
                onClick={onToggle}
            >
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br from-${complianceColor}-500/30 to-${complianceColor}-600/30 flex items-center justify-center`}>
                            <Package className={`text-${complianceColor}-400`} size={20} />
                        </div>
                        <div>
                            <h3 className="font-medium text-white">{product.name}</h3>
                            <p className="text-xs text-slate-400">{product.code}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="text-right">
                            <p className={`text-lg font-bold text-${complianceColor}-400`}>
                                {product.compliance_rate}%
                            </p>
                            <p className="text-xs text-slate-500">Compliance</p>
                        </div>
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                </div>
            </div>

            {/* Expanded content */}
            {expanded && (
                <div className="border-t border-slate-700 p-4 space-y-4">
                    {/* Quality Specs */}
                    <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                            <Target size={14} />
                            Quality Specifications
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {product.specs?.map(spec => (
                                <div key={spec.field} className="bg-slate-900/50 rounded-lg p-2">
                                    <p className="text-xs text-slate-500">{spec.label}</p>
                                    <p className="text-sm text-white">
                                        {spec.min_value} - {spec.max_value} {spec.unit}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Demand Schedule */}
                    <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                            <Calendar size={14} />
                            Demand Schedule
                        </h4>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-xs text-slate-500 uppercase">
                                        <th className="text-left py-2">Period</th>
                                        <th className="text-right py-2">Target (t)</th>
                                        <th className="text-right py-2">Committed (t)</th>
                                        <th className="text-right py-2">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {product.demand_schedule?.map(period => (
                                        <tr key={period.period} className="border-t border-slate-700/50">
                                            <td className="py-2 text-slate-300">{period.period}</td>
                                            <td className="py-2 text-right text-slate-300">
                                                {period.target_tonnes.toLocaleString()}
                                            </td>
                                            <td className="py-2 text-right text-blue-400">
                                                {period.committed_tonnes.toLocaleString()}
                                            </td>
                                            <td className="py-2 text-right">
                                                {period.committed_tonnes >= period.target_tonnes ? (
                                                    <span className="text-emerald-400 flex items-center justify-end gap-1">
                                                        <Check size={12} /> Met
                                                    </span>
                                                ) : (
                                                    <span className="text-amber-400 flex items-center justify-end gap-1">
                                                        <AlertTriangle size={12} />
                                                        -{(period.target_tonnes - period.committed_tonnes).toLocaleString()}
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-2 pt-2 border-t border-slate-700">
                        <button
                            onClick={() => onEdit(product)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-slate-300"
                        >
                            <Edit3 size={14} /> Edit
                        </button>
                        <button
                            onClick={() => onDelete(product.id)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-sm text-red-400"
                        >
                            <Trash2 size={14} /> Delete
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

// New product form
const NewProductForm = ({ onSave, onCancel }) => {
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [specs, setSpecs] = useState(
        QUALITY_FIELDS.map(f => ({ field: f.id, label: f.label, unit: f.unit, min_value: f.min, max_value: f.max }))
    );

    const updateSpec = (field, key, value) => {
        setSpecs(specs.map(s => s.field === field ? { ...s, [key]: parseFloat(value) } : s));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({
            name,
            code,
            specs,
            demand_schedule: [],
            compliance_rate: 100
        });
    };

    return (
        <form onSubmit={handleSubmit} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-white">New Product Specification</h3>
                <button type="button" onClick={onCancel} className="p-1 hover:bg-slate-700 rounded">
                    <X size={16} className="text-slate-400" />
                </button>
            </div>

            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs text-slate-400 mb-1">Product Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
                            placeholder="e.g., Export Grade A"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-slate-400 mb-1">Product Code</label>
                        <input
                            type="text"
                            value={code}
                            onChange={(e) => setCode(e.target.value.toUpperCase())}
                            required
                            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white font-mono"
                            placeholder="e.g., EXP-A"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-xs text-slate-400 mb-2">Quality Specifications</label>
                    <div className="space-y-2">
                        {specs.map(spec => (
                            <div key={spec.field} className="grid grid-cols-3 gap-2 items-center">
                                <span className="text-sm text-slate-300">{spec.label}</span>
                                <input
                                    type="number"
                                    value={spec.min_value}
                                    onChange={(e) => updateSpec(spec.field, 'min_value', e.target.value)}
                                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                                    placeholder="Min"
                                    step="0.1"
                                />
                                <input
                                    type="number"
                                    value={spec.max_value}
                                    onChange={(e) => updateSpec(spec.field, 'max_value', e.target.value)}
                                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                                    placeholder="Max"
                                    step="0.1"
                                />
                            </div>
                        ))}
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
                    Create Product
                </button>
            </div>
        </form>
    );
};

const ProductSpecDemandUI = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showNewForm, setShowNewForm] = useState(false);
    const [expandedId, setExpandedId] = useState(null);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE}/products`);
            setProducts(res.data);
        } catch (error) {
            console.error('Failed to fetch products:', error);
            // Demo data
            setProducts([
                {
                    id: '1',
                    name: 'Export Grade A',
                    code: 'EXP-A',
                    compliance_rate: 96,
                    specs: [
                        { field: 'cv', label: 'CV', unit: 'MJ/kg', min_value: 25, max_value: 28 },
                        { field: 'ash', label: 'Ash', unit: '%', min_value: 0, max_value: 12 },
                        { field: 'moisture', label: 'Moisture', unit: '%', min_value: 0, max_value: 10 },
                        { field: 'sulphur', label: 'Sulphur', unit: '%', min_value: 0, max_value: 0.8 }
                    ],
                    demand_schedule: [
                        { period: 'Jan 2026', target_tonnes: 150000, committed_tonnes: 155000 },
                        { period: 'Feb 2026', target_tonnes: 140000, committed_tonnes: 142000 },
                        { period: 'Mar 2026', target_tonnes: 160000, committed_tonnes: 145000 }
                    ]
                },
                {
                    id: '2',
                    name: 'Domestic Blend',
                    code: 'DOM-B',
                    compliance_rate: 88,
                    specs: [
                        { field: 'cv', label: 'CV', unit: 'MJ/kg', min_value: 20, max_value: 24 },
                        { field: 'ash', label: 'Ash', unit: '%', min_value: 0, max_value: 18 },
                        { field: 'moisture', label: 'Moisture', unit: '%', min_value: 0, max_value: 12 }
                    ],
                    demand_schedule: [
                        { period: 'Jan 2026', target_tonnes: 80000, committed_tonnes: 82000 },
                        { period: 'Feb 2026', target_tonnes: 75000, committed_tonnes: 70000 },
                        { period: 'Mar 2026', target_tonnes: 85000, committed_tonnes: 80000 }
                    ]
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (product) => {
        try {
            const res = await axios.post(`${API_BASE}/products`, product);
            setProducts([...products, res.data]);
        } catch (error) {
            console.error('Failed to create product:', error);
            setProducts([...products, { ...product, id: Date.now().toString() }]);
        }
        setShowNewForm(false);
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this product specification?')) return;
        try {
            await axios.delete(`${API_BASE}/products/${id}`);
        } catch (error) {
            console.error('Failed to delete product:', error);
        }
        setProducts(products.filter(p => p.id !== id));
    };

    // Calculate summary stats
    const totalDemand = products.reduce((sum, p) =>
        sum + (p.demand_schedule?.reduce((s, d) => s + d.target_tonnes, 0) || 0), 0
    );
    const totalCommitted = products.reduce((sum, p) =>
        sum + (p.demand_schedule?.reduce((s, d) => s + d.committed_tonnes, 0) || 0), 0
    );
    const avgCompliance = products.length > 0
        ? products.reduce((sum, p) => sum + p.compliance_rate, 0) / products.length
        : 0;

    return (
        <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Package size={20} className="text-orange-400" />
                    <div>
                        <h2 className="text-lg font-semibold text-white">Product Specifications</h2>
                        <p className="text-xs text-slate-400">Quality targets and demand schedules</p>
                    </div>
                </div>
                <button
                    onClick={() => setShowNewForm(true)}
                    className="flex items-center gap-2 px-3 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-sm text-white"
                >
                    <Plus size={14} />
                    New Product
                </button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-slate-800/30">
                <div className="text-center">
                    <p className="text-2xl font-bold text-white">{products.length}</p>
                    <p className="text-xs text-slate-400">Products</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">{(totalCommitted / 1e6).toFixed(1)}M</p>
                    <p className="text-xs text-slate-400">Tonnes Committed</p>
                </div>
                <div className="text-center">
                    <p className={`text-2xl font-bold ${avgCompliance >= 90 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {avgCompliance.toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-400">Avg Compliance</p>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 space-y-3">
                {showNewForm && (
                    <NewProductForm onSave={handleCreate} onCancel={() => setShowNewForm(false)} />
                )}

                {loading ? (
                    <div className="text-center py-12 text-slate-500">Loading products...</div>
                ) : products.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                        <Package size={32} className="mx-auto mb-3 opacity-50" />
                        <p>No products configured</p>
                        <button
                            onClick={() => setShowNewForm(true)}
                            className="mt-3 text-orange-400 hover:text-orange-300 text-sm"
                        >
                            Create your first product
                        </button>
                    </div>
                ) : (
                    products.map(product => (
                        <ProductCard
                            key={product.id}
                            product={product}
                            expanded={expandedId === product.id}
                            onToggle={() => setExpandedId(expandedId === product.id ? null : product.id)}
                            onEdit={() => { }}
                            onDelete={handleDelete}
                        />
                    ))
                )}
            </div>
        </div>
    );
};

export default ProductSpecDemandUI;
