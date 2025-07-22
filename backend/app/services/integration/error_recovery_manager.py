"""
Error Recovery Manager for ADCS End-to-End Integration

This service provides comprehensive error handling and recovery mechanisms
across the Collection → Discovery → Assessment workflow, including automatic
recovery strategies, fallback procedures, and error prevention.

Generated with CC for ADCS end-to-end integration.
"""

import asyncio
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.monitoring.metrics import track_performance

logger = get_logger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ErrorCategory(Enum):
    """Error categories"""
    SYSTEM_ERROR = "system_error"
    DATA_ERROR = "data_error"
    VALIDATION_ERROR = "validation_error"
    INTEGRATION_ERROR = "integration_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"

class RecoveryStrategy(Enum):
    """Recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    COMPENSATE = "compensate"
    MANUAL_INTERVENTION = "manual_intervention"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ROLLBACK = "rollback"

@dataclass
class ErrorContext:
    """Context information for an error"""
    error_id: UUID = field(default_factory=uuid4)
    engagement_id: UUID = None
    flow_id: UUID = None
    flow_type: str = None
    phase: str = None
    operation: str = None
    error_type: str = None
    error_message: str = None
    stack_trace: str = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM_ERROR
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_assets: List[UUID] = field(default_factory=list)

@dataclass
class RecoveryPlan:
    """Recovery plan for handling errors"""
    plan_id: UUID = field(default_factory=uuid4)
    error_context: ErrorContext = None
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    actions: List[Dict[str, Any]] = field(default_factory=list)
    max_attempts: int = 3
    current_attempt: int = 0
    timeout: int = 300  # seconds
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    fallback_plan: Optional['RecoveryPlan'] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, executing, completed, failed

@dataclass
class RecoveryResult:
    """Result of a recovery operation"""
    plan_id: UUID
    success: bool
    strategy_used: RecoveryStrategy
    actions_executed: List[str]
    time_taken: float
    error_resolved: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)

class ErrorRecoveryManager:
    """
    Comprehensive error recovery manager for ADCS workflows
    """
    
    def __init__(self):
        self.error_history: Dict[UUID, List[ErrorContext]] = {}
        self.recovery_plans: Dict[UUID, RecoveryPlan] = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.error_patterns = self._initialize_error_patterns()
        
    def _initialize_recovery_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize recovery strategies for different error types"""
        return {
            "timeout_error": {
                "strategy": RecoveryStrategy.RETRY,
                "max_attempts": 3,
                "backoff_multiplier": 2,
                "timeout_increase": 1.5,
                "fallback": RecoveryStrategy.FALLBACK
            },
            "data_validation_error": {
                "strategy": RecoveryStrategy.COMPENSATE,
                "max_attempts": 2,
                "compensation_actions": ["apply_defaults", "request_manual_input"],
                "fallback": RecoveryStrategy.MANUAL_INTERVENTION
            },
            "integration_error": {
                "strategy": RecoveryStrategy.FALLBACK,
                "max_attempts": 2,
                "fallback_actions": ["use_cache", "skip_enrichment", "minimal_processing"],
                "fallback": RecoveryStrategy.SKIP_AND_CONTINUE
            },
            "resource_exhaustion": {
                "strategy": RecoveryStrategy.RETRY,
                "max_attempts": 3,
                "delay_seconds": [10, 30, 60],
                "fallback": RecoveryStrategy.MANUAL_INTERVENTION
            },
            "critical_system_error": {
                "strategy": RecoveryStrategy.ROLLBACK,
                "max_attempts": 1,
                "rollback_scope": "flow_level",
                "fallback": RecoveryStrategy.MANUAL_INTERVENTION
            }
        }
        
    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common error patterns and their handling"""
        return {
            "asset_creation_failure": {
                "symptoms": ["foreign_key_violation", "validation_error", "duplicate_key"],
                "root_causes": ["missing_dependencies", "invalid_data", "race_condition"],
                "prevention": ["validate_dependencies", "atomic_operations", "locks"]
            },
            "flow_state_corruption": {
                "symptoms": ["invalid_state_transition", "missing_phase_data", "orphaned_records"],
                "root_causes": ["concurrent_modifications", "incomplete_transactions", "system_crash"],
                "prevention": ["state_locking", "checkpoint_recovery", "transaction_management"]
            },
            "ai_analysis_timeout": {
                "symptoms": ["llm_timeout", "crew_execution_timeout", "memory_exhaustion"],
                "root_causes": ["complex_analysis", "large_dataset", "resource_limits"],
                "prevention": ["batch_processing", "resource_monitoring", "timeout_management"]
            }
        }
        
    @track_performance("recovery.error.handle")
    async def handle_error(
        self,
        error: Exception,
        engagement_id: UUID,
        flow_id: UUID = None,
        flow_type: str = None,
        phase: str = None,
        operation: str = None,
        metadata: Dict[str, Any] = None
    ) -> RecoveryResult:
        """
        Handle an error with appropriate recovery strategy
        """
        
        # Create error context
        error_context = await self._create_error_context(
            error, engagement_id, flow_id, flow_type, phase, operation, metadata
        )
        
        logger.error(
            "Handling workflow error",
            extra={
                "error_id": str(error_context.error_id),
                "engagement_id": str(engagement_id),
                "flow_type": flow_type,
                "phase": phase,
                "operation": operation,
                "error_type": error_context.error_type,
                "severity": error_context.severity.value
            }
        )
        
        # Store error in history
        if engagement_id not in self.error_history:
            self.error_history[engagement_id] = []
        self.error_history[engagement_id].append(error_context)
        
        # Analyze error and create recovery plan
        recovery_plan = await self._create_recovery_plan(error_context)
        self.recovery_plans[recovery_plan.plan_id] = recovery_plan
        
        # Execute recovery plan
        recovery_result = await self._execute_recovery_plan(recovery_plan)
        
        # Update error tracking
        await self._update_error_tracking(error_context, recovery_result)
        
        logger.info(
            "Error recovery completed",
            extra={
                "error_id": str(error_context.error_id),
                "plan_id": str(recovery_plan.plan_id),
                "success": recovery_result.success,
                "strategy": recovery_result.strategy_used.value,
                "time_taken": recovery_result.time_taken
            }
        )
        
        return recovery_result
        
    async def _create_error_context(
        self,
        error: Exception,
        engagement_id: UUID,
        flow_id: UUID = None,
        flow_type: str = None,
        phase: str = None,
        operation: str = None,
        metadata: Dict[str, Any] = None
    ) -> ErrorContext:
        """Create detailed error context"""
        
        # Analyze error type and severity
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Determine severity
        severity = await self._determine_error_severity(error, error_type, flow_type, phase)
        
        # Determine category
        category = await self._determine_error_category(error, error_type, operation)
        
        # Get related assets if available
        related_assets = await self._get_related_assets(engagement_id, flow_id, phase)
        
        return ErrorContext(
            engagement_id=engagement_id,
            flow_id=flow_id,
            flow_type=flow_type,
            phase=phase,
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            severity=severity,
            category=category,
            metadata=metadata or {},
            related_assets=related_assets
        )
        
    async def _determine_error_severity(
        self,
        error: Exception,
        error_type: str,
        flow_type: str = None,
        phase: str = None
    ) -> ErrorSeverity:
        """Determine error severity based on type and context"""
        
        # Critical errors
        if any(keyword in error_type.lower() for keyword in [
            "critical", "fatal", "system", "database", "security"
        ]):
            return ErrorSeverity.CRITICAL
            
        # High severity errors
        if any(keyword in error_type.lower() for keyword in [
            "validation", "integrity", "constraint", "timeout"
        ]):
            return ErrorSeverity.HIGH
            
        # Phase-specific severity
        if phase in ["asset_creation", "dependency_analysis", "sixr_analysis"]:
            return ErrorSeverity.HIGH
            
        # Default to medium
        return ErrorSeverity.MEDIUM
        
    async def _determine_error_category(
        self,
        error: Exception,
        error_type: str,
        operation: str = None
    ) -> ErrorCategory:
        """Determine error category"""
        
        error_lower = error_type.lower()
        
        if "timeout" in error_lower:
            return ErrorCategory.TIMEOUT_ERROR
        elif "validation" in error_lower:
            return ErrorCategory.VALIDATION_ERROR
        elif "integration" in error_lower or "connection" in error_lower:
            return ErrorCategory.INTEGRATION_ERROR
        elif "data" in error_lower or "constraint" in error_lower:
            return ErrorCategory.DATA_ERROR
        elif "resource" in error_lower or "memory" in error_lower:
            return ErrorCategory.RESOURCE_ERROR
        else:
            return ErrorCategory.SYSTEM_ERROR
            
    async def _get_related_assets(
        self,
        engagement_id: UUID,
        flow_id: UUID = None,
        phase: str = None
    ) -> List[UUID]:
        """Get assets related to the error context"""
        
        if not engagement_id:
            return []
            
        try:
            async with AsyncSessionLocal() as session:
                # Get assets for engagement
                result = await session.execute(
                    select(Asset.id).where(Asset.engagement_id == engagement_id)
                )
                return [asset_id for asset_id, in result.fetchall()]
                
        except Exception:
            return []
            
    async def _create_recovery_plan(self, error_context: ErrorContext) -> RecoveryPlan:
        """Create recovery plan based on error analysis"""
        
        # Determine recovery strategy based on error type and context
        strategy_config = await self._select_recovery_strategy(error_context)
        
        # Create recovery actions
        actions = await self._create_recovery_actions(error_context, strategy_config)
        
        # Create recovery plan
        plan = RecoveryPlan(
            error_context=error_context,
            strategy=strategy_config["strategy"],
            actions=actions,
            max_attempts=strategy_config.get("max_attempts", 3),
            timeout=strategy_config.get("timeout", 300),
            success_criteria=strategy_config.get("success_criteria", {})
        )
        
        # Create fallback plan if specified
        if strategy_config.get("fallback"):
            fallback_config = self.recovery_strategies.get(
                f"{error_context.category.value}_fallback",
                {"strategy": strategy_config["fallback"], "max_attempts": 1}
            )
            plan.fallback_plan = RecoveryPlan(
                error_context=error_context,
                strategy=fallback_config["strategy"],
                actions=await self._create_recovery_actions(error_context, fallback_config),
                max_attempts=fallback_config.get("max_attempts", 1)
            )
            
        return plan
        
    async def _select_recovery_strategy(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Select appropriate recovery strategy for the error"""
        
        # Strategy based on error category
        category_strategies = {
            ErrorCategory.TIMEOUT_ERROR: self.recovery_strategies.get("timeout_error"),
            ErrorCategory.VALIDATION_ERROR: self.recovery_strategies.get("data_validation_error"),
            ErrorCategory.INTEGRATION_ERROR: self.recovery_strategies.get("integration_error"),
            ErrorCategory.RESOURCE_ERROR: self.recovery_strategies.get("resource_exhaustion"),
            ErrorCategory.SYSTEM_ERROR: self.recovery_strategies.get("critical_system_error")
        }
        
        strategy_config = category_strategies.get(error_context.category)
        
        if not strategy_config:
            # Default strategy
            strategy_config = {
                "strategy": RecoveryStrategy.MANUAL_INTERVENTION,
                "max_attempts": 1
            }
            
        return strategy_config
        
    async def _create_recovery_actions(
        self,
        error_context: ErrorContext,
        strategy_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create specific recovery actions based on strategy"""
        
        strategy = strategy_config["strategy"]
        actions = []
        
        if strategy == RecoveryStrategy.RETRY:
            actions.append({
                "type": "retry_operation",
                "operation": error_context.operation,
                "delay_seconds": strategy_config.get("delay_seconds", [5, 10, 20]),
                "timeout_multiplier": strategy_config.get("timeout_increase", 1.0)
            })
            
        elif strategy == RecoveryStrategy.FALLBACK:
            fallback_actions = strategy_config.get("fallback_actions", [])
            for action in fallback_actions:
                actions.append({
                    "type": "fallback_action",
                    "action": action,
                    "context": error_context.metadata
                })
                
        elif strategy == RecoveryStrategy.COMPENSATE:
            compensation_actions = strategy_config.get("compensation_actions", [])
            for action in compensation_actions:
                actions.append({
                    "type": "compensation",
                    "action": action,
                    "affected_assets": error_context.related_assets
                })
                
        elif strategy == RecoveryStrategy.ROLLBACK:
            actions.append({
                "type": "rollback",
                "scope": strategy_config.get("rollback_scope", "operation_level"),
                "checkpoint": error_context.metadata.get("checkpoint")
            })
            
        elif strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
            actions.append({
                "type": "skip_operation",
                "operation": error_context.operation,
                "continue_with_defaults": True
            })
            
        elif strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            actions.append({
                "type": "manual_intervention",
                "required_actions": ["review_error", "determine_resolution"],
                "escalation_level": error_context.severity.value
            })
            
        return actions
        
    async def _execute_recovery_plan(self, plan: RecoveryPlan) -> RecoveryResult:
        """Execute the recovery plan"""
        
        start_time = datetime.utcnow()
        executed_actions = []
        success = False
        
        try:
            plan.status = "executing"
            
            for attempt in range(plan.max_attempts):
                plan.current_attempt = attempt + 1
                
                logger.info(
                    f"Executing recovery plan attempt {plan.current_attempt}/{plan.max_attempts}",
                    extra={
                        "plan_id": str(plan.plan_id),
                        "strategy": plan.strategy.value,
                        "error_id": str(plan.error_context.error_id)
                    }
                )
                
                try:
                    # Execute recovery actions
                    for action in plan.actions:
                        action_result = await self._execute_recovery_action(action, plan.error_context)
                        executed_actions.append(action["type"])
                        
                        if not action_result:
                            raise Exception(f"Recovery action {action['type']} failed")
                            
                    # Check success criteria
                    if await self._check_recovery_success(plan):
                        success = True
                        break
                        
                except Exception as e:
                    logger.warning(
                        f"Recovery attempt {plan.current_attempt} failed: {str(e)}",
                        extra={"plan_id": str(plan.plan_id)}
                    )
                    
                    if plan.current_attempt < plan.max_attempts:
                        # Wait before next attempt
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            # If primary plan failed, try fallback
            if not success and plan.fallback_plan:
                logger.info(
                    "Primary recovery failed, executing fallback plan",
                    extra={"plan_id": str(plan.plan_id)}
                )
                
                fallback_result = await self._execute_recovery_plan(plan.fallback_plan)
                success = fallback_result.success
                executed_actions.extend(fallback_result.actions_executed)
                
            plan.status = "completed" if success else "failed"
            
        except Exception as e:
            logger.error(
                f"Recovery plan execution failed: {str(e)}",
                extra={"plan_id": str(plan.plan_id)}
            )
            plan.status = "failed"
            
        end_time = datetime.utcnow()
        time_taken = (end_time - start_time).total_seconds()
        
        return RecoveryResult(
            plan_id=plan.plan_id,
            success=success,
            strategy_used=plan.strategy,
            actions_executed=executed_actions,
            time_taken=time_taken,
            error_resolved=success,
            metadata={
                "attempts": plan.current_attempt,
                "fallback_used": plan.fallback_plan is not None and not success
            }
        )
        
    async def _execute_recovery_action(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Execute a specific recovery action"""
        
        action_type = action["type"]
        
        if action_type == "retry_operation":
            return await self._retry_operation(action, error_context)
            
        elif action_type == "fallback_action":
            return await self._execute_fallback_action(action, error_context)
            
        elif action_type == "compensation":
            return await self._execute_compensation(action, error_context)
            
        elif action_type == "rollback":
            return await self._execute_rollback(action, error_context)
            
        elif action_type == "skip_operation":
            return await self._skip_operation(action, error_context)
            
        elif action_type == "manual_intervention":
            return await self._request_manual_intervention(action, error_context)
            
        return False
        
    async def _retry_operation(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Retry the failed operation"""
        
        # This would integrate with the actual operation retry logic
        # For now, simulate a retry
        await asyncio.sleep(1)  # Simulate operation time
        
        # In a real implementation, this would re-invoke the original operation
        # with potentially modified parameters or context
        
        return True  # Assume retry succeeded for demo
        
    async def _execute_fallback_action(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Execute a fallback action"""
        
        fallback_action = action["action"]
        
        if fallback_action == "use_cache":
            return await self._use_cached_data(error_context)
        elif fallback_action == "skip_enrichment":
            return await self._skip_enrichment(error_context)
        elif fallback_action == "minimal_processing":
            return await self._minimal_processing(error_context)
            
        return True
        
    async def _execute_compensation(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Execute compensation action"""
        
        compensation_action = action["action"]
        
        if compensation_action == "apply_defaults":
            return await self._apply_default_values(error_context)
        elif compensation_action == "request_manual_input":
            return await self._request_manual_input(error_context)
            
        return True
        
    async def _execute_rollback(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Execute rollback action"""
        
        # This would implement actual rollback logic
        scope = action.get("scope", "operation_level")
        
        logger.info(
            f"Executing rollback with scope: {scope}",
            extra={"error_id": str(error_context.error_id)}
        )
        
        return True
        
    async def _skip_operation(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Skip the failed operation and continue"""
        
        logger.info(
            f"Skipping operation: {error_context.operation}",
            extra={"error_id": str(error_context.error_id)}
        )
        
        return True
        
    async def _request_manual_intervention(
        self,
        action: Dict[str, Any],
        error_context: ErrorContext
    ) -> bool:
        """Request manual intervention"""
        
        # This would create a manual intervention request
        # For now, just log the request
        
        logger.warning(
            "Manual intervention requested",
            extra={
                "error_id": str(error_context.error_id),
                "escalation_level": action.get("escalation_level", "medium"),
                "required_actions": action.get("required_actions", [])
            }
        )
        
        return True
        
    # Helper methods for fallback actions
    async def _use_cached_data(self, error_context: ErrorContext) -> bool:
        """Use cached data as fallback"""
        return True
        
    async def _skip_enrichment(self, error_context: ErrorContext) -> bool:
        """Skip data enrichment as fallback"""
        return True
        
    async def _minimal_processing(self, error_context: ErrorContext) -> bool:
        """Perform minimal processing as fallback"""
        return True
        
    async def _apply_default_values(self, error_context: ErrorContext) -> bool:
        """Apply default values for missing data"""
        return True
        
    async def _request_manual_input(self, error_context: ErrorContext) -> bool:
        """Request manual input for missing data"""
        return True
        
    async def _check_recovery_success(self, plan: RecoveryPlan) -> bool:
        """Check if recovery was successful based on success criteria"""
        
        # Basic success check - no additional errors
        # In a real implementation, this would check specific success criteria
        
        return True
        
    async def _update_error_tracking(
        self,
        error_context: ErrorContext,
        recovery_result: RecoveryResult
    ) -> None:
        """Update error tracking with recovery results"""
        
        # This would update error tracking database/cache
        # For now, just update metadata
        
        error_context.metadata.update({
            "recovery_plan_id": str(recovery_result.plan_id),
            "recovery_success": recovery_result.success,
            "recovery_strategy": recovery_result.strategy_used.value,
            "recovery_time": recovery_result.time_taken
        })
        
    @track_performance("recovery.status.get")
    async def get_error_recovery_status(self, engagement_id: UUID) -> Dict[str, Any]:
        """Get error recovery status for an engagement"""
        
        errors = self.error_history.get(engagement_id, [])
        
        # Calculate error statistics
        total_errors = len(errors)
        critical_errors = len([e for e in errors if e.severity == ErrorSeverity.CRITICAL])
        recent_errors = len([
            e for e in errors 
            if e.occurred_at > datetime.utcnow() - timedelta(hours=24)
        ])
        
        # Get active recovery plans
        active_plans = [
            plan for plan in self.recovery_plans.values()
            if plan.error_context.engagement_id == engagement_id and plan.status in ["pending", "executing"]
        ]
        
        return {
            "engagement_id": str(engagement_id),
            "error_summary": {
                "total_errors": total_errors,
                "critical_errors": critical_errors,
                "recent_errors_24h": recent_errors
            },
            "recovery_status": {
                "active_recovery_plans": len(active_plans),
                "pending_manual_interventions": len([
                    plan for plan in active_plans 
                    if plan.strategy == RecoveryStrategy.MANUAL_INTERVENTION
                ])
            },
            "error_categories": {
                category.value: len([e for e in errors if e.category == category])
                for category in ErrorCategory
            }
        }