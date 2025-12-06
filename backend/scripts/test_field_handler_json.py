#!/usr/bin/env python3
"""
Test script to show actual JSON output from available-target-fields endpoint.

Usage:
    cd backend
    python scripts/test_field_handler_json.py

Or from project root:
    python backend/scripts/test_field_handler_json.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment variables if needed
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/migration_db"
)

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from uuid import uuid4

    from app.core.context import RequestContext
    from app.api.v1.endpoints.data_import.handlers.field_handler import (
        get_available_target_fields,
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(
        "\nTrying alternative approach - checking if we can use database from environment..."
    )
    sys.exit(1)


async def test_endpoint_output(import_category: str = None):
    """Test endpoint and display actual JSON output."""
    # Try to use database URL from environment or use test in-memory SQLite
    database_url = os.environ.get("DATABASE_URL")

    if not database_url or "localhost" in database_url:
        print("⚠️  Using in-memory SQLite for testing (limited schema)")
        print("   For full output, ensure database connection is available\n")
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    else:
        # Use actual database connection
        engine = create_async_engine(database_url, echo=False)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create test context
        context = RequestContext(
            client_account_id=uuid4(),
            engagement_id=uuid4(),
            user_id=str(uuid4()),
            flow_id=None,
        )

        try:
            print(f"\n{'=' * 100}")
            category_label = import_category or "default (all fields)"
            print("Testing available-target-fields endpoint")
            print(f"Import Category: {category_label}")
            print(f"{'=' * 100}\n")

            # Call the endpoint handler
            result = await get_available_target_fields(
                flow_id=None,
                import_category=import_category,
                context=context,
                db=db,
            )

            # Display full JSON output
            json_output = json.dumps(result, indent=2, default=str)
            print(json_output)

            # Summary
            fields = result.get("fields", [])
            print(f"\n{'=' * 100}")
            print("Summary:")
            print(f"  Total fields: {len(fields)}")
            print(f"  Import category: {result.get('import_category', 'N/A')}")

            # Count fields with import_types
            fields_with_import_types = sum(
                1
                for f in fields
                if "import_types" in f and len(f.get("import_types", [])) > 0
            )
            print(
                f"  Fields with import_types: {fields_with_import_types}/{len(fields)}"
            )

            # Count by import type
            import_type_counts = {}
            for field in fields:
                for import_type in field.get("import_types", []):
                    import_type_counts[import_type] = (
                        import_type_counts.get(import_type, 0) + 1
                    )

            if import_type_counts:
                print("\n  Fields by import type:")
                for import_type, count in sorted(import_type_counts.items()):
                    print(f"    {import_type}: {count} fields")

            # Show sample fields
            print("\n  Sample fields (first 10):")
            for i, field in enumerate(fields[:10], 1):
                import_types_str = ", ".join(field.get("import_types", []))
                print(
                    f"    {i}. {field.get('name')} ({field.get('category')}) → [{import_types_str}]"
                )

            # Check for any missing import_types
            missing = [
                f["name"]
                for f in fields
                if "import_types" not in f or len(f.get("import_types", [])) == 0
            ]
            if missing:
                print(f"\n  ⚠️  Fields missing import_types: {missing}")
            else:
                print(f"\n  ✅ All {len(fields)} fields have import_types metadata")

            print(f"{'=' * 100}\n")

            return result

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            await engine.dispose()


async def main():
    """Run tests for different import categories."""
    print("=" * 100)
    print("Testing available-target-fields endpoint - Actual JSON Output")
    print("=" * 100)

    # Test with no import_category (default)
    await test_endpoint_output(None)

    print("\n\n")

    # Test with CMDB
    await test_endpoint_output("cmdb")

    print("\n\n")

    # Test with app_discovery
    await test_endpoint_output("app_discovery")

    print("\n\n")

    # Test with infrastructure
    await test_endpoint_output("infrastructure")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
