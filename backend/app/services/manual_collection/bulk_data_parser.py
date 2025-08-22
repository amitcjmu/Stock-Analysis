"""
Bulk Data Parser

Handles file parsing and format detection for bulk data uploads.
"""

import io
import json
import logging
from typing import Any, Dict, List

import pandas as pd

from .bulk_data_models import BulkDataFormat

logger = logging.getLogger(__name__)


class BulkDataParser:
    """Handles parsing of various bulk data formats."""

    def validate_file(self, file_content: bytes, filename: str) -> None:
        """Validate uploaded file"""
        if not file_content:
            raise ValueError("Empty file uploaded")

        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError("File size exceeds 50MB limit")

        # Validate file extension
        format_type = self.detect_format(filename)
        if not format_type:
            raise ValueError("Unsupported file format")

    def detect_format(self, filename: str) -> BulkDataFormat:
        """Detect file format from filename"""
        suffix = filename.lower().split(".")[-1]
        format_mapping = {
            "csv": BulkDataFormat.CSV,
            "xlsx": BulkDataFormat.EXCEL,
            "xls": BulkDataFormat.EXCEL,
            "json": BulkDataFormat.JSON,
            "tsv": BulkDataFormat.TSV,
            "txt": BulkDataFormat.TSV,
        }
        return format_mapping.get(suffix, BulkDataFormat.CSV)

    async def parse_file_content(
        self, file_content: bytes, format_type: BulkDataFormat
    ) -> List[Dict[str, Any]]:
        """Parse file content based on format"""
        try:
            if format_type == BulkDataFormat.CSV:
                return self._parse_csv(file_content)
            elif format_type == BulkDataFormat.EXCEL:
                return self._parse_excel(file_content)
            elif format_type == BulkDataFormat.JSON:
                return self._parse_json(file_content)
            elif format_type == BulkDataFormat.TSV:
                return self._parse_tsv(file_content)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise ValueError(f"Failed to parse file: {str(e)}")

    def _parse_csv(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV content"""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            return df.to_dict("records")
        except Exception as e:
            raise ValueError(f"Invalid CSV format: {str(e)}")

    def _parse_excel(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel content"""
        try:
            df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
            return df.to_dict("records")
        except Exception as e:
            raise ValueError(f"Invalid Excel format: {str(e)}")

    def _parse_json(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Parse JSON content"""
        try:
            data = json.loads(file_content.decode("utf-8"))
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError("JSON must contain object or array")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    def _parse_tsv(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Parse TSV content"""
        try:
            df = pd.read_csv(io.BytesIO(file_content), sep="\t")
            return df.to_dict("records")
        except Exception as e:
            raise ValueError(f"Invalid TSV format: {str(e)}")
