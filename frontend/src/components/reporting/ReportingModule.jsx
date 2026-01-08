/**
 * ReportingModule.jsx
 * 
 * Unified reporting module with tabs for Dashboard, Query Builder, and Product Specs.
 */

import React, { useState, useEffect } from 'react';
import { BarChart2, Database, Package, FileText, Search } from 'lucide-react';
import Dashboard from './Dashboard';
import QueryBuilder from './QueryBuilder';
import ProductSpecDemandUI from './ProductSpecDemandUI';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const TabButton = ({ active, icon: Icon, label, onClick }) => (
    <button
        onClick={onClick}
        className={`
            flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all border-b-2
            ${active
                ? 'text-blue-400 border-blue-400 bg-blue-400/10'
                : 'text-slate-400 border-transparent hover:text-slate-200 hover:bg-slate-800/50'
            }
        `}
    >
        <Icon size={16} />
        {label}
    </button>
);

const ReportingModule = ({ scheduleVersionId, siteId }) => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [availableTables, setAvailableTables] = useState([]);
    const [queryResult, setQueryResult] = useState(null);
    const [isQueryLoading, setIsQueryLoading] = useState(false);

    // Fetch available tables for Query Builder
    useEffect(() => {
        fetchAvailableTables();
    }, []);

    const fetchAvailableTables = async () => {
        try {
            const res = await axios.get(`${API_BASE}/reporting/tables`);
            setAvailableTables(res.data);
        } catch (e) {
            // Use mock data if endpoint not available
            setAvailableTables([
                {
                    tableName: 'tasks', columnCount: 8, columns: [
                        { columnName: 'task_id', dataType: 'string' },
                        { columnName: 'resource_id', dataType: 'string' },
                        { columnName: 'planned_quantity', dataType: 'number' },
                        { columnName: 'actual_quantity', dataType: 'number' },
                        { columnName: 'period_id', dataType: 'string' },
                        { columnName: 'status', dataType: 'string' },
                        { columnName: 'created_at', dataType: 'datetime' },
                        { columnName: 'notes', dataType: 'string' }
                    ]
                },
                {
                    tableName: 'load_tickets', columnCount: 6, columns: [
                        { columnName: 'ticket_id', dataType: 'string' },
                        { columnName: 'tonnes', dataType: 'number' },
                        { columnName: 'origin', dataType: 'string' },
                        { columnName: 'destination', dataType: 'string' },
                        { columnName: 'material_type', dataType: 'string' },
                        { columnName: 'timestamp', dataType: 'datetime' }
                    ]
                },
                {
                    tableName: 'equipment', columnCount: 5, columns: [
                        { columnName: 'equipment_id', dataType: 'string' },
                        { columnName: 'fleet_number', dataType: 'string' },
                        { columnName: 'equipment_type', dataType: 'string' },
                        { columnName: 'status', dataType: 'string' },
                        { columnName: 'operating_hours', dataType: 'number' }
                    ]
                },
                {
                    tableName: 'stockpiles', columnCount: 4, columns: [
                        { columnName: 'stockpile_id', dataType: 'string' },
                        { columnName: 'name', dataType: 'string' },
                        { columnName: 'current_tonnes', dataType: 'number' },
                        { columnName: 'capacity', dataType: 'number' }
                    ]
                }
            ]);
        }
    };

    const handleQueryExecute = async (queryConfig) => {
        setIsQueryLoading(true);
        try {
            const res = await axios.post(`${API_BASE}/reporting/query`, queryConfig);
            setQueryResult({
                success: true,
                columns: res.data.columns || Object.keys(res.data.rows[0] || {}),
                rows: res.data.rows || res.data,
                rowCount: res.data.rows?.length || res.data.length
            });
        } catch (e) {
            // Mock result for demo
            setQueryResult({
                success: true,
                columns: queryConfig.select_columns,
                rows: [
                    Object.fromEntries(queryConfig.select_columns.map(c => [c, 'Sample Data']))
                ],
                rowCount: 1
            });
        } finally {
            setIsQueryLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col bg-slate-900">
            {/* Tab Bar */}
            <div className="flex border-b border-slate-700 bg-slate-950/50">
                <TabButton
                    active={activeTab === 'dashboard'}
                    icon={BarChart2}
                    label="Production Dashboard"
                    onClick={() => setActiveTab('dashboard')}
                />
                <TabButton
                    active={activeTab === 'query'}
                    icon={Database}
                    label="Query Builder"
                    onClick={() => setActiveTab('query')}
                />
                <TabButton
                    active={activeTab === 'products'}
                    icon={Package}
                    label="Product Demand"
                    onClick={() => setActiveTab('products')}
                />
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
                {activeTab === 'dashboard' && (
                    <Dashboard
                        scheduleVersionId={scheduleVersionId}
                        siteId={siteId}
                    />
                )}

                {activeTab === 'query' && (
                    <div className="h-full p-4">
                        <QueryBuilder
                            availableTables={availableTables}
                            onExecute={handleQueryExecute}
                            isLoading={isQueryLoading}
                            lastResult={queryResult}
                        />
                    </div>
                )}

                {activeTab === 'products' && (
                    <ProductSpecDemandUI siteId={siteId} />
                )}
            </div>
        </div>
    );
};

export default ReportingModule;
