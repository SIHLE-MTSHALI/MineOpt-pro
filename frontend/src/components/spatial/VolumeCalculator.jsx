/**
 * VolumeCalculator.jsx - Volume and Tonnage Calculation UI
 * 
 * Provides UI for calculating:
 * - Seam Reserves (coal tonnage between roof/floor)
 * - Cut/Fill (earthworks between design and existing)
 * - Ramp Design volumes
 * - Dump Capacity estimates
 */

import React, { useState, useEffect } from 'react';
import {
    Calculator,
    Layers,
    Mountain,
    TrendingUp,
    Download,
    RefreshCw,
    ChevronDown,
    Info,
    AlertCircle
} from 'lucide-react';

// Calculation modes
const MODES = {
    SEAM_RESERVES: 'seam_reserves',
    CUT_FILL: 'cut_fill',
    RAMP_DESIGN: 'ramp_design',
    DUMP_CAPACITY: 'dump_capacity'
};

const MODE_CONFIG = {
    [MODES.SEAM_RESERVES]: {
        label: 'Seam Reserves',
        icon: Layers,
        description: 'Calculate coal tonnage between seam roof and floor surfaces',
        upperLabel: 'Seam Roof Surface',
        lowerLabel: 'Seam Floor Surface',
        showDensity: true,
        showMiningLoss: true,
        showYield: true,
        defaultDensity: 1.4
    },
    [MODES.CUT_FILL]: {
        label: 'Cut/Fill',
        icon: Mountain,
        description: 'Calculate earthwork volumes between design and existing terrain',
        upperLabel: 'Existing Surface',
        lowerLabel: 'Design Surface',
        showDensity: true,
        showSwellFactor: true,
        defaultDensity: 1.8
    },
    [MODES.RAMP_DESIGN]: {
        label: 'Ramp Design',
        icon: TrendingUp,
        description: 'Calculate ramp excavation and construction volumes',
        upperLabel: 'Terrain Surface',
        lowerLabel: 'Ramp Design Surface',
        showDensity: true,
        showSwellFactor: true,
        defaultDensity: 1.8
    },
    [MODES.DUMP_CAPACITY]: {
        label: 'Dump Capacity',
        icon: Mountain,
        description: 'Estimate waste dump storage capacity',
        upperLabel: 'Dump Design Surface',
        lowerLabel: 'Base Surface',
        showDensity: true,
        showSwellFactor: true,
        defaultDensity: 1.6
    }
};

/**
 * Format large numbers with appropriate units
 */
