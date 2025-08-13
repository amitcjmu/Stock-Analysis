"""
Field Mapping Service for Service Registry Architecture

This service provides field mapping capabilities for the discovery flow,
following the Service Registry pattern with proper session management
and multi-tenant context propagation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError

from app.core.context import RequestContext
from app.services.base_service import ServiceBase
from app.models.data_import.mapping import ImportFieldMapping as FieldMapping


@dataclass
class MappingAnalysis:
    """Result of field mapping analysis"""

    mapped_fields: Dict[str, str]
    unmapped_fields: List[str]
    suggested_mappings: Dict[str, List[str]]
    confidence_scores: Dict[str, float]
    missing_required_fields: List[str]
    overall_confidence: float


@dataclass
class MappingRule:
    """Field mapping rule with metadata"""

    source_field: str
    target_field: str
    confidence: float
    source: str  # 'learned', 'base', 'user', 'ai'
    context: Optional[str] = None
    created_at: Optional[datetime] = None


class FieldMappingService(ServiceBase):
    """
    Service for managing field mappings in the discovery flow.

    This service:
    - Manages field mapping rules and transformations
    - Learns from user feedback and AI analysis
    - Provides mapping suggestions and validation
    - Maintains multi-tenant context for mappings
    - Never commits or closes the database session
    """

    # Base mappings for common field variations
    BASE_MAPPINGS = {
        "hostname": [
            "host_name",
            "server_name",
            "machine_name",
            "computer_name",
            "fqdn",
        ],
        "ip_address": ["ip", "ip_addr", "ipv4", "ipv6", "network_address"],
        "asset_name": ["name", "asset", "resource_name", "display_name"],
        "asset_type": ["type", "resource_type", "category", "asset_category"],
        "environment": ["env", "stage", "deployment_env", "environment_type"],
        "business_owner": [
            "owner",
            "business_contact",
            "responsible_party",
            "app_owner",
        ],
        "department": ["dept", "division", "business_unit", "org_unit"],
        "operating_system": ["os", "os_name", "os_version", "platform"],
        "cpu_cores": ["cpu", "cores", "vcpu", "processors", "cpu_count"],
        "memory_gb": ["ram", "memory", "ram_gb", "total_memory", "mem_size"],
        "storage_gb": ["disk", "storage", "disk_size", "total_storage", "disk_gb"],
        "location": ["datacenter", "site", "region", "dc", "data_center"],
        "status": ["state", "operational_status", "current_status"],
        "criticality": ["priority", "importance", "critical_level", "tier"],
    }

    # Required fields for different asset types
    REQUIRED_FIELDS = {
        "server": [
            "hostname",
            "asset_name",
            "asset_type",
            "environment",
            "operating_system",
        ],
        "application": ["asset_name", "asset_type", "environment", "business_owner"],
        "database": ["asset_name", "asset_type", "environment", "database_type"],
        "network": ["asset_name", "asset_type", "ip_address", "location"],
        "storage": ["asset_name", "asset_type", "capacity", "location"],
    }

    def __init__(self, session: AsyncSession, context: RequestContext):
        """
        Initialize FieldMappingService.

        Args:
            session: Database session from orchestrator
            context: Request context with tenant information
        """
        super().__init__(session, context)

        # Initialize mapping caches
        self._learned_mappings_cache: Optional[Dict[str, List[MappingRule]]] = None
        self._negative_mappings_cache: Set[tuple] = set()

        self.logger.debug(
            f"Initialized FieldMappingService for client {context.client_account_id}"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for FieldMappingService.

        Returns:
            Health status and metrics
        """
        try:
            # Count mappings in database
            query = select(func.count(FieldMapping.id)).where(
                FieldMapping.client_account_id == self.context.client_account_id
            )
            result = await self.session.execute(query)
            mapping_count = result.scalar() or 0

            return {
                "status": "healthy",
                "service": "FieldMappingService",
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "mapping_count": mapping_count,
                "base_mappings": len(self.BASE_MAPPINGS),
                "cached_learned_mappings": (
                    len(self._learned_mappings_cache)
                    if self._learned_mappings_cache
                    else 0
                ),
            }
        except Exception as e:
            await self.record_failure(
                operation="health_check",
                error=e,
                context_data={"service": "FieldMappingService"},
            )
            return {
                "status": "unhealthy",
                "service": "FieldMappingService",
                "error": str(e),
            }

    async def analyze_columns(
        self,
        columns: List[str],
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        asset_type: str = "server",
        sample_data: Optional[List[List[Any]]] = None,
    ) -> MappingAnalysis:
        """
        Analyze columns and provide mapping insights.

        Args:
            columns: List of column names to analyze
            data_import_id: Optional data import ID for context
            master_flow_id: Optional master flow ID for context
            asset_type: Type of asset being analyzed
            sample_data: Optional sample data for content analysis

        Returns:
            MappingAnalysis with mapping suggestions and confidence scores
        """
        try:
            self.logger.debug(
                f"Analyzing {len(columns)} columns for {asset_type} assets"
            )

            # Load learned mappings if not cached
            if self._learned_mappings_cache is None:
                await self._load_learned_mappings(data_import_id, master_flow_id)

            mapped_fields = {}
            unmapped_fields = []
            suggested_mappings = {}
            confidence_scores = {}

            for column in columns:
                normalized_column = self._normalize_field_name(column)

                # Try to find mapping
                mapping_result = await self._find_best_mapping(
                    normalized_column, asset_type, sample_data
                )

                if mapping_result:
                    mapped_fields[column] = mapping_result.target_field
                    confidence_scores[column] = mapping_result.confidence

                    # Add to suggestions if confidence is not perfect
                    if mapping_result.confidence < 1.0:
                        alternatives = await self._find_alternative_mappings(
                            normalized_column, mapping_result.target_field
                        )
                        if alternatives:
                            suggested_mappings[column] = alternatives
                else:
                    unmapped_fields.append(column)
                    confidence_scores[column] = 0.0

                    # Try to suggest possible mappings
                    suggestions = await self._suggest_mappings_for_field(
                        normalized_column, asset_type
                    )
                    if suggestions:
                        suggested_mappings[column] = suggestions

            # Identify missing required fields
            required_fields = self.REQUIRED_FIELDS.get(asset_type, [])
            mapped_field_values = set(mapped_fields.values())
            missing_required = [
                field for field in required_fields if field not in mapped_field_values
            ]

            # Calculate overall confidence
            overall_confidence = (
                sum(confidence_scores.values()) / len(confidence_scores)
                if confidence_scores
                else 0.0
            )

            return MappingAnalysis(
                mapped_fields=mapped_fields,
                unmapped_fields=unmapped_fields,
                suggested_mappings=suggested_mappings,
                confidence_scores=confidence_scores,
                missing_required_fields=missing_required,
                overall_confidence=overall_confidence,
            )

        except Exception as e:
            await self.record_failure(
                operation="analyze_columns",
                error=e,
                context_data={"column_count": len(columns), "asset_type": asset_type},
            )
            # Return empty analysis on failure
            return MappingAnalysis(
                mapped_fields={},
                unmapped_fields=columns,
                suggested_mappings={},
                confidence_scores={col: 0.0 for col in columns},
                missing_required_fields=self.REQUIRED_FIELDS.get(asset_type, []),
                overall_confidence=0.0,
            )

    async def learn_field_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: UUID,
        master_flow_id: Optional[UUID] = None,
        confidence: float = 0.9,
        source: str = "user",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Learn a new field mapping.

        Args:
            source_field: Source field name
            target_field: Target canonical field name
            data_import_id: Required data import ID
            master_flow_id: Optional master flow ID
            confidence: Confidence score (0-1)
            source: Source of the mapping (user, ai, system)
            context: Optional context information

        Returns:
            Result of learning operation
        """
        try:
            normalized_source = self._normalize_field_name(source_field)
            normalized_target = self._normalize_field_name(target_field)

            # Check if this is a negative mapping we've seen before
            if (normalized_source, normalized_target) in self._negative_mappings_cache:
                return {
                    "success": False,
                    "message": f"Mapping {source_field} -> {target_field} was previously rejected",
                }

            # Create or update mapping in database
            existing_mapping = await self._get_existing_mapping(
                normalized_source, normalized_target, data_import_id
            )

            if existing_mapping:
                # Update confidence if this is higher
                if confidence > existing_mapping.confidence_score:
                    existing_mapping.confidence_score = confidence
                    existing_mapping.updated_at = datetime.utcnow()
                    existing_mapping.suggested_by = source
                    if context:
                        existing_mapping.transformation_rules = (
                            existing_mapping.transformation_rules or {}
                        )
                        existing_mapping.transformation_rules["context"] = context

                    # Flush to get ID without committing
                    await self.flush_for_id()

                    self.logger.info(
                        f"Updated field mapping: {source_field} -> {target_field} "
                        f"(confidence: {confidence})"
                    )

                    # Update cache
                    self._update_cache(
                        normalized_source, normalized_target, confidence, source
                    )

                    return {
                        "success": True,
                        "action": "updated",
                        "mapping_id": str(existing_mapping.id),
                        "confidence": confidence,
                    }
                else:
                    return {
                        "success": True,
                        "action": "exists",
                        "message": "Mapping already exists with equal or higher confidence",
                        "existing_confidence": existing_mapping.confidence_score,
                    }
            else:
                # Create new mapping
                new_mapping = FieldMapping(
                    data_import_id=data_import_id,  # Required field
                    master_flow_id=master_flow_id,  # Optional field
                    client_account_id=self.context.client_account_id,
                    source_field=normalized_source,
                    target_field=normalized_target,
                    confidence_score=confidence,
                    match_type="learned",  # Use match_type instead of mapping_type
                    suggested_by=source,  # Use suggested_by instead of source
                    transformation_rules=(
                        {"context": context} if context else {}
                    ),  # Use transformation_rules instead of metadata
                    status="approved",  # Set status as approved since it's being learned
                    approved_by=(
                        str(self.context.user_id) if self.context.user_id else None
                    ),
                    approved_at=datetime.utcnow() if source == "user" else None,
                )

                self.session.add(new_mapping)
                await self.flush_for_id()

                self.logger.info(
                    f"Learned new field mapping: {source_field} -> {target_field} "
                    f"(confidence: {confidence})"
                )

                # Update cache
                self._update_cache(
                    normalized_source, normalized_target, confidence, source
                )

                return {
                    "success": True,
                    "action": "created",
                    "mapping_id": str(new_mapping.id),
                    "source_field": source_field,
                    "target_field": target_field,
                    "confidence": confidence,
                }

        except IntegrityError as e:
            # Handle unique constraint violation
            self.logger.warning(f"Mapping already exists: {e}")
            return {
                "success": False,
                "error": "Mapping already exists",
                "message": str(e),
            }
        except Exception as e:
            await self.record_failure(
                operation="learn_field_mapping",
                error=e,
                context_data={
                    "source_field": source_field,
                    "target_field": target_field,
                },
            )
            return {"success": False, "error": str(e)}

    async def learn_negative_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: UUID,
        master_flow_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Learn that a field mapping should NOT be made.

        Args:
            source_field: Source field that should not map
            target_field: Target field to avoid
            data_import_id: Required data import ID
            master_flow_id: Optional master flow ID
            reason: Optional reason for rejection

        Returns:
            Result of negative learning
        """
        try:
            normalized_source = self._normalize_field_name(source_field)
            normalized_target = self._normalize_field_name(target_field)

            # Add to negative cache
            self._negative_mappings_cache.add((normalized_source, normalized_target))

            # Store in database as negative mapping using status field
            negative_mapping = FieldMapping(
                data_import_id=data_import_id,  # Required field
                master_flow_id=master_flow_id,  # Optional field
                client_account_id=self.context.client_account_id,
                source_field=normalized_source,
                target_field=normalized_target,
                confidence_score=0.0,  # Use 0 confidence for rejected
                match_type="manual",  # User rejected this
                suggested_by="user",  # User made this decision
                transformation_rules=(
                    {"rejection_reason": reason} if reason else {}
                ),  # Store rejection reason
                status="rejected",  # Set status as rejected
                approved_by=str(self.context.user_id) if self.context.user_id else None,
                approved_at=datetime.utcnow(),  # Rejection timestamp
            )

            self.session.add(negative_mapping)
            await self.flush_for_id()

            self.logger.info(
                f"Learned negative mapping: {source_field} should NOT map to {target_field}"
            )

            return {
                "success": True,
                "message": f"Learned to avoid mapping {source_field} to {target_field}",
                "mapping_id": str(negative_mapping.id),
            }

        except Exception as e:
            await self.record_failure(
                operation="learn_negative_mapping",
                error=e,
                context_data={
                    "source_field": source_field,
                    "target_field": target_field,
                },
            )
            return {"success": False, "error": str(e)}

    async def get_field_mappings(
        self,
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        asset_type: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        """
        Get all field mappings for the current context.

        Args:
            data_import_id: Optional data import ID filter
            master_flow_id: Optional master flow ID filter
            asset_type: Optional asset type filter

        Returns:
            Dictionary of canonical fields to their variations
        """
        try:
            # Start with base mappings
            mappings = dict(self.BASE_MAPPINGS)

            # Load learned mappings
            if self._learned_mappings_cache is None:
                await self._load_learned_mappings(data_import_id, master_flow_id)

            # Merge learned mappings
            if self._learned_mappings_cache:
                for target_field, rules in self._learned_mappings_cache.items():
                    if target_field not in mappings:
                        mappings[target_field] = []

                    for rule in rules:
                        if rule.source_field not in mappings[target_field]:
                            mappings[target_field].append(rule.source_field)

            # Filter by asset type if specified
            if asset_type and asset_type in self.REQUIRED_FIELDS:
                required = self.REQUIRED_FIELDS[asset_type]
                filtered_mappings = {
                    field: variations
                    for field, variations in mappings.items()
                    if field in required or field in self.BASE_MAPPINGS
                }
                return filtered_mappings

            return mappings

        except Exception as e:
            await self.record_failure(
                operation="get_field_mappings",
                error=e,
                context_data={"asset_type": asset_type},
            )
            return dict(self.BASE_MAPPINGS)  # Fallback to base mappings

    async def validate_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
        sample_values: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a field mapping with optional content analysis.

        Args:
            source_field: Source field name
            target_field: Target field name
            data_import_id: Optional data import ID for context
            master_flow_id: Optional master flow ID for context
            sample_values: Optional sample values for validation

        Returns:
            Validation result with confidence and issues
        """
        try:
            normalized_source = self._normalize_field_name(source_field)
            normalized_target = self._normalize_field_name(target_field)

            # Check if this is a known negative mapping
            if (normalized_source, normalized_target) in self._negative_mappings_cache:
                return {
                    "valid": False,
                    "confidence": 0.0,
                    "issues": ["This mapping was previously rejected"],
                }

            # Check base mappings
            if normalized_target in self.BASE_MAPPINGS:
                variations = [
                    self._normalize_field_name(v)
                    for v in self.BASE_MAPPINGS[normalized_target]
                ]
                if normalized_source in variations:
                    return {
                        "valid": True,
                        "confidence": 1.0,
                        "source": "base_mapping",
                        "issues": [],
                    }

            # Check learned mappings
            existing = await self._get_existing_mapping(
                normalized_source, normalized_target, data_import_id
            )
            if existing and existing.confidence_score > 0:
                return {
                    "valid": True,
                    "confidence": existing.confidence_score,
                    "source": "learned_mapping",
                    "issues": [],
                }

            # Perform content validation if sample values provided
            if sample_values:
                content_issues = self._validate_content(target_field, sample_values)
                if content_issues:
                    return {"valid": False, "confidence": 0.5, "issues": content_issues}

            # No existing mapping found
            return {
                "valid": False,
                "confidence": 0.0,
                "issues": ["No existing mapping found"],
                "suggestion": "Consider learning this mapping if valid",
            }

        except Exception as e:
            await self.record_failure(
                operation="validate_mapping",
                error=e,
                context_data={
                    "source_field": source_field,
                    "target_field": target_field,
                },
            )
            return {"valid": False, "confidence": 0.0, "error": str(e)}

    # Private helper methods

    async def _load_learned_mappings(
        self,
        data_import_id: Optional[UUID] = None,
        master_flow_id: Optional[UUID] = None,
    ) -> None:
        """Load learned mappings from database into cache."""
        try:
            # Build query with proper filters
            conditions = [
                FieldMapping.client_account_id == self.context.client_account_id,
                FieldMapping.status == "approved",  # Only approved mappings
                FieldMapping.confidence_score > 0,  # Exclude rejected
            ]

            # Add data_import_id or master_flow_id filter if provided
            if data_import_id:
                conditions.append(FieldMapping.data_import_id == data_import_id)
            elif master_flow_id:
                conditions.append(FieldMapping.master_flow_id == master_flow_id)

            query = select(FieldMapping).where(and_(*conditions))

            result = await self.session.execute(query)
            mappings = result.scalars().all()

            # Build cache
            self._learned_mappings_cache = {}
            for mapping in mappings:
                target = mapping.target_field
                if target not in self._learned_mappings_cache:
                    self._learned_mappings_cache[target] = []

                rule = MappingRule(
                    source_field=mapping.source_field,
                    target_field=mapping.target_field,
                    confidence=mapping.confidence_score,
                    source=mapping.suggested_by
                    or "learned",  # Use suggested_by instead of source
                    context=(
                        mapping.transformation_rules.get("context")
                        if mapping.transformation_rules
                        else None
                    ),  # Use transformation_rules instead of metadata
                    created_at=mapping.created_at,
                )
                self._learned_mappings_cache[target].append(rule)

            # Load rejected mappings
            negative_conditions = [
                FieldMapping.client_account_id == self.context.client_account_id,
                FieldMapping.status == "rejected",  # Use status field
            ]

            if data_import_id:
                negative_conditions.append(
                    FieldMapping.data_import_id == data_import_id
                )
            elif master_flow_id:
                negative_conditions.append(
                    FieldMapping.master_flow_id == master_flow_id
                )

            negative_query = select(FieldMapping).where(and_(*negative_conditions))

            negative_result = await self.session.execute(negative_query)
            negative_mappings = negative_result.scalars().all()

            for mapping in negative_mappings:
                self._negative_mappings_cache.add(
                    (mapping.source_field, mapping.target_field)
                )

            self.logger.debug(
                f"Loaded {len(mappings)} learned mappings and "
                f"{len(self._negative_mappings_cache)} negative mappings"
            )

        except Exception as e:
            self.logger.error(f"Failed to load learned mappings: {e}")
            self._learned_mappings_cache = {}

    async def _find_best_mapping(
        self,
        field_name: str,
        asset_type: str,
        sample_data: Optional[List[List[Any]]] = None,
    ) -> Optional[MappingRule]:
        """Find the best mapping for a field."""
        candidates = []

        # Check base mappings
        for canonical, variations in self.BASE_MAPPINGS.items():
            normalized_variations = [self._normalize_field_name(v) for v in variations]
            if field_name in normalized_variations:
                candidates.append(
                    MappingRule(
                        source_field=field_name,
                        target_field=canonical,
                        confidence=1.0,
                        source="base",
                    )
                )

        # Check learned mappings
        if self._learned_mappings_cache:
            for target, rules in self._learned_mappings_cache.items():
                for rule in rules:
                    if self._normalize_field_name(rule.source_field) == field_name:
                        candidates.append(rule)

        # Return highest confidence mapping
        if candidates:
            return max(candidates, key=lambda r: r.confidence)

        return None

    async def _find_alternative_mappings(
        self, field_name: str, exclude_target: str
    ) -> List[str]:
        """Find alternative mapping suggestions."""
        alternatives = []

        # Check base mappings
        for canonical, variations in self.BASE_MAPPINGS.items():
            if canonical != exclude_target:
                normalized_variations = [
                    self._normalize_field_name(v) for v in variations
                ]
                # Check for partial matches
                for variation in normalized_variations:
                    if field_name in variation or variation in field_name:
                        alternatives.append(canonical)
                        break

        return alternatives[:3]  # Return top 3 alternatives

    async def _suggest_mappings_for_field(
        self, field_name: str, asset_type: str
    ) -> List[str]:
        """Suggest possible mappings for an unmapped field."""
        suggestions = []

        # Use fuzzy matching on field name components
        field_parts = set(field_name.replace("_", " ").split())

        for canonical in self.BASE_MAPPINGS.keys():
            canonical_parts = set(canonical.replace("_", " ").split())

            # Check for word overlap
            if field_parts & canonical_parts:
                suggestions.append(canonical)

        # Prioritize required fields for the asset type
        required = self.REQUIRED_FIELDS.get(asset_type, [])
        prioritized = [s for s in suggestions if s in required]
        others = [s for s in suggestions if s not in required]

        return prioritized + others

    async def _get_existing_mapping(
        self,
        source_field: str,
        target_field: str,
        data_import_id: Optional[UUID] = None,
    ) -> Optional[FieldMapping]:
        """Get existing mapping from database."""
        conditions = [
            FieldMapping.client_account_id == self.context.client_account_id,
            FieldMapping.source_field == source_field,
            FieldMapping.target_field == target_field,
            FieldMapping.status.in_(["approved", "suggested"]),
        ]

        # Add data_import_id filter if provided
        if data_import_id:
            conditions.append(FieldMapping.data_import_id == data_import_id)

        query = select(FieldMapping).where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison."""
        return field_name.lower().strip().replace(" ", "_").replace("-", "_")

    def _update_cache(
        self, source_field: str, target_field: str, confidence: float, source: str
    ) -> None:
        """Update the learned mappings cache."""
        if self._learned_mappings_cache is None:
            self._learned_mappings_cache = {}

        if target_field not in self._learned_mappings_cache:
            self._learned_mappings_cache[target_field] = []

        # Check if mapping already exists in cache
        existing_index = None
        for i, rule in enumerate(self._learned_mappings_cache[target_field]):
            if rule.source_field == source_field:
                existing_index = i
                break

        new_rule = MappingRule(
            source_field=source_field,
            target_field=target_field,
            confidence=confidence,
            source=source,
            created_at=datetime.utcnow(),
        )

        if existing_index is not None:
            # Update existing rule
            self._learned_mappings_cache[target_field][existing_index] = new_rule
        else:
            # Add new rule
            self._learned_mappings_cache[target_field].append(new_rule)

    def _validate_content(
        self, target_field: str, sample_values: List[Any]
    ) -> List[str]:
        """Validate content against expected patterns for target field."""
        issues = []

        # Field-specific validation rules
        if target_field == "ip_address":
            for value in sample_values[:5]:  # Check first 5 values
                if not self._is_valid_ip(str(value)):
                    issues.append(f"Invalid IP address format: {value}")

        elif target_field == "email":
            for value in sample_values[:5]:
                if "@" not in str(value):
                    issues.append(f"Invalid email format: {value}")

        elif target_field in ["cpu_cores", "memory_gb", "storage_gb"]:
            for value in sample_values[:5]:
                try:
                    float(value)
                except (ValueError, TypeError):
                    issues.append(f"Expected numeric value, got: {value}")

        return issues[:3]  # Return max 3 issues

    def _is_valid_ip(self, value: str) -> bool:
        """Check if value is a valid IP address."""
        parts = value.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
