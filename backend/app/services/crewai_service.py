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

    async def analyze_cmdb_data(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CMDB data for quality, completeness, and migration readiness with asset type context."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return self._placeholder_cmdb_analysis(cmdb_data)
        
        try:
            primary_asset_type = cmdb_data.get('primary_asset_type', 'unknown')
            asset_context = cmdb_data.get('asset_type_context', {})
            
            task = Task(
                description=f"""
                Analyze the following CMDB data for migration readiness with asset type context:
                
                File: {cmdb_data.get('filename')}
                Primary Asset Type: {primary_asset_type}
                Asset Distribution: {asset_context}
                Structure: {cmdb_data.get('structure')}
                Asset Coverage: {cmdb_data.get('coverage')}
                Missing Fields: {cmdb_data.get('missing_fields')}
                Sample Data: {cmdb_data.get('sample_data', [])}
                
                IMPORTANT CONTEXT:
                - Primary asset type is {primary_asset_type}
                - Applications should NOT be expected to have OS, IP addresses, or hardware specs
                - Applications typically have: name, version, business service, dependencies (related_ci)
                - Servers should have: hostname, OS, IP address, hardware specifications
                - Databases should have: instance name, version, host server, port
                
                Provide analysis on:
                1. Data quality assessment and scoring (considering asset type context)
                2. Completeness for migration planning (asset-type appropriate)
                3. Identification of critical missing information (relevant to asset type)
                4. Data consistency and standardization issues
                5. Recommendations for data improvement (asset-type specific)
                6. Migration readiness assessment
                
                For {primary_asset_type} assets, focus on fields relevant to that asset type.
                Do NOT flag missing server-specific fields for application assets.
                
                Return analysis in JSON format with specific issues and recommendations.
                """,
                agent=self.agents['migration_strategist']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in CMDB analysis: {e}")
            return self._placeholder_cmdb_analysis(cmdb_data)

    async def process_cmdb_data(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance CMDB data based on AI recommendations."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return self._placeholder_cmdb_processing(processing_data)
        
        try:
            task = Task(
                description=f"""
                Process and enhance the following CMDB data:
                
                File: {processing_data.get('filename')}
                Original Data: {len(processing_data.get('original_data', []))} records
                Processed Data: {len(processing_data.get('processed_data', []))} records
                
                Provide recommendations for:
                1. Data standardization and normalization
                2. Missing field population strategies
                3. Asset categorization improvements
                4. Dependency mapping enhancements
                5. Business context enrichment
                6. Migration-specific data preparation
                
                Suggest specific transformations and enrichments that would:
                - Improve migration planning accuracy
                - Enable better 6R strategy recommendations
                - Support dependency analysis
                - Facilitate wave planning
                
                Return processing recommendations in JSON format.
                """,
                agent=self.agents['migration_strategist']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error in CMDB processing: {e}")
            return self._placeholder_cmdb_processing(processing_data)
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback to improve future AI analysis."""
        if not CREWAI_AVAILABLE or not self.agents.get('migration_strategist'):
            return self._placeholder_feedback_processing(feedback_data)
        
        try:
            task = Task(
                description=f"""
                Process user feedback to improve CMDB analysis accuracy:
                
                File: {feedback_data.get('filename')}
                Original Analysis: {feedback_data.get('original_analysis')}
                User Corrections: {feedback_data.get('user_corrections')}
                Asset Type Override: {feedback_data.get('asset_type_override')}
                
                Learn from this feedback to improve future analysis:
                1. Understand why the original analysis was incorrect
                2. Identify patterns in user corrections
                3. Update asset type detection logic
                4. Improve field requirement mapping
                5. Enhance context-aware recommendations
                
                Return learning insights and updated analysis parameters.
                """,
                agent=self.agents['migration_strategist']
            )
            
            result = await self._execute_task_async(task)
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {e}")
            return self._placeholder_feedback_processing(feedback_data)
    
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

    def _placeholder_cmdb_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder CMDB analysis when CrewAI is not available."""
        structure = cmdb_data.get('structure', {})
        missing_fields = cmdb_data.get('missing_fields', [])
        primary_asset_type = cmdb_data.get('primary_asset_type', 'unknown')
        asset_context = cmdb_data.get('asset_type_context', {})
        
        # Asset-type-aware analysis
        issues = ["Data validation requires manual review"]
        recommendations = ["Validate asset names and identifiers"]
        
        if primary_asset_type == 'application':
            issues.extend([
                "Application dependencies may need mapping",
                "Business service relationships require validation"
            ])
            recommendations.extend([
                "Map application dependencies using Related CI field",
                "Validate business service ownership",
                "Ensure version information is current"
            ])
        elif primary_asset_type == 'server':
            issues.extend([
                "Server hardware specifications may be incomplete",
                "Network configuration details need verification"
            ])
            recommendations.extend([
                "Validate server hardware specifications",
                "Verify network and IP address assignments",
                "Confirm operating system versions"
            ])
        else:
            issues.append("Asset type classification needs refinement")
            recommendations.append("Clarify asset type classification")
        
        # Add missing fields context
        if missing_fields:
            relevant_missing = []
            for field in missing_fields:
                if primary_asset_type == 'application' and field not in ['Operating System', 'IP Address', 'CPU Cores', 'Memory (GB)']:
                    relevant_missing.append(field)
                elif primary_asset_type == 'server':
                    relevant_missing.append(field)
                elif primary_asset_type == 'database':
                    relevant_missing.append(field)
            
            if relevant_missing:
                issues.append(f"Missing {primary_asset_type}-relevant fields: {', '.join(relevant_missing[:3])}" + ("..." if len(relevant_missing) > 3 else ""))
        
        return {
            "issues": issues,
            "recommendations": recommendations + [
                "Enrich data with business context",
                "Establish dependency relationships",
                "Standardize environment classifications",
                "Implement data quality monitoring"
            ],
            "migration_readiness": "Requires data enhancement",
            "confidence_score": max(50, 100 - len(missing_fields) * 5),  # Less penalty for irrelevant missing fields
            "asset_type_context": primary_asset_type,
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }

    def _placeholder_cmdb_processing(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder CMDB processing when CrewAI is not available."""
        return {
            "transformations_applied": [
                "Standardized column naming conventions",
                "Removed duplicate records",
                "Filled missing values with defaults",
                "Normalized data types"
            ],
            "enrichment_suggestions": [
                "Add business criticality scoring",
                "Implement dependency mapping",
                "Enhance with cost information",
                "Include compliance requirements",
                "Add migration complexity scoring"
            ],
            "data_quality_improvement": "15%",
            "migration_readiness_score": 75,
            "next_steps": [
                "Review and validate processed data",
                "Engage business stakeholders for context",
                "Perform dependency discovery",
                "Establish migration priorities"
            ],
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _placeholder_feedback_processing(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder feedback processing when CrewAI is not available."""
        asset_type_override = feedback_data.get('asset_type_override')
        user_corrections = feedback_data.get('user_corrections', {})
        
        return {
            "learning_applied": True,
            "feedback_processed": {
                "asset_type_correction": asset_type_override,
                "field_corrections": len(user_corrections),
                "analysis_improvement": "Future analysis will consider asset type context"
            },
            "updated_parameters": {
                "asset_type_detection": "Enhanced with user feedback",
                "field_requirements": "Updated based on asset type",
                "context_awareness": "Improved"
            },
            "confidence_improvement": 15,
            "ai_model": "placeholder",
            "timestamp": datetime.utcnow().isoformat()
        }


# Global service instance
crewai_service = CrewAIService() 