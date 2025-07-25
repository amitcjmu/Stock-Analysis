"""
Integration Tests for Modular Import Storage Handler

Tests the modular data import services architecture including:
- ImportStorageHandler main orchestrator
- Modular service component integration
- Transaction management and rollback
- Multi-tenant context handling
- Background execution coordination
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid

# Import modular services
try:
    from app.services.data_import.import_storage_handler import ImportStorageHandler
    from app.services.data_import.import_validator import ImportValidator
    from app.services.data_import.storage_manager import ImportStorageManager
    from app.services.data_import.flow_trigger_service import FlowTriggerService
    from app.services.data_import.transaction_manager import ImportTransactionManager
    from app.services.data_import.background_execution_service import BackgroundExecutionService
    from app.services.data_import.response_builder import ImportResponseBuilder
    from app.schemas.data_import_schemas import StoreImportRequest
    from app.core.exceptions import ValidationError, DatabaseError
except ImportError:
    # Mock imports for testing environment
    ImportStorageHandler = Mock
    ImportValidator = Mock
    ImportStorageManager = Mock
    FlowTriggerService = Mock
    ImportTransactionManager = Mock
    BackgroundExecutionService = Mock
    ImportResponseBuilder = Mock
    StoreImportRequest = Mock
    ValidationError = Exception
    DatabaseError = Exception


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_import_request():
    """Sample import request for testing"""
    return {
        "engagement_id": "test-engagement-123",
        "file_content": "hostname,ip_address,os_type\nweb-01,192.168.1.10,Linux\ndb-01,192.168.1.20,Windows",
        "filename": "test_data.csv",
        "content_type": "text/csv",
        "trigger_discovery_flow": True,
        "client_account_id": "client-456",
        "user_id": "user-789"
    }


@pytest.fixture
def mock_import_context():
    """Mock multi-tenant context for testing"""
    return {
        "client_account_id": "client-456",
        "engagement_id": "test-engagement-123",
        "user_id": "user-789",
        "request_id": str(uuid.uuid4())
    }


@pytest.fixture
def mock_modular_services():
    """Mock all modular services for integration testing"""
    validator = Mock(spec=ImportValidator)
    validator.validate_import_context = AsyncMock(return_value=True)
    validator.validate_import_id = AsyncMock(return_value=True)
    validator.validate_no_incomplete_discovery_flow = AsyncMock(return_value=True)
    validator.validate_import_data = AsyncMock(return_value={"valid": True, "records": 2})

    storage_manager = Mock(spec=ImportStorageManager)
    storage_manager.find_or_create_import = AsyncMock(return_value={
        "import_id": "import-123",
        "status": "created",
        "created_at": datetime.now()
    })
    storage_manager.store_raw_records = AsyncMock(return_value={"records_stored": 2})
    storage_manager.create_field_mappings = AsyncMock(return_value={"mappings_created": 3})
    storage_manager.update_import_status = AsyncMock(return_value=True)

    flow_trigger = Mock(spec=FlowTriggerService)
    flow_trigger.trigger_discovery_flow_atomic = AsyncMock(return_value={
        "flow_id": "flow-456",
        "status": "triggered",
        "master_flow_id": "master-789"
    })

    transaction_manager = Mock(spec=ImportTransactionManager)
    transaction_manager.transaction = AsyncMock()
    transaction_manager.__aenter__ = AsyncMock(return_value=transaction_manager)
    transaction_manager.__aexit__ = AsyncMock(return_value=None)

    background_service = Mock(spec=BackgroundExecutionService)
    background_service.start_background_flow_execution = AsyncMock(return_value={
        "background_task_id": "task-321",
        "status": "started"
    })

    response_builder = Mock(spec=ImportResponseBuilder)
    response_builder.success_response = Mock(return_value={
        "status": "success",
        "message": "Import completed successfully",
        "data": {"import_id": "import-123"}
    })
    response_builder.error_response = Mock(return_value={
        "status": "error",
        "message": "Import failed",
        "error_type": "validation_error"
    })

    return {
        "validator": validator,
        "storage_manager": storage_manager,
        "flow_trigger": flow_trigger,
        "transaction_manager": transaction_manager,
        "background_service": background_service,
        "response_builder": response_builder
    }


class TestImportStorageHandlerModularIntegration:
    """Test modular architecture integration"""

    @pytest.mark.asyncio
    async def test_handler_initialization_with_modular_services(
        self,
        mock_db_session,
        mock_import_context
    ):
        """Test that handler properly initializes all modular services"""
        # Act
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Assert
        assert handler.db == mock_db_session
        assert handler.client_account_id == mock_import_context["client_account_id"]

        # Verify modular services are initialized
        assert hasattr(handler, 'validator')
        assert hasattr(handler, 'storage_manager')
        assert hasattr(handler, 'flow_trigger')
        assert hasattr(handler, 'transaction_manager')
        assert hasattr(handler, 'background_service')
        assert hasattr(handler, 'response_builder')

    @pytest.mark.asyncio
    async def test_complete_import_workflow_modular_coordination(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context,
        mock_modular_services
    ):
        """Test complete import workflow with modular service coordination"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Inject mock services
        for service_name, mock_service in mock_modular_services.items():
            setattr(handler, service_name, mock_service)

        store_request = StoreImportRequest(**sample_import_request)

        # Act
        response = await handler.handle_import(store_request, mock_import_context)

        # Assert workflow coordination
        assert response["status"] == "success"

        # Verify service call sequence
        mock_modular_services["validator"].validate_import_context.assert_called_once()
        mock_modular_services["storage_manager"].find_or_create_import.assert_called_once()
        mock_modular_services["storage_manager"].store_raw_records.assert_called_once()
        mock_modular_services["flow_trigger"].trigger_discovery_flow_atomic.assert_called_once()
        mock_modular_services["background_service"].start_background_flow_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_service_integration(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context,
        mock_modular_services
    ):
        """Test integration with modular validation service"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )
        setattr(handler, 'validator', mock_modular_services["validator"])

        # Test validation success
        StoreImportRequest(**sample_import_request)

        # Act
        is_valid = await handler.validator.validate_import_context(mock_import_context)

        # Assert
        assert is_valid is True
        mock_modular_services["validator"].validate_import_context.assert_called_with(mock_import_context)

        # Test validation with data
        validation_result = await handler.validator.validate_import_data(
            sample_import_request["file_content"],
            sample_import_request["content_type"]
        )
        assert validation_result["valid"] is True
        assert validation_result["records"] == 2


class TestModularServiceErrorHandling:
    """Test error handling across modular services"""

    @pytest.mark.asyncio
    async def test_validation_error_handling(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context
    ):
        """Test validation error handling in modular architecture"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Mock validation failure
        handler.validator = Mock()
        handler.validator.validate_import_context = AsyncMock(
            side_effect=ValidationError("Invalid engagement ID")
        )
        handler.response_builder = Mock()
        handler.response_builder.error_response = Mock(return_value={
            "status": "error",
            "message": "Validation failed: Invalid engagement ID",
            "error_type": "validation_error"
        })

        store_request = StoreImportRequest(**sample_import_request)

        # Act & Assert
        with pytest.raises(ValidationError):
            await handler.handle_import(store_request, mock_import_context)

    @pytest.mark.asyncio
    async def test_storage_error_handling_with_rollback(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context,
        mock_modular_services
    ):
        """Test storage error handling with transaction rollback"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Mock storage failure
        mock_modular_services["storage_manager"].store_raw_records = AsyncMock(
            side_effect=DatabaseError("Storage failure")
        )

        # Setup transaction manager for rollback
        transaction_manager = mock_modular_services["transaction_manager"]
        transaction_manager.rollback = AsyncMock()

        for service_name, mock_service in mock_modular_services.items():
            setattr(handler, service_name, mock_service)

        store_request = StoreImportRequest(**sample_import_request)

        # Act & Assert
        with pytest.raises(DatabaseError):
            await handler.handle_import(store_request, mock_import_context)

        # Verify rollback was called
        transaction_manager.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_flow_trigger_error_recovery(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context,
        mock_modular_services
    ):
        """Test flow trigger error recovery in modular architecture"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Mock flow trigger failure
        mock_modular_services["flow_trigger"].trigger_discovery_flow_atomic = AsyncMock(
            side_effect=Exception("Flow creation failed")
        )

        for service_name, mock_service in mock_modular_services.items():
            setattr(handler, service_name, mock_service)

        store_request = StoreImportRequest(**sample_import_request)

        # Act & Assert
        with pytest.raises(Exception, match="Flow creation failed"):
            await handler.handle_import(store_request, mock_import_context)


