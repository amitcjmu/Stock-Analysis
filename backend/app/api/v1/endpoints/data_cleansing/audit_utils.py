"""
Audit Logging Utilities for Data Cleansing Exports
Functions for logging data export activities for security audit trails.
"""

import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import RequestContext
from app.services.collection_flow.audit_logging.logger import AuditLoggingService

logger = logging.getLogger(__name__)


async def log_raw_data_export_audit(
    db: AsyncSession,
    context: RequestContext,
    flow,
    filename: str,
    raw_records: List,
    file_size_bytes: int,
    pii_redacted_count: int,
    data_import,
) -> None:
    """Log raw data export for security audit trail.

    Args:
        db: Database session
        context: Request context with tenant information
        flow: The discovery flow object
        filename: Name of the exported file
        raw_records: List of raw records exported
        file_size_bytes: Size of the exported file in bytes
        pii_redacted_count: Number of records that had PII redacted
        data_import: The data import object
    """
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
        logger.warning(f"Failed to log raw data export audit: {e}")
        # Don't fail the export if audit logging fails


async def log_cleaned_data_export_audit(
    db: AsyncSession,
    context: RequestContext,
    flow,
    filename: str,
    raw_records: List,
    field_mappings: List,
    file_size_bytes: int,
    pii_redacted_count: int,
    data_import,
) -> None:
    """Log cleaned data export for security audit trail.

    Args:
        db: Database session
        context: Request context with tenant information
        flow: The discovery flow object
        filename: Name of the exported file
        raw_records: List of raw records exported
        field_mappings: List of field mappings applied
        file_size_bytes: Size of the exported file in bytes
        pii_redacted_count: Number of records that had PII redacted
        data_import: The data import object
    """
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
        logger.warning(f"Failed to log cleaned data export audit: {e}")
        # Don't fail the export if audit logging fails
