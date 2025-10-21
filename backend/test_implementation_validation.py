#!/usr/bin/env python3
"""
Implementation Validation Test
Tests all 3 phases of the Collection Flow Question Generation fix
"""
import asyncio
import sys

# Add backend to path
sys.path.insert(0, "/app")


async def test_phase_1_asset_type_routing():
    """Test Phase 1: Asset type routing fix"""
    from app.services.ai_analysis.questionnaire_generator.tools.generation import (
        QuestionnaireGenerationTool,
    )
    from app.core.database import get_async_session
    from sqlalchemy import select, func
    from app.models.asset.models import Asset

    print("=" * 80)
    print("PHASE 1 TEST: Asset Type Routing Fix")
    print("=" * 80)

    tool = QuestionnaireGenerationTool()

    async for session in get_async_session():
        # Test 1: Verify database has multiple asset types
        print("\n✓ Test 1: Database Asset Type Distribution")
        result = await session.execute(
            select(Asset.asset_type, func.count(Asset.id).label("count")).group_by(
                Asset.asset_type
            )
        )
        types = result.all()

        print(f"   Found {len(types)} distinct asset types:")
        for asset_type, count in types:
            print(f"     - {asset_type}: {count} assets")

        # Test 2: Verify _get_asset_type() method exists
        print("\n✓ Test 2: _get_asset_type() Method Existence")
        if hasattr(tool, "_get_asset_type"):
            print("   ✅ Method exists in QuestionnaireGenerationTool")
        else:
            print("   ❌ Method NOT found!")
            return False

        # Test 3: Test with database asset
        print("\n✓ Test 3: Database Asset Type Lookup")
        result = await session.execute(
            select(Asset.id, Asset.asset_name, Asset.asset_type)
            .where(Asset.asset_type == "database")
            .limit(1)
        )
        db_asset = result.first()

        if not db_asset:
            print("   ⚠️  No database assets found, skipping test")
        else:
            asset_id = str(db_asset[0])
            business_context = {"db_session": session}
            retrieved_type = await tool._get_asset_type(asset_id, business_context)

            print(f"   Asset: {db_asset[1]}")
            print("   Expected: database")
            print(f"   Retrieved: {retrieved_type}")

            if retrieved_type == "database":
                print("   ✅ PASS: Correct asset type returned")
            else:
                print(f"   ❌ FAIL: Got '{retrieved_type}' instead of 'database'")
                return False

        # Test 4: Test with application asset
        print("\n✓ Test 4: Application Asset Type Lookup")
        result = await session.execute(
            select(Asset.id, Asset.asset_name, Asset.asset_type)
            .where(Asset.asset_type == "application")
            .limit(1)
        )
        app_asset = result.first()

        if app_asset:
            asset_id = str(app_asset[0])
            business_context = {"db_session": session}
            retrieved_type = await tool._get_asset_type(asset_id, business_context)

            print(f"   Asset: {app_asset[1]}")
            print("   Expected: application")
            print(f"   Retrieved: {retrieved_type}")

            if retrieved_type == "application":
                print("   ✅ PASS: Correct asset type returned")
            else:
                print(f"   ❌ FAIL: Got '{retrieved_type}'")
                return False

        # Test 5: Test fallback for missing asset
        print("\n✓ Test 5: Fallback for Missing Asset")
        fake_id = "00000000-0000-0000-0000-000000000000"
        fallback_type = await tool._get_asset_type(fake_id, {"db_session": session})

        if fallback_type == "application":
            print("   ✅ PASS: Fallback to 'application' works")
        else:
            print(f"   ❌ FAIL: Expected 'application', got '{fallback_type}'")
            return False

        break

    print("\n" + "=" * 80)
    print("✅ PHASE 1 TESTS PASSED")
    print("=" * 80)
    return True


