"""
File parsers for CSV and JSON imports.
"""

import csv
import json
import logging
from io import StringIO
from typing import Any, Dict, List

from fastapi import UploadFile

logger = logging.getLogger(__name__)


async def parse_csv(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse CSV file to list of dictionaries."""
    try:
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(StringIO(text))
        return list(reader)
    except Exception as e:
        logger.error(f"❌ Failed to parse CSV: {e}")
        raise ValueError(f"Invalid CSV file: {e}")


async def parse_json(file: UploadFile) -> List[Dict[str, Any]]:
    """Parse JSON file to list of dictionaries."""
    try:
        content = await file.read()
        data = json.loads(content)

        # Handle both array and single object
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("JSON must be an array or object")

    except Exception as e:
        logger.error(f"❌ Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON file: {e}")
