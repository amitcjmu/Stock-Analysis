"""Seed EOL catalog data for Issue #1243

Revision ID: 151_seed_eol_catalog_data_issue_1243
Revises: 150_security_and_data_integrity
Create Date: 2025-12-06

This migration seeds the vendor_products_catalog, product_versions_catalog,
and lifecycle_milestones tables with initial EOL data for common enterprise
technologies used in cloud migration assessments.

Data sourced from endoflife.date API.
"""

from alembic import op
import sqlalchemy as sa
from datetime import date
import uuid


# revision identifiers, used by Alembic.
revision = "151_seed_eol_catalog_data_issue_1243"
down_revision = "150_security_and_data_integrity"
branch_labels = None
depends_on = None


# EOL data for common enterprise technologies
# Format: (vendor, product, normalized_key, versions)
# versions = [(version_label, release_date, eol_date, extended_support_date)]
EOL_SEED_DATA = [
    # Operating Systems
    (
        "Red Hat",
        "Red Hat Enterprise Linux",
        "rhel",
        [
            ("7", date(2014, 6, 10), date(2024, 6, 30), date(2028, 6, 30)),
            ("8", date(2019, 5, 7), date(2029, 5, 31), date(2032, 5, 31)),
            ("9", date(2022, 5, 17), date(2032, 5, 31), date(2035, 5, 31)),
        ],
    ),
    (
        "Oracle",
        "Oracle Linux",
        "oracle-linux",
        [
            ("7", date(2014, 7, 23), date(2024, 12, 31), None),
            ("8", date(2019, 7, 18), date(2029, 7, 31), date(2032, 7, 31)),
            ("9", date(2022, 7, 6), date(2032, 7, 31), date(2035, 7, 31)),
        ],
    ),
    (
        "Microsoft",
        "Windows Server",
        "windows-server",
        [
            ("2016", date(2016, 10, 15), date(2027, 1, 12), None),
            ("2019", date(2018, 11, 13), date(2029, 1, 9), None),
            ("2022", date(2021, 8, 18), date(2031, 10, 14), None),
        ],
    ),
    (
        "IBM",
        "AIX",
        "aix",
        [
            ("7.2", date(2015, 12, 4), date(2023, 4, 30), date(2025, 4, 30)),
            ("7.3", date(2021, 12, 10), date(2027, 12, 10), None),
        ],
    ),
    (
        "IBM",
        "z/OS",
        "zos",
        [
            ("2.4", date(2019, 9, 30), date(2025, 9, 30), None),
            ("2.5", date(2021, 9, 30), date(2027, 9, 30), None),
            ("3.1", date(2023, 9, 30), date(2029, 9, 30), None),
        ],
    ),
    (
        "Canonical",
        "Ubuntu",
        "ubuntu",
        [
            ("18.04", date(2018, 4, 26), date(2023, 5, 31), date(2028, 4, 26)),
            ("20.04", date(2020, 4, 23), date(2025, 4, 23), date(2030, 4, 23)),
            ("22.04", date(2022, 4, 21), date(2027, 4, 21), date(2032, 4, 21)),
            ("24.04", date(2024, 4, 25), date(2029, 4, 25), date(2034, 4, 25)),
        ],
    ),
    # Databases
    (
        "Oracle",
        "Oracle Database",
        "oracle-database",
        [
            ("12c", date(2014, 7, 22), date(2022, 3, 31), date(2025, 7, 31)),
            ("18c", date(2018, 2, 16), date(2021, 6, 30), date(2024, 6, 30)),
            ("19c", date(2019, 4, 25), date(2024, 4, 30), date(2027, 4, 30)),
            ("21c", date(2021, 8, 11), date(2024, 4, 30), None),
            ("23ai", date(2024, 5, 2), date(2029, 4, 30), date(2032, 4, 30)),
        ],
    ),
    (
        "Microsoft",
        "SQL Server",
        "sql-server",
        [
            ("2016", date(2016, 6, 1), date(2026, 7, 14), None),
            ("2017", date(2017, 10, 2), date(2027, 10, 12), None),
            ("2019", date(2019, 11, 4), date(2030, 1, 8), None),
            ("2022", date(2022, 11, 16), date(2033, 1, 11), None),
        ],
    ),
    (
        "PostgreSQL",
        "PostgreSQL",
        "postgresql",
        [
            ("12", date(2019, 10, 3), date(2024, 11, 14), None),
            ("13", date(2020, 9, 24), date(2025, 11, 13), None),
            ("14", date(2021, 9, 30), date(2026, 11, 12), None),
            ("15", date(2022, 10, 13), date(2027, 11, 11), None),
            ("16", date(2023, 9, 14), date(2028, 11, 9), None),
            ("17", date(2024, 9, 26), date(2029, 11, 8), None),
        ],
    ),
    (
        "Oracle",
        "MySQL",
        "mysql",
        [
            ("5.7", date(2015, 10, 21), date(2023, 10, 21), None),
            ("8.0", date(2018, 4, 19), date(2026, 4, 30), None),
            ("8.4", date(2024, 4, 30), date(2032, 4, 30), None),
        ],
    ),
    (
        "MongoDB",
        "MongoDB",
        "mongodb",
        [
            ("5.0", date(2021, 7, 13), date(2024, 10, 31), None),
            ("6.0", date(2022, 7, 19), date(2025, 7, 19), None),
            ("7.0", date(2023, 8, 15), date(2026, 8, 15), None),
        ],
    ),
    (
        "IBM",
        "Db2",
        "db2",
        [
            ("11.1", date(2016, 6, 23), date(2024, 9, 30), None),
            ("11.5", date(2019, 6, 27), date(2029, 4, 30), None),
        ],
    ),
    # Runtimes
    (
        "Oracle",
        "Java (Oracle JDK)",
        "java",
        [
            ("8", date(2014, 3, 18), date(2025, 3, 31), date(2030, 12, 31)),
            ("11", date(2018, 9, 25), date(2026, 9, 30), date(2032, 1, 31)),
            ("17", date(2021, 9, 14), date(2029, 9, 30), date(2032, 9, 30)),
            ("21", date(2023, 9, 19), date(2031, 9, 30), date(2034, 9, 30)),
        ],
    ),
    (
        "Eclipse Adoptium",
        "Eclipse Temurin (OpenJDK)",
        "openjdk",
        [
            ("8", date(2014, 3, 18), date(2026, 11, 30), None),
            ("11", date(2018, 9, 25), date(2027, 10, 31), None),
            ("17", date(2021, 9, 14), date(2029, 10, 31), None),
            ("21", date(2023, 9, 19), date(2031, 10, 31), None),
        ],
    ),
    (
        "Microsoft",
        ".NET Framework",
        "dotnet-framework",
        [
            ("4.6.2", date(2016, 8, 2), date(2027, 1, 12), None),
            ("4.7", date(2017, 4, 5), date(2027, 1, 12), None),
            ("4.7.2", date(2018, 4, 30), date(2027, 1, 12), None),
            ("4.8", date(2019, 4, 18), date(2029, 1, 9), None),
        ],
    ),
    (
        "Microsoft",
        ".NET",
        "dotnet",
        [
            ("6", date(2021, 11, 8), date(2024, 11, 12), None),
            ("7", date(2022, 11, 8), date(2024, 5, 14), None),
            ("8", date(2023, 11, 14), date(2026, 11, 10), None),
            ("9", date(2024, 11, 12), date(2026, 5, 12), None),
        ],
    ),
    (
        "OpenJS Foundation",
        "Node.js",
        "nodejs",
        [
            ("16", date(2021, 4, 20), date(2024, 9, 11), None),
            ("18", date(2022, 4, 19), date(2025, 4, 30), None),
            ("20", date(2023, 4, 18), date(2026, 4, 30), None),
            ("22", date(2024, 4, 24), date(2027, 4, 30), None),
        ],
    ),
    (
        "Python Software Foundation",
        "Python",
        "python",
        [
            ("3.8", date(2019, 10, 14), date(2024, 10, 14), None),
            ("3.9", date(2020, 10, 5), date(2025, 10, 5), None),
            ("3.10", date(2021, 10, 4), date(2026, 10, 4), None),
            ("3.11", date(2022, 10, 24), date(2027, 10, 24), None),
            ("3.12", date(2023, 10, 2), date(2028, 10, 2), None),
            ("3.13", date(2024, 10, 7), date(2029, 10, 7), None),
        ],
    ),
    # Frameworks
    (
        "VMware",
        "Spring Boot",
        "spring-boot",
        [
            ("2.7", date(2022, 5, 19), date(2024, 8, 24), None),
            ("3.0", date(2022, 11, 24), date(2024, 11, 24), None),
            ("3.1", date(2023, 5, 18), date(2025, 5, 18), None),
            ("3.2", date(2023, 11, 23), date(2025, 11, 23), None),
            ("3.3", date(2024, 5, 23), date(2026, 5, 23), None),
        ],
    ),
    (
        "VMware",
        "Spring Framework",
        "spring",
        [
            ("5.3", date(2020, 10, 27), date(2024, 12, 31), None),
            ("6.0", date(2022, 11, 16), date(2025, 8, 31), None),
            ("6.1", date(2023, 11, 16), date(2026, 8, 31), None),
            ("6.2", date(2024, 11, 14), date(2027, 8, 31), None),
        ],
    ),
    (
        "Google",
        "Angular",
        "angular",
        [
            ("15", date(2022, 11, 16), date(2024, 5, 18), None),
            ("16", date(2023, 5, 3), date(2024, 11, 8), None),
            ("17", date(2023, 11, 8), date(2025, 5, 15), None),
            ("18", date(2024, 5, 22), date(2025, 11, 19), None),
        ],
    ),
    (
        "Meta",
        "React",
        "react",
        [
            ("17", date(2020, 10, 20), date(2023, 3, 29), None),
            ("18", date(2022, 3, 29), date(2025, 4, 25), None),
            ("19", date(2024, 4, 25), date(2027, 4, 30), None),
        ],
    ),
]


