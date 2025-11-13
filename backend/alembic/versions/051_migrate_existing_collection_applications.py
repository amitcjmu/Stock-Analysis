"""Migrate existing collection applications to canonical system

Revision ID: 051_migrate_existing_collection_applications
Revises: 050_add_canonical_application_identity
Create Date: 2025-09-03 03:40:00.000000

This migration populates the canonical application system with existing collection flow applications:
- Creates canonical applications with deduplication
- Creates name variants for fuzzy matching
- Updates collection_flow_applications with canonical references
- Ensures multi-tenant data integrity
"""

from alembic import op
from sqlalchemy import text
import logging
import hashlib
import re

# revision identifiers, used by Alembic.
revision = "051_migrate_existing_collection_applications"
down_revision = "050_add_canonical_application_identity"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    if not name:
        return ""
    normalized = name.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s\-_.]", "", normalized)
    return normalized.strip()


def generate_name_hash(normalized_name: str) -> str:
    if not normalized_name:
        return ""
    return hashlib.sha256(normalized_name.encode("utf-8")).hexdigest()


def _get_existing_applications(conn):
    """Fetch all existing applications with unique names."""
    existing_apps_query = text(
        """
        SELECT DISTINCT application_name,
            COALESCE(client_account_id, (
                SELECT cf.client_account_id
                FROM migration.collection_flows cf
                WHERE cf.id = cfa.collection_flow_id LIMIT 1
            )) as client_account_id,
            COALESCE(engagement_id, (
                SELECT cf.engagement_id
                FROM migration.collection_flows cf
                WHERE cf.id = cfa.collection_flow_id LIMIT 1
            )) as engagement_id
        FROM migration.collection_flow_applications cfa
        WHERE application_name IS NOT NULL AND application_name != ''
        ORDER BY application_name
    """
    )

    existing_apps_result = conn.execute(existing_apps_query)
    return existing_apps_result.fetchall()


def _create_canonical_applications(conn, existing_apps):
    """Create canonical applications with deduplication."""
    canonical_mapping = {}
    processed_count = 0
    created_count = 0

    for app_row in existing_apps:
        app_name = app_row.application_name
        client_account_id = app_row.client_account_id
        engagement_id = app_row.engagement_id

        if not app_name or not client_account_id or not engagement_id:
            continue

        normalized_name = normalize_name(app_name)
        name_hash = generate_name_hash(normalized_name)

        if not normalized_name:
            continue

        mapping_key = (str(client_account_id), str(engagement_id), normalized_name)

        if mapping_key not in canonical_mapping:
            # Check if canonical application already exists in database
            check_existing = text(
                """
                SELECT id FROM migration.canonical_applications
                WHERE client_account_id = :client_account_id
                AND engagement_id = :engagement_id
                AND normalized_name = :normalized_name
                """
            )

            existing_result = conn.execute(
                check_existing,
                {
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                    "normalized_name": normalized_name,
                },
            )

            existing_row = existing_result.fetchone()

            if existing_row:
                # Use existing canonical application
                canonical_mapping[mapping_key] = existing_row.id
            else:
                # Create new canonical application
                insert_canonical = text(
                    """
                    INSERT INTO migration.canonical_applications (
                        id, canonical_name, normalized_name, name_hash,
                        client_account_id, engagement_id,
                        confidence_score, is_verified, verification_source,
                        usage_count, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :canonical_name, :normalized_name, :name_hash,
                        :client_account_id, :engagement_id,
                        1.0, false, 'bulk_migration',
                        1, now(), now()
                    ) RETURNING id
                    """
                )

                result = conn.execute(
                    insert_canonical,
                    {
                        "canonical_name": app_name.strip(),
                        "normalized_name": normalized_name,
                        "name_hash": name_hash,
                        "client_account_id": client_account_id,
                        "engagement_id": engagement_id,
                    },
                )

                canonical_id = result.scalar()
                canonical_mapping[mapping_key] = canonical_id
                created_count += 1

        processed_count += 1

    return canonical_mapping, created_count


