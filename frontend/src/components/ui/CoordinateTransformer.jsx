/**
 * CoordinateTransformer.jsx - Batch Coordinate Transformation Tool
 * 
 * Modal component for transforming coordinates between CRS systems.
 * Features:
 * - Single point transformation
 * - Batch transformation from file upload
 * - Copy/paste coordinate input
 * - Preview before/after
 * - Export transformed data
 */

import React, { useState, useCallback } from 'react';
import {
    ArrowRight, Upload, Download, Copy, Check, X,
    RefreshCw, FileText, AlertCircle, MapPin
} from 'lucide-react';

/**
 * Format number to fixed decimal places
 */
const formatCoord = (value, decimals = 3) => {
    if (value === null || value === undefined || isNaN(value)) return '-';
    return Number(value).toFixed(decimals);
};

/**
 * Main Coordinate Transformer Component
 */
function CoordinateTransformer({
    isOpen,
    onClose,
    defaultFromEpsg = 4326,
    defaultToEpsg = 2052,
    siteId
}) {
    // State
    const [mode, setMode] = useState('single'); // 'single' or 'batch'
    const [fromEpsg, setFromEpsg] = useState(defaultFromEpsg);
    const [toEpsg, setToEpsg] = useState(defaultToEpsg);
    const [systems, setSystems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [copied, setCopied] = useState(false);

    // Single point state
    const [inputX, setInputX] = useState('');
    const [inputY, setInputY] = useState('');
    const [inputZ, setInputZ] = useState('0');
    const [result, setResult] = useState(null);

    // Batch state
    const [batchInput, setBatchInput] = useState('');
    const [batchResults, setBatchResults] = useState([]);
    const [fileData, setFileData] = useState(null);

    // CRS info
    const [fromCrsInfo, setFromCrsInfo] = useState(null);
    const [toCrsInfo, setToCrsInfo] = useState(null);

    // Fetch CRS systems on mount
    React.useEffect(() => {
        if (isOpen) {
            fetchSystems();
            fetchCrsInfo(fromEpsg, 'from');
            fetchCrsInfo(toEpsg, 'to');
        }
    }, [isOpen, fromEpsg, toEpsg]);

    const fetchSystems = async () => {
        try {
            const response = await fetch('/api/crs/systems');
            if (response.ok) {
                setSystems(await response.json());
            }
        } catch (e) {
            console.error('Failed to fetch CRS systems:', e);
        }
    };

    const fetchCrsInfo = async (epsg, which) => {
        try {
            const response = await fetch(`/api/crs/${epsg}/info`);
            if (response.ok) {
                const data = await response.json();
                if (which === 'from') setFromCrsInfo(data);
                else setToCrsInfo(data);
            }
        } catch (e) {
            console.error(`Failed to fetch ${which} CRS info:`, e);
        }
    };

    // Transform single point
    const transformPoint = async () => {
        if (!inputX || !inputY) {
            setError('Please enter X and Y coordinates');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const url = `/api/crs/transform-point?x=${inputX}&y=${inputY}&z=${inputZ || 0}&from_epsg=${fromEpsg}&to_epsg=${toEpsg}`;
            const response = await fetch(url, { method: 'POST' });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Transform failed');
            }

            const data = await response.json();
            setResult(data.transformed);
        } catch (e) {
            setError(e.message);
        }

        setLoading(false);
    };

    // Transform batch points
    const transformBatch = async () => {
        if (!batchInput.trim()) {
            setError('Please enter coordinates or upload a file');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Parse input lines
            const lines = batchInput.trim().split('\n');
            const points = lines.map((line, idx) => {
                const parts = line.split(/[,\s\t]+/).map(p => parseFloat(p.trim()));
                if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1])) {
                    throw new Error(`Invalid coordinates on line ${idx + 1}`);
                }
                return [parts[0], parts[1], parts[2] || 0];
            });

            const response = await fetch('/api/crs/transform', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    points,
                    from_epsg: fromEpsg,
                    to_epsg: toEpsg
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Transform failed');
            }

            const data = await response.json();
            setBatchResults(data.transformed_points.map((pt, i) => ({
                original: data.source_points[i],
                transformed: pt
            })));
        } catch (e) {
            setError(e.message);
        }

        setLoading(false);
    };

    // Handle file upload
    const handleFileUpload = useCallback((event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result;
            if (typeof text === 'string') {
                setBatchInput(text);
                setFileData({ name: file.name, size: file.size });
            }
        };
        reader.readAsText(file);
    }, []);

    // Copy results to clipboard
    const copyResults = () => {
        let text = '';
        if (mode === 'single' && result) {
            text = `${result.x},${result.y},${result.z}`;
        } else if (batchResults.length > 0) {
            text = batchResults.map(r =>
                `${formatCoord(r.transformed[0], 6)},${formatCoord(r.transformed[1], 6)},${formatCoord(r.transformed[2], 3)}`
            ).join('\n');
        }

        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Export as CSV
    const exportCSV = () => {
        if (batchResults.length === 0) return;

        const header = 'Original_X,Original_Y,Original_Z,Transformed_X,Transformed_Y,Transformed_Z\n';
        const rows = batchResults.map(r =>
            `${r.original[0]},${r.original[1]},${r.original[2]},${r.transformed[0]},${r.transformed[1]},${r.transformed[2]}`
        ).join('\n');

        const blob = new Blob([header + rows], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transformed_coordinates_epsg${toEpsg}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Swap CRS
    const swapCRS = () => {
        setFromEpsg(toEpsg);
        setToEpsg(fromEpsg);
        setResult(null);
        setBatchResults([]);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <MapPin size={24} />
                            <div>
                                <h2 className="text-lg font-semibold">Coordinate Transformer</h2>
                                <p className="text-sm opacity-80">Convert coordinates between coordinate systems</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Mode Tabs */}
                <div className="flex border-b">
                    <button
                        onClick={() => setMode('single')}
                        className={`flex-1 py-3 text-sm font-medium transition ${mode === 'single'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Single Point
                    </button>
                    <button
                        onClick={() => setMode('batch')}
                        className={`flex-1 py-3 text-sm font-medium transition ${mode === 'batch'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Batch / File
                    </button>
                </div>

                {/* CRS Selection */}
                <div className="px-6 py-4 bg-gray-50 border-b">
                    <div className="flex items-center gap-4">
                        {/* From CRS */}
                        <div className="flex-1">
                            <label className="block text-xs text-gray-500 mb-1">From Coordinate System</label>
                            <select
                                value={fromEpsg}
                                onChange={(e) => setFromEpsg(parseInt(e.target.value))}
                                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                            >
                                {systems.map(sys => (
                                    <option key={sys.epsg} value={sys.epsg}>
                                        EPSG:{sys.epsg} - {sys.name}
                                    </option>
                                ))}
                            </select>
                            {fromCrsInfo && (
                                <div className="text-xs text-gray-500 mt-1">
                                    {fromCrsInfo.region} • {fromCrsInfo.units}
                                </div>
                            )}
                        </div>

                        {/* Swap Button */}
                        <button
                            onClick={swapCRS}
                            className="p-2 bg-white border rounded-full hover:bg-gray-100 shadow-sm"
                            title="Swap coordinate systems"
                        >
                            <RefreshCw size={18} className="text-gray-600" />
                        </button>

                        {/* To CRS */}
                        <div className="flex-1">
                            <label className="block text-xs text-gray-500 mb-1">To Coordinate System</label>
                            <select
                                value={toEpsg}
                                onChange={(e) => setToEpsg(parseInt(e.target.value))}
                                className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                            >
                                {systems.map(sys => (
                                    <option key={sys.epsg} value={sys.epsg}>
                                        EPSG:{sys.epsg} - {sys.name}
                                    </option>
                                ))}
                            </select>
                            {toCrsInfo && (
                                <div className="text-xs text-gray-500 mt-1">
                                    {toCrsInfo.region} • {toCrsInfo.units}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6">
                    {/* Error Display */}
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                            <AlertCircle size={18} />
                            <span className="text-sm">{error}</span>
                        </div>
                    )}

                    {mode === 'single' ? (
                        /* Single Point Mode */
                        <div className="grid grid-cols-2 gap-6">
                            {/* Input */}
                            <div className="space-y-4">
                                <h3 className="font-medium text-gray-800">Input Coordinates</h3>
                                <div className="grid grid-cols-3 gap-3">
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">X / Easting</label>
                                        <input
                                            type="number"
                                            value={inputX}
                                            onChange={(e) => setInputX(e.target.value)}
                                            placeholder="0.000"
                                            className="w-full px-3 py-2 border rounded-lg text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">Y / Northing</label>
                                        <input
                                            type="number"
                                            value={inputY}
                                            onChange={(e) => setInputY(e.target.value)}
                                            placeholder="0.000"
                                            className="w-full px-3 py-2 border rounded-lg text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs text-gray-500 mb-1">Z / Elevation</label>
                                        <input
                                            type="number"
                                            value={inputZ}
                                            onChange={(e) => setInputZ(e.target.value)}
                                            placeholder="0.000"
                                            className="w-full px-3 py-2 border rounded-lg text-sm"
                                        />
                                    </div>
                                </div>
                                <button
                                    onClick={transformPoint}
                                    disabled={loading}
                                    className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <RefreshCw size={18} className="animate-spin" />
                                    ) : (
                                        <>
                                            <ArrowRight size={18} />
                                            Transform
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Output */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="font-medium text-gray-800">Transformed Coordinates</h3>
                                    {result && (
                                        <button
                                            onClick={copyResults}
                                            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                                        >
                                            {copied ? <Check size={14} /> : <Copy size={14} />}
                                            {copied ? 'Copied!' : 'Copy'}
                                        </button>
                                    )}
                                </div>
                                {result ? (
                                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                        <div className="grid grid-cols-3 gap-3">
                                            <div>
                                                <div className="text-xs text-gray-500">X / Easting</div>
                                                <div className="font-mono font-medium">{formatCoord(result.x, 3)}</div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-gray-500">Y / Northing</div>
                                                <div className="font-mono font-medium">{formatCoord(result.y, 3)}</div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-gray-500">Z / Elevation</div>
                                                <div className="font-mono font-medium">{formatCoord(result.z, 3)}</div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-4 bg-gray-100 border border-gray-200 rounded-lg text-gray-500 text-sm text-center">
                                        Enter coordinates and click Transform
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        /* Batch Mode */
                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <h3 className="font-medium text-gray-800">Input Coordinates</h3>
                                <label className="flex items-center gap-2 text-sm text-blue-600 cursor-pointer hover:text-blue-700">
                                    <Upload size={16} />
                                    Upload CSV
                                    <input
                                        type="file"
                                        accept=".csv,.txt"
                                        onChange={handleFileUpload}
                                        className="hidden"
                                    />
                                </label>
                                {fileData && (
                                    <span className="text-xs text-gray-500">
                                        <FileText size={12} className="inline mr-1" />
                                        {fileData.name}
                                    </span>
                                )}
                            </div>

                            <textarea
                                value={batchInput}
                                onChange={(e) => setBatchInput(e.target.value)}
                                placeholder="Enter coordinates, one per line:&#10;X,Y,Z&#10;X,Y,Z&#10;...or paste from Excel"
                                className="w-full h-40 px-3 py-2 border rounded-lg text-sm font-mono resize-none"
                            />

                            <button
                                onClick={transformBatch}
                                disabled={loading || !batchInput.trim()}
                                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <RefreshCw size={18} className="animate-spin" />
                                ) : (
                                    <>
                                        <ArrowRight size={18} />
                                        Transform All
                                    </>
                                )}
                            </button>

                            {/* Results Table */}
                            {batchResults.length > 0 && (
                                <div className="mt-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-medium text-gray-800">
                                            Results ({batchResults.length} points)
                                        </h3>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={copyResults}
                                                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                                            >
                                                {copied ? <Check size={14} /> : <Copy size={14} />}
                                                Copy
                                            </button>
                                            <button
                                                onClick={exportCSV}
                                                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                                            >
                                                <Download size={14} />
                                                Export CSV
                                            </button>
                                        </div>
                                    </div>
                                    <div className="border rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-100 sticky top-0">
                                                <tr>
                                                    <th className="px-3 py-2 text-left">#</th>
                                                    <th className="px-3 py-2 text-left">Original X</th>
                                                    <th className="px-3 py-2 text-left">Original Y</th>
                                                    <th className="px-3 py-2 text-left">New X</th>
                                                    <th className="px-3 py-2 text-left">New Y</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {batchResults.map((r, i) => (
                                                    <tr key={i} className="border-t hover:bg-gray-50">
                                                        <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                                                        <td className="px-3 py-2 font-mono">{formatCoord(r.original[0], 2)}</td>
                                                        <td className="px-3 py-2 font-mono">{formatCoord(r.original[1], 2)}</td>
                                                        <td className="px-3 py-2 font-mono text-green-700">{formatCoord(r.transformed[0], 3)}</td>
                                                        <td className="px-3 py-2 font-mono text-green-700">{formatCoord(r.transformed[1], 3)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

export default CoordinateTransformer;
