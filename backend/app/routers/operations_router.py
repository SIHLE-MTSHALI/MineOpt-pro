"""
Material & Shift Operations REST API Router

Endpoints for load tickets, material tracking, shifts, and handovers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

from app.database import get_db
from app.services.material_shift_service import (
    MaterialTrackingService, ShiftService,
    get_material_tracking_service, get_shift_service
)
from app.domain.models_material_shift import MaterialType


router = APIRouter(prefix="/operations", tags=["Operations"])


# Schemas
class MaterialTypeEnum(str, Enum):
    ore_high_grade = "ore_high_grade"
    ore_low_grade = "ore_low_grade"
    marginal = "marginal"
    waste = "waste"
    topsoil = "topsoil"
    overburden = "overburden"


class LoadTicketCreate(BaseModel):
    site_id: str
    truck_fleet_number: str
    origin_name: str
    destination_name: str
    material_type: MaterialTypeEnum
    loaded_at: datetime
    shift_id: Optional[str] = None
    loader_fleet_number: Optional[str] = None
    tonnes: Optional[float] = None
    grade_percent: Optional[float] = None
    operator_name: Optional[str] = None


class LoadTicketResponse(BaseModel):
    ticket_id: str
    truck_fleet_number: str
    origin_name: str
    destination_name: str
    material_type: str
    tonnes: Optional[float]
    loaded_at: datetime
    dumped_at: Optional[datetime]
    is_valid: bool


class ShiftCreate(BaseModel):
    site_id: str
    shift_name: str
    scheduled_start: datetime
    scheduled_end: datetime
    supervisor_name: Optional[str] = None


class ShiftResponse(BaseModel):
    shift_id: str
    shift_name: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]


class HandoverCreate(BaseModel):
    shift_id: str
    outgoing_supervisor_name: str
    incoming_supervisor_name: Optional[str] = None
    ore_tonnes: float = 0
    waste_tonnes: float = 0
    total_loads: int = 0
    safety_notes: Optional[str] = None
    production_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    tasks_incomplete: Optional[List[str]] = None


class IncidentCreate(BaseModel):
    shift_id: str
    site_id: str
    incident_type: str
    severity: str
    title: str
    occurred_at: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    reported_by_name: Optional[str] = None


# Load Ticket Endpoints
@router.post("/tickets", response_model=LoadTicketResponse)
def create_load_ticket(data: LoadTicketCreate, db: Session = Depends(get_db)):
    """Create a load ticket."""
    service = get_material_tracking_service(db)
    ticket = service.create_load_ticket(
        site_id=data.site_id,
        truck_fleet_number=data.truck_fleet_number,
        origin_name=data.origin_name,
        destination_name=data.destination_name,
        material_type=MaterialType(data.material_type.value),
        loaded_at=data.loaded_at,
        shift_id=data.shift_id,
        loader_fleet_number=data.loader_fleet_number,
        tonnes=data.tonnes,
        grade_percent=data.grade_percent,
        operator_name=data.operator_name
    )
    return LoadTicketResponse(
        ticket_id=ticket.ticket_id,
        truck_fleet_number=ticket.truck_fleet_number,
        origin_name=ticket.origin_name,
        destination_name=ticket.destination_name,
        material_type=ticket.material_type.value if ticket.material_type else None,
        tonnes=ticket.tonnes,
        loaded_at=ticket.loaded_at,
        dumped_at=ticket.dumped_at,
        is_valid=ticket.is_valid
    )


@router.post("/tickets/{ticket_id}/dump")
def record_ticket_dump(
    ticket_id: str,
    dumped_at: datetime,
    net_weight_kg: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Record load dumped."""
    service = get_material_tracking_service(db)
    try:
        ticket = service.record_dump(ticket_id, dumped_at, net_weight_kg)
        return {"ticket_id": ticket_id, "dumped_at": dumped_at}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/shifts/{shift_id}/tickets", response_model=List[LoadTicketResponse])
def get_shift_tickets(shift_id: str, db: Session = Depends(get_db)):
    """Get all tickets for a shift."""
    service = get_material_tracking_service(db)
    tickets = service.get_tickets_for_shift(shift_id)
    return [
        LoadTicketResponse(
            ticket_id=t.ticket_id,
            truck_fleet_number=t.truck_fleet_number,
            origin_name=t.origin_name,
            destination_name=t.destination_name,
            material_type=t.material_type.value if t.material_type else None,
            tonnes=t.tonnes,
            loaded_at=t.loaded_at,
            dumped_at=t.dumped_at,
            is_valid=t.is_valid
        )
        for t in tickets
    ]