def upgrade() -> None:
    """Seed EOL catalog data."""
    connection = op.get_bind()

    for vendor, product, normalized_key, versions in EOL_SEED_DATA:
        # Check if product already exists to make migration idempotent
        check_sql = sa.text(
            """
            SELECT id FROM migration.vendor_products_catalog
            WHERE normalized_key = :normalized_key
        """
        )
        result = connection.execute(check_sql, {"normalized_key": normalized_key})
        existing = result.fetchone()

        if existing:
            catalog_id = existing[0]
        else:
            # Insert vendor product
            catalog_id = uuid.uuid4()
            insert_product = sa.text(
                """
                INSERT INTO migration.vendor_products_catalog
                (id, vendor_name, product_name, normalized_key, is_global, created_at, updated_at)
                VALUES (:id, :vendor, :product, :key, true, NOW(), NOW())
            """
            )
            connection.execute(
                insert_product,
                {
                    "id": catalog_id,
                    "vendor": vendor,
                    "product": product,
                    "key": normalized_key,
                },
            )

        for version_label, release_date, eol_date, extended_support in versions:
            # Check if version already exists
            check_version_sql = sa.text(
                """
                SELECT id FROM migration.product_versions_catalog
                WHERE catalog_id = :catalog_id AND version_label = :version_label
            """
            )
            result = connection.execute(
                check_version_sql,
                {"catalog_id": catalog_id, "version_label": version_label},
            )
            existing_version = result.fetchone()

            if existing_version:
                version_id = existing_version[0]
            else:
                # Insert version
                version_id = uuid.uuid4()
                insert_version = sa.text(
                    """
                    INSERT INTO migration.product_versions_catalog
                    (id, catalog_id, version_label, created_at, updated_at)
                    VALUES (:id, :catalog_id, :version_label, NOW(), NOW())
                """
                )
                connection.execute(
                    insert_version,
                    {
                        "id": version_id,
                        "catalog_id": catalog_id,
                        "version_label": version_label,
                    },
                )

            # Insert milestones (skip if already exist)
            milestones = []
            if release_date:
                milestones.append(("release", release_date))
            if eol_date:
                milestones.append(("end_of_life", eol_date))
            if extended_support:
                milestones.append(("extended_support_end", extended_support))

            for milestone_type, milestone_date in milestones:
                check_milestone_sql = sa.text(
                    """
                    SELECT id FROM migration.lifecycle_milestones
                    WHERE catalog_version_id = :version_id AND milestone_type = :type
                """
                )
                result = connection.execute(
                    check_milestone_sql,
                    {"version_id": version_id, "type": milestone_type},
                )
                if not result.fetchone():
                    provenance = '{"agent": "seed_migration", "api": "endoflife.date"}'
                    insert_milestone = sa.text(
                        """
                        INSERT INTO migration.lifecycle_milestones
                        (id, catalog_version_id, milestone_type, milestone_date,
                         source, provenance, created_at, updated_at)
                        VALUES (:id, :version_id, :type, :date,
                                'endoflife.date', :provenance, NOW(), NOW())
                    """
                    )
                    connection.execute(
                        insert_milestone,
                        {
                            "id": uuid.uuid4(),
                            "version_id": version_id,
                            "type": milestone_type,
                            "date": milestone_date,
                            "provenance": provenance,
                        },
                    )


