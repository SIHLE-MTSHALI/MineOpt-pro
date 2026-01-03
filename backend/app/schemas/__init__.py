"""
Comprehensive Pydantic Schemas for MineOpt Pro Enterprise API

This module provides request/response models for all API endpoints,
ensuring type safety and automatic validation.

Organized by domain:
- Core (Sites, Users, Roles)
- Calendar (Calendars, Periods)
- Resources (Resources, Activities, ActivityAreas, Materials)
- Flow (Networks, Nodes, Arcs, Quality Objectives)
- Scheduling (Versions, Tasks, Run Requests)
- Quality (Fields, Blending, Compliance)
- Stockpiles (Simple and Staged)
- Wash Plant (Tables, Operating Points)
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class MaterialCategory(str, Enum):
    ROM = "ROM"
    WASTE = "Waste"
    REJECT = "Reject"
    PRODUCT = "Product"
    INTERMEDIATE = "Intermediate"


class NodeType(str, Enum):
    SOURCE = "Source"
    STOCKPILE = "Stockpile"
    STAGED_STOCKPILE = "StagedStockpile"
    CRUSHER = "Crusher"
    WASH_PLANT = "WashPlant"
    DUMP = "Dump"
    PRODUCT_SINK = "ProductSink"
    LOADOUT = "Loadout"


class ResourceType(str, Enum):
    EXCAVATOR = "Excavator"
    TRUCK_FLEET = "TruckFleet"
    DOZER = "Dozer"
    DRILL = "Drill"
    CRUSHER = "Crusher"
    WASH_PLANT = "WashPlant"
    CONVEYOR = "Conveyor"
    LOADER = "Loader"


class TaskType(str, Enum):
    MINING = "Mining"
    HAULAGE = "Haulage"
    PROCESSING = "Processing"
    REHANDLE = "Rehandle"
    DELAY = "Delay"
    OPTIMISER_DELAY = "OptimiserDelay"
    MAINTENANCE = "Maintenance"


class ScheduleStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"


class ObjectiveType(str, Enum):
    TARGET = "Target"
    MIN = "Min"
    MAX = "Max"
    RANGE = "Range"


class QualityBasis(str, Enum):
    ARB = "ARB"
    ADB = "ADB"
    DAF = "DAF"
    OTHER = "Other"


class ReclaimMethod(str, Enum):
    FIFO = "FIFO"
    LIFO = "LIFO"
    PROPORTIONAL = "BlendedProportional"


class CutpointMode(str, Enum):
    FIXED = "FixedRD"
    TARGET_QUALITY = "TargetQuality"
    OPTIMIZER = "OptimiserSelected"


class PileState(str, Enum):
    BUILDING = "Building"
    FULL = "Full"
    DEPLETING = "Depleting"
    EMPTY = "Empty"


# =============================================================================
# BASE MODELS
# =============================================================================

class BaseResponse(BaseModel):
    """Base class for all response models."""
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Standard message response."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# =============================================================================
# CORE - SITES
# =============================================================================

class SiteCreate(BaseModel):
    """Request model for creating a site."""
    name: str
    time_zone: str = "UTC"
    unit_system: str = "Metric"
    default_quality_basis_preferences: Optional[Dict[str, str]] = None


class SiteUpdate(BaseModel):
    """Request model for updating a site."""
    name: Optional[str] = None
    time_zone: Optional[str] = None
    unit_system: Optional[str] = None
    default_quality_basis_preferences: Optional[Dict[str, str]] = None


class SiteResponse(BaseResponse):
    """Response model for a site."""
    site_id: str
    name: str
    time_zone: str
    unit_system: str
    default_quality_basis_preferences: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None


# =============================================================================
# CORE - USERS
# =============================================================================

class UserCreate(BaseModel):
    """Request model for creating a user."""
    username: str
    email: str
    password: str
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Request model for updating a user."""
    display_name: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseResponse):
    """Response model for a user (no password)."""
    user_id: str
    username: str
    display_name: Optional[str] = None
    email: str
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class RoleResponse(BaseResponse):
    """Response model for a role."""
    role_id: str
    name: str
    permissions: Optional[List[str]] = None


# =============================================================================
# CALENDAR
# =============================================================================

class CalendarCreate(BaseModel):
    """Request model for creating a calendar."""
    site_id: str
    name: str
    description: Optional[str] = None
    period_granularity_type: str = "Shift"


class CalendarResponse(BaseResponse):
    """Response model for a calendar."""
    calendar_id: str
    site_id: str
    name: str
    description: Optional[str] = None
    period_granularity_type: str
    created_at: Optional[datetime] = None


