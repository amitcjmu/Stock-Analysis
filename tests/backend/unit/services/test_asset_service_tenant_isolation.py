"""
Unit tests for tenant isolation in AssetService child table helpers.

Verifies that child table creation (EOL assessments, contacts) properly
uses RequestContext for tenant scoping and does not rely on asset object.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.request_context import RequestContext
from app.services.asset_service.child_table_helpers import (
    create_eol_assessment,
    create_contacts_if_exists,
    create_child_records_if_needed,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestTenantIsolation:
    """Test tenant isolation in child table helpers"""

    async def test_eol_assessment_uses_context_not_asset(
        self,
        mock_async_session,  # From conftest
        test_client_account_id,  # From conftest
        test_engagement_id,  # From conftest
    ):
        """Verify EOL assessment uses RequestContext for tenant IDs, not asset"""

        # Create mock asset with DIFFERENT tenant IDs (simulating wrong tenant)
        mock_asset = MagicMock()
        mock_asset.id = uuid.uuid4()
        mock_asset.name = "Test Asset"
        mock_asset.client_account_id = uuid.uuid4()  # Wrong tenant!
        mock_asset.engagement_id = uuid.uuid4()  # Wrong engagement!

        # Context has the CORRECT tenant IDs (from fixtures - source of truth)
        context = RequestContext(
            client_account_id=test_client_account_id,  # From fixture
            engagement_id=test_engagement_id,  # From fixture
        )

        asset_data = {
            "eol_date": "2025-12-31",
            "eol_risk_level": "high",
        }

        # Execute
        await create_eol_assessment(
            mock_async_session, mock_asset, asset_data, context
        )

        # Verify the created EOL assessment used context, NOT asset
        mock_async_session.add.assert_called_once()
        created_eol = mock_async_session.add.call_args[0][0]

        # CRITICAL: Verify tenant IDs come from context, not asset
        assert created_eol.client_account_id == test_client_account_id
        assert created_eol.engagement_id == test_engagement_id
        assert created_eol.client_account_id != mock_asset.client_account_id
        assert created_eol.engagement_id != mock_asset.engagement_id

    async def test_contact_creation_uses_context_not_asset(
        self,
        mock_async_session,  # From conftest
        test_client_account_id,  # From conftest
        test_engagement_id,  # From conftest
    ):
        """Verify contact creation uses RequestContext for tenant IDs, not asset"""

        # Create mock asset with DIFFERENT tenant IDs (simulating wrong tenant)
        mock_asset = MagicMock()
        mock_asset.id = uuid.uuid4()
        mock_asset.name = "Test Asset"
        mock_asset.client_account_id = uuid.uuid4()  # Wrong tenant!
        mock_asset.engagement_id = uuid.uuid4()  # Wrong engagement!

        # Context has the CORRECT tenant IDs (from fixtures - source of truth)
        context = RequestContext(
            client_account_id=test_client_account_id,  # From fixture
            engagement_id=test_engagement_id,  # From fixture
        )

        asset_data = {
            "business_owner_email": "owner@example.com",
            "business_owner_name": "John Doe",
        }

        # Execute
        await create_contacts_if_exists(
            mock_async_session, mock_asset, asset_data, context
        )

        # Verify the created contact used context, NOT asset
        mock_async_session.add.assert_called_once()
        created_contact = mock_async_session.add.call_args[0][0]

        # CRITICAL: Verify tenant IDs come from context, not asset
        assert created_contact.client_account_id == test_client_account_id
        assert created_contact.engagement_id == test_engagement_id
        assert created_contact.client_account_id != mock_asset.client_account_id
        assert created_contact.engagement_id != mock_asset.engagement_id

    async def test_child_records_pass_context_to_helpers(
        self,
        mock_async_session,  # From conftest
        test_client_account_id,  # From conftest
        test_engagement_id,  # From conftest
    ):
        """Verify orchestrator passes RequestContext to individual helpers"""

        mock_asset = MagicMock()
        mock_asset.id = uuid.uuid4()
        mock_asset.name = "Test Asset"

        # Use fixtures for context (source of truth)
        context = RequestContext(
            client_account_id=test_client_account_id,
            engagement_id=test_engagement_id,
        )

        asset_data = {
            "eol_date": "2025-12-31",
            "business_owner_email": "owner@example.com",
        }

        # Patch the individual helper functions to verify they're called with context
        with patch(
            "app.services.asset_service.child_table_helpers.create_eol_assessment",
            new_callable=AsyncMock,
        ) as mock_eol:
            with patch(
                "app.services.asset_service.child_table_helpers.create_contacts_if_exists",
                new_callable=AsyncMock,
            ) as mock_contacts:

                # Execute
                await create_child_records_if_needed(
                    mock_async_session, mock_asset, asset_data, context
                )

                # Verify context was passed to both helpers
                mock_eol.assert_called_once_with(
                    mock_async_session, mock_asset, asset_data, context
                )
                mock_contacts.assert_called_once_with(
                    mock_async_session, mock_asset, asset_data, context
                )
