"""
Platform Detection Crew
ADCS: Crew for detecting and identifying target platforms using intelligent agents
"""

import logging
from typing import Any, Dict, Optional

from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)


def create_platform_detection_crew(
    crewai_service,
    infrastructure_data: Dict[str, Any],
    context: Dict[str, Any],
    shared_memory: Optional[Any] = None,
):
    """
    Create a crew for platform detection phase

    Args:
        crewai_service: CrewAI service instance
        infrastructure_data: Data about infrastructure to analyze
        context: Additional context (credentials, tiers, etc.)
        shared_memory: Shared memory for agent learning

    Returns:
        CrewAI Crew for platform detection
    """

    try:
        # Get LLM from service
        llm = crewai_service.get_llm()

        # Import optimized config
        from ..crew_config import DEFAULT_AGENT_CONFIG

        # Create platform detection specialist agent
        platform_detection_agent = Agent(
            role="Platform Detection Specialist",
            goal=(
                "Identify and analyze all target platforms for migration, including cloud "
                "providers, on-premises systems, and hybrid environments"
            ),
            backstory="""You are an expert platform detection specialist with deep knowledge of:
            - Cloud platforms (AWS, Azure, GCP, Oracle Cloud, IBM Cloud)
            - On-premises infrastructure (VMware, Hyper-V, physical servers)
            - Container platforms (Kubernetes, OpenShift, Docker Swarm)
            - Database platforms (Oracle, SQL Server, PostgreSQL, MySQL)
            - Middleware and application servers

            You excel at:
            1. Detecting platform types from infrastructure metadata
            2. Identifying platform-specific features and capabilities
            3. Determining appropriate collection adapters for each platform
            4. Assessing platform readiness for migration
            5. Identifying potential compatibility issues

            Your analysis ensures comprehensive platform coverage for migration planning.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,  # Apply no-delegation config
        )

        # Create automation tier assessment agent
        tier_assessment_agent = Agent(
            role="Automation Tier Assessment Expert",
            goal=(
                "Determine the optimal automation tier for each detected platform based on "
                "API availability, credentials, and complexity"
            ),
            backstory="""You are an automation assessment expert who determines the best collection approach.
            You understand the four automation tiers:

            Tier 1 (Full Automation): APIs available, credentials valid, minimal complexity
            Tier 2 (Semi-Automated): Some APIs available, partial credentials, moderate complexity
            Tier 3 (Guided Collection): Limited APIs, complex authentication, high complexity
            Tier 4 (Manual Process): No APIs, missing credentials, extreme complexity

            You assess each platform's automation potential and recommend the appropriate tier.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create platform metadata from infrastructure data
        platform_info = context.get("platform_info", {})
        credentials_available = context.get("credentials_available", {})
        automation_preferences = context.get("automation_preferences", {})

        # Create platform detection task
        platform_detection_task = Task(
            description=f"""Analyze the infrastructure data to detect all platforms:

            Infrastructure Data Summary:
            - Total systems: {infrastructure_data.get('total_systems', 0)}
            - Known platforms: {list(platform_info.keys()) if platform_info else ['Unknown']}
            - Credential availability: {credentials_available}

            DETECTION OBJECTIVES:
            1. PLATFORM IDENTIFICATION:
               - Identify all cloud platforms (AWS, Azure, GCP, etc.)
               - Detect on-premises infrastructure (VMware, physical servers)
               - Find container platforms and orchestrators
               - Identify database and middleware platforms

            2. PLATFORM CHARACTERISTICS:
               - API availability and versions
               - Authentication methods supported
               - Regional presence and availability zones
               - Service limits and quotas
               - Compliance and security features

            3. ADAPTER MAPPING:
               - Match each platform to appropriate collection adapter
               - Identify required authentication parameters
               - Note any platform-specific collection requirements
               - Flag platforms without adapter support

            OUTPUT FORMAT:
            {{
                "platforms": [
                    {{
                        "id": "platform-uuid",
                        "type": "aws|azure|gcp|vmware|physical|other",
                        "name": "Human-readable platform name",
                        "version": "Platform version if applicable",
                        "regions": ["region1", "region2"],
                        "api_endpoints": ["endpoint1", "endpoint2"],
                        "authentication_type": "iam|service_principal|oauth|basic",
                        "detected_confidence": 0.95,
                        "collection_adapter": "aws_adapter|azure_adapter|etc",
                        "features": ["feature1", "feature2"],
                        "limitations": ["limitation1", "limitation2"]
                    }}
                ],
                "platform_summary": {{
                    "total_platforms": 5,
                    "cloud_platforms": 3,
                    "on_premise_platforms": 2,
                    "detection_confidence": 0.92
                }}
            }}""",
            agent=platform_detection_agent,
            expected_output="JSON object with detected platforms and their characteristics",
        )

        # Create tier assessment task
        tier_assessment_task = Task(
            description=f"""Assess automation tier for each detected platform:

            Automation Preferences: {automation_preferences}

            For each detected platform, determine:

            1. API AVAILABILITY ASSESSMENT:
               - Check if platform APIs are accessible
               - Verify API rate limits and quotas
               - Assess API coverage for required data

            2. CREDENTIAL VALIDATION:
               - Verify credential availability and validity
               - Check permission levels for collection
               - Identify any missing permissions

            3. COMPLEXITY EVALUATION:
               - Assess platform configuration complexity
               - Identify custom or non-standard setups
               - Evaluate data extraction challenges

            4. TIER RECOMMENDATION:
               - Tier 1: Full automation possible (>90% data via API)
               - Tier 2: Semi-automated (60-90% data via API)
               - Tier 3: Guided collection (30-60% data via API)
               - Tier 4: Manual process (<30% data via API)

            OUTPUT FORMAT:
            {{
                "tier_assessments": [
                    {{
                        "platform_id": "platform-uuid",
                        "recommended_tier": 1,
                        "automation_score": 0.95,
                        "api_coverage": 0.98,
                        "credential_status": "valid",
                        "complexity_score": 0.2,
                        "tier_justification": "Full API access with valid credentials",
                        "collection_approach": "parallel_api_collection",
                        "estimated_duration_minutes": 30
                    }}
                ],
                "overall_automation_tier": 2,
                "tier_distribution": {{
                    "tier_1": 2,
                    "tier_2": 2,
                    "tier_3": 1,
                    "tier_4": 0
                }}
            }}""",
            agent=tier_assessment_agent,
            expected_output="JSON object with automation tier assessments for each platform",
            context=[platform_detection_task],
        )

        # Import crew config
        from ..crew_config import get_optimized_crew_config

        # Create crew with optimized settings
        crew_config = get_optimized_crew_config()
        crew = Crew(
            agents=[platform_detection_agent, tier_assessment_agent],
            tasks=[platform_detection_task, tier_assessment_task],
            process="sequential",
            **crew_config,  # Apply optimized config
        )

        logger.info("✅ Platform Detection Crew created successfully")
        return crew

    except Exception as e:
        logger.error(f"❌ Failed to create platform detection crew: {e}")
        raise e
