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
