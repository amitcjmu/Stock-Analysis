"""
Unit tests for ResourceAllocationService

Tests the AI-driven resource allocation generation and manual override functionality.
"""

import json
import uuid

# from datetime import datetime  # Unused
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.planning.planning_flow import PlanningFlow
from app.services.planning.resource_allocation_service import ResourceAllocationService


@pytest.fixture
def mock_context():
    """Create mock RequestContext."""
    context = MagicMock(spec=RequestContext)
    context.client_account_id = uuid.uuid4()
    context.engagement_id = uuid.uuid4()
    context.user_id = uuid.uuid4()
    return context


@pytest.fixture
def mock_db():
    """Create mock AsyncSession."""
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def sample_wave_plan():
    """Sample wave plan data."""
    return {
        "waves": [
            {
                "wave_id": "wave-1",
                "applications": [
                    {"id": str(uuid.uuid4()), "name": "App1", "complexity": "high"}
                ],
                "dependencies": [],
            },
            {
                "wave_id": "wave-2",
                "applications": [
                    {"id": str(uuid.uuid4()), "name": "App2", "complexity": "medium"}
                ],
                "dependencies": ["wave-1"],
            },
        ]
    }


@pytest.fixture
def sample_allocation_result():
    """Sample AI-generated allocation result."""
    return {
        "allocations": [
            {
                "wave_id": "wave-1",
                "resources": [
                    {
                        "role": "cloud_architect",
                        "count": 2,
                        "effort_hours": 120,
                        "confidence_score": 85,
                        "rationale": "High complexity requires dedicated architects",
                    },
                    {
                        "role": "developer",
                        "count": 5,
                        "effort_hours": 400,
                        "confidence_score": 90,
                        "rationale": "Standard development effort",
                    },
                ],
                "total_cost": 50000.00,
            },
            {
                "wave_id": "wave-2",
                "resources": [
                    {
                        "role": "cloud_architect",
                        "count": 1,
                        "effort_hours": 80,
                        "confidence_score": 80,
                        "rationale": "Medium complexity",
                    },
                    {
                        "role": "developer",
                        "count": 3,
                        "effort_hours": 240,
                        "confidence_score": 85,
                        "rationale": "Standard development",
                    },
                ],
                "total_cost": 30000.00,
            },
        ],
        "metadata": {"total_estimated_cost": 80000.00},
    }


