"""
Reporting Router - API endpoints for report generation and export

Provides endpoints for:
- Dashboard statistics
- Report generation (multiple types)
- Full report pack generation
- Export in JSON, CSV, HTML formats
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..domain import models_scheduling, models_resource, models_calendar
from ..services.report_generator_service import ReportGeneratorService
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/reporting", tags=["Reporting"])


# =============================================================================
# Query Builder Endpoints
# =============================================================================

@router.get("/tables")
def get_available_tables(db: Session = Depends(get_db)):
    """Get list of available database tables for Query Builder."""
    return [
        {
            "tableName": "tasks",
            "columnCount": 8,
            "columns": [
                {"columnName": "task_id", "dataType": "string"},
                {"columnName": "resource_id", "dataType": "string"},
                {"columnName": "planned_quantity", "dataType": "number"},
                {"columnName": "actual_quantity", "dataType": "number"},
                {"columnName": "period_id", "dataType": "string"},
                {"columnName": "status", "dataType": "string"},
                {"columnName": "created_at", "dataType": "datetime"},
                {"columnName": "activity_area_id", "dataType": "string"}
            ]
        },
        {
            "tableName": "schedule_versions",
            "columnCount": 5,
            "columns": [
                {"columnName": "version_id", "dataType": "string"},
                {"columnName": "site_id", "dataType": "string"},
                {"columnName": "name", "dataType": "string"},
                {"columnName": "status", "dataType": "string"},
                {"columnName": "created_at", "dataType": "datetime"}
            ]
        },
        {
            "tableName": "resources",
            "columnCount": 6,
            "columns": [
                {"columnName": "resource_id", "dataType": "string"},
                {"columnName": "name", "dataType": "string"},
                {"columnName": "resource_type", "dataType": "string"},
                {"columnName": "base_rate", "dataType": "number"},
                {"columnName": "cost_per_hour", "dataType": "number"},
                {"columnName": "site_id", "dataType": "string"}
            ]
        },
        {
            "tableName": "activity_areas",
            "columnCount": 6,
            "columns": [
                {"columnName": "area_id", "dataType": "string"},
                {"columnName": "name", "dataType": "string"},
                {"columnName": "bench_level", "dataType": "string"},
                {"columnName": "elevation_rl", "dataType": "number"},
                {"columnName": "priority", "dataType": "number"},
                {"columnName": "is_locked", "dataType": "boolean"}
            ]
        },
        {
            "tableName": "periods",
            "columnCount": 5,
            "columns": [
                {"columnName": "period_id", "dataType": "string"},
                {"columnName": "calendar_id", "dataType": "string"},
                {"columnName": "start_datetime", "dataType": "datetime"},
                {"columnName": "end_datetime", "dataType": "datetime"},
                {"columnName": "group_shift", "dataType": "string"}
            ]
        },
        {
            "tableName": "flow_nodes",
            "columnCount": 5,
            "columns": [
                {"columnName": "node_id", "dataType": "string"},
                {"columnName": "name", "dataType": "string"},
                {"columnName": "node_type", "dataType": "string"},
                {"columnName": "capacity", "dataType": "number"},
                {"columnName": "network_id", "dataType": "string"}
            ]
        }
    ]


@router.post("/query")
def execute_query(query: dict, db: Session = Depends(get_db)):
    """Execute an ad-hoc query from Query Builder."""
    # This is a simplified query executor
    # In production, this would parse and validate the query safely
    table_name = query.get("from_table", "tasks")
    columns = query.get("select_columns", ["*"])
    limit = query.get("limit", 100)
    
    # For safety, we only allow predefined tables
    allowed_tables = {
        "tasks": models_scheduling.Task,
        "schedule_versions": models_scheduling.ScheduleVersion,
        "resources": models_resource.Resource,
        "activity_areas": models_resource.ActivityArea,
        "periods": models_calendar.Period
    }
    
    if table_name not in allowed_tables:
        return {"error": f"Table '{table_name}' not available", "rows": [], "columns": columns}
    
    model = allowed_tables[table_name]
    results = db.query(model).limit(limit).all()
    
    # Convert to dict representation
    rows = []
    for r in results:
        row = {}
        for col in columns:
            if col == "*":
                # Get all attributes
                for key in dir(r):
                    if not key.startswith('_') and not callable(getattr(r, key)):
                        val = getattr(r, key, None)
                        if not isinstance(val, (list, dict)) or isinstance(val, (str, int, float, bool, type(None))):
                            row[key] = val
            elif hasattr(r, col):
                row[col] = getattr(r, col, None)
        rows.append(row)
    
    return {
        "columns": columns if columns != ["*"] else list(rows[0].keys()) if rows else [],
        "rows": rows,
        "rowCount": len(rows)
    }


# =============================================================================
# Pydantic Models
# =============================================================================

class ReportRequest(BaseModel):
    """Request for generating a report."""
    schedule_version_id: str
    period_ids: Optional[List[str]] = None
    options: Optional[Dict] = None


class ReportPackRequest(BaseModel):
    """Request for generating full report pack."""
    schedule_version_id: str
    period_ids: Optional[List[str]] = None


# =============================================================================
# Dashboard Statistics (Legacy)
# =============================================================================

@router.get("/dashboard/{schedule_version_id}")
def get_dashboard_stats(schedule_version_id: str, db: Session = Depends(get_db)):
    """Get dashboard statistics for a schedule version."""
    tasks = db.query(models_scheduling.Task)\
        .filter(models_scheduling.Task.schedule_version_id == schedule_version_id)\
        .all()
    
    total_tons = 0
    coal_tons = 0
    waste_tons = 0
    
    area_ids = [t.activity_area_id for t in tasks if t.activity_area_id]
    areas = db.query(models_resource.ActivityArea)\
        .filter(models_resource.ActivityArea.area_id.in_(area_ids)).all()
    area_map = {a.area_id: a for a in areas}
    
    period_ids = [t.period_id for t in tasks if t.period_id]
    periods = db.query(models_calendar.Period)\
        .filter(models_calendar.Period.period_id.in_(period_ids)).all()
    period_map = {p.period_id: p for p in periods}
    
    production_by_period: Dict[str, Dict[str, Any]] = {}

    for task in tasks:
        qty = task.planned_quantity or 0
        total_tons += qty
        
        is_coal = False
        if task.activity_area_id and task.activity_area_id in area_map:
            area = area_map[task.activity_area_id]
            if area.slice_states and len(area.slice_states) > 0:
                mat_name = area.slice_states[0].get('material_name', '')
                if 'Coal' in mat_name:
                     is_coal = True
        
        if is_coal:
            coal_tons += qty
        else:
            waste_tons += qty
            
        p_id = task.period_id
        if p_id and p_id in period_map:
            period = period_map[p_id]
            p_label = f"{period.group_day} {period.group_shift}"
            
            if p_label not in production_by_period:
                production_by_period[p_label] = {
                    "name": p_label, "coal": 0, "waste": 0, 
                    "total": 0, "sort_dt": period.start_datetime
                }
            
            production_by_period[p_label]["total"] += qty
            if is_coal:
                production_by_period[p_label]["coal"] += qty
            else:
                production_by_period[p_label]["waste"] += qty
                
    stipping_ratio = round(waste_tons / coal_tons, 2) if coal_tons > 0 else 0
    sorted_periods = sorted(production_by_period.values(), key=lambda x: x["sort_dt"])
    chart_data = [{k:v for k,v in item.items() if k != 'sort_dt'} for item in sorted_periods]

    return {
        "total_tons": total_tons,
        "coal_tons": coal_tons,
        "waste_tons": waste_tons,
        "stripping_ratio": stipping_ratio,
        "chart_data": chart_data
    }


# =============================================================================
# Report Generation Endpoints
# =============================================================================

@router.get("/types")
def get_report_types():
    """Get list of available report types."""
    return {
        "report_types": [
            {"type": "daily_summary", "name": "Daily Plan Summary"},
            {"type": "shift_plan", "name": "Shift Plan Document"},
            {"type": "equipment_utilisation", "name": "Equipment Utilisation Report"},
            {"type": "production_by_material", "name": "Production by Material/Seam"},
            {"type": "haulage_routes", "name": "Haulage Route Tonnes Report"},
            {"type": "stockpile_balance", "name": "ROM & Product Stockpile Balance"},
            {"type": "plant_performance", "name": "Plant Performance Report"},
            {"type": "quality_compliance", "name": "Quality Compliance Report"},
            {"type": "planned_vs_actual", "name": "Planned vs Actual Reconciliation"}
        ]
    }


@router.post("/generate/{report_type}")
def generate_report(
    report_type: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a specific report type."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        report_type=report_type,
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids,
        options=request.options
    )
    
    return {
        "metadata": {
            "report_id": report.metadata.report_id,
            "report_type": report.metadata.report_type,
            "title": report.metadata.title,
            "generated_at": report.metadata.generated_at
        },
        "sections": [
            {
                "section_id": s.section_id,
                "title": s.title,
                "content_type": s.content_type,
                "data": s.data
            }
            for s in report.sections
        ],
        "summary": report.summary
    }


@router.post("/pack")
def generate_report_pack(
    request: ReportPackRequest,
    db: Session = Depends(get_db)
):
    """Generate full report pack with all standard reports."""
    service = ReportGeneratorService(db)
    reports = service.generate_full_pack(
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids
    )
    
    return {
        "pack_id": f"pack-{request.schedule_version_id[:8]}",
        "report_count": len(reports),
        "reports": [
            {
                "report_type": r.metadata.report_type,
                "title": r.metadata.title,
                "section_count": len(r.sections),
                "summary": r.summary
            }
            for r in reports
        ]
    }


# =============================================================================
# Export Endpoints
# =============================================================================

@router.post("/export/json/{report_type}")
def export_report_json(
    report_type: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Export a report as JSON."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        report_type=report_type,
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids
    )
    
    json_content = service.export_to_json(report)
    return PlainTextResponse(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={report_type}.json"}
    )


@router.post("/export/csv/{report_type}")
def export_report_csv(
    report_type: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Export a report as CSV."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        report_type=report_type,
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids
    )
    
    csv_content = service.export_to_csv(report)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}.csv"}
    )


@router.post("/export/html/{report_type}")
def export_report_html(
    report_type: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Export a report as HTML (for PDF conversion)."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        report_type=report_type,
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids
    )
    
    html_content = service.export_to_html(report)
    return HTMLResponse(content=html_content)


@router.post("/export/pdf/{report_type}")
def export_report_pdf(
    report_type: str,
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """
    Export a report as PDF.
    
    Generates a professionally styled PDF document suitable for printing.
    Requires WeasyPrint to be installed.
    """
    from fastapi.responses import Response
    
    service = ReportGeneratorService(db)
    report = service.generate_report(
        report_type=report_type,
        schedule_version_id=request.schedule_version_id,
        period_ids=request.period_ids,
        options=request.options
    )
    
    try:
        pdf_bytes = service.export_to_pdf(report)
    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail="PDF export not available. WeasyPrint is not installed."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )
    
    filename = f"{report_type}_{request.schedule_version_id[:8]}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# =============================================================================
# Quick Summary Endpoints
# =============================================================================

@router.get("/summary/production/{schedule_version_id}")
def get_production_summary(schedule_version_id: str, db: Session = Depends(get_db)):
    """Get quick production summary."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        'production_by_material', schedule_version_id, None, None
    )
    return report.summary


@router.get("/summary/equipment/{schedule_version_id}")
def get_equipment_summary(schedule_version_id: str, db: Session = Depends(get_db)):
    """Get quick equipment utilisation summary."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        'equipment_utilisation', schedule_version_id, None, None
    )
    return report.summary


@router.get("/summary/plant/{schedule_version_id}")
def get_plant_summary(schedule_version_id: str, db: Session = Depends(get_db)):
    """Get quick plant performance summary."""
    service = ReportGeneratorService(db)
    report = service.generate_report(
        'plant_performance', schedule_version_id, None, None
    )
    return report.summary

