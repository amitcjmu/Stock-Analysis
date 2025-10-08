"""
Flow transition threshold configurations.

This module contains configurable thresholds for flow phase transitions.
Separated from flow_configuration.py to keep files under 400 LOC limit.
"""

import logging
import os

logger = logging.getLogger(__name__)


# Field Mapping Approval Threshold Configuration
# Controls the minimum percentage of approved mappings required to transition
# from field_mapping phase to data_cleansing phase.
# Default: 60% (more reasonable than previous 80% hardcoded value)
# Can be overridden via FIELD_MAPPING_APPROVAL_THRESHOLD environment variable
# Issue: #521 - Previous 80% threshold was too strict, blocking flows with 75% approval
try:
    FIELD_MAPPING_APPROVAL_THRESHOLD = float(
        os.getenv("FIELD_MAPPING_APPROVAL_THRESHOLD", "60")
    )
except ValueError:
    logger.warning(
        "Invalid value for FIELD_MAPPING_APPROVAL_THRESHOLD. "
        "Must be a number. Falling back to default value of 60."
    )
    FIELD_MAPPING_APPROVAL_THRESHOLD = 60.0
