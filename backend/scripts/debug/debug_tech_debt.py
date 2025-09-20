#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to the path
sys.path.append("/app")  # noqa: E402

from app.api.v1.discovery.asset_handlers.asset_crud import (  # noqa: E402
    AssetCRUDHandler,
)
from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent  # noqa: E402


async def debug_tech_debt():
    print("=== TECH DEBT DEBUG ===")

    # Get assets
    crud_handler = AssetCRUDHandler()
    assets_result = await crud_handler.get_assets_paginated({"page_size": 10})
    assets = assets_result.get("assets", [])

    print(f"Total assets: {len(assets)}")

    # Check assets with OS info
    assets_with_os = [a for a in assets if a.get("operating_system")]
    print(f"Assets with OS info: {len(assets_with_os)}")

    for asset in assets_with_os[:5]:
        print(
            f"  - {asset.get('name', 'unknown')}: {asset.get('operating_system', 'none')}"
        )

        # Test OS extraction
        os_info = tech_debt_analysis_agent._extract_os_information(asset)
        print(f"    Extracted: {os_info}")

        if os_info:
            # Test lifecycle assessment
            lifecycle = tech_debt_analysis_agent._assess_os_lifecycle(
                os_info.get("os_name", ""), os_info.get("os_version", "")
            )
            print(f"    Lifecycle: {lifecycle}")

    # Run full analysis
    print("\n=== FULL ANALYSIS ===")
    result = await tech_debt_analysis_agent.analyze_tech_debt(assets)

    os_analysis = result.get("tech_debt_analysis", {}).get("os_analysis", {})
    print(f"OS inventory: {len(os_analysis.get('os_inventory', {}))}")
    print(f"Lifecycle status: {len(os_analysis.get('lifecycle_status', {}))}")
    print(f"Risk assessment: {len(os_analysis.get('risk_assessment', {}))}")

    prioritized_debt = result.get("prioritized_tech_debt", [])
    print(f"Prioritized debt items: {len(prioritized_debt)}")

    if prioritized_debt:
        print("Sample debt item:", prioritized_debt[0])


if __name__ == "__main__":
    asyncio.run(debug_tech_debt())
