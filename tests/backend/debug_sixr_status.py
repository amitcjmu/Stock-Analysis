#!/usr/bin/env python3

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRAnalysis
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel


async def check_sixr_status():
    async with AsyncSessionLocal() as session:
        # Check analyses
        result = await session.execute(select(SixRAnalysis))
        analyses = result.scalars().all()
        print(f"🔍 Found {len(analyses)} analyses")

        for analysis in analyses:
            print(
                f"  Analysis {analysis.id}: status={analysis.status}, apps={analysis.application_ids}, final_rec={analysis.final_recommendation}"
            )

        # Check recommendations
        rec_result = await session.execute(select(SixRRecommendationModel))
        recommendations = rec_result.scalars().all()
        print(f"🎯 Found {len(recommendations)} recommendations")

        for rec in recommendations:
            print(
                f"  Recommendation {rec.id}: analysis_id={rec.analysis_id}, strategy={rec.recommended_strategy}, confidence={rec.confidence_score}"
            )


if __name__ == "__main__":
    asyncio.run(check_sixr_status())
