#!/usr/bin/env python3
"""
Multi-Tenant Flow Manager for Master Flow Orchestrator
MFO-026: Create multi-tenant flow manager with isolation logic

This manager ensures complete tenant isolation across all flow operations
including data access, resource allocation, and security boundaries.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.context import RequestContext
from app.core.exceptions import ValidationError
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.crewai_flows.enhanced_flow_state_manager import EnhancedFlowStateManager

logger = logging.getLogger(__name__)


class TenantIsolationLevel(Enum):
    """Levels of tenant isolation"""
    STRICT = "strict"           # Complete isolation, no cross-tenant access
    CONTROLLED = "controlled"   # Limited cross-tenant access for admin operations
    SHARED = "shared"          # Shared resources with tenant-aware filtering


@dataclass
class TenantQuota:
    """Resource quotas per tenant"""
    max_concurrent_flows: int = 10
    max_total_flows_per_day: int = 100
    max_storage_mb: int = 1000
    max_cpu_units: int = 100
    max_memory_mb: int = 2048
    max_execution_time_minutes: int = 60
    priority_level: int = 1  # 1=low, 5=high


@dataclass
class TenantMetrics:
    """Current metrics for a tenant"""
    client_account_id: int
    current_flows: int = 0
    total_flows_today: int = 0
    storage_used_mb: float = 0.0
    cpu_used_units: float = 0.0
    memory_used_mb: float = 0.0
    last_activity: Optional[datetime] = None
    quota: TenantQuota = field(default_factory=TenantQuota)


class TenantIsolationError(Exception):
    """Raised when tenant isolation is violated"""
    pass


class TenantQuotaExceededError(Exception):
    """Raised when tenant quota is exceeded"""
    pass


class MultiTenantFlowManager:
    """
    Multi-tenant flow manager with complete isolation logic
    Ensures tenant boundaries are respected across all operations
    """
    
    def __init__(
        self,
        db: AsyncSession,
        isolation_level: TenantIsolationLevel = TenantIsolationLevel.STRICT
    ):
        self.db = db
        self.isolation_level = isolation_level
        
        # Tenant management
        self._tenant_metrics: Dict[int, TenantMetrics] = {}
        self._tenant_quotas: Dict[int, TenantQuota] = {}
        self._tenant_orchestrators: Dict[int, MasterFlowOrchestrator] = {}
        
        # Resource tracking
        self._resource_locks: Dict[str, Set[int]] = defaultdict(set)
        self._flow_tenant_mapping: Dict[str, int] = {}
        
        # Metrics collection
        self._metrics_lock = asyncio.Lock()
        
        logger.info(f"✅ Multi-tenant flow manager initialized with {isolation_level.value} isolation")
    
    async def get_tenant_orchestrator(self, context: RequestContext) -> MasterFlowOrchestrator:
        """Get or create tenant-specific orchestrator"""
        client_account_id = context.client_account_id
        
        # Validate tenant access
        await self._validate_tenant_access(context)
        
        # Get or create orchestrator for this tenant
        if client_account_id not in self._tenant_orchestrators:
            orchestrator = MasterFlowOrchestrator(self.db, context)
            self._tenant_orchestrators[client_account_id] = orchestrator
            logger.info(f"✅ Created orchestrator for tenant {client_account_id}")
        
        return self._tenant_orchestrators[client_account_id]
    
    async def create_tenant_flow(
        self,
        context: RequestContext,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a flow with tenant isolation"""
        try:
            # Validate tenant quotas
            await self._check_tenant_quotas(context, "create_flow")
            
            # Get tenant orchestrator
            orchestrator = await self.get_tenant_orchestrator(context)
            
            # Create flow through orchestrator
            flow_id, flow_details = await orchestrator.create_flow(
                flow_type=flow_type,
                flow_name=flow_name,
                configuration=configuration,
                initial_state=initial_state
            )
            
            # Track flow for tenant
            await self._track_tenant_flow(context.client_account_id, flow_id, "created")
            
            # Update metrics
            await self._update_tenant_metrics(context.client_account_id, "flow_created")
            
            logger.info(f"✅ Created tenant flow {flow_id} for client {context.client_account_id}")
            
            return {
                "flow_id": flow_id,
                "flow_details": flow_details,
                "tenant_info": {
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id,
                    "isolation_level": self.isolation_level.value
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create tenant flow: {e}")
            raise
    
    async def execute_tenant_flow_phase(
        self,
        context: RequestContext,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute flow phase with tenant validation"""
        try:
            # Validate tenant access to flow
            await self._validate_flow_access(context, flow_id)
            
            # Check quotas for execution
            await self._check_tenant_quotas(context, "execute_phase")
            
            # Get tenant orchestrator
            orchestrator = await self.get_tenant_orchestrator(context)
            
            # Execute phase
            result = await orchestrator.execute_phase(
                flow_id=flow_id,
                phase_name=phase_name,
                phase_input=phase_input,
                validation_overrides=validation_overrides
            )
            
            # Update metrics
            await self._update_tenant_metrics(context.client_account_id, "phase_executed")
            
            logger.info(f"✅ Executed phase {phase_name} for tenant flow {flow_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to execute tenant flow phase: {e}")
            raise
    
    async def get_tenant_flows(
        self,
        context: RequestContext,
        flow_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get flows for a specific tenant"""
        try:
            # Validate tenant access
            await self._validate_tenant_access(context)
            
            # Get tenant orchestrator
            orchestrator = await self.get_tenant_orchestrator(context)
            
            # Get active flows for this tenant
            flows = await orchestrator.get_active_flows(flow_type, limit)
            
            # Apply additional tenant filtering
            tenant_flows = []
            for flow in flows:
                if await self._validate_flow_ownership(context.client_account_id, flow["flow_id"]):
                    # Add tenant-specific metadata
                    flow["tenant_info"] = {
                        "client_account_id": context.client_account_id,
                        "engagement_id": context.engagement_id,
                        "isolation_level": self.isolation_level.value
                    }
                    
                    if status_filter is None or flow.get("status") == status_filter:
                        tenant_flows.append(flow)
            
            logger.info(f"✅ Retrieved {len(tenant_flows)} flows for tenant {context.client_account_id}")
            return tenant_flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get tenant flows: {e}")
            raise
    
    async def delete_tenant_flow(
        self,
        context: RequestContext,
        flow_id: str,
        soft_delete: bool = True,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a tenant flow with isolation validation"""
        try:
            # Validate tenant access to flow
            await self._validate_flow_access(context, flow_id)
            
            # Get tenant orchestrator
            orchestrator = await self.get_tenant_orchestrator(context)
            
            # Delete flow
            result = await orchestrator.delete_flow(
                flow_id=flow_id,
                soft_delete=soft_delete,
                reason=reason
            )
            
            # Update tracking
            await self._track_tenant_flow(context.client_account_id, flow_id, "deleted")
            
            # Update metrics
            await self._update_tenant_metrics(context.client_account_id, "flow_deleted")
            
            logger.info(f"✅ Deleted tenant flow {flow_id} for client {context.client_account_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to delete tenant flow: {e}")
            raise
    
    async def get_tenant_metrics(self, context: RequestContext) -> Dict[str, Any]:
        """Get metrics for a specific tenant"""
        try:
            await self._validate_tenant_access(context)
            
            client_account_id = context.client_account_id
            
            # Get current metrics
            metrics = await self._get_tenant_metrics(client_account_id)
            
            # Get quota information
            quota = self._tenant_quotas.get(client_account_id, TenantQuota())
            
            # Calculate usage percentages
            quota_usage = {
                "concurrent_flows": (metrics.current_flows / quota.max_concurrent_flows) * 100,
                "daily_flows": (metrics.total_flows_today / quota.max_total_flows_per_day) * 100,
                "storage": (metrics.storage_used_mb / quota.max_storage_mb) * 100,
                "cpu": (metrics.cpu_used_units / quota.max_cpu_units) * 100,
                "memory": (metrics.memory_used_mb / quota.max_memory_mb) * 100
            }
            
            return {
                "client_account_id": client_account_id,
                "current_metrics": {
                    "current_flows": metrics.current_flows,
                    "total_flows_today": metrics.total_flows_today,
                    "storage_used_mb": metrics.storage_used_mb,
                    "cpu_used_units": metrics.cpu_used_units,
                    "memory_used_mb": metrics.memory_used_mb,
                    "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
                },
                "quotas": {
                    "max_concurrent_flows": quota.max_concurrent_flows,
                    "max_total_flows_per_day": quota.max_total_flows_per_day,
                    "max_storage_mb": quota.max_storage_mb,
                    "max_cpu_units": quota.max_cpu_units,
                    "max_memory_mb": quota.max_memory_mb,
                    "max_execution_time_minutes": quota.max_execution_time_minutes,
                    "priority_level": quota.priority_level
                },
                "usage_percentages": quota_usage,
                "isolation_level": self.isolation_level.value,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get tenant metrics: {e}")
            raise
    
    async def set_tenant_quota(
        self,
        admin_context: RequestContext,
        target_client_account_id: int,
        quota: TenantQuota
    ) -> Dict[str, Any]:
        """Set quota for a tenant (admin operation)"""
        try:
            # Validate admin permissions
            await self._validate_admin_access(admin_context)
            
            # Set quota
            self._tenant_quotas[target_client_account_id] = quota
            
            logger.info(f"✅ Set quota for tenant {target_client_account_id}")
            
            return {
                "target_client_account_id": target_client_account_id,
                "quota_set": True,
                "quota": {
                    "max_concurrent_flows": quota.max_concurrent_flows,
                    "max_total_flows_per_day": quota.max_total_flows_per_day,
                    "max_storage_mb": quota.max_storage_mb,
                    "max_cpu_units": quota.max_cpu_units,
                    "max_memory_mb": quota.max_memory_mb,
                    "priority_level": quota.priority_level
                },
                "set_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to set tenant quota: {e}")
            raise
    
    async def get_all_tenant_metrics(self, admin_context: RequestContext) -> Dict[str, Any]:
        """Get metrics for all tenants (admin operation)"""
        try:
            # Validate admin permissions
            await self._validate_admin_access(admin_context)
            
            all_metrics = {}
            
            for client_account_id in self._tenant_metrics.keys():
                metrics = await self._get_tenant_metrics(client_account_id)
                quota = self._tenant_quotas.get(client_account_id, TenantQuota())
                
                all_metrics[str(client_account_id)] = {
                    "current_flows": metrics.current_flows,
                    "total_flows_today": metrics.total_flows_today,
                    "storage_used_mb": metrics.storage_used_mb,
                    "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                    "quota": {
                        "max_concurrent_flows": quota.max_concurrent_flows,
                        "priority_level": quota.priority_level
                    }
                }
            
            return {
                "total_tenants": len(all_metrics),
                "tenants": all_metrics,
                "isolation_level": self.isolation_level.value,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get all tenant metrics: {e}")
            raise
    
    # Private methods for tenant management
    
    async def _validate_tenant_access(self, context: RequestContext) -> None:
        """Validate tenant has access rights"""
        if not context.client_account_id:
            raise TenantIsolationError("Missing client_account_id in context")
        
        if not context.engagement_id:
            raise TenantIsolationError("Missing engagement_id in context")
        
        # Check if tenant is active
        if not await self._is_tenant_active(context.client_account_id):
            raise TenantIsolationError(f"Tenant {context.client_account_id} is not active")
    
    async def _validate_flow_access(self, context: RequestContext, flow_id: str) -> None:
        """Validate tenant has access to specific flow"""
        await self._validate_tenant_access(context)
        
        # Check flow ownership
        if not await self._validate_flow_ownership(context.client_account_id, flow_id):
            raise TenantIsolationError(f"Tenant {context.client_account_id} does not own flow {flow_id}")
    
    async def _validate_flow_ownership(self, client_account_id: int, flow_id: str) -> bool:
        """Validate that tenant owns the specified flow"""
        try:
            # Query database to verify ownership
            query = text("""
                SELECT client_account_id
                FROM crewai_flow_state_extensions
                WHERE flow_id = :flow_id
            """)
            
            result = await self.db.execute(query, {"flow_id": flow_id})
            row = result.fetchone()
            
            if row:
                return row.client_account_id == client_account_id
            
            # Check in flow mapping
            return self._flow_tenant_mapping.get(flow_id) == client_account_id
            
        except Exception as e:
            logger.error(f"❌ Failed to validate flow ownership: {e}")
            return False
    
    async def _validate_admin_access(self, context: RequestContext) -> None:
        """Validate admin access for cross-tenant operations"""
        if self.isolation_level == TenantIsolationLevel.STRICT:
            # In strict mode, check if user has platform admin role
            if not await self._is_platform_admin(context.user_id):
                raise TenantIsolationError("Admin access required for cross-tenant operations")
        
        # Additional admin validation logic here
    
    async def _is_tenant_active(self, client_account_id: int) -> bool:
        """Check if tenant is active"""
        try:
            query = text("""
                SELECT status
                FROM client_accounts
                WHERE id = :client_account_id
            """)
            
            result = await self.db.execute(query, {"client_account_id": client_account_id})
            row = result.fetchone()
            
            return row and row.status == "active"
            
        except Exception as e:
            logger.error(f"❌ Failed to check tenant status: {e}")
            return False
    
    async def _is_platform_admin(self, user_id: str) -> bool:
        """Check if user is platform admin"""
        try:
            query = text("""
                SELECT r.name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE u.id = :user_id AND r.name = 'platform_admin'
            """)
            
            result = await self.db.execute(query, {"user_id": user_id})
            return result.fetchone() is not None
            
        except Exception as e:
            logger.error(f"❌ Failed to check admin status: {e}")
            return False
    
    async def _check_tenant_quotas(self, context: RequestContext, operation: str) -> None:
        """Check if tenant has quota available for operation"""
        client_account_id = context.client_account_id
        metrics = await self._get_tenant_metrics(client_account_id)
        quota = self._tenant_quotas.get(client_account_id, TenantQuota())
        
        # Check concurrent flows
        if operation == "create_flow" and metrics.current_flows >= quota.max_concurrent_flows:
            raise TenantQuotaExceededError(
                f"Concurrent flows quota exceeded: {metrics.current_flows}/{quota.max_concurrent_flows}"
            )
        
        # Check daily flows
        if operation == "create_flow" and metrics.total_flows_today >= quota.max_total_flows_per_day:
            raise TenantQuotaExceededError(
                f"Daily flows quota exceeded: {metrics.total_flows_today}/{quota.max_total_flows_per_day}"
            )
        
        # Check storage
        if metrics.storage_used_mb >= quota.max_storage_mb:
            raise TenantQuotaExceededError(
                f"Storage quota exceeded: {metrics.storage_used_mb:.2f}/{quota.max_storage_mb} MB"
            )
        
        # Check CPU
        if metrics.cpu_used_units >= quota.max_cpu_units:
            raise TenantQuotaExceededError(
                f"CPU quota exceeded: {metrics.cpu_used_units:.2f}/{quota.max_cpu_units} units"
            )
        
        # Check memory
        if metrics.memory_used_mb >= quota.max_memory_mb:
            raise TenantQuotaExceededError(
                f"Memory quota exceeded: {metrics.memory_used_mb:.2f}/{quota.max_memory_mb} MB"
            )
    
    async def _track_tenant_flow(self, client_account_id: int, flow_id: str, action: str) -> None:
        """Track flow operations for tenant metrics"""
        self._flow_tenant_mapping[flow_id] = client_account_id
        
        # Update metrics based on action
        async with self._metrics_lock:
            if client_account_id not in self._tenant_metrics:
                self._tenant_metrics[client_account_id] = TenantMetrics(client_account_id)
            
            metrics = self._tenant_metrics[client_account_id]
            
            if action == "created":
                metrics.current_flows += 1
                metrics.total_flows_today += 1
            elif action == "deleted":
                metrics.current_flows = max(0, metrics.current_flows - 1)
            
            metrics.last_activity = datetime.utcnow()
    
    async def _update_tenant_metrics(self, client_account_id: int, operation: str) -> None:
        """Update tenant metrics for various operations"""
        async with self._metrics_lock:
            if client_account_id not in self._tenant_metrics:
                self._tenant_metrics[client_account_id] = TenantMetrics(client_account_id)
            
            metrics = self._tenant_metrics[client_account_id]
            metrics.last_activity = datetime.utcnow()
            
            # Update operation-specific metrics
            if operation == "phase_executed":
                metrics.cpu_used_units += 1.0  # Simplified CPU tracking
                metrics.memory_used_mb += 10.0  # Simplified memory tracking
    
    async def _get_tenant_metrics(self, client_account_id: int) -> TenantMetrics:
        """Get current metrics for tenant"""
        if client_account_id not in self._tenant_metrics:
            self._tenant_metrics[client_account_id] = TenantMetrics(client_account_id)
        
        # Update real-time metrics from database
        await self._refresh_tenant_metrics_from_db(client_account_id)
        
        return self._tenant_metrics[client_account_id]
    
    async def _refresh_tenant_metrics_from_db(self, client_account_id: int) -> None:
        """Refresh tenant metrics from database"""
        try:
            # Get current flow count
            flow_count_query = text("""
                SELECT COUNT(*) as current_flows
                FROM crewai_flow_state_extensions
                WHERE client_account_id = :client_account_id
                AND flow_status NOT IN ('completed', 'failed', 'deleted')
            """)
            
            result = await self.db.execute(flow_count_query, {"client_account_id": client_account_id})
            current_flows = result.scalar() or 0
            
            # Get daily flow count
            daily_query = text("""
                SELECT COUNT(*) as daily_flows
                FROM crewai_flow_state_extensions
                WHERE client_account_id = :client_account_id
                AND DATE(created_at) = CURRENT_DATE
            """)
            
            result = await self.db.execute(daily_query, {"client_account_id": client_account_id})
            daily_flows = result.scalar() or 0
            
            # Update metrics
            if client_account_id in self._tenant_metrics:
                self._tenant_metrics[client_account_id].current_flows = current_flows
                self._tenant_metrics[client_account_id].total_flows_today = daily_flows
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh tenant metrics: {e}")


# Factory function for creating multi-tenant flow managers
async def create_multi_tenant_flow_manager(
    db: AsyncSession,
    isolation_level: TenantIsolationLevel = TenantIsolationLevel.STRICT
) -> MultiTenantFlowManager:
    """Create a multi-tenant flow manager"""
    return MultiTenantFlowManager(db, isolation_level)


# Utility functions
async def get_tenant_orchestrator(
    context: RequestContext,
    isolation_level: TenantIsolationLevel = TenantIsolationLevel.STRICT
) -> MasterFlowOrchestrator:
    """Get tenant-specific orchestrator"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        manager = await create_multi_tenant_flow_manager(db, isolation_level)
        return await manager.get_tenant_orchestrator(context)


async def validate_tenant_flow_access(
    context: RequestContext,
    flow_id: str,
    db: AsyncSession
) -> bool:
    """Validate tenant has access to specific flow"""
    manager = MultiTenantFlowManager(db)
    try:
        await manager._validate_flow_access(context, flow_id)
        return True
    except TenantIsolationError:
        return False