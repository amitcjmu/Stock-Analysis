"""
Flow State Bridge
PostgreSQL-only persistence for CrewAI flows.
Single source of truth implementation replacing dual SQLite/PostgreSQL system.
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.context import RequestContext
from .postgresql_flow_persistence import PostgreSQLFlowPersistence

logger = logging.getLogger(__name__)

class FlowStateBridge:
    """
    PostgreSQL-only persistence bridge for CrewAI flows.
    
    Single source of truth implementation that:
    1. Uses PostgreSQL as the only persistence layer
    2. Provides enterprise multi-tenancy and data isolation
    3. Includes state validation and recovery mechanisms
    4. Supports atomic operations and optimistic locking
    """
    
    def __init__(self, context: RequestContext):
        """Initialize bridge with tenant context"""
        self.context = context
        self.pg_persistence = PostgreSQLFlowPersistence(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id
        )
        self._state_sync_enabled = True
    
    async def initialize_flow_state(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """
        Initialize flow state in PostgreSQL as single source of truth.
        Called when flow starts execution.
        """
        try:
            logger.info(f"🔄 Initializing PostgreSQL-only flow state: {state.flow_id}")
            logger.info(f"   📋 Session context: {state.session_id}")
            
            # Persist to PostgreSQL as single source of truth
            pg_result = await self.pg_persistence.persist_flow_initialization(state)
            
            logger.info(f"✅ PostgreSQL flow state initialized: Flow ID={state.flow_id}")
            
            return {
                "status": "success",
                "postgresql_persistence": pg_result,
                "persistence_model": "postgresql_only",
                "bridge_enabled": True
            }
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL flow state initialization failed: {e}")
            return {
                "status": "failed",
                "postgresql_persistence": {"status": "failed", "error": str(e)},
                "persistence_model": "postgresql_only",
                "bridge_enabled": False
            }
    
    async def sync_state_update(self, state: UnifiedDiscoveryFlowState, phase: str, crew_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update PostgreSQL state as single source of truth.
        Called during phase transitions and state changes.
        """
        if not self._state_sync_enabled:
            return {"status": "sync_disabled"}
        
        try:
            # Update PostgreSQL state (single source of truth)
            pg_result = await self.pg_persistence.update_workflow_state(state)
            
            # Log phase completion if crew results provided
            if crew_results:
                await self.pg_persistence.persist_phase_completion(state, phase, crew_results)
            
            logger.debug(f"🔄 PostgreSQL state updated for Flow ID: {state.flow_id}, phase: {phase}")
            
            return {
                "status": "success",
                "postgresql_update": pg_result,
                "phase": phase,
                "crew_results_logged": crew_results is not None,
                "persistence_model": "postgresql_only"
            }
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL state update failed: {e}")
            return {
                "status": "update_failed",
                "error": str(e),
                "persistence_model": "postgresql_only"
            }
    
    async def update_flow_state(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """
        Update flow state in PostgreSQL persistence layer.
        This method provides compatibility with the UnifiedDiscoveryFlow expectations.
        """
        try:
            # Determine current phase from state
            current_phase = getattr(state, 'current_phase', 'unknown')
            
            # Extract and ensure processing statistics are at root level of state data
            # This is critical for the frontend to receive the correct record counts
            state_dict = state.model_dump()
            
            # Ensure these fields are available at the root level for API responses
            processing_fields = ['records_processed', 'records_total', 'records_valid', 'records_failed']
            for field in processing_fields:
                if hasattr(state, field):
                    state_dict[field] = getattr(state, field)
            
            # Handle phase mapping for parallel analysis phases
            if current_phase == "analysis":
                # For analysis phase, update individual component phases based on completion status
                analysis_results = []
                
                # Check which analysis components completed and update them individually
                if state.phase_completion.get('asset_inventory', False):
                    inventory_result = await self.pg_persistence.update_workflow_state(state)
                    await self.pg_persistence.persist_phase_completion(state, "inventory", {
                        "assets": state.asset_inventory,
                        "confidence": state.agent_confidences.get('asset_inventory', 0.0)
                    })
                    analysis_results.append(("inventory", inventory_result))
                
                if state.phase_completion.get('dependency_analysis', False):
                    deps_result = await self.pg_persistence.update_workflow_state(state)
                    await self.pg_persistence.persist_phase_completion(state, "dependencies", {
                        "dependencies": state.dependency_analysis,
                        "confidence": state.agent_confidences.get('dependency_analysis', 0.0)
                    })
                    analysis_results.append(("dependencies", deps_result))
                
                if state.phase_completion.get('tech_debt_analysis', False):
                    tech_debt_result = await self.pg_persistence.update_workflow_state(state)
                    await self.pg_persistence.persist_phase_completion(state, "tech_debt", {
                        "tech_debt": state.tech_debt_analysis,
                        "confidence": state.agent_confidences.get('tech_debt_analysis', 0.0)
                    })
                    analysis_results.append(("tech_debt", tech_debt_result))
                
                logger.debug(f"🔄 Analysis phase components updated for CrewAI Flow ID: {state.flow_id}")
                
                return {
                    "status": "success",
                    "postgresql_update": analysis_results,
                    "phase": "analysis (multi-component)",
                    "flow_id": state.flow_id,
                    "components_updated": len(analysis_results)
                }
            else:
                # Standard single-phase update
                pg_result = await self.pg_persistence.update_workflow_state(state)
                
                logger.debug(f"🔄 Flow state updated for CrewAI Flow ID: {state.flow_id}, phase: {current_phase}")
                
                return {
                    "status": "success",
                    "postgresql_update": pg_result,
                    "phase": current_phase,
                    "flow_id": state.flow_id
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Flow state update failed (non-critical): {e}")
            # Don't fail the flow - this is supplementary persistence
            return {
                "status": "update_failed",
                "error": str(e),
                "impact": "PostgreSQL state may be stale, but CrewAI flow continues"
            }
    
    async def recover_flow_state(self, session_id: str) -> Optional[UnifiedDiscoveryFlowState]:
        """
        Recover flow state from PostgreSQL when CrewAI persistence fails.
        Provides fallback recovery mechanism.
        """
        try:
            logger.info(f"🔄 Attempting flow state recovery for session: {session_id}")
            
            # Try to restore from PostgreSQL
            restored_state = await self.pg_persistence.restore_flow_state(session_id)
            
            if restored_state:
                logger.info(f"✅ Flow state recovered from PostgreSQL: {session_id}")
                return restored_state
            else:
                logger.warning(f"⚠️ No recoverable state found for session: {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Flow state recovery failed: {e}")
            return None
    
    async def validate_state_integrity(self, session_id: str) -> Dict[str, Any]:
        """
        Validate PostgreSQL flow state integrity.
        Comprehensive health check for state consistency.
        """
        try:
            # Validate PostgreSQL state integrity (single source of truth)
            pg_validation = await self.pg_persistence.validate_flow_integrity(session_id)
            
            overall_valid = pg_validation.get("valid", False)
            
            return {
                "status": "validated",
                "session_id": session_id,
                "overall_valid": overall_valid,
                "postgresql_validation": pg_validation,
                "persistence_model": "postgresql_only",
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL state integrity validation failed: {e}")
            return {
                "status": "validation_error",
                "session_id": session_id,
                "overall_valid": False,
                "error": str(e),
                "persistence_model": "postgresql_only"
            }
    
    async def cleanup_expired_states(self, expiration_hours: int = 72) -> Dict[str, Any]:
        """
        Clean up expired flow states from PostgreSQL.
        Single source of truth cleanup.
        """
        try:
            cleanup_result = await self.pg_persistence.cleanup_expired_flows(expiration_hours)
            
            logger.info(f"✅ PostgreSQL cleanup completed: {cleanup_result.get('flows_cleaned', 0)} flows cleaned")
            
            return {
                "status": "success",
                "postgresql_cleanup": cleanup_result,
                "persistence_model": "postgresql_only"
            }
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL cleanup failed: {e}")
            return {
                "status": "cleanup_error",
                "error": str(e),
                "persistence_model": "postgresql_only"
            }
    
    def disable_sync(self, reason: str = "performance_optimization"):
        """
        Temporarily disable PostgreSQL state updates.
        Useful for performance optimization during intensive operations.
        """
        self._state_sync_enabled = False
        logger.info(f"🔄 PostgreSQL updates disabled: {reason}")
    
    def enable_sync(self):
        """Re-enable PostgreSQL state updates"""
        self._state_sync_enabled = True
        logger.info("🔄 PostgreSQL updates re-enabled")
    
    @asynccontextmanager
    async def sync_disabled(self, reason: str = "temporary_optimization"):
        """
        Context manager to temporarily disable sync during intensive operations.
        
        Usage:
            async with bridge.sync_disabled("bulk_processing"):
                # Intensive operations without state sync overhead
                pass
        """
        self.disable_sync(reason)
        try:
            yield
        finally:
            self.enable_sync()

# Factory function for creating flow state bridges
def create_flow_state_bridge(context: RequestContext) -> FlowStateBridge:
    """
    Factory function to create a flow state bridge with proper context.
    
    Args:
        context: RequestContext with tenant information
    
    Returns:
        FlowStateBridge instance configured for the tenant
    """
    return FlowStateBridge(context)

# Async context manager for automatic bridge lifecycle
@asynccontextmanager
async def managed_flow_bridge(context: RequestContext):
    """
    Async context manager for automatic bridge lifecycle management.
    
    Usage:
        async with managed_flow_bridge(context) as bridge:
            # Use bridge for flow operations
            await bridge.initialize_flow_state(state)
    """
    bridge = create_flow_state_bridge(context)
    try:
        yield bridge
    finally:
        # Cleanup if needed
        pass 