/**
 * BlockPropertiesPanel.jsx - Editable Side Panel for Block Properties
 * 
 * Provides editing controls for activity areas/blocks:
 * - Priority editing
 * - Slice release controls
 * - Destination preferences
 * - Quality display
 * - Status management
 */

import React, { useState, useEffect } from 'react';
import {
    X, ChevronDown, ChevronRight, Edit2, Save,
    Layers, Target, AlertTriangle, CheckCircle,
    Clock, Lock, Unlock, ArrowRight
} from 'lucide-react';

// Priority Slider Component
const PrioritySlider = ({ value, onChange }) => {
    const getColor = (val) => {
        if (val <= 3) return 'bg-green-500';
        if (val <= 6) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="space-y-2">
            <div className="flex justify-between items-center">
                <label className="text-xs text-slate-400">Priority</label>
                <span className={`px-2 py-0.5 rounded text-xs text-white ${getColor(value)}`}>
                    {value <= 3 ? 'Low' : value <= 6 ? 'Medium' : 'High'}
                </span>
            </div>
            <input
                type="range"
                min="1"
                max="10"
                value={value}
                onChange={(e) => onChange(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-slate-500">
                <span>1</span>
                <span>5</span>
                <span>10</span>
            </div>
        </div>
    );
};

// Slice Control Component
const SliceControl = ({ slice, onToggle, onRelease }) => {
    const statusColors = {
        Available: 'bg-green-500/20 text-green-400 border-green-500',
        Scheduled: 'bg-blue-500/20 text-blue-400 border-blue-500',
        InProgress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500',
        Complete: 'bg-slate-500/20 text-slate-400 border-slate-500',
        Locked: 'bg-red-500/20 text-red-400 border-red-500'
    };

    return (
        <div className={`p-3 rounded-lg border ${statusColors[slice.status] || statusColors.Available}`}>
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <Layers size={14} />
                    <span className="text-sm font-medium">{slice.name}</span>
                </div>
                <div className="flex items-center space-x-2">
                    {slice.status === 'Locked' ? (
                        <button onClick={() => onRelease(slice.id)} className="p-1 hover:bg-white/10 rounded">
                            <Unlock size={14} />
                        </button>
                    ) : (
                        <button onClick={() => onToggle(slice.id)} className="p-1 hover:bg-white/10 rounded">
                            <Lock size={14} />
                        </button>
                    )}
                </div>
            </div>

            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                <div className="bg-black/20 rounded px-2 py-1">
                    <span className="text-slate-500">Tonnes: </span>
                    <span>{slice.tonnes?.toLocaleString() || 0}</span>
                </div>
                <div className="bg-black/20 rounded px-2 py-1">
                    <span className="text-slate-500">Status: </span>
                    <span>{slice.status}</span>
                </div>
            </div>
        </div>
    );
};

// Quality Display Card
const QualityCard = ({ qualities }) => {
    if (!qualities || Object.keys(qualities).length === 0) {
        return (
            <div className="text-center py-4 text-slate-500 text-sm">
                No quality data available
            </div>
        );
    }

    const getQualityColor = (field, value) => {
        // Simplified quality status coloring
        if (field.includes('CV')) {
            return value >= 22 ? 'text-green-400' : value >= 18 ? 'text-yellow-400' : 'text-red-400';
        }
        if (field.includes('Ash')) {
            return value <= 12 ? 'text-green-400' : value <= 18 ? 'text-yellow-400' : 'text-red-400';
        }
        return 'text-slate-300';
    };

    return (
        <div className="grid grid-cols-2 gap-2">
            {Object.entries(qualities).map(([field, value]) => (
                <div key={field} className="bg-slate-800/50 rounded p-2">
                    <div className="text-xs text-slate-500">{field}</div>
                    <div className={`text-sm font-medium ${getQualityColor(field, value)}`}>
                        {typeof value === 'number' ? value.toFixed(2) : value}
                    </div>
                </div>
            ))}
        </div>
    );
};

// Destination Selector
const DestinationSelector = ({ destinations, selected, onChange }) => {
    return (
        <div className="space-y-2">
            <label className="text-xs text-slate-400">Preferred Destinations</label>
            <div className="space-y-2">
                {destinations.map(dest => (
                    <label
                        key={dest.id}
                        className="flex items-center space-x-2 p-2 rounded bg-slate-800/50 hover:bg-slate-800 cursor-pointer"
                    >
                        <input
                            type="checkbox"
                            checked={selected.includes(dest.id)}
                            onChange={(e) => {
                                if (e.target.checked) {
                                    onChange([...selected, dest.id]);
                                } else {
                                    onChange(selected.filter(id => id !== dest.id));
                                }
                            }}
                            className="rounded bg-slate-700 border-slate-600"
                        />
                        <Target size={14} className="text-slate-400" />
                        <span className="text-sm text-slate-300">{dest.name}</span>
                    </label>
                ))}
            </div>
        </div>
    );
};

// Main Block Properties Panel
const BlockPropertiesPanel = ({
    block,
    isOpen,
    onClose,
    onUpdate,
    destinations = []
}) => {
    const [editedBlock, setEditedBlock] = useState(null);
    const [expandedSections, setExpandedSections] = useState({
        slices: true,
        quality: true,
        destinations: false
    });

    useEffect(() => {
        if (block) {
            setEditedBlock({ ...block });
        }
    }, [block]);

    if (!isOpen || !editedBlock) return null;

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleSave = () => {
        onUpdate(editedBlock);
    };

    const handleSliceToggle = (sliceId) => {
        setEditedBlock(prev => ({
            ...prev,
            slices: prev.slices?.map(s =>
                s.id === sliceId
                    ? { ...s, status: s.status === 'Locked' ? 'Available' : 'Locked' }
                    : s
            )
        }));
    };

    const handleSliceRelease = (sliceId) => {
        setEditedBlock(prev => ({
            ...prev,
            slices: prev.slices?.map(s =>
                s.id === sliceId ? { ...s, status: 'Available' } : s
            )
        }));
    };

    // Mock destinations if not provided
    const defaultDestinations = destinations.length > 0 ? destinations : [
        { id: 'rom-01', name: 'ROM Stockpile 1' },
        { id: 'rom-02', name: 'ROM Stockpile 2' },
        { id: 'direct', name: 'Direct Feed' },
        { id: 'waste', name: 'Waste Dump' }
    ];

    return (
        <div className="fixed right-0 top-0 h-full w-80 bg-slate-900 border-l border-slate-700 shadow-xl z-50 flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-semibold text-white">{editedBlock.name}</h2>
                    <p className="text-xs text-slate-400">{editedBlock.type || 'Activity Area'}</p>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded text-slate-400">
                    <X size={20} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Priority */}
                <div className="bg-slate-800/50 rounded-lg p-4">
                    <PrioritySlider
                        value={editedBlock.priority || 5}
                        onChange={(val) => setEditedBlock(prev => ({ ...prev, priority: val }))}
                    />
                </div>

                {/* Status Badge */}
                <div className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3">
                    <span className="text-sm text-slate-400">Status</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${editedBlock.status === 'Available' ? 'bg-green-500/20 text-green-400' :
                            editedBlock.status === 'Scheduled' ? 'bg-blue-500/20 text-blue-400' :
                                editedBlock.status === 'InProgress' ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-slate-500/20 text-slate-400'
                        }`}>
                        {editedBlock.status || 'Unknown'}
                    </span>
                </div>

                {/* Slices Section */}
                <div className="bg-slate-800/50 rounded-lg overflow-hidden">
                    <button
                        onClick={() => toggleSection('slices')}
                        className="w-full p-3 flex items-center justify-between hover:bg-slate-800"
                    >
                        <div className="flex items-center space-x-2">
                            <Layers size={16} className="text-slate-400" />
                            <span className="text-sm font-medium text-white">Slices</span>
                            <span className="text-xs text-slate-500">({editedBlock.slices?.length || 0})</span>
                        </div>
                        {expandedSections.slices ?
                            <ChevronDown size={16} className="text-slate-400" /> :
                            <ChevronRight size={16} className="text-slate-400" />
                        }
                    </button>

                    {expandedSections.slices && (
                        <div className="p-3 space-y-2 border-t border-slate-700">
                            {editedBlock.slices?.length > 0 ? (
                                editedBlock.slices.map(slice => (
                                    <SliceControl
                                        key={slice.id}
                                        slice={slice}
                                        onToggle={handleSliceToggle}
                                        onRelease={handleSliceRelease}
                                    />
                                ))
                            ) : (
                                <div className="text-center py-4 text-slate-500 text-sm">
                                    No slices defined
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Quality Section */}
                <div className="bg-slate-800/50 rounded-lg overflow-hidden">
                    <button
                        onClick={() => toggleSection('quality')}
                        className="w-full p-3 flex items-center justify-between hover:bg-slate-800"
                    >
                        <div className="flex items-center space-x-2">
                            <AlertTriangle size={16} className="text-slate-400" />
                            <span className="text-sm font-medium text-white">Quality</span>
                        </div>
                        {expandedSections.quality ?
                            <ChevronDown size={16} className="text-slate-400" /> :
                            <ChevronRight size={16} className="text-slate-400" />
                        }
                    </button>

                    {expandedSections.quality && (
                        <div className="p-3 border-t border-slate-700">
                            <QualityCard qualities={editedBlock.quality} />
                        </div>
                    )}
                </div>

                {/* Destinations Section */}
                <div className="bg-slate-800/50 rounded-lg overflow-hidden">
                    <button
                        onClick={() => toggleSection('destinations')}
                        className="w-full p-3 flex items-center justify-between hover:bg-slate-800"
                    >
                        <div className="flex items-center space-x-2">
                            <Target size={16} className="text-slate-400" />
                            <span className="text-sm font-medium text-white">Destinations</span>
                        </div>
                        {expandedSections.destinations ?
                            <ChevronDown size={16} className="text-slate-400" /> :
                            <ChevronRight size={16} className="text-slate-400" />
                        }
                    </button>

                    {expandedSections.destinations && (
                        <div className="p-3 border-t border-slate-700">
                            <DestinationSelector
                                destinations={defaultDestinations}
                                selected={editedBlock.preferredDestinations || []}
                                onChange={(dests) => setEditedBlock(prev => ({
                                    ...prev,
                                    preferredDestinations: dests
                                }))}
                            />
                        </div>
                    )}
                </div>

                {/* Notes */}
                <div className="bg-slate-800/50 rounded-lg p-3">
                    <label className="text-xs text-slate-400 block mb-2">Notes</label>
                    <textarea
                        value={editedBlock.notes || ''}
                        onChange={(e) => setEditedBlock(prev => ({ ...prev, notes: e.target.value }))}
                        className="w-full bg-slate-700 border border-slate-600 rounded p-2 text-sm text-white resize-none"
                        rows={3}
                        placeholder="Add notes about this block..."
                    />
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 flex space-x-3">
                <button
                    onClick={onClose}
                    className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm"
                >
                    Cancel
                </button>
                <button
                    onClick={handleSave}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm flex items-center justify-center space-x-2"
                >
                    <Save size={16} />
                    <span>Save</span>
                </button>
            </div>
        </div>
    );
};

export default BlockPropertiesPanel;
