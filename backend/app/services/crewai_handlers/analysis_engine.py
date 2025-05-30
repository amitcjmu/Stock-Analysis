"""
Analysis Engine Handler
Handles analysis operations and AI processing.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Handles analysis operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.services.memory import AgentMemory
            from app.services.analysis import IntelligentAnalyzer, PlaceholderAnalyzer
            
            self.memory = AgentMemory()
            self.analyzer = IntelligentAnalyzer(self.memory)
            self.service_available = True
            logger.info("Analysis engine initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Analysis engine services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def analyze_asset_6r_strategy(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze asset for 6R migration strategy."""
        try:
            if not self.service_available:
                return self._fallback_analyze_6r_strategy(asset_data)
            
            # Extract asset information
            asset_name = asset_data.get('asset_name', 'Unknown Asset')
            
            # Simplified 6R analysis logic
            tech_stack = asset_data.get('technology_stack', [])
            complexity = asset_data.get('complexity_score', 3)
            criticality = asset_data.get('business_criticality', 'medium')
            
            # Determine strategy based on characteristics
            if complexity <= 2 and 'legacy' not in str(tech_stack).lower():
                strategy = 'rehost'
                confidence = 0.85
                reasoning = "Low complexity application suitable for lift-and-shift migration"
            elif complexity >= 4 or any('microservice' in str(s).lower() for s in tech_stack):
                strategy = 'refactor'
                confidence = 0.75
                reasoning = "High complexity or modern architecture benefits from refactoring"
            elif criticality == 'low':
                strategy = 'retire'
                confidence = 0.65
                reasoning = "Low business criticality suggests retirement consideration"
            else:
                strategy = 'replatform'
                confidence = 0.70
                reasoning = "Moderate complexity suggests platform modernization"
            
            return {
                "asset_name": asset_name,
                "recommended_strategy": strategy,
                "confidence_score": confidence,
                "reasoning": reasoning,
                "analysis_factors": {
                    "technical_complexity": complexity,
                    "business_criticality": criticality,
                    "technology_stack": tech_stack
                },
                "next_steps": [
                    f"Validate {strategy} strategy with stakeholders",
                    "Conduct detailed assessment",
                    "Plan implementation approach"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing 6R strategy: {e}")
            return self._fallback_analyze_6r_strategy(asset_data)
    
    async def assess_migration_risks(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess migration risks for applications."""
        try:
            if not self.service_available:
                return self._fallback_assess_risks(migration_data)
            
            applications = migration_data.get('applications', [])
            strategy = migration_data.get('strategy', 'rehost')
            
            # Risk assessment logic
            risks = []
            risk_score = 1  # Start with low risk
            
            # Assess based on strategy
            if strategy == 'refactor':
                risks.append("High development effort required")
                risks.append("Potential for scope creep")
                risk_score += 2
            elif strategy == 'replatform':
                risks.append("Platform compatibility issues")
                risks.append("Data migration complexity")
                risk_score += 1
            
            # Assess based on application count
            if len(applications) > 10:
                risks.append("Large-scale migration complexity")
                risk_score += 1
            
            # Assess based on criticality
            critical_apps = [app for app in applications if app.get('business_criticality') == 'high']
            if critical_apps:
                risks.append("Business-critical application downtime risk")
                risk_score += 1
            
            risk_level = "low" if risk_score <= 2 else "medium" if risk_score <= 4 else "high"
            
            return {
                "overall_risk_level": risk_level,
                "risk_score": min(risk_score, 5),
                "identified_risks": risks,
                "mitigation_strategies": [
                    "Implement comprehensive testing strategy",
                    "Plan rollback procedures",
                    "Conduct pilot migrations",
                    "Establish monitoring and alerts"
                ],
                "applications_assessed": len(applications),
                "critical_applications": len(critical_apps)
            }
            
        except Exception as e:
            logger.error(f"Error assessing migration risks: {e}")
            return self._fallback_assess_risks(migration_data)
    
    async def optimize_wave_plan(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize migration wave planning."""
        try:
            if not self.service_available:
                return self._fallback_optimize_waves(assets_data)
            
            # Simple wave planning logic
            waves = {"wave_1": [], "wave_2": [], "wave_3": []}
            
            for asset in assets_data:
                complexity = asset.get('complexity_score', 3)
                criticality = asset.get('business_criticality', 'medium')
                
                # Wave 1: Low complexity, non-critical
                if complexity <= 2 and criticality != 'high':
                    waves["wave_1"].append(asset)
                # Wave 3: High complexity or critical
                elif complexity >= 4 or criticality == 'high':
                    waves["wave_3"].append(asset)
                # Wave 2: Everything else
                else:
                    waves["wave_2"].append(asset)
            
            return {
                "optimized_waves": waves,
                "wave_summary": {
                    "wave_1": {"count": len(waves["wave_1"]), "description": "Low-risk applications"},
                    "wave_2": {"count": len(waves["wave_2"]), "description": "Medium complexity applications"},
                    "wave_3": {"count": len(waves["wave_3"]), "description": "High-complexity/critical applications"}
                },
                "recommendations": [
                    "Start with Wave 1 to build confidence and experience",
                    "Use Wave 1 learnings to refine Wave 2 approach",
                    "Reserve Wave 3 for when migration expertise is mature"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error optimizing wave plan: {e}")
            return self._fallback_optimize_waves(assets_data)
    
    # Fallback methods
    def _fallback_analyze_6r_strategy(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback 6R analysis."""
        return {
            "asset_name": asset_data.get('asset_name', 'Unknown Asset'),
            "recommended_strategy": "rehost",
            "confidence_score": 0.7,
            "reasoning": "Default conservative strategy in fallback mode",
            "analysis_factors": {"mode": "fallback"},
            "next_steps": ["Conduct detailed assessment"],
            "fallback_mode": True
        }
    
    def _fallback_assess_risks(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback risk assessment."""
        return {
            "overall_risk_level": "medium",
            "risk_score": 3,
            "identified_risks": ["General migration risks"],
            "mitigation_strategies": ["Follow migration best practices"],
            "fallback_mode": True
        }
    
    def _fallback_optimize_waves(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback wave optimization."""
        return {
            "optimized_waves": {"wave_1": assets_data[:3], "wave_2": assets_data[3:6], "wave_3": assets_data[6:]},
            "wave_summary": {"description": "Basic wave plan in fallback mode"},
            "recommendations": ["Plan migrations in phases"],
            "fallback_mode": True
        } 