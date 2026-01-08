import React, { useState, useEffect } from 'react';
import { fleetAPI } from '../../services/api';

const MaintenancePanel = ({ siteId }) => {
    const [maintenance, setMaintenance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isScheduling, setIsScheduling] = useState(false);

    // Form state
    const [newItem, setNewItem] = useState({
        equipment_id: '',
        title: '',
        maintenance_type: 'preventive',
        priority: 'medium',
        scheduled_date: ''
    });

    useEffect(() => {
        loadMaintenance();
    }, [siteId]);

    const loadMaintenance = async () => {
        try {
            setLoading(true);
            const data = await fleetAPI.getMaintenancePending(siteId);
            setMaintenance(data);
        } catch (error) {
            console.error('Failed to load maintenance:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await fleetAPI.scheduleMaintenance(newItem);
            setIsScheduling(false);
            loadMaintenance();
            setNewItem({
                equipment_id: '',
                title: '',
                maintenance_type: 'preventive',
                priority: 'medium',
                scheduled_date: ''
            });
        } catch (error) {
            alert('Failed to schedule maintenance: ' + error.message);
        }
    };

    if (loading) return <div>Loading maintenance schedule...</div>;

    return (
        <div className="maintenance-panel">
            <div className="panel-header">
                <h3>Scheduled Maintenance</h3>
                <button
                    className="primary-btn"
                    onClick={() => setIsScheduling(!isScheduling)}
                >
                    {isScheduling ? 'Cancel' : 'Schedule New'}
                </button>
            </div>

            {isScheduling && (
                <form onSubmit={handleSubmit} className="schedule-form card">
                    <h4>New Maintenance Task</h4>
                    <div className="form-group">
                        <label>Equipment ID</label>
                        <input
                            required
                            type="text"
                            value={newItem.equipment_id}
                            onChange={(e) => setNewItem({ ...newItem, equipment_id: e.target.value })}
                            placeholder="Enter Equipment UUID"
                        />
                    </div>
                    <div className="form-group">
                        <label>Title</label>
                        <input
                            required
                            type="text"
                            value={newItem.title}
                            onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                        />
                    </div>
                    <div className="form-group">
                        <label>Type</label>
                        <select
                            value={newItem.maintenance_type}
                            onChange={(e) => setNewItem({ ...newItem, maintenance_type: e.target.value })}
                        >
                            <option value="preventive">Preventive</option>
                            <option value="corrective">Corrective</option>
                            <option value="breakdown">Breakdown</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Date</label>
                        <input
                            type="datetime-local"
                            value={newItem.scheduled_date}
                            onChange={(e) => setNewItem({ ...newItem, scheduled_date: e.target.value })}
                        />
                    </div>
                    <button type="submit">Schedule</button>
                </form>
            )}

            <div className="maintenance-list">
                {maintenance.length === 0 ? (
                    <p>No pending maintenance tasks.</p>
                ) : (
                    maintenance.map(task => (
                        <div key={task.record_id} className={`maintenance-card priority-${task.priority}`}>
                            <div className="task-header">
                                <h5>{task.title}</h5>
                                <span className="status">{task.status}</span>
                            </div>
                            <p><strong>Equipment:</strong> {task.equipment_id}</p>
                            <p><strong>Scheduled:</strong> {new Date(task.scheduled_date).toLocaleDateString()}</p>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default MaintenancePanel;
