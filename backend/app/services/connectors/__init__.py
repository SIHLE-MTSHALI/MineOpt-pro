"""
Connectors Package

Integration connectors for external systems:
- Fleet Management Systems (FMS)
- Lab Information Management Systems (LIMS)
- GPS/Survey data
- Webhook publishing
"""

from .base_connector import (
    BaseConnector,
    FMSConnector,
    ModularMiningConnector,
    WencoConnector,
    LIMSConnector,
    ConnectorConfig,
    ConnectorType,
    ConnectionStatus,
    ConnectorStatus,
    SyncResult,
    ConnectorRegistry,
    connector_registry,
    create_connector
)

from .webhook_publisher import (
    WebhookPublisher,
    WebhookRegistration,
    WebhookDelivery,
    WebhookEventType,
    DeliveryStatus,
    webhook_publisher
)

__all__ = [
    # Base classes
    'BaseConnector',
    'FMSConnector',
    'LIMSConnector',
    
    # Implementations
    'ModularMiningConnector',
    'WencoConnector',
    
    # Data classes
    'ConnectorConfig',
    'ConnectorType',
    'ConnectionStatus',
    'ConnectorStatus',
    'SyncResult',
    
    # Registry
    'ConnectorRegistry',
    'connector_registry',
    'create_connector',
    
    # Webhooks
    'WebhookPublisher',
    'WebhookRegistration',
    'WebhookDelivery',
    'WebhookEventType',
    'DeliveryStatus',
    'webhook_publisher'
]
