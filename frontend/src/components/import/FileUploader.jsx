/**
 * FileUploader Component - Phase 4 Site Builder UI
 * 
 * Drag-and-drop file uploader with format detection for:
 * - DXF (CAD geometry)
 * - Surpac .str (string files)
 * - CSV/TXT (borehole data)
 * 
 * Features:
 * - Drag and drop zone
 * - File type detection
 * - Preview of parsed data
 * - Multiple file support
 */

import React, { useState, useCallback, useRef } from 'react';
import {
    Upload,
    FileText,
    AlertCircle,
    CheckCircle,
    X,
    Loader2,
    FileSpreadsheet,
    FileType,
    Map
} from 'lucide-react';

// File format icons and colors
const FILE_FORMAT_CONFIG = {
    dxf: { icon: Map, color: '#3B82F6', label: 'DXF CAD File' },
    str: { icon: FileType, color: '#10B981', label: 'Surpac String' },
    csv: { icon: FileSpreadsheet, color: '#F59E0B', label: 'CSV Data' },
    txt: { icon: FileText, color: '#6B7280', label: 'Text File' },
};

const FileUploader = ({
    onFileParsed,
    onError,
    acceptedFormats = ['dxf', 'str', 'csv', 'txt'],
    multiple = false,
    maxSize = 50 * 1024 * 1024, // 50MB
    title = "Upload Files",
    description = "Drag and drop files or click to browse"
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [files, setFiles] = useState([]);
    const [parsing, setParsing] = useState({});
    const [results, setResults] = useState({});
    const [errors, setErrors] = useState({});
    const fileInputRef = useRef(null);

    // Determine file format from extension
    const getFileFormat = (filename) => {
        const ext = filename.toLowerCase().split('.').pop();
        if (acceptedFormats.includes(ext)) {
            return ext;
        }
        return null;
    };

    // Parse file based on format
    const parseFile = async (file) => {
        const format = getFileFormat(file.name);
        if (!format) {
            throw new Error(`Unsupported file format: ${file.name}`);
        }

        const formData = new FormData();
        formData.append('file', file);

        let endpoint;
        switch (format) {
            case 'dxf':
                endpoint = '/api/files/parse/dxf';
                break;
            case 'str':
                endpoint = '/api/files/parse/surpac';
                break;
            case 'csv':
            case 'txt':
                endpoint = '/api/files/parse/tabular';
                break;
            default:
                throw new Error(`No parser for format: ${format}`);
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to parse ${file.name}`);
        }

        return await response.json();
    };

    // Handle file selection
    const handleFiles = useCallback(async (selectedFiles) => {
        const newFiles = Array.from(selectedFiles).filter(file => {
            const format = getFileFormat(file.name);
            if (!format) {
                setErrors(prev => ({
                    ...prev,
                    [file.name]: `Unsupported format. Accepted: ${acceptedFormats.join(', ')}`
                }));
                return false;
            }
            if (file.size > maxSize) {
                setErrors(prev => ({
                    ...prev,
                    [file.name]: `File too large. Maximum size: ${Math.round(maxSize / 1024 / 1024)}MB`
                }));
                return false;
            }
            return true;
        });

        if (!multiple && newFiles.length > 1) {
            newFiles.splice(1);
        }

        setFiles(prev => multiple ? [...prev, ...newFiles] : newFiles);

        // Parse each file
        for (const file of newFiles) {
            setParsing(prev => ({ ...prev, [file.name]: true }));

            try {
                const result = await parseFile(file);
                setResults(prev => ({ ...prev, [file.name]: result }));
                setErrors(prev => {
                    const next = { ...prev };
                    delete next[file.name];
                    return next;
                });

                if (onFileParsed) {
                    onFileParsed(file, result, getFileFormat(file.name));
                }
            } catch (error) {
                setErrors(prev => ({ ...prev, [file.name]: error.message }));
                if (onError) {
                    onError(file, error);
                }
            } finally {
                setParsing(prev => ({ ...prev, [file.name]: false }));
            }
        }
    }, [acceptedFormats, maxSize, multiple, onFileParsed, onError]);

    // Drag handlers
    const handleDragEnter = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles.length > 0) {
            handleFiles(droppedFiles);
        }
    }, [handleFiles]);

    // Click to browse
    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileInput = (e) => {
        if (e.target.files?.length > 0) {
            handleFiles(e.target.files);
        }
    };

    // Remove file
    const removeFile = (filename) => {
        setFiles(prev => prev.filter(f => f.name !== filename));
        setResults(prev => {
            const next = { ...prev };
            delete next[filename];
            return next;
        });
        setErrors(prev => {
            const next = { ...prev };
            delete next[filename];
            return next;
        });
    };

    // Render file item
    const renderFileItem = (file) => {
        const format = getFileFormat(file.name);
        const config = FILE_FORMAT_CONFIG[format] || { icon: FileText, color: '#6B7280', label: 'Unknown' };
        const Icon = config.icon;
        const isParsing = parsing[file.name];
        const result = results[file.name];
        const error = errors[file.name];

        return (
            <div
                key={file.name}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px',
                    backgroundColor: error ? '#FEE2E2' : result ? '#ECFDF5' : '#F3F4F6',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    border: `1px solid ${error ? '#FECACA' : result ? '#A7F3D0' : '#E5E7EB'}`
                }}
            >
                <div
                    style={{
                        backgroundColor: config.color + '20',
                        padding: '8px',
                        borderRadius: '8px',
                        marginRight: '12px'
                    }}
                >
                    <Icon size={24} color={config.color} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                        fontWeight: 500,
                        color: '#1F2937',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                    }}>
                        {file.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6B7280' }}>
                        {config.label} • {(file.size / 1024).toFixed(1)} KB
                    </div>
                    {result && !error && (
                        <div style={{ fontSize: '12px', color: '#059669', marginTop: '4px' }}>
                            {result.entity_count && `${result.entity_count} entities`}
                            {result.row_count && `${result.row_count} rows, ${result.column_count} columns`}
                            {result.string_count && `${result.string_count} strings, ${result.point_count} points`}
                        </div>
                    )}
                    {error && (
                        <div style={{ fontSize: '12px', color: '#DC2626', marginTop: '4px' }}>
                            {error}
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isParsing && <Loader2 size={20} color="#3B82F6" style={{ animation: 'spin 1s linear infinite' }} />}
                    {result && !error && <CheckCircle size={20} color="#059669" />}
                    {error && <AlertCircle size={20} color="#DC2626" />}

                    <button
                        onClick={() => removeFile(file.name)}
                        style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '4px',
                            borderRadius: '4px'
                        }}
                    >
                        <X size={16} color="#6B7280" />
                    </button>
                </div>
            </div>
        );
    };

    return (
        <div style={{ width: '100%' }}>
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                multiple={multiple}
                accept={acceptedFormats.map(f => `.${f}`).join(',')}
                onChange={handleFileInput}
                style={{ display: 'none' }}
            />

            {/* Drop zone */}
            <div
                onClick={handleClick}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                style={{
                    border: `2px dashed ${isDragging ? '#3B82F6' : '#D1D5DB'}`,
                    borderRadius: '12px',
                    padding: '40px 20px',
                    textAlign: 'center',
                    backgroundColor: isDragging ? '#EFF6FF' : '#FAFAFA',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    marginBottom: files.length > 0 ? '16px' : 0
                }}
            >
                <Upload
                    size={48}
                    color={isDragging ? '#3B82F6' : '#9CA3AF'}
                    style={{ marginBottom: '16px' }}
                />
                <div style={{ fontSize: '16px', fontWeight: 500, color: '#374151', marginBottom: '4px' }}>
                    {title}
                </div>
                <div style={{ fontSize: '14px', color: '#6B7280', marginBottom: '12px' }}>
                    {description}
                </div>
                <div style={{ fontSize: '12px', color: '#9CA3AF' }}>
                    Supported formats: {acceptedFormats.map(f => `.${f}`).join(', ')}
                </div>
            </div>

            {/* File list */}
            {files.length > 0 && (
                <div>
                    {files.map(renderFileItem)}
                </div>
            )}

            <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

export default FileUploader;
