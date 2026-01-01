from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine, Base
from ..domain import models_site, models_config, models_flow, models_resources, models_scheduling, models_calendar
from ..schemas import site_schemas
from ..services import seed_service

# Create Tables
models_site.Base.metadata.create_all(bind=engine)
models_config.Base.metadata.create_all(bind=engine)
models_flow.Base.metadata.create_all(bind=engine)
models_resources.Base.metadata.create_all(bind=engine)
models_scheduling.Base.metadata.create_all(bind=engine)
models_calendar.Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.post("/site", response_model=site_schemas.SiteResponse)
def create_site(site: site_schemas.SiteCreate, db: Session = Depends(get_db)):
    db_site = models_site.Site(**site.dict())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

@router.post("/seed-demo-data")
def seed_data(db: Session = Depends(get_db)):
    site_id = seed_service.seed_test_data(db)
    return {"message": "Demo data seeded", "site_id": site_id}

@router.get("/sites")
def get_sites(db: Session = Depends(get_db)):
    return db.query(models_site.Site).all()

@router.get("/resources")
def get_resources(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resources.Resource)
    if site_id:
        query = query.filter(models_resources.Resource.site_id == site_id)
    return query.all()

@router.get("/activity-areas")
def get_activity_areas(site_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models_resources.ActivityArea)
    if site_id:
        query = query.filter(models_resources.ActivityArea.site_id == site_id)
    return query.all()
