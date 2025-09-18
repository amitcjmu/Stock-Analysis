"""
Data Cleansing API Module
Modularized data cleansing endpoints with backward compatibility.

This module preserves the public API of the original data_cleansing.py file
while organizing the code into logical modules for better maintainability.
"""

# Import the router from base module
from .base import router

# Import all public functions and classes to maintain backward compatibility
from .base import (
    TriggerDataCleansingRequest,
    DataQualityIssue,
    DataCleansingRecommendation,
    DataCleansingAnalysis,
    DataCleansingStats,
)

from .operations import (
    get_data_cleansing_analysis,
    get_data_cleansing_stats,
)

from .triggers import (
    trigger_data_cleansing_analysis,
)

from .exports import (
    download_raw_data,
    download_cleaned_data,
)

# Import utilities for potential external use
from .csv_utils import (
    create_empty_csv_content,
    determine_fieldnames,
    process_record_for_csv,
    generate_raw_csv_content,
    generate_cleaned_csv_content,
    generate_filename,
)

from .response_utils import (
    create_csv_streaming_response,
    create_empty_csv_response,
)

from .audit_utils import (
    log_raw_data_export_audit,
    log_cleaned_data_export_audit,
)

from .validation import (
    _validate_and_get_flow,
    _get_data_import_for_flow,
)

from .analysis import (
    _perform_data_cleansing_analysis,
)

# Define public API for export
__all__ = [
    "router",
    "TriggerDataCleansingRequest",
    "DataQualityIssue",
    "DataCleansingRecommendation",
    "DataCleansingAnalysis",
    "DataCleansingStats",
    "get_data_cleansing_analysis",
    "get_data_cleansing_stats",
    "trigger_data_cleansing_analysis",
    "download_raw_data",
    "download_cleaned_data",
    "_perform_data_cleansing_analysis",
    "_validate_and_get_flow",
    "_get_data_import_for_flow",
    # CSV utilities
    "create_empty_csv_content",
    "determine_fieldnames",
    "process_record_for_csv",
    "generate_raw_csv_content",
    "generate_cleaned_csv_content",
    "generate_filename",
    # Response utilities
    "create_csv_streaming_response",
    "create_empty_csv_response",
    # Audit utilities
    "log_raw_data_export_audit",
    "log_cleaned_data_export_audit",
]
