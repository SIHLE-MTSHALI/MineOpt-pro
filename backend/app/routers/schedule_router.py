from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine
from ..domain import models_scheduling, models_resources
from ..schemas import schedule_schemas
from typing import List, Optional
from pydantic import BaseModel

# Create Tables
models_scheduling.Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/schedule", tags=["Scheduling"])

@router.post("/versions", response_model=schedule_schemas.ScheduleVersionResponse)
def create_version(version: schedule_schemas.ScheduleVersionCreate, db: Session = Depends(get_db)):
    db_version = models_scheduling.ScheduleVersion(**version.dict(), status="Draft")
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

@router.get("/versions/{version_id}", response_model=schedule_schemas.ScheduleVersionResponse)
def get_version(version_id: str, db: Session = Depends(get_db)):
    version = db.query(models_scheduling.ScheduleVersion).filter(models_scheduling.ScheduleVersion.version_id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Schedule Version not found")
    return version

@router.get("/site/{site_id}/versions", response_model=list[schedule_schemas.ScheduleVersionResponse])
def get_versions_by_site(site_id: str, db: Session = Depends(get_db)):
    return db.query(models_scheduling.ScheduleVersion).filter(models_scheduling.ScheduleVersion.site_id == site_id).all()

@router.post("/versions/{version_id}/tasks", response_model=schedule_schemas.TaskResponse)
def create_task(version_id: str, task: schedule_schemas.TaskCreate, db: Session = Depends(get_db)):
    # Validate Resource and Activity Exists (Skipped for brevity/trust in v1)
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

@router.put("/tasks/{task_id}", response_model=schedule_schemas.TaskResponse)
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
