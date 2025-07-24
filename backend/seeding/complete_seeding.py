"""
Complete the seeding process - runs all remaining seeding scripts.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


async def run_script(script_name: str) -> bool:
    """Run a Python script and return success status."""
    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit
        )
        print(result.stdout)
        if result.stderr:
            print(f"Errors/Warnings:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception running {script_name}: {str(e)}")
        return False


async def main():
    """Run all seeding scripts."""
    print("=" * 60)
    print("🌱 COMPLETING DATABASE SEEDING")
    print("=" * 60)

    # Run the core entities script (will skip if already done)
    print("\n👥 Step 1: Core entities...")
    success = await run_script("01_core_entities_simple.py")
    print(f"Core entities: {'✅ Complete' if success else '⚠️  Check logs'}")

    # Run discovery flows
    print("\n🔄 Step 2: Discovery flows...")
    success = await run_script("02_discovery_flows.py")
    print(f"Discovery flows: {'✅ Complete' if success else '❌ Failed'}")

    # Run data imports
    print("\n📊 Step 3: Data imports...")
    success = await run_script("03_data_imports.py")
    print(f"Data imports: {'✅ Complete' if success else '❌ Failed'}")

    # Check if SEEDED_IDS.json was created
    seeded_ids_path = Path(__file__).parent / "SEEDED_IDS.json"
    if seeded_ids_path.exists():
        print("\n✅ SEEDED_IDS.json created successfully!")
        with open(seeded_ids_path) as f:
            data = json.load(f)
        print("\nSeeded data summary:")
        print(f"  - Client: {data['client_account']['name']}")
        print(f"  - Engagement: {data['engagement']['name']}")
        print(f"  - Users: {len(data['users'])}")
        print(f"  - Flows: {len(data['flows'])}")
        print(f"  - Imports: {len(data['imports'])}")
    else:
        print("\n⚠️  SEEDED_IDS.json not found")

    print("\n" + "=" * 60)
    print("🎯 SEEDING PROCESS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
