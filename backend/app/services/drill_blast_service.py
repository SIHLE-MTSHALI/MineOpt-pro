"""
Drill & Blast Service

Pattern design, fragmentation prediction, and blast management.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import math
import logging

from app.domain.models_drill_blast import (
    BlastPattern, DrillHole, DrillHoleStatus, BlastEvent,
    FragmentationModel, ExplosiveType
)


# Explosive properties (relative to ANFO)
EXPLOSIVE_PROPERTIES = {
    ExplosiveType.ANFO: {
        'rws': 100,  # Relative Weight Strength
        'density': 0.8,  # g/cc
        'vod': 3500,  # Velocity of Detonation m/s
        'energy_kj_kg': 3900
    },
    ExplosiveType.EMULSION: {
        'rws': 115,
        'density': 1.15,
        'vod': 5500,
        'energy_kj_kg': 4200
    },
    ExplosiveType.HEAVY_ANFO: {
        'rws': 108,
        'density': 1.0,
        'vod': 4500,
        'energy_kj_kg': 4050
    },
    ExplosiveType.WATERGEL: {
        'rws': 110,
        'density': 1.2,
        'vod': 5000,
        'energy_kj_kg': 4100
    },
    ExplosiveType.DYNAMITE: {
        'rws': 120,
        'density': 1.4,
        'vod': 5500,
        'energy_kj_kg': 4400
    }
}


class DrillBlastService:
    """Service for drill and blast operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # BLAST PATTERN DESIGN
    # =========================================================================
    
    def create_pattern(
        self,
        site_id: str,
        burden: float,
        spacing: float,
        num_rows: int,
        num_holes_per_row: int,
        hole_depth_m: float,
        bench_name: Optional[str] = None,
        pattern_type: str = "rectangular",
        hole_diameter_mm: float = 165,
        subdrill_m: float = 0.5,
        stemming_height_m: float = 3.0,
        explosive_type: ExplosiveType = ExplosiveType.ANFO,
        origin_x: float = 0,
        origin_y: float = 0,
        origin_z: float = 0,
        orientation_degrees: float = 0,
        designed_by: Optional[str] = None
    ) -> BlastPattern:
        """Create a new blast pattern."""
        
        # Calculate powder factor
        powder_factor = self._calculate_powder_factor(
            burden, spacing, hole_depth_m, hole_diameter_mm,
            stemming_height_m, explosive_type
        )
        
        pattern = BlastPattern(
            site_id=site_id,
            bench_name=bench_name,
            pattern_type=pattern_type,
            burden=burden,
            spacing=spacing,
            num_rows=num_rows,
            num_holes_per_row=num_holes_per_row,
            hole_diameter_mm=hole_diameter_mm,
            hole_depth_m=hole_depth_m,
            subdrill_m=subdrill_m,
            stemming_height_m=stemming_height_m,
            explosive_type=explosive_type,
            powder_factor_kg_bcm=powder_factor,
            origin_x=origin_x,
            origin_y=origin_y,
            origin_z=origin_z,
            orientation_degrees=orientation_degrees,
            designed_by=designed_by
        )
        
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        
        # Generate drill holes
        self._generate_holes(pattern)
        
        return pattern
    
    def _generate_holes(self, pattern: BlastPattern) -> List[DrillHole]:
        """Generate drill holes for a pattern."""
        holes = []
        hole_number = 1
        
        # Pattern rotation
        rotation_rad = math.radians(pattern.orientation_degrees)
        cos_r = math.cos(rotation_rad)
        sin_r = math.sin(rotation_rad)
        
        for row in range(pattern.num_rows):
            for col in range(pattern.num_holes_per_row):
                # Calculate local position
                if pattern.pattern_type == "staggered" and row % 2 == 1:
                    local_x = col * pattern.spacing + pattern.spacing / 2
                else:
                    local_x = col * pattern.spacing
                
                local_y = row * pattern.burden
                
                # Apply rotation
                rotated_x = local_x * cos_r - local_y * sin_r
                rotated_y = local_x * sin_r + local_y * cos_r
                
                # Add origin offset
                design_x = pattern.origin_x + rotated_x
                design_y = pattern.origin_y + rotated_y
                
                hole = DrillHole(
                    pattern_id=pattern.pattern_id,
                    hole_number=hole_number,
                    row_number=row + 1,
                    hole_in_row=col + 1,
                    design_x=design_x,
                    design_y=design_y,
                    design_z=pattern.origin_z,
                    design_depth_m=pattern.hole_depth_m,
                    design_diameter_mm=pattern.hole_diameter_mm,
                    design_angle_degrees=90,  # Vertical
                    status=DrillHoleStatus.PLANNED
                )
                
                self.db.add(hole)
                holes.append(hole)
                hole_number += 1
        
        self.db.commit()
        return holes
    
    def _calculate_powder_factor(
        self,
        burden: float,
        spacing: float,
        hole_depth_m: float,
        hole_diameter_mm: float,
        stemming_height_m: float,
        explosive_type: ExplosiveType
    ) -> float:
        """Calculate powder factor in kg/BCM."""
        # Volume per hole (BCM)
        bench_height = hole_depth_m - 0.5  # Approximate bench height
        volume_per_hole = burden * spacing * bench_height
        
        # Charge column length
        charge_length = hole_depth_m - stemming_height_m
        if charge_length < 0:
            charge_length = 0
        
        # Hole radius in meters
        radius_m = (hole_diameter_mm / 1000) / 2
        
        # Charge volume
        charge_volume = math.pi * radius_m**2 * charge_length
        
        # Explosive density
        props = EXPLOSIVE_PROPERTIES.get(explosive_type, EXPLOSIVE_PROPERTIES[ExplosiveType.ANFO])
        density_kg_m3 = props['density'] * 1000
        
        # Charge weight
        charge_weight_kg = charge_volume * density_kg_m3
        
        # Powder factor
        if volume_per_hole > 0:
            return charge_weight_kg / volume_per_hole
        return 0
    
    def get_pattern(self, pattern_id: str) -> Optional[BlastPattern]:
        """Get pattern by ID."""
        return self.db.query(BlastPattern).filter(
            BlastPattern.pattern_id == pattern_id
        ).first()
    
    def list_patterns(
        self,
        site_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[BlastPattern]:
        """List patterns for site."""
        query = self.db.query(BlastPattern).filter(
            BlastPattern.site_id == site_id
        )
        
        if status:
            query = query.filter(BlastPattern.status == status)
        
        return query.order_by(BlastPattern.created_at.desc()).limit(limit).all()
    
    def approve_pattern(
        self,
        pattern_id: str,
        approved_by: str
    ) -> BlastPattern:
        """Approve a pattern for drilling."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        pattern.status = "approved"
        pattern.approved_by = approved_by
        pattern.approved_at = datetime.utcnow()
        
        self.db.commit()
        return pattern
    
    # =========================================================================
    # DRILL HOLE MANAGEMENT
    # =========================================================================
    
    def update_hole_actuals(
        self,
        hole_id: str,
        actual_x: float,
        actual_y: float,
        actual_z: float,
        actual_depth_m: float,
        drilled_by: Optional[str] = None,
        drill_rig_id: Optional[str] = None,
        penetration_rate: Optional[float] = None,
        water_present: bool = False,
        cavity_detected: bool = False,
        notes: Optional[str] = None
    ) -> DrillHole:
        """Update hole with actual drilled values."""
        hole = self.db.query(DrillHole).filter(
            DrillHole.hole_id == hole_id
        ).first()
        
        if not hole:
            raise ValueError(f"Hole {hole_id} not found")
        
        hole.actual_x = actual_x
        hole.actual_y = actual_y
        hole.actual_z = actual_z
        hole.actual_depth_m = actual_depth_m
        hole.drilled_at = datetime.utcnow()
        hole.drilled_by = drilled_by
        hole.drill_rig_id = drill_rig_id
        hole.penetration_rate_m_hr = penetration_rate
        hole.water_present = water_present
        hole.cavity_detected = cavity_detected
        hole.notes = notes
        hole.status = DrillHoleStatus.DRILLED
        
        self.db.commit()
        return hole
    
    def load_hole(
        self,
        hole_id: str,
        charge_weight_kg: float,
        explosive_type: ExplosiveType,
        detonator_delay_ms: int,
        stemming_height_m: float,
        loaded_by: Optional[str] = None,
        primer_type: Optional[str] = None,
        detonator_type: Optional[str] = None
    ) -> DrillHole:
        """Record hole loading."""
        hole = self.db.query(DrillHole).filter(
            DrillHole.hole_id == hole_id
        ).first()
        
        if not hole:
            raise ValueError(f"Hole {hole_id} not found")
        
        hole.charge_weight_kg = charge_weight_kg
        hole.explosive_type = explosive_type
        hole.detonator_delay_ms = detonator_delay_ms
        hole.stemming_height_m = stemming_height_m
        hole.loaded_at = datetime.utcnow()
        hole.loaded_by = loaded_by
        hole.primer_type = primer_type
        hole.detonator_type = detonator_type
        hole.status = DrillHoleStatus.LOADED
        
        self.db.commit()
        return hole
    
    def get_pattern_holes(self, pattern_id: str) -> List[DrillHole]:
        """Get all holes for a pattern."""
        return self.db.query(DrillHole).filter(
            DrillHole.pattern_id == pattern_id
        ).order_by(DrillHole.hole_number).all()
    
    # =========================================================================
    # FRAGMENTATION PREDICTION
    # =========================================================================
    
    def predict_fragmentation(
        self,
        pattern_id: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Predict fragmentation using Kuz-Ram model."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        # Get fragmentation model or use defaults
        model = None
        if model_id:
            model = self.db.query(FragmentationModel).filter(
                FragmentationModel.model_id == model_id
            ).first()
        
        rock_factor = model.rock_factor_a if model else 8
        uniformity = model.uniformity_index_n if model else 1.0
        
        # Kuz-Ram mean fragment size (X50)
        # X50 = A * (V0/Q)^0.8 * Q^0.167 * (E/115)^(-0.633)
        
        # Volume per hole
        bench_height = pattern.hole_depth_m - pattern.subdrill_m
        volume_per_hole = pattern.burden * pattern.spacing * bench_height
        
        # Charge per hole (approximate)
        charge_length = pattern.hole_depth_m - pattern.stemming_height_m
        radius_m = (pattern.hole_diameter_mm / 1000) / 2
        charge_volume = math.pi * radius_m**2 * charge_length
        
        props = EXPLOSIVE_PROPERTIES.get(
            pattern.explosive_type,
            EXPLOSIVE_PROPERTIES[ExplosiveType.ANFO]
        )
        charge_kg = charge_volume * props['density'] * 1000
        
        # Relative weight strength
        rws = props['rws']
        
        # Calculate X50 (mean fragment size in cm)
        if charge_kg > 0:
            x50 = rock_factor * (volume_per_hole / charge_kg)**0.8 * \
                  charge_kg**0.167 * (rws / 115)**(-0.633)
        else:
            x50 = 100  # Default large size
        
        # Rosin-Rammler distribution
        # P(x) = 1 - exp(-0.693 * (x/X50)^n)
        
        # Calculate size distribution
        sizes = [1, 2, 5, 10, 20, 30, 50, 75, 100, 150, 200]
        passing = []
        
        for size in sizes:
            p = 100 * (1 - math.exp(-0.693 * (size / x50)**uniformity))
            passing.append(round(p, 1))
        
        # Calculate oversize (typically > 1m)
        oversize_limit = 100  # cm
        oversize_percent = 100 - (1 - math.exp(-0.693 * (oversize_limit / x50)**uniformity)) * 100
        
        return {
            'pattern_id': pattern_id,
            'model_used': model.name if model else 'Default Kuz-Ram',
            'rock_factor': rock_factor,
            'uniformity_index': uniformity,
            'x50_cm': round(x50, 1),
            'size_distribution': {
                'sizes_cm': sizes,
                'passing_percent': passing
            },
            'oversize_percent': round(oversize_percent, 1),
            'powder_factor_kg_bcm': round(pattern.powder_factor_kg_bcm or 0, 3),
            'charge_per_hole_kg': round(charge_kg, 1)
        }
    
    # =========================================================================
    # BLAST EVENT MANAGEMENT
    # =========================================================================
    
    def create_blast_event(
        self,
        pattern_id: str,
        site_id: str,
        blast_date: datetime,
        blast_number: Optional[str] = None,
        shotfirer_name: Optional[str] = None,
        supervisor_name: Optional[str] = None,
        initiation_system: str = "electronic"
    ) -> BlastEvent:
        """Create a blast event."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        # Calculate totals from holes
        holes = self.get_pattern_holes(pattern_id)
        total_holes = len(holes)
        total_explosive = sum(h.charge_weight_kg or 0 for h in holes)
        
        # Calculate volume
        bench_height = pattern.hole_depth_m - pattern.subdrill_m
        total_volume = pattern.burden * pattern.spacing * bench_height * total_holes
        
        # Powder factor
        powder_factor = total_explosive / total_volume if total_volume > 0 else 0
        
        # Get maximum delay
        max_delay = max((h.detonator_delay_ms or 0) for h in holes) if holes else 0
        
        event = BlastEvent(
            pattern_id=pattern_id,
            site_id=site_id,
            blast_number=blast_number,
            blast_date=blast_date,
            total_holes=total_holes,
            total_explosive_kg=total_explosive,
            total_volume_bcm=total_volume,
            powder_factor_kg_bcm=powder_factor,
            initiation_system=initiation_system,
            total_delay_ms=max_delay,
            shotfirer_name=shotfirer_name,
            supervisor_name=supervisor_name,
            status="planned"
        )
        
        self.db.add(event)
        
        # Update pattern status
        pattern.status = "loaded"
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def record_blast_results(
        self,
        event_id: str,
        actual_fire_time: datetime,
        all_clear_time: Optional[datetime] = None,
        max_ppv_mm_s: Optional[float] = None,
        max_overpressure_db: Optional[float] = None,
        avg_fragment_size_cm: Optional[float] = None,
        oversize_percent: Optional[float] = None,
        misfires: int = 0,
        flyrock_incident: bool = False,
        flyrock_details: Optional[str] = None,
        notes: Optional[str] = None
    ) -> BlastEvent:
        """Record blast results after firing."""
        event = self.db.query(BlastEvent).filter(
            BlastEvent.event_id == event_id
        ).first()
        
        if not event:
            raise ValueError(f"Blast event {event_id} not found")
        
        event.actual_fire_time = actual_fire_time
        event.all_clear_time = all_clear_time
        event.max_ppv_mm_s = max_ppv_mm_s
        event.max_overpressure_db = max_overpressure_db
        event.avg_fragment_size_cm = avg_fragment_size_cm
        event.oversize_percent = oversize_percent
        event.misfires = misfires
        event.flyrock_incident = flyrock_incident
        event.flyrock_details = flyrock_details
        event.notes = notes
        event.status = "incident" if flyrock_incident or misfires > 0 else "completed"
        
        # Determine fragmentation rating
        if avg_fragment_size_cm:
            if avg_fragment_size_cm < 30 and (oversize_percent or 0) < 5:
                event.fragmentation_rating = "good"
            elif avg_fragment_size_cm < 50 and (oversize_percent or 0) < 15:
                event.fragmentation_rating = "acceptable"
            else:
                event.fragmentation_rating = "poor"
        
        # Update holes status
        holes = self.get_pattern_holes(event.pattern_id)
        for hole in holes:
            hole.status = DrillHoleStatus.DETONATED
        
        # Update pattern status
        pattern = self.get_pattern(event.pattern_id)
        if pattern:
            pattern.status = "fired"
        
        self.db.commit()
        return event
    
    def generate_drill_log(self, pattern_id: str) -> Dict[str, Any]:
        """Generate drill log report for a pattern."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")
        
        holes = self.get_pattern_holes(pattern_id)
        
        return {
            'pattern_id': pattern_id,
            'bench': pattern.bench_name,
            'pattern_type': pattern.pattern_type,
            'burden': pattern.burden,
            'spacing': pattern.spacing,
            'hole_diameter': pattern.hole_diameter_mm,
            'design_depth': pattern.hole_depth_m,
            'total_holes': len(holes),
            'status': pattern.status,
            'holes': [
                {
                    'number': h.hole_number,
                    'row': h.row_number,
                    'design_x': round(h.design_x, 2),
                    'design_y': round(h.design_y, 2),
                    'actual_x': round(h.actual_x, 2) if h.actual_x else None,
                    'actual_y': round(h.actual_y, 2) if h.actual_y else None,
                    'design_depth': h.design_depth_m,
                    'actual_depth': h.actual_depth_m,
                    'status': h.status.value if h.status else None,
                    'water': h.water_present,
                    'cavity': h.cavity_detected
                }
                for h in holes
            ]
        }


def get_drill_blast_service(db: Session) -> DrillBlastService:
    """Factory function for drill blast service."""
    return DrillBlastService(db)