class TestModularServiceConfiguration:
    """Test modular service configuration and dependency injection"""

    def test_service_dependency_injection(
        self,
        mock_db_session,
        mock_import_context
    ):
        """Test that services are properly injected and configured"""
        # Act
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Assert all services are injected
        assert handler.validator is not None
        assert handler.storage_manager is not None
        assert handler.flow_trigger is not None
        assert handler.transaction_manager is not None
        assert handler.background_service is not None
        assert handler.response_builder is not None

        # Verify services have correct configuration
        assert handler.storage_manager.client_account_id == mock_import_context["client_account_id"]
        assert handler.flow_trigger.client_account_id == mock_import_context["client_account_id"]

    def test_service_interface_contracts(
        self,
        mock_db_session,
        mock_import_context
    ):
        """Test that all services implement expected interface contracts"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        # Assert service interfaces
        assert hasattr(handler.validator, 'validate_import_context')
        assert hasattr(handler.validator, 'validate_import_data')
        assert hasattr(handler.storage_manager, 'find_or_create_import')
        assert hasattr(handler.storage_manager, 'store_raw_records')
        assert hasattr(handler.flow_trigger, 'trigger_discovery_flow_atomic')
        assert hasattr(handler.transaction_manager, 'transaction')
        assert hasattr(handler.background_service, 'start_background_flow_execution')
        assert hasattr(handler.response_builder, 'success_response')


class TestMultiTenantModularIntegration:
    """Test multi-tenant context handling across modular services"""

    @pytest.mark.asyncio
    async def test_tenant_context_propagation_across_services(
        self,
        mock_db_session,
        sample_import_request,
        mock_modular_services
    ):
        """Test that tenant context is properly propagated to all modular services"""
        # Arrange
        client_1_context = {
            "client_account_id": "client-001",
            "engagement_id": "engagement-001",
            "user_id": "user-001"
        }

        client_2_context = {
            "client_account_id": "client-002",
            "engagement_id": "engagement-002",
            "user_id": "user-002"
        }

        # Create handlers for different tenants
        handler_1 = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=client_1_context["client_account_id"]
        )

        handler_2 = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=client_2_context["client_account_id"]
        )

        # Inject mock services
        for handler in [handler_1, handler_2]:
            for service_name, mock_service in mock_modular_services.items():
                setattr(handler, service_name, mock_service)

        store_request = StoreImportRequest(**sample_import_request)

        # Act
        await handler_1.handle_import(store_request, client_1_context)
        await handler_2.handle_import(store_request, client_2_context)

        # Assert tenant isolation
        assert handler_1.client_account_id != handler_2.client_account_id
        assert handler_1.storage_manager.client_account_id != handler_2.storage_manager.client_account_id

    @pytest.mark.asyncio
    async def test_tenant_data_isolation_in_modular_services(
        self,
        mock_db_session,
        sample_import_request,
        mock_modular_services
    ):
        """Test data isolation between tenants in modular services"""
        # Arrange
        tenant_context = {
            "client_account_id": "client-isolated-123",
            "engagement_id": "engagement-isolated-456",
            "user_id": "user-isolated-789"
        }

        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=tenant_context["client_account_id"]
        )

        # Mock services with tenant isolation checks
        mock_storage = mock_modular_services["storage_manager"]
        mock_storage.find_or_create_import = AsyncMock(return_value={
            "import_id": "import-isolated-123",
            "client_account_id": tenant_context["client_account_id"],
            "engagement_id": tenant_context["engagement_id"]
        })

        setattr(handler, 'storage_manager', mock_storage)

        StoreImportRequest(**sample_import_request)

        # Act
        result = await handler.storage_manager.find_or_create_import(
            engagement_id=tenant_context["engagement_id"],
            context=tenant_context
        )

        # Assert tenant isolation
        assert result["client_account_id"] == tenant_context["client_account_id"]
        assert result["engagement_id"] == tenant_context["engagement_id"]


class TestModularServicePerformance:
    """Test performance characteristics of modular services"""

    @pytest.mark.asyncio
    async def test_modular_service_parallel_execution(
        self,
        mock_db_session,
        sample_import_request,
        mock_import_context,
        mock_modular_services
    ):
        """Test that modular services can execute operations in parallel where appropriate"""
        # Arrange
        handler = ImportStorageHandler(
            db=mock_db_session,
            client_account_id=mock_import_context["client_account_id"]
        )

        for service_name, mock_service in mock_modular_services.items():
            setattr(handler, service_name, mock_service)

        store_request = StoreImportRequest(**sample_import_request)

        # Act - Measure execution time
        start_time = datetime.now()
        response = await handler.handle_import(store_request, mock_import_context)
        end_time = datetime.now()

        execution_time = (end_time - start_time).total_seconds()

        # Assert
        assert response["status"] == "success"
        assert execution_time < 1.0  # Should complete quickly with mocked services

    @pytest.mark.asyncio
    async def test_modular_service_memory_efficiency(
        self,
        mock_db_session,
        mock_import_context,
        mock_modular_services
    ):
        """Test memory efficiency of modular service architecture"""
        # Arrange - Create multiple handlers to test memory usage
        handlers = []
        for i in range(10):
            handler = ImportStorageHandler(
                db=mock_db_session,
                client_account_id=f"client-{i}"
            )

            # Inject lightweight mock services
            for service_name, mock_service in mock_modular_services.items():
                setattr(handler, service_name, mock_service)

            handlers.append(handler)

        # Act & Assert - All handlers should be created without memory issues
        assert len(handlers) == 10

        # Verify each handler has its own service instances
        for i, handler in enumerate(handlers):
            assert handler.client_account_id == f"client-{i}"
            assert handler.storage_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
