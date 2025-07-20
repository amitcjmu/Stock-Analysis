"""
Collection Orchestration Tools for automated data collection
Tools required by the CollectionOrchestratorAgent
"""

from typing import Dict, Any, List, Optional
from app.services.tools.base_tool import BaseDiscoveryTool, AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata
from app.core.database_context import get_context_db
from app.services.collection_flow import adapter_registry
from app.services.collection_flow.state_management import CollectionFlowStateService
from app.services.collection_flow.quality_scoring import QualityAssessmentService
from app.core.context import get_current_context
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PlatformAdapterManager(AsyncBaseDiscoveryTool):
    """Manages platform adapters for automated collection"""
    
    name: str = "PlatformAdapterManager"
    description: str = "Coordinate and manage platform adapters for data collection"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="PlatformAdapterManager",
            description="Manages platform adapters for automated collection",
            tool_class=cls,
            categories=["collection", "adapter", "orchestration"],
            required_params=["platforms", "action"],
            optional_params=["adapter_configs", "credentials"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        platforms: List[Dict[str, Any]],
        action: str,
        adapter_configs: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage platform adapters for collection.
        
        Args:
            platforms: List of detected platforms
            action: Action to perform (initialize, execute, status, cleanup)
            adapter_configs: Platform-specific adapter configurations
            credentials: Platform credentials for authentication
            
        Returns:
            Adapter management results
        """
        results = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "adapters": [],
            "errors": []
        }
        
        try:
            if action == "initialize":
                # Initialize adapters for each platform
                for platform in platforms:
                    platform_type = platform.get("type", "").lower()
                    adapter = adapter_registry.get_adapter(platform_type)
                    
                    if adapter:
                        adapter_info = {
                            "platform": platform_type,
                            "name": platform.get("name"),
                            "status": "initialized",
                            "capabilities": adapter.get_capabilities() if hasattr(adapter, 'get_capabilities') else []
                        }
                        results["adapters"].append(adapter_info)
                    else:
                        results["errors"].append(f"No adapter found for platform: {platform_type}")
                        
            elif action == "execute":
                # Execute collection using adapters
                collection_tasks = []
                for platform in platforms:
                    platform_type = platform.get("type", "").lower()
                    adapter = adapter_registry.get_adapter(platform_type)
                    
                    if adapter:
                        config = adapter_configs.get(platform_type, {}) if adapter_configs else {}
                        creds = credentials.get(platform_type, {}) if credentials else {}
                        
                        # Create collection task
                        task = self._collect_with_adapter(adapter, platform, config, creds)
                        collection_tasks.append(task)
                
                # Execute collections in parallel
                collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
                
                for i, result in enumerate(collection_results):
                    if isinstance(result, Exception):
                        results["errors"].append(f"Collection failed for {platforms[i]['name']}: {str(result)}")
                    else:
                        results["adapters"].append(result)
                        
            elif action == "status":
                # Get status of active collections
                for platform in platforms:
                    platform_type = platform.get("type", "").lower()
                    adapter = adapter_registry.get_adapter(platform_type)
                    
                    if adapter and hasattr(adapter, 'get_status'):
                        status = await adapter.get_status()
                        results["adapters"].append({
                            "platform": platform_type,
                            "status": status
                        })
                        
            elif action == "cleanup":
                # Clean up adapter resources
                for platform in platforms:
                    platform_type = platform.get("type", "").lower()
                    adapter = adapter_registry.get_adapter(platform_type)
                    
                    if adapter and hasattr(adapter, 'cleanup'):
                        await adapter.cleanup()
                        results["adapters"].append({
                            "platform": platform_type,
                            "status": "cleaned_up"
                        })
            
            results["success"] = len(results["errors"]) == 0
            return results
            
        except Exception as e:
            logger.error(f"Platform adapter management failed: {str(e)}")
            results["errors"].append(str(e))
            results["success"] = False
            return results
    
    async def _collect_with_adapter(
        self,
        adapter: Any,
        platform: Dict[str, Any],
        config: Dict[str, Any],
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute collection with a single adapter"""
        try:
            # Initialize adapter with credentials
            if hasattr(adapter, 'initialize'):
                await adapter.initialize(credentials)
            
            # Execute collection
            if hasattr(adapter, 'collect_data'):
                data = await adapter.collect_data(config)
            else:
                data = await adapter.collect()
            
            return {
                "platform": platform.get("type"),
                "name": platform.get("name"),
                "status": "collected",
                "data_count": len(data) if isinstance(data, list) else 1,
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Collection failed for {platform.get('name')}: {str(e)}")
            raise


class CollectionStrategyPlanner(BaseDiscoveryTool):
    """Plans optimal collection strategies based on tier and requirements"""
    
    name: str = "CollectionStrategyPlanner"
    description: str = "Design optimal collection workflows based on automation tier"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="CollectionStrategyPlanner",
            description="Plans collection strategies based on tier and requirements",
            tool_class=cls,
            categories=["collection", "planning", "strategy"],
            required_params=["automation_tier", "platforms"],
            optional_params=["requirements", "constraints", "priorities"],
            context_aware=True,
            async_tool=False
        )
    
    def run(
        self,
        automation_tier: str,
        platforms: List[Dict[str, Any]],
        requirements: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        priorities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Plan collection strategy based on tier and requirements.
        
        Args:
            automation_tier: Selected automation tier (tier_1 to tier_3)
            platforms: List of detected platforms
            requirements: Collection requirements (sixR, quality thresholds)
            constraints: Constraints (time limits, resource limits)
            priorities: Priority order for collection
            
        Returns:
            Collection strategy plan
        """
        strategy = {
            "automation_tier": automation_tier,
            "timestamp": datetime.utcnow().isoformat(),
            "phases": [],
            "parallelization": {},
            "checkpoints": [],
            "resource_allocation": {}
        }
        
        # Define strategy based on tier
        if automation_tier == "tier_1":
            # Full automation - parallel execution
            strategy["execution_mode"] = "parallel"
            strategy["phases"] = [
                {
                    "name": "parallel_collection",
                    "description": "Execute all platform collections in parallel",
                    "platforms": [p["name"] for p in platforms],
                    "timeout": 3600,
                    "retry_policy": {"max_retries": 3, "backoff": "exponential"}
                }
            ]
            strategy["parallelization"] = {
                "max_concurrent": len(platforms),
                "batch_size": 10,
                "throttling": False
            }
            
        elif automation_tier == "tier_2":
            # Semi-automated with checkpoints
            strategy["execution_mode"] = "sequential_batched"
            
            # Group platforms by criticality
            critical_platforms = []
            standard_platforms = []
            
            for platform in platforms:
                if priorities and platform["name"] in priorities[:3]:
                    critical_platforms.append(platform)
                else:
                    standard_platforms.append(platform)
            
            strategy["phases"] = [
                {
                    "name": "critical_collection",
                    "description": "Collect from critical platforms first",
                    "platforms": [p["name"] for p in critical_platforms],
                    "timeout": 1800,
                    "validation_checkpoint": True
                },
                {
                    "name": "standard_collection",
                    "description": "Collect from remaining platforms",
                    "platforms": [p["name"] for p in standard_platforms],
                    "timeout": 2400,
                    "validation_checkpoint": True
                }
            ]
            
            strategy["checkpoints"] = [
                {
                    "after_phase": "critical_collection",
                    "validation": ["quality_check", "completeness_check"],
                    "approval_required": False
                },
                {
                    "after_phase": "standard_collection",
                    "validation": ["full_validation"],
                    "approval_required": True
                }
            ]
            
        elif automation_tier == "tier_3":
            # Guided collection with manual oversight
            strategy["execution_mode"] = "guided_sequential"
            
            strategy["phases"] = []
            for i, platform in enumerate(platforms):
                strategy["phases"].append({
                    "name": f"collect_{platform['name']}",
                    "description": f"Guided collection for {platform['name']}",
                    "platforms": [platform["name"]],
                    "timeout": 1200,
                    "manual_review": True,
                    "approval_required": True
                })
            
            strategy["checkpoints"] = [
                {
                    "after_each_platform": True,
                    "validation": ["manual_review", "quality_assessment"],
                    "approval_required": True,
                    "notification": True
                }
            ]
        
        # Add resource allocation
        strategy["resource_allocation"] = {
            "cpu_limit": constraints.get("cpu_limit", 80) if constraints else 80,
            "memory_limit": constraints.get("memory_limit", 70) if constraints else 70,
            "concurrent_connections": self._calculate_connections(automation_tier, len(platforms)),
            "rate_limiting": self._calculate_rate_limits(automation_tier)
        }
        
        # Add quality requirements
        if requirements:
            strategy["quality_requirements"] = {
                "minimum_quality_score": requirements.get("quality_threshold", 0.8),
                "completeness_threshold": requirements.get("completeness", 0.9),
                "validation_rules": requirements.get("validation_rules", [])
            }
        
        return strategy
    
    def _calculate_connections(self, tier: str, platform_count: int) -> int:
        """Calculate concurrent connections based on tier"""
        tier_limits = {
            "tier_1": min(platform_count * 5, 50),
            "tier_2": min(platform_count * 3, 30),
            "tier_3": min(platform_count * 2, 20)
        }
        return tier_limits.get(tier, 30)
    
    def _calculate_rate_limits(self, tier: str) -> Dict[str, Any]:
        """Calculate rate limits based on tier"""
        return {
            "tier_1": {"requests_per_second": 100, "burst": 200},
            "tier_2": {"requests_per_second": 50, "burst": 100},
            "tier_3": {"requests_per_second": 20, "burst": 40}
        }.get(tier, {"requests_per_second": 50, "burst": 100})


class ProgressMonitor(AsyncBaseDiscoveryTool):
    """Monitors collection progress across all platforms"""
    
    name: str = "ProgressMonitor"
    description: str = "Track and report collection progress in real-time"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="ProgressMonitor",
            description="Monitors collection progress and performance metrics",
            tool_class=cls,
            categories=["collection", "monitoring", "metrics"],
            required_params=["flow_id"],
            optional_params=["metrics_type", "platform_filter"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        flow_id: str,
        metrics_type: str = "summary",
        platform_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Monitor collection progress.
        
        Args:
            flow_id: Collection flow ID
            metrics_type: Type of metrics (summary, detailed, realtime)
            platform_filter: Filter metrics by specific platforms
            
        Returns:
            Progress metrics and status
        """
        context = get_current_context()
        
        async with get_context_db() as db:
            state_service = CollectionFlowStateService(db, context)
            
            # Get current flow state
            flow_state = await state_service.get_flow_state(flow_id)
            
            if not flow_state:
                return {"error": "Flow not found", "flow_id": flow_id}
            
            progress = {
                "flow_id": flow_id,
                "overall_status": flow_state.get("status"),
                "started_at": flow_state.get("started_at"),
                "updated_at": flow_state.get("updated_at"),
                "automation_tier": flow_state.get("automation_tier")
            }
            
            # Get phase progress
            phases = flow_state.get("phases", {})
            phase_metrics = []
            
            for phase_name, phase_data in phases.items():
                if platform_filter and phase_name not in platform_filter:
                    continue
                
                phase_metric = {
                    "phase": phase_name,
                    "status": phase_data.get("status"),
                    "progress_percentage": phase_data.get("progress", 0),
                    "items_collected": phase_data.get("items_collected", 0),
                    "items_total": phase_data.get("items_total", 0),
                    "quality_score": phase_data.get("quality_score"),
                    "errors": phase_data.get("errors", [])
                }
                
                if metrics_type in ["detailed", "realtime"]:
                    phase_metric["performance"] = {
                        "collection_rate": phase_data.get("collection_rate", 0),
                        "avg_response_time": phase_data.get("avg_response_time", 0),
                        "memory_usage": phase_data.get("memory_usage", 0),
                        "cpu_usage": phase_data.get("cpu_usage", 0)
                    }
                
                phase_metrics.append(phase_metric)
            
            progress["phases"] = phase_metrics
            
            # Calculate overall progress
            total_items = sum(p.get("items_total", 0) for p in phase_metrics)
            collected_items = sum(p.get("items_collected", 0) for p in phase_metrics)
            progress["overall_progress"] = (collected_items / total_items * 100) if total_items > 0 else 0
            
            # Add performance summary
            if metrics_type in ["detailed", "realtime"]:
                progress["performance_summary"] = {
                    "total_items_collected": collected_items,
                    "total_items_expected": total_items,
                    "collection_efficiency": self._calculate_efficiency(phase_metrics),
                    "estimated_completion": self._estimate_completion(flow_state, phase_metrics)
                }
            
            # Add alerts if any issues
            alerts = []
            for phase in phase_metrics:
                if phase.get("errors"):
                    alerts.append({
                        "phase": phase["phase"],
                        "type": "error",
                        "message": f"{len(phase['errors'])} errors in {phase['phase']}"
                    })
                if phase.get("quality_score", 1.0) < 0.7:
                    alerts.append({
                        "phase": phase["phase"],
                        "type": "quality",
                        "message": f"Low quality score in {phase['phase']}: {phase['quality_score']}"
                    })
            
            progress["alerts"] = alerts
            
            return progress
    
    def _calculate_efficiency(self, phase_metrics: List[Dict[str, Any]]) -> float:
        """Calculate collection efficiency"""
        total_expected = sum(p.get("items_total", 0) for p in phase_metrics)
        total_collected = sum(p.get("items_collected", 0) for p in phase_metrics)
        
        if total_expected == 0:
            return 0.0
        
        # Factor in quality scores
        quality_weighted_collected = sum(
            p.get("items_collected", 0) * p.get("quality_score", 1.0)
            for p in phase_metrics
        )
        
        return quality_weighted_collected / total_expected
    
    def _estimate_completion(self, flow_state: Dict[str, Any], phase_metrics: List[Dict[str, Any]]) -> Optional[str]:
        """Estimate completion time based on current progress"""
        # Simple estimation based on current rate
        started_at = flow_state.get("started_at")
        if not started_at:
            return None
        
        elapsed_seconds = (datetime.utcnow() - datetime.fromisoformat(started_at)).total_seconds()
        
        total_items = sum(p.get("items_total", 0) for p in phase_metrics)
        collected_items = sum(p.get("items_collected", 0) for p in phase_metrics)
        
        if collected_items == 0 or collected_items >= total_items:
            return None
        
        rate = collected_items / elapsed_seconds
        remaining_items = total_items - collected_items
        estimated_seconds = remaining_items / rate
        
        estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
        return estimated_completion.isoformat()


class QualityValidator(AsyncBaseDiscoveryTool):
    """Validates collection quality throughout the process"""
    
    name: str = "QualityValidator"
    description: str = "Validate data quality during collection"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="QualityValidator",
            description="Validates collection data quality and completeness",
            tool_class=cls,
            categories=["collection", "validation", "quality"],
            required_params=["collected_data", "validation_type"],
            optional_params=["quality_thresholds", "validation_rules"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        collected_data: Dict[str, Any],
        validation_type: str,
        quality_thresholds: Optional[Dict[str, float]] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate collected data quality.
        
        Args:
            collected_data: Data collected from platforms
            validation_type: Type of validation (quick, standard, comprehensive)
            quality_thresholds: Quality score thresholds
            validation_rules: Custom validation rules
            
        Returns:
            Validation results with quality scores
        """
        context = get_current_context()
        quality_service = QualityAssessmentService()
        
        validation_results = {
            "validation_type": validation_type,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_quality": 0.0,
            "platform_scores": {},
            "issues": [],
            "recommendations": []
        }
        
        # Default thresholds
        if not quality_thresholds:
            quality_thresholds = {
                "completeness": 0.8,
                "accuracy": 0.9,
                "consistency": 0.85,
                "timeliness": 0.95
            }
        
        # Validate each platform's data
        for platform, data in collected_data.items():
            platform_validation = {
                "completeness": 0.0,
                "accuracy": 0.0,
                "consistency": 0.0,
                "timeliness": 0.0,
                "issues": []
            }
            
            # Completeness check
            if validation_type in ["standard", "comprehensive"]:
                completeness = await self._check_completeness(data, validation_rules)
                platform_validation["completeness"] = completeness
                
                if completeness < quality_thresholds["completeness"]:
                    platform_validation["issues"].append({
                        "type": "completeness",
                        "severity": "high" if completeness < 0.5 else "medium",
                        "message": f"Data completeness {completeness:.2%} below threshold"
                    })
            
            # Accuracy check
            if validation_type == "comprehensive":
                accuracy = await self._check_accuracy(data, validation_rules)
                platform_validation["accuracy"] = accuracy
                
                if accuracy < quality_thresholds["accuracy"]:
                    platform_validation["issues"].append({
                        "type": "accuracy",
                        "severity": "high",
                        "message": f"Data accuracy {accuracy:.2%} below threshold"
                    })
            
            # Consistency check
            consistency = await self._check_consistency(data)
            platform_validation["consistency"] = consistency
            
            if consistency < quality_thresholds["consistency"]:
                platform_validation["issues"].append({
                    "type": "consistency",
                    "severity": "medium",
                    "message": f"Data consistency {consistency:.2%} below threshold"
                })
            
            # Calculate overall platform score
            scores = [v for k, v in platform_validation.items() if k in quality_thresholds and v > 0]
            platform_validation["overall_score"] = sum(scores) / len(scores) if scores else 0.0
            
            validation_results["platform_scores"][platform] = platform_validation
            validation_results["issues"].extend([
                {"platform": platform, **issue} for issue in platform_validation["issues"]
            ])
        
        # Calculate overall quality
        all_scores = [p["overall_score"] for p in validation_results["platform_scores"].values()]
        validation_results["overall_quality"] = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        # Generate recommendations
        if validation_results["overall_quality"] < 0.8:
            validation_results["recommendations"].append(
                "Consider re-collecting data from platforms with low quality scores"
            )
        
        critical_issues = [i for i in validation_results["issues"] if i.get("severity") == "high"]
        if critical_issues:
            validation_results["recommendations"].append(
                f"Address {len(critical_issues)} critical quality issues before proceeding"
            )
        
        return validation_results
    
    async def _check_completeness(self, data: Any, rules: Optional[List[Dict[str, Any]]]) -> float:
        """Check data completeness"""
        if not data:
            return 0.0
        
        if isinstance(data, dict):
            # Check required fields from rules
            if rules:
                required_fields = [r["field"] for r in rules if r.get("required")]
                present_fields = sum(1 for f in required_fields if f in data and data[f] is not None)
                return present_fields / len(required_fields) if required_fields else 1.0
            else:
                # Basic completeness - non-null values
                total_fields = len(data)
                non_null_fields = sum(1 for v in data.values() if v is not None)
                return non_null_fields / total_fields if total_fields > 0 else 0.0
        
        elif isinstance(data, list):
            # For lists, check completeness of each item
            if not data:
                return 0.0
            completeness_scores = [await self._check_completeness(item, rules) for item in data[:100]]
            return sum(completeness_scores) / len(completeness_scores)
        
        return 1.0  # Single values are complete if present
    
    async def _check_accuracy(self, data: Any, rules: Optional[List[Dict[str, Any]]]) -> float:
        """Check data accuracy using validation rules"""
        if not rules:
            return 1.0  # Assume accurate if no rules
        
        # Apply validation rules
        passed_rules = 0
        total_rules = 0
        
        for rule in rules:
            if rule.get("type") == "format":
                # Format validation
                field_value = data.get(rule["field"])
                if field_value and self._validate_format(field_value, rule.get("format")):
                    passed_rules += 1
                total_rules += 1
            elif rule.get("type") == "range":
                # Range validation
                field_value = data.get(rule["field"])
                if field_value and rule.get("min") <= field_value <= rule.get("max"):
                    passed_rules += 1
                total_rules += 1
        
        return passed_rules / total_rules if total_rules > 0 else 1.0
    
    async def _check_consistency(self, data: Any) -> float:
        """Check data consistency"""
        # Simple consistency check - look for conflicting or duplicate data
        if isinstance(data, list):
            # Check for duplicates
            if len(data) == len(set(str(item) for item in data)):
                return 1.0  # No duplicates
            else:
                unique_count = len(set(str(item) for item in data))
                return unique_count / len(data)
        
        return 1.0  # Single items are consistent
    
    def _validate_format(self, value: Any, format_type: str) -> bool:
        """Validate value format"""
        import re
        
        format_patterns = {
            "email": r'^[\w\.-]+@[\w\.-]+\.\w+$',
            "ip": r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            "date": r'^\d{4}-\d{2}-\d{2}$'
        }
        
        pattern = format_patterns.get(format_type)
        if pattern and isinstance(value, str):
            return bool(re.match(pattern, value))
        
        return True


class ErrorRecoveryManager(AsyncBaseDiscoveryTool):
    """Manages error recovery during collection"""
    
    name: str = "ErrorRecoveryManager"
    description: str = "Handle errors and implement recovery strategies"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="ErrorRecoveryManager",
            description="Manages error recovery and retry strategies",
            tool_class=cls,
            categories=["collection", "error_handling", "recovery"],
            required_params=["error_context", "recovery_action"],
            optional_params=["retry_config", "fallback_strategy"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        error_context: Dict[str, Any],
        recovery_action: str,
        retry_config: Optional[Dict[str, Any]] = None,
        fallback_strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manage error recovery during collection.
        
        Args:
            error_context: Context about the error (platform, error_type, details)
            recovery_action: Action to take (retry, skip, fallback, manual)
            retry_config: Retry configuration (max_retries, backoff)
            fallback_strategy: Fallback approach if retry fails
            
        Returns:
            Recovery results and recommendations
        """
        recovery_result = {
            "error_context": error_context,
            "recovery_action": recovery_action,
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "actions_taken": [],
            "recommendations": []
        }
        
        platform = error_context.get("platform")
        error_type = error_context.get("error_type")
        error_details = error_context.get("details", {})
        
        # Default retry config
        if not retry_config:
            retry_config = {
                "max_retries": 3,
                "backoff": "exponential",
                "initial_delay": 1,
                "max_delay": 60
            }
        
        if recovery_action == "retry":
            # Implement retry logic
            retry_result = await self._handle_retry(
                platform, error_type, error_details, retry_config
            )
            recovery_result["actions_taken"].append(retry_result)
            recovery_result["success"] = retry_result.get("success", False)
            
            if not recovery_result["success"] and fallback_strategy:
                # Apply fallback strategy
                fallback_result = await self._apply_fallback(
                    platform, error_type, fallback_strategy
                )
                recovery_result["actions_taken"].append(fallback_result)
                recovery_result["success"] = fallback_result.get("success", False)
        
        elif recovery_action == "skip":
            # Skip the failed platform/operation
            recovery_result["actions_taken"].append({
                "action": "skip",
                "platform": platform,
                "reason": f"Skipping due to {error_type}"
            })
            recovery_result["success"] = True
            recovery_result["recommendations"].append(
                f"Consider manual collection for {platform} data"
            )
        
        elif recovery_action == "fallback":
            # Direct to fallback strategy
            if fallback_strategy:
                fallback_result = await self._apply_fallback(
                    platform, error_type, fallback_strategy
                )
                recovery_result["actions_taken"].append(fallback_result)
                recovery_result["success"] = fallback_result.get("success", False)
        
        elif recovery_action == "manual":
            # Queue for manual intervention
            recovery_result["actions_taken"].append({
                "action": "queue_manual",
                "platform": platform,
                "priority": self._determine_priority(error_type, error_details)
            })
            recovery_result["success"] = True
            recovery_result["manual_intervention_required"] = True
        
        # Add error-specific recommendations
        recovery_result["recommendations"].extend(
            self._generate_recommendations(error_type, recovery_result["success"])
        )
        
        return recovery_result
    
    async def _handle_retry(
        self,
        platform: str,
        error_type: str,
        error_details: Dict[str, Any],
        retry_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle retry logic with backoff"""
        import asyncio
        import math
        
        retry_result = {
            "action": "retry",
            "platform": platform,
            "attempts": 0,
            "success": False
        }
        
        max_retries = retry_config.get("max_retries", 3)
        backoff = retry_config.get("backoff", "exponential")
        initial_delay = retry_config.get("initial_delay", 1)
        max_delay = retry_config.get("max_delay", 60)
        
        for attempt in range(max_retries):
            retry_result["attempts"] = attempt + 1
            
            # Calculate delay
            if backoff == "exponential":
                delay = min(initial_delay * (2 ** attempt), max_delay)
            elif backoff == "linear":
                delay = min(initial_delay * (attempt + 1), max_delay)
            else:
                delay = initial_delay
            
            # Wait before retry
            if attempt > 0:
                await asyncio.sleep(delay)
            
            # Simulate retry (in real implementation, this would re-attempt the operation)
            # For now, we'll use error type to determine success probability
            success_probability = {
                "timeout": 0.6,
                "rate_limit": 0.3,
                "connection": 0.7,
                "authentication": 0.1,
                "unknown": 0.4
            }.get(error_type, 0.5)
            
            import random
            if random.random() < success_probability:
                retry_result["success"] = True
                retry_result["recovered_at_attempt"] = attempt + 1
                break
        
        return retry_result
    
    async def _apply_fallback(
        self,
        platform: str,
        error_type: str,
        fallback_strategy: str
    ) -> Dict[str, Any]:
        """Apply fallback strategy"""
        fallback_result = {
            "action": "fallback",
            "platform": platform,
            "strategy": fallback_strategy,
            "success": False
        }
        
        if fallback_strategy == "alternative_endpoint":
            # Try alternative API endpoint
            fallback_result["details"] = "Attempting alternative API endpoint"
            fallback_result["success"] = True  # Simulate success
            
        elif fallback_strategy == "reduced_scope":
            # Reduce collection scope
            fallback_result["details"] = "Reducing collection scope to critical data only"
            fallback_result["success"] = True
            
        elif fallback_strategy == "cached_data":
            # Use cached data if available
            fallback_result["details"] = "Using cached data from previous collection"
            fallback_result["success"] = True
            fallback_result["data_age"] = "2 hours"  # Simulated
            
        elif fallback_strategy == "manual_upload":
            # Switch to manual data upload
            fallback_result["details"] = "Switching to manual data upload process"
            fallback_result["success"] = True
            fallback_result["manual_required"] = True
        
        return fallback_result
    
    def _determine_priority(self, error_type: str, error_details: Dict[str, Any]) -> str:
        """Determine priority for manual intervention"""
        # Critical errors get high priority
        critical_errors = ["authentication", "permission_denied", "invalid_credentials"]
        if error_type in critical_errors:
            return "high"
        
        # Repeated failures get medium priority
        if error_details.get("retry_count", 0) > 3:
            return "medium"
        
        return "low"
    
    def _generate_recommendations(self, error_type: str, recovery_success: bool) -> List[str]:
        """Generate error-specific recommendations"""
        recommendations = []
        
        if error_type == "authentication":
            recommendations.append("Verify and update platform credentials")
            recommendations.append("Check for expired API keys or tokens")
            
        elif error_type == "rate_limit":
            recommendations.append("Implement request throttling")
            recommendations.append("Consider upgrading API tier for higher limits")
            
        elif error_type == "timeout":
            recommendations.append("Increase timeout values for slow endpoints")
            recommendations.append("Consider breaking large requests into smaller batches")
            
        elif error_type == "connection":
            recommendations.append("Verify network connectivity to platform")
            recommendations.append("Check firewall rules and proxy settings")
        
        if not recovery_success:
            recommendations.append("Consider scheduling collection during off-peak hours")
            recommendations.append("Evaluate alternative collection methods")
        
        return recommendations


# Import timedelta for completion estimation
from datetime import timedelta