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

