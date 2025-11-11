"""
Helper functions for per-asset, per-section questionnaire generation.

Per ADR-035: Supporting functions for batched generation with Redis caching.
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def filter_gaps_by_section(gaps: List[str], section_id: str) -> List[str]:
    """
    Filter gaps relevant to assessment flow section.

    Per ADR-035: Map gaps to sections based on Issue #980 architecture.

    Args:
        gaps: List of gap field names (e.g., ["operating_system", "backup_frequency"])
        section_id: Assessment flow section (infrastructure, resilience, compliance, dependencies, tech_debt)

    Returns:
        List of gaps relevant to this section
    """
    # Per ADR-035: Section-to-gap mapping aligned with Issue #980
    section_gap_mapping = {
        "infrastructure": [
            # Column gaps: Hardware, OS, network
            "operating_system",
            "os_version",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "network_bandwidth",
            "virtualization_platform",
            "hostname",
            "ip_address",
            "datacenter_location",
        ],
        "resilience": [
            # Enrichment gaps: resilience table
            "high_availability_config",
            "disaster_recovery_plan",
            "backup_frequency",
            "backup_retention",
            "rto",
            "rpo",
            "failover_capability",
            "redundancy_level",
            "clustering_enabled",
        ],
        "compliance": [
            # Standards gaps + enrichment gaps: compliance_flags table
            "compliance_scopes",
            "data_classification",
            "encryption_at_rest",
            "encryption_in_transit",
            "access_controls",
            "audit_logging",
            "gdpr_compliance",
            "hipaa_compliance",
            "pci_dss_compliance",
            "security_certifications",
        ],
        "dependencies": [
            # Enrichment gaps: dependencies table
            "integration_points",
            "api_dependencies",
            "external_services",
            "data_sources",
            "downstream_consumers",
            "upstream_dependencies",
            "service_mesh_integration",
        ],
        "tech_debt": [
            # JSONB gaps: technical_details field
            "code_quality_score",
            "technical_debt_score",
            "security_vulnerabilities",
            "eol_technology_assessment",
            "modernization_readiness",
            "architecture_pattern",
            "test_coverage",
            "documentation_quality",
        ],
    }

    section_fields = section_gap_mapping.get(section_id, [])
    filtered = [gap for gap in gaps if gap in section_fields]

    logger.debug(
        f"Section {section_id}: {len(filtered)}/{len(gaps)} gaps filtered "
        f"({', '.join(filtered) if filtered else 'none'})"
    )

    return filtered


def get_section_title(section_id: str) -> str:
    """Get section title for aggregation."""
    titles = {
        "infrastructure": "Infrastructure Specifications",
        "resilience": "Resilience & Availability",
        "compliance": "Compliance & Security Standards",
        "dependencies": "Dependencies & Integrations",
        "tech_debt": "Technical Debt Assessment",
    }
    return titles.get(section_id, section_id.replace("_", " ").title())


def get_section_description(section_id: str) -> str:
    """Get section description for aggregation."""
    descriptions = {
        "infrastructure": "Hardware, operating system, and network infrastructure details",
        "resilience": "High availability, disaster recovery, and backup configurations",
        "compliance": "Regulatory compliance (GDPR, HIPAA, PCI-DSS) and security standards",
        "dependencies": "System dependencies, integrations, and API connections",
        "tech_debt": "Code quality, security vulnerabilities, and modernization readiness",
    }
    return descriptions.get(section_id, "")


async def store_section_in_redis(
    redis,
    flow_id: str,
    asset_id: UUID,
    section_id: str,
    section_data: dict,
    ttl: int = 3600,
) -> None:
    """
    Store section data in Redis cache.

    Per ADR-035: Cache intermediate results for aggregation.

    Args:
        redis: RedisConnectionManager instance
        flow_id: Collection flow ID
        asset_id: Asset UUID
        section_id: Section identifier (infrastructure, resilience, etc.)
        section_data: Section JSON data from agent
        ttl: Time-to-live in seconds (default: 1 hour)
    """
    cache_key = f"questionnaire:{flow_id}:{asset_id}:{section_id}"

    try:
        await redis.set(
            cache_key,
            json.dumps(section_data),
            ex=ttl,
        )
        logger.debug(f"Cached section: {cache_key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Failed to cache section {cache_key}: {e}")
        # Non-fatal: Continue without caching
        pass


async def retrieve_section_from_redis(
    redis,
    flow_id: str,
    asset_id: UUID,
    section_id: str,
) -> Optional[dict]:
    """
    Retrieve section data from Redis cache.

    Args:
        redis: RedisConnectionManager instance
        flow_id: Collection flow ID
        asset_id: Asset UUID
        section_id: Section identifier

    Returns:
        Section data dict if cached, None otherwise
    """
    cache_key = f"questionnaire:{flow_id}:{asset_id}:{section_id}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT: {cache_key}")
            return json.loads(cached)
        else:
            logger.debug(f"Cache MISS: {cache_key}")
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve cached section {cache_key}: {e}")
        return None


async def aggregate_sections_from_redis(
    redis,
    flow_id: str,
    asset_ids: List[UUID],
    sections: List[str],
) -> List[dict]:
    """
    Aggregate questionnaire sections from Redis cache.

    Per ADR-035: Retrieve all cached sections and organize by section type.

    Args:
        redis: RedisConnectionManager instance
        flow_id: Collection flow ID
        asset_ids: List of asset UUIDs
        sections: List of section IDs (infrastructure, resilience, etc.)

    Returns:
        List of section dicts with aggregated questions
    """
    aggregated_sections = []

    for section_id in sections:
        section_questions = []

        for asset_id in asset_ids:
            cached_section = await retrieve_section_from_redis(
                redis, flow_id, asset_id, section_id
            )

            if cached_section:
                # Extract questions from cached section
                questions = cached_section.get("questions", [])
                section_questions.extend(questions)

                logger.debug(
                    f"Aggregated {len(questions)} questions from "
                    f"{asset_id}/{section_id}"
                )

        # Only create section if it has questions
        if section_questions:
            aggregated_sections.append(
                {
                    "section_id": f"section_{section_id}",
                    "section_title": get_section_title(section_id),
                    "section_description": get_section_description(section_id),
                    "questions": section_questions,
                    "category": section_id,  # Per ADR-035: For deduplication
                }
            )

            logger.info(
                f"Section {section_id}: {len(section_questions)} questions aggregated"
            )

    logger.info(
        f"Aggregated {len(aggregated_sections)} sections from Redis "
        f"(total questions: {sum(len(s['questions']) for s in aggregated_sections)})"
    )

    return aggregated_sections


async def cleanup_redis_cache(
    redis,
    flow_id: str,
    asset_ids: List[UUID],
    sections: List[str],
) -> None:
    """
    Clean up Redis cache entries for completed flow.

    Args:
        redis: RedisConnectionManager instance
        flow_id: Collection flow ID
        asset_ids: List of asset UUIDs
        sections: List of section IDs
    """
    deleted_count = 0

    try:
        for asset_id in asset_ids:
            for section_id in sections:
                cache_key = f"questionnaire:{flow_id}:{asset_id}:{section_id}"
                deleted = await redis.delete(cache_key)
                if deleted:
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} cached sections for flow {flow_id}")
    except Exception as e:
        logger.error(f"Failed to cleanup Redis cache for flow {flow_id}: {e}")
        # Non-fatal: Cache will expire via TTL


def get_section_title_from_id(section_id: str) -> str:
    """Extract section title from section_id (e.g., 'section_infrastructure' -> 'Infrastructure Specifications')."""
    # Remove 'section_' prefix if present
    clean_id = section_id.replace("section_", "")
    return get_section_title(clean_id)


def get_section_description_from_id(section_id: str) -> str:
    """Extract section description from section_id."""
    clean_id = section_id.replace("section_", "")
    return get_section_description(clean_id)
