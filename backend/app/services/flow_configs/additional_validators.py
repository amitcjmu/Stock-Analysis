"""
Additional Flow Validators
MFO-055: Implement flow-specific validators for Planning, Execution, Modernize, FinOps, Observability, and Decommission flows
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Planning Flow Validators

async def wave_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate wave planning configuration"""
    try:
        assessment_results = phase_input.get("assessment_results", {})
        business_constraints = phase_input.get("business_constraints", {})
        errors = []
        warnings = []
        
        if not assessment_results:
            errors.append("Missing assessment results")
        
        if not business_constraints:
            warnings.append("No business constraints specified - using defaults")
        
        # Validate wave constraints
        if business_constraints:
            max_parallel = business_constraints.get("max_parallel_migrations", 0)
            if max_parallel < 1:
                errors.append("Invalid max parallel migrations constraint")
            
            blackout_windows = business_constraints.get("blackout_windows", [])
            if blackout_windows and not isinstance(blackout_windows, list):
                errors.append("Invalid blackout windows format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Wave validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def resource_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate resource planning inputs"""
    try:
        wave_plan = phase_input.get("wave_plan", {})
        resource_constraints = phase_input.get("resource_constraints", {})
        errors = []
        
        if not wave_plan:
            errors.append("Missing wave plan")
        
        if resource_constraints:
            # Validate resource types
            for resource_type in ["human", "infrastructure", "licensing"]:
                if resource_type in resource_constraints:
                    constraint = resource_constraints[resource_type]
                    if not isinstance(constraint, dict):
                        errors.append(f"Invalid {resource_type} resource constraint format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Resource validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# Execution Flow Validators

async def pre_migration_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate pre-migration readiness"""
    try:
        migration_plan = phase_input.get("migration_plan", {})
        target_environment = phase_input.get("target_environment", {})
        errors = []
        warnings = []
        
        if not migration_plan:
            errors.append("Missing migration plan")
        
        if not target_environment:
            errors.append("Missing target environment configuration")
        elif isinstance(target_environment, dict):
            # Validate environment readiness
            if not target_environment.get("validated", False):
                warnings.append("Target environment not pre-validated")
            
            if not target_environment.get("capacity_verified", False):
                warnings.append("Target environment capacity not verified")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Pre-migration validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def execution_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate execution configuration"""
    try:
        validated_plan = phase_input.get("validated_plan", {})
        execution_config = phase_input.get("execution_config", {})
        errors = []
        
        if not validated_plan:
            errors.append("Missing validated migration plan")
        
        if not execution_config:
            errors.append("Missing execution configuration")
        elif isinstance(execution_config, dict):
            # Validate execution mode
            mode = execution_config.get("mode")
            if mode not in ["big_bang", "phased", "parallel", "blue_green"]:
                errors.append(f"Invalid execution mode: {mode}")
            
            # Validate rollback configuration
            if not execution_config.get("rollback_plan"):
                errors.append("Missing rollback plan")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Execution validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def post_migration_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate post-migration success criteria"""
    try:
        migration_results = phase_input.get("migration_results", {})
        validation_criteria = phase_input.get("validation_criteria", {})
        errors = []
        warnings = []
        
        if not migration_results:
            errors.append("Missing migration results")
        
        if not validation_criteria:
            errors.append("Missing validation criteria")
        elif isinstance(validation_criteria, dict):
            # Check for required validation types
            required_validations = ["connectivity", "functionality", "performance"]
            for validation in required_validations:
                if validation not in validation_criteria:
                    warnings.append(f"Missing {validation} validation criteria")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Post-migration validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# Modernize Flow Validators

async def modernization_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate modernization assessment inputs"""
    try:
        current_architecture = phase_input.get("current_architecture", {})
        modernization_goals = phase_input.get("modernization_goals", {})
        errors = []
        
        if not current_architecture:
            errors.append("Missing current architecture information")
        
        if not modernization_goals:
            errors.append("Missing modernization goals")
        elif isinstance(modernization_goals, dict):
            # Validate goal priorities
            if not any(modernization_goals.get(goal, False) for goal in 
                      ["containerization", "microservices", "serverless", "cloud_native"]):
                errors.append("No modernization goals selected")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Modernization validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def architecture_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate architecture redesign"""
    try:
        modernization_opportunities = phase_input.get("modernization_opportunities", {})
        design_principles = phase_input.get("design_principles", {})
        errors = []
        warnings = []
        
        if not modernization_opportunities:
            errors.append("Missing modernization opportunities")
        
        if not design_principles:
            warnings.append("No design principles specified - using defaults")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Architecture validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# FinOps Flow Validators

async def cost_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate cost analysis inputs"""
    try:
        current_costs = phase_input.get("current_costs", {})
        usage_patterns = phase_input.get("usage_patterns", {})
        errors = []
        warnings = []
        
        if not current_costs:
            errors.append("Missing current cost data")
        elif isinstance(current_costs, dict):
            # Validate cost data completeness
            if not current_costs.get("total_monthly_cost"):
                errors.append("Missing total monthly cost")
            
            if not current_costs.get("cost_breakdown"):
                warnings.append("Missing detailed cost breakdown")
        
        if not usage_patterns:
            warnings.append("No usage patterns provided - optimization may be limited")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Cost validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def optimization_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate optimization opportunities"""
    try:
        cost_analysis = phase_input.get("cost_analysis", {})
        optimization_rules = phase_input.get("optimization_rules", {})
        errors = []
        
        if not cost_analysis:
            errors.append("Missing cost analysis results")
        
        if not optimization_rules:
            errors.append("Missing optimization rules")
        elif isinstance(optimization_rules, dict):
            # Validate rule configuration
            if not optimization_rules.get("enabled_optimizations"):
                errors.append("No optimization types enabled")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    except Exception as e:
        logger.error(f"Optimization validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def budget_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate budget planning inputs"""
    try:
        optimization_opportunities = phase_input.get("optimization_opportunities", {})
        business_goals = phase_input.get("business_goals", {})
        errors = []
        warnings = []
        
        if not optimization_opportunities:
            warnings.append("No optimization opportunities to implement")
        
        if not business_goals:
            errors.append("Missing business goals for budget planning")
        elif isinstance(business_goals, dict):
            # Validate budget targets
            if not business_goals.get("target_reduction") and not business_goals.get("budget_cap"):
                warnings.append("No specific budget targets defined")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Budget validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# Observability Flow Validators

async def monitoring_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate monitoring setup configuration"""
    try:
        target_environment = phase_input.get("target_environment", {})
        monitoring_requirements = phase_input.get("monitoring_requirements", {})
        errors = []
        warnings = []
        
        if not target_environment:
            errors.append("Missing target environment specification")
        
        if not monitoring_requirements:
            errors.append("Missing monitoring requirements")
        elif isinstance(monitoring_requirements, dict):
            # Validate monitoring coverage
            required_layers = ["infrastructure", "application"]
            for layer in required_layers:
                if layer not in monitoring_requirements:
                    warnings.append(f"No monitoring requirements for {layer} layer")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Monitoring validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def logging_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate logging configuration"""
    try:
        monitoring_infrastructure = phase_input.get("monitoring_infrastructure", {})
        logging_requirements = phase_input.get("logging_requirements", {})
        errors = []
        warnings = []
        
        if not monitoring_infrastructure:
            errors.append("Missing monitoring infrastructure")
        
        if not logging_requirements:
            errors.append("Missing logging requirements")
        elif isinstance(logging_requirements, dict):
            # Validate retention policies
            retention = logging_requirements.get("retention_days")
            if retention and retention < 7:
                warnings.append("Very short log retention period")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Logging validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def alerting_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate alerting configuration"""
    try:
        monitoring_infrastructure = phase_input.get("monitoring_infrastructure", {})
        alerting_rules = phase_input.get("alerting_rules", {})
        errors = []
        warnings = []
        
        if not monitoring_infrastructure:
            errors.append("Missing monitoring infrastructure")
        
        if not alerting_rules:
            errors.append("Missing alerting rules")
        elif isinstance(alerting_rules, list) and len(alerting_rules) == 0:
            errors.append("No alerting rules defined")
        elif isinstance(alerting_rules, dict):
            # Validate notification channels
            if not alerting_rules.get("notification_channels"):
                warnings.append("No notification channels configured")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Alerting validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# Decommission Flow Validators

async def decommission_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate decommission planning inputs"""
    try:
        decommission_targets = phase_input.get("decommission_targets", [])
        business_requirements = phase_input.get("business_requirements", {})
        errors = []
        warnings = []
        
        if not decommission_targets:
            errors.append("No decommission targets specified")
        elif isinstance(decommission_targets, list):
            # Validate each target
            for target in decommission_targets:
                if not isinstance(target, dict) or not target.get("system_id"):
                    errors.append("Invalid decommission target format")
                    break
        
        if not business_requirements:
            errors.append("Missing business requirements")
        elif isinstance(business_requirements, dict):
            # Check for required approvals
            if not business_requirements.get("approval_obtained", False):
                errors.append("Decommission approval not obtained")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Decommission validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def data_migration_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate data migration for decommission"""
    try:
        decommission_plan = phase_input.get("decommission_plan", {})
        data_requirements = phase_input.get("data_requirements", {})
        errors = []
        warnings = []
        
        if not decommission_plan:
            errors.append("Missing decommission plan")
        
        if not data_requirements:
            errors.append("Missing data requirements")
        elif isinstance(data_requirements, dict):
            # Validate data handling
            if not data_requirements.get("backup_location"):
                errors.append("No backup location specified")
            
            if not data_requirements.get("retention_period"):
                warnings.append("No data retention period specified")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Data migration validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def shutdown_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate system shutdown readiness"""
    try:
        migrated_data = phase_input.get("migrated_data", {})
        shutdown_procedures = phase_input.get("shutdown_procedures", {})
        errors = []
        warnings = []
        
        if not migrated_data:
            errors.append("Data migration not completed")
        elif isinstance(migrated_data, dict):
            # Validate migration success
            if not migrated_data.get("verification_passed", False):
                errors.append("Data migration verification failed")
        
        if not shutdown_procedures:
            errors.append("Missing shutdown procedures")
        elif isinstance(shutdown_procedures, dict):
            # Validate shutdown sequence
            if not shutdown_procedures.get("sequence"):
                errors.append("No shutdown sequence defined")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Shutdown validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


# Additional common validators

async def dependency_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generic dependency validation"""
    try:
        dependencies = phase_input.get("dependencies", {})
        errors = []
        warnings = []
        
        # Check for circular dependencies
        visited = set()
        def has_cycle(node, path):
            if node in path:
                return True
            if node in visited:
                return False
            visited.add(node)
            for dep in dependencies.get(node, []):
                if has_cycle(dep, path + [node]):
                    return True
            return False
        
        for node in dependencies:
            if has_cycle(node, []):
                errors.append(f"Circular dependency detected involving {node}")
                break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Dependency validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def timeline_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate timeline feasibility"""
    try:
        wave_plan = phase_input.get("wave_plan", {})
        resource_plan = phase_input.get("resource_plan", {})
        errors = []
        warnings = []
        
        if not wave_plan:
            errors.append("Missing wave plan for timeline validation")
        
        if not resource_plan:
            warnings.append("Missing resource plan - timeline may be unrealistic")
        
        # Basic timeline feasibility checks would go here
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Timeline validation error: {e}")
        return {"valid": False, "errors": [str(e)]}


async def capacity_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate capacity requirements"""
    try:
        required_capacity = phase_input.get("required_capacity", {})
        available_capacity = phase_input.get("available_capacity", {})
        errors = []
        warnings = []
        
        if not required_capacity:
            errors.append("Missing required capacity information")
        
        if not available_capacity:
            errors.append("Missing available capacity information")
        elif required_capacity and available_capacity:
            # Compare capacities
            for resource_type, required in required_capacity.items():
                available = available_capacity.get(resource_type, 0)
                if available < required:
                    errors.append(f"Insufficient {resource_type} capacity: required {required}, available {available}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Capacity validation error: {e}")
        return {"valid": False, "errors": [str(e)]}