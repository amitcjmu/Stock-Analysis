#!/usr/bin/env python
"""
Test the field mapping data retrieval through the API
"""
import asyncio
import json

from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
from app.core.context import RequestContext
from app.core.database import get_db


async def test_field_mapping_api():
    async for db in get_db():
        try:
            # Create a test context
            context = RequestContext(
                client_account_id="11111111-1111-1111-1111-111111111111",
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id="44444444-4444-4444-4444-444444444444",
                session_id=None,
            )

            # Create flow management handler
            handler = FlowManagementHandler(db, context)

            # Get flow status
            flow_id = "854f8360-cba4-4e7b-be3f-a0c1537f6eb0"
            status = await handler.get_flow_status(flow_id)

            print("Flow Status Retrieved:")
            print(f"  Status: {status.get('status')}")
            print(f"  Current Phase: {status.get('current_phase')}")
            print(f"  Progress: {status.get('progress_percentage')}%")

            # Check field mapping data
            if "field_mapping" in status:
                fm = status["field_mapping"]
                print("\n✅ Field Mapping Data Found:")
                print(f"  Type: {type(fm)}")
                if isinstance(fm, dict):
                    print(f"  Keys: {list(fm.keys())}")
                    if "mappings" in fm:
                        print(f"  Mappings: {len(fm['mappings'])} items")
                    if "attributes" in fm:
                        print(f"  Attributes: {len(fm['attributes'])} items")
                    if "progress" in fm:
                        print(f"  Progress: {fm['progress']}")
            else:
                print("\n❌ No field_mapping key in status response")
                print(f"Available keys: {list(status.keys())}")

            # Save full response for debugging
            with open("/tmp/flow_status_response.json", "w") as f:
                json.dump(status, f, indent=2, default=str)
            print("\n📄 Full response saved to /tmp/flow_status_response.json")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(test_field_mapping_api())
