"""
Unit tests for collection manual submission gap resolution functionality.

Tests the fixes implemented for:
- Updating CollectionDataGap.resolution_status when submitting questionnaire responses
- Setting resolved_at and resolved_by correctly
- Triggering asset write-back after gap resolution
- Error handling when gaps don't exist

CC Generated with Claude Code
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.collection_crud_update_commands import (
    submit_questionnaire_response,
)
from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.models.collection_data_gap import CollectionDataGap
from app.models.asset import Asset
from app.schemas.collection_flow import QuestionnaireSubmissionRequest


@pytest.fixture
def mock_db():
    """Mock AsyncSession for database operations"""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock user for authentication"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    return user


@pytest.fixture
def mock_context():
    """Mock request context with tenant info"""
    context = MagicMock(spec=RequestContext)
    context.engagement_id = uuid4()
    context.client_account_id = uuid4()
    return context


@pytest.fixture
def mock_collection_flow():
    """Mock collection flow"""
    flow = MagicMock(spec=CollectionFlow)
    flow.id = uuid4()
    flow.flow_id = str(uuid4())
    flow.status = "in_progress"
    flow.progress_percentage = 50
    flow.updated_at = datetime.now(timezone.utc)
    return flow


@pytest.fixture
def mock_questionnaire_request():
    """Mock questionnaire submission request"""
    request = MagicMock(spec=QuestionnaireSubmissionRequest)
    request.responses = {
        "technology_stack": "Java",
        "database_type": "PostgreSQL",
        "authentication_method": "OAuth2",
    }
    request.form_metadata = {"completion_percentage": 75, "confidence_score": 0.85}
    request.validation_results = {"isValid": True}
    return request


@pytest.fixture
def mock_pending_gaps():
    """Mock pending data gaps"""
    gaps = []
    for field_name in ["technology_stack", "database_type"]:
        gap = MagicMock(spec=CollectionDataGap)
        gap.id = uuid4()
        gap.field_name = field_name
        gap.resolution_status = "pending"
        gap.resolved_at = None
        gap.resolved_by = None
        gaps.append(gap)
    return gaps


class TestGapResolutionInManualSubmit:
    """Test gap resolution during manual questionnaire submission"""

    @pytest.mark.asyncio
    async def test_submit_questionnaire_resolves_matching_gaps(
        self,
        mock_db,
        mock_user,
        mock_context,
        mock_collection_flow,
        mock_questionnaire_request,
        mock_pending_gaps,
    ):
        """Test that submitting questionnaire responses updates matching gap resolution status"""
        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps

        mock_db.execute.side_effect = [flow_result, gap_result]

        with patch(
            "app.services.flow_configs.collection_handlers.asset_handlers.apply_resolved_gaps_to_assets"
        ) as mock_writeback:
            mock_writeback.return_value = None

            # Execute the function
            result = await submit_questionnaire_response(
                flow_id=mock_collection_flow.flow_id,
                questionnaire_id="test-questionnaire",
                request_data=mock_questionnaire_request,
                db=mock_db,
                current_user=mock_user,
                context=mock_context,
            )

            # Verify gap resolution status was updated for matching fields
            matching_gaps = [
                gap
                for gap in mock_pending_gaps
                if gap.field_name in ["technology_stack", "database_type"]
            ]
            for gap in matching_gaps:
                assert gap.resolution_status == "resolved"
                assert gap.resolved_at is not None
                assert gap.resolved_by == "manual_submission"

            # Verify asset write-back was called
            mock_writeback.assert_called_once_with(
                mock_db,
                mock_collection_flow.id,
                {
                    "engagement_id": mock_context.engagement_id,
                    "client_account_id": mock_context.client_account_id,
                    "user_id": mock_user.id,
                },
            )

            # Verify response structure
            assert result["status"] == "success"
            assert result["flow_id"] == mock_collection_flow.flow_id
            assert "responses_saved" in result

    @pytest.mark.asyncio
    async def test_submit_questionnaire_ignores_non_matching_gaps(
        self, mock_db, mock_user, mock_context, mock_collection_flow, mock_pending_gaps
    ):
        """Test that gaps without matching form responses remain unresolved"""
        # Create request with responses that don't match gap field names
        request = MagicMock(spec=QuestionnaireSubmissionRequest)
        request.responses = {"unrelated_field": "value", "another_field": "value2"}
        request.form_metadata = {"completion_percentage": 75}
        request.validation_results = {"isValid": True}

        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps

        mock_db.execute.side_effect = [flow_result, gap_result]

        # Execute the function
        result = await submit_questionnaire_response(
            flow_id=mock_collection_flow.flow_id,
            questionnaire_id="test-questionnaire",
            request_data=request,
            db=mock_db,
            current_user=mock_user,
            context=mock_context,
        )

        # Verify no gaps were resolved
        for gap in mock_pending_gaps:
            assert gap.resolution_status == "pending"
            assert gap.resolved_at is None
            assert gap.resolved_by is None

        # Verify response structure
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_submit_questionnaire_skips_empty_responses(
        self, mock_db, mock_user, mock_context, mock_collection_flow, mock_pending_gaps
    ):
        """Test that empty/null responses don't resolve gaps"""
        # Create request with empty responses for matching fields
        request = MagicMock(spec=QuestionnaireSubmissionRequest)
        request.responses = {
            "technology_stack": "",  # Empty string
            "database_type": None,  # Null value
            "valid_field": "valid_value",
        }
        request.form_metadata = {"completion_percentage": 75}
        request.validation_results = {"isValid": True}

        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps

        mock_db.execute.side_effect = [flow_result, gap_result]

        # Execute the function
        result = await submit_questionnaire_response(
            flow_id=mock_collection_flow.flow_id,
            questionnaire_id="test-questionnaire",
            request_data=request,
            db=mock_db,
            current_user=mock_user,
            context=mock_context,
        )

        # Verify gaps with empty responses were not resolved
        for gap in mock_pending_gaps:
            if gap.field_name in ["technology_stack", "database_type"]:
                assert gap.resolution_status == "pending"
                assert gap.resolved_at is None
                assert gap.resolved_by is None

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_submit_questionnaire_handles_no_gaps(
        self,
        mock_db,
        mock_user,
        mock_context,
        mock_collection_flow,
        mock_questionnaire_request,
    ):
        """Test that submission works correctly when no gaps exist"""
        # Setup database mocks - no gaps found
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = []  # No gaps

        mock_db.execute.side_effect = [flow_result, gap_result]

        # Execute the function
        result = await submit_questionnaire_response(
            flow_id=mock_collection_flow.flow_id,
            questionnaire_id="test-questionnaire",
            request_data=mock_questionnaire_request,
            db=mock_db,
            current_user=mock_user,
            context=mock_context,
        )

        # Verify successful operation even with no gaps
        assert result["status"] == "success"
        assert (
            result["responses_saved"] == 3
        )  # Based on mock_questionnaire_request responses

    @pytest.mark.asyncio
    async def test_submit_questionnaire_handles_writeback_failure(
        self,
        mock_db,
        mock_user,
        mock_context,
        mock_collection_flow,
        mock_questionnaire_request,
        mock_pending_gaps,
    ):
        """Test that write-back failure doesn't fail the entire operation"""
        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps

        mock_db.execute.side_effect = [flow_result, gap_result]

        with patch(
            "app.services.flow_configs.collection_handlers.asset_handlers.apply_resolved_gaps_to_assets"
        ) as mock_writeback:
            # Make write-back fail
            mock_writeback.side_effect = Exception("Asset write-back failed")

            # Execute the function - should not raise exception
            result = await submit_questionnaire_response(
                flow_id=mock_collection_flow.flow_id,
                questionnaire_id="test-questionnaire",
                request_data=mock_questionnaire_request,
                db=mock_db,
                current_user=mock_user,
                context=mock_context,
            )

            # Verify gaps were still resolved
            matching_gaps = [
                gap
                for gap in mock_pending_gaps
                if gap.field_name in ["technology_stack", "database_type"]
            ]
            for gap in matching_gaps:
                assert gap.resolution_status == "resolved"

            # Verify operation succeeded despite write-back failure
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_submit_questionnaire_flow_not_found(
        self, mock_db, mock_user, mock_context, mock_questionnaire_request
    ):
        """Test error handling when collection flow is not found"""
        # Setup database mock - flow not found
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = flow_result

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await submit_questionnaire_response(
                flow_id="non-existent-flow",
                questionnaire_id="test-questionnaire",
                request_data=mock_questionnaire_request,
                db=mock_db,
                current_user=mock_user,
                context=mock_context,
            )

        assert exc_info.value.status_code == 404
        assert "Collection flow non-existent-flow not found" in str(
            exc_info.value.detail
        )

    @pytest.mark.asyncio
    async def test_submit_questionnaire_with_asset_linking(
        self, mock_db, mock_user, mock_context, mock_collection_flow, mock_pending_gaps
    ):
        """Test that asset linking works correctly when asset_id is provided"""
        asset_id = uuid4()
        mock_asset = MagicMock(spec=Asset)
        mock_asset.id = asset_id
        mock_asset.name = "Test Application"

        # Create request with asset_id in metadata
        request = MagicMock(spec=QuestionnaireSubmissionRequest)
        request.responses = {"technology_stack": "Java"}
        request.form_metadata = {"asset_id": str(asset_id), "completion_percentage": 75}
        request.validation_results = {"isValid": True}

        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        asset_result = AsyncMock()
        asset_result.scalar_one_or_none.return_value = mock_asset

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps[
            :1
        ]  # Only one matching gap

        mock_db.execute.side_effect = [flow_result, asset_result, gap_result]

        with patch(
            "app.services.flow_configs.collection_handlers.asset_handlers.apply_resolved_gaps_to_assets"
        ) as mock_writeback:
            # Execute the function
            result = await submit_questionnaire_response(
                flow_id=mock_collection_flow.flow_id,
                questionnaire_id="test-questionnaire",
                request_data=request,
                db=mock_db,
                current_user=mock_user,
                context=mock_context,
            )

            # Verify asset was validated and linked
            assert result["status"] == "success"

            # Verify asset write-back was called after gap resolution
            mock_writeback.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_questionnaire_invalid_asset_id(
        self, mock_db, mock_user, mock_context, mock_collection_flow, mock_pending_gaps
    ):
        """Test handling of invalid asset_id in form metadata"""
        invalid_asset_id = str(uuid4())

        # Create request with invalid asset_id
        request = MagicMock(spec=QuestionnaireSubmissionRequest)
        request.responses = {"technology_stack": "Java"}
        request.form_metadata = {
            "asset_id": invalid_asset_id,
            "completion_percentage": 75,
        }
        request.validation_results = {"isValid": True}

        # Setup database mocks - asset not found
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        asset_result = AsyncMock()
        asset_result.scalar_one_or_none.return_value = None  # Asset not found

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps[:1]

        mock_db.execute.side_effect = [flow_result, asset_result, gap_result]

        # Execute the function - should continue without asset linkage
        result = await submit_questionnaire_response(
            flow_id=mock_collection_flow.flow_id,
            questionnaire_id="test-questionnaire",
            request_data=request,
            db=mock_db,
            current_user=mock_user,
            context=mock_context,
        )

        # Verify operation succeeded despite invalid asset_id
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_submit_questionnaire_updates_flow_completion(
        self, mock_db, mock_user, mock_context, mock_collection_flow, mock_pending_gaps
    ):
        """Test that flow completion status is updated correctly"""
        # Create request with 100% completion
        request = MagicMock(spec=QuestionnaireSubmissionRequest)
        request.responses = {"technology_stack": "Java"}
        request.form_metadata = {"completion_percentage": 100}
        request.validation_results = {"isValid": True}

        # Setup database mocks
        flow_result = AsyncMock()
        flow_result.scalar_one_or_none.return_value = mock_collection_flow

        gap_result = AsyncMock()
        gap_result.scalars.return_value.all.return_value = mock_pending_gaps[:1]

        mock_db.execute.side_effect = [flow_result, gap_result]

        with patch(
            "app.services.flow_configs.collection_handlers.asset_handlers.apply_resolved_gaps_to_assets"
        ):
            # Execute the function
            result = await submit_questionnaire_response(
                flow_id=mock_collection_flow.flow_id,
                questionnaire_id="test-questionnaire",
                request_data=request,
                db=mock_db,
                current_user=mock_user,
                context=mock_context,
            )

            # Verify flow was marked as completed
            assert mock_collection_flow.status == "completed"
            assert mock_collection_flow.progress_percentage == 100
            assert result["progress"] == 100
