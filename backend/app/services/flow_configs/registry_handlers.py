"""
Handler Registration Module
Registers all handlers with the handler registry
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def register_all_handlers(handler_registry, results: Dict[str, Any]) -> None:
    """Register all handlers with the handler registry"""
    from .additional_handlers import (
        cost_data_collection,
        decommission_completion,
        decommission_error_handler,
        decommission_finalization,
        decommission_initialization,
        environment_preparation,
        execution_error_handler,
        execution_finalization,
        execution_initialization,
        final_backup,
        finops_completion,
        finops_error_handler,
        finops_finalization,
        finops_initialization,
        impact_analysis,
        migration_completion,
        modernization_completion,
        modernize_error_handler,
        modernize_finalization,
        modernize_initialization,
        monitoring_design,
        observability_completion,
        observability_error_handler,
        observability_finalization,
        observability_initialization,
        planning_completion,
        planning_error_handler,
        planning_finalization,
        planning_initialization,
        wave_analysis,
        wave_optimization,
    )
    from .assessment_handlers import (
        assessment_completion,
        assessment_error_handler,
        assessment_finalization,
        assessment_initialization,
        complexity_categorization,
        complexity_preparation,
        mitigation_planning,
        readiness_preparation,
        readiness_scoring,
        recommendation_analysis,
        risk_identification,
        roadmap_generation,
    )
    from .collection_handler_extensions import (
        register_collection_extension_handlers,
    )
    from .collection_handlers import (
        adapter_preparation,
        collection_checkpoint_handler,
        collection_data_normalization,
        collection_error_handler,
        collection_finalization,
        collection_initialization,
        collection_rollback_handler,
        gap_analysis_preparation,
        gap_prioritization,
        platform_inventory_creation,
        questionnaire_generation,
        response_processing,
        synthesis_preparation,
    )
    from .discovery_handlers import (
        asset_creation_completion,
        asset_inventory,
        data_import_preparation,
        data_import_validation as data_import_validation_handler,
        discovery_error_handler,
        discovery_finalization,
        discovery_initialization,
    )

    handlers = {
        # Discovery handlers
        "discovery_initialization": discovery_initialization,
        "discovery_finalization": discovery_finalization,
        "discovery_error_handler": discovery_error_handler,
        "asset_creation_completion": asset_creation_completion,
        "asset_inventory": asset_inventory,
        "data_import_preparation": data_import_preparation,
        "data_import_validation": data_import_validation_handler,
        # Assessment handlers
        "assessment_initialization": assessment_initialization,
        "assessment_finalization": assessment_finalization,
        "assessment_error_handler": assessment_error_handler,
        "assessment_completion": assessment_completion,
        "readiness_preparation": readiness_preparation,
        "readiness_scoring": readiness_scoring,
        "complexity_preparation": complexity_preparation,
        "complexity_categorization": complexity_categorization,
        "risk_identification": risk_identification,
        "mitigation_planning": mitigation_planning,
        "recommendation_analysis": recommendation_analysis,
        "roadmap_generation": roadmap_generation,
        # Collection handlers
        "collection_initialization": collection_initialization,
        "collection_finalization": collection_finalization,
        "collection_error_handler": collection_error_handler,
        "collection_rollback_handler": collection_rollback_handler,
        "collection_checkpoint_handler": collection_checkpoint_handler,
        "platform_inventory_creation": platform_inventory_creation,
        "adapter_preparation": adapter_preparation,
        "collection_data_normalization": collection_data_normalization,
        "gap_analysis_preparation": gap_analysis_preparation,
        "gap_prioritization": gap_prioritization,
        "questionnaire_generation": questionnaire_generation,
        "response_processing": response_processing,
        "synthesis_preparation": synthesis_preparation,
        # Planning handlers
        "planning_initialization": planning_initialization,
        "planning_finalization": planning_finalization,
        "planning_error_handler": planning_error_handler,
        "planning_completion": planning_completion,
        "wave_analysis": wave_analysis,
        "wave_optimization": wave_optimization,
        # Execution handlers
        "execution_initialization": execution_initialization,
        "execution_finalization": execution_finalization,
        "execution_error_handler": execution_error_handler,
        "migration_completion": migration_completion,
        "environment_preparation": environment_preparation,
        # Modernize handlers
        "modernize_initialization": modernize_initialization,
        "modernize_finalization": modernize_finalization,
        "modernize_error_handler": modernize_error_handler,
        "modernization_completion": modernization_completion,
        # FinOps handlers
        "finops_initialization": finops_initialization,
        "finops_finalization": finops_finalization,
        "finops_error_handler": finops_error_handler,
        "finops_completion": finops_completion,
        "cost_data_collection": cost_data_collection,
        # Observability handlers
        "observability_initialization": observability_initialization,
        "observability_finalization": observability_finalization,
        "observability_error_handler": observability_error_handler,
        "observability_completion": observability_completion,
        "monitoring_design": monitoring_design,
        # Decommission handlers
        "decommission_initialization": decommission_initialization,
        "decommission_finalization": decommission_finalization,
        "decommission_error_handler": decommission_error_handler,
        "decommission_completion": decommission_completion,
        "impact_analysis": impact_analysis,
        "final_backup": final_backup,
    }

    for name, handler in handlers.items():
        try:
            handler_registry.register_handler(name, handler)
            results["handlers_registered"].append(name)
        except Exception as e:
            logger.error(f"Failed to register handler {name}: {e}")
            results["errors"].append(f"Handler {name}: {str(e)}")

    # Register collection extension handlers
    extension_results = register_collection_extension_handlers(handler_registry)
    results["handlers_registered"].extend(extension_results.get("registered", []))
    results["errors"].extend(extension_results.get("errors", []))
