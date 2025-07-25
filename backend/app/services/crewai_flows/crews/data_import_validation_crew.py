"""
Data Import Validation Crew
A focused CrewAI crew for data import validation.
Performs ONLY essential tasks: file type analysis, security validation, PII detection, and data relevance assessment.
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)


def create_data_import_validation_crew(
    crewai_service,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    shared_memory: Optional[Any] = None,
    callback_handler: Optional[Any] = None,
):
    """
    Create a focused data import validation crew.

    Args:
        crewai_service: CrewAI service instance
        raw_data: Raw data to validate
        metadata: File metadata
        shared_memory: Shared memory for agent learning
        callback_handler: Optional callback handler for task monitoring

    Returns:
        CrewAI Crew for data import validation
    """

    try:
        # Get LLM from service
        llm = crewai_service.get_llm()

        # Import optimized config
        from .crew_config import DEFAULT_AGENT_CONFIG

        # Create focused data validation agent with NO delegation
        data_validation_agent = Agent(
            role="Data Import Validation Specialist",
            goal="Quickly validate imported data for security, PII, file type, and relevance to asset inventory creation",
            backstory="""You are a focused data validation specialist. Your job is to perform ONLY essential validation tasks:
            1. Determine file type (CMDB, logs, monitoring, etc.)
            2. Check for PII and sensitive data
            3. Scan for malicious content
            4. Assess if data is suitable for asset inventory creation

            You DO NOT perform complex analysis, standardization, or transformation.
            You provide quick, accurate validation results for user approval.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,  # Apply no-delegation config
        )

        # Create focused validation task
        validation_task = Task(
            description=f"""Perform focused validation on the imported data:

            Data to validate:
            - Total records: {len(raw_data)}
            - Sample fields: {list(raw_data[0].keys()) if raw_data else []}
            - Metadata: {metadata}

            ESSENTIAL VALIDATION TASKS (DO NOT EXCEED THESE):
            1. FILE TYPE ANALYSIS: Determine if this is CMDB, log, monitoring, network, or other data type
            2. SECURITY SCAN: Check for SQL injection, script injection, or other malicious content
            3. PII DETECTION: Identify any personally identifiable information (emails, phones, SSNs)
            4. DATA RELEVANCE: Assess if this data can be used to create an asset inventory

            PROVIDE RESULTS IN THIS FORMAT:
            {{
                "file_type": "detected_type",
                "confidence": 0.8,
                "recommended_agent": "CMDB_Data_Analyst_Agent",
                "security_status": "clean|pii_detected|threats_detected",
                "pii_found": false,
                "threats_found": false,
                "asset_inventory_suitable": true,
                "summary": "Brief summary of findings",
                "user_approval_required": true
            }}

            Keep analysis focused and efficient. Do not perform data transformation or complex processing.""",
            agent=data_validation_agent,
            expected_output="JSON object with validation results as specified above",
        )

        # Import crew config
        from .crew_config import get_optimized_crew_config

        # Create focused crew with NO iterations, single pass only
        crew_config = get_optimized_crew_config()

        # Add callback handler if provided
        if callback_handler:
            crew_config["callbacks"] = [callback_handler]

        crew = Crew(
            agents=[data_validation_agent],
            tasks=[validation_task],
            process="sequential",  # Simple sequential process
            **crew_config,  # Apply optimized config (no iterations, 15s timeout)
        )

        logger.info("✅ Data Import Validation Crew created successfully")
        return crew

    except Exception as e:
        logger.error(f"❌ Failed to create data import validation crew: {e}")
        raise e
