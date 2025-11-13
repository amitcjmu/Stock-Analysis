"""
Data Cleansing API - Resolution Operations Module
Handles storing and applying quality issue resolutions.
"""

import logging
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.data_import.core import RawImportRecord
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .validation import _validate_and_get_flow, _get_data_import_for_flow

# Create resolution router
router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/flows/{flow_id}/data-cleansing/quality-issues/{issue_id}/resolution",
    summary="Store updated field values for an issue in data_quality_resolution (temporary table)",
)
async def store_quality_issue_resolution(
    flow_id: str,
    issue_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """
    Persist edited field values to a temporary storage table `data_quality_resolution`.
    Only the value for the specified field is stored (not the entire record).
    Body:
    {
      "field_name": "operating_system",
      "rows": [ { "IP_Address": "192.168.1.10", "OS": "Linux", ... }, ... ]
    }
    The field value for the specified field_name will be extracted and stored.
    """
    try:
        logger.info(
            f"📝 [RESOLUTION] Starting store_quality_issue_resolution for flow_id={flow_id}, issue_id={issue_id}"
        )
        logger.info(
            f"📝 [RESOLUTION] Payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'not a dict'}"
        )

        # Ensure transaction is in a good state - rollback if needed
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            logger.warning(
                "⚠️ [RESOLUTION] Transaction appears to be in failed state, rolling back..."
            )
            try:
                await db.rollback()
                logger.info("✅ [RESOLUTION] Transaction rolled back successfully")
            except Exception as rollback_err:
                logger.error(
                    f"❌ [RESOLUTION] Failed to rollback transaction: {str(rollback_err)}"
                )

        # Ensure flow exists
        # Per ADR-012: Use child flow (DiscoveryFlow) for operational decisions
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        # Per ADR-012: Returns DiscoveryFlow (child flow) for operational state
        flow = await _validate_and_get_flow(flow_id, flow_repo)
        logger.info(f"✅ [RESOLUTION] Flow {flow_id} validated successfully")

        if not isinstance(payload, dict):
            logger.error(f"❌ [RESOLUTION] Invalid payload type: {type(payload)}")
            raise HTTPException(status_code=400, detail="Invalid request body")
        field_name = payload.get("field_name")
        rows = payload.get("rows", [])
        rows_count = len(rows) if isinstance(rows, list) else "not a list"
        logger.info(f"📝 [RESOLUTION] field_name={field_name}, rows_count={rows_count}")

        if not field_name or not isinstance(rows, list):
            logger.error(
                f"❌ [RESOLUTION] Missing field_name or invalid rows. field_name={field_name}, rows_type={type(rows)}"
            )
            raise HTTPException(status_code=400, detail="Missing field_name or rows")

        # Create table if not exists
        from .resolution_helpers import ensure_resolution_table_exists

        await ensure_resolution_table_exists(db)

        # Resolve the actual field key from field_name
        resolved_field_key = _resolve_field_key(field_name, rows)
        logger.info(
            f"📝 [RESOLUTION] Resolved field key: '{field_name}' -> '{resolved_field_key}'"
        )

        # Insert rows using savepoints to handle individual failures
        inserted, failed, skipped = await _insert_resolution_rows(
            db, flow_id, issue_id, field_name, rows, resolved_field_key, current_user
        )

        logger.info(
            f"📊 [RESOLUTION] Insertion complete: {inserted} succeeded, "
            f"{failed} failed, {skipped} skipped (empty values) out of {len(rows)} total"
        )

        if inserted > 0:
            # Verify by counting rows (within same transaction)
            stored_count = await _count_resolution_rows(
                db, flow_id, issue_id, field_name
            )
            logger.info(
                f"📊 [RESOLUTION] Verification: {stored_count} rows found in table"
            )

            # Automatically apply resolutions to raw_import_records
            # This is done within the same transaction to ensure atomicity
            updated_count, matched_count = await _apply_resolutions_to_raw_records(
                db, flow_id, issue_id, field_name, flow
            )

            # Commit both resolution insertion and raw_record updates in a single transaction
            logger.info(
                f"💾 [RESOLUTION] Committing transaction: {inserted} resolution rows "
                f"and {updated_count} raw_import_record updates..."
            )
            await db.commit()
            logger.info(
                f"✅ [RESOLUTION] Transaction committed successfully. "
                f"{inserted} rows stored in data_quality_resolution table, "
                f"{updated_count} raw_import_records updated"
            )

            return {
                "status": "ok",
                "inserted": inserted,
                "failed": failed,
                "skipped": skipped,
                "total": len(rows),
                "applied_to_raw_records": updated_count,
                "matched": matched_count,
            }
        else:
            logger.warning(
                "⚠️ [RESOLUTION] No rows were inserted, skipping commit and application"
            )

        return {
            "status": "ok",
            "inserted": inserted,
            "failed": failed,
            "skipped": skipped,
            "total": len(rows),
            "applied_to_raw_records": 0,
        }
    except HTTPException as he:
        logger.error(f"❌ [RESOLUTION] HTTPException: {he.status_code} - {he.detail}")
        await db.rollback()
        raise
    except Exception as e:
        logger.exception(
            f"❌ [RESOLUTION] Unexpected error in store_quality_issue_resolution: {type(e).__name__}: {str(e)}"
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store quality issue resolution: {str(e)}",
        ) from e


@router.post(
    "/flows/{flow_id}/data-cleansing/quality-issues/{issue_id}/apply-resolution",
    summary="Apply resolution values from data_quality_resolution to raw_import_records.cleansed_data",
)
async def apply_quality_issue_resolution(
    flow_id: str,
    issue_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """
    Apply stored resolution values to raw_import_records.
    Reads from data_quality_resolution table and updates raw_import_records.cleansed_data
    with the field values, matching records by identifier fields.
    """
    try:
        logger.info(
            f"🔄 [APPLY_RESOLUTION] Starting apply_quality_issue_resolution for flow_id={flow_id}, issue_id={issue_id}"
        )

        # Per ADR-012: Use child flow (DiscoveryFlow) for operational decisions
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        # Per ADR-012: Returns DiscoveryFlow (child flow) for operational state
        flow = await _validate_and_get_flow(flow_id, flow_repo)
        logger.info(f"✅ [APPLY_RESOLUTION] Flow {flow_id} validated successfully")

        data_import = await _get_data_import_for_flow(flow_id, flow, db)
        if not data_import:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data import found for flow {flow_id}",
            )

        # Get all resolution records for this issue
        resolution_query = text(
            """
            SELECT field_name, field_value, record_identifier
            FROM data_quality_resolution
            WHERE flow_id = :flow_id AND issue_id = :issue_id
            """
        )
        resolution_result = await db.execute(
            resolution_query, {"flow_id": flow_id, "issue_id": issue_id}
        )
        resolutions = resolution_result.fetchall()

        if not resolutions:
            logger.warning("⚠️ [APPLY_RESOLUTION] No resolution records found")
            return {
                "status": "ok",
                "message": "No resolution records found to apply",
                "updated": 0,
            }

        logger.info(
            f"📊 [APPLY_RESOLUTION] Found {len(resolutions)} resolution records to apply"
        )

        # Get all raw import records
        raw_records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import.id
        )
        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()

        logger.info(
            f"📊 [APPLY_RESOLUTION] Found {len(raw_records)} raw import records to check"
        )

        updated_count, matched_count = await _apply_resolutions_to_raw_records(
            db, flow_id, issue_id, None, flow, resolutions, raw_records
        )

        if updated_count > 0:
            logger.info(f"💾 [APPLY_RESOLUTION] Committing {updated_count} updates...")
            await db.commit()
            logger.info(
                f"✅ [APPLY_RESOLUTION] Successfully updated {updated_count} raw_import_records"
            )
        else:
            logger.warning("⚠️ [APPLY_RESOLUTION] No records were updated")

        return {
            "status": "ok",
            "message": f"Applied {updated_count} resolution values to raw_import_records",
            "updated": updated_count,
            "matched": matched_count,
            "total_resolutions": len(resolutions),
        }

    except HTTPException as he:
        logger.error(
            f"❌ [APPLY_RESOLUTION] HTTPException: {he.status_code} - {he.detail}"
        )
        raise
    except Exception as e:
        logger.exception(
            f"❌ [APPLY_RESOLUTION] Unexpected error: {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply quality issue resolution: {str(e)}",
        ) from e


