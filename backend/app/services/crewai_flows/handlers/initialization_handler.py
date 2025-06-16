"""
Initialization Handler for Discovery Flow
Handles flow initialization, shared memory, knowledge bases, and planning setup
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from crewai.security import Fingerprint
from crewai.memory import LongTermMemory
from crewai.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

class InitializationHandler:
    """Handles flow initialization and setup"""
    
    def __init__(self, crewai_service, context):
        self.crewai_service = crewai_service
        self.context = context
    
    def setup_shared_memory(self) -> LongTermMemory:
        """Initialize shared memory across all crews"""
        return LongTermMemory(
            storage_type="vector",
            embedder_config={
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
        )
    
    def setup_knowledge_bases(self) -> Dict[str, KnowledgeBase]:
        """Setup domain-specific knowledge bases"""
        return {
            "field_mapping": KnowledgeBase(
                sources=["docs/field_mapping_patterns.json"],
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"}
            ),
            "data_quality": KnowledgeBase(
                sources=["docs/data_quality_standards.yaml"],
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"}
            ),
            "asset_classification": KnowledgeBase(
                sources=["docs/asset_classification_rules.json"],
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"}
            ),
            "dependency_patterns": KnowledgeBase(
                sources=["docs/dependency_analysis_patterns.json"],
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"}
            ),
            "modernization": KnowledgeBase(
                sources=["docs/modernization_strategies.yaml"],
                embedder_config={"provider": "openai", "model": "text-embedding-3-small"}
            )
        }
    
    def setup_fingerprint(self, session_id: str, client_account_id: str, 
                         engagement_id: str, raw_data: List[Dict[str, Any]]) -> Fingerprint:
        """Setup CrewAI fingerprinting for session management with hierarchical crew support"""
        # Enhanced fingerprint that includes crew architecture information
        fingerprint_seed = f"{session_id}_{client_account_id}_{engagement_id}"
        
        # Add crew architecture signature to fingerprint
        crew_signature = "hierarchical_field_mapping_data_cleansing_inventory_app_server_app_app_technical_debt"
        
        # Include data characteristics in fingerprint for proper session management
        data_signature = f"records_{len(raw_data)}_cols_{len(raw_data[0].keys()) if raw_data else 0}"
        
        # Full fingerprint with architectural context
        full_seed = f"{fingerprint_seed}_{crew_signature}_{data_signature}"
        
        fingerprint = Fingerprint.generate(seed=full_seed)
        
        # Store fingerprint metadata for crew management
        self.fingerprint_metadata = {
            "architecture": "hierarchical_with_collaboration",
            "crew_count": 6,
            "manager_agents": 6,
            "specialist_agents": 12,
            "memory_enabled": True,
            "knowledge_bases": 5,
            "collaboration_enabled": True,
            "planning_enabled": True,
            "session_id": session_id,
            "data_records": len(raw_data),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Enhanced fingerprint created: {fingerprint.uuid_str} with hierarchical crew architecture")
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
            "shared_memory_enabled": True,
            "knowledge_sharing": "cross_domain",
            "manager_oversight": True,
            "parallel_opportunities": ["inventory_classification_subtasks"],
            "collaboration_map": {
                "field_mapping": ["data_cleansing"],
                "inventory_building": ["app_server_dependencies", "app_app_dependencies"],
                "technical_debt": ["assessment_flow_preparation"]
            }
        } 