const formatNumber = (value, decimals = 2) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(decimals)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(decimals)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(decimals)}K`;
    return value.toFixed(decimals);
};

/**
 * Surface selector dropdown
 */
const SurfaceSelector = ({ label, surfaces, value, onChange, placeholder }) => {
    return (
        <div className="surface-selector">
            <label className="selector-label">{label}</label>
            <div className="selector-wrapper">
                <select
                    value={value || ''}
                    onChange={(e) => onChange(e.target.value)}
                    className="selector-dropdown"
                >
                    <option value="">{placeholder || 'Select surface...'}</option>
                    {surfaces.map(s => (
                        <option key={s.surface_id} value={s.surface_id}>
                            {s.name} ({s.surface_type})
                        </option>
                    ))}
                </select>
                <ChevronDown className="selector-icon" size={16} />
            </div>
        </div>
    );
};

/**
 * Result card for displaying calculation results
 */
const ResultCard = ({ label, value, unit, highlight = false }) => {
    return (
        <div className={`result-card ${highlight ? 'highlight' : ''}`}>
            <div className="result-label">{label}</div>
            <div className="result-value">
                {formatNumber(value)}
                <span className="result-unit">{unit}</span>
            </div>
        </div>
    );
};

/**
 * Main VolumeCalculator component
 */
const VolumeCalculator = ({
    surfaces = [],
    onCalculate,
    onExport,
    siteId
}) => {
    const [mode, setMode] = useState(MODES.SEAM_RESERVES);
    const [upperSurfaceId, setUpperSurfaceId] = useState('');
    const [lowerSurfaceId, setLowerSurfaceId] = useState('');
    const [density, setDensity] = useState(1.4);
    const [swellFactor, setSwellFactor] = useState(1.3);
    const [miningLoss, setMiningLoss] = useState(5);
    const [yieldPct, setYieldPct] = useState(85);
    const [gridSpacing, setGridSpacing] = useState(5);
    const [calculating, setCalculating] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const config = MODE_CONFIG[mode];

    // Reset parameters when mode changes
    useEffect(() => {
        setResult(null);
        setError(null);
        setDensity(config.defaultDensity);
    }, [mode, config.defaultDensity]);

    // Filter surfaces based on mode
    const upperSurfaces = surfaces.filter(s => {
        if (mode === MODES.SEAM_RESERVES) return s.surface_type === 'seam_roof' || s.surface_type === 'terrain';
        if (mode === MODES.CUT_FILL) return s.surface_type === 'terrain';
        if (mode === MODES.RAMP_DESIGN) return s.surface_type === 'terrain';
        if (mode === MODES.DUMP_CAPACITY) return s.surface_type === 'dump_design';
        return true;
    });

    const lowerSurfaces = surfaces.filter(s => {
        if (mode === MODES.SEAM_RESERVES) return s.surface_type === 'seam_floor';
        if (mode === MODES.CUT_FILL) return s.surface_type === 'pit_design' || s.surface_type === 'design';
        if (mode === MODES.RAMP_DESIGN) return s.surface_type === 'ramp_design';
        if (mode === MODES.DUMP_CAPACITY) return s.surface_type === 'terrain';
        return true;
    });

    const handleCalculate = async () => {
        if (!upperSurfaceId || !lowerSurfaceId) {
            setError('Please select both surfaces');
            return;
        }

        setCalculating(true);
        setError(null);

        try {
            let endpoint, body;

            if (mode === MODES.SEAM_RESERVES) {
                endpoint = '/api/surfaces/seam-tonnage';
                body = {
                    roof_surface_id: upperSurfaceId,
                    floor_surface_id: lowerSurfaceId,
                    density_t_m3: density,
                    mining_loss_pct: miningLoss,
                    yield_pct: yieldPct,
                    grid_spacing: gridSpacing
                };
            } else {
                endpoint = '/api/surfaces/volume-between';
                body = {
                    upper_surface_id: upperSurfaceId,
                    lower_surface_id: lowerSurfaceId,
                    density_t_m3: density,
                    swell_factor: swellFactor,
                    grid_spacing: gridSpacing
                };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Calculation failed');
            }

            const data = await response.json();
            setResult({ ...data, mode });

            if (onCalculate) {
                onCalculate(data);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setCalculating(false);
        }
    };

    const handleExport = () => {
        if (!result) return;

        // Create CSV report
        const lines = [
            'MineOpt Pro Volume Calculation Report',
            `Mode: ${config.label}`,
            `Date: ${new Date().toISOString()}`,
            '',
            'Parameters:',
            `Upper Surface: ${upperSurfaceId}`,
            `Lower Surface: ${lowerSurfaceId}`,
            `Density: ${density} t/m³`,
            `Grid Spacing: ${gridSpacing} m`,
            '',
            'Results:'
        ];

        if (mode === MODES.SEAM_RESERVES) {
            lines.push(`In-situ Tonnes: ${result.in_situ_tonnes?.toFixed(2)}`);
            lines.push(`ROM Tonnes: ${result.rom_tonnes?.toFixed(2)}`);
            lines.push(`Product Tonnes: ${result.product_tonnes?.toFixed(2)}`);
            lines.push(`Average Thickness: ${result.thickness_avg?.toFixed(2)} m`);
        } else {
            lines.push(`Total Volume: ${result.volume_m3?.toFixed(2)} m³`);
            lines.push(`Cut Volume: ${result.cut_volume?.toFixed(2)} m³`);
            lines.push(`Fill Volume: ${result.fill_volume?.toFixed(2)} m³`);
            lines.push(`Tonnage: ${result.tonnage?.toFixed(2)} t`);
        }

        const csv = lines.join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `volume_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="volume-calculator">
            <div className="calculator-header">
                <Calculator size={24} />
                <h3>Volume & Tonnage Calculator</h3>
            </div>

            {/* Mode Selector */}
            <div className="mode-selector">
                {Object.entries(MODE_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    return (
                        <button
                            key={key}
                            className={`mode-button ${mode === key ? 'active' : ''}`}
                            onClick={() => setMode(key)}
                            title={cfg.description}
                        >
                            <Icon size={18} />
                            <span>{cfg.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Mode Description */}
            <div className="mode-description">
                <Info size={16} />
                <span>{config.description}</span>
            </div>

            {/* Surface Selection */}
            <div className="surface-selection">
                <SurfaceSelector
                    label={config.upperLabel}
                    surfaces={upperSurfaces.length > 0 ? upperSurfaces : surfaces}
                    value={upperSurfaceId}
                    onChange={setUpperSurfaceId}
                />

                <SurfaceSelector
                    label={config.lowerLabel}
                    surfaces={lowerSurfaces.length > 0 ? lowerSurfaces : surfaces}
                    value={lowerSurfaceId}
                    onChange={setLowerSurfaceId}
                />
            </div>

            {/* Parameters */}
            <div className="parameters-section">
                <h4>Parameters</h4>

                <div className="parameter-grid">
                    {config.showDensity && (
                        <div className="parameter">
                            <label>Density (t/m³)</label>
                            <input
                                type="number"
                                step="0.1"
                                min="0.1"
                                max="5"
                                value={density}
                                onChange={(e) => setDensity(parseFloat(e.target.value) || 1.4)}
                            />
                        </div>
                    )}

                    {config.showSwellFactor && (
                        <div className="parameter">
                            <label>Swell Factor</label>
                            <input
                                type="number"
                                step="0.1"
                                min="1"
                                max="2"
                                value={swellFactor}
                                onChange={(e) => setSwellFactor(parseFloat(e.target.value) || 1.3)}
                            />
                        </div>
                    )}

                    {config.showMiningLoss && (
                        <div className="parameter">
                            <label>Mining Loss (%)</label>
                            <input
                                type="number"
                                step="1"
                                min="0"
                                max="50"
                                value={miningLoss}
                                onChange={(e) => setMiningLoss(parseFloat(e.target.value) || 5)}
                            />
                        </div>
                    )}

                    {config.showYield && (
                        <div className="parameter">
                            <label>Yield (%)</label>
                            <input
                                type="number"
                                step="1"
                                min="0"
                                max="100"
                                value={yieldPct}
                                onChange={(e) => setYieldPct(parseFloat(e.target.value) || 85)}
                            />
                        </div>
                    )}

                    <div className="parameter">
                        <label>Grid Spacing (m)</label>
                        <input
                            type="number"
                            step="1"
                            min="1"
                            max="50"
                            value={gridSpacing}
                            onChange={(e) => setGridSpacing(parseFloat(e.target.value) || 5)}
                        />
                    </div>
                </div>
            </div>

            {/* Calculate Button */}
            <button
                className="calculate-button"
                onClick={handleCalculate}
                disabled={calculating || !upperSurfaceId || !lowerSurfaceId}
            >
                {calculating ? (
                    <>
                        <RefreshCw size={18} className="spin" />
                        Calculating...
                    </>
                ) : (
                    <>
                        <Calculator size={18} />
                        Calculate
                    </>
                )}
            </button>

            {/* Error Display */}
            {error && (
                <div className="error-message">
                    <AlertCircle size={16} />
                    <span>{error}</span>
                </div>
            )}

            {/* Results */}
            {result && (
                <div className="results-section">
                    <div className="results-header">
                        <h4>Results</h4>
                        <button className="export-button" onClick={handleExport}>
                            <Download size={16} />
                            Export
                        </button>
                    </div>

                    <div className="results-grid">
                        {mode === MODES.SEAM_RESERVES ? (
                            <>
                                <ResultCard
                                    label="In-situ Tonnes"
                                    value={result.in_situ_tonnes || 0}
                                    unit="t"
                                />
                                <ResultCard
                                    label="ROM Tonnes"
                                    value={result.rom_tonnes || 0}
                                    unit="t"
                                />
                                <ResultCard
                                    label="Product Tonnes"
                                    value={result.product_tonnes || 0}
                                    unit="t"
                                    highlight
                                />
                                <ResultCard
                                    label="Avg Thickness"
                                    value={result.thickness_avg || 0}
                                    unit="m"
                                />
                                <ResultCard
                                    label="Area"
                                    value={result.area_m2 || 0}
                                    unit="m²"
                                />
                                <ResultCard
                                    label="Volume"
                                    value={result.volume_m3 || 0}
                                    unit="m³"
                                />
                            </>
                        ) : (
                            <>
                                <ResultCard
                                    label="Total Volume"
                                    value={result.volume_m3 || 0}
                                    unit="m³"
                                    highlight
                                />
                                <ResultCard
                                    label="Cut Volume"
                                    value={result.cut_volume || 0}
                                    unit="m³"
                                />
                                <ResultCard
                                    label="Fill Volume"
                                    value={result.fill_volume || 0}
                                    unit="m³"
                                />
                                <ResultCard
                                    label="Net Volume"
                                    value={result.net_volume || 0}
                                    unit="m³"
                                />
                                <ResultCard
                                    label="Tonnage"
                                    value={result.tonnage || 0}
                                    unit="t"
                                />
                                <ResultCard
                                    label="Area"
                                    value={result.area_m2 || 0}
                                    unit="m²"
                                />
                            </>
                        )}
                    </div>
                </div>
            )}

            <style jsx>{`
                .volume-calculator {
                    background: #1a1a2e;
                    border-radius: 12px;
                    padding: 20px;
                    color: #e0e0e0;
                }
                
                .calculator-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                }
                
                .calculator-header h3 {
                    margin: 0;
                    font-size: 1.2rem;
                }
                
                .mode-selector {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                    flex-wrap: wrap;
                }
                
                .mode-button {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 8px 12px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 8px;
                    color: #a0a0c0;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-size: 0.85rem;
                }
                
                .mode-button:hover {
                    background: #3a3a5a;
                }
                
                .mode-button.active {
                    background: #4040a0;
                    border-color: #6060c0;
                    color: #fff;
                }
                
                .mode-description {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 14px;
                    background: #2a2a4a;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    font-size: 0.85rem;
                    color: #8080a0;
                }
                
                .surface-selection {
                    display: grid;
                    gap: 16px;
                    margin-bottom: 20px;
                }
                
                .surface-selector {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                
                .selector-label {
                    font-size: 0.85rem;
                    color: #a0a0c0;
                }
                
                .selector-wrapper {
                    position: relative;
                }
                
                .selector-dropdown {
                    width: 100%;
                    padding: 10px 36px 10px 12px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 8px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                    appearance: none;
                    cursor: pointer;
                }
                
                .selector-icon {
                    position: absolute;
                    right: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    pointer-events: none;
                    color: #6060a0;
                }
                
                .parameters-section {
                    margin-bottom: 20px;
                }
                
                .parameters-section h4 {
                    margin: 0 0 12px 0;
                    font-size: 0.95rem;
                    color: #a0a0c0;
                }
                
                .parameter-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
                    gap: 12px;
                }
                
                .parameter {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                
                .parameter label {
                    font-size: 0.8rem;
                    color: #8080a0;
                }
                
                .parameter input {
                    padding: 8px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 0.9rem;
                }
                
                .calculate-button {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #4040a0, #6060c0);
                    border: none;
                    border-radius: 8px;
                    color: #fff;
                    font-size: 1rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .calculate-button:hover:not(:disabled) {
                    background: linear-gradient(135deg, #5050b0, #7070d0);
                }
                
                .calculate-button:disabled {
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
                
                .error-message {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-top: 12px;
                    padding: 10px 14px;
                    background: #4a2a2a;
                    border: 1px solid #6a3a3a;
                    border-radius: 8px;
                    color: #ff8080;
                    font-size: 0.85rem;
                }
                
                .results-section {
                    margin-top: 24px;
                    padding-top: 20px;
                    border-top: 1px solid #3a3a5a;
                }
                
                .results-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }
                
                .results-header h4 {
                    margin: 0;
                    color: #a0a0c0;
                }
                
                .export-button {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 6px;
                    color: #a0a0c0;
                    font-size: 0.8rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .export-button:hover {
                    background: #3a3a5a;
                    color: #e0e0e0;
                }
                
                .results-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
                    gap: 12px;
                }
                
                .result-card {
                    background: #2a2a4a;
                    border: 1px solid #3a3a5a;
                    border-radius: 10px;
                    padding: 14px;
                    text-align: center;
                }
                
                .result-card.highlight {
                    background: linear-gradient(135deg, #2a3a5a, #3a4a6a);
                    border-color: #4a5a7a;
                }
                
                .result-label {
                    font-size: 0.75rem;
                    color: #8080a0;
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .result-value {
                    font-size: 1.3rem;
                    font-weight: 600;
                    color: #e0e0e0;
                }
                
                .result-unit {
                    font-size: 0.75rem;
                    color: #8080a0;
                    margin-left: 4px;
                    font-weight: 400;
                }
            `}</style>
        </div>
    );
};

export default VolumeCalculator;
