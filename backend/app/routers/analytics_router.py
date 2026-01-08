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
