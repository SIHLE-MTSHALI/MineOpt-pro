"""
Report Generator Service - Section 4.6 of Enterprise Specification

Comprehensive reporting service providing:
- Template-based report building
- Data aggregation from schedule results
- Multiple export formats (JSON, CSV, PDF-ready)
- Standard report pack for mining operations
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from dataclasses import dataclass, asdict
from datetime import datetime, date
import json
import csv
import io
import uuid

from ..domain.models_scheduling import ScheduleVersion, Task
from ..domain.models_calendar import Period
from ..domain.models_flow import FlowNode, FlowNetwork
from ..domain.models_resource import Resource, Activity, ActivityArea
from ..domain.models_schedule_results import FlowResult, InventoryBalance
from ..domain.models_wash_table import WashPlantOperatingPoint


@dataclass
class ReportMetadata:
    """Metadata for a generated report."""
    report_id: str
    report_type: str
    title: str
    generated_at: str
    schedule_version_id: Optional[str]
    period_range: Optional[str]
    site_name: Optional[str]


@dataclass
class ReportSection:
    """A section within a report."""
    section_id: str
    title: str
    content_type: str  # table, summary, chart_data
    data: Any


@dataclass
class GeneratedReport:
    """A complete generated report."""
    metadata: ReportMetadata
    sections: List[ReportSection]
    summary: Dict[str, Any]


class ReportGeneratorService:
    """
    Generates standardized reports from schedule data.
    
    Reports:
    - Daily Plan Summary
    - Shift Plan
    - Equipment Utilisation
    - Production by Seam/Material
    - Haulage Routes
    - Stockpile Balances
    - Plant Performance
    - Quality Compliance
    - Planned vs Actual
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # -------------------------------------------------------------------------
    # Core Report Generation
    # -------------------------------------------------------------------------
    
    def generate_report(
        self,
        report_type: str,
        schedule_version_id: str,
        period_ids: List[str] = None,
        options: Dict = None
    ) -> GeneratedReport:
        """
        Generate a report of the specified type.
        
        Available types:
        - daily_summary
        - shift_plan
        - equipment_utilisation
        - production_by_material
        - haulage_routes
        - stockpile_balance
        - plant_performance
        - quality_compliance
        - planned_vs_actual
        """
        options = options or {}
        
        report_generators = {
            'daily_summary': self._generate_daily_summary,
            'shift_plan': self._generate_shift_plan,
            'equipment_utilisation': self._generate_equipment_utilisation,
            'production_by_material': self._generate_production_by_material,
            'haulage_routes': self._generate_haulage_routes,
            'stockpile_balance': self._generate_stockpile_balance,
            'plant_performance': self._generate_plant_performance,
            'quality_compliance': self._generate_quality_compliance,
            'planned_vs_actual': self._generate_planned_vs_actual,
        }
        
        generator = report_generators.get(report_type)
        if not generator:
            return self._generate_empty_report(report_type, schedule_version_id)
        
        return generator(schedule_version_id, period_ids, options)
    
    def generate_full_pack(
        self,
        schedule_version_id: str,
        period_ids: List[str] = None
    ) -> List[GeneratedReport]:
        """Generate all standard reports as a pack."""
        report_types = [
            'daily_summary',
            'equipment_utilisation',
            'production_by_material',
            'stockpile_balance',
            'plant_performance',
            'quality_compliance'
        ]
        
        reports = []
        for rtype in report_types:
            try:
                report = self.generate_report(rtype, schedule_version_id, period_ids)
                reports.append(report)
            except Exception as e:
                # Add error placeholder
                reports.append(self._generate_error_report(rtype, str(e)))
        
        return reports
    
    # -------------------------------------------------------------------------
    # Daily Summary Report
    # -------------------------------------------------------------------------
    
    def _generate_daily_summary(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate daily plan summary report."""
        schedule = self._get_schedule(schedule_version_id)
        
        # Get tasks for periods
        task_query = self.db.query(Task)\
            .filter(Task.schedule_version_id == schedule_version_id)
        if period_ids:
            task_query = task_query.filter(Task.period_id.in_(period_ids))
        tasks = task_query.all()
        
        # Aggregate by activity
        activity_summary = {}
        total_tonnes = 0
        
        for task in tasks:
            activity_name = task.activity_name or 'Unknown'
            if activity_name not in activity_summary:
                activity_summary[activity_name] = {
                    'activity': activity_name,
                    'total_tonnes': 0,
                    'task_count': 0,
                    'resources': set()
                }
            activity_summary[activity_name]['total_tonnes'] += task.quantity_tonnes or 0
            activity_summary[activity_name]['task_count'] += 1
            if task.resource_id:
                activity_summary[activity_name]['resources'].add(task.resource_id)
            total_tonnes += task.quantity_tonnes or 0
        
        # Convert sets to counts
        activity_data = []
        for k, v in activity_summary.items():
            activity_data.append({
                'activity': v['activity'],
                'total_tonnes': round(v['total_tonnes'], 0),
                'task_count': v['task_count'],
                'resource_count': len(v['resources'])
            })
        
        sections = [
            ReportSection(
                section_id='activity_summary',
                title='Activity Summary',
                content_type='table',
                data=activity_data
            )
        ]
        
        metadata = self._create_metadata(
            'daily_summary', 'Daily Plan Summary', schedule_version_id
        )
        
        return GeneratedReport(
            metadata=metadata,
            sections=sections,
            summary={
                'total_tonnes': round(total_tonnes, 0),
                'total_tasks': len(tasks),
                'activities': len(activity_summary)
            }
        )
    
    # -------------------------------------------------------------------------
    # Shift Plan Report
    # -------------------------------------------------------------------------
    
    def _generate_shift_plan(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate shift-level plan document."""
        task_query = self.db.query(Task)\
            .filter(Task.schedule_version_id == schedule_version_id)\
            .order_by(Task.period_id, Task.start_offset_hours)
        
        if period_ids:
            task_query = task_query.filter(Task.period_id.in_(period_ids))
        
        tasks = task_query.all()
        
        # Group by period (shift)
        shifts = {}
        for task in tasks:
            period_id = task.period_id
            if period_id not in shifts:
                shifts[period_id] = []
            shifts[period_id].append({
                'resource': task.resource_id,
                'activity': task.activity_name,
                'area': task.activity_area_id,
                'destination': task.destination_node_id,
                'tonnes': round(task.quantity_tonnes or 0, 0),
                'start_hour': task.start_offset_hours,
                'duration': task.duration_hours
            })
        
        sections = [
            ReportSection(
                section_id=f'shift_{pid}',
                title=f'Shift: {pid}',
                content_type='table',
                data=task_list
            )
            for pid, task_list in shifts.items()
        ]
        
        metadata = self._create_metadata(
            'shift_plan', 'Shift Plan', schedule_version_id
        )
        
        return GeneratedReport(
            metadata=metadata,
            sections=sections,
            summary={'shift_count': len(shifts), 'total_tasks': len(tasks)}
        )
    
    # -------------------------------------------------------------------------
    # Equipment Utilisation Report
    # -------------------------------------------------------------------------
    
    def _generate_equipment_utilisation(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate equipment utilisation report."""
        task_query = self.db.query(Task)\
            .filter(Task.schedule_version_id == schedule_version_id)
        if period_ids:
            task_query = task_query.filter(Task.period_id.in_(period_ids))
        tasks = task_query.all()
        
        # Aggregate by resource
        resource_stats = {}
        for task in tasks:
            rid = task.resource_id or 'Unassigned'
            if rid not in resource_stats:
                resource_stats[rid] = {
                    'resource_id': rid,
                    'scheduled_hours': 0,
                    'total_tonnes': 0,
                    'task_count': 0
                }
            resource_stats[rid]['scheduled_hours'] += task.duration_hours or 0
            resource_stats[rid]['total_tonnes'] += task.quantity_tonnes or 0
            resource_stats[rid]['task_count'] += 1
        
        # Calculate utilisation (assume 12hr shifts)
        shift_hours = len(set(t.period_id for t in tasks)) * 12
        resource_data = []
        for rs in resource_stats.values():
            utilisation = (rs['scheduled_hours'] / shift_hours * 100) if shift_hours > 0 else 0
            resource_data.append({
                'resource': rs['resource_id'],
                'scheduled_hours': round(rs['scheduled_hours'], 1),
                'total_tonnes': round(rs['total_tonnes'], 0),
                'task_count': rs['task_count'],
                'utilisation_pct': round(utilisation, 1)
            })
        
        sections = [
            ReportSection(
                section_id='equipment_utilisation',
                title='Equipment Utilisation',
                content_type='table',
                data=resource_data
            )
        ]
        
        avg_utilisation = sum(r['utilisation_pct'] for r in resource_data) / len(resource_data) if resource_data else 0
        
        return GeneratedReport(
            metadata=self._create_metadata('equipment_utilisation', 'Equipment Utilisation Report', schedule_version_id),
            sections=sections,
            summary={
                'resource_count': len(resource_stats),
                'average_utilisation': round(avg_utilisation, 1)
            }
        )
    
    # -------------------------------------------------------------------------
    # Production by Material Report
    # -------------------------------------------------------------------------
    
    def _generate_production_by_material(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate production breakdown by material/seam."""
        flow_query = self.db.query(FlowResult)\
            .filter(FlowResult.schedule_version_id == schedule_version_id)
        if period_ids:
            flow_query = flow_query.filter(FlowResult.period_id.in_(period_ids))
        flows = flow_query.all()
        
        material_stats = {}
        for flow in flows:
            mat = flow.material_type_id or 'Unknown'
            if mat not in material_stats:
                material_stats[mat] = {
                    'material_type': mat,
                    'total_tonnes': 0,
                    'flow_count': 0,
                    'quality_sum': {},
                    'quality_weight': 0
                }
            material_stats[mat]['total_tonnes'] += flow.tonnes
            material_stats[mat]['flow_count'] += 1
            
            # Accumulate quality for weighted average
            if flow.quality_vector:
                for k, v in flow.quality_vector.items():
                    if k not in material_stats[mat]['quality_sum']:
                        material_stats[mat]['quality_sum'][k] = 0
                    material_stats[mat]['quality_sum'][k] += v * flow.tonnes
                material_stats[mat]['quality_weight'] += flow.tonnes
        
        # Calculate weighted average qualities
        material_data = []
        for ms in material_stats.values():
            avg_quality = {}
            if ms['quality_weight'] > 0:
                for k, v in ms['quality_sum'].items():
                    avg_quality[k] = round(v / ms['quality_weight'], 2)
            material_data.append({
                'material_type': ms['material_type'],
                'total_tonnes': round(ms['total_tonnes'], 0),
                'flow_count': ms['flow_count'],
                'avg_quality': avg_quality
            })
        
        return GeneratedReport(
            metadata=self._create_metadata('production_by_material', 'Production by Material', schedule_version_id),
            sections=[ReportSection('material_breakdown', 'Material Breakdown', 'table', material_data)],
            summary={'material_types': len(material_stats), 'total_tonnes': sum(m['total_tonnes'] for m in material_data)}
        )
    
    # -------------------------------------------------------------------------
    # Haulage Routes Report
    # -------------------------------------------------------------------------
    
    def _generate_haulage_routes(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate haulage route tonnes report."""
        flow_query = self.db.query(FlowResult)\
            .filter(FlowResult.schedule_version_id == schedule_version_id)
        if period_ids:
            flow_query = flow_query.filter(FlowResult.period_id.in_(period_ids))
        flows = flow_query.all()
        
        route_stats = {}
        for flow in flows:
            route_key = f"{flow.from_node_id} → {flow.to_node_id}"
            if route_key not in route_stats:
                route_stats[route_key] = {
                    'route': route_key,
                    'from_node': flow.from_node_id,
                    'to_node': flow.to_node_id,
                    'total_tonnes': 0,
                    'trip_count': 0
                }
            route_stats[route_key]['total_tonnes'] += flow.tonnes
            route_stats[route_key]['trip_count'] += 1
        
        route_data = sorted(route_stats.values(), key=lambda x: -x['total_tonnes'])
        
        return GeneratedReport(
            metadata=self._create_metadata('haulage_routes', 'Haulage Routes Report', schedule_version_id),
            sections=[ReportSection('routes', 'Haulage Routes', 'table', route_data)],
            summary={'route_count': len(route_stats), 'total_tonnes': sum(r['total_tonnes'] for r in route_data)}
        )
    
    # -------------------------------------------------------------------------
    # Stockpile Balance Report
    # -------------------------------------------------------------------------
    
    def _generate_stockpile_balance(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate ROM and product stockpile balance report."""
        balance_query = self.db.query(InventoryBalance)\
            .filter(InventoryBalance.schedule_version_id == schedule_version_id)\
            .order_by(InventoryBalance.node_id, InventoryBalance.period_id)
        balances = balance_query.all()
        
        # Group by stockpile
        stockpile_data = {}
        for bal in balances:
            nid = bal.node_id
            if nid not in stockpile_data:
                stockpile_data[nid] = []
            stockpile_data[nid].append({
                'period': bal.period_id,
                'opening': round(bal.opening_tonnes, 0),
                'additions': round(bal.additions_tonnes, 0),
                'reclaim': round(bal.reclaim_tonnes, 0),
                'closing': round(bal.closing_tonnes, 0)
            })
        
        sections = [
            ReportSection(
                section_id=f'stockpile_{nid}',
                title=f'Stockpile: {nid}',
                content_type='table',
                data=periods
            )
            for nid, periods in stockpile_data.items()
        ]
        
        return GeneratedReport(
            metadata=self._create_metadata('stockpile_balance', 'Stockpile Balance Report', schedule_version_id),
            sections=sections,
            summary={'stockpile_count': len(stockpile_data)}
        )
    
    # -------------------------------------------------------------------------
    # Plant Performance Report
    # -------------------------------------------------------------------------
    
    def _generate_plant_performance(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate wash plant performance report."""
        op_query = self.db.query(WashPlantOperatingPoint)\
            .filter(WashPlantOperatingPoint.schedule_version_id == schedule_version_id)
        if period_ids:
            op_query = op_query.filter(WashPlantOperatingPoint.period_id.in_(period_ids))
        ops = op_query.all()
        
        plant_data = []
        total_feed = 0
        total_product = 0
        
        for op in ops:
            plant_data.append({
                'period': op.period_id,
                'plant': op.plant_node_id,
                'feed_tonnes': round(op.feed_tonnes, 0),
                'product_tonnes': round(op.product_tonnes, 0),
                'reject_tonnes': round(op.reject_tonnes, 0),
                'yield_pct': round(op.yield_fraction * 100, 1),
                'cutpoint': op.selected_rd_cutpoint,
                'mode': op.cutpoint_selection_mode
            })
            total_feed += op.feed_tonnes
            total_product += op.product_tonnes
        
        avg_yield = (total_product / total_feed * 100) if total_feed > 0 else 0
        
        return GeneratedReport(
            metadata=self._create_metadata('plant_performance', 'Plant Performance Report', schedule_version_id),
            sections=[ReportSection('plant_ops', 'Plant Operations', 'table', plant_data)],
            summary={
                'total_feed': round(total_feed, 0),
                'total_product': round(total_product, 0),
                'average_yield': round(avg_yield, 1)
            }
        )
    
    # -------------------------------------------------------------------------
    # Quality Compliance Report
    # -------------------------------------------------------------------------
    
    def _generate_quality_compliance(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate quality compliance report."""
        op_query = self.db.query(WashPlantOperatingPoint)\
            .filter(WashPlantOperatingPoint.schedule_version_id == schedule_version_id)
        ops = op_query.all()
        
        compliance_data = []
        for op in ops:
            if op.product_quality_vector:
                for field, value in op.product_quality_vector.items():
                    compliance_data.append({
                        'period': op.period_id,
                        'plant': op.plant_node_id,
                        'quality_field': field,
                        'value': round(value, 2),
                        'product_tonnes': round(op.product_tonnes, 0)
                    })
        
        return GeneratedReport(
            metadata=self._create_metadata('quality_compliance', 'Quality Compliance Report', schedule_version_id),
            sections=[ReportSection('quality_data', 'Product Quality', 'table', compliance_data)],
            summary={'data_points': len(compliance_data)}
        )
    
    # -------------------------------------------------------------------------
    # Planned vs Actual Report
    # -------------------------------------------------------------------------
    
    def _generate_planned_vs_actual(
        self,
        schedule_version_id: str,
        period_ids: List[str],
        options: Dict
    ) -> GeneratedReport:
        """Generate planned vs actual reconciliation report."""
        
        # Get schedule version
        version = self.db.query(ScheduleVersion).filter(
            ScheduleVersion.version_id == schedule_version_id
        ).first()
        
        if not version:
            return self._generate_error_report('planned_vs_actual', 'Schedule version not found')
        
        # Get scheduled tasks
        task_query = self.db.query(ScheduledTask).filter(
            ScheduledTask.schedule_version_id == schedule_version_id
        )
        if period_ids:
            task_query = task_query.filter(ScheduledTask.period_id.in_(period_ids))
        tasks = task_query.all()
        
        # Get flow results for actuals
        flow_query = self.db.query(FlowResult).filter(
            FlowResult.schedule_version_id == schedule_version_id
        )
        if period_ids:
            flow_query = flow_query.filter(FlowResult.period_id.in_(period_ids))
        flows = flow_query.all()
        
        # Aggregate by period
        planned_by_period = {}
        actual_by_period = {}
        
        for task in tasks:
            pid = task.period_id
            if pid not in planned_by_period:
                planned_by_period[pid] = {'tonnes': 0, 'tasks': 0}
            planned_by_period[pid]['tonnes'] += task.scheduled_quantity or 0
            planned_by_period[pid]['tasks'] += 1
        
        for flow in flows:
            pid = flow.period_id
            if pid not in actual_by_period:
                actual_by_period[pid] = {'tonnes': 0, 'flows': 0}
            actual_by_period[pid]['tonnes'] += flow.quantity_tonnes or 0
            actual_by_period[pid]['flows'] += 1
        
        # Build variance table
        all_periods = sorted(set(list(planned_by_period.keys()) + list(actual_by_period.keys())))
        
        variance_data = []
        total_planned = 0
        total_actual = 0
        
        for period_id in all_periods:
            planned = planned_by_period.get(period_id, {}).get('tonnes', 0)
            actual = actual_by_period.get(period_id, {}).get('tonnes', 0)
            variance = actual - planned
            variance_pct = (variance / planned * 100) if planned > 0 else 0
            
            variance_data.append({
                'period_id': period_id,
                'planned_tonnes': round(planned, 1),
                'actual_tonnes': round(actual, 1),
                'variance_tonnes': round(variance, 1),
                'variance_percent': round(variance_pct, 1),
                'status': 'on_target' if abs(variance_pct) < 5 else ('over' if variance > 0 else 'under')
            })
            
            total_planned += planned
            total_actual += actual
        
        # Summary statistics
        total_variance = total_actual - total_planned
        total_variance_pct = (total_variance / total_planned * 100) if total_planned > 0 else 0
        
        # Build chart data for waterfall visualization
        waterfall_data = []
        running_total = total_planned
        waterfall_data.append({'label': 'Planned', 'value': total_planned, 'type': 'total'})
        
        for row in variance_data:
            waterfall_data.append({
                'label': row['period_id'],
                'value': row['variance_tonnes'],
                'type': 'increase' if row['variance_tonnes'] > 0 else 'decrease'
            })
        
        waterfall_data.append({'label': 'Actual', 'value': total_actual, 'type': 'total'})
        
        # Build sections
        sections = [
            ReportSection(
                section_id='summary',
                title='Variance Summary',
                content_type='summary',
                data={
                    'total_planned': round(total_planned, 1),
                    'total_actual': round(total_actual, 1),
                    'total_variance': round(total_variance, 1),
                    'variance_percent': round(total_variance_pct, 1),
                    'periods_analyzed': len(all_periods),
                    'on_target_periods': len([v for v in variance_data if v['status'] == 'on_target']),
                    'over_periods': len([v for v in variance_data if v['status'] == 'over']),
                    'under_periods': len([v for v in variance_data if v['status'] == 'under'])
                }
            ),
            ReportSection(
                section_id='variance_table',
                title='Period Variance Details',
                content_type='table',
                data={
                    'columns': ['Period', 'Planned (t)', 'Actual (t)', 'Variance (t)', 'Variance %', 'Status'],
                    'rows': [
                        [
                            v['period_id'],
                            v['planned_tonnes'],
                            v['actual_tonnes'],
                            v['variance_tonnes'],
                            f"{v['variance_percent']:+.1f}%",
                            v['status']
                        ]
                        for v in variance_data
                    ]
                }
            ),
            ReportSection(
                section_id='waterfall_chart',
                title='Variance Waterfall',
                content_type='chart',
                data={
                    'chart_type': 'waterfall',
                    'data': waterfall_data
                }
            ),
            ReportSection(
                section_id='bar_chart',
                title='Planned vs Actual by Period',
                content_type='chart',
                data={
                    'chart_type': 'grouped_bar',
                    'categories': [v['period_id'] for v in variance_data],
                    'series': [
                        {'name': 'Planned', 'data': [v['planned_tonnes'] for v in variance_data]},
                        {'name': 'Actual', 'data': [v['actual_tonnes'] for v in variance_data]}
                    ]
                }
            )
        ]
        
        return GeneratedReport(
            metadata=self._create_metadata('planned_vs_actual', 'Planned vs Actual Reconciliation', schedule_version_id),
            sections=sections,
            summary={
                'total_planned': round(total_planned, 1),
                'total_actual': round(total_actual, 1),
                'variance_percent': round(total_variance_pct, 1)
            }
        )
    
    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------
    
    def export_to_json(self, report: GeneratedReport) -> str:
        """Export report to JSON string."""
        return json.dumps({
            'metadata': asdict(report.metadata),
            'sections': [asdict(s) for s in report.sections],
            'summary': report.summary
        }, indent=2, default=str)
    
    def export_to_csv(self, report: GeneratedReport) -> str:
        """Export report tables to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write metadata
        writer.writerow(['Report:', report.metadata.title])
        writer.writerow(['Generated:', report.metadata.generated_at])
        writer.writerow([])
        
        # Write each table section
        for section in report.sections:
            if section.content_type == 'table' and section.data:
                writer.writerow([f'=== {section.title} ==='])
                if section.data:
                    headers = list(section.data[0].keys())
                    writer.writerow(headers)
                    for row in section.data:
                        writer.writerow([row.get(h, '') for h in headers])
                writer.writerow([])
        
        # Write summary
        writer.writerow(['=== Summary ==='])
        for k, v in report.summary.items():
            writer.writerow([k, v])
        
        return output.getvalue()
    
    def export_to_html(self, report: GeneratedReport) -> str:
        """Export report to HTML format (for PDF conversion)."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.metadata.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .meta {{ color: #888; font-size: 0.9em; }}
        .summary {{ background: #f9f9f9; padding: 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>{report.metadata.title}</h1>
    <p class="meta">Generated: {report.metadata.generated_at}</p>
"""
        for section in report.sections:
            html += f"<h2>{section.title}</h2>"
            if section.content_type == 'table' and section.data:
                html += "<table><tr>"
                headers = list(section.data[0].keys())
                for h in headers:
                    html += f"<th>{h}</th>"
                html += "</tr>"
                for row in section.data:
                    html += "<tr>"
                    for h in headers:
                        val = row.get(h, '')
                        if isinstance(val, dict):
                            val = json.dumps(val)
                        html += f"<td>{val}</td>"
                    html += "</tr>"
                html += "</table>"
            elif section.content_type == 'summary':
                html += f"<p>{section.data}</p>"
        
        html += '<div class="summary"><h2>Summary</h2><ul>'
        for k, v in report.summary.items():
            html += f"<li><strong>{k}:</strong> {v}</li>"
        html += "</ul></div></body></html>"
        
        return html
    
    def export_to_pdf(self, report: GeneratedReport) -> bytes:
        """
        Export report to PDF format.
        
        Uses WeasyPrint to convert HTML to a styled PDF document.
        Returns PDF as bytes for streaming or saving.
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF export. "
                "Install with: pip install weasyprint"
            )
        
        # Generate enhanced HTML for print
        html_content = self._generate_print_html(report)
        
        # Convert to PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
    
    def _generate_print_html(self, report: GeneratedReport) -> str:
        """Generate HTML optimized for PDF printing."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report.metadata.title}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
            @top-center {{
                content: "{report.metadata.title}";
                font-size: 10pt;
                color: #666;
            }}
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
        }}
        
        .header {{
            border-bottom: 2px solid #1e3a5f;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        
        h1 {{
            color: #1e3a5f;
            font-size: 24pt;
            margin: 0 0 10px 0;
        }}
        
        h2 {{
            color: #1e3a5f;
            font-size: 14pt;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            margin-top: 25px;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #333;
            font-size: 12pt;
            margin-top: 15px;
        }}
        
        .meta {{
            color: #666;
            font-size: 10pt;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 9pt;
            page-break-inside: avoid;
        }}
        
        th {{
            background-color: #1e3a5f;
            color: white;
            padding: 8px 6px;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            border: 1px solid #ddd;
            padding: 6px;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-left: 4px solid #1e3a5f;
            padding: 15px 20px;
            margin-top: 30px;
            page-break-inside: avoid;
        }}
        
        .summary-box h2 {{
            color: #1e3a5f;
            margin-top: 0;
            border: none;
            font-size: 13pt;
        }}
        
        .summary-box ul {{
            margin: 0;
            padding-left: 20px;
        }}
        
        .summary-box li {{
            margin: 5px 0;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        
        .kpi-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            text-align: center;
            border-radius: 4px;
        }}
        
        .kpi-value {{
            font-size: 18pt;
            font-weight: bold;
            color: #1e3a5f;
        }}
        
        .kpi-label {{
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }}
        
        .positive {{
            color: #28a745;
        }}
        
        .negative {{
            color: #dc3545;
        }}
        
        .warning {{
            color: #ffc107;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 9pt;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.metadata.title}</h1>
        <p class="meta">
            Generated: {report.metadata.generated_at}<br>
            Schedule Version: {report.metadata.schedule_version_id or 'N/A'}<br>
            Site: {report.metadata.site_name or 'N/A'}
        </p>
    </div>
"""
        
        # Render KPI summary if available
        if report.summary:
            kpi_items = []
            for key, value in report.summary.items():
                if isinstance(value, (int, float)):
                    if 'tonnes' in key.lower() or 'tonnage' in key.lower():
                        kpi_items.append((key, f"{value:,.0f}t"))
                    elif 'cost' in key.lower() or 'value' in key.lower() or 'benefit' in key.lower():
                        kpi_items.append((key, f"${value:,.0f}"))
                    elif 'percent' in key.lower() or '%' in key:
                        kpi_items.append((key, f"{value:.1f}%"))
                    else:
                        kpi_items.append((key, f"{value:,.2f}"))
            
            if kpi_items:
                html += '<div class="kpi-grid">'
                for label, value in kpi_items[:6]:  # Max 6 KPIs
                    html += f'''
                    <div class="kpi-card">
                        <div class="kpi-value">{value}</div>
                        <div class="kpi-label">{label.replace("_", " ").title()}</div>
                    </div>'''
                html += '</div>'
        
        # Render sections
        for section in report.sections:
            html += f'<h2>{section.title}</h2>'
            
            if section.content_type == 'table' and section.data:
                html += '<table><thead><tr>'
                headers = list(section.data[0].keys())
                for h in headers:
                    html += f'<th>{h.replace("_", " ").title()}</th>'
                html += '</tr></thead><tbody>'
                
                for row in section.data:
                    html += '<tr>'
                    for h in headers:
                        val = row.get(h, '')
                        if isinstance(val, dict):
                            val = json.dumps(val)
                        elif isinstance(val, float):
                            val = f"{val:,.2f}"
                        html += f'<td>{val}</td>'
                    html += '</tr>'
                html += '</tbody></table>'
                
            elif section.content_type == 'summary':
                html += f'<p>{section.data}</p>'
                
            elif section.content_type == 'kpi':
                html += '<div class="kpi-grid">'
                if isinstance(section.data, dict):
                    for k, v in section.data.items():
                        html += f'''
                        <div class="kpi-card">
                            <div class="kpi-value">{v}</div>
                            <div class="kpi-label">{k}</div>
                        </div>'''
                html += '</div>'
        
        # Summary box
        if report.summary:
            html += '''
            <div class="summary-box">
                <h2>Summary</h2>
                <ul>'''
            for k, v in report.summary.items():
                if isinstance(v, float):
                    v = f"{v:,.2f}"
                html += f'<li><strong>{k.replace("_", " ").title()}:</strong> {v}</li>'
            html += '''
                </ul>
            </div>'''
        
        # Footer
        html += f'''
    <div class="footer">
        <p>
            Report generated by MineOpt Pro Enterprise | 
            {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
        </p>
    </div>
</body>
</html>'''
        
        return html
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _get_schedule(self, schedule_version_id: str) -> Optional[ScheduleVersion]:
        return self.db.query(ScheduleVersion)\
            .filter(ScheduleVersion.version_id == schedule_version_id)\
            .first()
    
    def _create_metadata(
        self, report_type: str, title: str, schedule_version_id: str
    ) -> ReportMetadata:
        return ReportMetadata(
            report_id=str(uuid.uuid4()),
            report_type=report_type,
            title=title,
            generated_at=datetime.utcnow().isoformat(),
            schedule_version_id=schedule_version_id,
            period_range=None,
            site_name=None
        )
    
    def _generate_empty_report(
        self, report_type: str, schedule_version_id: str
    ) -> GeneratedReport:
        return GeneratedReport(
            metadata=self._create_metadata(report_type, f'Unknown Report: {report_type}', schedule_version_id),
            sections=[],
            summary={'error': 'Unknown report type'}
        )
    
    def _generate_error_report(self, report_type: str, error: str) -> GeneratedReport:
        return GeneratedReport(
            metadata=self._create_metadata(report_type, f'Error: {report_type}', None),
            sections=[],
            summary={'error': error}
        )
