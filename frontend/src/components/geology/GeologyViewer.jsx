/**
 * GeologyViewer.jsx - Block Model & Geology Visualization
 * 
 * Provides:
 * - Block model data browser
 * - Quality grade visualization by color
 * - Block filtering and search
 * - Statistics summary by material type
 * - Block selection for scheduling
 */

import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
    Layers, Filter, Search, RefreshCw, ChevronDown, ChevronRight,
    Box, Eye, EyeOff, Download, Upload, Info, MapPin
} from 'lucide-react';

// Color scales for quality visualization
const QUALITY_COLORS = {
    CV: [
        { min: 0, max: 18, color: '#ef4444', label: 'Low' },      // Red
        { min: 18, max: 22, color: '#f59e0b', label: 'Medium' },  // Amber
        { min: 22, max: 26, color: '#22c55e', label: 'Good' },    // Green
        { min: 26, max: 100, color: '#3b82f6', label: 'High' },   // Blue
    ],
    Ash: [
        { min: 0, max: 10, color: '#3b82f6', label: 'Low' },
        { min: 10, max: 14, color: '#22c55e', label: 'Medium' },
        { min: 14, max: 20, color: '#f59e0b', label: 'High' },
        { min: 20, max: 100, color: '#ef4444', label: 'Very High' },
    ]
};

// Block Row Component
const BlockRow = ({ block, selected, onSelect, colorBy }) => {
    const getQualityColor = () => {
        const value = block[colorBy] || 0;
        const scale = QUALITY_COLORS[colorBy] || QUALITY_COLORS.CV;
        for (const range of scale) {
            if (value >= range.min && value < range.max) {
                return range.color;
            }
        }
        return '#6b7280';
    };

    return (
        <tr
            className={`border-b border-slate-700 hover:bg-slate-800/50 cursor-pointer ${selected ? 'bg-blue-900/30' : ''
                }`}
            onClick={() => onSelect(block)}
        >
            <td className="p-2">
                <div className="flex items-center gap-2">
                    <div
                        className="w-3 h-3 rounded-sm"
                        style={{ backgroundColor: getQualityColor() }}
                    />
                    <span className="text-white font-medium">{block.name || block.id}</span>
                </div>
            </td>
            <td className="p-2 text-slate-300">{block.material_type}</td>
            <td className="p-2 text-right text-white">{block.tonnes?.toLocaleString() || 0}</td>
            <td className="p-2 text-right text-slate-300">{block.CV?.toFixed(1) || '-'}</td>
            <td className="p-2 text-right text-slate-300">{block.Ash?.toFixed(1) || '-'}%</td>
            <td className="p-2 text-right text-slate-300">{block.Moisture?.toFixed(1) || '-'}%</td>
            <td className="p-2">
                <span className={`px-2 py-0.5 text-xs rounded-full ${block.status === 'Available' ? 'bg-green-900/50 text-green-400' :
                        block.status === 'Scheduled' ? 'bg-blue-900/50 text-blue-400' :
                            block.status === 'Mined' ? 'bg-slate-700 text-slate-400' :
                                'bg-amber-900/50 text-amber-400'
                    }`}>
                    {block.status || 'Available'}
                </span>
            </td>
        </tr>
    );
};

