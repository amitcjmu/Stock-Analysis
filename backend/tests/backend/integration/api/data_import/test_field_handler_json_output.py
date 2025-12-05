"""
Standalone script to test and display JSON output from available-target-fields endpoint.

This script can be run directly to see the JSON response structure for different import types.

Usage:
    python backend/tests/backend/integration/api/data_import/test_field_handler_json_output.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.core.context import RequestContext
from app.api.v1.endpoints.data_import.handlers.field_handler import (
    get_available_target_fields,
)


async def test_and_display_json(import_category: str = None):
    """Test the endpoint and display JSON output."""
    # Create a test database session (using in-memory SQLite for testing)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create mock context
        context = RequestContext(
            client_account_id=uuid4(),
            engagement_id=uuid4(),
            user_id=str(uuid4()),
            flow_id=None,
        )

        try:
            # Call the endpoint handler
            result = await get_available_target_fields(
                flow_id=None,
                import_category=import_category,
                context=context,
                db=db,
            )

            # Display JSON output
            category_label = import_category or "default (all fields)"
            print("\n" + "=" * 100)
            print(f"JSON Response for import_category: {category_label}")
            print("=" * 100)
            print(json.dumps(result, indent=2, default=str))
            print("=" * 100)

            # Summary statistics
            fields = result.get("fields", [])
            print("\n📊 Summary:")
            print(f"  Total fields: {len(fields)}")
            print(f"  Import category: {result.get('import_category', 'N/A')}")

            # Count fields by import type
            import_type_counts = {}
            for field in fields:
                for import_type in field.get("import_types", []):
                    import_type_counts[import_type] = (
                        import_type_counts.get(import_type, 0) + 1
                    )

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

            # Verify all fields have import_types
            fields_without_import_types = [
                f["name"]
                for f in fields
                if "import_types" not in f or len(f.get("import_types", [])) == 0
            ]
            if fields_without_import_types:
                print(
                    f"\n  ⚠️  Fields missing import_types: {fields_without_import_types}"
                )
            else:
                print(f"\n  ✅ All {len(fields)} fields have import_types metadata")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await engine.dispose()


async def main():
    """Run tests for different import categories."""
    print("Testing available-target-fields endpoint JSON output")
    print("=" * 100)

    # Test default (no import_category)
    await test_and_display_json(None)

    print("\n\n")

    # Test CMDB
    await test_and_display_json("cmdb")

    print("\n\n")

    # Test app_discovery
    await test_and_display_json("app_discovery")

    print("\n\n")

    # Test infrastructure
    await test_and_display_json("infrastructure")


if __name__ == "__main__":
    asyncio.run(main())
