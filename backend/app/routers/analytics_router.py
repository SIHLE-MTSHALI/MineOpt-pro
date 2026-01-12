from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_scheduling, models_resource, models_flow
from typing import List, Dict, Any
import math

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/cycle-times/{schedule_version_id}")
def get_cycle_times(schedule_version_id: str, db: Session = Depends(get_db)):
    """
    Calculate estimated cycle times for all tasks in a schedule.
    Returns: List of {task_id, block, destination, distance_m, cycle_time_min, productivity_tph}
    """
    tasks = db.query(models_scheduling.Task).filter(models_scheduling.Task.schedule_version_id == schedule_version_id).all()
    
    results = []
    
    # Cache Areas
    areas = {a.area_id: a for a in db.query(models_resource.ActivityArea).all()}
    
    # Destination Positions (Mocked if missing from DB FlowNodes)
    # Ideally we'd query FlowNodes -> location_geometry
    # ROM Pad @ (150, 0, -50), Dump @ (-50, 0, -50) matches Frontend HaulageRenderer
    pos_rom = [150, 0, -50]
    pos_dump = [-50, 0, -50]
    
    truck_speed_kmh = 25.0
    truck_speed_mpm = (truck_speed_kmh * 1000) / 60 # Meters per minute (~416 m/min)
    
    fixed_time_min = 5.0 # Load (3m) + Dump (2m) + Queue
    
    for t in tasks:
        area = areas.get(t.activity_area_id)
        if not area or not area.geometry:
            continue
            
        # Get Block Position
        # geometry is {"position": [x, y, z], ...}
        pos_block = area.geometry.get("position", [0, 0, 0])
        
        # Determine Dest
        # Logic: If Area slice 0 is Coal -> ROM, else Dump
        # Simplification: Check if "Coal" in slice states
        is_coal = False
        if area.slice_states and len(area.slice_states) > 0:
            if "Coal" in area.slice_states[0].get("material", ""):
                is_coal = True
                
        pos_dest = pos_rom if is_coal else pos_dump
        dest_name = "ROM Pad" if is_coal else "Waste Dump"
        
        # Calc 3D Distance (Euclidean)
        dx = pos_dest[0] - pos_block[0]
        dy = pos_dest[1] - pos_block[1]
        dz = pos_dest[2] - pos_block[2]
        dist_m = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Cycle Time (Round Trip)
        # Travel Empty + Travel Full = 2 * dist
        travel_time_min = (dist_m * 2) / truck_speed_mpm
        total_cycle_min = fixed_time_min + travel_time_min
        
        # Productivity (t/h)
        # Assume Truck Payload = 220 tons? 
        # Actually we don't know the truck count here per task, 
        # but we can estimate "Instantaneous Potential t/h per truck"
        truck_payload = 220
        cycles_per_hour = 60 / total_cycle_min
        potential_tph = cycles_per_hour * truck_payload
        
        results.append({
            "task_id": t.task_id,
            "block_name": area.name,
            "destination": dest_name,
            "distance_m": round(dist_m, 1),
            "cycle_time_min": round(total_cycle_min, 1),
            "potential_tph": round(potential_tph, 0),
            "quantity": t.planned_quantity
        })
        
    return results


