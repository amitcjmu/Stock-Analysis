"""
Inventory Building Agents - Agent Creation Logic

This module contains agent creation functions for the Inventory Building Crew.
It defines four specialized agents:
1. Inventory Manager - Coordinates multi-domain asset classification
2. Server Classification Expert - Infrastructure domain specialist
3. Application Discovery Expert - Application domain specialist
4. Device Classification Expert - Network/device domain specialist
"""

import logging
from typing import Any, Optional

from app.services.crewai_flows.config.crew_factory import create_agent
from app.services.crewai_flows.crews.inventory_building_crew_original.tools import (
    _create_app_classification_tools,
    _create_device_classification_tools,
)

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge import Knowledge, LocalKnowledgeBase
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

    class LocalKnowledgeBase:
        def __init__(self, **kwargs):
            pass


logger = logging.getLogger(__name__)


def create_inventory_agents(
    llm_model: Any,
    shared_memory: Optional[LongTermMemory] = None,
    knowledge_base: Optional[Knowledge] = None,
) -> list:
    """
    Create all agents for the Inventory Building Crew.

    Args:
        llm_model: LLM model instance for agent reasoning
        shared_memory: Optional shared memory for cross-domain insights
        knowledge_base: Optional knowledge base for classification rules

    Returns:
        List of agent instances: [manager, server_expert, app_expert, device_expert]
    """
    # Manager Agent for multi-domain coordination
    inventory_manager = create_agent(
        role="IT Asset Inventory Coordination Manager",
        goal=(
            "Coordinate comprehensive IT asset inventory building across "
            "servers, applications, and devices with cross-domain validation"
        ),
        backstory="""You are a senior enterprise architect with specialized expertise in IT asset inventory
        management and CMDB classification for large-scale migration projects. Your specific role and boundaries:

        INTELLIGENCE & EFFICIENCY RESPONSIBILITIES:
        - FIRST: Use task_completion_checker tool to verify if asset inventory has been completed recently
        - If completed recently, return existing results instead of re-processing to avoid redundant work
        - BEFORE creating any assets: Use asset_deduplication_checker tool to ensure no duplicates are created
        - AFTER asset classification: Use asset_enrichment_analyzer tool to enrich each asset with metadata
        - Use execution_coordinator tool to coordinate with other agents and avoid conflicts
        - Only proceed with full inventory if no recent completion or results are insufficient

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
        llm=llm_model,
        memory=shared_memory,
        knowledge_base=knowledge_base,
        verbose=True,
        allow_delegation=False,  # Disabled to prevent back-and-forth delays
        max_delegation=0,  # No delegations to speed up processing
        max_retry=1,  # Prevent retry loops
        collaboration=False,  # Disabled for faster processing
    )

    # Server Classification Expert - infrastructure domain specialist
    server_expert = create_agent(
        role="Enterprise Server & Infrastructure Classification Expert",
        goal=(
            "Classify server and infrastructure assets with detailed "
            "technical specifications and hosting capacity analysis"
        ),
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
        llm=llm_model,
        memory=shared_memory,
        knowledge_base=knowledge_base,
        verbose=True,
        allow_delegation=False,
        max_retry=1,
        collaboration=False,
        tools=[],  # Tools will be added by crew creation logic
    )

    # Application Discovery Expert - application domain
    app_expert = create_agent(
        role="Application Discovery Expert",
        goal="Identify and categorize application assets with business context and dependencies",
        backstory="""You are an application portfolio expert with deep knowledge of enterprise
        applications. You excel at identifying application types, versions, business criticality,
        and hosting relationships for migration strategy.""",
        llm=llm_model,
        memory=shared_memory,
        knowledge_base=knowledge_base,
        verbose=True,
        allow_delegation=False,
        max_retry=1,
        collaboration=False,
        tools=_create_app_classification_tools(),
    )

    # Device Classification Expert - network/device domain
    device_expert = create_agent(
        role="Device Classification Expert",
        goal="Classify network devices and infrastructure components for migration planning",
        backstory="""You are a network infrastructure expert with knowledge of enterprise device
        topologies. You excel at identifying network devices, security appliances, and
        infrastructure components that support migration planning.""",
        llm=llm_model,
        memory=shared_memory,
        knowledge_base=knowledge_base,
        verbose=True,
        allow_delegation=False,
        max_retry=1,
        collaboration=False,
        tools=_create_device_classification_tools(),
    )

    logger.info(
        "✅ Created 4 inventory building agents: manager, server_expert, app_expert, device_expert"
    )

    return [inventory_manager, server_expert, app_expert, device_expert]


__all__ = ["create_inventory_agents", "CREWAI_ADVANCED_AVAILABLE"]
