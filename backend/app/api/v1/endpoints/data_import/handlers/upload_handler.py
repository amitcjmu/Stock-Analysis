"""
Upload handler for multi-category data imports.
"""

from __future__ import annotations

import json
from datetime import datetime
import os
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import (
    RequestContext,
    get_current_context_dependency,
)
from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.data_import_schemas import (
    FileMetadata,
    StoreImportRequest,
    UploadContext,
)
from app.services.data_import import ImportStorageHandler

logger = get_logger(__name__)

SUPPORTED_IMPORT_CATEGORIES = {
    "cmdb_export",
    "app_discovery",
    "infrastructure",
    "sensitive_data",
}


MAX_UPLOAD_SIZE_MB = 100
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
# Qodo bot: JSON parsing limits to prevent DoS
MAX_JSON_DEPTH = 100  # Maximum nesting depth for JSON structures
MAX_RECORDS = 100000  # Maximum number of records in import file

router = APIRouter()


@router.post("/upload")
async def upload_data_import(
    file: UploadFile = File(...),
    import_category: str = Form(...),
    processing_config: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Ingest a data import file and queue background processing.

    The payload is multipart/form-data with:
      - file: UploadFile
      - import_category: Upload category identifier
      - processing_config: Optional JSON object with processor configuration
    """
    normalized_category = import_category.lower()
    if normalized_category not in SUPPORTED_IMPORT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported import_category '{import_category}'. "
            f"Supported categories: {sorted(SUPPORTED_IMPORT_CATEGORIES)}",
        )

    # Enforce upload size limit before reading into memory
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(f"Uploaded file exceeds {MAX_UPLOAD_SIZE_MB}MB limit."),
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Qodo bot: Add JSON parsing limits to prevent DoS
    try:
        parsed_data = json.loads(file_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse uploaded file as JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be valid JSON representing import records.",
        ) from exc

    # Validate JSON depth to prevent deeply nested structures causing DoS
    def _check_json_depth(obj: Any, current_depth: int = 0) -> int:
        """Recursively check maximum depth of JSON structure."""
        if current_depth > MAX_JSON_DEPTH:
            raise ValueError(
                f"JSON structure exceeds maximum depth of {MAX_JSON_DEPTH} levels"
            )
        if isinstance(obj, dict):
            return max(
                (_check_json_depth(v, current_depth + 1) for v in obj.values()),
                default=current_depth,
            )
        elif isinstance(obj, list):
            return max(
                (_check_json_depth(item, current_depth + 1) for item in obj),
                default=current_depth,
            )
        return current_depth

    try:
        _check_json_depth(parsed_data)
    except ValueError as exc:
        logger.error("JSON depth validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file structure is too deeply nested. Maximum depth: {MAX_JSON_DEPTH} levels.",
        ) from exc

    try:
        records = _normalize_records(parsed_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Validate record count to prevent DoS
    if len(records) > MAX_RECORDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Uploaded file contains {len(records)} records, "
                f"which exceeds the maximum of {MAX_RECORDS} records."
            ),
        )
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No records found in uploaded file.",
        )

    try:
        config_payload = json.loads(processing_config) if processing_config else {}
        if not isinstance(config_payload, dict):
            raise ValueError("processing_config must be a JSON object.")
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="processing_config must be a valid JSON object.",
        ) from exc

    metadata = FileMetadata(
        filename=file.filename or "uploaded-data.json",
        size=len(file_bytes),
        type=file.content_type or "application/json",
    )
    upload_context = UploadContext(
        intended_type=normalized_category,
        upload_timestamp=datetime.utcnow().isoformat(),
    )

    store_request = StoreImportRequest(
        file_data=records,
        metadata=metadata,
        upload_context=upload_context,
        client_id=context.client_account_id,
        engagement_id=context.engagement_id,
        import_category=normalized_category,
        processing_config=config_payload,
    )

    handler = ImportStorageHandler(db, context.client_account_id)
    response = await handler.handle_import(store_request, context)

    # Qodo bot: Add audit logging for file upload (required for compliance)
    data_import_id = response.get("data_import_id", "unknown")
    try:
        from app.models.rbac.audit_models import AccessAuditLog

        audit_log = AccessAuditLog(
            user_id=context.user_id,
            action_type="data_import_upload",
            resource_type="data_import",
            resource_id=str(data_import_id),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            result="success" if response.get("success") else "failure",
            reason=(
                f"Data import upload: {len(records)} records, category={normalized_category}, "
                f"filename={metadata.filename}, size={metadata.size} bytes"
            ),
            details={
                "import_category": normalized_category,
                "record_count": len(records),
                "filename": metadata.filename,
                "file_size_bytes": metadata.size,
                "master_flow_id": response.get("flow_id"),
            },
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        db.add(audit_log)
        await db.commit()
        logger.info(
            f"✅ Audit log created for data import upload: "
            f"{len(records)} records, category={normalized_category}"
        )
    except Exception as e:
        logger.warning(
            f"⚠️ Failed to log data import upload audit: {str(e)}. "
            "Upload will continue without audit log."
        )
        # Don't raise - audit logging should not break the upload flow

    if not response.get("success"):
        error_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_payload: Any = response.get("message", "Failed to process import.")
        if response.get("error") == "conflict":
            error_code = status.HTTP_409_CONFLICT
            response_payload = response

        # Log audit for failed upload
        try:
            from app.models.rbac.audit_models import AccessAuditLog

            audit_log = AccessAuditLog(
                user_id=context.user_id,
                action_type="data_import_upload",
                resource_type="data_import",
                resource_id=str(data_import_id),
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                result="failure",
                reason=f"Data import upload failed: {response.get('error', 'unknown error')}",
                details={
                    "import_category": normalized_category,
                    "error_type": response.get("error"),
                    "filename": metadata.filename,
                },
                ip_address=context.ip_address,
                user_agent=context.user_agent,
            )
            db.add(audit_log)
            await db.commit()
        except Exception:
            pass  # Best effort audit logging

        raise HTTPException(
            status_code=error_code,
            detail=response_payload,
        )

    return {
        "data_import_id": response.get("data_import_id"),
        "master_flow_id": response.get("flow_id"),
        "records_stored": response.get("records_stored"),
        "status": "queued",
        "message": "Import stored and background processing started.",
        "import_category": normalized_category,
        "processing_config": config_payload,
    }


def _normalize_records(payload: Any) -> List[Dict[str, Any]]:
    """
    Normalize uploaded payload into a list of dictionaries.
    """

    def _to_dict_list(items: List[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Invalid record at index {idx}: each entry must be a JSON object."
                )
            normalized.append(dict(item))
        return normalized

    if isinstance(payload, list):
        return _to_dict_list(payload)

    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], list):
            return _to_dict_list(payload["data"])
        return [payload]

    raise ValueError("Payload must be a JSON object or a list of JSON objects.")
