"""
JSON serialization utilities for the discovery module.
Handles conversion of pandas/numpy data types to JSON-serializable types.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List

def clean_for_json_serialization(data: Any) -> Any:
    """Convert pandas/numpy data types to JSON-serializable types."""
    if isinstance(data, dict):
        return {k: clean_for_json_serialization(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_for_json_serialization(item) for item in data]
    elif isinstance(data, (pd.Timestamp, pd.DatetimeIndex)):
        return str(data)
    elif isinstance(data, (np.integer, np.int64, np.int32, int)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, float)):
        if isinstance(data, (np.floating, np.float64, np.float32)):
            if np.isnan(data) or np.isinf(data):
                return None
        return float(data)
    elif isinstance(data, (np.bool_, bool)):
        return bool(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    elif hasattr(data, 'item'):  # numpy scalars
        try:
            return data.item()
        except (AttributeError, ValueError):
            return str(data)
    else:
        return data

def ensure_json_serializable(value: Any) -> Any:
    """Ensure a value is JSON serializable."""
    if isinstance(value, dict):
        return {k: ensure_json_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [ensure_json_serializable(item) for item in value]
    elif isinstance(value, (str, int, float, bool)) or value is None:
        return value
    elif pd.isna(value):
        return None
    elif hasattr(value, 'item'):
        try:
            return value.item()
        except (AttributeError, ValueError):
            return str(value)
    else:
        return str(value) 