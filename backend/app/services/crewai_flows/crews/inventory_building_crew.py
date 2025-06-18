"""
Inventory Building Crew - Multi-Domain Classification Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Inventory Manager
- Multi-domain expertise (servers, applications, devices)
- Cross-domain collaboration for asset relationships
- Shared memory integration for classification insights
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

# Import advanced CrewAI features with fallbacks
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge.knowledge import Knowledge
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class Knowledge:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class InventoryBuildingCrew:
    """Enhanced Inventory Building Crew with multi-domain classification"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Inventory Building Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ Inventory Building Crew initialized with multi-domain classification")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for cross-domain classification insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None
        
        try:
            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai", 
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None
    
    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for asset classification rules"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            return Knowledge(
                sources=[
                    "backend/app/knowledge_bases/asset_classification_rules.json"
                ],
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None
    
    def create_agents(self):
        """Create agents with hierarchical management and domain expertise"""
        
        # Manager Agent for multi-domain coordination
        inventory_manager = Agent(
            role="Inventory Manager",
            goal="Coordinate comprehensive asset inventory building across all IT domains",
            backstory="""You are a senior enterprise architect with expertise in managing complex 
            asset classification projects. You excel at coordinating multiple domain experts and 
            ensuring comprehensive asset inventory coverage across servers, applications, and devices.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=3,
            planning=True if CREWAI_ADVANCED_AVAILABLE else False
        )
        
        # Server Classification Expert - infrastructure domain
        server_expert = Agent(
            role="Server Classification Expert", 
            goal="Classify server and infrastructure assets with detailed technical specifications",
            backstory="""You are an infrastructure expert with deep knowledge of enterprise server 
            environments. You excel at identifying server types, operating systems, hardware specs, 
            and infrastructure relationships for migration planning.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_server_classification_tools()
        )
        
        # Application Discovery Expert - application domain
        app_expert = Agent(
            role="Application Discovery Expert",
            goal="Identify and categorize application assets with business context and dependencies",
            backstory="""You are an application portfolio expert with deep knowledge of enterprise 
            applications. You excel at identifying application types, versions, business criticality, 
            and hosting relationships for migration strategy.""",
            llm=self.llm,
            memory=self.shared_memory, 
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_app_classification_tools()
        )
        
        # Device Classification Expert - network/device domain
        device_expert = Agent(
            role="Device Classification Expert",
            goal="Classify network devices and infrastructure components for migration planning",
            backstory="""You are a network infrastructure expert with knowledge of enterprise device 
            topologies. You excel at identifying network devices, security appliances, and 
            infrastructure components that support migration planning.""",
            llm=self.llm,
            memory=self.shared_memory,
            knowledge=self.knowledge_base,
            verbose=True,
            collaboration=True if CREWAI_ADVANCED_AVAILABLE else False,
            tools=self._create_device_classification_tools()
        )
        
        return [inventory_manager, server_expert, app_expert, device_expert]
    
    def create_tasks(self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create hierarchical tasks with cross-domain collaboration"""
        manager, server_expert, app_expert, device_expert = agents
        
        data_sample = cleaned_data[:5] if cleaned_data else []
        mapped_fields = field_mappings.get("mappings", {})
        
        # Planning Task - Manager coordinates multi-domain classification
        planning_task = Task(
            description=f"""Plan comprehensive asset inventory strategy across all IT domains.
            
            Data to classify: {len(cleaned_data)} records
            Available field mappings: {list(mapped_fields.keys())}
            Asset type indicators: {self._identify_asset_type_indicators(cleaned_data)}
            
            Create a classification plan that:
            1. Assigns domain experts to appropriate asset types
            2. Defines cross-domain collaboration strategies
            3. Establishes classification criteria and validation
            4. Plans relationship mapping between domains
            5. Leverages field mappings and data quality insights
            
            Use your planning capabilities to coordinate multi-domain asset classification.""",
            expected_output="Comprehensive asset classification plan with domain assignments and collaboration strategy",
            agent=manager,
            tools=[]
        )
        
        # Server Classification Task - Infrastructure assets
        server_classification_task = Task(
            description=f"""Classify server and infrastructure assets with detailed specifications.
            
            Data to analyze: {len(cleaned_data)} records
            Sample data: {data_sample}
            Relevant field mappings: {self._filter_infrastructure_mappings(mapped_fields)}
            
            Classification Requirements:
            1. Identify servers, virtual machines, and infrastructure components
            2. Extract technical specifications (CPU, memory, storage, OS)
            3. Determine hosting relationships and infrastructure dependencies
            4. Assess migration complexity and hosting requirements
            5. Generate server inventory with technical details
            6. Collaborate with application expert for hosting relationships
            7. Store infrastructure insights in shared memory
            
            Collaborate with application and device experts for complete topology.""",
            expected_output="Comprehensive server inventory with technical specifications and hosting relationships",
            agent=server_expert,
            context=[planning_task],
            tools=self._create_server_classification_tools()
        )
        
        # Application Classification Task - Application assets
        app_classification_task = Task(
            description=f"""Identify and categorize application assets with business context.
            
            Data to analyze: {len(cleaned_data)} records
            Field mappings: {self._filter_application_mappings(mapped_fields)}
            Server insights: Use server expert insights from shared memory
            
            Classification Requirements:
            1. Identify applications, services, and software components
            2. Determine application types, versions, and technologies
            3. Assess business criticality and owner information
            4. Map applications to hosting infrastructure
            5. Identify application dependencies and integrations
            6. Generate application portfolio with business context
            7. Collaborate with server expert for hosting validation
            8. Store application insights in shared memory
            
            Collaborate with server and device experts for dependency mapping.""",
            expected_output="Comprehensive application inventory with business context and hosting relationships",
            agent=app_expert,
            context=[server_classification_task],
            tools=self._create_app_classification_tools()
        )
        
        # Device Classification Task - Network and device assets
        device_classification_task = Task(
            description=f"""Classify network devices and infrastructure components.
            
            Data to analyze: {len(cleaned_data)} records
            Field mappings: {self._filter_device_mappings(mapped_fields)}
            Infrastructure context: Use server and app insights from shared memory
            
            Classification Requirements:
            1. Identify network devices, security appliances, and infrastructure
            2. Determine device types, roles, and network functions
            3. Map network topology and device relationships
            4. Assess migration impact on network infrastructure
            5. Generate device inventory with network context
            6. Validate topology with server and application insights
            7. Store device insights in shared memory
            
            Collaborate with all experts for complete infrastructure topology.""",
            expected_output="Comprehensive device inventory with network topology and relationships",
            agent=device_expert,
            context=[app_classification_task],
            tools=self._create_device_classification_tools()
        )
        
        return [planning_task, server_classification_task, app_classification_task, device_classification_task]
    
    def create_crew(self, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create hierarchical crew with cross-domain collaboration"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, cleaned_data, field_mappings)
        
        # Use hierarchical process if advanced features available
        process = Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True
        }
        
        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update({
                "manager_llm": self.llm,  # Critical: Use our DeepInfra LLM
                "planning": True,
                "planning_llm": self.llm,  # Force planning to use our LLM too
                "memory": True,
                "knowledge": self.knowledge_base,
                "share_crew": True,
                "collaboration": True
            })
            
            # Additional environment override to prevent any gpt-4o-mini fallback
            import os
            os.environ["OPENAI_MODEL_NAME"] = str(self.llm.model) if hasattr(self.llm, 'model') else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        logger.info(f"Creating Inventory Building Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm.model if hasattr(self.llm, 'model') else 'Unknown'}")
        return Crew(**crew_config)
    
    def _identify_asset_type_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify potential asset type indicators in the data"""
        if not data:
            return {}
        
        indicators = {"servers": 0, "applications": 0, "devices": 0, "unknown": 0}
        server_keywords = ['server', 'host', 'vm', 'virtual', 'linux', 'windows']
        app_keywords = ['app', 'application', 'service', 'software', 'web']
        device_keywords = ['router', 'switch', 'firewall', 'network', 'device']
        
        for record in data[:10]:  # Sample analysis
            record_str = str(record).lower()
            if any(keyword in record_str for keyword in server_keywords):
                indicators["servers"] += 1
            elif any(keyword in record_str for keyword in app_keywords):
                indicators["applications"] += 1
            elif any(keyword in record_str for keyword in device_keywords):
                indicators["devices"] += 1
            else:
                indicators["unknown"] += 1
        
        return indicators
    
    def _filter_infrastructure_mappings(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Filter field mappings relevant to infrastructure"""
        infra_fields = ['operating_system', 'ip_address', 'cpu_cores', 'memory_gb', 'storage_gb']
        return {k: v for k, v in mappings.items() if any(field in str(v).lower() for field in infra_fields)}
    
    def _filter_application_mappings(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Filter field mappings relevant to applications"""
        app_fields = ['application', 'service', 'version', 'environment', 'business_criticality']
        return {k: v for k, v in mappings.items() if any(field in str(v).lower() for field in app_fields)}
    
    def _filter_device_mappings(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Filter field mappings relevant to devices"""
        device_fields = ['device', 'network', 'router', 'switch', 'firewall']
        return {k: v for k, v in mappings.items() if any(field in str(v).lower() for field in device_fields)}
    
    def _create_server_classification_tools(self):
        """Create tools for server classification"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_app_classification_tools(self):
        """Create tools for application classification"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_device_classification_tools(self):
        """Create tools for device classification"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_inventory_building_crew(crewai_service, cleaned_data: List[Dict[str, Any]], 
                                  field_mappings: Dict[str, Any], shared_memory=None, 
                                  knowledge_base=None) -> Crew:
    """Factory function to create enhanced Inventory Building Crew"""
    crew_instance = InventoryBuildingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(cleaned_data, field_mappings)