class PeriodCreate(BaseModel):
    """Request model for creating a period."""
    calendar_id: str
    name: str
    start_datetime: datetime
    end_datetime: datetime
    duration_hours: float = 12.0
    group_shift: Optional[str] = None
    group_day: Optional[str] = None
    group_week: Optional[str] = None
    group_month: Optional[str] = None
    is_working_period: bool = True
    notes: Optional[str] = None


class PeriodResponse(BaseResponse):
    """Response model for a period."""
    period_id: str
    calendar_id: str
    name: str
    start_datetime: datetime
    end_datetime: datetime
    duration_hours: float
    group_shift: Optional[str] = None
    group_day: Optional[str] = None
    group_week: Optional[str] = None
    group_month: Optional[str] = None
    is_working_period: bool


# =============================================================================
# RESOURCES
# =============================================================================

class ResourceCreate(BaseModel):
    """Request model for creating a resource."""
    site_id: str
    name: str
    resource_type: str
    capacity_type: str = "Throughput"
    base_rate: Optional[float] = None
    base_rate_units: Optional[str] = None
    can_reduce_rate_for_blend: bool = False
    min_rate_factor: float = 0.0
    max_rate_factor: float = 1.0
    cost_per_hour: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    emissions_factor: Optional[float] = None
    supported_activities: Optional[List[str]] = None


class ResourceResponse(BaseResponse):
    """Response model for a resource."""
    resource_id: str
    site_id: str
    name: str
    resource_type: str
    capacity_type: str
    base_rate: Optional[float] = None
    base_rate_units: Optional[str] = None
    can_reduce_rate_for_blend: bool
    min_rate_factor: float
    max_rate_factor: float
    cost_per_hour: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    emissions_factor: Optional[float] = None
    supported_activities: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class ResourcePeriodParamsCreate(BaseModel):
    """Request model for resource period parameters."""
    resource_id: str
    period_id: str
    availability_fraction: float = 1.0
    utilisation_fraction: float = 1.0
    efficiency_fraction: float = 1.0
    rate_factor: float = 1.0
    notes: Optional[str] = None


class ResourcePeriodParamsResponse(BaseResponse):
    """Response model for resource period parameters."""
    param_id: str
    resource_id: str
    period_id: str
    availability_fraction: float
    utilisation_fraction: float
    efficiency_fraction: float
    rate_factor: float
    notes: Optional[str] = None


# =============================================================================
# ACTIVITIES
# =============================================================================

class ActivityCreate(BaseModel):
    """Request model for creating an activity."""
    site_id: str
    name: str
    display_color: Optional[str] = None
    moves_material: bool = True
    required_haulage: bool = True
    quantity_field_type: str = "Tonnes"
    default_number_of_slices: int = 1
    max_resources: Optional[int] = None
    is_selectable_in_ui: bool = True
    precedence_rules: Optional[List[str]] = None


class ActivityResponse(BaseResponse):
    """Response model for an activity."""
    activity_id: str
    site_id: str
    name: str
    display_color: Optional[str] = None
    moves_material: bool
    required_haulage: bool
    quantity_field_type: str
    default_number_of_slices: int
    max_resources: Optional[int] = None
    is_selectable_in_ui: bool
    precedence_rules: Optional[List[str]] = None


# =============================================================================
# ACTIVITY AREAS
# =============================================================================

class SliceState(BaseModel):
    """Model for a slice within an activity area."""
    index: int
    status: str  # Locked, Released, Completed
    quantity: float
    material_type_id: Optional[str] = None
    material_name: Optional[str] = None
    qualities: Optional[Dict[str, float]] = None


class ActivityAreaCreate(BaseModel):
    """Request model for creating an activity area."""
    site_id: str
    name: str
    activity_id: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    bench_level: Optional[str] = None
    elevation_rl: Optional[float] = None
    mining_direction_vector: Optional[List[float]] = None
    slice_count: int = 1
    slice_states: Optional[List[SliceState]] = None
    priority: int = 0
    is_locked: bool = False
    lock_reason: Optional[str] = None
    preferred_destination_node_id: Optional[str] = None


class ActivityAreaResponse(BaseResponse):
    """Response model for an activity area."""
    area_id: str
    site_id: str
    name: str
    activity_id: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    bench_level: Optional[str] = None
    elevation_rl: Optional[float] = None
    mining_direction_vector: Optional[List[float]] = None
    slice_count: int
    slice_states: Optional[List[Dict[str, Any]]] = None
    priority: int
    is_locked: bool
    lock_reason: Optional[str] = None
    preferred_destination_node_id: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# MATERIAL TYPES
# =============================================================================

