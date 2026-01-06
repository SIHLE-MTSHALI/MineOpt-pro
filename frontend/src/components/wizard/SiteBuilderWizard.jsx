/**
 * SiteBuilderWizard (Full 7-Step) - Phase 4 Site Builder UI
 * 
 * Per implementation plan WP-UI5: 7-step wizard for site creation.
 * 
 * Steps:
 * 1. Upload files (collar, survey, assay, geometry)
 * 2. Map columns to fields
 * 3. Preview in 3D
 * 4. Configure block model grid
 * 5. Run estimation (Kriging/IDW)
 * 6. Create activity areas
 * 7. Confirm and save site
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
    ChevronLeft,
    ChevronRight,
    Check,
    Upload,
    Columns,
    Eye,
    Grid3X3,
    Zap,
    MapPin,
    Save,
    Loader2,
    AlertCircle,
    CheckCircle
} from 'lucide-react';
import FileUploader from '../import/FileUploader';
import ColumnMapper from '../import/ColumnMapper';

const STEPS = [
    {
        id: 'upload',
        title: 'Upload Files',
        description: 'Load borehole and geometry files',
        icon: Upload
    },
    {
        id: 'mapping',
        title: 'Map Columns',
        description: 'Configure field mappings',
        icon: Columns
    },
    {
        id: 'preview',
        title: '3D Preview',
        description: 'Visualize imported data',
        icon: Eye
    },
    {
        id: 'grid',
        title: 'Block Grid',
        description: 'Define block model parameters',
        icon: Grid3X3
    },
    {
        id: 'estimate',
        title: 'Estimation',
        description: 'Run grade estimation',
        icon: Zap
    },
    {
        id: 'areas',
        title: 'Activity Areas',
        description: 'Create mining areas from blocks',
        icon: MapPin
    },
    {
        id: 'confirm',
        title: 'Save Site',
        description: 'Review and confirm',
        icon: Save
    },
];

const SiteBuilderWizard = ({
    siteId,
    siteName = "New Site",
    onComplete,
    onCancel
}) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [stepStatus, setStepStatus] = useState({});

    // Wizard state
    const [files, setFiles] = useState({
        collar: null,
        survey: null,
        assay: null,
        dxf: null
    });
    const [parsedData, setParsedData] = useState({});
    const [mappings, setMappings] = useState({});
    const [importResult, setImportResult] = useState(null);

    // Block model config
    const [blockConfig, setBlockConfig] = useState({
        name: `${siteName}_BlockModel`,
        blockSizeX: 10,
        blockSizeY: 10,
        blockSizeZ: 5,
        padding: 50
    });

    // Estimation config
    const [estimationConfig, setEstimationConfig] = useState({
        qualityField: '',
        method: 'kriging',
        variogramModel: 'spherical',
        autoFit: true,
        maxSamples: 20,
        minSamples: 3
    });
    const [estimationResult, setEstimationResult] = useState(null);

    // Activity area config
    const [areaConfig, setAreaConfig] = useState({
        minValue: 20,
        maxValue: null,
        activityType: 'Coal Mining',
        autoGenerate: true
    });
    const [areasCreated, setAreasCreated] = useState([]);

    // Mark step as complete
    const markStepComplete = (stepId) => {
        setStepStatus(prev => ({ ...prev, [stepId]: 'complete' }));
    };

    // Handle file parsed
    const handleFileParsed = useCallback((file, data, format) => {
        let fileType = format;
        if (format === 'csv' || format === 'txt') {
            fileType = data.inferred_purpose || 'collar';
        }

        setFiles(prev => ({ ...prev, [fileType]: file }));
        setParsedData(prev => ({ ...prev, [fileType]: data }));
    }, []);

    // API calls for each step
    const importBoreholes = async () => {
        const formData = new FormData();
        formData.append('site_id', siteId);
        formData.append('collar_file', files.collar);
        formData.append('collar_mappings', JSON.stringify(mappings.collar?.mappings || {}));

        if (files.survey) {
            formData.append('survey_file', files.survey);
            formData.append('survey_mappings', JSON.stringify(mappings.survey?.mappings || {}));
        }
        if (files.assay) {
            formData.append('assay_file', files.assay);
            formData.append('assay_mappings', JSON.stringify(mappings.assay?.mappings || {}));
            formData.append('quality_columns', JSON.stringify(mappings.assay?.qualityColumns || []));
        }

        const response = await fetch('/api/boreholes/import', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Borehole import failed');
        return await response.json();
    };

    const createBlockModel = async (collarIds) => {
        const response = await fetch('/api/blockmodels', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                site_id: siteId,
                name: blockConfig.name,
                collar_ids: collarIds,
                block_size_x: blockConfig.blockSizeX,
                block_size_y: blockConfig.blockSizeY,
                block_size_z: blockConfig.blockSizeZ,
                padding: blockConfig.padding
            })
        });

        if (!response.ok) throw new Error('Block model creation failed');
        return await response.json();
    };

    const runEstimation = async (modelId, collarIds) => {
        const response = await fetch(`/api/blockmodels/${modelId}/estimate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                collar_ids: collarIds,
                quality_field: estimationConfig.qualityField,
                method: estimationConfig.method,
                variogram_model: estimationConfig.variogramModel,
                auto_fit_variogram: estimationConfig.autoFit,
                max_samples: estimationConfig.maxSamples,
                min_samples: estimationConfig.minSamples,
                run_cross_validation: true
            })
        });

        if (!response.ok) throw new Error('Estimation failed');
        return await response.json();
    };

    const createActivityAreas = async (modelId) => {
        const params = new URLSearchParams({
            min_value: areaConfig.minValue,
            activity_type: areaConfig.activityType
        });
        if (areaConfig.maxValue) {
            params.append('max_value', areaConfig.maxValue);
        }

        const response = await fetch(`/api/blockmodels/${modelId}/activity-areas?${params}`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Activity area creation failed');
        return await response.json();
    };

    // Step handlers
    const handleStep = async () => {
        setIsProcessing(true);
        setError(null);

        try {
            switch (currentStep) {
                case 0: // Upload - just validate files exist
                    if (!files.collar) throw new Error('Collar file is required');
                    markStepComplete('upload');
                    break;

                case 1: // Mapping - validate mappings
                    if (!mappings.collar?.mappings?.HoleID) throw new Error('HoleID mapping required');
                    if (!mappings.collar?.mappings?.Easting) throw new Error('Easting mapping required');
                    markStepComplete('mapping');
                    break;

                case 2: // Preview - import boreholes
                    const result = await importBoreholes();
                    setImportResult(result);
                    markStepComplete('preview');
                    break;

                case 3: // Grid - create block model
                    if (!importResult?.collar_ids?.length) throw new Error('No boreholes imported');
                    const modelResult = await createBlockModel(importResult.collar_ids);
                    setBlockConfig(prev => ({ ...prev, modelId: modelResult.model_id }));
                    markStepComplete('grid');
                    break;

                case 4: // Estimation - run kriging/IDW
                    if (!estimationConfig.qualityField) throw new Error('Select a quality field');
                    const estResult = await runEstimation(blockConfig.modelId, importResult.collar_ids);
                    setEstimationResult(estResult);
                    markStepComplete('estimate');
                    break;

                case 5: // Activity areas
                    if (areaConfig.autoGenerate) {
                        const areas = await createActivityAreas(blockConfig.modelId);
                        setAreasCreated(areas.activity_area_ids || []);
                    }
                    markStepComplete('areas');
                    break;

                case 6: // Confirm - finalize
                    markStepComplete('confirm');
                    if (onComplete) {
                        onComplete({
                            importResult,
                            modelId: blockConfig.modelId,
                            estimationResult,
                            areasCreated
                        });
                    }
                    break;
            }

            if (currentStep < STEPS.length - 1) {
                setCurrentStep(prev => prev + 1);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setIsProcessing(false);
        }
    };

    const goBack = () => {
        if (currentStep === 0) {
            onCancel?.();
        } else {
            setCurrentStep(prev => prev - 1);
            setError(null);
        }
    };

    // Can proceed check
    const canProceed = useMemo(() => {
        switch (currentStep) {
            case 0: return files.collar !== null;
            case 1: return mappings.collar?.mappings?.HoleID;
            case 2: return true;
            case 3: return importResult?.collar_ids?.length > 0;
            case 4: return estimationConfig.qualityField;
            case 5: return true;
            case 6: return true;
            default: return false;
        }
    }, [currentStep, files, mappings, importResult, estimationConfig]);

    // Render step content
    const renderStepContent = () => {
        switch (currentStep) {
            case 0: // Upload
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937', fontSize: '14px' }}>
                                Collar File <span style={{ color: '#EF4444' }}>*</span>
                            </h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Collar File"
                                description="HoleID, Easting, Northing, Elevation"
                                onFileParsed={(file, data) => {
                                    setFiles(prev => ({ ...prev, collar: file }));
                                    setParsedData(prev => ({ ...prev, collar: data }));
                                }}
                            />
                        </div>

                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937', fontSize: '14px' }}>
                                Survey File (optional)
                            </h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Survey File"
                                description="HoleID, Depth, Azimuth, Dip"
                                onFileParsed={(file, data) => {
                                    setFiles(prev => ({ ...prev, survey: file }));
                                    setParsedData(prev => ({ ...prev, survey: data }));
                                }}
                            />
                        </div>

                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937', fontSize: '14px' }}>
                                Assay/Quality File (optional)
                            </h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Assay File"
                                description="HoleID, From, To, Quality values"
                                onFileParsed={(file, data) => {
                                    setFiles(prev => ({ ...prev, assay: file }));
                                    setParsedData(prev => ({ ...prev, assay: data }));
                                }}
                            />
                        </div>

                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937', fontSize: '14px' }}>
                                Geometry File (optional)
                            </h3>
                            <FileUploader
                                acceptedFormats={['dxf', 'str']}
                                title="Upload Geometry"
                                description="DXF or Surpac .str file"
                                onFileParsed={(file, data, format) => {
                                    setFiles(prev => ({ ...prev, dxf: file }));
                                    setParsedData(prev => ({ ...prev, geometry: data }));
                                }}
                            />
                        </div>
                    </div>
                );

            case 1: // Mapping
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {parsedData.collar && (
                            <ColumnMapper
                                columns={parsedData.collar.columns || []}
                                previewRows={parsedData.collar.preview_rows || []}
                                fileType="collar"
                                onChange={(data) => setMappings(prev => ({ ...prev, collar: data }))}
                            />
                        )}
                        {parsedData.survey && (
                            <ColumnMapper
                                columns={parsedData.survey.columns || []}
                                previewRows={parsedData.survey.preview_rows || []}
                                fileType="survey"
                                onChange={(data) => setMappings(prev => ({ ...prev, survey: data }))}
                            />
                        )}
                        {parsedData.assay && (
                            <ColumnMapper
                                columns={parsedData.assay.columns || []}
                                previewRows={parsedData.assay.preview_rows || []}
                                fileType="assay"
                                onChange={(data) => setMappings(prev => ({ ...prev, assay: data }))}
                            />
                        )}
                    </div>
                );

            case 2: // 3D Preview
                return (
                    <div style={{
                        backgroundColor: '#1F2937',
                        borderRadius: '12px',
                        height: '400px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#9CA3AF'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <Eye size={48} style={{ marginBottom: '12px', opacity: 0.5 }} />
                            <div>3D Borehole Preview</div>
                            <div style={{ fontSize: '12px', marginTop: '4px' }}>
                                Click Next to import and visualize
                            </div>
                            {importResult && (
                                <div style={{ color: '#10B981', marginTop: '16px' }}>
                                    ✓ {importResult.collars_imported} boreholes imported
                                </div>
                            )}
                        </div>
                    </div>
                );

            case 3: // Block Grid Config
                return (
                    <div style={{ backgroundColor: '#FFF', borderRadius: '12px', padding: '20px' }}>
                        <h3 style={{ marginBottom: '16px', color: '#1F2937' }}>Block Model Grid</h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Model Name</label>
                                <input
                                    type="text"
                                    value={blockConfig.name}
                                    onChange={e => setBlockConfig(prev => ({ ...prev, name: e.target.value }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Padding (m)</label>
                                <input
                                    type="number"
                                    value={blockConfig.padding}
                                    onChange={e => setBlockConfig(prev => ({ ...prev, padding: parseFloat(e.target.value) }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Block Size X (m)</label>
                                <input
                                    type="number"
                                    value={blockConfig.blockSizeX}
                                    onChange={e => setBlockConfig(prev => ({ ...prev, blockSizeX: parseFloat(e.target.value) }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Block Size Y (m)</label>
                                <input
                                    type="number"
                                    value={blockConfig.blockSizeY}
                                    onChange={e => setBlockConfig(prev => ({ ...prev, blockSizeY: parseFloat(e.target.value) }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Block Size Z (m)</label>
                                <input
                                    type="number"
                                    value={blockConfig.blockSizeZ}
                                    onChange={e => setBlockConfig(prev => ({ ...prev, blockSizeZ: parseFloat(e.target.value) }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                />
                            </div>
                        </div>
                    </div>
                );

            case 4: // Estimation
                return (
                    <div style={{ backgroundColor: '#FFF', borderRadius: '12px', padding: '20px' }}>
                        <h3 style={{ marginBottom: '16px', color: '#1F2937' }}>Grade Estimation</h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Quality Field</label>
                                <select
                                    value={estimationConfig.qualityField}
                                    onChange={e => setEstimationConfig(prev => ({ ...prev, qualityField: e.target.value }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                >
                                    <option value="">-- Select --</option>
                                    {mappings.assay?.qualityColumns?.map(col => (
                                        <option key={col} value={col}>{col}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Method</label>
                                <select
                                    value={estimationConfig.method}
                                    onChange={e => setEstimationConfig(prev => ({ ...prev, method: e.target.value }))}
                                    style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                >
                                    <option value="kriging">Ordinary Kriging</option>
                                    <option value="idw">Inverse Distance Weighting</option>
                                </select>
                            </div>

                            {estimationConfig.method === 'kriging' && (
                                <>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Variogram Model</label>
                                        <select
                                            value={estimationConfig.variogramModel}
                                            onChange={e => setEstimationConfig(prev => ({ ...prev, variogramModel: e.target.value }))}
                                            style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                        >
                                            <option value="spherical">Spherical</option>
                                            <option value="exponential">Exponential</option>
                                            <option value="gaussian">Gaussian</option>
                                        </select>
                                    </div>

                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <input
                                            type="checkbox"
                                            checked={estimationConfig.autoFit}
                                            onChange={e => setEstimationConfig(prev => ({ ...prev, autoFit: e.target.checked }))}
                                        />
                                        <label style={{ fontSize: '13px' }}>Auto-fit variogram</label>
                                    </div>
                                </>
                            )}
                        </div>

                        {estimationResult && (
                            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#ECFDF5', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 500, color: '#065F46' }}>✓ Estimation Complete</div>
                                <div style={{ fontSize: '12px', color: '#047857', marginTop: '4px' }}>
                                    {estimationResult.blocks_estimated} blocks estimated
                                    {estimationResult.cv_rmse && ` • RMSE: ${estimationResult.cv_rmse.toFixed(2)}`}
                                </div>
                            </div>
                        )}
                    </div>
                );

            case 5: // Activity Areas  
                return (
                    <div style={{ backgroundColor: '#FFF', borderRadius: '12px', padding: '20px' }}>
                        <h3 style={{ marginBottom: '16px', color: '#1F2937' }}>Activity Areas</h3>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                            <input
                                type="checkbox"
                                checked={areaConfig.autoGenerate}
                                onChange={e => setAreaConfig(prev => ({ ...prev, autoGenerate: e.target.checked }))}
                            />
                            <label style={{ fontSize: '14px' }}>Auto-generate activity areas from blocks</label>
                        </div>

                        {areaConfig.autoGenerate && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                                <div>
                                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>
                                        Min {estimationConfig.qualityField || 'Value'}
                                    </label>
                                    <input
                                        type="number"
                                        value={areaConfig.minValue}
                                        onChange={e => setAreaConfig(prev => ({ ...prev, minValue: parseFloat(e.target.value) }))}
                                        style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                    />
                                </div>

                                <div>
                                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Max (optional)</label>
                                    <input
                                        type="number"
                                        value={areaConfig.maxValue || ''}
                                        onChange={e => setAreaConfig(prev => ({ ...prev, maxValue: e.target.value ? parseFloat(e.target.value) : null }))}
                                        style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                    />
                                </div>

                                <div>
                                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '4px' }}>Activity Type</label>
                                    <select
                                        value={areaConfig.activityType}
                                        onChange={e => setAreaConfig(prev => ({ ...prev, activityType: e.target.value }))}
                                        style={{ width: '100%', padding: '8px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
                                    >
                                        <option value="Coal Mining">Coal Mining</option>
                                        <option value="Overburden Removal">Overburden Removal</option>
                                        <option value="Rehabilitation">Rehabilitation</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {areasCreated.length > 0 && (
                            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#ECFDF5', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 500, color: '#065F46' }}>✓ Areas Created</div>
                                <div style={{ fontSize: '12px', color: '#047857', marginTop: '4px' }}>
                                    {areasCreated.length} activity areas generated
                                </div>
                            </div>
                        )}
                    </div>
                );

            case 6: // Confirm
                return (
                    <div style={{ backgroundColor: '#FFF', borderRadius: '12px', padding: '20px' }}>
                        <h3 style={{ marginBottom: '16px', color: '#1F2937' }}>Review & Confirm</h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div style={{ padding: '12px', backgroundColor: '#F3F4F6', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 500, marginBottom: '8px' }}>Data Import</div>
                                <div style={{ fontSize: '13px', color: '#4B5563' }}>
                                    ✓ {importResult?.collars_imported || 0} boreholes imported<br />
                                    {importResult?.surveys_imported > 0 && `✓ ${importResult.surveys_imported} surveys imported`}<br />
                                    {importResult?.intervals_imported > 0 && `✓ ${importResult.intervals_imported} intervals imported`}
                                </div>
                            </div>

                            <div style={{ padding: '12px', backgroundColor: '#F3F4F6', borderRadius: '8px' }}>
                                <div style={{ fontWeight: 500, marginBottom: '8px' }}>Block Model</div>
                                <div style={{ fontSize: '13px', color: '#4B5563' }}>
                                    ✓ {blockConfig.name}<br />
                                    ✓ Block size: {blockConfig.blockSizeX}m × {blockConfig.blockSizeY}m × {blockConfig.blockSizeZ}m<br />
                                    {estimationResult && `✓ ${estimationResult.blocks_estimated} blocks estimated (${estimationConfig.method})`}
                                </div>
                            </div>

                            {areasCreated.length > 0 && (
                                <div style={{ padding: '12px', backgroundColor: '#F3F4F6', borderRadius: '8px' }}>
                                    <div style={{ fontWeight: 500, marginBottom: '8px' }}>Activity Areas</div>
                                    <div style={{ fontSize: '13px', color: '#4B5563' }}>
                                        ✓ {areasCreated.length} areas created for {areaConfig.activityType}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#F3F4F6', padding: '24px' }}>
            {/* Header */}
            <div style={{ maxWidth: '900px', margin: '0 auto 24px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#1F2937', marginBottom: '4px' }}>
                    Site Builder
                </h1>
                <p style={{ color: '#6B7280', fontSize: '14px' }}>{siteName}</p>
            </div>

            {/* Progress */}
            <div style={{ maxWidth: '900px', margin: '0 auto 24px', display: 'flex', justifyContent: 'space-between' }}>
                {STEPS.map((step, index) => {
                    const Icon = step.icon;
                    const isComplete = stepStatus[step.id] === 'complete';
                    const isActive = index === currentStep;

                    return (
                        <div key={step.id} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                <div style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '50%',
                                    backgroundColor: isComplete ? '#10B981' : isActive ? '#3B82F6' : '#E5E7EB',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}>
                                    {isComplete ? (
                                        <Check size={20} color="white" />
                                    ) : (
                                        <Icon size={18} color={isActive ? 'white' : '#9CA3AF'} />
                                    )}
                                </div>
                                <span style={{ fontSize: '11px', marginTop: '4px', color: isActive ? '#1F2937' : '#6B7280' }}>
                                    {step.title}
                                </span>
                            </div>
                            {index < STEPS.length - 1 && (
                                <div style={{ flex: 1, height: '2px', backgroundColor: isComplete ? '#10B981' : '#E5E7EB', margin: '0 8px 24px' }} />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Error */}
            {error && (
                <div style={{ maxWidth: '900px', margin: '0 auto 16px', padding: '12px', backgroundColor: '#FEE2E2', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertCircle size={18} color="#DC2626" />
                    <span style={{ color: '#B91C1C' }}>{error}</span>
                </div>
            )}

            {/* Content */}
            <div style={{ maxWidth: '900px', margin: '0 auto 24px' }}>
                {renderStepContent()}
            </div>

            {/* Navigation */}
            <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', justifyContent: 'space-between' }}>
                <button
                    onClick={goBack}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 20px',
                        backgroundColor: 'white',
                        border: '1px solid #D1D5DB',
                        borderRadius: '8px',
                        cursor: 'pointer'
                    }}
                >
                    <ChevronLeft size={18} />
                    {currentStep === 0 ? 'Cancel' : 'Back'}
                </button>

                <button
                    onClick={handleStep}
                    disabled={!canProceed || isProcessing}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 20px',
                        backgroundColor: canProceed && !isProcessing ? '#3B82F6' : '#E5E7EB',
                        color: canProceed && !isProcessing ? 'white' : '#9CA3AF',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: canProceed && !isProcessing ? 'pointer' : 'not-allowed'
                    }}
                >
                    {isProcessing ? (
                        <>
                            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            Processing...
                        </>
                    ) : currentStep === STEPS.length - 1 ? (
                        <>
                            Complete Setup
                            <CheckCircle size={18} />
                        </>
                    ) : (
                        <>
                            Next
                            <ChevronRight size={18} />
                        </>
                    )}
                </button>
            </div>

            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
    );
};

export default SiteBuilderWizard;
