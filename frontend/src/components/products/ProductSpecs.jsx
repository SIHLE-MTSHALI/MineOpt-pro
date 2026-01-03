/**
 * ProductSpecs.jsx - Product & Quality Specifications Screen
 * 
 * Manage product definitions and quality constraints:
 * - Product definition forms
 * - Demand schedule input (tonnes/period)
 * - Quality constraint configuration
 * - Penalty curve visualization
 */

import React, { useState, useEffect } from 'react';
import {
    Package, Plus, Trash2, Save, AlertCircle, CheckCircle,
    Target, TrendingUp, TrendingDown, BarChart2, Edit2
} from 'lucide-react';

// Quality Field Types
const QUALITY_FIELDS = [
    { key: 'CV_ARB', name: 'CV (ARB)', unit: 'MJ/kg', typical: { min: 18, max: 26 } },
    { key: 'Ash_ADB', name: 'Ash (ADB)', unit: '%', typical: { min: 8, max: 20 } },
    { key: 'Moisture_AR', name: 'Moisture (AR)', unit: '%', typical: { min: 5, max: 15 } },
    { key: 'Sulphur_ADB', name: 'Sulphur (ADB)', unit: '%', typical: { min: 0.3, max: 1.5 } },
    { key: 'VM_ADB', name: 'Volatile Matter', unit: '%', typical: { min: 20, max: 35 } },
    { key: 'HGI', name: 'HGI', unit: '', typical: { min: 40, max: 80 } }
];

// Penalty Curve Types
const PENALTY_TYPES = ['Linear', 'Quadratic', 'Step', 'Exponential'];

// Product Card Component
const ProductCard = ({ product, selected, onSelect, onDelete }) => {
    return (
        <div
            className={`p-4 rounded-lg border cursor-pointer transition-all ${selected
                    ? 'bg-slate-800 border-blue-500'
                    : 'bg-slate-900 border-slate-700 hover:border-slate-600'
                }`}
            onClick={onSelect}
        >
            <div className="flex justify-between items-start">
                <div className="flex items-center space-x-3">
                    <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: product.color || '#3b82f6' }}
                    >
                        <Package size={20} className="text-white" />
                    </div>
                    <div>
                        <h3 className="text-white font-medium">{product.name}</h3>
                        <p className="text-slate-400 text-sm">{product.code}</p>
                    </div>
                </div>
                <button
                    onClick={(e) => { e.stopPropagation(); onDelete(product.id); }}
                    className="text-slate-500 hover:text-red-400"
                >
                    <Trash2 size={16} />
                </button>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-800/50 rounded p-2">
                    <span className="text-slate-500">Target</span>
                    <div className="text-white font-medium">{product.targetTonnes?.toLocaleString() || 0} t/m</div>
                </div>
                <div className="bg-slate-800/50 rounded p-2">
                    <span className="text-slate-500">Constraints</span>
                    <div className="text-white font-medium">{product.constraints?.length || 0} specs</div>
                </div>
            </div>
        </div>
    );
};