# Helper functions


def _resolve_field_key(field_name: str, rows: list) -> str:
    """Resolve the actual field key from field_name (handle case-insensitive matching)."""

    def normalize(s: str) -> str:
        return "".join(ch for ch in s.lower() if ch.isalnum())

    resolved_field_key = field_name
    if rows:
        sample = rows[0]
        if field_name not in sample:
            field_norm = normalize(field_name)
            for key in sample.keys():
                if normalize(key) == field_norm:
                    resolved_field_key = key
                    break
            else:
                alias_map = {
                    "os": ["operating_system", "os", "os_name"],
                    "ip": ["ip", "ip_address", "ipaddr", "ipaddress"],
                }
                for alias, candidates in alias_map.items():
                    if field_norm == alias or any(
                        normalize(c) == field_norm for c in candidates
                    ):
                        for cand in candidates:
                            if cand in sample:
                                resolved_field_key = cand
                                break
                        if resolved_field_key != field_name:
                            break
    return resolved_field_key


def _build_record_identifier(rec: dict, resolved_field_key: str) -> dict:
    """Build record identifier from common identifying fields."""
    record_identifier = {}
    identifier_fields = [
        "ip_address",
        "IP_Address",
        "hostname",
        "Hostname",
        "name",
        "Name",
        "id",
        "ID",
    ]

    # First, try exact matches
    for id_field in identifier_fields:
        if id_field in rec and rec[id_field]:
            record_identifier[id_field] = str(rec[id_field])
            logger.debug(
                f"✅ [RESOLUTION] Using identifier field '{id_field}' = '{record_identifier[id_field]}'"
            )

    # If no exact matches, try case-insensitive matching
    if not record_identifier:
        rec_keys_lower = {k.lower(): k for k in rec.keys()}
        identifier_fields_lower = [f.lower() for f in identifier_fields]

        for id_field_lower, id_field in zip(identifier_fields_lower, identifier_fields):
            if id_field_lower in rec_keys_lower:
                actual_key = rec_keys_lower[id_field_lower]
                if rec[actual_key]:
                    record_identifier[actual_key] = str(rec[actual_key])
                    logger.debug(
                        f"✅ [RESOLUTION] Using identifier field (case-insensitive) "
                        f"'{actual_key}' = '{record_identifier[actual_key]}'"
                    )

    # If still no identifier found, use all non-empty fields as fallback
    if not record_identifier:
        logger.debug(
            "⚠️ [RESOLUTION] No standard identifier found, using fallback fields"
        )
        for key, val in rec.items():
            if val and key != resolved_field_key:
                record_identifier[key] = str(val)
                if len(record_identifier) >= 3:
                    break

    return record_identifier


