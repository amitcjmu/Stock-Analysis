"""
Mapping Utilities
Utility classes for field mapping operations including similarity calculation
and standard field registry.
"""

import difflib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class FieldMappingRule:
    """Field mapping rule with confidence and source information"""

    def __init__(
        self, rule_name: str = "", rule_type: str = "", confidence: float = 0.0
    ):
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.confidence = confidence
        self.created_at = datetime.utcnow()


class MappingContext:
    """Context information for field mapping operations"""

    def __init__(self, context_data: Optional[Dict[str, Any]] = None):
        self.context_data = context_data or {}
        self.asset_type = (
            context_data.get("asset_type", "server") if context_data else "server"
        )
        self.client_account_id = (
            context_data.get("client_account_id") if context_data else None
        )
        self.engagement_id = context_data.get("engagement_id") if context_data else None


class FieldSimilarityCalculator:
    """Advanced field similarity calculator using multiple algorithms"""

    def __init__(self):
        self.similarity_cache = {}
        self.embedding_service = EmbeddingService()
        self.logger = logger

    async def calculate_similarity(self, field1: str, field2: str) -> float:
        """
        Calculate similarity between two field names.

        Uses caching to improve performance for repeated calculations.
        """
        # Check cache first
        cache_key = f"{field1}:{field2}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        try:
            # Normalize field names
            norm_field1 = field1.lower().strip().replace(" ", "_").replace("-", "_")
            norm_field2 = field2.lower().strip().replace(" ", "_").replace("-", "_")

            if norm_field1 == norm_field2:
                similarity = 1.0
            else:
                # Try embedding similarity first
                if self.embedding_service.ai_available:
                    try:
                        embedding1 = await self.embedding_service.embed_text(field1)
                        embedding2 = await self.embedding_service.embed_text(field2)

                        # Check if embeddings are valid
                        if embedding1 is not None and embedding2 is not None:
                            cosine_sim = (
                                self.embedding_service.calculate_cosine_similarity(
                                    embedding1, embedding2
                                )
                            )
                            # Additional check for valid cosine similarity result
                            if cosine_sim is not None and not (
                                isinstance(cosine_sim, float)
                                and (cosine_sim != cosine_sim)
                            ):  # NaN check
                                similarity = (
                                    cosine_sim + 1.0
                                ) / 2.0  # Normalize to 0-1
                            else:
                                # Fall back to fuzzy matching if cosine similarity is invalid
                                similarity = difflib.SequenceMatcher(
                                    None, norm_field1, norm_field2
                                ).ratio()
                        else:
                            # Fall back to fuzzy matching if embeddings are None
                            similarity = difflib.SequenceMatcher(
                                None, norm_field1, norm_field2
                            ).ratio()
                    except Exception as e:
                        logger.warning(
                            f"Embedding calculation failed: {e}. Falling back to fuzzy matching."
                        )
                        # Fall back to fuzzy matching if embedding process fails
                        similarity = difflib.SequenceMatcher(
                            None, norm_field1, norm_field2
                        ).ratio()
                else:
                    # Fall back to fuzzy string matching
                    similarity = difflib.SequenceMatcher(
                        None, norm_field1, norm_field2
                    ).ratio()

            # Cache the result
            self.similarity_cache[cache_key] = similarity
            return similarity

        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0


class StandardFieldRegistry:
    """Registry of standard field names and their variations"""

    def __init__(self):
        self.standard_fields = {
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
            "technology_stack": [
                "tech_stack",
                "technologies",
                "stack",
                "platform_stack",
            ],
            "data_classification": ["classification", "sensitivity", "data_class"],
            "compliance_requirements": ["compliance", "regulations", "standards"],
            "cost_center": ["cost_centre", "billing_code", "charge_code"],
            "location": ["site", "datacenter", "region", "availability_zone"],
            "backup_schedule": ["backup_policy", "backup_freq", "backup_time"],
            "maintenance_window": ["maint_window", "maintenance_schedule"],
        }

        # Create reverse mapping for efficient lookup
        self.field_variations = {}
        for standard_field, variations in self.standard_fields.items():
            self.field_variations[standard_field] = standard_field
            for variation in variations:
                self.field_variations[variation] = standard_field

    def get_standard_field(self, field_name: str) -> Optional[str]:
        """Get the standard field name for a given field variation"""
        normalized = field_name.lower().strip().replace(" ", "_").replace("-", "_")
        return self.field_variations.get(normalized)

    def get_variations(self, standard_field: str) -> List[str]:
        """Get all variations for a standard field"""
        return self.standard_fields.get(standard_field, [])

    def is_standard_field(self, field_name: str) -> bool:
        """Check if a field name is a known standard field or variation"""
        return self.get_standard_field(field_name) is not None

    def get_all_standard_fields(self) -> List[str]:
        """Get list of all standard field names"""
        return list(self.standard_fields.keys())

    def get_field_suggestions(
        self, field_name: str, threshold: float = 0.6
    ) -> List[str]:
        """Get suggested standard fields based on similarity"""
        suggestions = []
        normalized_input = (
            field_name.lower().strip().replace(" ", "_").replace("-", "_")
        )

        for standard_field in self.standard_fields:
            # Check direct similarity to standard field
            similarity = difflib.SequenceMatcher(
                None, normalized_input, standard_field
            ).ratio()
            if similarity >= threshold:
                suggestions.append((standard_field, similarity))

            # Check similarity to variations
            for variation in self.standard_fields[standard_field]:
                similarity = difflib.SequenceMatcher(
                    None, normalized_input, variation
                ).ratio()
                if similarity >= threshold:
                    suggestions.append((standard_field, similarity))

        # Sort by similarity and remove duplicates
        suggestions = sorted(set(suggestions), key=lambda x: x[1], reverse=True)
        return [field for field, _ in suggestions[:5]]  # Return top 5 suggestions
