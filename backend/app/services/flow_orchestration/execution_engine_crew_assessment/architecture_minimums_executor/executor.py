"""
Architecture Minimums Executor Mixin

Mixin for executing architecture minimums (compliance validation) phase.
Issue #1243: Three-level compliance validation using CrewAI agent.
"""

import json
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.utils.json_sanitization import safe_parse_llm_json
from crewai import Task

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.services.crewai_flows.config.crew_factory import create_crew

from .helpers import (
    aggregate_asset_data,
    build_empty_result,
    build_error_result,
    fallback_deterministic_validation,
    get_default_standards,
    transform_agent_result,
)
from .prompts import THREE_LEVEL_COMPLIANCE_PROMPT

logger = get_logger(__name__)


class ArchitectureMinimumsExecutorMixin:
    """Mixin for architecture minimums (compliance validation) phase execution."""

    async def _execute_architecture_minimums(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute architecture minimums phase - three-level compliance validation.

        Issue #1243: Uses compliance_validator agent with:
        - eol_catalog_lookup tool (DB-first)
        - rag_eol_enrichment tool (RAG fallback)
        - asset_product_linker tool (persistence)

        Three levels:
        1. OS Compliance - Asset.operating_system/os_version
        2. Application Compliance - COTS apps vs vendor EOL
        3. Component Compliance - databases, runtimes, frameworks
        """
        logger.info(
            "Executing architecture minimums (three-level compliance validation)"
        )

        try:
            # Get assessment flow ID (child flow ID, not master)
            assessment_flow_id = phase_input.get("flow_id", str(master_flow.flow_id))

            # Load engagement standards from database
            engagement_standards = await data_repo.get_engagement_standards(
                str(master_flow.engagement_id)
            )
            if not engagement_standards:
                engagement_standards = get_default_standards()
                logger.warning(
                    "No engagement standards found, using defaults. "
                    f"Engagement: {master_flow.engagement_id}"
                )

            # Load applications with their asset data for this assessment
            applications = await data_repo.get_assessment_applications(
                assessment_flow_id
            )

            # Aggregate asset data for agent
            assets_data = await aggregate_asset_data(
                data_repo, applications, assessment_flow_id
            )

            total_apps = len(assets_data)

            if total_apps == 0:
                logger.warning("No applications found for compliance validation")
                return build_empty_result(engagement_standards)

            # Execute agent-based validation
            compliance_result = await self._execute_agent_validation(
                agent_pool=agent_pool,
                master_flow=master_flow,
                assets_data=assets_data,
                engagement_standards=engagement_standards,
                phase_input=phase_input,
            )

            # Parse and transform results
            architecture_minimums_data = transform_agent_result(
                compliance_result=compliance_result,
                engagement_standards=engagement_standards,
                total_apps=total_apps,
            )

            logger.info(
                f"Architecture minimums completed - "
                f"{architecture_minimums_data['compliance_validation']['summary']['compliant_count']}"
                f"/{total_apps} applications compliant"
            )

            return {
                "phase": "architecture_minimums",
                "status": "completed",
                "agent": "compliance_validator",
                **architecture_minimums_data,
            }

        except Exception as e:
            logger.error(f"Architecture minimums phase failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return build_error_result(str(e))

    async def _execute_agent_validation(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        assets_data: List[Dict[str, Any]],
        engagement_standards: Dict[str, Any],
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute compliance validation using the compliance_validator agent."""
        try:
            # Get the compliance validator agent from pool
            context = RequestContext(
                client_account_id=master_flow.client_account_id,
                engagement_id=master_flow.engagement_id,
            )

            # Get service registry from phase input or agent pool
            service_registry = phase_input.get("service_registry")
            if not service_registry and hasattr(agent_pool, "service_registry"):
                service_registry = agent_pool.service_registry

            compliance_agent = await TenantScopedAgentPool.get_agent(
                context=context,
                agent_type="compliance_validator",
                service_registry=service_registry,
            )

            if not compliance_agent:
                logger.warning(
                    "Could not get compliance_validator agent, falling back to deterministic"
                )
                return fallback_deterministic_validation(
                    assets_data, engagement_standards
                )

            # Build the prompt
            prompt = THREE_LEVEL_COMPLIANCE_PROMPT.format(
                assets=json.dumps(assets_data, indent=2, default=str),
                engagement_standards=json.dumps(engagement_standards, indent=2),
            )

            # Create task
            task = Task(
                description=prompt,
                expected_output="JSON with checked_items array and compliance summary",
                agent=compliance_agent,
            )

            # Create crew with memory disabled per ADR-024
            crew = create_crew(
                agents=[compliance_agent],
                tasks=[task],
                memory=False,
                verbose=False,
            )

            # Execute the crew - OBSERVABILITY: tracking not needed
            result = await crew.kickoff_async()

            # Parse the result
            if hasattr(result, "raw"):
                result_text = result.raw
            elif hasattr(result, "output"):
                result_text = result.output
            else:
                result_text = str(result)

            # Use safe_parse_llm_json per ADR-029
            parsed_result = safe_parse_llm_json(result_text)

            # Validate result is a dict with expected structure
            if isinstance(parsed_result, dict) and (
                "checked_items" in parsed_result or "summary" in parsed_result
            ):
                return parsed_result
            else:
                logger.warning(
                    f"Agent result has unexpected type or structure: "
                    f"{type(parsed_result).__name__}, using fallback"
                )
                return fallback_deterministic_validation(
                    assets_data, engagement_standards
                )

        except Exception as e:
            logger.error(f"Agent validation failed: {e}, using fallback")
            return fallback_deterministic_validation(assets_data, engagement_standards)
