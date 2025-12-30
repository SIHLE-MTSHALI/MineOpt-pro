from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TaskBase(BaseModel):
    resource_id: str
    activity_id: str
    period_id: str
    activity_area_id: Optional[str] = None
    planned_quantity: float = 0.0

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    task_id: str
    schedule_version_id: str
    
    # Flattened for UI convenience if needed, but keeping relational for now
    class Config:
        from_attributes = True

class ScheduleVersionCreate(BaseModel):
    site_id: str
    name: str

class ScheduleVersionResponse(ScheduleVersionCreate):
    version_id: str
    status: str
    created_at: datetime
    tasks: List[TaskResponse] = []
    
    class Config:
        from_attributes = True
