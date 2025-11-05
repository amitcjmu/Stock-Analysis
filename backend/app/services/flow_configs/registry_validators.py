"""
Validator Registration Module
Registers all validators with the validator registry
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def register_all_validators(validator_registry, results: Dict[str, Any]) -> None:
    """Register all validators with the validator registry"""
    from .additional_validators import (
        alerting_validation,
        architecture_validation,
        budget_validation,
        capacity_validation,
        cost_validation,
        data_migration_validation,
        decommission_validation,
        dependency_validation,
        execution_validation,
        logging_validation,
        modernization_validation,
        monitoring_validation,
        optimization_validation,
        post_migration_validation,
        pre_migration_validation,
        resource_validation,
        shutdown_validation,
        timeline_validation,
        wave_validation,
    )
    from .assessment_validators import (
        assessment_validation,
        complexity_validation,
        inventory_completeness,
        mitigation_validation,
        recommendation_validation,
        risk_validation,
        roadmap_validation,
        score_validation,
    )
    from .collection_validators import (
        collection_validation,
        completeness_validation,
        credential_validation,
        data_quality_validation,
        final_validation,
        gap_validation,
        platform_validation,
        response_validation,
        sixr_impact_validation,
        sixr_readiness_validation,
    )
    from .discovery_validators import (
        asset_validation,
        circular_dependency_check,
        cleansing_validation,
        dependency_validation as discovery_dependency_validation,
        field_mapping_validation,
        inventory_validation,
        mapping_completeness,
    )

    validators = {
        # Discovery validators
        "field_mapping_validation": field_mapping_validation,
        "asset_validation": asset_validation,
        "inventory_validation": inventory_validation,
        "discovery_dependency_validation": discovery_dependency_validation,
        "mapping_completeness": mapping_completeness,
        "cleansing_validation": cleansing_validation,
        "circular_dependency_check": circular_dependency_check,
        # Assessment validators
        "assessment_validation": assessment_validation,
        "complexity_validation": complexity_validation,
        "risk_validation": risk_validation,
        "recommendation_validation": recommendation_validation,
        "inventory_completeness": inventory_completeness,
        "score_validation": score_validation,
        "mitigation_validation": mitigation_validation,
        "roadmap_validation": roadmap_validation,
        # Collection validators
        "platform_validation": platform_validation,
        "credential_validation": credential_validation,
        "collection_validation": collection_validation,
        "data_quality_validation": data_quality_validation,
        "gap_validation": gap_validation,
        "sixr_impact_validation": sixr_impact_validation,
        "response_validation": response_validation,
        "completeness_validation": completeness_validation,
        "final_validation": final_validation,
        "sixr_readiness_validation": sixr_readiness_validation,
        # Planning validators
        "wave_validation": wave_validation,
        "resource_validation": resource_validation,
        # Execution validators
        "pre_migration_validation": pre_migration_validation,
        "execution_validation": execution_validation,
        "post_migration_validation": post_migration_validation,
        # Modernize validators
        "modernization_validation": modernization_validation,
        "architecture_validation": architecture_validation,
        # FinOps validators
        "cost_validation": cost_validation,
        "optimization_validation": optimization_validation,
        "budget_validation": budget_validation,
        # Observability validators
        "monitoring_validation": monitoring_validation,
        "logging_validation": logging_validation,
        "alerting_validation": alerting_validation,
        # Decommission validators
        "decommission_validation": decommission_validation,
        "data_migration_validation": data_migration_validation,
        "shutdown_validation": shutdown_validation,
        # Common validators
        "dependency_validation": dependency_validation,
        "timeline_validation": timeline_validation,
        "capacity_validation": capacity_validation,
    }

    for name, validator in validators.items():
        try:
            validator_registry.register_validator(name, validator)
            results["validators_registered"].append(name)
        except Exception as e:
            logger.error(f"Failed to register validator {name}: {e}")
            results["errors"].append(f"Validator {name}: {str(e)}")
