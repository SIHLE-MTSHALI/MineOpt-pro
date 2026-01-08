import React, { useState, useEffect } from 'react';
import { operationsAPI } from '../../services/api';

const ShiftLog = ({ siteId, activeShift, onShiftUpdate, onRequestHandover }) => {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(false);

    // New Ticket Form
    const [newTicket, setNewTicket] = useState({
        site_id: siteId,
        truck_fleet_number: '',
        origin_name: 'Pit A',
        destination_name: 'ROM Pad',
        material_type: 'ore_high_grade',
        loaded_at: '',
        shift_id: '',
        tonnes: 0
    });

    useEffect(() => {
        if (activeShift) {
            loadTickets();
        }
    }, [activeShift]);

    const loadTickets = async () => {
        try {
            setLoading(true);
            const data = await operationsAPI.getShiftTickets(activeShift.shift_id);
            setTickets(data);
        } catch (error) {
            console.error('Failed to load tickets', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartShift = async () => {
        const name = prompt("Enter Shift Name (e.g. Day Shift A):");
        if (!name) return;

        try {
            const now = new Date();
            const end = new Date(now.getTime() + 12 * 60 * 60 * 1000); // 12h shift

            await operationsAPI.startShift({
                site_id: siteId,
                shift_name: name,
                scheduled_start: now.toISOString(),
                scheduled_end: end.toISOString(),
                supervisor_name: "Current User"
            });
            onShiftUpdate();
        } catch (error) {
            alert('Failed to start shift: ' + error.message);
        }
    };

    const handleEndShift = async () => {
        if (!activeShift) return;
        if (!window.confirm("Are you sure you want to end this shift?")) return;

        try {
            await operationsAPI.endShift(activeShift.shift_id);
            onShiftUpdate();
        } catch (error) {
            alert('Failed to end shift: ' + error.message);
        }
    };

    const handleTicketSubmit = async (e) => {
        e.preventDefault();
        if (!activeShift) {
            alert("No active shift!");
            return;
        }

        try {
            await operationsAPI.createTicket({
                ...newTicket,
                shift_id: activeShift.shift_id,
                loaded_at: new Date().toISOString()
            });

            loadTickets();
            // Reset form
            setNewTicket(prev => ({ ...prev, truck_fleet_number: '', tonnes: 0 }));
        } catch (error) {
            alert('Failed to log ticket: ' + error.message);
        }
    };

    if (!activeShift) {
        return (
            <div className="shift-log-empty card center-content">
                <h3>No Active Shift</h3>
                <p>Start a shift to begin logging production.</p>
                <button className="primary-btn large" onClick={handleStartShift}>
                    Start New Shift
                </button>
            </div>
        );
    }

    return (
        <div className="shift-log-container">
            <div className="shift-header card">
                <div className="shift-info">
                    <h3>{activeShift.shift_name}</h3>
                    <span className="status-badge operating">Active</span>
                    <p>Started: {new Date(activeShift.actual_start).toLocaleTimeString()}</p>
                    <p>Supervisor: {activeShift.supervisor_name || 'N/A'}</p>
                </div>
                <button className="danger-btn" onClick={onRequestHandover}>End Shift & Handover</button>
            </div>

            <div className="log-content grid-layout">
                <div className="ticket-form card">
                    <h4>Log Load (Haul Cycle)</h4>
                    <form onSubmit={handleTicketSubmit}>
                        <div className="form-group">
                            <label>Truck #</label>
                            <input
                                required
                                value={newTicket.truck_fleet_number}
                                onChange={e => setNewTicket({ ...newTicket, truck_fleet_number: e.target.value })}
                            />
                        </div>
                        <div className="form-group">
                            <label>Origin</label>
                            <input
                                value={newTicket.origin_name}
                                onChange={e => setNewTicket({ ...newTicket, origin_name: e.target.value })}
                            />
                        </div>
                        <div className="form-group">
                            <label>Destination</label>
                            <input
                                value={newTicket.destination_name}
                                onChange={e => setNewTicket({ ...newTicket, destination_name: e.target.value })}
                            />
                        </div>
                        <div className="form-group">
                            <label>Material</label>
                            <select
                                value={newTicket.material_type}
                                onChange={e => setNewTicket({ ...newTicket, material_type: e.target.value })}
                            >
                                <option value="ore_high_grade">High Grade Ore</option>
                                <option value="ore_low_grade">Low Grade Ore</option>
                                <option value="waste">Waste</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Payload (tonnes)</label>
                            <input
                                type="number"
                                required
                                value={newTicket.tonnes}
                                onChange={e => setNewTicket({ ...newTicket, tonnes: parseFloat(e.target.value) })}
                            />
                        </div>
                        <button type="submit" className="primary-btn">Log Load</button>
                    </form>
                </div>

                <div className="recent-tickets card">
                    <h4>Recent Loads</h4>
                    {loading ? <p>Loading...</p> : (
                        <table className="compact-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Truck</th>
                                    <th>Mat.</th>
                                    <th>To</th>
                                    <th>Tn</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tickets.slice(0, 10).map(t => (
                                    <tr key={t.ticket_id}>
                                        <td>{new Date(t.loaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                                        <td>{t.truck_fleet_number}</td>
                                        <td>{t.material_type.split('_')[0]}</td>
                                        <td>{t.destination_name}</td>
                                        <td>{t.tonnes}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ShiftLog;
