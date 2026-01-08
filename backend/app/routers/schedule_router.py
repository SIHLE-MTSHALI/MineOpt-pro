from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine
from ..domain import models_scheduling, models_resource, models_calendar
# from ..schemas import schedule_schemas
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Note: Database tables are now created in main.py lifespan


router = APIRouter(prefix="/schedule", tags=["Scheduling"])

# --- Schemas (Inline for simplicity or move to schemas later) ---
class ScheduleVersionCreate(BaseModel):
    site_id: str
    name: str

class TaskCreate(BaseModel):
    resource_id: str
    activity_id: str
    period_id: str
    activity_area_id: str
    planned_quantity: float

# --- Endpoints ---

@router.post("/versions")
def create_version(version: ScheduleVersionCreate, db: Session = Depends(get_db)):
    db_version = models_scheduling.ScheduleVersion(**version.dict(), status="Draft")
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

@router.post("/versions/{version_id}/fork")
def fork_version(version_id: str, new_name: str = None, db: Session = Depends(get_db)):
    # 1. Get Source
    source = db.query(models_scheduling.ScheduleVersion).filter(models_scheduling.ScheduleVersion.version_id == version_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source version not found")
        
    # 2. Create Target
    name = new_name or f"Copy of {source.name}"
    target = models_scheduling.ScheduleVersion(
        site_id=source.site_id,
        name=name,
        status="Draft"
    )
    db.add(target)
    db.commit() # get ID
    db.refresh(target)
    
    # 3. Copy Tasks
    source_tasks = db.query(models_scheduling.Task).filter(models_scheduling.Task.schedule_version_id == version_id).all()
    new_tasks = []
    
    for t in source_tasks:
        nt = models_scheduling.Task(
            schedule_version_id=target.version_id,
            resource_id=t.resource_id,
            activity_id=t.activity_id,
            period_id=t.period_id,
            activity_area_id=t.activity_area_id,
            planned_quantity=t.planned_quantity
        )
        new_tasks.append(nt)
        
    db.add_all(new_tasks)
    db.commit()
    
    return target

@router.get("/site/{site_id}/versions")
def get_versions_by_site(site_id: str, db: Session = Depends(get_db)):
    return db.query(models_scheduling.ScheduleVersion).filter(models_scheduling.ScheduleVersion.site_id == site_id).all()


@router.get("/versions/{version_id}")
def get_version_by_id(version_id: str, db: Session = Depends(get_db)):
    """Get a single schedule version by ID."""
    version = db.query(models_scheduling.ScheduleVersion).filter(
        models_scheduling.ScheduleVersion.version_id == version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Schedule version not found")
    return version


@router.get("/versions/{version_id}/runs")
def get_version_runs(version_id: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get optimization run history for a schedule version."""
    # Check if DecisionExplanation or a run tracking table exists
    runs = []
    
    # Try to get runs from schedule_run_requests if it exists
    try:
        from ..domain import models_schedule_results
        run_requests = db.query(models_schedule_results.ScheduleRunRequest).filter(
            models_schedule_results.ScheduleRunRequest.schedule_version_id == version_id
        ).order_by(models_schedule_results.ScheduleRunRequest.created_at.desc()).limit(limit).all()
        
        for r in run_requests:
            runs.append({
                "run_id": r.request_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "objective_value": r.objective_value,
                "solve_time_seconds": r.solve_time_seconds
            })
    except Exception:
        # If no runs table, return empty but valid response
        pass
    
    return {"runs": runs, "count": len(runs)}


class ScheduleOptimizeRequest(BaseModel):
    schedule_version_id: str
    mode: str = "full"  # "full" or "fast"
    time_limit_seconds: int = 300


@router.post("/run/full-pass")
def run_full_pass(request: ScheduleOptimizeRequest, db: Session = Depends(get_db)):
    """Run a full optimization pass on the schedule."""
    # Validate version exists
    version = db.query(models_scheduling.ScheduleVersion).filter(
        models_scheduling.ScheduleVersion.version_id == request.schedule_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Schedule version not found")
    
    # In production, this would trigger an async optimization job
    # For now, return a pending status
    import uuid
    run_id = str(uuid.uuid4())
    
    return {
        "run_id": run_id,
        "status": "queued",
        "message": "Full optimization pass queued",
        "schedule_version_id": request.schedule_version_id,
        "estimated_time_seconds": request.time_limit_seconds
    }


@router.post("/optimize")
def optimize_schedule(request: ScheduleOptimizeRequest, db: Session = Depends(get_db)):
    """Alias endpoint for optimization - redirects to appropriate optimization type."""
    # Validate version exists
    version = db.query(models_scheduling.ScheduleVersion).filter(
        models_scheduling.ScheduleVersion.version_id == request.schedule_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Schedule version not found")
    
    import uuid
    run_id = str(uuid.uuid4())
    
    return {
        "run_id": run_id,
        "status": "queued",
        "message": f"Optimization ({request.mode} mode) queued",
        "schedule_version_id": request.schedule_version_id,
        "mode": request.mode
    }

@router.get("/versions/{version_id}/tasks")
def get_tasks(version_id: str, db: Session = Depends(get_db)):
    return db.query(models_scheduling.Task).filter(models_scheduling.Task.schedule_version_id == version_id).all()

@router.post("/versions/{version_id}/tasks")
def create_task(version_id: str, task: TaskCreate, db: Session = Depends(get_db)):
    db_task = models_scheduling.Task(**task.dict(), schedule_version_id=version_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

class TaskUpdate(BaseModel):
    resource_id: Optional[str] = None
    period_id: Optional[str] = None
    activity_area_id: Optional[str] = None
    planned_quantity: Optional[float] = None
    rate_factor_applied: Optional[float] = None

@router.put("/tasks/{task_id}")
def update_task(task_id: str, updates: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models_scheduling.Task).filter(models_scheduling.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if updates.resource_id:
        task.resource_id = updates.resource_id
    if updates.period_id:
        task.period_id = updates.period_id
    if updates.activity_area_id:
        task.activity_area_id = updates.activity_area_id
    if updates.planned_quantity is not None:
        task.planned_quantity = updates.planned_quantity
    if updates.rate_factor_applied is not None:
        task.rate_factor_applied = updates.rate_factor_applied
        
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(models_scheduling.Task).filter(models_scheduling.Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.get("/versions/{version_id}/diagnostics")
def get_diagnostics(version_id: str, db: Session = Depends(get_db)):
    """
    Get diagnostics for a schedule version including:
    - Feasibility analysis
    - Binding constraints
    - Decision explanations
    """
    version = db.query(models_scheduling.ScheduleVersion).filter(
        models_scheduling.ScheduleVersion.version_id == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Schedule version not found")
    
    tasks = db.query(models_scheduling.Task).filter(
        models_scheduling.Task.schedule_version_id == version_id
    ).all()
    
    # Calculate summary metrics
    total_tasks = len(tasks)
    total_tonnes = sum(t.planned_quantity or 0 for t in tasks)
    
    # Check for decision explanations stored with the version
    explanations = db.query(models_scheduling.DecisionExplanation).filter(
        models_scheduling.DecisionExplanation.schedule_version_id == version_id
    ).all() if hasattr(models_scheduling, 'DecisionExplanation') else []
    
    # Build diagnostics response
    diagnostics = {
        "summary": {
            "status": version.status,
            "totalTasks": total_tasks,
            "totalTonnes": total_tonnes,
            "feasibilityScore": 1.0 if total_tasks > 0 else 0.0,
            "qualityCompliance": 0.95  # Placeholder - would come from quality analysis
        },
        "infeasibilities": [],  # Would be populated from optimization run
        "blockedRoutes": [],
        "unmetDemands": [],
        "bindingConstraints": [],
        "decisions": [
            {
                "id": exp.explanation_id if hasattr(exp, 'explanation_id') else str(i),
                "decisionType": exp.decision_type if hasattr(exp, 'decision_type') else "Unknown",
                "explanation": exp.explanation_text if hasattr(exp, 'explanation_text') else "",
                "bindingConstraints": exp.binding_constraints if hasattr(exp, 'binding_constraints') else [],
                "penaltyBreakdown": exp.penalty_breakdown if hasattr(exp, 'penalty_breakdown') else [],
                "alternativesConsidered": exp.alternatives_considered if hasattr(exp, 'alternatives_considered') else []
            }
            for i, exp in enumerate(explanations)
        ]
    }
    
    return diagnostics
