#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Master Flow Orchestrator Components
MFO-028: Write unit tests for all components with 90% coverage target

This test suite covers:
- Master Flow Orchestrator
- Enhanced Flow State Manager  
- Multi-Tenant Flow Manager
- Flow Type Registry
- Validator Registry
- Handler Registry
- Flow Error Handler
- Performance Tracker
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.context import RequestContext
from app.core.exceptions import ValidationError
from app.services.crewai_flows.enhanced_flow_state_manager import (
    EncryptionConfig,
    EnhancedFlowStateManager,
    SerializationConfig,
    StateEncryption,
    StateEncryptionError,
    StateSerializationError,
    StateSerializer,
)
from app.services.flow_error_handler import ErrorStrategy, FlowErrorHandler
from app.services.flow_type_registry import FlowTypeConfig, FlowTypeRegistry, PhaseConfig
from app.services.handler_registry import HandlerRegistry

# Test imports
from app.services.master_flow_orchestrator import FlowOperationType, MasterFlowOrchestrator
from app.services.multi_tenant_flow_manager import (
    MultiTenantFlowManager,
    TenantIsolationError,
    TenantIsolationLevel,
    TenantMetrics,
    TenantQuota,
    TenantQuotaExceededError,
)
from app.services.performance_tracker import PerformanceTracker
from app.services.validator_registry import ValidatorRegistry


