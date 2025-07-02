"""
Initialization Handler for Discovery Flow
Handles flow initialization, shared memory, knowledge bases, and planning setup
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Initialize logger first before any usage
logger = logging.getLogger(__name__)

# CrewAI imports for advanced features
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge import Knowledge, JSONKnowledgeSource, TextFileKnowledgeSource
    CREWAI_ADVANCED_AVAILABLE = True
    logger.info("✅ CrewAI advanced features available")
except ImportError:
    logger.warning("CrewAI advanced features not available - using fallbacks")
    CREWAI_ADVANCED_AVAILABLE = False
    
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            self.storage_id = "fallback_memory"
            
    class Knowledge:
        def __init__(self, collection_name=None, sources=None, **kwargs):
            self.collection_name = collection_name
            
    class JSONKnowledgeSource:
        def __init__(self, **kwargs):
            pass
            
    class TextFileKnowledgeSource:
        def __init__(self, **kwargs):
            pass

class InitializationHandler:
    """Handles flow initialization and setup"""
    
    def __init__(self, crewai_service, context):
        self.crewai_service = crewai_service
        self.context = context
    
    def setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Initialize shared memory across all crews following CrewAI best practices"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Using fallback memory - CrewAI advanced features not available")
            return None
        
        try:
            # For now, disable shared memory to avoid embedding requirements
            # TODO: Configure with DeepInfra embeddings (thenlper/gte-large) later
            logger.info("✅ Shared memory bypassed to avoid embedding requirement")
            return None
            
        except Exception as e:
            logger.error(f"Failed to initialize shared memory: {e}")
            logger.info("Using fallback memory implementation")
            return None
    
    def setup_knowledge_bases(self) -> Dict[str, Knowledge]:
        """Setup domain-specific knowledge bases following CrewAI best practices"""
        knowledge_bases = {}
        
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Using fallback knowledge bases - CrewAI advanced features not available")
            return {
                "field_mapping": None,
                "data_quality": None,
                "asset_classification": None,
                "dependency_patterns": None,
                "modernization": None
            }
        
        # Knowledge base source files
        knowledge_sources = {
            "field_mapping": [
                "backend/app/knowledge_bases/field_mapping_patterns.json",
                "backend/app/knowledge_bases/cmdb_schema_standards.yaml"
            ],
            "data_quality": [
                "backend/app/knowledge_bases/data_quality_standards.yaml"
            ],
            "asset_classification": [
                "backend/app/knowledge_bases/asset_classification_rules.json"
            ],
            "dependency_patterns": [
                "backend/app/knowledge_bases/dependency_analysis_patterns.json"
            ],
            "modernization": [
                "backend/app/knowledge_bases/modernization_strategies.yaml"
            ]
        }
        
        for domain, sources in knowledge_sources.items():
            try:
                # For now, skip knowledge bases to avoid embedding requirements
                # TODO: Configure proper knowledge sources with DeepInfra embeddings (thenlper/gte-large) later
                knowledge_bases[domain] = None
                
                existing_sources = [source for source in sources if os.path.exists(source)]
                if existing_sources:
                    logger.info(f"✅ {domain} knowledge base bypassed (sources found but skipped to avoid embedding requirement)")
                else:
                    logger.warning(f"⚠️ {domain} knowledge base bypassed - no source files found")
                    
            except Exception as e:
                logger.error(f"Failed to setup {domain} knowledge base: {e}")
                knowledge_bases[domain] = None
        
        return knowledge_bases
    
    def setup_flow_id(self, client_account_id: str, 
                     engagement_id: str, raw_data: List[Dict[str, Any]]) -> str:
        """Setup flow ID using the flow service for session management"""
        
        try:
            # Import flow service for proper ID generation
            from app.services.crewai_flow_service import CrewAIFlowService
            
            # Create flow service instance
            flow_service = CrewAIFlowService()
            
            # Generate unique flow ID using the service
            flow_id = flow_service.generate_flow_id(
                flow_type="discovery_redesigned",
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            # Create flow metadata
            flow_metadata = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "data_sample_size": len(raw_data),
                "data_headers": list(raw_data[0].keys()) if raw_data else [],
                "flow_type": "discovery_redesigned",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Register flow with the service
            flow_service.register_flow(
                flow_id=flow_id,
                flow_type="discovery_redesigned",
                metadata=flow_metadata
            )
            
            logger.info(f"✅ Flow ID created and registered: {flow_id}")
            return flow_id
            
        except Exception as e:
            logger.error(f"Failed to create flow ID: {e}")
            # Fallback flow ID generation
            import uuid
            flow_id = f"discovery_redesigned_{uuid.uuid4().hex[:8]}"
            logger.warning(f"Using fallback flow ID: {flow_id}")
            return flow_id
    
    def initialize_flow_state(self, client_account_id: str, 
                             engagement_id: str, user_id: str, raw_data: List[Dict[str, Any]],
                             metadata: Dict[str, Any], flow_id: str, 
                             shared_memory: Optional[LongTermMemory]) -> Dict[str, Any]:
        """Initialize complete flow state"""
        
        now = datetime.utcnow().isoformat()
        
        # Create overall discovery plan
        discovery_plan = self.create_discovery_plan()
        
        # Setup crew coordination
        crew_coordination = self.plan_crew_coordination()
        
        return {
            "flow_id": flow_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "raw_data": raw_data,
            "metadata": metadata,
            "created_at": now,
            "updated_at": now,
            "started_at": now,
            "overall_plan": discovery_plan,
            "crew_coordination": crew_coordination,
            "shared_memory_id": getattr(shared_memory, 'storage_id', 'shared_memory_default') if shared_memory else 'no_shared_memory',
            "current_phase": "field_mapping"
        }
    
    def create_discovery_plan(self) -> Dict[str, Any]:
        """Create comprehensive discovery execution plan"""
        return {
            "phases": [
                {
                    "name": "field_mapping",
                    "crew": "FieldMappingCrew",
                    "manager": "Field Mapping Manager",
                    "dependencies": [],
                    "success_criteria": ["field_mappings_confidence > 0.8", "unmapped_fields < 10%"]
                },
                {
                    "name": "data_cleansing", 
                    "crew": "DataCleansingCrew",
                    "manager": "Data Quality Manager",
                    "dependencies": ["field_mapping"],
                    "success_criteria": ["data_quality_score > 0.85", "standardization_complete"]
                },
                {
                    "name": "inventory_building",
                    "crew": "InventoryBuildingCrew", 
                    "manager": "Inventory Manager",
                    "dependencies": ["data_cleansing"],
                    "success_criteria": ["asset_classification_complete", "cross_domain_validation"]
                },
                {
                    "name": "app_server_dependencies",
                    "crew": "AppServerDependencyCrew",
                    "manager": "Dependency Manager", 
                    "dependencies": ["inventory_building"],
                    "success_criteria": ["hosting_relationships_mapped", "topology_validated"]
                },
                {
                    "name": "app_app_dependencies",
                    "crew": "AppAppDependencyCrew",
                    "manager": "Integration Manager",
                    "dependencies": ["app_server_dependencies"],
                    "success_criteria": ["communication_patterns_mapped", "api_dependencies_identified"]
                },
                {
                    "name": "technical_debt",
                    "crew": "TechnicalDebtCrew",
                    "manager": "Technical Debt Manager",
                    "dependencies": ["app_app_dependencies"],
                    "success_criteria": ["debt_assessment_complete", "six_r_recommendations_ready"]
                }
            ],
            "coordination_strategy": "hierarchical_with_collaboration",
            "memory_sharing": "enabled",
            "knowledge_integration": "cross_domain"
        }
    
    def plan_crew_coordination(self) -> Dict[str, Any]:
        """Plan crew coordination strategy"""
        return {
            "coordination_type": "hierarchical_with_collaboration",
            "shared_memory_enabled": CREWAI_ADVANCED_AVAILABLE,
            "knowledge_sharing": "cross_domain",
            "manager_oversight": True,
            "parallel_opportunities": ["inventory_classification_subtasks"],
            "collaboration_map": {
                "field_mapping": ["data_cleansing"],
                "inventory_building": ["app_server_dependencies", "app_app_dependencies"],
                "technical_debt": ["assessment_flow_preparation"]
            }
        } 