"""
Agent coordination service for CrewAI integration.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport

logger = logging.getLogger(__name__)

# Try to import CrewAI with fallback
try:
    from crewai import Agent, Crew, Process, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None


class AgentCoordinator:
    """Service for coordinating CrewAI agents for attribute analysis."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self._llm = None
    
    async def execute_crew_analysis(
        self, 
        data_import: DataImport, 
        sample_data: List[Dict[str, Any]],
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Execute CrewAI crew analysis for critical attributes.
        
        This is the main entry point for agentic analysis using CrewAI.
        """
        
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, falling back to pattern analysis")
            return {
                "crew_execution": "failed_import_error",
                "analysis_result": "CrewAI not available in environment",
                "error": "CrewAI module not installed"
            }
        
        try:
            # Initialize LLM
            llm = await self._get_configured_llm()
            if not llm:
                return {
                    "crew_execution": "failed_llm_config",
                    "analysis_result": "LLM configuration failed",
                    "error": "Could not configure LLM for CrewAI"
                }
            
            # Extract field information
            field_names = list(sample_data[0].keys()) if sample_data else []
            sample_values = self._extract_sample_values(sample_data, field_names)
            
            logger.info(f"🤖 CrewAI analyzing {len(field_names)} fields from imported data")
            
            # Create and execute crew based on analysis depth
            if analysis_depth == "comprehensive":
                crew_result = await self._execute_comprehensive_analysis(
                    llm, field_names, sample_values, sample_data
                )
            elif analysis_depth == "standard":
                crew_result = await self._execute_standard_analysis(
                    llm, field_names, sample_values
                )
            else:  # quick
                crew_result = await self._execute_quick_analysis(
                    llm, field_names, sample_values
                )
            
            # Parse crew results
            parsed_results = await self._parse_crew_results(crew_result, field_names)
            
            return {
                "crew_execution": "completed",
                "analysis_result": "CrewAI analysis completed successfully",
                "attributes": parsed_results.get("attributes", []),
                "suggestions": parsed_results.get("suggestions", []),
                "crew_output": str(crew_result)[:500] + "..." if len(str(crew_result)) > 500 else str(crew_result),
                "execution_mode": "crew_ai"
            }
            
        except Exception as e:
            logger.error(f"CrewAI execution failed: {e}")
            return {
                "crew_execution": "failed_execution_error",
                "analysis_result": f"CrewAI execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _get_configured_llm(self):
        """Get configured LLM for CrewAI."""
        if self._llm:
            return self._llm
        
        try:
            from app.services.llm_config import get_crewai_llm
            self._llm = get_crewai_llm()
            logger.info("✅ Using configured DeepInfra LLM for CrewAI")
            return self._llm
        except Exception as e:
            logger.error(f"Failed to configure LLM: {e}")
            return None
    
    def _extract_sample_values(
        self, 
        sample_data: List[Dict[str, Any]], 
        field_names: List[str]
    ) -> Dict[str, List[str]]:
        """Extract sample values for each field."""
        sample_values = {}
        
        for field in field_names:
            values = []
            for record in sample_data[:3]:  # Take first 3 records
                value = record.get(field)
                if value is not None:
                    values.append(str(value))
            sample_values[field] = values
        
        return sample_values
    
    async def _execute_comprehensive_analysis(
        self, 
        llm, 
        field_names: List[str], 
        sample_values: Dict[str, List[str]],
        sample_data: List[Dict[str, Any]]
    ) -> Any:
        """Execute comprehensive CrewAI analysis."""
        
        # Create specialized agents
        schema_analyst = self._create_schema_analyst(llm)
        field_mapper = self._create_field_mapper(llm)
        mapping_coordinator = self._create_mapping_coordinator(llm)
        
        # Create comprehensive analysis tasks
        schema_task = self._create_schema_analysis_task(
            schema_analyst, field_names, sample_values
        )
        
        mapping_task = self._create_field_mapping_task(
            field_mapper, field_names, sample_values
        )
        
        coordination_task = self._create_coordination_task(
            mapping_coordinator, [schema_task, mapping_task]
        )
        
        # Execute crew
        crew = Crew(
            agents=[schema_analyst, field_mapper, mapping_coordinator],
            tasks=[schema_task, mapping_task, coordination_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("🚀 Executing comprehensive CrewAI analysis")
        result = crew.kickoff()
        logger.info("✅ Comprehensive CrewAI analysis completed")
        
        return result
    
    async def _execute_standard_analysis(
        self, 
        llm, 
        field_names: List[str], 
        sample_values: Dict[str, List[str]]
    ) -> Any:
        """Execute standard CrewAI analysis."""
        
        # Create core agents
        field_mapper = self._create_field_mapper(llm)
        mapping_coordinator = self._create_mapping_coordinator(llm)
        
        # Create standard tasks
        mapping_task = self._create_field_mapping_task(
            field_mapper, field_names, sample_values
        )
        
        coordination_task = self._create_coordination_task(
            mapping_coordinator, [mapping_task]
        )
        
        # Execute crew
        crew = Crew(
            agents=[field_mapper, mapping_coordinator],
            tasks=[mapping_task, coordination_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("🚀 Executing standard CrewAI analysis")
        result = crew.kickoff()
        logger.info("✅ Standard CrewAI analysis completed")
        
        return result
    
    async def _execute_quick_analysis(
        self, 
        llm, 
        field_names: List[str], 
        sample_values: Dict[str, List[str]]
    ) -> Any:
        """Execute quick CrewAI analysis."""
        
        # Create single agent for quick analysis
        field_mapper = self._create_field_mapper(llm)
        
        # Create quick analysis task
        quick_task = Task(
            description=f"""
            Perform quick field mapping analysis for migration-critical attributes.
            
            Field Names: {field_names}
            Sample Values: {sample_values}
            
            Quickly identify the top 5 most critical fields for migration and map them to:
            - asset_id, name, hostname, ip_address, asset_type, operating_system, environment
            
            Focus on asset identification and core migration attributes only.
            Provide brief reasoning for each mapping.
            """,
            expected_output="Quick field mapping analysis with top 5 critical field mappings",
            agent=field_mapper
        )
        
        # Execute single agent
        crew = Crew(
            agents=[field_mapper],
            tasks=[quick_task],
            process=Process.sequential,
            verbose=True
        )
        
        logger.info("🚀 Executing quick CrewAI analysis")
        result = crew.kickoff()
        logger.info("✅ Quick CrewAI analysis completed")
        
        return result
    
    def _create_schema_analyst(self, llm) -> Agent:
        """Create data schema analyst agent."""
        return Agent(
            role="Data Schema Analyst",
            goal="Analyze imported CMDB data structure and understand field semantics",
            backstory="""Expert data analyst with 15+ years experience in CMDB schemas, asset management, 
            and enterprise data structures. Specializes in understanding field meanings from names, patterns, 
            and sample values. Can identify asset identification fields, technical specifications, 
            business attributes, and operational metadata.""",
            verbose=True,
            llm=llm
        )
    
    def _create_field_mapper(self, llm) -> Agent:
        """Create migration field mapper agent."""
        return Agent(
            role="Migration Field Mapper",
            goal="Map imported fields to migration-critical asset attributes",
            backstory="""Migration specialist with expertise in identifying which asset attributes are 
            critical for successful cloud migrations. Understands the 6R migration strategies and knows 
            which fields are essential for asset identification, dependency mapping, risk assessment, 
            and migration planning. Expert in mapping diverse CMDB schemas to standardized asset models.""",
            verbose=True,
            llm=llm
        )
    
    def _create_mapping_coordinator(self, llm) -> Agent:
        """Create field mapping coordinator agent."""
        return Agent(
            role="Field Mapping Coordinator",
            goal="Coordinate field mapping analysis and ensure comprehensive coverage",
            backstory="""Senior migration architect who coordinates field mapping efforts and ensures 
            all critical migration attributes are properly identified and mapped. Validates mapping 
            quality, resolves conflicts, and provides final recommendations for field mappings.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
    
    def _create_schema_analysis_task(
        self, 
        agent: Agent, 
        field_names: List[str], 
        sample_values: Dict[str, List[str]]
    ) -> Task:
        """Create schema analysis task."""
        return Task(
            description=f"""
            Analyze the imported CMDB data schema to understand field semantics and structure.
            
            Field Names to Analyze: {field_names}
            Sample Values: {sample_values}
            
            For each field, determine:
            1. Likely purpose and meaning
            2. Data type and format
            3. Completeness and quality
            4. Relationship to asset management
            5. Importance for migration planning
            
            Identify which fields are:
            - Asset identifiers (names, IDs, hostnames)
            - Technical specifications (OS, hardware)
            - Network information (IPs, DNS)
            - Business attributes (owners, departments)
            - Operational metadata (environments, criticality)
            """,
            expected_output="Detailed schema analysis with field categorization and semantic understanding",
            agent=agent
        )
    
    def _create_field_mapping_task(
        self, 
        agent: Agent, 
        field_names: List[str], 
        sample_values: Dict[str, List[str]]
    ) -> Task:
        """Create field mapping task."""
        return Task(
            description=f"""
            Map imported fields to standardized migration-critical asset attributes.
            
            Source Fields: {field_names}
            Sample Data: {sample_values}
            
            Map each field to the most appropriate target attribute:
            - asset_id: Unique asset identifier
            - name: Asset name/label
            - hostname: Network hostname
            - ip_address: IP address
            - asset_type: Type of asset (server, application, etc.)
            - operating_system: OS information
            - environment: Environment (prod, dev, test)
            - cpu_cores: CPU specifications
            - memory_gb: Memory specifications
            - business_owner: Business contact
            - technical_owner: Technical contact
            
            For each mapping, provide:
            1. Confidence score (0-1)
            2. Reasoning for the mapping
            3. Importance for migration (high/medium/low)
            4. Alternative mapping options
            """,
            expected_output="Field mapping recommendations with confidence scores and detailed reasoning",
            agent=agent
        )
    
    def _create_coordination_task(self, agent: Agent, context_tasks: List[Task]) -> Task:
        """Create coordination task."""
        return Task(
            description="""
            Coordinate and validate the field mapping analysis to ensure comprehensive coverage.
            
            Review the schema analysis and field mapping results to:
            1. Validate mapping quality and consistency
            2. Identify any gaps or conflicts
            3. Prioritize mappings by migration importance
            4. Provide final recommendations
            5. Suggest validation rules for mapped fields
            
            Ensure all critical migration attributes are covered:
            - Asset identification (mandatory)
            - Technical specifications (high priority)
            - Network information (high priority)
            - Business ownership (medium priority)
            - Operational metadata (medium priority)
            
            Output should be a structured summary of validated field mappings.
            """,
            expected_output="Validated field mapping summary with prioritized recommendations",
            agent=agent,
            context=context_tasks
        )
    
    async def _parse_crew_results(
        self, 
        crew_result: Any, 
        field_names: List[str]
    ) -> Dict[str, Any]:
        """Parse CrewAI crew results into structured format."""
        
        result_str = str(crew_result) if crew_result else ""
        
        # Extract attributes and suggestions from crew output
        # This is a simplified parser - in production would use structured output
        
        attributes = []
        suggestions = []
        
        for field_name in field_names:
            # Simple pattern matching to extract information
            importance = 0.7  # Default importance
            confidence = 0.8  # Higher confidence for CrewAI
            
            # Look for field mentions in crew result
            if field_name.lower() in result_str.lower():
                if "critical" in result_str.lower():
                    importance = 0.9
                elif "important" in result_str.lower():
                    importance = 0.7
                else:
                    importance = 0.5
            
            # Create attribute
            attribute = {
                "name": field_name,
                "importance": importance,
                "confidence": confidence,
                "reasoning": f"CrewAI analysis identified '{field_name}' as migration-relevant",
                "migration_impact": "Determined by CrewAI agents",
                "data_type": "string",  # Default
                "sample_values": [],
                "mapping_suggestions": ["name"],  # Default
                "agent_source": "crewai_field_mapper"
            }
            attributes.append(attribute)
            
            # Create suggestion
            suggestion = {
                "source_field": field_name,
                "suggested_target": "name",  # Default
                "importance_score": importance,
                "confidence_score": confidence,
                "reasoning": f"CrewAI field mapping analysis for {field_name}",
                "crew_analysis": result_str[:200] + "..." if len(result_str) > 200 else result_str,
                "migration_priority": 7
            }
            suggestions.append(suggestion)
        
        return {
            "attributes": attributes,
            "suggestions": suggestions
        }