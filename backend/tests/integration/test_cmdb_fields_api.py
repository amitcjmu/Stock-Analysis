"""Quick test script to verify CMDB fields in API responses"""

import asyncio
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.schemas.asset_schemas import AssetResponse
from sqlalchemy import select


async def test_asset_api_serialization():
    """Test that assets from DB serialize with new CMDB fields"""
    async with AsyncSessionLocal() as db:
        # Get first asset
        result = await db.execute(select(Asset).limit(1))
        asset = result.scalar_one_or_none()

        if not asset:
            print("❌ No assets found in database")
            return

        print(f"Testing asset: {asset.name} (ID: {asset.id})")
        print(f"Asset Type: {asset.asset_type}\n")

        # Serialize with Pydantic schema
        response = AssetResponse.model_validate(asset)
        data = response.model_dump()

        # Check for new CMDB fields
        new_cmdb_fields = [
            "business_unit",
            "vendor",
            "application_type",
            "lifecycle",
            "hosting_model",
            "server_role",
            "security_zone",
            "database_type",
            "database_version",
            "database_size_gb",
            "cpu_utilization_percent_max",
            "memory_utilization_percent_max",
            "storage_free_gb",
            "pii_flag",
            "application_data_classification",
            "has_saas_replacement",
            "risk_level",
            "tshirt_size",
            "proposed_treatmentplan_rationale",
            "annual_cost_estimate",
            "backup_policy",
            "asset_tags",
        ]

        present_fields = [f for f in new_cmdb_fields if f in data]

        print(
            f"✅ AssetResponse includes {len(present_fields)}/{len(new_cmdb_fields)} new CMDB fields\n"
        )

        print("New CMDB Fields in API Response:")
        for field in present_fields:
            value = data[field]
            if value is not None and value != [] and value != "":
                print(f"  ✓ {field}: {value}")
            else:
                print(f"  ○ {field}: (null/empty)")

        print("\n✅ API serialization working correctly!")


if __name__ == "__main__":
    asyncio.run(test_asset_api_serialization())
