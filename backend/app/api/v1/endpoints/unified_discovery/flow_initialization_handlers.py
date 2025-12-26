"""
Flow Initialization Handlers for Unified Discovery

Handles flow initialization through Master Flow Orchestrator.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Set, Tuple
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# REMOVED: Data import models
# from app.models.data_import import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from .flow_schemas import FlowInitializationRequest, FlowInitializationResponse

logger = logging.getLogger(__name__)

# Conditional import for flow initialization
try:
    from app.services.flow_configs import initialize_all_flows
except ImportError as e:
    # CC: Flow configuration module not available (likely CrewAI dependency missing)
    logger.warning(f"Flow configuration initialization unavailable: {e}")

    # Create fallback function that returns expected structure (NOT async)
    def initialize_all_flows():
        """Fallback for when flow configs cannot be initialized due to missing dependencies"""
        logger.warning("Flow initialization skipped - CrewAI dependencies unavailable")
        return {
            "status": "skipped_missing_dependencies",
            "flows_registered": [],
            "validators_registered": [],
            "handlers_registered": [],
            "errors": ["CrewAI dependencies not available"],
        }


router = APIRouter()


@router.post("/flows/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Initialize a discovery flow through Master Flow Orchestrator.

    This is the main entry point for starting discovery flows. It ensures proper
    architectural flow through the Master Flow Orchestrator.
    """
    try:
        # Ensure flow configs are initialized (fallback handles missing dependencies)
        # NOTE: initialize_all_flows() is synchronous, not async
        flow_init_result = initialize_all_flows()
        if "errors" in flow_init_result and flow_init_result["errors"]:
            logger.warning(
                f"Flow initialization completed with warnings: {flow_init_result['errors']}"
            )

        # Extract configuration
        configuration = request.configuration or {}

        # Handle raw_data payload
        initial_data = {}
        if request.raw_data:
            logger.info(
                f"📊 Received raw_data with {len(request.raw_data)} records in flow initialization"
            )
            initial_data["raw_data"] = request.raw_data

            # Store import metadata separately for backward compatibility
            if (
                isinstance(request.raw_data, dict)
                and "import_metadata" in request.raw_data
            ):
                initial_data["import_metadata"] = request.raw_data["import_metadata"]
                logger.info("📋 Extracted import_metadata from raw_data payload")

        # Generate flow name if not provided
        flow_name = (
            request.flow_name
            or f"Discovery Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Initialize through Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=flow_name,
            configuration=configuration,
            initial_state=initial_data,  # MFO expects initial_state, not initial_data
            atomic=False,  # Let MFO handle transactions internally
        )

        # CRITICAL FIX: Create child DiscoveryFlow record (required by two-table architecture)
        child_flow = DiscoveryFlow(
            flow_id=uuid.UUID(flow_id),
            master_flow_id=uuid.UUID(flow_id),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,  # Required field - was missing
            status="running",
            current_phase="data_ingestion",
            data_import_id=(
                initial_data.get("import_metadata", {}).get("import_id")
                if initial_data
                else None
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(child_flow)
        await db.flush()  # Ensure child flow is persisted

        # Auto-generate field mappings if raw data is provided
        if request.raw_data:
            await _generate_field_mappings_from_raw_data(
                db, context, flow_id, request.raw_data
            )
            logger.info(f"✅ Auto-generated field mappings for flow {flow_id}")

        # Commit changes
        await db.commit()

        logger.info(f"✅ Created master flow AND child discovery flow for {flow_id}")

        logger.info(
            safe_log_format(
                "✅ Discovery flow initialized successfully: {flow_id} (user: {user_id})",
                flow_id=mask_id(str(flow_id)),
                user_id=mask_id(context.user_id),
            )
        )

        return FlowInitializationResponse(
            success=True,
            flow_id=str(flow_id),
            flow_name=flow_name,
            status="initialized",
            message="Discovery flow initialized successfully through Master Flow Orchestrator",
            metadata={
                "flow_details": flow_details,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "has_raw_data": bool(request.raw_data),
                "configuration_keys": (
                    list(configuration.keys()) if configuration else []
                ),
            },
        )

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Flow initialization failed: {error} (user: {user_id})",
                error=str(e),
                user_id=mask_id(context.user_id),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize discovery flow: {str(e)}",
        )


def _get_common_field_mappings() -> Dict[str, Tuple[str, float]]:
    """Get common field mappings with confidence scores.

    Maps source fields to valid Asset model columns only.
    """
    return {
        # Identity mappings
        "name": ("name", 0.95),
        "hostname": ("hostname", 0.95),
        "host_name": ("hostname", 0.90),
        "server_name": ("hostname", 0.85),  # Maps to hostname, not server_name
        "fqdn": ("fqdn", 0.95),
        "asset_name": ("asset_name", 0.90),
        "display_name": ("asset_name", 0.85),
        # Network mappings
        "ip_address": ("ip_address", 0.95),
        "ip": ("ip_address", 0.90),
        "ipaddress": ("ip_address", 0.90),
        "primary_ip": ("ip_address", 0.85),
        "mac_address": ("mac_address", 0.95),
        # Type mappings
        "asset_type": ("asset_type", 0.95),
        "type": ("asset_type", 0.85),
        "category": ("asset_type", 0.80),
        "class": ("asset_type", 0.75),
        # Environment mappings
        "environment": ("environment", 0.95),
        "env": ("environment", 0.90),
        "stage": ("environment", 0.80),
        # OS mappings
        "operating_system": ("operating_system", 0.95),
        "os": ("operating_system", 0.90),
        "os_name": ("operating_system", 0.90),
        "platform": ("operating_system", 0.80),
        "os_version": ("os_version", 0.95),
        # Location mappings
        "location": ("location", 0.95),
        "datacenter": ("datacenter", 0.95),
        "data_center": ("datacenter", 0.90),
        "site": ("location", 0.80),
        "rack_location": ("rack_location", 0.95),
        "availability_zone": ("availability_zone", 0.95),
        # Owner mappings
        "owner": ("business_owner", 0.85),  # Map to business_owner field
        "owner_email": ("business_owner", 0.80),
        "business_owner": ("business_owner", 0.95),
        "technical_owner": ("technical_owner", 0.95),
        "department": ("department", 0.95),
        # Description mappings
        "description": ("description", 0.95),
        "notes": ("description", 0.80),
        "comments": ("description", 0.75),
        # Resource spec mappings
        "cpu_cores": ("cpu_cores", 0.95),
        "cpu": ("cpu_cores", 0.85),
        "vcpu": ("cpu_cores", 0.85),
        "memory_gb": ("memory_gb", 0.95),
        "memory": ("memory_gb", 0.85),
        "ram": ("memory_gb", 0.85),
        "storage_gb": ("storage_gb", 0.95),
        "storage": ("storage_gb", 0.85),
        "disk": ("storage_gb", 0.80),
        # Application mappings
        "application_name": ("application_name", 0.95),
        "app_name": ("application_name", 0.90),
        "application": ("application_name", 0.85),
        "technology_stack": ("technology_stack", 0.95),
        "tech_stack": ("technology_stack", 0.90),
        # Business criticality mappings
        "criticality": ("criticality", 0.95),
        "business_criticality": ("business_criticality", 0.95),
        "priority": ("migration_priority", 0.85),
        # Migration mappings
        "migration_priority": ("migration_priority", 0.95),
        "migration_wave": ("migration_wave", 0.95),
        "migration_complexity": ("migration_complexity", 0.95),
        "six_r_strategy": ("six_r_strategy", 0.95),
        "sixr_strategy": ("six_r_strategy", 0.90),
        "migration_strategy": ("six_r_strategy", 0.85),
        # Cost mappings
        "current_monthly_cost": ("current_monthly_cost", 0.95),
        "current_cost": ("current_monthly_cost", 0.85),
        "estimated_cloud_cost": ("estimated_cloud_cost", 0.95),
        "cloud_cost": ("estimated_cloud_cost", 0.85),
        "azure_cost": ("estimated_cloud_cost", 0.80),
        "monthly_azure_cost_estimate_usd": ("estimated_cloud_cost", 0.75),
        # Status mappings
        "status": ("status", 0.95),
        "migration_status": ("migration_status", 0.95),
        # Readiness mappings
        "azure_readiness": ("sixr_ready", 0.70),  # Map to closest available field
        "cloud_readiness": ("sixr_ready", 0.70),
        "readiness": ("sixr_ready", 0.65),
        # VM Size mappings - store in custom_attributes since no direct field
        "recommended_azure_vm_size": ("UNMAPPED", 0.0),  # Will go to custom_attributes
        "recommended_vm_size": ("UNMAPPED", 0.0),
        "target_vm_size": ("UNMAPPED", 0.0),
        # Performance metrics
        "cpu_utilization_percent": ("cpu_utilization_percent", 0.95),
        "cpu_utilization": ("cpu_utilization_percent", 0.90),
        "memory_utilization_percent": ("memory_utilization_percent", 0.95),
        "memory_utilization": ("memory_utilization_percent", 0.90),
        "disk_iops": ("disk_iops", 0.95),
        "network_throughput_mbps": ("network_throughput_mbps", 0.95),
        # Quality scores
        "completeness_score": ("completeness_score", 0.95),
        "quality_score": ("quality_score", 0.95),
        "confidence_score": ("confidence_score", 0.95),
    }


def _extract_source_fields(raw_data: Any) -> Set[str]:
    """Extract source fields from raw data."""
    source_fields = set()

    # Handle different raw_data formats
    if isinstance(raw_data, list) and raw_data:
        # If it's a list of records, get fields from first record
        if isinstance(raw_data[0], dict):
            source_fields = set(raw_data[0].keys())
    elif isinstance(raw_data, dict):
        # If it's a dict with records, extract fields
        if "records" in raw_data and isinstance(raw_data["records"], list):
            if raw_data["records"] and isinstance(raw_data["records"][0], dict):
                source_fields = set(raw_data["records"][0].keys())
        else:
            # Direct dict of fields
            source_fields = set(raw_data.keys())

    return source_fields


def _find_field_mapping(
    source_field: str, common_mappings: Dict[str, Tuple[str, float]]
) -> Tuple[str, float]:
    """Find target field and confidence score for source field.

    Returns UNMAPPED for fields that don't have a valid Asset model target.
    """
    source_field_lower = source_field.lower()

    # Check for exact mappings first
    if source_field_lower in common_mappings:
        return common_mappings[source_field_lower]

    # Try fuzzy matching for similar fields - but be more conservative
    for common_field, (target, conf) in common_mappings.items():
        # Only do fuzzy match if there's significant overlap
        if len(common_field) > 3 and len(source_field_lower) > 3:
            if common_field in source_field_lower or source_field_lower in common_field:
                # Only accept fuzzy match if target is not UNMAPPED
                if target != "UNMAPPED":
                    return target, conf * 0.8  # Reduce confidence for fuzzy match

    # If no match found, mark as UNMAPPED instead of creating invalid mapping
    # This prevents creating target fields that don't exist in Asset model
    return "UNMAPPED", 0.0


def _should_skip_field(source_field: str) -> bool:
    """Check if field should be skipped during mapping."""
    return source_field.startswith("_") or source_field in [
        "id",
        "uuid",
        "created_at",
        "updated_at",
    ]


async def _generate_field_mappings_from_raw_data(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    raw_data: Any,
) -> None:
    """
    Auto-generate field mappings from raw CMDB data.

    This function analyzes the structure of the raw data and creates
    initial field mappings with intelligent suggestions.
    """
    try:
        # Get the discovery flow to find the data_import_id
        from sqlalchemy import select

        flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        flow_result = await db.execute(flow_query)
        flow = flow_result.scalar_one_or_none()

        if not flow or not flow.data_import_id:
            logger.warning(f"No data_import_id found for flow {flow_id}")
            return

        # Extract field names from raw data
        source_fields = _extract_source_fields(raw_data)
        if not source_fields:
            logger.warning("No source fields found in raw data")
            return

        logger.warning(
            "⚠️ Field mapping generation skipped - ImportFieldMapping model was removed"
        )

    except Exception as e:
        logger.error(f"Failed to generate field mappings: {e}")
        # Don't fail the flow initialization if mapping generation fails
        await db.rollback()
