/**
 * ColumnMapper Component - Phase 4 Site Builder UI
 * 
 * Maps source columns from imported CSV/TXT files to standard fields.
 * Supports auto-detection of column mappings with user override.
 * 
 * Features:
 * - Suggested mappings from parser
 * - Drag-and-drop column assignment
 * - Data preview
 * - Validation
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
    Columns,
    ChevronRight,
    Check,
    AlertTriangle,
    Info,
    RefreshCw
} from 'lucide-react';

// Standard field definitions
const STANDARD_FIELDS = {
    collar: [
        { key: 'HoleID', label: 'Hole ID', required: true, description: 'Unique borehole identifier' },
        { key: 'Easting', label: 'Easting (X)', required: true, description: 'X coordinate' },
        { key: 'Northing', label: 'Northing (Y)', required: true, description: 'Y coordinate' },
        { key: 'Elevation', label: 'Elevation (Z)', required: true, description: 'Collar elevation/RL' },
        { key: 'TotalDepth', label: 'Total Depth', required: false, description: 'End of hole depth' },
        { key: 'Azimuth', label: 'Azimuth', required: false, description: 'Hole direction (degrees)' },
        { key: 'Dip', label: 'Dip', required: false, description: 'Inclination from horizontal' },
    ],
    survey: [
        { key: 'HoleID', label: 'Hole ID', required: true, description: 'Borehole identifier' },
        { key: 'Depth', label: 'Depth', required: true, description: 'Survey depth' },
        { key: 'Azimuth', label: 'Azimuth', required: true, description: 'Direction at depth' },
        { key: 'Dip', label: 'Dip', required: true, description: 'Inclination at depth' },
    ],
    assay: [
        { key: 'HoleID', label: 'Hole ID', required: true, description: 'Borehole identifier' },
        { key: 'From', label: 'From Depth', required: true, description: 'Start of interval' },
        { key: 'To', label: 'To Depth', required: true, description: 'End of interval' },
        { key: 'Seam', label: 'Seam Name', required: false, description: 'Coal seam identifier' },
    ],
};

const ColumnMapper = ({
    columns = [],
    previewRows = [],
    fileType = 'collar',
    suggestedMappings = {},
    onChange,
    onValidate
}) => {
    const [mappings, setMappings] = useState({});
    const [qualityColumns, setQualityColumns] = useState([]);

    // Get standard fields for file type
    const standardFields = useMemo(() => {
        return STANDARD_FIELDS[fileType] || STANDARD_FIELDS.collar;
    }, [fileType]);

    // Initialize mappings from suggestions
    useEffect(() => {
        const initial = {};
        columns.forEach(col => {
            if (col.suggested_mapping) {
                initial[col.suggested_mapping] = col.name;
            }
        });
        setMappings(initial);

        // Identify quality columns (not mapped to standard fields)
        const standardKeys = standardFields.map(f => f.key);
        const quality = columns
            .filter(col => !standardKeys.includes(col.suggested_mapping) && col.inferred_type === 'float')
            .map(col => col.name);
        setQualityColumns(quality);
    }, [columns, standardFields]);

    // Notify parent of mapping changes
    useEffect(() => {
        if (onChange) {
            onChange({ mappings, qualityColumns });
        }
    }, [mappings, qualityColumns, onChange]);

    // Validate mappings
    const validation = useMemo(() => {
        const required = standardFields.filter(f => f.required);
        const missing = required.filter(f => !mappings[f.key]);
        const isValid = missing.length === 0;

        if (onValidate) {
            onValidate(isValid, missing.map(f => f.label));
        }

        return { isValid, missing };
    }, [mappings, standardFields, onValidate]);

    // Update a mapping
    const updateMapping = (standardKey, sourceColumn) => {
        setMappings(prev => {
            const next = { ...prev };
            if (sourceColumn === '') {
                delete next[standardKey];
            } else {
                next[standardKey] = sourceColumn;
            }
            return next;
        });
    };

    // Toggle quality column
    const toggleQualityColumn = (columnName) => {
        setQualityColumns(prev => {
            if (prev.includes(columnName)) {
                return prev.filter(c => c !== columnName);
            } else {
                return [...prev, columnName];
            }
        });
    };

    // Auto-detect mappings
    const autoDetect = () => {
        const detected = {};
        columns.forEach(col => {
            if (col.suggested_mapping) {
                detected[col.suggested_mapping] = col.name;
            }
        });
        setMappings(detected);
    };

    // Get mapped columns to filter from available
    const mappedColumns = Object.values(mappings);

    return (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '12px', overflow: 'hidden' }}>
            {/* Header */}
            <div style={{
                padding: '16px 20px',
                borderBottom: '1px solid #E5E7EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Columns size={20} color="#3B82F6" />
                    <span style={{ fontWeight: 600, color: '#1F2937' }}>Column Mapping</span>
                </div>
                <button
                    onClick={autoDetect}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 12px',
                        backgroundColor: '#F3F4F6',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '13px',
                        color: '#374151',
                        cursor: 'pointer'
                    }}
                >
                    <RefreshCw size={14} />
                    Auto-detect
                </button>
            </div>

            {/* Validation status */}
            {!validation.isValid && (
                <div style={{
                    padding: '12px 20px',
                    backgroundColor: '#FEF3C7',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    borderBottom: '1px solid #FDE68A'
                }}>
                    <AlertTriangle size={16} color="#D97706" />
                    <span style={{ fontSize: '13px', color: '#92400E' }}>
                        Missing required fields: {validation.missing.map(f => f.label).join(', ')}
                    </span>
                </div>
            )}

            {/* Standard field mappings */}
            <div style={{ padding: '16px 20px' }}>
                <div style={{ fontSize: '13px', fontWeight: 500, color: '#6B7280', marginBottom: '12px' }}>
                    Map source columns to standard fields
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {standardFields.map(field => (
                        <div
                            key={field.key}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px'
                            }}
                        >
                            {/* Target field */}
                            <div style={{
                                width: '160px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                            }}>
                                <span style={{
                                    fontSize: '14px',
                                    color: field.required ? '#1F2937' : '#6B7280',
                                    fontWeight: field.required ? 500 : 400
                                }}>
                                    {field.label}
                                </span>
                                {field.required && <span style={{ color: '#EF4444' }}>*</span>}
                            </div>

                            {/* Arrow */}
                            <ChevronRight size={16} color="#9CA3AF" />

                            {/* Source column select */}
                            <select
                                value={mappings[field.key] || ''}
                                onChange={(e) => updateMapping(field.key, e.target.value)}
                                style={{
                                    flex: 1,
                                    padding: '8px 12px',
                                    border: `1px solid ${mappings[field.key] ? '#10B981' : '#D1D5DB'}`,
                                    borderRadius: '6px',
                                    fontSize: '14px',
                                    backgroundColor: mappings[field.key] ? '#ECFDF5' : '#FFFFFF'
                                }}
                            >
                                <option value="">-- Select column --</option>
                                {columns.map(col => (
                                    <option
                                        key={col.name}
                                        value={col.name}
                                        disabled={mappedColumns.includes(col.name) && mappings[field.key] !== col.name}
                                    >
                                        {col.name} ({col.inferred_type})
                                    </option>
                                ))}
                            </select>

                            {/* Status icon */}
                            <div style={{ width: '24px' }}>
                                {mappings[field.key] && <Check size={18} color="#10B981" />}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Quality columns (for assay files) */}
            {fileType === 'assay' && (
                <div style={{
                    padding: '16px 20px',
                    borderTop: '1px solid #E5E7EB',
                    backgroundColor: '#F9FAFB'
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        marginBottom: '12px'
                    }}>
                        <Info size={16} color="#3B82F6" />
                        <span style={{ fontSize: '13px', fontWeight: 500, color: '#374151' }}>
                            Quality Columns (select columns containing assay values)
                        </span>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {columns
                            .filter(col => !standardFields.map(f => mappings[f.key]).includes(col.name))
                            .filter(col => col.inferred_type === 'float' || col.inferred_type === 'integer')
                            .map(col => (
                                <button
                                    key={col.name}
                                    onClick={() => toggleQualityColumn(col.name)}
                                    style={{
                                        padding: '6px 12px',
                                        borderRadius: '16px',
                                        border: qualityColumns.includes(col.name)
                                            ? '2px solid #3B82F6'
                                            : '1px solid #D1D5DB',
                                        backgroundColor: qualityColumns.includes(col.name)
                                            ? '#EFF6FF'
                                            : '#FFFFFF',
                                        fontSize: '13px',
                                        color: qualityColumns.includes(col.name) ? '#1D4ED8' : '#4B5563',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                >
                                    {qualityColumns.includes(col.name) && <Check size={14} />}
                                    {col.name}
                                </button>
                            ))
                        }
                    </div>
                </div>
            )}

            {/* Data preview */}
            {previewRows.length > 0 && (
                <div style={{
                    padding: '16px 20px',
                    borderTop: '1px solid #E5E7EB'
                }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: '#6B7280', marginBottom: '12px' }}>
                        Data Preview (first 5 rows)
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                        <table style={{
                            width: '100%',
                            borderCollapse: 'collapse',
                            fontSize: '12px'
                        }}>
                            <thead>
                                <tr style={{ backgroundColor: '#F3F4F6' }}>
                                    {columns.slice(0, 8).map(col => (
                                        <th
                                            key={col.name}
                                            style={{
                                                textAlign: 'left',
                                                padding: '8px 12px',
                                                fontWeight: 500,
                                                color: '#374151',
                                                borderBottom: '1px solid #E5E7EB'
                                            }}
                                        >
                                            {col.name}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {previewRows.slice(0, 5).map((row, idx) => (
                                    <tr key={idx}>
                                        {columns.slice(0, 8).map(col => (
                                            <td
                                                key={col.name}
                                                style={{
                                                    padding: '8px 12px',
                                                    color: '#4B5563',
                                                    borderBottom: '1px solid #F3F4F6'
                                                }}
                                            >
                                                {row[col.name] || '-'}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ColumnMapper;
