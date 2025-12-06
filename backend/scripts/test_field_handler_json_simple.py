#!/usr/bin/env python3
"""
Simple test script to show JSON output - run this from Docker container.

Usage inside Docker:
    docker-compose exec backend python scripts/test_field_handler_json_simple.py

Or if backend is running locally:
    cd backend && python scripts/test_field_handler_json_simple.py
"""

import asyncio
import json
import sys
import os
from uuid import uuid4

# Add backend to path (when run from backend directory)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.context import RequestContext
from app.api.v1.endpoints.data_import.handlers.field_handler import (
    get_available_target_fields,
)


async def test_and_show_json(import_category: str = None):
    """Test endpoint and display JSON output."""
    print(f"\n{'=' * 100}")
    category_label = import_category or "default (all fields)"
    print("Testing available-target-fields endpoint")
    print(f"Import Category: {category_label}")
    print(f"{'=' * 100}\n")

    # Use actual database connection from environment
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        context = RequestContext(
            client_account_id=uuid4(),
            engagement_id=uuid4(),
            user_id=str(uuid4()),
            flow_id=None,
        )

        try:
            result = await get_available_target_fields(
                flow_id=None,
                import_category=import_category,
                context=context,
                db=db,
            )

            # Display full JSON
            json_output = json.dumps(result, indent=2, default=str)
            print(json_output)

            # Summary
            fields = result.get("fields", [])
            print(f"\n{'=' * 100}")
            print("Summary:")
            print(f"  Total fields: {len(fields)}")
            print(f"  Import category: {result.get('import_category', 'N/A')}")

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

            # Show sample
            print("\n  Sample fields (first 5):")
            for i, field in enumerate(fields[:5], 1):
                import_types_str = ", ".join(field.get("import_types", []))
                print(f"    {i}. {field.get('name')} → [{import_types_str}]")

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


async def main():
    """Run tests."""
    print("=" * 100)
    print("Testing available-target-fields endpoint - Actual JSON Output")
    print("=" * 100)

    # Test CMDB
    await test_and_show_json("cmdb")

    print("\n")

    # Test app_discovery
    await test_and_show_json("app_discovery")

    print("\n")

    # Test infrastructure
    await test_and_show_json("infrastructure")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        print("\n💡 Tip: Make sure to run this from Docker container:")
        print(
            "   docker-compose exec backend python scripts/test_field_handler_json_simple.py"
        )
