"""
Execution Engine - Recommendation Validation

Validation logic for recommendation generation phase outputs.
Ensures agent returned proper 6R strategies for all applications (ISSUE-999).
"""

from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_recommendation_structure(
    parsed_result: Dict[str, Any], expected_app_count: int
) -> Dict[str, Any]:
    """
    Validate per-application recommendation structure.

    ISSUE-999: Ensures agent returned proper 6R strategies for all applications.

    Args:
        parsed_result: Parsed JSON from recommendation agent
        expected_app_count: Number of applications that should have recommendations

    Returns:
        Validation summary with counts and issues
    """
    validation = {
        "is_valid": True,
        "applications_with_6r": 0,
        "missing_applications": 0,
        "invalid_strategies": [],
        "missing_fields": [],
    }

    try:
        applications = parsed_result.get("applications", [])
        validation["applications_with_6r"] = len(applications)
        validation["missing_applications"] = max(
            0, expected_app_count - len(applications)
        )

        # Valid 6R strategies per standardized framework
        valid_strategies = {
            "rehost",
            "replatform",
            "refactor",
            "rearchitect",
            "replace",
            "retire",
        }

        # Validate each application recommendation
        required_fields = {
            "application_id",
            "application_name",
            "six_r_strategy",
            "confidence_score",
            "reasoning",
        }

        for i, app_rec in enumerate(applications):
            # Check for missing required fields
            missing = required_fields - set(app_rec.keys())
            if missing:
                validation["missing_fields"].append(
                    {
                        "index": i,
                        "application_id": app_rec.get("application_id"),
                        "missing": list(missing),
                    }
                )
                validation["is_valid"] = False

            # Validate 6R strategy value
            strategy = app_rec.get("six_r_strategy", "").lower()
            if strategy not in valid_strategies:
                validation["invalid_strategies"].append(
                    {
                        "index": i,
                        "application_id": app_rec.get("application_id"),
                        "application_name": app_rec.get("application_name"),
                        "invalid_strategy": strategy,
                    }
                )
                validation["is_valid"] = False

        # Log validation issues
        if not validation["is_valid"]:
            logger.warning(
                f"[ISSUE-999] Recommendation validation issues: "
                f"{len(validation['invalid_strategies'])} invalid strategies, "
                f"{len(validation['missing_fields'])} incomplete recommendations"
            )

        if validation["missing_applications"] > 0:
            logger.warning(
                f"[ISSUE-999] Missing {validation['missing_applications']} "
                f"application recommendations (expected {expected_app_count}, got {len(applications)})"
            )

    except Exception as e:
        logger.error(f"[ISSUE-999] Error validating recommendation structure: {e}")
        validation["is_valid"] = False
        validation["validation_error"] = str(e)

    return validation
