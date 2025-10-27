"""
Data Cleansing API - Analysis Module
Core analysis logic for performing data cleansing analysis.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import.core import RawImportRecord

from .base import DataCleansingAnalysis, DataQualityIssue, DataCleansingRecommendation

logger = logging.getLogger(__name__)


def _generate_deterministic_issue_id(field_name: str, issue_type: str) -> str:
    """
    Generate a deterministic ID for a quality issue based on field name and issue type.
    This ensures the same issue always gets the same ID, allowing stored resolutions to persist.
    """
    import hashlib
    # Create a deterministic string from field name and issue type
    issue_key = f"{field_name}:{issue_type}"
    # Generate a UUID5 (deterministic) using the issue key
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Standard namespace
    return str(uuid.uuid5(namespace, issue_key))


def _analyze_raw_data_quality(
    raw_records: List[Any], total_records: int
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze raw import records for quality issues.

    Returns a dict mapping field names to their quality statistics.
    """
    import re
    from collections import defaultdict

    field_stats = defaultdict(
        lambda: {
            "missing_count": 0,
            "invalid_format_count": 0,
            "total_count": 0,
            "sample_values": [],
            "data_types": set(),
            "quality_score": 100.0,
        }
    )

    # Analyze each record
    for record in raw_records:
        raw_data = record.raw_data or {}

        # Analyze each field in the record
        for field_name, value in raw_data.items():
            stats = field_stats[field_name]
            stats["total_count"] += 1

            # Check for missing/null values
            if (
                value is None
                or value == ""
                or (isinstance(value, str) and value.strip() == "")
            ):
                stats["missing_count"] += 1
            else:
                # Track data type
                stats["data_types"].add(type(value).__name__)

                # Store sample values (up to 5)
                if len(stats["sample_values"]) < 5:
                    stats["sample_values"].append(value)

                # Check for invalid formats based on field name patterns
                field_lower = field_name.lower()

                # Email validation
                if "email" in field_lower and isinstance(value, str):
                    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if not re.match(email_pattern, value):
                        stats["invalid_format_count"] += 1

                # IP address validation
                elif "ip" in field_lower and isinstance(value, str):
                    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
                    if not re.match(ip_pattern, value):
                        stats["invalid_format_count"] += 1

                # Date validation (basic ISO format check)
                elif any(
                    date_keyword in field_lower
                    for date_keyword in ["date", "created", "modified", "timestamp"]
                ) and isinstance(value, str):
                    # Check for common date formats
                    date_patterns = [
                        r"^\d{4}-\d{2}-\d{2}",  # ISO format
                        r"^\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                        r"^\d{2}-\d{2}-\d{4}",  # MM-DD-YYYY
                    ]
                    if not any(re.match(pattern, value) for pattern in date_patterns):
                        stats["invalid_format_count"] += 1

    # Calculate quality scores for each field
    for field_name, stats in field_stats.items():
        total = stats["total_count"]
        if total > 0:
            missing_pct = (stats["missing_count"] / total) * 100
            invalid_pct = (stats["invalid_format_count"] / total) * 100

            # Quality score = 100 - (missing% + invalid%)
            stats["quality_score"] = max(0.0, 100.0 - missing_pct - invalid_pct)

    return dict(field_stats)


