/**
 * MaintenanceCalendar.jsx
 * 
 * Gantt-style maintenance schedule visualization.
 */

import React, { useState, useMemo } from 'react';
import {
    Wrench,
    Calendar,
    ChevronLeft,
    ChevronRight,
    Plus,
    Filter,
    AlertTriangle
} from 'lucide-react';

const PRIORITY_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e'
};

const MaintenanceCalendar = ({
    maintenanceRecords = [],
    equipment = [],
    startDate,
    endDate,
    onAddMaintenance,
    onEditMaintenance,
    onNavigate,
    className = ''
}) => {
    const [viewMode, setViewMode] = useState('week'); // week, month
    const [filterPriority, setFilterPriority] = useState(null);

    // Generate date columns
    const dateColumns = useMemo(() => {
        const dates = [];
        const current = new Date(startDate);
        const end = new Date(endDate);

        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }

        return dates;
    }, [startDate, endDate]);

    // Group maintenance by equipment
    const maintenanceByEquipment = useMemo(() => {
        const grouped = {};

        equipment.forEach(eq => {
            grouped[eq.equipment_id] = {
                equipment: eq,
                records: maintenanceRecords
                    .filter(m => m.equipment_id === eq.equipment_id)
                    .filter(m => !filterPriority || m.priority === filterPriority)
            };
        });

        return grouped;
    }, [equipment, maintenanceRecords, filterPriority]);

    // Get record position on timeline
    const getRecordStyle = (record) => {
        const start = new Date(startDate);
        const scheduled = new Date(record.scheduled_date || record.created_at);
        const dayOffset = Math.floor((scheduled - start) / (1000 * 60 * 60 * 24));
        const dayWidth = 100 / dateColumns.length;

        return {
            left: `${dayOffset * dayWidth}%`,
            width: `${dayWidth}%`,
            backgroundColor: PRIORITY_COLORS[record.priority] || PRIORITY_COLORS.medium
        };
    };

    const formatDate = (date) => {
        return date.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });
    };

    return (
        <div className={`maintenance-calendar ${className}`}>
            {/* Header */}
            <div className="calendar-header">
                <div className="header-left">
                    <h3>
                        <Wrench size={18} />
                        Maintenance Schedule
                    </h3>
                </div>

                <div className="header-right">
                    <div className="nav-buttons">
                        <button onClick={() => onNavigate?.('prev')}>
                            <ChevronLeft size={16} />
                        </button>
                        <span className="date-range">
                            {new Date(startDate).toLocaleDateString()} - {new Date(endDate).toLocaleDateString()}
                        </span>
                        <button onClick={() => onNavigate?.('next')}>
                            <ChevronRight size={16} />
                        </button>
                    </div>

                    <select
                        className="priority-filter"
                        value={filterPriority || ''}
                        onChange={(e) => setFilterPriority(e.target.value || null)}
                    >
                        <option value="">All Priorities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                    </select>

                    <button className="add-btn" onClick={onAddMaintenance}>
                        <Plus size={14} />
                        Add
                    </button>
                </div>
            </div>

            {/* Timeline Header */}
            <div className="timeline-header">
                <div className="equipment-column">Equipment</div>
                <div className="dates-row">
                    {dateColumns.map((date, i) => (
                        <div
                            key={i}
                            className={`date-cell ${date.getDay() === 0 || date.getDay() === 6 ? 'weekend' : ''}`}
                        >
                            {formatDate(date)}
                        </div>
                    ))}
                </div>
            </div>

            {/* Timeline Rows */}
            <div className="timeline-body">
                {Object.values(maintenanceByEquipment).map(({ equipment: eq, records }) => (
                    <div key={eq.equipment_id} className="timeline-row">
                        <div className="equipment-cell">
                            <span className="fleet-number">{eq.fleet_number}</span>
                            <span className="equipment-type">{eq.equipment_type?.replace(/_/g, ' ')}</span>
                        </div>

                        <div className="schedule-track">
                            {/* Grid lines */}
                            {dateColumns.map((_, i) => (
                                <div key={i} className="grid-line" style={{ left: `${(i / dateColumns.length) * 100}%` }} />
                            ))}

                            {/* Maintenance items */}
                            {records.map((record) => (
                                <div
                                    key={record.record_id}
                                    className={`maintenance-item ${record.status}`}
                                    style={getRecordStyle(record)}
                                    onClick={() => onEditMaintenance?.(record)}
                                    title={record.title}
                                >
                                    {record.priority === 'critical' && (
                                        <AlertTriangle size={10} />
                                    )}
                                    <span className="item-title">{record.title}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Legend */}
            <div className="calendar-legend">
                {Object.entries(PRIORITY_COLORS).map(([priority, color]) => (
                    <div key={priority} className="legend-item">
                        <span className="legend-dot" style={{ backgroundColor: color }} />
                        <span>{priority}</span>
                    </div>
                ))}
            </div>

            <style jsx>{`
        .maintenance-calendar {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .calendar-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .calendar-header h3 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0;
          font-size: 16px;
          color: #fff;
        }
        
        .header-right {
          display: flex;
          gap: 12px;
          align-items: center;
        }
        
        .nav-buttons {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .nav-buttons button {
          padding: 6px;
          background: rgba(255,255,255,0.05);
          border: none;
          border-radius: 4px;
          color: #aaa;
          cursor: pointer;
        }
        
        .nav-buttons button:hover {
          background: rgba(255,255,255,0.1);
        }
        
        .date-range {
          font-size: 13px;
          color: #888;
        }
        
        .priority-filter {
          padding: 6px 10px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #ccc;
          font-size: 12px;
        }
        
        .add-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 8px 12px;
          background: rgba(34, 197, 94, 0.2);
          border: none;
          border-radius: 6px;
          color: #22c55e;
          font-size: 12px;
          cursor: pointer;
        }
        
        .add-btn:hover {
          background: rgba(34, 197, 94, 0.3);
        }
        
        .timeline-header {
          display: flex;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .equipment-column {
          width: 150px;
          flex-shrink: 0;
          padding: 10px 16px;
          font-size: 11px;
          color: #888;
          text-transform: uppercase;
          background: rgba(0,0,0,0.2);
        }
        
        .dates-row {
          display: flex;
          flex: 1;
        }
        
        .date-cell {
          flex: 1;
          padding: 8px 4px;
          font-size: 10px;
          color: #888;
          text-align: center;
          border-left: 1px solid rgba(255,255,255,0.05);
        }
        
        .date-cell.weekend {
          background: rgba(255,255,255,0.02);
        }
        
        .timeline-body {
          max-height: 400px;
          overflow-y: auto;
        }
        
        .timeline-row {
          display: flex;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .equipment-cell {
          width: 150px;
          flex-shrink: 0;
          padding: 12px 16px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          background: rgba(0,0,0,0.1);
        }
        
        .fleet-number {
          font-size: 13px;
          font-weight: 600;
          color: #fff;
        }
        
        .equipment-type {
          font-size: 10px;
          color: #666;
          text-transform: capitalize;
        }
        
        .schedule-track {
          flex: 1;
          position: relative;
          height: 50px;
        }
        
        .grid-line {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 1px;
          background: rgba(255,255,255,0.05);
        }
        
        .maintenance-item {
          position: absolute;
          top: 8px;
          bottom: 8px;
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 0 8px;
          border-radius: 4px;
          cursor: pointer;
          overflow: hidden;
          opacity: 0.9;
        }
        
        .maintenance-item:hover {
          opacity: 1;
          z-index: 1;
        }
        
        .maintenance-item.completed {
          opacity: 0.6;
        }
        
        .item-title {
          font-size: 10px;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        .calendar-legend {
          display: flex;
          gap: 16px;
          padding: 12px 20px;
          border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #888;
          text-transform: capitalize;
        }
        
        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: 2px;
        }
      `}</style>
        </div>
    );
};

export default MaintenanceCalendar;
