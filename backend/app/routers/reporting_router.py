from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..domain import models_scheduling, models_resource, models_calendar
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/reporting", tags=["Reporting"])

@router.get("/dashboard/{schedule_version_id}")
def get_dashboard_stats(schedule_version_id: str, db: Session = Depends(get_db)):
    # 1. Fetch all tasks for the version
    tasks = db.query(models_scheduling.Task).filter(models_scheduling.Task.schedule_version_id == schedule_version_id).all()
    
    total_tons = 0
    coal_tons = 0
    waste_tons = 0
    
    # 2. Aggregate Data
    
    # Helper to get material from Area
    # We need to fetch areas to know their material
    area_ids = [t.activity_area_id for t in tasks if t.activity_area_id]
    areas = db.query(models_resource.ActivityArea).filter(models_resource.ActivityArea.area_id.in_(area_ids)).all()
    area_map = {a.area_id: a for a in areas}
    
    # Helper to get Periods
    period_ids = [t.period_id for t in tasks if t.period_id]
    periods = db.query(models_calendar.Period).filter(models_calendar.Period.period_id.in_(period_ids)).all()
    period_map = {p.period_id: p for p in periods}
    
    production_by_period: Dict[str, Dict[str, float]] = {}

    for task in tasks:
        qty = task.planned_quantity or 0
        total_tons += qty
        
        # determine material
        is_coal = False
        if task.activity_area_id and task.activity_area_id in area_map:
            area = area_map[task.activity_area_id]
            # Check slice_states (List of dicts)
            if area.slice_states and len(area.slice_states) > 0:
                # NEW LOGIC: check material_name
                mat_name = area.slice_states[0].get('material_name', '')
                if 'Coal' in mat_name:
                     is_coal = True
        
        if is_coal:
            coal_tons += qty
        else:
            waste_tons += qty
            
        # Period Aggregation
        p_id = task.period_id
        if p_id and p_id in period_map:
            period = period_map[p_id]
            p_label = f"{period.group_day} {period.group_shift}" # Better Label
            
            if p_label not in production_by_period:
                production_by_period[p_label] = {"name": p_label, "coal": 0, "waste": 0, "total": 0, "sort_dt": period.start_datetime}
            
            production_by_period[p_label]["total"] += qty
            if is_coal:
                production_by_period[p_label]["coal"] += qty
            else:
                production_by_period[p_label]["waste"] += qty
                
    stipping_ratio = round(waste_tons / coal_tons, 2) if coal_tons > 0 else 0
    
    # Sort periods by date
    sorted_periods = sorted(production_by_period.values(), key=lambda x: x["sort_dt"])
    
    # Clean output (remove sort_dt)
    chart_data = [{k:v for k,v in item.items() if k != 'sort_dt'} for item in sorted_periods]

    return {
        "total_tons": total_tons,
        "coal_tons": coal_tons,
        "waste_tons": waste_tons,
        "stripping_ratio": stipping_ratio,
        "chart_data": chart_data
    }
