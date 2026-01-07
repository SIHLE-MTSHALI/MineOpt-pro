"""
Geotechnical, Environmental & Safety Services

Services for slope monitoring, water management, dust, rehabilitation, and safety zones.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import math
import logging

from app.domain.models_geotech_safety import (
    GeotechDomain, SlopeMonitoringPrism, PrismReading,
    MonitoringBore, WaterLevelReading,
    DustMonitor, DustReading, RehabilitationArea,
    HazardZone, HazardZoneEntry, FatigueEvent, OperatorFatigueScore
)


class GeotechService:
    """Service for geotechnical monitoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def create_domain(
        self,
        site_id: str,
        name: str,
        batter_angle: float,
        berm_width: float,
        batter_height: float,
        inter_ramp_angle: Optional[float] = None,
        rock_type: Optional[str] = None,
        boundary_geojson: Optional[dict] = None
    ) -> GeotechDomain:
        """Create geotechnical domain."""
        domain = GeotechDomain(
            site_id=site_id,
            name=name,
            rock_type=rock_type,
            boundary_geojson=boundary_geojson,
            inter_ramp_angle=inter_ramp_angle,
            batter_angle=batter_angle,
            berm_width=berm_width,
            batter_height=batter_height
        )
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        return domain
    
    def install_prism(
        self,
        site_id: str,
        prism_name: str,
        x: float,
        y: float,
        z: float,
        domain_id: Optional[str] = None,
        warning_threshold_mm: float = 50,
        critical_threshold_mm: float = 100
    ) -> SlopeMonitoringPrism:
        """Install a monitoring prism."""
        prism = SlopeMonitoringPrism(
            site_id=site_id,
            domain_id=domain_id,
            prism_name=prism_name,
            initial_x=x,
            initial_y=y,
            initial_z=z,
            current_x=x,
            current_y=y,
            current_z=z,
            installed_at=datetime.utcnow(),
            warning_threshold_mm=warning_threshold_mm,
            critical_threshold_mm=critical_threshold_mm
        )
        self.db.add(prism)
        self.db.commit()
        self.db.refresh(prism)
        return prism
    
    def record_prism_reading(
        self,
        prism_id: str,
        x: float,
        y: float,
        z: float,
        measured_at: datetime,
        accuracy_mm: Optional[float] = None
    ) -> PrismReading:
        """Record prism position reading."""
        prism = self.db.query(SlopeMonitoringPrism).filter(
            SlopeMonitoringPrism.prism_id == prism_id
        ).first()
        
        if not prism:
            raise ValueError(f"Prism {prism_id} not found")
        
        # Calculate displacement from initial
        delta_x = (x - prism.initial_x) * 1000  # Convert to mm
        delta_y = (y - prism.initial_y) * 1000
        delta_z = (z - prism.initial_z) * 1000
        total_disp = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
        
        # Calculate rate if previous reading exists
        last_reading = self.db.query(PrismReading).filter(
            PrismReading.prism_id == prism_id
        ).order_by(PrismReading.measured_at.desc()).first()
        
        rate = 0
        if last_reading:
            days = (measured_at - last_reading.measured_at).total_seconds() / 86400
            if days > 0:
                prev_disp = last_reading.total_displacement_mm or 0
                rate = (total_disp - prev_disp) / days
        
        reading = PrismReading(
            prism_id=prism_id,
            x=x,
            y=y,
            z=z,
            delta_x=delta_x,
            delta_y=delta_y,
            delta_z=delta_z,
            total_displacement_mm=total_disp,
            displacement_rate_mm_day=rate,
            accuracy_mm=accuracy_mm,
            measured_at=measured_at
        )
        self.db.add(reading)
        
        # Update prism
        prism.current_x = x
        prism.current_y = y
        prism.current_z = z
        prism.total_displacement_mm = total_disp
        prism.displacement_rate_mm_day = rate
        prism.last_reading_at = measured_at
        
        # Check thresholds
        if total_disp >= prism.critical_threshold_mm:
            prism.alert_status = "critical"
        elif total_disp >= prism.warning_threshold_mm:
            prism.alert_status = "warning"
        else:
            prism.alert_status = "normal"
        
        self.db.commit()
        self.db.refresh(reading)
        return reading
    
    def get_slope_alerts(self, site_id: str) -> List[SlopeMonitoringPrism]:
        """Get prisms with active alerts."""
        return self.db.query(SlopeMonitoringPrism).filter(
            SlopeMonitoringPrism.site_id == site_id,
            SlopeMonitoringPrism.is_active == True,
            SlopeMonitoringPrism.alert_status.in_(["warning", "critical"])
        ).all()


