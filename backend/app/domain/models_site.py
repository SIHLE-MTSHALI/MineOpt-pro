from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base

class Site(Base):
    __tablename__ = "sites"
    
    site_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    time_zone = Column(String, default="UTC")
    unit_system = Column(String, default="metric")
    default_quality_basis_preferences = Column(JSON, default={}) # e.g. {"CV": "ARB"}
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    material_types = relationship("MaterialType", back_populates="site")
    quality_fields = relationship("QualityField", back_populates="site")
    resources = relationship("Resource", back_populates="site")
    activities = relationship("Activity", back_populates="site")
    flow_networks = relationship("FlowNetwork", back_populates="site")


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    site_access = Column(JSON, default=[]) # List of site_ids
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Roles would be a Many-to-Many, simplifying for v1 to JSON list of role names
    roles = Column(JSON, default=[]) 
