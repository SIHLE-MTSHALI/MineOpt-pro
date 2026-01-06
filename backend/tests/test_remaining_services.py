"""
CP Solver and Additional Services Tests

Tests for:
- Constraint Programming solver
- Auto-layout algorithm
- Report scheduler
- Credential vault
"""

import pytest
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# =============================================================================
# CP Solver Tests
# =============================================================================

class TestCPSolver:
    """Tests for Constraint Programming solver."""
    
    def test_variable_domain(self):
        """Test variable creation with domain."""
        from app.services.cp_solver import Variable
        
        var = Variable(name="x", domain={1, 2, 3, 4, 5})
        
        assert var.domain_size == 5
        assert not var.is_assigned
        
        var.assign(3)
        assert var.is_assigned
        assert var.assigned_value == 3
    
    def test_variable_domain_reduction(self):
        """Test removing values from domain."""
        from app.services.cp_solver import Variable
        
        var = Variable(name="x", domain={1, 2, 3, 4, 5})
        
        empty = var.remove_value(3)
        assert not empty
        assert 3 not in var.domain
        assert var.domain_size == 4
    
    def test_precedence_constraint(self):
        """Test precedence constraint satisfaction."""
        from app.services.cp_solver import Constraint, ConstraintType
        
        constraint = Constraint(
            constraint_type=ConstraintType.PRECEDENCE,
            variables=["A", "B"]
        )
        
        # A before B - satisfied
        assert constraint.is_satisfied({"A": 1, "B": 2})
        
        # B before A - not satisfied
        assert not constraint.is_satisfied({"A": 2, "B": 1})
        
        # Same time - not satisfied
        assert not constraint.is_satisfied({"A": 1, "B": 1})
    
    def test_alldifferent_constraint(self):
        """Test all-different constraint."""
        from app.services.cp_solver import Constraint, ConstraintType
        
        constraint = Constraint(
            constraint_type=ConstraintType.ALLDIFFERENT,
            variables=["A", "B", "C"]
        )
        
        # All different - satisfied
        assert constraint.is_satisfied({"A": 1, "B": 2, "C": 3})
        
        # Duplicate - not satisfied
        assert not constraint.is_satisfied({"A": 1, "B": 1, "C": 3})
    
    def test_solver_simple_problem(self):
        """Test solving a simple problem."""
        from app.services.cp_solver import CPSolverService, ConstraintType
        
        solver = CPSolverService()
        solver.add_variable("task1", {1, 2, 3})
        solver.add_variable("task2", {1, 2, 3})
        solver.add_constraint(ConstraintType.PRECEDENCE, ["task1", "task2"])
        
        solution = solver.solve(time_limit=5.0)
        
        assert solution is not None
        assert solution.assignments["task1"] < solution.assignments["task2"]
    
    def test_solver_with_objective(self):
        """Test optimization objective."""
        from app.services.cp_solver import CPSolverService, ConstraintType
        
        solver = CPSolverService()
        solver.add_variable("x", {1, 2, 3, 4, 5})
        solver.add_variable("y", {1, 2, 3, 4, 5})
        solver.add_constraint(ConstraintType.PRECEDENCE, ["x", "y"])
        solver.set_objective("y", "min")
        
        solution = solver.solve(time_limit=5.0)
        
        assert solution is not None
        assert solution.assignments["y"] == 2  # Minimum valid value (x=1, y=2)
    
    def test_solution_enumeration(self):
        """Test finding multiple solutions."""
        from app.services.cp_solver import CPSolverService, ConstraintType
        
        solver = CPSolverService()
        solver.add_variable("x", {1, 2})
        solver.add_variable("y", {1, 2})
        solver.add_constraint(ConstraintType.ALLDIFFERENT, ["x", "y"])
        
        solutions = solver.enumerate_solutions(max_solutions=10)
        
        assert len(solutions) == 2  # (1,2) and (2,1)
    
    def test_domain_propagation(self):
        """Test arc consistency propagation."""
        from app.services.cp_solver import CPSolverService, ConstraintType
        
        solver = CPSolverService()
        solver.add_variable("A", {1, 2, 3})
        solver.add_variable("B", {1, 2})
        solver.add_constraint(ConstraintType.PRECEDENCE, ["A", "B"])
        
        result = solver.domain_propagation()
        
        assert result  # Should not fail
        # A must be 1 (only value < all B values)
        assert 1 in solver.variables["A"].domain
    
    def test_mining_sequence_constraint(self):
        """Test mining-specific constraint builder."""
        from app.services.cp_solver import CPSolverService
        
        blocks = ["block1", "block2", "block3"]
        constraints = CPSolverService.create_mining_sequence_constraint(blocks, [])
        
        assert len(constraints) == 2  # block1->block2, block2->block3


# =============================================================================
# Auto-Layout Tests
# =============================================================================

