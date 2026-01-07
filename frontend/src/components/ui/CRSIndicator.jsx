/**
 * CRSIndicator.jsx - Coordinate Reference System Indicator
 * 
 * Always-visible component showing the current site's coordinate system.
 * Features:
 * - Color-coded by CRS type (geographic/projected/local)
 * - Click to open CRS settings
 * - Tooltip with full CRS details
 * - Compact and non-intrusive design
 */

import React, { useState, useEffect } from 'react';
import { MapPin, Globe, Grid3X3, Settings, ChevronDown, Check, Search } from 'lucide-react';

// CRS Category colors
const CATEGORY_COLORS = {
    geographic: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300', icon: Globe },
    projected: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300', icon: Grid3X3 },
    local: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300', icon: MapPin },
    custom: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300', icon: Settings }
};

// Common CRS options for quick selection
const QUICK_CRS_OPTIONS = [
    { epsg: 4326, name: 'WGS 84', region: 'Global' },
    { epsg: 2052, name: 'SA Lo27', region: 'South Africa' },
    { epsg: 2048, name: 'SA Lo19', region: 'South Africa' },
    { epsg: 28356, name: 'MGA Zone 56', region: 'Australia' },
    { epsg: 26913, name: 'NAD83 / UTM 13N', region: 'USA' },
];

/**
 * CRS Indicator Component
 */
