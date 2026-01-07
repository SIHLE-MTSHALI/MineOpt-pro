"""
Geotechnical & Safety REST API Router

Endpoints for slope monitoring, water levels, dust, hazard zones, and fatigue.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.services.geotech_safety_service import (
    GeotechService, WaterService, EnvironmentalService, SafetyService,
    get_geotech_service, get_water_service, get_environmental_service, get_safety_service
)


router = APIRouter(prefix="/monitoring", tags=["Monitoring & Safety"])


# Schemas
class PrismCreate(BaseModel):
    site_id: str
    prism_name: str
    x: float
    y: float
    z: float
    domain_id: Optional[str] = None
    warning_threshold_mm: float = 50
    critical_threshold_mm: float = 100


class PrismReadingCreate(BaseModel):
    prism_id: str
    x: float
    y: float
    z: float
    measured_at: datetime
    accuracy_mm: Optional[float] = None


class BoreCreate(BaseModel):
    site_id: str
    bore_name: str
    easting: float
    northing: float
    bore_type: str = "monitoring"
    collar_rl: Optional[float] = None
    total_depth_m: Optional[float] = None


class WaterLevelCreate(BaseModel):
    bore_id: str
    water_level_m: float
    measured_at: datetime
    measured_by: Optional[str] = None


class DustMonitorCreate(BaseModel):
    site_id: str
    name: str
    easting: Optional[float] = None
    northing: Optional[float] = None
    pm10_threshold: float = 50
    pm25_threshold: float = 25


class DustReadingCreate(BaseModel):
    monitor_id: str
    measured_at: datetime
    pm10: Optional[float] = None
    pm25: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None


class HazardZoneCreate(BaseModel):
    site_id: str
    name: str
    hazard_type: str
    boundary_geojson: dict
    severity: str = "medium"
    is_exclusion: bool = True
    active_from: Optional[datetime] = None
    active_to: Optional[datetime] = None


class FatigueEventCreate(BaseModel):
    site_id: str
    operator_name: str
    equipment_fleet_number: str
    event_type: str
    severity: str
    occurred_at: datetime
    detection_system: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# Prism Endpoints
@router.post("/prisms")
def install_prism(data: PrismCreate, db: Session = Depends(get_db)):
    """Install monitoring prism."""
    service = get_geotech_service(db)
    prism = service.install_prism(
        site_id=data.site_id,
        prism_name=data.prism_name,
        x=data.x,
        y=data.y,
        z=data.z,
        domain_id=data.domain_id,
        warning_threshold_mm=data.warning_threshold_mm,
        critical_threshold_mm=data.critical_threshold_mm
    )
    return {
        "prism_id": prism.prism_id,
        "prism_name": prism.prism_name,
        "installed": True
    }


@router.post("/prisms/readings")
def record_prism_reading(data: PrismReadingCreate, db: Session = Depends(get_db)):
    """Record prism position reading."""
    service = get_geotech_service(db)
    try:
        reading = service.record_prism_reading(
            prism_id=data.prism_id,
            x=data.x,
            y=data.y,
            z=data.z,
            measured_at=data.measured_at,
            accuracy_mm=data.accuracy_mm
        )
        return {
            "reading_id": reading.reading_id,
            "total_displacement_mm": reading.total_displacement_mm,
            "rate_mm_day": reading.displacement_rate_mm_day
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sites/{site_id}/slope-alerts")
def get_slope_alerts(site_id: str, db: Session = Depends(get_db)):
    """Get prisms with active alerts."""
    service = get_geotech_service(db)
    prisms = service.get_slope_alerts(site_id)
    return [
        {
            "prism_id": p.prism_id,
            "prism_name": p.prism_name,
            "alert_status": p.alert_status,
            "total_displacement_mm": p.total_displacement_mm,
            "rate_mm_day": p.displacement_rate_mm_day
        }
        for p in prisms
    ]


# Water Level Endpoints
@router.post("/bores")
def create_bore(data: BoreCreate, db: Session = Depends(get_db)):
    """Create monitoring bore."""
    service = get_water_service(db)
    bore = service.create_bore(
        site_id=data.site_id,
        bore_name=data.bore_name,
        easting=data.easting,
        northing=data.northing,
        bore_type=data.bore_type,
        collar_rl=data.collar_rl,
        total_depth_m=data.total_depth_m
    )
    return {"bore_id": bore.bore_id, "bore_name": bore.bore_name}


@router.post("/bores/readings")
def record_water_level(data: WaterLevelCreate, db: Session = Depends(get_db)):
    """Record water level reading."""
    service = get_water_service(db)
    try:
        reading = service.record_water_level(
            bore_id=data.bore_id,
            water_level_m=data.water_level_m,
            measured_at=data.measured_at,
            measured_by=data.measured_by
        )
        return {
            "reading_id": reading.reading_id,
            "water_level_m": reading.water_level_m,
            "water_rl": reading.water_rl
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Dust Monitoring Endpoints
@router.post("/dust-monitors")
def create_dust_monitor(data: DustMonitorCreate, db: Session = Depends(get_db)):
    """Create dust monitoring station."""
    service = get_environmental_service(db)
    monitor = service.create_dust_monitor(
        site_id=data.site_id,
        name=data.name,
        easting=data.easting,
        northing=data.northing,
        pm10_threshold=data.pm10_threshold,
        pm25_threshold=data.pm25_threshold
    )
    return {"monitor_id": monitor.monitor_id, "name": monitor.name}


@router.post("/dust-monitors/readings")
def record_dust_reading(data: DustReadingCreate, db: Session = Depends(get_db)):
    """Record dust reading."""
    service = get_environmental_service(db)
    try:
        reading = service.record_dust_reading(
            monitor_id=data.monitor_id,
            measured_at=data.measured_at,
            pm10=data.pm10,
            pm25=data.pm25,
            wind_speed=data.wind_speed,
            wind_direction=data.wind_direction
        )
        return {
            "reading_id": reading.reading_id,
            "pm10_exceeded": reading.pm10_exceeded,
            "pm25_exceeded": reading.pm25_exceeded
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sites/{site_id}/dust-exceedances")
def get_dust_exceedances(
    site_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """Get dust exceedance events."""
    service = get_environmental_service(db)
    exceedances = service.get_exceedances(site_id, start_date, end_date)
    return [
        {
            "reading_id": e.reading_id,
            "measured_at": e.measured_at.isoformat(),
            "pm10": e.pm10_ug_m3,
            "pm25": e.pm25_ug_m3,
            "pm10_exceeded": e.pm10_exceeded,
            "pm25_exceeded": e.pm25_exceeded
        }
        for e in exceedances
    ]


# Hazard Zone Endpoints
@router.post("/hazard-zones")
def create_hazard_zone(data: HazardZoneCreate, db: Session = Depends(get_db)):
    """Create hazard zone."""
    service = get_safety_service(db)
    zone = service.create_hazard_zone(
        site_id=data.site_id,
        name=data.name,
        hazard_type=data.hazard_type,
        boundary_geojson=data.boundary_geojson,
        severity=data.severity,
        is_exclusion=data.is_exclusion,
        active_from=data.active_from,
        active_to=data.active_to
    )
    return {"zone_id": zone.zone_id, "name": zone.name}


# Fatigue Endpoints
@router.post("/fatigue-events")
def record_fatigue_event(data: FatigueEventCreate, db: Session = Depends(get_db)):
    """Record fatigue detection event."""
    service = get_safety_service(db)
    event = service.record_fatigue_event(
        site_id=data.site_id,
        operator_name=data.operator_name,
        equipment_fleet_number=data.equipment_fleet_number,
        event_type=data.event_type,
        severity=data.severity,
        occurred_at=data.occurred_at,
        detection_system=data.detection_system,
        latitude=data.latitude,
        longitude=data.longitude
    )
    return {"event_id": event.event_id, "severity": event.severity}


@router.get("/operators/{operator_id}/fatigue-score")
def get_operator_fatigue_score(
    operator_id: str,
    site_id: str,
    db: Session = Depends(get_db)
):
    """Calculate operator fatigue risk score."""
    service = get_safety_service(db)
    score = service.calculate_operator_fatigue_score(operator_id, site_id)
    return {
        "operator_id": operator_id,
        "fatigue_risk_score": score.fatigue_risk_score,
        "alertness_level": score.alertness_level,
        "recommended_action": score.recommended_action,
        "mandatory_rest": score.mandatory_rest
    }