@router.get("/summary")
def get_analytics_summary(site_id: str, db: Session = Depends(get_db)):
    """
    Get analytics summary for site dashboard.
    Returns KPIs like total production, active equipment, etc.
    """
    from ..domain import models_core
    from datetime import datetime, timedelta
    
    result = {
        "total_production_tonnes": 0,
        "active_equipment_count": 0,
        "pending_blasts": 0,
        "active_alerts": 0,
        "stockpile_levels": [],
        "recent_activity": []
    }
    
    try:
        # Get site info
        site = db.query(models_core.Site).filter(models_core.Site.site_id == site_id).first()
        if not site:
            return result
            
        # Count active equipment
        try:
            from ..domain import models_fleet
            result["active_equipment_count"] = db.query(models_fleet.Equipment).filter(
                models_fleet.Equipment.site_id == site_id,
                models_fleet.Equipment.status == "operating"
            ).count()
        except Exception:
            result["active_equipment_count"] = 0
        
        # Count pending blasts
        try:
            from ..domain import models_drill_blast
            result["pending_blasts"] = db.query(models_drill_blast.BlastPattern).filter(
                models_drill_blast.BlastPattern.site_id == site_id,
                models_drill_blast.BlastPattern.status.in_(["designed", "drilled"])
            ).count()
        except Exception:
            result["pending_blasts"] = 0
        
        # Get stockpile levels (from flow nodes via network join)
        try:
            # FlowNode connects to site via FlowNetwork
            networks = db.query(models_flow.FlowNetwork).filter(
                models_flow.FlowNetwork.site_id == site_id
            ).all()
            
            network_ids = [n.network_id for n in networks]
            if network_ids:
                stockpiles = db.query(models_flow.FlowNode).filter(
                    models_flow.FlowNode.network_id.in_(network_ids),
                    models_flow.FlowNode.node_type.in_(["Stockpile", "stockpile"])
                ).all()
                
                result["stockpile_levels"] = [
                    {
                        "name": s.name,
                        "current": s.capacity_tonnes * 0.6 if s.capacity_tonnes else 0,  # Mock 60% full
                        "capacity": s.capacity_tonnes or 0
                    }
                    for s in stockpiles
                ]
        except Exception:
            result["stockpile_levels"] = []
        
        # Mock production data (LoadTicket model doesn't exist)
        result["total_production_tonnes"] = 45200  # Mock value
        
    except Exception as e:
        # Return empty result on error - don't crash dashboard
        print(f"Analytics summary error: {e}")
    
    return result


