/**
 * SiteBuilderWizard Component - Phase 4 Site Builder UI
 * 
 * Multi-step wizard for building a new site from borehole data:
 * 1. Upload Files - Load CSV/DXF/STR files
 * 2. Map Columns - Configure field mappings
 * 3. Create Block Model - Define grid and estimate grades
 * 4. Review & Create - Final confirmation
 * 
 * Features:
 * - Step navigation with validation
 * - Progress indicator
 * - Data preview at each step
 * - Background processing with status updates
 */

import React, { useState, useCallback } from 'react';
import {
    ChevronLeft,
    ChevronRight,
    Check,
    Upload,
    Columns,
    Grid3X3,
    CheckCircle,
    Loader2,
    MapPin,
    Database,
    AlertCircle
} from 'lucide-react';
import FileUploader from './FileUploader';
import ColumnMapper from './ColumnMapper';

const STEPS = [
    {
        id: 'upload',
        title: 'Upload Files',
        description: 'Load your borehole data files',
        icon: Upload
    },
    {
        id: 'mapping',
        title: 'Map Columns',
        description: 'Configure column mappings',
        icon: Columns
    },
    {
        id: 'blockmodel',
        title: 'Block Model',
        description: 'Define grid and estimate grades',
        icon: Grid3X3
    },
    {
        id: 'review',
        title: 'Review & Create',
        description: 'Confirm and create site',
        icon: CheckCircle
    },
];

