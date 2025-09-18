"""
Data Cleansing API - Exports Module
Download functionality for raw and cleaned data as CSV files.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.config import settings
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.data_import.core import RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .audit_utils import log_raw_data_export_audit, log_cleaned_data_export_audit
from .base import router
from .csv_utils import (
    generate_filename,
    generate_raw_csv_content,
    generate_cleaned_csv_content,
)
from .response_utils import create_csv_streaming_response, create_empty_csv_response
from .validation import _validate_and_get_flow, _get_data_import_for_flow

logger = logging.getLogger(__name__)


@router.get(
    "/flows/{flow_id}/data-cleansing/download/raw",
    summary="Download raw data as CSV",
)
async def download_raw_data(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Download raw imported data as CSV file.

    This endpoint exports the original raw data that was imported into the system
    before any data cleansing operations were performed.
    """
    try:
        logger.info(f"📥 Downloading raw data for flow {flow_id}")

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Get data import for this flow
        data_import = await _get_data_import_for_flow(flow_id, flow, db)

        if not data_import:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "failed",
                    "error_code": "DATA_IMPORT_NOT_FOUND",
                    "details": {
                        "flow_id": flow_id,
                        "message": "No data import found for flow",
                    },
                },
            )

        # Query raw import records with configurable limit
        raw_records_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == data_import.id)
            .limit(settings.MAX_EXPORT_RECORDS)
        )  # Configurable limit for security and performance

        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()

        if not raw_records:
            # Return empty CSV file instead of error to allow graceful download
            logger.warning(f"No raw data found for flow {flow_id}, returning empty CSV")
            return create_empty_csv_response(flow_id, "raw")

        # Create CSV content with error handling
        try:
            csv_content, pii_redacted_count = generate_raw_csv_content(raw_records)
        except Exception as csv_error:
            logger.error(f"Failed to generate CSV content: {csv_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "failed",
                    "error_code": "CSV_GENERATION_FAILED",
                    "details": {
                        "flow_id": flow_id,
                        "message": "Failed to generate CSV content",
                        "error": str(csv_error),
                    },
                },
            )

        # Generate filename with timestamp
        filename = generate_filename(flow_id, "raw")

        # Calculate file size for audit logging
        file_size_bytes = len(csv_content.encode("utf-8"))

        # Log data export for security audit trail
        await log_raw_data_export_audit(
            db,
            context,
            flow,
            filename,
            raw_records,
            file_size_bytes,
            pii_redacted_count,
            data_import,
        )

        logger.info(
            f"✅ Generated raw data CSV for flow {flow_id}: {len(raw_records)} records, {file_size_bytes} bytes"
        )

        logger.info(f"📊 Returning raw CSV response: {file_size_bytes} bytes")

        # Return CSV as streaming response
        return create_csv_streaming_response(csv_content, filename)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download raw data for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "failed",
                "error_code": "RAW_DATA_EXPORT_FAILED",
                "details": {
                    "flow_id": flow_id,
                    "message": "Failed to download raw data",
                    "error": str(e),
                },
            },
        )


@router.get(
    "/flows/{flow_id}/data-cleansing/download/cleaned",
    summary="Download cleaned data as CSV",
)
async def download_cleaned_data(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Download cleaned and processed data as CSV file.

    This endpoint exports the data after it has been processed through
    the data cleansing pipeline, with quality issues resolved and
    transformations applied.
    """
    try:
        logger.info(f"📥 Downloading cleaned data for flow {flow_id}")

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Get data import for this flow
        data_import = await _get_data_import_for_flow(flow_id, flow, db)

        if not data_import:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "failed",
                    "error_code": "DATA_IMPORT_NOT_FOUND",
                    "details": {
                        "flow_id": flow_id,
                        "message": "No data import found for flow",
                    },
                },
            )

        # Query raw import records (for now, as cleaned data structure isn't fully implemented)
        # TODO: Replace with actual cleaned data when data cleansing pipeline is complete
        raw_records_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == data_import.id)
            .limit(settings.MAX_EXPORT_RECORDS)
        )  # Configurable limit for security and performance

        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()

        if not raw_records:
            # Return empty CSV file instead of error to allow graceful download
            logger.warning(
                f"No cleaned data found for flow {flow_id}, returning empty CSV"
            )
            return create_empty_csv_response(flow_id, "cleaned")

        # Get field mappings to understand data transformations
        field_mapping_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == data_import.id
        )
        field_mapping_result = await db.execute(field_mapping_query)
        field_mappings = field_mapping_result.scalars().all()

        # Create a mapping of source fields to target fields
        field_mapping_dict = {
            mapping.source_field: mapping.target_field for mapping in field_mappings
        }

        # Create CSV content with cleaned/mapped field names and error handling
        try:
            csv_content, pii_redacted_count = generate_cleaned_csv_content(
                raw_records, field_mapping_dict
            )
        except Exception as csv_error:
            logger.error(f"Failed to generate cleaned CSV content: {csv_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "failed",
                    "error_code": "CLEANED_CSV_GENERATION_FAILED",
                    "details": {
                        "flow_id": flow_id,
                        "message": "Failed to generate cleaned CSV content",
                        "error": str(csv_error),
                    },
                },
            )

        # Generate filename with timestamp
        filename = generate_filename(flow_id, "cleaned")

        # Calculate file size for audit logging
        file_size_bytes = len(csv_content.encode("utf-8"))

        # Log data export for security audit trail
        await log_cleaned_data_export_audit(
            db,
            context,
            flow,
            filename,
            raw_records,
            field_mappings,
            file_size_bytes,
            pii_redacted_count,
            data_import,
        )

        logger.info(
            f"✅ Generated cleaned data CSV for flow {flow_id}: "
            f"{len(raw_records)} records with {len(field_mappings)} field mappings, {file_size_bytes} bytes"
        )

        logger.info(f"📊 Returning cleaned CSV response: {file_size_bytes} bytes")

        # Return CSV as streaming response
        return create_csv_streaming_response(csv_content, filename)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download cleaned data for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "failed",
                "error_code": "CLEANED_DATA_EXPORT_FAILED",
                "details": {
                    "flow_id": flow_id,
                    "message": "Failed to download cleaned data",
                    "error": str(e),
                },
            },
        )
