"""
Unit Tests for Discovery Flow Service

Tests the key methods in the discovery flow service without database operations,
transaction management, or tenant isolation complexity.

Coverage:
- DiscoveryFlowService class methods
- create_discovery_flow
- create_or_get_discovery_flow
- get_flow_by_id
- update_phase_completion
- complete_discovery_flow
- get_active_flows
- get_completed_flows
- get_flow_assets
- get_assets_by_type
- validate_asset
- delete_flow
- get_flow_summary
- get_flow_health_report
- get_multi_flow_summary
- bulk_validate_assets
- get_assets_requiring_review
- filter_flow_assets
- update_asset_quality_scores
- _create_assets_from_inventory
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.discovery_flow_service.discovery_flow_service import DiscoveryFlowService
from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow
from app.models.asset import Asset


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_context():
    """Mock RequestContext"""
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="33333333-3333-3333-3333-333333333333",
    )


@pytest.fixture
def sample_discovery_flow():
    """Sample DiscoveryFlow object"""
    flow = Mock(spec=DiscoveryFlow)
    flow.id = uuid.uuid4()
    flow.flow_id = "55555555-5555-5555-5555-555555555555"
    flow.flow_name = "Test Discovery Flow"
    flow.status = "running"
    flow.current_phase = "data_validation"
    flow.progress_percentage = 25.0
    return flow


@pytest.fixture
def sample_asset():
    """Sample Asset object"""
    asset = Mock(spec=Asset)
    asset.id = uuid.uuid4()
    asset.name = "Test Server"
    asset.asset_type = "server"
    asset.confidence_score = 0.85
    asset.quality_score = 0.90
    return asset


@pytest.fixture
def sample_raw_data():
    """Sample raw data for discovery flow"""
    return [
        {"hostname": "server1", "ip": "192.168.1.1", "type": "server"},
        {"hostname": "server2", "ip": "192.168.1.2", "type": "database"},
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for discovery flow"""
    return {
        "source": "data_import",
        "import_id": "44444444-4444-4444-4444-444444444444",
        "detected_columns": ["hostname", "ip", "type"],
    }


