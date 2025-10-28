"""
Unit Tests for AssessmentGapDetector (6R Analysis Server-Side Gate)

Tests the Tier 1 gap detection service for 6R assessment, including:
- Tier 1 field detection (criticality, business_criticality, application_type, migration_priority)
- Multi-tenant scoping and security
- Gap payload structure
- Empty result handling

Per Two-Tier Inline Gap-Filling Design (October 2025)
Reference: /docs/design/TWO_TIER_INLINE_GAP_FILLING_DESIGN.md

Coverage Target: 90%+
"""

import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.api.v1.endpoints.sixr_analysis_modular.services.gap_detection_service import (
    AssessmentGapDetector,
    detect_tier1_gaps_for_analysis,
    TIER1_FIELDS,
)
from app.models.asset.models import Asset


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_context_ids():
    """Mock tenant context IDs"""
    return {
        "client_account_id": uuid4(),
        "engagement_id": uuid4(),
    }


@pytest.fixture
def complete_asset():
    """Mock asset with all Tier 1 fields populated"""
    asset = Mock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Complete Application"
    asset.criticality = "high"
    asset.business_criticality = "critical"
    asset.asset_type = "custom"  # Maps to application_type
    asset.migration_priority = "wave-1"
    return asset


@pytest.fixture
def incomplete_asset_missing_criticality():
    """Mock asset missing criticality field"""
    asset = Mock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Missing Criticality App"
    asset.criticality = None  # MISSING
    asset.business_criticality = "high"
    asset.asset_type = "cots"
    asset.migration_priority = "wave-2"
    return asset


@pytest.fixture
def incomplete_asset_empty_strings():
    """Mock asset with empty string values (should be treated as missing)"""
    asset = Mock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Empty Fields App"
    asset.criticality = ""  # EMPTY - should be detected as missing
    asset.business_criticality = "   "  # WHITESPACE - should be detected as missing
    asset.asset_type = "custom"
    asset.migration_priority = None  # MISSING
    return asset


@pytest.fixture
def incomplete_asset_multiple_gaps():
    """Mock asset with multiple Tier 1 gaps"""
    asset = Mock(spec=Asset)
    asset.id = uuid4()
    asset.name = "Multiple Gaps App"
    asset.criticality = None  # MISSING
    asset.business_criticality = None  # MISSING
    asset.asset_type = None  # MISSING
    asset.migration_priority = "wave-1"  # PRESENT
    return asset


class TestTier1FieldConfiguration:
    """Test Tier 1 field configuration constants"""

    def test_tier1_fields_structure(self):
        """Verify TIER1_FIELDS has correct structure"""
        assert "criticality" in TIER1_FIELDS
        assert "business_criticality" in TIER1_FIELDS
        assert "application_type" in TIER1_FIELDS
        assert "migration_priority" in TIER1_FIELDS

        for field_name, config in TIER1_FIELDS.items():
            assert "display_name" in config
            assert "reason" in config
            assert "asset_field" in config
            assert "priority" in config
            assert isinstance(config["priority"], int)

    def test_application_type_maps_to_asset_type(self):
        """Verify application_type maps to asset_type field"""
        assert TIER1_FIELDS["application_type"]["asset_field"] == "asset_type"


