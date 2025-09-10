#!/usr/bin/env python3
"""
Fix for stuck discovery flow progression
Manually completes the data import phase and progresses to asset inventory
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append("/app" if os.path.exists("/app") else "backend")


async def fix_stuck_flow():
    """Fix the stuck discovery flow by manually updating phase completion"""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        flow_id = "817812b5-ae6d-41e1-8a30-ccdcfb7b4f8a"
        data_import_id = "02471817-d01c-4d8e-9a2b-6fd16f0ad1fc"

        async with AsyncSessionLocal() as db:
            print(f"🔧 Fixing stuck discovery flow: {flow_id}")

            # Step 1: Update data import status to completed
            print("Step 1: Updating data import status to 'completed'...")
            await db.execute(
                text(
                    """
                UPDATE data_imports
                SET status = 'completed',
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = :import_id
            """
                ),
                {"import_id": data_import_id},
            )

            # Step 2: Update discovery flow phase completion flags
            print("Step 2: Updating discovery flow phase completion...")
            await db.execute(
                text(
                    """
                UPDATE discovery_flows
                SET data_import_completed = TRUE,
                    current_phase = 'asset_inventory',
                    progress_percentage = 16.7,
                    updated_at = NOW()
                WHERE flow_id = :flow_id
            """
                ),
                {"flow_id": flow_id},
            )

            # Step 3: Commit the changes
            await db.commit()
            print("✅ Changes committed to database")

            # Step 4: Verify the fix
            print("Step 4: Verifying the fix...")
            result = await db.execute(
                text(
                    """
                SELECT
                    df.current_phase,
                    df.progress_percentage,
                    df.data_import_completed,
                    di.status as import_status
                FROM discovery_flows df
                JOIN data_imports di ON df.data_import_id = di.id
                WHERE df.flow_id = :flow_id
            """
                ),
                {"flow_id": flow_id},
            )

            row = result.fetchone()
            if row:
                print("✅ Flow fixed successfully:")
                print(f"   Current Phase: {row[0]}")
                print(f"   Progress: {row[1]}%")
                print(f"   Data Import Completed: {row[2]}")
                print(f"   Data Import Status: {row[3]}")

            print("\n🎉 Discovery flow should now be ready for asset inventory phase!")
            print("   Assets will be created when the flow processing continues.")

    except Exception as e:
        print(f"❌ Error fixing flow: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(fix_stuck_flow())
