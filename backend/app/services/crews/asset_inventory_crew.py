"""
Asset Inventory Crew - Converted to proper CrewAI pattern
"""

from typing import List, Dict, Any
from crewai import Task, Process
from app.services.crews.base_crew import BaseDiscoveryCrew
from app.services.crews.task_templates import TaskTemplates
import logging

logger = logging.getLogger(__name__)

class AssetInventoryCrew(BaseDiscoveryCrew):
    """
    Crew for asset classification and inventory management.
    
    Process:
    1. Asset classification
    2. Criticality assessment
    3. Environment detection
    4. Inventory organization
    """
    
    def __init__(self):
        """Initialize asset inventory crew"""
        super().__init__(
            name="asset_inventory_crew",
            description="Asset classification and inventory management",
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True
        )
    
    def create_agents(self) -> List[Any]:
        """Create specialized agents for asset inventory"""
        agents = []
        
        try:
            # Import agent factory locally to avoid circular imports
            from app.services.agents.factory import agent_factory
            
            # Primary asset inventory agent
            inventory_agent = agent_factory.create_agent("asset_inventory_agent")
            if inventory_agent:
                agents.append(inventory_agent)
            
            # Data validation agent for inventory validation
            validation_agent = agent_factory.create_agent("data_validation_agent")
            if validation_agent:
                agents.append(validation_agent)
            
        except Exception as e:
            logger.warning(f"Agent factory creation failed: {e}")
        
        # Fallback agent if factory fails
        if not agents:
            logger.info("Creating fallback asset inventory agent")
            from crewai import Agent
            
            fallback_agent = Agent(
                role="Asset Inventory Specialist",
                goal="Classify and categorize assets for comprehensive inventory management",
                backstory="""You are an expert asset inventory specialist with deep knowledge of:
                - IT infrastructure asset types and classifications
                - Business criticality assessment methodologies
                - Environment categorization (production, staging, development)
                - Asset relationship mapping and dependencies
                - Inventory organization and management best practices
                
                Your expertise enables accurate asset classification and risk assessment for migration planning.""",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                tools=[]
            )
            agents.append(fallback_agent)
        
        return agents
    
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create asset inventory tasks"""
        raw_data = inputs.get("raw_data", [])
        classification_rules = inputs.get("classification_rules", self._get_default_classification_rules())
        criticality_criteria = inputs.get("criticality_criteria", self._get_default_criticality_criteria())
        
        tasks = []
        
        # Task 1: Asset Classification
        classification_task = TaskTemplates.create_classification_task(
            items_to_classify=raw_data[:20],  # Sample for classification
            classification_schema={
                "asset_types": {
                    "server": ["server", "host", "machine", "vm", "virtual"],
                    "database": ["db", "database", "sql", "oracle", "mysql", "postgres"],
                    "application": ["app", "application", "service", "webapp", "api"],
                    "network": ["router", "switch", "firewall", "load balancer"],
                    "storage": ["storage", "nas", "san", "disk", "volume"],
                    "middleware": ["middleware", "message queue", "broker", "cache"]
                },
                "environments": {
                    "production": ["prod", "production", "live", "prd"],
                    "staging": ["stage", "staging", "stg", "uat"],
                    "development": ["dev", "development", "develop"],
                    "test": ["test", "testing", "qa", "quality"]
                }
            },
            agent=self.agents[0]
        )
        tasks.append(classification_task)
        
        # Task 2: Criticality Assessment
        criticality_task = Task(
            description=f"""
            ASSET CRITICALITY ASSESSMENT:
            
            Assets to Assess: {len(raw_data)} total assets
            Classification Results: Use results from previous classification task
            Criticality Criteria: {criticality_criteria}
            
            Your assessment objectives:
            
            1. BUSINESS CRITICALITY ANALYSIS:
               - Assess business impact if asset becomes unavailable
               - Consider production vs non-production environments
               - Evaluate dependencies and downstream impacts
               - Review asset type importance (databases vs dev servers)
            
            2. CRITICALITY SCORING:
               - CRITICAL (90-100): Mission-critical production systems
               - HIGH (70-89): Important business systems, production databases
               - MEDIUM (50-69): Standard business applications, staging systems
               - LOW (0-49): Development, test, backup systems
            
            3. RISK FACTOR IDENTIFICATION:
               - Single points of failure
               - Assets without redundancy
               - Legacy systems requiring special handling
               - High-availability requirements
            
            4. MIGRATION PRIORITIZATION:
               - Priority 1: Low-risk, non-critical assets (good for testing)
               - Priority 2: Medium criticality with good documentation
               - Priority 3: High criticality with proven migration patterns
               - Priority 4: Critical assets requiring extensive planning
            
            5. OUTPUT FORMAT:
            Return JSON with:
            {{
                "asset_criticality": [
                    {{
                        "asset_id": "identifier",
                        "asset_name": "name",
                        "asset_type": "server|database|application|etc",
                        "environment": "production|staging|development|test",
                        "criticality_level": "critical|high|medium|low",
                        "criticality_score": 85,
                        "business_impact": "description",
                        "risk_factors": ["factor1", "factor2"],
                        "migration_priority": 1-4,
                        "migration_complexity": "low|medium|high|critical"
                    }}
                ],
                "summary": {{
                    "total_assets": count,
                    "critical_assets": count,
                    "high_priority_assets": count,
                    "migration_waves": {{
                        "wave_1_candidates": count,
                        "wave_2_candidates": count,
                        "wave_3_candidates": count,
                        "requires_special_handling": count
                    }}
                }},
                "recommendations": [
                    "Migration strategy recommendations",
                    "Risk mitigation suggestions"
                ]
            }}
            """,
            agent=self.agents[0],
            expected_output="JSON with asset criticality assessments and migration priorities",
            context=[classification_task]
        )
        tasks.append(criticality_task)
        
        # Task 3: Final Inventory Validation (if we have a validation agent)
        if len(self.agents) > 1:
            validation_task = Task(
                description="""
                INVENTORY VALIDATION TASK:
                
                Validate the asset inventory and criticality assessments:
                
                1. Verify all assets have been properly classified
                2. Review criticality assessments for consistency
                3. Check migration priority assignments
                4. Validate business impact assessments
                5. Ensure no critical assets are overlooked
                6. Confirm environment classifications are accurate
                
                Provide validation summary with any issues or recommendations.
                """,
                agent=self.agents[1],
                expected_output="Inventory validation report with findings and recommendations",
                context=[criticality_task]
            )
            tasks.append(validation_task)
        
        return tasks
    
    def _get_default_classification_rules(self) -> Dict[str, Any]:
        """Get default asset classification rules"""
        return {
            "asset_type_keywords": {
                "server": ["server", "host", "machine", "node", "vm", "virtual", "compute"],
                "database": ["db", "database", "sql", "oracle", "mysql", "postgres", "mongo", "redis"],
                "application": ["app", "application", "service", "webapp", "api", "web"],
                "network": ["router", "switch", "firewall", "load balancer", "proxy", "gateway"],
                "storage": ["storage", "nas", "san", "disk", "volume", "backup"],
                "middleware": ["middleware", "message queue", "broker", "cache", "mq"]
            },
            "environment_patterns": {
                "production": ["prod", "production", "live", "prd", "p01", "p02"],
                "staging": ["stage", "staging", "stg", "uat", "s01", "s02"],
                "development": ["dev", "development", "develop", "d01", "d02"],
                "test": ["test", "testing", "qa", "quality", "t01", "t02"],
                "dr": ["dr", "disaster", "backup", "recovery", "bcp"]
            },
            "criticality_indicators": {
                "critical": ["prod", "production", "critical", "tier 1", "tier1", "core"],
                "high": ["important", "high", "tier 2", "tier2", "business"],
                "medium": ["medium", "standard", "tier 3", "tier3", "normal"],
                "low": ["dev", "development", "test", "staging", "low", "backup"]
            }
        }
    
    def _get_default_criticality_criteria(self) -> Dict[str, Any]:
        """Get default criticality assessment criteria"""
        return {
            "scoring_factors": {
                "environment_weight": 0.4,  # Production vs non-production
                "asset_type_weight": 0.3,   # Database vs application vs server
                "business_impact_weight": 0.2, # Revenue/operations impact
                "availability_weight": 0.1   # Uptime requirements
            },
            "environment_scores": {
                "production": 90,
                "staging": 60,
                "development": 30,
                "test": 20,
                "dr": 70
            },
            "asset_type_scores": {
                "database": 85,
                "application": 70,
                "server": 60,
                "network": 80,
                "storage": 75,
                "middleware": 65
            },
            "business_impact_levels": {
                "revenue_critical": 95,
                "operations_critical": 85,
                "business_important": 70,
                "support_function": 50,
                "development_only": 25
            }
        }
    
    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process asset inventory results"""
        try:
            # Extract results from final task
            final_result = raw_results
            
            # Parse JSON if results are in string format
            if isinstance(final_result, str):
                try:
                    import re
                    json_match = re.search(r'\{.*\}', final_result, re.DOTALL)
                    if json_match:
                        import json
                        final_result = json.loads(json_match.group())
                    else:
                        final_result = self._parse_text_results(final_result)
                except Exception as e:
                    logger.warning(f"Could not parse JSON from results: {e}")
                    final_result = {"error": "Failed to parse results"}
            
            # Ensure expected structure
            if not isinstance(final_result, dict):
                final_result = {"error": "Unexpected result format"}
            
            asset_criticality = final_result.get("asset_criticality", [])
            summary = final_result.get("summary", {})
            
            # Calculate additional metrics
            total_assets = len(asset_criticality)
            critical_count = sum(1 for asset in asset_criticality if asset.get("criticality_level") == "critical")
            high_count = sum(1 for asset in asset_criticality if asset.get("criticality_level") == "high")
            medium_count = sum(1 for asset in asset_criticality if asset.get("criticality_level") == "medium")
            low_count = sum(1 for asset in asset_criticality if asset.get("criticality_level") == "low")
            
            return {
                "crew_name": self.name,
                "status": "completed",
                "asset_inventory": asset_criticality,
                "classification_summary": {
                    "total_assets": total_assets,
                    "classified_assets": total_assets,
                    "classification_rate": 100.0 if total_assets > 0 else 0.0
                },
                "criticality_distribution": {
                    "critical": critical_count,
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count,
                    "risk_percentage": ((critical_count + high_count) / total_assets * 100) if total_assets > 0 else 0.0
                },
                "migration_readiness": {
                    "wave_1_ready": sum(1 for asset in asset_criticality if asset.get("migration_priority") == 1),
                    "wave_2_ready": sum(1 for asset in asset_criticality if asset.get("migration_priority") == 2),
                    "wave_3_ready": sum(1 for asset in asset_criticality if asset.get("migration_priority") == 3),
                    "requires_planning": sum(1 for asset in asset_criticality if asset.get("migration_priority") == 4),
                    "readiness_score": self._calculate_readiness_score(asset_criticality)
                },
                "recommendations": final_result.get("recommendations", []),
                "context": {
                    "client_account_id": self.context.client_account_id if self.context else None,
                    "engagement_id": self.context.engagement_id if self.context else None
                },
                "metadata": {
                    "agent_count": len(self.agents),
                    "task_count": len(self.tasks),
                    "inventory_complete": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing asset inventory results: {e}")
            return {
                "crew_name": self.name,
                "status": "error",
                "error": str(e),
                "asset_inventory": [],
                "classification_summary": {"error": True},
                "context": {
                    "client_account_id": self.context.client_account_id if self.context else None,
                    "engagement_id": self.context.engagement_id if self.context else None
                }
            }
    
    def _parse_text_results(self, text_result: str) -> Dict[str, Any]:
        """Parse inventory results from text when JSON parsing fails"""
        result = {
            "asset_criticality": [],
            "summary": {"parsing_fallback": True},
            "recommendations": []
        }
        
        # Extract basic counts from text
        lines = text_result.split('\n')
        for line in lines:
            line = line.strip().lower()
            if 'total assets' in line or 'assets processed' in line:
                try:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        result["summary"]["total_assets"] = int(numbers[0])
                except:
                    pass
            elif 'critical' in line and 'asset' in line:
                try:
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        result["summary"]["critical_assets"] = int(numbers[0])
                except:
                    pass
        
        return result
    
    def _calculate_readiness_score(self, asset_criticality: List[Dict[str, Any]]) -> float:
        """Calculate migration readiness score"""
        if not asset_criticality:
            return 0.0
        
        total_assets = len(asset_criticality)
        ready_assets = sum(1 for asset in asset_criticality 
                          if asset.get("migration_priority", 4) <= 2)
        
        return (ready_assets / total_assets) * 100