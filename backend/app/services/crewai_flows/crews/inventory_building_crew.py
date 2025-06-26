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
            llm=self.llm,
            memory=None,  # Agent-level memory approach
            knowledge=None,  # Will be added when available
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
            llm=self.llm,
            memory=None,  # Agent-level memory approach
            knowledge=None,  # Will be added when available
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
            llm=self.llm,
            memory=None,  # DISABLED: Causing APIStatusError loops
            knowledge=None,  # DISABLED: Causing API errors
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
            llm=self.llm,
            memory=None,  # DISABLED: Causing APIStatusError loops
            knowledge=None,  # DISABLED: Causing API errors
            verbose=True,
            max_execution_time=180,  # ADD: 3 minute timeout
            max_retry=1,  # ADD: Prevent retry loops
            collaboration=True,  # Re-enabled for proper agent coordination
            tools=self._create_device_classification_tools()
        )
        
        return [inventory_manager, server_expert, app_expert, device_expert]
    
    def create_tasks(self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]):
        """Create hierarchical tasks with cross-domain collaboration and insight generation"""
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
            
            CRITICAL: Generate comprehensive STRATEGIC INSIGHTS for the inventory management:
            - Infrastructure standardization opportunities
            - Technology stack consolidation recommendations
            - Migration complexity assessment patterns
            - Asset portfolio optimization insights
            - Risk factors and mitigation strategies
            
            Store strategic insights in shared memory for domain experts to enhance.""",
            expected_output="""Comprehensive asset classification plan with domain assignments and collaboration strategy.
            
            PLUS: Strategic Insights JSON containing:
            {
                "infrastructure_patterns": {
                    "standardization_level": "high/medium/low",
                    "consolidation_opportunities": [],
                    "complexity_factors": []
                },
                "migration_strategy": {
                    "recommended_approach": "lift_shift/replatform/refactor",
                    "readiness_assessment": "ready/needs_prep/complex",
                    "sequencing_recommendations": []
                },
                "portfolio_insights": {
                    "technology_diversity": "homogeneous/mixed/heterogeneous",
                    "business_criticality_distribution": {},
                    "modernization_priorities": []
                }
            }""",
            agent=manager,
            tools=[]
        )
        
        # Server Classification Task - Infrastructure assets with deep insights
        server_classification_task = Task(
            description=f"""Classify server and infrastructure assets with detailed specifications AND generate comprehensive infrastructure insights.
            
            Data to analyze: {len(cleaned_data)} records
            Sample data: {data_sample}
            Relevant field mappings: {self._filter_infrastructure_mappings(mapped_fields)}
            Strategic insights: Use manager's strategic insights from shared memory
            
            Classification Requirements:
            1. Identify servers, virtual machines, and infrastructure components
            2. Extract technical specifications (CPU, memory, storage, OS)
            3. Determine hosting relationships and infrastructure dependencies
            4. Assess migration complexity and hosting requirements
            5. Generate server inventory with technical details
            6. Collaborate with application expert for hosting relationships
            
            CRITICAL: Generate INFRASTRUCTURE INSIGHTS by analyzing patterns:
            - Operating system distribution and standardization
            - Hardware specification patterns and capacity trends
            - Virtualization adoption and cloud readiness
            - Infrastructure age and modernization needs
            - Geographic/location distribution patterns
            - Security and compliance posture assessment
            - Performance and scalability bottlenecks
            - Cost optimization opportunities
            
            Store infrastructure insights in shared memory for cross-domain analysis.""",
            expected_output="""Comprehensive server inventory with technical specifications and hosting relationships.
            
            PLUS: Infrastructure Insights JSON containing:
            {
                "hosting_patterns": {
                    "os_distribution": {},
                    "virtualization_level": "percentage",
                    "cloud_readiness_score": "0-100",
                    "standardization_assessment": "high/medium/low"
                },
                "capacity_analysis": {
                    "resource_utilization": {},
                    "scaling_opportunities": [],
                    "consolidation_potential": []
                },
                "migration_readiness": {
                    "lift_shift_candidates": "count",
                    "replatform_candidates": "count",
                    "modernization_required": "count",
                    "risk_factors": []
                },
                "recommendations": {
                    "immediate_actions": [],
                    "strategic_initiatives": [],
                    "cost_optimizations": []
                }
            }""",
            agent=server_expert,
            context=[planning_task],
            tools=self._create_server_classification_tools()
        )
        
        # Application Classification Task - Application assets with business insights
        app_classification_task = Task(
            description=f"""Identify and categorize application assets with business context AND generate comprehensive application portfolio insights.
            
            Data to analyze: {len(cleaned_data)} records
            Field mappings: {self._filter_application_mappings(mapped_fields)}
            Server insights: Use server expert insights from shared memory
            Strategic insights: Use manager's strategic insights from shared memory
            
            Classification Requirements:
            1. Identify applications, services, and software components
            2. Determine application types, versions, and technologies
            3. Assess business criticality and owner information
            4. Map applications to hosting infrastructure
            5. Identify application dependencies and integrations
            6. Generate application portfolio with business context
            7. Collaborate with server expert for hosting validation
            
            CRITICAL: Generate APPLICATION PORTFOLIO INSIGHTS by analyzing:
            - Technology stack diversity and standardization opportunities
            - Application architecture patterns (monolith/microservices/hybrid)
            - Business criticality distribution and risk assessment
            - Integration complexity and API modernization needs
            - License optimization and vendor consolidation opportunities
            - Technical debt assessment and modernization priorities
            - Performance and user experience optimization potential
            - Security and compliance gaps and recommendations
            
            Store application insights in shared memory for complete portfolio analysis.""",
            expected_output="""Comprehensive application inventory with business context and hosting relationships.
            
            PLUS: Application Portfolio Insights JSON containing:
            {
                "technology_analysis": {
                    "stack_diversity": "homogeneous/mixed/heterogeneous",
                    "modernization_score": "0-100",
                    "architecture_patterns": {},
                    "integration_complexity": "low/medium/high"
                },
                "business_analysis": {
                    "criticality_distribution": {},
                    "user_impact_assessment": {},
                    "business_value_score": "0-100"
                },
                "migration_strategy": {
                    "containerization_candidates": [],
                    "cloud_native_opportunities": [],
                    "legacy_modernization_priorities": [],
                    "6r_recommendations": {}
                },
                "optimization_opportunities": {
                    "license_consolidation": [],
                    "performance_improvements": [],
                    "security_enhancements": []
                }
            }""",
            agent=app_expert,
            context=[server_classification_task],
            tools=self._create_app_classification_tools()
        )
        
        # Device Classification Task - Network and device assets with topology insights
        device_classification_task = Task(
            description=f"""Classify network devices and infrastructure components AND generate comprehensive network topology insights.
            
            Data to analyze: {len(cleaned_data)} records
            Field mappings: {self._filter_device_mappings(mapped_fields)}
            Infrastructure context: Use server and app insights from shared memory
            Strategic insights: Use all previous insights from shared memory
            
            Classification Requirements:
            1. Identify network devices, security appliances, and infrastructure
            2. Determine device types, roles, and network functions
            3. Map network topology and device relationships
            4. Assess migration impact on network infrastructure
            5. Generate device inventory with network context
            6. Validate topology with server and application insights
            
            CRITICAL: Generate COMPREHENSIVE DISCOVERY INSIGHTS by synthesizing ALL crew analysis:
            - Network topology assessment and cloud migration readiness
            - Security infrastructure evaluation and modernization needs
            - Device consolidation and SDN transformation opportunities
            - Complete infrastructure dependency mapping
            - Migration wave planning and sequencing recommendations
            - Risk assessment across all infrastructure domains
            - Cost optimization through infrastructure rationalization
            - Business continuity and disaster recovery assessment
            
            FINAL TASK: Create UNIFIED DISCOVERY INSIGHTS that consolidate insights from:
            - Manager's strategic planning insights
            - Server expert's infrastructure insights  
            - Application expert's portfolio insights
            - Device expert's network topology insights
            
            Store consolidated discovery insights in shared memory for UI retrieval.""",
            expected_output="""Comprehensive device inventory with network topology and relationships.
            
            PLUS: Consolidated Discovery Insights JSON containing:
            {
                "executive_summary": {
                    "total_assets_analyzed": "count",
                    "infrastructure_readiness_score": "0-100",
                    "migration_complexity": "low/medium/high",
                    "recommended_strategy": "detailed_recommendation"
                },
                "infrastructure_analysis": {
                    "hosting_patterns": "from_server_expert",
                    "application_portfolio": "from_app_expert", 
                    "network_topology": "from_device_expert",
                    "integration_points": []
                },
                "migration_recommendations": {
                    "6r_strategy_distribution": {},
                    "wave_planning": [],
                    "risk_mitigation": [],
                    "quick_wins": []
                },
                "business_impact": {
                    "cost_optimization_potential": "percentage",
                    "performance_improvement_areas": [],
                    "compliance_and_security_gaps": [],
                    "modernization_roi_estimate": "high/medium/low"
                },
                "next_steps": {
                    "immediate_actions": [],
                    "phase_2_initiatives": [],
                    "long_term_strategy": []
                }
            }""",
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
                "planning": False,  # DISABLED: Causing loops
                "planning_llm": self.llm,  # Force planning to use our LLM too
                "memory": False,  # DISABLED: Causing APIStatusError loops
                "knowledge": None,  # DISABLED: Causing API errors
                "share_crew": False,  # DISABLED: Causing complexity
                "collaboration": True  # Re-enabled for proper agent coordination
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
