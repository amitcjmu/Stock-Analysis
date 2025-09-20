"""
Tests for Flow State Machine

Comprehensive test suite covering:
- State transition validation
- Progress calculation
- Error handling and recovery
- Phase order enforcement
- Edge cases and rollback scenarios

🔧 CC: Tests for enhanced state machine addressing PR #374 issues
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from app.services.flow_state_machine import (
    FlowStateMachine,
    PhaseState,
    FlowStatus,
    PhaseTransition,
    FlowTransitionError
)


class TestFlowStateMachine:
    """Test suite for FlowStateMachine class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.state_machine = FlowStateMachine()

    def test_initial_state_machine_setup(self):
        """Test initial state machine configuration"""
        assert len(self.state_machine.PHASES) == 5
        assert sum(self.state_machine.PHASE_WEIGHTS.values()) == 100.0
        assert len(self.state_machine.transition_history) == 0

    def test_valid_phase_transitions(self):
        """Test valid phase state transitions"""
        # Test starting a phase
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.NOT_STARTED, PhaseState.IN_PROGRESS
        )
        assert is_valid
        assert error is None

        # Test completing a phase
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.IN_PROGRESS, PhaseState.COMPLETED
        )
        assert is_valid
        assert error is None

        # Test phase failure
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.IN_PROGRESS, PhaseState.FAILED
        )
        assert is_valid
        assert error is None

        # Test retry after failure
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.FAILED, PhaseState.RETRY_NEEDED
        )
        assert is_valid
        assert error is None

    def test_invalid_phase_transitions(self):
        """Test invalid phase state transitions"""
        # Test invalid phase name
        is_valid, error = self.state_machine.validate_phase_transition(
            "invalid_phase", PhaseState.NOT_STARTED, PhaseState.IN_PROGRESS
        )
        assert not is_valid
        assert error.error_code == "INVALID_PHASE"

        # Test invalid transition
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.NOT_STARTED, PhaseState.COMPLETED
        )
        assert not is_valid
        assert error.error_code == "INVALID_PHASE_TRANSITION"

        # Test transition from completed to in_progress (not allowed directly)
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.COMPLETED, PhaseState.IN_PROGRESS
        )
        assert not is_valid
        assert error.error_code == "INVALID_PHASE_TRANSITION"

    def test_valid_flow_transitions(self):
        """Test valid flow status transitions"""
        # Test normal progression
        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.INITIALIZED, FlowStatus.ACTIVE
        )
        assert is_valid
        assert error is None

        # Test pause/resume
        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.ACTIVE, FlowStatus.PAUSED
        )
        assert is_valid

        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.PAUSED, FlowStatus.ACTIVE
        )
        assert is_valid

        # Test error recovery
        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.FAILED, FlowStatus.ACTIVE
        )
        assert is_valid

    def test_invalid_flow_transitions(self):
        """Test invalid flow status transitions"""
        # Test invalid transition from completed
        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.COMPLETED, FlowStatus.ACTIVE
        )
        assert not is_valid
        assert error.error_code == "INVALID_FLOW_TRANSITION"

        # Test invalid transition from cancelled (terminal state)
        is_valid, error = self.state_machine.validate_flow_transition(
            FlowStatus.CANCELLED, FlowStatus.ACTIVE
        )
        assert not is_valid

    def test_progress_calculation(self):
        """Test progress calculation logic"""
        # Test initial state (all phases not started)
        phase_states = {
            "data_import": PhaseState.NOT_STARTED,
            "field_mapping": PhaseState.NOT_STARTED,
            "data_cleansing": PhaseState.NOT_STARTED,
            "asset_inventory": PhaseState.NOT_STARTED,
            "dependency_analysis": PhaseState.NOT_STARTED
        }
        progress = self.state_machine.calculate_progress(phase_states)
        assert progress == 0.0

        # Test one phase in progress
        phase_states["data_import"] = PhaseState.IN_PROGRESS
        progress = self.state_machine.calculate_progress(phase_states)
        assert progress == 6.0  # 20% * 0.3

        # Test one phase completed
        phase_states["data_import"] = PhaseState.COMPLETED
        progress = self.state_machine.calculate_progress(phase_states)
        assert progress == 20.0

        # Test all phases completed
        for phase in phase_states:
            phase_states[phase] = PhaseState.COMPLETED
        progress = self.state_machine.calculate_progress(phase_states)
        assert progress == 100.0

        # Test mixed states
        phase_states = {
            "data_import": PhaseState.COMPLETED,
            "field_mapping": PhaseState.IN_PROGRESS,
            "data_cleansing": PhaseState.NOT_STARTED,
            "asset_inventory": PhaseState.WAITING_APPROVAL,
            "dependency_analysis": PhaseState.FAILED
        }
        progress = self.state_machine.calculate_progress(phase_states)
        expected = 20.0 + (20.0 * 0.3) + 0 + (20.0 * 0.8) + 0  # 42.0
        assert progress == expected

    def test_flow_status_determination(self):
        """Test flow status determination based on phase states"""
        # Test initial state
        phase_states = {phase: PhaseState.NOT_STARTED for phase in self.state_machine.PHASES}
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.INITIALIZED)
        assert status == FlowStatus.INITIALIZED

        # Test all completed
        phase_states = {phase: PhaseState.COMPLETED for phase in self.state_machine.PHASES}
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.COMPLETED

        # Test with failures
        phase_states["data_import"] = PhaseState.FAILED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.FAILED

        # Test with retry needed
        phase_states["data_import"] = PhaseState.RETRY_NEEDED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.RETRY_PENDING

        # Test with waiting approval
        phase_states["data_import"] = PhaseState.WAITING_APPROVAL
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.WAITING_APPROVAL

        # Test progression through phases
        phase_states = {
            "data_import": PhaseState.COMPLETED,
            "field_mapping": PhaseState.NOT_STARTED,
            "data_cleansing": PhaseState.NOT_STARTED,
            "asset_inventory": PhaseState.NOT_STARTED,
            "dependency_analysis": PhaseState.NOT_STARTED
        }
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.DATA_GATHERING

    def test_phase_order_validation(self):
        """Test phase dependency order validation"""
        # Test valid order - starting first phase
        phase_states = {phase: PhaseState.NOT_STARTED for phase in self.state_machine.PHASES}
        is_valid, error = self.state_machine.validate_phase_order(
            phase_states, "data_import", PhaseState.IN_PROGRESS
        )
        assert is_valid
        assert error is None

        # Test invalid order - trying to start later phase without completing earlier ones
        is_valid, error = self.state_machine.validate_phase_order(
            phase_states, "field_mapping", PhaseState.IN_PROGRESS
        )
        assert not is_valid
        assert "data_import" in error

        # Test valid order - progressing after completing dependency
        phase_states["data_import"] = PhaseState.COMPLETED
        is_valid, error = self.state_machine.validate_phase_order(
            phase_states, "field_mapping", PhaseState.IN_PROGRESS
        )
        assert is_valid

    def test_transition_execution(self):
        """Test phase transition execution with audit trail"""
        # Execute a transition
        success, error = self.state_machine.transition_phase(
            phase="data_import",
            current_state=PhaseState.NOT_STARTED,
            target_state=PhaseState.IN_PROGRESS,
            reason="starting_phase",
            metadata={"user_action": True},
            user_id="test_user"
        )

        assert success
        assert error is None
        assert len(self.state_machine.transition_history) == 1

        transition = self.state_machine.transition_history[0]
        assert transition.phase == "data_import"
        assert transition.from_state == PhaseState.NOT_STARTED
        assert transition.to_state == PhaseState.IN_PROGRESS
        assert transition.reason == "starting_phase"
        assert transition.user_id == "test_user"
        assert transition.metadata["user_action"] is True

    def test_recovery_options(self):
        """Test recovery options generation"""
        # Test with failed phases
        phase_states = {
            "data_import": PhaseState.FAILED,
            "field_mapping": PhaseState.COMPLETED,
            "data_cleansing": PhaseState.RETRY_NEEDED,
            "asset_inventory": PhaseState.NOT_STARTED,
            "dependency_analysis": PhaseState.NOT_STARTED
        }

        recovery_options = self.state_machine.get_recovery_options(phase_states)

        # Should have options for failed and retry_needed phases
        assert len(recovery_options) >= 3  # failed, completed (rollback), retry_needed

        # Find specific options
        retry_option = next(
            (opt for opt in recovery_options if opt["phase"] == "data_import" and opt["action"] == "retry"),
            None
        )
        assert retry_option is not None
        assert retry_option["target_state"] == PhaseState.RETRY_NEEDED.value

        rollback_option = next(
            (opt for opt in recovery_options if opt["phase"] == "field_mapping" and opt["action"] == "rollback"),
            None
        )
        assert rollback_option is not None
        assert rollback_option["target_state"] == PhaseState.ROLLED_BACK.value

    def test_error_response_creation(self):
        """Test structured error response creation"""
        error_response = self.state_machine.create_error_response(
            "PHASE_EXECUTION_FAILED",
            "Phase failed to execute",
            phase="data_import",
            attempt_count=3
        )

        assert error_response["status"] == "failed"
        assert error_response["error_code"] == "PHASE_EXECUTION_FAILED"
        assert error_response["message"] == "Phase failed to execute"
        assert error_response["details"]["phase"] == "data_import"
        assert error_response["details"]["attempt_count"] == 3
        assert error_response["retry_allowed"] is True  # PHASE_EXECUTION_FAILED is retryable
        assert "timestamp" in error_response

        # Test non-retryable error
        error_response = self.state_machine.create_error_response(
            "DATA_VALIDATION_FAILED",
            "Data validation failed"
        )
        assert error_response["retry_allowed"] is False

    def test_phase_dependencies(self):
        """Test phase dependency mapping"""
        dependencies = self.state_machine.get_phase_dependencies()

        assert dependencies["data_import"] == []
        assert dependencies["field_mapping"] == ["data_import"]
        assert dependencies["data_cleansing"] == ["field_mapping"]
        assert dependencies["asset_inventory"] == ["data_cleansing"]
        assert dependencies["dependency_analysis"] == ["asset_inventory"]

    def test_edge_case_empty_phase_states(self):
        """Test handling of empty or missing phase states"""
        # Test empty phase states
        progress = self.state_machine.calculate_progress({})
        assert progress == 0.0

        # Test determine status with empty states
        status = self.state_machine.determine_flow_status({}, FlowStatus.INITIALIZED)
        assert status == FlowStatus.INITIALIZED

    def test_edge_case_invalid_phase_states(self):
        """Test handling of invalid phase state values"""
        # This would normally be caught at the enum level, but test robustness
        phase_states = {
            "data_import": PhaseState.COMPLETED,
            "invalid_phase": PhaseState.COMPLETED  # This should be ignored
        }

        # Should only count valid phases
        progress = self.state_machine.calculate_progress(phase_states)
        assert progress == 20.0  # Only data_import counted

    def test_rollback_scenario(self):
        """Test rollback scenario where completed phase needs revision"""
        # Start with completed phase
        current_state = PhaseState.COMPLETED
        target_state = PhaseState.ROLLED_BACK

        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", current_state, target_state
        )
        assert is_valid
        assert error is None

        # After rollback, should be able to restart
        is_valid, error = self.state_machine.validate_phase_transition(
            "data_import", PhaseState.ROLLED_BACK, PhaseState.IN_PROGRESS
        )
        assert is_valid

    def test_complex_failure_recovery_scenario(self):
        """Test complex scenario with multiple failures and recoveries"""
        phase_states = {
            "data_import": PhaseState.COMPLETED,
            "field_mapping": PhaseState.FAILED,
            "data_cleansing": PhaseState.NOT_STARTED,
            "asset_inventory": PhaseState.NOT_STARTED,
            "dependency_analysis": PhaseState.NOT_STARTED
        }

        # Should be in error recovery status
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        # Since we have a failure but no retry_needed or in_progress, it should be FAILED
        assert status == FlowStatus.FAILED

        # Add retry_needed to trigger error recovery
        phase_states["field_mapping"] = PhaseState.RETRY_NEEDED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.RETRY_PENDING

        # Progress should reflect partial completion
        progress = self.state_machine.calculate_progress(phase_states)
        expected = 20.0 + (20.0 * 0.1)  # completed + retry_needed
        assert progress == expected


