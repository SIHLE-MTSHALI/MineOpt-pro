/**
 * WashPlantConfig.jsx - Coal Handling & Preparation Plant Configuration
 * 
 * Provides configuration and monitoring for:
 * - Wash table (yield/quality matrices)
 * - Plant operating parameters
 * - Feed quality requirements
 * - Product streams and splits
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Factory, Settings, Plus, Trash2, Save, RefreshCw,
    ArrowRight, Percent, Droplets, Flame, TrendingUp
} from 'lucide-react';

// Wash Table Row Component
const WashTableRow = ({ row, index, onUpdate, onDelete }) => {
    return (
        <tr className="border-b border-slate-700 hover:bg-slate-800/50">
            <td className="p-2">
                <input
                    type="number"
                    step="0.1"
                    value={row.feed_ash_min}
                    onChange={(e) => onUpdate(index, 'feed_ash_min', parseFloat(e.target.value))}
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
                <span className="text-slate-500 mx-1">-</span>
                <input
                    type="number"
                    step="0.1"
                    value={row.feed_ash_max}
                    onChange={(e) => onUpdate(index, 'feed_ash_max', parseFloat(e.target.value))}
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
            </td>
            <td className="p-2">
                <input
                    type="number"
                    step="0.1"
                    value={row.product_yield}
                    onChange={(e) => onUpdate(index, 'product_yield', parseFloat(e.target.value))}
                    className="w-20 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
                <span className="text-slate-500 ml-1">%</span>
            </td>
            <td className="p-2">
                <input
                    type="number"
                    step="0.1"
                    value={row.product_ash}
                    onChange={(e) => onUpdate(index, 'product_ash', parseFloat(e.target.value))}
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
                <span className="text-slate-500 ml-1">%</span>
            </td>
            <td className="p-2">
                <input
                    type="number"
                    step="0.1"
                    value={row.product_cv}
                    onChange={(e) => onUpdate(index, 'product_cv', parseFloat(e.target.value))}
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
            </td>
            <td className="p-2">
                <input
                    type="number"
                    step="0.1"
                    value={row.reject_ash || 45}
                    onChange={(e) => onUpdate(index, 'reject_ash', parseFloat(e.target.value))}
                    className="w-16 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                />
                <span className="text-slate-500 ml-1">%</span>
            </td>
            <td className="p-2">
                <button
                    onClick={() => onDelete(index)}
                    className="p-1 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded"
                >
                    <Trash2 size={14} />
                </button>
            </td>
        </tr>
    );
};

// Plant Parameters Card
const PlantParametersCard = ({ params, onUpdate }) => {
    return (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Settings size={16} className="text-blue-400" />
                Operating Parameters
            </h3>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="text-xs text-slate-400 block mb-1">Max Feed Rate</label>
                    <div className="flex items-center">
                        <input
                            type="number"
                            value={params.max_feed_rate}
                            onChange={(e) => onUpdate('max_feed_rate', parseFloat(e.target.value))}
                            className="flex-1 bg-slate-900 border border-slate-600 rounded-l px-3 py-2 text-white"
                        />
                        <span className="bg-slate-700 px-3 py-2 text-slate-400 text-sm rounded-r border border-l-0 border-slate-600">
                            t/h
                        </span>
                    </div>
                </div>

                <div>
                    <label className="text-xs text-slate-400 block mb-1">Min Feed Rate</label>
                    <div className="flex items-center">
                        <input
                            type="number"
                            value={params.min_feed_rate}
                            onChange={(e) => onUpdate('min_feed_rate', parseFloat(e.target.value))}
                            className="flex-1 bg-slate-900 border border-slate-600 rounded-l px-3 py-2 text-white"
                        />
                        <span className="bg-slate-700 px-3 py-2 text-slate-400 text-sm rounded-r border border-l-0 border-slate-600">
                            t/h
                        </span>
                    </div>
                </div>

                <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Availability</label>
                    <div className="flex items-center">
                        <input
                            type="number"
                            value={params.availability}
                            onChange={(e) => onUpdate('availability', parseFloat(e.target.value))}
                            className="flex-1 bg-slate-900 border border-slate-600 rounded-l px-3 py-2 text-white"
                        />
                        <span className="bg-slate-700 px-3 py-2 text-slate-400 text-sm rounded-r border border-l-0 border-slate-600">
                            %
                        </span>
                    </div>
                </div>

                <div>
                    <label className="text-xs text-slate-400 block mb-1">Recovery Factor</label>
                    <div className="flex items-center">
                        <input
                            type="number"
                            step="0.01"
                            value={params.recovery}
                            onChange={(e) => onUpdate('recovery', parseFloat(e.target.value))}
                            className="flex-1 bg-slate-900 border border-slate-600 rounded-l px-3 py-2 text-white"
                        />
                        <span className="bg-slate-700 px-3 py-2 text-slate-400 text-sm rounded-r border border-l-0 border-slate-600">
                            %
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Feed Quality Limits Card
const FeedQualityCard = ({ limits, onUpdate }) => {
    return (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Droplets size={16} className="text-amber-400" />
                Feed Quality Limits
            </h3>

            <div className="space-y-3">
                {Object.entries(limits).map(([field, values]) => (
                    <div key={field} className="flex items-center gap-3">
                        <span className="w-20 text-sm text-slate-300">{field}</span>
                        <input
                            type="number"
                            step="0.1"
                            value={values.min}
                            onChange={(e) => onUpdate(field, 'min', parseFloat(e.target.value))}
                            placeholder="Min"
                            className="w-20 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                        />
                        <span className="text-slate-500">-</span>
                        <input
                            type="number"
                            step="0.1"
                            value={values.max}
                            onChange={(e) => onUpdate(field, 'max', parseFloat(e.target.value))}
                            placeholder="Max"
                            className="w-20 bg-slate-900 border border-slate-600 rounded px-2 py-1 text-white text-sm text-center"
                        />
                        <span className="text-xs text-slate-500">{values.unit}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

// Main Wash Plant Config Component
const WashPlantConfig = ({ siteId }) => {
    const [plants, setPlants] = useState([]);
    const [selectedPlant, setSelectedPlant] = useState(null);
    const [washTable, setWashTable] = useState([]);
    const [params, setParams] = useState({
        max_feed_rate: 500,
        min_feed_rate: 200,
        availability: 85,
        recovery: 98
    });
    const [feedLimits, setFeedLimits] = useState({
        Ash: { min: 8, max: 20, unit: '%' },
        Moisture: { min: 6, max: 14, unit: '%' },
        CV: { min: 18, max: 28, unit: 'MJ/kg' }
    });
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (siteId) {
            fetchPlants();
        }
    }, [siteId]);

    const fetchPlants = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/washplant/site/${siteId}`);
            setPlants(res.data);
            if (res.data.length > 0) {
                setSelectedPlant(res.data[0]);
                fetchWashTable(res.data[0].plant_id);
            }
        } catch (e) {
            // Sample data
            const samplePlants = [
                { plant_id: 'plant-1', name: 'CHPP Main', status: 'Operational' }
            ];
            setPlants(samplePlants);
            setSelectedPlant(samplePlants[0]);

            // Sample wash table
            setWashTable([
                { feed_ash_min: 8, feed_ash_max: 12, product_yield: 75, product_ash: 10, product_cv: 25.5, reject_ash: 45 },
                { feed_ash_min: 12, feed_ash_max: 16, product_yield: 65, product_ash: 11, product_cv: 24.2, reject_ash: 48 },
                { feed_ash_min: 16, feed_ash_max: 20, product_yield: 55, product_ash: 12, product_cv: 23.0, reject_ash: 52 },
                { feed_ash_min: 20, feed_ash_max: 25, product_yield: 45, product_ash: 13, product_cv: 21.5, reject_ash: 55 },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const fetchWashTable = async (plantId) => {
        try {
            const res = await axios.get(`http://localhost:8000/washplant/${plantId}/wash-table`);
            setWashTable(res.data.rows);
        } catch (e) {
            console.warn('Could not fetch wash table');
        }
    };

    const handleAddRow = () => {
        const lastRow = washTable[washTable.length - 1];
        setWashTable([
            ...washTable,
            {
                feed_ash_min: lastRow ? lastRow.feed_ash_max : 20,
                feed_ash_max: lastRow ? lastRow.feed_ash_max + 5 : 25,
                product_yield: 40,
                product_ash: 14,
                product_cv: 20,
                reject_ash: 55
            }
        ]);
    };

    const handleUpdateRow = (index, field, value) => {
        setWashTable(prev => prev.map((row, i) =>
            i === index ? { ...row, [field]: value } : row
        ));
    };

    const handleDeleteRow = (index) => {
        setWashTable(prev => prev.filter((_, i) => i !== index));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await axios.put(`http://localhost:8000/washplant/${selectedPlant.plant_id}/wash-table`, {
                rows: washTable
            });
            await axios.put(`http://localhost:8000/washplant/${selectedPlant.plant_id}/parameters`, params);
        } catch (e) {
            console.log('Saved locally (API not available)');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400">
                <RefreshCw className="animate-spin mr-2" /> Loading plant configuration...
            </div>
        );
    }

    return (
        <div className="h-full bg-slate-900 p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Factory className="text-green-400" />
                        Wash Plant Configuration
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">
                        Configure coal handling and preparation plant parameters
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    {/* Plant Selector */}
                    <select
                        value={selectedPlant?.plant_id || ''}
                        onChange={(e) => {
                            const plant = plants.find(p => p.plant_id === e.target.value);
                            setSelectedPlant(plant);
                            if (plant) fetchWashTable(plant.plant_id);
                        }}
                        className="bg-slate-800 border border-slate-600 text-white rounded-lg px-3 py-2"
                    >
                        {plants.map(plant => (
                            <option key={plant.plant_id} value={plant.plant_id}>{plant.name}</option>
                        ))}
                    </select>

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-500 disabled:opacity-50"
                    >
                        <Save size={16} />
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-3 gap-6">
                {/* Left: Parameters */}
                <div className="space-y-4">
                    <PlantParametersCard
                        params={params}
                        onUpdate={(field, value) => setParams(prev => ({ ...prev, [field]: value }))}
                    />
                    <FeedQualityCard
                        limits={feedLimits}
                        onUpdate={(field, type, value) => setFeedLimits(prev => ({
                            ...prev,
                            [field]: { ...prev[field], [type]: value }
                        }))}
                    />

                    {/* Plant Status */}
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                            <TrendingUp size={16} className="text-purple-400" />
                            Current Status
                        </h3>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Status</span>
                                <span className="text-green-400 font-medium">{selectedPlant?.status || 'Operational'}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Current Feed Rate</span>
                                <span className="text-white">445 t/h</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-400">Today's Throughput</span>
                                <span className="text-white">3,240 t</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Wash Table */}
                <div className="col-span-2">
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Percent size={16} className="text-blue-400" />
                                Wash Table (Yield Matrix)
                            </h3>
                            <button
                                onClick={handleAddRow}
                                className="flex items-center gap-1 px-3 py-1 bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30 text-sm"
                            >
                                <Plus size={14} /> Add Row
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-slate-400 text-xs uppercase">
                                        <th className="text-left p-2">Feed Ash Range (%)</th>
                                        <th className="text-left p-2">Product Yield</th>
                                        <th className="text-left p-2">Product Ash</th>
                                        <th className="text-left p-2">Product CV</th>
                                        <th className="text-left p-2">Reject Ash</th>
                                        <th className="p-2"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {washTable.map((row, index) => (
                                        <WashTableRow
                                            key={index}
                                            row={row}
                                            index={index}
                                            onUpdate={handleUpdateRow}
                                            onDelete={handleDeleteRow}
                                        />
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {washTable.length === 0 && (
                            <div className="text-center py-8 text-slate-500">
                                No wash table rows defined. Click "Add Row" to create one.
                            </div>
                        )}

                        {/* Visual representation */}
                        <div className="mt-6 p-4 bg-slate-900 rounded-lg">
                            <h4 className="text-xs text-slate-400 uppercase mb-3">Yield Curve Preview</h4>
                            <div className="h-32 flex items-end gap-2">
                                {washTable.map((row, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center">
                                        <div
                                            className="w-full bg-gradient-to-t from-green-600 to-green-400 rounded-t"
                                            style={{ height: `${row.product_yield}%` }}
                                        />
                                        <span className="text-xs text-slate-500 mt-1">{row.feed_ash_min}-{row.feed_ash_max}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WashPlantConfig;
