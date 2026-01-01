from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from ..database import Base
import uuid
import datetime

# 3.1 Users, Roles, Permissions (Associations)
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', String, ForeignKey('users.user_id')),
    Column('role_id', String, ForeignKey('roles.role_id'))
)

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String, unique=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login_at = Column(DateTime)
    
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False) # Admin, Planner, Viewer
    permissions = Column(JSON) # List of strings ["SITE_CONFIG_EDIT", ...]
    
    users = relationship("User", secondary=user_roles, back_populates="roles")

# 3.2 Site
class Site(Base):
    __tablename__ = "sites"
    site_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    time_zone = Column(String, default="UTC")
    unit_system = Column(String, default="Metric")
    default_quality_basis_preferences = Column(JSON) # e.g. {"CV": "ARB"}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    material_types = relationship("MaterialType", back_populates="site")
    quality_fields = relationship("QualityField", back_populates="site")
    resources = relationship("Resource", back_populates="site")
    activities = relationship("Activity", back_populates="site")
