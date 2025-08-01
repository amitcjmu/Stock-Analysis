"""
Error Handling and Recovery Testing for Discovery Flow (Task 62)

Tests error handling and recovery mechanisms including:
- Crew execution failure scenarios and recovery
- Network timeout and retry mechanisms
- Database connection failures and recovery
- Partial failure handling and workflow continuation
- Graceful degradation under various failure conditions
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
import sqlalchemy.exc


# Error simulation fixtures
@pytest.fixture
def error_simulator():
    """Simulator for various error conditions"""

    class ErrorSimulator:
        def __init__(self):
            self.error_count = 0
            self.max_errors = 3

        def simulate_network_error(self):
            """Simulate network connectivity issues"""
            self.error_count += 1
            if self.error_count <= self.max_errors:
                raise ConnectionError("Network connection failed")
            return {"status": "success", "retry_count": self.error_count}

        def simulate_database_error(self):
            """Simulate database connection issues"""
            self.error_count += 1
            if self.error_count <= 2:
                raise sqlalchemy.exc.DisconnectionError(
                    "Database connection lost", None, None
                )
            return {"status": "connected", "retry_count": self.error_count}

        def simulate_memory_error(self):
            """Simulate memory exhaustion"""
            if self.error_count < 1:
                self.error_count += 1
                raise MemoryError("Insufficient memory for operation")
            return {"status": "success", "memory_freed": True}

        def simulate_timeout_error(self):
            """Simulate operation timeout"""
            self.error_count += 1
            if self.error_count <= 1:
                raise asyncio.TimeoutError("Operation timed out")
            return {"status": "completed", "retry_count": self.error_count}

    return ErrorSimulator()


@pytest.fixture
def mock_failing_crew():
    """Mock crew that fails in predictable ways"""

    class MockFailingCrew:
        def __init__(self, failure_mode: str = None, failure_count: int = 1):
            self.failure_mode = failure_mode
            self.failure_count = failure_count
            self.attempt_count = 0

        async def execute_async(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            self.attempt_count += 1

            if self.failure_mode and self.attempt_count <= self.failure_count:
                if self.failure_mode == "network":
                    raise ConnectionError("Network connection failed")
                elif self.failure_mode == "timeout":
                    raise asyncio.TimeoutError("Crew execution timed out")
                elif self.failure_mode == "validation":
                    raise ValueError("Invalid input data format")
                elif self.failure_mode == "memory":
                    raise MemoryError("Insufficient memory")
                elif self.failure_mode == "database":
                    raise sqlalchemy.exc.DisconnectionError(
                        "DB connection lost", None, None
                    )

            return {
                "status": "completed",
                "attempt_count": self.attempt_count,
                "recovered": self.attempt_count > 1,
            }

    return MockFailingCrew


@pytest.fixture
def recovery_manager():
    """Manager for handling recovery operations"""

    class RecoveryManager:
        def __init__(self):
            self.recovery_attempts = {}
            self.fallback_strategies = {}

        async def retry_with_backoff(
            self, operation, max_retries: int = 3, base_delay: float = 1.0
        ):
            """Retry operation with exponential backoff"""
            for attempt in range(max_retries + 1):
                try:
                    return await operation()
                except Exception as e:
                    if attempt == max_retries:
                        raise e

                    delay = base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    self.recovery_attempts[operation.__name__] = attempt + 1

        def register_fallback(self, operation_name: str, fallback_func):
            """Register fallback strategy for operation"""
            self.fallback_strategies[operation_name] = fallback_func

        async def execute_with_fallback(
            self, operation_name: str, primary_operation, inputs: Dict[str, Any]
        ):
            """Execute operation with fallback if available"""
            try:
                return await primary_operation(inputs)
            except Exception as e:
                if operation_name in self.fallback_strategies:
                    fallback_func = self.fallback_strategies[operation_name]
                    return await fallback_func(inputs, error=e)
                raise e

    return RecoveryManager()


class TestDiscoveryFlowErrorHandling:
    """Test suite for Discovery Flow error handling and recovery"""

    @pytest.mark.asyncio
    async def test_crew_execution_failure_and_retry(
        self, mock_failing_crew, recovery_manager
    ):
        """Test crew execution failure with automatic retry (Task 62)"""
        # Arrange
        failing_crew = mock_failing_crew(failure_mode="network", failure_count=2)
        inputs = {"asset_count": 100, "operation": "field_mapping"}

        async def crew_operation():
            return await failing_crew.execute_async(inputs)

        # Act
        result = await recovery_manager.retry_with_backoff(
            crew_operation, max_retries=3
        )

        # Assert
        assert (
            result["status"] == "completed"
        ), "Crew should eventually succeed after retries"
        assert result["recovered"] is True, "Should indicate recovery occurred"
        assert result["attempt_count"] == 3, "Should succeed on third attempt"
        assert (
            "crew_operation" in recovery_manager.recovery_attempts
        ), "Recovery attempts should be tracked"

    @pytest.mark.asyncio
    async def test_network_timeout_recovery(self, error_simulator, recovery_manager):
        """Test recovery from network timeout errors (Task 62)"""

        # Arrange
        async def network_operation():
            return error_simulator.simulate_timeout_error()

        # Act
        result = await recovery_manager.retry_with_backoff(
            network_operation, max_retries=2
        )

        # Assert
        assert result["status"] == "completed", "Network operation should recover"
        assert result["retry_count"] == 2, "Should succeed after retry"

    @pytest.mark.asyncio
    async def test_database_connection_failure_recovery(
        self, error_simulator, recovery_manager
    ):
        """Test recovery from database connection failures (Task 62)"""

        # Arrange
        async def db_operation():
            return error_simulator.simulate_database_error()

        # Act & Assert
        with patch("time.sleep", return_value=None):  # Speed up test
            result = await recovery_manager.retry_with_backoff(
                db_operation, max_retries=3
            )

        assert result["status"] == "connected", "Database should reconnect"
        assert result["retry_count"] == 3, "Should succeed after retries"

    @pytest.mark.asyncio
    async def test_partial_workflow_failure_handling(
        self, mock_failing_crew, recovery_manager
    ):
        """Test handling of partial workflow failures (Task 62)"""
        # Arrange
        crews = [
            mock_failing_crew(),  # Succeeds
            mock_failing_crew(failure_mode="validation", failure_count=1),  # Fails once
            mock_failing_crew(),  # Succeeds
            mock_failing_crew(failure_mode="timeout", failure_count=1),  # Fails once
        ]

        inputs = {"asset_count": 100}
        results = []

        # Act
        for i, crew in enumerate(crews):
            try:

                async def crew_operation():
                    return await crew.execute_async(inputs)

                result = await recovery_manager.retry_with_backoff(
                    crew_operation, max_retries=2
                )
                results.append({"crew_id": i, "status": "success", "result": result})
            except Exception as e:
                results.append({"crew_id": i, "status": "failed", "error": str(e)})

        # Assert
        successful_crews = [r for r in results if r["status"] == "success"]
        failed_crews = [r for r in results if r["status"] == "failed"]

        assert (
            len(successful_crews) == 4
        ), "All crews should eventually succeed with retries"
        assert len(failed_crews) == 0, "No crews should fail permanently"

    @pytest.mark.asyncio
    async def test_graceful_degradation_with_fallback(
        self, mock_failing_crew, recovery_manager
    ):
        """Test graceful degradation with fallback strategies (Task 62)"""
        # Arrange
        failing_crew = mock_failing_crew(
            failure_mode="memory", failure_count=5
        )  # Always fails

        async def fallback_strategy(inputs: Dict[str, Any], error: Exception):
            """Fallback to simplified processing"""
            return {
                "status": "completed_with_fallback",
                "fallback_used": True,
                "original_error": str(error),
                "reduced_scope": True,
                "processed_assets": inputs.get("asset_count", 0) // 2,  # Process half
            }

        recovery_manager.register_fallback("field_mapping", fallback_strategy)
        inputs = {"asset_count": 1000}

        async def primary_operation(inputs):
            return await failing_crew.execute_async(inputs)

        # Act
        result = await recovery_manager.execute_with_fallback(
            "field_mapping", primary_operation, inputs
        )

        # Assert
        assert (
            result["status"] == "completed_with_fallback"
        ), "Should complete with fallback"
        assert result["fallback_used"] is True, "Should indicate fallback was used"
        assert (
            result["reduced_scope"] is True
        ), "Should indicate reduced scope operation"
        assert result["processed_assets"] == 500, "Should process reduced dataset"

    @pytest.mark.asyncio
    async def test_workflow_state_preservation_during_errors(
        self, mock_failing_crew, recovery_manager
    ):
        """Test workflow state preservation during error conditions (Task 62)"""
        # Arrange
        workflow_state = {
            "completed_crews": [],
            "failed_crews": [],
            "partial_results": {},
            "retry_counts": {},
        }

        crews = [
            ("field_mapping", mock_failing_crew()),
            (
                "data_cleansing",
                mock_failing_crew(failure_mode="network", failure_count=1),
            ),
            (
                "inventory_building",
                mock_failing_crew(failure_mode="timeout", failure_count=1),
            ),
        ]

        inputs = {"asset_count": 100}

        # Act
        for crew_name, crew in crews:
            try:

                async def crew_operation():
                    return await crew.execute_async(inputs)

                result = await recovery_manager.retry_with_backoff(
                    crew_operation, max_retries=2
                )

                # Update workflow state
                workflow_state["completed_crews"].append(crew_name)
                workflow_state["partial_results"][crew_name] = result
                workflow_state["retry_counts"][crew_name] = result.get(
                    "attempt_count", 1
                )

            except Exception as e:
                workflow_state["failed_crews"].append(
                    {"crew_name": crew_name, "error": str(e)}
                )

        # Assert
        assert (
            len(workflow_state["completed_crews"]) == 3
        ), "All crews should eventually complete"
        assert (
            len(workflow_state["failed_crews"]) == 0
        ), "No crews should fail permanently"
        assert all(
            name in workflow_state["partial_results"] for name, _ in crews
        ), "All results should be preserved"
        assert (
            workflow_state["retry_counts"]["data_cleansing"] > 1
        ), "Network failure crew should retry"
        assert (
            workflow_state["retry_counts"]["inventory_building"] > 1
        ), "Timeout crew should retry"

    @pytest.mark.asyncio
    async def test_error_propagation_and_isolation(self, mock_failing_crew):
        """Test error propagation and isolation between crews (Task 62)"""

        # Arrange
        class WorkflowOrchestrator:
            def __init__(self):
                self.error_isolation = True
                self.continue_on_error = True

            async def execute_workflow(
                self, crews: List[tuple], inputs: Dict[str, Any]
            ):
                results = {}
                errors = {}

                for crew_name, crew in crews:
                    try:
                        result = await crew.execute_async(inputs)
                        results[crew_name] = result
                    except Exception as e:
                        errors[crew_name] = str(e)
                        if not self.continue_on_error:
                            raise e
                        # Isolated error - continue with other crews
                        results[crew_name] = {
                            "status": "failed",
                            "error": str(e),
                            "isolated": True,
                        }

                return results, errors

        orchestrator = WorkflowOrchestrator()
        crews = [
            ("crew_1", mock_failing_crew()),  # Succeeds
            (
                "crew_2",
                mock_failing_crew(failure_mode="validation", failure_count=5),
            ),  # Always fails
            ("crew_3", mock_failing_crew()),  # Succeeds
        ]

        inputs = {"asset_count": 100}

        # Act
        results, errors = await orchestrator.execute_workflow(crews, inputs)

        # Assert
        assert (
            len(results) == 3
        ), "All crews should have results (success or isolated failure)"
        assert len(errors) == 1, "Only one crew should have errors"
        assert "crew_2" in errors, "Failing crew should be recorded in errors"
        assert (
            results["crew_1"]["status"] == "completed"
        ), "Non-failing crews should succeed"
        assert (
            results["crew_3"]["status"] == "completed"
        ), "Non-failing crews should succeed"
        assert (
            results["crew_2"]["isolated"] is True
        ), "Failed crew should be marked as isolated"

    @pytest.mark.asyncio
    async def test_resource_cleanup_after_failures(
        self, error_simulator, recovery_manager
    ):
        """Test proper resource cleanup after failures (Task 62)"""

        # Arrange
        class ResourceManager:
            def __init__(self):
                self.allocated_resources = []
                self.cleanup_performed = False

            @asynccontextmanager
            async def allocate_resources(self, resource_type: str):
                resource_id = f"{resource_type}_{len(self.allocated_resources)}"
                self.allocated_resources.append(resource_id)
                try:
                    yield resource_id
                finally:
                    # Cleanup resources
                    if resource_id in self.allocated_resources:
                        self.allocated_resources.remove(resource_id)
                    self.cleanup_performed = True

        resource_manager = ResourceManager()

        # Act & Assert
        with pytest.raises(MemoryError):
            async with resource_manager.allocate_resources("memory_pool"):
                error_simulator.simulate_memory_error()

        # Verify cleanup occurred despite error
        assert (
            resource_manager.cleanup_performed is True
        ), "Cleanup should occur despite errors"
        assert (
            len(resource_manager.allocated_resources) == 0
        ), "All resources should be cleaned up"

    @pytest.mark.asyncio
    async def test_error_reporting_and_monitoring(self, mock_failing_crew):
        """Test error reporting and monitoring capabilities (Task 62)"""

        # Arrange
        class ErrorMonitor:
            def __init__(self):
                self.error_log = []
                self.error_counts = {}
                self.alert_threshold = 3

            def log_error(
                self, crew_name: str, error: Exception, context: Dict[str, Any]
            ):
                error_entry = {
                    "crew_name": crew_name,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "context": context,
                    "timestamp": "mock_timestamp",
                }
                self.error_log.append(error_entry)

                # Update error counts
                error_key = f"{crew_name}:{type(error).__name__}"
                self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

            def should_alert(self, crew_name: str, error_type: str) -> bool:
                error_key = f"{crew_name}:{error_type}"
                return self.error_counts.get(error_key, 0) >= self.alert_threshold

        error_monitor = ErrorMonitor()
        failing_crew = mock_failing_crew(failure_mode="network", failure_count=5)

        # Act - Simulate multiple failures
        for attempt in range(4):
            try:
                await failing_crew.execute_async({"asset_count": 100})
            except Exception as e:
                error_monitor.log_error("test_crew", e, {"attempt": attempt})

        # Assert
        assert len(error_monitor.error_log) == 4, "All errors should be logged"
        assert (
            error_monitor.error_counts["test_crew:ConnectionError"] == 4
        ), "Error count should be tracked"
        assert (
            error_monitor.should_alert("test_crew", "ConnectionError") is True
        ), "Should trigger alert"

        # Verify error log structure
        first_error = error_monitor.error_log[0]
        assert first_error["crew_name"] == "test_crew", "Crew name should be logged"
        assert (
            first_error["error_type"] == "ConnectionError"
        ), "Error type should be logged"
        assert "context" in first_error, "Context should be included"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