def _create_name_variants(conn, existing_apps, canonical_mapping):
    """Create name variants for non-exact matches."""
    variant_count = 0

    for app_row in existing_apps:
        app_name = app_row.application_name
        client_account_id = app_row.client_account_id
        engagement_id = app_row.engagement_id

        if not app_name or not client_account_id or not engagement_id:
            continue

        normalized_name = normalize_name(app_name)
        if not normalized_name:
            continue

        mapping_key = (str(client_account_id), str(engagement_id), normalized_name)
        canonical_id = canonical_mapping.get(mapping_key)

        if not canonical_id:
            continue

        # Get the canonical name for comparison
        canonical_name_query = text(
            "SELECT canonical_name FROM migration.canonical_applications WHERE id = :canonical_id"
        )
        canonical_name_result = conn.execute(
            canonical_name_query, {"canonical_id": canonical_id}
        )
        canonical_name_row = canonical_name_result.fetchone()

        if not canonical_name_row:
            continue

        canonical_name = canonical_name_row.canonical_name

        # Create variant only if the original name differs from canonical name
        if app_name.strip() != canonical_name:
            variant_count += _create_single_variant(
                conn, app_name, canonical_id, client_account_id, engagement_id
            )

    return variant_count


def _create_single_variant(
    conn, app_name, canonical_id, client_account_id, engagement_id
):
    """Create a single name variant if it doesn't exist."""
    variant_normalized = normalize_name(app_name)
    variant_hash = generate_name_hash(variant_normalized)

    # Check if variant already exists
    existing_variant_query = text(
        """
        SELECT id FROM migration.application_name_variants
        WHERE client_account_id = :client_account_id
        AND engagement_id = :engagement_id
        AND variant_hash = :variant_hash
    """
    )

    existing_variant_result = conn.execute(
        existing_variant_query,
        {
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "variant_hash": variant_hash,
        },
    )

    if existing_variant_result.fetchone():
        return 0  # Variant already exists

    # Create new variant
    insert_variant = text(
        """
        INSERT INTO migration.application_name_variants (
            id, canonical_application_id, variant_name,
            normalized_variant, variant_hash,
            client_account_id, engagement_id,
            similarity_score, match_method, match_confidence,
            usage_count, first_seen_at, last_used_at
        ) VALUES (
            gen_random_uuid(), :canonical_application_id,
            :variant_name, :normalized_variant, :variant_hash,
            :client_account_id, :engagement_id,
            1.0, 'bulk_migration', 1.0,
            1, now(), now()
        )
    """
    )

    conn.execute(
        insert_variant,
        {
            "canonical_application_id": canonical_id,
            "variant_name": app_name.strip(),
            "normalized_variant": variant_normalized,
            "variant_hash": variant_hash,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
        },
    )

    return 1  # Variant created


def _update_tenant_fields(conn):
    """Update tenant fields for collection flow applications."""
    update_tenant_fields = text(
        """
        UPDATE migration.collection_flow_applications
        SET
            client_account_id = COALESCE(collection_flow_applications.client_account_id, cf.client_account_id),
            engagement_id = COALESCE(collection_flow_applications.engagement_id, cf.engagement_id)
        FROM migration.collection_flows cf
        WHERE collection_flow_applications.collection_flow_id = cf.id
        AND (collection_flow_applications.client_account_id IS NULL
             OR collection_flow_applications.engagement_id IS NULL)
    """
    )

    tenant_update_result = conn.execute(update_tenant_fields)
    return tenant_update_result.rowcount


def _update_collection_flow_applications(conn, canonical_mapping):
    """Update collection flow applications with canonical references."""
    # Get all collection flow applications that need updating
    apps_to_update_query = text(
        """
        SELECT id, application_name, client_account_id, engagement_id
        FROM migration.collection_flow_applications
        WHERE canonical_application_id IS NULL
        AND application_name IS NOT NULL
        AND application_name != ''
        AND client_account_id IS NOT NULL
        AND engagement_id IS NOT NULL
    """
    )

    apps_to_update_result = conn.execute(apps_to_update_query)
    apps_to_update = apps_to_update_result.fetchall()

    update_count = 0

    for app_row in apps_to_update:
        update_count += _update_single_application(conn, app_row, canonical_mapping)

    return update_count


def _update_single_application(conn, app_row, canonical_mapping):
    """Update a single collection flow application with canonical reference."""
    cfa_id = app_row.id
    app_name = app_row.application_name
    client_account_id = app_row.client_account_id
    engagement_id = app_row.engagement_id

    normalized_name = normalize_name(app_name)
    mapping_key = (str(client_account_id), str(engagement_id), normalized_name)
    canonical_id = canonical_mapping.get(mapping_key)

    if not canonical_id:
        return 0

    # Find matching variant if application name differs from canonical name
    variant_id = _find_variant_id(
        conn, canonical_id, app_name, client_account_id, engagement_id
    )

    # Update the collection flow application
    update_cfa = text(
        """
        UPDATE migration.collection_flow_applications
        SET
            canonical_application_id = :canonical_id,
            name_variant_id = :variant_id,
            deduplication_method = 'bulk_migration',
            match_confidence = 1.0
        WHERE id = :cfa_id
    """
    )

    conn.execute(
        update_cfa,
        {
            "canonical_id": canonical_id,
            "variant_id": variant_id,
            "cfa_id": cfa_id,
        },
    )

    return 1


