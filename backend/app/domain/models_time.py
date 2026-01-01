from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from ..database import Base
import uuid

# 3.3 Calendar and Periods
class Calendar(Base):
    __tablename__ = "calendars"
    calendar_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    description = Column(String)
    period_granularity_type = Column(String) # Shift, Day
    
    periods = relationship("Period", back_populates="calendar", order_by="Period.start_datetime")

class Period(Base):
    __tablename__ = "periods"
    period_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    calendar_id = Column(String, ForeignKey("calendars.calendar_id"))
    name = Column(String, nullable=False) # "2026-01-03 Night Shift"
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    duration_hours = Column(Float)
    group_shift = Column(String) # Day/Night
    group_day = Column(String) # YYYY-MM-DD
    group_week = Column(String)
    group_month = Column(String)
    is_working_period = Column(Boolean, default=True)
    notes = Column(String)
    
    calendar = relationship("Calendar", back_populates="periods")
