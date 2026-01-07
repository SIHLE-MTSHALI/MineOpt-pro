/**
 * CRSSelector.jsx - Phase 1
 * 
 * CRS selector for site settings.
 * 
 * Features:
 * - Search and filter coordinate systems
 * - Grouped by region/type
 * - Auto-detection from data
 * - Custom EPSG entry
 * - Preview of selected CRS
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
    Globe,
    Search,
    MapPin,
    Check,
    X,
    ChevronDown,
    Info,
    RefreshCw
} from 'lucide-react';

// Common coordinate systems grouped by region
const CRS_GROUPS = {
    'South Africa': [
        { epsg: 2046, name: 'Hartebeesthoek94 / Lo15', zone: 'Lo15' },
        { epsg: 2047, name: 'Hartebeesthoek94 / Lo17', zone: 'Lo17' },
        { epsg: 2048, name: 'Hartebeesthoek94 / Lo19', zone: 'Lo19' },
        { epsg: 2049, name: 'Hartebeesthoek94 / Lo21', zone: 'Lo21' },
        { epsg: 2050, name: 'Hartebeesthoek94 / Lo23', zone: 'Lo23' },
        { epsg: 2051, name: 'Hartebeesthoek94 / Lo25', zone: 'Lo25' },
        { epsg: 2052, name: 'Hartebeesthoek94 / Lo27', zone: 'Lo27' },
        { epsg: 2053, name: 'Hartebeesthoek94 / Lo29', zone: 'Lo29' },
        { epsg: 2054, name: 'Hartebeesthoek94 / Lo31', zone: 'Lo31' },
        { epsg: 2055, name: 'Hartebeesthoek94 / Lo33', zone: 'Lo33' },
        { epsg: 22234, name: 'Cape / Lo19', zone: 'Lo19 (old)' },
        { epsg: 22235, name: 'Cape / Lo21', zone: 'Lo21 (old)' }
    ],
    'Australia': [
        { epsg: 28349, name: 'GDA94 / MGA zone 49', zone: 'MGA49' },
        { epsg: 28350, name: 'GDA94 / MGA zone 50', zone: 'MGA50' },
        { epsg: 28351, name: 'GDA94 / MGA zone 51', zone: 'MGA51' },
        { epsg: 28352, name: 'GDA94 / MGA zone 52', zone: 'MGA52' },
        { epsg: 28353, name: 'GDA94 / MGA zone 53', zone: 'MGA53' },
        { epsg: 28354, name: 'GDA94 / MGA zone 54', zone: 'MGA54' },
        { epsg: 28355, name: 'GDA94 / MGA zone 55', zone: 'MGA55' },
        { epsg: 28356, name: 'GDA94 / MGA zone 56', zone: 'MGA56' },
        { epsg: 7849, name: 'GDA2020 / MGA zone 49', zone: 'MGA49 (2020)' },
        { epsg: 7850, name: 'GDA2020 / MGA zone 50', zone: 'MGA50 (2020)' }
    ],
    'UTM Zones': [
        { epsg: 32601, name: 'WGS 84 / UTM zone 1N', zone: '1N' },
        { epsg: 32610, name: 'WGS 84 / UTM zone 10N', zone: '10N' },
        { epsg: 32617, name: 'WGS 84 / UTM zone 17N', zone: '17N' },
        { epsg: 32618, name: 'WGS 84 / UTM zone 18N', zone: '18N' },
        { epsg: 32632, name: 'WGS 84 / UTM zone 32N', zone: '32N' },
        { epsg: 32633, name: 'WGS 84 / UTM zone 33N', zone: '33N' },
        { epsg: 32734, name: 'WGS 84 / UTM zone 34S', zone: '34S' },
        { epsg: 32735, name: 'WGS 84 / UTM zone 35S', zone: '35S' },
        { epsg: 32736, name: 'WGS 84 / UTM zone 36S', zone: '36S' }
    ],
    'Chile': [
        { epsg: 32718, name: 'WGS 84 / UTM zone 18S', zone: 'Zone 18S' },
        { epsg: 32719, name: 'WGS 84 / UTM zone 19S', zone: 'Zone 19S' },
        { epsg: 5361, name: 'SIRGAS-Chile 2002 / UTM zone 18S', zone: 'SIRGAS 18S' },
        { epsg: 5362, name: 'SIRGAS-Chile 2002 / UTM zone 19S', zone: 'SIRGAS 19S' }
    ],
    'Americas': [
        { epsg: 2154, name: 'RGF93 / Lambert-93', zone: 'France' },
        { epsg: 26917, name: 'NAD83 / UTM zone 17N', zone: 'NAD83 17N' },
        { epsg: 26918, name: 'NAD83 / UTM zone 18N', zone: 'NAD83 18N' },
        { epsg: 3857, name: 'WGS 84 / Pseudo-Mercator', zone: 'Web' }
    ],
    'Geographic': [
        { epsg: 4326, name: 'WGS 84', zone: 'Geographic' },
        { epsg: 4148, name: 'Hartebeesthoek94', zone: 'SA Geographic' },
        { epsg: 4283, name: 'GDA94', zone: 'AU Geographic' }
    ]
};

const CRSSelector = ({
    value,
    onChange,
    onAutoDetect,
    samplePoint,
    className = ''
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [customEPSG, setCustomEPSG] = useState('');
    const [activeGroup, setActiveGroup] = useState(null);
    const [isDetecting, setIsDetecting] = useState(false);

    // Flatten all CRS options for search
    const allCRS = useMemo(() => {
        const result = [];
        Object.entries(CRS_GROUPS).forEach(([region, systems]) => {
            systems.forEach(sys => {
                result.push({ ...sys, region });
            });
        });
        return result;
    }, []);

    // Filter CRS by search
    const filteredCRS = useMemo(() => {
        if (!searchQuery) return null; // Show grouped view

        const query = searchQuery.toLowerCase();
        return allCRS.filter(crs =>
            crs.name.toLowerCase().includes(query) ||
            crs.epsg.toString().includes(query) ||
            crs.zone.toLowerCase().includes(query) ||
            crs.region.toLowerCase().includes(query)
        );
    }, [searchQuery, allCRS]);

    // Find current selection
    const selectedCRS = useMemo(() => {
        if (!value) return null;
        return allCRS.find(crs => crs.epsg === value);
    }, [value, allCRS]);

    // Handle selection
    const handleSelect = useCallback((epsg) => {
        onChange?.(epsg);
        setIsOpen(false);
        setSearchQuery('');
    }, [onChange]);

    // Handle custom EPSG
    const handleCustomSubmit = useCallback(() => {
        const epsg = parseInt(customEPSG, 10);
        if (epsg > 0 && epsg < 100000) {
            handleSelect(epsg);
            setCustomEPSG('');
        }
    }, [customEPSG, handleSelect]);

    // Handle auto-detect
    const handleAutoDetect = useCallback(async () => {
        setIsDetecting(true);
        try {
            if (onAutoDetect) {
                const detected = await onAutoDetect(samplePoint);
                if (detected) {
                    handleSelect(detected);
                }
            }
        } finally {
            setIsDetecting(false);
        }
    }, [onAutoDetect, samplePoint, handleSelect]);

    return (
        <div className={`crs-selector ${className}`}>
            {/* Selected Value Display */}
            <button
                className="selector-trigger"
                onClick={() => setIsOpen(!isOpen)}
            >
                <Globe size={16} className="icon" />
                <div className="selected-info">
                    {selectedCRS ? (
                        <>
                            <span className="epsg">EPSG:{selectedCRS.epsg}</span>
                            <span className="name">{selectedCRS.name}</span>
                        </>
                    ) : value ? (
                        <>
                            <span className="epsg">EPSG:{value}</span>
                            <span className="name">Custom</span>
                        </>
                    ) : (
                        <span className="placeholder">Select Coordinate System...</span>
                    )}
                </div>
                <ChevronDown size={16} className={`chevron ${isOpen ? 'open' : ''}`} />
            </button>

            {/* Dropdown */}
            {isOpen && (
                <div className="selector-dropdown">
                    {/* Search */}
                    <div className="search-bar">
                        <Search size={14} />
                        <input
                            type="text"
                            placeholder="Search by name, EPSG, or region..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            autoFocus
                        />
                    </div>

                    {/* Auto-detect Button */}
                    {onAutoDetect && (
                        <button
                            className="auto-detect-btn"
                            onClick={handleAutoDetect}
                            disabled={isDetecting}
                        >
                            <RefreshCw size={14} className={isDetecting ? 'spinning' : ''} />
                            {isDetecting ? 'Detecting...' : 'Auto-detect from data'}
                        </button>
                    )}

                    {/* Search Results */}
                    {filteredCRS ? (
                        <div className="search-results">
                            {filteredCRS.length === 0 ? (
                                <div className="no-results">No matching coordinate systems</div>
                            ) : (
                                filteredCRS.map(crs => (
                                    <button
                                        key={crs.epsg}
                                        className={`crs-option ${value === crs.epsg ? 'selected' : ''}`}
                                        onClick={() => handleSelect(crs.epsg)}
                                    >
                                        <span className="epsg">EPSG:{crs.epsg}</span>
                                        <span className="name">{crs.name}</span>
                                        <span className="region">{crs.region}</span>
                                        {value === crs.epsg && <Check size={14} className="check" />}
                                    </button>
                                ))
                            )}
                        </div>
                    ) : (
                        /* Grouped View */
                        <div className="grouped-list">
                            {Object.entries(CRS_GROUPS).map(([region, systems]) => (
                                <div key={region} className="crs-group">
                                    <button
                                        className={`group-header ${activeGroup === region ? 'expanded' : ''}`}
                                        onClick={() => setActiveGroup(activeGroup === region ? null : region)}
                                    >
                                        <MapPin size={14} />
                                        <span>{region}</span>
                                        <span className="count">{systems.length}</span>
                                        <ChevronDown size={14} className="expand-icon" />
                                    </button>

                                    {activeGroup === region && (
                                        <div className="group-items">
                                            {systems.map(crs => (
                                                <button
                                                    key={crs.epsg}
                                                    className={`crs-option ${value === crs.epsg ? 'selected' : ''}`}
                                                    onClick={() => handleSelect(crs.epsg)}
                                                >
                                                    <span className="epsg">EPSG:{crs.epsg}</span>
                                                    <span className="name">{crs.name}</span>
                                                    {value === crs.epsg && <Check size={14} className="check" />}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Custom EPSG Entry */}
                    <div className="custom-entry">
                        <span className="label">Custom EPSG:</span>
                        <input
                            type="number"
                            placeholder="e.g., 32735"
                            value={customEPSG}
                            onChange={(e) => setCustomEPSG(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleCustomSubmit()}
                        />
                        <button onClick={handleCustomSubmit} disabled={!customEPSG}>
                            <Check size={14} />
                        </button>
                    </div>
                </div>
            )}

            <style jsx>{`
        .crs-selector {
          position: relative;
        }
        
        .selector-trigger {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          padding: 10px 14px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          color: #fff;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        
        .selector-trigger:hover {
          border-color: rgba(255,255,255,0.25);
        }
        
        .icon {
          color: #60a5fa;
          flex-shrink: 0;
        }
        
        .selected-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 2px;
          text-align: left;
        }
        
        .epsg {
          font-size: 11px;
          color: #60a5fa;
          font-family: 'SF Mono', monospace;
        }
        
        .name {
          font-size: 12px;
          color: #c0c0d0;
        }
        
        .placeholder {
          font-size: 12px;
          color: #666;
        }
        
        .chevron {
          color: #666;
          transition: transform 0.2s ease;
        }
        
        .chevron.open {
          transform: rotate(180deg);
        }
        
        .selector-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          margin-top: 4px;
          background: #2a2a3e;
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.4);
          z-index: 1000;
          max-height: 400px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        
        .search-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
          color: #666;
        }
        
        .search-bar input {
          flex: 1;
          background: transparent;
          border: none;
          color: #fff;
          font-size: 12px;
          outline: none;
        }
        
        .auto-detect-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 8px 12px;
          margin: 8px;
          background: rgba(59, 130, 246, 0.15);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 6px;
          color: #60a5fa;
          font-size: 12px;
          cursor: pointer;
        }
        
        .auto-detect-btn:hover:not(:disabled) {
          background: rgba(59, 130, 246, 0.25);
        }
        
        .spinning {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .search-results, .grouped-list {
          flex: 1;
          overflow-y: auto;
          padding: 4px 0;
        }
        
        .no-results {
          padding: 16px;
          text-align: center;
          color: #666;
          font-size: 12px;
        }
        
        .crs-group {
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .group-header {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 10px 12px;
          background: transparent;
          border: none;
          color: #a0a0b0;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
        }
        
        .group-header:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .group-header span:first-of-type {
          flex: 1;
          text-align: left;
        }
        
        .count {
          background: rgba(255,255,255,0.1);
          padding: 2px 6px;
          border-radius: 8px;
          font-size: 10px;
        }
        
        .expand-icon {
          transition: transform 0.2s ease;
        }
        
        .group-header.expanded .expand-icon {
          transform: rotate(180deg);
        }
        
        .group-items {
          padding-left: 24px;
          background: rgba(0,0,0,0.1);
        }
        
        .crs-option {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 8px 12px;
          background: transparent;
          border: none;
          color: #c0c0d0;
          font-size: 11px;
          cursor: pointer;
          text-align: left;
        }
        
        .crs-option:hover {
          background: rgba(255,255,255,0.05);
        }
        
        .crs-option.selected {
          background: rgba(59, 130, 246, 0.15);
        }
        
        .crs-option .epsg {
          min-width: 80px;
        }
        
        .crs-option .name {
          flex: 1;
        }
        
        .crs-option .region {
          color: #666;
          font-size: 10px;
        }
        
        .check {
          color: #4ade80;
        }
        
        .custom-entry {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-top: 1px solid rgba(255,255,255,0.1);
          background: rgba(0,0,0,0.2);
        }
        
        .custom-entry .label {
          font-size: 11px;
          color: #888;
        }
        
        .custom-entry input {
          flex: 1;
          padding: 4px 8px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 4px;
          color: #fff;
          font-size: 11px;
        }
        
        .custom-entry button {
          padding: 4px 8px;
          background: rgba(34, 197, 94, 0.2);
          border: none;
          border-radius: 4px;
          color: #4ade80;
          cursor: pointer;
        }
        
        .custom-entry button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
        </div>
    );
};

export default CRSSelector;
