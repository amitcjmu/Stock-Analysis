"""
Assessment Flow Validators
MFO-044: Implement Assessment-specific validators

Validators for assessment, complexity, risk, and recommendation validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def assessment_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate assessment inputs
    
    Ensures:
    - Asset inventory is complete
    - Assessment criteria are valid
    - All required data is present
    """
    try:
        asset_inventory = phase_input.get("asset_inventory")
        assessment_criteria = phase_input.get("assessment_criteria")
        
        errors = []
        warnings = []
        
        # Validate asset inventory
        if not asset_inventory:
            errors.append("Missing asset inventory")
        elif isinstance(asset_inventory, dict):
            # Check for required inventory sections
            required_sections = ["servers", "applications", "databases"]
            missing_sections = [s for s in required_sections if s not in asset_inventory]
            if missing_sections:
                warnings.append(f"Missing inventory sections: {', '.join(missing_sections)}")
            
            # Check if inventory has assets
            total_assets = sum(
                len(items) if isinstance(items, list) else 0 
                for items in asset_inventory.values()
            )
            if total_assets == 0:
                errors.append("Asset inventory is empty")
        
        # Validate assessment criteria
        if not assessment_criteria:
            errors.append("Missing assessment criteria")
        elif isinstance(assessment_criteria, dict):
            # Check for required criteria
            required_criteria = ["technical", "business", "operational"]
            missing_criteria = [c for c in required_criteria if c not in assessment_criteria]
            if missing_criteria:
                warnings.append(f"Missing assessment criteria: {', '.join(missing_criteria)}")
            
            # Validate scoring weights
            if "scoring_weights" in assessment_criteria:
                weights = assessment_criteria["scoring_weights"]
                if isinstance(weights, dict):
                    total_weight = sum(weights.values())
                    if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                        warnings.append(f"Scoring weights don't sum to 1.0: {total_weight}")
        
        # Check for optional but recommended inputs
        business_priorities = phase_input.get("business_priorities")
        if not business_priorities:
            warnings.append("No business priorities provided - using default priorities")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "asset_count": sum(
                len(items) if isinstance(items, list) else 0 
                for items in asset_inventory.values()
            ) if isinstance(asset_inventory, dict) else 0,
            "criteria_count": len(assessment_criteria) if isinstance(assessment_criteria, dict) else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Assessment validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def complexity_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate complexity analysis inputs
    
    Ensures:
    - Readiness scores are available
    - Complexity rules are defined
    - Scores are within valid ranges
    """
    try:
        readiness_scores = phase_input.get("readiness_scores")
        complexity_rules = phase_input.get("complexity_rules")
        
        errors = []
        warnings = []
        
        # Validate readiness scores
        if not readiness_scores:
            errors.append("Missing readiness scores from previous phase")
        elif isinstance(readiness_scores, dict):
            # Check score format and ranges
            for asset_id, scores in readiness_scores.items():
                if not isinstance(scores, dict):
                    errors.append(f"Invalid score format for asset {asset_id}")
                    continue
                
                # Validate score ranges (0-1)
                for dimension, score in scores.items():
                    if not isinstance(score, (int, float)):
                        errors.append(f"Invalid score type for {asset_id}.{dimension}")
                    elif not 0 <= score <= 1:
                        errors.append(f"Score out of range for {asset_id}.{dimension}: {score}")
        
        # Validate complexity rules
        if not complexity_rules:
            errors.append("Missing complexity rules")
        elif isinstance(complexity_rules, dict):
            # Check for required rule categories
            required_rules = ["technical_debt", "dependencies", "data_volume"]
            missing_rules = [r for r in required_rules if r not in complexity_rules]
            if missing_rules:
                warnings.append(f"Missing complexity rules: {', '.join(missing_rules)}")
            
            # Validate rule thresholds
            for rule_name, rule_config in complexity_rules.items():
                if isinstance(rule_config, dict) and "thresholds" in rule_config:
                    thresholds = rule_config["thresholds"]
                    if not all(k in thresholds for k in ["low", "medium", "high"]):
                        warnings.append(f"Incomplete thresholds for rule: {rule_name}")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "asset_count": len(readiness_scores) if isinstance(readiness_scores, dict) else 0,
            "rule_count": len(complexity_rules) if isinstance(complexity_rules, dict) else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Complexity validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def risk_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate risk assessment inputs
    
    Ensures:
    - Complexity scores are available
    - Risk matrix is properly defined
    - Risk categories are complete
    """
    try:
        complexity_scores = phase_input.get("complexity_scores")
        risk_matrix = phase_input.get("risk_matrix")
        
        errors = []
        warnings = []
        
        # Validate complexity scores
        if not complexity_scores:
            errors.append("Missing complexity scores from previous phase")
        elif isinstance(complexity_scores, dict):
            # Validate score format
            for asset_id, score_data in complexity_scores.items():
                if not isinstance(score_data, dict):
                    errors.append(f"Invalid complexity score format for asset {asset_id}")
                elif "complexity_level" not in score_data:
                    errors.append(f"Missing complexity level for asset {asset_id}")
                elif score_data["complexity_level"] not in ["low", "medium", "high", "very_high"]:
                    errors.append(f"Invalid complexity level for asset {asset_id}: {score_data['complexity_level']}")
        
        # Validate risk matrix
        if not risk_matrix:
            errors.append("Missing risk matrix")
        elif isinstance(risk_matrix, dict):
            # Check matrix structure
            required_dimensions = ["probability", "impact"]
            for dimension in required_dimensions:
                if dimension not in risk_matrix:
                    errors.append(f"Risk matrix missing dimension: {dimension}")
            
            # Validate risk categories
            if "categories" in risk_matrix:
                categories = risk_matrix["categories"]
                required_categories = ["technical", "business", "operational", "security"]
                missing_categories = [c for c in required_categories if c not in categories]
                if missing_categories:
                    warnings.append(f"Missing risk categories: {', '.join(missing_categories)}")
            
            # Validate scoring method
            if "scoring_method" not in risk_matrix:
                warnings.append("No risk scoring method defined - using default")
        
        # Check for optional risk data
        if not phase_input.get("historical_data"):
            warnings.append("No historical data provided for risk calibration")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "asset_count": len(complexity_scores) if isinstance(complexity_scores, dict) else 0,
            "risk_categories": len(risk_matrix.get("categories", {})) if isinstance(risk_matrix, dict) else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Risk validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def recommendation_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate recommendation generation inputs
    
    Ensures:
    - Risk scores are available
    - Business priorities are defined
    - Constraints are valid
    """
    try:
        risk_scores = phase_input.get("risk_scores")
        business_priorities = phase_input.get("business_priorities")
        
        errors = []
        warnings = []
        
        # Validate risk scores
        if not risk_scores:
            errors.append("Missing risk scores from previous phase")
        elif isinstance(risk_scores, dict):
            # Check risk score format
            for asset_id, risk_data in risk_scores.items():
                if not isinstance(risk_data, dict):
                    errors.append(f"Invalid risk score format for asset {asset_id}")
                elif "overall_risk" not in risk_data:
                    errors.append(f"Missing overall risk score for asset {asset_id}")
                elif "mitigation_strategies" not in risk_data:
                    warnings.append(f"No mitigation strategies for asset {asset_id}")
        
        # Validate business priorities
        if not business_priorities:
            errors.append("Missing business priorities")
        elif isinstance(business_priorities, dict):
            # Check priority structure
            required_priorities = ["cost_optimization", "time_to_market", "risk_minimization"]
            for priority in required_priorities:
                if priority not in business_priorities:
                    warnings.append(f"Missing business priority: {priority}")
                elif not isinstance(business_priorities[priority], (int, float)):
                    errors.append(f"Invalid priority value for {priority}")
                elif not 0 <= business_priorities[priority] <= 10:
                    errors.append(f"Priority value out of range for {priority}: {business_priorities[priority]}")
        
        # Validate optional constraints
        cost_constraints = phase_input.get("cost_constraints")
        if cost_constraints:
            if not isinstance(cost_constraints, dict):
                warnings.append("Invalid cost constraints format")
            elif "budget_limit" in cost_constraints:
                if not isinstance(cost_constraints["budget_limit"], (int, float)) or cost_constraints["budget_limit"] <= 0:
                    warnings.append("Invalid budget limit")
        
        timeline_preferences = phase_input.get("timeline_preferences")
        if timeline_preferences:
            if not isinstance(timeline_preferences, dict):
                warnings.append("Invalid timeline preferences format")
            elif "target_completion" in timeline_preferences:
                # Could validate date format here
                pass
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "asset_count": len(risk_scores) if isinstance(risk_scores, dict) else 0,
            "priority_count": len(business_priorities) if isinstance(business_priorities, dict) else 0,
            "has_constraints": bool(cost_constraints or timeline_preferences)
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Recommendation validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def inventory_completeness(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate inventory completeness for assessment
    
    Ensures inventory has sufficient data for assessment
    """
    try:
        asset_inventory = phase_input.get("asset_inventory")
        errors = []
        warnings = []
        
        if not asset_inventory:
            errors.append("No asset inventory provided")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        # Check minimum asset requirements
        total_assets = 0
        asset_quality_issues = []
        
        for category, assets in asset_inventory.items():
            if not isinstance(assets, list):
                warnings.append(f"Invalid format for category: {category}")
                continue
            
            total_assets += len(assets)
            
            # Check asset data quality
            for idx, asset in enumerate(assets):
                if not isinstance(asset, dict):
                    asset_quality_issues.append(f"{category}[{idx}]: Not a dictionary")
                    continue
                
                # Check for assessment-required fields
                required_fields = ["asset_id", "name", "type", "environment"]
                missing_fields = [f for f in required_fields if f not in asset]
                if missing_fields:
                    asset_quality_issues.append(
                        f"{category}[{idx}]: Missing fields {missing_fields}"
                    )
        
        # Aggregate quality issues
        if len(asset_quality_issues) > 10:
            warnings.append(f"Found {len(asset_quality_issues)} asset quality issues (showing first 10)")
            warnings.extend(asset_quality_issues[:10])
        else:
            warnings.extend(asset_quality_issues)
        
        # Check minimum asset count
        if total_assets == 0:
            errors.append("No assets found in inventory")
        elif total_assets < 5:
            warnings.append(f"Low asset count ({total_assets}) may affect assessment accuracy")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "total_assets": total_assets,
            "categories": list(asset_inventory.keys()),
            "quality_issues": len(asset_quality_issues)
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Inventory completeness validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def score_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generic score validation
    
    Validates any scoring data for proper format and ranges
    """
    try:
        errors = []
        warnings = []
        
        # Look for any score-like data in the input
        score_fields = [k for k in phase_input.keys() if "score" in k.lower()]
        
        for field in score_fields:
            scores = phase_input[field]
            
            if isinstance(scores, dict):
                for key, value in scores.items():
                    if isinstance(value, dict) and any("score" in k for k in value.keys()):
                        # Validate nested scores
                        for score_key, score_value in value.items():
                            if "score" in score_key:
                                if not isinstance(score_value, (int, float)):
                                    errors.append(f"Invalid score type in {field}.{key}.{score_key}")
                                elif not 0 <= score_value <= 1:
                                    warnings.append(f"Score out of typical range in {field}.{key}.{score_key}: {score_value}")
                    elif isinstance(value, (int, float)):
                        # Direct score value
                        if not 0 <= value <= 1:
                            warnings.append(f"Score out of typical range in {field}.{key}: {value}")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "score_fields_found": len(score_fields),
            "validation_performed": True
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Score validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def mitigation_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate risk mitigation strategies
    
    Ensures mitigation plans are complete and actionable
    """
    try:
        risk_scores = phase_input.get("risk_scores", {})
        errors = []
        warnings = []
        
        high_risk_without_mitigation = []
        
        for asset_id, risk_data in risk_scores.items():
            if not isinstance(risk_data, dict):
                continue
            
            overall_risk = risk_data.get("overall_risk", 0)
            mitigation_strategies = risk_data.get("mitigation_strategies", [])
            
            # Check if high-risk items have mitigation
            if overall_risk > 0.7 and not mitigation_strategies:
                high_risk_without_mitigation.append(asset_id)
            
            # Validate mitigation strategy structure
            for strategy in mitigation_strategies:
                if not isinstance(strategy, dict):
                    warnings.append(f"Invalid mitigation strategy format for {asset_id}")
                elif not all(k in strategy for k in ["action", "impact", "effort"]):
                    warnings.append(f"Incomplete mitigation strategy for {asset_id}")
        
        if high_risk_without_mitigation:
            errors.append(
                f"High-risk assets without mitigation: {', '.join(high_risk_without_mitigation[:5])}"
                + (f" and {len(high_risk_without_mitigation) - 5} more" if len(high_risk_without_mitigation) > 5 else "")
            )
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "assets_with_mitigation": sum(
                1 for r in risk_scores.values() 
                if isinstance(r, dict) and r.get("mitigation_strategies")
            ),
            "high_risk_count": len(high_risk_without_mitigation)
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Mitigation validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }


