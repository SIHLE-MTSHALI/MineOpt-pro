"""
Block Model Router - Phase 3 Block Model API

REST API endpoints for block model management:
- POST /blockmodels - Create a block model
- GET /blockmodels/{site_id} - List block models
- POST /blockmodels/{model_id}/estimate - Run grade estimation
- GET /blockmodels/{model_id}/blocks - Get blocks for visualization
- DELETE /blockmodels/{model_id} - Delete block model
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.block_model_service import (
    get_block_model_service, 
    BlockModelConfig,
    EstimationConfig,
    BlockModelResult
)
from ..services.kriging_service import VariogramModel
from ..domain.models_block_model import BlockModelDefinition, Block, BlockModelRun


router = APIRouter(prefix="/blockmodels", tags=["Block Models"])


# Request/Response Models

class CreateBlockModelRequest(BaseModel):
    """Request to create a block model."""
    site_id: str
    name: str
    collar_ids: Optional[List[str]] = None
    origin_x: Optional[float] = None
    origin_y: Optional[float] = None
    origin_z: Optional[float] = None
    block_size_x: float = Field(default=10.0, ge=1.0)
    block_size_y: float = Field(default=10.0, ge=1.0)
    block_size_z: float = Field(default=5.0, ge=0.5)
    count_x: Optional[int] = None
    count_y: Optional[int] = None
    count_z: Optional[int] = None
    description: str = ""


class EstimateGradesRequest(BaseModel):
    """Request to estimate grades."""
    collar_ids: List[str]
    quality_field: str
    method: str = "kriging"  # kriging or idw
    variogram_model: str = "spherical"
    auto_fit_variogram: bool = True
    max_samples: int = 20
    min_samples: int = 3
    search_radius: Optional[float] = None
    idw_power: float = 2.0
    run_cross_validation: bool = True


class BlockModelSummary(BaseModel):
    """Summary of a block model."""
    model_id: str
    name: str
    status: str
    block_count: int
    block_size: Dict[str, float]
    extent: Dict[str, float]
    latest_run: Optional[Dict[str, Any]]


class BlockVisualizationData(BaseModel):
    """Block data for visualization."""
    block_id: str
    i: int
    j: int
    k: int
    x: float
    y: float
    z: float
    value: Optional[float]
    variance: Optional[float]
    material_type_id: Optional[str]
    is_mineable: bool


class EstimationResultResponse(BaseModel):
    """Response from grade estimation."""
    success: bool
    model_id: str
    run_id: Optional[str]
    blocks_estimated: int
    variogram: Optional[Dict[str, Any]]
    cv_rmse: Optional[float]
    errors: List[str]
    warnings: List[str]


# Endpoints

@router.post("", response_model=Dict[str, Any])
async def create_block_model(
    request: CreateBlockModelRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new block model.
    
    If collar_ids are provided, the grid extent will be auto-calculated
    from the borehole locations.
    """
    service = get_block_model_service(db)
    
    config = BlockModelConfig(
        name=request.name,
        site_id=request.site_id,
        origin_x=request.origin_x,
        origin_y=request.origin_y,
        origin_z=request.origin_z,
        block_size_x=request.block_size_x,
        block_size_y=request.block_size_y,
        block_size_z=request.block_size_z,
        count_x=request.count_x,
        count_y=request.count_y,
        count_z=request.count_z,
        description=request.description
    )
    
    result = service.create_block_model(config, request.collar_ids)
    
    if not result.success:
        raise HTTPException(400, result.errors[0] if result.errors else "Creation failed")
    
    return {
        "success": True,
        "model_id": result.model_id,
        "blocks_created": result.blocks_created
    }


@router.get("/site/{site_id}", response_model=List[BlockModelSummary])
async def list_block_models(
    site_id: str,
    db: Session = Depends(get_db)
):
    """List all block models for a site."""
    models = db.query(BlockModelDefinition).filter(
        BlockModelDefinition.site_id == site_id
    ).order_by(BlockModelDefinition.created_at.desc()).all()
    
    result = []
    for model in models:
        # Get block count
        block_count = db.query(Block).filter(Block.model_id == model.model_id).count()
        
        # Get latest run
        latest_run = db.query(BlockModelRun).filter(
            BlockModelRun.model_id == model.model_id
        ).order_by(BlockModelRun.created_at.desc()).first()
        
        result.append(BlockModelSummary(
            model_id=model.model_id,
            name=model.name,
            status=model.status,
            block_count=block_count,
            block_size={
                "x": model.block_size_x,
                "y": model.block_size_y,
                "z": model.block_size_z
            },
            extent={
                "x": model.extent_x,
                "y": model.extent_y,
                "z": model.extent_z
            },
            latest_run={
                "run_id": latest_run.run_id,
                "quality_field": latest_run.quality_field,
                "method": latest_run.method,
                "cv_rmse": latest_run.cv_rmse,
                "completed_at": latest_run.completed_at.isoformat() if latest_run.completed_at else None
            } if latest_run else None
        ))
    
    return result


