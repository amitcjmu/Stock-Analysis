#!/usr/bin/env python3

import asyncio
import sys
import traceback

sys.path.append('/app')

from app.services.tech_debt_analysis_agent import tech_debt_analysis_agent
from app.api.v1.discovery.asset_handlers.asset_crud import AssetCRUDHandler

async def debug_full_analysis():
    print("=== FULL ANALYSIS DEBUG ===")
    
    try:
        # Get full asset set (same as endpoint)
        crud_handler = AssetCRUDHandler()
        assets_result = await crud_handler.get_assets_paginated({'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        print(f"Total assets: {len(assets)}")
        print(f"Assets with OS: {len([a for a in assets if a.get('operating_system')])}")
        
        # Test each step individually
        print("\n=== STEP 1: OS ANALYSIS ===")
        try:
            os_analysis = await tech_debt_analysis_agent._analyze_operating_systems(assets)
            print(f"OS analysis completed: {len(os_analysis.get('os_inventory', {}))}")
        except Exception as e:
            print(f"OS analysis failed: {e}")
            traceback.print_exc()
            return
        
        print("\n=== STEP 2: APP ANALYSIS ===")
        try:
            app_analysis = await tech_debt_analysis_agent._analyze_application_versions(assets)
            print(f"App analysis completed: {len(app_analysis.get('application_inventory', {}))}")
        except Exception as e:
            print(f"App analysis failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 3: INFRASTRUCTURE ANALYSIS ===")
        try:
            infrastructure_analysis = await tech_debt_analysis_agent._analyze_infrastructure_debt(assets)
            print(f"Infrastructure analysis completed")
        except Exception as e:
            print(f"Infrastructure analysis failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 4: SECURITY ANALYSIS ===")
        try:
            security_analysis = await tech_debt_analysis_agent._analyze_security_debt(assets)
            print(f"Security analysis completed")
        except Exception as e:
            print(f"Security analysis failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 5: BUSINESS RISK ASSESSMENT ===")
        try:
            technical_analysis = {
                "os_analysis": os_analysis,
                "app_analysis": app_analysis,
                "infrastructure_analysis": infrastructure_analysis,
                "security_analysis": security_analysis
            }
            
            business_risk_assessment = await tech_debt_analysis_agent._assess_business_risk_context(
                technical_analysis,
                {},  # stakeholder_context
                "6-12 months"  # migration_timeline
            )
            print(f"Business risk assessment completed")
        except Exception as e:
            print(f"Business risk assessment failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 6: PRIORITIZATION ===")
        try:
            prioritized_debt = await tech_debt_analysis_agent._prioritize_tech_debt(
                business_risk_assessment, 
                {},  # stakeholder_context
                "6-12 months"  # migration_timeline
            )
            print(f"Prioritized debt: {len(prioritized_debt)}")
            if prioritized_debt:
                print(f"Sample item: {prioritized_debt[0]}")
        except Exception as e:
            print(f"Prioritization failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 7: STAKEHOLDER QUESTIONS ===")
        try:
            stakeholder_questions = await tech_debt_analysis_agent._generate_stakeholder_questions(
                prioritized_debt, {}
            )
            print(f"Stakeholder questions: {len(stakeholder_questions)}")
        except Exception as e:
            print(f"Stakeholder questions failed: {e}")
            traceback.print_exc()
            return
            
        print("\n=== STEP 8: MIGRATION RECOMMENDATIONS ===")
        try:
            migration_recommendations = await tech_debt_analysis_agent._generate_migration_recommendations(
                prioritized_debt, "6-12 months"
            )
            print(f"Migration recommendations: {len(migration_recommendations)}")
        except Exception as e:
            print(f"Migration recommendations failed: {e}")
            traceback.print_exc()
            return
            
        print("\n✅ All steps completed successfully!")
        
    except Exception as e:
        print(f"Overall error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_full_analysis()) 