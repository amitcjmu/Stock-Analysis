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

    # Mock quality issues for demo (replace with actual data cleansing crew analysis)
    quality_issues = []
    recommendations = []
    field_quality_scores = {}

    if include_details and field_mappings:
        # Generate sample quality issues based on field mappings
        for i, mapping in enumerate(field_mappings[:5]):  # Limit to first 5 for demo
            source_field = mapping.source_field

            # Mock quality issue
            quality_issues.append(
                DataQualityIssue(
                    id=str(uuid.uuid4()),
                    field_name=source_field,
                    issue_type="missing_values",
                    severity="medium",
                    description=f"Field '{source_field}' has missing values in some records",
                    affected_records=max(1, int(total_records * 0.1)),
                    recommendation=(
                        f"Consider filling missing values for '{source_field}' with default values "
                        f"or remove incomplete records"
                    ),
                    auto_fixable=True,
                )
            )

            # Mock field quality score
            field_quality_scores[source_field] = round(85.0 + (i * 2), 1)

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
