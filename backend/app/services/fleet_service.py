"""
Fleet Management Service

Comprehensive service for equipment tracking, GPS, haul cycles, and maintenance.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json
import math
import logging

from app.domain.models_fleet import (
    Equipment, EquipmentType, EquipmentStatus,
    GPSReading, Geofence, GeofenceViolation,
    HaulCycle, MaintenanceRecord, ComponentLife
)


class FleetService:
    """Service for fleet management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # EQUIPMENT CRUD
    # =========================================================================
    
    def register_equipment(
        self,
        site_id: str,
        fleet_number: str,
        equipment_type: EquipmentType,
        name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        payload_tonnes: Optional[float] = None,
        bucket_capacity_bcm: Optional[float] = None
    ) -> Equipment:
        """Register new equipment in the fleet."""
        equipment = Equipment(
            site_id=site_id,
            fleet_number=fleet_number,
            equipment_type=equipment_type,
            name=name or fleet_number,
            manufacturer=manufacturer,
            model=model,
            payload_tonnes=payload_tonnes,
            bucket_capacity_bcm=bucket_capacity_bcm
        )
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment
    
    def get_equipment(self, equipment_id: str) -> Optional[Equipment]:
        """Get equipment by ID."""
        return self.db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()
    
    def get_equipment_by_fleet_number(self, site_id: str, fleet_number: str) -> Optional[Equipment]:
        """Get equipment by fleet number."""
        return self.db.query(Equipment).filter(
            Equipment.site_id == site_id,
            Equipment.fleet_number == fleet_number
        ).first()
    
    def list_equipment(
        self,
        site_id: str,
        equipment_type: Optional[EquipmentType] = None,
        status: Optional[EquipmentStatus] = None,
        active_only: bool = True
    ) -> List[Equipment]:
        """List equipment with filters."""
        query = self.db.query(Equipment).filter(Equipment.site_id == site_id)
        
        if active_only:
            query = query.filter(Equipment.is_active == True)
        if equipment_type:
            query = query.filter(Equipment.equipment_type == equipment_type)
        if status:
            query = query.filter(Equipment.status == status)
        
        return query.order_by(Equipment.fleet_number).all()
    
    def update_equipment_status(
        self,
        equipment_id: str,
        status: EquipmentStatus,
        operator_id: Optional[str] = None
    ) -> Equipment:
        """Update equipment operating status."""
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment {equipment_id} not found")
        
        equipment.status = status
        if operator_id is not None:
            equipment.current_operator_id = operator_id
        equipment.updated_at = datetime.utcnow()
        
        self.db.commit()
        return equipment
    
    # =========================================================================
    # GPS TRACKING
    # =========================================================================
    
    def record_gps_reading(
        self,
        equipment_id: str,
        latitude: float,
        longitude: float,
        timestamp: datetime,
        altitude: Optional[float] = None,
        heading: Optional[float] = None,
        speed_kmh: Optional[float] = None,
        hdop: Optional[float] = None,
        num_satellites: Optional[int] = None,
        engine_on: bool = True,
        status: Optional[EquipmentStatus] = None
    ) -> GPSReading:
        """Record GPS reading for equipment."""
        reading = GPSReading(
            equipment_id=equipment_id,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            heading=heading,
            speed_kmh=speed_kmh,
            hdop=hdop,
            num_satellites=num_satellites,
            engine_on=engine_on,
            status=status,
            timestamp=timestamp
        )
        self.db.add(reading)
        
        # Update equipment's last known position
        equipment = self.get_equipment(equipment_id)
        if equipment:
            equipment.last_latitude = latitude
            equipment.last_longitude = longitude
            equipment.last_heading = heading
            equipment.last_speed_kmh = speed_kmh
            equipment.last_position_time = timestamp
            if status:
                equipment.status = status
        
        self.db.commit()
        self.db.refresh(reading)
        
        # Check geofence violations
        self._check_geofence_violations(equipment_id, latitude, longitude, speed_kmh, timestamp)
        
        return reading
    
    def get_equipment_trail(
        self,
        equipment_id: str,
        start_time: datetime,
        end_time: datetime,
        simplify: bool = True
    ) -> List[GPSReading]:
        """Get GPS trail for equipment in time range."""
        query = self.db.query(GPSReading).filter(
            GPSReading.equipment_id == equipment_id,
            GPSReading.timestamp >= start_time,
            GPSReading.timestamp <= end_time
        ).order_by(GPSReading.timestamp)
        
        readings = query.all()
        
        if simplify and len(readings) > 500:
            # Downsample to reduce points for display
            step = len(readings) // 500
            readings = readings[::step]
        
        return readings
    
    def get_fleet_positions(self, site_id: str) -> List[Dict[str, Any]]:
        """Get current positions of all equipment in site."""
        equipment_list = self.list_equipment(site_id, active_only=True)
        
        positions = []
        for eq in equipment_list:
            if eq.last_latitude and eq.last_longitude:
                positions.append({
                    'equipment_id': eq.equipment_id,
                    'fleet_number': eq.fleet_number,
                    'name': eq.name,
                    'equipment_type': eq.equipment_type.value,
                    'status': eq.status.value if eq.status else None,
                    'latitude': eq.last_latitude,
                    'longitude': eq.last_longitude,
                    'heading': eq.last_heading,
                    'speed_kmh': eq.last_speed_kmh,
                    'last_update': eq.last_position_time.isoformat() if eq.last_position_time else None
                })
        
        return positions
    
    # =========================================================================
    # GEOFENCING
    # =========================================================================
    
    def create_geofence(
        self,
        site_id: str,
        name: str,
        boundary_coords: List[Tuple[float, float]],
        zone_type: str = "general",
        speed_limit_kmh: Optional[float] = None,
        is_restricted: bool = False,
        alert_on_entry: bool = False,
        alert_on_exit: bool = False
    ) -> Geofence:
        """Create a geofence zone."""
        # Convert coords to GeoJSON polygon
        geojson = {
            "type": "Polygon",
            "coordinates": [[list(coord) for coord in boundary_coords]]
        }
        
        geofence = Geofence(
            site_id=site_id,
            name=name,
            zone_type=zone_type,
            boundary_geojson=geojson,
            speed_limit_kmh=speed_limit_kmh,
            is_restricted=is_restricted,
            alert_on_entry=alert_on_entry,
            alert_on_exit=alert_on_exit
        )
        self.db.add(geofence)
        self.db.commit()
        self.db.refresh(geofence)
        return geofence
    
    def list_geofences(self, site_id: str, active_only: bool = True) -> List[Geofence]:
        """List geofences for site."""
        query = self.db.query(Geofence).filter(Geofence.site_id == site_id)
        if active_only:
            query = query.filter(Geofence.is_active == True)
        return query.all()
    
    def _check_geofence_violations(
        self,
        equipment_id: str,
        latitude: float,
        longitude: float,
        speed_kmh: Optional[float],
        timestamp: datetime
    ) -> List[GeofenceViolation]:
        """Check if position violates any geofences."""
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return []
        
        geofences = self.list_geofences(equipment.site_id)
        violations = []
        
        for gf in geofences:
            if not self._is_geofence_active(gf, timestamp):
                continue
            
            inside = self._point_in_geofence(latitude, longitude, gf)
            
            # Check violations
            if inside and gf.is_restricted:
                violation = self._create_violation(
                    gf.geofence_id, equipment_id,
                    "unauthorized_entry", latitude, longitude,
                    speed_kmh, gf.speed_limit_kmh, timestamp
                )
                violations.append(violation)
            
            if inside and gf.speed_limit_kmh and speed_kmh:
                if speed_kmh > gf.speed_limit_kmh:
                    violation = self._create_violation(
                        gf.geofence_id, equipment_id,
                        "speeding", latitude, longitude,
                        speed_kmh, gf.speed_limit_kmh, timestamp
                    )
                    violations.append(violation)
        
        return violations
    
    def _is_geofence_active(self, geofence: Geofence, timestamp: datetime) -> bool:
        """Check if geofence is active at given time."""
        if not geofence.is_active:
            return False
        
        # Check time window if specified
        if geofence.active_start_time and geofence.active_end_time:
            current_time = timestamp.strftime("%H:%M")
            if not (geofence.active_start_time <= current_time <= geofence.active_end_time):
                return False
        
        # Check day of week if specified
        if geofence.active_days:
            day_name = timestamp.strftime("%a")
            if day_name not in geofence.active_days:
                return False
        
        return True
    
    def _point_in_geofence(self, lat: float, lon: float, geofence: Geofence) -> bool:
        """Check if point is inside geofence polygon."""
        try:
            coords = geofence.boundary_geojson['coordinates'][0]
            return self._point_in_polygon(lon, lat, coords)
        except (KeyError, IndexError):
            return False
    
    def _point_in_polygon(self, x: float, y: float, polygon: List) -> bool:
        """Ray casting algorithm for point-in-polygon."""
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i][0], polygon[i][1]
            xj, yj = polygon[j][0], polygon[j][1]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def _create_violation(
        self,
        geofence_id: str,
        equipment_id: str,
        violation_type: str,
        latitude: float,
        longitude: float,
        speed_kmh: Optional[float],
        speed_limit_kmh: Optional[float],
        timestamp: datetime
    ) -> GeofenceViolation:
        """Create a geofence violation record."""
        violation = GeofenceViolation(
            geofence_id=geofence_id,
            equipment_id=equipment_id,
            violation_type=violation_type,
            latitude=latitude,
            longitude=longitude,
            speed_kmh=speed_kmh,
            speed_limit_kmh=speed_limit_kmh,
            violation_time=timestamp
        )
        self.db.add(violation)
        self.db.commit()
        return violation
    
    # =========================================================================
    # HAUL CYCLE DETECTION
    # =========================================================================
    
    def detect_haul_cycles(
        self,
        equipment_id: str,
        start_time: datetime,
        end_time: datetime,
        loading_zones: List[str] = None,
        dumping_zones: List[str] = None
    ) -> List[HaulCycle]:
        """Detect haul cycles from GPS data."""
        readings = self.get_equipment_trail(equipment_id, start_time, end_time, simplify=False)
        
        if len(readings) < 10:
            return []
        
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return []
        
        cycles = []
        current_cycle = None
        current_phase = None
        phase_start_time = None
        phase_start_reading = None
        
        # Simplified cycle detection based on speed patterns
        for i, reading in enumerate(readings):
            speed = reading.speed_kmh or 0
            
            # Detect loading (stopped with engine on)
            if speed < 2 and reading.engine_on:
                if current_phase != 'loading':
                    if current_cycle and current_phase == 'travel_loaded':
                        # Start dumping phase
                        current_phase = 'dumping'
                        phase_start_time = reading.timestamp
                    elif not current_cycle:
                        # Start new cycle
                        current_cycle = {
                            'start': reading.timestamp,
                            'loading_start': reading.timestamp,
                            'source_lat': reading.latitude,
                            'source_lon': reading.longitude
                        }
                        current_phase = 'loading'
                        phase_start_time = reading.timestamp
            
            # Detect traveling
            elif speed > 10:
                if current_phase == 'loading' and current_cycle:
                    current_cycle['loading_sec'] = (reading.timestamp - phase_start_time).total_seconds()
                    current_phase = 'travel_loaded'
                    phase_start_time = reading.timestamp
                    phase_start_reading = reading
                
                elif current_phase == 'dumping' and current_cycle:
                    current_cycle['dumping_sec'] = (reading.timestamp - phase_start_time).total_seconds()
                    current_cycle['dest_lat'] = phase_start_reading.latitude if phase_start_reading else reading.latitude
                    current_cycle['dest_lon'] = phase_start_reading.longitude if phase_start_reading else reading.longitude
                    current_phase = 'travel_empty'
                    phase_start_time = reading.timestamp
            
            # Detect cycle completion (back at loading area)
            if current_phase == 'travel_empty' and current_cycle:
                source_lat = current_cycle.get('source_lat', 0)
                source_lon = current_cycle.get('source_lon', 0)
                dist_to_source = self._haversine_distance(
                    reading.latitude, reading.longitude,
                    source_lat, source_lon
                )
                
                if dist_to_source < 0.1:  # Within 100m of source
                    current_cycle['travel_empty_sec'] = (reading.timestamp - phase_start_time).total_seconds()
                    current_cycle['end'] = reading.timestamp
                    
                    # Save complete cycle
                    cycle = self._save_haul_cycle(equipment, current_cycle)
                    if cycle:
                        cycles.append(cycle)
                    
                    current_cycle = None
                    current_phase = None
        
        return cycles
    
    def _save_haul_cycle(self, equipment: Equipment, cycle_data: Dict) -> Optional[HaulCycle]:
        """Save detected haul cycle to database."""
        try:
            total_sec = (cycle_data['end'] - cycle_data['start']).total_seconds()
            
            cycle = HaulCycle(
                equipment_id=equipment.equipment_id,
                site_id=equipment.site_id,
                loading_sec=cycle_data.get('loading_sec', 0),
                travel_loaded_sec=cycle_data.get('travel_loaded_sec', 0),
                dumping_sec=cycle_data.get('dumping_sec', 0),
                travel_empty_sec=cycle_data.get('travel_empty_sec', 0),
                total_cycle_sec=total_sec,
                cycle_start=cycle_data['start'],
                cycle_end=cycle_data['end'],
                payload_tonnes=equipment.payload_tonnes
            )
            self.db.add(cycle)
            self.db.commit()
            return cycle
        except Exception as e:
            self.logger.error(f"Error saving haul cycle: {e}")
            return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_cycle_statistics(
        self,
        site_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get haul cycle statistics for site."""
        cycles = self.db.query(HaulCycle).filter(
            HaulCycle.site_id == site_id,
            HaulCycle.cycle_start >= start_date,
            HaulCycle.cycle_end <= end_date,
            HaulCycle.is_valid == True
        ).all()
        
        if not cycles:
            return {'total_cycles': 0}
        
        total_cycles = len(cycles)
        avg_cycle_time = sum(c.total_cycle_sec for c in cycles) / total_cycles
        avg_loading = sum(c.loading_sec or 0 for c in cycles) / total_cycles
        avg_travel_loaded = sum(c.travel_loaded_sec or 0 for c in cycles) / total_cycles
        avg_dumping = sum(c.dumping_sec or 0 for c in cycles) / total_cycles
        avg_travel_empty = sum(c.travel_empty_sec or 0 for c in cycles) / total_cycles
        total_tonnes = sum(c.payload_tonnes or 0 for c in cycles)
        
        return {
            'total_cycles': total_cycles,
            'total_tonnes': total_tonnes,
            'avg_cycle_time_min': avg_cycle_time / 60,
            'avg_loading_min': avg_loading / 60,
            'avg_travel_loaded_min': avg_travel_loaded / 60,
            'avg_dumping_min': avg_dumping / 60,
            'avg_travel_empty_min': avg_travel_empty / 60,
            'productivity_tph': total_tonnes / ((end_date - start_date).total_seconds() / 3600) if cycles else 0
        }
    
    # =========================================================================
    # MAINTENANCE
    # =========================================================================
    
    def schedule_maintenance(
        self,
        equipment_id: str,
        title: str,
        maintenance_type: str = "preventive",
        scheduled_date: Optional[datetime] = None,
        due_engine_hours: Optional[float] = None,
        priority: str = "medium",
        description: Optional[str] = None
    ) -> MaintenanceRecord:
        """Schedule maintenance for equipment."""
        record = MaintenanceRecord(
            equipment_id=equipment_id,
            title=title,
            maintenance_type=maintenance_type,
            scheduled_date=scheduled_date,
            due_engine_hours=due_engine_hours,
            priority=priority,
            description=description,
            status="scheduled"
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def get_pending_maintenance(self, site_id: str) -> List[MaintenanceRecord]:
        """Get all pending maintenance for site equipment."""
        equipment_ids = [e.equipment_id for e in self.list_equipment(site_id)]
        
        return self.db.query(MaintenanceRecord).filter(
            MaintenanceRecord.equipment_id.in_(equipment_ids),
            MaintenanceRecord.status.in_(["scheduled", "in_progress"])
        ).order_by(MaintenanceRecord.scheduled_date).all()
    
    def complete_maintenance(
        self,
        record_id: str,
        performed_by: str,
        parts_used: Optional[List[Dict]] = None,
        labor_hours: Optional[float] = None,
        total_cost: Optional[float] = None,
        notes: Optional[str] = None
    ) -> MaintenanceRecord:
        """Mark maintenance as completed."""
        record = self.db.query(MaintenanceRecord).filter(
            MaintenanceRecord.record_id == record_id
        ).first()
        
        if not record:
            raise ValueError(f"Maintenance record {record_id} not found")
        
        record.status = "completed"
        record.completed_at = datetime.utcnow()
        record.performed_by = performed_by
        record.parts_used = parts_used
        record.labor_hours = labor_hours
        record.total_cost = total_cost
        record.notes = notes
        
        # Update equipment engine hours at service
        equipment = self.get_equipment(record.equipment_id)
        if equipment:
            record.engine_hours_at_service = equipment.engine_hours
        
        self.db.commit()
        return record
    
    def get_equipment_health(self, equipment_id: str) -> Dict[str, Any]:
        """Get equipment health summary."""
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            return {}
        
        # Get component life data
        components = self.db.query(ComponentLife).filter(
            ComponentLife.equipment_id == equipment_id,
            ComponentLife.is_active == True
        ).all()
        
        # Get maintenance history
        recent_maintenance = self.db.query(MaintenanceRecord).filter(
            MaintenanceRecord.equipment_id == equipment_id,
            MaintenanceRecord.status == "completed"
        ).order_by(MaintenanceRecord.completed_at.desc()).limit(5).all()
        
        # Calculate overall health score
        min_life = 100
        for comp in components:
            if comp.remaining_life_percent < min_life:
                min_life = comp.remaining_life_percent
        
        return {
            'equipment_id': equipment_id,
            'fleet_number': equipment.fleet_number,
            'status': equipment.status.value if equipment.status else None,
            'engine_hours': equipment.engine_hours,
            'health_score': min_life,
            'components': [
                {
                    'type': c.component_type,
                    'name': c.component_name,
                    'remaining_life_percent': c.remaining_life_percent
                }
                for c in components
            ],
            'recent_maintenance': [
                {
                    'title': m.title,
                    'completed_at': m.completed_at.isoformat() if m.completed_at else None,
                    'type': m.maintenance_type
                }
                for m in recent_maintenance
            ]
        }


def get_fleet_service(db: Session) -> FleetService:
    """Factory function for fleet service."""
    return FleetService(db)
