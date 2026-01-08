import React, { useState, useEffect } from 'react';
import { fleetAPI } from '../../services/api';

const EquipmentList = ({ siteId }) => {
    const [equipment, setEquipment] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterType, setFilterType] = useState('');

    useEffect(() => {
        loadEquipment();
    }, [siteId, filterType]);

    const loadEquipment = async () => {
        try {
            setLoading(true);
            const data = await fleetAPI.getEquipmentList(siteId, filterType, null);
            setEquipment(data);
        } catch (error) {
            console.error('Failed to load equipment:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id, newStatus) => {
        try {
            await fleetAPI.updateStatus(id, newStatus);
            loadEquipment();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    if (loading) return <div>Loading fleet data...</div>;

    return (
        <div className="equipment-list-container">
            <div className="filters">
                <select onChange={(e) => setFilterType(e.target.value)} value={filterType}>
                    <option value="">All Types</option>
                    <option value="haul_truck">Haul Trucks</option>
                    <option value="excavator">Excavators</option>
                    <option value="drill_rig">Drills</option>
                </select>
                <button onClick={loadEquipment}>Refresh</button>
            </div>

            <table className="data-table">
                <thead>
                    <tr>
                        <th>Fleet #</th>
                        <th>Type</th>
                        <th>Model</th>
                        <th>Status</th>
                        <th>Engine Hours</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {equipment.map(eq => (
                        <tr key={eq.equipment_id}>
                            <td>{eq.fleet_number}</td>
                            <td>{eq.equipment_type}</td>
                            <td>{eq.model}</td>
                            <td>
                                <span className={`status-badge ${eq.status}`}>
                                    {eq.status}
                                </span>
                            </td>
                            <td>{eq.engine_hours?.toFixed(1) || '-'}</td>
                            <td>
                                <select
                                    value={eq.status || ''}
                                    onChange={(e) => handleStatusUpdate(eq.equipment_id, e.target.value)}
                                >
                                    <option value="operating">Operating</option>
                                    <option value="standby">Standby</option>
                                    <option value="maintenance">Maintenance</option>
                                    <option value="breakdown">Breakdown</option>
                                </select>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default EquipmentList;
