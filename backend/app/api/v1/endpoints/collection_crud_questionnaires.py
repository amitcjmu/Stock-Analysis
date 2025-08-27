"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific read operations for collection flows.
"""

import logging
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of adaptive questionnaires

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # First verify the flow exists and user has access
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # CRITICAL FIX: Check for questionnaires in master flow execution
        # Questionnaires are created during MFO execution in the questionnaire_generation phase
        questionnaires = []

        if flow.master_flow_id:
            logger.info(
                f"Looking for questionnaires from master flow execution: {flow.master_flow_id}"
            )

            # Try to get questionnaires that were created during master flow execution
            # These might be stored in crewai_flow_state_extensions.flow_persistence_data
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flow_result = await db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow.master_flow_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                )
            )
            master_flow = master_flow_result.scalar_one_or_none()

            if master_flow and master_flow.flow_persistence_data:
                # Check if questionnaires exist in the master flow's persistence data
                persistence_data = master_flow.flow_persistence_data
                if isinstance(persistence_data, dict):
                    # Look for questionnaires in different possible keys
                    questionnaire_data = (
                        persistence_data.get("questionnaires", [])
                        or persistence_data.get("adaptive_questionnaires", [])
                        or persistence_data.get("generated_questionnaires", [])
                        or []
                    )

                    if questionnaire_data:
                        logger.info(
                            f"Found {len(questionnaire_data)} questionnaires in master flow persistence data"
                        )

                        # Convert master flow questionnaire data to AdaptiveQuestionnaireResponse format
                        for idx, q_data in enumerate(questionnaire_data):
                            if isinstance(q_data, dict):
                                questionnaire = AdaptiveQuestionnaireResponse(
                                    id=q_data.get("id", f"generated_{idx}"),
                                    collection_flow_id=flow_id,
                                    title=q_data.get(
                                        "title", f"Generated Questionnaire {idx + 1}"
                                    ),
                                    description=q_data.get(
                                        "description",
                                        "AI-generated questionnaire from gap analysis",
                                    ),
                                    target_gaps=q_data.get("target_gaps", []),
                                    questions=q_data.get("questions", []),
                                    validation_rules=q_data.get("validation_rules", []),
                                    completion_status=q_data.get(
                                        "completion_status", "pending"
                                    ),
                                    responses_collected=q_data.get(
                                        "responses_collected", []
                                    ),
                                    created_at=q_data.get(
                                        "created_at", datetime.utcnow().isoformat()
                                    ),
                                    completed_at=q_data.get("completed_at"),
                                )
                                questionnaires.append(questionnaire)
                    else:
                        logger.info(
                            f"No questionnaire data found in master flow persistence for flow {flow.master_flow_id}"
                        )
                else:
                    logger.info(
                        f"Master flow {flow.master_flow_id} has no valid persistence data"
                    )

        # Fallback: Get questionnaires directly linked to collection flow (legacy approach)
        if not questionnaires:
            logger.info(
                "No master flow questionnaires found, checking direct collection flow questionnaires"
            )
            result = await db.execute(
                select(AdaptiveQuestionnaire)
                .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
                .order_by(AdaptiveQuestionnaire.created_at.desc())
            )
            db_questionnaires = result.scalars().all()

            if db_questionnaires:
                logger.info(
                    f"Found {len(db_questionnaires)} direct questionnaires for collection flow {flow_id}"
                )
                # Convert to response format
                questionnaires = [
                    collection_serializers.serialize_adaptive_questionnaire(q)
                    for q in db_questionnaires
                ]

        logger.debug(
            "Found %d total questionnaires for flow %s",
            len(questionnaires),
            flow_id,
        )

        # If no questionnaires exist yet, provide a bootstrap questionnaire instead of hard failing
        if not questionnaires:
            logger.info(f"No questionnaires found yet for flow {flow_id}")
            logger.debug(
                "About to check applications for engagement %s",
                context.engagement_id,
            )

            # Check if we have selected applications to pre-populate data
            selected_application_name = None
            selected_application_id = None

            if flow.collection_config and flow.collection_config.get(
                "selected_application_ids"
            ):
                selected_app_ids = flow.collection_config.get(
                    "selected_application_ids", []
                )
                if selected_app_ids:
                    selected_application_id = selected_app_ids[
                        0
                    ]  # Use first selected app

                    # Fetch the asset details to get the application name
                    from app.models.asset import Asset

                    asset_result = await db.execute(
                        select(Asset)
                        .where(Asset.id == selected_application_id)
                        .where(Asset.engagement_id == context.engagement_id)
                    )
                    selected_asset = asset_result.scalar_one_or_none()

                    if selected_asset:
                        selected_application_name = (
                            selected_asset.name or selected_asset.application_name
                        )
                        logger.info(
                            f"Pre-populating questionnaire with application: "
                            f"{selected_application_name} (ID: {selected_application_id})"
                        )
                    else:
                        logger.warning(
                            f"Selected application {selected_application_id} not found in asset inventory"
                        )

            # Comprehensive bootstrap questionnaire with all sections needed for collection
            bootstrap_questionnaire = AdaptiveQuestionnaireResponse(
                id=f"bootstrap_{flow_id}",
                collection_flow_id=flow_id,
                title="Comprehensive Application Data Collection",
                description=(
                    "Please provide comprehensive information about your application "
                    "to complete the adaptive collection process."
                ),
                target_gaps=[
                    "application_selection",
                    "basic_info",
                    "technical_details",
                    "infrastructure",
                    "compliance",
                ],
                questions=[
                    # Basic Information Section
                    {
                        "field_id": "application_name",
                        "question_text": "What is the application name?",
                        "field_type": "text",
                        "required": True,
                        "category": "basic",
                        "help_text": "Enter the official application name",
                        "default_value": selected_application_name,  # Pre-fill if available
                    },
                    {
                        "field_id": "application_type",
                        "question_text": "What type of application is this?",
                        "field_type": "select",
                        "required": True,
                        "category": "basic",
                        "options": [
                            "web",
                            "desktop",
                            "mobile",
                            "service",
                            "batch",
                        ],
                    },
                    {
                        "field_id": "business_criticality",
                        "question_text": "What is the business criticality level?",
                        "field_type": "select",
                        "required": True,
                        "category": "basic",
                        "options": [
                            "critical",
                            "high",
                            "medium",
                            "low",
                        ],
                        "help_text": "Assess the impact on business operations if this application fails",
                    },
                    {
                        "field_id": "primary_users",
                        "question_text": "Who are the primary users of this application?",
                        "field_type": "text",
                        "required": True,
                        "category": "basic",
                        "help_text": "E.g., Internal employees, External customers, Partners",
                    },
                    {
                        "field_id": "user_count",
                        "question_text": "Approximately how many users does this application have?",
                        "field_type": "number",
                        "required": False,
                        "category": "basic",
                    },
                    # Technical Details Section
                    {
                        "field_id": "technology_stack",
                        "question_text": "What is the primary technology stack?",
                        "field_type": "text",
                        "required": True,
                        "category": "technical",
                        "help_text": "E.g., Java/Spring, .NET/C#, Python/Django, Node.js",
                    },
                    {
                        "field_id": "database_type",
                        "question_text": "What database system(s) does the application use?",
                        "field_type": "text",
                        "required": True,
                        "category": "technical",
                        "help_text": "E.g., MySQL, PostgreSQL, Oracle, MongoDB, SQL Server",
                    },
                    {
                        "field_id": "architecture_pattern",
                        "question_text": "What is the architecture pattern?",
                        "field_type": "select",
                        "required": True,
                        "category": "technical",
                        "options": [
                            "monolithic",
                            "microservices",
                            "serverless",
                            "event_driven",
                            "layered",
                            "other",
                        ],
                    },
                    {
                        "field_id": "api_interfaces",
                        "question_text": "Does the application expose or consume APIs?",
                        "field_type": "select",
                        "required": True,
                        "category": "technical",
                        "options": [
                            "exposes_only",
                            "consumes_only",
                            "both",
                            "none",
                        ],
                    },
                    {
                        "field_id": "authentication_method",
                        "question_text": "What authentication method is used?",
                        "field_type": "text",
                        "required": False,
                        "category": "technical",
                        "help_text": "E.g., LDAP, OAuth2, SAML, Custom",
                    },
                    # Infrastructure Section
                    {
                        "field_id": "deployment_environment",
                        "question_text": "Where is the application currently deployed?",
                        "field_type": "select",
                        "required": True,
                        "category": "infrastructure",
                        "options": [
                            "on_premise",
                            "private_cloud",
                            "public_cloud",
                            "hybrid",
                            "edge",
                        ],
                    },
                    {
                        "field_id": "cloud_provider",
                        "question_text": "If cloud-based, which provider(s)?",
                        "field_type": "text",
                        "required": False,
                        "category": "infrastructure",
                        "help_text": "E.g., AWS, Azure, GCP, IBM Cloud",
                    },
                    {
                        "field_id": "containerized",
                        "question_text": "Is the application containerized?",
                        "field_type": "select",
                        "required": True,
                        "category": "infrastructure",
                        "options": [
                            "yes_docker",
                            "yes_kubernetes",
                            "yes_openshift",
                            "no",
                            "planned",
                        ],
                    },
                    {
                        "field_id": "scalability_requirements",
                        "question_text": "What are the scalability requirements?",
                        "field_type": "select",
                        "required": False,
                        "category": "infrastructure",
                        "options": [
                            "auto_scaling",
                            "manual_scaling",
                            "fixed_capacity",
                            "not_applicable",
                        ],
                    },
                    # Compliance & Security Section
                    {
                        "field_id": "data_classification",
                        "question_text": "What is the data classification level?",
                        "field_type": "select",
                        "required": True,
                        "category": "compliance",
                        "options": [
                            "public",
                            "internal",
                            "confidential",
                            "restricted",
                        ],
                    },
                    {
                        "field_id": "compliance_requirements",
                        "question_text": "Are there specific compliance requirements?",
                        "field_type": "text",
                        "required": False,
                        "category": "compliance",
                        "help_text": "E.g., GDPR, HIPAA, PCI-DSS, SOX",
                    },
                    {
                        "field_id": "disaster_recovery",
                        "question_text": "What is the disaster recovery strategy?",
                        "field_type": "select",
                        "required": False,
                        "category": "compliance",
                        "options": [
                            "active_active",
                            "active_passive",
                            "backup_restore",
                            "none",
                            "in_development",
                        ],
                    },
                ],
                validation_rules={
                    "required": ["application_name", "application_type"],
                },
                completion_status="pending",
                responses_collected=(
                    {
                        # Pre-populate with selected application data if available
                        "application_name": selected_application_name,
                        "_metadata": {
                            "selected_application_id": selected_application_id,
                            "pre_filled_from_asset": bool(selected_application_name),
                        },
                    }
                    if selected_application_name
                    else {}
                ),
                created_at=datetime.utcnow(),
                completed_at=None,
            )

            logger.info(
                "Returning bootstrap questionnaire to enable in-form application selection"
            )
            return [bootstrap_questionnaire]

        return [
            (
                collection_serializers.serialize_adaptive_questionnaire(q)
                if hasattr(q, "__dict__") and hasattr(q, "id")
                else q
            )  # Already serialized from master flow data
            for q in questionnaires
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
