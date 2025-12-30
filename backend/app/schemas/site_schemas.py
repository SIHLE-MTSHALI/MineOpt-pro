from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SiteCreate(BaseModel):
    name: str
    time_zone: str = "UTC"
    unit_system: str = "metric"

class SiteResponse(SiteCreate):
    site_id: str
    class Config:
        from_attributes = True

class MaterialTypeCreate(BaseModel):
    name: str
    category: str
    default_density: float

class FlowNodeCreate(BaseModel):
    name: str
    node_type: str
    capacity_tonnes: Optional[float] = None

class FlowArcCreate(BaseModel):
    from_node_id: str
    to_node_id: str
    allowed_material_type_ids: List[str] = []

class FullSiteConfig(BaseModel):
    site: SiteCreate
    materials: List[MaterialTypeCreate]
    nodes: List[FlowNodeCreate] = []
    arcs: List[FlowArcCreate] = []