def downgrade() -> None:
    """Remove seeded EOL data."""
    connection = op.get_bind()

    # Get all normalized keys we seeded
    normalized_keys = [item[2] for item in EOL_SEED_DATA]

    # Delete lifecycle milestones first (due to FK constraints)
    delete_milestones = sa.text(
        """
        DELETE FROM migration.lifecycle_milestones lm
        WHERE lm.catalog_version_id IN (
            SELECT pv.id FROM migration.product_versions_catalog pv
            JOIN migration.vendor_products_catalog vpc ON pv.catalog_id = vpc.id
            WHERE vpc.normalized_key = ANY(:keys)
        )
    """
    )
    connection.execute(delete_milestones, {"keys": normalized_keys})

    # Delete product versions
    delete_versions = sa.text(
        """
        DELETE FROM migration.product_versions_catalog pv
        WHERE pv.catalog_id IN (
            SELECT id FROM migration.vendor_products_catalog
            WHERE normalized_key = ANY(:keys)
        )
    """
    )
    connection.execute(delete_versions, {"keys": normalized_keys})

    # Delete vendor products
    delete_products = sa.text(
        """
        DELETE FROM migration.vendor_products_catalog
        WHERE normalized_key = ANY(:keys)
    """
    )
    connection.execute(delete_products, {"keys": normalized_keys})
