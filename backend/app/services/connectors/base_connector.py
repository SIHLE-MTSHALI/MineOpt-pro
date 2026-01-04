"""
Integration Connector Framework

Abstract base for external system integrations:
- Fleet Management Systems (Modular Mining, Wenco, Caterpillar)
- GPS/Survey data streaming
- Lab Information Management Systems (LIMS)
- Webhook publishing

Each connector implements a common interface for:
- Connection testing
- Data synchronization
- Status monitoring
- Error handling
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    """Supported connector types."""
    FMS = "fms"  # Fleet Management System
    GPS = "gps"  # GPS/Survey Data
    LIMS = "lims"  # Lab Information Management
    ERP = "erp"  # Enterprise Resource Planning
    WEBHOOK = "webhook"  # Outbound webhooks


class ConnectionStatus(str, Enum):
    """Connector connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"


@dataclass
class ConnectorConfig:
    """Base configuration for connectors."""
    connector_id: str
    connector_type: ConnectorType
    name: str
    enabled: bool = True
    site_id: Optional[str] = None
    
    # Connection settings
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Should be encrypted in storage
    
    # Sync settings
    sync_interval_seconds: int = 300  # 5 minutes default
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    connector_id: str
    sync_type: str  # 'pull', 'push', 'full'
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    def complete(self, success: bool = True, error: str = None):
        """Mark sync as complete."""
        self.completed_at = datetime.utcnow()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        self.success = success
        if error:
            self.error_message = error


@dataclass
class ConnectorStatus:
    """Current status of a connector."""
    connector_id: str
    status: ConnectionStatus
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class for all integration connectors.
    
    Subclasses must implement:
    - test_connection()
    - sync_data()
    - get_status()
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectionStatus.DISCONNECTED
        self._last_sync: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._sync_history: List[SyncResult] = []
    
    @property
    def connector_id(self) -> str:
        return self.config.connector_id
    
    @property
    def connector_type(self) -> ConnectorType:
        return self.config.connector_type
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the external system.
        Returns True if connection is successful.
        """
        pass
    
    @abstractmethod
    async def sync_data(self, sync_type: str = 'full') -> SyncResult:
        """
        Synchronize data with the external system.
        
        Args:
            sync_type: 'pull' (inbound), 'push' (outbound), or 'full' (both)
        
        Returns:
            SyncResult with details of the operation
        """
        pass
    
    def get_status(self) -> ConnectorStatus:
        """Get current connector status."""
        return ConnectorStatus(
            connector_id=self.connector_id,
            status=self._status,
            last_sync=self._last_sync,
            last_error=self._last_error,
            metrics={
                'total_syncs': len(self._sync_history),
                'successful_syncs': len([s for s in self._sync_history if s.success]),
                'failed_syncs': len([s for s in self._sync_history if not s.success])
            }
        )
    
    async def connect(self):
        """Establish connection to the external system."""
        self._status = ConnectionStatus.CONNECTING
        try:
            success = await self.test_connection()
            self._status = ConnectionStatus.CONNECTED if success else ConnectionStatus.ERROR
            return success
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            self._last_error = str(e)
            logger.error(f"Connector {self.connector_id} connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the external system."""
        self._status = ConnectionStatus.DISCONNECTED
    
    def _record_sync(self, result: SyncResult):
        """Record a sync result in history."""
        self._sync_history.append(result)
        self._last_sync = result.completed_at
        if not result.success:
            self._last_error = result.error_message
        # Keep only last 100 sync records
        if len(self._sync_history) > 100:
            self._sync_history = self._sync_history[-100:]


class FMSConnector(BaseConnector):
    """
    Fleet Management System connector base class.
    
    Handles:
    - Equipment positions and status
    - Load/haul cycle data
    - Operator assignments
    - Delay/downtime events
    """
    
    async def test_connection(self) -> bool:
        """Test FMS API connection."""
        # Subclasses should implement actual API test
        logger.info(f"Testing FMS connection: {self.config.base_url}")
        return True
    
    async def sync_data(self, sync_type: str = 'pull') -> SyncResult:
        """Sync equipment and cycle data from FMS."""
        result = SyncResult(
            connector_id=self.connector_id,
            sync_type=sync_type
        )
        
        try:
            if sync_type in ('pull', 'full'):
                # Pull equipment positions
                await self._sync_equipment_positions(result)
                
                # Pull cycle data
                await self._sync_cycle_data(result)
                
                # Pull delay events
                await self._sync_delay_events(result)
            
            if sync_type in ('push', 'full'):
                # Push schedule assignments
                await self._push_assignments(result)
            
            result.complete(success=True)
            
        except Exception as e:
            result.complete(success=False, error=str(e))
            logger.error(f"FMS sync failed: {e}")
        
        self._record_sync(result)
        return result
    
    async def _sync_equipment_positions(self, result: SyncResult):
        """Pull current equipment positions."""
        # Subclass implements actual API call
        pass
    
    async def _sync_cycle_data(self, result: SyncResult):
        """Pull load/haul cycle data."""
        pass
    
    async def _sync_delay_events(self, result: SyncResult):
        """Pull delay and downtime events."""
        pass
    
    async def _push_assignments(self, result: SyncResult):
        """Push schedule assignments to FMS."""
        pass


