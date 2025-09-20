#!/usr/bin/env python3

import asyncio
import sys

sys.path.append("/app")

from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent  # noqa: E402


async def simple_test():
    print("=== SIMPLE TECH DEBT TEST ===")

    # Test with a single asset that we know has tech debt
    test_asset = {
        "id": "SRV0012",
        "name": "srv-monitor-01",
        "asset_type": "Server",
        "operating_system": "Windows Server 2016",
        "version/hostname": "srv-monitor-01",
    }

    print(f"Test asset: {test_asset['name']} - {test_asset['operating_system']}")

    # Test OS extraction
    os_info = tech_debt_analysis_agent._extract_os_information(test_asset)
    print(f"OS Info: {os_info}")

    # Test lifecycle assessment
    if os_info:
        lifecycle = tech_debt_analysis_agent._assess_os_lifecycle(
            os_info.get("os_name", ""), os_info.get("os_version", "")
        )
        print(f"Lifecycle: {lifecycle}")

        # Test risk calculation
        risk_score = tech_debt_analysis_agent._calculate_os_risk_score(
            lifecycle, os_info
        )
        print(f"Risk Score: {risk_score}")

    # Test OS analysis step by step
    print("\n=== OS ANALYSIS ===")
    os_analysis = await tech_debt_analysis_agent._analyze_operating_systems(
        [test_asset]
    )
    print(f"OS Analysis: {os_analysis}")

    # Test business risk categorization
    print("\n=== BUSINESS RISK ===")
    business_risks = tech_debt_analysis_agent._categorize_business_risk(os_analysis, {})
    print(f"Business Risks: {business_risks}")


if __name__ == "__main__":
    asyncio.run(simple_test())