class TestResourceAllocationService:
    """Test suite for ResourceAllocationService."""

    def test_initialization(self, mock_db, mock_context):
        """Test service initialization with tenant scoping."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        assert service.db == mock_db
        assert service.context == mock_context
        assert service.client_account_uuid == mock_context.client_account_id
        assert service.engagement_uuid == mock_context.engagement_id
        assert service.planning_repo is not None

    def test_build_allocation_context(self, mock_db, mock_context, sample_wave_plan):
        """Test context building for agent."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        resource_pools = {"architects": 5, "developers": 20}
        historical_data = {"avg_effort_per_app": 100}

        context = service._build_allocation_context(
            sample_wave_plan, resource_pools, historical_data
        )

        assert "wave_plan" in context
        assert context["wave_plan"] == sample_wave_plan
        assert context["resource_pools"] == resource_pools
        assert context["historical_data"] == historical_data
        assert "objectives" in context
        assert len(context["objectives"]) > 0

    def test_parse_allocation_result_dict(self, mock_db, mock_context):
        """Test parsing when result is already a dict."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        result = {"allocations": [], "metadata": {}}
        parsed = service._parse_allocation_result(result)

        assert parsed == result

    def test_parse_allocation_result_json_string(
        self, mock_db, mock_context, sample_allocation_result
    ):
        """Test parsing when result is JSON string."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        result_str = json.dumps(sample_allocation_result)
        parsed = service._parse_allocation_result(result_str)

        assert parsed == sample_allocation_result

    def test_parse_allocation_result_markdown_wrapped(
        self, mock_db, mock_context, sample_allocation_result
    ):
        """Test parsing when result has markdown code block wrapper."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        result_str = f"```json\n{json.dumps(sample_allocation_result)}\n```"
        parsed = service._parse_allocation_result(result_str)

        assert parsed == sample_allocation_result

    def test_parse_allocation_result_invalid_json(self, mock_db, mock_context):
        """Test parsing when result is invalid JSON."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        result_str = "This is not valid JSON"
        parsed = service._parse_allocation_result(result_str)

        assert "allocations" in parsed
        assert parsed["allocations"] == []
        assert "error" in parsed["metadata"]

    def test_get_nested_value(self, mock_db, mock_context):
        """Test getting nested values from dict."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        data = {"resources": {"cloud_architect": {"count": 2, "effort_hours": 120}}}

        value = service._get_nested_value(data, "resources.cloud_architect.count")
        assert value == 2

        value = service._get_nested_value(
            data, "resources.cloud_architect.effort_hours"
        )
        assert value == 120

        value = service._get_nested_value(data, "nonexistent.path")
        assert value is None

    def test_set_nested_value(self, mock_db, mock_context):
        """Test setting nested values in dict."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        data = {"resources": {"cloud_architect": {"count": 2, "effort_hours": 120}}}

        service._set_nested_value(data, "resources.cloud_architect.count", 3)
        assert data["resources"]["cloud_architect"]["count"] == 3

        service._set_nested_value(data, "resources.developer.count", 5)
        assert data["resources"]["developer"]["count"] == 5

    @patch("app.services.planning.resource_allocation_service.Task")
    def test_create_resource_allocation_task(
        self, mock_task_class, mock_db, mock_context, sample_wave_plan
    ):
        """Test task creation for resource allocation."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        mock_agent = MagicMock()
        mock_agent._agent = MagicMock()
        mock_task_instance = MagicMock()
        mock_task_class.return_value = mock_task_instance

        task = service._create_resource_allocation_task(
            agent=mock_agent,
            wave_plan_data=sample_wave_plan,
            resource_pools=None,
            historical_data=None,
        )

        # Task should be created
        assert task is not None
        # Verify Task class was called with correct parameters
        mock_task_class.assert_called_once()
        call_kwargs = mock_task_class.call_args.kwargs
        assert "description" in call_kwargs
        assert "expected_output" in call_kwargs
        assert "agent" in call_kwargs
        # Description should mention wave count
        assert (
            "2" in call_kwargs["description"]
            or "waves" in call_kwargs["description"].lower()
        )


@pytest.mark.asyncio
class TestResourceAllocationServiceAsync:
    """Async tests for ResourceAllocationService."""

    async def test_apply_manual_override(self, mock_db, mock_context):
        """Test applying manual overrides to allocations."""
        service = ResourceAllocationService(db=mock_db, context=mock_context)

        planning_flow_id = uuid.uuid4()
        wave_id = "wave-1"
        user_id = str(uuid.uuid4())

        # Mock planning flow with existing allocations
        mock_planning_flow = MagicMock(spec=PlanningFlow)
        mock_planning_flow.id = planning_flow_id
        mock_planning_flow.resource_allocation_data = {
            "allocations": [
                {
                    "wave_id": "wave-1",
                    "resources": {"cloud_architect": {"count": 2, "effort_hours": 120}},
                }
            ],
            "metadata": {},
        }

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_planning_flow
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Apply override
        overrides = {"resources.cloud_architect.count": 3}

        result = await service.apply_manual_override(
            planning_flow_id=planning_flow_id,
            wave_id=wave_id,
            overrides=overrides,
            user_id=user_id,
            reason="Need additional capacity",
        )

        # Verify override was applied
        wave_alloc = result["allocations"][0]
        assert wave_alloc["resources"]["cloud_architect"]["count"] == 3
        assert "overrides" in wave_alloc
        assert len(wave_alloc["overrides"]) == 1
        assert wave_alloc["overrides"][0]["user_id"] == user_id
        assert wave_alloc["overrides"][0]["old_value"] == 2
        assert wave_alloc["overrides"][0]["new_value"] == 3

        # Verify database was updated
        mock_db.commit.assert_called_once()
