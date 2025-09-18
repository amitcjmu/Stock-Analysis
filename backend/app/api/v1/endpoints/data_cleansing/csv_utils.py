"""
CSV Utilities for Data Cleansing Exports
Reusable functions for CSV generation, processing, and content creation.
"""

import csv
import io
import logging
from datetime import datetime
from typing import List, Tuple

from app.core.security.pii_protection import (
    redact_record,
    PIISensitivityLevel,
)
from app.models.data_import.core import RawImportRecord

logger = logging.getLogger(__name__)


def create_empty_csv_content(flow_id: str, export_type: str = "cleaned") -> str:
    """Create empty CSV content when no data is available.

    Args:
        flow_id: The flow identifier for filename generation
        export_type: Type of export ('raw' or 'cleaned') for filename

    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["No data available"])
    output.seek(0)
    csv_content = output.getvalue()
    output.close()
    return csv_content


def determine_fieldnames(first_record_data: dict, field_mapping_dict: dict) -> list:
    """Determine CSV fieldnames based on first record and field mappings.

    Args:
        first_record_data: Data from the first record
        field_mapping_dict: Dictionary mapping source to target field names

    Returns:
        List of field names for CSV header
    """
    if first_record_data and field_mapping_dict:
        # Use mapped field names where available
        fieldnames = []
        for original_field in first_record_data.keys():
            mapped_field = field_mapping_dict.get(original_field, original_field)
            fieldnames.append(mapped_field)
        return fieldnames
    else:
        return list(first_record_data.keys()) if first_record_data else ["id", "data"]


def process_record_for_csv(
    record: RawImportRecord, field_mapping_dict: dict
) -> Tuple[dict, bool]:
    """Process a single record for CSV export with field mapping and cleaning.

    Args:
        record: Raw import record to process
        field_mapping_dict: Dictionary mapping source to target field names

    Returns:
        Tuple of (processed_row, pii_was_redacted)
    """
    if record.data and isinstance(record.data, dict):
        cleaned_row = {}
        for original_field, value in record.data.items():
            # Apply field mapping
            mapped_field = field_mapping_dict.get(original_field, original_field)

            # Apply basic data cleaning (trim whitespace, handle nulls)
            cleaned_value = value
            if isinstance(value, str):
                cleaned_value = value.strip() if value else ""
            elif value is None:
                cleaned_value = ""

            cleaned_row[mapped_field] = cleaned_value

        # Apply PII redaction for security compliance
        redacted_row = redact_record(cleaned_row, PIISensitivityLevel.RESTRICTED)
        pii_was_redacted = redacted_row != cleaned_row
        return redacted_row, pii_was_redacted
    else:
        # Fallback for non-dict data
        return {"id": record.id, "data": str(record.data or "")}, False


def generate_raw_csv_content(raw_records: List[RawImportRecord]) -> Tuple[str, int]:
    """Generate CSV content for raw data export.

    Args:
        raw_records: List of raw import records

    Returns:
        Tuple of (csv_content, pii_redacted_count)
    """
    output = io.StringIO()

    # Get field names from the first record
    first_record_data = raw_records[0].data if raw_records[0].data else {}
    fieldnames = list(first_record_data.keys()) if first_record_data else ["id", "data"]

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
                writer.writerow({"id": record.id, "data": str(record.data or "")})
        except Exception as row_error:
            logger.warning(f"Error writing record {record.id}: {row_error}")
            # Write error row instead of skipping
            writer.writerow({"id": record.id, "data": f"[ERROR: {str(row_error)}]"})

    output.seek(0)
    csv_content = output.getvalue()
    output.close()

    return csv_content, pii_redacted_count


def generate_cleaned_csv_content(
    raw_records: List[RawImportRecord], field_mapping_dict: dict
) -> Tuple[str, int]:
    """Generate CSV content with cleaned data and field mappings applied.

    Args:
        raw_records: List of raw import records
        field_mapping_dict: Dictionary mapping source to target field names

    Returns:
        Tuple of (csv_content, pii_redacted_count)
    """
    output = io.StringIO()

    # Get field names from the first record and apply field mappings
    first_record_data = raw_records[0].data if raw_records[0].data else {}
    fieldnames = determine_fieldnames(first_record_data, field_mapping_dict)

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    # Write data rows with field mapping applied and PII protection
    pii_redacted_count = 0
    for record in raw_records:
        try:
            processed_row, pii_was_redacted = process_record_for_csv(
                record, field_mapping_dict
            )
            if pii_was_redacted:
                pii_redacted_count += 1
            writer.writerow(processed_row)
        except Exception as row_error:
            logger.warning(f"Error processing record {record.id}: {row_error}")
            # Write error row instead of skipping
            writer.writerow({"id": record.id, "data": f"[ERROR: {str(row_error)}]"})

    output.seek(0)
    csv_content = output.getvalue()
    output.close()

    return csv_content, pii_redacted_count


def generate_filename(flow_id: str, export_type: str, is_empty: bool = False) -> str:
    """Generate filename for CSV export.

    Args:
        flow_id: The flow identifier
        export_type: Type of export ('raw' or 'cleaned')
        is_empty: Whether this is an empty file

    Returns:
        Generated filename string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = "_empty" if is_empty else ""
    return f"{export_type}_data_{flow_id[:8]}_{timestamp}{suffix}.csv"