class MaterialTypeCreate(BaseModel):
    """Request model for creating a material type."""
    site_id: str
    name: str
    category: str
    default_density: Optional[float] = None
    moisture_basis_for_quantity: str = "as-mined"
    reporting_group: Optional[str] = None


class MaterialTypeResponse(BaseResponse):
    """Response model for a material type."""
    material_type_id: str
    site_id: str
    name: str
    category: str
    default_density: Optional[float] = None
    moisture_basis_for_quantity: str
    reporting_group: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# QUALITY FIELDS
# =============================================================================

class QualityFieldCreate(BaseModel):
    """Request model for creating a quality field."""
    site_id: str
    name: str
    description: Optional[str] = None
    units: Optional[str] = None
    basis: str = "ARB"
    aggregation_rule: str = "WeightedAverage"
    missing_data_policy: str = "Error"
    default_value: Optional[float] = None
    constraint_direction_default: Optional[str] = None
    penalty_function_type: str = "Linear"
    penalty_parameters: Optional[Dict[str, Any]] = None


class QualityFieldResponse(BaseResponse):
    """Response model for a quality field."""
    quality_field_id: str
    site_id: str
    name: str
    description: Optional[str] = None
    units: Optional[str] = None
    basis: str
    aggregation_rule: str
    missing_data_policy: str
    default_value: Optional[float] = None
    constraint_direction_default: Optional[str] = None
    penalty_function_type: str
    penalty_parameters: Optional[Dict[str, Any]] = None


# =============================================================================
# FLOW NETWORK
# =============================================================================

class FlowNetworkCreate(BaseModel):
    """Request model for creating a flow network."""
    site_id: str
    name: str
    description: Optional[str] = None


class FlowNetworkResponse(BaseResponse):
    """Response model for a flow network."""
    network_id: str
    site_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class FlowNodeCreate(BaseModel):
    """Request model for creating a flow node."""
    network_id: str
    node_type: str
    name: str
    location_geometry: Optional[Dict[str, Any]] = None
    capacity_tonnes: Optional[float] = None
    operating_resource_id: Optional[str] = None
    inventory_tracking_enabled: bool = True


class FlowNodeResponse(BaseResponse):
    """Response model for a flow node."""
    node_id: str
    network_id: str
    node_type: str
    name: str
    location_geometry: Optional[Dict[str, Any]] = None
    capacity_tonnes: Optional[float] = None
    operating_resource_id: Optional[str] = None
    inventory_tracking_enabled: bool
    created_at: Optional[datetime] = None


class FlowArcCreate(BaseModel):
    """Request model for creating a flow arc."""
    network_id: str
    from_node_id: str
    to_node_id: str
    allowed_material_type_ids: Optional[List[str]] = None
    capacity_tonnes_per_period: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    benefit_per_tonne: Optional[float] = None
    transport_time_model_id: Optional[str] = None
    is_enabled: bool = True


class FlowArcResponse(BaseResponse):
    """Response model for a flow arc."""
    arc_id: str
    network_id: str
    from_node_id: str
    to_node_id: str
    allowed_material_type_ids: Optional[List[str]] = None
    capacity_tonnes_per_period: Optional[float] = None
    cost_per_tonne: Optional[float] = None
    benefit_per_tonne: Optional[float] = None
    transport_time_model_id: Optional[str] = None
    is_enabled: bool
    created_at: Optional[datetime] = None


class ArcQualityObjectiveCreate(BaseModel):
    """Request model for creating an arc quality objective."""
    arc_id: str
    quality_field_id: str
    objective_type: str  # Target, Min, Max, Range
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    penalty_weight: float = 1.0
    penalty_function_override: Optional[str] = None
    hard_constraint: bool = False
    notes: Optional[str] = None


class ArcQualityObjectiveResponse(BaseResponse):
    """Response model for an arc quality objective."""
    objective_id: str
    arc_id: str
    quality_field_id: str
    objective_type: str
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    penalty_weight: float
    penalty_function_override: Optional[str] = None
    hard_constraint: bool
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# STOCKPILE
# =============================================================================

class StockpileConfigCreate(BaseModel):
    """Request model for creating a stockpile configuration."""
    node_id: str
    inventory_method: str = "WeightedAverage"
    reclaim_method: str = "FIFO"
    max_capacity_tonnes: Optional[float] = None
    current_inventory_tonnes: float = 0.0
    current_grade_vector: Optional[Dict[str, float]] = None


