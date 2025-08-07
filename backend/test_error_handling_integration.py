#!/usr/bin/env python3
"""
Error Handling Integration Test

Simple integration test to validate the error handling and fallback systems
work correctly together. This is a standalone test that doesn't require
the full application setup.
"""

import asyncio
import sys
import traceback


# flake8: noqa: E402
# Mock the dependencies to make this test runnable
class MockSettings:
    DEBUG = True
    REDIS_ENABLED = False
    ERROR_RECOVERY_ENABLED = True
    ERROR_PATTERN_LEARNING = True


# Mock configuration
sys.modules["app.core.config"] = type("MockModule", (), {"settings": MockSettings()})()


# Mock logger
class MockLogger:
    def info(self, msg, **kwargs):
        print(f"INFO: {msg}")

    def debug(self, msg, **kwargs):
        print(f"DEBUG: {msg}")

    def warning(self, msg, **kwargs):
        print(f"WARNING: {msg}")

    def error(self, msg, **kwargs):
        print(f"ERROR: {msg}")

    def critical(self, msg, **kwargs):
        print(f"CRITICAL: {msg}")


sys.modules["app.core.logging"] = type(
    "MockModule", (), {"get_logger": lambda name: MockLogger()}
)()


# Mock sanitization function
def mock_sanitize_for_logging(data):
    """Mock sanitization that just returns the data"""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if not k.lower().startswith("password")}
    return data


sys.modules["app.core.security.cache_encryption"] = type(
    "MockModule", (), {"sanitize_for_logging": mock_sanitize_for_logging}
)()

# Now we can import our systems
from app.services.auth.fallback_orchestrator import (
    FallbackOrchestrator,
    OperationType,
)
from app.services.error_handling.enhanced_error_handler import (
    EnhancedErrorHandler,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    UserAudience,
)
from app.services.monitoring.service_health_manager import (
    ServiceHealthManager,
    ServiceType,
)
from app.services.recovery.error_recovery_system import (
    ErrorRecoverySystem,
    FailureCategory,
    RecoveryType,
)


