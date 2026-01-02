"""
Calendar and Period Entities - Section 3.3 of Enterprise Specification

The calendar system provides the temporal backbone for scheduling:
- Calendar: Container for periods with site-specific configuration
- Period: Fixed scheduling time buckets (shifts, days, custom)

Periods support grouping for reporting (by shift, day, week, month).
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base


class Calendar(Base):
    """
    A calendar containing periods for a site.
    Sites may have multiple calendars (e.g., production, maintenance).
    """
    __tablename__ = "calendars"

    calendar_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)  # e.g. "Production Roster 4 Panel"
    description = Column(String, nullable=True)
    
    # Period configuration
    # Shift: 12-hour shifts
    # Day: 24-hour days
    # Custom: Variable length periods
    period_granularity_type = Column(String, default="Shift")
    
    # Default period duration (hours) for this calendar
    default_period_hours = Column(Float, default=12.0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    site = relationship("Site")
    periods = relationship("Period", back_populates="calendar", order_by="Period.start_datetime")

    def __repr__(self):
        return f"<Calendar {self.name}>"


class Period(Base):
    """
    A fixed scheduling time bucket.
    The fundamental unit of time for production planning.
    """
    __tablename__ = "periods"

    period_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    calendar_id = Column(String, ForeignKey("calendars.calendar_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)  # "2026-01-01 Day Shift"
    
    # Time bounds
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    
    # Duration (calculated or specified)
    duration_hours = Column(Float, nullable=True)
    
    # Grouping Metadata for Reporting
    group_shift = Column(String, nullable=True)  # "Day", "Night"
    group_day = Column(String, nullable=True)  # "2026-01-01" (date string)
    group_week = Column(String, nullable=True)  # "2026-W01" (ISO week)
    group_month = Column(String, nullable=True)  # "2026-01" (YYYY-MM)
    
    # Working status
    is_working_period = Column(Boolean, default=True)
    
    # Notes and special conditions
    notes = Column(Text, nullable=True)
    
    # Special period flags
    is_maintenance_window = Column(Boolean, default=False)
    is_weather_affected = Column(Boolean, default=False)
    
    # Sequence for ordering (auto-assigned or manual)
    sequence = Column(Integer, nullable=True)
    
    # Relationships
    calendar = relationship("Calendar", back_populates="periods")

    def __repr__(self):
        return f"<Period {self.name}>"

    @property
    def calculated_duration_hours(self) -> float:
        """Calculate duration from datetime bounds if not explicitly set."""
        if self.duration_hours:
            return self.duration_hours
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return delta.total_seconds() / 3600
        return 0.0

