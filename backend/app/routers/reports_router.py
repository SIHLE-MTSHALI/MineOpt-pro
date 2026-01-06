"""
Reports Router - API endpoints for report scheduling and generation

Provides endpoints for:
- Report schedule management
- Report pack generation
- Email delivery configuration
- Product specifications and demand schedules
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/reports", tags=["Reports"])


# =============================================================================
# Pydantic Models
# =============================================================================

class EmailRecipientModel(BaseModel):
    email: str
    name: Optional[str] = None
    role: Optional[str] = None


class ReportScheduleCreate(BaseModel):
    name: str
    report_type: str
    cron_expression: str
    recipients: List[EmailRecipientModel]
    enabled: bool = True
    include_attachments: bool = True


class ReportScheduleUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    recipients: Optional[List[EmailRecipientModel]] = None
    enabled: Optional[bool] = None


class ReportPackRequest(BaseModel):
    pack_name: str
    report_types: List[str]
    date_range: Optional[Dict] = None


class ProductSpec(BaseModel):
    field: str
    label: str
    unit: str
    min_value: float
    max_value: float


class DemandPeriod(BaseModel):
    period: str
    target_tonnes: float
    committed_tonnes: float = 0


class ProductCreate(BaseModel):
    name: str
    code: str
    specs: List[ProductSpec]
    demand_schedule: List[DemandPeriod] = []


# =============================================================================
# In-Memory Storage (Demo)
# =============================================================================

_schedules_store: List[Dict] = [
    {
        "schedule_id": "1",
        "name": "Daily Production Summary",
        "report_type": "daily_production",
        "cron_expression": "0 6 * * *",
        "recipients": [{"email": "manager@site.com", "name": "Site Manager", "role": "manager"}],
        "enabled": True,
        "include_attachments": True,
        "created_at": "2026-01-01T00:00:00Z",
        "last_sent": None
    }
]

_products_store: List[Dict] = [
    {
        "id": "1",
        "name": "Export Grade A",
        "code": "EXP-A",
        "compliance_rate": 96,
        "specs": [
            {"field": "cv", "label": "CV", "unit": "MJ/kg", "min_value": 25, "max_value": 28},
            {"field": "ash", "label": "Ash", "unit": "%", "min_value": 0, "max_value": 12},
            {"field": "moisture", "label": "Moisture", "unit": "%", "min_value": 0, "max_value": 10}
        ],
        "demand_schedule": [
            {"period": "Jan 2026", "target_tonnes": 150000, "committed_tonnes": 155000},
            {"period": "Feb 2026", "target_tonnes": 140000, "committed_tonnes": 142000}
        ]
    },
    {
        "id": "2",
        "name": "Domestic Blend",
        "code": "DOM-B",
        "compliance_rate": 88,
        "specs": [
            {"field": "cv", "label": "CV", "unit": "MJ/kg", "min_value": 20, "max_value": 24},
            {"field": "ash", "label": "Ash", "unit": "%", "min_value": 0, "max_value": 18}
        ],
        "demand_schedule": [
            {"period": "Jan 2026", "target_tonnes": 80000, "committed_tonnes": 82000}
        ]
    }
]

_deliveries_store: List[Dict] = []


# =============================================================================
# Report Schedule Endpoints
# =============================================================================

@router.get("/schedules")
def list_report_schedules():
    """List all report schedules."""
    return _schedules_store


@router.get("/schedules/{schedule_id}")
def get_report_schedule(schedule_id: str):
    """Get a specific report schedule."""
    for s in _schedules_store:
        if s["schedule_id"] == schedule_id:
            return s
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/schedules")
def create_report_schedule(schedule: ReportScheduleCreate):
    """Create a new report schedule."""
    new_schedule = schedule.model_dump()
    new_schedule["schedule_id"] = str(uuid.uuid4())
    new_schedule["created_at"] = datetime.utcnow().isoformat()
    new_schedule["last_sent"] = None
    _schedules_store.append(new_schedule)
    return new_schedule


@router.patch("/schedules/{schedule_id}")
def update_report_schedule(schedule_id: str, updates: ReportScheduleUpdate):
    """Update a report schedule."""
    for i, s in enumerate(_schedules_store):
        if s["schedule_id"] == schedule_id:
            update_dict = updates.model_dump(exclude_unset=True)
            _schedules_store[i].update(update_dict)
            return _schedules_store[i]
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.delete("/schedules/{schedule_id}")
def delete_report_schedule(schedule_id: str):
    """Delete a report schedule."""
    global _schedules_store
    initial_len = len(_schedules_store)
    _schedules_store = [s for s in _schedules_store if s["schedule_id"] != schedule_id]
    if len(_schedules_store) == initial_len:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}


@router.post("/schedules/{schedule_id}/send")
def send_report_now(schedule_id: str):
    """Trigger immediate sending of a scheduled report."""
    for s in _schedules_store:
        if s["schedule_id"] == schedule_id:
            # Simulate sending
            delivery = {
                "delivery_id": str(uuid.uuid4()),
                "schedule_id": schedule_id,
                "recipients": [r["email"] for r in s.get("recipients", [])],
                "subject": f"{s['name']} - {datetime.utcnow().strftime('%Y-%m-%d')}",
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }
            _deliveries_store.append(delivery)
            s["last_sent"] = delivery["sent_at"]
            return delivery
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.get("/deliveries")
def list_deliveries(schedule_id: Optional[str] = None, limit: int = 50):
    """Get email delivery history."""
    deliveries = _deliveries_store
    if schedule_id:
        deliveries = [d for d in deliveries if d["schedule_id"] == schedule_id]
    return sorted(deliveries, key=lambda d: d.get("sent_at", ""), reverse=True)[:limit]


# =============================================================================
# Report Pack Generation
# =============================================================================

@router.get("/pack-types")
def get_report_pack_types():
    """Get available report types for pack generation."""
    return [
        {"id": "production_summary", "name": "Production Summary", "description": "Daily/weekly production overview"},
        {"id": "quality_report", "name": "Quality Analysis", "description": "Quality metrics and compliance"},
        {"id": "equipment_utilization", "name": "Equipment Utilization", "description": "Fleet performance and utilization"},
        {"id": "schedule_comparison", "name": "Schedule Comparison", "description": "Plan vs actual analysis"}
    ]


@router.post("/generate-pack")
def generate_report_pack(request: ReportPackRequest):
    """Generate a bundled PDF report pack."""
    pack_id = str(uuid.uuid4())
    
    # Simulate report generation
    reports = []
    total_pages = 0
    for report_type in request.report_types:
        pages = {"production_summary": 3, "quality_report": 4, "equipment_utilization": 2, "schedule_comparison": 2}.get(report_type, 1)
        reports.append({"type": report_type, "pages": pages})
        total_pages += pages
    
    return {
        "pack_id": pack_id,
        "pack_name": request.pack_name,
        "generated_at": datetime.utcnow().isoformat(),
        "reports": reports,
        "total_pages": total_pages,
        "file_path": f"/reports/{pack_id}/{request.pack_name.replace(' ', '_')}.pdf",
        "status": "generated"
    }


# =============================================================================
# Product Specifications - registered separately as /products
# =============================================================================

products_router = APIRouter(prefix="/products", tags=["Products"])


@products_router.get("")
def list_products():
    """List all product specifications."""
    return _products_store


@products_router.get("/{product_id}")
def get_product(product_id: str):
    """Get a specific product specification."""
    for p in _products_store:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")


@products_router.post("")
def create_product(product: ProductCreate):
    """Create a new product specification."""
    new_product = product.model_dump()
    new_product["id"] = str(uuid.uuid4())
    new_product["compliance_rate"] = 100  # Default to 100%
    new_product["created_at"] = datetime.utcnow().isoformat()
    _products_store.append(new_product)
    return new_product


@products_router.put("/{product_id}")
def update_product(product_id: str, product: ProductCreate):
    """Update a product specification."""
    for i, p in enumerate(_products_store):
        if p["id"] == product_id:
            updated = product.model_dump()
            updated["id"] = product_id
            updated["compliance_rate"] = p.get("compliance_rate", 100)
            updated["updated_at"] = datetime.utcnow().isoformat()
            _products_store[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Product not found")


@products_router.delete("/{product_id}")
def delete_product(product_id: str):
    """Delete a product specification."""
    global _products_store
    initial_len = len(_products_store)
    _products_store = [p for p in _products_store if p["id"] != product_id]
    if len(_products_store) == initial_len:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "deleted"}


@products_router.post("/{product_id}/demand")
def add_demand_period(product_id: str, period: DemandPeriod):
    """Add a demand period to a product."""
    for p in _products_store:
        if p["id"] == product_id:
            if "demand_schedule" not in p:
                p["demand_schedule"] = []
            p["demand_schedule"].append(period.model_dump())
            return p
    raise HTTPException(status_code=404, detail="Product not found")
