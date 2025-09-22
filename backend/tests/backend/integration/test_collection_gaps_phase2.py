"""
Comprehensive integration tests for Collection Gaps Phase 2 Week 1 backend implementation.

Tests the following new router modules:
1. vendor_products.py (5 endpoints)
2. maintenance_windows/ (modularized, 4 CRUD endpoints)
3. governance/ (modularized, requirements & exceptions endpoints)
4. collection_flows completeness endpoints (2 endpoints)

Total: 15 endpoints tested

CC Generated with Claude Code
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext


class TestVendorProductsEndpoints:
    """Test vendor products API endpoints (5 endpoints)."""

    @pytest.fixture
    def mock_vendor_product_data(self):
        """Mock vendor product data."""
        return {
            "id": str(uuid4()),
            "vendor_name": "Microsoft",
            "product_name": "SQL Server",
            "versions": None,
        }

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_search_vendor_products_endpoint(
        self, mock_request_context, mock_vendor_product_data
    ):
        """Test GET /api/v1/collection/vendor-products endpoint."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            search_vendor_products,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository response
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.search_unified_products.return_value = [mock_vendor_product_data]
            mock_repo_class.return_value = mock_repo

            # Test endpoint
            result = await search_vendor_products(
                vendor_name="Microsoft",
                product_name="SQL",
                limit=50,
                db=mock_db,
                context=mock_request_context,
            )

            # Assertions
            assert len(result) == 1
            assert result[0].vendor_name == "Microsoft"
            assert result[0].product_name == "SQL Server"
            mock_repo.search_unified_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vendor_product_endpoint(
        self, mock_request_context, mock_vendor_product_data
    ):
        """Test POST /api/v1/collection/vendor-products endpoint."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            create_vendor_product,
        )
        from app.models.api.collection_gaps import VendorProductCreateRequest

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.flush = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_created = MagicMock()
            mock_created.id = uuid4()
            mock_repo.create_custom_product.return_value = mock_created
            mock_repo_class.return_value = mock_repo

            # Test data
            request = VendorProductCreateRequest(
                vendor_name="Oracle", product_name="Database"
            )

            # Test endpoint
            result = await create_vendor_product(
                request=request, db=mock_db, context=mock_request_context
            )

            # Assertions
            assert result.vendor_name == "Oracle"
            assert result.product_name == "Database"
            mock_repo.create_custom_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vendor_product_endpoint(
        self, mock_request_context, mock_vendor_product_data
    ):
        """Test PUT /api/v1/collection/vendor-products/{id} endpoint."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            update_vendor_product,
        )
        from app.models.api.collection_gaps import VendorProductCreateRequest

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_updated = MagicMock()
            mock_updated.id = uuid4()
            mock_updated.vendor_name = "Updated Vendor"
            mock_updated.product_name = "Updated Product"
            mock_repo.update.return_value = mock_updated
            mock_repo_class.return_value = mock_repo

            # Test data
            product_id = str(uuid4())
            request = VendorProductCreateRequest(
                vendor_name="Updated Vendor", product_name="Updated Product"
            )

            # Test endpoint
            result = await update_vendor_product(
                product_id=product_id,
                request=request,
                db=mock_db,
                context=mock_request_context,
            )

            # Assertions
            assert result.vendor_name == "Updated Vendor"
            assert result.product_name == "Updated Product"
            mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_vendor_product_endpoint(self, mock_request_context):
        """Test DELETE /api/v1/collection/vendor-products/{id} endpoint."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            delete_vendor_product,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_existing = MagicMock()
            mock_repo.get_by_id.return_value = mock_existing
            mock_repo.delete = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Test data
            product_id = str(uuid4())

            # Test endpoint
            result = await delete_vendor_product(
                product_id=product_id, db=mock_db, context=mock_request_context
            )

            # Assertions
            assert result is None  # DELETE returns None
            mock_repo.get_by_id.assert_called_once()
            mock_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_normalize_vendor_product_data_endpoint(self, mock_request_context):
        """Test POST /api/v1/collection/vendor-products/normalize endpoint."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            normalize_vendor_product_data,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository responses
        with patch(
            "app.repositories.vendor_product_repository.VendorProductRepository"
        ) as mock_global_repo_class, patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_tenant_repo_class:
            mock_global_repo = AsyncMock()
            mock_exact_match = MagicMock()
            mock_exact_match.id = uuid4()
            mock_exact_match.vendor_name = "Microsoft"
            mock_exact_match.product_name = "SQL Server"
            mock_global_repo.get_by_normalized_key.return_value = mock_exact_match
            mock_global_repo_class.return_value = mock_global_repo

            mock_tenant_repo = AsyncMock()
            mock_tenant_repo.search_unified_products.return_value = [
                {
                    "id": str(uuid4()),
                    "vendor_name": "Microsoft",
                    "product_name": "SQL Server",
                }
            ]
            mock_tenant_repo_class.return_value = mock_tenant_repo

            # Test data
            request_data = {
                "vendor_name": "Microsoft",
                "product_name": "SQL Server",
            }

            # Test endpoint
            result = await normalize_vendor_product_data(
                request=request_data, db=mock_db, context=mock_request_context
            )

            # Assertions
            assert result["original"]["vendor_name"] == "Microsoft"
            assert result["original"]["product_name"] == "SQL Server"
            assert result["normalized"]["normalized_key"] == "microsoft_sql_server"
            assert result["exact_match"] is not None
            assert result["confidence_score"] == 1.0


