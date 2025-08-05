#!/usr/bin/env python3
"""
Simple Railway Migration Check
Uses docker exec to check the Railway database state without complex imports
"""

import subprocess
import sys


def run_psql_command(command: str) -> tuple[bool, str]:
    """Run a PostgreSQL command via docker exec"""
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "migration_postgres",
                "psql",
                "-U",
                "postgres",
                "-d",
                "migration_db",
                "-c",
                command,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def check_migration_version():
    """Check current migration version"""
    print("🔍 Checking current migration version...")
    success, output = run_psql_command("SELECT version_num FROM alembic_version;")

    if success:
        version = output.strip().split("\n")[-2].strip()  # Get the actual version
        print(f"✅ Current migration version: {version}")
        return version
    else:
        print(f"❌ Failed to get migration version: {output}")
        return None


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists"""
    command = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'migration'
        AND table_name = '{table_name}'
    );
    """  # nosec B608 - table_name is validated internally for migration table checks
    success, output = run_psql_command(command)

    if success:
        exists = "t" in output.lower()  # PostgreSQL returns 't' for true
        status = "✅" if exists else "❌"
        print(
            f"{status} Table migration.{table_name}: {'EXISTS' if exists else 'MISSING'}"
        )
        return exists
    else:
        print(f"❌ Error checking table {table_name}: {output}")
        return False


def check_workflow_states_columns():
    """Check workflow_states table columns"""
    print("🔍 Checking workflow_states columns...")
    command = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'migration'
    AND table_name = 'workflow_states'
    ORDER BY ordinal_position;
    """
    success, output = run_psql_command(command)

    if success:
        columns = [
            line.strip()
            for line in output.split("\n")
            if line.strip() and not line.startswith("-") and "column_name" not in line
        ]
        columns = [col for col in columns if col and col != "(" and col != ")"]

        print(f"✅ workflow_states has {len(columns)} columns")

        # Check for key unified discovery flow columns
        expected_columns = [
            "flow_id",
            "user_id",
            "progress_percentage",
            "field_mappings",
            "cleaned_data",
            "asset_inventory",
            "dependencies",
            "technical_debt",
        ]

        missing = [col for col in expected_columns if col not in columns]
        if missing:
            print(f"❌ Missing unified discovery flow columns: {missing}")
            return False
        else:
            print("✅ All key unified discovery flow columns present")
            return True
    else:
        print(f"❌ Error checking workflow_states columns: {output}")
        return False


def check_sixr_constraint():
    """Check sixr_analysis_parameters constraint"""
    print("🔍 Checking sixr_analysis_parameters constraint...")
    command = """
    SELECT conname, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conname = 'sixr_analysis_parameters_analysis_id_fkey';
    """
    success, output = run_psql_command(command)

    if success and "sixr_analysis_parameters_analysis_id_fkey" in output:
        print("✅ sixr_analysis_parameters foreign key constraint exists")
        return True
    else:
        print("❌ sixr_analysis_parameters foreign key constraint missing or broken")
        return False


def main():
    """Main check function"""
    print("🚀 Railway Database Migration Check")
    print("=" * 50)

    # Check current migration version
    current_version = check_migration_version()
    if not current_version:
        print("❌ Cannot proceed without migration version")
        return False

    print("\n📋 Expected migration version: 9d6b856ba8a7")
    if current_version != "9d6b856ba8a7":
        print("⚠️ Version mismatch! Railway may be missing migrations.")
    else:
        print("✅ Migration version matches expected")

    print("\n🔍 Checking critical tables...")

    # Check critical tables
    critical_tables = [
        "client_accounts",
        "engagements",
        "users",
        "user_roles",
        "workflow_states",
        "sixr_analyses",
        "sixr_analysis_parameters",
    ]

    all_tables_exist = True
    for table in critical_tables:
        if not check_table_exists(table):
            all_tables_exist = False

    # Check workflow_states columns
    print("\n🔍 Checking workflow_states structure...")
    workflow_states_ok = check_workflow_states_columns()

    # Check constraints
    print("\n🔍 Checking database constraints...")
    constraints_ok = check_sixr_constraint()

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)

    issues = []
    if current_version != "9d6b856ba8a7":
        issues.append("Migration version mismatch")
    if not all_tables_exist:
        issues.append("Missing critical tables")
    if not workflow_states_ok:
        issues.append("workflow_states missing columns")
    if not constraints_ok:
        issues.append("Database constraints broken")

    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Run 'alembic upgrade head' on Railway")
        print("   2. Check Railway build logs for migration failures")
        print("   3. Ensure all migration files are deployed to Railway")
        return False
    else:
        print("✅ All checks passed - database state looks good")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
