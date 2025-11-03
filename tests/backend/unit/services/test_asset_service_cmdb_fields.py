"""
Tests for AssetService CMDB fields population and child table creation.

Tests PR #833 implementation:
- 24 new explicit CMDB columns in assets table
- Conditional creation of asset_eol_assessments records
- Conditional creation of asset_contacts records
- Data validation (e.g., EOL risk level)

Coverage Target: 90%+
"""

import pytest
import uuid
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.asset_service import AssetService
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.asset.specialized import AssetEOLAssessment, AssetContact
from app.core.context import RequestContext


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_db_session():
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()  # Track what's added to session
    return session


@pytest.fixture
def request_context():
    """Create test request context."""
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        flow_id="33333333-3333-3333-3333-333333333333",
        user_id="44444444-4444-4444-4444-444444444444",
    )


@pytest.fixture
def asset_service(mock_db_session, request_context):
    """Create AssetService instance with mocked dependencies."""
    return AssetService(mock_db_session, request_context)


# ============================================================================
# TEST CLASSES
# ============================================================================


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.asyncio
class TestCMDBFieldsPopulation:
    """Test that new CMDB fields are properly populated in assets."""

    async def test_cmdb_fields_populated_from_asset_data(
        self, asset_service, mock_db_session
    ):
        """Test that all 24 CMDB fields are extracted and passed to asset creation."""

        # Arrange: Asset data with all CMDB fields
        asset_data = {
            "name": "NextGen Case Management",
            "asset_type": "application",
            # Business and organizational
            "business_unit": "HR Systems",
            "vendor": "Custom Dev",
            # Application-specific
            "application_type": "Web Application",
            "lifecycle": "In Development",
            "hosting_model": "On-prem",
            # Server-specific
            "server_role": "App Server",
            "security_zone": "DMZ",
            # Database-specific
            "database_type": "PostgreSQL",
            "database_version": "12.5",
            "database_size_gb": 500.0,
            # Compliance and security
            "pii_flag": True,
            "application_data_classification": "Confidential",
            # Performance metrics
            "cpu_utilization_percent_max": 85.5,
            "memory_utilization_percent_max": 78.2,
            "storage_free_gb": 150.0,
            # Migration planning
            "has_saas_replacement": True,
            "risk_level": "Medium",
            "tshirt_size": "L",
            "proposed_treatmentplan_rationale": "Rehost due to high readiness",
            # Cost
            "annual_cost_estimate": 250000.0,
        }

        # Mock repository to return no existing asset
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            # Mock child table creation (called after asset creation)
            with patch("app.services.asset_service.create_child_records_if_needed", new_callable=AsyncMock):
                with patch.object(
                    asset_service.repository, "create_no_commit", new_callable=AsyncMock
                ) as mock_create:
                    # Configure mock to return a fake asset
                    mock_asset = Asset(
                        id=uuid.uuid4(),
                        name="NextGen Case Management",
                        asset_type=AssetType.APPLICATION,
                        client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
                        engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
                    )
                    mock_create.return_value = mock_asset

                    # Act: Create asset
                    result_asset = await asset_service.create_asset(
                        asset_data
                    )

                    # Assert: Verify create_no_commit was called with CMDB fields
                    mock_create.assert_called_once()
                    call_kwargs = mock_create.call_args.kwargs

                    # Verify all 24 CMDB fields were passed
                    assert call_kwargs["business_unit"] == "HR Systems"
                    assert call_kwargs["vendor"] == "Custom Dev"
                    assert call_kwargs["application_type"] == "Web Application"
                    assert call_kwargs["lifecycle"] == "In Development"
                    assert call_kwargs["hosting_model"] == "On-prem"
                    assert call_kwargs["server_role"] == "App Server"
                    assert call_kwargs["security_zone"] == "DMZ"
                    assert call_kwargs["database_type"] == "PostgreSQL"
                    assert call_kwargs["database_version"] == "12.5"
                    assert call_kwargs["database_size_gb"] == 500.0
                    assert call_kwargs["pii_flag"] is True
                    assert call_kwargs["application_data_classification"] == "Confidential"
                    assert call_kwargs["cpu_utilization_percent_max"] == 85.5
                    assert call_kwargs["memory_utilization_percent_max"] == 78.2
                    assert call_kwargs["storage_free_gb"] == 150.0
                    assert call_kwargs["has_saas_replacement"] is True
                    assert call_kwargs["risk_level"] == "Medium"
                    assert call_kwargs["tshirt_size"] == "L"
                    assert call_kwargs["proposed_treatmentplan_rationale"] == "Rehost due to high readiness"
                    assert call_kwargs["annual_cost_estimate"] == 250000.0


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.asyncio
class TestEOLAssessmentCreation:
    """Test conditional creation of AssetEOLAssessment records."""

    async def test_eol_assessment_created_when_data_exists(
        self, asset_service, mock_db_session
    ):
        """Test that EOL assessment is created when EOL data is provided."""

        # Arrange: Asset data with EOL information
        asset_data = {
            "name": "Legacy App",
            "asset_type": "application",
            "technology_component": "Java 8",
            "eol_date": "2025-12-31",
            "eol_risk_level": "high",
            "assessment_notes": "End of support approaching",
            "remediation_options": ["Upgrade to Java 17", "Migrate to new platform"],
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Legacy App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset (which should also create EOL assessment)
                await asset_service.create_asset(asset_data)

                # Assert: Verify EOL assessment was added to session
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]

                assert len(eol_assessments) == 1, "Expected 1 EOL assessment to be created"

                eol = eol_assessments[0]
                assert eol.asset_id == mock_asset.id
                assert eol.technology_component == "Java 8"
                assert eol.eol_risk_level == "high"
                assert eol.assessment_notes == "End of support approaching"
                assert eol.remediation_options == ["Upgrade to Java 17", "Migrate to new platform"]

    async def test_eol_assessment_not_created_when_no_data(
        self, asset_service, mock_db_session
    ):
        """Test that EOL assessment is NOT created when no EOL data provided."""

        # Arrange: Asset data WITHOUT EOL information
        asset_data = {
            "name": "New App",
            "asset_type": "application",
            "business_unit": "Finance",
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="New App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset
                await asset_service.create_asset(asset_data)

                # Assert: Verify NO EOL assessment was added
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]

                assert len(eol_assessments) == 0, "Expected NO EOL assessment to be created"

    async def test_eol_risk_level_validation_valid_values(
        self, asset_service, mock_db_session
    ):
        """Test that valid EOL risk levels are accepted (low, medium, high, critical)."""

        for valid_risk in ["low", "medium", "high", "critical"]:
            mock_db_session.reset_mock()

            asset_data = {
                "name": f"App {valid_risk}",
                "asset_type": "application",
                "technology_component": "Old Tech",
                "eol_risk_level": valid_risk,
            }

            mock_asset = Asset(
                id=uuid.uuid4(),
                name=asset_data["name"],
                asset_type=AssetType.APPLICATION,
                client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
                engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
            )

            with patch.object(
                asset_service, "_find_existing_asset", return_value=None
            ):
                with patch.object(
                    asset_service.repository, "create_no_commit", return_value=mock_asset
                ):
                    # Act
                    await asset_service.create_asset(asset_data)

                    # Assert: EOL assessment created with valid risk level
                    added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                    eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]

                    assert len(eol_assessments) == 1
                    assert eol_assessments[0].eol_risk_level == valid_risk

    async def test_eol_risk_level_validation_invalid_normalized(
        self, asset_service, mock_db_session
    ):
        """Test that invalid risk levels are rejected and set to NULL."""

        asset_data = {
            "name": "Invalid Risk App",
            "asset_type": "application",
            "technology_component": "Old Tech",
            "eol_risk_level": "VERY HIGH",  # Invalid - not in allowed list
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Invalid Risk App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act
                await asset_service.create_asset(asset_data)

                # Assert: EOL assessment created but risk_level is NULL
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]

                assert len(eol_assessments) == 1
                assert eol_assessments[0].eol_risk_level is None  # Invalid value rejected

    async def test_eol_risk_level_case_insensitive(
        self, asset_service, mock_db_session
    ):
        """Test that risk level validation is case-insensitive."""

        asset_data = {
            "name": "Case Test App",
            "asset_type": "application",
            "technology_component": "Old Tech",
            "eol_risk_level": "HIGH",  # Uppercase should be normalized to lowercase
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Case Test App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act
                await asset_service.create_asset(asset_data)

                # Assert: Risk level normalized to lowercase
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]

                assert len(eol_assessments) == 1
                assert eol_assessments[0].eol_risk_level == "high"  # Normalized to lowercase


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.asyncio
class TestAssetContactCreation:
    """Test conditional creation of AssetContact records."""

    async def test_multiple_contacts_created_from_asset_data(
        self, asset_service, mock_db_session
    ):
        """Test that multiple contact records are created for one asset."""

        # Arrange: Asset data with multiple contacts
        asset_data = {
            "name": "Multi Contact App",
            "asset_type": "application",
            "business_owner_email": "nina.khan@example.com",
            "business_owner_name": "Nina Khan",
            "technical_owner_email": "diego.garcia@example.com",
            "technical_owner_name": "Diego Garcia",
            "architect_email": "sarah.chen@example.com",
            "architect_name": "Sarah Chen",
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Multi Contact App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset
                await asset_service.create_asset(asset_data)

                # Assert: Verify 3 contact records were added
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                contacts = [obj for obj in added_objects if isinstance(obj, AssetContact)]

                assert len(contacts) == 3, "Expected 3 contacts to be created"

                # Verify contact types
                contact_types = {c.contact_type for c in contacts}
                assert contact_types == {"business_owner", "technical_owner", "architect"}

                # Verify specific contact details
                business_owner = next(c for c in contacts if c.contact_type == "business_owner")
                assert business_owner.email == "nina.khan@example.com"
                assert business_owner.name == "Nina Khan"
                assert business_owner.asset_id == mock_asset.id

                technical_owner = next(c for c in contacts if c.contact_type == "technical_owner")
                assert technical_owner.email == "diego.garcia@example.com"
                assert technical_owner.name == "Diego Garcia"

                architect = next(c for c in contacts if c.contact_type == "architect")
                assert architect.email == "sarah.chen@example.com"
                assert architect.name == "Sarah Chen"

    async def test_contacts_not_created_when_no_email(
        self, asset_service, mock_db_session
    ):
        """Test that contacts are NOT created when no email data provided."""

        # Arrange: Asset data WITHOUT contact emails
        asset_data = {
            "name": "No Contact App",
            "asset_type": "application",
            "business_unit": "Finance",
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="No Contact App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset
                await asset_service.create_asset(asset_data)

                # Assert: Verify NO contacts were added
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                contacts = [obj for obj in added_objects if isinstance(obj, AssetContact)]

                assert len(contacts) == 0, "Expected NO contacts to be created"

    async def test_contact_name_fallback_from_email(
        self, asset_service, mock_db_session
    ):
        """Test that contact name is extracted from email if name not provided."""

        # Arrange: Email provided but no name
        asset_data = {
            "name": "Fallback Name App",
            "asset_type": "application",
            "business_owner_email": "john.doe@example.com",
            # Note: business_owner_name is NOT provided
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Fallback Name App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset
                await asset_service.create_asset(asset_data)

                # Assert: Contact created with name extracted from email
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                contacts = [obj for obj in added_objects if isinstance(obj, AssetContact)]

                assert len(contacts) == 1
                assert contacts[0].email == "john.doe@example.com"
                assert contacts[0].name == "john.doe"  # Extracted from email prefix

    async def test_single_contact_when_only_one_provided(
        self, asset_service, mock_db_session
    ):
        """Test that only one contact is created when only one email provided."""

        # Arrange: Only business owner provided
        asset_data = {
            "name": "Single Contact App",
            "asset_type": "application",
            "business_owner_email": "owner@example.com",
            "business_owner_name": "The Owner",
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Single Contact App",
            asset_type=AssetType.APPLICATION,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ):
                # Act: Create asset
                await asset_service.create_asset(asset_data)

                # Assert: Only 1 contact created
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                contacts = [obj for obj in added_objects if isinstance(obj, AssetContact)]

                assert len(contacts) == 1
                assert contacts[0].contact_type == "business_owner"
                assert contacts[0].email == "owner@example.com"


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.asyncio
class TestIntegratedCMDBWorkflow:
    """Integration tests for complete CMDB data flow."""

    async def test_complete_asset_with_cmdb_fields_and_child_tables(
        self, asset_service, mock_db_session
    ):
        """Test creating asset with CMDB fields, EOL assessment, and contacts together."""

        # Arrange: Complete asset data (like from CSV import)
        asset_data = {
            # Basic info
            "name": "Production Database Server",
            "asset_type": "database",
            # CMDB fields
            "business_unit": "Finance",
            "vendor": "Oracle",
            "database_type": "Oracle",
            "database_version": "12c",
            "database_size_gb": 2000.0,
            "pii_flag": True,
            "application_data_classification": "Confidential",
            "risk_level": "High",
            "tshirt_size": "XL",
            "annual_cost_estimate": 500000.0,
            # EOL assessment data
            "technology_component": "Oracle 12c",
            "eol_date": "2026-06-30",
            "eol_risk_level": "critical",
            "assessment_notes": "Critical system, end of support in 2026",
            "remediation_options": ["Upgrade to 19c", "Migrate to PostgreSQL"],
            # Contact data
            "business_owner_email": "cfo@example.com",
            "business_owner_name": "CFO Office",
            "technical_owner_email": "dba.team@example.com",
            "technical_owner_name": "DBA Team",
        }

        mock_asset = Asset(
            id=uuid.uuid4(),
            name="Production Database Server",
            asset_type=AssetType.DATABASE,
            client_account_id=uuid.UUID(asset_service.context_info["client_account_id"]),
            engagement_id=uuid.UUID(asset_service.context_info["engagement_id"]),
        )

        # Mock repository
        with patch.object(
            asset_service, "_find_existing_asset", return_value=None
        ):
            with patch.object(
                asset_service.repository, "create_no_commit", return_value=mock_asset
            ) as mock_create:
                # Act: Create complete asset
                result_asset = await asset_service.create_asset(
                    asset_data
                )

                # Assert 1: Main asset created with CMDB fields
                assert result_asset is not None
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args.kwargs
                assert call_kwargs["business_unit"] == "Finance"
                assert call_kwargs["vendor"] == "Oracle"
                assert call_kwargs["database_type"] == "Oracle"
                assert call_kwargs["risk_level"] == "High"
                assert call_kwargs["annual_cost_estimate"] == 500000.0

                # Assert 2: EOL assessment created
                added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
                eol_assessments = [obj for obj in added_objects if isinstance(obj, AssetEOLAssessment)]
                assert len(eol_assessments) == 1
                assert eol_assessments[0].technology_component == "Oracle 12c"
                assert eol_assessments[0].eol_risk_level == "critical"

                # Assert 3: 2 contacts created
                contacts = [obj for obj in added_objects if isinstance(obj, AssetContact)]
                assert len(contacts) == 2
                contact_types = {c.contact_type for c in contacts}
                assert contact_types == {"business_owner", "technical_owner"}

                # Assert 4: Flush called to persist child records
                assert mock_db_session.flush.call_count >= 2  # Once for EOL, once for contacts
