"""
MineOpt Pro Enterprise API

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    config_router, 
    calendar_router, 
    schedule_router, 
    stockpile_router, 
    reporting_router, 
    optimization_router, 
    integration_router, 
    auth_router,
    quality_router,
    staged_stockpile_router
)
from .database import engine, Base


# Import all domain models to register them with SQLAlchemy
from .domain.models_core import User, Role, Site
from .domain.models_calendar import Calendar, Period
from .domain.models_resource import (
    MaterialType, QualityField, Activity, ActivityArea, 
    Resource, ResourcePeriodParameters
)
from .domain.models_flow import (
    FlowNetwork, FlowNode, FlowArc, ArcQualityObjective,
    TransportTimeModel, StockpileConfig, WashPlantConfig
)
from .domain.models_parcel import Parcel, ParcelMovement
from .domain.models_wash_table import WashTable, WashTableRow, WashPlantOperatingPoint
from .domain.models_staged_stockpile import (
    StagedStockpileConfig, BuildSpec, StagedPileState, StagedPileTransaction
)
from .domain.models_scheduling import ScheduleVersion, Task
from .domain.models_schedule_results import (
    ScheduleRunRequest, FlowResult, InventoryBalance, 
    DecisionExplanation, ObjectiveProfile
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Create all database tables on startup
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized with {len(Base.metadata.tables)} tables")
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="MineOpt Pro Enterprise API",
    description="Enterprise coal mine production scheduling and optimization system",
    version="2.0.0-Enterprise",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router.router)
app.include_router(calendar_router.router)
app.include_router(schedule_router.router)
app.include_router(optimization_router.router)
app.include_router(stockpile_router.router)
app.include_router(reporting_router.router)
app.include_router(integration_router.router)
app.include_router(auth_router.router)
app.include_router(quality_router.router)
app.include_router(staged_stockpile_router.router)


@app.get("/")
def health_check():
    """API health check endpoint."""
    return {
        "status": "MineOpt Pro Server Running", 
        "version": "2.0.0-Enterprise",
        "tables_registered": len(Base.metadata.tables)
    }