function CRSIndicator({
    currentEpsg = null,
    currentName = null,
    category = 'projected',
    onCRSChange,
    siteId,
    compact = false
}) {
    const [isOpen, setIsOpen] = useState(false);
    const [systems, setSystems] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedRegion, setSelectedRegion] = useState('all');
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [crsDetails, setCrsDetails] = useState(null);

    // Get styling based on category
    const categoryStyle = CATEGORY_COLORS[category] || CATEGORY_COLORS.projected;
    const CategoryIcon = categoryStyle.icon;

    // Fetch available CRS systems
    useEffect(() => {
        if (isOpen && systems.length === 0) {
            fetchSystems();
            fetchRegions();
        }
    }, [isOpen]);

    // Fetch CRS details when EPSG changes
    useEffect(() => {
        if (currentEpsg) {
            fetchCrsDetails(currentEpsg);
        }
    }, [currentEpsg]);

    const fetchSystems = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/crs/systems');
            if (response.ok) {
                const data = await response.json();
                setSystems(data);
            }
        } catch (error) {
            console.error('Failed to fetch CRS systems:', error);
        }
        setLoading(false);
    };

    const fetchRegions = async () => {
        try {
            const response = await fetch('/api/crs/regions');
            if (response.ok) {
                const data = await response.json();
                setRegions(data);
            }
        } catch (error) {
            console.error('Failed to fetch regions:', error);
        }
    };

    const fetchCrsDetails = async (epsg) => {
        try {
            const response = await fetch(`/api/crs/${epsg}/info`);
            if (response.ok) {
                const data = await response.json();
                setCrsDetails(data);
            }
        } catch (error) {
            console.error('Failed to fetch CRS details:', error);
        }
    };

    const handleSelectCRS = async (epsg) => {
        if (onCRSChange) {
            onCRSChange(epsg);
        }
        setIsOpen(false);
    };

    // Filter systems based on search and region
    const filteredSystems = systems.filter(sys => {
        const matchesSearch = searchTerm === '' ||
            sys.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            sys.epsg.toString().includes(searchTerm);
        const matchesRegion = selectedRegion === 'all' ||
            sys.region.toLowerCase().includes(selectedRegion.toLowerCase());
        return matchesSearch && matchesRegion;
    });

    // Compact mode - just show icon and EPSG
    if (compact) {
        return (
            <div
                className={`flex items-center gap-1 px-2 py-1 rounded ${categoryStyle.bg} ${categoryStyle.text} cursor-pointer hover:opacity-80`}
                onClick={() => setIsOpen(true)}
                title={currentName || `EPSG:${currentEpsg}`}
            >
                <CategoryIcon size={14} />
                <span className="text-xs font-medium">
                    {currentEpsg || 'CRS'}
                </span>
            </div>
        );
    }

    return (
        <div className="relative">
            {/* Main Indicator Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${categoryStyle.bg} ${categoryStyle.text} ${categoryStyle.border} hover:shadow-md transition-shadow`}
            >
                <CategoryIcon size={18} />
                <div className="text-left">
                    <div className="text-xs opacity-70">Coordinate System</div>
                    <div className="font-medium text-sm">
                        {currentName || (currentEpsg ? `EPSG:${currentEpsg}` : 'Not Set')}
                    </div>
                </div>
                <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Panel */}
            {isOpen && (
                <div className="absolute top-full left-0 mt-2 w-96 bg-white rounded-lg shadow-xl border z-50 max-h-[500px] overflow-hidden flex flex-col">
                    {/* Header */}
                    <div className="p-4 border-b bg-gray-50">
                        <h3 className="font-semibold text-gray-800 mb-3">Select Coordinate System</h3>

                        {/* Search */}
                        <div className="relative mb-3">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search by name or EPSG..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        {/* Region Filter */}
                        <div className="flex gap-2 flex-wrap">
                            <button
                                onClick={() => setSelectedRegion('all')}
                                className={`px-3 py-1 text-xs rounded-full ${selectedRegion === 'all'
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                                    }`}
                            >
                                All
                            </button>
                            {regions.map(region => (
                                <button
                                    key={region}
                                    onClick={() => setSelectedRegion(region)}
                                    className={`px-3 py-1 text-xs rounded-full ${selectedRegion === region
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                                        }`}
                                >
                                    {region}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Quick Options */}
                    {searchTerm === '' && selectedRegion === 'all' && (
                        <div className="p-3 border-b bg-blue-50">
                            <div className="text-xs font-medium text-blue-600 mb-2">Quick Select</div>
                            <div className="flex flex-wrap gap-2">
                                {QUICK_CRS_OPTIONS.map(opt => (
                                    <button
                                        key={opt.epsg}
                                        onClick={() => handleSelectCRS(opt.epsg)}
                                        className={`px-2 py-1 text-xs rounded border ${currentEpsg === opt.epsg
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-100'
                                            }`}
                                    >
                                        {opt.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* CRS List */}
                    <div className="flex-1 overflow-y-auto max-h-64">
                        {loading ? (
                            <div className="p-4 text-center text-gray-500">Loading...</div>
                        ) : filteredSystems.length === 0 ? (
                            <div className="p-4 text-center text-gray-500">No coordinate systems found</div>
                        ) : (
                            filteredSystems.map(sys => (
                                <button
                                    key={sys.epsg}
                                    onClick={() => handleSelectCRS(sys.epsg)}
                                    className={`w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 border-b text-left ${currentEpsg === sys.epsg ? 'bg-blue-50' : ''
                                        }`}
                                >
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${CATEGORY_COLORS[sys.category]?.bg || 'bg-gray-100'
                                        }`}>
                                        {React.createElement(
                                            CATEGORY_COLORS[sys.category]?.icon || Grid3X3,
                                            { size: 16, className: CATEGORY_COLORS[sys.category]?.text || 'text-gray-600' }
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <div className="font-medium text-gray-800 text-sm">{sys.name}</div>
                                        <div className="text-xs text-gray-500">
                                            EPSG:{sys.epsg} • {sys.region} • {sys.units}
                                        </div>
                                    </div>
                                    {currentEpsg === sys.epsg && (
                                        <Check size={18} className="text-blue-500" />
                                    )}
                                </button>
                            ))
                        )}
                    </div>

                    {/* Current CRS Details */}
                    {crsDetails && (
                        <div className="p-3 border-t bg-gray-50">
                            <div className="text-xs text-gray-500 mb-1">Current CRS Details</div>
                            <div className="text-sm font-medium text-gray-800">{crsDetails.name}</div>
                            <div className="text-xs text-gray-500">
                                EPSG:{crsDetails.epsg} • {crsDetails.units} • {crsDetails.region}
                            </div>
                            {crsDetails.bounds && (
                                <div className="text-xs text-gray-400 mt-1">
                                    Bounds: {crsDetails.bounds.map(b => b.toFixed(1)).join(', ')}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Footer */}
                    <div className="p-3 border-t flex justify-end gap-2">
                        <button
                            onClick={() => setIsOpen(false)}
                            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Click outside to close */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
}

export default CRSIndicator;
