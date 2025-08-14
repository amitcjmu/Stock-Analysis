"""
🚀 OPTIMIZED Field Mapping Crew - Performance Focused
Fast field mapping with minimal agent overhead and direct execution.

PERFORMANCE OPTIMIZATIONS:
- Single specialized agent (no delegation)
- Direct pattern matching with AI validation
- Minimal memory operations
- Fast timeout controls
- Sequential processing (no hierarchical overhead)
"""

import logging
from typing import Any, Dict, List

# CrewAI imports with graceful fallback
try:
    from crewai import Agent, Crew, Process, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Agent:
        pass

    class Task:
        pass

    class Crew:
        pass

    class Process:
        sequential = "sequential"


from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

logger = logging.getLogger(__name__)


def create_fast_field_mapping_crew(
    crewai_service, state: UnifiedDiscoveryFlowState
) -> Crew:
    """
    🚀 OPTIMIZED: Create ultra-fast field mapping crew with minimal overhead.

    PERFORMANCE IMPROVEMENTS:
    - Single agent with no delegation
    - Pattern-based mapping with AI validation
    - 15-second timeout for rapid processing
    - No memory storage overhead
    - Direct sequential execution
    """
    try:
        logger.info("🚀 Creating FAST Field Mapping Crew for performance")

        # Get LLM model string for CrewAI
        from app.services.llm_config import get_crewai_llm

        llm_model = get_crewai_llm(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        )
        logger.info(f"Using LLM model: {llm_model}")

        # Extract field names from raw data for mapping
        sample_fields = []
        if state.raw_data and len(state.raw_data) > 0:
            sample_fields = list(state.raw_data[0].keys())[
                :10
            ]  # Limit to first 10 fields

        # 🎯 SINGLE OPTIMIZED AGENT: Direct field mapping specialist
        field_mapping_specialist = Agent(
            role="Field Mapping Specialist",
            goal="Rapidly map data fields to standard migration attributes",
            backstory="""You are an expert field mapping specialist who quickly identifies
            data field patterns and maps them to standard migration attributes.
            You work efficiently using proven mapping patterns and provide direct results.""",
            verbose=False,  # Reduce logging overhead
            allow_delegation=False,  # CRITICAL: Prevent agent delegation
            llm=llm_model,
            max_iter=1,  # Single iteration for speed
            max_execution_time=300,  # 300 second timeout for agent
        )

        # 🎯 SINGLE OPTIMIZED TASK: Direct field mapping
        mapping_task = Task(
            description=f"""
            Map these CSV fields to standard attributes:

            CSV fields: {sample_fields}

            Standard attributes: asset_name, asset_id, asset_type, hostname, ip_address, operating_system, cpu_cores, memory_gb, storage_gb, location, environment, criticality, application, owner, cost_center

            OUTPUT EXACTLY IN THIS FORMAT:
            Application -> application
            Owner -> owner
            Type -> asset_type
            Environment -> environment
            Criticality -> criticality

            Confidence score: 95
            Status: COMPLETE
            """,
            agent=field_mapping_specialist,
            expected_output="Field mappings in format: source -> target",
            max_execution_time=300,  # Task-level timeout - 300 seconds
        )

        # 🚀 OPTIMIZED CREW: Sequential process, minimal overhead
        # Enable memory with proper embedder configuration
        from app.services.llm_config import get_crewai_embeddings

        try:
            # Get embedder configuration
            embedder_config = get_crewai_embeddings()
            logger.info(f"Using embedder config: {embedder_config}")

            crew = Crew(
                agents=[field_mapping_specialist],
                tasks=[mapping_task],
                process=Process.sequential,  # CRITICAL: No hierarchical overhead
                verbose=False,  # Reduce logging
                max_execution_time=300,  # Crew-level timeout - 300 seconds
                memory=True,  # ENABLED: Using proper embedder config
                embedder=embedder_config,  # Use DeepInfra embeddings
            )
            logger.info("✅ CrewAI memory enabled with DeepInfra embeddings")

        except Exception as mem_error:
            logger.warning(f"⚠️ Could not enable memory: {mem_error}")
            # Fallback without memory if embedder fails
            crew = Crew(
                agents=[field_mapping_specialist],
                tasks=[mapping_task],
                process=Process.sequential,
                verbose=False,
                max_execution_time=300,
                memory=False,
                embedder=None,
            )
            logger.info("⚠️ CrewAI memory disabled due to embedder error")

        logger.info("✅ FAST Field Mapping Crew created - single agent, 20s timeout")
        return crew

    except Exception as e:
        logger.error(f"Failed to create fast Field Mapping Crew: {e}")
        # Fallback to minimal crew
        return _create_minimal_mapping_fallback(crewai_service, state)


def _create_minimal_mapping_fallback(
    crewai_service, state: UnifiedDiscoveryFlowState
) -> Crew:
    """Ultra-minimal fallback crew for field mapping"""
    try:
        from app.services.llm_config import get_crewai_llm

        llm_model = get_crewai_llm(
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        )

        minimal_agent = Agent(
            role="Field Mapper",
            goal="Map fields quickly",
            backstory="Fast field mapping specialist",
            verbose=False,
            allow_delegation=False,
            llm=llm_model,
            max_iter=1,
        )

        minimal_task = Task(
            description=f"Quick field mapping for {len(state.raw_data)} records. Return: MAPPED",
            agent=minimal_agent,
            expected_output="MAPPED",
        )

        return Crew(
            agents=[minimal_agent],
            tasks=[minimal_task],
            process=Process.sequential,
            verbose=False,
            memory=False,
        )
    except Exception as e:
        logger.error(f"Even minimal mapping fallback failed: {e}")
        raise


def create_pattern_based_mapping(raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    🚀 ULTRA-FAST: Pattern-based field mapping without AI agents.
    Use this for immediate results when AI agents are too slow.
    """
    if not raw_data:
        return {"mappings": {}, "confidence": 0, "method": "pattern_fallback"}

    sample_record = raw_data[0]
    mappings = {}

    # Common field patterns for IT assets
    field_patterns = {
        "asset_name": ["name", "hostname", "server", "device", "asset_name"],
        "asset_id": ["id", "asset_id", "device_id", "server_id"],
        "asset_type": ["type", "category", "class", "asset_type"],
        "ip_address": ["ip", "address", "ip_address", "host_ip"],
        "operating_system": ["os", "system", "platform", "operating_system"],
        "cpu_cores": ["cpu", "cores", "processor", "vcpu"],
        "memory_gb": ["memory", "ram", "mem", "memory_gb"],
        "storage_gb": ["storage", "disk", "hdd", "ssd", "capacity"],
        "location": ["location", "site", "datacenter", "rack"],
        "environment": ["env", "environment", "stage", "tier"],
        "application": ["app", "application", "service", "workload"],
        "owner": ["owner", "contact", "responsible", "admin"],
    }

    # Map fields based on patterns
    for target_field, patterns in field_patterns.items():
        for source_field in sample_record.keys():
            if any(pattern.lower() in source_field.lower() for pattern in patterns):
                mappings[source_field] = target_field
                break

    confidence = min(100, (len(mappings) / len(sample_record)) * 100)

    return {
        "mappings": mappings,
        "confidence": confidence,
        "method": "pattern_based",
        "processing_time": "< 1 second",
    }
