"""
Initialization Handler for Discovery Flow
Handles flow initialization, shared memory, knowledge bases, and planning setup
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# CrewAI imports for advanced features
try:
    from crewai.security import Fingerprint
    from crewai.memory import LongTermMemory
    from crewai.knowledge import KnowledgeBase
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI advanced features not available: {e}")
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            self.storage_id = "fallback_memory"
    
    class KnowledgeBase:
        def __init__(self, **kwargs):
            pass
    
    class Fingerprint:
        def __init__(self, **kwargs):
            self.uuid_str = "fallback_fingerprint"

logger = logging.getLogger(__name__)

class InitializationHandler:
    """Handles flow initialization and setup"""
    
    def __init__(self, crewai_service, context):
        self.crewai_service = crewai_service
        self.context = context
    
    def setup_shared_memory(self) -> LongTermMemory:
        """Initialize shared memory across all crews following CrewAI best practices"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Using fallback memory - CrewAI advanced features not available")
            return LongTermMemory()
        
        try:
            # Configure LongTermMemory with vector storage as per CrewAI documentation
            shared_memory = LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small"
                }
            )
            
            logger.info("✅ Shared memory initialized with vector storage")
            return shared_memory
            
        except Exception as e:
            logger.error(f"Failed to initialize shared memory: {e}")
            logger.info("Using fallback memory implementation")
            return LongTermMemory()
    
    def setup_knowledge_bases(self) -> Dict[str, KnowledgeBase]:
        """Setup domain-specific knowledge bases following CrewAI best practices"""
        knowledge_bases = {}
        
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Using fallback knowledge bases - CrewAI advanced features not available")
            return {
                "field_mapping": KnowledgeBase(),
                "data_quality": KnowledgeBase(),
                "asset_classification": KnowledgeBase(),
                "dependency_patterns": KnowledgeBase(),
                "modernization": KnowledgeBase()
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
                # Filter sources to only existing files
                existing_sources = [source for source in sources if os.path.exists(source)]
                
                if existing_sources:
                    knowledge_bases[domain] = KnowledgeBase(
                        sources=existing_sources,
                        embedder_config={
                            "provider": "openai",
                            "model": "text-embedding-3-small"
                        }
                    )
                    logger.info(f"✅ {domain} knowledge base loaded with {len(existing_sources)} sources")
                else:
                    # Create placeholder knowledge base
                    knowledge_bases[domain] = KnowledgeBase()
                    logger.warning(f"⚠️ {domain} knowledge base created as placeholder - no source files found")
                    
            except Exception as e:
                logger.error(f"Failed to create {domain} knowledge base: {e}")
                knowledge_bases[domain] = KnowledgeBase()
        
        return knowledge_bases
    
    def setup_fingerprint(self, session_id: str, client_account_id: str, 
                         engagement_id: str, raw_data: List[Dict[str, Any]]) -> Fingerprint:
        """Setup flow fingerprint for session management"""
        
        if not CREWAI_ADVANCED_AVAILABLE:
            # Create fallback fingerprint
            fingerprint = Fingerprint()
            fingerprint.uuid_str = f"{session_id}_{client_account_id}_{engagement_id}"
            return fingerprint
        
        try:
            # Create fingerprint with flow context
            fingerprint_data = {
                "session_id": session_id,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "data_sample_size": len(raw_data),
                "data_headers": list(raw_data[0].keys()) if raw_data else [],
                "flow_type": "discovery_redesigned"
            }
            
            fingerprint = Fingerprint(**fingerprint_data)
            logger.info(f"✅ Flow fingerprint created: {fingerprint.uuid_str}")
            return fingerprint
            
        except Exception as e:
            logger.error(f"Failed to create fingerprint: {e}")
            # Fallback fingerprint
            fingerprint = Fingerprint()
            fingerprint.uuid_str = f"{session_id}_{client_account_id}_{engagement_id}"
            return fingerprint
    
    def initialize_flow_state(self, session_id: str, client_account_id: str, 
                             engagement_id: str, user_id: str, raw_data: List[Dict[str, Any]],
                             metadata: Dict[str, Any], fingerprint: str, 
                             shared_memory: LongTermMemory) -> Dict[str, Any]:
        """Initialize complete flow state"""
        
        now = datetime.utcnow().isoformat()
        
        # Create overall discovery plan
        discovery_plan = self.create_discovery_plan()
        
        # Setup crew coordination
        crew_coordination = self.plan_crew_coordination()
        
        return {
            "session_id": session_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "flow_fingerprint": fingerprint,
            "raw_data": raw_data,
            "metadata": metadata,
            "created_at": now,
            "updated_at": now,
            "started_at": now,
            "overall_plan": discovery_plan,
            "crew_coordination": crew_coordination,
            "shared_memory_id": getattr(shared_memory, 'storage_id', 'shared_memory_default'),
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