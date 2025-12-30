from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class Calendar(Base):
    __tablename__ = "calendars"

    calendar_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String) # e.g. "Production Roster 4 Panel"
    period_granularity_type = Column(String, default="Shift") # Shift, Day
    
    periods = relationship("Period", back_populates="calendar")


class Period(Base):
    __tablename__ = "periods"

    period_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    calendar_id = Column(String, ForeignKey("calendars.calendar_id"))
    
    name = Column(String) # "2026-01-01 Day"
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    
    # Grouping Metadata for Reporting
    group_shift = Column(String) # "Day", "Night"
    group_day = Column(String) # "2026-01-01"
    
    is_working_period = Column(Boolean, default=True)
    
    calendar = relationship("Calendar", back_populates="periods")