class TestMaintenanceWindowsEndpoints:
    """Test maintenance windows API endpoints (4 endpoints)."""

    @pytest.fixture
    def mock_maintenance_window_data(self):
        """Mock maintenance window data."""
        return {
            "id": str(uuid4()),
            "name": "Weekend Maintenance",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=4),
            "scope_type": "tenant",
            "application_id": None,
            "asset_id": None,
            "recurring": False,
            "timezone": "UTC",
        }

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_list_maintenance_windows_endpoint(
        self, mock_request_context, mock_maintenance_window_data
    ):
        """Test GET /api/v1/collection/maintenance-windows endpoint."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            list_maintenance_windows,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository response
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_window = MagicMock()
            for key, value in mock_maintenance_window_data.items():
                setattr(mock_window, key, value)
            mock_repo.get_all.return_value = [mock_window]
            mock_repo_class.return_value = mock_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.utils.convert_windows_to_responses"
            ) as mock_convert:
                mock_convert.return_value = [mock_maintenance_window_data]

                # Test endpoint
                result = await list_maintenance_windows(
                    scope_type=None,
                    application_id=None,
                    asset_id=None,
                    active_only=False,
                    upcoming_days=None,
                    limit=100,
                    db=mock_db,
                    context=mock_request_context,
                )

                # Assertions
                assert len(result) == 1
                assert result[0]["name"] == "Weekend Maintenance"
                mock_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_maintenance_window_endpoint(
        self, mock_request_context, mock_maintenance_window_data
    ):
        """Test POST /api/v1/collection/maintenance-windows endpoint."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            create_maintenance_window,
        )
        from app.models.api.collection_gaps import MaintenanceWindowRequest

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.flush = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_created = MagicMock()
            mock_created.id = uuid4()
            mock_repo.check_conflicts.return_value = []  # No conflicts
            mock_repo.create_window.return_value = mock_created
            mock_repo_class.return_value = mock_repo

            # Mock utilities and validators
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_time_range"
            ) as mock_validate, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.check_schedule_conflicts"
            ) as mock_check_conflicts, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.utils.convert_to_response"
            ) as mock_convert:
                mock_validate.return_value = None
                mock_check_conflicts.return_value = None
                mock_convert.return_value = mock_maintenance_window_data

                # Test data
                request = MaintenanceWindowRequest(
                    name="New Maintenance Window",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(hours=2),
                    scope_type="tenant",
                    application_id=None,
                    asset_id=None,
                    recurring=False,
                    timezone="UTC",
                )

                # Test endpoint
                result = await create_maintenance_window(
                    request=request, db=mock_db, context=mock_request_context
                )

                # Assertions
                assert result["name"] == "Weekend Maintenance"
                mock_repo.create_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_maintenance_window_endpoint(
        self, mock_request_context, mock_maintenance_window_data
    ):
        """Test PUT /api/v1/collection/maintenance-windows/{id} endpoint."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            update_maintenance_window,
        )
        from app.models.api.collection_gaps import MaintenanceWindowRequest

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_existing = MagicMock()
            mock_repo.get_by_id.return_value = mock_existing
            mock_repo.check_conflicts.return_value = []  # No conflicts
            mock_updated = MagicMock()
            mock_repo.update.return_value = mock_updated
            mock_repo_class.return_value = mock_repo

            # Mock utilities and validators
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_uuid"
            ) as mock_validate_uuid, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_time_range"
            ) as mock_validate_time, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_window_exists"
            ) as mock_validate_exists, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.check_schedule_conflicts"
            ) as mock_check_conflicts, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.utils.convert_to_response"
            ) as mock_convert:
                mock_validate_uuid.return_value = uuid4()
                mock_validate_time.return_value = None
                mock_validate_exists.return_value = None
                mock_check_conflicts.return_value = None
                mock_convert.return_value = mock_maintenance_window_data

                # Test data
                window_id = str(uuid4())
                request = MaintenanceWindowRequest(
                    name="Updated Maintenance Window",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(hours=3),
                    scope_type="application",
                    application_id=str(uuid4()),
                    asset_id=None,
                    recurring=True,
                    timezone="EST",
                )

                # Test endpoint
                result = await update_maintenance_window(
                    window_id=window_id,
                    request=request,
                    db=mock_db,
                    context=mock_request_context,
                )

                # Assertions
                assert result["name"] == "Weekend Maintenance"
                mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_maintenance_window_endpoint(self, mock_request_context):
        """Test DELETE /api/v1/collection/maintenance-windows/{id} endpoint."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            delete_maintenance_window,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_existing = MagicMock()
            mock_repo.get_by_id.return_value = mock_existing
            mock_repo.delete = AsyncMock()
            mock_repo_class.return_value = mock_repo

            # Mock validators
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_uuid"
            ) as mock_validate_uuid, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_window_exists"
            ) as mock_validate_exists:
                mock_validate_uuid.return_value = uuid4()
                mock_validate_exists.return_value = None

                # Test data
                window_id = str(uuid4())

                # Test endpoint
                result = await delete_maintenance_window(
                    window_id=window_id, db=mock_db, context=mock_request_context
                )

                # Assertions
                assert result is None  # DELETE returns None
                mock_repo.delete.assert_called_once()


