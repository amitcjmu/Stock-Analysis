"""
API handlers for governance endpoints.

Provides FastAPI route handlers for governance requirements and migration exceptions.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.models.api.collection_gaps import StandardErrorResponse
from app.repositories.governance_repository import (
    ApprovalRequestRepository,
    MigrationExceptionRepository,
)

from .schemas import (
    GovernanceRequirementRequest,
    GovernanceRequirementResponse,
    MigrationExceptionRequest,
    MigrationExceptionResponse,
)
from .utils import (
    format_optional_id,
    format_timestamp,
    generate_approval_notes,
    requires_approval,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/governance")


@router.get(
    "/requirements",
    response_model=List[GovernanceRequirementResponse],
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="List governance requirements",
    description=(
        "Get approval requests with optional filtering by status and entity type."
    ),
)
async def list_governance_requirements(
    status: Optional[str] = Query(
        None, description="Filter by approval status (PENDING, APPROVED, REJECTED)"
    ),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    approver_id: Optional[str] = Query(None, description="Filter by approver ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> List[GovernanceRequirementResponse]:
    """
    List governance requirements (approval requests) with flexible filtering.

    Supports filtering by status, entity type, and approver for comprehensive
    governance oversight and workflow management.
    """
    try:
        # Initialize repository with tenant context
        repo = ApprovalRequestRepository(
            db, context.client_account_id, context.engagement_id
        )

        if status == "PENDING":
            # Get pending requests with optional filters
            requests = await repo.get_pending_requests(
                entity_type=entity_type, entity_id=entity_id
            )
        elif approver_id:
            # Get requests by approver
            requests = await repo.get_by_approver(
                approver_id=approver_id, status=status
            )
        elif entity_type and entity_id:
            # Get requests for specific entity
            requests = await repo.get_by_entity(
                entity_type=entity_type, entity_id=entity_id
            )
        else:
            # Get all requests with optional status filter
            if status:
                requests = await repo.get_by_filters(status=status)
            else:
                requests = await repo.get_all()

        # Apply limit and convert to response models
        limited_requests = requests[:limit]

        results = []
        for request in limited_requests:
            results.append(
                GovernanceRequirementResponse(
                    id=str(request.id),
                    entity_type=request.entity_type,
                    entity_id=format_optional_id(request.entity_id),
                    status=request.status,
                    notes=request.notes,
                    requested_at=format_timestamp(request.requested_at),
                    decided_at=format_timestamp(request.decided_at),
                    approver_id=format_optional_id(request.approver_id),
                )
            )

        logger.info(
            f"✅ Retrieved {len(results)} governance requirements for "
            f"client {context.client_account_id}, engagement {context.engagement_id}"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Failed to list governance requirements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "list_failed",
                "message": f"Failed to list governance requirements: {str(e)}",
                "details": {
                    "status": status,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                },
            },
        )


@router.post(
    "/requirements",
    response_model=GovernanceRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Create governance requirement",
    description="Create a new approval request for governance compliance.",
)
async def create_governance_requirement(
    request: GovernanceRequirementRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> GovernanceRequirementResponse:
    """
    Create a new governance requirement (approval request).

    Initiates an approval workflow for the specified entity,
    typically used for high-risk exceptions or custom approaches.
    """
    try:
        async with db.begin():
            # Initialize repository
            repo = ApprovalRequestRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Create the approval request
            created_request = await repo.create_request(
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                notes=request.notes,
                commit=False,  # Will commit with transaction
            )

            await db.flush()  # Ensure ID is available

            result = GovernanceRequirementResponse(
                id=str(created_request.id),
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                status="PENDING",
                notes=request.notes,
                requested_at=format_timestamp(created_request.requested_at),
                decided_at=None,
                approver_id=None,
            )

            logger.info(
                f"✅ Created governance requirement {created_request.id} for "
                f"client {context.client_account_id}, "
                f"engagement {context.engagement_id}"
            )

            return result

    except Exception as e:
        logger.error(f"❌ Failed to create governance requirement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "creation_failed",
                "message": f"Failed to create governance requirement: {str(e)}",
                "details": {
                    "entity_type": request.entity_type,
                    "entity_id": request.entity_id,
                },
            },
        )


@router.get(
    "/exceptions",
    response_model=List[MigrationExceptionResponse],
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="List migration exceptions",
    description=(
        "Get migration exceptions with optional filtering by status, "
        "risk level, and scope."
    ),
)
async def list_migration_exceptions(
    status: Optional[str] = Query(
        None, description="Filter by exception status (OPEN, CLOSED)"
    ),
    risk_level: Optional[str] = Query(
        None, description="Filter by risk level (low, medium, high, critical)"
    ),
    exception_type: Optional[str] = Query(None, description="Filter by exception type"),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    high_risk_only: bool = Query(
        False, description="Show only high and critical risk exceptions"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> List[MigrationExceptionResponse]:
    """
    List migration exceptions with comprehensive filtering options.

    Supports filtering by status, risk level, scope, and type for
    effective exception tracking and risk management.
    """
    try:
        # Initialize repository with tenant context
        repo = MigrationExceptionRepository(
            db, context.client_account_id, context.engagement_id
        )

        if high_risk_only:
            # Get high and critical risk exceptions
            exceptions = await repo.get_high_risk_exceptions()
        elif status == "OPEN":
            # Get open exceptions with optional filters
            exceptions = await repo.get_open_exceptions(
                exception_type=exception_type, risk_level=risk_level
            )
        elif application_id or asset_id:
            # Get exceptions by scope
            exceptions = await repo.get_by_scope(
                application_id=application_id, asset_id=asset_id, status=status
            )
        else:
            # Get all exceptions with optional filters
            filters = {}
            if status:
                filters["status"] = status
            if risk_level:
                filters["risk_level"] = risk_level
            if exception_type:
                filters["exception_type"] = exception_type

            if filters:
                exceptions = await repo.get_by_filters(**filters)
            else:
                exceptions = await repo.get_all()

        # Apply limit and convert to response models
        limited_exceptions = exceptions[:limit]

        results = []
        for exception in limited_exceptions:
            results.append(
                MigrationExceptionResponse(
                    id=str(exception.id),
                    exception_type=exception.exception_type,
                    rationale=exception.rationale,
                    risk_level=exception.risk_level,
                    status=exception.status,
                    application_id=format_optional_id(exception.application_id),
                    asset_id=format_optional_id(exception.asset_id),
                    approval_request_id=format_optional_id(
                        exception.approval_request_id
                    ),
                    created_at=(
                        exception.created_at.isoformat()
                        if hasattr(exception, "created_at") and exception.created_at
                        else ""
                    ),
                )
            )

        logger.info(
            f"✅ Retrieved {len(results)} migration exceptions for "
            f"client {context.client_account_id}, engagement {context.engagement_id}"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Failed to list migration exceptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "list_failed",
                "message": f"Failed to list migration exceptions: {str(e)}",
                "details": {
                    "status": status,
                    "risk_level": risk_level,
                    "exception_type": exception_type,
                },
            },
        )


@router.post(
    "/exceptions",
    response_model=MigrationExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Create migration exception",
    description=(
        "Create a new migration exception with automatic approval "
        "workflow for high-risk cases."
    ),
)
async def create_migration_exception(
    request: MigrationExceptionRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> MigrationExceptionResponse:
    """
    Create a new migration exception.

    Automatically creates approval requests for high-risk exceptions
    or specific exception types that require governance approval.
    """
    try:
        async with db.begin():
            # Initialize repositories
            exception_repo = MigrationExceptionRepository(
                db, context.client_account_id, context.engagement_id
            )
            approval_repo = ApprovalRequestRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Create the migration exception
            created_exception = await exception_repo.create_exception(
                exception_type=request.exception_type,
                rationale=request.rationale,
                risk_level=request.risk_level,
                application_id=request.application_id,
                asset_id=request.asset_id,
                commit=False,  # Will commit with transaction
            )

            await db.flush()  # Ensure ID is available

            # Check if automatic approval request is needed
            approval_request_id = None
            if requires_approval(request.risk_level, request.exception_type):
                # Create approval request
                approval_request = await approval_repo.create_request(
                    entity_type="migration_exception",
                    entity_id=str(created_exception.id),
                    notes=generate_approval_notes(
                        request.risk_level, request.exception_type
                    ),
                    commit=False,
                )
                await db.flush()

                # Link approval request to exception
                await exception_repo.update(
                    str(created_exception.id),
                    commit=False,
                    approval_request_id=str(approval_request.id),
                )
                approval_request_id = str(approval_request.id)

            result = MigrationExceptionResponse(
                id=str(created_exception.id),
                exception_type=request.exception_type,
                rationale=request.rationale,
                risk_level=request.risk_level,
                status="OPEN",
                application_id=request.application_id,
                asset_id=request.asset_id,
                approval_request_id=approval_request_id,
                created_at="",  # Would need to add created_at to model
            )

            logger.info(
                f"✅ Created migration exception {created_exception.id} for "
                f"client {context.client_account_id}, "
                f"engagement {context.engagement_id}"
                + (
                    f" with approval request {approval_request_id}"
                    if approval_request_id
                    else ""
                )
            )

            return result

    except Exception as e:
        logger.error(f"❌ Failed to create migration exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "creation_failed",
                "message": f"Failed to create migration exception: {str(e)}",
                "details": {
                    "exception_type": request.exception_type,
                    "risk_level": request.risk_level,
                },
            },
        )