async def roadmap_validation(
    phase_input: Dict[str, Any],
    flow_state: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate generated roadmap
    
    Ensures roadmap is complete and executable
    """
    try:
        recommendations = phase_input.get("recommendations", {})
        errors = []
        warnings = []
        
        # Check for roadmap in recommendations
        roadmap = recommendations.get("migration_roadmap")
        
        if not roadmap:
            errors.append("No migration roadmap generated")
        elif isinstance(roadmap, dict):
            # Validate roadmap structure
            required_elements = ["phases", "timeline", "resource_requirements"]
            missing_elements = [e for e in required_elements if e not in roadmap]
            
            if missing_elements:
                errors.append(f"Roadmap missing required elements: {', '.join(missing_elements)}")
            
            # Validate phases
            if "phases" in roadmap:
                phases = roadmap["phases"]
                if not isinstance(phases, list) or len(phases) == 0:
                    errors.append("Roadmap has no phases defined")
                else:
                    for idx, phase in enumerate(phases):
                        if not isinstance(phase, dict):
                            warnings.append(f"Invalid phase format at index {idx}")
                        elif not all(k in phase for k in ["name", "duration", "assets"]):
                            warnings.append(f"Incomplete phase definition at index {idx}")
            
            # Validate timeline
            if "timeline" in roadmap:
                timeline = roadmap["timeline"]
                if not isinstance(timeline, dict):
                    warnings.append("Invalid timeline format")
                elif "total_duration" not in timeline:
                    warnings.append("Timeline missing total duration")
        
        metadata = {
            "validated_at": datetime.utcnow().isoformat(),
            "has_roadmap": bool(roadmap),
            "phase_count": len(roadmap.get("phases", [])) if isinstance(roadmap, dict) else 0
        }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Roadmap validation error: {e}")
        return {
            "valid": False,
            "errors": [f"Validation exception: {str(e)}"],
            "warnings": []
        }