"""
Core agent service layer providing synchronous access to backend services.
"""

import asyncio
import concurrent.futures
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


from app.core.context import RequestContext

from ..handlers.asset_handler import AssetHandler
from ..handlers.data_handler import DataHandler
from ..handlers.flow_handler import FlowHandler
from ..metrics.performance_tracker import PerformanceTracker
from ..validators.service_validator import ServiceValidator

logger = logging.getLogger(__name__)


class AgentServiceLayer:
    """
    Main synchronous service layer for AI agents.
    Provides clean, direct access to backend services without HTTP/auth complexity.
    """
    
    def __init__(self, client_account_id: str, engagement_id: str, user_id: Optional[str] = None):
        """Initialize with multi-tenant context"""
        self.context = RequestContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            session_id=None
        )
        
        # Initialize thread executor for async-to-sync conversion
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Initialize components
        self.flow_handler = FlowHandler(self.context)
        self.data_handler = DataHandler(self.context)
        self.asset_handler = AssetHandler(self.context)
        self.validator = ServiceValidator(self.context)
        self.performance_tracker = PerformanceTracker()
    
    # Flow Management Methods
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status - synchronous wrapper for agents"""
        return self._execute_with_tracking(
            "get_flow_status",
            self.flow_handler.get_flow_status,
            flow_id
        )
    
    def get_navigation_guidance(self, flow_id: str, current_phase: str) -> Dict[str, Any]:
        """Get navigation guidance for a flow"""
        return self._execute_with_tracking(
            "get_navigation_guidance",
            self.flow_handler.get_navigation_guidance,
            flow_id,
            current_phase
        )
    
    def validate_phase_completion(self, flow_id: str, phase: str) -> Dict[str, Any]:
        """Validate if a phase is properly completed"""
        return self._execute_with_tracking(
            "validate_phase_completion",
            self.flow_handler.validate_phase_completion,
            flow_id,
            phase
        )
    
    def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active discovery flows"""
        return self._execute_with_tracking(
            "get_active_flows",
            self.flow_handler.get_active_flows
        )
    
    def validate_phase_transition(self, flow_id: str, from_phase: str, to_phase: str) -> Dict[str, Any]:
        """Validate if phase transition is allowed"""
        return self._execute_with_tracking(
            "validate_phase_transition",
            self.flow_handler.validate_phase_transition,
            flow_id,
            from_phase,
            to_phase
        )
    
    # Data Management Methods
    
    def get_import_data(self, flow_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get imported data for a flow"""
        return self._execute_with_tracking(
            "get_import_data",
            self.data_handler.get_import_data,
            flow_id,
            limit
        )
    
    def get_field_mappings(self, flow_id: str) -> Dict[str, Any]:
        """Get field mappings for a flow"""
        return self._execute_with_tracking(
            "get_field_mappings",
            self.data_handler.get_field_mappings,
            flow_id
        )
    
    def validate_mappings(self, flow_id: str, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate field mappings"""
        return self._execute_with_tracking(
            "validate_mappings",
            self.data_handler.validate_mappings,
            flow_id,
            mappings
        )
    
    def get_cleansing_results(self, flow_id: str) -> Dict[str, Any]:
        """Get data cleansing results"""
        return self._execute_with_tracking(
            "get_cleansing_results",
            self.data_handler.get_cleansing_results,
            flow_id
        )
    
    def get_validation_issues(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get validation issues for a flow"""
        return self._execute_with_tracking(
            "get_validation_issues",
            self.data_handler.get_validation_issues,
            flow_id
        )
    
    # Asset Management Methods
    
    def get_discovered_assets(self, flow_id: str, asset_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get discovered assets for a flow"""
        return self._execute_with_tracking(
            "get_discovered_assets",
            self.asset_handler.get_discovered_assets,
            flow_id,
            asset_type
        )
    
    def get_asset_dependencies(self, flow_id: str) -> Dict[str, Any]:
        """Get asset dependencies for a flow"""
        return self._execute_with_tracking(
            "get_asset_dependencies",
            self.asset_handler.get_asset_dependencies,
            flow_id
        )
    
    def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get technical debt analysis for a flow"""
        return self._execute_with_tracking(
            "get_tech_debt_analysis",
            self.asset_handler.get_tech_debt_analysis,
            flow_id
        )
    
    def validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        return self._execute_with_tracking(
            "validate_asset_data",
            self.asset_handler.validate_asset_data,
            asset_id
        )
    
    def get_asset_relationships(self, asset_id: str) -> Dict[str, Any]:
        """Get relationships for a specific asset"""
        return self._execute_with_tracking(
            "get_asset_relationships",
            self.asset_handler.get_asset_relationships,
            asset_id
        )
    
    # Performance and Metrics
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service layer performance metrics"""
        return self.performance_tracker.get_metrics(self.context)
    
    # Core Execution Infrastructure
    
    def _execute_with_tracking(self, method_name: str, async_method, *args, **kwargs) -> Any:
        """Execute async method with performance tracking and error handling"""
        start_time = time.time()
        
        try:
            # Execute async method in thread executor
            future = self.executor.submit(
                asyncio.run,
                async_method(*args, **kwargs)
            )
            result = future.result(timeout=30)
            
            # Track successful call
            duration = time.time() - start_time
            self.performance_tracker.log_call(method_name, duration, True)
            return result
            
        except concurrent.futures.TimeoutError:
            duration = time.time() - start_time
            error_msg = "Service call timed out after 30 seconds"
            self.performance_tracker.log_call(method_name, duration, False, error_msg)
            return self._handle_service_error(method_name, Exception(error_msg))
            
        except Exception as e:
            duration = time.time() - start_time
            self.performance_tracker.log_call(method_name, duration, False, str(e))
            return self._handle_service_error(method_name, e)
    
    def _handle_service_error(self, method_name: str, error: Exception) -> Dict[str, Any]:
        """Standardized error handling"""
        error_msg = str(error)
        error_type = "system"
        
        # Categorize errors
        if "not found" in error_msg.lower():
            error_type = "not_found"
        elif "permission" in error_msg.lower() or "access" in error_msg.lower():
            error_type = "permission"
        elif "validation" in error_msg.lower():
            error_type = "validation"
        
        return {
            "status": "error",
            "error": error_msg,
            "error_type": error_type,
            "method": method_name,
            "timestamp": datetime.utcnow().isoformat(),
            "guidance": self._get_error_guidance(error_type)
        }
    
    def _get_error_guidance(self, error_type: str) -> str:
        """Get user guidance based on error type"""
        guidance_map = {
            "not_found": "Resource not found. Please check the ID and try again.",
            "permission": "Access denied. Please verify your permissions.",
            "validation": "Invalid data provided. Please check your input.",
            "system": "System error occurred. Please try again or contact support."
        }
        return guidance_map.get(error_type, "An error occurred. Please try again.")
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)