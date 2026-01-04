"""
Integration Router - API endpoints for external system integration

Provides endpoints for:
- Fleet actuals import (tonnes, hours, cycles)
- GPS/Survey streaming (geometry, volumes)
- Maintenance integration (windows, availability)
- Publishing workflow (draft → published)
- BI system export
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_resource, models_flow
from ..services.integration_service import IntegrationService, MaintenanceWindow
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import io

router = APIRouter(prefix="/integration", tags=["Integration"])


# =============================================================================
# Pydantic Models
# =============================================================================

class SurveyUpdate(BaseModel):
    block_id: str
    mined_tonnes: float
    remaining_tonnes: float
    status: str  # Available, Mined, PartiallyMined


class ActualTonnesInput(BaseModel):
    equipment_id: str
    period_id: str
    area_id: Optional[str] = None
    destination_id: Optional[str] = None
    actual_tonnes: float
    material_type: Optional[str] = None
    quality_vector: Optional[Dict[str, float]] = None


class ActualTonnesBatch(BaseModel):
    source_system: str = "FMS"
    records: List[ActualTonnesInput]


class EquipmentHoursInput(BaseModel):
    equipment_id: str
    period_id: str
    operating_hours: float
    delay_hours: float = 0
    standby_hours: float = 0
    maintenance_hours: float = 0


class EquipmentHoursBatch(BaseModel):
    source_system: str = "FMS"
    records: List[EquipmentHoursInput]


class CycleTimeInput(BaseModel):
    equipment_id: str
    period_id: str
    route_id: str
    cycle_count: int
    average_cycle_minutes: float
    total_tonnes: float


class CycleTimeBatch(BaseModel):
    source_system: str = "FMS"
    records: List[CycleTimeInput]


class GeometryUpdateInput(BaseModel):
    area_id: str
    geometry_type: str  # polygon, centroid, elevation
    geometry_data: Dict
    survey_date: datetime
    source: str = "Survey"


class StockpileVolumeInput(BaseModel):
    stockpile_id: str
    survey_date: datetime
    volume_bcm: float
    calculated_tonnes: float
    density_factor: float = 1.6
    source: str = "Survey"


class MaintenanceWindowInput(BaseModel):
    equipment_id: str
    start_time: datetime
    end_time: datetime
    maintenance_type: str
    description: Optional[str] = None
    priority: int = 0


class MaintenanceBatch(BaseModel):
    source_system: str = "CMMS"
    windows: List[MaintenanceWindowInput]


class PublishRequest(BaseModel):
    schedule_version_id: str
    published_by: str


class WebhookRequest(BaseModel):
    event_type: str
    payload: Dict
    webhook_url: Optional[str] = None


# =============================================================================
# Legacy Survey/Lab Endpoints
# =============================================================================

@router.post("/survey/actuals")
def import_survey_actuals(updates: List[SurveyUpdate], db: Session = Depends(get_db)):
    """Updates Block Model status based on Survey data."""
    updated_count = 0
    not_found = []
    
    for up in updates:
        area = db.query(models_resource.ActivityArea)\
            .filter(models_resource.ActivityArea.area_id == up.block_id).first()
        if not area:
            area = db.query(models_resource.ActivityArea)\
                .filter(models_resource.ActivityArea.name == up.block_id).first()
             
        if area:
            if not area.slice_states:
                area.slice_states = [{}]
                
            state = list(area.slice_states)
            current_slice = state[0]
            
            current_slice['quantity'] = up.remaining_tonnes
            current_slice['status'] = up.status
            
            area.slice_states = state
            updated_count += 1
        else:
            not_found.append(up.block_id)
            
    db.commit()
    
    return {
        "message": f"Processed {len(updates)} updates.",
        "updated": updated_count,
        "not_found": not_found
    }


@router.post("/lab/quality")
def import_lab_results(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import Lab csv: StockpileID, CV, Ash, etc."""
    try:
        content = file.file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        results = []
        for index, row in df.iterrows():
            node_name = row.get('Stockpile')
            if not node_name:
                continue
            
            node = db.query(models_flow.FlowNode)\
                .filter(models_flow.FlowNode.name == node_name).first()
            if node and node.stockpile_config:
                config = node.stockpile_config
                current_q = config.current_grade_vector or {}
                
                for col in df.columns:
                    if col in ['Stockpile', 'Date', 'SampleID']:
                        continue
                    current_q[col] = float(row[col])
                    
                config.current_grade_vector = current_q
                results.append(node_name)
                
        db.commit()
        return {"message": "Lab Data Imported", "updated_stockpiles": results}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Fleet Actuals Import
