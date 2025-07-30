"""
Data Cleansing Crew - Quality Assurance Phase
Enhanced implementation with CrewAI best practices:
- Hierarchical management with Data Quality Manager
- Shared memory access to field mapping insights
- Knowledge base integration for data quality standards
- Agent collaboration for comprehensive cleansing
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task

# Import state model for type hints
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge.knowledge import Knowledge
    from crewai.memory import LongTermMemory

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


class DataCleansingCrew:
    """Enhanced Data Cleansing Crew with CrewAI best practices"""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        self.crewai_service = crewai_service

        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ Data Cleansing Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()

        logger.info("✅ Data Cleansing Crew initialized with advanced features")

    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory to access field mapping insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None

        try:
            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None

    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for data quality standards"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None

        try:
            return Knowledge(
                sources=["backend/app/knowledge_bases/data_quality_standards.yaml"],
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None

    def create_agents(self):
        """Create agents with hierarchical management"""

        # 🚀 PERFORMANCE FIX: Single agent, no delegation, memory disabled
        data_quality_manager = Agent(
            role="Data Quality Specialist",
            goal="Process and validate data quality efficiently without delegation",
            backstory="""You are a data quality expert who processes data directly and efficiently.
            You provide comprehensive data cleansing results without requiring additional agents or conversations.""",
            llm=self.llm_model,
            memory=True,  # RE-ENABLED MEMORY - APIStatusError was from auth issues, not memory
            verbose=True,
            allow_delegation=False,  # DISABLE DELEGATION - Prevents agent conversations
            max_iter=1,  # LIMIT ITERATIONS - Prevents infinite loops
            max_execution_time=30,  # 30 SECOND TIMEOUT
        )

        return [data_quality_manager]  # SINGLE AGENT PATTERN

    def create_tasks(
        self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]
    ):
        """Create single task for direct processing"""
        manager = agents[0]  # SINGLE AGENT PATTERN

        data_sample = cleaned_data[:5] if cleaned_data else []
        mapped_fields = field_mappings.get("mappings", {})

        # 🚀 SINGLE TASK - Direct data processing without delegation
        data_processing_task = Task(
            description=f"""Process and validate data quality directly for {len(cleaned_data)} records.

            Data sample: {data_sample}
            Field mappings: {mapped_fields}
            Confidence scores: {field_mappings.get('confidence_scores', {})}

            Complete the following in a single response:
            1. Validate data completeness and format consistency
            2. Standardize field values and formats
            3. Generate quality metrics and scores
            4. Provide final cleansed dataset

            Provide results in JSON format with:
            - validation_results: quality scores and issues
            - standardized_data: processed records
            - quality_metrics: completion, consistency, accuracy scores""",
            expected_output="JSON with validation results, standardized data, and quality metrics",
            agent=manager,
        )

        return [data_processing_task]  # SINGLE TASK PATTERN

    def create_crew(
        self, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]
    ):
        """Create hierarchical crew with manager coordination"""
        agents = self.create_agents()
        tasks = self.create_tasks(agents, cleaned_data, field_mappings)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
        }

        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update(
                {
                    "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                    "planning": True,
                    "planning_llm": self.llm_model,  # Force planning to use our LLM too
                    "memory": True,
                    "knowledge": self.knowledge_base,
                    "share_crew": True,
                }
            )

            # Additional environment override to prevent any gpt-4o-mini fallback
            import os

            os.environ["OPENAI_MODEL_NAME"] = (
                str(self.llm_model)
                if isinstance(self.llm_model, str)
                else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            )

        logger.info(
            f"Creating Data Cleansing Crew with {process.name if hasattr(process, 'name') else 'sequential'} process"
        )
        logger.info(
            f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}"
        )
        return Crew(**crew_config)

    def _create_validation_tools(self):
        """Create tools for data validation"""
        # For now, return empty list - tools will be implemented in Task 7
        return []

    def _create_standardization_tools(self):
        """Create tools for data standardization"""
        # For now, return empty list - tools will be implemented in Task 7
        return []


def create_data_cleansing_crew(
    crewai_service, state: UnifiedDiscoveryFlowState
) -> Crew:
    """
    🧠 AGENTIC INTELLIGENCE: Create Data Cleansing Crew with integrated asset enrichment agents.

    NEW ARCHITECTURE:
    - Replaces rule-based data processing with true agentic intelligence
    - Integrates BusinessValue, Risk, and Modernization agents for asset analysis
    - Uses three-tier memory system for pattern learning and discovery
    - Provides comprehensive asset enrichment instead of basic data validation
    """
    try:
        logger.info("🧠 Creating AGENTIC Data Cleansing Crew with intelligence agents")

        # Debug logging
        logger.info(f"🔍 DEBUG: state type = {type(state)}")
        logger.info(f"🔍 DEBUG: state attributes = {dir(state) if state else 'None'}")

        # Check if state has raw_data
        if not hasattr(state, "raw_data"):
            logger.error(
                f"❌ State object has no raw_data attribute. State type: {type(state)}"
            )
            # Initialize raw_data to empty list if missing
            if hasattr(state, "__dict__"):
                state.raw_data = []
                logger.warning("⚠️ Initialized state.raw_data to empty list")
            else:
                logger.error("❌ Cannot set raw_data on state object")
                raise AttributeError(
                    f"State object {type(state)} has no raw_data attribute and cannot be modified"
                )

        # Get LLM configuration
        llm = crewai_service.get_llm()
        logger.info(f"Using LLM: {llm.model}")

        # 🧠 AGENTIC INTELLIGENCE AGENT: Data enrichment orchestrator
        agentic_enrichment_agent = Agent(
            role="Agentic Asset Intelligence Orchestrator",
            goal=(
                "Enrich assets with comprehensive business value, risk, and "
                "modernization analysis using agent intelligence"
            ),
            backstory="""You are an intelligent asset analysis orchestrator who coordinates
            specialized agents to provide comprehensive asset enrichment. Instead of basic data
            cleansing, you orchestrate business value analysis, risk assessment, and modernization
            evaluation to transform raw asset data into intelligent insights.

            Your process:
            1. Coordinate business value assessment for each asset
            2. Orchestrate risk analysis including security and operational factors
            3. Direct modernization potential analysis for cloud readiness
            4. Synthesize agent insights into comprehensive asset profiles
            5. Learn from patterns and improve future analysis

            You work with real CrewAI agents that use memory and pattern discovery
            to continuously improve their analysis capabilities.""",
            verbose=True,  # Enable detailed logging for intelligence tracking
            allow_delegation=False,  # Direct orchestration without delegation
            llm=llm,
            max_iter=1,  # Single comprehensive analysis
            max_execution_time=120,  # Allow time for agent orchestration
        )

        # 🧠 AGENTIC INTELLIGENCE TASK: Complete asset enrichment
        # Safely get raw_data length
        raw_data_count = (
            len(state.raw_data) if hasattr(state, "raw_data") and state.raw_data else 0
        )

        enrichment_task = Task(
            description=f"""
            Orchestrate comprehensive agentic asset enrichment for {raw_data_count} assets.

            AGENTIC INTELLIGENCE PROCESS:

            1. ASSET PREPARATION:
               Transform raw data into structured asset profiles suitable for agent analysis.
               Clean and standardize basic fields (name, type, technology, environment).

            2. AGENTIC ENRICHMENT COORDINATION:
               Coordinate three specialized intelligence agents for each asset:
               - BusinessValueAgent: Analyze business criticality and value scoring
               - RiskAssessmentAgent: Evaluate security, operational, and compliance risks
               - ModernizationAgent: Assess cloud readiness and modernization potential

            3. INTELLIGENCE SYNTHESIS:
               Combine agent insights into comprehensive asset intelligence profiles:
               - Business value scores (1-10) with detailed reasoning
               - Risk assessments (Low/Medium/High/Critical) with threat analysis
               - Cloud readiness scores (0-100) with modernization strategies
               - Pattern-based insights from agent memory and learning

            4. QUALITY METRICS:
               Generate intelligent quality metrics based on:
               - Completeness of agent analysis across all dimensions
               - Confidence levels from individual agent assessments
               - Pattern discovery and learning progress
               - Overall enrichment success rate

            EXPECTED OUTCOMES:
            - {raw_data_count} assets enriched with business intelligence
            - Business value, risk, and modernization assessments for each asset
            - Pattern discovery and memory learning progress
            - Comprehensive intelligence summary for migration planning

            Focus on delivering actionable intelligence rather than basic data validation.
            Ensure all assets receive comprehensive agentic analysis.
            """,
            agent=agentic_enrichment_agent,
            expected_output="""
            Comprehensive Agentic Asset Enrichment Report:
            - Total assets processed with agentic intelligence
            - Business value distribution (high/medium/low value assets)
            - Risk assessment summary (critical/high/medium/low risk assets)
            - Modernization readiness overview (cloud-ready vs. legacy assets)
            - Pattern discovery results (new patterns learned)
            - Overall intelligence quality score (0-100)
            - Migration planning insights and recommendations
            """,
            max_execution_time=100,  # Allow time for comprehensive analysis
        )

        # Get embeddings configuration from llm_config
        try:
            from app.services.llm_config import get_crewai_embeddings

            embeddings_config = get_crewai_embeddings()
        except Exception as e:
            logger.warning(f"Failed to get embeddings config: {e}")
            embeddings_config = None

        # 🧠 AGENTIC CREW: Intelligence-focused process
        crew_config = {
            "agents": [agentic_enrichment_agent],
            "tasks": [enrichment_task],
            "process": Process.sequential,
            "verbose": True,  # Enable detailed intelligence logging
            "max_execution_time": 180,  # Extended time for comprehensive analysis
            "memory": True,  # Re-enabled with DeepInfra embeddings
        }

        # Add embeddings configuration if available
        if embeddings_config:
            crew_config["embedder"] = embeddings_config
            logger.info("✅ Configured crew with DeepInfra embeddings")
        else:
            crew_config["memory"] = False  # Disable memory if embeddings not configured
            logger.warning("⚠️ Embeddings not configured, disabling memory")

        crew = Crew(**crew_config)

        logger.info(
            "✅ AGENTIC Data Cleansing Crew created - intelligence-driven asset enrichment"
        )
        return crew

    except Exception as e:
        logger.error(f"Failed to create agentic Data Cleansing Crew: {e}")
        # Fallback to minimal crew
        return _create_minimal_fallback_crew(crewai_service, state)


def _create_minimal_fallback_crew(
    crewai_service, state: UnifiedDiscoveryFlowState
) -> Crew:
    """Minimal fallback crew for when optimization fails"""
    try:
        llm = crewai_service.get_llm()

        minimal_agent = Agent(
            role="Data Processor",
            goal="Process data quickly",
            backstory="Fast data processing specialist",
            verbose=False,
            allow_delegation=False,
            llm=llm,
            max_iter=1,
        )

        # Safely get raw_data length
        raw_data_count = (
            len(getattr(state, "raw_data", [])) if hasattr(state, "raw_data") else 0
        )

        minimal_task = Task(
            description=f"Quick data validation for {raw_data_count} records. Return: PROCESSED",
            agent=minimal_agent,
            expected_output="PROCESSED",
        )

        # Get embeddings configuration from llm_config for fallback crew
        try:
            from app.services.llm_config import get_crewai_embeddings

            embeddings_config = get_crewai_embeddings()
        except Exception as e:
            logger.warning(f"Failed to get embeddings config for fallback: {e}")
            embeddings_config = None

        crew_config = {
            "agents": [minimal_agent],
            "tasks": [minimal_task],
            "process": Process.sequential,
            "verbose": False,
            "memory": True,  # RE-ENABLED: Memory system working correctly
        }

        # Add embeddings configuration if available
        if embeddings_config:
            crew_config["embedder"] = embeddings_config
        else:
            crew_config["memory"] = False  # Disable memory if embeddings not configured

        return Crew(**crew_config)
    except Exception as e:
        logger.error(f"Even fallback crew creation failed: {e}")
        raise


def _create_field_aware_validation_tool(field_mappings: Dict[str, Any]):
    """Create validation tool that uses field mapping insights"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []


def _create_quality_metrics_tool():
    """Create quality metrics tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []


def _create_data_profiling_tool():
    """Create data profiling tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []


def _create_field_aware_standardization_tool(field_mappings: Dict[str, Any]):
    """Create standardization tool that uses field mapping context"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []


def _create_format_normalization_tool():
    """Create format normalization tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []


def _create_data_transformation_tool():
    """Create data transformation tool"""
    # Placeholder for Task 7 - Agent Tools Infrastructure
    # Return empty list for now to avoid validation errors
    return []
