"""
Application Intelligence Agent
Advanced AI agent for comprehensive application portfolio discovery and intelligence.
Extends the Application Discovery Agent with business context and portfolio analytics.
Enhanced with context-scoped learning for multi-tenancy.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

from ..agent_learning_system import agent_learning_system, LearningContext

logger = logging.getLogger(__name__)

class ApplicationIntelligenceAgent:
    """
    Advanced AI agent that provides comprehensive application portfolio intelligence including:
    - Business-aligned application discovery and classification
    - Portfolio health assessment and readiness evaluation
    - Strategic migration planning and priority assessment
    - Stakeholder requirement integration and business context mapping
    """
    
    def __init__(self, context: Optional[LearningContext] = None):
        self.agent_id = "application_intelligence"
        self.agent_name = "Application Intelligence Agent"
        self.confidence_threshold = 0.75
        self.learning_enabled = True
        self.context = context or LearningContext()
        
        # Application intelligence patterns
        self.intelligence_patterns = {
            "business_criticality_indicators": {},
            "technology_stack_patterns": {},
            "dependency_complexity_patterns": {},
            "migration_readiness_patterns": {}
        }
        
        # Business context understanding
        self.business_context = {
            "organizational_patterns": {},
            "risk_tolerance": "medium",
            "migration_timeline": "standard",
            "stakeholder_priorities": []
        }
        
        self._load_intelligence_data()
    
    async def analyze_application_portfolio(self, applications: List[Dict[str, Any]], 
                                          business_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive application portfolio analysis with business intelligence.
        
        Args:
            applications: List of discovered applications
            business_context: Additional business requirements and constraints
            
        Returns:
            Portfolio analysis with business-aligned recommendations
        """
        try:
            logger.info(f"Starting application portfolio intelligence analysis for {len(applications)} applications")
            
            if business_context:
                self._update_business_context(business_context)
            
            # Step 1: Assess business criticality for each application
            applications_with_criticality = await self._assess_business_criticality(applications)
            
            # Step 2: Evaluate migration readiness
            applications_with_readiness = await self._evaluate_migration_readiness(applications_with_criticality)
            
            # Step 3: Analyze portfolio health and gaps
            portfolio_health = await self._analyze_portfolio_health(applications_with_readiness)
            
            # Step 4: Generate strategic recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(
                applications_with_readiness, portfolio_health
            )
            
            # Step 5: Assess assessment-phase readiness
            assessment_readiness = await self._assess_assessment_readiness(applications_with_readiness)
            
            portfolio_intelligence = {
                "portfolio_analysis": {
                    "applications": applications_with_readiness,
                    "portfolio_health": portfolio_health,
                    "assessment_readiness": assessment_readiness
                },
                "strategic_recommendations": strategic_recommendations,
                "business_insights": await self._generate_business_insights(applications_with_readiness),
                "clarification_priorities": await self._identify_clarification_priorities(applications_with_readiness),
                "intelligence_metadata": {
                    "total_applications": len(applications),
                    "high_criticality_apps": len([app for app in applications_with_readiness 
                                                if app.get("business_criticality_score", 0) >= 0.8]),
                    "ready_for_assessment": len([app for app in applications_with_readiness 
                                               if app.get("assessment_readiness", {}).get("ready", False)]),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "confidence": self._calculate_portfolio_confidence(applications_with_readiness)
                }
            }
            
            # Learn from analysis results for future improvements
            await self._learn_from_analysis(applications_with_readiness, portfolio_intelligence)
            
            logger.info(f"Application portfolio intelligence completed with {len(strategic_recommendations)} recommendations")
            return portfolio_intelligence
            
        except Exception as e:
            logger.error(f"Error in application portfolio intelligence: {e}")
            return {
                "portfolio_analysis": {"applications": applications, "portfolio_health": {}, "assessment_readiness": {}},
                "strategic_recommendations": [],
                "business_insights": [],
                "error": str(e)
            }
    
    async def _assess_business_criticality(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess business criticality for each application using AI patterns."""
        enhanced_applications = []
        
        for app in applications:
            criticality_score = 0.0
            criticality_factors = []
            
            # Analyze application type and function
            app_name = app.get("name", "").lower()
            if any(keyword in app_name for keyword in ["core", "critical", "primary", "main", "production"]):
                criticality_score += 0.3
                criticality_factors.append("Critical naming pattern")
            
            # Analyze technology stack maturity
            tech_stack = app.get("technology_stack", [])
            if tech_stack:
                modern_techs = ["microservices", "kubernetes", "docker", "react", "angular", "node.js"]
                legacy_techs = ["mainframe", "cobol", "vb6", "asp.net", "silverlight"]
                
                if any(tech.lower() in str(tech_stack).lower() for tech in modern_techs):
                    criticality_score += 0.2
                    criticality_factors.append("Modern technology stack")
                elif any(tech.lower() in str(tech_stack).lower() for tech in legacy_techs):
                    criticality_score += 0.4  # Legacy systems often more critical
                    criticality_factors.append("Legacy system - likely critical")
            
            # Analyze component count and complexity
            component_count = len(app.get("components", []))
            if component_count > 5:
                criticality_score += 0.2
                criticality_factors.append("Complex multi-component application")
            
            # Analyze dependencies
            dependencies = app.get("dependencies", {})
            total_deps = len(dependencies.get("internal", [])) + len(dependencies.get("external", []))
            if total_deps > 3:
                criticality_score += 0.2
                criticality_factors.append("High dependency complexity")
            
            # Analyze environment presence
            environments = set()
            for component in app.get("components", []):
                if component.get("environment"):
                    environments.add(component.get("environment"))
            
            if "production" in str(environments).lower():
                criticality_score += 0.3
                criticality_factors.append("Production environment presence")
            
            # Apply business context adjustments
            if self.business_context.get("risk_tolerance") == "low":
                criticality_score *= 1.2  # More conservative scoring
            
            app_with_criticality = app.copy()
            app_with_criticality.update({
                "business_criticality_score": min(criticality_score, 1.0),
                "criticality_factors": criticality_factors,
                "business_impact": self._determine_business_impact(criticality_score),
                "criticality_assessment": {
                    "level": "high" if criticality_score >= 0.7 else "medium" if criticality_score >= 0.4 else "low",
                    "confidence": 0.8,
                    "requires_stakeholder_validation": criticality_score >= 0.6
                }
            })
            
            enhanced_applications.append(app_with_criticality)
        
        return enhanced_applications
    
    async def _evaluate_migration_readiness(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate migration readiness for each application."""
        applications_with_readiness = []
        
        for app in applications:
            readiness_score = 0.0
            readiness_factors = []
            blockers = []
            
            # Documentation and understanding factor
            if app.get("confidence", 0) >= 0.8:
                readiness_score += 0.25
                readiness_factors.append("Well-understood application structure")
            elif app.get("confidence", 0) >= 0.6:
                readiness_score += 0.15
                readiness_factors.append("Good application understanding")
            else:
                blockers.append("Application structure needs clarification")
            
            # Dependency clarity factor
            dependencies = app.get("dependencies", {})
            if dependencies:
                internal_deps = dependencies.get("internal", [])
                external_deps = dependencies.get("external", [])
                
                # Check if dependencies are properly structured (dicts with confidence)
                structured_deps = []
                for dep in internal_deps + external_deps:
                    if isinstance(dep, dict) and "confidence" in dep:
                        structured_deps.append(dep)
                
                if structured_deps and all(dep.get("confidence", 0) >= 0.7 for dep in structured_deps):
                    readiness_score += 0.25
                    readiness_factors.append("Clear dependency mapping")
                elif len(internal_deps) + len(external_deps) > 0:
                    readiness_score += 0.1
                    readiness_factors.append("Partial dependency understanding")
                else:
                    blockers.append("Dependencies need analysis")
            else:
                blockers.append("Dependencies need analysis")
            
            # Technology stack assessment
            tech_stack = app.get("technology_stack", [])
            if tech_stack:
                readiness_score += 0.2
                readiness_factors.append("Technology stack identified")
            else:
                blockers.append("Technology stack needs identification")
            
            # Component completeness
            components = app.get("components", [])
            if len(components) >= 1:
                readiness_score += 0.15
                readiness_factors.append("Application components identified")
            else:
                blockers.append("Application components need identification")
            
            # Business context alignment
            if app.get("business_criticality_score", 0) > 0:
                readiness_score += 0.15
                readiness_factors.append("Business context understood")
            else:
                blockers.append("Business criticality needs assessment")
            
            # Determine readiness level
            if readiness_score >= 0.8 and not blockers:
                readiness_level = "ready"
            elif readiness_score >= 0.6 and len(blockers) <= 1:
                readiness_level = "mostly_ready"
            elif readiness_score >= 0.4:
                readiness_level = "needs_attention"
            else:
                readiness_level = "not_ready"
            
            app_with_readiness = app.copy()
            app_with_readiness.update({
                "migration_readiness": {
                    "score": readiness_score,
                    "level": readiness_level,
                    "factors": readiness_factors,
                    "blockers": blockers,
                    "assessment_ready": readiness_level in ["ready", "mostly_ready"],
                    "priority": self._calculate_migration_priority(app, readiness_score)
                }
            })
            
            applications_with_readiness.append(app_with_readiness)
        
        return applications_with_readiness
    
    async def _analyze_portfolio_health(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall portfolio health and identify gaps."""
        if not applications:
            return {"health_score": 0.0, "gaps": ["No applications in portfolio"]}
        
        total_apps = len(applications)
        ready_apps = len([app for app in applications 
                         if app.get("migration_readiness", {}).get("assessment_ready", False)])
        high_criticality_apps = len([app for app in applications 
                                   if app.get("business_criticality_score", 0) >= 0.7])
        
        # Calculate health metrics
        readiness_ratio = ready_apps / total_apps if total_apps > 0 else 0
        avg_confidence = sum(app.get("confidence", 0) for app in applications) / total_apps if total_apps > 0 else 0
        avg_criticality = sum(app.get("business_criticality_score", 0) for app in applications) / total_apps if total_apps > 0 else 0
        
        health_score = (readiness_ratio * 0.4 + avg_confidence * 0.3 + avg_criticality * 0.3)
        
        # Identify gaps
        gaps = []
        if readiness_ratio < 0.7:
            gaps.append(f"Only {ready_apps}/{total_apps} applications ready for assessment")
        if avg_confidence < 0.7:
            gaps.append("Application understanding needs improvement")
        if high_criticality_apps == 0:
            gaps.append("No high-criticality applications identified - may need business validation")
        
        # Portfolio insights
        insights = []
        if readiness_ratio >= 0.8:
            insights.append("Portfolio shows strong assessment readiness")
        if avg_criticality >= 0.6:
            insights.append("Portfolio contains significant business-critical applications")
        if total_apps >= 10:
            insights.append("Large portfolio may benefit from phased assessment approach")
        
        return {
            "health_score": health_score,
            "readiness_ratio": readiness_ratio,
            "average_confidence": avg_confidence,
            "average_criticality": avg_criticality,
            "total_applications": total_apps,
            "ready_applications": ready_apps,
            "high_criticality_applications": high_criticality_apps,
            "gaps": gaps,
            "insights": insights,
            "recommendation": self._generate_health_recommendation(health_score, gaps)
        }
    
    async def _generate_strategic_recommendations(self, applications: List[Dict[str, Any]], 
                                                portfolio_health: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations for the application portfolio."""
        recommendations = []
        
        # Portfolio readiness recommendations
        if portfolio_health.get("readiness_ratio", 0) < 0.7:
            recommendations.append({
                "category": "portfolio_readiness",
                "priority": "high",
                "title": "Improve Portfolio Assessment Readiness",
                "description": f"Only {portfolio_health.get('ready_applications', 0)} of {portfolio_health.get('total_applications', 0)} applications are assessment-ready",
                "actions": [
                    "Focus on clarifying application boundaries and dependencies",
                    "Validate business criticality assessments with stakeholders",
                    "Complete missing technology stack information"
                ],
                "impact": "Enables comprehensive 6R analysis across portfolio",
                "confidence": 0.9
            })
        
        # Business alignment recommendations
        high_crit_apps = portfolio_health.get("high_criticality_applications", 0)
        if high_crit_apps == 0:
            recommendations.append({
                "category": "business_alignment",
                "priority": "medium",
                "title": "Validate Business Criticality Assessments",
                "description": "No high-criticality applications identified - stakeholder validation needed",
                "actions": [
                    "Conduct stakeholder interviews for business context",
                    "Review application revenue impact and user base",
                    "Validate compliance and regulatory requirements"
                ],
                "impact": "Ensures migration planning aligns with business priorities",
                "confidence": 0.8
            })
        
        # Technology modernization recommendations
        legacy_apps = [app for app in applications 
                      if any(tech in str(app.get("technology_stack", [])).lower() 
                            for tech in ["mainframe", "cobol", "vb6", "asp.net"])]
        if legacy_apps:
            recommendations.append({
                "category": "technology_modernization",
                "priority": "medium",
                "title": f"Address {len(legacy_apps)} Legacy Technology Applications",
                "description": "Legacy applications may require specialized migration approaches",
                "actions": [
                    "Assess modernization vs. replacement for legacy applications",
                    "Evaluate cloud-native alternatives",
                    "Plan for potential application retirement opportunities"
                ],
                "impact": "Reduces technical debt and improves cloud migration success",
                "confidence": 0.7
            })
        
        # Dependency management recommendations
        complex_apps = []
        for app in applications:
            deps = app.get("dependencies", {})
            internal_count = len(deps.get("internal", [])) if isinstance(deps, dict) else 0
            external_count = len(deps.get("external", [])) if isinstance(deps, dict) else 0
            if internal_count + external_count > 5:
                complex_apps.append(app)
        if complex_apps:
            recommendations.append({
                "category": "dependency_management",
                "priority": "high",
                "title": f"Manage {len(complex_apps)} High-Dependency Applications",
                "description": "Applications with complex dependencies need careful migration sequencing",
                "actions": [
                    "Map critical dependency paths",
                    "Identify shared infrastructure components",
                    "Plan migration waves to minimize dependency conflicts"
                ],
                "impact": "Reduces migration risk and ensures application functionality",
                "confidence": 0.8
            })
        
        return recommendations
    
    async def _generate_business_insights(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate business-focused insights about the application portfolio."""
        insights = []
        
        if not applications:
            return insights
        
        # Portfolio composition insight
        app_types = {}
        for app in applications:
            primary_type = app.get("primary_asset", {}).get("asset_type", "unknown")
            app_types[primary_type] = app_types.get(primary_type, 0) + 1
        
        insights.append({
            "category": "portfolio_composition",
            "title": "Application Portfolio Composition",
            "description": f"Portfolio contains {len(applications)} applications across {len(app_types)} asset types",
            "details": app_types,
            "confidence": 0.9
        })
        
        # Business criticality distribution
        criticality_distribution = {"high": 0, "medium": 0, "low": 0}
        for app in applications:
            level = app.get("criticality_assessment", {}).get("level", "low")
            criticality_distribution[level] += 1
        
        insights.append({
            "category": "business_criticality",
            "title": "Business Criticality Distribution",
            "description": f"High: {criticality_distribution['high']}, Medium: {criticality_distribution['medium']}, Low: {criticality_distribution['low']}",
            "details": criticality_distribution,
            "confidence": 0.8
        })
        
        # Technology diversity insight
        tech_diversity = set()
        for app in applications:
            for tech in app.get("technology_stack", []):
                tech_diversity.add(tech.lower())
        
        insights.append({
            "category": "technology_diversity",
            "title": "Technology Stack Diversity",
            "description": f"Portfolio spans {len(tech_diversity)} different technologies",
            "details": list(tech_diversity),
            "confidence": 0.7
        })
        
        return insights
    
    async def _identify_clarification_priorities(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify high-priority clarifications needed for portfolio assessment."""
        priorities = []
        
        # High-criticality apps needing clarification
        high_crit_unclear = [app for app in applications 
                           if app.get("business_criticality_score", 0) >= 0.7 and 
                              app.get("confidence", 0) < 0.7]
        
        if high_crit_unclear:
            priorities.append({
                "priority": "critical",
                "category": "business_critical_clarification",
                "title": f"Clarify {len(high_crit_unclear)} High-Criticality Applications",
                "description": "High business impact applications need better understanding",
                "affected_applications": [app.get("name") for app in high_crit_unclear],
                "urgency": "immediate"
            })
        
        # Complex dependencies needing validation
        complex_deps = []
        for app in applications:
            deps = app.get("dependencies", {})
            if isinstance(deps, dict):
                internal_deps = deps.get("internal", [])
                if len(internal_deps) > 3:
                    # Check if any dependencies have low confidence (only for dict dependencies)
                    has_low_confidence = any(
                        isinstance(dep, dict) and dep.get("confidence", 0) < 0.6 
                        for dep in internal_deps
                    )
                    if has_low_confidence or any(isinstance(dep, str) for dep in internal_deps):
                        complex_deps.append(app)
        
        if complex_deps:
            priorities.append({
                "priority": "high",
                "category": "dependency_validation",
                "title": f"Validate Dependencies for {len(complex_deps)} Complex Applications",
                "description": "Applications with unclear dependencies risk migration delays",
                "affected_applications": [app.get("name") for app in complex_deps],
                "urgency": "high"
            })
        
        return priorities
    
    async def _assess_assessment_readiness(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall readiness for moving to assessment phase."""
        total_apps = len(applications)
        if total_apps == 0:
            return {"ready": False, "reason": "No applications in portfolio"}
        
        ready_apps = len([app for app in applications 
                         if app.get("migration_readiness", {}).get("assessment_ready", False)])
        readiness_percentage = (ready_apps / total_apps) * 100
        
        # Assessment readiness criteria
        criteria = {
            "sufficient_applications": total_apps >= 1,
            "adequate_readiness_ratio": readiness_percentage >= 70,
            "business_context_available": any(app.get("business_criticality_score", 0) > 0 for app in applications),
            "critical_apps_understood": all(app.get("confidence", 0) >= 0.6 for app in applications 
                                          if app.get("business_criticality_score", 0) >= 0.7)
        }
        
        met_criteria = sum(criteria.values())
        overall_ready = met_criteria >= 3  # At least 3 out of 4 criteria
        
        assessment_readiness = {
            "ready": overall_ready,
            "readiness_percentage": readiness_percentage,
            "ready_applications": ready_apps,
            "total_applications": total_apps,
            "criteria_met": met_criteria,
            "criteria_details": criteria,
            "recommendation": "Proceed to assessment phase" if overall_ready else "Address readiness gaps before assessment",
            "next_steps": self._generate_readiness_next_steps(criteria, overall_ready)
        }
        
        return assessment_readiness
    
    def _determine_business_impact(self, criticality_score: float) -> str:
        """Determine business impact level from criticality score."""
        if criticality_score >= 0.8:
            return "critical"
        elif criticality_score >= 0.6:
            return "high"
        elif criticality_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_migration_priority(self, app: Dict[str, Any], readiness_score: float) -> str:
        """Calculate migration priority based on criticality and readiness."""
        criticality = app.get("business_criticality_score", 0)
        
        if criticality >= 0.7 and readiness_score >= 0.7:
            return "high"
        elif criticality >= 0.5 or readiness_score >= 0.7:
            return "medium"
        else:
            return "low"
    
    def _calculate_portfolio_confidence(self, applications: List[Dict[str, Any]]) -> float:
        """Calculate overall portfolio analysis confidence."""
        if not applications:
            return 0.0
        
        total_confidence = sum(app.get("confidence", 0) for app in applications)
        return total_confidence / len(applications)
    
    def _generate_health_recommendation(self, health_score: float, gaps: List[str]) -> str:
        """Generate overall health recommendation."""
        if health_score >= 0.8:
            return "Portfolio is in excellent health for assessment phase"
        elif health_score >= 0.6:
            return "Portfolio shows good health with minor improvements needed"
        elif health_score >= 0.4:
            return "Portfolio needs significant improvement before assessment"
        else:
            return "Portfolio requires substantial clarification and validation"
    
    def _generate_readiness_next_steps(self, criteria: Dict[str, bool], overall_ready: bool) -> List[str]:
        """Generate next steps based on readiness assessment."""
        if overall_ready:
            return [
                "Proceed to 6R assessment phase",
                "Validate stakeholder priorities",
                "Prepare application deep-dive sessions"
            ]
        
        next_steps = []
        if not criteria.get("sufficient_applications"):
            next_steps.append("Complete application discovery process")
        if not criteria.get("adequate_readiness_ratio"):
            next_steps.append("Improve application understanding and documentation")
        if not criteria.get("business_context_available"):
            next_steps.append("Conduct business criticality assessment")
        if not criteria.get("critical_apps_understood"):
            next_steps.append("Focus on understanding high-criticality applications")
        
        return next_steps
    
    def _update_business_context(self, business_context: Optional[Dict[str, Any]]):
        """Update internal business context understanding."""
        if business_context is None:
            return
            
        if "risk_tolerance" in business_context:
            self.business_context["risk_tolerance"] = business_context["risk_tolerance"]
        if "migration_timeline" in business_context:
            self.business_context["migration_timeline"] = business_context["migration_timeline"]
        if "stakeholder_priorities" in business_context:
            self.business_context["stakeholder_priorities"] = business_context["stakeholder_priorities"]
    
    def _load_intelligence_data(self):
        """Load existing intelligence patterns and business context."""
        # In a real implementation, this would load from persistent storage
        pass
    
    def _save_intelligence_data(self):
        """Save intelligence patterns and business context."""
        # In a real implementation, this would save to persistent storage
        pass

    async def _learn_from_analysis(self, applications: List[Dict[str, Any]], analysis_result: Dict[str, Any]):
        """Learn from analysis results to improve future assessments."""
        try:
            # Learn application patterns
            for app in applications:
                if app.get("business_criticality_score", 0) > 0.7:
                    # Learn high-criticality patterns
                    learning_data = {
                        "pattern_type": "high_criticality_application",
                        "application_name": app.get("name", ""),
                        "technology_stack": app.get("technology_stack", []),
                        "criticality_factors": app.get("criticality_factors", []),
                        "confidence": app.get("business_criticality_score", 0)
                    }
                    await agent_learning_system.learn_data_source_pattern(learning_data, self.context)
                
                if app.get("migration_readiness", {}).get("score", 0) > 0.8:
                    # Learn migration readiness patterns
                    learning_data = {
                        "pattern_type": "migration_ready_application",
                        "application_name": app.get("name", ""),
                        "readiness_factors": app.get("migration_readiness", {}).get("factors", []),
                        "confidence": app.get("migration_readiness", {}).get("score", 0)
                    }
                    await agent_learning_system.learn_data_source_pattern(learning_data, self.context)
            
            # Learn portfolio-level patterns
            portfolio_health = analysis_result.get("portfolio_analysis", {}).get("portfolio_health", {})
            if portfolio_health.get("overall_health_score", 0) > 0.7:
                learning_data = {
                    "pattern_type": "healthy_portfolio",
                    "health_score": portfolio_health.get("overall_health_score", 0),
                    "strengths": portfolio_health.get("strengths", []),
                    "application_count": len(applications)
                }
                await agent_learning_system.learn_quality_assessment(learning_data, self.context)
            
            logger.info(f"Learned patterns from application analysis in context {self.context.context_hash}")
            
        except Exception as e:
            logger.warning(f"Failed to learn from analysis: {e}")


# Global instance for the application
application_intelligence_agent = ApplicationIntelligenceAgent() 