from sqlalchemy.orm import Session
from ..domain import models_scheduling, models_resources, models_calendar
from datetime import datetime

class OptimizationService:
    def run_greedy(self, db: Session, site_id: str, schedule_version_id: str):
        # 1. Fetch Resources (Excavators)
        resources = db.query(models_resources.Resource)\
            .filter(models_resources.Resource.site_id == site_id)\
            .filter(models_resources.Resource.resource_type == "Excavator")\
            .all()
            
        if not resources:
            return {"status": "error", "message": "No excavators found"}

        # 2. Fetch All Periods for the Site's Calendar
        # Assuming one active calendar for simplicity
        calendar = db.query(models_calendar.Calendar).filter(models_calendar.Calendar.site_id == site_id).first()
        if not calendar:
            return {"status": "error", "message": "No calendar found"}
            
        periods = db.query(models_calendar.Period)\
            .filter(models_calendar.Period.calendar_id == calendar.calendar_id)\
            .order_by(models_calendar.Period.start_datetime)\
            .all()

        # 3. Fetch All Activity Areas (Blocks)
        blocks = db.query(models_resources.ActivityArea)\
            .filter(models_resources.ActivityArea.site_id == site_id)\
            .order_by(models_resources.ActivityArea.priority.desc())\
            .all() # Sorted by Priority (High to Low)

        # 4. Filter out already scheduled blocks
        existing_tasks = db.query(models_scheduling.Task)\
            .filter(models_scheduling.Task.schedule_version_id == schedule_version_id)\
            .all()
            
        scheduled_block_ids = {t.activity_area_id for t in existing_tasks}
        unscheduled_blocks = [b for b in blocks if b.area_id not in scheduled_block_ids]
        
        # 5. Greedy Assignment Logic
        # Strategy: Fill Period 1 with all Resources, then Period 2, etc.
        tasks_created = []
        
        block_idx = 0
        total_blocks = len(unscheduled_blocks)
        
        for period in periods:
            for resource in resources:
                if block_idx >= total_blocks:
                    break
                
                block = unscheduled_blocks[block_idx]
                
                # Check (Naive): Is resource already busy in this period?
                # For greedy, we assume 1 task per period per resource for now.
                # In real life, we check capacity. Here, we blindly assign.
                
                # Double check we haven't already assigned this resource in this period (from previous manual tasks)
                is_busy = any(t.resource_id == resource.resource_id and t.period_id == period.period_id for t in existing_tasks + tasks_created)
                
                if not is_busy:
                    new_task = models_scheduling.Task(
                        schedule_version_id=schedule_version_id,
                        resource_id=resource.resource_id,
                        activity_id=block.activity_id,
                        period_id=period.period_id,
                        activity_area_id=block.area_id,
                        planned_quantity=1000 # Placeholder capacity
                    )
                    tasks_created.append(new_task)
                    block_idx += 1
            
            if block_idx >= total_blocks:
                break
                
        # 6. Persist
        db.add_all(tasks_created)
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Optimization Complete. Scheduled {len(tasks_created)} tasks.",
            "tasks_count": len(tasks_created)
        }

optimizer = OptimizationService()
