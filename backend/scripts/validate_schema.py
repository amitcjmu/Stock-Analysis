#!/usr/bin/env python3
"""
Schema validation script for database consolidation
Ensures the consolidated schema is correctly created
"""

import os
import sys

from sqlalchemy import create_engine, inspect

# Database connection from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/migration_db"
)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Expected tables in consolidated schema
EXPECTED_TABLES = {
    # Core multi-tenant
    "client_accounts",
    "users",
    "engagements",
    "user_account_associations",
    # Master orchestration
    "crewai_flow_state_extensions",
    # Discovery phase
    "data_imports",
    "data_import_sessions",
    "discovery_flows",
    "import_field_mappings",
    "raw_import_records",
    "assets",
    "asset_dependencies",
    # Assessment phase
    "migrations",
    "migration_waves",
    "cmdb_sixr_analyses",
    # Supporting
    "security_audit_logs",
    "access_audit_log",
    "llm_usage_tracking",
    "user_feedback",
}

# Tables that should NOT exist
DEPRECATED_TABLES = {
    # V3 tables
    "v3_data_imports",
    "v3_discovery_flows",
    "v3_field_mappings",
    "v3_raw_import_records",
    # Other deprecated tables
    "workflow_states",
    "discovery_assets",
    "mapping_learning_patterns",
    "data_quality_issues",
    "workflow_progress",
    "import_processing_steps",
}

# Expected enum types
EXPECTED_ENUMS = {
    "asset_type",
    "asset_status",
    "sixr_strategy",
    "import_status",
    "flow_status",
}

# Critical fields that must exist
CRITICAL_FIELDS = {
    "data_imports": {
        "filename",  # NOT source_filename
        "file_size",  # NOT file_size_bytes
        "mime_type",  # NOT file_type
        "master_flow_id",
        "error_message",
        "error_details",
    },
    "discovery_flows": {
        # Boolean flags
        "data_validation_completed",
        "field_mapping_completed",
        "data_cleansing_completed",
        "asset_inventory_completed",
        "dependency_analysis_completed",
        "tech_debt_assessment_completed",
        # JSON fields
        "current_phase",
        "phases_completed",
        "crew_outputs",
        "field_mappings",
        "discovered_assets",
    },
    "assets": {
        "master_flow_id",
        "discovery_flow_id",
        "hostname",
        "ip_address",
        "operating_system",
        "cpu_cores",
        "memory_gb",
        "storage_gb",
    },
}

# Fields that should NOT exist
REMOVED_FIELDS = {
    "is_mock",  # Should not exist in ANY table
    "source_filename",  # Renamed to filename
    "file_size_bytes",  # Renamed to file_size
    "file_type",  # Renamed to mime_type
}


class SchemaValidator:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url.replace("+asyncpg", ""))
        self.inspector = inspect(self.engine)
        self.errors = []
        self.warnings = []

    def validate(self) -> bool:
        """Run all validation checks"""
        print("Starting schema validation...\n")

        # Check tables
        self._check_expected_tables()
        self._check_no_deprecated_tables()

        # Check enums
        self._check_enum_types()

        # Check critical fields
        self._check_critical_fields()

        # Check removed fields
        self._check_removed_fields()

        # Check indexes
        self._check_indexes()

        # Check foreign keys
        self._check_foreign_keys()

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def _check_expected_tables(self):
        """Verify all expected tables exist"""
        print("Checking expected tables...")
        existing_tables = set(self.inspector.get_table_names())

        missing_tables = EXPECTED_TABLES - existing_tables
        if missing_tables:
            self.errors.append(f"Missing expected tables: {sorted(missing_tables)}")
        else:
            print(f"✓ All {len(EXPECTED_TABLES)} expected tables exist")

    def _check_no_deprecated_tables(self):
        """Ensure no deprecated tables exist"""
        print("Checking for deprecated tables...")
        existing_tables = set(self.inspector.get_table_names())

        deprecated_found = existing_tables & DEPRECATED_TABLES
        if deprecated_found:
            self.errors.append(
                f"Deprecated tables still exist: {sorted(deprecated_found)}"
            )
        else:
            print("✓ No deprecated tables found")

    def _check_enum_types(self):
        """Check enum types exist"""
        print("Checking enum types...")
        # Get all enum types from database
        result = self.engine.execute(
            """
            SELECT typname
            FROM pg_type
            WHERE typtype = 'e'
        """
        )
        existing_enums = {row[0] for row in result}

        missing_enums = EXPECTED_ENUMS - existing_enums
        if missing_enums:
            self.warnings.append(f"Missing enum types: {sorted(missing_enums)}")
        else:
            print("✓ All expected enum types exist")

    def _check_critical_fields(self):
        """Verify critical fields exist with correct names"""
        print("Checking critical fields...")

        for table, expected_fields in CRITICAL_FIELDS.items():
            if table not in self.inspector.get_table_names():
                continue

            columns = {col["name"] for col in self.inspector.get_columns(table)}
            missing_fields = expected_fields - columns

            if missing_fields:
                self.errors.append(
                    f"Table '{table}' missing fields: {sorted(missing_fields)}"
                )
            else:
                print(f"✓ Table '{table}' has all critical fields")

    def _check_removed_fields(self):
        """Ensure removed fields don't exist"""
        print("Checking for removed fields...")

        for table in self.inspector.get_table_names():
            columns = {col["name"] for col in self.inspector.get_columns(table)}

            found_removed = columns & REMOVED_FIELDS
            if found_removed:
                self.errors.append(
                    f"Table '{table}' still has removed fields: {sorted(found_removed)}"
                )

        if not any("removed fields" in e for e in self.errors):
            print("✓ No removed fields found in any table")

    def _check_indexes(self):
        """Check for multi-tenant indexes"""
        print("Checking indexes...")

        tables_needing_client_index = [
            "data_imports",
            "discovery_flows",
            "assets",
            "import_field_mappings",
            "raw_import_records",
        ]

        for table in tables_needing_client_index:
            if table not in self.inspector.get_table_names():
                continue

            indexes = self.inspector.get_indexes(table)
            has_client_index = any(
                "client_account_id" in idx.get("column_names", []) for idx in indexes
            )

            if not has_client_index:
                self.warnings.append(f"Table '{table}' missing client_account_id index")

    def _check_foreign_keys(self):
        """Verify foreign key relationships"""
        print("Checking foreign keys...")

        # Check master_flow_id relationships
        tables_with_master_flow = ["data_imports", "discovery_flows", "assets"]

        for table in tables_with_master_flow:
            if table not in self.inspector.get_table_names():
                continue

            fks = self.inspector.get_foreign_keys(table)
            has_master_flow_fk = any(
                "master_flow_id" in fk.get("constrained_columns", []) for fk in fks
            )

            if not has_master_flow_fk:
                self.warnings.append(
                    f"Table '{table}' missing master_flow_id foreign key"
                )

    def _report_results(self):
        """Report validation results"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ Schema validation PASSED! All checks successful.")
        elif not self.errors:
            print("\n✅ Schema validation PASSED with warnings.")
        else:
            print("\n❌ Schema validation FAILED!")

        print("=" * 60)


def main():
    """Main entry point"""
    env = os.getenv("ENV", "development")
    print(f"Validating schema in {env} environment")
    print(
        f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}\n"
    )

    validator = SchemaValidator(DATABASE_URL)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
