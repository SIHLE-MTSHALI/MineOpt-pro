"""
Domain Model Package

This package contains all SQLAlchemy entity definitions for MineOpt Pro.
These models represent the enterprise specification domain objects.

Sections:
- Core: User, Role, Site
- Calendar: Calendar, Period
- Resource: MaterialType, QualityField, Activity, ActivityArea, Resource
- Flow: FlowNetwork, FlowNode, FlowArc, StockpileConfig, WashPlantConfig
- Parcel: Parcel, ParcelMovement
- WashTable: WashTable, WashTableRow, WashPlantOperatingPoint
- StagedStockpile: StagedStockpileConfig, BuildSpec, StagedPileState
- Scheduling: ScheduleVersion, Task
- ScheduleResults: ScheduleRunRequest, FlowResult, InventoryBalance, DecisionExplanation
"""

# Core entities
from .models_core import User, Role, Site

# Calendar/Time entities
from .models_calendar import Calendar, Period

# Resource and activity entities
from .models_resource import (
    MaterialType,
    QualityField,
    Activity,
    ActivityArea,
    Resource,
    ResourcePeriodParameters
)

# Flow network entities
from .models_flow import (
    FlowNetwork,
    FlowNode,
    FlowArc,
    ArcQualityObjective,
    TransportTimeModel,
    StockpileConfig,
    WashPlantConfig
)

# Material tracking entities
from .models_parcel import Parcel, ParcelMovement

# Wash table entities
from .models_wash_table import (
    WashTable,
    WashTableRow,
    WashPlantOperatingPoint
)

# Staged stockpile entities
from .models_staged_stockpile import (
    StagedStockpileConfig,
    BuildSpec,
    StagedPileState,
    StagedPileTransaction
)

# Scheduling entities
from .models_scheduling import ScheduleVersion, Task

# Schedule results entities
from .models_schedule_results import (
    ScheduleRunRequest,
    FlowResult,
    InventoryBalance,
    DecisionExplanation,
    ObjectiveProfile
)

# Export all models for easy import
__all__ = [
    # Core
    'User', 'Role', 'Site',
    # Calendar
    'Calendar', 'Period',
    # Resource
    'MaterialType', 'QualityField', 'Activity', 'ActivityArea', 
    'Resource', 'ResourcePeriodParameters',
    # Flow
    'FlowNetwork', 'FlowNode', 'FlowArc', 'ArcQualityObjective',
    'TransportTimeModel', 'StockpileConfig', 'WashPlantConfig',
    # Parcel
    'Parcel', 'ParcelMovement',
    # Wash Table
    'WashTable', 'WashTableRow', 'WashPlantOperatingPoint',
    # Staged Stockpile
    'StagedStockpileConfig', 'BuildSpec', 'StagedPileState', 'StagedPileTransaction',
    # Scheduling
    'ScheduleVersion', 'Task',
    # Schedule Results
    'ScheduleRunRequest', 'FlowResult', 'InventoryBalance', 
    'DecisionExplanation', 'ObjectiveProfile',
]