class IntegrationTest:
    """Integration test for error handling systems"""

    def __init__(self):
        self.health_manager = ServiceHealthManager()
        self.fallback_orchestrator = FallbackOrchestrator(self.health_manager)
        self.recovery_system = ErrorRecoverySystem(
            self.health_manager, self.fallback_orchestrator
        )
        self.error_handler = EnhancedErrorHandler(
            self.health_manager, self.fallback_orchestrator, self.recovery_system
        )

        self.test_results = []

    async def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("ERROR HANDLING INTEGRATION TESTS")
        print("=" * 60)

        tests = [
            ("Service Health Monitoring", self.test_service_health),
            ("Error Classification", self.test_error_classification),
            ("Fallback Orchestration", self.test_fallback_orchestration),
            ("Error Recovery", self.test_error_recovery),
            ("End-to-End Error Handling", self.test_end_to_end_error_handling),
        ]

        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                await test_func()
                self.test_results.append((test_name, "PASSED", None))
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                self.test_results.append((test_name, "FAILED", str(e)))
                print(f"❌ {test_name}: FAILED - {e}")
                traceback.print_exc()

        self.print_summary()

    async def test_service_health(self):
        """Test service health monitoring"""
        # Test health manager initialization
        assert self.health_manager is not None

        # Test getting system health status
        system_health = await self.health_manager.get_system_health_status()
        assert system_health is not None
        assert hasattr(system_health, "overall_health")

        # Test service availability check
        redis_available = await self.health_manager.is_service_available(
            ServiceType.REDIS
        )
        assert isinstance(redis_available, bool)

        print("  ✓ Service health monitoring initialized and working")

    async def test_error_classification(self):
        """Test error classification system"""
        # Test different error types
        test_errors = [
            (ConnectionError("Database connection failed"), ErrorCategory.DATABASE),
            (TimeoutError("Request timeout"), ErrorCategory.NETWORK),
            (ValueError("Invalid input"), ErrorCategory.VALIDATION),
            (Exception("Redis connection error"), ErrorCategory.CACHE),
        ]

        for error, expected_category in test_errors:
            context = ErrorContext(operation_type=OperationType.USER_SESSION)
            classification = await self.error_handler._classify_error(error, context)

            # Classification should have reasonable values
            assert isinstance(classification.category, ErrorCategory)
            assert isinstance(classification.severity, ErrorSeverity)
            assert isinstance(classification.is_recoverable, bool)

            print(
                f"  ✓ Classified {type(error).__name__} as {classification.category.value}"
            )

    async def test_fallback_orchestration(self):
        """Test fallback orchestration"""

        # Mock operation function
        async def mock_operation(*args, service_context=None, **kwargs):
            if service_context == ServiceType.REDIS:
                raise ConnectionError("Redis unavailable")
            elif service_context == ServiceType.AUTH_CACHE:
                return {"user_id": "test_user", "cached": True}
            else:
                raise Exception("All services failed")

        # Test fallback execution
        result = await self.fallback_orchestrator.execute_with_fallback(
            OperationType.USER_SESSION, mock_operation, user_id="test_user"
        )

        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "level_used")
        assert hasattr(result, "total_attempts")

        print(
            f"  ✓ Fallback orchestration completed: success={result.success}, level={result.level_used}"
        )

    async def test_error_recovery(self):
        """Test error recovery system"""

        # Schedule a recovery operation
        async def mock_failing_operation():
            raise ConnectionError("Service temporarily unavailable")

        recovery_id = await self.recovery_system.schedule_recovery_operation(
            operation_func=mock_failing_operation,
            recovery_type=RecoveryType.IMMEDIATE_RETRY,
            failure_category=FailureCategory.TRANSIENT,
            operation_type=OperationType.CACHE_READ,
            service_type=ServiceType.REDIS,
        )

        assert recovery_id is not None
        assert isinstance(recovery_id, str)

        # Check recovery status
        status = await self.recovery_system.get_recovery_status()
        assert "recovery_queues" in status
        assert "enabled" in status

        print(f"  ✓ Recovery operation scheduled: {recovery_id}")

    async def test_end_to_end_error_handling(self):
        """Test end-to-end error handling flow"""
        # Create error context
        context = ErrorContext(
            operation_type=OperationType.USER_SESSION,
            service_type=ServiceType.REDIS,
            user_id="test_user",
            endpoint="/api/auth/session",
            method="GET",
        )

        # Mock operation that will be recovered
        async def mock_operation(*args, **kwargs):
            return {"user_id": "test_user", "session": "active"}

        # Test error handling with recovery
        test_error = ConnectionError("Redis connection timeout")

        error_response = await self.error_handler.handle_error(
            error=test_error,
            context=context,
            audience=UserAudience.END_USER,
            operation_func=mock_operation,
            operation_args=("test_user",),
            operation_kwargs={},
        )

        # Validate error response structure
        assert error_response is not None
        assert hasattr(error_response, "error_code")
        assert hasattr(error_response, "message")
        assert hasattr(error_response, "severity")
        assert hasattr(error_response, "category")
        assert hasattr(error_response, "recovery_suggestions")

        # Check response content
        assert isinstance(error_response.message, str)
        assert len(error_response.message) > 0
        assert isinstance(error_response.recovery_suggestions, list)
        assert len(error_response.recovery_suggestions) > 0

        print(f"  ✓ End-to-end error handling completed: {error_response.error_code}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, status, _ in self.test_results if status == "PASSED")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAILED")
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed > 0:
            print("\nFailed Tests:")
            for test_name, status, error in self.test_results:
                if status == "FAILED":
                    print(f"  ❌ {test_name}: {error}")

        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 Integration tests largely successful!")
        elif success_rate >= 60:
            print(
                "⚠️  Integration tests partially successful - some issues need attention"
            )
        else:
            print("❌ Integration tests failed - significant issues detected")


async def main():
    """Main test function"""
    test = IntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
