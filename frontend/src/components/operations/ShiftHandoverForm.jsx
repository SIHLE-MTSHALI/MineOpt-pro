/**
 * ShiftHandoverForm.jsx
 * 
 * Digital shift handover form component.
 */

import React, { useState } from 'react';
import {
    ClipboardCheck,
    AlertTriangle,
    Truck,
    Wrench,
    FileText,
    Send,
    CheckCircle,
    Clock
} from 'lucide-react';

const ShiftHandoverForm = ({
    shiftData,
    productionSummary,
    equipmentStatus = [],
    incidentsList = [],
    onSubmit,
    onAcknowledge,
    isOutgoing = true,
    className = ''
}) => {
    const [formData, setFormData] = useState({
        safetyNotes: '',
        productionNotes: '',
        equipmentNotes: '',
        generalNotes: '',
        tasksIncomplete: [],
        newTask: ''
    });
    const [submitted, setSubmitted] = useState(false);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const addTask = () => {
        if (formData.newTask.trim()) {
            setFormData(prev => ({
                ...prev,
                tasksIncomplete: [...prev.tasksIncomplete, formData.newTask.trim()],
                newTask: ''
            }));
        }
    };

    const removeTask = (index) => {
        setFormData(prev => ({
            ...prev,
            tasksIncomplete: prev.tasksIncomplete.filter((_, i) => i !== index)
        }));
    };

    const handleSubmit = () => {
        onSubmit?.({
            ...formData,
            oreTonnes: productionSummary?.oreTonnes || 0,
            wasteTonnes: productionSummary?.wasteTonnes || 0,
            totalLoads: productionSummary?.totalLoads || 0
        });
        setSubmitted(true);
    };

    return (
        <div className={`shift-handover-form ${className}`}>
            {/* Header */}
            <div className="form-header">
                <div className="header-content">
                    <ClipboardCheck size={24} />
                    <div>
                        <h2>{isOutgoing ? 'Outgoing' : 'Incoming'} Shift Handover</h2>
                        <p>{shiftData?.shiftName} - {shiftData?.date}</p>
                    </div>
                </div>
                {submitted && (
                    <div className="submitted-badge">
                        <CheckCircle size={16} />
                        Submitted
                    </div>
                )}
            </div>

            {/* Production Summary */}
            <div className="form-section">
                <h3><Truck size={16} /> Production Summary</h3>
                <div className="summary-grid">
                    <div className="summary-item">
                        <span className="label">Ore Tonnes</span>
                        <span className="value">{(productionSummary?.oreTonnes || 0).toLocaleString()}</span>
                    </div>
                    <div className="summary-item">
                        <span className="label">Waste Tonnes</span>
                        <span className="value">{(productionSummary?.wasteTonnes || 0).toLocaleString()}</span>
                    </div>
                    <div className="summary-item">
                        <span className="label">Total Loads</span>
                        <span className="value">{productionSummary?.totalLoads || 0}</span>
                    </div>
                    <div className="summary-item">
                        <span className="label">Shift Hours</span>
                        <span className="value">{productionSummary?.shiftHours || 12}</span>
                    </div>
                </div>
            </div>

            {/* Equipment Status */}
            <div className="form-section">
                <h3><Wrench size={16} /> Equipment Status</h3>
                <div className="equipment-grid">
                    {equipmentStatus.map((eq, i) => (
                        <div key={i} className={`equipment-card ${eq.status}`}>
                            <span className="fleet-number">{eq.fleetNumber}</span>
                            <span className={`status-badge ${eq.status}`}>{eq.status}</span>
                        </div>
                    ))}
                    {equipmentStatus.length === 0 && (
                        <p className="no-data">No equipment data available</p>
                    )}
                </div>
            </div>

            {/* Incidents */}
            {incidentsList.length > 0 && (
                <div className="form-section incidents-section">
                    <h3><AlertTriangle size={16} /> Shift Incidents</h3>
                    <div className="incidents-list">
                        {incidentsList.map((incident, i) => (
                            <div key={i} className={`incident-item ${incident.severity}`}>
                                <div className="incident-header">
                                    <span className={`severity-badge ${incident.severity}`}>
                                        {incident.severity}
                                    </span>
                                    <span className="incident-time">
                                        <Clock size={12} /> {incident.time}
                                    </span>
                                </div>
                                <p className="incident-title">{incident.title}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Notes Sections */}
            <div className="form-section">
                <h3><FileText size={16} /> Handover Notes</h3>

                <div className="notes-group">
                    <label>Safety Notes</label>
                    <textarea
                        value={formData.safetyNotes}
                        onChange={(e) => handleChange('safetyNotes', e.target.value)}
                        placeholder="Safety concerns, hazards, near misses..."
                        rows={3}
                    />
                </div>

                <div className="notes-group">
                    <label>Production Notes</label>
                    <textarea
                        value={formData.productionNotes}
                        onChange={(e) => handleChange('productionNotes', e.target.value)}
                        placeholder="Production issues, delays, achievements..."
                        rows={3}
                    />
                </div>

                <div className="notes-group">
                    <label>Equipment Notes</label>
                    <textarea
                        value={formData.equipmentNotes}
                        onChange={(e) => handleChange('equipmentNotes', e.target.value)}
                        placeholder="Equipment issues, repairs needed..."
                        rows={3}
                    />
                </div>

                <div className="notes-group">
                    <label>General Notes</label>
                    <textarea
                        value={formData.generalNotes}
                        onChange={(e) => handleChange('generalNotes', e.target.value)}
                        placeholder="Other information for incoming shift..."
                        rows={3}
                    />
                </div>
            </div>

            {/* Outstanding Tasks */}
            <div className="form-section">
                <h3>Outstanding Tasks for Next Shift</h3>
                <div className="tasks-input">
                    <input
                        type="text"
                        value={formData.newTask}
                        onChange={(e) => handleChange('newTask', e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && addTask()}
                        placeholder="Add task..."
                    />
                    <button onClick={addTask}>Add</button>
                </div>
                <ul className="tasks-list">
                    {formData.tasksIncomplete.map((task, i) => (
                        <li key={i}>
                            <span>{task}</span>
                            <button onClick={() => removeTask(i)}>×</button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Submit */}
            <div className="form-actions">
                {isOutgoing ? (
                    <button
                        className="submit-btn"
                        onClick={handleSubmit}
                        disabled={submitted}
                    >
                        <Send size={16} />
                        {submitted ? 'Submitted' : 'Submit Handover'}
                    </button>
                ) : (
                    <button
                        className="acknowledge-btn"
                        onClick={onAcknowledge}
                    >
                        <CheckCircle size={16} />
                        Acknowledge & Accept
                    </button>
                )}
            </div>

            <style jsx>{`
        .shift-handover-form {
          background: linear-gradient(145deg, #1a1a2e, #252538);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .form-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-content {
          display: flex;
          gap: 12px;
          align-items: center;
          color: #fff;
        }
        
        .header-content h2 {
          margin: 0;
          font-size: 18px;
        }
        
        .header-content p {
          margin: 0;
          font-size: 13px;
          color: #888;
        }
        
        .submitted-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: rgba(34, 197, 94, 0.2);
          border-radius: 6px;
          color: #22c55e;
          font-size: 12px;
        }
        
        .form-section {
          padding: 20px;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .form-section h3 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0 0 16px;
          font-size: 14px;
          color: #ccc;
        }
        
        .summary-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
        }
        
        .summary-item {
          background: rgba(255,255,255,0.03);
          padding: 12px;
          border-radius: 8px;
          text-align: center;
        }
        
        .summary-item .label {
          display: block;
          font-size: 11px;
          color: #888;
          margin-bottom: 4px;
        }
        
        .summary-item .value {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }
        
        .equipment-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        
        .equipment-card {
          display: flex;
          gap: 8px;
          align-items: center;
          padding: 8px 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          border-left: 3px solid #6b7280;
        }
        
        .equipment-card.operating { border-color: #22c55e; }
        .equipment-card.maintenance { border-color: #3b82f6; }
        .equipment-card.breakdown { border-color: #ef4444; }
        
        .fleet-number {
          font-weight: 600;
          color: #fff;
        }
        
        .status-badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
        }
        
        .status-badge.operating { background: rgba(34,197,94,0.2); color: #22c55e; }
        .status-badge.maintenance { background: rgba(59,130,246,0.2); color: #3b82f6; }
        .status-badge.breakdown { background: rgba(239,68,68,0.2); color: #ef4444; }
        
        .incidents-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .incident-item {
          padding: 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 8px;
          border-left: 3px solid #eab308;
        }
        
        .incident-item.critical { border-color: #ef4444; }
        .incident-item.serious { border-color: #f97316; }
        
        .incident-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        
        .severity-badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          text-transform: uppercase;
        }
        
        .severity-badge.critical { background: rgba(239,68,68,0.2); color: #ef4444; }
        .severity-badge.serious { background: rgba(249,115,22,0.2); color: #f97316; }
        
        .incident-time {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 11px;
          color: #888;
        }
        
        .incident-title {
          margin: 0;
          font-size: 13px;
          color: #ddd;
        }
        
        .notes-group {
          margin-bottom: 16px;
        }
        
        .notes-group label {
          display: block;
          font-size: 12px;
          color: #888;
          margin-bottom: 6px;
        }
        
        .notes-group textarea {
          width: 100%;
          padding: 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          resize: vertical;
        }
        
        .tasks-input {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }
        
        .tasks-input input {
          flex: 1;
          padding: 8px 12px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
        }
        
        .tasks-input button {
          padding: 8px 16px;
          background: rgba(59,130,246,0.2);
          border: none;
          border-radius: 6px;
          color: #3b82f6;
          cursor: pointer;
        }
        
        .tasks-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        
        .tasks-list li {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          background: rgba(255,255,255,0.03);
          border-radius: 6px;
          margin-bottom: 4px;
          color: #ccc;
        }
        
        .tasks-list button {
          background: none;
          border: none;
          color: #888;
          cursor: pointer;
        }
        
        .form-actions {
          padding: 20px;
        }
        
        .submit-btn, .acknowledge-btn {
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 8px;
          padding: 14px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
        }
        
        .submit-btn {
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color: #fff;
        }
        
        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .acknowledge-btn {
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          color: #fff;
        }
        
        .no-data {
          color: #666;
          font-style: italic;
        }
      `}</style>
        </div>
    );
};

export default ShiftHandoverForm;
