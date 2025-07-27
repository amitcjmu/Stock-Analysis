"""
Application-Server Mappings Endpoints.
Handles relationships between applications and servers.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.api.v1.discovery.persistence import get_processed_assets
from app.api.v1.discovery.serialization import clean_for_json_serialization

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/app-server-mappings")
async def get_app_server_mappings():
    """
    Get application to server mappings for dependency visualization.
    """
    try:
        all_assets = get_processed_assets()

        # Extract actual applications from the current asset inventory
        applications = []
        for asset in all_assets:
            asset_type = asset.get("intelligent_asset_type") or asset.get(
                "asset_type", ""
            )
            if asset_type and asset_type.lower() == "application":
                app_data = {
                    "id": asset.get("ci_id")
                    or asset.get("id")
                    or str(asset.get("hostname", "unknown")),
                    "name": asset.get("asset_name") or asset.get("hostname", "Unknown"),
                    "department": asset.get("business_owner", "Unknown"),
                    "environment": asset.get("environment", "Unknown"),
                    "criticality": asset.get("status", "Unknown"),
                    "hostname": asset.get("hostname", ""),
                    "ip_address": asset.get("ip_address", ""),
                    "operating_system": asset.get("operating_system", ""),
                    "version": asset.get("version/hostname", ""),
                    "location": asset.get("location", ""),
                    "_original": asset,
                }
                applications.append(app_data)

        # Build mappings from real assets if we have them
        if applications:
            real_mappings = _build_app_server_mappings_from_apps(
                applications, all_assets
            )
            summary = _get_mapping_summary(real_mappings)
            summary["total_applications"] = len(applications)

            return {
                "mappings": real_mappings,
                "applications": applications,  # Frontend expects this
                "total_count": len(real_mappings),
                "summary": summary,
            }

        # Fallback: Create demo data if no applications found
        demo_application = {
            "id": "demo-app-1",
            "name": "Demo Application",
            "department": "IT",
            "environment": "Development",
            "criticality": "Medium",
            "hostname": "demo-app",
            "ip_address": "192.168.1.100",
            "operating_system": "Ubuntu 20.04",
            "version": "1.0.0",
            "location": "Data Center 1",
        }

        demo_mappings = [
            {
                "id": "mapping-demo",
                "application": demo_application,
                "servers": [],
                "dependencies": [],
                "created_date": "2024-01-15T10:30:00Z",
                "last_updated": "2024-01-20T14:15:00Z",
            }
        ]

        return {
            "mappings": demo_mappings,
            "applications": [demo_application],  # Frontend expects this
            "total_count": len(demo_mappings),
            "summary": {
                "total_applications": 1,
                "total_servers": 0,
                "avg_servers_per_app": 0.0,
                "by_environment": {"Development": 1},
                "by_department": {"IT": 1},
            },
        }

    except Exception as e:
        logger.error(f"Error retrieving app-server mappings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve mappings: {str(e)}"
        )


@router.post("/app-server-mappings/{app_id}/add-server")
async def add_server_to_app(app_id: str, server_data: Dict[str, Any]):
    """
    Add a server mapping to an application.
    """
    try:
        # For now, this is a placeholder that simulates adding a server mapping
        # In a real implementation, this would:
        # 1. Validate the application exists
        # 2. Validate the server data
        # 3. Create the mapping relationship
        # 4. Store in database/persistence layer

        logger.info(f"Adding server mapping for app {app_id}: {server_data}")

        # Simulate successful creation
        mapping_id = f"mapping-{app_id}-{server_data.get('hostname', 'unknown')}"

        return {
            "status": "success",
            "message": f"Server mapping created for application {app_id}",
            "mapping_id": mapping_id,
            "server_data": clean_for_json_serialization(server_data),
        }

    except Exception as e:
        logger.error(f"Error adding server mapping for app {app_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to add server mapping: {str(e)}"
        )


# Helper functions
def _build_app_server_mappings(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build application-server mappings from asset data."""
    mappings = []

    # Group assets by application
    app_groups = {}

    for asset in assets:
        app_name = asset.get("application_name")
        if not app_name:
            continue

        if app_name not in app_groups:
            app_groups[app_name] = {"application": None, "servers": []}

        asset_type = asset.get("asset_type", "").lower()

        if "application" in asset_type or "service" in asset_type:
            app_groups[app_name]["application"] = asset
        elif "server" in asset_type:
            app_groups[app_name]["servers"].append(asset)

    # Create mappings for groups that have both application and servers
    for app_name, group in app_groups.items():
        if group["application"] and group["servers"]:
            mapping = {
                "id": f"mapping-{group['application'].get('id', app_name)}",
                "application": {
                    "id": group["application"].get("id"),
                    "name": app_name,
                    "department": group["application"].get("department"),
                    "environment": group["application"].get("environment"),
                    "criticality": group["application"].get("criticality"),
                },
                "servers": [
                    {
                        "id": server.get("id"),
                        "hostname": server.get("hostname"),
                        "role": server.get("asset_type", "Server"),
                        "environment": server.get("environment"),
                        "dependencies": (
                            server.get("dependencies", "").split(",")
                            if server.get("dependencies")
                            else []
                        ),
                    }
                    for server in group["servers"]
                ],
                "dependencies": _extract_dependencies(group["application"]),
                "created_date": group["application"].get("processed_timestamp"),
                "last_updated": group["application"].get(
                    "updated_timestamp", group["application"].get("processed_timestamp")
                ),
            }
            mappings.append(mapping)

    return mappings


