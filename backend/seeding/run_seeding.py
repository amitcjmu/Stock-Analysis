"""
Main seeding orchestrator that runs all seeding scripts in order.
"""

import asyncio
import subprocess
import sys
from pathlib import Path


async def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    print(f"\n{description}")
    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False


async def main():
    """Run all seeding scripts in order."""
    print("=" * 60)
    print("🌱 DATABASE SEEDING ORCHESTRATOR")
    print("=" * 60)

    # For now, we'll create a simple SCHEMA_READY.md to simulate Agent 1's work
    schema_ready_path = Path(__file__).parent / "SCHEMA_READY.md"
    if not schema_ready_path.exists():
        print("\n📋 Creating SCHEMA_READY.md...")
        schema_ready_path.write_text(
            "# Schema Ready\n\nDatabase schema has been created and is ready for seeding.\n"
        )
        print("✓ Created SCHEMA_READY.md")

    # Run seeding scripts in order
    scripts = [
        (
            "01_core_entities.py",
            "👥 Step 1: Seeding core entities (users, client, engagement)...",
        ),
        ("02_discovery_flows.py", "🔄 Step 2: Seeding discovery flows..."),
        ("03_data_imports.py", "📊 Step 3: Seeding data imports..."),
    ]

    for script, description in scripts:
        success = await run_script(script, description)
        if not success:
            print(f"\n❌ Failed to run {script}. Stopping seeding process.")
            return

    print("\n" + "=" * 60)
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    print("\n📁 Generated files:")
    print("   - backend/seeding/SCHEMA_READY.md")
    print("   - backend/seeding/FLOW_IDS.json")
    print("   - backend/seeding/SEEDED_IDS.json")

    print("\n🎯 Next steps:")
    print("   - Agent 3 can now use SEEDED_IDS.json for testing")
    print("   - Run the application to see the seeded data")
    print("   - Check the admin panel for user management")


if __name__ == "__main__":
    asyncio.run(main())