// Filter Panel Component
const FilterPanel = ({ filters, onFilterChange, materialTypes = [] }) => {
    return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Filter size={14} className="text-blue-400" />
                Filters
            </h3>

            <div className="grid grid-cols-5 gap-4">
                {/* Material Type */}
                <div>
                    <label className="text-xs text-slate-400 block mb-1">Material</label>
                    <select
                        value={filters.materialType}
                        onChange={(e) => onFilterChange('materialType', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white"
                    >
                        <option value="">All Materials</option>
                        {materialTypes.map(mt => (
                            <option key={mt} value={mt}>{mt}</option>
                        ))}
                    </select>
                </div>

                {/* Status */}
                <div>
                    <label className="text-xs text-slate-400 block mb-1">Status</label>
                    <select
                        value={filters.status}
                        onChange={(e) => onFilterChange('status', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white"
                    >
                        <option value="">All Statuses</option>
                        <option value="Available">Available</option>
                        <option value="Scheduled">Scheduled</option>
                        <option value="Mined">Mined</option>
                        <option value="Reserved">Reserved</option>
                    </select>
                </div>

                {/* CV Range */}
                <div>
                    <label className="text-xs text-slate-400 block mb-1">CV Min</label>
                    <input
                        type="number"
                        value={filters.cvMin}
                        onChange={(e) => onFilterChange('cvMin', e.target.value)}
                        placeholder="Min CV"
                        className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white"
                    />
                </div>

                {/* Ash Max */}
                <div>
                    <label className="text-xs text-slate-400 block mb-1">Ash Max</label>
                    <input
                        type="number"
                        value={filters.ashMax}
                        onChange={(e) => onFilterChange('ashMax', e.target.value)}
                        placeholder="Max Ash"
                        className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white"
                    />
                </div>

                {/* Min Tonnes */}
                <div>
                    <label className="text-xs text-slate-400 block mb-1">Min Tonnes</label>
                    <input
                        type="number"
                        value={filters.minTonnes}
                        onChange={(e) => onFilterChange('minTonnes', e.target.value)}
                        placeholder="Min Tonnes"
                        className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white"
                    />
                </div>
            </div>
        </div>
    );
};

// Statistics Summary Component
const StatsSummary = ({ blocks }) => {
    const stats = useMemo(() => {
        if (!blocks.length) return null;

        const coal = blocks.filter(b => b.material_type === 'Coal' || b.material_type === 'Thermal Coal');
        const waste = blocks.filter(b => b.material_type === 'Waste' || b.material_type === 'Overburden');

        const totalTonnes = blocks.reduce((sum, b) => sum + (b.tonnes || 0), 0);
        const coalTonnes = coal.reduce((sum, b) => sum + (b.tonnes || 0), 0);
        const wasteTonnes = waste.reduce((sum, b) => sum + (b.tonnes || 0), 0);

        const avgCV = coal.length > 0
            ? coal.reduce((sum, b) => sum + (b.CV || 0), 0) / coal.length
            : 0;
        const avgAsh = coal.length > 0
            ? coal.reduce((sum, b) => sum + (b.Ash || 0), 0) / coal.length
            : 0;

        return {
            totalBlocks: blocks.length,
            totalTonnes,
            coalTonnes,
            wasteTonnes,
            stripRatio: coalTonnes > 0 ? (wasteTonnes / coalTonnes).toFixed(2) : 0,
            avgCV: avgCV.toFixed(1),
            avgAsh: avgAsh.toFixed(1),
            available: blocks.filter(b => b.status === 'Available').length
        };
    }, [blocks]);

    if (!stats) return null;

    return (
        <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                <p className="text-xs text-slate-400 uppercase">Total Blocks</p>
                <p className="text-xl font-bold text-white">{stats.totalBlocks}</p>
                <p className="text-xs text-slate-500">{stats.available} available</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                <p className="text-xs text-slate-400 uppercase">Total Tonnes</p>
                <p className="text-xl font-bold text-white">{(stats.totalTonnes / 1000000).toFixed(2)}M</p>
                <p className="text-xs text-slate-500">Coal: {(stats.coalTonnes / 1000000).toFixed(2)}M</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                <p className="text-xs text-slate-400 uppercase">Strip Ratio</p>
                <p className="text-xl font-bold text-amber-400">{stats.stripRatio}:1</p>
                <p className="text-xs text-slate-500">Waste to Coal</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3">
                <p className="text-xs text-slate-400 uppercase">Avg Quality</p>
                <p className="text-xl font-bold text-green-400">{stats.avgCV} MJ/kg</p>
                <p className="text-xs text-slate-500">Ash: {stats.avgAsh}%</p>
            </div>
        </div>
    );
};

// Main Geology Viewer Component
const GeologyViewer = ({ siteId }) => {
    const [blocks, setBlocks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [colorBy, setColorBy] = useState('CV');
    const [selectedBlock, setSelectedBlock] = useState(null);
    const [filters, setFilters] = useState({
        materialType: '',
        status: '',
        cvMin: '',
        ashMax: '',
        minTonnes: ''
    });

    useEffect(() => {
        if (siteId) {
            fetchBlocks();
        }
    }, [siteId]);

    const fetchBlocks = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/geology/site/${siteId}/blocks`);
            setBlocks(res.data);
        } catch (e) {
            // Sample block model data
            setBlocks([
                { id: 'BLK-001', name: 'Block A-1-1', material_type: 'Thermal Coal', tonnes: 45000, CV: 24.2, Ash: 11.5, Moisture: 8.2, status: 'Available', bench: 'B1', x: 100, y: 200, z: 50 },
                { id: 'BLK-002', name: 'Block A-1-2', material_type: 'Thermal Coal', tonnes: 52000, CV: 23.8, Ash: 12.1, Moisture: 8.5, status: 'Scheduled', bench: 'B1', x: 110, y: 200, z: 50 },
                { id: 'BLK-003', name: 'Block A-2-1', material_type: 'Thermal Coal', tonnes: 38000, CV: 22.5, Ash: 13.8, Moisture: 9.1, status: 'Available', bench: 'B2', x: 100, y: 210, z: 45 },
                { id: 'BLK-004', name: 'Block B-1-1', material_type: 'Overburden', tonnes: 120000, CV: 0, Ash: 85, Moisture: 5, status: 'Available', bench: 'B1', x: 150, y: 200, z: 55 },
                { id: 'BLK-005', name: 'Block B-1-2', material_type: 'Overburden', tonnes: 95000, CV: 0, Ash: 82, Moisture: 4.5, status: 'Mined', bench: 'B1', x: 160, y: 200, z: 55 },
                { id: 'BLK-006', name: 'Block C-1-1', material_type: 'Thermal Coal', tonnes: 61000, CV: 25.1, Ash: 10.2, Moisture: 7.8, status: 'Available', bench: 'B3', x: 100, y: 220, z: 40 },
                { id: 'BLK-007', name: 'Block C-1-2', material_type: 'Thermal Coal', tonnes: 48000, CV: 19.5, Ash: 16.2, Moisture: 10.5, status: 'Reserved', bench: 'B3', x: 110, y: 220, z: 40 },
                { id: 'BLK-008', name: 'Block D-1-1', material_type: 'Overburden', tonnes: 180000, CV: 0, Ash: 88, Moisture: 4.2, status: 'Available', bench: 'B2', x: 150, y: 210, z: 45 },
            ]);
        } finally {
            setLoading(false);
        }
    };

    // Filter and search blocks
    const filteredBlocks = useMemo(() => {
        return blocks.filter(block => {
            // Search query
            if (searchQuery && !block.name?.toLowerCase().includes(searchQuery.toLowerCase())) {
                return false;
            }
            // Filters
            if (filters.materialType && block.material_type !== filters.materialType) return false;
            if (filters.status && block.status !== filters.status) return false;
            if (filters.cvMin && block.CV < parseFloat(filters.cvMin)) return false;
            if (filters.ashMax && block.Ash > parseFloat(filters.ashMax)) return false;
            if (filters.minTonnes && block.tonnes < parseFloat(filters.minTonnes)) return false;

            return true;
        });
    }, [blocks, searchQuery, filters]);

    // Get unique material types
    const materialTypes = useMemo(() => {
        return [...new Set(blocks.map(b => b.material_type))];
    }, [blocks]);

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center text-slate-400">
                <RefreshCw className="animate-spin mr-2" /> Loading block model...
            </div>
        );
    }

    return (
        <div className="h-full bg-slate-900 p-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Layers className="text-purple-400" />
                        Geology & Block Model
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">
                        Browse and filter block model data for scheduling
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    {/* Color By Selector */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">Color by:</span>
                        <select
                            value={colorBy}
                            onChange={(e) => setColorBy(e.target.value)}
                            className="bg-slate-800 border border-slate-600 text-white rounded px-2 py-1 text-sm"
                        >
                            <option value="CV">Calorific Value</option>
                            <option value="Ash">Ash Content</option>
                        </select>
                    </div>

                    <button
                        onClick={fetchBlocks}
                        className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white"
                    >
                        <RefreshCw size={18} />
                    </button>

                    <button className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-700">
                        <Download size={14} /> Export
                    </button>
                </div>
            </div>

            {/* Search Bar */}
            <div className="relative mb-4">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search blocks by name..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-white placeholder-slate-500"
                />
            </div>

            {/* Filters */}
            <FilterPanel
                filters={filters}
                onFilterChange={handleFilterChange}
                materialTypes={materialTypes}
            />

            {/* Statistics */}
            <StatsSummary blocks={filteredBlocks} />

            {/* Block Table */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-900">
                            <tr className="text-slate-400 text-xs uppercase">
                                <th className="text-left p-3">Block</th>
                                <th className="text-left p-3">Material</th>
                                <th className="text-right p-3">Tonnes</th>
                                <th className="text-right p-3">CV (MJ/kg)</th>
                                <th className="text-right p-3">Ash</th>
                                <th className="text-right p-3">Moisture</th>
                                <th className="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredBlocks.map(block => (
                                <BlockRow
                                    key={block.id}
                                    block={block}
                                    selected={selectedBlock?.id === block.id}
                                    onSelect={setSelectedBlock}
                                    colorBy={colorBy}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>

                {filteredBlocks.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                        <Layers size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No blocks match your filters.</p>
                    </div>
                )}
            </div>

            {/* Color Legend */}
            <div className="mt-4 flex items-center gap-6 text-xs">
                <span className="text-slate-400">Quality Scale ({colorBy}):</span>
                {QUALITY_COLORS[colorBy]?.map((range, i) => (
                    <div key={i} className="flex items-center gap-1">
                        <div
                            className="w-3 h-3 rounded-sm"
                            style={{ backgroundColor: range.color }}
                        />
                        <span className="text-slate-300">{range.label}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GeologyViewer;
