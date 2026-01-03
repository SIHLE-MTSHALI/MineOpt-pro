"""
Service Layer Tests - Phase 11 Testing & QA

Unit tests for core services including:
- Quality/Blending Service
- Stockpile Service
- Schedule Engine
- Integration Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# =============================================================================
# Quality Service Tests
# =============================================================================

class TestQualityService:
    """Tests for QualityService."""
    
    def test_weighted_average_quality(self):
        """Test weighted average quality calculation."""
        from app.services.quality_service import QualityService
        
        service = QualityService(db=None)
        
        # Sample parcels with qualities
        parcels = [
            {"tonnes": 1000, "quality": {"CV": 22.0, "Ash": 12.0}},
            {"tonnes": 2000, "quality": {"CV": 24.0, "Ash": 10.0}},
        ]
        
        result = service.calculate_blend_quality(parcels)
        
        # Expected: (1000*22 + 2000*24) / 3000 = 23.33
        # Expected: (1000*12 + 2000*10) / 3000 = 10.67
        assert abs(result["CV"] - 23.33) < 0.1
        assert abs(result["Ash"] - 10.67) < 0.1
    
    def test_spec_compliance_check_pass(self):
        """Test spec compliance when within limits."""
        from app.services.quality_service import QualityService
        
        service = QualityService(db=None)
        
        quality = {"CV": 23.0, "Ash": 12.0}
        specs = [
            {"field": "CV", "min_value": 22.0, "max_value": None},
            {"field": "Ash", "min_value": None, "max_value": 14.0},
        ]
        
        result = service.check_spec_compliance(quality, specs)
        
        assert result["compliant"] == True
        assert len(result["violations"]) == 0
    
    def test_spec_compliance_check_fail(self):
        """Test spec compliance when outside limits."""
        from app.services.quality_service import QualityService
        
        service = QualityService(db=None)
        
        quality = {"CV": 20.0, "Ash": 16.0}  # Below CV min, above Ash max
        specs = [
            {"field": "CV", "min_value": 22.0, "max_value": None},
            {"field": "Ash", "min_value": None, "max_value": 14.0},
        ]
        
        result = service.check_spec_compliance(quality, specs)
        
        assert result["compliant"] == False
        assert len(result["violations"]) == 2


# =============================================================================
# Blending Service Tests
# =============================================================================

class TestBlendingService:
    """Tests for BlendingService."""
    
    def test_calculate_blend_quality(self):
        """Test multi-source blend quality calculation."""
        from app.services.blending_service import BlendingService
        
        service = BlendingService()
        
        sources = [
            {"tonnes": 500, "quality": {"CV": 20.0, "Ash": 15.0}},
            {"tonnes": 500, "quality": {"CV": 26.0, "Ash": 9.0}},
        ]
        
        result = service.calculate_blend(sources)
        
        # 50/50 blend should average
        assert abs(result["blend_quality"]["CV"] - 23.0) < 0.1
        assert abs(result["blend_quality"]["Ash"] - 12.0) < 0.1
        assert result["total_tonnes"] == 1000
    
    def test_find_optimal_blend(self):
        """Test finding optimal blend ratios."""
        from app.services.blending_service import BlendingService
        
        service = BlendingService()
        
        sources = [
            {"id": "src1", "available_tonnes": 1000, "quality": {"CV": 20.0, "Ash": 18.0}},
            {"id": "src2", "available_tonnes": 1000, "quality": {"CV": 26.0, "Ash": 8.0}},
        ]
        
        specs = [
            {"field": "CV", "min_value": 22.0},
            {"field": "Ash", "max_value": 14.0},
        ]
        
        result = service.find_optimal_blend(sources, specs, target_tonnes=500)
        
        assert result is not None
        assert result["feasible"] == True


# =============================================================================
# Stock pile Service Tests
# =============================================================================

class TestStockpileService:
    """Tests for StockpileService."""
    
    def test_stockpile_state_dataclass(self):
        """Test StockpileState dataclass exists and has required fields."""
        from app.services.stockpile_service import StockpileState
        
        state = StockpileState(
            node_id="node-1",
            name="ROM Pad A",
            current_tonnes=10000,
            current_quality={"CV": 22.0, "Ash": 12.0},
            capacity_tonnes=50000,
            utilization_percent=20.0,
            parcel_count=0,
            inventory_method="Aggregate"
        )
        
        assert state.node_id == "node-1"
        assert state.current_tonnes == 10000
        assert state.utilization_percent == 20.0
    
    def test_reclaim_result_dataclass(self):
        """Test ReclaimResult dataclass exists and has required fields."""
        from app.services.stockpile_service import ReclaimResult
        
        result = ReclaimResult(
            reclaimed_tonnes=1000,
            reclaimed_quality={"CV": 23.0},
            remaining_tonnes=9000,
            remaining_quality={"CV": 23.0},
            parcels_used=[],
            warnings=[]
        )
        
        assert result.reclaimed_tonnes == 1000
        assert result.remaining_tonnes == 9000
    
    def test_balance_record_dataclass(self):
        """Test BalanceRecord dataclass exists and has required fields."""
        from app.services.stockpile_service import BalanceRecord
        
        record = BalanceRecord(
            period_id="P1",
            opening_tonnes=1000,
            additions_tonnes=500,
            reclaim_tonnes=200,
            closing_tonnes=1300,
            closing_quality={"CV": 22.0}
        )
        
        assert record.opening_tonnes + record.additions_tonnes - record.reclaim_tonnes == record.closing_tonnes
    
    def test_service_instantiation(self):
        """Test StockpileService can be instantiated with a db session."""
        from app.services.stockpile_service import StockpileService
        
        mock_db = Mock()
        service = StockpileService(mock_db)
        
        assert service.db == mock_db



# =============================================================================
# Integration Service Tests
# =============================================================================

class TestIntegrationService:
    """Tests for IntegrationService."""
    
    def test_idempotent_import(self):
        """Test that duplicate imports are detected."""
        from app.services.integration_service import IntegrationService, ImportStatus
        
        mock_db = Mock()
        service = IntegrationService(mock_db)
        
        records = [
            {"equipment_id": "EX-01", "period_id": "P1", "actual_tonnes": 5000}
        ]
        
        # First import should succeed
        result1 = service.import_actual_tonnes(records, "FMS")
        assert result1.status != ImportStatus.DUPLICATE
        
        # Second identical import should be marked as duplicate
        result2 = service.import_actual_tonnes(records, "FMS")
        assert result2.status == ImportStatus.DUPLICATE
    
    def test_hash_computation(self):
        """Test hash computation for duplicate detection."""
        from app.services.integration_service import IntegrationService
        
        mock_db = Mock()
        service = IntegrationService(mock_db)
        
        data1 = {"key": "value", "number": 123}
        data2 = {"key": "value", "number": 123}
        data3 = {"key": "different", "number": 123}
        
        hash1 = service._compute_hash(data1)
        hash2 = service._compute_hash(data2)
        hash3 = service._compute_hash(data3)
        
        assert hash1 == hash2  # Same data, same hash
        assert hash1 != hash3  # Different data, different hash


# =============================================================================
# Audit Service Tests
# =============================================================================

class TestAuditService:
    """Tests for AuditService."""
    
    def test_log_create_action(self):
        """Test logging a create action."""
        from app.services.audit_service import AuditService, AuditAction
        
        service = AuditService()
        
        log_id = service.log_create(
            user_id="user-001",
            username="testuser",
            entity_type="ScheduleVersion",
            entity_id="sched-001",
            entity_data={"name": "Test Schedule"},
            entity_name="Test Schedule"
        )
        
        assert log_id is not None
        
        # Verify log was recorded
        logs = service.get_entity_history("ScheduleVersion", "sched-001")
        assert len(logs) == 1
        assert logs[0]["action"] == "create"
    
    def test_log_update_with_diff(self):
        """Test logging an update with before/after values."""
        from app.services.audit_service import AuditService
        
        service = AuditService()
        
        log_id = service.log_update(
            user_id="user-001",
            username="testuser",
            entity_type="Resource",
            entity_id="res-001",
            previous_values={"rate": 1000, "name": "Old Name"},
            new_values={"rate": 1200, "name": "Old Name"},
            reason="Performance improvement"
        )
        
        assert log_id is not None
        
        logs = service.get_entity_history("Resource", "res-001")
        assert len(logs) == 1
        assert "rate" in logs[0]["changes"]
        assert logs[0]["changes"]["rate"]["from"] == 1000
        assert logs[0]["changes"]["rate"]["to"] == 1200
    
    def test_audit_statistics(self):
        """Test audit statistics calculation."""
        from app.services.audit_service import AuditService, AuditAction
        
        service = AuditService()
        
        # Create some log entries
        service.log_create("u1", "user1", "Type1", "id1", {})
        service.log_create("u1", "user1", "Type2", "id2", {})
        service.log_update("u2", "user2", "Type1", "id1", {"a": 1}, {"a": 2})
        
        stats = service.get_statistics()
        
        assert stats["total_entries"] == 3
        assert stats["by_action"]["create"] == 2
        assert stats["by_action"]["update"] == 1


# =============================================================================
# Security Service Tests
# =============================================================================

class TestSecurityService:
    """Tests for SecurityService."""
    
    def test_role_permissions(self):
        """Test that roles have correct permissions."""
        from app.services.security_service import RBACService, Role, Permission
        
        service = RBACService()
        
        viewer_perms = service.get_user_permissions(Role.VIEWER)
        admin_perms = service.get_user_permissions(Role.ADMIN)
        
        # Viewer should have view permissions only
        assert Permission.VIEW_SCHEDULE in viewer_perms
        assert Permission.EDIT_SCHEDULE not in viewer_perms
        
        # Admin should have most permissions
        assert Permission.EDIT_SCHEDULE in admin_perms
        assert Permission.MANAGE_USERS in admin_perms
    
    def test_permission_check(self):
        """Test permission checking."""
        from app.services.security_service import RBACService, Role, Permission
        
        service = RBACService()
        
        user = service.create_user_context(
            user_id="u1",
            username="planner1",
            email="planner@test.com",
            role="planner",
            site_ids=["site-1", "site-2"]
        )
        
        assert service.check_permission(user, Permission.VIEW_SCHEDULE) == True
        assert service.check_permission(user, Permission.EDIT_SCHEDULE) == True
        assert service.check_permission(user, Permission.MANAGE_USERS) == False
    
    def test_site_access_check(self):
        """Test site-level access scoping."""
        from app.services.security_service import RBACService, Role
        
        service = RBACService()
        
        user = service.create_user_context(
            user_id="u1",
            username="user1",
            email="user@test.com",
            role="planner",
            site_ids=["site-1", "site-2"]
        )
        
        assert service.check_site_access(user, "site-1") == True
        assert service.check_site_access(user, "site-3") == False


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
