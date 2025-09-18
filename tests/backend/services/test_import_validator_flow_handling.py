"""
Test import validator handling of DiscoveryFlow objects vs dictionaries.

This test ensures the import validator can handle both:
1. DiscoveryFlow model objects (returned by repository)
2. Dictionary representations (for backward compatibility)
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.context import RequestContext
from app.services.data_import.import_validator import ImportValidator


class MockDiscoveryFlow:
    """Mock DiscoveryFlow model object"""

    def __init__(self, flow_id: str, status: str = "active", progress: float = 25.0):
        self.flow_id = uuid.UUID(flow_id)
        self.status = status
        self.progress_percentage = progress
        self.updated_at = datetime.utcnow()
        self.data_import_completed = True
        self.field_mapping_completed = True
        self.data_cleansing_completed = False
        self.asset_inventory_completed = False
        self.dependency_analysis_completed = False
        self.tech_debt_assessment_completed = False

    def get_current_phase(self) -> str:
        """Return current phase based on completion status"""
        if not self.data_cleansing_completed:
            return "data_cleansing"
        elif not self.asset_inventory_completed:
            return "inventory"
        elif not self.dependency_analysis_completed:
            return "dependencies"
        elif not self.tech_debt_assessment_completed:
            return "tech_debt"
        return "completed"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "flow_id": str(self.flow_id),
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "current_phase": self.get_current_phase(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "phase_completion": {
                "data_import": self.data_import_completed,
                "attribute_mapping": self.field_mapping_completed,
                "data_cleansing": self.data_cleansing_completed,
                "inventory": self.asset_inventory_completed,
                "dependencies": self.dependency_analysis_completed,
                "tech_debt": self.tech_debt_assessment_completed,
            }
        }


@pytest.mark.asyncio
async def test_validate_no_incomplete_discovery_flow_with_objects():
    """Test validation when get_active_flows returns DiscoveryFlow objects"""

    # Setup
    mock_db = AsyncMock()
    validator = ImportValidator(mock_db, "test-client-id")

    # Create mock discovery service that returns DiscoveryFlow objects
    mock_discovery_service = MagicMock()
    mock_flow = MockDiscoveryFlow("12345678-1234-5678-1234-567812345678")
    mock_discovery_service.get_active_flows = AsyncMock(return_value=[mock_flow])

    with patch("app.services.data_import.import_validator.DISCOVERY_FLOW_AVAILABLE", True):
        with patch("app.services.data_import.import_validator.DiscoveryFlowService", return_value=mock_discovery_service):
            result = await validator.validate_no_incomplete_discovery_flow(
                "test-client-id",
                "test-engagement-id"
            )

    # Assertions
    assert result["can_proceed"] is False
    assert "incomplete Discovery Flow exists" in result["message"]
    assert result["existing_flow"]["flow_id"] == "12345678-1234-5678-1234-567812345678"
    assert result["existing_flow"]["current_phase"] == "data_cleansing"
    assert result["existing_flow"]["progress_percentage"] == 25.0
    assert result["show_flow_manager"] is True


@pytest.mark.asyncio
async def test_validate_no_incomplete_discovery_flow_with_dicts():
    """Test validation when get_active_flows returns dictionaries (backward compatibility)"""

    # Setup
    mock_db = AsyncMock()
    validator = ImportValidator(mock_db, "test-client-id")

    # Create mock discovery service that returns dictionaries
    mock_discovery_service = MagicMock()
    mock_flow_dict = {
        "flow_id": "87654321-4321-8765-4321-876543210987",
        "status": "active",
        "current_phase": "inventory",
        "progress_percentage": 50.0,
        "updated_at": datetime.utcnow().isoformat(),
        "phase_completion": {"data_import": True, "attribute_mapping": True, "data_cleansing": True}
    }
    mock_discovery_service.get_active_flows = AsyncMock(return_value=[mock_flow_dict])

    with patch("app.services.data_import.import_validator.DISCOVERY_FLOW_AVAILABLE", True):
        with patch("app.services.data_import.import_validator.DiscoveryFlowService", return_value=mock_discovery_service):
            result = await validator.validate_no_incomplete_discovery_flow(
                "test-client-id",
                "test-engagement-id"
            )

    # Assertions
    assert result["can_proceed"] is False
    assert "incomplete Discovery Flow exists" in result["message"]
    assert result["existing_flow"]["flow_id"] == "87654321-4321-8765-4321-876543210987"
    assert result["existing_flow"]["current_phase"] == "inventory"
    assert result["existing_flow"]["progress_percentage"] == 50.0


@pytest.mark.asyncio
async def test_validate_no_incomplete_discovery_flow_empty():
    """Test validation when no incomplete flows exist"""

    # Setup
    mock_db = AsyncMock()
    validator = ImportValidator(mock_db, "test-client-id")

    # Create mock discovery service that returns empty list
    mock_discovery_service = MagicMock()
    mock_discovery_service.get_active_flows = AsyncMock(return_value=[])

    with patch("app.services.data_import.import_validator.DISCOVERY_FLOW_AVAILABLE", True):
        with patch("app.services.data_import.import_validator.DiscoveryFlowService", return_value=mock_discovery_service):
            result = await validator.validate_no_incomplete_discovery_flow(
                "test-client-id",
                "test-engagement-id"
            )

    # Assertions
    assert result["can_proceed"] is True
    assert "No incomplete discovery flows found" in result["message"]


@pytest.mark.asyncio
async def test_flow_to_dict_method():
    """Test the _flow_to_dict helper method"""

    mock_db = AsyncMock()
    validator = ImportValidator(mock_db, "test-client-id")

    # Test with dictionary input
    dict_input = {"flow_id": "123", "status": "active"}
    result = validator._flow_to_dict(dict_input)
    assert result == dict_input

    # Test with DiscoveryFlow object
    flow_obj = MockDiscoveryFlow("12345678-1234-5678-1234-567812345678")
    result = validator._flow_to_dict(flow_obj)
    assert isinstance(result, dict)
    assert result["flow_id"] == "12345678-1234-5678-1234-567812345678"
    assert result["current_phase"] == "data_cleansing"
    assert "phase_completion" in result
