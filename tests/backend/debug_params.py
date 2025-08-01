#!/usr/bin/env python3

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRParameters as SixRParametersModel


async def check_params():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SixRParametersModel).order_by(SixRParametersModel.id.desc()).limit(5)
        )
        params = result.scalars().all()
        print(f"📊 Found {len(params)} parameter sets:")
        for p in params:
            print(f"  Params {p.id} (Analysis {p.analysis_id}):")
            print(f"    Business Value: {p.business_value}")
            print(f"    Technical Complexity: {p.technical_complexity}")
            print(f"    Migration Urgency: {p.migration_urgency}")
            print(f"    Compliance Requirements: {p.compliance_requirements}")
            print(f"    Cost Sensitivity: {p.cost_sensitivity}")
            print(f"    Risk Tolerance: {p.risk_tolerance}")
            print(f"    Innovation Priority: {p.innovation_priority}")
            print()


if __name__ == "__main__":
    asyncio.run(check_params())