@pytest.mark.asyncio
class TestFlowStateMachineIntegration:
    """Integration tests for flow state machine with realistic scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.state_machine = FlowStateMachine()

    def test_complete_flow_lifecycle(self):
        """Test complete flow lifecycle from start to finish"""
        # Initialize phase states
        phase_states = {phase: PhaseState.NOT_STARTED for phase in self.state_machine.PHASES}
        current_status = FlowStatus.INITIALIZED

        # Start flow
        current_status = self.state_machine.determine_flow_status(phase_states, current_status)
        assert current_status == FlowStatus.INITIALIZED

        # Complete each phase in order
        for phase in self.state_machine.PHASES:
            # Start phase
            phase_states[phase] = PhaseState.IN_PROGRESS
            current_status = self.state_machine.determine_flow_status(phase_states, current_status)

            # Complete phase
            phase_states[phase] = PhaseState.COMPLETED
            current_status = self.state_machine.determine_flow_status(phase_states, current_status)

            # Validate progress increases
            progress = self.state_machine.calculate_progress(phase_states)
            expected_progress = (self.state_machine.PHASES.index(phase) + 1) * 20.0
            assert progress == expected_progress

        # Final status should be completed
        assert current_status == FlowStatus.COMPLETED
        assert self.state_machine.calculate_progress(phase_states) == 100.0

    def test_flow_with_approval_workflow(self):
        """Test flow with approval requirements"""
        phase_states = {phase: PhaseState.NOT_STARTED for phase in self.state_machine.PHASES}

        # Complete first phase normally
        phase_states["data_import"] = PhaseState.COMPLETED

        # Second phase needs approval
        phase_states["field_mapping"] = PhaseState.WAITING_APPROVAL
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.WAITING_APPROVAL

        # Approve and complete
        phase_states["field_mapping"] = PhaseState.COMPLETED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.WAITING_APPROVAL)
        # Should progress to discovery phase
        assert status in {FlowStatus.DISCOVERY, FlowStatus.DATA_GATHERING}

    def test_flow_with_failure_and_recovery(self):
        """Test flow with failure and recovery"""
        phase_states = {phase: PhaseState.NOT_STARTED for phase in self.state_machine.PHASES}

        # Complete first phase
        phase_states["data_import"] = PhaseState.COMPLETED

        # Second phase fails
        phase_states["field_mapping"] = PhaseState.FAILED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ACTIVE)
        assert status == FlowStatus.FAILED

        # Mark for retry
        phase_states["field_mapping"] = PhaseState.RETRY_NEEDED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.FAILED)
        assert status == FlowStatus.RETRY_PENDING

        # Retry and complete
        phase_states["field_mapping"] = PhaseState.IN_PROGRESS
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.RETRY_PENDING)
        assert status == FlowStatus.ERROR_RECOVERY

        phase_states["field_mapping"] = PhaseState.COMPLETED
        status = self.state_machine.determine_flow_status(phase_states, FlowStatus.ERROR_RECOVERY)
        assert status == FlowStatus.DISCOVERY