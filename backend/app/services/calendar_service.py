from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..domain import models_calendar
import uuid

def generate_standard_roster(db: Session, site_id: str, start_date: datetime, days: int = 14):
    """
    Generates a standard 2-shift roster (Day/Night) for N days.
    Day: 06:00 - 18:00
    Night: 18:00 - 06:00 (+1 day)
    """
    # 1. Create Calendar
    cal = models_calendar.Calendar(
        site_id=site_id,
        name="Standard 12h Roster",
        period_granularity_type="Shift"
    )
    db.add(cal)
    db.flush()

    periods = []
    current_date = start_date.replace(hour=6, minute=0, second=0, microsecond=0)

    for i in range(days):
        # Day Shift
        day_start = current_date
        day_end = day_start + timedelta(hours=12)
        day_str = day_start.strftime("%Y-%m-%d")
        
        p_day = models_calendar.Period(
            calendar_id=cal.calendar_id,
            name=f"{day_str} Day",
            start_datetime=day_start,
            end_datetime=day_end,
            group_shift="Day",
            group_day=day_str,
            is_working_period=True
        )
        periods.append(p_day)

        # Night Shift
        night_start = day_end
        night_end = night_start + timedelta(hours=12)
        
        p_night = models_calendar.Period(
            calendar_id=cal.calendar_id,
            name=f"{day_str} Night",
            start_datetime=night_start,
            end_datetime=night_end,
            group_shift="Night",
            group_day=day_str,
            is_working_period=True
        )
        periods.append(p_night)
        
        # Advance 24h
        current_date += timedelta(days=1)

    db.add_all(periods)
    db.commit()
    return cal