// Quality Constraint Editor
const ConstraintEditor = ({ constraint, fields, onChange, onDelete }) => {
    const field = fields.find(f => f.key === constraint.field);

    return (
        <div className="bg-slate-800/50 rounded-lg p-3 space-y-3">
            <div className="flex justify-between items-center">
                <select
                    value={constraint.field}
                    onChange={(e) => onChange({ ...constraint, field: e.target.value })}
                    className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                >
                    {fields.map(f => (
                        <option key={f.key} value={f.key}>{f.name}</option>
                    ))}
                </select>
                <button onClick={onDelete} className="text-red-400 hover:text-red-300">
                    <Trash2 size={14} />
                </button>
            </div>

            <div className="grid grid-cols-3 gap-2">
                <div>
                    <label className="text-xs text-slate-500">Type</label>
                    <select
                        value={constraint.type}
                        onChange={(e) => onChange({ ...constraint, type: e.target.value })}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                    >
                        <option value="Max">Max</option>
                        <option value="Min">Min</option>
                        <option value="Range">Range</option>
                        <option value="Target">Target</option>
                    </select>
                </div>

                {(constraint.type === 'Max' || constraint.type === 'Target') && (
                    <div>
                        <label className="text-xs text-slate-500">{constraint.type} Value</label>
                        <input
                            type="number"
                            value={constraint.maxValue || ''}
                            onChange={(e) => onChange({ ...constraint, maxValue: parseFloat(e.target.value) })}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                            placeholder={field?.unit || ''}
                        />
                    </div>
                )}

                {(constraint.type === 'Min' || constraint.type === 'Range') && (
                    <div>
                        <label className="text-xs text-slate-500">Min Value</label>
                        <input
                            type="number"
                            value={constraint.minValue || ''}
                            onChange={(e) => onChange({ ...constraint, minValue: parseFloat(e.target.value) })}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        />
                    </div>
                )}

                {constraint.type === 'Range' && (
                    <div>
                        <label className="text-xs text-slate-500">Max Value</label>
                        <input
                            type="number"
                            value={constraint.maxValue || ''}
                            onChange={(e) => onChange({ ...constraint, maxValue: parseFloat(e.target.value) })}
                            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                        />
                    </div>
                )}
            </div>

            <div className="grid grid-cols-2 gap-2">
                <div>
                    <label className="text-xs text-slate-500">Penalty Type</label>
                    <select
                        value={constraint.penaltyType || 'Linear'}
                        onChange={(e) => onChange({ ...constraint, penaltyType: e.target.value })}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                    >
                        {PENALTY_TYPES.map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="text-xs text-slate-500">Penalty $/unit</label>
                    <input
                        type="number"
                        value={constraint.penaltyRate || ''}
                        onChange={(e) => onChange({ ...constraint, penaltyRate: parseFloat(e.target.value) })}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white mt-1"
                    />
                </div>
            </div>

            <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2 text-sm text-slate-400">
                    <input
                        type="checkbox"
                        checked={constraint.isHard || false}
                        onChange={(e) => onChange({ ...constraint, isHard: e.target.checked })}
                        className="rounded bg-slate-700 border-slate-600"
                    />
                    <span>Hard Constraint (blocking)</span>
                </label>
            </div>
        </div>
    );
};

// Demand Schedule Editor
const DemandSchedule = ({ periods, demand, onChange }) => {
    return (
        <div className="space-y-2">
            <h4 className="text-sm font-medium text-slate-300">Demand Schedule</h4>
            <div className="bg-slate-800/50 rounded-lg p-3 max-h-48 overflow-y-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-slate-500 text-xs">
                            <th className="text-left py-1">Period</th>
                            <th className="text-right py-1">Target (t)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {periods.map(period => (
                            <tr key={period.id} className="border-t border-slate-700">
                                <td className="py-2 text-slate-300">{period.label}</td>
                                <td className="py-2">
                                    <input
                                        type="number"
                                        value={demand[period.id] || ''}
                                        onChange={(e) => onChange({ ...demand, [period.id]: parseFloat(e.target.value) || 0 })}
                                        className="w-24 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white text-right"
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// Main Product Specs Component
const ProductSpecs = () => {
    const [products, setProducts] = useState([
        {
            id: 'prod-1',
            name: 'Prime Export Coal',
            code: 'PEC-01',
            color: '#3b82f6',
            targetTonnes: 500000,
            constraints: [
                { id: 'c1', field: 'CV_ARB', type: 'Min', minValue: 22, penaltyType: 'Linear', penaltyRate: 5 },
                { id: 'c2', field: 'Ash_ADB', type: 'Max', maxValue: 14, penaltyType: 'Linear', penaltyRate: 3, isHard: true }
            ],
            demand: {}
        },
        {
            id: 'prod-2',
            name: 'Secondary Grade',
            code: 'SEC-02',
            color: '#10b981',
            targetTonnes: 200000,
            constraints: [
                { id: 'c3', field: 'CV_ARB', type: 'Min', minValue: 18, penaltyType: 'Linear', penaltyRate: 2 }
            ],
            demand: {}
        }
    ]);

    const [selectedProduct, setSelectedProduct] = useState('prod-1');
    const [periods] = useState([
        { id: 'p1', label: 'Week 1' },
        { id: 'p2', label: 'Week 2' },
        { id: 'p3', label: 'Week 3' },
        { id: 'p4', label: 'Week 4' }
    ]);

    const currentProduct = products.find(p => p.id === selectedProduct);

    const handleAddProduct = () => {
        const newProduct = {
            id: `prod-${Date.now()}`,
            name: 'New Product',
            code: `NEW-${products.length + 1}`,
            color: '#8b5cf6',
            targetTonnes: 0,
            constraints: [],
            demand: {}
        };
        setProducts([...products, newProduct]);
        setSelectedProduct(newProduct.id);
    };

    const handleDeleteProduct = (id) => {
        setProducts(products.filter(p => p.id !== id));
        if (selectedProduct === id && products.length > 1) {
            setSelectedProduct(products.find(p => p.id !== id)?.id);
        }
    };

    const handleUpdateProduct = (field, value) => {
        setProducts(products.map(p =>
            p.id === selectedProduct ? { ...p, [field]: value } : p
        ));
    };

    const handleAddConstraint = () => {
        if (!currentProduct) return;
        const newConstraint = {
            id: `c-${Date.now()}`,
            field: 'CV_ARB',
            type: 'Max',
            maxValue: 0,
            penaltyType: 'Linear',
            penaltyRate: 1
        };
        handleUpdateProduct('constraints', [...currentProduct.constraints, newConstraint]);
    };

    const handleUpdateConstraint = (constraintId, updates) => {
        if (!currentProduct) return;
        const updatedConstraints = currentProduct.constraints.map(c =>
            c.id === constraintId ? updates : c
        );
        handleUpdateProduct('constraints', updatedConstraints);
    };

    const handleDeleteConstraint = (constraintId) => {
        if (!currentProduct) return;
        handleUpdateProduct('constraints', currentProduct.constraints.filter(c => c.id !== constraintId));
    };

    const handleSave = () => {
        console.log('Saving products:', products);
        // API call would go here
    };

    return (
        <div className="h-full flex bg-slate-950">
            {/* Product List */}
            <div className="w-80 border-r border-slate-800 p-4 flex flex-col">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold text-white">Products</h2>
                    <button
                        onClick={handleAddProduct}
                        className="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white"
                    >
                        <Plus size={18} />
                    </button>
                </div>

                <div className="flex-1 space-y-3 overflow-y-auto">
                    {products.map(product => (
                        <ProductCard
                            key={product.id}
                            product={product}
                            selected={selectedProduct === product.id}
                            onSelect={() => setSelectedProduct(product.id)}
                            onDelete={handleDeleteProduct}
                        />
                    ))}
                </div>
            </div>

            {/* Product Details */}
            <div className="flex-1 p-6 overflow-y-auto">
                {currentProduct ? (
                    <div className="max-w-3xl space-y-6">
                        {/* Header */}
                        <div className="flex justify-between items-start">
                            <div>
                                <input
                                    type="text"
                                    value={currentProduct.name}
                                    onChange={(e) => handleUpdateProduct('name', e.target.value)}
                                    className="text-2xl font-bold text-white bg-transparent border-b border-transparent hover:border-slate-600 focus:border-blue-500 outline-none px-1"
                                />
                                <input
                                    type="text"
                                    value={currentProduct.code}
                                    onChange={(e) => handleUpdateProduct('code', e.target.value)}
                                    className="block mt-1 text-slate-400 bg-transparent border-b border-transparent hover:border-slate-600 focus:border-blue-500 outline-none px-1"
                                />
                            </div>
                            <button
                                onClick={handleSave}
                                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-white"
                            >
                                <Save size={18} />
                                <span>Save</span>
                            </button>
                        </div>

                        {/* Basic Info */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                                <label className="text-sm text-slate-400">Monthly Target (tonnes)</label>
                                <input
                                    type="number"
                                    value={currentProduct.targetTonnes || ''}
                                    onChange={(e) => handleUpdateProduct('targetTonnes', parseFloat(e.target.value) || 0)}
                                    className="w-full mt-2 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white"
                                />
                            </div>
                            <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                                <label className="text-sm text-slate-400">Product Color</label>
                                <input
                                    type="color"
                                    value={currentProduct.color}
                                    onChange={(e) => handleUpdateProduct('color', e.target.value)}
                                    className="w-full mt-2 h-10 rounded cursor-pointer"
                                />
                            </div>
                        </div>

                        {/* Quality Constraints */}
                        <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-medium text-white">Quality Constraints</h3>
                                <button
                                    onClick={handleAddConstraint}
                                    className="flex items-center space-x-1 px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300"
                                >
                                    <Plus size={14} />
                                    <span>Add Constraint</span>
                                </button>
                            </div>

                            <div className="space-y-3">
                                {currentProduct.constraints.map(constraint => (
                                    <ConstraintEditor
                                        key={constraint.id}
                                        constraint={constraint}
                                        fields={QUALITY_FIELDS}
                                        onChange={(updated) => handleUpdateConstraint(constraint.id, updated)}
                                        onDelete={() => handleDeleteConstraint(constraint.id)}
                                    />
                                ))}

                                {currentProduct.constraints.length === 0 && (
                                    <div className="text-center py-8 text-slate-500">
                                        No quality constraints defined
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Demand Schedule */}
                        <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                            <DemandSchedule
                                periods={periods}
                                demand={currentProduct.demand}
                                onChange={(demand) => handleUpdateProduct('demand', demand)}
                            />
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center justify-center h-full text-slate-500">
                        Select a product or create a new one
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProductSpecs;