def _extract_dependencies(app_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract dependencies from application data."""
    dependencies = []

    # Look for dependencies in the original asset data
    original = app_data.get("_original", {})
    deps = original.get("dependencies", "")

    if deps:
        for dep in deps.split(","):
            dep = dep.strip()
            if dep and dep.lower() != "unknown":
                dependencies.append(
                    {"type": "service", "target": dep, "connection_type": "Unknown"}
                )

    return dependencies


def _get_mapping_summary(mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get summary statistics for mappings."""
    total_applications = len(mappings)
    total_servers = sum(len(mapping.get("servers", [])) for mapping in mappings)

    # Count by environment
    env_count = {}
    dept_count = {}

    for mapping in mappings:
        env = mapping.get("application", {}).get("environment", "Unknown")
        env_count[env] = env_count.get(env, 0) + 1

        dept = mapping.get("application", {}).get("department", "Unknown")
        dept_count[dept] = dept_count.get(dept, 0) + 1

    return {
        "total_applications": total_applications,
        "total_servers": total_servers,
        "avg_servers_per_app": (
            round(total_servers / total_applications, 2)
            if total_applications > 0
            else 0
        ),
        "by_environment": env_count,
        "by_department": dept_count,
    }


def _build_app_server_mappings_from_apps(
    applications: List[Dict[str, Any]], all_assets: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Build application-server mappings from a list of applications and all assets."""
    mappings = []

    for app in applications:
        app_name = app["name"]
        app_id = app["id"]

        # Find all servers that depend on this application
        dependent_servers = []
        for asset in all_assets:
            if asset.get("dependencies"):
                for dep in asset["dependencies"].split(","):
                    if dep.strip() == app_name:
                        dependent_servers.append(asset)

        if dependent_servers:
            mapping = {
                "id": f"mapping-{app_id}",
                "application": app,
                "servers": [
                    {
                        "id": server.get("id"),
                        "hostname": server.get("hostname"),
                        "role": server.get("asset_type", "Server"),
                        "environment": server.get("environment"),
                        "dependencies": (
                            server.get("dependencies", "").split(",")
                            if server.get("dependencies")
                            else []
                        ),
                    }
                    for server in dependent_servers
                ],
                "dependencies": _extract_dependencies(app),
                "created_date": app.get("processed_timestamp"),
                "last_updated": app.get(
                    "updated_timestamp", app.get("processed_timestamp")
                ),
            }
            mappings.append(mapping)

    return mappings
