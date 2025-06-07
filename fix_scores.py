#!/usr/bin/env python3

import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRRecommendation
from sqlalchemy import select

async def fix_scores():
    async with AsyncSessionLocal() as session:
        # Get all recommendations
        result = await session.execute(select(SixRRecommendation))
        recommendations = result.scalars().all()
        
        fixed_count = 0
        for rec in recommendations:
            if rec.strategy_scores:
                scores_changed = False
                for score_item in rec.strategy_scores:
                    if isinstance(score_item, dict) and 'score' in score_item:
                        if score_item['score'] > 100.0:
                            print(f"Fixing analysis {rec.analysis_id}: score {score_item['score']} -> 100.0")
                            score_item['score'] = 100.0
                            scores_changed = True
                
                if scores_changed:
                    # Mark as modified and commit
                    rec.strategy_scores = rec.strategy_scores  # Trigger update
                    session.add(rec)
                    fixed_count += 1
        
        if fixed_count > 0:
            await session.commit()
            print(f"Fixed {fixed_count} recommendations with scores > 100")
        else:
            print("No recommendations found with scores > 100")

if __name__ == "__main__":
    asyncio.run(fix_scores()) 