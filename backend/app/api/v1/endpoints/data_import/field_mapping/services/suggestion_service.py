"""
AI-powered field mapping suggestion service.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, RawImportRecord

from ..models.mapping_schemas import (FieldMappingAnalysis,
                                      FieldMappingSuggestion)

# Legacy hardcoded mapping helpers removed - using CrewAI agents only
# from ..utils.mapping_helpers import intelligent_field_mapping, calculate_mapping_confidence

logger = logging.getLogger(__name__)

# Import CrewAI Field Mapping Crew with fallback
try:
    from app.services.crewai_flows.crews.field_mapping_crew import \
        create_field_mapping_crew

    CREWAI_FIELD_MAPPING_AVAILABLE = True
except ImportError:
    CREWAI_FIELD_MAPPING_AVAILABLE = False
    create_field_mapping_crew = None


class SuggestionService:
    """Service for generating AI-powered field mapping suggestions."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def get_field_mapping_suggestions(
        self, import_id: str
    ) -> FieldMappingAnalysis:
        """Get AI-powered field mapping suggestions for an import."""

        # Convert string UUID to UUID object if needed
        from uuid import UUID

        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")

        # Get import data
        import_query = select(DataImport).where(
            and_(
                DataImport.id == import_uuid,
                DataImport.client_account_id == client_account_uuid,
            )
        )
        import_result = await self.db.execute(import_query)
        data_import = import_result.scalar_one_or_none()

        if not data_import:
            raise ValueError(f"Data import {import_id} not found")

        # Get sample data for analysis
        sample_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == import_id)
            .limit(5)
        )  # Get first 5 records for analysis

        sample_result = await self.db.execute(sample_query)
        sample_records = sample_result.scalars().all()

        if not sample_records:
            raise ValueError("No sample data found for analysis")

        # Extract source fields and sample data
        source_fields = []
        sample_data = []

        for record in sample_records:
            if record.raw_data:
                sample_data.append(record.raw_data)
                if not source_fields:  # Get field names from first record
                    source_fields = list(record.raw_data.keys())

        if not source_fields:
            raise ValueError("No source fields found in data")

        logger.info(
            f"Analyzing {len(source_fields)} fields with {len(sample_data)} sample records"
        )

        # Get available target fields
        available_fields = await self._get_available_target_fields()

        # Generate AI-powered suggestions
        try:
            from app.services.crewai_modular import crewai_service

            suggestions = await self._generate_ai_suggestions(
                source_fields=source_fields,
                sample_data=sample_data,
                available_fields=available_fields,
                crewai_service=(
                    crewai_service if hasattr(crewai_service, "llm") else None
                ),
            )
        except Exception as e:
            logger.error(f"❌ CrewAI service not available: {e}")
            # DISABLED FALLBACK - Let the error propagate to see actual agent issues
            # suggestions = await self._generate_fallback_suggestions(
            #     source_fields, sample_data, available_fields
            # )
            raise e

        # Calculate analysis metrics
        total_fields = len(source_fields)
        confidence_scores = [s.confidence for s in suggestions]
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return FieldMappingAnalysis(
            total_fields=total_fields,
            mapped_fields=len(suggestions),
            unmapped_fields=max(0, total_fields - len(suggestions)),
            confidence_score=avg_confidence,
            suggestions=suggestions,
        )

    async def _get_available_target_fields(self) -> List[Dict[str, Any]]:
        """Get list of available target fields for mapping based on Asset model."""
        # Define all available target fields based on Asset model
        standard_fields = [
            # Identity fields (Critical for migration)
            {
                "name": "name",
                "type": "string",
                "description": "Asset name",
                "category": "identification",
                "required": True,
            },
            {
                "name": "asset_name",
                "type": "string",
                "description": "Asset display name",
                "category": "identification",
                "required": False,
            },
            {
                "name": "hostname",
                "type": "string",
                "description": "Network hostname",
                "category": "identification",
                "required": True,
            },
            {
                "name": "fqdn",
                "type": "string",
                "description": "Fully qualified domain name",
                "category": "identification",
                "required": False,
            },
            {
                "name": "asset_type",
                "type": "string",
                "description": "Type of asset (server, database, application, etc.)",
                "category": "identification",
                "required": True,
            },
            {
                "name": "description",
                "type": "string",
                "description": "Asset description",
                "category": "identification",
                "required": False,
            },
            # Network fields (Critical for migration)
            {
                "name": "ip_address",
                "type": "string",
                "description": "IP address",
                "category": "network",
                "required": True,
            },
            {
                "name": "mac_address",
                "type": "string",
                "description": "MAC address",
                "category": "network",
                "required": False,
            },
            # System fields (Critical for migration)
            {
                "name": "operating_system",
                "type": "string",
                "description": "Operating system",
                "category": "technical",
                "required": True,
            },
            {
                "name": "os_version",
                "type": "string",
                "description": "OS version",
                "category": "technical",
                "required": False,
            },
            {
                "name": "cpu_cores",
                "type": "integer",
                "description": "Number of CPU cores",
                "category": "technical",
                "required": True,
            },
            {
                "name": "memory_gb",
                "type": "number",
                "description": "Memory in GB",
                "category": "technical",
                "required": True,
            },
            {
                "name": "storage_gb",
                "type": "number",
                "description": "Storage in GB",
                "category": "technical",
                "required": True,
            },
            # Location and Environment fields (Critical for migration)
            {
                "name": "environment",
                "type": "string",
                "description": "Environment (prod, dev, test)",
                "category": "environment",
                "required": True,
            },
            {
                "name": "location",
                "type": "string",
                "description": "Physical location",
                "category": "environment",
                "required": False,
            },
            {
                "name": "datacenter",
                "type": "string",
                "description": "Data center",
                "category": "environment",
                "required": False,
            },
            {
                "name": "rack_location",
                "type": "string",
                "description": "Rack location",
                "category": "environment",
                "required": False,
            },
            {
                "name": "availability_zone",
                "type": "string",
                "description": "Availability zone",
                "category": "environment",
                "required": False,
            },
            # Business fields (Critical for migration)
            {
                "name": "business_owner",
                "type": "string",
                "description": "Business owner",
                "category": "business",
                "required": True,
            },
            {
                "name": "technical_owner",
                "type": "string",
                "description": "Technical owner",
                "category": "business",
                "required": True,
            },
            {
                "name": "department",
                "type": "string",
                "description": "Department",
                "category": "business",
                "required": True,
            },
            {
                "name": "application_name",
                "type": "string",
                "description": "Application name",
                "category": "application",
                "required": True,
            },
            {
                "name": "technology_stack",
                "type": "string",
                "description": "Technology stack",
                "category": "application",
                "required": False,
            },
            {
                "name": "criticality",
                "type": "string",
                "description": "Business criticality (low, medium, high, critical)",
                "category": "business",
                "required": True,
            },
            {
                "name": "business_criticality",
                "type": "string",
                "description": "Business criticality level",
                "category": "business",
                "required": True,
            },
            # Migration fields (Critical for migration)
            {
                "name": "six_r_strategy",
                "type": "string",
                "description": "6R migration strategy",
                "category": "migration",
                "required": True,
            },
            {
                "name": "migration_priority",
                "type": "integer",
                "description": "Migration priority (1-10)",
                "category": "migration",
                "required": True,
            },
            {
                "name": "migration_complexity",
                "type": "string",
                "description": "Migration complexity (low, medium, high)",
                "category": "migration",
                "required": True,
            },
            {
                "name": "migration_wave",
                "type": "integer",
                "description": "Migration wave number",
                "category": "migration",
                "required": False,
            },
            {
                "name": "sixr_ready",
                "type": "string",
                "description": "6R readiness status",
                "category": "migration",
                "required": False,
            },
            # Status fields
            {
                "name": "status",
                "type": "string",
                "description": "Operational status",
                "category": "status",
                "required": False,
            },
            {
                "name": "migration_status",
                "type": "string",
                "description": "Migration status",
                "category": "status",
                "required": False,
            },
            {
                "name": "mapping_status",
                "type": "string",
                "description": "Mapping status",
                "category": "status",
                "required": False,
            },
            # Dependencies (Critical for migration)
            {
                "name": "dependencies",
                "type": "json",
                "description": "List of dependent assets",
                "category": "dependencies",
                "required": True,
            },
            {
                "name": "related_assets",
                "type": "json",
                "description": "Related CI items",
                "category": "dependencies",
                "required": False,
            },
            # Discovery metadata
            {
                "name": "discovery_method",
                "type": "string",
                "description": "Discovery method",
                "category": "discovery",
                "required": False,
            },
            {
                "name": "discovery_source",
                "type": "string",
                "description": "Discovery source",
                "category": "discovery",
                "required": False,
            },
            {
                "name": "discovery_timestamp",
                "type": "datetime",
                "description": "Discovery timestamp",
                "category": "discovery",
                "required": False,
            },
            # Performance metrics
            {
                "name": "cpu_utilization_percent",
                "type": "number",
                "description": "CPU utilization percentage",
                "category": "performance",
                "required": False,
            },
            {
                "name": "memory_utilization_percent",
                "type": "number",
                "description": "Memory utilization percentage",
                "category": "performance",
                "required": False,
            },
            {
                "name": "disk_iops",
                "type": "number",
                "description": "Disk IOPS",
                "category": "performance",
                "required": False,
            },
            {
                "name": "network_throughput_mbps",
                "type": "number",
                "description": "Network throughput in Mbps",
                "category": "performance",
                "required": False,
            },
            # Data quality
            {
                "name": "completeness_score",
                "type": "number",
                "description": "Data completeness score",
                "category": "ai_insights",
                "required": False,
            },
            {
                "name": "quality_score",
                "type": "number",
                "description": "Data quality score",
                "category": "ai_insights",
                "required": False,
            },
            # Cost information
            {
                "name": "current_monthly_cost",
                "type": "number",
                "description": "Current monthly cost",
                "category": "cost",
                "required": False,
            },
            {
                "name": "estimated_cloud_cost",
                "type": "number",
                "description": "Estimated cloud cost",
                "category": "cost",
                "required": False,
            },
            # Import metadata
            {
                "name": "source_filename",
                "type": "string",
                "description": "Source filename",
                "category": "metadata",
                "required": False,
            },
            {
                "name": "custom_attributes",
                "type": "json",
                "description": "Custom attributes",
                "category": "metadata",
                "required": False,
            },
        ]

        return standard_fields

    async def _generate_ai_suggestions(
        self,
        source_fields: List[str],
        sample_data: List[Dict[str, Any]],
        available_fields: List[Dict[str, Any]],
        crewai_service=None,
    ) -> List[FieldMappingSuggestion]:
        """Generate AI-powered field mapping suggestions using CrewAI."""

        if not CREWAI_FIELD_MAPPING_AVAILABLE or not crewai_service:
            logger.error("❌ CrewAI Field Mapping not available")
            # DISABLED FALLBACK - Let the error propagate to see actual agent issues
            # return await self._generate_fallback_suggestions(source_fields, sample_data, available_fields)
            raise RuntimeError(
                "CrewAI Field Mapping crew is required but not available"
            )

        try:
            # Create Field Mapping Crew
            field_mapping_crew = create_field_mapping_crew(
                crewai_service=crewai_service,
                raw_data=sample_data,
                shared_memory=None,
                knowledge_base=None,
            )

            # Execute the crew
            crew_result = field_mapping_crew.kickoff()

            # Parse crew results
            suggestions = await self._parse_crew_results(
                crew_result, source_fields, available_fields
            )

            logger.info(
                f"CrewAI generated {len(suggestions)} field mapping suggestions"
            )
            return suggestions

        except Exception as e:
            logger.error(f"❌ Error in CrewAI field mapping analysis: {e}")
            # DISABLED FALLBACK - Let the error propagate to see actual agent issues
            # return await self._generate_fallback_suggestions(source_fields, sample_data, available_fields)
            raise e

    async def _parse_crew_results(
        self,
        crew_result: Any,
        source_fields: List[str],
        available_fields: List[Dict[str, Any]],
    ) -> List[FieldMappingSuggestion]:
        """Parse CrewAI crew results into structured suggestions."""
        suggestions = []
        result_str = str(crew_result) if crew_result else ""

        try:
            for source_field in source_fields:
                # Look for field mapping suggestions in crew result
                best_match = None
                confidence = 0.7  # Default confidence for AI analysis

                # Simple pattern matching to find suggested target fields
                for field in available_fields:
                    field_name = field.get("name", "")
                    if (
                        field_name.lower() in result_str.lower()
                        or source_field.lower() in field_name.lower()
                    ):
                        best_match = field_name
                        confidence = 0.8
                        break

                # If no specific match found, use simple pattern matching
                if not best_match:
                    # Simple fallback pattern matching
                    source_lower = source_field.lower()
                    if "name" in source_lower or "hostname" in source_lower:
                        best_match = "name"
                    elif "type" in source_lower:
                        best_match = "asset_type"
                    elif "env" in source_lower:
                        best_match = "environment"
                    elif "ip" in source_lower:
                        best_match = "ip_address"
                    else:
                        best_match = "name"  # Default fallback
                    confidence = 0.5

                suggestion = FieldMappingSuggestion(
                    source_field=source_field,
                    target_field=best_match,
                    confidence=confidence,
                    reasoning=f"AI analysis using CrewAI: Semantic analysis suggests mapping '{source_field}' to '{best_match}'",
                    sample_values=[],  # Would be populated with actual sample data
                    mapping_type="ai_crewai",
                    crew_analysis=(
                        result_str[:200] + "..."
                        if len(result_str) > 200
                        else result_str
                    ),
                    ai_driven=True,
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"❌ Error parsing crew results: {e}")
            # DISABLED FALLBACK - Let the error propagate to see actual agent issues
            # return await self._generate_fallback_suggestions(source_fields, [], available_fields)
            raise e

    async def _generate_fallback_suggestions(
        self,
        source_fields: List[str],
        sample_data: List[Dict[str, Any]],
        available_fields: List[Dict[str, Any]],
    ) -> List[FieldMappingSuggestion]:
        """Generate fallback field mapping suggestions using pattern matching."""
        suggestions = []

        for source_field in source_fields:
            # Simple pattern-based mapping since hardcoded helpers were removed
            source_lower = source_field.lower()
            if "name" in source_lower or "hostname" in source_lower:
                target_field = "name"
                confidence = 0.8
            elif "type" in source_lower:
                target_field = "asset_type"
                confidence = 0.8
            elif "env" in source_lower:
                target_field = "environment"
                confidence = 0.7
            elif "ip" in source_lower:
                target_field = "ip_address"
                confidence = 0.8
            elif "os" in source_lower:
                target_field = "operating_system"
                confidence = 0.7
            else:
                target_field = source_field  # Keep original name
                confidence = 0.5

            # Extract sample values if available
            sample_values = []
            if sample_data:
                sample_values = [
                    str(record.get(source_field, ""))
                    for record in sample_data[:3]
                    if record.get(source_field) is not None
                ]

            suggestion = FieldMappingSuggestion(
                source_field=source_field,
                target_field=target_field,
                confidence=confidence,
                reasoning=f"Pattern-based mapping: '{source_field}' mapped to '{target_field}' based on field name similarity",
                sample_values=sample_values,
                mapping_type="fallback_pattern",
                ai_driven=False,
            )
            suggestions.append(suggestion)

        return suggestions

    async def regenerate_suggestions(
        self, import_id: str, feedback: Optional[Dict[str, Any]] = None
    ) -> FieldMappingAnalysis:
        """Regenerate suggestions with user feedback incorporated."""

        # TODO: Implement learning from feedback
        # For now, just regenerate with current logic
        logger.info(
            f"Regenerating suggestions for import {import_id} with feedback: {feedback}"
        )

        return await self.get_field_mapping_suggestions(import_id)

    async def get_suggestion_confidence_metrics(self, import_id: str) -> Dict[str, Any]:
        """Get confidence metrics for suggestions."""

        analysis = await self.get_field_mapping_suggestions(import_id)

        confidence_levels = {
            "high": len([s for s in analysis.suggestions if s.confidence >= 0.8]),
            "medium": len(
                [s for s in analysis.suggestions if 0.5 <= s.confidence < 0.8]
            ),
            "low": len([s for s in analysis.suggestions if s.confidence < 0.5]),
        }

        return {
            "total_suggestions": len(analysis.suggestions),
            "confidence_levels": confidence_levels,
            "average_confidence": analysis.confidence_score,
            "ai_generated": len([s for s in analysis.suggestions if s.ai_driven]),
            "pattern_based": len([s for s in analysis.suggestions if not s.ai_driven]),
        }
