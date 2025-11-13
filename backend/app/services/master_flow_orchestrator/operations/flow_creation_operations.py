"""
Flow Creation Operations

Handles complex flow creation logic including:
- Redis cleanup and registration
- Retry mechanisms
- Atomic operations
- Comprehensive error handling
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_contracts import FlowAuditLogger, AuditCategory, AuditLevel

from .enums import FlowOperationType
from .flow_cache_manager import FlowCacheManager
from .mock_monitor import MockFlowPerformanceMonitor

logger = logging.getLogger(__name__)


class FlowCreationOperations:
    """Handles flow creation operations with comprehensive error handling"""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        cache_manager: FlowCacheManager,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.cache_manager = cache_manager

    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        atomic: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new flow with comprehensive error handling and cleanup

        Args:
            flow_type: Type of flow to create
            flow_name: Optional name for the flow
            configuration: Flow configuration
            initial_state: Initial flow state data
            atomic: If True, assumes we're already in a transaction (no commits)

        Returns:
            Tuple of (flow_id, flow_data)
        """
        flow_id = str(uuid4())
        tracking_id = None

        try:
            # Start performance monitoring
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="create_flow", metadata={}
            )

            logger.info(f"🚀 Creating flow: {flow_id} (type: {flow_type})")

            # Validate flow type
            if not self.flow_registry.is_registered(flow_type):
                raise ValueError(f"Unknown flow type: {flow_type}")

            # Prepare flow data
            flow_data = await self._prepare_flow_data(
                flow_id, flow_type, flow_name, configuration, initial_state
            )

            # Attempt Redis registration with cleanup logic
            redis_registered = await self._register_with_redis_cleanup(
                flow_id, flow_type, flow_data
            )

            # Create database record
            await self._create_database_record(flow_id, flow_data, atomic)

            # Execute flow creation through registry
            await self._execute_flow_creation(
                flow_id, flow_type, flow_data, redis_registered
            )

            # Warm cache for better performance
            await self.cache_manager.warm_cache_for_flow(flow_id)

            # Log successful creation
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.CREATE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"flow_type": flow_type, "flow_name": flow_name},
            )

            self.performance_monitor.end_operation(tracking_id, success=True)
            logger.info(f"✅ Flow created successfully: {flow_id}")

            return flow_id, flow_data

        except Exception as e:
            logger.error(f"❌ Flow creation failed: {flow_id} - {str(e)}")

            # Comprehensive cleanup on failure
            await self._cleanup_failed_creation(flow_id, e)

            # Log failure
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.CREATE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )

            if tracking_id:
                self.performance_monitor.end_operation(tracking_id, success=False)

            raise RuntimeError(f"Failed to create flow: {str(e)}")

    async def _prepare_flow_data(
        self,
        flow_id: str,
        flow_type: str,
        flow_name: Optional[str],
        configuration: Optional[Dict[str, Any]],
        initial_state: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare comprehensive flow data"""
        now = datetime.now(timezone.utc)

        return {
            "flow_id": flow_id,
            "flow_type": flow_type,
            "flow_name": flow_name or f"{flow_type.title()} Flow",
            "flow_status": "running",
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "flow_configuration": configuration or {},
            "flow_persistence_data": initial_state or {},
            "created_at": now,
            "updated_at": now,
            "created_by": self.context.user_id or "system",
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id,
            "metadata": {
                "creation_timestamp": now.isoformat(),
                "creation_context": "master_flow_orchestrator",
                "initial_configuration": configuration or {},
            },
        }

    async def _register_with_redis_cleanup(
        self, flow_id: str, flow_type: str, flow_data: Dict[str, Any]
    ) -> bool:
        """Register flow with Redis with comprehensive cleanup on failure"""
        try:
            from app.services.caching.redis_cache import redis_cache

            # Attempt atomic registration
            success = await redis_cache.register_flow_atomic(
                flow_id=flow_id,
                flow_type=flow_type,
                flow_data=flow_data,
            )

            if not success:
                logger.warning(f"⚠️ Redis registration failed for {flow_id}")
                retry_success = await self._handle_redis_registration_failure(
                    flow_id, flow_type, flow_data
                )
                return retry_success

            logger.info(f"✅ Redis registration successful for {flow_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Redis registration error for {flow_id}: {e}")
            retry_success = await self._handle_redis_registration_failure(
                flow_id, flow_type, flow_data
            )
            return retry_success

    async def _handle_redis_registration_failure(
        self, flow_id: str, flow_type: str, flow_data: Dict[str, Any]
    ) -> bool:
        """
        Handle Redis registration failure with comprehensive error handling

        Returns:
            bool: True if retry succeeded, False if Redis is unavailable or retry failed
        """
        try:
            from app.services.caching.redis_cache import redis_cache

            # First check if Redis is completely unavailable
            if not self._is_redis_available(redis_cache):
                logger.warning(
                    f"Redis is completely unavailable, continuing without Redis for {flow_id}"
                )
                return False

            logger.info(f"🔄 Attempting Redis cleanup and retry for {flow_id}")

            # Cleanup any partial registration with timeout
            try:
                await redis_cache.cleanup_partial_flow_registration(
                    flow_id, self.context.client_account_id, self.context.engagement_id
                )
                logger.debug(f"Redis cleanup completed for {flow_id}")
            except Exception as cleanup_error:
                logger.warning(f"Redis cleanup failed for {flow_id}: {cleanup_error}")
                # Don't fail completely if cleanup fails, continue with retry

            # Wait briefly and retry once
            import asyncio

            await asyncio.sleep(0.1)

            try:
                retry_success = await redis_cache.register_flow_atomic(
                    flow_id=flow_id,
                    flow_type=flow_type,
                    flow_data=flow_data,
                )

                if retry_success:
                    logger.info(f"✅ Redis registration retry successful for {flow_id}")
                    return True
                else:
                    logger.warning(
                        f"⚠️ Redis registration retry also failed for {flow_id}"
                    )
                    return False

            except Exception as retry_error:
                logger.warning(
                    f"Redis registration retry error for {flow_id}: {retry_error}"
                )
                return False

        except ImportError:
            logger.warning(f"Redis service not available for {flow_id}")
            return False
        except Exception as retry_error:
            logger.error(f"❌ Redis cleanup/retry failed for {flow_id}: {retry_error}")
            return False

    def _is_redis_available(self, redis_cache) -> bool:
        """Check if Redis is available and accessible"""
        try:
            # Check if redis_cache exists and has a client
            if not redis_cache or not hasattr(redis_cache, "client"):
                return False

            # Check if client is None (common indicator Redis is unavailable)
            if redis_cache.client is None:
                return False

            return True

        except Exception:
            return False

    async def _create_database_record(
        self, flow_id: str, flow_data: Dict[str, Any], atomic: bool = False
    ) -> CrewAIFlowStateExtensions:
        """Create database record for the flow

        Args:
            flow_id: Unique flow identifier
            flow_data: Flow configuration data
            atomic: If True, only flush (parent will commit). If False, commit immediately.
        """
        master_flow = CrewAIFlowStateExtensions(
            flow_id=flow_id,
            flow_type=flow_data["flow_type"],
            flow_name=flow_data["flow_name"],
            flow_status=flow_data["flow_status"],
            flow_configuration=flow_data["flow_configuration"],
            flow_persistence_data=flow_data["flow_persistence_data"],
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            user_id=self.context.user_id or "system",
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
        )

        # Add to session
        self.db.add(master_flow)

        # Per ADR-006: Respect atomic parameter for transaction control
        if atomic:
            # We're in a parent transaction, just flush (parent will commit)
            await self.db.flush()
            logger.info(
                f"✅ Database record flushed for flow {flow_id} (atomic=True, parent will commit)"
            )
        else:
            # Not in parent transaction, commit immediately
            await self.db.commit()
            logger.info(f"✅ Database record committed for flow {flow_id}")

        await self.db.refresh(master_flow)

        return master_flow

    async def _execute_flow_creation(
        self,
        flow_id: str,
        flow_type: str,
        flow_data: Dict[str, Any],
        redis_registered: bool,
    ) -> Dict[str, Any]:
        """Execute flow creation through the registry"""
        try:
            # Get flow configuration from registry
            flow_config = self.flow_registry.get_flow_config(flow_type)

            # Create flow instance using crew_class if available and compatible
            can_instantiate = bool(flow_config.crew_class)
            # Special-case discovery: actual instantiation is handled later by the initializer
            if flow_type == "discovery":
                can_instantiate = False

            if can_instantiate:
                try:
                    flow_instance = flow_config.crew_class(
                        flow_id=flow_id,
                        initial_state=flow_data.get("flow_persistence_data", {}),
                        configuration=flow_data.get("flow_configuration", {}),
                        context=self.context,
                    )

                    # Execute initialization if the instance has an initialize method
                    initialization_result = None
                    if hasattr(flow_instance, "initialize"):
                        initialization_result = await flow_instance.initialize()
                except TypeError as e:
                    # Fallback for crew classes that require additional dependencies (e.g., crewai_service)
                    logger.warning(
                        f"Crew class instantiation fallback for {flow_type}: {e}"
                    )
                    flow_instance = {
                        "flow_id": flow_id,
                        "flow_type": flow_type,
                        "configuration": flow_data.get("flow_configuration", {}),
                        "state": flow_data.get("flow_persistence_data", {}),
                    }
                    initialization_result = {
                        "status": "initialized",
                        "message": "Flow created (deferred crew instantiation handled by initializer)",
                    }
            else:
                # Fallback: create a simple flow instance dict
                flow_instance = {
                    "flow_id": flow_id,
                    "flow_type": flow_type,
                    "configuration": flow_data.get("flow_configuration", {}),
                    "state": flow_data.get("flow_persistence_data", {}),
                }
                initialization_result = {
                    "status": "initialized",
                    "message": "Flow created successfully",
                }

            logger.info(f"✅ Flow instance created and initialized for {flow_id}")

            return {
                "flow_instance": flow_instance,
                "initialization_result": initialization_result,
                "redis_registered": redis_registered,
            }

        except Exception as e:
            logger.error(f"❌ Flow creation execution failed for {flow_id}: {e}")
            raise

    async def _cleanup_failed_creation(self, flow_id: str, error: Exception) -> None:
        """Comprehensive cleanup after failed flow creation"""
        logger.info(f"🧹 Cleaning up failed flow creation: {flow_id}")

        cleanup_results = []

        # 1. Database cleanup
        try:
            # Remove from database if it was created
            await self.master_repo.delete_master_flow(flow_id)
            cleanup_results.append("✅ Database cleanup successful")
        except Exception as db_error:
            cleanup_results.append(f"❌ Database cleanup failed: {db_error}")

        # 2. Redis cleanup
        try:
            from app.services.caching.redis_cache import redis_cache

            await redis_cache.cleanup_failed_flow_creation(
                flow_id,
                self.context.client_account_id,
                self.context.engagement_id,
            )
            cleanup_results.append("✅ Redis cleanup successful")
        except Exception as redis_error:
            cleanup_results.append(f"❌ Redis cleanup failed: {redis_error}")

        # 3. Cache invalidation
        try:
            await self.cache_manager.invalidate_comprehensive_cache(
                flow_id, operation_type="cleanup"
            )
            cleanup_results.append("✅ Cache cleanup successful")
        except Exception as cache_error:
            cleanup_results.append(f"❌ Cache cleanup failed: {cache_error}")

        # Log cleanup results
        for result in cleanup_results:
            logger.info(f"  {result}")

        logger.info(f"🧹 Cleanup completed for failed flow {flow_id}")