# =============================================================================

@router.post("/fleet/actual-tonnes")
def import_actual_tonnes(batch: ActualTonnesBatch, db: Session = Depends(get_db)):
    """Import actual production tonnes from Fleet Management System."""
    service = IntegrationService(db)
    records = [r.model_dump() for r in batch.records]
    result = service.import_actual_tonnes(records, batch.source_system)
    
    return {
        "import_id": result.import_id,
        "status": result.status.value,
        "records_received": result.records_received,
        "records_processed": result.records_processed,
        "records_skipped": result.records_skipped,
        "errors": result.errors[:10],  # Limit error list
        "warnings": result.warnings[:10]
    }


@router.post("/fleet/equipment-hours")
def import_equipment_hours(batch: EquipmentHoursBatch, db: Session = Depends(get_db)):
    """Import equipment operating hours from Fleet Management System."""
    service = IntegrationService(db)
    records = [r.model_dump() for r in batch.records]
    result = service.import_equipment_hours(records, batch.source_system)
    
    return {
        "import_id": result.import_id,
        "status": result.status.value,
        "records_received": result.records_received,
        "records_processed": result.records_processed
    }


@router.post("/fleet/cycle-times")
def import_cycle_times(batch: CycleTimeBatch, db: Session = Depends(get_db)):
    """Import cycle time actuals from Fleet Management System."""
    service = IntegrationService(db)
    records = [r.model_dump() for r in batch.records]
    result = service.import_cycle_times(records, batch.source_system)
    
    return {
        "import_id": result.import_id,
        "status": result.status.value,
        "records_received": result.records_received,
        "records_processed": result.records_processed
    }


# =============================================================================
# GPS/Survey Streaming
# =============================================================================

@router.post("/survey/geometry")
def update_geometry(update: GeometryUpdateInput, db: Session = Depends(get_db)):
    """Update activity area geometry from GPS/Survey data."""
    from ..services.integration_service import GeometryUpdate
    
    service = IntegrationService(db)
    geo_update = GeometryUpdate(
        area_id=update.area_id,
        geometry_type=update.geometry_type,
        geometry_data=update.geometry_data,
        survey_date=update.survey_date,
        source=update.source
    )
    
    return service.update_geometry(geo_update)


@router.post("/survey/stockpile-volume")
def update_stockpile_volume(update: StockpileVolumeInput, db: Session = Depends(get_db)):
    """Update stockpile volume from survey data."""
    from ..services.integration_service import StockpileVolumeUpdate
    
    service = IntegrationService(db)
    vol_update = StockpileVolumeUpdate(
        stockpile_id=update.stockpile_id,
        survey_date=update.survey_date,
        volume_bcm=update.volume_bcm,
        calculated_tonnes=update.calculated_tonnes,
        density_factor=update.density_factor,
        source=update.source
    )
    
    return service.update_stockpile_volume(vol_update)


# =============================================================================
# Maintenance Integration
# =============================================================================

@router.post("/maintenance/windows")
def import_maintenance_windows(batch: MaintenanceBatch, db: Session = Depends(get_db)):
    """Import scheduled maintenance windows from CMMS."""
    service = IntegrationService(db)
    windows = [
        MaintenanceWindow(
            equipment_id=w.equipment_id,
            start_time=w.start_time,
            end_time=w.end_time,
            maintenance_type=w.maintenance_type,
            description=w.description,
            priority=w.priority
        )
        for w in batch.windows
    ]
    
    result = service.import_maintenance_windows(windows, batch.source_system)
    
    return {
        "import_id": result.import_id,
        "status": result.status.value,
        "windows_received": result.records_received,
        "windows_processed": result.records_processed,
        "errors": result.errors
    }


