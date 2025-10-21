#!/usr/bin/env python3
"""
Test Phase 1: Asset Type Routing Fix
Verifies _get_asset_type() method works correctly
"""
import asyncio
import sys

# Add backend to path
sys.path.insert(0, "/app")


async def test_asset_type_lookup():
    """Test asset type lookup for database asset"""
    from app.services.ai_analysis.questionnaire_generator.tools.generation import (
        QuestionnaireGenerationTool,
    )
    from app.core.database import get_async_session
    from sqlalchemy import select
    from app.models.asset.models import Asset

    print("=" * 80)
    print("PHASE 1 TEST: Asset Type Routing Fix")
    print("=" * 80)

    # Initialize tool
    tool = QuestionnaireGenerationTool()

    # Test 1: Get database asset from DB
    print("\n✓ Test 1: Database Query for Database Assets")
    async for session in get_async_session():
        result = await session.execute(
            select(Asset.id, Asset.asset_name, Asset.asset_type)
            .where(Asset.asset_type == "database")
            .limit(3)
        )
        assets = result.all()

        if not assets:
            print("❌ No database assets found in database!")
            return False

        print(f"✅ Found {len(assets)} database assets:")
        for asset_id, asset_name, asset_type in assets:
            print(f"   - {asset_name} (type={asset_type}, id={asset_id})")

        # Test 2: Test _get_asset_type() method
        print("\n✓ Test 2: _get_asset_type() Method Test")
        test_asset = assets[0]
        test_id = str(test_asset[0])
        test_name = test_asset[1]

        # Create business_context with db_session
        business_context = {"db_session": session}

        # Call _get_asset_type()
        retrieved_type = await tool._get_asset_type(test_id, business_context)

        print(f"   Asset: {test_name}")
        print("   Expected type: database")
        print(f"   Retrieved type: {retrieved_type}")

        if retrieved_type == "database":
            print("   ✅ PASS: Correct asset type returned!")
        else:
            print(f"   ❌ FAIL: Got '{retrieved_type}' instead of 'database'")
            return False

        # Test 3: Test with business_context preloading
        print("\n✓ Test 3: business_context['asset_types'] Preloading Test")
        business_context_preloaded = {"asset_types": {test_id: "database"}}

        retrieved_type_cached = await tool._get_asset_type(
            test_id, business_context_preloaded
        )

        if retrieved_type_cached == "database":
            print("   ✅ PASS: Cached asset type works!")
        else:
            print(f"   ❌ FAIL: Cached lookup returned '{retrieved_type_cached}'")
            return False

        # Test 4: Test fallback for missing asset
        print("\n✓ Test 4: Fallback for Missing Asset")
        fake_id = "00000000-0000-0000-0000-000000000000"
        fallback_type = await tool._get_asset_type(fake_id, {"db_session": session})

        if fallback_type == "application":
            print("   ✅ PASS: Fallback to 'application' works!")
        else:
            print(f"   ❌ FAIL: Expected 'application' fallback, got '{fallback_type}'")
            return False

        # Test 5: Verify technical detail question routing
        print("\n✓ Test 5: Question Generator Routing Test")
        asset_context = {
            "asset_id": test_id,
            "asset_name": test_name,
            "asset_type": "database",
        }

        question = tool._generate_technical_detail_question({}, asset_context)

        print(f"   Generated question type: {question.get('question_type', 'unknown')}")

        # Check if it's database-specific
        question_text = str(question)
        if any(
            keyword in question_text.lower()
            for keyword in ["database", "replication", "backup", "engine"]
        ):
            print("   ✅ PASS: Database-specific question generated!")
        else:
            print("   ❌ FAIL: Question doesn't appear database-specific")
            print(f"   Question: {question_text[:200]}")
            return False

        break  # Exit after first session

    print("\n" + "=" * 80)
    print("✅ ALL PHASE 1 TESTS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("- ✅ Database assets exist in database")
    print("- ✅ _get_asset_type() returns correct type")
    print("- ✅ business_context preloading works")
    print("- ✅ Fallback to 'application' works")
    print("- ✅ DatabaseQuestionsGenerator routing works")
    print("\n🎯 Phase 1 Implementation: VERIFIED AND WORKING")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_asset_type_lookup())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
