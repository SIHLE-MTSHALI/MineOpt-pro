"""
Webhook Publisher Service

Handles outbound webhook notifications for:
- Schedule events (created, updated, published)
- Task changes
- Quality alerts
- Inventory threshold breaches

Features:
- Retry logic with exponential backoff
- Delivery history logging
- Webhook registration management
- Signature verification
"""

import asyncio
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Supported webhook event types."""
    SCHEDULE_CREATED = "schedule.created"
    SCHEDULE_UPDATED = "schedule.updated"
    SCHEDULE_PUBLISHED = "schedule.published"
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    QUALITY_ALERT = "quality.alert"
    STOCKPILE_LOW = "stockpile.low"
    STOCKPILE_HIGH = "stockpile.high"
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookRegistration:
    """Registered webhook endpoint."""
    webhook_id: str
    site_id: str
    url: str
    secret: Optional[str] = None  # For HMAC signature
    event_types: List[str] = field(default_factory=list)  # Empty = all events
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    headers: Dict[str, str] = field(default_factory=dict)
    
    def should_receive(self, event_type: WebhookEventType) -> bool:
        """Check if this webhook should receive an event type."""
        if not self.enabled:
            return False
        if not self.event_types:
            return True  # Empty list = receive all
        return event_type.value in self.event_types


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    delivery_id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    max_attempts: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    
    def next_retry_delay(self) -> int:
        """Calculate delay before next retry (exponential backoff)."""
        return min(300, 2 ** self.attempts * 5)  # Max 5 minutes


class WebhookPublisher:
    """
    Manages webhook publishing with retry logic.
    
    Usage:
        publisher = WebhookPublisher()
        publisher.register_webhook(webhook)
        await publisher.publish(event_type, payload, site_id)
    """
    
    def __init__(self, db=None):
        self.db = db
        self._webhooks: Dict[str, WebhookRegistration] = {}
        self._delivery_history: List[WebhookDelivery] = []
        self._pending_deliveries: List[WebhookDelivery] = []
        self._retry_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def start(self):
        """Start the webhook publisher and retry processor."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._retry_task = asyncio.create_task(self._process_retries())
        logger.info("Webhook publisher started")
    
    async def stop(self):
        """Stop the webhook publisher."""
        if self._retry_task:
            self._retry_task.cancel()
        if self._http_client:
            await self._http_client.aclose()
        logger.info("Webhook publisher stopped")
    
    def register_webhook(self, webhook: WebhookRegistration):
        """Register a webhook endpoint."""
        self._webhooks[webhook.webhook_id] = webhook
        logger.info(f"Registered webhook: {webhook.webhook_id} -> {webhook.url}")
    
    def unregister_webhook(self, webhook_id: str):
        """Unregister a webhook endpoint."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookRegistration]:
        """Get a registered webhook."""
        return self._webhooks.get(webhook_id)
    
    def list_webhooks(self, site_id: Optional[str] = None) -> List[WebhookRegistration]:
        """List registered webhooks, optionally filtered by site."""
        webhooks = list(self._webhooks.values())
        if site_id:
            webhooks = [w for w in webhooks if w.site_id == site_id]
        return webhooks
    
    async def publish(
        self,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        site_id: str
    ) -> List[str]:
        """
        Publish an event to all matching webhooks.
        
        Returns list of delivery IDs.
        """
        delivery_ids = []
        
        # Find matching webhooks
        matching_webhooks = [
            w for w in self._webhooks.values()
            if w.site_id == site_id and w.should_receive(event_type)
        ]
        
        for webhook in matching_webhooks:
            delivery = await self._create_delivery(webhook, event_type, payload)
            delivery_ids.append(delivery.delivery_id)
            
            # Attempt immediate delivery
            asyncio.create_task(self._deliver(delivery, webhook))
        
        return delivery_ids
    
    async def _create_delivery(
        self,
        webhook: WebhookRegistration,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Create a delivery record."""
        import uuid
        
        delivery = WebhookDelivery(
            delivery_id=str(uuid.uuid4()),
            webhook_id=webhook.webhook_id,
            event_type=event_type.value,
            payload=payload
        )
        
        self._delivery_history.append(delivery)
        
        # Trim history to last 1000 deliveries
        if len(self._delivery_history) > 1000:
            self._delivery_history = self._delivery_history[-1000:]
        
        return delivery
    
    async def _deliver(self, delivery: WebhookDelivery, webhook: WebhookRegistration):
        """Attempt to deliver a webhook."""
        delivery.attempts += 1
        delivery.last_attempt_at = datetime.utcnow()
        delivery.status = DeliveryStatus.RETRYING if delivery.attempts > 1 else DeliveryStatus.PENDING
        
        try:
            # Build request
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-Delivery": delivery.delivery_id,
                "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
                **webhook.headers
            }
            
            body = json.dumps({
                "event": delivery.event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "delivery_id": delivery.delivery_id,
                "data": delivery.payload
            })
            
            # Add signature if secret is configured
            if webhook.secret:
                signature = self._compute_signature(body, webhook.secret)
                headers["X-Webhook-Signature"] = signature
            
            # Send request
            response = await self._http_client.post(
                webhook.url,
                headers=headers,
                content=body
            )
            
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:500] if response.text else None
            
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                delivery.delivered_at = datetime.utcnow()
                logger.info(f"Webhook delivered: {delivery.delivery_id} -> {webhook.url}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
            
        except Exception as e:
            delivery.error_message = str(e)[:500]
            logger.warning(f"Webhook delivery failed: {delivery.delivery_id} - {e}")
            
            if delivery.attempts < delivery.max_attempts:
                # Queue for retry
                self._pending_deliveries.append(delivery)
            else:
                delivery.status = DeliveryStatus.FAILED
                logger.error(f"Webhook permanently failed after {delivery.attempts} attempts: {delivery.delivery_id}")
    
    def _compute_signature(self, body: str, secret: str) -> str:
        """Compute HMAC-SHA256 signature for webhook verification."""
        return hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def _process_retries(self):
        """Background task to process retry queue."""
        while True:
            try:
                now = datetime.utcnow()
                to_retry = []
                still_pending = []
                
                for delivery in self._pending_deliveries:
                    if delivery.last_attempt_at:
                        delay = delivery.next_retry_delay()
                        elapsed = (now - delivery.last_attempt_at).total_seconds()
                        
                        if elapsed >= delay:
                            to_retry.append(delivery)
                        else:
                            still_pending.append(delivery)
                    else:
                        to_retry.append(delivery)
                
                self._pending_deliveries = still_pending
                
                # Process retries
                for delivery in to_retry:
                    webhook = self._webhooks.get(delivery.webhook_id)
                    if webhook:
                        await self._deliver(delivery, webhook)
                
            except Exception as e:
                logger.error(f"Retry processor error: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get delivery history."""
        deliveries = self._delivery_history
        
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        
        # Sort by created_at descending
        deliveries = sorted(deliveries, key=lambda d: d.created_at, reverse=True)[:limit]
        
        return [{
            "delivery_id": d.delivery_id,
            "webhook_id": d.webhook_id,
            "event_type": d.event_type,
            "status": d.status.value,
            "attempts": d.attempts,
            "created_at": d.created_at.isoformat(),
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            "response_code": d.response_code,
            "error_message": d.error_message
        } for d in deliveries]
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get a specific delivery by ID."""
        for delivery in self._delivery_history:
            if delivery.delivery_id == delivery_id:
                return delivery
        return None


# Global publisher instance
webhook_publisher = WebhookPublisher()
