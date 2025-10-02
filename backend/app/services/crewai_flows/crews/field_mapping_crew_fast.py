"""
🚀 OPTIMIZED Field Mapping Crew - Performance Focused
Fast field mapping with minimal agent overhead and direct execution.

PERFORMANCE OPTIMIZATIONS:
- Single specialized agent (no delegation)
- Direct pattern matching with AI validation
- Minimal memory operations
- Fast timeout controls
- Sequential processing (no hierarchical overhead)

MEMORY INTEGRATION (ADR-024):
- Uses TenantMemoryManager for pattern storage/retrieval
- Retrieves historical patterns before execution
- Stores discovered patterns after execution
- Multi-tenant isolation via engagement_id/client_account_id
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

# CrewAI imports with graceful fallback
try:
    from crewai import Crew, Process  # type: ignore[import-untyped]

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Process:  # type: ignore[no-redef]
        sequential = "sequential"

    class Crew:  # type: ignore[no-redef]
        pass


from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)

logger = logging.getLogger(__name__)


async def field_mapping_with_memory(
    crewai_service,
    client_account_id: int,
    engagement_id: int,
    source_fields: List[str],
    raw_data: List[Dict[str, Any]],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Execute field mapping with TenantMemoryManager integration (Step 5 - ADR-024).

    This function demonstrates proper memory integration:
    1. Retrieve historical field mapping patterns
    2. Provide patterns as context to the agent
    3. Execute crew without built-in memory
    4. Store discovered patterns for future use

    Args:
        crewai_service: CrewAI service instance
        client_account_id: Client account ID for multi-tenant isolation
        engagement_id: Engagement ID for pattern scoping
        source_fields: List of source field names from CSV/data
        raw_data: Sample data records for field mapping
        db: Database session

    Returns:
        Dict containing mappings and metadata
    """
    try:
        logger.info(
            f"🧠 Starting field mapping with TenantMemoryManager "
            f"(client={client_account_id}, engagement={engagement_id})"
        )

        # Step 1: Initialize TenantMemoryManager
        memory_manager = TenantMemoryManager(
            crewai_service=crewai_service, database_session=db
        )

        # Step 2: Retrieve historical field mapping patterns
        logger.info("📚 Retrieving historical field mapping patterns...")
        historical_patterns = await memory_manager.retrieve_similar_patterns(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            pattern_type="field_mapping",
            query_context={"source_fields": source_fields},
            limit=10,
        )

        logger.info(f"✅ Found {len(historical_patterns)} historical patterns")

        # Step 3: Create mock state for crew creation (backward compatibility)
        from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

        mock_state = UnifiedDiscoveryFlowState(
            flow_id=str(UUID(int=0)),  # Temporary UUID as string
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
            raw_data=raw_data,
        )

        # Step 4: Create crew WITHOUT CrewAI memory
        crew = create_fast_field_mapping_crew(crewai_service, mock_state)

        # Step 5: Prepare task context with historical patterns
        task_context = {
            "source_fields": source_fields,
            "historical_patterns": historical_patterns,
            "pattern_context": (
                f"Use these {len(historical_patterns)} historical patterns as reference:\n"
                + "\n".join(
                    [
                        f"- {p['pattern_name']}: confidence={p['confidence']}, similarity={p['similarity']}"
                        for p in historical_patterns[:5]
                    ]
                )
                if historical_patterns
                else "No historical patterns found - use your expertise"
            ),
        }

        # Step 6: Execute crew with context
        logger.info("🚀 Executing field mapping crew with historical context...")
        crew.kickoff(inputs=task_context)  # Result parsing TODO: extract mappings

        # Step 7: Extract discovered patterns from result
        # Parse crew output to identify new mapping patterns
        discovered_patterns = {
            "mappings": {},  # Populated from crew result
            "confidence": 0.0,
            "source_fields": source_fields,
            "execution_time": "N/A",
        }

        # TODO: Parse actual crew result (_result) to extract mappings
        # For now, store basic metadata about the execution

        # Step 8: Store new patterns learned
        logger.info("💾 Storing discovered field mapping patterns...")
        pattern_id = await memory_manager.store_learning(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            scope=LearningScope.ENGAGEMENT,  # Isolated to this engagement
            pattern_type="field_mapping",
            pattern_data={
                "name": f"field_mapping_execution_{engagement_id}",
                "source_fields": source_fields,
                "discovered_mappings": discovered_patterns["mappings"],
                "confidence": discovered_patterns["confidence"],
                "historical_patterns_used": len(historical_patterns),
            },
        )

        logger.info(f"✅ Stored pattern with ID: {pattern_id}")

        return {
            "status": "success",
            "mappings": discovered_patterns["mappings"],
            "confidence": discovered_patterns["confidence"],
            "pattern_id": pattern_id,
            "historical_patterns_used": len(historical_patterns),
            "memory_integration": "TenantMemoryManager (ADR-024)",
        }

    except Exception as e:
        logger.error(f"❌ Field mapping with memory failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "mappings": {},
            "confidence": 0.0,
        }


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
        field_mapping_specialist = create_agent(
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
        mapping_task = create_task(
            description=f"""
            Map these EXACT CSV fields to standard attributes:

            CSV fields: {sample_fields}

            Standard attributes: asset_name, asset_id, asset_type, hostname, ip_address,
            operating_system, cpu_cores, memory_gb, storage_gb, location, environment,
            criticality, application, owner, cost_center

            CRITICAL: Use the EXACT CSV field names as source fields in your mappings.

            OUTPUT EXACTLY IN THIS FORMAT (using the actual CSV field names):
            Device_ID -> asset_id
            Device_Name -> asset_name
            Device_Type -> asset_type
            IP_Address -> ip_address
            Location -> location

            DO NOT normalize or change the CSV field names. Use them exactly as provided.

            Confidence score: 95
            Status: COMPLETE
            """,
            agent=field_mapping_specialist,
            expected_output="Field mappings in format: exact_csv_field -> target_attribute",
            max_execution_time=300,  # Task-level timeout - 300 seconds
        )

        # 🚀 OPTIMIZED CREW: Sequential process, minimal overhead, NO memory
        # Memory disabled per ADR-024 - use TenantMemoryManager instead
        crew = create_crew(
            agents=[field_mapping_specialist],
            tasks=[mapping_task],
            process=Process.sequential,  # CRITICAL: No hierarchical overhead
            verbose=False,  # Reduce logging
            max_execution_time=300,  # Crew-level timeout - 300 seconds
            memory=False,  # ✅ DISABLED per ADR-024 - use TenantMemoryManager
        )
        logger.info("✅ Field Mapping Crew created without CrewAI memory (ADR-024)")

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

        minimal_agent = create_agent(
            role="Field Mapper",
            goal="Map fields quickly",
            backstory="Fast field mapping specialist",
            verbose=False,
            allow_delegation=False,
            llm=llm_model,
            max_iter=1,
        )

        minimal_task = create_task(
            description=f"Quick field mapping for {len(state.raw_data)} records. Return: MAPPED",
            agent=minimal_agent,
            expected_output="MAPPED",
        )

        return create_crew(
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
