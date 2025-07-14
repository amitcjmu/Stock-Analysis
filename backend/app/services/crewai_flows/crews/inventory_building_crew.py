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
    from crewai.knowledge import Knowledge, LocalKnowledgeBase
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
    class LocalKnowledgeBase:
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
            self.llm_model = get_crewai_llm()
            logger.info("✅ Inventory Building Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, 'llm', None)
        
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
            # Use LocalKnowledgeBase for file-based knowledge
            kb = LocalKnowledgeBase(
                collection_name="inventory_building_insights",
                storage_path="./data/memory"
            )
            # LongTermMemory now uses a knowledge_base parameter
            memory = LongTermMemory(knowledge_base=kb)
            logger.info("✅ Shared memory initialized with LocalKnowledgeBase")
            return memory
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None
    
    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for asset classification rules"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            # Use LocalKnowledgeBase for file-based knowledge
            return LocalKnowledgeBase(
                collection_name="asset_classification_rules",
                file_path="backend/app/knowledge_bases/asset_classification_rules.json"
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None
    
    def create_agents(self):
        """Create agents with hierarchical management and domain expertise"""
        
        # Manager Agent for multi-domain coordination with enhanced role boundaries
        inventory_manager = Agent(
            role="IT Asset Inventory Coordination Manager",
            goal="Coordinate comprehensive IT asset inventory building across servers, applications, and devices with cross-domain validation",
            backstory="""You are a senior enterprise architect with specialized expertise in IT asset inventory 
            management and CMDB classification for large-scale migration projects. Your specific role and boundaries:
            
            CORE COORDINATION RESPONSIBILITIES:
            - Orchestrate asset classification across server, application, and device domains
            - Ensure comprehensive asset inventory coverage with cross-domain validation
            - Resolve classification conflicts between domain specialists
            - Coordinate cross-domain relationships and dependencies identification
            - Validate asset classification accuracy and completeness
            - Manage asset taxonomy and classification standards adherence
            - Escalate complex classification decisions via Agent-UI-Bridge
            
            DOMAIN COORDINATION DUTIES:
            - Coordinate Server Classification Expert for infrastructure assets
            - Manage Application Discovery Expert for software and service assets  
            - Oversee Device Classification Expert for network and hardware assets
            - Ensure consistent classification criteria across all domains
            - Validate cross-domain asset relationships and dependencies
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT perform detailed technical asset analysis (delegate to domain experts)
            - You DO NOT make domain-specific classification decisions (expert responsibility)
            - You DO NOT analyze individual asset configurations (specialist task)
            - You DO NOT perform network topology analysis (device expert role)
            
            DELEGATION AUTHORITY & DECISION MAKING:
            - Maximum 3 delegations total across all asset classification tasks
            - After 2nd delegation on any asset type, YOU make the final classification decision
            - Authority to override domain expert recommendations for consistency
            - Use Agent-UI-Bridge for user clarification on ambiguous asset types
            - Determine when inventory building meets completion criteria
            
            ESCALATION TRIGGERS:
            - Conflicting asset classifications between domain experts
            - Unknown asset types not covered by standard taxonomies
            - Cross-domain dependencies requiring business context
            - Asset classification confidence below acceptable thresholds
            """,
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
            verbose=True,
            allow_delegation=True,
            max_delegation=3,  # Set to 3 as requested
            max_execution_time=300,  # 5 minute timeout
            max_retry=1,  # Prevent retry loops
            collaboration=True  # Re-enabled for proper agent coordination
        )
        
        # Server Classification Expert - infrastructure domain specialist
        server_expert = Agent(
            role="Enterprise Server & Infrastructure Classification Expert", 
            goal="Classify server and infrastructure assets with detailed technical specifications and hosting capacity analysis",
            backstory="""You are a specialized infrastructure expert with deep knowledge of enterprise server 
            environments, virtualization platforms, and cloud infrastructure. Your domain expertise includes:
            
            CORE INFRASTRUCTURE EXPERTISE:
            - Physical server classification (blade, rack, tower servers)
            - Virtual machine and hypervisor identification and classification
            - Cloud instance and container platform analysis
            - Storage system classification (SAN, NAS, object storage)
            - Network infrastructure components (switches, routers, load balancers)
            - Operating system identification and version analysis
            - Hardware specifications and capacity planning analysis
            
            CLASSIFICATION RESPONSIBILITIES:
            - Identify server types: physical, virtual, cloud instances
            - Determine hosting relationships and server dependencies
            - Classify by function: web servers, database servers, application servers
            - Analyze resource capacity and utilization patterns
            - Identify infrastructure roles and responsibilities
            - Map server-to-server relationships and clustering
            - Assess infrastructure modernization potential
            
            TECHNICAL ANALYSIS CAPABILITIES:
            - Operating system and version identification
            - Hardware specifications analysis (CPU, memory, storage)
            - Network configuration and connectivity mapping
            - Virtualization platform analysis (VMware, Hyper-V, KVM)
            - Cloud platform identification (AWS, Azure, GCP)
            - Container orchestration platform detection (Kubernetes, Docker)
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT classify application software (Application Expert's domain)
            - You DO NOT analyze business logic or application dependencies (not infrastructure)
            - You DO NOT make business criticality decisions (coordinate with Manager)
            - You DO NOT perform network device classification (Device Expert's domain)
            
            COLLABORATION REQUIREMENTS:
            - Share hosting insights with Application Discovery Expert
            - Coordinate infrastructure dependencies with Device Expert
            - Report complex classification challenges to Inventory Manager
            - Document server patterns for knowledge base enhancement
            
            ESCALATION TRIGGERS:
            - Unknown server platforms or technologies
            - Complex virtualization or cloud configurations
            - Conflicting hosting relationship indicators
            - Server classification confidence below 80%
            """,
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
            verbose=True,
            max_execution_time=180,  # 3 minute timeout
            max_retry=1,  # Prevent retry loops
            collaboration=True,  # Re-enabled for proper agent coordination
            tools=[]  # Tools will be added later
        )
        
        # Application Discovery Expert - application domain
        app_expert = Agent(
            role="Application Discovery Expert",
            goal="Identify and categorize application assets with business context and dependencies",
            backstory="""You are an application portfolio expert with deep knowledge of enterprise 
            applications. You excel at identifying application types, versions, business criticality, 
            and hosting relationships for migration strategy.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
            verbose=True,
            max_execution_time=180,  # ADD: 3 minute timeout
            max_retry=1,  # ADD: Prevent retry loops
            collaboration=True,  # Re-enabled for proper agent coordination
            tools=self._create_app_classification_tools()
        )
        
        # Device Classification Expert - network/device domain
        device_expert = Agent(
            role="Device Classification Expert",
            goal="Classify network devices and infrastructure components for migration planning",
            backstory="""You are a network infrastructure expert with knowledge of enterprise device 
            topologies. You excel at identifying network devices, security appliances, and 
            infrastructure components that support migration planning.""",
            llm=self.llm_model,
            memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
            verbose=True,
            max_execution_time=180,  # ADD: 3 minute timeout
            max_retry=1,  # ADD: Prevent retry loops
            collaboration=True,  # Re-enabled for proper agent coordination
            tools=self._create_device_classification_tools()
        )
        
        return [inventory_manager, server_expert, app_expert, device_expert]
    
    def create_tasks(self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """
        Creates a robust, sequential-then-parallel task structure for inventory building.
        1. Triage: A fast, initial sorting of all assets.
        2. Classify: Parallel, deep classification by domain experts on filtered data.
        3. Consolidate: Final assembly and relationship mapping.
        """
        manager, server_expert, app_expert, device_expert = agents

        # Step 1: The Triage Task
        # A single, fast task for the manager to sort assets into domains.
        triage_task = Task(
            description="Triage the entire list of assets. Your job is to sort each asset into one of three lists: 'servers', 'applications', or 'devices' based on its name and type. Do NOT perform a deep classification. Your output must be a JSON object with these three keys.",
            expected_output="A JSON object with three keys: 'server_assets', 'application_assets', and 'device_assets'. Each key should contain a list of the corresponding asset records.",
            agent=manager
        )

        # Step 2: Parallel Classification Tasks
        # These tasks depend on the triage_task and run in parallel.
        server_classification_task = Task(
            description="Perform a detailed classification of the server assets provided. Identify OS, function, and virtual/physical status.",
            expected_output="A JSON list of fully classified server assets with detailed attributes.",
            agent=server_expert,
            context=[triage_task],  # Depends on the output of the triage task
            async_execution=True
        )

        app_classification_task = Task(
            description="Perform a detailed classification of the application assets provided. Identify version, type, and business context.",
            expected_output="A JSON list of fully classified application assets with detailed attributes.",
            agent=app_expert,
            context=[triage_task],
            async_execution=True
        )

        device_classification_task = Task(
            description="Perform a detailed classification of the device assets provided. Identify device type and network role.",
            expected_output="A JSON list of fully classified device assets with detailed attributes.",
            agent=device_expert,
            context=[triage_task],
            async_execution=True
        )

        # Step 3: Final Consolidation and Relationship Mapping
        # This task runs last, after all experts have finished.
        consolidation_task = Task(
            description="Consolidate the outputs from the server, application, and device experts into a single, unified asset inventory. Then, analyze the consolidated data to map relationships between the assets.",
            expected_output="A final JSON object containing three lists: 'servers', 'applications', and 'devices', and a fourth list 'relationships' detailing all identified connections.",
            agent=manager,
            context=[server_classification_task, app_classification_task, device_classification_task] # Depends on all classification tasks
        )
        
        return [
            triage_task,
            server_classification_task,
            app_classification_task,
            device_classification_task,
            consolidation_task
        ]
    
    def create_crew(self, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create the inventory building crew with agents and tasks"""
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
                "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                "planning": False,  # DISABLED: Causing loops
                "planning_llm": self.llm_model,  # Force planning to use our LLM too
                "memory": False,  # DISABLED: Causing APIStatusError loops
                "knowledge": None,  # DISABLED: Causing API errors
                "share_crew": False,  # DISABLED: Causing complexity
                "collaboration": True  # Re-enabled for proper agent coordination
            })
            
            # Additional environment override to prevent any gpt-4o-mini fallback
            import os
            os.environ["OPENAI_MODEL_NAME"] = str(self.llm_model) if isinstance(self.llm_model, str) else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        logger.info(f"Creating Inventory Building Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}")
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