async def _insert_resolution_rows(
    db: AsyncSession,
    flow_id: str,
    issue_id: str,
    field_name: str,
    rows: list,
    resolved_field_key: str,
    current_user: User,
) -> tuple[int, int, int]:
    """Insert resolution rows into data_quality_resolution table."""
    logger.info(
        f"📥 [RESOLUTION] Starting insertion of {len(rows)} rows (only updated rows will be stored)..."
    )
    inserted = 0
    failed = 0
    skipped = 0

    for idx, rec in enumerate(rows):
        savepoint_name = f"sp_row_{idx}"
        try:
            # Extract the field value
            field_value = rec.get(resolved_field_key, "")
            if field_value is None:
                field_value = ""
            elif not isinstance(field_value, str):
                field_value = str(field_value)

            # Only store rows where the field value was actually updated (non-empty)
            if not field_value or field_value.strip() == "":
                logger.debug(
                    f"⏭️ [RESOLUTION] Skipping row {idx + 1} - field value is empty (not updated)"
                )
                skipped += 1
                continue

            # Build record identifier
            record_identifier = _build_record_identifier(rec, resolved_field_key)

            # Create savepoint
            await db.execute(text(f"SAVEPOINT {savepoint_name}"))

            try:
                # Primary: let database generate UUID via DEFAULT
                insert_stmt = text(
                    """
                    INSERT INTO data_quality_resolution
                    (flow_id, issue_id, field_name, field_value, record_identifier, updated_by)
                    VALUES (:flow_id, :issue_id, :field_name, :field_value,
                            CAST(:record_identifier AS JSONB), :updated_by)
                    """
                )
                await db.execute(
                    insert_stmt,
                    {
                        "flow_id": flow_id,
                        "issue_id": issue_id,
                        "field_name": field_name,
                        "field_value": field_value,
                        "record_identifier": (
                            json.dumps(record_identifier) if record_identifier else None
                        ),
                        "updated_by": str(current_user.id),
                    },
                )
                await db.execute(text(f"RELEASE SAVEPOINT {savepoint_name}"))
                logger.debug(
                    f"✅ [RESOLUTION] Row {idx + 1} inserted successfully (DEFAULT UUID method)"
                )
                inserted += 1
            except Exception as e1:
                await db.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
                logger.warning(
                    f"⚠️ [RESOLUTION] DEFAULT UUID insert failed for row {idx + 1}: {str(e1)}, trying Python UUID..."
                )

                try:
                    # Fallback: generate UUID in Python
                    row_uuid = str(uuid.uuid4())
                    insert_stmt_fallback = text(
                        """
                        INSERT INTO data_quality_resolution
                        (id, flow_id, issue_id, field_name, field_value, record_identifier, updated_by)
                        VALUES (:id, :flow_id, :issue_id, :field_name, :field_value,
                                CAST(:record_identifier AS JSONB), :updated_by)
                        """
                    )
                    await db.execute(
                        insert_stmt_fallback,
                        {
                            "id": row_uuid,
                            "flow_id": flow_id,
                            "issue_id": issue_id,
                            "field_name": field_name,
                            "field_value": field_value,
                            "record_identifier": (
                                json.dumps(record_identifier)
                                if record_identifier
                                else None
                            ),
                            "updated_by": str(current_user.id),
                        },
                    )
                    await db.execute(text(f"RELEASE SAVEPOINT {savepoint_name}"))
                    logger.debug(
                        f"✅ [RESOLUTION] Row {idx + 1} inserted successfully (Python UUID method)"
                    )
                    inserted += 1
                except Exception as e2:
                    await db.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
                    # Savepoint is automatically discarded after rollback, no need to release
                    logger.error(
                        f"❌ [RESOLUTION] Both insert methods failed for row {idx + 1}: {str(e2)}"
                    )
                    failed += 1
                    continue
        except Exception as e:
            try:
                await db.execute(text(f"ROLLBACK TO SAVEPOINT {savepoint_name}"))
                # Savepoint is automatically discarded after rollback, no need to release
            except Exception:
                pass
            logger.error(
                f"❌ [RESOLUTION] Unexpected error inserting row {idx + 1}: {str(e)}"
            )
            failed += 1
            continue

    return inserted, failed, skipped