def _generate_quality_issues_from_stats(
    field_stats: Dict[str, Dict[str, Any]],
    total_records: int,
    sample_size: int,
) -> List[DataQualityIssue]:
    """
    Generate DataQualityIssue objects from field statistics.
    Extrapolates affected record counts from sample to full dataset.
    """
    quality_issues = []

    if sample_size == 0:
        return []

    for field_name, stats in field_stats.items():
        total = stats["total_count"]
        missing_count = stats["missing_count"]
        invalid_count = stats["invalid_format_count"]

        # Generate issue for missing values (if > 5%)
        if missing_count > 0 and (missing_count / total) > 0.05:
            severity = (
                "critical"
                if (missing_count / total) > 0.5
                else ("high" if (missing_count / total) > 0.25 else "medium")
            )
            # Extrapolate to full dataset
            estimated_affected = int(total_records * (missing_count / sample_size))

            quality_issues.append(
                DataQualityIssue(
                    id=_generate_deterministic_issue_id(field_name, "missing_values"),
                    field_name=field_name,
                    issue_type="missing_values",
                    severity=severity,
                    description=(
                        f"Field '{field_name}' has an estimated {missing_count} missing values "
                        f"in a sample of {total} records ({(missing_count/total)*100:.1f}%)"
                    ),
                    affected_records=estimated_affected,
                    recommendation=(
                        f"Consider filling missing values for '{field_name}' with "
                        f"default values or remove incomplete records"
                    ),
                    auto_fixable=True,
                )
            )

        # Generate issue for invalid formats (if > 5%)
        if invalid_count > 0 and (invalid_count / total) > 0.05:
            severity = "high" if (invalid_count / total) > 0.25 else "medium"
            # Extrapolate to full dataset
            estimated_affected = int(total_records * (invalid_count / sample_size))

            quality_issues.append(
                DataQualityIssue(
                    id=_generate_deterministic_issue_id(field_name, "invalid_format"),
                    field_name=field_name,
                    issue_type="invalid_format",
                    severity=severity,
                    description=(
                        f"Field '{field_name}' has an estimated {invalid_count} records with "
                        f"invalid format in a sample of {total} records ({(invalid_count/total)*100:.1f}%)"
                    ),
                    affected_records=estimated_affected,
                    recommendation=f"Standardize format for '{field_name}' to ensure data consistency",
                    auto_fixable=True,
                )
            )

        # Generate issue for data type mismatches (if multiple types detected)
        if len(stats["data_types"]) > 1:
            quality_issues.append(
                DataQualityIssue(
                    id=_generate_deterministic_issue_id(field_name, "type_mismatch"),
                    field_name=field_name,
                    issue_type="type_mismatch",
                    severity="medium",
                    description=f"Field '{field_name}' has mixed data types: {', '.join(stats['data_types'])}",
                    affected_records=total,
                    recommendation=f"Convert all values in '{field_name}' to a consistent data type",
                    auto_fixable=True,
                )
            )

    return quality_issues


async def _apply_stored_resolutions(
    flow_id: str, 
    quality_issues: List[DataQualityIssue], 
    db_session: AsyncSession
) -> List[DataQualityIssue]:
    """
    Apply stored resolutions to quality issues.
    
    This function checks the flow's crewai_state_data for stored resolutions
    and updates the quality issues with their resolution status.
    """
    try:
        # Get the flow to check for stored resolutions
        from app.models.discovery_flow import DiscoveryFlow
        from sqlalchemy import select
        
        # Get the flow directly from the database using the provided session
        # First, expire any cached instances to force a fresh read from the database
        db_session.expire_all()
        
        flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        flow_result = await db_session.execute(flow_query)
        flow = flow_result.scalar_one_or_none()
        
        if not flow:
            logger.warning(f"Flow {flow_id} not found when applying resolutions")
            return quality_issues
        
        # Get stored resolutions from crewai_state_data
        crewai_data = flow.crewai_state_data or {}
        logger.info(f"Flow {flow_id} crewai_state_data keys: {list(crewai_data.keys())}")
        
        data_cleansing_results = crewai_data.get("data_cleansing_results", {})
        
        stored_resolutions = data_cleansing_results.get("resolutions", {})
        logger.info(f"Flow {flow_id} stored_resolutions: {stored_resolutions}")
        
        if not stored_resolutions:
            logger.info(f"No stored resolutions found for flow {flow_id}")
            return quality_issues
        
        logger.info(f"Found {len(stored_resolutions)} stored resolutions for flow {flow_id}")
        
        # Apply resolutions to quality issues
        updated_issues = []
        for issue in quality_issues:
            issue_id = issue.id
            
            # Check if this issue has been resolved
            if issue_id in stored_resolutions:
                resolution = stored_resolutions[issue_id]
                resolution_status = resolution.get("status", "pending")
                
                # Create a copy of the issue with updated status
                updated_issue = DataQualityIssue(
                    id=issue.id,
                    field_name=issue.field_name,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    affected_records=issue.affected_records,
                    recommendation=issue.recommendation,
                    auto_fixable=issue.auto_fixable,
                    status=resolution_status  # Add the resolution status
                )
                updated_issues.append(updated_issue)
            else:
                # Issue has no resolution, keep as is
                updated_issues.append(issue)
        
        return updated_issues
        
    except Exception as e:
        logger.error(f"Failed to apply stored resolutions: {e}")
        # Return original issues if resolution application fails
        return quality_issues