class TestAutoLayout:
    """Tests for auto-layout algorithms."""
    
    def test_hierarchical_layout(self):
        """Test hierarchical layout."""
        from app.services.auto_layout import AutoLayoutService
        
        service = AutoLayoutService()
        
        nodes = [
            {'node_id': 'source1'},
            {'node_id': 'process1'},
            {'node_id': 'sink1'}
        ]
        edges = [
            {'source_node_id': 'source1', 'target_node_id': 'process1'},
            {'source_node_id': 'process1', 'target_node_id': 'sink1'}
        ]
        
        result = service.hierarchical_layout(nodes, edges)
        
        assert len(result.positions) == 3
        assert result.algorithm == 'hierarchical'
        
        # Sources should be leftmost
        source_pos = next(p for p in result.positions if p.node_id == 'source1')
        sink_pos = next(p for p in result.positions if p.node_id == 'sink1')
        assert source_pos.x < sink_pos.x
    
    def test_grid_layout(self):
        """Test grid layout."""
        from app.services.auto_layout import AutoLayoutService
        
        service = AutoLayoutService()
        
        nodes = [{'node_id': f'n{i}'} for i in range(6)]
        
        result = service.grid_layout(nodes, columns=3)
        
        assert len(result.positions) == 6
        assert result.algorithm == 'grid'
        
        # Should have 2 rows of 3
        row1 = [p for p in result.positions if p.y == result.positions[0].y]
        assert len(row1) == 3
    
    def test_force_directed_layout(self):
        """Test force-directed layout."""
        from app.services.auto_layout import AutoLayoutService
        
        service = AutoLayoutService()
        
        nodes = [
            {'node_id': 'a'},
            {'node_id': 'b'},
            {'node_id': 'c'}
        ]
        edges = [
            {'source_node_id': 'a', 'target_node_id': 'b'},
            {'source_node_id': 'b', 'target_node_id': 'c'}
        ]
        
        result = service.force_directed_layout(nodes, edges, iterations=20)
        
        assert len(result.positions) == 3
        assert result.algorithm == 'force_directed'
        
        # All nodes should have different positions
        positions = [(p.x, p.y) for p in result.positions]
        assert len(set(positions)) == 3


# =============================================================================
# Report Scheduler Tests
# =============================================================================

class TestReportScheduler:
    """Tests for report scheduling."""
    
    def test_create_schedule(self):
        """Test schedule creation."""
        from app.services.report_scheduler import ReportScheduler, ScheduleFrequency
        
        scheduler = ReportScheduler()
        
        schedule = scheduler.create_schedule(
            schedule_id="sched1",
            name="Daily Summary",
            report_type="daily_summary",
            schedule_version_id="sv1",
            frequency=ScheduleFrequency.DAILY,
            delivery_emails=["user@example.com"],
            run_hour=8
        )
        
        assert schedule.schedule_id == "sched1"
        assert schedule.frequency == ScheduleFrequency.DAILY
        assert schedule.next_run is not None
    
    def test_calculate_next_run_daily(self):
        """Test daily next run calculation."""
        from app.services.report_scheduler import ReportScheduler, ScheduleFrequency
        
        scheduler = ReportScheduler()
        
        next_run = scheduler._calculate_next_run(
            ScheduleFrequency.DAILY,
            run_hour=6,
            run_day_of_week=0,
            run_day_of_month=1
        )
        
        assert next_run is not None
        assert next_run.hour == 6
        assert next_run > datetime.now()
    
    def test_list_schedules(self):
        """Test schedule listing."""
        from app.services.report_scheduler import ReportScheduler, ScheduleFrequency
        
        scheduler = ReportScheduler()
        
        scheduler.create_schedule(
            schedule_id="s1", name="Report 1", report_type="daily_summary",
            schedule_version_id="sv1", frequency=ScheduleFrequency.DAILY,
            delivery_emails=[]
        )
        scheduler.create_schedule(
            schedule_id="s2", name="Report 2", report_type="shift_plan",
            schedule_version_id="sv1", frequency=ScheduleFrequency.WEEKLY,
            delivery_emails=[]
        )
        
        schedules = scheduler.list_schedules()
        
        assert len(schedules) == 2
    
    def test_delete_schedule(self):
        """Test schedule deletion."""
        from app.services.report_scheduler import ReportScheduler, ScheduleFrequency
        
        scheduler = ReportScheduler()
        
        scheduler.create_schedule(
            schedule_id="s1", name="Report", report_type="daily_summary",
            schedule_version_id="sv1", frequency=ScheduleFrequency.DAILY,
            delivery_emails=[]
        )
        
        assert scheduler.delete_schedule("s1")
        assert scheduler.get_schedule("s1") is None


# =============================================================================
# Credential Vault Tests (Additional)
# =============================================================================

class TestCredentialVaultAdditional:
    """Additional tests for credential vault."""
    
    def test_credential_expiration(self):
        """Test credential expiration."""
        from app.services.credential_vault import CredentialVault
        
        vault = CredentialVault()
        
        # Create credential that expires in 1 day
        vault.store_credential(
            credential_id="exp1",
            name="Expiring Cred",
            connector_type="test",
            credential_data={"key": "value"},
            expires_days=1
        )
        
        cred = vault.get_credential("exp1")
        assert cred is not None
        
        # Check expiring credentials
        expiring = vault.get_expiring_credentials(days=7)
        assert len(expiring) == 1
    
    def test_deactivate_credential(self):
        """Test credential deactivation."""
        from app.services.credential_vault import CredentialVault
        
        vault = CredentialVault()
        
        vault.store_credential(
            credential_id="deact1",
            name="Test Cred",
            connector_type="test",
            credential_data={"key": "value"}
        )
        
        assert vault.deactivate_credential("deact1")
        assert vault.get_credential("deact1") is None
        
        assert vault.reactivate_credential("deact1")
        assert vault.get_credential("deact1") is not None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
