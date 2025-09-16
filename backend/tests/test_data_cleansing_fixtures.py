"""
Shared fixtures for data cleansing endpoint tests.
"""

import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Mock crewai module before importing other modules
sys.modules["crewai"] = MagicMock()
sys.modules["crewai.tools"] = MagicMock()
sys.modules["crewai.agent"] = MagicMock()
sys.modules["crewai.task"] = MagicMock()
sys.modules["crewai.crew"] = MagicMock()

from app.api.v1.endpoints.data_cleansing import (  # noqa: E402
    DataQualityIssue,
    DataCleansingRecommendation,
)
from app.core.context import RequestContext  # noqa: E402
from app.models.client_account import User  # noqa: E402
from app.models.data_import.core import DataImport  # noqa: E402
from app.models.data_import.mapping import ImportFieldMapping  # noqa: E402


class DataCleansingTestFixtures:
    """Base class with shared fixtures for data cleansing tests"""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_context(self):
        """Create mock request context"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = MagicMock(spec=User)
        user.id = str(uuid.uuid4())
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def sample_flow_id(self):
        """Sample flow ID for testing"""
        return str(uuid.uuid4())

    @pytest.fixture
    def mock_flow(self, sample_flow_id):
        """Create mock discovery flow"""
        flow = MagicMock()
        flow.flow_id = sample_flow_id
        flow.id = str(uuid.uuid4())
        flow.status = "active"
        flow.data_import_id = str(uuid.uuid4())
        return flow

    @pytest.fixture
    def mock_data_import(self):
        """Create mock data import"""
        data_import = MagicMock(spec=DataImport)
        data_import.id = str(uuid.uuid4())
        data_import.total_records = 1000
        data_import.created_at = datetime.utcnow()
        return data_import

    @pytest.fixture
    def mock_field_mappings(self):
        """Create mock field mappings"""
        mappings = []
        for i, field in enumerate(["hostname", "ip_address", "os", "cpu", "memory"]):
            mapping = MagicMock(spec=ImportFieldMapping)
            mapping.id = str(uuid.uuid4())
            mapping.source_field = field
            mapping.target_field = field
            mappings.append(mapping)
        return mappings

    @pytest.fixture
    def mock_stats_response(self):
        """Create mock stats response"""
        return {
            "total_records": 1000,
            "clean_records": 850,
            "records_with_issues": 150,
            "issues_by_severity": {"low": 80, "medium": 50, "high": 15, "critical": 5},
            "completion_percentage": 85.0,
            "flow_id": str(uuid.uuid4()),
        }

    @pytest.fixture
    def sample_quality_issues(self):
        """Sample quality issues for testing"""
        return [
            DataQualityIssue(
                id=str(uuid.uuid4()),
                field_name="hostname",
                issue_type="missing_values",
                severity="medium",
                description="Missing hostname values detected",
                affected_records=50,
                recommendation="Fill missing hostnames with default values",
                auto_fixable=True,
            ),
            DataQualityIssue(
                id=str(uuid.uuid4()),
                field_name="ip_address",
                issue_type="invalid_format",
                severity="high",
                description="Invalid IP address formats found",
                affected_records=25,
                recommendation="Validate and correct IP address formats",
                auto_fixable=False,
            ),
        ]

    @pytest.fixture
    def sample_recommendations(self):
        """Sample recommendations for testing"""
        return [
            DataCleansingRecommendation(
                id=str(uuid.uuid4()),
                category="standardization",
                title="Standardize hostname formats",
                description="Ensure all hostnames follow consistent naming convention",
                priority="high",
                impact="Improves data consistency",
                effort_estimate="2-4 hours",
                fields_affected=["hostname"],
            )
        ]