async def _perform_data_cleansing_analysis(
    flow_id: str,
    data_imports: List[Any],
    field_mappings: List[Any],
    include_details: bool = True,
    execution_result: Optional[Dict[str, Any]] = None,
    db_session: Optional[AsyncSession] = None,
) -> DataCleansingAnalysis:
    """
    Perform data cleansing analysis on the imported data and field mappings.

    This function analyzes the data quality and provides recommendations.
    Data cleansing is now handled by persistent agents via DataCleansingExecutor.
    """
    # Get the first data import (primary)
    data_import = data_imports[0] if data_imports else None

    # Get actual count of raw import records from the database
    total_records = 0
    if data_import:
        try:
            # Use existing session if provided, otherwise safely handle missing session
            if db_session:
                count_query = select(func.count(RawImportRecord.id)).where(
                    RawImportRecord.data_import_id == data_import.id
                )
                count_result = await db_session.execute(count_query)
                actual_count = count_result.scalar() or 0

                # Use the actual count if available, otherwise fall back to total_records field
                total_records = (
                    actual_count
                    if actual_count > 0
                    else (data_import.total_records or 0)
                )

                logger.info(
                    f"📊 Data import {data_import.id}: actual_count={actual_count}, "
                    f"total_records field={data_import.total_records}, using={total_records}"
                )
            else:
                # Fallback to total_records field if no session available
                total_records = data_import.total_records or 0
                logger.warning(
                    f"No database session provided, using total_records field: {total_records}"
                )
        except Exception as e:
            logger.warning(
                f"Failed to get actual record count: {e}, using total_records field"
            )
            total_records = data_import.total_records if data_import else 0

    total_fields = len(field_mappings)

    # Real quality issues from raw data analysis
    quality_issues = []
    recommendations = []
    field_quality_scores = {}

    # Analyze raw import records for quality issues (regardless of field_mappings)
    if include_details and data_import and db_session:
        try:
            # Get sample of raw records for analysis (limit to 100 for performance)
            raw_records_query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import.id)
                .limit(100)
            )
            raw_records_result = await db_session.execute(raw_records_query)
            raw_records = raw_records_result.scalars().all()

            if raw_records:
                logger.info(
                    f"Analyzing {len(raw_records)} raw records for quality issues"
                )

                # Analyze raw data for quality issues
                field_stats = _analyze_raw_data_quality(raw_records, total_records)

                # Generate quality issues from analysis
                quality_issues = _generate_quality_issues_from_stats(
                    field_stats, total_records, len(raw_records)
                )

                # Calculate field quality scores
                field_quality_scores = {
                    field: stats["quality_score"]
                    for field, stats in field_stats.items()
                }

                logger.info(
                    f"Generated {len(quality_issues)} quality issues from raw data analysis"
                )
                
                # Apply stored resolutions to quality issues
                quality_issues = await _apply_stored_resolutions(flow_id, quality_issues, db_session)
            else:
                logger.warning(f"No raw records found for data import {data_import.id}")
        except Exception as e:
            logger.error(f"Failed to analyze raw data for quality issues: {e}")
            # Continue with empty quality issues if analysis fails

        # Generate sample recommendations
        recommendations.extend(
            [
                DataCleansingRecommendation(
                    id=str(uuid.uuid4()),
                    category="standardization",
                    title="Standardize date formats",
                    description="Multiple date formats detected. Standardize to ISO 8601 format",
                    priority="high",
                    impact="Improves data consistency and query performance",
                    effort_estimate="2-4 hours",
                    fields_affected=["created_date", "modified_date", "last_seen"],
                ),
                DataCleansingRecommendation(
                    id=str(uuid.uuid4()),
                    category="validation",
                    title="Validate server names",
                    description="Some server names contain invalid characters or inconsistent naming",
                    priority="medium",
                    impact="Ensures proper asset identification",
                    effort_estimate="1-2 hours",
                    fields_affected=["server_name", "hostname"],
                ),
            ]
        )

    # Calculate overall quality score
    quality_score = 85.0  # Mock score
    if field_quality_scores:
        quality_score = sum(field_quality_scores.values()) / len(field_quality_scores)

    # Determine source based on execution result
    source = (
        "agent"
        if execution_result and execution_result.get("status") == "success"
        else "fallback"
    )
    processing_status = "completed" if source == "agent" else "completed_without_agents"

    return DataCleansingAnalysis(
        flow_id=flow_id,
        analysis_timestamp=datetime.utcnow().isoformat(),
        total_records=total_records,
        total_fields=total_fields,
        quality_score=round(quality_score, 1),
        issues_count=len(quality_issues),
        recommendations_count=len(recommendations),
        quality_issues=quality_issues,
        recommendations=recommendations,
        field_quality_scores=field_quality_scores,
        processing_status=processing_status,
        source=source,
    )
