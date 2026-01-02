"""
Parcel Entity - Section 3.9 of Enterprise Specification

Parcels represent discrete units of material for simulation and tracking.
They can originate from:
- Block model queries (ActivityArea slices)
- Stockpile inventory splits
- External imports (reconciliation data)

Each parcel carries quantity, quality, and optional uncertainty parameters.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime


class Parcel(Base):
    """
    A discrete unit of material with defined quantity and quality.
    Used for material flow simulation and blending calculations.
    """
    __tablename__ = "parcels"

    parcel_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Source reference - identifies where this parcel came from
    # Format: "area:{area_id}:slice:{slice_index}" or "stockpile:{node_id}" or "import:{ref}"
    source_reference = Column(String, nullable=False)
    
    # When this parcel becomes available for scheduling (optional)
    period_available_from = Column(String, ForeignKey("periods.period_id"), nullable=True)
    
    # Quantity metrics
    quantity_tonnes = Column(Float, nullable=False)
    quantity_bcm = Column(Float, nullable=True)  # Bank Cubic Metres (optional)
    
    # Material classification
    material_type_id = Column(String, ForeignKey("material_types.material_type_id"), nullable=False)
    
    # Quality vector - dictionary of quality field names to values
    # Example: {"CV_ARB": 24.5, "Ash_ADB": 12.0, "TS_ARB": 0.5}
    quality_vector = Column(JSON, nullable=False, default=dict)
    
    # Reference to washability curve data (if available)
    washability_reference_id = Column(String, nullable=True)
    
    # Uncertainty parameters for Monte Carlo simulation (optional)
    # Example: {"CV_ARB": {"mean": 24.5, "std_dev": 1.2, "distribution": "normal"}}
    uncertainty_parameters = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String, default="Available")  # Available, Committed, Processed, Depleted
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    site = relationship("Site")
    material_type = relationship("MaterialType")

    def __repr__(self):
        return f"<Parcel {self.parcel_id[:8]}... {self.quantity_tonnes}t>"

    def get_quality(self, field_name: str, default: float = 0.0) -> float:
        """Get a quality value from the vector with a default."""
        if self.quality_vector:
            return self.quality_vector.get(field_name, default)
        return default


class ParcelMovement(Base):
    """
    Tracks the movement of a parcel through the flow network.
    Creates an audit trail of material flow.
    """
    __tablename__ = "parcel_movements"

    movement_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id = Column(String, ForeignKey("parcels.parcel_id"), nullable=False)
    
    # Flow path
    from_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=True)
    to_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    
    # Scheduling context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=True)
    
    # Quantity moved (may be partial if parcel is split)
    quantity_tonnes = Column(Float, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    parcel = relationship("Parcel")