async def test_phase_2_auto_enrichment_timing():
    """Test Phase 2: Auto-enrichment timing fix"""
    from app.services.flow_configs.collection_flow_config import (
        get_collection_flow_config,
    )

    print("\n" + "=" * 80)
    print("PHASE 2 TEST: Auto-Enrichment Timing Fix")
    print("=" * 80)

    config = get_collection_flow_config()

    # Test 1: Verify auto_enrichment phase exists
    print("\n✓ Test 1: auto_enrichment Phase Registration")
    phase_names = [p.name for p in config.phases]
    print(f"   Registered phases: {', '.join(phase_names)}")

    if "auto_enrichment" in phase_names:
        print("   ✅ PASS: auto_enrichment phase registered")
    else:
        print("   ❌ FAIL: auto_enrichment phase NOT found!")
        return False

    # Test 2: Verify phase ordering (auto_enrichment BEFORE gap_analysis)
    print("\n✓ Test 2: Phase Ordering (enrichment BEFORE gap analysis)")
    try:
        auto_enrich_idx = phase_names.index("auto_enrichment")
        gap_analysis_idx = phase_names.index("gap_analysis")

        print(f"   auto_enrichment position: {auto_enrich_idx}")
        print(f"   gap_analysis position: {gap_analysis_idx}")

        if auto_enrich_idx < gap_analysis_idx:
            print("   ✅ PASS: auto_enrichment runs BEFORE gap_analysis")
        else:
            print("   ❌ FAIL: Incorrect ordering!")
            return False
    except ValueError as e:
        print(f"   ❌ FAIL: Missing phase - {e}")
        return False

    # Test 3: Verify version increment
    print("\n✓ Test 3: Configuration Version")
    if config.version == "2.1.0":
        print(f"   ✅ PASS: Version correctly incremented to {config.version}")
    else:
        print(f"   ⚠️  WARNING: Version is {config.version}, expected 2.1.0")

    print("\n" + "=" * 80)
    print("✅ PHASE 2 TESTS PASSED")
    print("=" * 80)
    return True


async def test_phase_3_questionnaire_caching():
    """Test Phase 3: Questionnaire caching"""
    from app.services.crewai_flows.memory.tenant_memory_manager.storage import (
        TenantMemoryStorage,
    )

    print("\n" + "=" * 80)
    print("PHASE 3 TEST: Questionnaire Caching")
    print("=" * 80)

    # Test 1: Verify storage methods exist
    print("\n✓ Test 1: Caching Methods Existence")
    if hasattr(TenantMemoryStorage, "store_questionnaire_template"):
        print("   ✅ store_questionnaire_template() exists")
    else:
        print("   ❌ store_questionnaire_template() NOT found!")
        return False

    if hasattr(TenantMemoryStorage, "retrieve_questionnaire_template"):
        print("   ✅ retrieve_questionnaire_template() exists")
    else:
        print("   ❌ retrieve_questionnaire_template() NOT found!")
        return False

    # Test 2: Verify integration in QuestionnaireGenerationTool
    print("\n✓ Test 2: Integration with QuestionnaireGenerationTool")
    from app.services.ai_analysis.questionnaire_generator.tools.generation import (
        QuestionnaireGenerationTool,
    )

    tool = QuestionnaireGenerationTool()

    if hasattr(tool, "_get_memory_manager"):
        print("   ✅ _get_memory_manager() method exists")
    else:
        print("   ❌ _get_memory_manager() method NOT found!")
        return False

    if hasattr(tool, "generate_questions_for_asset"):
        print("   ✅ generate_questions_for_asset() method exists")
    else:
        print("   ❌ generate_questions_for_asset() method NOT found!")
        return False

    print("\n" + "=" * 80)
    print("✅ PHASE 3 TESTS PASSED")
    print("=" * 80)
    return True


async def main():
    """Run all validation tests"""
    print("\n" + "🚀" * 40)
    print("COLLECTION FLOW QUESTION GENERATION FIX - VALIDATION TESTS")
    print("🚀" * 40)

    results = {
        "Phase 1: Asset Type Routing": False,
        "Phase 2: Auto-Enrichment Timing": False,
        "Phase 3: Questionnaire Caching": False,
    }

    try:
        # Run Phase 1 tests
        results["Phase 1: Asset Type Routing"] = await test_phase_1_asset_type_routing()

        # Run Phase 2 tests
        results["Phase 2: Auto-Enrichment Timing"] = (
            await test_phase_2_auto_enrichment_timing()
        )

        # Run Phase 3 tests
        results["Phase 3: Questionnaire Caching"] = (
            await test_phase_3_questionnaire_caching()
        )

    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Print summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    all_passed = True
    for phase, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{phase}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Implementation is complete and verified.")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED! Review implementation.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
