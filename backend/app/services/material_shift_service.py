"""
Material Tracking Service

Load ticket management, material flow, and reconciliation.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from app.domain.models_material_shift import (
    LoadTicket, MaterialMovementSummary, MaterialType,
    Shift, ShiftHandover, ShiftIncident, ReconciliationPeriod
)


class MaterialTrackingService:
    """Service for material tracking and reconciliation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # LOAD TICKETS
    # =========================================================================
    
    def create_load_ticket(
        self,
        site_id: str,
        truck_fleet_number: str,
        origin_name: str,
        destination_name: str,
        material_type: MaterialType,
        loaded_at: datetime,
        shift_id: Optional[str] = None,
        loader_fleet_number: Optional[str] = None,
        origin_type: str = "dig_block",
        destination_type: str = "dump",
        tonnes: Optional[float] = None,
        grade_percent: Optional[float] = None,
        operator_name: Optional[str] = None
    ) -> LoadTicket:
        """Create a load ticket."""
        ticket = LoadTicket(
            site_id=site_id,
            shift_id=shift_id,
            truck_fleet_number=truck_fleet_number,
            loader_fleet_number=loader_fleet_number,
            origin_type=origin_type,
            origin_name=origin_name,
            destination_type=destination_type,
            destination_name=destination_name,
            material_type=material_type,
            tonnes=tonnes,
            grade_percent=grade_percent,
            loaded_at=loaded_at,
            operator_name=operator_name
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
    
    def record_dump(
        self,
        ticket_id: str,
        dumped_at: datetime,
        net_weight_kg: Optional[float] = None
    ) -> LoadTicket:
        """Record that load was dumped."""
        ticket = self.db.query(LoadTicket).filter(
            LoadTicket.ticket_id == ticket_id
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket.dumped_at = dumped_at
        if net_weight_kg:
            ticket.net_weight_kg = net_weight_kg
            ticket.tonnes = net_weight_kg / 1000
            ticket.weighed = True
        
        self.db.commit()
        return ticket
    
    def void_ticket(self, ticket_id: str, reason: str) -> LoadTicket:
        """Void a load ticket."""
        ticket = self.db.query(LoadTicket).filter(
            LoadTicket.ticket_id == ticket_id
        ).first()
        
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket.is_valid = False
        ticket.void_reason = reason
        
        self.db.commit()
        return ticket
    
    def get_tickets_for_shift(self, shift_id: str) -> List[LoadTicket]:
        """Get all tickets for a shift."""
        return self.db.query(LoadTicket).filter(
            LoadTicket.shift_id == shift_id,
            LoadTicket.is_valid == True
        ).order_by(LoadTicket.loaded_at).all()
    
    def get_material_flow(
        self,
        site_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated material flow for Sankey diagram."""
        tickets = self.db.query(LoadTicket).filter(
            LoadTicket.site_id == site_id,
            LoadTicket.loaded_at >= start_date,
            LoadTicket.loaded_at <= end_date,
            LoadTicket.is_valid == True
        ).all()
        
        # Build flow links
        flows = {}
        for t in tickets:
            key = (t.origin_name, t.destination_name, t.material_type.value if t.material_type else 'unknown')
            if key not in flows:
                flows[key] = {'tonnes': 0, 'loads': 0}
            flows[key]['tonnes'] += t.tonnes or 0
            flows[key]['loads'] += 1
        
        # Format for Sankey
        nodes = set()
        links = []
        
        for (source, target, material), data in flows.items():
            nodes.add(source)
            nodes.add(target)
            links.append({
                'source': source,
                'target': target,
                'material': material,
                'tonnes': data['tonnes'],
                'loads': data['loads']
            })
        
        return {
            'nodes': list(nodes),
            'links': links,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
    
    # =========================================================================
    # RECONCILIATION
    # =========================================================================
    
    def reconcile_period(
        self,
        site_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "month",
        planned_ore_tonnes: Optional[float] = None,
        planned_ore_grade: Optional[float] = None,
        planned_waste_tonnes: Optional[float] = None
    ) -> ReconciliationPeriod:
        """Create reconciliation for a period."""
        # Get delivered totals from tickets
        ore_result = self.db.query(
            func.sum(LoadTicket.tonnes),
            func.avg(LoadTicket.grade_percent)
        ).filter(
            LoadTicket.site_id == site_id,
            LoadTicket.loaded_at >= period_start,
            LoadTicket.loaded_at <= period_end,
            LoadTicket.is_valid == True,
            LoadTicket.material_type.in_([
                MaterialType.ORE_HIGH_GRADE,
                MaterialType.ORE_LOW_GRADE,
                MaterialType.MARGINAL
            ])
        ).first()
        
        waste_result = self.db.query(
            func.sum(LoadTicket.tonnes)
        ).filter(
            LoadTicket.site_id == site_id,
            LoadTicket.loaded_at >= period_start,
            LoadTicket.loaded_at <= period_end,
            LoadTicket.is_valid == True,
            LoadTicket.material_type.in_([
                MaterialType.WASTE,
                MaterialType.OVERBURDEN
            ])
        ).first()
        
        delivered_ore = ore_result[0] or 0
        delivered_grade = ore_result[1] or 0
        delivered_waste = waste_result[0] or 0
        
        # Calculate variances
        ore_variance = (delivered_ore - (planned_ore_tonnes or 0)) if planned_ore_tonnes else None
        ore_variance_pct = (ore_variance / planned_ore_tonnes * 100) if planned_ore_tonnes else None
        grade_variance = (delivered_grade - (planned_ore_grade or 0)) if planned_ore_grade else None
        
        recon = ReconciliationPeriod(
            site_id=site_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            period_name=period_start.strftime("%B %Y"),
            planned_ore_tonnes=planned_ore_tonnes,
            planned_ore_grade=planned_ore_grade,
            planned_waste_tonnes=planned_waste_tonnes,
            delivered_ore_tonnes=delivered_ore,
            delivered_ore_grade=delivered_grade,
            delivered_waste_tonnes=delivered_waste,
            ore_variance_tonnes=ore_variance,
            ore_variance_percent=ore_variance_pct,
            grade_variance=grade_variance
        )
        
        self.db.add(recon)
        self.db.commit()
        self.db.refresh(recon)
        return recon


class ShiftService:
    """Service for shift operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # SHIFTS
    # =========================================================================
    
    def start_shift(
        self,
        site_id: str,
        shift_name: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
        supervisor_name: Optional[str] = None
    ) -> Shift:
        """Start a new shift."""
        shift = Shift(
            site_id=site_id,
            shift_name=shift_name,
            shift_date=scheduled_start.date(),
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            actual_start=datetime.utcnow(),
            supervisor_name=supervisor_name,
            status="active"
        )
        
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift
    
    def end_shift(
        self,
        shift_id: str,
        handover_notes: Optional[str] = None
    ) -> Shift:
        """End a shift."""
        shift = self.db.query(Shift).filter(
            Shift.shift_id == shift_id
        ).first()
        
        if not shift:
            raise ValueError(f"Shift {shift_id} not found")
        
        shift.actual_end = datetime.utcnow()
        shift.status = "completed"
        
        self.db.commit()
        return shift
    
    def get_active_shift(self, site_id: str) -> Optional[Shift]:
        """Get currently active shift."""
        return self.db.query(Shift).filter(
            Shift.site_id == site_id,
            Shift.status == "active"
        ).first()
    
    # =========================================================================
    # HANDOVERS
    # =========================================================================
    
    def create_handover(
        self,
        shift_id: str,
        outgoing_supervisor_name: str,
        incoming_supervisor_name: Optional[str] = None,
        ore_tonnes: float = 0,
        waste_tonnes: float = 0,
        total_loads: int = 0,
        safety_notes: Optional[str] = None,
        production_notes: Optional[str] = None,
        equipment_notes: Optional[str] = None,
        tasks_incomplete: Optional[List[str]] = None
    ) -> ShiftHandover:
        """Create shift handover."""
        handover = ShiftHandover(
            shift_id=shift_id,
            handover_type="outgoing",
            outgoing_supervisor_name=outgoing_supervisor_name,
            incoming_supervisor_name=incoming_supervisor_name,
            ore_tonnes=ore_tonnes,
            waste_tonnes=waste_tonnes,
            total_loads=total_loads,
            safety_notes=safety_notes,
            production_notes=production_notes,
            equipment_notes=equipment_notes,
            tasks_incomplete=tasks_incomplete,
            handover_time=datetime.utcnow()
        )
        
        self.db.add(handover)
        self.db.commit()
        self.db.refresh(handover)
        return handover
    
    def acknowledge_handover(
        self,
        handover_id: str,
        acknowledged_by: str
    ) -> ShiftHandover:
        """Acknowledge receipt of handover."""
        handover = self.db.query(ShiftHandover).filter(
            ShiftHandover.handover_id == handover_id
        ).first()
        
        if not handover:
            raise ValueError(f"Handover {handover_id} not found")
        
        handover.acknowledged = True
        handover.acknowledged_at = datetime.utcnow()
        handover.acknowledged_by = acknowledged_by
        
        self.db.commit()
        return handover
    
    # =========================================================================
    # INCIDENTS
    # =========================================================================
    
    def log_incident(
        self,
        shift_id: str,
        site_id: str,
        incident_type: str,
        severity: str,
        title: str,
        occurred_at: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        reported_by_name: Optional[str] = None,
        equipment_fleet_number: Optional[str] = None,
        immediate_actions: Optional[str] = None
    ) -> ShiftIncident:
        """Log a shift incident."""
        incident = ShiftIncident(
            shift_id=shift_id,
            site_id=site_id,
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            location=location,
            occurred_at=occurred_at,
            reported_by_name=reported_by_name,
            equipment_fleet_number=equipment_fleet_number,
            immediate_actions=immediate_actions,
            investigation_required=severity in ['serious', 'critical']
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident
    
    def get_shift_incidents(self, shift_id: str) -> List[ShiftIncident]:
        """Get all incidents for a shift."""
        return self.db.query(ShiftIncident).filter(
            ShiftIncident.shift_id == shift_id
        ).order_by(ShiftIncident.occurred_at).all()
    
    def get_shift_summary(self, shift_id: str) -> Dict[str, Any]:
        """Get complete shift summary."""
        shift = self.db.query(Shift).filter(
            Shift.shift_id == shift_id
        ).first()
        
        if not shift:
            raise ValueError(f"Shift {shift_id} not found")
        
        # Get tickets for shift
        tickets = self.db.query(LoadTicket).filter(
            LoadTicket.shift_id == shift_id,
            LoadTicket.is_valid == True
        ).all()
        
        # Aggregate by material type
        ore_tonnes = sum(t.tonnes or 0 for t in tickets 
                        if t.material_type in [MaterialType.ORE_HIGH_GRADE, MaterialType.ORE_LOW_GRADE])
        waste_tonnes = sum(t.tonnes or 0 for t in tickets 
                         if t.material_type in [MaterialType.WASTE, MaterialType.OVERBURDEN])
        
        # Get incidents
        incidents = self.get_shift_incidents(shift_id)
        
        return {
            'shift_id': shift_id,
            'shift_name': shift.shift_name,
            'status': shift.status,
            'start': shift.actual_start.isoformat() if shift.actual_start else None,
            'end': shift.actual_end.isoformat() if shift.actual_end else None,
            'supervisor': shift.supervisor_name,
            'production': {
                'total_loads': len(tickets),
                'ore_tonnes': ore_tonnes,
                'waste_tonnes': waste_tonnes,
                'total_tonnes': ore_tonnes + waste_tonnes
            },
            'incidents': {
                'total': len(incidents),
                'by_severity': {
                    'critical': len([i for i in incidents if i.severity == 'critical']),
                    'serious': len([i for i in incidents if i.severity == 'serious']),
                    'moderate': len([i for i in incidents if i.severity == 'moderate']),
                    'minor': len([i for i in incidents if i.severity == 'minor'])
                }
            }
        }


def get_material_tracking_service(db: Session) -> MaterialTrackingService:
    """Factory for material tracking service."""
    return MaterialTrackingService(db)


def get_shift_service(db: Session) -> ShiftService:
    """Factory for shift service."""
    return ShiftService(db)
