import React, { useState } from 'react';
import { drillBlastAPI } from '../../services/api';

const BlastEventLogger = ({ siteId, patterns, onEventLogged }) => {
    const [formData, setFormData] = useState({
        site_id: siteId,
        pattern_id: '',
        blast_time: '',
        actual_tonnes: 0,
        vibration_peak_particle_velocity: 0,
        airblast_db: 0,
        notes: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await drillBlastAPI.createBlastEvent({
                ...formData,
                blast_time: new Date(formData.blast_time).toISOString()
            });
            onEventLogged();
            alert('Blast recorded successfully');
            setFormData({
                site_id: siteId,
                pattern_id: '',
                blast_time: '',
                actual_tonnes: 0,
                vibration_peak_particle_velocity: 0,
                airblast_db: 0,
                notes: ''
            });
        } catch (error) {
            alert('Failed to log blast: ' + error.message);
        }
    };

    return (
        <div className="blast-logger card">
            <h3>Log Blast Event</h3>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Pattern</label>
                    <select
                        required
                        value={formData.pattern_id}
                        onChange={e => setFormData({ ...formData, pattern_id: e.target.value })}
                    >
                        <option value="">Select a Pattern</option>
                        {patterns.map(p => (
                            <option key={p.pattern_id} value={p.pattern_id}>
                                {p.bench_name} (ID: {p.pattern_id.slice(0, 8)})
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Blast Time</label>
                    <input
                        required
                        type="datetime-local"
                        value={formData.blast_time}
                        onChange={e => setFormData({ ...formData, blast_time: e.target.value })}
                    />
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label>Tonnes Blasted</label>
                        <input
                            type="number"
                            value={formData.actual_tonnes}
                            onChange={e => setFormData({ ...formData, actual_tonnes: parseFloat(e.target.value) })}
                        />
                    </div>
                    <div className="form-group">
                        <label>PPV (mm/s)</label>
                        <input
                            type="number"
                            step="0.1"
                            value={formData.vibration_peak_particle_velocity}
                            onChange={e => setFormData({ ...formData, vibration_peak_particle_velocity: parseFloat(e.target.value) })}
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label>Airblast (dB)</label>
                    <input
                        type="number"
                        value={formData.airblast_db}
                        onChange={e => setFormData({ ...formData, airblast_db: parseFloat(e.target.value) })}
                    />
                </div>

                <button type="submit" className="primary-btn">Record Blast</button>
            </form>
        </div>
    );
};

export default BlastEventLogger;
