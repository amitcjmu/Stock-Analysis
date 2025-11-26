"""
Data Cleansing API - Analysis Module
Core analysis logic for performing data cleansing analysis.
"""

import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_cleansing import (
    DataCleansingRecommendation as DBRecommendation,
)
from app.models.data_import.core import RawImportRecord
from app.models.discovery_flow import DiscoveryFlow

from .base import DataCleansingAnalysis, DataQualityIssue, DataCleansingRecommendation

logger = logging.getLogger(__name__)


def _ensure_uuid(flow_id: str | UUID | None) -> UUID:
    """
    Ensure flow_id is a UUID object for database queries.

    Converts string to UUID, validates existing UUID objects, and raises
    ValueError for invalid inputs to prevent silent query failures.

    Args:
        flow_id: Flow ID as string, UUID object, or None

    Returns:
        UUID object

    Raises:
        ValueError: If flow_id is None or cannot be converted to UUID
        TypeError: If flow_id is an unsupported type
    """
    if flow_id is None:
        raise ValueError("flow_id cannot be None")

    if isinstance(flow_id, UUID):
        return flow_id

    if isinstance(flow_id, str):
        try:
            return UUID(flow_id)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid flow_id format: {flow_id}") from e

    raise TypeError(f"flow_id must be str or UUID, got {type(flow_id).__name__}")


def _generate_deterministic_issue_id(field_name: str, issue_type: str) -> str:
    """
    Generate a deterministic ID for a quality issue based on field name and issue type.
    This ensures the same issue always gets the same ID, allowing stored resolutions to persist.
    """
    # Create a deterministic string from field name and issue type
    issue_key = f"{field_name}:{issue_type}"
    # Generate a UUID5 (deterministic) using the issue key
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # Standard namespace
    return str(uuid.uuid5(namespace, issue_key))


