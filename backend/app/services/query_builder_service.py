"""
Query Builder Service

Ad-hoc query building and execution for BI/reporting.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import json
import logging


class QueryBuilderService:
    """
    Service for building and executing ad-hoc queries.
    
    Provides a safe interface for users to query data without
    direct SQL access.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Define queryable tables and their columns
        self.tables = {
            'load_tickets': {
                'description': 'Material load tickets',
                'columns': {
                    'ticket_id': {'type': 'string', 'description': 'Unique ID'},
                    'truck_fleet_number': {'type': 'string', 'description': 'Truck number'},
                    'origin_name': {'type': 'string', 'description': 'Loading location'},
                    'destination_name': {'type': 'string', 'description': 'Dump location'},
                    'material_type': {'type': 'string', 'description': 'Material classification'},
                    'tonnes': {'type': 'number', 'description': 'Load weight'},
                    'grade_percent': {'type': 'number', 'description': 'Material grade'},
                    'loaded_at': {'type': 'datetime', 'description': 'Load timestamp'}
                }
            },
            'haul_cycles': {
                'description': 'Equipment haul cycles',
                'columns': {
                    'cycle_id': {'type': 'string', 'description': 'Unique ID'},
                    'equipment_id': {'type': 'string', 'description': 'Equipment reference'},
                    'total_cycle_sec': {'type': 'number', 'description': 'Cycle duration'},
                    'loading_sec': {'type': 'number', 'description': 'Loading time'},
                    'travel_loaded_sec': {'type': 'number', 'description': 'Loaded travel time'},
                    'dumping_sec': {'type': 'number', 'description': 'Dumping time'},
                    'payload_tonnes': {'type': 'number', 'description': 'Payload weight'},
                    'cycle_start': {'type': 'datetime', 'description': 'Cycle start time'}
                }
            },
            'equipment': {
                'description': 'Fleet equipment',
                'columns': {
                    'equipment_id': {'type': 'string', 'description': 'Unique ID'},
                    'fleet_number': {'type': 'string', 'description': 'Fleet number'},
                    'equipment_type': {'type': 'string', 'description': 'Equipment type'},
                    'status': {'type': 'string', 'description': 'Current status'},
                    'engine_hours': {'type': 'number', 'description': 'Engine hours'},
                    'payload_tonnes': {'type': 'number', 'description': 'Rated payload'}
                }
            },
            'blast_patterns': {
                'description': 'Drill and blast patterns',
                'columns': {
                    'pattern_id': {'type': 'string', 'description': 'Unique ID'},
                    'bench_name': {'type': 'string', 'description': 'Bench location'},
                    'burden': {'type': 'number', 'description': 'Burden distance'},
                    'spacing': {'type': 'number', 'description': 'Hole spacing'},
                    'hole_depth_m': {'type': 'number', 'description': 'Hole depth'},
                    'powder_factor_kg_bcm': {'type': 'number', 'description': 'Powder factor'},
                    'status': {'type': 'string', 'description': 'Pattern status'}
                }
            },
            'shift_incidents': {
                'description': 'Safety/operational incidents',
                'columns': {
                    'incident_id': {'type': 'string', 'description': 'Unique ID'},
                    'incident_type': {'type': 'string', 'description': 'Incident type'},
                    'severity': {'type': 'string', 'description': 'Severity level'},
                    'title': {'type': 'string', 'description': 'Incident title'},
                    'occurred_at': {'type': 'datetime', 'description': 'Occurrence time'},
                    'status': {'type': 'string', 'description': 'Status'}
                }
            }
        }
        
        # Allowed aggregations
        self.aggregations = ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX']
    
    def list_available_tables(self) -> List[Dict[str, Any]]:
        """List tables available for querying."""
        return [
            {
                'table_name': name,
                'description': info['description'],
                'column_count': len(info['columns'])
            }
            for name, info in self.tables.items()
        ]
    
    def list_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """List columns for a table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} not available")
        
        return [
            {
                'column_name': name,
                'data_type': info['type'],
                'description': info['description']
            }
            for name, info in self.tables[table_name]['columns'].items()
        ]
    
    def build_query(
        self,
        table: str,
        select_columns: List[str],
        aggregations: Optional[Dict[str, str]] = None,
        group_by: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: int = 1000
    ) -> str:
        """
        Build a safe SQL query from parameters.
        
        filters: List of {column, operator, value}
        aggregations: {column: aggregation_function}
        """
        if table not in self.tables:
            raise ValueError(f"Invalid table: {table}")
        
        valid_columns = set(self.tables[table]['columns'].keys())
        
        # Validate columns
        for col in select_columns:
            if col not in valid_columns:
                raise ValueError(f"Invalid column: {col}")
        
        # Build SELECT clause
        select_parts = []
        for col in select_columns:
            if aggregations and col in aggregations:
                agg = aggregations[col].upper()
                if agg not in self.aggregations:
                    raise ValueError(f"Invalid aggregation: {agg}")
                select_parts.append(f"{agg}({col}) as {col}_{agg.lower()}")
            else:
                select_parts.append(col)
        
        select_clause = ", ".join(select_parts)
        
        # Build WHERE clause
        where_parts = []
        if filters:
            for f in filters:
                col = f.get('column')
                op = f.get('operator', '=')
                val = f.get('value')
                
                if col not in valid_columns:
                    raise ValueError(f"Invalid filter column: {col}")
                
                if op not in ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN']:
                    raise ValueError(f"Invalid operator: {op}")
                
                if op == 'IN' and isinstance(val, list):
                    quoted = [f"'{v}'" for v in val]
                    where_parts.append(f"{col} IN ({', '.join(quoted)})")
                elif op == 'LIKE':
                    where_parts.append(f"{col} LIKE '%{val}%'")
                elif isinstance(val, str):
                    where_parts.append(f"{col} {op} '{val}'")
                else:
                    where_parts.append(f"{col} {op} {val}")
        
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        
        # Build GROUP BY clause
        group_clause = ""
        if group_by:
            for col in group_by:
                if col not in valid_columns:
                    raise ValueError(f"Invalid group by column: {col}")
            group_clause = f"GROUP BY {', '.join(group_by)}"
        
        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            direction = "DESC" if order_desc else "ASC"
            order_clause = f"ORDER BY {order_by} {direction}"
        
        # Assemble query
        query = f"""
            SELECT {select_clause}
            FROM {table}
            WHERE {where_clause}
            {group_clause}
            {order_clause}
            LIMIT {min(limit, 10000)}
        """
        
        return query.strip()
    
    def execute_query(
        self,
        table: str,
        select_columns: List[str],
        aggregations: Optional[Dict[str, str]] = None,
        group_by: Optional[List[str]] = None,
        filters: Optional[List[Dict]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Execute query and return results."""
        try:
            query = self.build_query(
                table, select_columns, aggregations,
                group_by, filters, order_by, order_desc, limit
            )
            
            self.logger.info(f"Executing query: {query}")
            
            result = self.db.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
            
            return {
                'success': True,
                'query': query,
                'columns': list(columns),
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows),
                'executed_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
    
    def save_query(
        self,
        user_id: str,
        name: str,
        description: str,
        query_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save query configuration for reuse."""
        # In production, save to database
        return {
            'query_id': f"query_{datetime.utcnow().timestamp()}",
            'name': name,
            'description': description,
            'config': query_config,
            'created_by': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def get_chart_data(
        self,
        query_result: Dict[str, Any],
        x_column: str,
        y_column: str,
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """Format query results for charting."""
        if not query_result.get('success'):
            return {'error': 'Query failed'}
        
        rows = query_result.get('rows', [])
        
        return {
            'chart_type': chart_type,
            'labels': [row.get(x_column) for row in rows],
            'datasets': [{
                'label': y_column,
                'data': [row.get(y_column) for row in rows]
            }]
        }


def get_query_builder_service(db: Session) -> QueryBuilderService:
    return QueryBuilderService(db)