@router.get("/sites/{site_id}/material-flow")
def get_material_flow(
    site_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """Get material flow for Sankey diagram."""
    service = get_material_tracking_service(db)
    return service.get_material_flow(site_id, start_date, end_date)


# Shift Endpoints
@router.post("/shifts", response_model=ShiftResponse)
def start_shift(data: ShiftCreate, db: Session = Depends(get_db)):
    """Start a new shift."""
    service = get_shift_service(db)
    shift = service.start_shift(
        site_id=data.site_id,
        shift_name=data.shift_name,
        scheduled_start=data.scheduled_start,
        scheduled_end=data.scheduled_end,
        supervisor_name=data.supervisor_name
    )
    return ShiftResponse(
        shift_id=shift.shift_id,
        shift_name=shift.shift_name,
        status=shift.status,
        scheduled_start=shift.scheduled_start,
        scheduled_end=shift.scheduled_end,
        actual_start=shift.actual_start,
        actual_end=shift.actual_end
    )


@router.post("/shifts/{shift_id}/end")
def end_shift(shift_id: str, db: Session = Depends(get_db)):
    """End a shift."""
    service = get_shift_service(db)
    try:
        shift = service.end_shift(shift_id)
        return {"shift_id": shift_id, "status": "completed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sites/{site_id}/active-shift", response_model=Optional[ShiftResponse])
def get_active_shift(site_id: str, db: Session = Depends(get_db)):
    """Get currently active shift."""
    service = get_shift_service(db)
    shift = service.get_active_shift(site_id)
    if not shift:
        return None
    return ShiftResponse(
        shift_id=shift.shift_id,
        shift_name=shift.shift_name,
        status=shift.status,
        scheduled_start=shift.scheduled_start,
        scheduled_end=shift.scheduled_end,
        actual_start=shift.actual_start,
        actual_end=shift.actual_end
    )


@router.get("/shifts/{shift_id}/summary")
def get_shift_summary(shift_id: str, db: Session = Depends(get_db)):
    """Get complete shift summary."""
    service = get_shift_service(db)
    try:
        return service.get_shift_summary(shift_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Handover Endpoints
@router.post("/handovers")
def create_handover(data: HandoverCreate, db: Session = Depends(get_db)):
    """Create shift handover."""
    service = get_shift_service(db)
    handover = service.create_handover(
        shift_id=data.shift_id,
        outgoing_supervisor_name=data.outgoing_supervisor_name,
        incoming_supervisor_name=data.incoming_supervisor_name,
        ore_tonnes=data.ore_tonnes,
        waste_tonnes=data.waste_tonnes,
        total_loads=data.total_loads,
        safety_notes=data.safety_notes,
        production_notes=data.production_notes,
        equipment_notes=data.equipment_notes,
        tasks_incomplete=data.tasks_incomplete
    )
    return {"handover_id": handover.handover_id, "created": True}


@router.post("/handovers/{handover_id}/acknowledge")
def acknowledge_handover(
    handover_id: str,
    acknowledged_by: str = Query(...),
    db: Session = Depends(get_db)
):
    """Acknowledge handover receipt."""
    service = get_shift_service(db)
    try:
        service.acknowledge_handover(handover_id, acknowledged_by)
        return {"acknowledged": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Incident Endpoints
@router.post("/incidents")
def log_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    """Log a shift incident."""
    service = get_shift_service(db)
    incident = service.log_incident(
        shift_id=data.shift_id,
        site_id=data.site_id,
        incident_type=data.incident_type,
        severity=data.severity,
        title=data.title,
        occurred_at=data.occurred_at,
        description=data.description,
        location=data.location,
        reported_by_name=data.reported_by_name
    )
    return {"incident_id": incident.incident_id, "logged": True}


@router.get("/shifts/{shift_id}/incidents")
def get_shift_incidents(shift_id: str, db: Session = Depends(get_db)):
    """Get all incidents for a shift."""
    service = get_shift_service(db)
    incidents = service.get_shift_incidents(shift_id)
    return [
        {
            "incident_id": i.incident_id,
            "incident_type": i.incident_type,
            "severity": i.severity,
            "title": i.title,
            "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None,
            "status": i.status
        }
        for i in incidents
    ]
