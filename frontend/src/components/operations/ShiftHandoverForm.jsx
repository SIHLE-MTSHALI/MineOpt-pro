import React, { useState } from 'react';
import { operationsAPI } from '../../services/api';

const ShiftHandoverForm = ({ shiftId, onComplete, onCancel }) => {
  const [formData, setFormData] = useState({
    shift_id: shiftId,
    outgoing_supervisor: '',
    incoming_supervisor: '',
    notes: '',
    issues_flagged: false
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // First create the handover record
      await operationsAPI.createHandover(formData);
      // Then end the shift
      await operationsAPI.endShift(shiftId);
      onComplete();
    } catch (error) {
      alert('Failed to complete handover: ' + error.message);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content card">
        <h3>Shift Handover</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Outgoing Supervisor</label>
            <input
              required
              value={formData.outgoing_supervisor}
              onChange={e => setFormData({ ...formData, outgoing_supervisor: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Incoming Supervisor</label>
            <input
              required
              value={formData.incoming_supervisor}
              onChange={e => setFormData({ ...formData, incoming_supervisor: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Notes / Issues</label>
            <textarea
              rows="4"
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>
          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={formData.issues_flagged}
                onChange={e => setFormData({ ...formData, issues_flagged: e.target.checked })}
              />
              Flag major issues?
            </label>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onCancel}>Cancel</button>
            <button type="submit" className="primary-btn">Complete Shift</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ShiftHandoverForm;
