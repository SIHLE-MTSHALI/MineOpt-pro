/**
 * TerrainImportPanel.jsx - Multi-source Terrain Import
 * 
 * Provides 3 ways to import/create terrain surfaces:
 * 1. XYZ/ASC file upload - Point cloud to TIN
 * 2. DXF file - Import existing TIN surfaces
 * 3. Borehole collars - Generate terrain from collar elevations
 */

import React, { useState, useCallback } from 'react';
import {
    Upload,
    FileText,
    MapPin,
    Mountain,
    Check,
    AlertCircle,
    Loader2,
    Eye,
    RefreshCw
} from 'lucide-react';

// Import sources
const IMPORT_SOURCES = {
    XYZ: 'xyz',
    DXF: 'dxf',
    BOREHOLES: 'boreholes'
};

const SOURCE_CONFIG = {
    [IMPORT_SOURCES.XYZ]: {
        label: 'XYZ/ASC File',
        icon: FileText,
        description: 'Upload point cloud file (.xyz, .txt, .asc)',
        accept: '.xyz,.txt,.asc,.csv'
    },
    [IMPORT_SOURCES.DXF]: {
        label: 'DXF File',
        icon: Upload,
        description: 'Import existing TIN surface from DXF',
        accept: '.dxf'
    },
    [IMPORT_SOURCES.BOREHOLES]: {
        label: 'Borehole Collars',
        icon: MapPin,
        description: 'Generate terrain from collar elevations',
        accept: null
    }
};

/**
 * File upload dropzone
 */