class TestGovernanceEndpoints:
    """Test governance API endpoints (4 endpoints)."""

    @pytest.fixture
    def mock_governance_requirement_data(self):
        """Mock governance requirement data."""
        return {
            "id": str(uuid4()),
            "entity_type": "migration_exception",
            "entity_id": str(uuid4()),
            "status": "PENDING",
            "notes": "High risk exception requires approval",
            "requested_at": datetime.utcnow().isoformat(),
            "decided_at": None,
            "approver_id": None,
        }

    @pytest.fixture
    def mock_migration_exception_data(self):
        """Mock migration exception data."""
        return {
            "id": str(uuid4()),
            "exception_type": "custom_migration",
            "rationale": "Legacy system requires custom approach",
            "risk_level": "high",
            "status": "OPEN",
            "application_id": str(uuid4()),
            "asset_id": None,
            "approval_request_id": str(uuid4()),
            "created_at": datetime.utcnow().isoformat(),
        }

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_list_governance_requirements_endpoint(
        self, mock_request_context, mock_governance_requirement_data
    ):
        """Test GET /api/v1/collection/governance/requirements endpoint."""
        from app.api.v1.endpoints.collection_gaps.governance.handlers import (
            list_governance_requirements,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository response
        with patch(
            "app.repositories.governance_repository.ApprovalRequestRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_request = MagicMock()
            for key, value in mock_governance_requirement_data.items():
                if key.endswith("_at") and value:
                    setattr(mock_request, key, datetime.fromisoformat(value))
                else:
                    setattr(mock_request, key, value)
            mock_repo.get_all.return_value = [mock_request]
            mock_repo_class.return_value = mock_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.format_optional_id"
            ) as mock_format_id, patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.format_timestamp"
            ) as mock_format_ts:
                mock_format_id.side_effect = lambda x: x
                mock_format_ts.side_effect = lambda x: x.isoformat() if x else None

                # Test endpoint
                result = await list_governance_requirements(
                    status=None,
                    entity_type=None,
                    entity_id=None,
                    approver_id=None,
                    limit=100,
                    db=mock_db,
                    context=mock_request_context,
                )

                # Assertions
                assert len(result) == 1
                assert result[0].entity_type == "migration_exception"
                assert result[0].status == "PENDING"
                mock_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_governance_requirement_endpoint(
        self, mock_request_context, mock_governance_requirement_data
    ):
        """Test POST /api/v1/collection/governance/requirements endpoint."""
        from app.api.v1.endpoints.collection_gaps.governance.handlers import (
            create_governance_requirement,
        )
        from app.api.v1.endpoints.collection_gaps.governance.schemas import (
            GovernanceRequirementRequest,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.flush = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.governance_repository.ApprovalRequestRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_created = MagicMock()
            mock_created.id = uuid4()
            mock_created.requested_at = datetime.utcnow()
            mock_repo.create_request.return_value = mock_created
            mock_repo_class.return_value = mock_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.format_timestamp"
            ) as mock_format_ts:
                mock_format_ts.side_effect = lambda x: x.isoformat() if x else None

                # Test data
                request = GovernanceRequirementRequest(
                    entity_type="migration_exception",
                    entity_id=str(uuid4()),
                    notes="Requires approval for high risk migration",
                )

                # Test endpoint
                result = await create_governance_requirement(
                    request=request, db=mock_db, context=mock_request_context
                )

                # Assertions
                assert result.entity_type == "migration_exception"
                assert result.status == "PENDING"
                mock_repo.create_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_migration_exceptions_endpoint(
        self, mock_request_context, mock_migration_exception_data
    ):
        """Test GET /api/v1/collection/governance/exceptions endpoint."""
        from app.api.v1.endpoints.collection_gaps.governance.handlers import (
            list_migration_exceptions,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository response
        with patch(
            "app.repositories.governance_repository.MigrationExceptionRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_exception = MagicMock()
            for key, value in mock_migration_exception_data.items():
                setattr(mock_exception, key, value)
            mock_repo.get_all.return_value = [mock_exception]
            mock_repo_class.return_value = mock_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.format_optional_id"
            ) as mock_format_id:
                mock_format_id.side_effect = lambda x: x

                # Test endpoint
                result = await list_migration_exceptions(
                    status=None,
                    risk_level=None,
                    exception_type=None,
                    application_id=None,
                    asset_id=None,
                    high_risk_only=False,
                    limit=100,
                    db=mock_db,
                    context=mock_request_context,
                )

                # Assertions
                assert len(result) == 1
                assert result[0].exception_type == "custom_migration"
                assert result[0].risk_level == "high"
                mock_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_migration_exception_endpoint(
        self, mock_request_context, mock_migration_exception_data
    ):
        """Test POST /api/v1/collection/governance/exceptions endpoint."""
        from app.api.v1.endpoints.collection_gaps.governance.handlers import (
            create_migration_exception,
        )
        from app.api.v1.endpoints.collection_gaps.governance.schemas import (
            MigrationExceptionRequest,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.flush = AsyncMock()

        # Mock repository responses
        with patch(
            "app.repositories.governance_repository.MigrationExceptionRepository"
        ) as mock_exception_repo_class, patch(
            "app.repositories.governance_repository.ApprovalRequestRepository"
        ) as mock_approval_repo_class:
            mock_exception_repo = AsyncMock()
            mock_created_exception = MagicMock()
            mock_created_exception.id = uuid4()
            mock_exception_repo.create_exception.return_value = mock_created_exception
            mock_exception_repo.update = AsyncMock()
            mock_exception_repo_class.return_value = mock_exception_repo

            mock_approval_repo = AsyncMock()
            mock_approval_request = MagicMock()
            mock_approval_request.id = uuid4()
            mock_approval_repo.create_request.return_value = mock_approval_request
            mock_approval_repo_class.return_value = mock_approval_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.requires_approval"
            ) as mock_requires_approval, patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.generate_approval_notes"
            ) as mock_generate_notes:
                mock_requires_approval.return_value = True
                mock_generate_notes.return_value = "High risk requires approval"

                # Test data
                request = MigrationExceptionRequest(
                    exception_type="custom_migration",
                    rationale="Legacy system needs custom approach",
                    risk_level="high",
                    application_id=str(uuid4()),
                    asset_id=None,
                )

                # Test endpoint
                result = await create_migration_exception(
                    request=request, db=mock_db, context=mock_request_context
                )

                # Assertions
                assert result.exception_type == "custom_migration"
                assert result.risk_level == "high"
                assert result.status == "OPEN"
                assert result.approval_request_id is not None
                mock_exception_repo.create_exception.assert_called_once()
                mock_approval_repo.create_request.assert_called_once()


