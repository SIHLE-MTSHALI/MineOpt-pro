from sqlalchemy import Column, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
import uuid
from ..database import Base

class MaterialType(Base):
    __tablename__ = "material_types"

    material_type_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False)
    category = Column(String) # ROM, Waste, Reject, Product
    default_density = Column(Float)
    moisture_basis_for_quantity = Column(String, default="as-mined")
    reporting_group = Column(String) # Coal, Waste

    site = relationship("Site", back_populates="material_types")


class QualityField(Base):
    __tablename__ = "quality_fields"

    quality_field_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    site_id = Column(String, ForeignKey("sites.site_id"))
    name = Column(String, nullable=False) # CV, ASH
    description = Column(String)
    units = Column(String) # %, MJ/kg
    basis = Column(String) # ARB, ADB, DAF
    aggregation_rule = Column(String, default="WeightedAverage")
    missing_data_policy = Column(String, default="Error") 
    
    # Penalty Configuration
    constraint_direction_default = Column(String) # Max, Min, Target
    penalty_function_type = Column(String, default="Linear")
    penalty_parameters = Column(JSON, default={}) # {slope: 10, offset: 0}

    site = relationship("Site", back_populates="quality_fields")