class TestMasterFlowOrchestrator:
    """Test Master Flow Orchestrator functionality"""
    
    @pytest.fixture
    async def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_context(self):
        """Mock request context"""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id="test-user"
        )
    
    @pytest.fixture
    async def orchestrator(self, mock_db, mock_context):
        """Create orchestrator instance for testing"""
        with patch('app.services.master_flow_orchestrator.CrewAIFlowStateExtensionsRepository') as mock_repo:
            mock_repo.return_value = AsyncMock()
            orchestrator = MasterFlowOrchestrator(mock_db, mock_context)
            return orchestrator
    
    @pytest.mark.asyncio
    async def test_create_flow_success(self, orchestrator):
        """Test successful flow creation"""
        # Mock registry
        orchestrator.flow_registry.is_registered = Mock(return_value=True)
        mock_config = Mock()
        mock_config.display_name = "Test Flow"
        mock_config.default_configuration = {"test": True}
        mock_config.initialization_handler = None
        orchestrator.flow_registry.get_flow_config = Mock(return_value=mock_config)
        
        # Mock repository
        mock_flow = Mock()
        mock_flow.to_dict.return_value = {"flow_id": "test-flow-123", "status": "created"}
        orchestrator.master_repo.create_master_flow = AsyncMock(return_value=mock_flow)
        
        # Mock performance tracker
        orchestrator.performance_tracker.start_operation = Mock(return_value="track-123")
        orchestrator.performance_tracker.end_operation = Mock()
        
        # Test flow creation
        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name="Test Discovery Flow",
            configuration={"env": "test"}
        )
        
        assert flow_id is not None
        assert isinstance(flow_details, dict)
        orchestrator.master_repo.create_master_flow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_flow_invalid_type(self, orchestrator):
        """Test flow creation with invalid type"""
        orchestrator.flow_registry.is_registered = Mock(return_value=False)
        
        with pytest.raises(ValueError, match="Unknown flow type"):
            await orchestrator.create_flow(flow_type="invalid_type")
    
    @pytest.mark.asyncio
    async def test_execute_phase_success(self, orchestrator):
        """Test successful phase execution"""
        # Mock flow retrieval
        mock_flow = Mock()
        mock_flow.flow_type = "discovery"
        mock_flow.flow_status = "running"
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        
        # Mock flow config
        mock_config = Mock()
        mock_phase_config = Mock()
        mock_phase_config.completion_handler = None
        mock_config.get_phase_config = Mock(return_value=mock_phase_config)
        orchestrator.flow_registry.get_flow_config = Mock(return_value=mock_config)
        
        # Mock validation
        orchestrator._run_phase_validators = AsyncMock(return_value={"valid": True, "errors": []})
        
        # Mock crew execution
        orchestrator._execute_crew_phase = AsyncMock(return_value={"status": "completed", "results": {}})
        
        # Mock repository updates
        orchestrator.master_repo.update_flow_status = AsyncMock()
        
        # Mock performance tracking
        orchestrator.performance_tracker.start_operation = Mock(return_value="track-123")
        orchestrator.performance_tracker.end_operation = Mock()
        
        # Test phase execution
        result = await orchestrator.execute_phase(
            flow_id="test-flow-123",
            phase_name="data_import",
            phase_input={"test": "data"}
        )
        
        assert result["phase"] == "data_import"
        assert result["status"] == "completed"
        orchestrator.master_repo.update_flow_status.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_phase_flow_not_found(self, orchestrator):
        """Test phase execution with non-existent flow"""
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Flow not found"):
            await orchestrator.execute_phase("non-existent-flow", "test_phase")
    
    @pytest.mark.asyncio
    async def test_pause_flow_success(self, orchestrator):
        """Test successful flow pausing"""
        mock_flow = Mock()
        mock_flow.flow_status = "running"
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        orchestrator.master_repo.update_flow_status = AsyncMock()
        
        result = await orchestrator.pause_flow("test-flow-123", "testing")
        
        assert result["status"] == "paused"
        assert result["reason"] == "testing"
        orchestrator.master_repo.update_flow_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_flow_success(self, orchestrator):
        """Test successful flow resuming"""
        mock_flow = Mock()
        mock_flow.flow_status = "paused"
        mock_flow.flow_persistence_data = {"last_completed_phase": "data_import"}
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        orchestrator.master_repo.update_flow_status = AsyncMock()
        
        # Mock flow config
        mock_config = Mock()
        mock_config.get_next_phase = Mock(return_value="field_mapping")
        orchestrator.flow_registry.get_flow_config = Mock(return_value=mock_config)
        
        result = await orchestrator.resume_flow("test-flow-123")
        
        assert result["status"] == "resumed"
        assert "resume_phase" in result
        orchestrator.master_repo.update_flow_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_flow_soft_delete(self, orchestrator):
        """Test soft delete flow"""
        mock_flow = Mock()
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        orchestrator.master_repo.update_flow_status = AsyncMock()
        
        result = await orchestrator.delete_flow("test-flow-123", soft_delete=True)
        
        assert result["deleted"] is True
        assert result["soft_delete"] is True
        orchestrator.master_repo.update_flow_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_flow_hard_delete(self, orchestrator):
        """Test hard delete flow"""
        mock_flow = Mock()
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        orchestrator.master_repo.delete_master_flow = AsyncMock(return_value=True)
        
        result = await orchestrator.delete_flow("test-flow-123", soft_delete=False)
        
        assert result["deleted"] is True
        assert result["soft_delete"] is False
        orchestrator.master_repo.delete_master_flow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_flow_status_success(self, orchestrator):
        """Test get flow status"""
        mock_flow = Mock()
        mock_flow.flow_type = "discovery"
        mock_flow.flow_name = "Test Flow"
        mock_flow.flow_status = "running"
        mock_flow.created_at = datetime.utcnow()
        mock_flow.updated_at = datetime.utcnow()
        mock_flow.flow_configuration = {"test": True}
        mock_flow.phase_execution_times = {"data_import": 1000}
        mock_flow.get_performance_summary = Mock(return_value={"avg_time": 1000})
        mock_flow.agent_collaboration_log = []
        mock_flow.flow_persistence_data = {}
        
        orchestrator.master_repo.get_by_flow_id = AsyncMock(return_value=mock_flow)
        
        # Mock flow config
        mock_config = Mock()
        mock_config.phases = [Mock(name="data_import"), Mock(name="field_mapping")]
        orchestrator.flow_registry.get_flow_config = Mock(return_value=mock_config)
        
        # Mock performance tracking
        orchestrator.performance_tracker.start_operation = Mock(return_value="track-123")
        orchestrator.performance_tracker.end_operation = Mock()
        
        result = await orchestrator.get_flow_status("test-flow-123", include_details=True)
        
        assert result["flow_id"] == "test-flow-123"
        assert result["status"] == "running"
        assert "phases" in result
        assert "performance" in result
    
    @pytest.mark.asyncio
    async def test_get_active_flows_success(self, orchestrator):
        """Test get active flows"""
        mock_flows = [
            Mock(flow_id="flow-1", flow_type="discovery", flow_name="Flow 1", 
                 flow_status="running", created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
            Mock(flow_id="flow-2", flow_type="assessment", flow_name="Flow 2",
                 flow_status="paused", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        ]
        
        orchestrator.master_repo.get_active_flows = AsyncMock(return_value=mock_flows)
        
        result = await orchestrator.get_active_flows(limit=10)
        
        assert len(result) == 2
        assert result[0]["flow_id"] == "flow-1"
        assert result[1]["flow_id"] == "flow-2"


class TestEnhancedFlowStateManager:
    """Test Enhanced Flow State Manager functionality"""
    
    @pytest.fixture
    def serialization_config(self):
        """Test serialization configuration"""
        return SerializationConfig(
            format="json",
            compress=True,
            encrypt_sensitive=True,
            max_size_mb=10
        )
    
    @pytest.fixture
    def encryption_config(self):
        """Test encryption configuration"""
        return EncryptionConfig(
            enabled=True,
            sensitive_fields=["api_keys", "passwords", "tokens"]
        )
    
    @pytest.fixture
    def state_serializer(self, serialization_config):
        """Create state serializer for testing"""
        return StateSerializer(serialization_config)
    
    def test_serialization_json_format(self, state_serializer):
        """Test JSON serialization"""
        test_state = {
            "flow_id": "test-123",
            "status": "running",
            "data": {"key": "value"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Serialize
        serialized = state_serializer.serialize_state(test_state)
        assert isinstance(serialized, bytes)
        
        # Deserialize
        deserialized = state_serializer.deserialize_state(serialized)
        assert deserialized["flow_id"] == "test-123"
        assert deserialized["status"] == "running"
    
    @patch.dict(os.environ, {'FLOW_STATE_PASSWORD': 'test-password-123'})
    def test_encryption_sensitive_data(self, encryption_config):
        """Test sensitive data encryption"""
        encryption = StateEncryption(encryption_config)
        
        test_data = {
            "flow_id": "test-123",
            "api_keys": {"service": "secret-key-123"},
            "passwords": {"admin": "admin-pass"},
            "public_data": "not-sensitive"
        }
        
        # Encrypt
        encrypted_data = encryption.encrypt_sensitive_data(test_data)
        
        # Check that sensitive fields are encrypted
        assert encrypted_data["api_keys"]["__encrypted__"] is True
        assert encrypted_data["passwords"]["__encrypted__"] is True
        assert encrypted_data["public_data"] == "not-sensitive"  # Not encrypted
        
        # Decrypt
        decrypted_data = encryption.decrypt_sensitive_data(encrypted_data)
        assert decrypted_data["api_keys"] == {"service": "secret-key-123"}
        assert decrypted_data["passwords"] == {"admin": "admin-pass"}
    
    def test_serialization_size_limit(self, state_serializer):
        """Test serialization size limit enforcement"""
        # Create large state that exceeds limit
        large_data = "x" * (15 * 1024 * 1024)  # 15MB
        large_state = {"flow_id": "test", "large_data": large_data}
        
        with pytest.raises(StateSerializationError, match="too large"):
            state_serializer.serialize_state(large_state)
    
    def test_serialization_metadata_handling(self, state_serializer):
        """Test serialization metadata handling"""
        test_state = {"flow_id": "test-123", "data": "test"}
        
        # Serialize (adds metadata)
        serialized = state_serializer.serialize_state(test_state)
        
        # Deserialize (removes metadata)
        deserialized = state_serializer.deserialize_state(serialized)
        
        # Metadata should be removed in final result
        assert "__serialization__" not in deserialized
        assert deserialized["flow_id"] == "test-123"


class TestMultiTenantFlowManager:
    """Test Multi-Tenant Flow Manager functionality"""
    
    @pytest.fixture
    async def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def tenant_context(self):
        """Test tenant context"""
        return RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id="tenant-user"
        )
    
    @pytest.fixture
    def admin_context(self):
        """Test admin context"""
        return RequestContext(
            client_account_id=999,  # Admin account
            engagement_id=999,
            user_id="admin-user"
        )
    
    @pytest.fixture
    async def tenant_manager(self, mock_db):
        """Create tenant manager for testing"""
        manager = MultiTenantFlowManager(mock_db, TenantIsolationLevel.STRICT)
        
        # Mock database queries
        mock_db.execute = AsyncMock()
        
        return manager
    
    @pytest.mark.asyncio
    async def test_tenant_access_validation(self, tenant_manager, tenant_context):
        """Test tenant access validation"""
        # Mock active tenant check
        tenant_manager._is_tenant_active = AsyncMock(return_value=True)
        
        # Should not raise exception for valid context
        await tenant_manager._validate_tenant_access(tenant_context)
        
        # Test invalid context
        invalid_context = RequestContext(client_account_id=None, engagement_id=1, user_id="user")
        
        with pytest.raises(TenantIsolationError, match="Missing client_account_id"):
            await tenant_manager._validate_tenant_access(invalid_context)
    
    @pytest.mark.asyncio
    async def test_flow_ownership_validation(self, tenant_manager, tenant_context):
        """Test flow ownership validation"""
        flow_id = "test-flow-123"
        
        # Mock database response for owned flow
        mock_result = Mock()
        mock_row = Mock()
        mock_row.client_account_id = tenant_context.client_account_id
        mock_result.fetchone.return_value = mock_row
        tenant_manager.db.execute = AsyncMock(return_value=mock_result)
        
        # Should return True for owned flow
        result = await tenant_manager._validate_flow_ownership(
            tenant_context.client_account_id, flow_id
        )
        assert result is True
        
        # Mock database response for unowned flow
        mock_row.client_account_id = 999  # Different tenant
        
        result = await tenant_manager._validate_flow_ownership(
            tenant_context.client_account_id, flow_id
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_tenant_quota_checking(self, tenant_manager, tenant_context):
        """Test tenant quota enforcement"""
        # Set restrictive quota
        quota = TenantQuota(
            max_concurrent_flows=1,
            max_total_flows_per_day=2,
            max_storage_mb=100
        )
        tenant_manager._tenant_quotas[tenant_context.client_account_id] = quota
        
        # Mock metrics that exceed quota
        metrics = TenantMetrics(
            client_account_id=tenant_context.client_account_id,
            current_flows=2,  # Exceeds max_concurrent_flows
            total_flows_today=1,
            storage_used_mb=50.0
        )
        tenant_manager._tenant_metrics[tenant_context.client_account_id] = metrics
        
        # Should raise quota exceeded error
        with pytest.raises(TenantQuotaExceededError, match="Concurrent flows quota exceeded"):
            await tenant_manager._check_tenant_quotas(tenant_context, "create_flow")
    
    @pytest.mark.asyncio
    async def test_tenant_metrics_tracking(self, tenant_manager, tenant_context):
        """Test tenant metrics tracking"""
        flow_id = "test-flow-123"
        client_account_id = tenant_context.client_account_id
        
        # Track flow creation
        await tenant_manager._track_tenant_flow(client_account_id, flow_id, "created")
        
        # Check metrics updated
        assert flow_id in tenant_manager._flow_tenant_mapping
        assert tenant_manager._flow_tenant_mapping[flow_id] == client_account_id
        
        metrics = tenant_manager._tenant_metrics[client_account_id]
        assert metrics.current_flows == 1
        assert metrics.total_flows_today == 1
        assert metrics.last_activity is not None
        
        # Track flow deletion
        await tenant_manager._track_tenant_flow(client_account_id, flow_id, "deleted")
        
        # Check metrics updated
        assert metrics.current_flows == 0
    
    @pytest.mark.asyncio
    async def test_admin_operations(self, tenant_manager, admin_context):
        """Test admin operations"""
        target_tenant_id = 1
        
        # Mock admin check
        tenant_manager._is_platform_admin = AsyncMock(return_value=True)
        
        # Test setting tenant quota
        new_quota = TenantQuota(max_concurrent_flows=20, max_total_flows_per_day=200)
        
        result = await tenant_manager.set_tenant_quota(admin_context, target_tenant_id, new_quota)
        
        assert result["target_client_account_id"] == target_tenant_id
        assert result["quota_set"] is True
        assert tenant_manager._tenant_quotas[target_tenant_id] == new_quota


class TestFlowTypeRegistry:
    """Test Flow Type Registry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create registry for testing"""
        return FlowTypeRegistry()
    
    def test_flow_type_registration(self, registry):
        """Test flow type registration"""
        # Create test flow config
        phases = [
            PhaseConfig(name="phase1", order=1, required=True),
            PhaseConfig(name="phase2", order=2, required=False)
        ]
        
        config = FlowTypeConfig(
            name="test_flow",
            display_name="Test Flow",
            description="Test flow type",
            phases=phases
        )
        
        # Register flow type
        registry.register_flow_type(config)
        
        # Test registration
        assert registry.is_registered("test_flow") is True
        assert registry.is_registered("nonexistent") is False
        
        # Test retrieval
        retrieved_config = registry.get_flow_config("test_flow")
        assert retrieved_config.name == "test_flow"
        assert len(retrieved_config.phases) == 2
    
    def test_duplicate_registration(self, registry):
        """Test duplicate flow type registration"""
        config = FlowTypeConfig(name="duplicate_test", display_name="Duplicate")
        
        # First registration should succeed
        registry.register_flow_type(config)
        
        # Duplicate registration should raise error
        with pytest.raises(ValueError, match="already registered"):
            registry.register_flow_type(config)
    
    def test_get_all_flow_types(self, registry):
        """Test getting all registered flow types"""
        # Register multiple flow types
        for i in range(3):
            config = FlowTypeConfig(
                name=f"flow_{i}",
                display_name=f"Flow {i}"
            )
            registry.register_flow_type(config)
        
        all_types = registry.get_all_flow_types()
        assert len(all_types) >= 3  # At least our test types


class TestValidatorRegistry:
    """Test Validator Registry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create validator registry for testing"""
        return ValidatorRegistry()
    
    @pytest.mark.asyncio
    async def test_validator_registration_and_execution(self, registry):
        """Test validator registration and execution"""
        # Define test validator
        async def test_validator(phase_input, flow_state, overrides=None):
            if phase_input.get("invalid"):
                return {"valid": False, "errors": ["Test validation failed"]}
            return {"valid": True, "errors": []}
        
        # Register validator
        registry.register_validator("test_validator", test_validator)
        
        # Test validator exists
        assert registry.has_validator("test_validator") is True
        assert registry.has_validator("nonexistent") is False
        
        # Test validator execution - valid case
        validator = registry.get_validator("test_validator")
        result = await validator({"valid": True}, {})
        assert result["valid"] is True
        
        # Test validator execution - invalid case
        result = await validator({"invalid": True}, {})
        assert result["valid"] is False
        assert "Test validation failed" in result["errors"]
    
    def test_built_in_validators(self, registry):
        """Test built-in validators are available"""
        # Built-in validators should be registered automatically
        built_in_validators = [
            "required_fields",
            "data_format",
            "phase_transition",
            "resource_limits"
        ]
        
        for validator_name in built_in_validators:
            assert registry.has_validator(validator_name) is True


class TestHandlerRegistry:
    """Test Handler Registry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create handler registry for testing"""
        return HandlerRegistry()
    
    @pytest.mark.asyncio
    async def test_handler_registration_and_execution(self, registry):
        """Test handler registration and execution"""
        # Define test handler
        async def test_handler(flow_id, flow_type, **kwargs):
            return {
                "handled": True,
                "flow_id": flow_id,
                "flow_type": flow_type,
                "kwargs": kwargs
            }
        
        # Register handler
        registry.register_handler("test_handler", test_handler)
        
        # Test handler exists
        assert registry.has_handler("test_handler") is True
        
        # Test handler execution
        handler = registry.get_handler("test_handler")
        result = await handler(
            flow_id="test-123",
            flow_type="discovery",
            test_param="test_value"
        )
        
        assert result["handled"] is True
        assert result["flow_id"] == "test-123"
        assert result["flow_type"] == "discovery"
        assert result["kwargs"]["test_param"] == "test_value"
    
    def test_common_handlers(self, registry):
        """Test common handlers are available"""
        common_handlers = [
            "asset_creation",
            "data_validation",
            "notification",
            "audit_logging"
        ]
        
        for handler_name in common_handlers:
            assert registry.has_handler(handler_name) is True


class TestFlowErrorHandler:
    """Test Flow Error Handler functionality"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler for testing"""
        return FlowErrorHandler()
    
    @pytest.mark.asyncio
    async def test_error_handling_with_retry(self, error_handler):
        """Test error handling with retry logic"""
        test_error = Exception("Test error")
        context = {
            "operation": "test_operation",
            "flow_id": "test-123"
        }
        retry_config = {
            "max_retries": 3,
            "backoff_multiplier": 2
        }
        
        result = await error_handler.handle_error(test_error, context, retry_config)
        
        assert "should_retry" in result
        assert "retry_delay" in result
        assert "error_type" in result
        assert result["error_message"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_error_strategy_selection(self, error_handler):
        """Test error strategy selection based on error type"""
        # Test different error types
        connection_error = ConnectionError("Database connection failed")
        validation_error = ValidationError("Invalid input")
        runtime_error = RuntimeError("Runtime error")
        
        # Test connection error strategy
        result = await error_handler.handle_error(connection_error, {})
        assert result["strategy"] == ErrorStrategy.RETRY_WITH_BACKOFF.value
        
        # Test validation error strategy
        result = await error_handler.handle_error(validation_error, {})
        assert result["strategy"] == ErrorStrategy.FAIL_FAST.value
        
        # Test runtime error strategy
        result = await error_handler.handle_error(runtime_error, {})
        assert result["strategy"] == ErrorStrategy.RETRY_WITH_CIRCUIT_BREAKER.value


class TestPerformanceTracker:
    """Test Performance Tracker functionality"""
    
    @pytest.fixture
    def tracker(self):
        """Create performance tracker for testing"""
        return PerformanceTracker()
    
    def test_operation_tracking(self, tracker):
        """Test operation performance tracking"""
        # Start operation
        operation_id = tracker.start_operation(
            operation_type="test_operation",
            metadata={"test": "data"}
        )
        
        assert operation_id is not None
        assert operation_id in tracker._active_operations
        
        # End operation
        tracker.end_operation(
            operation_id,
            success=True,
            result_metadata={"result": "success"}
        )
        
        assert operation_id not in tracker._active_operations
        
        # Check metrics recorded
        metrics = tracker.get_operation_metrics("test_operation")
        assert metrics["total_operations"] >= 1
        assert metrics["successful_operations"] >= 1
    
    def test_metrics_collection(self, tracker):
        """Test metrics collection and aggregation"""
        # Simulate multiple operations
        for i in range(5):
            op_id = tracker.start_operation("bulk_test")
            tracker.end_operation(op_id, success=i % 2 == 0)  # 60% success rate
        
        metrics = tracker.get_operation_metrics("bulk_test")
        assert metrics["total_operations"] == 5
        assert metrics["successful_operations"] == 3
        assert metrics["failed_operations"] == 2
        assert abs(metrics["success_rate"] - 0.6) < 0.01
    
    def test_performance_summary(self, tracker):
        """Test performance summary generation"""
        # Add some operations
        for operation_type in ["create", "execute", "delete"]:
            for _ in range(3):
                op_id = tracker.start_operation(operation_type)
                tracker.end_operation(op_id, success=True)
        
        summary = tracker.get_performance_summary()
        
        assert "total_operations" in summary
        assert "operation_types" in summary
        assert summary["total_operations"] >= 9
        assert len(summary["operation_types"]) >= 3
    
    def test_audit_event_recording(self, tracker):
        """Test audit event recording"""
        audit_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "test_audit",
            "user_id": "test-user",
            "details": {"test": "audit"}
        }
        
        tracker.record_audit_event(audit_event)
        
        # Verify event was recorded
        events = tracker.get_audit_events()
        assert len(events) >= 1
        assert any(event["operation"] == "test_audit" for event in events)


# Integration tests
class TestMasterFlowOrchestratorIntegration:
    """Integration tests for Master Flow Orchestrator components"""
    
    @pytest.mark.asyncio
    async def test_full_flow_lifecycle(self):
        """Test complete flow lifecycle integration"""
        # This would be a more complex integration test
        # Testing the interaction between all components
        pass
    
    @pytest.mark.asyncio
    async def test_multi_tenant_flow_isolation(self):
        """Test multi-tenant flow isolation"""
        # Test that tenant A cannot access tenant B's flows
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test error recovery across components"""
        # Test error handling and recovery mechanisms
        pass


# Performance and load tests
class TestPerformanceAndLoad:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_flow_creation(self):
        """Test concurrent flow creation performance"""
        # Test creating multiple flows concurrently
        pass
    
    @pytest.mark.asyncio
    async def test_large_state_serialization(self):
        """Test serialization performance with large states"""
        # Test serialization/deserialization performance
        pass
    
    @pytest.mark.asyncio
    async def test_tenant_quota_enforcement_performance(self):
        """Test tenant quota enforcement performance"""
        # Test quota checking performance
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=app.services", "--cov-report=term-missing"])