class ModularMiningConnector(FMSConnector):
    """
    Modular Mining (Caterpillar) MineStar connector.
    
    Implements the Modular Mining API for:
    - Equipment tracking
    - Assignment dispatch
    - Production tracking
    """
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.api_version = config.custom_settings.get('api_version', 'v2')
    
    async def test_connection(self) -> bool:
        """Test Modular Mining API connection."""
        # Would implement actual API call
        logger.info(f"Testing Modular Mining connection: {self.config.base_url}")
        
        # Simulated test - replace with actual API call
        if not self.config.base_url or not self.config.api_key:
            return False
        
        return True
    
    async def _sync_equipment_positions(self, result: SyncResult):
        """Pull equipment positions from MineStar."""
        # Implementation would call MineStar API
        # GET /api/v2/equipment/positions
        logger.info("Syncing equipment positions from Modular Mining")
        result.records_processed += 10  # Placeholder


class WencoConnector(FMSConnector):
    """
    Wenco International Mining Systems connector.
    
    Implements the Wenco API for:
    - Fleet tracking
    - Production monitoring
    - Dispatch integration
    """
    
    async def test_connection(self) -> bool:
        """Test Wenco API connection."""
        logger.info(f"Testing Wenco connection: {self.config.base_url}")
        
        if not self.config.base_url:
            return False
        
        return True
    
    async def _sync_equipment_positions(self, result: SyncResult):
        """Pull equipment positions from Wenco."""
        logger.info("Syncing equipment positions from Wenco")
        result.records_processed += 10


class LIMSConnector(BaseConnector):
    """
    Lab Information Management System connector.
    
    Handles:
    - Sample result import
    - Quality vector updates
    - Sample-to-parcel mapping
    """
    
    async def test_connection(self) -> bool:
        """Test LIMS connection."""
        logger.info(f"Testing LIMS connection: {self.config.base_url}")
        return True
    
    async def sync_data(self, sync_type: str = 'pull') -> SyncResult:
        """Sync lab results from LIMS."""
        result = SyncResult(
            connector_id=self.connector_id,
            sync_type=sync_type
        )
        
        try:
            if sync_type in ('pull', 'full'):
                await self._import_lab_results(result)
            
            result.complete(success=True)
            
        except Exception as e:
            result.complete(success=False, error=str(e))
        
        self._record_sync(result)
        return result
    
    async def _import_lab_results(self, result: SyncResult):
        """Import lab results and update quality vectors."""
        # Implementation would:
        # 1. Fetch new results from LIMS API
        # 2. Map sample IDs to parcels/activity areas
        # 3. Update quality vectors
        # 4. Handle revised results
        logger.info("Importing lab results from LIMS")


class ConnectorRegistry:
    """
    Registry for managing multiple connectors.
    
    Provides:
    - Connector registration and lookup
    - Scheduled sync management
    - Status aggregation
    """
    
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._sync_tasks: Dict[str, asyncio.Task] = {}
    
    def register(self, connector: BaseConnector):
        """Register a connector."""
        self._connectors[connector.connector_id] = connector
        logger.info(f"Registered connector: {connector.connector_id}")
    
    def unregister(self, connector_id: str):
        """Unregister a connector."""
        if connector_id in self._connectors:
            del self._connectors[connector_id]
            if connector_id in self._sync_tasks:
                self._sync_tasks[connector_id].cancel()
                del self._sync_tasks[connector_id]
    
    def get(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector by ID."""
        return self._connectors.get(connector_id)
    
    def list_connectors(self) -> List[ConnectorStatus]:
        """Get status of all registered connectors."""
        return [c.get_status() for c in self._connectors.values()]
    
    async def start_scheduled_syncs(self):
        """Start scheduled sync tasks for all enabled connectors."""
        for connector_id, connector in self._connectors.items():
            if connector.config.enabled:
                self._sync_tasks[connector_id] = asyncio.create_task(
                    self._run_scheduled_sync(connector)
                )
    
    async def _run_scheduled_sync(self, connector: BaseConnector):
        """Run scheduled sync for a connector."""
        while True:
            try:
                await connector.sync_data()
            except Exception as e:
                logger.error(f"Scheduled sync failed for {connector.connector_id}: {e}")
            
            await asyncio.sleep(connector.config.sync_interval_seconds)
    
    async def stop_all(self):
        """Stop all scheduled syncs."""
        for task in self._sync_tasks.values():
            task.cancel()
        self._sync_tasks.clear()


# Global registry instance
connector_registry = ConnectorRegistry()


def create_connector(config: ConnectorConfig) -> BaseConnector:
    """Factory function to create connectors based on type."""
    if config.connector_type == ConnectorType.FMS:
        vendor = config.custom_settings.get('vendor', 'modular')
        if vendor == 'modular':
            return ModularMiningConnector(config)
        elif vendor == 'wenco':
            return WencoConnector(config)
        else:
            raise ValueError(f"Unknown FMS vendor: {vendor}")
    
    elif config.connector_type == ConnectorType.LIMS:
        return LIMSConnector(config)
    
    else:
        raise ValueError(f"Unknown connector type: {config.connector_type}")