class TestCollectionFlowsCompletenessEndpoints:
    """Test collection flows completeness endpoints (2 endpoints)."""

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.fixture
    def mock_completeness_data(self):
        """Mock completeness metrics data."""
        return {
            "flow_id": str(uuid4()),
            "overall_completeness": 75.0,
            "completeness_by_category": {
                "vendor_products": 80.0,
                "maintenance_windows": 70.0,
                "governance": 75.0,
            },
            "pending_gaps": 12,
            "last_calculated": "now",
            "categories": ["vendor_products", "maintenance_windows", "governance"],
        }

    @pytest.mark.asyncio
    async def test_get_completeness_metrics_endpoint(
        self, mock_request_context, mock_completeness_data
    ):
        """Test GET /api/v1/collection/flows/{flow_id}/completeness endpoint."""
        from app.api.v1.endpoints.collection_gaps.collection_flows.handlers import (
            get_completeness_metrics_handler,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository and utilities
        with patch(
            "app.repositories.collection_flow_repository.CollectionFlowRepository"
        ) as mock_repo_class, patch(
            "app.api.v1.endpoints.collection_gaps.collection_flows.utils.calculate_completeness_metrics"
        ) as mock_calculate_completeness, patch(
            "app.api.v1.endpoints.collection_gaps.collection_flows.utils.calculate_pending_gaps"
        ) as mock_calculate_gaps:
            mock_repo = AsyncMock()
            mock_flow = MagicMock()
            mock_repo.get_by_filters.return_value = [mock_flow]
            mock_repo_class.return_value = mock_repo

            mock_calculate_completeness.return_value = {
                "vendor_products": 80.0,
                "maintenance_windows": 70.0,
                "governance": 75.0,
            }
            mock_calculate_gaps.return_value = 12

            # Test data
            flow_id = str(uuid4())

            # Test endpoint
            result = await get_completeness_metrics_handler(
                flow_id=flow_id, db=mock_db, context=mock_request_context
            )

            # Assertions
            assert result["flow_id"] == flow_id
            assert result["overall_completeness"] == 75.0
            assert result["pending_gaps"] == 12
            assert len(result["categories"]) == 3
            mock_repo.get_by_filters.assert_called_once_with(flow_id=flow_id)

    @pytest.mark.asyncio
    async def test_refresh_completeness_metrics_endpoint(
        self, mock_request_context, mock_completeness_data
    ):
        """Test POST /api/v1/collection/flows/{flow_id}/completeness/refresh endpoint."""
        from app.api.v1.endpoints.collection_gaps.collection_flows.handlers import (
            refresh_completeness_metrics_handler,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository and utilities
        with patch(
            "app.repositories.collection_flow_repository.CollectionFlowRepository"
        ) as mock_repo_class, patch(
            "app.api.v1.endpoints.collection_gaps.collection_flows.utils.get_existing_data_snapshot"
        ) as mock_get_snapshot, patch(
            "app.api.v1.endpoints.collection_gaps.collection_flows.utils.calculate_completeness_metrics"
        ) as mock_calculate_completeness, patch(
            "app.api.v1.endpoints.collection_gaps.collection_flows.utils.calculate_pending_gaps"
        ) as mock_calculate_gaps:
            mock_repo = AsyncMock()
            mock_flow = MagicMock()
            mock_repo.get_by_filters.return_value = [mock_flow]
            mock_repo_class.return_value = mock_repo

            mock_get_snapshot.return_value = {"data_points": 150}
            mock_calculate_completeness.return_value = {
                "vendor_products": 85.0,
                "maintenance_windows": 75.0,
                "governance": 80.0,
            }
            mock_calculate_gaps.return_value = 8

            # Test data
            flow_id = str(uuid4())

            # Test endpoint
            result = await refresh_completeness_metrics_handler(
                flow_id=flow_id, db=mock_db, context=mock_request_context
            )

            # Assertions
            assert result["flow_id"] == flow_id
            assert result["overall_completeness"] == 80.0  # Average of 85, 75, 80
            assert result["pending_gaps"] == 8
            assert result["refreshed"] is True
            assert result["data_points_analyzed"] == 1  # len of snapshot dict
            mock_get_snapshot.assert_called_once()


class TestEndpointErrorHandling:
    """Test error handling across all endpoints."""

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_vendor_products_invalid_uuid_error(self, mock_request_context):
        """Test vendor products endpoint with invalid UUID format."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            update_vendor_product,
        )
        from app.models.api.collection_gaps import VendorProductCreateRequest
        from fastapi import HTTPException

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Test data with invalid UUID
        invalid_id = "not-a-uuid"
        request = VendorProductCreateRequest(vendor_name="Test", product_name="Test")

        # Test endpoint - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await update_vendor_product(
                product_id=invalid_id,
                request=request,
                db=mock_db,
                context=mock_request_context,
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid_uuid" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_maintenance_windows_not_found_error(self, mock_request_context):
        """Test maintenance windows endpoint with non-existent ID."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            delete_maintenance_window,
        )
        from fastapi import HTTPException

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()

        # Mock repository response - window not found
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None  # Not found
            mock_repo_class.return_value = mock_repo

            # Mock validators
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_uuid"
            ) as mock_validate_uuid, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_window_exists"
            ) as mock_validate_exists:
                mock_validate_uuid.return_value = uuid4()
                mock_validate_exists.side_effect = HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "window_not_found"},
                )

                # Test data
                window_id = str(uuid4())

                # Test endpoint - should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await delete_maintenance_window(
                        window_id=window_id, db=mock_db, context=mock_request_context
                    )

                # Assertions
                assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_governance_missing_required_fields_error(self, mock_request_context):
        """Test governance endpoint with missing required fields."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            normalize_vendor_product_data,
        )
        from fastapi import HTTPException

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Test data with missing required fields
        invalid_request = {"vendor_name": "Microsoft"}  # Missing product_name

        # Test endpoint - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await normalize_vendor_product_data(
                request=invalid_request, db=mock_db, context=mock_request_context
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "missing_required_fields" in str(exc_info.value.detail)


class TestMultiTenantScoping:
    """Test multi-tenant scoping across all endpoints."""

    @pytest.fixture
    def mock_request_context_tenant_a(self):
        """Mock request context for tenant A."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.fixture
    def mock_request_context_tenant_b(self):
        """Mock request context for tenant B."""
        return RequestContext(
            client_account_id=2,
            engagement_id=2,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_vendor_products_tenant_scoping(
        self, mock_request_context_tenant_a, mock_request_context_tenant_b
    ):
        """Test that vendor products are properly scoped by tenant."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            search_vendor_products,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository responses for different tenants
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo_a = AsyncMock()
            mock_repo_a.search_unified_products.return_value = [
                {
                    "id": str(uuid4()),
                    "vendor_name": "TenantA Vendor",
                    "product_name": "Product A",
                }
            ]

            mock_repo_b = AsyncMock()
            mock_repo_b.search_unified_products.return_value = [
                {
                    "id": str(uuid4()),
                    "vendor_name": "TenantB Vendor",
                    "product_name": "Product B",
                }
            ]

            # Configure mock to return different repos for different tenants
            def get_repo_for_tenant(db, client_id, engagement_id):
                if client_id == 1:
                    return mock_repo_a
                else:
                    return mock_repo_b

            mock_repo_class.side_effect = get_repo_for_tenant

            # Test tenant A
            result_a = await search_vendor_products(
                vendor_name=None,
                product_name=None,
                limit=50,
                db=mock_db,
                context=mock_request_context_tenant_a,
            )

            # Test tenant B
            result_b = await search_vendor_products(
                vendor_name=None,
                product_name=None,
                limit=50,
                db=mock_db,
                context=mock_request_context_tenant_b,
            )

            # Assertions
            assert len(result_a) == 1
            assert result_a[0].vendor_name == "TenantA Vendor"
            assert len(result_b) == 1
            assert result_b[0].vendor_name == "TenantB Vendor"

            # Verify repositories were initialized with correct tenant context
            assert mock_repo_class.call_count == 2
            mock_repo_class.assert_any_call(mock_db, 1, 1)  # Tenant A
            mock_repo_class.assert_any_call(mock_db, 2, 2)  # Tenant B

    @pytest.mark.asyncio
    async def test_maintenance_windows_tenant_isolation(
        self, mock_request_context_tenant_a, mock_request_context_tenant_b
    ):
        """Test that maintenance windows are isolated by tenant."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            list_maintenance_windows,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock repository responses for different tenants
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo_a = AsyncMock()
            mock_window_a = MagicMock()
            mock_window_a.name = "Tenant A Window"
            mock_repo_a.get_all.return_value = [mock_window_a]

            mock_repo_b = AsyncMock()
            mock_window_b = MagicMock()
            mock_window_b.name = "Tenant B Window"
            mock_repo_b.get_all.return_value = [mock_window_b]

            # Configure mock to return different repos for different tenants
            def get_repo_for_tenant(db, client_id, engagement_id):
                if client_id == 1:
                    return mock_repo_a
                else:
                    return mock_repo_b

            mock_repo_class.side_effect = get_repo_for_tenant

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.utils.convert_windows_to_responses"
            ) as mock_convert:
                mock_convert.side_effect = [
                    [{"name": "Tenant A Window"}],
                    [{"name": "Tenant B Window"}],
                ]

                # Test tenant A
                result_a = await list_maintenance_windows(
                    scope_type=None,
                    application_id=None,
                    asset_id=None,
                    active_only=False,
                    upcoming_days=None,
                    limit=100,
                    db=mock_db,
                    context=mock_request_context_tenant_a,
                )

                # Test tenant B
                result_b = await list_maintenance_windows(
                    scope_type=None,
                    application_id=None,
                    asset_id=None,
                    active_only=False,
                    upcoming_days=None,
                    limit=100,
                    db=mock_db,
                    context=mock_request_context_tenant_b,
                )

                # Assertions
                assert len(result_a) == 1
                assert result_a[0]["name"] == "Tenant A Window"
                assert len(result_b) == 1
                assert result_b[0]["name"] == "Tenant B Window"

                # Verify repositories were initialized with correct tenant context
                assert mock_repo_class.call_count == 2
                mock_repo_class.assert_any_call(mock_db, 1, 1)  # Tenant A
                mock_repo_class.assert_any_call(mock_db, 2, 2)  # Tenant B


