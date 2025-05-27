"""
CrewAI service integration for AI-powered migration analysis.
Provides AI agents for migration planning, 6R analysis, and recommendations.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from crewai import Agent, Task, Crew
    from langchain_openai import ChatOpenAI
    from langchain_community.llms import DeepInfra
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logging.warning("CrewAI not available. AI features will use placeholder logic.")

from app.core.config import settings
from app.models.asset import Asset, SixRStrategy
from app.models.assessment import Assessment, AssessmentType

logger = logging.getLogger(__name__)


class CrewAIService:
    """Service for managing CrewAI agents and tasks."""
    
    def __init__(self):
        self.llm = None
        self.agents = {}
        self.crews = {}
        
        if CREWAI_AVAILABLE and settings.DEEPINFRA_API_KEY:
            self._initialize_llm()
            self._create_agents()
            self._create_crews()
        else:
            logger.warning("CrewAI service initialized in placeholder mode")
    
    def _initialize_llm(self):
        """Initialize the language model for CrewAI using DeepInfra."""
        try:
            self.llm = DeepInfra(
                model_id=settings.CREWAI_MODEL,
                deepinfra_api_token=settings.DEEPINFRA_API_KEY,
                temperature=settings.CREWAI_TEMPERATURE,
                max_tokens=settings.CREWAI_MAX_TOKENS
            )
            logger.info(f"Initialized DeepInfra LLM: {settings.CREWAI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize DeepInfra LLM: {e}")
            # Fallback to OpenAI if available
            try:
                if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                    self.llm = ChatOpenAI(
                        model="gpt-3.5-turbo",
                        temperature=settings.CREWAI_TEMPERATURE,
                        api_key=settings.OPENAI_API_KEY
                    )
                    logger.info("Fallback to OpenAI LLM initialized")
                else:
                    self.llm = None
            except Exception as fallback_error:
                logger.error(f"Fallback LLM initialization failed: {fallback_error}")
                self.llm = None
    
    def _create_agents(self):
        """Create specialized AI agents for migration tasks."""
        if not self.llm:
            return
        
        try:
            # Migration Strategy Agent
            self.agents['migration_strategist'] = Agent(
                role='Migration Strategy Expert',
                goal='Analyze infrastructure assets and recommend optimal 6R migration strategies',
                backstory="""You are an expert cloud migration strategist with deep knowledge of the 6R framework:
                Rehost (lift-and-shift), Replatform (lift-tinker-shift), Refactor (re-architect), 
                Rearchitect (rebuild), Retire (decommission), and Retain (keep as-is).
                You analyze technical specifications, dependencies, and business requirements to recommend 
                the most suitable migration approach for each asset.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Risk Assessment Agent
            self.agents['risk_assessor'] = Agent(
                role='Migration Risk Analyst',
                goal='Identify and assess migration risks, dependencies, and potential blockers',
                backstory="""You are a seasoned risk analyst specializing in cloud migration projects.
                You excel at identifying technical risks, dependency conflicts, security concerns,
                compliance issues, and operational challenges that could impact migration success.
                Your assessments help teams prepare mitigation strategies and contingency plans.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Cost Optimization Agent
            self.agents['cost_optimizer'] = Agent(
                role='Cloud Cost Optimization Specialist',
                goal='Analyze current costs and project cloud migration cost implications',
                backstory="""You are a cloud economics expert who understands the cost implications
                of different migration strategies. You analyze current infrastructure costs,
                project cloud costs for various scenarios, and identify cost optimization opportunities.
                Your recommendations help organizations make financially sound migration decisions.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            # Wave Planning Agent
            self.agents['wave_planner'] = Agent(
                role='Migration Wave Planning Expert',
                goal='Optimize migration sequencing and wave planning based on dependencies and priorities',
                backstory="""You are a migration orchestration expert who specializes in creating
                optimal migration sequences. You understand dependency relationships, business priorities,
                resource constraints, and risk factors to create efficient wave plans that minimize
                disruption and maximize success probability.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )
            
            logger.info("Created CrewAI agents successfully")
            
        except Exception as e:
            logger.error(f"Failed to create CrewAI agents: {e}")
            self.agents = {}
    
    def _create_crews(self):
        """Create specialized crews for different migration tasks."""
        if not self.agents:
            return
        
        try:
            # 6R Analysis Crew
            self.crews['six_r_analysis'] = Crew(
                agents=[
                    self.agents['migration_strategist'],
                    self.agents['risk_assessor'],
                    self.agents['cost_optimizer']
                ],
                verbose=True
            )
            
            # Wave Planning Crew
            self.crews['wave_planning'] = Crew(
                agents=[
                    self.agents['wave_planner'],
                    self.agents['risk_assessor']
                ],
                verbose=True
            )
            
            logger.info("Created CrewAI crews successfully")
            
        except Exception as e:
            logger.error(f"Failed to create CrewAI crews: {e}")
            self.crews = {}
    
    async def analyze_asset_6r_strategy(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an asset and recommend 6R migration strategy."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return self._placeholder_6r_analysis(asset_data)
        
        try:
            task = Task(
                description=f"""
                Analyze the following infrastructure asset and recommend the optimal 6R migration strategy:
                
                Asset Details:
                - Name: {asset_data.get('name')}
                - Type: {asset_data.get('asset_type')}
                - OS: {asset_data.get('operating_system')} {asset_data.get('os_version')}
                - CPU Cores: {asset_data.get('cpu_cores')}
                - Memory: {asset_data.get('memory_gb')} GB
                - Storage: {asset_data.get('storage_gb')} GB
                - Environment: {asset_data.get('environment')}
                - Business Criticality: {asset_data.get('business_criticality')}
                - Dependencies: {len(asset_data.get('dependencies', []))} dependencies
                
                Provide a detailed analysis including:
                1. Recommended 6R strategy with rationale
                2. Alternative strategies with pros/cons
                3. Risk assessment (low/medium/high/critical)
                4. Estimated complexity (low/medium/high)
                5. Migration priority (1-10)
                6. Key considerations and recommendations
                
                Return the analysis in JSON format.
                """,
                agent=self.agents['migration_strategist']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in 6R analysis: {e}")
            return self._placeholder_6r_analysis(asset_data)
    
    async def assess_migration_risks(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks for a migration project."""
        if not CREWAI_AVAILABLE or not self.agents.get('risk_assessor'):
            return self._placeholder_risk_assessment(migration_data)
        
        try:
            task = Task(
                description=f"""
                Perform a comprehensive risk assessment for this migration project:
                
                Migration Details:
                - Total Assets: {migration_data.get('total_assets', 0)}
                - Source Environment: {migration_data.get('source_environment')}
                - Target Environment: {migration_data.get('target_environment')}
                - Timeline: {migration_data.get('timeline_days', 90)} days
                - Business Criticality: {migration_data.get('business_criticality')}
                
                Identify and assess:
                1. Technical risks and mitigation strategies
                2. Business continuity risks
                3. Security and compliance risks
                4. Resource and timeline risks
                5. Dependency-related risks
                6. Overall risk level and recommendations
                
                Return the assessment in JSON format.
                """,
                agent=self.agents['risk_assessor']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return self._placeholder_risk_assessment(migration_data)
    
    async def optimize_wave_plan(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize migration wave planning based on assets and dependencies."""
        if not CREWAI_AVAILABLE or not self.agents.get('wave_planner'):
            return self._placeholder_wave_plan(assets_data)
        
        try:
            task = Task(
                description=f"""
                Create an optimized migration wave plan for {len(assets_data)} assets:
                
                Consider:
                1. Asset dependencies and relationships
                2. Business criticality and priorities
                3. Technical complexity and risk levels
                4. Resource constraints and parallel execution
                5. Minimize business disruption
                
                Create 3-5 migration waves with:
                - Wave sequencing rationale
                - Asset assignments per wave
                - Timeline recommendations
                - Risk mitigation strategies
                - Success criteria
                
                Return the wave plan in JSON format.
                """,
                agent=self.agents['wave_planner']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in wave planning: {e}")
            return self._placeholder_wave_plan(assets_data)
    
    async def _execute_task_async(self, task: Any) -> str:
        """Execute a CrewAI task asynchronously."""
        # Note: CrewAI doesn't have native async support yet
        # This is a placeholder for future async implementation
        return "AI analysis placeholder - CrewAI integration pending"
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and return structured data."""
        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Return structured placeholder if parsing fails
            return {
                "ai_response": response,
                "parsed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _placeholder_6r_analysis(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder 6R analysis when CrewAI is not available."""
        asset_type = asset_data.get('asset_type', 'unknown')
        business_criticality = asset_data.get('business_criticality', 'medium')
        
        # Simple rule-based recommendations
        if asset_type in ['database', 'application']:
            strategy = SixRStrategy.REPLATFORM
            complexity = "medium"
        elif business_criticality == 'critical':
            strategy = SixRStrategy.REHOST
            complexity = "low"
        else:
            strategy = SixRStrategy.REHOST
            complexity = "low"
        
        return {
            "recommended_strategy": strategy.value,
            "alternative_strategies": [
                {"strategy": "rehost", "score": 85, "rationale": "Low risk, quick migration"},
                {"strategy": "replatform", "score": 70, "rationale": "Moderate optimization potential"}
            ],
            "risk_level": "medium",
            "complexity": complexity,
            "priority": 5,
            "confidence": 0.6,
            "rationale": f"Placeholder analysis for {asset_type} asset",
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _placeholder_risk_assessment(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder risk assessment when CrewAI is not available."""
        return {
            "overall_risk": "medium",
            "risk_score": 65,
            "identified_risks": [
                {
                    "category": "technical",
                    "description": "Dependency complexity",
                    "impact": "medium",
                    "probability": "medium",
                    "mitigation": "Thorough dependency mapping and testing"
                }
            ],
            "recommendations": [
                "Conduct pilot migration with non-critical assets",
                "Implement comprehensive monitoring",
                "Prepare rollback procedures"
            ],
            "confidence": 0.5,
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _placeholder_wave_plan(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Placeholder wave plan when CrewAI is not available."""
        total_assets = len(assets_data)
        assets_per_wave = max(1, total_assets // 3)
        
        return {
            "total_waves": 3,
            "waves": [
                {
                    "wave_number": 1,
                    "name": "Pilot Wave",
                    "asset_count": min(assets_per_wave, total_assets),
                    "description": "Low-risk assets for initial validation",
                    "estimated_duration_days": 30
                },
                {
                    "wave_number": 2,
                    "name": "Core Wave", 
                    "asset_count": min(assets_per_wave, total_assets - assets_per_wave),
                    "description": "Primary business assets",
                    "estimated_duration_days": 45
                },
                {
                    "wave_number": 3,
                    "name": "Final Wave",
                    "asset_count": total_assets - (2 * assets_per_wave),
                    "description": "Remaining assets and cleanup",
                    "estimated_duration_days": 30
                }
            ],
            "optimization_score": 70,
            "confidence": 0.5,
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }


# Global service instance
crewai_service = CrewAIService() 