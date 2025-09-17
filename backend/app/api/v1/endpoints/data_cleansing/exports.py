"""
Data Cleansing API - Exports Module
Download functionality for raw and cleaned data as CSV files.
"""

import csv
import io
import logging
from datetime import datetime

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
from app.services.collection_flow.audit_logging.logger import AuditLoggingService
from app.core.security.pii_protection import (
    redact_record,
    PIISensitivityLevel,
)

from .base import router
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
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["No data available"])
            output.seek(0)
            csv_content = output.getvalue()
            output.close()

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_data_{flow_id[:8]}_{timestamp}_empty.csv"

            csv_bytes = csv_content.encode("utf-8")
            csv_stream = io.BytesIO(csv_bytes)
            csv_stream.seek(0)

            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(csv_bytes)),
                    "Cache-Control": "no-cache",
                    "Content-Type": "text/csv; charset=utf-8",
                },
            )

        # Create CSV content with error handling
        try:
            output = io.StringIO()

            # Get field names from the first record
            first_record_data = raw_records[0].data if raw_records[0].data else {}
            fieldnames = (
                list(first_record_data.keys()) if first_record_data else ["id", "data"]
            )

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            # Write data rows with PII protection
            pii_redacted_count = 0
            for record in raw_records:
                try:
                    if record.data and isinstance(record.data, dict):
                        # Apply PII redaction for security compliance
                        redacted_data = redact_record(
                            record.data, PIISensitivityLevel.RESTRICTED
                        )
                        if redacted_data != record.data:
                            pii_redacted_count += 1
                        writer.writerow(redacted_data)
                    else:
                        # Fallback for non-dict data
                        writer.writerow(
                            {"id": record.id, "data": str(record.data or "")}
                        )
                except Exception as row_error:
                    logger.warning(f"Error writing record {record.id}: {row_error}")
                    # Write error row instead of skipping
                    writer.writerow(
                        {"id": record.id, "data": f"[ERROR: {str(row_error)}]"}
                    )

            output.seek(0)
            csv_content = output.getvalue()
            output.close()

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
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_data_{flow_id[:8]}_{timestamp}.csv"

        # Calculate file size for audit logging
        file_size_bytes = len(csv_content.encode("utf-8"))

        # Log data export for security audit trail
        try:
            audit_service = AuditLoggingService(db, context)
            await audit_service.log_data_export(
                flow_id=flow.flow_id,
                export_type="raw",
                record_count=len(raw_records),
                file_size_bytes=file_size_bytes,
                details={
                    "filename": filename,
                    "user_ip": context.ip_address,
                    "user_agent": context.user_agent,
                    "data_import_id": str(data_import.id),
                    "pii_redacted_records": pii_redacted_count,
                    "pii_protection_enabled": settings.ENABLE_PII_REDACTION,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log data export audit: {e}")
            # Don't fail the export if audit logging fails

        logger.info(
            f"✅ Generated raw data CSV for flow {flow_id}: {len(raw_records)} records, {file_size_bytes} bytes"
        )

        # Create CSV stream response with proper headers
        csv_bytes = csv_content.encode("utf-8")
        csv_stream = io.BytesIO(csv_bytes)

        # Ensure we start reading from the beginning
        csv_stream.seek(0)

        logger.info(f"📊 Returning raw CSV response: {len(csv_bytes)} bytes")

        # Return CSV as streaming response with additional headers for better browser compatibility
        return StreamingResponse(
            csv_stream,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(csv_bytes)),
                "Cache-Control": "no-cache",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

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
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["No data available"])
            output.seek(0)
            csv_content = output.getvalue()
            output.close()

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"cleaned_data_{flow_id[:8]}_{timestamp}_empty.csv"

            csv_bytes = csv_content.encode("utf-8")
            csv_stream = io.BytesIO(csv_bytes)
            csv_stream.seek(0)

            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(csv_bytes)),
                    "Cache-Control": "no-cache",
                    "Content-Type": "text/csv; charset=utf-8",
                },
            )

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
            output = io.StringIO()

            # Get field names from the first record and apply field mappings
            first_record_data = raw_records[0].data if raw_records[0].data else {}
            if first_record_data and field_mapping_dict:
                # Use mapped field names where available
                fieldnames = []
                for original_field in first_record_data.keys():
                    mapped_field = field_mapping_dict.get(
                        original_field, original_field
                    )
                    fieldnames.append(mapped_field)
            else:
                fieldnames = (
                    list(first_record_data.keys())
                    if first_record_data
                    else ["id", "data"]
                )

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            # Write data rows with field mapping applied and PII protection
            pii_redacted_count = 0
            for record in raw_records:
                try:
                    if record.data and isinstance(record.data, dict):
                        cleaned_row = {}
                        for original_field, value in record.data.items():
                            # Apply field mapping
                            mapped_field = field_mapping_dict.get(
                                original_field, original_field
                            )

                            # Apply basic data cleaning (trim whitespace, handle nulls)
                            cleaned_value = value
                            if isinstance(value, str):
                                cleaned_value = value.strip() if value else ""
                            elif value is None:
                                cleaned_value = ""

                            cleaned_row[mapped_field] = cleaned_value

                        # Apply PII redaction for security compliance
                        redacted_row = redact_record(
                            cleaned_row, PIISensitivityLevel.RESTRICTED
                        )
                        if redacted_row != cleaned_row:
                            pii_redacted_count += 1
                        writer.writerow(redacted_row)
                    else:
                        # Fallback for non-dict data
                        writer.writerow(
                            {"id": record.id, "data": str(record.data or "")}
                        )
                except Exception as row_error:
                    logger.warning(f"Error processing record {record.id}: {row_error}")
                    # Write error row instead of skipping
                    writer.writerow(
                        {"id": record.id, "data": f"[ERROR: {str(row_error)}]"}
                    )

            output.seek(0)
            csv_content = output.getvalue()
            output.close()

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
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"cleaned_data_{flow_id[:8]}_{timestamp}.csv"

        # Calculate file size for audit logging
        file_size_bytes = len(csv_content.encode("utf-8"))

        # Log data export for security audit trail
        try:
            audit_service = AuditLoggingService(db, context)
            await audit_service.log_data_export(
                flow_id=flow.flow_id,
                export_type="cleaned",
                record_count=len(raw_records),
                file_size_bytes=file_size_bytes,
                details={
                    "filename": filename,
                    "user_ip": context.ip_address,
                    "user_agent": context.user_agent,
                    "data_import_id": str(data_import.id),
                    "field_mappings_count": len(field_mappings),
                    "pii_redacted_records": pii_redacted_count,
                    "pii_protection_enabled": settings.ENABLE_PII_REDACTION,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log data export audit: {e}")
            # Don't fail the export if audit logging fails

        logger.info(
            f"✅ Generated cleaned data CSV for flow {flow_id}: "
            f"{len(raw_records)} records with {len(field_mappings)} field mappings, {file_size_bytes} bytes"
        )

        # Create CSV stream response with proper headers
        csv_bytes = csv_content.encode("utf-8")
        csv_stream = io.BytesIO(csv_bytes)

        # Ensure we start reading from the beginning
        csv_stream.seek(0)

        logger.info(f"📊 Returning cleaned CSV response: {len(csv_bytes)} bytes")

        # Return CSV as streaming response with additional headers for better browser compatibility
        return StreamingResponse(
            csv_stream,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(csv_bytes)),
                "Cache-Control": "no-cache",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

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
