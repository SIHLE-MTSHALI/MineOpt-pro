from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine
from ..domain import models_calendar
from typing import List
from pydantic import BaseModel
from datetime import datetime

# Models
models_calendar.Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/calendar", tags=["Calendar"])

class PeriodResponse(BaseModel):
    period_id: str
    name: str # e.g. "2026-01-01 Day"
    start_datetime: datetime
    end_datetime: datetime
    group_shift: str
    is_working_period: bool
    
    class Config:
        orm_mode = True

class CalendarResponse(BaseModel):
    calendar_id: str
    name: str
    class Config:
        orm_mode = True

@router.get("/site/{site_id}", response_model=List[CalendarResponse])
def get_calendars_by_site(site_id: str, db: Session = Depends(get_db)):
    return db.query(models_calendar.Calendar).filter(models_calendar.Calendar.site_id == site_id).all()

@router.get("/{calendar_id}/periods", response_model=List[PeriodResponse])
def get_periods(calendar_id: str, db: Session = Depends(get_db)):
    # Sort by start time
    return db.query(models_calendar.Period)\
             .filter(models_calendar.Period.calendar_id == calendar_id)\
             .order_by(models_calendar.Period.start_datetime)\
             .all()