class StockpileConfigResponse(BaseResponse):
    """Response model for a stockpile configuration."""
    config_id: str
    node_id: str
    inventory_method: str
    reclaim_method: str
    max_capacity_tonnes: Optional[float] = None
    current_inventory_tonnes: float
    current_grade_vector: Optional[Dict[str, float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockpileOperationRequest(BaseModel):
    """Request for stockpile operations (add/reclaim)."""
    tonnes: float
    quality_vector: Optional[Dict[str, float]] = None
    period_id: Optional[str] = None
    material_type_id: Optional[str] = None


class StockpileOperationResponse(BaseModel):
    """Response for stockpile operations."""
    success: bool
    operation: str  # add, reclaim
    tonnes: float
    new_inventory: float
    new_quality_vector: Optional[Dict[str, float]] = None
    message: Optional[str] = None


# =============================================================================
# STAGED STOCKPILE
# =============================================================================

class BuildSpecCreate(BaseModel):
    """Request for creating a build specification."""
    config_id: str
    build_name: str
    target_tonnes: float
    min_threshold_tonnes: Optional[float] = None
    max_capacity_tonnes: Optional[float] = None
    quality_targets: Optional[Dict[str, Dict[str, float]]] = None
    planned_start_period_id: Optional[str] = None
    planned_end_period_id: Optional[str] = None


class BuildSpecResponse(BaseResponse):
    """Response for a build specification."""
    spec_id: str
    config_id: str
    build_name: str
    target_tonnes: float
    min_threshold_tonnes: Optional[float] = None
    max_capacity_tonnes: Optional[float] = None
    quality_targets: Optional[Dict[str, Dict[str, float]]] = None
    planned_start_period_id: Optional[str] = None
    planned_end_period_id: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None


class StagedPileStateResponse(BaseResponse):
    """Response for staged pile state."""
    state_id: str
    config_id: str
    pile_index: int
    state: str  # Building, Full, Depleting, Empty
    current_spec_id: Optional[str] = None
    current_tonnes: float
    current_quality_vector: Optional[Dict[str, float]] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# WASH PLANT
# =============================================================================

class WashTableRowCreate(BaseModel):
    """Request for creating a wash table row."""
    table_id: str
    relative_density_cutpoint: float
    cumulative_yield_fraction: float
    product_quality_vector: Dict[str, float]
    reject_quality_vector: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class WashTableRowResponse(BaseResponse):
    """Response for a wash table row."""
    row_id: str
    table_id: str
    row_index: int
    relative_density_cutpoint: float
    cumulative_yield_fraction: float
    product_quality_vector: Dict[str, float]
    reject_quality_vector: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class WashTableCreate(BaseModel):
    """Request for creating a wash table."""
    site_id: str
    name: str
    description: Optional[str] = None
    basis_assumptions: Optional[Dict[str, str]] = None


class WashTableResponse(BaseResponse):
    """Response for a wash table."""
    table_id: str
    site_id: str
    name: str
    description: Optional[str] = None
    basis_assumptions: Optional[Dict[str, str]] = None
    rows: Optional[List[WashTableRowResponse]] = None
    created_at: Optional[datetime] = None


class WashPlantProcessRequest(BaseModel):
    """Request for processing material through wash plant."""
    node_id: str
    feed_tonnes: float
    feed_quality_vector: Dict[str, float]
    cutpoint_rd: Optional[float] = None
    target_quality_field: Optional[str] = None
    target_quality_value: Optional[float] = None


class WashPlantProcessResponse(BaseModel):
    """Response for wash plant processing."""
    product_tonnes: float
    product_quality_vector: Dict[str, float]
    reject_tonnes: float
    reject_quality_vector: Optional[Dict[str, float]] = None
    cutpoint_used: float
    yield_achieved: float
    explanation: Optional[str] = None


# =============================================================================
# SCHEDULING
# =============================================================================

class ScheduleVersionCreate(BaseModel):
    """Request for creating a schedule version."""
    site_id: str
    name: str
    description: Optional[str] = None
    schedule_type: str = "Authoritative"
    horizon_start_period_id: Optional[str] = None
    horizon_end_period_id: Optional[str] = None
    parent_schedule_version_id: Optional[str] = None
    change_reason: Optional[str] = None


class ScheduleVersionResponse(BaseResponse):
    """Response for a schedule version."""
    version_id: str
    site_id: str
    name: str
    description: Optional[str] = None
    status: str
    schedule_type: str
    horizon_start_period_id: Optional[str] = None
    horizon_end_period_id: Optional[str] = None
    parent_schedule_version_id: Optional[str] = None
    change_reason: Optional[str] = None
    run_diagnostics_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None


class TaskCreate(BaseModel):
    """Request for creating a task."""
    schedule_version_id: str
    resource_id: Optional[str] = None
    activity_id: Optional[str] = None
    period_id: Optional[str] = None
    activity_area_id: Optional[str] = None
    from_node_id: Optional[str] = None
    to_node_id: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    planned_quantity: float = 0.0
    material_type_id: Optional[str] = None
    task_type: str = "Mining"
    delay_reason_code: Optional[str] = None
    delay_reason_description: Optional[str] = None
    rate_factor_applied: float = 1.0
    kpi_tags: Optional[Dict[str, str]] = None
    expected_quality_vector: Optional[Dict[str, float]] = None
    notes: Optional[str] = None


class TaskResponse(BaseResponse):
    """Response for a task."""
    task_id: str
    schedule_version_id: str
    resource_id: Optional[str] = None
    activity_id: Optional[str] = None
    period_id: Optional[str] = None
    activity_area_id: Optional[str] = None
    from_node_id: Optional[str] = None
    to_node_id: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    planned_quantity: float
    actual_quantity: Optional[float] = None
    material_type_id: Optional[str] = None
    task_type: str
    delay_reason_code: Optional[str] = None
    delay_reason_description: Optional[str] = None
    status: str
    rate_factor_applied: float
    kpi_tags: Optional[Dict[str, str]] = None
    expected_quality_vector: Optional[Dict[str, float]] = None
    actual_quality_vector: Optional[Dict[str, float]] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class ScheduleRunRequest(BaseModel):
    """Request for running a schedule."""
    site_id: str
    schedule_version_id: str
    run_type: str = "FastPass"  # FastPass or FullPass
    horizon_start_period_id: Optional[str] = None
    horizon_end_period_id: Optional[str] = None
    objective_profile_id: Optional[str] = None
    max_iterations: int = 5


class ScheduleRunResponse(BaseModel):
    """Response for a schedule run."""
    request_id: str
    schedule_version_id: str
    status: str  # Pending, Running, Completed, Failed
    run_type: str
    tasks_created: int = 0
    flows_created: int = 0
    total_tonnes: float = 0.0
    total_cost: float = 0.0
    total_benefit: float = 0.0
    total_penalty: float = 0.0
    diagnostics: List[str] = []
    explanation_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


# =============================================================================
# QUALITY / BLENDING
# =============================================================================

class BlendSourceInput(BaseModel):
    """Input for a blend source (parcel or stockpile)."""
    source_id: str
    tonnes: float
    quality_vector: Dict[str, float]


class BlendCalculateRequest(BaseModel):
    """Request for calculating a blend."""
    sources: List[BlendSourceInput]


class BlendCalculateResponse(BaseModel):
    """Response for blend calculation."""
    total_tonnes: float
    blended_quality_vector: Dict[str, float]
    source_contributions: List[Dict[str, Any]]


class SpecComplianceRequest(BaseModel):
    """Request for checking spec compliance."""
    quality_vector: Dict[str, float]
    specs: Dict[str, Dict[str, float]]  # field_name -> {min, max, target}


class SpecComplianceResponse(BaseModel):
    """Response for spec compliance check."""
    compliant: bool
    violations: List[Dict[str, Any]]
    penalties: Dict[str, float]
    total_penalty: float


# =============================================================================
# REPORTING
# =============================================================================

class ReportRequest(BaseModel):
    """Request for generating a report."""
    report_type: str
    schedule_version_id: Optional[str] = None
    site_id: Optional[str] = None
    start_period_id: Optional[str] = None
    end_period_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    format: str = "json"  # json, csv, pdf


class ReportResponse(BaseModel):
    """Response for a generated report."""
    report_type: str
    generated_at: datetime
    parameters: Dict[str, Any]
    data: Any  # Report-specific data structure
    summary: Optional[Dict[str, Any]] = None


# =============================================================================
# INTEGRATION
# =============================================================================

class FleetActualsImport(BaseModel):
    """Request for importing fleet actuals."""
    source_system: str
    timestamp: datetime
    records: List[Dict[str, Any]]  # Flexible structure for different FMS


class FleetActualsResponse(BaseModel):
    """Response for fleet actuals import."""
    records_received: int
    records_processed: int
    records_failed: int
    errors: List[str]


class DispatchTargetResponse(BaseModel):
    """Response for dispatch targets."""
    schedule_version_id: str
    period_id: str
    targets: List[Dict[str, Any]]
    generated_at: datetime


# =============================================================================
# AUDIT
# =============================================================================

class AuditLogEntry(BaseResponse):
    """Response for an audit log entry."""
    log_id: str
    timestamp: datetime
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None


class AuditLogQuery(BaseModel):
    """Request for querying audit logs."""
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
