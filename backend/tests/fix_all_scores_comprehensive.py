#!/usr/bin/env python3

import asyncio
import json

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel


def fix_scores_recursively(data, path="", changes=None):
    """Recursively find and fix ALL scores > 100 in any data structure"""
    if changes is None:
        changes = []
    
    if isinstance(data, list):
        for i, item in enumerate(data):
            fix_scores_recursively(item, f"{path}[{i}]", changes)
    elif isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if key == 'score' and isinstance(value, (int, float)) and value > 100:
                changes.append({
                    'path': current_path,
                    'old_value': value,
                    'new_value': 100.0
                })
                data[key] = 100.0
            elif isinstance(value, (dict, list)):
                fix_scores_recursively(value, current_path, changes)
    
    return changes

async def comprehensive_score_fix():
    async with AsyncSessionLocal() as session:
        print("🔍 COMPREHENSIVE SCORE VALIDATION FIX")
        print("=" * 50)
        
        # Get ALL recommendations without any filtering
        result = await session.execute(
            select(SixRRecommendationModel).order_by(SixRRecommendationModel.id)
        )
        recommendations = result.scalars().all()
        
        print(f"📊 Found {len(recommendations)} total recommendations")
        
        total_fixed = 0
        for rec in recommendations:
            print(f"\n🔎 Analyzing recommendation {rec.id}...")
            
            changes_made = []
            
            # Check strategy_scores
            if rec.strategy_scores:
                print("  📋 Checking strategy_scores...")
                json.loads(json.dumps(rec.strategy_scores))
                changes = fix_scores_recursively(rec.strategy_scores, "strategy_scores")
                
                if changes:
                    changes_made.extend(changes)
                    rec.strategy_scores = rec.strategy_scores  # Mark as dirty
                    
            # Also check other JSON fields that might contain scores
            for field_name in ['key_factors', 'assumptions', 'risk_factors', 'business_benefits', 'technical_benefits']:
                field_value = getattr(rec, field_name, None)
                if field_value and isinstance(field_value, (dict, list)):
                    changes = fix_scores_recursively(field_value, field_name)
                    if changes:
                        changes_made.extend(changes)
                        setattr(rec, field_name, field_value)  # Mark as dirty
            
            if changes_made:
                total_fixed += 1
                print(f"  ✅ FIXED {len(changes_made)} score(s) in recommendation {rec.id}:")
                for change in changes_made:
                    print(f"    - {change['path']}: {change['old_value']} → {change['new_value']}")
            else:
                print(f"  ✅ No issues found in recommendation {rec.id}")
        
        # Commit all changes
        if total_fixed > 0:
            await session.commit()
            print(f"\n🎯 SUMMARY: Fixed scores in {total_fixed} recommendations")
            
            # Verify fix worked by testing a problematic query
            try:
                print("\n🧪 VERIFICATION TEST...")
                test_result = await session.execute(
                    text("SELECT id, strategy_scores FROM sixr_recommendations WHERE strategy_scores::text LIKE '%108.0%' LIMIT 5")
                )
                remaining_issues = test_result.fetchall()
                
                if remaining_issues:
                    print(f"⚠️  Found {len(remaining_issues)} records still containing '108.0':")
                    for row in remaining_issues:
                        print(f"   - Recommendation {row[0]}: {row[1]}")
                else:
                    print("✅ Verification passed - no more 108.0 scores found!")
                    
            except Exception as e:
                print(f"⚠️  Verification test failed: {e}")
        else:
            print("\n✅ No scores > 100 found in any recommendations")

if __name__ == "__main__":
    asyncio.run(comprehensive_score_fix()) 