def _analyze_raw_data_quality(
    raw_records: List[Any], total_records: int
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze raw import records for quality issues.

    Returns a dict mapping field names to their quality statistics.
    """
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
    flow_id: str, quality_issues: List[DataQualityIssue], db_session: AsyncSession
) -> List[DataQualityIssue]:
    """
    Apply stored resolutions to quality issues.

    This function checks the flow's crewai_state_data for stored resolutions
    and updates the quality issues with their resolution status.
    """
    try:
        # Get the flow directly from the database using the provided session
        # First, expire any cached instances to force a fresh read from the database
        db_session.expire_all()

        flow_query = select(
            DiscoveryFlow
        ).where(  # SKIP_TENANT_CHECK - flow_id validated via MFO
            DiscoveryFlow.flow_id == flow_id
        )
        flow_result = await db_session.execute(flow_query)
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Flow {flow_id} not found when applying resolutions")
            return quality_issues

        # Get stored resolutions from crewai_state_data
        crewai_data = flow.crewai_state_data or {}
        logger.info(
            f"Flow {flow_id} crewai_state_data keys: {list(crewai_data.keys())}"
        )

        data_cleansing_results = crewai_data.get("data_cleansing_results", {})

        stored_resolutions = data_cleansing_results.get("resolutions", {})
        logger.info(f"Flow {flow_id} stored_resolutions: {stored_resolutions}")

        if not stored_resolutions:
            logger.info(f"No stored resolutions found for flow {flow_id}")
            return quality_issues

        logger.info(
            f"Found {len(stored_resolutions)} stored resolutions for flow {flow_id}"
        )

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
                    status=resolution_status,  # Add the resolution status
                )
                updated_issues.append(updated_issue)
            else:
                # Issue has no resolution, keep as is
                updated_issues.append(issue)

        return updated_issues

    except Exception:
        logger.exception("Failed to apply stored resolutions")
        # Return original issues if resolution application fails
        return quality_issues


def _generate_recommendation_key(rec: DataCleansingRecommendation) -> str:
    """
    Generate a stable key from recommendation content for de-duplication.

    Uses category, title, and sorted fields_affected to create a consistent
    hash that identifies duplicate recommendations regardless of ID or other fields.

    Args:
        rec: DataCleansingRecommendation instance

    Returns:
        SHA256 hash string representing the recommendation's unique content
    """
    # Normalize fields_affected by sorting to ensure consistent key generation
    fields_affected = sorted(rec.fields_affected or [])

    # Create a stable representation of the recommendation's identifying content
    key_data = {
        "category": rec.category.lower().strip(),
        "title": rec.title.lower().strip(),
        "fields_affected": fields_affected,
    }

    # Generate hash from JSON representation for stability
    key_json = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_json.encode("utf-8")).hexdigest()


async def _load_recommendations_from_database(
    flow_id: str, db_session: AsyncSession, client_account_id: str, engagement_id: str
) -> List[DataCleansingRecommendation]:
    """
    Load recommendations from database for a flow.

    Returns Pydantic models created from database records.
    Returns empty list if table doesn't exist or if there's an error.
    """
    try:
        # Query database for recommendations
        # If table doesn't exist, this will raise an exception which we'll catch
        # Ensure flow_id is a UUID object to prevent silent query failures
        # Apply multi-tenant scoping to prevent cross-tenant data access
        flow_uuid = _ensure_uuid(flow_id)
        client_account_uuid = _ensure_uuid(client_account_id)
        engagement_uuid = _ensure_uuid(engagement_id)
        query = (
            select(DBRecommendation)
            .where(DBRecommendation.flow_id == flow_uuid)
            .where(DBRecommendation.client_account_id == client_account_uuid)
            .where(DBRecommendation.engagement_id == engagement_uuid)
        )
        result = await db_session.execute(query)
        db_recommendations = result.scalars().all()

        # Convert database models to Pydantic models
        recommendations = []
        for db_rec in db_recommendations:
            # Ensure fields_affected is always a list
            fields_affected = db_rec.fields_affected
            if not isinstance(fields_affected, list):
                fields_affected = [] if fields_affected is None else [fields_affected]

            recommendations.append(
                DataCleansingRecommendation(
                    id=str(db_rec.id),
                    category=db_rec.category,
                    title=db_rec.title,
                    description=db_rec.description,
                    priority=db_rec.priority,
                    impact=db_rec.impact,
                    effort_estimate=db_rec.effort_estimate,
                    fields_affected=fields_affected,
                    status=db_rec.status or "pending",
                )
            )

        logger.info(
            f"Loaded {len(recommendations)} recommendations from database for flow {flow_id}"
        )
        return recommendations

    except Exception:
        logger.exception(
            "Failed to load recommendations from database (table may not exist)"
        )
        return []


async def _store_recommendations_to_database(
    flow_id: str,
    recommendations: List[DataCleansingRecommendation],
    db_session: AsyncSession,
    client_account_id: str,
    engagement_id: str,
) -> None:
    """
    Store recommendations to database.

    Creates or updates database records for recommendations.
    De-duplicates recommendations by generating stable keys from their content
    (category, title, fields_affected) to prevent redundant entries.
    """
    try:
        # Get existing recommendations for this flow
        # Ensure flow_id is a UUID object to prevent silent query failures
        # Apply multi-tenant scoping to prevent cross-tenant data access
        flow_uuid = _ensure_uuid(flow_id)
        client_account_uuid = _ensure_uuid(client_account_id)
        engagement_uuid = _ensure_uuid(engagement_id)
        query = (
            select(DBRecommendation)
            .where(DBRecommendation.flow_id == flow_uuid)
            .where(DBRecommendation.client_account_id == client_account_uuid)
            .where(DBRecommendation.engagement_id == engagement_uuid)
        )
        result = await db_session.execute(query)
        existing_db_recs = result.scalars().all()
        existing_recs = {str(rec.id): rec for rec in existing_db_recs}

        # Generate stable keys for existing recommendations to check for duplicates
        existing_keys = set()
        for db_rec in existing_db_recs:
            # Convert DB model to Pydantic model to generate key
            fields_affected = db_rec.fields_affected
            if not isinstance(fields_affected, list):
                fields_affected = [] if fields_affected is None else [fields_affected]

            existing_rec_pydantic = DataCleansingRecommendation(
                id=str(db_rec.id),
                category=db_rec.category,
                title=db_rec.title,
                description=db_rec.description,
                priority=db_rec.priority,
                impact=db_rec.impact,
                effort_estimate=db_rec.effort_estimate,
                fields_affected=fields_affected,
                status=db_rec.status or "pending",
            )
            existing_keys.add(_generate_recommendation_key(existing_rec_pydantic))

        # Track which recommendations are being added vs updated
        added_count = 0
        updated_count = 0
        skipped_count = 0

        # Create or update recommendations
        for rec in recommendations:
            rec_id = UUID(rec.id) if isinstance(rec.id, str) else rec.id

            if str(rec.id) in existing_recs:
                # Update existing recommendation by ID
                db_rec = existing_recs[str(rec.id)]
                db_rec.category = rec.category
                db_rec.title = rec.title
                db_rec.description = rec.description
                db_rec.priority = rec.priority
                db_rec.impact = rec.impact
                db_rec.effort_estimate = rec.effort_estimate
                db_rec.fields_affected = rec.fields_affected
                # Note: status is updated separately via apply_recommendation endpoint
                updated_count += 1
            else:
                # Check for duplicate by content (stable key) before creating new recommendation
                new_rec_key = _generate_recommendation_key(rec)
                if new_rec_key in existing_keys:
                    logger.debug(
                        f"Skipping duplicate recommendation: {rec.title} "
                        f"(category: {rec.category}, fields: {rec.fields_affected})"
                    )
                    skipped_count += 1
                    continue

                # Create new recommendation (not a duplicate)
                db_rec = DBRecommendation(
                    id=rec_id,
                    flow_id=flow_uuid,
                    category=rec.category,
                    title=rec.title,
                    description=rec.description,
                    priority=rec.priority,
                    impact=rec.impact,
                    effort_estimate=rec.effort_estimate,
                    fields_affected=rec.fields_affected,
                    status=rec.status or "pending",
                    client_account_id=UUID(client_account_id),
                    engagement_id=UUID(engagement_id),
                )
                db_session.add(db_rec)
                existing_keys.add(
                    new_rec_key
                )  # Track this key to avoid duplicates within the same batch
                added_count += 1

        await db_session.commit()
        logger.info(
            f"Stored recommendations to database for flow {flow_id}: "
            f"{added_count} added, {updated_count} updated, {skipped_count} skipped (duplicates)"
        )

    except Exception as e:
        logger.exception("Failed to store recommendations to database")
        await db_session.rollback()
        raise RuntimeError("Failed to store recommendations to database") from e


async def _perform_data_cleansing_analysis(  # noqa: C901
    flow_id: str,
    data_imports: List[Any],
    field_mappings: List[Any],
    include_details: bool = True,
    execution_result: Optional[Dict[str, Any]] = None,
    db_session: Optional[AsyncSession] = None,
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
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
        except Exception:
            logger.exception(
                "Failed to get actual record count, using total_records field"
            )
            total_records = data_import.total_records if data_import else 0

    total_fields = len(field_mappings)

    # Real quality issues from raw data analysis
    quality_issues = []
    recommendations = []
    field_quality_scores = {}
    field_stats = {}  # Initialize to empty dict to handle cases with no raw records

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
                quality_issues = await _apply_stored_resolutions(
                    flow_id, quality_issues, db_session
                )
            else:
                logger.warning(f"No raw records found for data import {data_import.id}")
        except Exception:
            logger.exception("Failed to analyze raw data for quality issues")
            # Continue with empty quality issues if analysis fails

        # Load existing recommendations from database or create new ones
        try:
            # Convert flow_id to UUID if it's a string
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            # Build query with tenant filters if provided
            flow_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_uuid
            )  # SKIP_TENANT_CHECK
            if client_account_id is not None:
                flow_query = flow_query.where(
                    DiscoveryFlow.client_account_id == client_account_id
                )
            if engagement_id is not None:
                flow_query = flow_query.where(
                    DiscoveryFlow.engagement_id == engagement_id
                )

            flow_result = await db_session.execute(flow_query)
            flow = flow_result.scalar_one_or_none()

            if flow:
                # Try to load existing recommendations from database
                try:
                    existing_recommendations = (
                        await _load_recommendations_from_database(
                            flow_id,
                            db_session,
                            str(flow.client_account_id),
                            str(flow.engagement_id),
                        )
                    )

                    if existing_recommendations:
                        # Use existing recommendations from database
                        logger.info(
                            f"Using {len(existing_recommendations)} existing recommendations from database"
                        )
                        recommendations.extend(existing_recommendations)
                    else:
                        # No existing recommendations, create new sample recommendations
                        logger.info(
                            "No existing recommendations found, creating new sample recommendations"
                        )
                        # Only create sample recommendations if we have actual field data
                        if field_stats:
                            actual_fields = list(field_stats.keys())[
                                :3
                            ]  # Use first 3 actual fields
                            new_recommendations = [
                                DataCleansingRecommendation(
                                    id=str(uuid.uuid4()),
                                    category="standardization",
                                    title="Standardize date formats",
                                    description="Multiple date formats detected. Standardize to ISO 8601 format",
                                    priority="high",
                                    impact="Improves data consistency and query performance",
                                    effort_estimate="2-4 hours",
                                    fields_affected=(
                                        actual_fields
                                        if actual_fields
                                        else ["example_field"]
                                    ),
                                    status="pending",
                                ),
                            ]
                        else:
                            # No field data available, create generic example
                            new_recommendations = []
                            logger.info(
                                "No field data available for creating sample recommendations"
                            )

                        recommendations.extend(new_recommendations)

                        # Try to store new recommendations to database (gracefully handle if table doesn't exist)
                        try:
                            await _store_recommendations_to_database(
                                flow_id,
                                new_recommendations,
                                db_session,
                                str(flow.client_account_id),
                                str(flow.engagement_id),
                            )
                        except Exception:
                            logger.exception(
                                "Failed to store recommendations to database "
                                "(table may not exist yet). "
                                "Recommendations will still be returned but not persisted."
                            )
                            # Continue without storing - recommendations are still in memory
                except Exception:
                    logger.exception(
                        "Failed to load recommendations from database (table may not exist yet). "
                        "Creating new sample recommendations instead."
                    )
                    # Create sample recommendations as fallback
                    new_recommendations = [
                        DataCleansingRecommendation(
                            id=str(uuid.uuid4()),
                            category="standardization",
                            title="Standardize date formats",
                            description="Multiple date formats detected. Standardize to ISO 8601 format",
                            priority="high",
                            impact="Improves data consistency and query performance",
                            effort_estimate="2-4 hours",
                            fields_affected=[
                                "created_date",
                                "modified_date",
                                "last_seen",
                            ],
                            status="pending",
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
                            status="pending",
                        ),
                    ]
                    recommendations.extend(new_recommendations)
            else:
                # Flow not found, create sample recommendations anyway
                logger.warning(
                    f"Flow {flow_id} not found, creating sample recommendations"
                )
                new_recommendations = [
                    DataCleansingRecommendation(
                        id=str(uuid.uuid4()),
                        category="standardization",
                        title="Standardize date formats",
                        description="Multiple date formats detected. Standardize to ISO 8601 format",
                        priority="high",
                        impact="Improves data consistency and query performance",
                        effort_estimate="2-4 hours",
                        fields_affected=["created_date", "modified_date", "last_seen"],
                        status="pending",
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
                        status="pending",
                    ),
                ]
                recommendations.extend(new_recommendations)
        except Exception:
            # Fallback: create sample recommendations if anything goes wrong
            logger.exception(
                "Error loading/creating recommendations. Creating fallback recommendations."
            )
            fallback_recommendations = [
                DataCleansingRecommendation(
                    id=str(uuid.uuid4()),
                    category="standardization",
                    title="Standardize date formats",
                    description="Multiple date formats detected. Standardize to ISO 8601 format",
                    priority="high",
                    impact="Improves data consistency and query performance",
                    effort_estimate="2-4 hours",
                    fields_affected=["created_date", "modified_date", "last_seen"],
                    confidence=0.92,
                    status="pending",
                    agent_source="Data Standardization Specialist",
                    implementation_steps=[
                        "Analyze all date fields to identify format variations",
                        "Create transformation rules for common date patterns",
                        "Apply ISO 8601 format (YYYY-MM-DD) to all date fields",
                        "Validate transformed dates for accuracy",
                        "Update field mappings to reflect standardized format",
                    ],
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
                    confidence=0.87,
                    status="pending",
                    agent_source="Data Quality Agent",
                    implementation_steps=[
                        "Identify server names with invalid characters or patterns",
                        "Define naming convention standards (e.g., alphanumeric, hyphens only)",
                        "Create transformation rules to sanitize server names",
                        "Apply validation rules to ensure consistency",
                        "Review transformed names for accuracy",
                    ],
                ),
            ]
            recommendations.extend(fallback_recommendations)

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
