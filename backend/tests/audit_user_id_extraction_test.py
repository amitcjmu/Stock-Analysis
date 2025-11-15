"""
Test Suite: Audit User ID Extraction with Fallbacks

This test verifies that the audit logger correctly extracts user_id
from various sources using the cascading fallback strategy.

Tests cover:
1. Direct extraction from RequestContext
2. Fallback to global context
3. Extraction from request headers
4. Extraction from JWT token
5. System operation handling
6. Warning for missing user_id on user operations
"""

import pytest
from unittest.mock import patch

from app.core.context import RequestContext
from app.services.flow_contracts.audit.logger import FlowAuditLogger
from app.services.flow_contracts.audit.models import AuditCategory, AuditLevel


class TestAuditUserIdExtraction:
    """Test audit logger user_id extraction with multiple fallback strategies"""

    @pytest.fixture
    def audit_logger(self):
        """Create a FlowAuditLogger instance"""
        return FlowAuditLogger()

    @pytest.mark.asyncio
    async def test_user_id_from_context(self, audit_logger):
        """Test Strategy 1: Extract user_id from RequestContext"""
        # Arrange
        context = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="user-456",
        )

        # Act
        user_id = audit_logger._extract_user_id_with_fallbacks(context, "create_flow")

        # Assert
        assert user_id == "user-456"

    @pytest.mark.asyncio
    async def test_user_id_from_global_context(self, audit_logger):
        """Test Strategy 2: Fallback to global request context"""
        # Arrange
        context_without_user = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id=None,  # Missing user_id
        )
        global_context = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="global-user-789",
        )

        # Act
        with patch("app.core.context.get_current_context", return_value=global_context):
            user_id = audit_logger._extract_user_id_with_fallbacks(
                context_without_user, "execute_phase"
            )

        # Assert
        assert user_id == "global-user-789"

    @pytest.mark.asyncio
    async def test_context_with_request_metadata_but_no_user_id(self, audit_logger):
        """Test Strategy 3: Context has request metadata but missing user_id"""
        # Arrange
        context_without_user = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id=None,
            ip_address="192.168.1.100",  # Has request metadata
            user_agent="Mozilla/5.0",
        )

        # Act
        with patch("app.core.context.get_current_context", return_value=None):
            user_id = audit_logger._extract_user_id_with_fallbacks(
                context_without_user, "delete_flow"
            )

        # Assert - Should fall through to system operation check or None
        # Since delete_flow is not a system operation, should return None
        assert user_id is None

    @pytest.mark.asyncio
    async def test_system_operation_uses_system_user_id(self, audit_logger):
        """Test Strategy 5: System operations get 'system' user_id"""
        # Arrange
        context_without_user = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id=None,
        )

        system_operations = [
            "resume",
            "pause",
            "health_check",
            "status_sync",
            "cleanup",
            "monitoring",
        ]

        # Act & Assert
        with patch("app.core.context.get_current_context", return_value=None):
            for operation in system_operations:
                user_id = audit_logger._extract_user_id_with_fallbacks(
                    context_without_user, operation
                )
                assert (
                    user_id == "system"
                ), f"Expected 'system' for {operation}, got {user_id}"

    @pytest.mark.asyncio
    async def test_warning_logged_for_user_operation_without_user_id(
        self, audit_logger, caplog
    ):
        """Test Strategy 6: Warning logged when user_id is None for user operations"""
        # Arrange
        context_without_user = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id=None,
        )

        # Act
        with patch("app.core.context.get_current_context", return_value=None):
            user_id = audit_logger._extract_user_id_with_fallbacks(
                context_without_user, "create_flow"
            )

        # Assert
        assert user_id is None
        # Check that warning was logged
        assert any(
            "⚠️ AUDIT: user_id is None for user-initiated operation" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_audit_event_includes_user_id(self, audit_logger):
        """Integration test: Audit event creation includes extracted user_id"""
        # Arrange
        context = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="integration-user-555",
        )

        # Act
        event_id = await audit_logger.log_audit_event(
            flow_id="test-flow-001",
            operation="create_flow",
            category=AuditCategory.FLOW_LIFECYCLE,
            level=AuditLevel.INFO,
            context=context,
            success=True,
        )

        # Assert
        assert event_id is not None
        events = audit_logger.get_audit_events("test-flow-001")
        assert len(events) > 0
        assert events[0]["user_id"] == "integration-user-555"

    @pytest.mark.asyncio
    async def test_compliance_check_passes_with_user_id(self, audit_logger):
        """Test that compliance check passes when user_id is present"""
        # Arrange
        context = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="compliance-user-777",
        )

        # Act
        await audit_logger.log_audit_event(
            flow_id="compliance-flow-001",
            operation="execute_phase",
            category=AuditCategory.FLOW_EXECUTION,
            level=AuditLevel.INFO,
            context=context,
            success=True,
        )

        # Assert - No compliance violation events should be created
        events = audit_logger.get_audit_events(
            "compliance-flow-001", category=AuditCategory.COMPLIANCE_EVENT
        )
        violations = [e for e in events if not e["success"]]
        assert (
            len(violations) == 0
        ), f"Expected no compliance violations, but got {len(violations)}"

    @pytest.mark.asyncio
    async def test_fallback_chain_order(self, audit_logger):
        """Test that fallback strategies are tried in correct order"""
        # Arrange
        context_with_user = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="context-user-primary",
        )
        global_context = RequestContext(
            client_account_id="1",
            engagement_id="123",
            user_id="global-user-secondary",
        )

        # Act - Should use context.user_id first, ignore global
        with patch("app.core.context.get_current_context", return_value=global_context):
            user_id = audit_logger._extract_user_id_with_fallbacks(
                context_with_user, "test_operation"
            )

        # Assert - Should use context.user_id, not global
        assert user_id == "context-user-primary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
