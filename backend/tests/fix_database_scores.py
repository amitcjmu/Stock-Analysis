#!/usr/bin/env python3

import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
from sqlalchemy import select

def fix_scores_in_data(data, path=""):
    """Recursively fix any scores > 100 in the data structure"""
    if isinstance(data, list):
        for i, item in enumerate(data):
            fix_scores_in_data(item, f"{path}[{i}]")
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == 'score' and isinstance(value, (int, float)) and value > 100:
                print(f"  Fixing score at {path}.{key}: {value} -> 100.0")
                data[key] = 100.0
            else:
                fix_scores_in_data(value, f"{path}.{key}")

async def fix_scores():
    async with AsyncSessionLocal() as session:
        # Get all recommendations
        result = await session.execute(select(SixRRecommendationModel))
        recommendations = result.scalars().all()
        
        fixed_count = 0
        for rec in recommendations:
            print(f"\nChecking recommendation {rec.id}...")
            
            if rec.strategy_scores:
                original_scores = json.dumps(rec.strategy_scores)
                fix_scores_in_data(rec.strategy_scores, "strategy_scores")
                new_scores = json.dumps(rec.strategy_scores)
                
                if original_scores != new_scores:
                    # Mark the field as dirty for SQLAlchemy
                    rec.strategy_scores = rec.strategy_scores
                    fixed_count += 1
                    print(f"  ✅ Fixed recommendation {rec.id}")
                else:
                    print(f"  ✅ No issues found in recommendation {rec.id}")
        
        if fixed_count > 0:
            await session.commit()
            print(f"\n🎯 SUMMARY: Fixed {fixed_count} recommendations with scores > 100")
        else:
            print("\n🎯 SUMMARY: No scores > 100 found")

if __name__ == "__main__":
    asyncio.run(fix_scores()) 