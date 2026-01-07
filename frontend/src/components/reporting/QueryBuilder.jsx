/**
 * QueryBuilder.jsx
 * 
 * Interactive ad-hoc query builder for BI/reporting.
 */

import React, { useState, useEffect } from 'react';
import {
    Database,
    Plus,
    Trash2,
    Play,
    Download,
    Save,
    BarChart2,
    Table
} from 'lucide-react';

const OPERATORS = [
    { value: '=', label: 'Equals' },
    { value: '!=', label: 'Not Equals' },
    { value: '>', label: 'Greater Than' },
    { value: '<', label: 'Less Than' },
    { value: '>=', label: 'Greater or Equal' },
    { value: '<=', label: 'Less or Equal' },
    { value: 'LIKE', label: 'Contains' }
];

const AGGREGATIONS = [
    { value: '', label: 'None' },
    { value: 'SUM', label: 'Sum' },
    { value: 'AVG', label: 'Average' },
    { value: 'COUNT', label: 'Count' },
    { value: 'MIN', label: 'Minimum' },
    { value: 'MAX', label: 'Maximum' }
];

const QueryBuilder = ({
    availableTables = [],
    onExecute,
    onSave,
    isLoading = false,
    lastResult = null,
    className = ''
}) => {
    const [selectedTable, setSelectedTable] = useState('');
    const [tableColumns, setTableColumns] = useState([]);
    const [selectedColumns, setSelectedColumns] = useState([]);
    const [aggregations, setAggregations] = useState({});
    const [groupBy, setGroupBy] = useState([]);
    const [filters, setFilters] = useState([]);
    const [orderBy, setOrderBy] = useState('');
    const [orderDesc, setOrderDesc] = useState(false);
    const [limit, setLimit] = useState(100);
    const [viewMode, setViewMode] = useState('table'); // table, chart

    // Load columns when table changes
    useEffect(() => {
        if (selectedTable) {
            const table = availableTables.find(t => t.tableName === selectedTable);
            if (table && table.columns) {
                setTableColumns(table.columns);
                setSelectedColumns([]);
                setFilters([]);
            }
        }
    }, [selectedTable, availableTables]);

    const toggleColumn = (columnName) => {
        if (selectedColumns.includes(columnName)) {
            setSelectedColumns(prev => prev.filter(c => c !== columnName));
        } else {
            setSelectedColumns(prev => [...prev, columnName]);
        }
    };

    const addFilter = () => {
        setFilters(prev => [...prev, { column: '', operator: '=', value: '' }]);
    };

    const updateFilter = (index, field, value) => {
        setFilters(prev => {
            const updated = [...prev];
            updated[index] = { ...updated[index], [field]: value };
            return updated;
        });
    };

    const removeFilter = (index) => {
        setFilters(prev => prev.filter((_, i) => i !== index));
    };

    const handleExecute = () => {
        onExecute?.({
            table: selectedTable,
            select_columns: selectedColumns,
            aggregations: Object.keys(aggregations).length > 0 ? aggregations : null,
            group_by: groupBy.length > 0 ? groupBy : null,
            filters: filters.filter(f => f.column && f.value),
            order_by: orderBy || null,
            order_desc: orderDesc,
            limit
        });
    };

    return (
        <div className={`query-builder ${className}`}>
            {/* Header */}
            <div className="builder-header">
                <div className="header-left">
                    <Database size={20} />
                    <h3>Query Builder</h3>
                </div>
                <div className="header-right">
                    <button onClick={() => onSave?.()} className="btn-secondary">
                        <Save size={14} />
                        Save Query
                    </button>
                    <button
                        onClick={handleExecute}
                        className="btn-primary"
                        disabled={!selectedTable || selectedColumns.length === 0 || isLoading}
                    >
                        <Play size={14} />
                        {isLoading ? 'Running...' : 'Run Query'}
                    </button>
                </div>
            </div>

            <div className="builder-body">
                {/* Left Panel - Configuration */}
                <div className="config-panel">
                    {/* Table Selection */}
                    <div className="config-section">
                        <label>Select Table</label>
                        <select
                            value={selectedTable}
                            onChange={(e) => setSelectedTable(e.target.value)}
                        >
                            <option value="">Choose a table...</option>
                            {availableTables.map(t => (
                                <option key={t.tableName} value={t.tableName}>
                                    {t.tableName} ({t.columnCount} columns)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Column Selection */}
                    {tableColumns.length > 0 && (
                        <div className="config-section">
                            <label>Select Columns</label>
                            <div className="column-list">
                                {tableColumns.map(col => (
                                    <div key={col.columnName} className="column-item">
                                        <label className="checkbox-label">
                                            <input
                                                type="checkbox"
                                                checked={selectedColumns.includes(col.columnName)}
                                                onChange={() => toggleColumn(col.columnName)}
                                            />
                                            <span>{col.columnName}</span>
                                            <span className="column-type">{col.dataType}</span>
                                        </label>
                                        {selectedColumns.includes(col.columnName) && col.dataType === 'number' && (
                                            <select
                                                value={aggregations[col.columnName] || ''}
                                                onChange={(e) => setAggregations(prev => ({
                                                    ...prev,
                                                    [col.columnName]: e.target.value
                                                }))}
                                                className="agg-select"
                                            >
                                                {AGGREGATIONS.map(a => (
                                                    <option key={a.value} value={a.value}>{a.label}</option>
                                                ))}
                                            </select>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Filters */}
                    <div className="config-section">
                        <div className="section-header">
                            <label>Filters</label>
                            <button onClick={addFilter} className="add-btn">
                                <Plus size={12} /> Add
                            </button>
                        </div>
                        {filters.map((filter, i) => (
                            <div key={i} className="filter-row">
                                <select
                                    value={filter.column}
                                    onChange={(e) => updateFilter(i, 'column', e.target.value)}
                                >
                                    <option value="">Column</option>
                                    {tableColumns.map(c => (
                                        <option key={c.columnName} value={c.columnName}>{c.columnName}</option>
                                    ))}
                                </select>
                                <select
                                    value={filter.operator}
                                    onChange={(e) => updateFilter(i, 'operator', e.target.value)}
                                >
                                    {OPERATORS.map(o => (
                                        <option key={o.value} value={o.value}>{o.label}</option>
                                    ))}
                                </select>
                                <input
                                    type="text"
                                    value={filter.value}
                                    onChange={(e) => updateFilter(i, 'value', e.target.value)}
                                    placeholder="Value"
                                />
                                <button onClick={() => removeFilter(i)} className="remove-btn">
                                    <Trash2 size={12} />
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Order & Limit */}
                    <div className="config-section">
                        <label>Order By</label>
                        <div className="order-row">
                            <select
                                value={orderBy}
                                onChange={(e) => setOrderBy(e.target.value)}
                            >
                                <option value="">None</option>
                                {selectedColumns.map(c => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                            <button
                                className={`order-dir ${orderDesc ? 'desc' : 'asc'}`}
                                onClick={() => setOrderDesc(!orderDesc)}
                            >
                                {orderDesc ? 'DESC' : 'ASC'}
                            </button>
                        </div>
                    </div>

                    <div className="config-section">
                        <label>Limit</label>
                        <input
                            type="number"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                            min={1}
                            max={10000}
                        />
                    </div>
                </div>

                {/* Right Panel - Results */}
                <div className="results-panel">
                    <div className="results-header">
                        <div className="view-toggle">
                            <button
                                className={viewMode === 'table' ? 'active' : ''}
                                onClick={() => setViewMode('table')}
                            >
                                <Table size={14} /> Table
                            </button>
                            <button
                                className={viewMode === 'chart' ? 'active' : ''}
                                onClick={() => setViewMode('chart')}
                            >
                                <BarChart2 size={14} /> Chart
                            </button>
                        </div>
                        {lastResult && (
                            <span className="row-count">{lastResult.rowCount} rows</span>
                        )}
                    </div>

                    {lastResult?.success ? (
                        viewMode === 'table' ? (
                            <div className="results-table-container">
                                <table className="results-table">
                                    <thead>
                                        <tr>
                                            {lastResult.columns.map(col => (
                                                <th key={col}>{col}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {lastResult.rows.slice(0, 100).map((row, i) => (
                                            <tr key={i}>
                                                {lastResult.columns.map(col => (
                                                    <td key={col}>{String(row[col] ?? '')}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="chart-placeholder">
                                <BarChart2 size={48} />
                                <p>Select X and Y columns for chart</p>
                            </div>
                        )
                    ) : lastResult?.error ? (
                        <div className="error-message">{lastResult.error}</div>
                    ) : (
                        <div className="empty-results">
                            <Database size={48} />
                            <p>Run a query to see results</p>
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
        .query-builder {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: 100%;
        }
        
        .builder-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          background: rgba(0,0,0,0.3);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #fff;
        }
        
        .header-left h3 { margin: 0; font-size: 16px; }
        
        .header-right { display: flex; gap: 8px; }
        
        .btn-primary, .btn-secondary {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
        }
        
        .btn-primary {
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color: #fff;
        }
        
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .btn-secondary {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: #ccc;
        }
        
        .builder-body {
          display: flex;
          flex: 1;
          overflow: hidden;
        }
        
        .config-panel {
          width: 300px;
          padding: 16px;
          overflow-y: auto;
          border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        .config-section {
          margin-bottom: 20px;
        }
        
        .config-section > label {
          display: block;
          font-size: 11px;
          color: #888;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        
        .config-section select,
        .config-section input {
          width: 100%;
          padding: 8px 10px;
          background: rgba(0,0,0,0.3);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
        }
        
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .add-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          background: rgba(59,130,246,0.2);
          border: none;
          border-radius: 4px;
          color: #3b82f6;
          font-size: 11px;
          cursor: pointer;
        }
        
        .column-list {
          max-height: 200px;
          overflow-y: auto;
        }
        
        .column-item {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          padding: 6px 0;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 6px;
          flex: 1;
          color: #ccc;
          font-size: 12px;
          cursor: pointer;
        }
        
        .column-type {
          font-size: 10px;
          color: #666;
          padding: 2px 4px;
          background: rgba(255,255,255,0.05);
          border-radius: 3px;
        }
        
        .agg-select {
          width: 80px !important;
          padding: 4px !important;
          font-size: 10px !important;
        }
        
        .filter-row {
          display: flex;
          gap: 4px;
          margin-bottom: 8px;
        }
        
        .filter-row select,
        .filter-row input {
          flex: 1;
          padding: 6px !important;
          font-size: 11px !important;
        }
        
        .remove-btn {
          padding: 6px;
          background: rgba(239,68,68,0.2);
          border: none;
          border-radius: 4px;
          color: #ef4444;
          cursor: pointer;
        }
        
        .order-row {
          display: flex;
          gap: 8px;
        }
        
        .order-dir {
          padding: 6px 12px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 6px;
          color: #aaa;
          font-size: 11px;
          cursor: pointer;
        }
        
        .results-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        
        .results-header {
          display: flex;
          justify-content: space-between;
          padding: 12px 16px;
          background: rgba(0,0,0,0.2);
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .view-toggle {
          display: flex;
          gap: 4px;
        }
        
        .view-toggle button {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 6px 10px;
          background: transparent;
          border: none;
          border-radius: 4px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
        }
        
        .view-toggle button.active {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        
        .row-count {
          font-size: 11px;
          color: #888;
        }
        
        .results-table-container {
          flex: 1;
          overflow: auto;
          padding: 0 16px 16px;
        }
        
        .results-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }
        
        .results-table th {
          text-align: left;
          padding: 8px;
          background: rgba(0,0,0,0.3);
          color: #888;
          font-weight: 500;
          position: sticky;
          top: 0;
        }
        
        .results-table td {
          padding: 8px;
          color: #ccc;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .empty-results,
        .chart-placeholder {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #666;
        }
        
        .error-message {
          padding: 16px;
          color: #ef4444;
        }
      `}</style>
        </div>
    );
};

export default QueryBuilder;