class WaterService:
    """Service for groundwater management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_bore(
        self,
        site_id: str,
        bore_name: str,
        easting: float,
        northing: float,
        bore_type: str = "monitoring",
        collar_rl: Optional[float] = None,
        total_depth_m: Optional[float] = None
    ) -> MonitoringBore:
        """Create monitoring bore."""
        bore = MonitoringBore(
            site_id=site_id,
            bore_name=bore_name,
            bore_type=bore_type,
            easting=easting,
            northing=northing,
            collar_rl=collar_rl,
            total_depth_m=total_depth_m
        )
        self.db.add(bore)
        self.db.commit()
        self.db.refresh(bore)
        return bore
    
    def record_water_level(
        self,
        bore_id: str,
        water_level_m: float,
        measured_at: datetime,
        measured_by: Optional[str] = None
    ) -> WaterLevelReading:
        """Record water level reading."""
        bore = self.db.query(MonitoringBore).filter(
            MonitoringBore.bore_id == bore_id
        ).first()
        
        if not bore:
            raise ValueError(f"Bore {bore_id} not found")
        
        water_rl = bore.collar_rl - water_level_m if bore.collar_rl else None
        
        reading = WaterLevelReading(
            bore_id=bore_id,
            water_level_m=water_level_m,
            water_rl=water_rl,
            measured_at=measured_at,
            measured_by=measured_by
        )
        self.db.add(reading)
        
        bore.current_water_level_m = water_level_m
        bore.current_water_rl = water_rl
        bore.last_reading_at = measured_at
        
        self.db.commit()
        self.db.refresh(reading)
        return reading


class EnvironmentalService:
    """Service for environmental monitoring."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_dust_monitor(
        self,
        site_id: str,
        name: str,
        easting: Optional[float] = None,
        northing: Optional[float] = None,
        pm10_threshold: float = 50,
        pm25_threshold: float = 25
    ) -> DustMonitor:
        """Create dust monitoring station."""
        monitor = DustMonitor(
            site_id=site_id,
            name=name,
            easting=easting,
            northing=northing,
            pm10_threshold_ug_m3=pm10_threshold,
            pm25_threshold_ug_m3=pm25_threshold
        )
        self.db.add(monitor)
        self.db.commit()
        self.db.refresh(monitor)
        return monitor
    
    def record_dust_reading(
        self,
        monitor_id: str,
        measured_at: datetime,
        pm10: Optional[float] = None,
        pm25: Optional[float] = None,
        wind_speed: Optional[float] = None,
        wind_direction: Optional[str] = None
    ) -> DustReading:
        """Record dust reading."""
        monitor = self.db.query(DustMonitor).filter(
            DustMonitor.monitor_id == monitor_id
        ).first()
        
        if not monitor:
            raise ValueError(f"Monitor {monitor_id} not found")
        
        reading = DustReading(
            monitor_id=monitor_id,
            pm10_ug_m3=pm10,
            pm25_ug_m3=pm25,
            pm10_exceeded=pm10 and pm10 > monitor.pm10_threshold_ug_m3,
            pm25_exceeded=pm25 and pm25 > monitor.pm25_threshold_ug_m3,
            wind_speed_kmh=wind_speed,
            wind_direction=wind_direction,
            measured_at=measured_at
        )
        self.db.add(reading)
        
        monitor.last_reading_at = measured_at
        
        self.db.commit()
        self.db.refresh(reading)
        return reading
    
    def get_exceedances(
        self,
        site_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[DustReading]:
        """Get dust exceedance events."""
        monitor_ids = [m.monitor_id for m in 
                      self.db.query(DustMonitor).filter(DustMonitor.site_id == site_id).all()]
        
        return self.db.query(DustReading).filter(
            DustReading.monitor_id.in_(monitor_ids),
            DustReading.measured_at >= start_date,
            DustReading.measured_at <= end_date,
            (DustReading.pm10_exceeded == True) | (DustReading.pm25_exceeded == True)
        ).order_by(DustReading.measured_at.desc()).all()
    
    def create_rehab_area(
        self,
        site_id: str,
        name: str,
        area_type: str,
        boundary_geojson: dict,
        area_hectares: Optional[float] = None
    ) -> RehabilitationArea:
        """Create rehabilitation area."""
        area = RehabilitationArea(
            site_id=site_id,
            name=name,
            area_type=area_type,
            boundary_geojson=boundary_geojson,
            area_hectares=area_hectares,
            status="active"
        )
        self.db.add(area)
        self.db.commit()
        self.db.refresh(area)
        return area


class SafetyService:
    """Service for safety management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_hazard_zone(
        self,
        site_id: str,
        name: str,
        hazard_type: str,
        boundary_geojson: dict,
        severity: str = "medium",
        is_exclusion: bool = True,
        active_from: Optional[datetime] = None,
        active_to: Optional[datetime] = None
    ) -> HazardZone:
        """Create hazard zone."""
        zone = HazardZone(
            site_id=site_id,
            name=name,
            hazard_type=hazard_type,
            severity=severity,
            boundary_geojson=boundary_geojson,
            is_exclusion=is_exclusion,
            active_from=active_from,
            active_to=active_to
        )
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return zone
    
    def record_zone_entry(
        self,
        zone_id: str,
        entry_time: datetime,
        equipment_fleet_number: Optional[str] = None,
        person_name: Optional[str] = None,
        was_authorized: bool = False,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> HazardZoneEntry:
        """Record entry into hazard zone."""
        entry = HazardZoneEntry(
            zone_id=zone_id,
            equipment_fleet_number=equipment_fleet_number,
            person_name=person_name,
            entry_time=entry_time,
            was_authorized=was_authorized,
            entry_latitude=latitude,
            entry_longitude=longitude
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def record_fatigue_event(
        self,
        site_id: str,
        operator_name: str,
        equipment_fleet_number: str,
        event_type: str,
        severity: str,
        occurred_at: datetime,
        detection_system: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> FatigueEvent:
        """Record fatigue detection event."""
        event = FatigueEvent(
            site_id=site_id,
            operator_name=operator_name,
            equipment_fleet_number=equipment_fleet_number,
            event_type=event_type,
            severity=severity,
            occurred_at=occurred_at,
            detection_system=detection_system,
            latitude=latitude,
            longitude=longitude
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def calculate_operator_fatigue_score(
        self,
        operator_id: str,
        site_id: str
    ) -> OperatorFatigueScore:
        """Calculate operator fatigue risk score."""
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        # Count events
        events_24h = self.db.query(FatigueEvent).filter(
            FatigueEvent.operator_id == operator_id,
            FatigueEvent.occurred_at >= day_ago
        ).count()
        
        events_7d = self.db.query(FatigueEvent).filter(
            FatigueEvent.operator_id == operator_id,
            FatigueEvent.occurred_at >= week_ago
        ).count()
        
        # Calculate score (simplified)
        base_score = 0
        base_score += events_24h * 20
        base_score += events_7d * 5
        risk_score = min(100, base_score)
        
        # Determine level
        if risk_score >= 80:
            level = "critical"
            action = "Mandatory rest required"
            mandatory = True
        elif risk_score >= 60:
            level = "fatigued"
            action = "Extended break recommended"
            mandatory = False
        elif risk_score >= 30:
            level = "moderate"
            action = "Monitor closely"
            mandatory = False
        else:
            level = "alert"
            action = "Normal operations"
            mandatory = False
        
        score = OperatorFatigueScore(
            operator_id=operator_id,
            site_id=site_id,
            fatigue_risk_score=risk_score,
            alertness_level=level,
            events_24h=events_24h,
            events_7d=events_7d,
            recommended_action=action,
            mandatory_rest=mandatory,
            valid_until=now + timedelta(hours=4)
        )
        
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score


def get_geotech_service(db: Session) -> GeotechService:
    return GeotechService(db)

def get_water_service(db: Session) -> WaterService:
    return WaterService(db)

def get_environmental_service(db: Session) -> EnvironmentalService:
    return EnvironmentalService(db)

def get_safety_service(db: Session) -> SafetyService:
    return SafetyService(db)
