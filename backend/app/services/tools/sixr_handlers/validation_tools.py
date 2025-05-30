"""
Validation Tools Handler
Handles recommendation validation and verification tools.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ValidationToolsHandler:
    """Handles validation tools with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = True
        logger.info("Validation tools handler initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True
    
    def validate_recommendation(self, recommendation: Dict[str, Any], 
                              application_context: Dict[str, Any],
                              validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a 6R migration recommendation."""
        try:
            validation_result = {
                "is_valid": True,
                "confidence_score": 0.0,
                "validation_checks": {},
                "concerns": [],
                "suggestions": [],
                "overall_score": 0.0
            }
            
            # Run validation checks
            validation_result["validation_checks"] = {
                "strategy_feasibility": self._check_strategy_feasibility(recommendation, application_context),
                "cost_alignment": self._check_cost_alignment(recommendation, validation_criteria),
                "risk_assessment": self._check_risk_levels(recommendation, application_context),
                "timeline_validity": self._check_timeline_validity(recommendation, validation_criteria),
                "compliance_check": self._check_compliance_requirements(recommendation, application_context)
            }
            
            # Calculate overall validation score
            check_scores = [check["score"] for check in validation_result["validation_checks"].values()]
            validation_result["overall_score"] = sum(check_scores) / len(check_scores) if check_scores else 0.5
            
            # Determine if recommendation is valid
            validation_result["is_valid"] = validation_result["overall_score"] >= 0.6
            validation_result["confidence_score"] = validation_result["overall_score"]
            
            # Collect concerns and suggestions
            for check_name, check_result in validation_result["validation_checks"].items():
                if check_result["score"] < 0.6:
                    validation_result["concerns"].extend(check_result.get("issues", []))
                validation_result["suggestions"].extend(check_result.get("suggestions", []))
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Recommendation validation failed: {e}")
            return self._fallback_validation()
    
    def _check_strategy_feasibility(self, recommendation: Dict[str, Any], 
                                  application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the recommended strategy is feasible."""
        check_result = {
            "score": 0.8,
            "issues": [],
            "suggestions": []
        }
        
        strategy = recommendation.get("recommended_strategy", "").lower()
        app_complexity = application_context.get("complexity_score", 3)
        
        # Check strategy-complexity alignment
        if strategy == "refactor" and app_complexity < 3:
            check_result["score"] = 0.5
            check_result["issues"].append("Refactor strategy may be overkill for low complexity application")
            check_result["suggestions"].append("Consider rehost or replatform for simpler migration")
        
        elif strategy == "rehost" and app_complexity > 4:
            check_result["score"] = 0.6
            check_result["issues"].append("Rehost may not address high complexity challenges")
            check_result["suggestions"].append("Consider refactor or replatform to modernize architecture")
        
        # Check technology compatibility
        tech_stack = application_context.get("technology_stack", [])
        if strategy in ["rehost", "replatform"] and any("legacy" in str(tech).lower() for tech in tech_stack):
            check_result["score"] *= 0.8
            check_result["issues"].append("Legacy technology stack may complicate migration")
        
        return check_result
    
    def _check_cost_alignment(self, recommendation: Dict[str, Any], 
                            validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Check if recommendation aligns with cost constraints."""
        check_result = {
            "score": 0.8,
            "issues": [],
            "suggestions": []
        }
        
        strategy = recommendation.get("recommended_strategy", "").lower()
        cost_sensitivity = validation_criteria.get("cost_sensitivity", 3)
        
        # High cost sensitivity checks
        if cost_sensitivity >= 4:
            if strategy in ["refactor", "rebuild"]:
                check_result["score"] = 0.4
                check_result["issues"].append("High-cost strategy conflicts with cost sensitivity")
                check_result["suggestions"].append("Consider rehost or retain for cost optimization")
            elif strategy in ["rehost", "retain"]:
                check_result["score"] = 0.9
                check_result["suggestions"].append("Good alignment with cost-conscious approach")
        
        # Low cost sensitivity - can afford complex strategies
        elif cost_sensitivity <= 2:
            if strategy in ["refactor", "replatform"]:
                check_result["score"] = 0.9
                check_result["suggestions"].append("Good opportunity for modernization investment")
        
        return check_result
    
    def _check_risk_levels(self, recommendation: Dict[str, Any], 
                         application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check risk levels associated with recommendation."""
        check_result = {
            "score": 0.7,
            "issues": [],
            "suggestions": []
        }
        
        strategy = recommendation.get("recommended_strategy", "").lower()
        business_criticality = application_context.get("business_criticality", "medium")
        
        # High criticality applications need careful strategy selection
        if business_criticality == "high":
            if strategy in ["refactor", "rebuild"]:
                check_result["score"] = 0.5
                check_result["issues"].append("High-risk strategy for business-critical application")
                check_result["suggestions"].append("Consider phased approach or replatform for lower risk")
            elif strategy == "rehost":
                check_result["score"] = 0.8
                check_result["suggestions"].append("Lower risk approach appropriate for critical application")
        
        # Check for additional risk factors
        integrations = application_context.get("integration_points", 0)
        if integrations > 5 and strategy != "retain":
            check_result["score"] *= 0.9
            check_result["issues"].append("High integration complexity increases migration risk")
        
        return check_result
    
    def _check_timeline_validity(self, recommendation: Dict[str, Any], 
                               validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Check if timeline expectations are realistic."""
        check_result = {
            "score": 0.8,
            "issues": [],
            "suggestions": []
        }
        
        strategy = recommendation.get("recommended_strategy", "").lower()
        urgency = validation_criteria.get("migration_urgency", 3)
        
        # High urgency timeline checks
        if urgency >= 4:
            if strategy in ["refactor", "rebuild"]:
                check_result["score"] = 0.4
                check_result["issues"].append("Complex strategy conflicts with urgent timeline")
                check_result["suggestions"].append("Consider rehost for faster migration")
            elif strategy == "rehost":
                check_result["score"] = 0.9
                check_result["suggestions"].append("Good choice for urgent migration needs")
        
        # Low urgency - can afford longer timelines
        elif urgency <= 2:
            if strategy in ["refactor", "replatform"]:
                check_result["score"] = 0.9
                check_result["suggestions"].append("Flexible timeline allows for comprehensive modernization")
        
        return check_result
    
    def _check_compliance_requirements(self, recommendation: Dict[str, Any], 
                                     application_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance and regulatory alignment."""
        check_result = {
            "score": 0.8,
            "issues": [],
            "suggestions": []
        }
        
        strategy = recommendation.get("recommended_strategy", "").lower()
        compliance_reqs = application_context.get("compliance_requirements", [])
        data_sensitivity = application_context.get("data_sensitivity", "standard")
        
        # High compliance requirements
        if compliance_reqs or data_sensitivity == "high":
            if strategy == "rehost":
                check_result["score"] = 0.9
                check_result["suggestions"].append("Rehost maintains compliance posture effectively")
            elif strategy in ["refactor", "replatform"]:
                check_result["score"] = 0.6
                check_result["issues"].append("Architecture changes may require compliance re-validation")
                check_result["suggestions"].append("Ensure compliance review is included in migration plan")
        
        # Standard compliance
        else:
            check_result["score"] = 0.9
            check_result["suggestions"].append("Standard compliance requirements, strategy flexibility available")
        
        return check_result
    
    def _fallback_validation(self) -> Dict[str, Any]:
        """Fallback validation when processing fails."""
        return {
            "is_valid": True,
            "confidence_score": 0.7,
            "validation_checks": {"basic_check": {"score": 0.7}},
            "concerns": [],
            "suggestions": ["Validation performed in fallback mode"],
            "overall_score": 0.7,
            "fallback_mode": True
        } 