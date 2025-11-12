"""
Data Cleansing API - Suggestion Operations Module
Handles suggesting values for missing fields.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.data_import.core import RawImportRecord
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.api.v1.endpoints.data_import.utilities import get_suggested_value

from .validation import _validate_and_get_flow, _get_data_import_for_flow
from .analysis import _perform_data_cleansing_analysis

# Create suggestion router
router = APIRouter()

logger = logging.getLogger(__name__)


@router.api_route(
    "/flows/{flow_id}/data-cleansing/quality-issues/{issue_id}/suggest",
    methods=["GET", "POST"],
    summary="Suggest values for records with missing field for a specific quality issue",
)
async def suggest_missing_values_for_issue(
    flow_id: str,
    issue_id: str,
    limit: int = Query(200, ge=1, le=1000, description="Max rows to return"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """
    Return records where the issue's field is empty, with suggested values populated.
    Uses existing data utilities/agent suggestions to infer values. The client may update these before finalizing.
    """
    try:
        logger.info(f"Suggesting missing values for issue {issue_id} in flow {flow_id}")

        # Get flow
        # Per ADR-012: Use child flow (DiscoveryFlow) for operational decisions
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        # Per ADR-012: Returns DiscoveryFlow (child flow) for operational state
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Get data import for this flow
        data_import = await _get_data_import_for_flow(flow_id, flow, db)
        if not data_import:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data import found for flow {flow_id}",
            )

        # Get the analysis to resolve the issue's field_name
        analysis_result = await _perform_data_cleansing_analysis(
            flow_id=flow_id,
            data_imports=[data_import],
            field_mappings=[],
            include_details=True,
            db_session=db,
        )

        # Find the issue
        issue = next(
            (i for i in analysis_result.quality_issues if i.id == issue_id), None
        )
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue {issue_id} not found for flow {flow_id}",
            )

        field_label = issue.field_name

        # Query raw records and filter empties for the field
        raw_records_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == data_import.id)
            .limit(2000)  # broader scan before limiting response
        )
        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()

        def normalize(s: str) -> str:
            return "".join(ch for ch in s.lower() if ch.isalnum())

        # Resolve actual key present in data
        resolved_key = field_label
        if raw_records:
            sample = raw_records[0].raw_data or {}
            if field_label not in sample:
                lbl_norm = normalize(field_label)
                # try normalized match
                for k in sample.keys():
                    if normalize(k) == lbl_norm:
                        resolved_key = k
                        break
                else:
                    # simple aliasing
                    alias_map = {
                        "os": ["operating_system", "os", "os_name"],
                        "ip": ["ip", "ip_address", "ipaddr", "ipaddress"],
                    }
                    for alias, candidates in alias_map.items():
                        if lbl_norm == alias or any(
                            normalize(c) == lbl_norm for c in candidates
                        ):
                            for cand in candidates:
                                if cand in sample:
                                    resolved_key = cand
                                    break
                            break

        suggested_rows = []
        for record in raw_records:
            rd = record.raw_data or {}
            value = rd.get(resolved_key)
            is_empty = value is None or (isinstance(value, str) and value.strip() == "")
            if is_empty:
                # Use existing suggestion utility (agent-backed service can be wired here)
                suggestion = get_suggested_value(resolved_key, rd)
                shaped = dict(rd)
                shaped[resolved_key] = suggestion
                suggested_rows.append(shaped)
                if len(suggested_rows) >= limit:
                    break

        logger.info(
            f"Returning {len(suggested_rows)} suggested rows for issue {issue_id} (field: {resolved_key})"
        )
        return {
            "field_key": resolved_key,
            "count": len(suggested_rows),
            "rows": suggested_rows,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to suggest missing values for issue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest missing values: {str(e)}",
        ) from e
