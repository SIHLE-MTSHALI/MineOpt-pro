"""
API Endpoint Tests - Phase 11 Testing & QA

Tests for FastAPI endpoints using TestClient.
Covers all major routers.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test that the health check endpoint returns OK."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


# =============================================================================
# Config Router Tests
# =============================================================================

class TestConfigRouter:
    """Tests for configuration endpoints."""
    
    def test_get_sites(self, client):
        """Test getting list of sites."""
        response = client.get("/config/sites")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_material_types(self, client):
        """Test getting material types."""
        response = client.get("/config/material-types")
        
        assert response.status_code == 200


# =============================================================================
# Calendar Router Tests
# =============================================================================

class TestCalendarRouter:
    """Tests for calendar endpoints."""
    
    def test_get_calendars(self, client):
        """Test getting list of calendars."""
        response = client.get("/calendar/calendars")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_calendar(self, client):
        """Test creating a new calendar."""
        payload = {
            "name": "Test Calendar",
            "site_id": "site-001",
            "period_type": "Weekly"
        }
        
        response = client.post("/calendar/calendars", json=payload)
        
        # May fail if site doesn't exist, but should not error
        assert response.status_code in [200, 201, 400, 422]


# =============================================================================
# Schedule Router Tests
# =============================================================================

class TestScheduleRouter:
    """Tests for schedule endpoints."""
    
    def test_get_schedules(self, client):
        """Test getting list of schedule versions."""
        response = client.get("/schedule/versions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_schedule_version(self, client):
        """Test creating a new schedule version."""
        payload = {
            "name": "Test Schedule",
            "description": "Test schedule for API testing",
            "site_id": "site-001"
        }
        
        response = client.post("/schedule/versions", json=payload)
        
        # Should accept the request format
        assert response.status_code in [200, 201, 400, 422]


# =============================================================================
# Optimization Router Tests
# =============================================================================

class TestOptimizationRouter:
    """Tests for optimization endpoints."""
    
    def test_get_optimization_status(self, client):
        """Test getting optimization run status."""
        response = client.get("/optimization/status/run-001")
        
        # Should return status or not found
        assert response.status_code in [200, 404]
    
    def test_fast_pass_endpoint_exists(self, client):
        """Test that fast pass endpoint exists."""
        payload = {
            "schedule_version_id": "test-001",
            "calendar_id": "cal-001"
        }
        
        response = client.post("/optimization/fast-pass", json=payload)
        
        # Should accept the request format
        assert response.status_code in [200, 400, 404, 422]


# =============================================================================
# Quality Router Tests
# =============================================================================

class TestQualityRouter:
    """Tests for quality endpoints."""
    
    def test_get_quality_fields(self, client):
        """Test getting quality field definitions."""
        response = client.get("/quality/fields")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_calculate_blend(self, client):
        """Test blend calculation endpoint."""
        payload = {
            "sources": [
                {"tonnes": 1000, "quality": {"CV": 22.0, "Ash": 12.0}},
                {"tonnes": 1000, "quality": {"CV": 24.0, "Ash": 10.0}}
            ]
        }
        
        response = client.post("/quality/calculate-blend", json=payload)
        
        assert response.status_code in [200, 422]


# =============================================================================
# Stockpile Router Tests
# =============================================================================

class TestStockpileRouter:
    """Tests for stockpile endpoints."""
    
    def test_get_stockpiles(self, client):
        """Test getting list of stockpiles."""
        response = client.get("/stockpiles")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# =============================================================================
# Integration Router Tests
# =============================================================================

class TestIntegrationRouter:
    """Tests for integration endpoints."""
    
    def test_import_actual_tonnes(self, client):
        """Test importing actual tonnes."""
        payload = {
            "source_system": "FMS",
            "records": [
                {
                    "equipment_id": "EX-01",
                    "period_id": "P-001",
                    "actual_tonnes": 5000.0
                }
            ]
        }
        
        response = client.post("/integration/fleet/actual-tonnes", json=payload)
        
        assert response.status_code in [200, 422]
    
    def test_import_history(self, client):
        """Test getting import history."""
        response = client.get("/integration/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "records" in data


# =============================================================================
# Security Router Tests
# =============================================================================

class TestSecurityRouter:
    """Tests for security endpoints."""
    
    def test_get_roles(self, client):
        """Test getting list of roles."""
        response = client.get("/security/roles")
        
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
    
    def test_get_permissions(self, client):
        """Test getting list of permissions."""
        response = client.get("/security/permissions")
        
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
    
    def test_get_role_permissions(self, client):
        """Test getting permissions for a specific role."""
        response = client.get("/security/roles/planner/permissions")
        
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
    
    def test_check_permission(self, client):
        """Test permission check endpoint."""
        payload = {
            "user_id": "user-001",
            "username": "testuser",
            "role": "planner",
            "permission": "view:schedule"
        }
        
        response = client.post("/security/check-permission", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
    
    def test_get_audit_logs(self, client):
        """Test getting audit logs."""
        response = client.get("/security/audit/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data


# =============================================================================
# Reporting Router Tests
# =============================================================================

class TestReportingRouter:
    """Tests for reporting endpoints."""
    
    def test_get_report_types(self, client):
        """Test getting available report types."""
        response = client.get("/reporting/types")
        
        assert response.status_code == 200
        data = response.json()
        assert "report_types" in data


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/invalid/endpoint/that/does/not/exist")
        
        assert response.status_code == 404
    
    def test_invalid_json_payload(self, client):
        """Test that invalid JSON payloads are handled."""
        response = client.post(
            "/integration/fleet/actual-tonnes",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test that missing required fields return validation error."""
        payload = {
            # Missing required fields
        }
        
        response = client.post("/integration/fleet/actual-tonnes", json=payload)
        
        assert response.status_code == 422


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