@router.post("/maintenance/availability/{equipment_id}")
def update_availability_forecast(
    equipment_id: str,
    forecast: List[Dict],
    db: Session = Depends(get_db)
):
    """Update equipment availability forecast."""
    service = IntegrationService(db)
    return service.update_availability_forecast(equipment_id, forecast)


# =============================================================================
# Publishing Workflow
# =============================================================================

@router.post("/publish")
def publish_schedule(request: PublishRequest, db: Session = Depends(get_db)):
    """Transition schedule from Draft to Published."""
    service = IntegrationService(db)
    return service.publish_schedule(request.schedule_version_id, request.published_by)


@router.get("/dispatch-targets/{schedule_version_id}")
def get_dispatch_targets(schedule_version_id: str, db: Session = Depends(get_db)):
    """Generate dispatch targets from published schedule."""
    service = IntegrationService(db)
    targets = service.generate_dispatch_targets(schedule_version_id)
    
    return {
        "schedule_version_id": schedule_version_id,
        "target_count": len(targets),
        "targets": targets
    }


@router.get("/export/bi/{schedule_version_id}")
def export_to_bi_system(
    schedule_version_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Export schedule data for BI systems."""
    service = IntegrationService(db)
    return service.export_to_bi_system(schedule_version_id, format)


@router.post("/webhook")
def trigger_webhook(request: WebhookRequest, db: Session = Depends(get_db)):
    """Trigger webhook for event publishing."""
    service = IntegrationService(db)
    return service.trigger_webhook(
        request.event_type,
        request.payload,
        request.webhook_url
    )


# =============================================================================
# Import History
# =============================================================================

@router.get("/history")
def get_import_history(
    record_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get import history records."""
    service = IntegrationService(db)
    history = service.get_import_history(record_type, limit)
    
    return {
        "record_count": len(history),
        "records": history
    }


# =============================================================================
# Connector Management
# =============================================================================

class ConnectorCreate(BaseModel):
    connector_type: str  # 'fms', 'lims'
    name: str
    site_id: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sync_interval_seconds: int = 300
    custom_settings: Dict = {}


@router.get("/connectors")
def list_connectors():
    """List all registered connectors."""
    from ..services.connectors import connector_registry
    
    return {
        "connectors": [
            {
                "connector_id": s.connector_id,
                "status": s.status.value,
                "last_sync": s.last_sync.isoformat() if s.last_sync else None,
                "last_error": s.last_error,
                "metrics": s.metrics
            }
            for s in connector_registry.list_connectors()
        ]
    }


@router.post("/connectors")
def create_connector(config: ConnectorCreate):
    """Create and register a new connector."""
    import uuid
    from ..services.connectors import (
        ConnectorConfig, ConnectorType, 
        create_connector as factory_create, connector_registry
    )
    
    connector_config = ConnectorConfig(
        connector_id=str(uuid.uuid4()),
        connector_type=ConnectorType(config.connector_type),
        name=config.name,
        site_id=config.site_id,
        base_url=config.base_url,
        api_key=config.api_key,
        username=config.username,
        password=config.password,
        sync_interval_seconds=config.sync_interval_seconds,
        custom_settings=config.custom_settings
    )
    
    connector = factory_create(connector_config)
    connector_registry.register(connector)
    
    return {
        "connector_id": connector.connector_id,
        "message": "Connector registered successfully"
    }


@router.post("/connectors/{connector_id}/test")
async def test_connector(connector_id: str):
    """Test connection to external system."""
    from ..services.connectors import connector_registry
    
    connector = connector_registry.get(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    success = await connector.test_connection()
    
    return {
        "connector_id": connector_id,
        "success": success,
        "status": connector.get_status().status.value
    }


@router.post("/connectors/{connector_id}/sync")
async def sync_connector(connector_id: str, sync_type: str = "pull"):
    """Trigger a sync operation for a connector."""
    from ..services.connectors import connector_registry
    
    connector = connector_registry.get(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    result = await connector.sync_data(sync_type)
    
    return {
        "connector_id": connector_id,
        "success": result.success,
        "records_processed": result.records_processed,
        "records_created": result.records_created,
        "records_updated": result.records_updated,
        "records_failed": result.records_failed,
        "duration_ms": result.duration_ms,
        "error_message": result.error_message
    }


@router.delete("/connectors/{connector_id}")
def delete_connector(connector_id: str):
    """Unregister a connector."""
    from ..services.connectors import connector_registry
    
    connector = connector_registry.get(connector_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    connector_registry.unregister(connector_id)
    
    return {"message": "Connector unregistered"}


# =============================================================================
# Webhook Management
# =============================================================================

class WebhookCreate(BaseModel):
    site_id: str
    url: str
    secret: Optional[str] = None
    event_types: List[str] = []  # Empty = all events
    headers: Dict[str, str] = {}


@router.get("/webhooks")
def list_webhooks(site_id: Optional[str] = None):
    """List registered webhooks."""
    from ..services.connectors import webhook_publisher
    
    webhooks = webhook_publisher.list_webhooks(site_id)
    
    return {
        "webhooks": [
            {
                "webhook_id": w.webhook_id,
                "site_id": w.site_id,
                "url": w.url,
                "event_types": w.event_types,
                "enabled": w.enabled,
                "created_at": w.created_at.isoformat()
            }
            for w in webhooks
        ]
    }


@router.post("/webhooks")
def register_webhook(webhook: WebhookCreate):
    """Register a new webhook endpoint."""
    import uuid
    from ..services.connectors import WebhookRegistration, webhook_publisher
    
    registration = WebhookRegistration(
        webhook_id=str(uuid.uuid4()),
        site_id=webhook.site_id,
        url=webhook.url,
        secret=webhook.secret,
        event_types=webhook.event_types,
        headers=webhook.headers
    )
    
    webhook_publisher.register_webhook(registration)
    
    return {
        "webhook_id": registration.webhook_id,
        "message": "Webhook registered successfully"
    }


@router.delete("/webhooks/{webhook_id}")
def unregister_webhook(webhook_id: str):
    """Unregister a webhook."""
    from ..services.connectors import webhook_publisher
    
    webhook = webhook_publisher.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook_publisher.unregister_webhook(webhook_id)
    
    return {"message": "Webhook unregistered"}


@router.get("/webhooks/{webhook_id}/deliveries")
def get_webhook_deliveries(webhook_id: str, limit: int = 50):
    """Get delivery history for a webhook."""
    from ..services.connectors import webhook_publisher
    
    deliveries = webhook_publisher.get_delivery_history(webhook_id, limit)
    
    return {
        "webhook_id": webhook_id,
        "delivery_count": len(deliveries),
        "deliveries": deliveries
    }


@router.post("/webhooks/test")
async def test_webhook(url: str, event_type: str = "test.ping"):
    """Send a test webhook to verify endpoint."""
    from ..services.connectors import WebhookEventType, webhook_publisher
    import uuid
    
    # Create temporary registration for test
    from ..services.connectors import WebhookRegistration
    
    test_webhook = WebhookRegistration(
        webhook_id=f"test-{uuid.uuid4().hex[:8]}",
        site_id="test",
        url=url
    )
    
    webhook_publisher.register_webhook(test_webhook)
    
    try:
        delivery_ids = await webhook_publisher.publish(
            WebhookEventType.RUN_COMPLETED,  # Use a generic event
            {"message": "Test webhook from MineOpt", "timestamp": datetime.utcnow().isoformat()},
            "test"
        )
        
        return {
            "success": True,
            "delivery_id": delivery_ids[0] if delivery_ids else None,
            "message": "Test webhook sent"
        }
    finally:
        webhook_publisher.unregister_webhook(test_webhook.webhook_id)