def _find_variant_id(conn, canonical_id, app_name, client_account_id, engagement_id):
    """Find matching variant ID if application name differs from canonical name."""
    # Get canonical name
    canonical_name_query = text(
        "SELECT canonical_name FROM migration.canonical_applications WHERE id = :canonical_id"
    )
    canonical_name_result = conn.execute(
        canonical_name_query, {"canonical_id": canonical_id}
    )
    canonical_name_row = canonical_name_result.fetchone()

    if not canonical_name_row or canonical_name_row.canonical_name == app_name.strip():
        return None

    # Find the variant
    variant_query = text(
        """
        SELECT id FROM migration.application_name_variants
        WHERE canonical_application_id = :canonical_id
        AND variant_name = :variant_name
        AND client_account_id = :client_account_id
        AND engagement_id = :engagement_id
    """
    )

    variant_result = conn.execute(
        variant_query,
        {
            "canonical_id": canonical_id,
            "variant_name": app_name.strip(),
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
        },
    )
    variant_row = variant_result.fetchone()

    return variant_row.id if variant_row else None


def _update_usage_statistics(conn):
    """Update usage statistics for canonical applications."""
    usage_update = text(
        """
        WITH usage_stats AS (
            SELECT
                canonical_application_id,
                COUNT(*) as usage_count,
                MAX(cfa.created_at) as last_used_at
            FROM migration.collection_flow_applications cfa
            WHERE canonical_application_id IS NOT NULL
            GROUP BY canonical_application_id
        )
        UPDATE migration.canonical_applications ca
        SET
            usage_count = us.usage_count,
            last_used_at = us.last_used_at,
            updated_at = now()
        FROM usage_stats us
        WHERE ca.id = us.canonical_application_id
    """
    )

    usage_result = conn.execute(usage_update)
    return usage_result.rowcount


def upgrade() -> None:
    """Migrate existing collection flow applications to canonical system"""
    conn = op.get_bind()
    logger.info("Starting migration of collection flow applications")

    try:
        # Step 1: Get all existing applications
        existing_apps = _get_existing_applications(conn)
        if not existing_apps:
            logger.info("No existing applications found - skipping migration")
            return

        logger.info(f"Found {len(existing_apps)} unique applications")

        # Step 2: Create canonical applications with deduplication
        canonical_mapping, created_count = _create_canonical_applications(
            conn, existing_apps
        )
        logger.info(f"Created {created_count} canonical applications")

        # Step 3: Create name variants for non-exact matches
        variant_count = _create_name_variants(conn, existing_apps, canonical_mapping)
        logger.info(f"Created {variant_count} name variants")

        # Step 4: Update tenant fields
        tenant_update_count = _update_tenant_fields(conn)
        logger.info(f"Updated tenant fields for {tenant_update_count} applications")

        # Step 5: Update collection flow applications with canonical references
        update_count = _update_collection_flow_applications(conn, canonical_mapping)
        logger.info(f"Updated {update_count} collection flow applications")

        # Step 6: Update usage statistics
        usage_update_count = _update_usage_statistics(conn)
        logger.info(f"Updated usage statistics for {usage_update_count} applications")

        logger.info("✅ Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


def downgrade() -> None:
    """Remove canonical application references and revert to legacy system"""

    conn = op.get_bind()

    try:
        # Clear canonical application references
        clear_canonical_refs = text(
            """
            UPDATE migration.collection_flow_applications
            SET
                canonical_application_id = NULL,
                name_variant_id = NULL,
                deduplication_method = NULL,
                match_confidence = NULL
        """
        )
        conn.execute(clear_canonical_refs)

        # Remove application name variants
        conn.execute(text("DELETE FROM migration.application_name_variants"))

        # Remove canonical applications
        conn.execute(text("DELETE FROM migration.canonical_applications"))

        logger.info("✅ Downgrade completed successfully")

    except Exception as e:
        logger.error(f"❌ Downgrade failed: {str(e)}")
        raise
