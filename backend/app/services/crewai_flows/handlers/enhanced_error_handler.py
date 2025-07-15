"""
Enhanced Error Handler for Discovery Flow
Integrates retry logic, error classification, and recovery strategies
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import traceback

from ..utils.retry_utils import (
    RetryConfig, 
    classify_error, 
    ErrorCategory,
    retry_with_backoff,
    retry_metrics
)
from ..persistence.checkpoint_manager import checkpoint_manager
from ..monitoring.flow_health_monitor import flow_health_monitor

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Recovery strategies for different error scenarios"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    CHECKPOINT_RESTORE = "checkpoint_restore"
    SKIP_PHASE = "skip_phase"
    PARTIAL_RESULT = "partial_result"
    FAIL_FAST = "fail_fast"


class EnhancedErrorHandler:
    """
    Enhanced error handling with retry logic and recovery strategies
    """
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.phase_retry_configs = {
            "data_import_validation": RetryConfig(max_retries=3, base_delay=2.0),
            "field_mapping": RetryConfig(max_retries=5, base_delay=3.0, max_delay=120.0),
            "data_cleansing": RetryConfig(max_retries=3, base_delay=1.0),
            "asset_inventory": RetryConfig(max_retries=3, base_delay=2.0),
            "dependency_analysis": RetryConfig(max_retries=4, base_delay=2.0),
            "tech_debt_assessment": RetryConfig(max_retries=3, base_delay=1.5)
        }
    
    async def handle_phase_error(
        self,
        phase_name: str,
        error: Exception,
        state: Any,
        phase_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle error during phase execution with retry and recovery
        
        Args:
            phase_name: Name of the phase that failed
            error: The exception that occurred
            state: Current flow state
            phase_func: The phase function to retry
            *args, **kwargs: Arguments for the phase function
            
        Returns:
            Recovery result with status and data
        """
        try:
            # Log error
            error_info = self._log_error(phase_name, error, state)
            
            # Classify error
            error_category = classify_error(error)
            
            # Determine recovery strategy
            strategy = self._determine_recovery_strategy(
                phase_name,
                error,
                error_category,
                state
            )
            
            # Execute recovery strategy
            result = await self._execute_recovery_strategy(
                strategy,
                phase_name,
                error,
                state,
                phase_func,
                *args,
                **kwargs
            )
            
            # Update metrics
            self._update_error_metrics(phase_name, error, strategy, result)
            
            return result
            
        except Exception as recovery_error:
            logger.error(f"Recovery failed for {phase_name}: {recovery_error}")
            return {
                "status": "recovery_failed",
                "error": str(recovery_error),
                "original_error": str(error),
                "phase": phase_name
            }
    
    def _log_error(self, phase_name: str, error: Exception, state: Any) -> Dict[str, Any]:
        """Log error details"""
        error_info = {
            "phase": phase_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "flow_id": getattr(state, 'flow_id', None),
            "progress": getattr(state, 'progress_percentage', 0),
            "traceback": traceback.format_exc()
        }
        
        self.error_history.append(error_info)
        
        # Log to file
        logger.error(f"❌ Error in phase '{phase_name}': {error}")
        logger.debug(f"Error details: {error_info}")
        
        # Update state errors
        if hasattr(state, 'errors'):
            state.errors.append(error_info)
        
        return error_info
    
    def _determine_recovery_strategy(
        self,
        phase_name: str,
        error: Exception,
        error_category: ErrorCategory,
        state: Any
    ) -> RecoveryStrategy:
        """Determine the best recovery strategy"""
        
        # Check retry attempts
        retry_key = f"{getattr(state, 'flow_id', 'unknown')}_{phase_name}"
        retry_count = self.recovery_attempts.get(retry_key, 0)
        
        # Permanent errors - fail fast
        if error_category == ErrorCategory.PERMANENT:
            return RecoveryStrategy.FAIL_FAST
        
        # Check if we have checkpoints available
        has_checkpoint = hasattr(state, 'flow_id') and phase_name in [
            "field_mapping", "data_cleansing", "asset_inventory"
        ]
        
        # Transient errors - retry with backoff
        if error_category == ErrorCategory.TRANSIENT and retry_count < 3:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        # Resource errors - try checkpoint restore if available
        if error_category == ErrorCategory.RESOURCE and has_checkpoint and retry_count < 2:
            return RecoveryStrategy.CHECKPOINT_RESTORE
        
        # Phase-specific strategies
        if phase_name in ["dependency_analysis", "tech_debt_assessment"]:
            # These phases can provide partial results
            return RecoveryStrategy.PARTIAL_RESULT
        elif phase_name == "field_mapping" and retry_count > 2:
            # Skip to manual mapping after multiple failures
            return RecoveryStrategy.SKIP_PHASE
        
        # Default: retry with backoff if retries available
        max_retries = self.phase_retry_configs.get(phase_name, RetryConfig()).max_retries
        if retry_count < max_retries:
            return RecoveryStrategy.RETRY_WITH_BACKOFF
        
        return RecoveryStrategy.FAIL_FAST
    
    async def _execute_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        phase_name: str,
        error: Exception,
        state: Any,
        phase_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the chosen recovery strategy"""
        
        retry_key = f"{getattr(state, 'flow_id', 'unknown')}_{phase_name}"
        
        if strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            logger.info(f"🔄 Retrying {phase_name} with backoff...")
            
            # Update retry count
            self.recovery_attempts[retry_key] = self.recovery_attempts.get(retry_key, 0) + 1
            
            # Get retry config for phase
            retry_config = self.phase_retry_configs.get(phase_name, RetryConfig())
            
            try:
                # Retry with backoff
                result = await retry_with_backoff(
                    phase_func,
                    *args,
                    config=retry_config,
                    **kwargs
                )
                
                logger.info(f"✅ Retry successful for {phase_name}")
                return {
                    "status": "recovered",
                    "recovery_method": "retry_with_backoff",
                    "result": result
                }
                
            except Exception as retry_error:
                logger.error(f"Retry failed for {phase_name}: {retry_error}")
                # Fall through to fail fast
                
        elif strategy == RecoveryStrategy.CHECKPOINT_RESTORE:
            logger.info(f"🔄 Attempting checkpoint restore for {phase_name}...")
            
            # Try to restore from checkpoint
            checkpoint = await checkpoint_manager.get_latest_checkpoint(
                state.flow_id,
                phase_name
            )
            
            if checkpoint:
                # Restore state
                restored_state = checkpoint['state']
                
                # Copy restored attributes to current state
                for attr in ['raw_data', 'field_mappings', 'cleaned_data']:
                    if hasattr(restored_state, attr):
                        setattr(state, attr, getattr(restored_state, attr))
                
                logger.info(f"✅ Restored from checkpoint: {checkpoint['phase']}")
                
                # Retry with restored state
                self.recovery_attempts[retry_key] = self.recovery_attempts.get(retry_key, 0) + 1
                
                try:
                    result = await phase_func(*args, **kwargs)
                    return {
                        "status": "recovered",
                        "recovery_method": "checkpoint_restore",
                        "checkpoint_id": checkpoint.get('checkpoint_id'),
                        "result": result
                    }
                except Exception as restore_error:
                    logger.error(f"Checkpoint restore failed: {restore_error}")
                    
        elif strategy == RecoveryStrategy.SKIP_PHASE:
            logger.warning(f"⏭️ Skipping phase {phase_name} due to errors")
            
            # Mark phase as skipped
            if hasattr(state, 'phase_completion'):
                state.phase_completion[phase_name] = False
            
            # Add skip notification
            if hasattr(state, 'agent_insights'):
                state.agent_insights.append({
                    "agent": "Error Handler",
                    "insight": f"Phase {phase_name} was skipped due to errors. Manual intervention may be required.",
                    "confidence": 0.9,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return {
                "status": "skipped",
                "recovery_method": "skip_phase",
                "reason": str(error),
                "manual_intervention_required": True
            }
            
        elif strategy == RecoveryStrategy.PARTIAL_RESULT:
            logger.warning(f"⚠️ Returning partial result for {phase_name}")
            
            # Create partial result based on phase
            partial_result = self._create_partial_result(phase_name, state)
            
            return {
                "status": "partial_success",
                "recovery_method": "partial_result",
                "result": partial_result,
                "completeness": 0.5  # 50% complete
            }
            
        # Default: FAIL_FAST
        logger.error(f"❌ Failing fast for {phase_name} - no recovery possible")
        
        return {
            "status": "failed",
            "recovery_method": "fail_fast",
            "error": str(error),
            "error_type": type(error).__name__,
            "phase": phase_name
        }
    
    def _create_partial_result(self, phase_name: str, state: Any) -> Dict[str, Any]:
        """Create partial result for a phase"""
        
        if phase_name == "dependency_analysis":
            return {
                "dependencies": {
                    "app_server": {"hosting_relationships": []},
                    "app_app": {"communication_patterns": []}
                },
                "analysis_complete": False,
                "partial_result": True
            }
        elif phase_name == "tech_debt_assessment":
            return {
                "assessment": {
                    "debt_scores": {},
                    "modernization_recommendations": [],
                    "six_r_preparation": {"ready": False}
                },
                "assessment_complete": False,
                "partial_result": True
            }
        else:
            return {
                "data": [],
                "complete": False,
                "partial_result": True
            }
    
    def _update_error_metrics(
        self,
        phase_name: str,
        error: Exception,
        strategy: RecoveryStrategy,
        result: Dict[str, Any]
    ):
        """Update error and recovery metrics"""
        
        # Record in retry metrics
        success = result.get("status") in ["recovered", "partial_success", "skipped"]
        retry_metrics.record_call(
            f"{phase_name}_recovery",
            success,
            self.recovery_attempts.get(f"{phase_name}_recovery", 0),
            str(error) if not success else None
        )
        
        # Log recovery outcome
        logger.info(
            f"📊 Recovery outcome - Phase: {phase_name}, "
            f"Strategy: {strategy.value}, "
            f"Status: {result.get('status')}"
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary"""
        
        # Group errors by phase
        errors_by_phase = {}
        for error in self.error_history:
            phase = error.get("phase", "unknown")
            if phase not in errors_by_phase:
                errors_by_phase[phase] = []
            errors_by_phase[phase].append(error)
        
        # Calculate recovery success rate
        total_recoveries = sum(self.recovery_attempts.values())
        successful_recoveries = len([
            e for e in self.error_history
            if "recovered" in str(e.get("resolution", ""))
        ])
        
        recovery_rate = (
            successful_recoveries / total_recoveries
            if total_recoveries > 0
            else 0
        )
        
        return {
            "total_errors": len(self.error_history),
            "errors_by_phase": {
                phase: len(errors)
                for phase, errors in errors_by_phase.items()
            },
            "recovery_attempts": self.recovery_attempts,
            "recovery_success_rate": recovery_rate,
            "recent_errors": self.error_history[-5:],
            "retry_metrics": retry_metrics.get_summary()
        }
    
    async def handle_critical_flow_error(
        self,
        flow_id: str,
        error: Exception,
        state: Any
    ) -> Dict[str, Any]:
        """
        Handle critical flow-level errors that affect the entire flow
        """
        logger.error(f"🚨 Critical flow error for {flow_id}: {error}")
        
        # Update flow health monitor
        await flow_health_monitor._log_health_event(
            flow_id,
            "critical_error",
            {
                "error": str(error),
                "error_type": type(error).__name__,
                "phase": getattr(state, 'current_phase', 'unknown'),
                "traceback": traceback.format_exc()
            }
        )
        
        # Try to save current state as checkpoint
        try:
            checkpoint_id = await checkpoint_manager.create_checkpoint(
                flow_id=flow_id,
                phase=f"error_{getattr(state, 'current_phase', 'unknown')}",
                state=state,
                metadata={
                    "error": str(error),
                    "critical": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"💾 Saved error checkpoint: {checkpoint_id}")
        except Exception as cp_error:
            logger.error(f"Failed to save error checkpoint: {cp_error}")
        
        # Determine if flow can be recovered
        error_category = classify_error(error)
        can_recover = error_category != ErrorCategory.PERMANENT
        
        return {
            "status": "critical_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "can_recover": can_recover,
            "recovery_options": [
                "restart_from_checkpoint",
                "restart_flow",
                "manual_intervention"
            ] if can_recover else ["manual_intervention"],
            "flow_id": flow_id
        }


# Global instance
enhanced_error_handler = EnhancedErrorHandler()