class TestDiscoveryFlowService:
    """Test DiscoveryFlowService class"""

    def test_initialization(self, mock_db_session, mock_context):
        """Test service initialization with modular components"""
        service = DiscoveryFlowService(mock_db_session, mock_context)

        assert service.db == mock_db_session
        assert service.context == mock_context
        assert service.flow_manager is not None
        assert service.asset_manager is not None
        assert service.summary_manager is not None

    @pytest.mark.asyncio
    async def test_create_discovery_flow_success(
        self, mock_db_session, mock_context, sample_raw_data, sample_metadata, sample_discovery_flow
    ):
        """Test successful discovery flow creation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "create_discovery_flow") as mock_create:
            mock_create.return_value = sample_discovery_flow

            result = await service.create_discovery_flow(
                flow_id=flow_id,
                raw_data=sample_raw_data,
                metadata=sample_metadata,
                data_import_id="44444444-4444-4444-4444-444444444444",
                user_id="33333333-3333-3333-3333-333333333333",
                master_flow_id="66666666-6666-6666-6666-666666666666",
            )

            assert result == sample_discovery_flow
            mock_create.assert_called_once_with(
                flow_id=flow_id,
                raw_data=sample_raw_data,
                metadata=sample_metadata,
                data_import_id="44444444-4444-4444-4444-444444444444",
                user_id="33333333-3333-3333-3333-333333333333",
                master_flow_id="66666666-6666-6666-6666-666666666666",
            )

    @pytest.mark.asyncio
    async def test_create_or_get_discovery_flow_success(
        self, mock_db_session, mock_context, sample_raw_data, sample_metadata, sample_discovery_flow
    ):
        """Test successful create or get discovery flow"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "create_or_get_discovery_flow") as mock_create_or_get:
            mock_create_or_get.return_value = sample_discovery_flow

            result = await service.create_or_get_discovery_flow(
                flow_id=flow_id,
                raw_data=sample_raw_data,
                metadata=sample_metadata,
                data_import_id="44444444-4444-4444-4444-444444444444",
                user_id="33333333-3333-3333-3333-333333333333",
            )

            assert result == sample_discovery_flow
            mock_create_or_get.assert_called_once_with(
                flow_id=flow_id,
                raw_data=sample_raw_data,
                metadata=sample_metadata,
                data_import_id="44444444-4444-4444-4444-444444444444",
                user_id="33333333-3333-3333-3333-333333333333",
            )

    @pytest.mark.asyncio
    async def test_get_flow_by_id_success(self, mock_db_session, mock_context, sample_discovery_flow):
        """Test successful flow retrieval by ID"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            result = await service.get_flow_by_id(flow_id)

            assert result == sample_discovery_flow
            mock_get_flow.assert_called_once_with(flow_id)

    @pytest.mark.asyncio
    async def test_get_flow_by_id_not_found(self, mock_db_session, mock_context):
        """Test handling when flow is not found"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = None

            result = await service.get_flow_by_id(flow_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_update_phase_completion_success(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test successful phase completion update"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        phase = "data_validation"
        phase_data = {"validation_results": {"status": "passed"}}
        crew_status = {"crew_id": "crew123", "status": "completed"}
        agent_insights = [{"agent": "validator", "insight": "Data is valid"}]

        with patch.object(service.flow_manager, "update_phase_completion") as mock_update:
            mock_update.return_value = sample_discovery_flow

            result = await service.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                phase_data=phase_data,
                crew_status=crew_status,
                agent_insights=agent_insights,
            )

            assert result == sample_discovery_flow
            mock_update.assert_called_once_with(
                flow_id=flow_id,
                phase=phase,
                phase_data=phase_data,
                crew_status=crew_status,
                agent_insights=agent_insights,
            )

    @pytest.mark.asyncio
    async def test_complete_discovery_flow_success(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test successful discovery flow completion"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "complete_discovery_flow") as mock_complete:
            mock_complete.return_value = sample_discovery_flow

            result = await service.complete_discovery_flow(flow_id)

            assert result == sample_discovery_flow
            mock_complete.assert_called_once_with(flow_id)

    @pytest.mark.asyncio
    async def test_get_active_flows_success(self, mock_db_session, mock_context, sample_discovery_flow):
        """Test successful retrieval of active flows"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flows = [sample_discovery_flow]

        with patch.object(service.flow_manager, "get_active_flows") as mock_get_active:
            mock_get_active.return_value = flows

            result = await service.get_active_flows()

            assert result == flows
            mock_get_active.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_completed_flows_success(self, mock_db_session, mock_context, sample_discovery_flow):
        """Test successful retrieval of completed flows"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flows = [sample_discovery_flow]
        limit = 5

        with patch.object(service.flow_manager, "get_completed_flows") as mock_get_completed:
            mock_get_completed.return_value = flows

            result = await service.get_completed_flows(limit)

            assert result == flows
            mock_get_completed.assert_called_once_with(limit)

    @pytest.mark.asyncio
    async def test_get_flow_assets_success(
        self, mock_db_session, mock_context, sample_discovery_flow, sample_asset
    ):
        """Test successful retrieval of flow assets"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        assets = [sample_asset]

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.asset_manager, "get_flow_assets") as mock_get_assets:
                mock_get_assets.return_value = assets

                result = await service.get_flow_assets(flow_id)

                assert result == assets
                mock_get_flow.assert_called_once_with(flow_id)
                mock_get_assets.assert_called_once_with(flow_id, sample_discovery_flow.id)

    @pytest.mark.asyncio
    async def test_get_flow_assets_flow_not_found(self, mock_db_session, mock_context):
        """Test handling when flow is not found for asset retrieval"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await service.get_flow_assets(flow_id)

            assert f"Discovery flow not found: {flow_id}" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_assets_by_type_success(self, mock_db_session, mock_context, sample_asset):
        """Test successful retrieval of assets by type"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        asset_type = "server"
        assets = [sample_asset]

        with patch.object(service.asset_manager, "get_assets_by_type") as mock_get_assets:
            mock_get_assets.return_value = assets

            result = await service.get_assets_by_type(asset_type)

            assert result == assets
            mock_get_assets.assert_called_once_with(asset_type)

    @pytest.mark.asyncio
    async def test_validate_asset_success(self, mock_db_session, mock_context, sample_asset):
        """Test successful asset validation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        asset_id = sample_asset.id
        validation_status = "validated"
        validation_results = {"confidence": 0.95, "issues": []}

        with patch.object(service.asset_manager, "validate_asset") as mock_validate:
            mock_validate.return_value = sample_asset

            result = await service.validate_asset(
                asset_id=asset_id,
                validation_status=validation_status,
                validation_results=validation_results,
            )

            assert result == sample_asset
            mock_validate.assert_called_once_with(
                asset_id=asset_id,
                validation_status=validation_status,
                validation_results=validation_results,
            )

    @pytest.mark.asyncio
    async def test_delete_flow_success(self, mock_db_session, mock_context):
        """Test successful flow deletion"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service.flow_manager, "delete_flow") as mock_delete:
            mock_delete.return_value = True

            result = await service.delete_flow(flow_id)

            assert result is True
            mock_delete.assert_called_once_with(flow_id)

    @pytest.mark.asyncio
    async def test_get_flow_summary_success(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test successful flow summary generation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        summary = {"flow_id": flow_id, "status": "running", "progress": 25.0}

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.summary_manager, "get_flow_summary") as mock_get_summary:
                mock_get_summary.return_value = summary

                result = await service.get_flow_summary(flow_id)

                assert result == summary
                mock_get_flow.assert_called_once_with(flow_id)
                mock_get_summary.assert_called_once_with(sample_discovery_flow)

    @pytest.mark.asyncio
    async def test_get_flow_summary_flow_not_found(self, mock_db_session, mock_context):
        """Test handling when flow is not found for summary generation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await service.get_flow_summary(flow_id)

            assert f"Discovery flow not found: {flow_id}" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_flow_health_report_success(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test successful flow health report generation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        health_report = {"flow_id": flow_id, "health_score": 0.85, "issues": []}

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.summary_manager, "get_flow_health_report") as mock_get_health:
                mock_get_health.return_value = health_report

                result = await service.get_flow_health_report(flow_id)

                assert result == health_report
                mock_get_flow.assert_called_once_with(flow_id)
                mock_get_health.assert_called_once_with(sample_discovery_flow)

    @pytest.mark.asyncio
    async def test_get_multi_flow_summary_with_flow_ids(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test multi-flow summary with specific flow IDs"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_ids = ["55555555-5555-5555-5555-555555555555", "66666666-6666-6666-6666-666666666666"]
        flows = [sample_discovery_flow]
        summary = {"total_flows": 1, "active_flows": 1}

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.summary_manager, "get_multi_flow_summary") as mock_get_summary:
                mock_get_summary.return_value = summary

                result = await service.get_multi_flow_summary(flow_ids)

                assert result == summary
                mock_get_summary.assert_called_once_with(flows)

    @pytest.mark.asyncio
    async def test_get_multi_flow_summary_without_flow_ids(
        self, mock_db_session, mock_context, sample_discovery_flow
    ):
        """Test multi-flow summary without specific flow IDs"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flows = [sample_discovery_flow]
        summary = {"total_flows": 1, "active_flows": 1}

        with patch.object(service, "get_active_flows") as mock_get_active:
            mock_get_active.return_value = flows

            with patch.object(service.summary_manager, "get_multi_flow_summary") as mock_get_summary:
                mock_get_summary.return_value = summary

                result = await service.get_multi_flow_summary()

                assert result == summary
                mock_get_active.assert_called_once()
                mock_get_summary.assert_called_once_with(flows)

    @pytest.mark.asyncio
    async def test_bulk_validate_assets_success(self, mock_db_session, mock_context, sample_asset):
        """Test successful bulk asset validation"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        asset_ids = [sample_asset.id, uuid.uuid4()]
        validation_status = "validated"
        validation_results = {"batch_id": "batch123"}
        assets = [sample_asset]

        with patch.object(service.asset_manager, "bulk_validate_assets") as mock_bulk_validate:
            mock_bulk_validate.return_value = assets

            result = await service.bulk_validate_assets(
                asset_ids=asset_ids,
                validation_status=validation_status,
                validation_results=validation_results,
            )

            assert result == assets
            mock_bulk_validate.assert_called_once_with(
                asset_ids=asset_ids,
                validation_status=validation_status,
                validation_results=validation_results,
            )

    @pytest.mark.asyncio
    async def test_get_assets_requiring_review_with_flow_id(
        self, mock_db_session, mock_context, sample_discovery_flow, sample_asset
    ):
        """Test getting assets requiring review for specific flow"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        min_confidence_threshold = 0.7
        sample_asset.confidence_score = 0.5  # Below threshold
        assets = [sample_asset]

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.asset_manager, "get_flow_assets") as mock_get_assets:
                mock_get_assets.return_value = assets

                result = await service.get_assets_requiring_review(flow_id, min_confidence_threshold)

                assert result == assets
                mock_get_flow.assert_called_once_with(flow_id)
                mock_get_assets.assert_called_once_with(flow_id, sample_discovery_flow.id)

    @pytest.mark.asyncio
    async def test_get_assets_requiring_review_without_flow_id(
        self, mock_db_session, mock_context, sample_asset
    ):
        """Test getting assets requiring review without specific flow"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        min_confidence_threshold = 0.7
        assets = [sample_asset]

        with patch.object(service.asset_manager, "get_assets_requiring_review") as mock_get_assets:
            mock_get_assets.return_value = assets

            result = await service.get_assets_requiring_review(min_confidence_threshold=min_confidence_threshold)

            assert result == assets
            mock_get_assets.assert_called_once_with(min_confidence_threshold)

    @pytest.mark.asyncio
    async def test_filter_flow_assets_success(
        self, mock_db_session, mock_context, sample_discovery_flow, sample_asset
    ):
        """Test successful asset filtering by criteria"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        flow_id = "55555555-5555-5555-5555-555555555555"
        criteria = {"asset_type": "server", "confidence_score": {"min": 0.8}}
        assets = [sample_asset]

        with patch.object(service, "get_flow_by_id") as mock_get_flow:
            mock_get_flow.return_value = sample_discovery_flow

            with patch.object(service.asset_manager, "filter_assets_by_criteria") as mock_filter:
                mock_filter.return_value = assets

                result = await service.filter_flow_assets(flow_id, criteria)

                assert result == assets
                mock_get_flow.assert_called_once_with(flow_id)
                mock_filter.assert_called_once_with(sample_discovery_flow.id, criteria)

    @pytest.mark.asyncio
    async def test_update_asset_quality_scores_success(
        self, mock_db_session, mock_context, sample_asset
    ):
        """Test successful asset quality scores update"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        asset_id = sample_asset.id
        quality_score = 0.95
        confidence_score = 0.90

        with patch.object(service.asset_manager, "update_asset_quality_scores") as mock_update:
            mock_update.return_value = sample_asset

            result = await service.update_asset_quality_scores(
                asset_id=asset_id,
                quality_score=quality_score,
                confidence_score=confidence_score,
            )

            assert result == sample_asset
            mock_update.assert_called_once_with(
                asset_id=asset_id,
                quality_score=quality_score,
                confidence_score=confidence_score,
            )

    @pytest.mark.asyncio
    async def test_create_assets_from_inventory_success(
        self, mock_db_session, mock_context, sample_discovery_flow, sample_asset
    ):
        """Test successful asset creation from inventory"""
        service = DiscoveryFlowService(mock_db_session, mock_context)
        asset_data_list = [{"name": "server1", "type": "server"}]
        assets = [sample_asset]

        with patch.object(service.asset_manager, "create_assets_from_discovery") as mock_create:
            mock_create.return_value = assets

            result = await service._create_assets_from_inventory(sample_discovery_flow, asset_data_list)

            assert result == assets
            mock_create.assert_called_once_with(
                discovery_flow_id=sample_discovery_flow.id,
                asset_data_list=asset_data_list,
                discovered_in_phase="inventory",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