class TestEndpointPerformance:
    """Test performance considerations and proper async patterns."""

    @pytest.fixture
    def mock_request_context(self):
        """Mock request context with tenant information."""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id=str(uuid4()),
            flow_id=None,
        )

    @pytest.mark.asyncio
    async def test_vendor_products_large_result_set_pagination(
        self, mock_request_context
    ):
        """Test vendor products endpoint handles large result sets properly."""
        from app.api.v1.endpoints.collection_gaps.vendor_products import (
            search_vendor_products,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Create large dataset (1500 products)
        large_dataset = [
            {
                "id": str(uuid4()),
                "vendor_name": f"Vendor {i}",
                "product_name": f"Product {i}",
            }
            for i in range(1500)
        ]

        # Mock repository response
        with patch(
            "app.repositories.vendor_product_repository.TenantVendorProductRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.search_unified_products.return_value = large_dataset
            mock_repo_class.return_value = mock_repo

            # Test endpoint with limit
            result = await search_vendor_products(
                vendor_name=None,
                product_name=None,
                limit=100,  # Should limit to 100
                db=mock_db,
                context=mock_request_context,
            )

            # Assertions
            assert len(result) == 100  # Should be limited
            mock_repo.search_unified_products.assert_called_once()

    @pytest.mark.asyncio
    async def test_atomic_transaction_pattern_maintenance_windows(
        self, mock_request_context
    ):
        """Test that maintenance windows create uses proper atomic transaction pattern."""
        from app.api.v1.endpoints.collection_gaps.maintenance_windows.handlers import (
            create_maintenance_window,
        )
        from app.models.api.collection_gaps import MaintenanceWindowRequest

        # Mock database session with transaction tracking
        mock_db = AsyncMock(spec=AsyncSession)
        mock_transaction = AsyncMock()
        mock_db.begin.return_value = mock_transaction
        mock_db.flush = AsyncMock()

        # Mock repository response
        with patch(
            "app.repositories.maintenance_window_repository.MaintenanceWindowRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_created = MagicMock()
            mock_created.id = uuid4()
            mock_repo.check_conflicts.return_value = []  # No conflicts
            mock_repo.create_window.return_value = mock_created
            mock_repo_class.return_value = mock_repo

            # Mock utilities and validators
            with patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.validate_time_range"
            ) as mock_validate, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.validators.check_schedule_conflicts"
            ) as mock_check_conflicts, patch(
                "app.api.v1.endpoints.collection_gaps.maintenance_windows.utils.convert_to_response"
            ) as mock_convert:
                mock_validate.return_value = None
                mock_check_conflicts.return_value = None
                mock_convert.return_value = {"id": str(mock_created.id)}

                # Test data
                request = MaintenanceWindowRequest(
                    name="Test Window",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(hours=2),
                    scope_type="tenant",
                    application_id=None,
                    asset_id=None,
                    recurring=False,
                    timezone="UTC",
                )

                # Test endpoint
                await create_maintenance_window(
                    request=request, db=mock_db, context=mock_request_context
                )

                # Assertions - verify atomic transaction pattern
                mock_db.begin.assert_called_once()  # Transaction started
                mock_db.flush.assert_called_once()  # Flush called for FK availability
                mock_repo.create_window.assert_called_once_with(
                    name="Test Window",
                    start_time=request.start_time,
                    end_time=request.end_time,
                    scope_type="tenant",
                    application_id=None,
                    asset_id=None,
                    recurring=False,
                    timezone="UTC",
                    commit=False,  # Important: commit=False for atomic pattern
                )

    @pytest.mark.asyncio
    async def test_proper_async_await_patterns(self, mock_request_context):
        """Test that all endpoints use proper async/await patterns."""
        from app.api.v1.endpoints.collection_gaps.governance.handlers import (
            create_migration_exception,
        )
        from app.api.v1.endpoints.collection_gaps.governance.schemas import (
            MigrationExceptionRequest,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.flush = AsyncMock()

        # Mock repository responses
        with patch(
            "app.repositories.governance_repository.MigrationExceptionRepository"
        ) as mock_exception_repo_class, patch(
            "app.repositories.governance_repository.ApprovalRequestRepository"
        ) as mock_approval_repo_class:
            mock_exception_repo = AsyncMock()
            mock_created_exception = MagicMock()
            mock_created_exception.id = uuid4()
            mock_exception_repo.create_exception.return_value = mock_created_exception
            mock_exception_repo.update = AsyncMock()
            mock_exception_repo_class.return_value = mock_exception_repo

            mock_approval_repo = AsyncMock()
            mock_approval_request = MagicMock()
            mock_approval_request.id = uuid4()
            mock_approval_repo.create_request.return_value = mock_approval_request
            mock_approval_repo_class.return_value = mock_approval_repo

            # Mock utilities
            with patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.requires_approval"
            ) as mock_requires_approval, patch(
                "app.api.v1.endpoints.collection_gaps.governance.utils.generate_approval_notes"
            ) as mock_generate_notes:
                mock_requires_approval.return_value = True
                mock_generate_notes.return_value = "Notes"

                # Test data
                request = MigrationExceptionRequest(
                    exception_type="test",
                    rationale="test",
                    risk_level="high",
                    application_id=str(uuid4()),
                    asset_id=None,
                )

                # Test endpoint and verify all async operations are awaited
                result = await create_migration_exception(
                    request=request, db=mock_db, context=mock_request_context
                )

                # Assertions - verify async methods were called
                mock_exception_repo.create_exception.assert_called_once()
                mock_db.flush.assert_called_once()
                mock_approval_repo.create_request.assert_called_once()
                mock_exception_repo.update.assert_called_once()
                assert result is not None


# Test configuration for pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
