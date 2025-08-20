"""
API health and introspection endpoints.

Provides information about registered routes, tags, and API configuration.
"""

import logging
from typing import Dict, Any
from collections import defaultdict

from fastapi import APIRouter, Request
from datetime import datetime

from app.api.v1.api_tags import APITags

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api-info")
async def get_api_info(request: Request) -> Dict[str, Any]:
    """
    Get comprehensive API information including routes and tags.

    This endpoint provides:
    - Total route count
    - Routes per tag
    - Untagged routes
    - Route registration summary
    """
    app = request.app

    # Collect all routes
    routes_by_tag = defaultdict(list)
    untagged_routes = []
    total_routes = 0

    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            path = route.path
            methods = list(route.methods) if route.methods else []

            # Skip non-API routes
            if not path.startswith("/api/"):
                continue

            total_routes += len(methods)

            # Get tags from route
            tags = []
            if hasattr(route, "endpoint") and hasattr(route.endpoint, "tags"):
                tags = route.endpoint.tags
            elif hasattr(route, "tags"):
                tags = route.tags

            # Categorize route
            if tags:
                for tag in tags:
                    for method in methods:
                        routes_by_tag[tag].append(f"{method} {path}")
            else:
                for method in methods:
                    untagged_routes.append(f"{method} {path}")

    # Count routes per tag
    tag_counts = {tag: len(routes) for tag, routes in routes_by_tag.items()}

    # Check for invalid tags
    invalid_tags = [tag for tag in tag_counts.keys() if not APITags.validate_tag(tag)]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "v1",
        "total_routes": total_routes,
        "total_tags": len(tag_counts),
        "tag_counts": dict(sorted(tag_counts.items())),
        "untagged_count": len(untagged_routes),
        "invalid_tags": invalid_tags,
        "canonical_tags": APITags.get_all_tags(),
        "health_status": "healthy" if not invalid_tags else "warning",
        "warnings": [
            f"Found {len(invalid_tags)} invalid tags" if invalid_tags else None,
            (
                f"Found {len(untagged_routes)} untagged routes"
                if untagged_routes
                else None
            ),
        ],
        "sample_untagged": untagged_routes[:10] if untagged_routes else [],
    }


@router.get("/api-tags")
async def get_api_tags() -> Dict[str, Any]:
    """
    Get list of all canonical API tags.

    Returns the official tag list that should be used for all endpoints.
    """
    return {
        "canonical_tags": APITags.get_all_tags(),
        "total_tags": len(APITags.get_all_tags()),
        "categories": {
            "authentication": [
                APITags.AUTHENTICATION,
                APITags.USER_MANAGEMENT,
                APITags.ADMIN_USER_MANAGEMENT,
            ],
            "data_import": [
                APITags.DATA_IMPORT_CORE,
                APITags.FIELD_MAPPING,
                APITags.FIELD_MAPPING_ANALYSIS,
                APITags.FIELD_MAPPING_CRUD,
                APITags.FIELD_MAPPING_UTILITIES,
                APITags.IMPORT_STORAGE,
                APITags.IMPORT_RETRIEVAL,
                APITags.ASSET_PROCESSING,
                APITags.CRITICAL_ATTRIBUTES,
                APITags.CLEAN_API,
            ],
            "administration": [
                APITags.CLIENT_MANAGEMENT,
                APITags.ENGAGEMENT_MANAGEMENT,
                APITags.PLATFORM_ADMIN,
                APITags.SECURITY_MONITORING,
                APITags.FLOW_COMPARISON,
            ],
            "monitoring": [
                APITags.AGENT_MONITORING,
                APITags.AGENT_PERFORMANCE,
                APITags.CREWAI_FLOW_MONITORING,
                APITags.ERROR_MONITORING,
                APITags.HEALTH_METRICS,
                APITags.ANALYSIS_QUEUES,
            ],
            "business": [
                APITags.FINOPS,
                APITags.MASTER_FLOW_COORDINATION,
                APITags.AI_LEARNING,
            ],
            "assessment": [
                APITags.ASSESSMENT_FLOW_MANAGEMENT,
                APITags.ARCHITECTURE_STANDARDS,
                APITags.COMPONENT_ANALYSIS,
                APITags.TECH_DEBT_ANALYSIS,
                APITags.SIXR_DECISIONS,
                APITags.FLOW_FINALIZATION,
            ],
            "discovery": [
                APITags.UNIFIED_DISCOVERY,
                APITags.COLLECTION_FLOW,
                APITags.DEPENDENCY_ANALYSIS,
                APITags.AGENT_INSIGHTS,
            ],
            "system": [
                APITags.SYSTEM_HEALTH,
                APITags.EMERGENCY_CONTROL,
                APITags.WEBSOCKET_CACHE,
            ],
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/startup-summary")
async def get_startup_summary(request: Request) -> Dict[str, Any]:
    """
    Get a startup summary suitable for logging at application start.

    This provides a quick overview of the API configuration.
    """
    info = await get_api_info(request)

    # Format for logging
    summary_lines = [
        "=" * 60,
        "API Startup Summary",
        "=" * 60,
        f"Total Routes: {info['total_routes']}",
        f"Total Tags: {info['total_tags']}",
        f"Untagged Routes: {info['untagged_count']}",
        f"Invalid Tags: {len(info['invalid_tags'])}",
        "",
        "Routes per Tag:",
    ]

    for tag, count in sorted(info["tag_counts"].items(), key=lambda x: -x[1])[:10]:
        summary_lines.append(f"  {tag}: {count}")

    if info["total_tags"] > 10:
        summary_lines.append(f"  ...and {info['total_tags'] - 10} more tags")

    summary_lines.append("=" * 60)

    # Log the summary
    for line in summary_lines:
        logger.info(line)

    return {
        "summary": "\n".join(summary_lines),
        "timestamp": datetime.utcnow().isoformat(),
        "health_status": info["health_status"],
    }
