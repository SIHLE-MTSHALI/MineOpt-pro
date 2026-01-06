/**
 * ExportPanel Component - Phase 5 Export & Collaboration
 * 
 * UI for exporting geometry and data to various file formats.
 * 
 * Features:
 * - Format selection (DXF, Surpac .str, CSV)
 * - Layer/field selection
 * - Export preview
 * - Download handling
 */

import React, { useState, useMemo } from 'react';
import {
    Download,
    FileText,
    Map,
    FileSpreadsheet,
    Check,
    Loader2,
    ChevronDown,
    Settings
} from 'lucide-react';

const EXPORT_FORMATS = [
    {
        id: 'dxf',
        name: 'AutoCAD DXF',
        icon: Map,
        extension: '.dxf',
        description: 'CAD geometry file',
        supports: ['activity_areas', 'boreholes', 'block_model_outline']
    },
    {
        id: 'str',
        name: 'Surpac String',
        icon: FileText,
        extension: '.str',
        description: 'GEOVIA Surpac format',
        supports: ['activity_areas', 'boreholes']
    },
    {
        id: 'csv',
        name: 'CSV Data',
        icon: FileSpreadsheet,
        extension: '.csv',
        description: 'Comma-separated values',
        supports: ['boreholes', 'collars', 'intervals', 'blocks', 'schedule']
    }
];

const DATA_TYPES = [
    { id: 'activity_areas', name: 'Activity Areas', description: 'Mining block boundaries' },
    { id: 'boreholes', name: 'Boreholes', description: 'Collar locations and traces' },
    { id: 'intervals', name: 'Borehole Intervals', description: 'Quality data by depth' },
    { id: 'blocks', name: 'Block Model', description: 'Estimated grades' },
    { id: 'schedule', name: 'Schedule', description: 'Task data and timing' }
];

const ExportPanel = ({
    siteId,
    availableData = ['activity_areas', 'boreholes', 'intervals'],
    onExportComplete,
    style = {}
}) => {
    const [selectedFormat, setSelectedFormat] = useState('csv');
    const [selectedDataType, setSelectedDataType] = useState('boreholes');
    const [isExporting, setIsExporting] = useState(false);
    const [showOptions, setShowOptions] = useState(false);
    const [options, setOptions] = useState({
        includeAttributes: true,
        includeQuality: true,
        separateFiles: false
    });

    // Get current format info
    const formatInfo = useMemo(() => {
        return EXPORT_FORMATS.find(f => f.id === selectedFormat);
    }, [selectedFormat]);

    // Filter data types by format support
    const availableDataTypes = useMemo(() => {
        const format = EXPORT_FORMATS.find(f => f.id === selectedFormat);
        if (!format) return [];

        return DATA_TYPES.filter(dt =>
            format.supports.includes(dt.id) && availableData.includes(dt.id)
        );
    }, [selectedFormat, availableData]);

    // Handle export
    const handleExport = async () => {
        setIsExporting(true);

        try {
            const response = await fetch(`/api/files/export/${selectedFormat}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    format: selectedFormat,
                    data_type: selectedDataType,
                    site_id: siteId,
                    filename: `${selectedDataType}_export`,
                    options
                })
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            // Handle file download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${selectedDataType}_export${formatInfo?.extension || '.csv'}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            if (onExportComplete) {
                onExportComplete({ format: selectedFormat, dataType: selectedDataType });
            }
        } catch (error) {
            console.error('Export error:', error);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div
            style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                overflow: 'hidden',
                ...style
            }}
        >
            {/* Header */}
            <div style={{
                padding: '16px 20px',
                borderBottom: '1px solid #E5E7EB',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
            }}>
                <Download size={20} color="#3B82F6" />
                <span style={{ fontWeight: 600, color: '#1F2937' }}>Export Data</span>
            </div>

            {/* Format selection */}
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #F3F4F6' }}>
                <label style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#374151',
                    marginBottom: '8px'
                }}>
                    Export Format
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                    {EXPORT_FORMATS.map(format => {
                        const Icon = format.icon;
                        const isSelected = selectedFormat === format.id;

                        return (
                            <button
                                key={format.id}
                                onClick={() => setSelectedFormat(format.id)}
                                style={{
                                    flex: 1,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: '6px',
                                    padding: '12px',
                                    border: isSelected ? '2px solid #3B82F6' : '1px solid #E5E7EB',
                                    borderRadius: '8px',
                                    backgroundColor: isSelected ? '#EFF6FF' : '#FFFFFF',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s'
                                }}
                            >
                                <Icon size={24} color={isSelected ? '#3B82F6' : '#6B7280'} />
                                <span style={{
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    color: isSelected ? '#1D4ED8' : '#4B5563'
                                }}>
                                    {format.name}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Data type selection */}
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #F3F4F6' }}>
                <label style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#374151',
                    marginBottom: '8px'
                }}>
                    Data to Export
                </label>
                <select
                    value={selectedDataType}
                    onChange={(e) => setSelectedDataType(e.target.value)}
                    style={{
                        width: '100%',
                        padding: '10px 12px',
                        border: '1px solid #D1D5DB',
                        borderRadius: '6px',
                        fontSize: '14px',
                        backgroundColor: '#FFFFFF'
                    }}
                >
                    {availableDataTypes.map(dt => (
                        <option key={dt.id} value={dt.id}>
                            {dt.name} - {dt.description}
                        </option>
                    ))}
                </select>
            </div>

            {/* Options toggle */}
            <div style={{ padding: '12px 20px', borderBottom: '1px solid #F3F4F6' }}>
                <button
                    onClick={() => setShowOptions(!showOptions)}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '13px',
                        color: '#6B7280'
                    }}
                >
                    <Settings size={14} />
                    Advanced Options
                    <ChevronDown
                        size={14}
                        style={{
                            transform: showOptions ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s'
                        }}
                    />
                </button>

                {showOptions && (
                    <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <label style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '13px',
                            color: '#4B5563',
                            cursor: 'pointer'
                        }}>
                            <input
                                type="checkbox"
                                checked={options.includeAttributes}
                                onChange={(e) => setOptions(prev => ({ ...prev, includeAttributes: e.target.checked }))}
                            />
                            Include all attributes
                        </label>

                        <label style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '13px',
                            color: '#4B5563',
                            cursor: 'pointer'
                        }}>
                            <input
                                type="checkbox"
                                checked={options.includeQuality}
                                onChange={(e) => setOptions(prev => ({ ...prev, includeQuality: e.target.checked }))}
                            />
                            Include quality data
                        </label>
                    </div>
                )}
            </div>

            {/* Export button */}
            <div style={{ padding: '16px 20px' }}>
                <button
                    onClick={handleExport}
                    disabled={isExporting || availableDataTypes.length === 0}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        padding: '12px',
                        backgroundColor: isExporting || availableDataTypes.length === 0 ? '#E5E7EB' : '#3B82F6',
                        color: isExporting || availableDataTypes.length === 0 ? '#9CA3AF' : '#FFFFFF',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 500,
                        cursor: isExporting || availableDataTypes.length === 0 ? 'not-allowed' : 'pointer'
                    }}
                >
                    {isExporting ? (
                        <>
                            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            Exporting...
                        </>
                    ) : (
                        <>
                            <Download size={18} />
                            Export {formatInfo?.extension}
                        </>
                    )}
                </button>
            </div>

            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

export default ExportPanel;
