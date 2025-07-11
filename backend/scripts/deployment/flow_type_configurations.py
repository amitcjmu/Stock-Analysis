#!/usr/bin/env python3
"""
Flow Type Configurations for Master Flow Orchestrator
Phase 3 Days 4-5: MFO-039 through MFO-058

This script implements all flow type configurations for the Master Flow Orchestrator:
- Discovery flows (MFO-039 to MFO-042)
- Assessment flows (MFO-043 to MFO-045)
- Planning flows (MFO-049)
- Execution flows (MFO-050)
- Modernize flows (MFO-051)
- FinOps flows (MFO-052)
- Observability flows (MFO-053)
- Decommission flows (MFO-054)
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.services.flow_type_registry import FlowTypeRegistry, FlowTypeConfig, PhaseConfig
from app.services.validator_registry import ValidatorRegistry
from app.services.handler_registry import HandlerRegistry
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class FlowTypeConfigurator:
    """Configures all flow types for the Master Flow Orchestrator"""
    
    def __init__(self):
        self.flow_registry = FlowTypeRegistry()
        self.validator_registry = ValidatorRegistry()
        self.handler_registry = HandlerRegistry()
        
    async def configure_all_flow_types(self) -> Dict[str, Any]:
        """Configure all flow types (MFO-039 through MFO-058)"""
        results = {
            "configured_flows": [],
            "validation_errors": [],
            "handler_errors": [],
            "total_flows": 0,
            "successful_configurations": 0
        }
        
        try:
            logger.info("🔄 Starting flow type configuration...")
            
            # Day 4: Discovery and Assessment flows
            discovery_result = await self._configure_discovery_flow()
            assessment_result = await self._configure_assessment_flow()
            
            # Day 5: Remaining flow types
            planning_result = await self._configure_planning_flow()
            execution_result = await self._configure_execution_flow()
            modernize_result = await self._configure_modernize_flow()
            finops_result = await self._configure_finops_flow()
            observability_result = await self._configure_observability_flow()
            decommission_result = await self._configure_decommission_flow()
            
            # Collect results
            all_results = [
                discovery_result, assessment_result, planning_result,
                execution_result, modernize_result, finops_result,
                observability_result, decommission_result
            ]
            
            for result in all_results:
                if result["success"]:
                    results["configured_flows"].append(result["flow_type"])
                    results["successful_configurations"] += 1
                else:
                    results["validation_errors"].extend(result.get("errors", []))
                
                results["total_flows"] += 1
            
            # Verify all configurations
            verification_result = await self._verify_flow_configurations()
            results["verification"] = verification_result
            
            logger.info(f"✅ Flow configuration complete: {results['successful_configurations']}/{results['total_flows']} flows configured")
            return results
            
        except Exception as e:
            logger.error(f"❌ Flow configuration failed: {e}")
            results["configuration_error"] = str(e)
            return results
    
    async def _configure_discovery_flow(self) -> Dict[str, Any]:
        """MFO-039 to MFO-042: Configure Discovery flow"""
        try:
            logger.info("🔄 Configuring Discovery flow...")
            
            # Define discovery phases (all 6 phases)
            discovery_phases = [
                PhaseConfig(
                    name="data_import",
                    display_name="Data Import",
                    description="Import and validate data from various sources",
                    required_inputs=["raw_data", "import_config"],
                    validators=["required_fields", "data_format"],
                    timeout_seconds=1800
                ),
                PhaseConfig(
                    name="field_mapping",
                    display_name="Field Mapping",
                    description="Map imported fields to standard schema",
                    required_inputs=["imported_data", "mapping_rules"],
                    validators=["field_mapping_validation"],
                    timeout_seconds=1200
                ),
                PhaseConfig(
                    name="data_cleansing",
                    order=3,
                    required=True,
                    description="Clean and normalize data",
                    inputs=["mapped_data", "cleansing_rules"],
                    outputs=["cleansed_data", "cleansing_report"],
                    validators=["data_quality"],
                    timeout_minutes=25
                ),
                PhaseConfig(
                    name="asset_creation",
                    order=4,
                    required=True,
                    description="Create asset records from cleansed data",
                    inputs=["cleansed_data", "asset_templates"],
                    outputs=["assets", "creation_report"],
                    validators=["asset_validation"],
                    completion_handler="asset_creation",
                    timeout_minutes=40
                ),
                PhaseConfig(
                    name="asset_inventory",
                    order=5,
                    required=True,
                    description="Build comprehensive asset inventory",
                    inputs=["assets", "inventory_config"],
                    outputs=["inventory", "inventory_report"],
                    validators=["inventory_validation"],
                    timeout_minutes=30
                ),
                PhaseConfig(
                    name="dependency_analysis",
                    order=6,
                    required=False,
                    description="Analyze asset dependencies",
                    inputs=["inventory", "dependency_rules"],
                    outputs=["dependencies", "dependency_report"],
                    validators=["dependency_validation"],
                    timeout_minutes=35
                )
            ]
            
            # Import the actual CrewAI Flow class
            try:
                from app.services.crewai_flows.unified_discovery_flow.base_flow import UnifiedDiscoveryFlow
                discovery_crew_class = UnifiedDiscoveryFlow
            except ImportError:
                logger.warning("UnifiedDiscoveryFlow not available, flow will use placeholder")
                discovery_crew_class = None
            
            # Create discovery flow configuration
            discovery_config = FlowTypeConfig(
                name="discovery",
                display_name="Discovery Flow",
                description="Comprehensive asset discovery and inventory flow",
                phases=discovery_phases,
                crew_class=discovery_crew_class,  # Link to actual CrewAI implementation
                default_configuration={
                    "enable_real_time_validation": True,
                    "auto_retry_failed_phases": True,
                    "max_retries": 3,
                    "notification_channels": ["email", "webhook"],
                    "agent_collaboration": True
                },
                required_permissions=["discovery.read", "discovery.write"],
                initialization_handler="discovery_initialization",
                completion_handler="discovery_completion",
                error_handler="discovery_error_handler"
            )
            
            # Register discovery-specific validators (MFO-040)
            await self._register_discovery_validators()
            
            # Register discovery asset creation handler (MFO-041)
            await self._register_discovery_handlers()
            
            # Register discovery flow (MFO-042)
            self.flow_registry.register(discovery_config)
            
            logger.info("✅ Discovery flow configured successfully")
            return {
                "success": True,
                "flow_type": "discovery",
                "phases_count": len(discovery_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "discovery",
                "errors": [str(e)]
            }
    
    async def _configure_assessment_flow(self) -> Dict[str, Any]:
        """MFO-043 to MFO-045: Configure Assessment flow"""
        try:
            logger.info("🔄 Configuring Assessment flow...")
            
            # Define assessment phases (all 4 phases)
            assessment_phases = [
                PhaseConfig(
                    name="readiness_assessment",
                    order=1,
                    required=True,
                    description="Assess migration readiness of assets",
                    inputs=["asset_inventory", "assessment_criteria"],
                    outputs=["readiness_scores", "readiness_report"],
                    validators=["required_fields", "assessment_validation"],
                    timeout_minutes=45
                ),
                PhaseConfig(
                    name="complexity_analysis",
                    order=2,
                    required=True,
                    description="Analyze migration complexity",
                    inputs=["readiness_scores", "complexity_rules"],
                    outputs=["complexity_scores", "complexity_report"],
                    validators=["complexity_validation"],
                    timeout_minutes=35
                ),
                PhaseConfig(
                    name="risk_assessment",
                    order=3,
                    required=True,
                    description="Assess migration risks",
                    inputs=["complexity_scores", "risk_matrix"],
                    outputs=["risk_scores", "risk_report"],
                    validators=["risk_validation"],
                    timeout_minutes=30
                ),
                PhaseConfig(
                    name="recommendation_generation",
                    order=4,
                    required=True,
                    description="Generate migration recommendations",
                    inputs=["risk_scores", "business_priorities"],
                    outputs=["recommendations", "recommendation_report"],
                    validators=["recommendation_validation"],
                    completion_handler="assessment_completion",
                    timeout_minutes=25
                )
            ]
            
            # Create assessment flow configuration
            assessment_config = FlowTypeConfig(
                name="assessment",
                display_name="Assessment Flow",
                description="Comprehensive migration assessment and recommendation flow",
                phases=assessment_phases,
                default_configuration={
                    "enable_risk_scoring": True,
                    "auto_generate_reports": True,
                    "assessment_depth": "comprehensive",
                    "include_business_impact": True,
                    "agent_collaboration": True
                },
                required_permissions=["assessment.read", "assessment.write"],
                initialization_handler="assessment_initialization",
                completion_handler="assessment_completion",
                error_handler="assessment_error_handler"
            )
            
            # Register assessment-specific validators (MFO-044)
            await self._register_assessment_validators()
            
            # Register assessment flow (MFO-045)
            self.flow_registry.register_flow_type(assessment_config)
            
            logger.info("✅ Assessment flow configured successfully")
            return {
                "success": True,
                "flow_type": "assessment",
                "phases_count": len(assessment_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Assessment flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "assessment",
                "errors": [str(e)]
            }
    
    async def _configure_planning_flow(self) -> Dict[str, Any]:
        """MFO-049: Configure Planning flow"""
        try:
            logger.info("🔄 Configuring Planning flow...")
            
            planning_phases = [
                PhaseConfig(
                    name="wave_planning",
                    order=1,
                    required=True,
                    description="Plan migration waves based on dependencies",
                    inputs=["assessment_results", "business_constraints"],
                    outputs=["wave_plan", "timeline"],
                    validators=["wave_validation"],
                    timeout_minutes=60
                ),
                PhaseConfig(
                    name="resource_planning",
                    order=2,
                    required=True,
                    description="Plan resource allocation and capacity",
                    inputs=["wave_plan", "resource_constraints"],
                    outputs=["resource_plan", "capacity_plan"],
                    validators=["resource_validation"],
                    timeout_minutes=45
                ),
                PhaseConfig(
                    name="timeline_optimization",
                    order=3,
                    required=False,
                    description="Optimize migration timeline",
                    inputs=["wave_plan", "resource_plan"],
                    outputs=["optimized_timeline", "optimization_report"],
                    validators=["timeline_validation"],
                    timeout_minutes=30
                )
            ]
            
            planning_config = FlowTypeConfig(
                name="planning",
                display_name="Planning Flow",
                description="Migration wave and resource planning flow",
                phases=planning_phases,
                default_configuration={
                    "optimization_enabled": True,
                    "dependency_tracking": True,
                    "resource_constraints": True
                },
                required_permissions=["planning.read", "planning.write"]
            )
            
            self.flow_registry.register_flow_type(planning_config)
            
            logger.info("✅ Planning flow configured successfully")
            return {
                "success": True,
                "flow_type": "planning",
                "phases_count": len(planning_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Planning flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "planning",
                "errors": [str(e)]
            }
    
    async def _configure_execution_flow(self) -> Dict[str, Any]:
        """MFO-050: Configure Execution flow"""
        try:
            logger.info("🔄 Configuring Execution flow...")
            
            execution_phases = [
                PhaseConfig(
                    name="pre_migration_validation",
                    order=1,
                    required=True,
                    description="Validate readiness before migration",
                    inputs=["migration_plan", "target_environment"],
                    outputs=["validation_results", "readiness_status"],
                    validators=["pre_migration_validation"],
                    timeout_minutes=30
                ),
                PhaseConfig(
                    name="migration_execution",
                    order=2,
                    required=True,
                    description="Execute the actual migration",
                    inputs=["validated_plan", "execution_config"],
                    outputs=["migration_results", "execution_log"],
                    validators=["execution_validation"],
                    timeout_minutes=180
                ),
                PhaseConfig(
                    name="post_migration_validation",
                    order=3,
                    required=True,
                    description="Validate migration success",
                    inputs=["migration_results", "validation_criteria"],
                    outputs=["validation_report", "success_status"],
                    validators=["post_migration_validation"],
                    completion_handler="migration_completion",
                    timeout_minutes=45
                )
            ]
            
            execution_config = FlowTypeConfig(
                name="execution",
                display_name="Execution Flow",
                description="Migration execution and validation flow",
                phases=execution_phases,
                default_configuration={
                    "rollback_enabled": True,
                    "real_time_monitoring": True,
                    "automated_validation": True
                },
                required_permissions=["execution.read", "execution.write", "execution.execute"]
            )
            
            self.flow_registry.register_flow_type(execution_config)
            
            logger.info("✅ Execution flow configured successfully")
            return {
                "success": True,
                "flow_type": "execution",
                "phases_count": len(execution_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Execution flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "execution",
                "errors": [str(e)]
            }
    
    async def _configure_modernize_flow(self) -> Dict[str, Any]:
        """MFO-051: Configure Modernize flow"""
        try:
            logger.info("🔄 Configuring Modernize flow...")
            
            modernize_phases = [
                PhaseConfig(
                    name="modernization_assessment",
                    order=1,
                    required=True,
                    description="Assess modernization opportunities",
                    inputs=["current_architecture", "modernization_goals"],
                    outputs=["modernization_opportunities", "assessment_report"],
                    validators=["modernization_validation"],
                    timeout_minutes=60
                ),
                PhaseConfig(
                    name="architecture_redesign",
                    order=2,
                    required=True,
                    description="Redesign architecture for cloud-native patterns",
                    inputs=["modernization_opportunities", "design_principles"],
                    outputs=["new_architecture", "design_artifacts"],
                    validators=["architecture_validation"],
                    timeout_minutes=90
                ),
                PhaseConfig(
                    name="implementation_planning",
                    order=3,
                    required=True,
                    description="Plan modernization implementation",
                    inputs=["new_architecture", "implementation_constraints"],
                    outputs=["implementation_plan", "modernization_roadmap"],
                    validators=["implementation_validation"],
                    completion_handler="modernization_completion",
                    timeout_minutes=45
                )
            ]
            
            modernize_config = FlowTypeConfig(
                name="modernize",
                display_name="Modernize Flow",
                description="Application modernization and cloud-native transformation flow",
                phases=modernize_phases,
                default_configuration={
                    "cloud_native_patterns": True,
                    "microservices_assessment": True,
                    "containerization_analysis": True
                },
                required_permissions=["modernize.read", "modernize.write"]
            )
            
            self.flow_registry.register_flow_type(modernize_config)
            
            logger.info("✅ Modernize flow configured successfully")
            return {
                "success": True,
                "flow_type": "modernize",
                "phases_count": len(modernize_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Modernize flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "modernize",
                "errors": [str(e)]
            }
    
    async def _configure_finops_flow(self) -> Dict[str, Any]:
        """MFO-052: Configure FinOps flow"""
        try:
            logger.info("🔄 Configuring FinOps flow...")
            
            finops_phases = [
                PhaseConfig(
                    name="cost_analysis",
                    order=1,
                    required=True,
                    description="Analyze current and projected costs",
                    inputs=["current_costs", "usage_patterns"],
                    outputs=["cost_analysis", "cost_projections"],
                    validators=["cost_validation"],
                    timeout_minutes=45
                ),
                PhaseConfig(
                    name="optimization_identification",
                    order=2,
                    required=True,
                    description="Identify cost optimization opportunities",
                    inputs=["cost_analysis", "optimization_rules"],
                    outputs=["optimization_opportunities", "savings_potential"],
                    validators=["optimization_validation"],
                    timeout_minutes=60
                ),
                PhaseConfig(
                    name="budget_planning",
                    order=3,
                    required=True,
                    description="Plan budgets and cost controls",
                    inputs=["optimization_opportunities", "business_goals"],
                    outputs=["budget_plan", "cost_controls"],
                    validators=["budget_validation"],
                    completion_handler="finops_completion",
                    timeout_minutes=30
                )
            ]
            
            finops_config = FlowTypeConfig(
                name="finops",
                display_name="FinOps Flow",
                description="Financial operations and cost optimization flow",
                phases=finops_phases,
                default_configuration={
                    "real_time_cost_tracking": True,
                    "automated_optimization": True,
                    "budget_alerts": True
                },
                required_permissions=["finops.read", "finops.write"]
            )
            
            self.flow_registry.register_flow_type(finops_config)
            
            logger.info("✅ FinOps flow configured successfully")
            return {
                "success": True,
                "flow_type": "finops",
                "phases_count": len(finops_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ FinOps flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "finops",
                "errors": [str(e)]
            }
    
    async def _configure_observability_flow(self) -> Dict[str, Any]:
        """MFO-053: Configure Observability flow"""
        try:
            logger.info("🔄 Configuring Observability flow...")
            
            observability_phases = [
                PhaseConfig(
                    name="monitoring_setup",
                    order=1,
                    required=True,
                    description="Set up monitoring infrastructure",
                    inputs=["target_environment", "monitoring_requirements"],
                    outputs=["monitoring_infrastructure", "setup_report"],
                    validators=["monitoring_validation"],
                    timeout_minutes=60
                ),
                PhaseConfig(
                    name="logging_configuration",
                    order=2,
                    required=True,
                    description="Configure logging and log aggregation",
                    inputs=["monitoring_infrastructure", "logging_requirements"],
                    outputs=["logging_configuration", "log_pipelines"],
                    validators=["logging_validation"],
                    timeout_minutes=45
                ),
                PhaseConfig(
                    name="alerting_setup",
                    order=3,
                    required=True,
                    description="Set up alerting and notification systems",
                    inputs=["monitoring_infrastructure", "alerting_rules"],
                    outputs=["alerting_configuration", "notification_channels"],
                    validators=["alerting_validation"],
                    completion_handler="observability_completion",
                    timeout_minutes=30
                )
            ]
            
            observability_config = FlowTypeConfig(
                name="observability",
                display_name="Observability Flow",
                description="Monitoring, logging, and alerting setup flow",
                phases=observability_phases,
                default_configuration={
                    "real_time_monitoring": True,
                    "distributed_tracing": True,
                    "automated_alerting": True
                },
                required_permissions=["observability.read", "observability.write"]
            )
            
            self.flow_registry.register_flow_type(observability_config)
            
            logger.info("✅ Observability flow configured successfully")
            return {
                "success": True,
                "flow_type": "observability",
                "phases_count": len(observability_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Observability flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "observability",
                "errors": [str(e)]
            }
    
    async def _configure_decommission_flow(self) -> Dict[str, Any]:
        """MFO-054: Configure Decommission flow"""
        try:
            logger.info("🔄 Configuring Decommission flow...")
            
            decommission_phases = [
                PhaseConfig(
                    name="decommission_planning",
                    order=1,
                    required=True,
                    description="Plan system decommissioning",
                    inputs=["decommission_targets", "business_requirements"],
                    outputs=["decommission_plan", "timeline"],
                    validators=["decommission_validation"],
                    timeout_minutes=45
                ),
                PhaseConfig(
                    name="data_migration",
                    order=2,
                    required=True,
                    description="Migrate critical data before decommission",
                    inputs=["decommission_plan", "data_requirements"],
                    outputs=["migrated_data", "migration_report"],
                    validators=["data_migration_validation"],
                    timeout_minutes=120
                ),
                PhaseConfig(
                    name="system_shutdown",
                    order=3,
                    required=True,
                    description="Safely shutdown and decommission systems",
                    inputs=["migrated_data", "shutdown_procedures"],
                    outputs=["shutdown_report", "decommission_status"],
                    validators=["shutdown_validation"],
                    completion_handler="decommission_completion",
                    timeout_minutes=60
                )
            ]
            
            decommission_config = FlowTypeConfig(
                name="decommission",
                display_name="Decommission Flow",
                description="Safe system decommissioning and data migration flow",
                phases=decommission_phases,
                default_configuration={
                    "data_backup_required": True,
                    "approval_workflow": True,
                    "audit_trail": True
                },
                required_permissions=["decommission.read", "decommission.write", "decommission.execute"]
            )
            
            self.flow_registry.register_flow_type(decommission_config)
            
            logger.info("✅ Decommission flow configured successfully")
            return {
                "success": True,
                "flow_type": "decommission",
                "phases_count": len(decommission_phases),
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Decommission flow configuration failed: {e}")
            return {
                "success": False,
                "flow_type": "decommission",
                "errors": [str(e)]
            }
    
    async def _register_discovery_validators(self) -> None:
        """Register Discovery-specific validators (MFO-040)"""
        
        async def field_mapping_validation(phase_input, flow_state, overrides=None):
            """Validate field mapping configuration"""
            mapping_rules = phase_input.get("mapping_rules", {})
            imported_data = phase_input.get("imported_data", [])
            
            if not mapping_rules:
                return {"valid": False, "errors": ["Missing mapping rules"]}
            
            if not imported_data:
                return {"valid": False, "errors": ["No data to map"]}
            
            # Validate mapping completeness
            required_fields = ["hostname", "ip_address", "os_type"]
            mapped_fields = list(mapping_rules.keys())
            
            missing_fields = [field for field in required_fields if field not in mapped_fields]
            if missing_fields:
                return {"valid": False, "errors": [f"Missing required field mappings: {missing_fields}"]}
            
            return {"valid": True, "errors": []}
        
        async def asset_validation(phase_input, flow_state, overrides=None):
            """Validate created assets"""
            assets = phase_input.get("assets", [])
            
            if not assets:
                return {"valid": False, "errors": ["No assets created"]}
            
            # Validate asset structure
            for asset in assets:
                if not asset.get("asset_id"):
                    return {"valid": False, "errors": ["Asset missing asset_id"]}
                if not asset.get("asset_type"):
                    return {"valid": False, "errors": ["Asset missing asset_type"]}
            
            return {"valid": True, "errors": []}
        
        # Register validators
        self.validator_registry.register_validator("field_mapping_validation", field_mapping_validation)
        self.validator_registry.register_validator("asset_validation", asset_validation)
        self.validator_registry.register_validator("inventory_validation", asset_validation)  # Reuse for inventory
        self.validator_registry.register_validator("dependency_validation", asset_validation)  # Simplified
    
    async def _register_discovery_handlers(self) -> None:
        """Register Discovery asset creation handler (MFO-041)"""
        
        async def discovery_initialization(flow_id, flow_type, **kwargs):
            """Initialize discovery flow"""
            return {
                "initialized": True,
                "flow_id": flow_id,
                "initialization_time": datetime.utcnow().isoformat()
            }
        
        async def discovery_completion(flow_id, flow_type, **kwargs):
            """Handle discovery flow completion"""
            return {
                "completed": True,
                "flow_id": flow_id,
                "completion_time": datetime.utcnow().isoformat(),
                "assets_created": kwargs.get("asset_count", 0)
            }
        
        async def discovery_error_handler(flow_id, flow_type, error, **kwargs):
            """Handle discovery flow errors"""
            return {
                "error_handled": True,
                "flow_id": flow_id,
                "error": str(error),
                "recovery_action": "restart_from_last_checkpoint"
            }
        
        # Register handlers
        self.handler_registry.register_handler("discovery_initialization", discovery_initialization)
        self.handler_registry.register_handler("discovery_completion", discovery_completion)
        self.handler_registry.register_handler("discovery_error_handler", discovery_error_handler)
    
    async def _register_assessment_validators(self) -> None:
        """Register Assessment-specific validators (MFO-044)"""
        
        async def assessment_validation(phase_input, flow_state, overrides=None):
            """Validate assessment inputs"""
            asset_inventory = phase_input.get("asset_inventory")
            assessment_criteria = phase_input.get("assessment_criteria")
            
            if not asset_inventory:
                return {"valid": False, "errors": ["Missing asset inventory"]}
            
            if not assessment_criteria:
                return {"valid": False, "errors": ["Missing assessment criteria"]}
            
            return {"valid": True, "errors": []}
        
        async def complexity_validation(phase_input, flow_state, overrides=None):
            """Validate complexity analysis"""
            readiness_scores = phase_input.get("readiness_scores")
            if not readiness_scores:
                return {"valid": False, "errors": ["Missing readiness scores"]}
            return {"valid": True, "errors": []}
        
        async def risk_validation(phase_input, flow_state, overrides=None):
            """Validate risk assessment"""
            complexity_scores = phase_input.get("complexity_scores")
            if not complexity_scores:
                return {"valid": False, "errors": ["Missing complexity scores"]}
            return {"valid": True, "errors": []}
        
        async def recommendation_validation(phase_input, flow_state, overrides=None):
            """Validate recommendations"""
            risk_scores = phase_input.get("risk_scores")
            if not risk_scores:
                return {"valid": False, "errors": ["Missing risk scores"]}
            return {"valid": True, "errors": []}
        
        # Register validators
        self.validator_registry.register_validator("assessment_validation", assessment_validation)
        self.validator_registry.register_validator("complexity_validation", complexity_validation)
        self.validator_registry.register_validator("risk_validation", risk_validation)
        self.validator_registry.register_validator("recommendation_validation", recommendation_validation)
    
    async def _verify_flow_configurations(self) -> Dict[str, Any]:
        """Verify all flow configurations (MFO-058)"""
        try:
            all_flow_types = self.flow_registry.get_all_flow_types()
            
            verification_results = {
                "total_flows": len(all_flow_types),
                "verified_flows": [],
                "configuration_issues": [],
                "consistency_check": True
            }
            
            expected_flows = [
                "discovery", "assessment", "planning", "execution", 
                "modernize", "finops", "observability", "decommission"
            ]
            
            for flow_name in expected_flows:
                if self.flow_registry.is_registered(flow_name):
                    config = self.flow_registry.get_flow_config(flow_name)
                    
                    # Verify configuration completeness
                    if not config.phases:
                        verification_results["configuration_issues"].append(f"{flow_name}: No phases defined")
                    elif len(config.phases) == 0:
                        verification_results["configuration_issues"].append(f"{flow_name}: Empty phases list")
                    else:
                        verification_results["verified_flows"].append({
                            "flow_type": flow_name,
                            "phases_count": len(config.phases),
                            "has_validators": any(phase.validators for phase in config.phases),
                            "has_handlers": bool(config.completion_handler)
                        })
                else:
                    verification_results["configuration_issues"].append(f"{flow_name}: Not registered")
            
            if verification_results["configuration_issues"]:
                verification_results["consistency_check"] = False
            
            return verification_results
            
        except Exception as e:
            return {
                "verification_error": str(e),
                "consistency_check": False
            }


async def run_flow_type_configuration():
    """Main function to run flow type configuration"""
    configurator = FlowTypeConfigurator()
    
    try:
        logger.info("🚀 Starting Master Flow Orchestrator flow type configuration...")
        
        # Configure all flow types
        results = await configurator.configure_all_flow_types()
        
        # Print results
        print("\n" + "="*60)
        print("FLOW TYPE CONFIGURATION RESULTS")
        print("="*60)
        
        print(f"\nTotal flows configured: {results['successful_configurations']}/{results['total_flows']}")
        print(f"Configured flows: {', '.join(results['configured_flows'])}")
        
        if results.get("validation_errors"):
            print(f"\nValidation errors: {len(results['validation_errors'])}")
            for error in results["validation_errors"]:
                print(f"  ❌ {error}")
        
        if results.get("verification"):
            verification = results["verification"]
            print(f"\nVerification results:")
            print(f"  - Total flows: {verification['total_flows']}")
            print(f"  - Verified flows: {len(verification['verified_flows'])}")
            print(f"  - Consistency check: {'✅ PASSED' if verification['consistency_check'] else '❌ FAILED'}")
            
            if verification.get("configuration_issues"):
                print("  - Configuration issues:")
                for issue in verification["configuration_issues"]:
                    print(f"    ❌ {issue}")
        
        print(f"\n{'✅ CONFIGURATION COMPLETED SUCCESSFULLY' if results['successful_configurations'] == results['total_flows'] else '⚠️ CONFIGURATION COMPLETED WITH ISSUES'}")
        print("="*60)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Flow type configuration failed: {e}")
        print(f"\n❌ Configuration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_flow_type_configuration())