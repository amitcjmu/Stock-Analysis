"""
Tests for base constants and validation functions.

Tests the phase transition state machine validation and constants.
"""

from app.services.discovery.phase_persistence_helpers import (
    PHASE_FLAG_MAP,
    PhaseTransitionResult,
    _is_valid_transition,
)


class TestPhaseTransitionStateMachine:
    """Test the phase transition state machine validation."""

    def test_valid_initial_transitions(self):
        """Test valid transitions from initial state."""
        assert _is_valid_transition(None, "data_import")
        assert not _is_valid_transition(None, "field_mapping")
        assert not _is_valid_transition(None, "asset_inventory")

    def test_valid_sequential_transitions(self):
        """Test valid sequential transitions through all phases."""
        phases = [
            ("data_import", "field_mapping"),
            ("field_mapping", "data_cleansing"),
            ("data_cleansing", "asset_inventory"),
            ("asset_inventory", "dependency_analysis"),
            ("dependency_analysis", "tech_debt_assessment"),
        ]

        for from_phase, to_phase in phases:
            assert _is_valid_transition(from_phase, to_phase)

    def test_invalid_backwards_transitions(self):
        """Test that backwards transitions are invalid."""
        assert not _is_valid_transition("field_mapping", "data_import")
        assert not _is_valid_transition("asset_inventory", "data_cleansing")
        assert not _is_valid_transition("tech_debt_assessment", "dependency_analysis")

    def test_invalid_skip_transitions(self):
        """Test that skipping phases is invalid."""
        assert not _is_valid_transition("data_import", "data_cleansing")
        assert not _is_valid_transition("field_mapping", "asset_inventory")
        assert not _is_valid_transition("data_cleansing", "dependency_analysis")

    def test_terminal_phase_transitions(self):
        """Test that no transitions are allowed from terminal phase."""
        assert not _is_valid_transition("tech_debt_assessment", "data_import")
        assert not _is_valid_transition("tech_debt_assessment", "completed")

    def test_phase_flag_mapping(self):
        """Test that all phases have corresponding completion flags."""
        expected_phases = {
            "data_import",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_assessment",
        }

        assert set(PHASE_FLAG_MAP.keys()) == expected_phases

        # Verify all flag names end with '_completed'
        for flag_name in PHASE_FLAG_MAP.values():
            assert flag_name.endswith("_completed")


class TestPhaseTransitionResult:
    """Test the PhaseTransitionResult dataclass."""

    def test_add_warning(self):
        """Test adding warnings to the result."""
        result = PhaseTransitionResult(
            success=False, was_idempotent=False, prior_phase="data_import", warnings=[]
        )

        result.add_warning("First warning")
        result.add_warning("Second warning")

        assert len(result.warnings) == 2
        assert "First warning" in result.warnings
        assert "Second warning" in result.warnings
