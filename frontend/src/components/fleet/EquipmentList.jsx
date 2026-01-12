/**
 * EquipmentList.jsx - Enhanced Equipment List with Detail Modal
 * 
 * Features:
 * - Modern card-based display
 * - Status update buttons
 * - Equipment detail modal
 * - Filter and search
 * - Animated transitions
 */

import React, { useState, useEffect } from 'react';
import { fleetAPI } from '../../services/api';
import {
    Truck, Search, RefreshCw, X, Settings, Activity,
    Fuel, Wrench, AlertTriangle, MapPin, Clock, ChevronDown
} from 'lucide-react';

// Status badge component
const StatusBadge = ({ status }) => {
    const statusConfig = {
        operating: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'Operating' },
        standby: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Standby' },
        maintenance: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'Maintenance' },
        breakdown: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Breakdown' },
        refueling: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Refueling' },
        shift_change: { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'Shift Change' },
        off_site: { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'Off Site' }
    };

    const config = statusConfig[status] || statusConfig.standby;

    return (
        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
            {config.label}
        </span>
    );
};

// Equipment type icon
const EquipmentIcon = ({ type, size = 20 }) => {
    const iconMap = {
        haul_truck: Truck,
        excavator: Settings,
        drill_rig: Activity,
        front_end_loader: Truck,
        dozer: Truck,
        water_cart: Fuel,
        fuel_truck: Fuel
    };
    const Icon = iconMap[type] || Truck;
    return <Icon size={size} />;
};

