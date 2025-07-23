"""
Automated Collection Crew
ADCS: Crew for automated data collection using platform adapters with intelligent orchestration
"""

import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Task

logger = logging.getLogger(__name__)


def create_automated_collection_crew(
    crewai_service,
    platforms: List[Dict[str, Any]],
    tier_assessments: Dict[str, Any],
    context: Dict[str, Any],
    shared_memory: Optional[Any] = None,
):
    """
    Create a crew for automated collection phase

    Args:
        crewai_service: CrewAI service instance
        platforms: List of detected platforms from platform detection phase
        tier_assessments: Tier assessments for each platform
        context: Additional context (adapters, credentials, etc.)
        shared_memory: Shared memory for agent learning

    Returns:
        CrewAI Crew for automated collection
    """

    try:
        # Get LLM from service
        llm = crewai_service.get_llm()

        # Import optimized config
        from ..crew_config import DEFAULT_AGENT_CONFIG

        # Create collection orchestrator agent
        collection_orchestrator = Agent(
            role="Collection Orchestration Specialist",
            goal="Orchestrate efficient and comprehensive automated data collection across all platforms while maintaining data quality",
            backstory="""You are a master collection orchestrator with expertise in:
            - Multi-platform data collection strategies
            - Platform API optimization and rate limiting
            - Parallel collection coordination
            - Data quality assurance during collection
            - Error handling and retry strategies
            
            You excel at:
            1. Designing optimal collection workflows based on tier assessments
            2. Coordinating multiple platform adapters simultaneously
            3. Prioritizing collection tasks for maximum efficiency
            4. Monitoring collection progress and adjusting strategies
            5. Ensuring data completeness and quality
            
            Your orchestration maximizes collection efficiency while maintaining data integrity.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create data quality validator agent
        quality_validator = Agent(
            role="Collection Quality Assurance Expert",
            goal="Validate collected data quality, identify gaps, and ensure data meets migration requirements",
            backstory="""You are a data quality expert specializing in migration data validation.
            
            Your expertise includes:
            - Validating data completeness against critical attributes framework
            - Identifying data quality issues and anomalies
            - Assessing data consistency across platforms
            - Detecting missing or incomplete data fields
            - Calculating quality scores for collected data
            
            You ensure all collected data meets the quality standards required for accurate 6R strategy recommendations.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Create collection progress monitor agent
        progress_monitor = Agent(
            role="Collection Progress Analytics Expert",
            goal="Monitor collection progress, identify bottlenecks, and provide real-time insights for optimization",
            backstory="""You are a collection analytics expert who monitors and optimizes data collection processes.
            
            You specialize in:
            - Real-time progress tracking across platforms
            - Identifying collection bottlenecks and failures
            - Calculating collection metrics and KPIs
            - Predicting collection completion times
            - Recommending optimization strategies
            
            Your monitoring ensures collection stays on track and identifies issues early.""",
            llm=llm,
            memory=shared_memory,
            **DEFAULT_AGENT_CONFIG,
        )

        # Extract platform and adapter information
        available_adapters = context.get("available_adapters", {})
        collection_timeout = context.get("collection_timeout_minutes", 60)
        quality_thresholds = context.get("quality_thresholds", {"minimum": 0.8})

        # Create collection orchestration task
        orchestration_task = Task(
            description=f"""Orchestrate automated data collection across detected platforms:

            DETECTED PLATFORMS:
            {[{'name': p.get('name'), 'type': p.get('type'), 'tier': tier_assessments.get('tier_assessments', [{}])[i].get('recommended_tier', 2) if i < len(tier_assessments.get('tier_assessments', [])) else 2} for i, p in enumerate(platforms)]}

            AVAILABLE ADAPTERS:
            {list(available_adapters.keys())}

            COLLECTION REQUIREMENTS:
            - Timeout: {collection_timeout} minutes
            - Quality threshold: {quality_thresholds['minimum']}
            - Parallel collection where possible
            - Respect API rate limits

            ORCHESTRATION TASKS:
            1. COLLECTION STRATEGY:
               - Design optimal collection sequence based on tiers
               - Identify platforms for parallel collection
               - Set appropriate timeouts and retries per platform
               - Plan fallback strategies for failures

            2. ADAPTER COORDINATION:
               - Map platforms to appropriate adapters
               - Configure adapter parameters
               - Set collection priorities
               - Define data extraction scope

            3. EXECUTION PLAN:
               - Create detailed collection workflow
               - Define success criteria per platform
               - Set quality checkpoints
               - Plan error recovery procedures

            OUTPUT FORMAT:
            {{
                "collection_strategy": {{
                    "execution_mode": "parallel|sequential|hybrid",
                    "estimated_duration_minutes": 45,
                    "platform_sequence": [
                        {{
                            "platform_id": "platform-uuid",
                            "adapter": "aws_adapter",
                            "priority": 1,
                            "parallel_group": 1,
                            "timeout_minutes": 15,
                            "retry_attempts": 3,
                            "collection_scope": ["compute", "storage", "network"]
                        }}
                    ]
                }},
                "adapter_configurations": {{
                    "aws_adapter": {{
                        "regions": ["us-east-1", "us-west-2"],
                        "services": ["ec2", "rds", "s3"],
                        "rate_limit": 100,
                        "batch_size": 50
                    }}
                }},
                "quality_criteria": {{
                    "minimum_fields_required": 15,
                    "critical_fields": ["instance_id", "instance_type", "region"],
                    "validation_rules": ["no_nulls_in_critical", "valid_instance_types"]
                }}
            }}""",
            agent=collection_orchestrator,
            expected_output="JSON object with comprehensive collection strategy and configurations",
        )

        # Create quality validation task
        quality_validation_task = Task(
            description=f"""Validate quality of collected data as it arrives:

            QUALITY REQUIREMENTS:
            - Minimum quality score: {quality_thresholds['minimum']}
            - Critical attributes framework compliance
            - Data consistency across platforms
            - No duplicate or corrupted data

            VALIDATION OBJECTIVES:
            1. COMPLETENESS CHECK:
               - Verify all expected fields are present
               - Check for null or empty critical fields
               - Assess coverage of 22 critical attributes
               - Calculate field completion percentages

            2. CONSISTENCY VALIDATION:
               - Cross-reference data between platforms
               - Verify data format consistency
               - Check for logical inconsistencies
               - Validate relationships between entities

            3. QUALITY SCORING:
               - Calculate quality score per platform
               - Identify quality issues and their severity
               - Assess impact on 6R strategy accuracy
               - Recommend data enrichment if needed

            OUTPUT FORMAT:
            {{
                "quality_assessment": {{
                    "overall_quality_score": 0.87,
                    "platform_scores": {{
                        "platform-uuid-1": 0.92,
                        "platform-uuid-2": 0.85
                    }},
                    "critical_attribute_coverage": 0.78,
                    "data_consistency_score": 0.90
                }},
                "quality_issues": [
                    {{
                        "platform_id": "platform-uuid",
                        "issue_type": "missing_field",
                        "field_name": "cost_center",
                        "severity": "medium",
                        "impact": "Affects TCO calculations",
                        "records_affected": 125
                    }}
                ],
                "enrichment_recommendations": [
                    {{
                        "platform_id": "platform-uuid",
                        "recommendation": "Collect cost allocation tags",
                        "priority": "high",
                        "method": "manual_collection"
                    }}
                ]
            }}""",
            agent=quality_validator,
            expected_output="JSON object with quality assessment and recommendations",
            context=[orchestration_task],
        )

        # Create progress monitoring task
        progress_monitoring_task = Task(
            description="""Monitor and analyze collection progress in real-time:

            MONITORING OBJECTIVES:
            1. PROGRESS TRACKING:
               - Track collection status per platform
               - Monitor data volume collected
               - Calculate completion percentages
               - Estimate time to completion

            2. PERFORMANCE ANALYSIS:
               - Measure collection throughput
               - Identify slow or failing adapters
               - Detect rate limiting issues
               - Track resource utilization

            3. OPTIMIZATION INSIGHTS:
               - Identify bottlenecks in collection
               - Recommend performance improvements
               - Suggest strategy adjustments
               - Alert on critical issues

            OUTPUT FORMAT:
            {{
                "collection_progress": {{
                    "overall_completion": 0.75,
                    "estimated_completion_time": "2024-01-15T14:30:00Z",
                    "platforms_completed": 3,
                    "platforms_in_progress": 2,
                    "platforms_pending": 1
                }},
                "platform_metrics": [
                    {{
                        "platform_id": "platform-uuid",
                        "status": "in_progress",
                        "completion_percentage": 85,
                        "records_collected": 1250,
                        "throughput_per_minute": 42,
                        "errors_encountered": 2,
                        "last_activity": "2024-01-15T13:45:00Z"
                    }}
                ],
                "performance_insights": {{
                    "bottlenecks": ["AWS rate limiting in us-east-1"],
                    "optimization_opportunities": ["Increase batch size for Azure"],
                    "critical_issues": [],
                    "recommended_actions": ["Reduce AWS API call frequency"]
                }},
                "collection_summary": {{
                    "total_records": 5847,
                    "total_platforms": 6,
                    "average_quality_score": 0.88,
                    "collection_duration_minutes": 35
                }}
            }}""",
            agent=progress_monitor,
            expected_output="JSON object with progress metrics and optimization insights",
            context=[orchestration_task, quality_validation_task],
        )

        # Import crew config
        from ..crew_config import get_optimized_crew_config

        # Create crew with optimized settings
        crew_config = get_optimized_crew_config()
        crew = Crew(
            agents=[collection_orchestrator, quality_validator, progress_monitor],
            tasks=[
                orchestration_task,
                quality_validation_task,
                progress_monitoring_task,
            ],
            process="sequential",
            **crew_config,  # Apply optimized config
        )

        logger.info("✅ Automated Collection Crew created successfully")
        return crew

    except Exception as e:
        logger.error(f"❌ Failed to create automated collection crew: {e}")
        raise e
