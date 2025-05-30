"""
Analysis Tools Handler
Handles CMDB analysis and parameter scoring tools.
"""

import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AnalysisToolsHandler:
    """Handles analysis tools with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            # Try to import dependencies
            from app.services.field_mapper_modular import FieldMapperService
            from app.services.sixr_engine import SixRDecisionEngine
            
            self.field_mapper = FieldMapperService()
            self.decision_engine = SixRDecisionEngine()
            self.service_available = True
            logger.info("Analysis tools handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Analysis tools services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def analyze_cmdb_data(self, application_data: Dict[str, Any], analysis_focus: str = "all") -> Dict[str, Any]:
        """Analyze CMDB data to extract 6R-relevant insights."""
        try:
            if not self.service_available:
                return self._fallback_cmdb_analysis(application_data)
            
            insights = {
                "technical_insights": {},
                "business_insights": {},
                "compliance_insights": {},
                "risk_indicators": [],
                "recommended_parameters": {}
            }
            
            # Technical Analysis
            if analysis_focus in ["technical", "all"]:
                insights["technical_insights"] = self._analyze_technical_aspects(application_data)
            
            # Business Analysis
            if analysis_focus in ["business", "all"]:
                insights["business_insights"] = self._analyze_business_aspects(application_data)
            
            # Compliance Analysis
            if analysis_focus in ["compliance", "all"]:
                insights["compliance_insights"] = self._analyze_compliance_aspects(application_data)
            
            # Risk Analysis
            insights["risk_indicators"] = self._identify_risk_indicators(application_data)
            
            # Parameter Recommendations
            insights["recommended_parameters"] = self._recommend_initial_parameters(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"CMDB analysis failed: {e}")
            return self._fallback_cmdb_analysis(application_data)
    
    def score_parameters(self, parameters: Dict[str, float], strategy: str) -> Dict[str, Any]:
        """Score parameter configuration for a given strategy."""
        try:
            if not self.service_available:
                return self._fallback_parameter_scoring(parameters, strategy)
            
            # Calculate individual parameter scores
            scoring_results = {
                "parameter_scores": {},
                "overall_score": 0.0,
                "strategy_alignment": 0.0,
                "confidence_level": 0.0,
                "recommendations": []
            }
            
            # Score each parameter based on strategy
            for param, value in parameters.items():
                score = self._score_parameter_for_strategy(param, value, strategy)
                scoring_results["parameter_scores"][param] = score
            
            # Calculate overall score
            if scoring_results["parameter_scores"]:
                scoring_results["overall_score"] = sum(scoring_results["parameter_scores"].values()) / len(scoring_results["parameter_scores"])
            
            # Calculate strategy alignment
            scoring_results["strategy_alignment"] = self._calculate_strategy_alignment(parameters, strategy)
            
            # Calculate confidence level
            scoring_results["confidence_level"] = min(scoring_results["overall_score"] / 5.0, 1.0)
            
            # Generate recommendations
            scoring_results["recommendations"] = self._generate_parameter_recommendations(parameters, strategy)
            
            return scoring_results
            
        except Exception as e:
            logger.error(f"Parameter scoring failed: {e}")
            return self._fallback_parameter_scoring(parameters, strategy)
    
    def _analyze_technical_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical complexity indicators."""
        technical_insights = {
            "complexity_score": 3.0,
            "technology_stack": [],
            "architecture_patterns": [],
            "integration_points": 0,
            "performance_characteristics": {}
        }
        
        # Analyze technology stack
        tech_info = data.get("technology", data.get("tech_stack", ""))
        if isinstance(tech_info, str):
            technical_insights["technology_stack"] = [tech_info]
        elif isinstance(tech_info, list):
            technical_insights["technology_stack"] = tech_info
        
        # Calculate complexity score based on technology
        complexity_indicators = 0
        for tech in technical_insights["technology_stack"]:
            if any(legacy in str(tech).lower() for legacy in ["mainframe", "cobol", "fortran", "legacy"]):
                complexity_indicators += 2
            elif any(modern in str(tech).lower() for modern in ["java", "python", ".net", "node"]):
                complexity_indicators += 1
            elif any(cloud in str(tech).lower() for cloud in ["kubernetes", "docker", "microservice"]):
                complexity_indicators -= 1
        
        technical_insights["complexity_score"] = max(1, min(5, 3 + complexity_indicators * 0.5))
        
        return technical_insights
    
    def _analyze_business_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business value and criticality indicators."""
        business_insights = {
            "business_value": 3.0,
            "criticality_level": "medium",
            "user_base_size": 0,
            "revenue_impact": "unknown",
            "operational_importance": "standard"
        }
        
        # Analyze criticality
        criticality = data.get("business_criticality", data.get("criticality", "medium"))
        if criticality in ["high", "critical", "mission-critical"]:
            business_insights["business_value"] = 5.0
            business_insights["criticality_level"] = "high"
        elif criticality in ["low", "non-critical"]:
            business_insights["business_value"] = 2.0
            business_insights["criticality_level"] = "low"
        
        # Analyze user base
        users = data.get("users", data.get("user_count", 0))
        if isinstance(users, (int, float)):
            business_insights["user_base_size"] = users
            if users > 1000:
                business_insights["business_value"] = min(5.0, business_insights["business_value"] + 1.0)
        
        return business_insights
    
    def _analyze_compliance_aspects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance and regulatory requirements."""
        compliance_insights = {
            "compliance_requirements": [],
            "data_sensitivity": "standard",
            "regulatory_frameworks": [],
            "security_classification": "internal"
        }
        
        # Check for compliance indicators
        compliance_keywords = ["gdpr", "hipaa", "pci", "sox", "iso", "compliance", "regulation"]
        for key, value in data.items():
            if any(keyword in str(key).lower() or keyword in str(value).lower() for keyword in compliance_keywords):
                compliance_insights["compliance_requirements"].append(str(value))
        
        # Determine data sensitivity
        sensitive_keywords = ["personal", "financial", "medical", "sensitive", "confidential"]
        if any(keyword in str(data).lower() for keyword in sensitive_keywords):
            compliance_insights["data_sensitivity"] = "high"
        
        return compliance_insights
    
    def _identify_risk_indicators(self, data: Dict[str, Any]) -> List[str]:
        """Identify potential risks based on application data."""
        risks = []
        
        # Technology risks
        tech_info = str(data.get("technology", "")).lower()
        if any(legacy in tech_info for legacy in ["mainframe", "cobol", "legacy"]):
            risks.append("Legacy technology stack migration complexity")
        
        # Data risks
        if "database" in data or "data" in data:
            risks.append("Data migration complexity and integrity concerns")
        
        # Integration risks
        if "integration" in str(data).lower() or "api" in str(data).lower():
            risks.append("Integration dependencies and compatibility issues")
        
        # Scale risks
        users = data.get("users", 0)
        if isinstance(users, (int, float)) and users > 10000:
            risks.append("High user volume performance impact")
        
        return risks if risks else ["Standard migration risks"]
    
    def _recommend_initial_parameters(self, insights: Dict[str, Any]) -> Dict[str, float]:
        """Recommend initial 6R parameters based on insights."""
        parameters = {
            "business_value": 3.0,
            "technical_complexity": 3.0,
            "migration_urgency": 3.0,
            "compliance_requirements": 3.0,
            "cost_sensitivity": 3.0,
            "risk_tolerance": 3.0,
            "innovation_priority": 3.0
        }
        
        # Adjust based on technical insights
        if insights.get("technical_insights"):
            parameters["technical_complexity"] = insights["technical_insights"].get("complexity_score", 3.0)
        
        # Adjust based on business insights
        if insights.get("business_insights"):
            parameters["business_value"] = insights["business_insights"].get("business_value", 3.0)
        
        # Adjust based on compliance
        if insights.get("compliance_insights", {}).get("compliance_requirements"):
            parameters["compliance_requirements"] = 4.0
        
        # Adjust based on risks
        risk_count = len(insights.get("risk_indicators", []))
        if risk_count > 3:
            parameters["risk_tolerance"] = 2.0
        elif risk_count > 1:
            parameters["risk_tolerance"] = 2.5
        
        return parameters
    
    def _score_parameter_for_strategy(self, param: str, value: float, strategy: str) -> float:
        """Score individual parameter for strategy alignment."""
        strategy_preferences = {
            "rehost": {
                "technical_complexity": {"preferred": [1, 2, 3], "weight": 0.8},
                "migration_urgency": {"preferred": [4, 5], "weight": 0.9},
                "cost_sensitivity": {"preferred": [4, 5], "weight": 0.7}
            },
            "replatform": {
                "technical_complexity": {"preferred": [2, 3, 4], "weight": 0.7},
                "innovation_priority": {"preferred": [3, 4], "weight": 0.6},
                "business_value": {"preferred": [3, 4, 5], "weight": 0.8}
            },
            "refactor": {
                "technical_complexity": {"preferred": [3, 4, 5], "weight": 0.9},
                "innovation_priority": {"preferred": [4, 5], "weight": 0.9},
                "business_value": {"preferred": [4, 5], "weight": 0.8}
            }
        }
        
        if strategy in strategy_preferences and param in strategy_preferences[strategy]:
            pref = strategy_preferences[strategy][param]
            if value in pref["preferred"]:
                return 5.0 * pref["weight"]
            else:
                return 3.0 * pref["weight"]
        
        return 3.0  # Default neutral score
    
    def _calculate_strategy_alignment(self, parameters: Dict[str, float], strategy: str) -> float:
        """Calculate overall alignment with strategy."""
        total_score = 0.0
        param_count = 0
        
        for param, value in parameters.items():
            score = self._score_parameter_for_strategy(param, value, strategy)
            total_score += score
            param_count += 1
        
        return (total_score / param_count) / 5.0 if param_count > 0 else 0.5
    
    def _generate_parameter_recommendations(self, parameters: Dict[str, float], strategy: str) -> List[str]:
        """Generate recommendations for parameter improvements."""
        recommendations = []
        
        if strategy == "rehost" and parameters.get("technical_complexity", 3) > 3:
            recommendations.append("Consider reducing technical complexity assessment for rehost strategy")
        
        if strategy == "refactor" and parameters.get("innovation_priority", 3) < 4:
            recommendations.append("Increase innovation priority for refactor strategy")
        
        if parameters.get("business_value", 3) < 3:
            recommendations.append("Reassess business value - may be underestimated")
        
        return recommendations if recommendations else ["Parameter configuration looks reasonable"]
    
    # Fallback methods
    def _fallback_cmdb_analysis(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback CMDB analysis when services unavailable."""
        return {
            "technical_insights": {"complexity_score": 3.0, "technology_stack": ["unknown"]},
            "business_insights": {"business_value": 3.0, "criticality_level": "medium"},
            "compliance_insights": {"compliance_requirements": [], "data_sensitivity": "standard"},
            "risk_indicators": ["Standard migration risks"],
            "recommended_parameters": {
                "business_value": 3.0,
                "technical_complexity": 3.0,
                "migration_urgency": 3.0
            },
            "fallback_mode": True
        }
    
    def _fallback_parameter_scoring(self, parameters: Dict[str, float], strategy: str) -> Dict[str, Any]:
        """Fallback parameter scoring when services unavailable."""
        return {
            "parameter_scores": {param: 3.0 for param in parameters.keys()},
            "overall_score": 3.0,
            "strategy_alignment": 0.6,
            "confidence_level": 0.6,
            "recommendations": ["Analysis performed in fallback mode"],
            "fallback_mode": True
        } 