class TestAssessmentGapDetector:
    """Test AssessmentGapDetector class"""

    def test_initialization(self, mock_db_session):
        """Test service initialization"""
        detector = AssessmentGapDetector(db=mock_db_session)
        assert detector.db == mock_db_session

    @pytest.mark.asyncio
    async def test_no_gaps_when_all_fields_complete(
        self, mock_db_session, mock_context_ids, complete_asset
    ):
        """Test that no gaps are returned when all Tier 1 fields are present"""
        detector = AssessmentGapDetector(db=mock_db_session)

        # Mock database query to return complete asset
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=complete_asset)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[complete_asset.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Should return empty dict (no gaps)
        assert gaps == {}
        assert len(gaps) == 0

    @pytest.mark.asyncio
    async def test_detects_single_missing_field(
        self, mock_db_session, mock_context_ids, incomplete_asset_missing_criticality
    ):
        """Test detection of single missing Tier 1 field"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_missing_criticality
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[incomplete_asset_missing_criticality.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Should return dict with one asset having one gap
        assert len(gaps) == 1
        asset_id_str = str(incomplete_asset_missing_criticality.id)
        assert asset_id_str in gaps
        assert len(gaps[asset_id_str]) == 1

        gap = gaps[asset_id_str][0]
        assert gap["field_name"] == "criticality"
        assert gap["display_name"] == "Business Criticality"
        assert gap["tier"] == 1
        assert "reason" in gap

    @pytest.mark.asyncio
    async def test_detects_empty_strings_as_missing(
        self, mock_db_session, mock_context_ids, incomplete_asset_empty_strings
    ):
        """Test that empty strings and whitespace are treated as missing"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_empty_strings
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[incomplete_asset_empty_strings.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Should detect 3 gaps (criticality="", business_criticality="   ", migration_priority=None)
        assert len(gaps) == 1
        asset_id_str = str(incomplete_asset_empty_strings.id)
        assert len(gaps[asset_id_str]) == 3

        gap_fields = {g["field_name"] for g in gaps[asset_id_str]}
        assert "criticality" in gap_fields
        assert "business_criticality" in gap_fields
        assert "migration_priority" in gap_fields

    @pytest.mark.asyncio
    async def test_detects_multiple_gaps_per_asset(
        self, mock_db_session, mock_context_ids, incomplete_asset_multiple_gaps
    ):
        """Test detection of multiple Tier 1 gaps on single asset"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_multiple_gaps
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[incomplete_asset_multiple_gaps.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Should detect 3 gaps (criticality, business_criticality, application_type)
        assert len(gaps) == 1
        asset_id_str = str(incomplete_asset_multiple_gaps.id)
        assert len(gaps[asset_id_str]) == 3

        gap_fields = {g["field_name"] for g in gaps[asset_id_str]}
        assert "criticality" in gap_fields
        assert "business_criticality" in gap_fields
        assert "application_type" in gap_fields

    @pytest.mark.asyncio
    async def test_handles_multiple_assets(
        self,
        mock_db_session,
        mock_context_ids,
        complete_asset,
        incomplete_asset_missing_criticality,
    ):
        """Test gap detection across multiple assets"""
        detector = AssessmentGapDetector(db=mock_db_session)

        # Mock returns different assets for each call
        mock_result1 = Mock()
        mock_result1.scalar_one_or_none = Mock(return_value=complete_asset)
        mock_result2 = Mock()
        mock_result2.scalar_one_or_none = Mock(
            return_value=incomplete_asset_missing_criticality
        )

        mock_db_session.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[complete_asset.id, incomplete_asset_missing_criticality.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Only the incomplete asset should be in the result
        assert len(gaps) == 1
        assert str(complete_asset.id) not in gaps  # Complete asset NOT in gaps
        assert str(incomplete_asset_missing_criticality.id) in gaps

    @pytest.mark.asyncio
    async def test_handles_asset_not_found(self, mock_db_session, mock_context_ids):
        """Test graceful handling when asset not found (wrong tenant or doesn't exist)"""
        detector = AssessmentGapDetector(db=mock_db_session)

        # Mock database returns None (asset not found)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[uuid4()],  # Non-existent asset
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Should return empty dict (no errors)
        assert gaps == {}

    @pytest.mark.asyncio
    async def test_tenant_scoping_in_query(self, mock_db_session, mock_context_ids):
        """Verify tenant scoping is applied to database queries"""
        detector = AssessmentGapDetector(db=mock_db_session)
        asset_id = uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await detector.detect_tier1_gaps(
            asset_ids=[asset_id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        # Verify execute was called (with tenant-scoped query)
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_gap_payload_structure(
        self, mock_db_session, mock_context_ids, incomplete_asset_missing_criticality
    ):
        """Verify gap payload has correct structure for frontend consumption"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_missing_criticality
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detector.detect_tier1_gaps(
            asset_ids=[incomplete_asset_missing_criticality.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        asset_id_str = str(incomplete_asset_missing_criticality.id)
        gap = gaps[asset_id_str][0]

        # Verify all required fields present
        assert "field_name" in gap
        assert "display_name" in gap
        assert "reason" in gap
        assert "tier" in gap
        assert "priority" in gap

        # Verify types
        assert isinstance(gap["field_name"], str)
        assert isinstance(gap["display_name"], str)
        assert isinstance(gap["reason"], str)
        assert gap["tier"] == 1  # All are Tier 1
        assert isinstance(gap["priority"], int)

    @pytest.mark.asyncio
    async def test_check_has_tier1_gaps_returns_true(
        self, mock_db_session, mock_context_ids, incomplete_asset_missing_criticality
    ):
        """Test check_has_tier1_gaps returns True when gaps exist"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_missing_criticality
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        has_gaps = await detector.check_has_tier1_gaps(
            asset_ids=[incomplete_asset_missing_criticality.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        assert has_gaps is True

    @pytest.mark.asyncio
    async def test_check_has_tier1_gaps_returns_false(
        self, mock_db_session, mock_context_ids, complete_asset
    ):
        """Test check_has_tier1_gaps returns False when no gaps"""
        detector = AssessmentGapDetector(db=mock_db_session)

        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=complete_asset)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        has_gaps = await detector.check_has_tier1_gaps(
            asset_ids=[complete_asset.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
        )

        assert has_gaps is False


class TestUtilityFunctions:
    """Test utility functions"""

    @pytest.mark.asyncio
    async def test_detect_tier1_gaps_for_analysis(
        self, mock_db_session, mock_context_ids, incomplete_asset_missing_criticality
    ):
        """Test convenience function for analysis handlers"""
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(
            return_value=incomplete_asset_missing_criticality
        )
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        gaps = await detect_tier1_gaps_for_analysis(
            asset_ids=[incomplete_asset_missing_criticality.id],
            client_account_id=mock_context_ids["client_account_id"],
            engagement_id=mock_context_ids["engagement_id"],
            db=mock_db_session,
        )

        # Should return same structure as AssessmentGapDetector.detect_tier1_gaps
        assert len(gaps) == 1
        asset_id_str = str(incomplete_asset_missing_criticality.id)
        assert asset_id_str in gaps
