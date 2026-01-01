from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.optimization_service import optimizer
from pydantic import BaseModel

router = APIRouter(prefix="/optimization", tags=["Optimization"])

class OptimizationRequest(BaseModel):
    site_id: str
    schedule_version_id: str

@router.post("/run")
def run_optimization(request: OptimizationRequest, db: Session = Depends(get_db)):
    result = optimizer.run_greedy(db, request.site_id, request.schedule_version_id)
    return result
