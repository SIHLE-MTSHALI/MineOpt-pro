from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine, Base
from ..domain import models_core, models_time, models_resource, models_flow
# from ..schemas import site_schemas
from ..services import seed_service

# Create Tables (Enterprise Schema)
models_core.Base.metadata.create_all(bind=engine)
models_time.Base.metadata.create_all(bind=engine)
models_resource.Base.metadata.create_all(bind=engine)
models_flow.Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.post("/seed-demo-data")
def seed_data(db: Session = Depends(get_db)):
    site_id = seed_service.seed_enterprise_data(db)
    return {"message": "Enterprise Demo data seeded", "site_id": site_id}

@router.get("/sites")
def get_sites(db: Session = Depends(get_db)):
    return db.query(models_core.Site).all()

@router.get("/resources")
def get_resources(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resource.Resource)
    if site_id:
        query = query.filter(models_resource.Resource.site_id == site_id)
    return query.all()

@router.get("/activity-areas")
def get_activity_areas(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resource.ActivityArea)
    if site_id:
        query = query.filter(models_resource.ActivityArea.site_id == site_id)
    return query.all()

@router.get("/network-nodes")
def get_network_nodes(site_id: str = None, db: Session = Depends(get_db)):
    # Join Network to filter by Site
    query = db.query(models_flow.FlowNode).join(models_flow.FlowNetwork)
    if site_id:
        query = query.filter(models_flow.FlowNetwork.site_id == site_id)
    
    # Eager load configs
    # We rely on lazy loading default or simple JSON serialization
    return query.all()
