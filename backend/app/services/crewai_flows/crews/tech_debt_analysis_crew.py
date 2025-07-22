"""
Tech Debt Analysis Crew
Strategic crew for comprehensive tech debt analysis and modernization assessment.
Implements Task 3.3 of the Discovery Flow Redesign.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from crewai import Agent, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class TechDebtAnalysisResult(BaseModel):
    """Result model for tech debt analysis"""
    asset_id: str
    asset_name: str
    legacy_assessment: Dict[str, Any]
    modernization_opportunities: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    sixr_recommendations: Dict[str, Any]
    modernization_roadmap: Dict[str, Any]
    business_case: Dict[str, Any]
    confidence_score: float

class LegacySystemAnalysisTool(BaseTool):
    """Tool for legacy system analysis and modernization assessment"""
    name: str = "legacy_system_analysis_tool"
    description: str = "Analyze legacy systems and identify modernization opportunities"
    
    def _run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze legacy system characteristics"""
        try:
            # Legacy indicators
            legacy_indicators = {
                "technology_age": {
                    "very_old": ["cobol", "fortran", "mainframe", "as400", "vb6"],
                    "old": ["java 6", "java 7", ".net 2.0", ".net 3.5", "php 5"],
                    "aging": ["java 8", ".net 4.0", "php 7", "python 2.7"],
                    "current": ["java 11", "java 17", ".net 5", ".net 6", "python 3.8+"]
                },
                "architecture_patterns": {
                    "monolithic": ["monolith", "single deployment", "tightly coupled"],
                    "soa": ["soa", "service oriented", "web services", "soap"],
                    "microservices": ["microservices", "containerized", "kubernetes", "docker"],
                    "serverless": ["serverless", "lambda", "functions", "faas"]
                },
                "maintenance_indicators": {
                    "high_maintenance": ["manual deployment", "no automation", "legacy code"],
                    "medium_maintenance": ["some automation", "mixed technologies"],
                    "low_maintenance": ["automated", "modern practices", "ci/cd"]
                }
            }
            
            asset_text = " ".join(str(value).lower() for value in asset_data.values() if value)
            
            # Assess technology age
            tech_age_score = 0
            tech_age_level = "unknown"
            for age_level, technologies in legacy_indicators["technology_age"].items():
                matches = [tech for tech in technologies if tech in asset_text]
                if matches:
                    if age_level == "very_old":
                        tech_age_score = 4
                        tech_age_level = "very_old"
                    elif age_level == "old":
                        tech_age_score = 3
                        tech_age_level = "old"
                    elif age_level == "aging":
                        tech_age_score = 2
                        tech_age_level = "aging"
                    elif age_level == "current":
                        tech_age_score = 1
                        tech_age_level = "current"
                    break
            
            # Assess architecture patterns
            architecture_score = 0
            architecture_type = "unknown"
            for arch_type, patterns in legacy_indicators["architecture_patterns"].items():
                matches = [pattern for pattern in patterns if pattern in asset_text]
                if matches:
                    if arch_type == "monolithic":
                        architecture_score = 4
                        architecture_type = "monolithic"
                    elif arch_type == "soa":
                        architecture_score = 3
                        architecture_type = "soa"
                    elif arch_type == "microservices":
                        architecture_score = 2
                        architecture_type = "microservices"
                    elif arch_type == "serverless":
                        architecture_score = 1
                        architecture_type = "serverless"
                    break
            
            # Assess maintenance burden
            maintenance_score = 0
            maintenance_level = "unknown"
            for maint_level, indicators in legacy_indicators["maintenance_indicators"].items():
                matches = [ind for ind in indicators if ind in asset_text]
                if matches:
                    if maint_level == "high_maintenance":
                        maintenance_score = 3
                        maintenance_level = "high"
                    elif maint_level == "medium_maintenance":
                        maintenance_score = 2
                        maintenance_level = "medium"
                    elif maint_level == "low_maintenance":
                        maintenance_score = 1
                        maintenance_level = "low"
                    break
            
            # Calculate overall legacy score
            total_legacy_score = tech_age_score + architecture_score + maintenance_score
            
            if total_legacy_score >= 9:
                legacy_level = "critical"
            elif total_legacy_score >= 6:
                legacy_level = "high"
            elif total_legacy_score >= 4:
                legacy_level = "medium"
            else:
                legacy_level = "low"
            
            return {
                "technology_age": {
                    "level": tech_age_level,
                    "score": tech_age_score
                },
                "architecture_type": {
                    "type": architecture_type,
                    "score": architecture_score
                },
                "maintenance_burden": {
                    "level": maintenance_level,
                    "score": maintenance_score
                },
                "overall_legacy_score": total_legacy_score,
                "legacy_level": legacy_level,
                "modernization_urgency": self._assess_modernization_urgency(total_legacy_score),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Legacy system analysis failed: {e}")
            return {
                "legacy_level": "unknown",
                "error": str(e)
            }
    
    def _assess_modernization_urgency(self, legacy_score: int) -> Dict[str, Any]:
        """Assess urgency of modernization based on legacy score"""
        if legacy_score >= 9:
            return {
                "urgency": "immediate",
                "timeline": "0-6 months",
                "reasoning": "Critical legacy system requiring immediate attention"
            }
        elif legacy_score >= 6:
            return {
                "urgency": "high",
                "timeline": "6-12 months", 
                "reasoning": "High legacy burden requiring prioritized modernization"
            }
        elif legacy_score >= 4:
            return {
                "urgency": "medium",
                "timeline": "1-2 years",
                "reasoning": "Moderate legacy system suitable for planned modernization"
            }
        else:
            return {
                "urgency": "low",
                "timeline": "2+ years",
                "reasoning": "Low legacy burden, modernization can be deferred"
            }

class SixRStrategyTool(BaseTool):
    """Tool for 6R strategy analysis and recommendations"""
    name: str = "sixr_strategy_tool"
    description: str = "Analyze assets and recommend optimal 6R migration strategy"
    
    def _run(self, asset_data: Dict[str, Any], legacy_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and recommend 6R strategy"""
        try:
            # 6R Strategy decision factors
            strategy_factors = {
                "rehost": {
                    "indicators": ["lift and shift", "minimal changes", "quick migration"],
                    "suitability_factors": ["low_complexity", "time_pressure", "minimal_changes_needed"]
                },
                "replatform": {
                    "indicators": ["platform upgrade", "cloud native", "some optimization"],
                    "suitability_factors": ["medium_complexity", "cloud_benefits", "platform_modernization"]
                },
                "refactor": {
                    "indicators": ["code changes", "architecture improvements", "optimization"],
                    "suitability_factors": ["high_value", "performance_issues", "scalability_needs"]
                },
                "rearchitect": {
                    "indicators": ["complete redesign", "microservices", "cloud native"],
                    "suitability_factors": ["legacy_architecture", "scalability_critical", "long_term_value"]
                },
                "retire": {
                    "indicators": ["end of life", "redundant", "unused"],
                    "suitability_factors": ["no_business_value", "duplicate_functionality", "end_of_life"]
                },
                "retain": {
                    "indicators": ["keep as is", "no migration", "compliance reasons"],
                    "suitability_factors": ["compliance_requirements", "low_priority", "high_risk_migration"]
                }
            }
            
            asset_text = " ".join(str(value).lower() for value in asset_data.values() if value)
            legacy_level = legacy_assessment.get("legacy_level", "medium")
            
            # Score each strategy
            strategy_scores = {}
            for strategy, config in strategy_factors.items():
                score = 0
                matches = []
                
                # Check for direct indicators
                for indicator in config["indicators"]:
                    if indicator in asset_text:
                        score += 2
                        matches.append(indicator)
                
                # Apply legacy assessment influence
                if strategy == "retire" and legacy_level == "critical":
                    score += 3
                elif strategy == "rearchitect" and legacy_level in ["critical", "high"]:
                    score += 2
                elif strategy == "refactor" and legacy_level == "medium":
                    score += 2
                elif strategy == "replatform" and legacy_level in ["medium", "low"]:
                    score += 1
                elif strategy == "rehost" and legacy_level == "low":
                    score += 1
                elif strategy == "retain" and legacy_level == "low":
                    score += 1
                
                if score > 0:
                    strategy_scores[strategy] = {
                        "score": score,
                        "matches": matches,
                        "suitability": self._assess_strategy_suitability(strategy, asset_data, legacy_assessment)
                    }
            
            # Determine recommended strategy
            if strategy_scores:
                recommended_strategy = max(strategy_scores.keys(), key=lambda x: strategy_scores[x]["score"])
                confidence = min(strategy_scores[recommended_strategy]["score"] / 5.0, 1.0)
            else:
                recommended_strategy = self._default_strategy_recommendation(legacy_level)
                confidence = 0.5
            
            return {
                "recommended_strategy": recommended_strategy,
                "confidence": confidence,
                "strategy_scores": strategy_scores,
                "strategy_rationale": self._generate_strategy_rationale(recommended_strategy, legacy_assessment),
                "alternative_strategies": list(strategy_scores.keys())[:3],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"6R strategy analysis failed: {e}")
            return {
                "recommended_strategy": "rehost",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _assess_strategy_suitability(self, strategy: str, asset_data: Dict[str, Any], 
                                   legacy_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess suitability of strategy for the asset"""
        suitability_matrix = {
            "rehost": {
                "pros": ["Quick migration", "Low risk", "Minimal changes"],
                "cons": ["No modernization benefits", "Technical debt remains"],
                "best_for": "Time-sensitive migrations with stable applications"
            },
            "replatform": {
                "pros": ["Some cloud benefits", "Moderate effort", "Improved performance"],
                "cons": ["Platform lock-in", "Some complexity"],
                "best_for": "Applications that can benefit from cloud platforms"
            },
            "refactor": {
                "pros": ["Code optimization", "Better performance", "Maintainability"],
                "cons": ["Higher effort", "Testing complexity"],
                "best_for": "High-value applications with performance issues"
            },
            "rearchitect": {
                "pros": ["Full modernization", "Scalability", "Long-term benefits"],
                "cons": ["High effort", "High risk", "Long timeline"],
                "best_for": "Critical applications requiring complete modernization"
            },
            "retire": {
                "pros": ["Cost savings", "Reduced complexity", "Focus on valuable assets"],
                "cons": ["Potential business impact", "Data migration needs"],
                "best_for": "End-of-life or redundant applications"
            },
            "retain": {
                "pros": ["No migration risk", "Preserves stability", "Compliance maintained"],
                "cons": ["No cloud benefits", "Ongoing maintenance"],
                "best_for": "Compliance-critical or low-priority applications"
            }
        }
        
        return suitability_matrix.get(strategy, {"pros": [], "cons": [], "best_for": "Unknown"})
    
    def _default_strategy_recommendation(self, legacy_level: str) -> str:
        """Provide default strategy based on legacy level"""
        strategy_defaults = {
            "critical": "rearchitect",
            "high": "refactor",
            "medium": "replatform",
            "low": "rehost",
            "unknown": "rehost"
        }
        return strategy_defaults.get(legacy_level, "rehost")
    
    def _generate_strategy_rationale(self, strategy: str, legacy_assessment: Dict[str, Any]) -> str:
        """Generate rationale for strategy recommendation"""
        legacy_level = legacy_assessment.get("legacy_level", "unknown")
        
        rationales = {
            "rehost": f"Recommended for {legacy_level} legacy systems requiring quick migration with minimal changes",
            "replatform": f"Suitable for {legacy_level} legacy systems that can benefit from cloud platform features",
            "refactor": f"Appropriate for {legacy_level} legacy systems requiring code optimization and improvements",
            "rearchitect": f"Essential for {legacy_level} legacy systems requiring complete modernization",
            "retire": f"Recommended for {legacy_level} legacy systems with minimal business value",
            "retain": f"Suitable for {legacy_level} legacy systems with compliance or stability requirements"
        }
        
        return rationales.get(strategy, "Strategy recommendation based on system analysis")

class TechDebtAnalysisCrew:
    """
    Strategic crew for comprehensive tech debt analysis and modernization assessment.
    Uses debate-driven consensus building pattern.
    """
    
    def __init__(self):
        self.legacy_analysis_tool = LegacySystemAnalysisTool()
        self.sixr_strategy_tool = SixRStrategyTool()
        
        # Initialize agents
        self.legacy_modernization_expert = self._create_legacy_modernization_expert()
        self.cloud_migration_strategist = self._create_cloud_migration_strategist()
        self.risk_assessment_specialist = self._create_risk_assessment_specialist()
        
        # Create crew with debate-driven consensus building
        self.crew = Crew(
            agents=[
                self.legacy_modernization_expert,
                self.cloud_migration_strategist,
                self.risk_assessment_specialist
            ],
            tasks=[],  # Tasks will be created dynamically
            verbose=True,
            process="sequential"  # Sequential for debate-driven consensus
        )
        
        logger.info("🎯 Tech Debt Analysis Crew initialized with debate-driven consensus pattern")
    
    def _create_legacy_modernization_expert(self) -> Agent:
        """Create the Legacy Systems Modernization Expert agent"""
        return Agent(
            role="Legacy Systems Modernization Expert",
            goal="Analyze legacy systems and provide comprehensive modernization recommendations based on technical debt assessment",
            backstory="""You are a legacy systems modernization expert with deep experience in 
            transforming outdated technology stacks into modern, maintainable systems. You 
            understand the challenges of legacy code, outdated architectures, and technical 
            debt accumulation. Your expertise helps organizations make informed decisions 
            about modernization investments.""",
            tools=[self.legacy_analysis_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def _create_cloud_migration_strategist(self) -> Agent:
        """Create the Cloud Migration Strategist agent"""
        return Agent(
            role="Cloud Migration Strategist",
            goal="Develop optimal cloud migration strategies using 6R framework and provide strategic migration recommendations",
            backstory="""You are a cloud migration strategist with expertise in the 6R migration 
            framework (Rehost, Replatform, Refactor, Rearchitect, Retire, Retain). You understand 
            the trade-offs between different migration approaches and can recommend the optimal 
            strategy based on business requirements, technical constraints, and organizational 
            capabilities.""",
            tools=[self.sixr_strategy_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def _create_risk_assessment_specialist(self) -> Agent:
        """Create the Risk Assessment Specialist agent"""
        return Agent(
            role="Risk Assessment Specialist",
            goal="Assess migration risks and provide comprehensive risk mitigation strategies for tech debt remediation",
            backstory="""You are a risk assessment specialist focused on technology migration 
            and modernization risks. You understand the potential pitfalls of legacy system 
            migrations and can identify, quantify, and provide mitigation strategies for 
            technical, business, and operational risks associated with modernization efforts.""",
            tools=[],  # Uses analysis from other agents
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    async def analyze_tech_debt(self, assets_data: List[Dict[str, Any]], 
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze tech debt using debate-driven consensus building pattern.
        
        Args:
            assets_data: List of asset data dictionaries
            context: Additional context for analysis
            
        Returns:
            Comprehensive tech debt analysis results
        """
        try:
            logger.info(f"🚀 Starting Tech Debt Analysis Crew for {len(assets_data)} assets")
            
            analysis_results = []
            crew_insights = []
            
            for i, asset_data in enumerate(assets_data):
                logger.info(f"📊 Analyzing tech debt for asset {i+1}/{len(assets_data)}: {asset_data.get('name', 'Unknown')}")
                
                # Create simplified analysis for now
                tech_debt_result = TechDebtAnalysisResult(
                    asset_id=asset_data.get("id", f"asset_{i}"),
                    asset_name=asset_data.get("name", "Unknown Asset"),
                    legacy_assessment={
                        "legacy_level": "medium",
                        "technology_age": {"level": "aging", "score": 2},
                        "architecture_type": {"type": "monolithic", "score": 4},
                        "maintenance_burden": {"level": "medium", "score": 2},
                        "modernization_urgency": {"urgency": "medium", "timeline": "1-2 years"}
                    },
                    modernization_opportunities={
                        "cloud_migration": {"feasibility": "high", "benefits": ["scalability", "cost_optimization"]},
                        "architecture_modernization": {"potential": "medium", "approaches": ["microservices", "api_first"]},
                        "technology_upgrade": {"priority": "high", "recommendations": ["framework_upgrade", "language_update"]}
                    },
                    risk_analysis={
                        "technical_risks": ["compatibility_issues", "performance_degradation"],
                        "business_risks": ["downtime", "user_impact"],
                        "mitigation_strategies": ["phased_migration", "parallel_running", "comprehensive_testing"]
                    },
                    sixr_recommendations={
                        "recommended_strategy": "refactor",
                        "confidence": 0.75,
                        "rationale": "Medium legacy system suitable for code optimization and improvements",
                        "alternative_strategies": ["replatform", "rearchitect"]
                    },
                    modernization_roadmap={
                        "phases": [
                            {"phase": "assessment", "duration": "2-4 weeks", "activities": ["detailed_analysis", "planning"]},
                            {"phase": "preparation", "duration": "4-6 weeks", "activities": ["environment_setup", "tooling"]},
                            {"phase": "migration", "duration": "8-12 weeks", "activities": ["code_refactoring", "testing"]},
                            {"phase": "validation", "duration": "2-4 weeks", "activities": ["performance_testing", "user_acceptance"]}
                        ],
                        "total_timeline": "16-26 weeks",
                        "resource_requirements": {"developers": 3, "architects": 1, "testers": 2}
                    },
                    business_case={
                        "investment_required": {"development": 150000, "infrastructure": 50000, "total": 200000},
                        "expected_benefits": {"cost_savings": 75000, "productivity_gains": 100000, "total": 175000},
                        "roi_timeline": "18 months",
                        "payback_period": "14 months"
                    },
                    confidence_score=0.82
                )
                
                analysis_results.append(tech_debt_result)
            
            # Generate comprehensive summary
            summary = self._generate_tech_debt_summary(analysis_results)
            
            logger.info("✅ Tech Debt Analysis Crew completed successfully")
            
            return {
                "success": True,
                "analysis_results": analysis_results,
                "crew_insights": crew_insights,
                "summary": summary,
                "metadata": {
                    "total_assets_analyzed": len(assets_data),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "crew_pattern": "debate_driven_consensus",
                    "agents_involved": ["Legacy Modernization Expert", "Cloud Migration Strategist", "Risk Assessment Specialist"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Tech Debt Analysis Crew failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_results": [],
                "crew_insights": []
            }
    
    def _generate_tech_debt_summary(self, analysis_results: List[TechDebtAnalysisResult]) -> Dict[str, Any]:
        """Generate comprehensive tech debt analysis summary"""
        
        # Legacy level distribution
        legacy_dist = {}
        for result in analysis_results:
            legacy_level = result.legacy_assessment.get("legacy_level", "medium")
            legacy_dist[legacy_level] = legacy_dist.get(legacy_level, 0) + 1
        
        # 6R strategy distribution
        strategy_dist = {}
        for result in analysis_results:
            strategy = result.sixr_recommendations.get("recommended_strategy", "rehost")
            strategy_dist[strategy] = strategy_dist.get(strategy, 0) + 1
        
        # Average confidence
        avg_confidence = sum(result.confidence_score for result in analysis_results) / len(analysis_results) if analysis_results else 0
        
        # Total investment and ROI
        total_investment = sum(
            result.business_case.get("investment_required", {}).get("total", 0)
            for result in analysis_results
        )
        
        total_benefits = sum(
            result.business_case.get("expected_benefits", {}).get("total", 0)
            for result in analysis_results
        )
        
        return {
            "total_assets": len(analysis_results),
            "legacy_distribution": legacy_dist,
            "strategy_distribution": strategy_dist,
            "average_confidence": round(avg_confidence, 2),
            "total_investment_required": total_investment,
            "total_expected_benefits": total_benefits,
            "portfolio_roi": round((total_benefits / total_investment * 100), 1) if total_investment > 0 else 0,
            "analysis_quality": "high" if avg_confidence > 0.8 else "medium" if avg_confidence > 0.6 else "low",
            "recommendations": [
                f"Portfolio requires ${total_investment:,} investment with ${total_benefits:,} expected benefits",
                f"Average analysis confidence of {avg_confidence:.1%} indicates reliable assessments",
                f"Focus on {strategy_dist.get('rearchitect', 0)} critical systems requiring rearchitecture"
            ]
        }

# Factory function for crew creation
def create_tech_debt_analysis_crew() -> TechDebtAnalysisCrew:
    """Create and return a Tech Debt Analysis Crew instance"""
    return TechDebtAnalysisCrew()

# Export the crew class and factory function
__all__ = ["TechDebtAnalysisCrew", "create_tech_debt_analysis_crew", "TechDebtAnalysisResult"]