async def _count_resolution_rows(
    db: AsyncSession, flow_id: str, issue_id: str, field_name: str
) -> int:
    """Count resolution rows in the table."""
    count_stmt = text(
        """
        SELECT COUNT(*) FROM data_quality_resolution
        WHERE flow_id = :flow_id AND issue_id = :issue_id AND field_name = :field_name
        """
    )
    count_result = await db.execute(
        count_stmt, {"flow_id": flow_id, "issue_id": issue_id, "field_name": field_name}
    )
    return count_result.scalar() or 0


async def _apply_resolutions_to_raw_records(
    db: AsyncSession,
    flow_id: str,
    issue_id: str,
    field_name: str | None,
    flow,
    resolutions=None,
    raw_records=None,
) -> tuple[int, int]:
    """Apply resolution values to raw_import_records.cleansed_data."""
    from .resolution_helpers import (
        get_resolutions,
        get_raw_records,
        match_record_by_identifier,
        update_cleansed_data,
    )

    logger.info(
        "🔄 [RESOLUTION] Starting automatic application of resolutions to raw_import_records..."
    )

    # Get data import
    data_import = await _get_data_import_for_flow(flow_id, flow, db)
    if not data_import:
        logger.warning(f"⚠️ [RESOLUTION] No data import found for flow {flow_id}")
        return 0, 0

    logger.info(
        f"✅ [RESOLUTION] Found data import {data_import.id} for flow {flow_id}"
    )

    # Get resolutions if not provided
    if resolutions is None:
        resolutions = await get_resolutions(db, flow_id, issue_id, field_name)

    if not resolutions:
        logger.warning("⚠️ [RESOLUTION] No resolution records found to apply")
        return 0, 0

    logger.info(
        f"📊 [RESOLUTION] Retrieved {len(resolutions)} resolution records to apply"
    )

    # Get raw records if not provided
    if raw_records is None:
        raw_records = await get_raw_records(db, data_import.id)

    logger.info(
        f"📊 [RESOLUTION] Found {len(raw_records)} raw import records to check for matching"
    )

    # Log sample records for debugging
    if raw_records:
        for idx, rec in enumerate(raw_records[:3]):
            raw_data = rec.raw_data or {}
            cleansed_data = rec.cleansed_data or {}
            logger.info(f"📋 [RESOLUTION] Raw record {idx + 1} (id={rec.id}):")
            logger.info(f"   raw_data keys: {list(raw_data.keys())}")
            logger.info(
                f"   cleansed_data keys: {list(cleansed_data.keys()) if cleansed_data else 'None/Empty'}"
            )

    updated_count = 0
    matched_count = 0

    # Process each resolution
    for res_idx, resolution in enumerate(resolutions):
        res_field_name = resolution.field_name
        res_field_value = resolution.field_value
        res_record_identifier = resolution.record_identifier or {}

        logger.info(
            f"🔍 [RESOLUTION] Processing resolution {res_idx + 1}/{len(resolutions)}: "
            f"field_name={res_field_name}, field_value={res_field_value}, "
            f"identifier={res_record_identifier}"
        )

        # Find matching raw import record
        matched_record, resolved_cleansed_field_name = await match_record_by_identifier(
            raw_records, res_record_identifier, res_field_name
        )

        if matched_record and resolved_cleansed_field_name:
            try:
                updated = await update_cleansed_data(
                    matched_record, resolved_cleansed_field_name, res_field_value
                )
                if updated:
                    updated_count += 1
                    matched_count += 1
                    logger.info(
                        f"✅ [RESOLUTION] Updated raw_record {matched_record.id}.cleansed_data"
                        f"['{resolved_cleansed_field_name}']: '' -> '{res_field_value}'"
                    )
            except Exception as update_err:
                logger.error(
                    f"❌ [RESOLUTION] Failed to update raw_record {matched_record.id}: {str(update_err)}"
                )
                logger.exception("Update error traceback:")
        else:
            if res_idx < 3:
                logger.warning(
                    f"⚠️ [RESOLUTION] No matching raw_record found for resolution "
                    f"{res_idx + 1} with identifier {res_record_identifier}"
                )

    if updated_count > 0:
        logger.info(
            f"💾 [RESOLUTION] Flushing {updated_count} updates to raw_import_records.cleansed_data..."
        )
        await db.flush()
        logger.info(
            f"✅ [RESOLUTION] Successfully updated {updated_count} raw_import_records with cleansed_data"
        )
    else:
        logger.warning(
            f"⚠️ [RESOLUTION] No raw_import_records were updated (matched {matched_count} but none had empty fields)"
        )

    return updated_count, matched_count