const FileDropzone = ({ accept, onFileSelect, uploading }) => {
    const [dragActive, setDragActive] = useState(false);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            onFileSelect(files[0]);
        }
    }, [onFileSelect]);

    const handleChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            onFileSelect(e.target.files[0]);
        }
    };

    return (
        <div
            className={`dropzone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
        >
            <input
                type="file"
                accept={accept}
                onChange={handleChange}
                id="file-upload"
                style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" className="dropzone-content">
                {uploading ? (
                    <Loader2 className="spin" size={32} />
                ) : (
                    <Upload size={32} />
                )}
                <p>Drop file here or click to browse</p>
                <span className="accepted-formats">Accepted: {accept}</span>
            </label>

            <style jsx>{`
                .dropzone {
                    border: 2px dashed #4a4a6a;
                    border-radius: 12px;
                    padding: 32px;
                    text-align: center;
                    transition: all 0.2s;
                    cursor: pointer;
                }
                
                .dropzone:hover, .dropzone.active {
                    border-color: #6060a0;
                    background: rgba(96, 96, 160, 0.1);
                }
                
                .dropzone-content {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 12px;
                    cursor: pointer;
                    color: #a0a0c0;
                }
                
                .dropzone-content p {
                    margin: 0;
                    font-size: 1rem;
                }
                
                .accepted-formats {
                    font-size: 0.8rem;
                    color: #6060a0;
                }
                
                .spin {
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

/**
 * Borehole selection panel
 */
const BoreholeSelector = ({ boreholes = [], selected = [], onSelectionChange }) => {
    const toggleAll = () => {
        if (selected.length === boreholes.length) {
            onSelectionChange([]);
        } else {
            onSelectionChange(boreholes.map(b => b.collar_id || b.hole_id));
        }
    };

    const toggleOne = (id) => {
        if (selected.includes(id)) {
            onSelectionChange(selected.filter(s => s !== id));
        } else {
            onSelectionChange([...selected, id]);
        }
    };

    return (
        <div className="borehole-selector">
            <div className="selector-header">
                <span>{selected.length} of {boreholes.length} selected</span>
                <button onClick={toggleAll}>
                    {selected.length === boreholes.length ? 'Deselect All' : 'Select All'}
                </button>
            </div>

            <div className="borehole-list">
                {boreholes.map(bh => {
                    const id = bh.collar_id || bh.hole_id;
                    const isSelected = selected.includes(id);
                    return (
                        <div
                            key={id}
                            className={`borehole-item ${isSelected ? 'selected' : ''}`}
                            onClick={() => toggleOne(id)}
                        >
                            <div className="checkbox">
                                {isSelected && <Check size={14} />}
                            </div>
                            <div className="borehole-info">
                                <span className="borehole-id">{bh.hole_id}</span>
                                <span className="borehole-coords">
                                    E: {bh.easting?.toFixed(0)} | N: {bh.northing?.toFixed(0)} | Z: {bh.elevation?.toFixed(1)}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <style jsx>{`
                .borehole-selector {
                    border: 1px solid #3a3a5a;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .selector-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 14px;
                    background: #2a2a4a;
                    border-bottom: 1px solid #3a3a5a;
                }
                
                .selector-header span {
                    font-size: 0.85rem;
                    color: #a0a0c0;
                }
                
                .selector-header button {
                    background: none;
                    border: none;
                    color: #6080c0;
                    cursor: pointer;
                    font-size: 0.85rem;
                }
                
                .borehole-list {
                    max-height: 200px;
                    overflow-y: auto;
                }
                
                .borehole-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px 14px;
                    cursor: pointer;
                    transition: background 0.2s;
                    border-bottom: 1px solid #2a2a4a;
                }
                
                .borehole-item:hover {
                    background: #2a2a4a;
                }
                
                .borehole-item.selected {
                    background: rgba(64, 64, 160, 0.2);
                }
                
                .checkbox {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #4a4a6a;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .borehole-item.selected .checkbox {
                    background: #4040a0;
                    border-color: #6060c0;
                    color: white;
                }
                
                .borehole-info {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                }
                
                .borehole-id {
                    font-weight: 500;
                }
                
                .borehole-coords {
                    font-size: 0.75rem;
                    color: #6060a0;
                }
            `}</style>
        </div>
    );
};

/**
 * Main TerrainImportPanel component
 */
const TerrainImportPanel = ({
    siteId,
    boreholes = [],
    onSurfaceCreated,
    onPreview
}) => {
    const [source, setSource] = useState(IMPORT_SOURCES.XYZ);
    const [file, setFile] = useState(null);
    const [selectedBoreholes, setSelectedBoreholes] = useState([]);
    const [surfaceName, setSurfaceName] = useState('Terrain');
    const [importing, setImporting] = useState(false);
    const [preview, setPreview] = useState(null);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const config = SOURCE_CONFIG[source];

    const handleFileSelect = async (selectedFile) => {
        setFile(selectedFile);
        setError(null);

        // Try to preview the file
        if (source === IMPORT_SOURCES.XYZ) {
            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                // Preview first few rows
                const text = await selectedFile.text();
                const lines = text.split('\n').slice(0, 10);
                setPreview({
                    filename: selectedFile.name,
                    size: selectedFile.size,
                    preview_lines: lines.length,
                    sample: lines
                });
            } catch (err) {
                // Preview failed, continue anyway
            }
        }
    };

    const handleImport = async () => {
        setImporting(true);
        setError(null);

        try {
            let response;

            if (source === IMPORT_SOURCES.BOREHOLES) {
                // Create from borehole collars
                if (selectedBoreholes.length < 3) {
                    throw new Error('At least 3 boreholes required for triangulation');
                }

                // Get collar data and generate surface
                response = await fetch('/api/surfaces/create-from-points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        site_id: siteId,
                        name: surfaceName,
                        surface_type: 'terrain',
                        points: boreholes
                            .filter(b => selectedBoreholes.includes(b.collar_id || b.hole_id))
                            .map(b => [b.easting, b.northing, b.elevation])
                    })
                });
            } else {
                // Upload file
                if (!file) {
                    throw new Error('Please select a file');
                }

                const formData = new FormData();
                formData.append('file', file);

                response = await fetch(
                    `/api/surfaces/create-from-file?site_id=${siteId}&name=${encodeURIComponent(surfaceName)}&surface_type=terrain`,
                    {
                        method: 'POST',
                        body: formData
                    }
                );
            }

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Import failed');
            }

            const data = await response.json();
            setResult(data);

            if (onSurfaceCreated) {
                onSurfaceCreated(data);
            }

        } catch (err) {
            setError(err.message);
        } finally {
            setImporting(false);
        }
    };

    return (
        <div className="terrain-import-panel">
            <div className="panel-header">
                <Mountain size={24} />
                <h3>Import Terrain Surface</h3>
            </div>

            {/* Source Selection */}
            <div className="source-tabs">
                {Object.entries(SOURCE_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    return (
                        <button
                            key={key}
                            className={`source-tab ${source === key ? 'active' : ''}`}
                            onClick={() => {
                                setSource(key);
                                setFile(null);
                                setPreview(null);
                                setResult(null);
                            }}
                        >
                            <Icon size={18} />
                            <span>{cfg.label}</span>
                        </button>
                    );
                })}
            </div>

            <p className="source-description">{config.description}</p>

            {/* Surface Name */}
            <div className="input-group">
                <label>Surface Name</label>
                <input
                    type="text"
                    value={surfaceName}
                    onChange={(e) => setSurfaceName(e.target.value)}
                    placeholder="Enter surface name..."
                />
            </div>

            {/* Source-specific content */}
            <div className="source-content">
                {source === IMPORT_SOURCES.BOREHOLES ? (
                    <BoreholeSelector
                        boreholes={boreholes}
                        selected={selectedBoreholes}
                        onSelectionChange={setSelectedBoreholes}
                    />
                ) : (
                    <FileDropzone
                        accept={config.accept}
                        onFileSelect={handleFileSelect}
                        uploading={importing}
                    />
                )}
            </div>

            {/* File Preview */}
            {preview && (
                <div className="preview-section">
                    <h4>Preview</h4>
                    <div className="preview-info">
                        <span>File: {preview.filename}</span>
                        <span>Size: {(preview.size / 1024).toFixed(1)} KB</span>
                    </div>
                    <pre className="preview-sample">
                        {preview.sample?.join('\n')}
                    </pre>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="error-message">
                    <AlertCircle size={16} />
                    <span>{error}</span>
                </div>
            )}

            {/* Result Display */}
            {result && (
                <div className="success-message">
                    <Check size={16} />
                    <div>
                        <strong>Surface Created!</strong>
                        <span>{result.vertex_count} vertices, {result.triangle_count} triangles</span>
                    </div>
                </div>
            )}

            {/* Import Button */}
            <button
                className="import-button"
                onClick={handleImport}
                disabled={importing || (!file && source !== IMPORT_SOURCES.BOREHOLES) ||
                    (source === IMPORT_SOURCES.BOREHOLES && selectedBoreholes.length < 3)}
            >
                {importing ? (
                    <>
                        <Loader2 size={18} className="spin" />
                        Importing...
                    </>
                ) : (
                    <>
                        <Mountain size={18} />
                        Create Terrain Surface
                    </>
                )}
            </button>

            <style jsx>{`
                .terrain-import-panel {
                    background: #1a1a2e;
                    border-radius: 12px;
                    padding: 24px;
                    color: #e0e0e0;
                }
                
                .panel-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                }
                
                .panel-header h3 {
                    margin: 0;
                    font-size: 1.2rem;
                }
                
                .source-tabs {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                }
                
                .source-tab {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 10px 16px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 8px;
                    color: #a0a0c0;
                    cursor: pointer;
                    transition: all 0.2s;
                    flex: 1;
                    justify-content: center;
                }
                
                .source-tab:hover {
                    background: #3a3a5a;
                }
                
                .source-tab.active {
                    background: #4040a0;
                    border-color: #6060c0;
                    color: #fff;
                }
                
                .source-description {
                    color: #8080a0;
                    font-size: 0.9rem;
                    margin-bottom: 20px;
                }
                
                .input-group {
                    margin-bottom: 20px;
                }
                
                .input-group label {
                    display: block;
                    margin-bottom: 6px;
                    font-size: 0.9rem;
                    color: #a0a0c0;
                }
                
                .input-group input {
                    width: 100%;
                    padding: 10px 12px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 8px;
                    color: #e0e0e0;
                    font-size: 0.95rem;
                }
                
                .source-content {
                    margin-bottom: 20px;
                }
                
                .preview-section {
                    background: #2a2a4a;
                    border-radius: 8px;
                    padding: 14px;
                    margin-bottom: 20px;
                }
                
                .preview-section h4 {
                    margin: 0 0 10px 0;
                    font-size: 0.9rem;
                    color: #a0a0c0;
                }
                
                .preview-info {
                    display: flex;
                    gap: 16px;
                    font-size: 0.8rem;
                    color: #6060a0;
                    margin-bottom: 10px;
                }
                
                .preview-sample {
                    background: #1a1a2e;
                    padding: 10px;
                    border-radius: 6px;
                    font-size: 0.75rem;
                    overflow-x: auto;
                    margin: 0;
                    color: #8080a0;
                }
                
                .error-message {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 14px;
                    background: #4a2a2a;
                    border: 1px solid #6a3a3a;
                    border-radius: 8px;
                    color: #ff8080;
                    margin-bottom: 16px;
                }
                
                .success-message {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 14px;
                    background: #2a4a2a;
                    border: 1px solid #3a6a3a;
                    border-radius: 8px;
                    color: #80ff80;
                    margin-bottom: 16px;
                }
                
                .success-message div {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                }
                
                .success-message span {
                    font-size: 0.85rem;
                    color: #60c060;
                }
                
                .import-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    width: 100%;
                    padding: 14px;
                    background: linear-gradient(135deg, #4040a0, #6060c0);
                    border: none;
                    border-radius: 8px;
                    color: #fff;
                    font-size: 1rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .import-button:hover:not(:disabled) {
                    background: linear-gradient(135deg, #5050b0, #7070d0);
                }
                
                .import-button:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                .spin {
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export default TerrainImportPanel;