// Equipment Detail Modal
const EquipmentDetailModal = ({ equipment, onClose, onStatusUpdate }) => {
    const [updating, setUpdating] = useState(false);

    const handleStatusChange = async (newStatus) => {
        setUpdating(true);
        await onStatusUpdate(equipment.equipment_id, newStatus);
        setUpdating(false);
    };

    if (!equipment) return null;

    const statusOptions = [
        { value: 'operating', label: 'Operating', icon: Activity, color: 'emerald' },
        { value: 'standby', label: 'Standby', icon: Clock, color: 'blue' },
        { value: 'maintenance', label: 'Maintenance', icon: Wrench, color: 'amber' },
        { value: 'breakdown', label: 'Breakdown', icon: AlertTriangle, color: 'red' },
        { value: 'refueling', label: 'Refueling', icon: Fuel, color: 'purple' }
    ];

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full shadow-2xl animate-scale-in">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                            <EquipmentIcon type={equipment.equipment_type} size={24} />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">{equipment.fleet_number}</h3>
                            <p className="text-sm text-slate-400">{equipment.name || equipment.equipment_type}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <X size={20} className="text-slate-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Current Status */}
                    <div>
                        <div className="text-sm text-slate-400 mb-2">Current Status</div>
                        <StatusBadge status={equipment.status} />
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 rounded-lg p-3">
                            <div className="text-xs text-slate-500">Type</div>
                            <div className="text-sm text-white mt-1 capitalize">
                                {equipment.equipment_type?.replace(/_/g, ' ')}
                            </div>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3">
                            <div className="text-xs text-slate-500">Model</div>
                            <div className="text-sm text-white mt-1">
                                {equipment.manufacturer} {equipment.model || '-'}
                            </div>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3">
                            <div className="text-xs text-slate-500">Engine Hours</div>
                            <div className="text-sm text-white mt-1">
                                {equipment.engine_hours?.toFixed(1) || '-'} hrs
                            </div>
                        </div>
                        <div className="bg-slate-800/50 rounded-lg p-3">
                            <div className="text-xs text-slate-500">Payload Capacity</div>
                            <div className="text-sm text-white mt-1">
                                {equipment.payload_tonnes ? `${equipment.payload_tonnes}t` : '-'}
                            </div>
                        </div>
                    </div>

                    {/* Location */}
                    {(equipment.last_latitude && equipment.last_longitude) && (
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                            <MapPin size={14} />
                            <span>
                                {equipment.last_latitude?.toFixed(5)}, {equipment.last_longitude?.toFixed(5)}
                            </span>
                            {equipment.last_speed_kmh && (
                                <span className="ml-2">• {equipment.last_speed_kmh.toFixed(1)} km/h</span>
                            )}
                        </div>
                    )}

                    {/* Status Update Actions */}
                    <div>
                        <div className="text-sm text-slate-400 mb-3">Update Status</div>
                        <div className="grid grid-cols-2 gap-2">
                            {statusOptions.map(option => (
                                <button
                                    key={option.value}
                                    onClick={() => handleStatusChange(option.value)}
                                    disabled={updating || equipment.status === option.value}
                                    className={`
                                        flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
                                        transition-all disabled:opacity-50
                                        ${equipment.status === option.value
                                            ? `bg-${option.color}-500/30 text-${option.color}-400 border-2 border-${option.color}-500/50`
                                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border-2 border-transparent'
                                        }
                                    `}
                                >
                                    <option.icon size={14} />
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const EquipmentList = ({ siteId }) => {
    const [equipment, setEquipment] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterType, setFilterType] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedEquipment, setSelectedEquipment] = useState(null);

    useEffect(() => {
        loadEquipment();
    }, [siteId, filterType]);

    const loadEquipment = async () => {
        if (!siteId) return;
        try {
            setLoading(true);
            const data = await fleetAPI.getEquipmentList(siteId, filterType || null, null);
            setEquipment(data || []);
        } catch (error) {
            console.error('Failed to load equipment:', error);
            setEquipment([]);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id, newStatus) => {
        try {
            await fleetAPI.updateStatus(id, newStatus);
            await loadEquipment();
            // Update modal state if open
            if (selectedEquipment?.equipment_id === id) {
                const updated = equipment.find(e => e.equipment_id === id);
                if (updated) {
                    setSelectedEquipment({ ...updated, status: newStatus });
                }
            }
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    // Filter equipment by search query
    const filteredEquipment = equipment.filter(eq => {
        if (!searchQuery) return true;
        const query = searchQuery.toLowerCase();
        return (
            eq.fleet_number?.toLowerCase().includes(query) ||
            eq.name?.toLowerCase().includes(query) ||
            eq.equipment_type?.toLowerCase().includes(query) ||
            eq.model?.toLowerCase().includes(query)
        );
    });

    // Loading skeleton
    if (loading) {
        return (
            <div className="space-y-4">
                <div className="flex gap-4">
                    <div className="h-10 w-64 bg-slate-800 rounded-lg animate-pulse"></div>
                    <div className="h-10 w-40 bg-slate-800 rounded-lg animate-pulse"></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 animate-pulse">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-slate-700 rounded-lg"></div>
                                <div className="flex-1">
                                    <div className="h-4 w-20 bg-slate-700 rounded mb-2"></div>
                                    <div className="h-3 w-32 bg-slate-700 rounded"></div>
                                </div>
                            </div>
                            <div className="h-6 w-24 bg-slate-700 rounded-full"></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 max-w-md">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search equipment..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
                    />
                </div>

                <div className="relative">
                    <select
                        onChange={(e) => setFilterType(e.target.value)}
                        value={filterType}
                        className="appearance-none px-4 py-2.5 pr-10 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors cursor-pointer"
                    >
                        <option value="">All Types</option>
                        <option value="haul_truck">Haul Trucks</option>
                        <option value="excavator">Excavators</option>
                        <option value="drill_rig">Drills</option>
                        <option value="front_end_loader">Loaders</option>
                        <option value="dozer">Dozers</option>
                    </select>
                    <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>

                <button
                    onClick={loadEquipment}
                    className="px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2"
                >
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* Equipment count */}
            <div className="text-sm text-slate-400">
                Showing {filteredEquipment.length} of {equipment.length} equipment
            </div>

            {/* Equipment Grid */}
            {filteredEquipment.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredEquipment.map((eq, idx) => (
                        <div
                            key={eq.equipment_id}
                            onClick={() => setSelectedEquipment(eq)}
                            className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 hover:border-slate-600 hover:bg-slate-800/70 transition-all cursor-pointer group"
                            style={{
                                animation: `slideUp 0.3s ease-out forwards`,
                                animationDelay: `${idx * 50}ms`,
                                opacity: 0
                            }}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                                    <EquipmentIcon type={eq.equipment_type} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-medium text-white truncate">{eq.fleet_number}</div>
                                    <div className="text-xs text-slate-400 truncate capitalize">
                                        {eq.equipment_type?.replace(/_/g, ' ')}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between">
                                <StatusBadge status={eq.status} />
                                {eq.engine_hours && (
                                    <span className="text-xs text-slate-500">
                                        {eq.engine_hours.toFixed(0)} hrs
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-12 text-slate-400">
                    <Truck size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No equipment found</p>
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
                        >
                            Clear search
                        </button>
                    )}
                </div>
            )}

            {/* Detail Modal */}
            {selectedEquipment && (
                <EquipmentDetailModal
                    equipment={selectedEquipment}
                    onClose={() => setSelectedEquipment(null)}
                    onStatusUpdate={handleStatusUpdate}
                />
            )}
        </div>
    );
};

export default EquipmentList;