@router.get("/{model_id}")
async def get_block_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Get block model details."""
    model = db.query(BlockModelDefinition).filter(
        BlockModelDefinition.model_id == model_id
    ).first()
    
    if not model:
        raise HTTPException(404, "Block model not found")
    
    block_count = db.query(Block).filter(Block.model_id == model_id).count()
    
    runs = db.query(BlockModelRun).filter(
        BlockModelRun.model_id == model_id
    ).order_by(BlockModelRun.created_at.desc()).all()
    
    return {
        "model_id": model.model_id,
        "name": model.name,
        "description": model.description,
        "status": model.status,
        "origin": {"x": model.origin_x, "y": model.origin_y, "z": model.origin_z},
        "block_size": {"x": model.block_size_x, "y": model.block_size_y, "z": model.block_size_z},
        "grid_size": {"x": model.count_x, "y": model.count_y, "z": model.count_z},
        "extent": {"x": model.extent_x, "y": model.extent_y, "z": model.extent_z},
        "block_count": block_count,
        "runs": [
            {
                "run_id": r.run_id,
                "quality_field": r.quality_field,
                "method": r.method,
                "variogram_model": r.variogram_model,
                "mean_value": r.mean_value,
                "cv_rmse": r.cv_rmse,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in runs
        ],
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat() if model.updated_at else None
    }


@router.post("/{model_id}/estimate", response_model=EstimationResultResponse)
async def estimate_grades(
    model_id: str,
    request: EstimateGradesRequest,
    db: Session = Depends(get_db)
):
    """
    Estimate grades for all blocks using kriging or IDW.
    """
    service = get_block_model_service(db)
    
    # Map string to enum
    variogram_model_map = {
        "spherical": VariogramModel.SPHERICAL,
        "exponential": VariogramModel.EXPONENTIAL,
        "gaussian": VariogramModel.GAUSSIAN,
        "linear": VariogramModel.LINEAR
    }
    
    config = EstimationConfig(
        quality_field=request.quality_field,
        method=request.method,
        variogram_model=variogram_model_map.get(request.variogram_model, VariogramModel.SPHERICAL),
        auto_fit_variogram=request.auto_fit_variogram,
        max_samples=request.max_samples,
        min_samples=request.min_samples,
        search_radius=request.search_radius,
        idw_power=request.idw_power,
        run_cross_validation=request.run_cross_validation
    )
    
    result = service.estimate_grades(model_id, request.collar_ids, config)
    
    return EstimationResultResponse(
        success=result.success,
        model_id=model_id,
        run_id=result.run_id,
        blocks_estimated=result.blocks_estimated,
        variogram={
            "model": result.variogram_params.model.value,
            "nugget": result.variogram_params.nugget,
            "sill": result.variogram_params.sill,
            "range": result.variogram_params.range,
            "r_squared": result.variogram_params.r_squared
        } if result.variogram_params else None,
        cv_rmse=result.cv_rmse,
        errors=result.errors,
        warnings=result.warnings
    )


@router.get("/{model_id}/blocks", response_model=List[BlockVisualizationData])
async def get_blocks_for_visualization(
    model_id: str,
    quality_field: Optional[str] = Query(None),
    k_level: Optional[int] = Query(None, description="Filter to specific Z level"),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get block data formatted for 3D visualization.
    """
    service = get_block_model_service(db)
    blocks = service.get_blocks_for_visualization(model_id, quality_field, k_level)
    
    # Apply value filter
    if min_value is not None:
        blocks = [b for b in blocks if b.get("value") is not None and b["value"] >= min_value]
    if max_value is not None:
        blocks = [b for b in blocks if b.get("value") is not None and b["value"] <= max_value]
    
    return [
        BlockVisualizationData(**b) for b in blocks
    ]


@router.post("/{model_id}/activity-areas")
async def create_activity_areas(
    model_id: str,
    min_value: float = Query(..., description="Minimum quality value"),
    max_value: Optional[float] = Query(None),
    activity_type: str = Query("Coal Mining"),
    seam_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Create activity areas from blocks meeting quality criteria.
    """
    service = get_block_model_service(db)
    
    area_ids = service.create_activity_areas_from_blocks(
        model_id=model_id,
        min_value=min_value,
        max_value=max_value,
        activity_type=activity_type,
        seam_name=seam_name
    )
    
    return {
        "success": True,
        "activity_area_ids": area_ids,
        "count": len(area_ids)
    }


@router.delete("/{model_id}")
async def delete_block_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """Delete a block model and all related data."""
    model = db.query(BlockModelDefinition).filter(
        BlockModelDefinition.model_id == model_id
    ).first()
    
    if not model:
        raise HTTPException(404, "Block model not found")
    
    db.delete(model)  # Cascade deletes blocks and runs
    db.commit()
    
    return {"message": f"Block model {model.name} deleted"}
