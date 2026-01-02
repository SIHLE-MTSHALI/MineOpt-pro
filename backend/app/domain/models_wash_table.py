"""
Wash Table Entities - Section 3.13 of Enterprise Specification

Wash tables model the behavior of coal preparation plants (CHPP).
They map relative density (RD) cutpoints to:
- Cumulative yield fractions
- Product quality vectors
- Reject quality vectors

The system uses these tables to simulate wash plant performance
and optimize cutpoint selection for product quality targets.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime


class WashTable(Base):
    """
    A washability table for a specific coal source or blend.
    Contains rows mapping RD cutpoints to yields and qualities.
    """
    __tablename__ = "wash_tables"

    wash_table_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Source reference (optional - links to seam, block, or sample source)
    source_reference = Column(String, nullable=True)
    
    # Basis assumptions for the table data
    # Example: {"quantity_basis": "tonnes", "quality_basis": "ADB", "moisture_basis": "air_dried"}
    basis_assumptions = Column(JSON, default=dict)
    
    # Table format metadata
    # "cumulative" = rows show cumulative yield up to cutpoint
    # "incremental" = rows show yield in the density band
    table_format = Column(String, default="cumulative")
    
    # Validity period (optional)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("Site")
    rows = relationship("WashTableRow", back_populates="wash_table", order_by="WashTableRow.rd_cutpoint")

    def __repr__(self):
        return f"<WashTable {self.name}>"

    def get_yield_at_rd(self, rd_cutpoint: float) -> tuple:
        """
        Interpolate to get yield and qualities at a given RD cutpoint.
        Returns: (yield_fraction, product_quality_dict, reject_quality_dict)
        """
        if not self.rows:
            return (0.0, {}, {})
        
        sorted_rows = sorted(self.rows, key=lambda r: r.rd_cutpoint)
        
        # Find bounding rows for interpolation
        lower_row = None
        upper_row = None
        
        for row in sorted_rows:
            if row.rd_cutpoint <= rd_cutpoint:
                lower_row = row
            elif upper_row is None:
                upper_row = row
                break
        
        # Exact match or extrapolation
        if lower_row and lower_row.rd_cutpoint == rd_cutpoint:
            return (
                lower_row.cumulative_yield_fraction,
                lower_row.product_quality_vector or {},
                lower_row.reject_quality_vector or {}
            )
        
        # Below minimum RD
        if lower_row is None:
            first_row = sorted_rows[0]
            return (
                first_row.cumulative_yield_fraction,
                first_row.product_quality_vector or {},
                first_row.reject_quality_vector or {}
            )
        
        # Above maximum RD
        if upper_row is None:
            return (
                lower_row.cumulative_yield_fraction,
                lower_row.product_quality_vector or {},
                lower_row.reject_quality_vector or {}
            )
        
        # Linear interpolation
        rd_range = upper_row.rd_cutpoint - lower_row.rd_cutpoint
        if rd_range == 0:
            factor = 0.5
        else:
            factor = (rd_cutpoint - lower_row.rd_cutpoint) / rd_range
        
        # Interpolate yield
        yield_interp = lower_row.cumulative_yield_fraction + factor * (
            upper_row.cumulative_yield_fraction - lower_row.cumulative_yield_fraction
        )
        
        # Interpolate product quality
        product_quality = {}
        lower_pq = lower_row.product_quality_vector or {}
        upper_pq = upper_row.product_quality_vector or {}
        all_keys = set(lower_pq.keys()) | set(upper_pq.keys())
        for key in all_keys:
            lower_val = lower_pq.get(key, 0)
            upper_val = upper_pq.get(key, 0)
            product_quality[key] = lower_val + factor * (upper_val - lower_val)
        
        # Interpolate reject quality
        reject_quality = {}
        lower_rq = lower_row.reject_quality_vector or {}
        upper_rq = upper_row.reject_quality_vector or {}
        all_keys = set(lower_rq.keys()) | set(upper_rq.keys())
        for key in all_keys:
            lower_val = lower_rq.get(key, 0)
            upper_val = upper_rq.get(key, 0)
            reject_quality[key] = lower_val + factor * (upper_val - lower_val)
        
        return (yield_interp, product_quality, reject_quality)


class WashTableRow(Base):
    """
    A single row in a wash table representing yield and quality at a cutpoint.
    """
    __tablename__ = "wash_table_rows"

    row_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wash_table_id = Column(String, ForeignKey("wash_tables.wash_table_id"), nullable=False)
    
    # The relative density cutpoint (e.g., 1.30, 1.40, 1.50, 1.60)
    rd_cutpoint = Column(Float, nullable=False)
    
    # Cumulative yield fraction at this cutpoint (0.0 to 1.0)
    # For cumulative tables: yield of floats at this RD
    cumulative_yield_fraction = Column(Float, nullable=False)
    
    # Product quality vector at this cutpoint
    # Example: {"Ash_ADB": 8.5, "CV_ARB": 28.0, "VM_ADB": 25.0}
    product_quality_vector = Column(JSON, nullable=False, default=dict)
    
    # Reject quality vector at this cutpoint (optional, can be derived)
    reject_quality_vector = Column(JSON, nullable=True)
    
    # Row ordering (for display and iteration)
    sequence = Column(Integer, nullable=True)
    
    # Notes for this row (e.g., "Lab Sample 2024-01-15")
    notes = Column(String, nullable=True)
    
    # Relationships
    wash_table = relationship("WashTable", back_populates="rows")

    def __repr__(self):
        return f"<WashTableRow RD={self.rd_cutpoint} Yield={self.cumulative_yield_fraction:.1%}>"


class WashPlantOperatingPoint(Base):
    """
    Records actual or planned wash plant operating conditions for a period.
    Links wash table data to scheduling results.
    """
    __tablename__ = "wash_plant_operating_points"

    operating_point_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    schedule_version_id = Column(String, ForeignKey("schedule_versions.version_id"), nullable=False)
    period_id = Column(String, ForeignKey("periods.period_id"), nullable=False)
    plant_node_id = Column(String, ForeignKey("flow_nodes.node_id"), nullable=False)
    
    # Operating parameters
    selected_rd_cutpoint = Column(Float, nullable=False)
    wash_table_id = Column(String, ForeignKey("wash_tables.wash_table_id"), nullable=True)
    
    # Feed characteristics
    feed_tonnes = Column(Float, nullable=False)
    feed_quality_vector = Column(JSON, default=dict)
    
    # Achieved results
    product_tonnes = Column(Float, nullable=False)
    product_quality_vector = Column(JSON, default=dict)
    reject_tonnes = Column(Float, nullable=False)
    reject_quality_vector = Column(JSON, nullable=True)
    
    # Yield achieved
    yield_fraction = Column(Float, nullable=False)
    
    # Selection mode used
    cutpoint_selection_mode = Column(String, default="FixedRD")  # FixedRD, TargetQuality, OptimizerSelected
    
    # Explanation of cutpoint choice (if optimizer selected)
    selection_rationale = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
