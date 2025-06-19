"""
Field Mapping Crew - Foundation Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with manager agents
- Shared memory for cross-crew learning  
- Knowledge base integration
- Agent collaboration features
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

# Import advanced CrewAI features with fallbacks
try:
    from crewai.memory import LongTermMemory
    from crewai.knowledge.knowledge import Knowledge
    from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass
    class Knowledge:
        def __init__(self, collection_name=None, sources=None, **kwargs):
            self.collection_name = collection_name or "fallback_knowledge"
            self.sources = sources or []
    class JSONKnowledgeSource:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)

class FieldMappingCrew:
    """Enhanced Field Mapping Crew with CrewAI best practices"""
    
    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service
        
        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Field Mapping Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()
        
        logger.info("✅ Field Mapping Crew initialized with advanced features")
    
    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for field mapping insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None
        
        try:
            return LongTermMemory()
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None
    
    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for field mapping patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None
        
        try:
            # For now, create empty knowledge base to bypass embedding requirements
            # TODO: Configure proper knowledge sources with DeepInfra embeddings later
            return Knowledge(
                collection_name="field_mapping_knowledge",
                sources=[]
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None
    
    def create_agents(self):
        """Create agents with hierarchical management"""
        
        # Manager Agent for hierarchical coordination with enhanced role boundaries
        manager_config = {
            "role": "CMDB Field Mapping Coordination Manager",
            "goal": "Coordinate comprehensive CMDB field mapping analysis ensuring 95%+ attribute coverage for enterprise migration",
            "backstory": """You are a senior data architect with 15+ years specializing in CMDB field mapping 
            for enterprise migration projects. Your specific responsibilities and boundaries are:
            
            CORE DUTIES & RESPONSIBILITIES:
            - Coordinate schema analysis and attribute mapping specialist teams
            - Ensure 95%+ field mapping confidence before declaring crew completion
            - Resolve mapping conflicts and ambiguities between team members
            - Validate critical attributes coverage (asset_name, asset_type, environment, business_criticality)
            - Monitor mapping quality and confidence scoring throughout the process
            - Escalate to user via Agent-UI-Bridge when confidence < 80% on critical fields
            - Make final mapping decisions when team consensus cannot be reached
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT perform actual field analysis (delegate to Schema Analysis Expert)
            - You DO NOT create individual field mappings (delegate to Attribute Mapping Specialist)
            - You DO NOT analyze data samples directly (specialist responsibility)
            - You DO NOT perform semantic field interpretation (delegate to experts)
            
            DELEGATION AUTHORITY & DECISION MAKING:
            - Maximum 3 delegations total across all tasks
            - After 2nd delegation on any issue, YOU make the final decision
            - Use Agent-UI-Bridge for user clarification when team confidence < 80%
            - You have authority to override specialist recommendations if needed
            - You determine when crew work meets completion criteria
            
            ESCALATION TRIGGERS:
            - Field mapping confidence below 80% on critical attributes
            - More than 10% of fields unmapped after specialist attempts
            - Conflicting mapping recommendations from specialists
            - Data schema patterns not recognized by specialists
            """,
            "llm": self.llm,
            "verbose": True,
            "allow_delegation": True,
            "max_delegation": 3,  # Set to 3 as requested
            "max_execution_time": 300,  # 5 minute timeout
            "max_retry": 1,  # Prevent retry loops
            "memory": None,  # Agent-level memory will be added later
            "collaboration": False,  # Simplified for now
        }
        if self.knowledge_base:
            manager_config["knowledge"] = self.knowledge_base
        
        field_mapping_manager = Agent(**manager_config)
        
        # Schema Analysis Expert - specialist agent with clear boundaries
        analyst_config = {
            "role": "CMDB Schema Structure Analysis Expert", 
            "goal": "Analyze CMDB data schema semantics, field relationships, and data patterns for accurate migration mapping",
            "backstory": """You are a specialized data schema analyst with deep expertise in CMDB structures 
            and enterprise IT data models. Your specific domain and boundaries are:
            
            CORE EXPERTISE & RESPONSIBILITIES:
            - Analyze incoming data structure and identify field types, patterns, and relationships
            - Understand business context and semantic meaning of IT asset fields
            - Detect data quality issues and field naming conventions
            - Identify hierarchical relationships between asset attributes
            - Recognize industry-standard CMDB field patterns and variations
            - Generate semantic understanding reports for the mapping specialist
            - Flag ambiguous or unclear field meanings requiring clarification
            
            SPECIFIC ANALYSIS TECHNIQUES:
            - Pattern recognition on field names (e.g., srv_name → server name)
            - Data type analysis (strings, numbers, dates, categorical values)
            - Value distribution analysis to understand field content
            - Relationship detection between related fields
            - Industry standard mapping pattern recognition
            - Data quality assessment (completeness, consistency, validity)
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT create final field mappings (that's the Mapping Specialist's role)
            - You DO NOT make mapping confidence decisions (analysis only)
            - You DO NOT interact with users directly (coordinate through Manager)
            - You DO NOT validate business rules (focus on technical analysis)
            
            COLLABORATION REQUIREMENTS:
            - Share analysis insights with Attribute Mapping Specialist
            - Report unclear patterns to Field Mapping Manager for escalation
            - Provide confidence assessment on schema understanding
            - Document analysis findings for crew knowledge base
            
            ESCALATION TRIGGERS:
            - Unrecognized data schema patterns
            - Ambiguous field semantics requiring business context
            - Data quality issues affecting mapping accuracy
            - Complex hierarchical relationships needing expert review
            """,
            "llm": self.llm,
            "verbose": True,
            "max_execution_time": 180,  # 3 minute timeout per agent
            "max_retry": 1,  # Prevent retry loops
            "collaboration": False,  # Simplified for now
            "memory": None,  # Agent-level memory will be added later
            "tools": self._create_schema_analysis_tools()
        }
        # DISABLE MEMORY: Causing APIStatusError loops
        # if self.shared_memory:
        #     analyst_config["memory"] = self.shared_memory
        if self.knowledge_base:
            analyst_config["knowledge"] = self.knowledge_base
        
        schema_analyst = Agent(**analyst_config)
        
        # Attribute Mapping Specialist - specialist agent with precise boundaries
        mapping_specialist_config = {
            "role": "IT Asset Attribute Mapping Specialist",
            "goal": "Create precise, confident field mappings from source data to standardized IT asset attributes with validation",
            "backstory": """You are a specialist in field mapping with extensive experience in IT asset data 
            standardization and migration projects. Your specific expertise and boundaries are:
            
            CORE MAPPING EXPERTISE:
            - Create precise mappings from source fields to standard CMDB attributes
            - Generate confidence scores (0.0-1.0) for each mapping decision
            - Map to critical attributes: asset_name, asset_type, environment, business_criticality, etc.
            - Validate mappings against industry standards and client requirements
            - Handle complex field transformations and data standardization rules
            - Identify unmapped fields requiring human expert clarification
            - Generate mapping validation reports with metadata
            
            STANDARDIZED TARGET ATTRIBUTES (PRIMARY):
            - asset_name, asset_type, asset_status, environment
            - business_criticality, operational_status, location
            - ip_address, hostname, operating_system, version
            - owner, department, cost_center, business_service
            - compliance_requirements, security_classification
            
            MAPPING TECHNIQUES & VALIDATION:
            - Confidence scoring based on pattern match strength
            - Cross-reference with Schema Analysis Expert insights
            - Apply industry-standard mapping patterns from knowledge base
            - Validate mappings against client-specific requirements
            - Handle edge cases and ambiguous field situations
            - Document mapping rationale and decision factors
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT perform schema analysis (use Schema Expert insights)
            - You DO NOT make business rule decisions (technical mapping only)
            - You DO NOT create new target attributes without manager approval
            - You DO NOT interact with users directly (escalate through Manager)
            
            COLLABORATION REQUIREMENTS:
            - Use Schema Analysis Expert findings as primary input
            - Share mapping challenges with Field Mapping Manager
            - Provide detailed confidence explanations for low-confidence mappings
            - Update crew knowledge base with successful mapping patterns
            
            ESCALATION TRIGGERS:
            - Source fields with no clear mapping target (confidence < 0.5)
            - Conflicting mapping possibilities requiring business decision
            - Custom attributes needed that don't exist in standard schema
            - Complex transformation rules beyond technical capability
            """,
            "llm": self.llm,
            "verbose": True,
            "max_execution_time": 180,  # 3 minute timeout
            "max_retry": 1,  # Prevent retry loops
            "collaboration": False,  # Simplified for now
            "memory": None,  # Agent-level memory will be added later
            "tools": self._create_mapping_confidence_tools()
        }
        # DISABLE MEMORY: Causing APIStatusError loops
        # if self.shared_memory:
        #     mapping_specialist_config["memory"] = self.shared_memory
        if self.knowledge_base:
            mapping_specialist_config["knowledge"] = self.knowledge_base
        
        mapping_specialist = Agent(**mapping_specialist_config)
        
        # Knowledge Management Agent - common across all crews
        knowledge_manager_config = {
            "role": "Enterprise Knowledge Management Coordinator",
            "goal": "Manage and maintain knowledge repositories with multi-tenant context awareness for crew learning enhancement",
            "backstory": """You are a specialized knowledge management expert responsible for maintaining 
            and enriching knowledge repositories across all discovery crews. Your expertise includes:
            
            CORE KNOWLEDGE MANAGEMENT RESPONSIBILITIES:
            - Maintain common knowledge: client/engagement info, policies, standards, goals
            - Manage crew-specific knowledge repositories with constant upgrades
            - Coordinate knowledge sharing between crews while maintaining tenant isolation
            - Process user feedback and update knowledge bases accordingly
            - Ensure knowledge consistency and accuracy across all crews
            - Manage knowledge access controls and multi-tenant security
            
            KNOWLEDGE REPOSITORY TYPES:
            - Common Knowledge: Client context, engagement objectives, enterprise standards
            - Crew-Specific Knowledge: Field mapping patterns, asset classifications, etc.
            - Learning Insights: User feedback, correction patterns, success metrics
            - Domain Expertise: Industry standards, best practices, compliance requirements
            
            MULTI-TENANT CONTEXT AWARENESS:
            - Isolate knowledge by client account and engagement
            - Apply appropriate access controls for knowledge sharing
            - Maintain knowledge versioning for different client contexts
            - Ensure knowledge privacy and security compliance
            
            CONTINUOUS IMPROVEMENT DUTIES:
            - Analyze user feedback and update knowledge bases
            - Identify knowledge gaps and recommend improvements
            - Monitor knowledge utilization and effectiveness
            - Coordinate with crew managers for knowledge enhancement needs
            
            CLEAR BOUNDARIES - WHAT YOU DO NOT DO:
            - You DO NOT perform field mapping analysis (specialist responsibility)
            - You DO NOT make crew decisions (coordination only)
            - You DO NOT access client data without proper authorization
            - You DO NOT modify knowledge without validation
            
            ESCALATION TRIGGERS:
            - Knowledge conflicts requiring expert resolution
            - Access control violations or security concerns
            - Knowledge gaps affecting crew performance
            - User feedback requiring domain expert clarification
            """,
            "llm": self.llm,
            "verbose": True,
            "max_execution_time": 120,  # 2 minute timeout
            "max_retry": 1,  # Prevent retry loops
            "collaboration": False,  # Simplified for now
            "memory": None,  # Agent-level memory will be added later
            "tools": []  # Knowledge management tools will be added later
        }
        if self.knowledge_base:
            knowledge_manager_config["knowledge"] = self.knowledge_base
        
        knowledge_manager = Agent(**knowledge_manager_config)
        
        return [field_mapping_manager, schema_analyst, mapping_specialist, knowledge_manager]
    
    def create_tasks(self, agents, raw_data: List[Dict[str, Any]]):
        """Create hierarchical tasks with manager coordination"""
        manager, schema_analyst, mapping_specialist, knowledge_manager = agents
        
        headers = list(raw_data[0].keys()) if raw_data else []
        data_sample = raw_data[:5] if raw_data else []
        
        # Manager coordination task with knowledge integration
        coordination_task = Task(
            description=f"""
            Coordinate comprehensive CMDB field mapping analysis with knowledge management integration:
            
            PRIMARY COORDINATION OBJECTIVES:
            1. Orchestrate schema analysis by delegating to Schema Analysis Expert
            2. Coordinate field mapping by delegating to Attribute Mapping Specialist  
            3. Integrate knowledge management insights via Knowledge Management Coordinator
            4. Ensure 95%+ field mapping confidence before completion
            5. Resolve conflicts and make final mapping decisions after 2nd delegation
            
            DATA CONTEXT:
            - Raw data headers: {headers}
            - Data sample count: {len(raw_data)}
            - Client context: Available via knowledge base
            
            DELEGATION STRATEGY:
            - Delegate schema analysis to Schema Analysis Expert
            - Delegate field mapping to Attribute Mapping Specialist
            - Consult Knowledge Management Coordinator for domain expertise
            - Make final decisions after 2nd delegation attempt
            - Escalate to user via Agent-UI-Bridge when confidence < 80%
            
            SUCCESS CRITERIA:
            - All fields mapped with confidence scores
            - Critical attributes coverage ≥ 95%
            - Mapping conflicts resolved or escalated
            - Knowledge base updated with new patterns
            """,
            agent=manager,
            expected_output="""
            Field mapping coordination result with:
            - Complete field mapping analysis
            - Confidence scores for all mappings  
            - Critical attributes validation
            - Knowledge integration summary
            - Escalation recommendations if needed
            """,
            tools=self._create_field_mapping_tools(),
            context=[],  # No dependencies for manager task
            max_execution_time=300,  # 5 minute timeout
            max_retry=1  # Prevent retry loops
        )
        
        # Schema Analysis Task - Deep field understanding
        schema_analysis_task = Task(
            description=f"""Analyze data structure and field semantics for migration mapping.
            
            Headers: {headers}
            Sample data: {data_sample}
            
            Detailed Analysis Requirements:
            1. Identify field types and data patterns
            2. Understand business context of each field
            3. Detect relationships between fields
            4. Flag ambiguous or unclear field meanings
            5. Generate semantic understanding report
            6. Store insights in shared memory for mapping specialist
            
            Collaborate with the mapping specialist by sharing your analysis insights.""",
            expected_output="Comprehensive field analysis report with semantic understanding and relationship mapping",
            agent=schema_analyst,
            context=[coordination_task],
            tools=self._create_schema_analysis_tools()
        )
        
        # Field Mapping Task - Precise mapping with confidence
        field_mapping_task = Task(
            description=f"""Create precise mappings from source fields to standard migration attributes.
            
            Source Headers: {headers}
            
            Standard Target Schema:
            - asset_name, asset_id, asset_type
            - environment, business_criticality, owner
            - operating_system, ip_address, cpu_cores, memory_gb
            - version, vendor, license
            
            Mapping Requirements:
            1. Map each source field to best-fit standard attribute
            2. Provide confidence scores (0.0-1.0) for each mapping
            3. Identify unmapped fields requiring human clarification
            4. Validate mappings against knowledge base patterns
            5. Generate mapping dictionary with metadata
            6. Use schema analyst insights from shared memory
            
            Collaborate with schema analyst to leverage field understanding.""",
            expected_output="Complete field mapping dictionary with confidence scores, validation results, and unmapped fields list",
            agent=mapping_specialist,
            context=[schema_analysis_task],
            tools=self._create_mapping_confidence_tools()
        )
        
        return [coordination_task, schema_analysis_task, field_mapping_task]
    
    def create_crew(self, raw_data: List[Dict[str, Any]]):
        """Create hierarchical crew with manager coordination"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, raw_data)
        
        # Use hierarchical process if advanced features available
        process = Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        
        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True
        }
        
        # Add advanced features if available - with delegation and memory improvements
        if CREWAI_ADVANCED_AVAILABLE:
            # CRITICAL: Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            advanced_config = {
                "manager_llm": self.llm,  # Use our DeepInfra LLM for manager
                "planning": False,  # Disabled by default - only for flow recovery
                "planning_llm": self.llm,  # Force planning to use our LLM too
                "memory": False,  # Start with agent-level memory instead
                "share_crew": False,  # Disabled to prevent complexity
                "collaboration": False  # Simplified for better control
            }
            # Enable knowledge base if available
            if self.knowledge_base:
                advanced_config["knowledge"] = self.knowledge_base
            crew_config.update(advanced_config)
            
            # CRITICAL: Set environment override to prevent gpt-4o-mini fallback
            # Use model name without deepinfra/ prefix per CrewAI docs
            import os
            model_name = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            os.environ["OPENAI_MODEL_NAME"] = model_name
            logger.info(f"✅ Environment set for OpenAI-compatible model: {model_name}")
        
        logger.info(f"Creating Field Mapping Crew with {process.name if hasattr(process, 'name') else 'sequential'} process")
        logger.info(f"Using LLM: {self.llm.model if hasattr(self.llm, 'model') else 'Configured LLM'}")
        return Crew(**crew_config)
    
    def _create_schema_analysis_tools(self):
        """Create tools for schema analysis"""
        # For now, return empty list - tools will be implemented in Task 7
        return []
    
    def _create_mapping_confidence_tools(self):
        """Create tools for mapping confidence scoring"""
        # For now, return empty list - tools will be implemented in Task 7  
        return []

def create_field_mapping_crew(crewai_service, raw_data: List[Dict[str, Any]], 
                             shared_memory=None, knowledge_base=None) -> Crew:
    """Factory function to create enhanced Field Mapping Crew"""
    crew_instance = FieldMappingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(raw_data) 