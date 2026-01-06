"""
Block Model Domain Models - Phase 3 Block Model with Kriging

SQLAlchemy models for 3D block model management:
- BlockModelDefinition: Grid configuration and metadata
- Block: Individual block with estimated grades
- BlockModelRun: Estimation run history

Block models represent the discretized ore body used for
mine planning and scheduling.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
from datetime import datetime


class BlockModelDefinition(Base):
    """
    Definition of a block model grid.
    
    Specifies the origin, block dimensions, and extent of the model.
    Multiple estimation runs can be performed on the same definition.
    """
    __tablename__ = "block_model_definitions"
    
    model_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    # Identification
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Grid origin (lower-left-bottom corner)
    origin_x = Column(Float, nullable=False)  # Easting
    origin_y = Column(Float, nullable=False)  # Northing
    origin_z = Column(Float, nullable=False)  # Elevation
    
    # Block dimensions
    block_size_x = Column(Float, nullable=False, default=10.0)  # Width (E-W)
    block_size_y = Column(Float, nullable=False, default=10.0)  # Length (N-S)
    block_size_z = Column(Float, nullable=False, default=5.0)   # Height (vertical)
    
    # Grid extent (number of blocks)
    count_x = Column(Integer, nullable=False, default=10)
    count_y = Column(Integer, nullable=False, default=10)
    count_z = Column(Integer, nullable=False, default=5)
    
    # Rotation (optional, for angled grids)
    rotation = Column(Float, default=0.0)  # Degrees from north
    
    # Coordinate system
    coordinate_system = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="Draft")  # Draft, Estimated, Active, Archived
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("Site")
    blocks = relationship("Block", back_populates="model", cascade="all, delete-orphan")
    runs = relationship("BlockModelRun", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BlockModelDefinition {self.name}>"
    
    @property
    def total_blocks(self) -> int:
        """Total number of blocks in the model."""
        return self.count_x * self.count_y * self.count_z
    
    @property
    def extent_x(self) -> float:
        """Total extent in X direction."""
        return self.count_x * self.block_size_x
    
    @property
    def extent_y(self) -> float:
        """Total extent in Y direction."""
        return self.count_y * self.block_size_y
    
    @property
    def extent_z(self) -> float:
        """Total extent in Z direction."""
        return self.count_z * self.block_size_z
    
    def get_block_centroid(self, i: int, j: int, k: int) -> tuple:
        """Get the centroid coordinates of a block at indices (i, j, k)."""
        cx = self.origin_x + (i + 0.5) * self.block_size_x
        cy = self.origin_y + (j + 0.5) * self.block_size_y
        cz = self.origin_z + (k + 0.5) * self.block_size_z
        return (cx, cy, cz)


class Block(Base):
    """
    An individual block in the block model.
    
    Stores estimated grades and classification for a single block.
    Blocks are identified by their (i, j, k) indices within the model.
    """
    __tablename__ = "blocks"
    
    block_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("block_model_definitions.model_id"), nullable=False)
    
    # Block indices (position in grid)
    i = Column(Integer, nullable=False)  # X index (0 to count_x - 1)
    j = Column(Integer, nullable=False)  # Y index (0 to count_y - 1)
    k = Column(Integer, nullable=False)  # Z index (0 to count_z - 1)
    
    # Centroid coordinates (denormalized for query performance)
    centroid_x = Column(Float, nullable=False)
    centroid_y = Column(Float, nullable=False)
    centroid_z = Column(Float, nullable=False)
    
    # Material classification
    material_type_id = Column(String, ForeignKey("material_types.material_type_id"), nullable=True)
    rock_code = Column(String, nullable=True)  # Lithology code
    
    # Estimated quality values (stored as JSON)
    quality_vector = Column(JSON, nullable=True)
    # Example: {"CV_ARB": 24.5, "Ash_ADB": 12.0, "TS_ARB": 0.45}
    
    # Primary quality value (for filtering/visualization)
    primary_value = Column(Float, nullable=True)
    primary_field = Column(String, nullable=True)  # Which field is primary
    
    # Estimation metadata
    estimation_method = Column(String, nullable=True)  # kriging, idw
    estimation_variance = Column(Float, nullable=True)  # Kriging variance
    num_samples = Column(Integer, nullable=True)  # Samples used
    
    # Volume and tonnage
    volume_bcm = Column(Float, nullable=True)  # Bank Cubic Metres
    density = Column(Float, nullable=True)  # t/bcm
    tonnes = Column(Float, nullable=True)  # Calculated tonnage
    
    # Mining status
    is_mineable = Column(Boolean, default=True)
    is_mined = Column(Boolean, default=False)
    linked_activity_area_id = Column(String, ForeignKey("activity_areas.area_id"), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    model = relationship("BlockModelDefinition", back_populates="blocks")
    material_type = relationship("MaterialType")
    
    def __repr__(self):
        return f"<Block ({self.i},{self.j},{self.k})>"
    
    def get_quality(self, field_name: str, default: float = 0.0) -> float:
        """Get a quality value from the vector."""
        if self.quality_vector:
            return self.quality_vector.get(field_name, default)
        return default
    
    @property
    def indices(self) -> tuple:
        """Block indices as a tuple."""
        return (self.i, self.j, self.k)


class BlockModelRun(Base):
    """
    Record of an estimation run on a block model.
    
    Tracks parameters and results of kriging/IDW estimation runs.
    Enables comparison of different estimation approaches.
    """
    __tablename__ = "block_model_runs"
    
    run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("block_model_definitions.model_id"), nullable=False)
    
    # Run identification
    run_name = Column(String, nullable=True)
    run_number = Column(Integer, nullable=False, default=1)
    
    # Quality field being estimated
    quality_field = Column(String, nullable=False)
    
    # Estimation method
    method = Column(String, nullable=False)  # kriging, idw
    
    # Variogram parameters (for kriging)
    variogram_model = Column(String, nullable=True)  # spherical, exponential, gaussian
    variogram_nugget = Column(Float, nullable=True)
    variogram_sill = Column(Float, nullable=True)
    variogram_range = Column(Float, nullable=True)
    variogram_r_squared = Column(Float, nullable=True)
    
    # Search parameters
    max_samples = Column(Integer, default=20)
    min_samples = Column(Integer, default=3)
    search_radius = Column(Float, nullable=True)
    
    # IDW parameters
    idw_power = Column(Float, default=2.0)
    
    # Results summary
    blocks_estimated = Column(Integer, default=0)
    mean_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    
    # Cross-validation results
    cv_rmse = Column(Float, nullable=True)
    cv_r_squared = Column(Float, nullable=True)
    
    # Source data
    num_samples_used = Column(Integer, nullable=True)
    sample_source = Column(String, nullable=True)  # "boreholes", "composites"
    
    # Status
    status = Column(String, default="Completed")  # Running, Completed, Failed
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    
    # Relationships
    model = relationship("BlockModelDefinition", back_populates="runs")
    
    def __repr__(self):
        return f"<BlockModelRun {self.run_name or self.run_id[:8]}>"
