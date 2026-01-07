"""
Fleet Management REST API Router

Endpoints for equipment tracking, GPS, geofencing, haul cycles, and maintenance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from app.database import get_db
from app.services.fleet_service import FleetService, get_fleet_service
from app.domain.models_fleet import EquipmentType, EquipmentStatus


router = APIRouter(prefix="/fleet", tags=["Fleet Management"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class EquipmentTypeEnum(str, Enum):
    haul_truck = "haul_truck"
    excavator = "excavator"
    front_end_loader = "front_end_loader"
    dozer = "dozer"
    grader = "grader"
    drill_rig = "drill_rig"
    water_cart = "water_cart"
    fuel_truck = "fuel_truck"
    light_vehicle = "light_vehicle"
    other = "other"


class EquipmentStatusEnum(str, Enum):
    operating = "operating"
    standby = "standby"
    maintenance = "maintenance"
    breakdown = "breakdown"
    refueling = "refueling"
    shift_change = "shift_change"
    off_site = "off_site"


class EquipmentCreate(BaseModel):
    site_id: str
    fleet_number: str
    equipment_type: EquipmentTypeEnum
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    payload_tonnes: Optional[float] = None
    bucket_capacity_bcm: Optional[float] = None


class EquipmentResponse(BaseModel):
    equipment_id: str
    site_id: str
    fleet_number: str
    name: Optional[str]
    equipment_type: str
    manufacturer: Optional[str]
    model: Optional[str]
    status: Optional[str]
    payload_tonnes: Optional[float]
    engine_hours: Optional[float]
    last_latitude: Optional[float]
    last_longitude: Optional[float]
    last_speed_kmh: Optional[float]
    is_active: bool
    
    class Config:
        from_attributes = True


class EquipmentStatusUpdate(BaseModel):
    status: EquipmentStatusEnum
    operator_id: Optional[str] = None


class GPSReadingCreate(BaseModel):
    equipment_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed_kmh: Optional[float] = None
    engine_on: bool = True


class GPSReadingResponse(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[float]
    heading: Optional[float]
    speed_kmh: Optional[float]
    timestamp: datetime


class FleetPositionResponse(BaseModel):
    equipment_id: str
    fleet_number: str
    name: Optional[str]
    equipment_type: str
    status: Optional[str]
    latitude: float
    longitude: float
    heading: Optional[float]
    speed_kmh: Optional[float]
    last_update: Optional[str]


class GeofenceCreate(BaseModel):
    site_id: str
    name: str
    boundary_coords: List[List[float]]  # [[lon, lat], ...]
    zone_type: str = "general"
    speed_limit_kmh: Optional[float] = None
    is_restricted: bool = False
    alert_on_entry: bool = False
    alert_on_exit: bool = False


class GeofenceResponse(BaseModel):
    geofence_id: str
    site_id: str
    name: str
    zone_type: Optional[str]
    speed_limit_kmh: Optional[float]
    is_restricted: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class MaintenanceCreate(BaseModel):
    equipment_id: str
    title: str
    maintenance_type: str = "preventive"
    scheduled_date: Optional[datetime] = None
    due_engine_hours: Optional[float] = None
    priority: str = "medium"
    description: Optional[str] = None


class MaintenanceComplete(BaseModel):
    performed_by: str
    parts_used: Optional[List[dict]] = None
    labor_hours: Optional[float] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    record_id: str
    equipment_id: str
    title: str
    maintenance_type: Optional[str]
    priority: Optional[str]
    status: str
    scheduled_date: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CycleStatisticsResponse(BaseModel):
    total_cycles: int
    total_tonnes: float
    avg_cycle_time_min: float
    avg_loading_min: float
    avg_travel_loaded_min: float
    avg_dumping_min: float
    avg_travel_empty_min: float
    productivity_tph: float


class EquipmentHealthResponse(BaseModel):
    equipment_id: str
    fleet_number: str
    status: Optional[str]
    engine_hours: Optional[float]
    health_score: float
    components: List[dict]
    recent_maintenance: List[dict]


# =============================================================================
# Equipment Endpoints
# =============================================================================

@router.post("/equipment", response_model=EquipmentResponse)
def register_equipment(data: EquipmentCreate, db: Session = Depends(get_db)):
    """Register new equipment in the fleet."""
    service = get_fleet_service(db)
    equipment = service.register_equipment(
        site_id=data.site_id,
        fleet_number=data.fleet_number,
        equipment_type=EquipmentType(data.equipment_type.value),
        name=data.name,
        manufacturer=data.manufacturer,
        model=data.model,
        payload_tonnes=data.payload_tonnes,
        bucket_capacity_bcm=data.bucket_capacity_bcm
    )
    return EquipmentResponse(
        equipment_id=equipment.equipment_id,
        site_id=equipment.site_id,
        fleet_number=equipment.fleet_number,
        name=equipment.name,
        equipment_type=equipment.equipment_type.value,
        manufacturer=equipment.manufacturer,
        model=equipment.model,
        status=equipment.status.value if equipment.status else None,
        payload_tonnes=equipment.payload_tonnes,
        engine_hours=equipment.engine_hours,
        last_latitude=equipment.last_latitude,
        last_longitude=equipment.last_longitude,
        last_speed_kmh=equipment.last_speed_kmh,
        is_active=equipment.is_active
    )


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    """Get equipment by ID."""
    service = get_fleet_service(db)
    equipment = service.get_equipment(equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentResponse(
        equipment_id=equipment.equipment_id,
        site_id=equipment.site_id,
        fleet_number=equipment.fleet_number,
        name=equipment.name,
        equipment_type=equipment.equipment_type.value,
        manufacturer=equipment.manufacturer,
        model=equipment.model,
        status=equipment.status.value if equipment.status else None,
        payload_tonnes=equipment.payload_tonnes,
        engine_hours=equipment.engine_hours,
        last_latitude=equipment.last_latitude,
        last_longitude=equipment.last_longitude,
        last_speed_kmh=equipment.last_speed_kmh,
        is_active=equipment.is_active
    )


@router.get("/sites/{site_id}/equipment", response_model=List[EquipmentResponse])
def list_equipment(
    site_id: str,
    equipment_type: Optional[EquipmentTypeEnum] = None,
    status: Optional[EquipmentStatusEnum] = None,
    db: Session = Depends(get_db)
):
    """List all equipment for a site."""
    service = get_fleet_service(db)
    equipment_list = service.list_equipment(
        site_id=site_id,
        equipment_type=EquipmentType(equipment_type.value) if equipment_type else None,
        status=EquipmentStatus(status.value) if status else None
    )
    return [
        EquipmentResponse(
            equipment_id=e.equipment_id,
            site_id=e.site_id,
            fleet_number=e.fleet_number,
            name=e.name,
            equipment_type=e.equipment_type.value,
            manufacturer=e.manufacturer,
            model=e.model,
            status=e.status.value if e.status else None,
            payload_tonnes=e.payload_tonnes,
            engine_hours=e.engine_hours,
            last_latitude=e.last_latitude,
            last_longitude=e.last_longitude,
            last_speed_kmh=e.last_speed_kmh,
            is_active=e.is_active
        )
        for e in equipment_list
    ]


@router.patch("/equipment/{equipment_id}/status", response_model=EquipmentResponse)
def update_equipment_status(
    equipment_id: str,
    data: EquipmentStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update equipment status."""
    service = get_fleet_service(db)
    try:
        equipment = service.update_equipment_status(
            equipment_id=equipment_id,
            status=EquipmentStatus(data.status.value),
            operator_id=data.operator_id
        )
        return EquipmentResponse(
            equipment_id=equipment.equipment_id,
            site_id=equipment.site_id,
            fleet_number=equipment.fleet_number,
            name=equipment.name,
            equipment_type=equipment.equipment_type.value,
            manufacturer=equipment.manufacturer,
            model=equipment.model,
            status=equipment.status.value if equipment.status else None,
            payload_tonnes=equipment.payload_tonnes,
            engine_hours=equipment.engine_hours,
            last_latitude=equipment.last_latitude,
            last_longitude=equipment.last_longitude,
            last_speed_kmh=equipment.last_speed_kmh,
            is_active=equipment.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# GPS Tracking Endpoints
# =============================================================================

@router.post("/gps", response_model=GPSReadingResponse)
def record_gps_reading(data: GPSReadingCreate, db: Session = Depends(get_db)):
    """Record GPS reading for equipment."""
    service = get_fleet_service(db)
    reading = service.record_gps_reading(
        equipment_id=data.equipment_id,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=data.timestamp,
        altitude=data.altitude,
        heading=data.heading,
        speed_kmh=data.speed_kmh,
        engine_on=data.engine_on
    )
    return GPSReadingResponse(
        latitude=reading.latitude,
        longitude=reading.longitude,
        altitude=reading.altitude,
        heading=reading.heading,
        speed_kmh=reading.speed_kmh,
        timestamp=reading.timestamp
    )


@router.get("/equipment/{equipment_id}/trail", response_model=List[GPSReadingResponse])
def get_equipment_trail(
    equipment_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    """Get GPS trail for equipment in time range."""
    service = get_fleet_service(db)
    readings = service.get_equipment_trail(equipment_id, start_time, end_time)
    return [
        GPSReadingResponse(
            latitude=r.latitude,
            longitude=r.longitude,
            altitude=r.altitude,
            heading=r.heading,
            speed_kmh=r.speed_kmh,
            timestamp=r.timestamp
        )
        for r in readings
    ]


@router.get("/sites/{site_id}/positions", response_model=List[FleetPositionResponse])
def get_fleet_positions(site_id: str, db: Session = Depends(get_db)):
    """Get current positions of all equipment in site."""
    service = get_fleet_service(db)
    positions = service.get_fleet_positions(site_id)
    return [FleetPositionResponse(**p) for p in positions]


# =============================================================================
# Geofence Endpoints
# =============================================================================

@router.post("/geofences", response_model=GeofenceResponse)
def create_geofence(data: GeofenceCreate, db: Session = Depends(get_db)):
    """Create a geofence zone."""
    service = get_fleet_service(db)
    geofence = service.create_geofence(
        site_id=data.site_id,
        name=data.name,
        boundary_coords=[(c[0], c[1]) for c in data.boundary_coords],
        zone_type=data.zone_type,
        speed_limit_kmh=data.speed_limit_kmh,
        is_restricted=data.is_restricted,
        alert_on_entry=data.alert_on_entry,
        alert_on_exit=data.alert_on_exit
    )
    return GeofenceResponse(
        geofence_id=geofence.geofence_id,
        site_id=geofence.site_id,
        name=geofence.name,
        zone_type=geofence.zone_type,
        speed_limit_kmh=geofence.speed_limit_kmh,
        is_restricted=geofence.is_restricted,
        is_active=geofence.is_active
    )


@router.get("/sites/{site_id}/geofences", response_model=List[GeofenceResponse])
def list_geofences(site_id: str, db: Session = Depends(get_db)):
    """List geofences for site."""
    service = get_fleet_service(db)
    geofences = service.list_geofences(site_id)
    return [
        GeofenceResponse(
            geofence_id=g.geofence_id,
            site_id=g.site_id,
            name=g.name,
            zone_type=g.zone_type,
            speed_limit_kmh=g.speed_limit_kmh,
            is_restricted=g.is_restricted,
            is_active=g.is_active
        )
        for g in geofences
    ]


# =============================================================================
# Haul Cycle Endpoints
# =============================================================================

@router.post("/equipment/{equipment_id}/detect-cycles")
def detect_haul_cycles(
    equipment_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    """Detect haul cycles from GPS data."""
    service = get_fleet_service(db)
    cycles = service.detect_haul_cycles(equipment_id, start_time, end_time)
    return {
        "cycles_detected": len(cycles),
        "cycles": [
            {
                "cycle_id": c.cycle_id,
                "start": c.cycle_start.isoformat(),
                "end": c.cycle_end.isoformat(),
                "total_minutes": c.total_cycle_sec / 60
            }
            for c in cycles
        ]
    }


@router.get("/sites/{site_id}/cycle-statistics", response_model=CycleStatisticsResponse)
def get_cycle_statistics(
    site_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """Get haul cycle statistics for site."""
    service = get_fleet_service(db)
    stats = service.get_cycle_statistics(site_id, start_date, end_date)
    return CycleStatisticsResponse(**stats)


# =============================================================================
# Maintenance Endpoints
# =============================================================================

@router.post("/maintenance", response_model=MaintenanceResponse)
def schedule_maintenance(data: MaintenanceCreate, db: Session = Depends(get_db)):
    """Schedule maintenance for equipment."""
    service = get_fleet_service(db)
    record = service.schedule_maintenance(
        equipment_id=data.equipment_id,
        title=data.title,
        maintenance_type=data.maintenance_type,
        scheduled_date=data.scheduled_date,
        due_engine_hours=data.due_engine_hours,
        priority=data.priority,
        description=data.description
    )
    return MaintenanceResponse(
        record_id=record.record_id,
        equipment_id=record.equipment_id,
        title=record.title,
        maintenance_type=record.maintenance_type,
        priority=record.priority,
        status=record.status,
        scheduled_date=record.scheduled_date,
        completed_at=record.completed_at
    )


@router.get("/sites/{site_id}/maintenance/pending", response_model=List[MaintenanceResponse])
def get_pending_maintenance(site_id: str, db: Session = Depends(get_db)):
    """Get all pending maintenance for site."""
    service = get_fleet_service(db)
    records = service.get_pending_maintenance(site_id)
    return [
        MaintenanceResponse(
            record_id=r.record_id,
            equipment_id=r.equipment_id,
            title=r.title,
            maintenance_type=r.maintenance_type,
            priority=r.priority,
            status=r.status,
            scheduled_date=r.scheduled_date,
            completed_at=r.completed_at
        )
        for r in records
    ]


@router.post("/maintenance/{record_id}/complete", response_model=MaintenanceResponse)
def complete_maintenance(
    record_id: str,
    data: MaintenanceComplete,
    db: Session = Depends(get_db)
):
    """Mark maintenance as completed."""
    service = get_fleet_service(db)
    try:
        record = service.complete_maintenance(
            record_id=record_id,
            performed_by=data.performed_by,
            parts_used=data.parts_used,
            labor_hours=data.labor_hours,
            total_cost=data.total_cost,
            notes=data.notes
        )
        return MaintenanceResponse(
            record_id=record.record_id,
            equipment_id=record.equipment_id,
            title=record.title,
            maintenance_type=record.maintenance_type,
            priority=record.priority,
            status=record.status,
            scheduled_date=record.scheduled_date,
            completed_at=record.completed_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/equipment/{equipment_id}/health", response_model=EquipmentHealthResponse)
def get_equipment_health(equipment_id: str, db: Session = Depends(get_db)):
    """Get equipment health summary."""
    service = get_fleet_service(db)
    health = service.get_equipment_health(equipment_id)
    if not health:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentHealthResponse(**health)