const SiteBuilderWizard = ({
    siteId,
    onComplete,
    onCancel
}) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);

    // Wizard state
    const [files, setFiles] = useState({
        collar: null,
        survey: null,
        assay: null,
        dxf: null
    });
    const [parsedData, setParsedData] = useState({});
    const [mappings, setMappings] = useState({});
    const [blockModelConfig, setBlockModelConfig] = useState({
        name: '',
        blockSizeX: 10,
        blockSizeY: 10,
        blockSizeZ: 5,
        qualityField: '',
        estimationMethod: 'kriging'
    });
    const [result, setResult] = useState(null);

    // Handle file parsed
    const handleFileParsed = useCallback((file, data, format) => {
        // Determine file type based on content
        let fileType = 'unknown';

        if (format === 'dxf') {
            fileType = 'dxf';
        } else if (format === 'str') {
            fileType = 'geometry';
        } else if (data.inferred_purpose) {
            fileType = data.inferred_purpose;
        }

        setFiles(prev => ({ ...prev, [fileType]: file }));
        setParsedData(prev => ({ ...prev, [fileType]: data }));
    }, []);

    // Handle mapping change
    const handleMappingChange = useCallback((fileType, mappingData) => {
        setMappings(prev => ({ ...prev, [fileType]: mappingData }));
    }, []);

    // Import boreholes
    const importBoreholes = async () => {
        setIsProcessing(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('site_id', siteId);
            formData.append('collar_file', files.collar);

            if (files.survey) {
                formData.append('survey_file', files.survey);
            }
            if (files.assay) {
                formData.append('assay_file', files.assay);
            }

            const response = await fetch('/api/boreholes/import', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Import failed');
            }

            const result = await response.json();
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsProcessing(false);
        }
    };

    // Create block model
    const createBlockModel = async (collarIds) => {
        setIsProcessing(true);
        setError(null);

        try {
            // This would call the block model creation and estimation endpoints
            // For now, simulate the process
            const response = await fetch('/api/blockmodels', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    site_id: siteId,
                    name: blockModelConfig.name || 'Block Model 1',
                    collar_ids: collarIds,
                    block_size_x: blockModelConfig.blockSizeX,
                    block_size_y: blockModelConfig.blockSizeY,
                    block_size_z: blockModelConfig.blockSizeZ,
                    quality_field: blockModelConfig.qualityField,
                    estimation_method: blockModelConfig.estimationMethod
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Block model creation failed');
            }

            return await response.json();
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setIsProcessing(false);
        }
    };

    // Run full wizard process
    const runWizard = async () => {
        setIsProcessing(true);
        setError(null);

        try {
            // Step 1: Import boreholes
            const importResult = await importBoreholes();

            if (!importResult.success) {
                throw new Error('Borehole import failed');
            }

            // Step 2: Create block model (if configured)
            if (blockModelConfig.qualityField) {
                const modelResult = await createBlockModel(importResult.collar_ids);
                setResult({
                    ...importResult,
                    blockModel: modelResult
                });
            } else {
                setResult(importResult);
            }

            return true;
        } catch (err) {
            setError(err.message);
            return false;
        } finally {
            setIsProcessing(false);
        }
    };

    // Navigation
    const canGoNext = () => {
        switch (currentStep) {
            case 0: // Upload
                return files.collar !== null;
            case 1: // Mapping
                return mappings.collar?.mappings?.HoleID &&
                    mappings.collar?.mappings?.Easting &&
                    mappings.collar?.mappings?.Northing;
            case 2: // Block Model
                return true; // Optional step
            case 3: // Review
                return true;
            default:
                return false;
        }
    };

    const goNext = async () => {
        if (currentStep === STEPS.length - 1) {
            // Final step - run wizard
            const success = await runWizard();
            if (success && onComplete) {
                onComplete(result);
            }
        } else {
            setCurrentStep(prev => prev + 1);
        }
    };

    const goBack = () => {
        if (currentStep === 0 && onCancel) {
            onCancel();
        } else {
            setCurrentStep(prev => prev - 1);
        }
    };

    // Render step content
    const renderStepContent = () => {
        switch (currentStep) {
            case 0:
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937' }}>Collar File (Required)</h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Collar File"
                                description="CSV with HoleID, Easting, Northing, Elevation"
                                onFileParsed={(file, data, format) => {
                                    setFiles(prev => ({ ...prev, collar: file }));
                                    setParsedData(prev => ({ ...prev, collar: data }));
                                }}
                            />
                        </div>

                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937' }}>Survey File (Optional)</h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Survey File"
                                description="CSV with HoleID, Depth, Azimuth, Dip"
                                onFileParsed={(file, data, format) => {
                                    setFiles(prev => ({ ...prev, survey: file }));
                                    setParsedData(prev => ({ ...prev, survey: data }));
                                }}
                            />
                        </div>

                        <div>
                            <h3 style={{ marginBottom: '8px', color: '#1F2937' }}>Assay File (Optional)</h3>
                            <FileUploader
                                acceptedFormats={['csv', 'txt']}
                                title="Upload Assay File"
                                description="CSV with HoleID, From, To, Quality values"
                                onFileParsed={(file, data, format) => {
                                    setFiles(prev => ({ ...prev, assay: file }));
                                    setParsedData(prev => ({ ...prev, assay: data }));
                                }}
                            />
                        </div>
                    </div>
                );

            case 1:
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        {parsedData.collar && (
                            <div>
                                <h3 style={{ marginBottom: '12px', color: '#1F2937' }}>Collar Column Mapping</h3>
                                <ColumnMapper
                                    columns={parsedData.collar.columns || []}
                                    previewRows={parsedData.collar.preview_rows || []}
                                    fileType="collar"
                                    onChange={(data) => handleMappingChange('collar', data)}
                                />
                            </div>
                        )}

                        {parsedData.survey && (
                            <div>
                                <h3 style={{ marginBottom: '12px', color: '#1F2937' }}>Survey Column Mapping</h3>
                                <ColumnMapper
                                    columns={parsedData.survey.columns || []}
                                    previewRows={parsedData.survey.preview_rows || []}
                                    fileType="survey"
                                    onChange={(data) => handleMappingChange('survey', data)}
                                />
                            </div>
                        )}

                        {parsedData.assay && (
                            <div>
                                <h3 style={{ marginBottom: '12px', color: '#1F2937' }}>Assay Column Mapping</h3>
                                <ColumnMapper
                                    columns={parsedData.assay.columns || []}
                                    previewRows={parsedData.assay.preview_rows || []}
                                    fileType="assay"
                                    onChange={(data) => handleMappingChange('assay', data)}
                                />
                            </div>
                        )}
                    </div>
                );

            case 2:
                return (
                    <div style={{
                        backgroundColor: '#FFFFFF',
                        borderRadius: '12px',
                        padding: '24px'
                    }}>
                        <h3 style={{ marginBottom: '20px', color: '#1F2937' }}>
                            Block Model Configuration
                        </h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Model Name
                                </label>
                                <input
                                    type="text"
                                    value={blockModelConfig.name}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="Block Model 1"
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Quality Field to Estimate
                                </label>
                                <select
                                    value={blockModelConfig.qualityField}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, qualityField: e.target.value }))}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                >
                                    <option value="">-- Select field --</option>
                                    {mappings.assay?.qualityColumns?.map(col => (
                                        <option key={col} value={col}>{col}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Block Size X (m)
                                </label>
                                <input
                                    type="number"
                                    value={blockModelConfig.blockSizeX}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, blockSizeX: parseFloat(e.target.value) }))}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Block Size Y (m)
                                </label>
                                <input
                                    type="number"
                                    value={blockModelConfig.blockSizeY}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, blockSizeY: parseFloat(e.target.value) }))}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Block Size Z (m)
                                </label>
                                <input
                                    type="number"
                                    value={blockModelConfig.blockSizeZ}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, blockSizeZ: parseFloat(e.target.value) }))}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', color: '#374151', fontSize: '14px' }}>
                                    Estimation Method
                                </label>
                                <select
                                    value={blockModelConfig.estimationMethod}
                                    onChange={(e) => setBlockModelConfig(prev => ({ ...prev, estimationMethod: e.target.value }))}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        border: '1px solid #D1D5DB',
                                        borderRadius: '6px',
                                        fontSize: '14px'
                                    }}
                                >
                                    <option value="kriging">Ordinary Kriging</option>
                                    <option value="idw">Inverse Distance Weighting</option>
                                </select>
                            </div>
                        </div>
                    </div>
                );

            case 3:
                return (
                    <div style={{
                        backgroundColor: '#FFFFFF',
                        borderRadius: '12px',
                        padding: '24px'
                    }}>
                        <h3 style={{ marginBottom: '20px', color: '#1F2937' }}>
                            Review & Create Site
                        </h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {/* Files summary */}
                            <div style={{
                                padding: '16px',
                                backgroundColor: '#F3F4F6',
                                borderRadius: '8px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                    <Database size={18} color="#3B82F6" />
                                    <span style={{ fontWeight: 500 }}>Data Files</span>
                                </div>
                                <div style={{ fontSize: '14px', color: '#4B5563' }}>
                                    <div>✓ Collar: {files.collar?.name}</div>
                                    {files.survey && <div>✓ Survey: {files.survey.name}</div>}
                                    {files.assay && <div>✓ Assay: {files.assay.name}</div>}
                                </div>
                            </div>

                            {/* Block model summary */}
                            {blockModelConfig.qualityField && (
                                <div style={{
                                    padding: '16px',
                                    backgroundColor: '#F3F4F6',
                                    borderRadius: '8px'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                        <Grid3X3 size={18} color="#10B981" />
                                        <span style={{ fontWeight: 500 }}>Block Model</span>
                                    </div>
                                    <div style={{ fontSize: '14px', color: '#4B5563' }}>
                                        <div>Name: {blockModelConfig.name || 'Block Model 1'}</div>
                                        <div>Block Size: {blockModelConfig.blockSizeX}m × {blockModelConfig.blockSizeY}m × {blockModelConfig.blockSizeZ}m</div>
                                        <div>Quality Field: {blockModelConfig.qualityField}</div>
                                        <div>Method: {blockModelConfig.estimationMethod === 'kriging' ? 'Ordinary Kriging' : 'IDW'}</div>
                                    </div>
                                </div>
                            )}

                            {/* Error display */}
                            {error && (
                                <div style={{
                                    padding: '16px',
                                    backgroundColor: '#FEE2E2',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px'
                                }}>
                                    <AlertCircle size={18} color="#DC2626" />
                                    <span style={{ color: '#B91C1C' }}>{error}</span>
                                </div>
                            )}

                            {/* Result display */}
                            {result && (
                                <div style={{
                                    padding: '16px',
                                    backgroundColor: '#ECFDF5',
                                    borderRadius: '8px'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                        <CheckCircle size={18} color="#059669" />
                                        <span style={{ fontWeight: 500, color: '#065F46' }}>Import Successful!</span>
                                    </div>
                                    <div style={{ fontSize: '14px', color: '#047857' }}>
                                        <div>Collars imported: {result.collars_imported}</div>
                                        {result.surveys_imported > 0 && <div>Surveys imported: {result.surveys_imported}</div>}
                                        {result.intervals_imported > 0 && <div>Intervals imported: {result.intervals_imported}</div>}
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
        <div style={{
            minHeight: '100vh',
            backgroundColor: '#F3F4F6',
            padding: '32px'
        }}>
            {/* Header */}
            <div style={{
                maxWidth: '900px',
                margin: '0 auto',
                marginBottom: '32px'
            }}>
                <h1 style={{
                    fontSize: '28px',
                    fontWeight: 700,
                    color: '#1F2937',
                    marginBottom: '8px'
                }}>
                    Site Builder Wizard
                </h1>
                <p style={{ color: '#6B7280' }}>
                    Create a new site from your borehole and exploration data
                </p>
            </div>

            {/* Progress steps */}
            <div style={{
                maxWidth: '900px',
                margin: '0 auto',
                marginBottom: '32px',
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                {STEPS.map((step, index) => {
                    const Icon = step.icon;
                    const isActive = index === currentStep;
                    const isComplete = index < currentStep;

                    return (
                        <div
                            key={step.id}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                position: 'relative'
                            }}
                        >
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                zIndex: 1
                            }}>
                                <div style={{
                                    width: '48px',
                                    height: '48px',
                                    borderRadius: '50%',
                                    backgroundColor: isComplete ? '#10B981' : isActive ? '#3B82F6' : '#E5E7EB',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    marginBottom: '8px'
                                }}>
                                    {isComplete ? (
                                        <Check size={24} color="#FFFFFF" />
                                    ) : (
                                        <Icon size={24} color={isActive ? '#FFFFFF' : '#9CA3AF'} />
                                    )}
                                </div>
                                <span style={{
                                    fontSize: '13px',
                                    fontWeight: isActive ? 600 : 400,
                                    color: isActive ? '#1F2937' : '#6B7280',
                                    textAlign: 'center'
                                }}>
                                    {step.title}
                                </span>
                            </div>

                            {index < STEPS.length - 1 && (
                                <div style={{
                                    flex: 1,
                                    height: '2px',
                                    backgroundColor: isComplete ? '#10B981' : '#E5E7EB',
                                    marginLeft: '8px',
                                    marginRight: '8px',
                                    marginBottom: '32px'
                                }} />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Step content */}
            <div style={{
                maxWidth: '900px',
                margin: '0 auto',
                marginBottom: '32px'
            }}>
                {renderStepContent()}
            </div>

            {/* Navigation */}
            <div style={{
                maxWidth: '900px',
                margin: '0 auto',
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                <button
                    onClick={goBack}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '12px 24px',
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #D1D5DB',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 500,
                        color: '#374151',
                        cursor: 'pointer'
                    }}
                >
                    <ChevronLeft size={18} />
                    {currentStep === 0 ? 'Cancel' : 'Back'}
                </button>

                <button
                    onClick={goNext}
                    disabled={!canGoNext() || isProcessing}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '12px 24px',
                        backgroundColor: canGoNext() ? '#3B82F6' : '#E5E7EB',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 500,
                        color: canGoNext() ? '#FFFFFF' : '#9CA3AF',
                        cursor: canGoNext() ? 'pointer' : 'not-allowed'
                    }}
                >
                    {isProcessing ? (
                        <>
                            <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                            Processing...
                        </>
                    ) : currentStep === STEPS.length - 1 ? (
                        <>
                            Create Site
                            <Check size={18} />
                        </>
                    ) : (
                        <>
                            Next
                            <ChevronRight size={18} />
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

export default SiteBuilderWizard;
