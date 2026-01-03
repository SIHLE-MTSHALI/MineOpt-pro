"""
Optimization Router - Scheduling Engine API Endpoints

Provides endpoints for:
- Fast Pass: Quick scheduling for interactive editing (<5 seconds)
- Full Pass: Complete optimization with all constraints (async)
- Status polling for long-running optimizations
- Decision explanations for transparency
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.optimization_service import optimizer
from ..services.schedule_engine import ScheduleEngine, ScheduleRunConfig
from ..domain.models_schedule_results import ScheduleRunRequest, DecisionExplanation
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/optimization", tags=["Optimization"])


class OptimizationRequest(BaseModel):
    """Request body for optimization runs."""
    site_id: str
    schedule_version_id: str
    horizon_start_period_id: Optional[str] = None
    horizon_end_period_id: Optional[str] = None
    objective_profile_id: Optional[str] = None


class OptimizationResponse(BaseModel):
    """Response from optimization run."""
    success: bool
    schedule_version_id: str
    tasks_created: int
    flows_created: int
    total_tonnes: float
    total_cost: float
    total_benefit: float
    total_penalty: float
    diagnostics: List[str]
    explanation_count: int


class RunStatusResponse(BaseModel):
    """Status of an async optimization run."""
    request_id: str
    status: str
    progress_percent: float
    schedule_type: str


# Legacy endpoint for backwards compatibility
@router.post("/run")
def run_optimization_legacy(request: OptimizationRequest, db: Session = Depends(get_db)):
    """
    [LEGACY] Run basic greedy optimization.
    Use /run-fast or /run-full for new implementations.
    """
    result = optimizer.run_greedy(db, request.site_id, request.schedule_version_id)
    return result


@router.post("/run-fast", response_model=OptimizationResponse)
def run_fast_pass(request: OptimizationRequest, db: Session = Depends(get_db)):
    """
    Quick schedule generation for interactive editing.
    
    Target response time: <5 seconds
    
    Stages executed:
    - Basic validation
    - Resource assignment
    - Greedy routing
    
    Skips full optimization, quality penalties, and explanations.
    """
    config = ScheduleRunConfig(
        site_id=request.site_id,
        schedule_version_id=request.schedule_version_id,
        horizon_start_period_id=request.horizon_start_period_id,
        horizon_end_period_id=request.horizon_end_period_id,
        objective_profile_id=request.objective_profile_id
    )
    
    engine = ScheduleEngine(db)
    result = engine.run_fast_pass(config)
    
    return OptimizationResponse(
        success=result.success,
        schedule_version_id=result.schedule_version_id,
        tasks_created=result.tasks_created,
        flows_created=result.flows_created,
        total_tonnes=result.total_tonnes,
        total_cost=result.total_cost,
        total_benefit=result.total_benefit,
        total_penalty=result.total_penalty,
        diagnostics=result.diagnostics,
        explanation_count=result.explanation_count
    )


def execute_full_pass_background(
    config: ScheduleRunConfig,
    request_id: str,
    db_url: str
):
    """Background task for full pass optimization."""
    # Note: In production, use proper async DB session
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        engine = ScheduleEngine(db)
        engine.update_run_status(request_id, "Running", 10.0)
        
        result = engine.run_full_pass(config)
        
        if result.success:
            engine.update_run_status(request_id, "Complete", 100.0)
        else:
            engine.update_run_status(request_id, "Failed", 100.0)
    finally:
        db.close()


@router.post("/run-full")
def run_full_pass(
    request: OptimizationRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Full optimization run with all constraints.
    
    Runs asynchronously. Returns run_id for status polling.
    
    All 8 stages executed:
    - Full validation
    - Candidate building
    - Resource assignment
    - Material generation
    - Flow optimization
    - Quality constraint evaluation
    - Iterative adjustment
    - Finalization with explanations
    """
    config = ScheduleRunConfig(
        site_id=request.site_id,
        schedule_version_id=request.schedule_version_id,
        horizon_start_period_id=request.horizon_start_period_id,
        horizon_end_period_id=request.horizon_end_period_id,
        objective_profile_id=request.objective_profile_id
    )
    
    engine = ScheduleEngine(db)
    run_request = engine.create_run_request(config, "FullPass")
    
    # For synchronous execution (can be made async with BackgroundTasks)
    # For now, run synchronously for simplicity
    result = engine.run_full_pass(config)
    engine.update_run_status(
        run_request.request_id, 
        "Complete" if result.success else "Failed",
        100.0
    )
    
    return {
        "run_id": run_request.request_id,
        "status": "Complete" if result.success else "Failed",
        "result": {
            "tasks_created": result.tasks_created,
            "flows_created": result.flows_created,
            "total_tonnes": result.total_tonnes,
            "diagnostics": result.diagnostics
        }
    }


