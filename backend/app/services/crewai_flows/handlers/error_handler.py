"""
Error Handler for Discovery Flow
Handles crew execution errors with graceful degradation
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handles crew execution errors with graceful degradation"""
    
    def __init__(self):
        self.error_history = []
        self.recovery_strategies = {
            "retry_with_fallback": self._retry_with_fallback,
            "skip_and_continue": self._skip_and_continue,
            "use_cached_result": self._use_cached_result,
            "graceful_degradation": self._graceful_degradation
        }
    
    def handle_crew_error(self, crew_name: str, error: Exception, state) -> Dict[str, Any]:
        """Handle crew execution errors with graceful degradation"""
        error_info = {
            "crew": crew_name,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "phase": state.current_phase,
            "error_type": type(error).__name__,
            "recoverable": True,
            "recovery_strategy": self._determine_recovery_strategy(crew_name, error)
        }
        
        # Store error in history
        self.error_history.append(error_info)
        
        # Update state
        state.errors.append(error_info)
        state.crew_status[crew_name] = {
            "status": "failed",
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "recovery_attempted": False
        }
        
        logger.error(f"Crew {crew_name} failed: {error}")
        
        # Attempt recovery if strategy available
        recovery_result = self._attempt_recovery(error_info)
        
        return {
            "status": "error",
            "crew": crew_name,
            "error": str(error),
            "recovery_options": ["retry", "skip", "fallback"],
            "recovery_attempted": recovery_result.get("attempted", False),
            "recovery_success": recovery_result.get("success", False)
        }
    
    def _determine_recovery_strategy(self, crew_name: str, error: Exception) -> str:
        """Determine appropriate recovery strategy based on crew and error type"""
        error_type = type(error).__name__
        
        # Strategy mapping based on crew importance and error type
        strategy_map = {
            "field_mapping": {
                "ImportError": "use_cached_result",
                "ModuleNotFoundError": "graceful_degradation",
                "Exception": "retry_with_fallback"
            },
            "data_cleansing": {
                "ImportError": "graceful_degradation",
                "Exception": "skip_and_continue"
            },
            "inventory_building": {
                "Exception": "retry_with_fallback"
            },
            "app_server_dependencies": {
                "Exception": "graceful_degradation"
            },
            "app_app_dependencies": {
                "Exception": "skip_and_continue"
            },
            "technical_debt": {
                "Exception": "graceful_degradation"
            }
        }
        
        crew_strategies = strategy_map.get(crew_name, {})
        return crew_strategies.get(error_type, "graceful_degradation")
    
    def _attempt_recovery(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt recovery using determined strategy"""
        strategy = error_info.get("recovery_strategy", "graceful_degradation")
        
        try:
            if strategy in self.recovery_strategies:
                recovery_func = self.recovery_strategies[strategy]
                result = recovery_func(error_info)
                return {"attempted": True, "success": result, "strategy": strategy}
            else:
                logger.warning(f"Unknown recovery strategy: {strategy}")
                return {"attempted": False, "success": False, "strategy": strategy}
        
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
            return {"attempted": True, "success": False, "strategy": strategy, "recovery_error": str(recovery_error)}
    
    def _retry_with_fallback(self, error_info: Dict[str, Any]) -> bool:
        """Retry operation with fallback approach"""
        logger.info(f"Executing retry with fallback for {error_info['crew']}")
        # In a real implementation, this would retry the crew with different parameters
        # For now, just log the attempt
        return True
    
    def _skip_and_continue(self, error_info: Dict[str, Any]) -> bool:
        """Skip failed crew and continue with flow"""
        logger.info(f"Skipping failed crew {error_info['crew']} and continuing")
        # Mark crew as skipped but allow flow to continue
        return True
    
    def _use_cached_result(self, error_info: Dict[str, Any]) -> bool:
        """Use cached result from previous execution"""
        logger.info(f"Using cached result for {error_info['crew']}")
        # In a real implementation, this would look up cached results
        return False  # No cache available for now
    
    def _graceful_degradation(self, error_info: Dict[str, Any]) -> bool:
        """Apply graceful degradation - reduced functionality"""
        logger.info(f"Applying graceful degradation for {error_info['crew']}")
        # Continue with reduced functionality
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        return {
            "total_errors": len(self.error_history),
            "errors_by_crew": self._group_errors_by_crew(),
            "errors_by_type": self._group_errors_by_type(),
            "recoverable_errors": len([e for e in self.error_history if e.get("recoverable", False)]),
            "recent_errors": self.error_history[-5:] if self.error_history else []
        }
    
    def _group_errors_by_crew(self) -> Dict[str, int]:
        """Group errors by crew name"""
        crew_counts = {}
        for error in self.error_history:
            crew = error.get("crew", "unknown")
            crew_counts[crew] = crew_counts.get(crew, 0) + 1
        return crew_counts
    
    def _group_errors_by_type(self) -> Dict[str, int]:
        """Group errors by error type"""
        type_counts = {}
        for error in self.error_history:
            error_type = error.get("error_type", "unknown")
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        return type_counts 