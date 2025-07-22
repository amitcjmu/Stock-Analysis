#!/usr/bin/env python3

import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def fix_scores_with_sql():
    async with AsyncSessionLocal() as session:
        print("🔧 DIRECT SQL SCORE FIX")
        print("=" * 40)
        
        # Find records with scores > 100
        find_query = text("""
            SELECT id, strategy_scores 
            FROM sixr_recommendations 
            WHERE strategy_scores::text LIKE '%108.0%' 
               OR strategy_scores::text ~ '"score":\s*1[0-9][0-9]\.[0-9]'
            ORDER BY id
        """)
        
        result = await session.execute(find_query)
        problematic_records = result.fetchall()
        
        print(f"📊 Found {len(problematic_records)} records with scores > 100")
        
        if not problematic_records:
            print("✅ No problematic scores found!")
            return
        
        # Use direct SQL UPDATE with JSON manipulation
        fix_query = text("""
            UPDATE sixr_recommendations 
            SET strategy_scores = (
                SELECT jsonb_agg(
                    CASE 
                        WHEN (item->>'score')::float > 100 
                        THEN jsonb_set(item, '{score}', '100.0'::jsonb)
                        ELSE item
                    END
                )
                FROM jsonb_array_elements(strategy_scores) AS item
            )
            WHERE strategy_scores::text LIKE '%108.0%' 
               OR strategy_scores::text ~ '"score":\s*1[0-9][0-9]\.[0-9]'
        """)
        
        print("🔧 Executing direct SQL fix...")
        fix_result = await session.execute(fix_query)
        await session.commit()
        
        print(f"✅ Updated {fix_result.rowcount} records")
        
        # Verify the fix
        verify_result = await session.execute(find_query)
        remaining_issues = verify_result.fetchall()
        
        if remaining_issues:
            print(f"⚠️  Still found {len(remaining_issues)} problematic records:")
            for row in remaining_issues:
                print(f"   - Record {row[0]}")
        else:
            print("🎉 All scores > 100 have been fixed!")

if __name__ == "__main__":
    asyncio.run(fix_scores_with_sql()) 