@router.get("/status/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """
    Poll for optimization run progress.
    
    Returns current status and progress percentage.
    """
    run_request = db.query(ScheduleRunRequest)\
        .filter(ScheduleRunRequest.request_id == run_id)\
        .first()
    
    if not run_request:
        raise HTTPException(status_code=404, detail="Run request not found")
    
    return RunStatusResponse(
        request_id=run_request.request_id,
        status=run_request.status,
        progress_percent=run_request.progress_percent or 0,
        schedule_type=run_request.schedule_type
    )


@router.get("/explain/{schedule_version_id}")
def get_explanations(
    schedule_version_id: str, 
    period_id: Optional[str] = None,
    decision_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get decision explanations for a schedule.
    
    Explanations document why the optimizer made specific decisions,
    including quality constraint violations and alternative routes considered.
    
    Args:
        schedule_version_id: The schedule to get explanations for
        period_id: Optional filter by period
        decision_type: Optional filter by type (Routing, Blend, Cutpoint, RateReduction)
    """
    query = db.query(DecisionExplanation)\
        .filter(DecisionExplanation.schedule_version_id == schedule_version_id)
    
    if period_id:
        query = query.filter(DecisionExplanation.period_id == period_id)
    
    if decision_type:
        query = query.filter(DecisionExplanation.decision_type == decision_type)
    
    explanations = query.all()
    
    return {
        "schedule_version_id": schedule_version_id,
        "explanation_count": len(explanations),
        "explanations": [
            {
                "explanation_id": e.explanation_id,
                "period_id": e.period_id,
                "decision_type": e.decision_type,
                "summary": e.summary_text,
                "total_penalty": e.total_penalty,
                "binding_constraints": e.binding_constraints
            }
            for e in explanations
        ]
    }


@router.get("/diagnostics/{schedule_version_id}")
def get_schedule_diagnostics(schedule_version_id: str, db: Session = Depends(get_db)):
    """
    Get diagnostic summary for a schedule version.
    
    Returns aggregated metrics and any warnings/issues.
    """
    from ..domain.models_scheduling import Task
    from ..domain.models_schedule_results import FlowResult
    
    # Count tasks
    task_count = db.query(Task)\
        .filter(Task.schedule_version_id == schedule_version_id)\
        .count()
    
    # Sum tonnes
    from sqlalchemy import func
    total_tonnes = db.query(func.sum(Task.planned_quantity))\
        .filter(Task.schedule_version_id == schedule_version_id)\
        .scalar() or 0
    
    # Count flows
    flow_count = db.query(FlowResult)\
        .filter(FlowResult.schedule_version_id == schedule_version_id)\
        .count()
    
    # Sum penalties
    total_penalty = db.query(func.sum(FlowResult.penalty_cost))\
        .filter(FlowResult.schedule_version_id == schedule_version_id)\
        .scalar() or 0
    
    # Get explanation count
    explanation_count = db.query(DecisionExplanation)\
        .filter(DecisionExplanation.schedule_version_id == schedule_version_id)\
        .count()
    
    return {
        "schedule_version_id": schedule_version_id,
        "task_count": task_count,
        "total_tonnes": total_tonnes,
        "flow_count": flow_count,
        "total_penalty": total_penalty,
        "explanation_count": explanation_count,
        "warnings": []  # Future: add quality violations, capacity issues, etc.
    }

