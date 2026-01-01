from sqlalchemy.orm import Session
from ..domain import models_scheduling, models_resource, models_time
from datetime import datetime

class OptimizationService:
    def run_greedy(self, db: Session, site_id: str, schedule_version_id: str):
        # 1. Fetch Resources (Excavators)
        resources = db.query(models_resource.Resource)\
            .filter(models_resource.Resource.site_id == site_id)\
            .filter(models_resource.Resource.resource_type == "Excavator")\
            .all()
            
        if not resources:
            return {"status": "error", "message": "No excavators found"}

        # 2. Fetch All Periods
        calendar = db.query(models_time.Calendar).filter(models_time.Calendar.site_id == site_id).first()
        if not calendar:
            return {"status": "error", "message": "No calendar found"}
            
        periods = db.query(models_time.Period)\
            .filter(models_time.Period.calendar_id == calendar.calendar_id)\
            .order_by(models_time.Period.start_datetime)\
            .all()

        # 3. Fetch All Activity Areas & Build Topology
        all_blocks = db.query(models_resource.ActivityArea)\
            .filter(models_resource.ActivityArea.site_id == site_id)\
            .all()
            
        # Map: block_id -> block
        block_map = {b.area_id: b for b in all_blocks}
        
        # Build Spatial Index (x, y, z)
        # Assuming geometry={"position": [x, y, z]}
        spatial_index = {} # (x, z) -> list of blocks sorted by y (descending = top first)
        
        for b in all_blocks:
            pos = b.geometry.get("position", [0, 0, 0])
            x, y, z = pos[0], pos[1], pos[2]
            col_key = (x, z)
            if col_key not in spatial_index:
                spatial_index[col_key] = []
            spatial_index[col_key].append(b)
            
        # Sort each column by Y descending (Top block first)
        for k in spatial_index:
            spatial_index[k].sort(key=lambda b: b.geometry.get("position")[1], reverse=True)

        # 4. State Tracking
        # Track which blocks are mined (completed)
        scheduled_block_ids = set()
        existing_tasks = db.query(models_scheduling.Task)\
            .filter(models_scheduling.Task.schedule_version_id == schedule_version_id)\
            .all()
        for t in existing_tasks:
            if t.activity_area_id:
                scheduled_block_ids.add(t.activity_area_id)
        
        tasks_created = []
        
        # Period Loop
        for period in periods:
            # Capacity Tracking per Resource for this period
            # Assumed duration 12h for now if not set
            duration_hours = 12 
            resource_usage = {r.resource_id: 0 for r in resources} # tons used
            
            # Inner Loop: Assign tasks until resources function full or no blocks available
            # We iterate multiple times per period to allow multiple small blocks if capacity allows
            while True:
                made_assignment = False
                
                # Identify Available Blocks (Precedence Check)
                available_candidates = []
                for col_key, column_blocks in spatial_index.items():
                    # Find highest unmined block
                    for block in column_blocks:
                        if block.area_id not in scheduled_block_ids:
                            # This is the top-most unmined block in this column. 
                            # It is a candidate. All blocks above it are mined (or it is the top).
                            # Blocks below it are NOT candidates.
                            available_candidates.append(block)
                            break 
                
                # Sort candidates by defined Priority
                available_candidates.sort(key=lambda b: b.priority, reverse=True)
                
                if not available_candidates:
                    break # No more blocks left to mine ever
                
                # Try to assign top candidate
                for block in available_candidates:
                    # Find a resource with capacity
                    assigned_res = None
                    for res in resources:
                        current_load = resource_usage[res.resource_id]
                        max_capacity = res.base_rate * duration_hours
                        
                        # Default block quantity (placeholder)
                        block_qty = 5000 
                        if block.slice_states and len(block.slice_states) > 0:
                            block_qty = block.slice_states[0].get("quantity", 5000)
                            
                        if current_load + block_qty <= max_capacity:
                            assigned_res = res
                            break
                    
                    if assigned_res:
                        # Create Task
                        new_task = models_scheduling.Task(
                            schedule_version_id=schedule_version_id,
                            resource_id=assigned_res.resource_id,
                            activity_id=block.activity_id,
                            period_id=period.period_id,
                            activity_area_id=block.area_id,
                            planned_quantity=block_qty
                        )
                        tasks_created.append(new_task)
                        
                        # Update State
                        scheduled_block_ids.add(block.area_id)
                        resource_usage[assigned_res.resource_id] += block_qty
                        made_assignment = True
                        break # Break candidate loop to re-evaluate availability (though for distinct columns it doesn't change, but safe)
                
                if not made_assignment:
                    break # Resources are full for this period (or no matching block fits)
            
        # 6. Persist
        db.add_all(tasks_created)
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Optimization Complete. Scheduled {len(tasks_created)} tasks with constraints.",
            "tasks_count": len(tasks_created)
        }

optimizer = OptimizationService()