@router.get("/dashboard-summary")
def get_dashboard_summary(site_id: str, db: Session = Depends(get_db)):
    """
    Comprehensive dashboard summary with all KPIs for the main dashboard.
    Returns planned vs actual performance, alerts, stockpiles, and recent activity.
    """
    from ..domain import models_core
    from datetime import datetime, timedelta
    
    result = {
        # Production KPIs
        "planned_tonnes_today": 0,
        "actual_tonnes_today": 0,
        "plan_adherence_percent": 0,
        
        # Equipment KPIs
        "active_equipment": 0,
        "total_equipment": 0,
        "equipment_availability_percent": 0,
        
        # Quality KPIs
        "quality_compliance_percent": 0,
        "avg_cv": 0,
        "avg_ash": 0,
        
        # Stockpile data
        "stockpiles": [],
        
        # Alerts
        "active_alerts": [],
        "alerts_count": 0,
        
        # Recent activity
        "recent_events": [],
        
        # Drill & Blast
        "pending_blasts": 0,
        "blasts_this_week": 0
    }
    
    try:
        # Get site info
        site = db.query(models_core.Site).filter(models_core.Site.site_id == site_id).first()
        if not site:
            return result
            
        # Equipment stats
        try:
            from ..domain import models_fleet
            from ..domain.models_fleet import EquipmentStatus
            
            all_equipment = db.query(models_fleet.Equipment).filter(
                models_fleet.Equipment.site_id == site_id,
                models_fleet.Equipment.is_active == True
            ).all()
            
            result["total_equipment"] = len(all_equipment)
            result["active_equipment"] = sum(1 for e in all_equipment if e.status == EquipmentStatus.operating)
            
            if result["total_equipment"] > 0:
                result["equipment_availability_percent"] = round(
                    (result["active_equipment"] / result["total_equipment"]) * 100, 1
                )
        except Exception as e:
            print(f"Equipment stats error: {e}")
        
        # Drill & Blast stats
        try:
            from ..domain import models_drill_blast
            
            result["pending_blasts"] = db.query(models_drill_blast.BlastPattern).filter(
                models_drill_blast.BlastPattern.site_id == site_id,
                models_drill_blast.BlastPattern.status.in_(["designed", "drilled", "loaded"])
            ).count()
            
            # Blasts this week
            week_ago = datetime.utcnow() - timedelta(days=7)
            result["blasts_this_week"] = db.query(models_drill_blast.BlastEvent).filter(
                models_drill_blast.BlastEvent.site_id == site_id,
                models_drill_blast.BlastEvent.event_time >= week_ago
            ).count()
        except Exception as e:
            print(f"Drill blast stats error: {e}")
        
        # Stockpile levels
        try:
            networks = db.query(models_flow.FlowNetwork).filter(
                models_flow.FlowNetwork.site_id == site_id
            ).all()
            
            network_ids = [n.network_id for n in networks]
            if network_ids:
                stockpiles = db.query(models_flow.FlowNode).filter(
                    models_flow.FlowNode.network_id.in_(network_ids),
                    models_flow.FlowNode.node_type.in_(["Stockpile", "stockpile", "ROM", "rom"])
                ).all()
                
                result["stockpiles"] = [
                    {
                        "id": s.node_id,
                        "name": s.name,
                        "current_tonnes": round(s.capacity_tonnes * 0.65 if s.capacity_tonnes else 0, 0),
                        "capacity_tonnes": s.capacity_tonnes or 0,
                        "fill_percent": 65  # Mock 65% full
                    }
                    for s in stockpiles
                ]
        except Exception as e:
            print(f"Stockpile stats error: {e}")
        
        # Alerts from monitoring
        try:
            from ..domain import models_geotech_safety
            
            # Get prism alerts
            prisms = db.query(models_geotech_safety.SlopeMonitorPrism).filter(
                models_geotech_safety.SlopeMonitorPrism.site_id == site_id,
                models_geotech_safety.SlopeMonitorPrism.alert_status.in_(["warning", "critical"])
            ).limit(5).all()
            
            for p in prisms:
                result["active_alerts"].append({
                    "id": p.prism_id,
                    "type": "slope",
                    "severity": p.alert_status,
                    "message": f"Slope movement detected at {p.prism_name}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            result["alerts_count"] = len(result["active_alerts"])
        except Exception as e:
            print(f"Alerts error: {e}")
        
        # Production metrics (mock based on schedule data)
        try:
            # Get active schedule
            active_schedules = db.query(models_scheduling.ScheduleVersion).filter(
                models_scheduling.ScheduleVersion.site_id == site_id,
                models_scheduling.ScheduleVersion.status == "published"
            ).all()
            
            if active_schedules:
                # Sum planned quantities
                for schedule in active_schedules:
                    tasks = db.query(models_scheduling.Task).filter(
                        models_scheduling.Task.schedule_version_id == schedule.version_id
                    ).all()
                    result["planned_tonnes_today"] += sum(t.planned_quantity or 0 for t in tasks)
                
                # Mock actual as 88-95% of planned
                import random
                adherence = random.uniform(88, 96)
                result["actual_tonnes_today"] = round(result["planned_tonnes_today"] * (adherence / 100), 0)
                result["plan_adherence_percent"] = round(adherence, 1)
            else:
                # Fallback mock values
                result["planned_tonnes_today"] = 48000
                result["actual_tonnes_today"] = 45200
                result["plan_adherence_percent"] = 94.2
        except Exception as e:
            print(f"Production metrics error: {e}")
            result["planned_tonnes_today"] = 48000
            result["actual_tonnes_today"] = 45200
            result["plan_adherence_percent"] = 94.2
        
        # Quality metrics (mock)
        result["quality_compliance_percent"] = 92.5
        result["avg_cv"] = 24.8
        result["avg_ash"] = 14.2
        
    except Exception as e:
        print(f"Dashboard summary error: {e}")
    
    return result


