"""
Admin User Access Management API Endpoints

Provides endpoints for admins to manage user access to clients and engagements.
"""

from fastapi import APIRouter

from . import commands, queries

router = APIRouter()

# Query endpoints (GET)
router.add_api_route(
    "/clients/{user_id}",
    queries.get_user_client_access,
    methods=["GET"],
    name="get_user_client_access",
)

router.add_api_route(
    "/engagements/{user_id}",
    queries.get_user_engagement_access,
    methods=["GET"],
    name="get_user_engagement_access",
)

router.add_api_route(
    "/recent-activities",
    queries.get_recent_activities,
    methods=["GET"],
    name="get_recent_activities",
)

# Command endpoints (POST/DELETE)
router.add_api_route(
    "/clients",
    commands.grant_client_access,
    methods=["POST"],
    name="grant_client_access",
)

router.add_api_route(
    "/engagements",
    commands.grant_engagement_access,
    methods=["POST"],
    name="grant_engagement_access",
)

router.add_api_route(
    "/clients/{access_id}",
    commands.revoke_client_access,
    methods=["DELETE"],
    name="revoke_client_access",
)

router.add_api_route(
    "/engagements/{access_id}",
    commands.revoke_engagement_access,
    methods=["DELETE"],
    name="revoke_engagement_access",
)
