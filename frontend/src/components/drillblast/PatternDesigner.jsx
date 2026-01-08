import React, { useState } from 'react';
import { drillBlastAPI } from '../../services/api';

const PatternDesigner = ({ siteId, onPatternCreated }) => {
    const [formData, setFormData] = useState({
        site_id: siteId,
        bench_name: '',
        pattern_type: 'rectangular',
        burden: 4.0,
        spacing: 5.0,
        num_rows: 5,
        num_holes_per_row: 10,
        hole_depth_m: 10.0,
        hole_diameter_mm: 165,
        explosive_type: 'anfo',
        subdrill_m: 0.5,
        stemming_height_m: 3.0
    });

    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            await drillBlastAPI.createPattern(formData);
            if (onPatternCreated) onPatternCreated();
            alert('Pattern created successfully!');
        } catch (error) {
            alert('Failed to create pattern: ' + error.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="pattern-designer card">
            <h3>Create Blast Pattern</h3>
            <form onSubmit={handleSubmit} className="designer-grid">
                <div className="form-section">
                    <h4>Location</h4>
                    <div className="form-group">
                        <label>Bench Name</label>
                        <input name="bench_name" value={formData.bench_name} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Pattern Type</label>
                        <select name="pattern_type" value={formData.pattern_type} onChange={handleChange}>
                            <option value="rectangular">Rectangular</option>
                            <option value="staggered">Staggered</option>
                        </select>
                    </div>
                </div>

                <div className="form-section">
                    <h4>Geometry</h4>
                    <div className="form-group">
                        <label>Burden (m)</label>
                        <input type="number" step="0.1" name="burden" value={formData.burden} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Spacing (m)</label>
                        <input type="number" step="0.1" name="spacing" value={formData.spacing} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Rows</label>
                        <input type="number" name="num_rows" value={formData.num_rows} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Holes/Row</label>
                        <input type="number" name="num_holes_per_row" value={formData.num_holes_per_row} onChange={handleChange} />
                    </div>
                </div>

                <div className="form-section">
                    <h4>Drilling Specs</h4>
                    <div className="form-group">
                        <label>Depth (m)</label>
                        <input type="number" step="0.1" name="hole_depth_m" value={formData.hole_depth_m} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Diameter (mm)</label>
                        <input type="number" name="hole_diameter_mm" value={formData.hole_diameter_mm} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label>Subdrill (m)</label>
                        <input type="number" step="0.1" name="subdrill_m" value={formData.subdrill_m} onChange={handleChange} />
                    </div>
                </div>

                <div className="form-actions">
                    <button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? 'Creating...' : 'Create Pattern'}
                    </button>
                    <div className="summary">
                        <strong>Total Holes: </strong> {formData.num_rows * formData.num_holes_per_row}
                    </div>
                </div>
            </form>
        </div>
    );
};

export default PatternDesigner;
