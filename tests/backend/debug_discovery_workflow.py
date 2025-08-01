#!/usr/bin/env python3
"""
Discovery Workflow End-to-End Debugger

This script tests the complete discovery workflow to identify the root cause
of the disconnect between agentic processing and user-visible results.
"""

import asyncio
import csv
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

# Add the backend directory to the path
sys.path.append("/app")

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.client_account import ClientAccount, Engagement
from app.models.data_import import DataImport, RawImportRecord

# Application model is not used - Asset model handles all assets
APPLICATION_AVAILABLE = False
Application = None

# Engagement model availability
ENGAGEMENT_AVAILABLE = True


class DiscoveryWorkflowDebugger:
    """Debug the complete discovery workflow from CSV to dashboard."""

    def __init__(self):
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "database_baseline": {},
            "csv_upload": {},
            "crewai_processing": {},
            "database_final": {},
            "api_tests": {},
            "workflow_gaps": [],
            "errors": [],
        }

    async def run_complete_debug(self):
        """Run comprehensive debugging of the discovery workflow."""
        print("🔍 Starting Discovery Workflow Debug Analysis")
        print("=" * 80)

        try:
            # Phase 1: Database baseline analysis
            await self.analyze_database_baseline()

            # Phase 2: Create test data and test upload flow
            await self.test_csv_upload_flow()

            # Phase 3: Test CrewAI processing manually
            await self.test_crewai_processing()

            # Phase 4: Analyze final database state
            await self.analyze_database_final()

            # Phase 5: Test all discovery APIs
            await self.test_discovery_apis()

            # Phase 6: Identify workflow gaps
            await self.identify_workflow_gaps()

            # Phase 7: Generate diagnostic report
            await self.generate_diagnostic_report()

        except Exception as e:
            self.test_results["errors"].append(f"Debug execution failed: {e}")
            print(f"❌ Debug execution failed: {e}")

        finally:
            print(f"\n📊 Debug completed at: {datetime.now().isoformat()}")

    async def analyze_database_baseline(self):
        """Analyze current database state as baseline."""
        print("\n📊 Phase 1: Database Baseline Analysis")
        print("-" * 50)

        try:
            async with AsyncSessionLocal() as session:
                # Get client account and engagement info
                client_result = await session.execute(select(ClientAccount).limit(1))
                client_account = client_result.scalar_one_or_none()

                engagement = None
                if ENGAGEMENT_AVAILABLE:
                    engagement_result = await session.execute(
                        select(Engagement).limit(1)
                    )
                    engagement = engagement_result.scalar_one_or_none()

                # Count all major entities
                asset_count = await session.execute(select(func.count(Asset.id)))
                total_assets = asset_count.scalar()

                import_count = await session.execute(select(func.count(DataImport.id)))
                total_imports = import_count.scalar()

                raw_count = await session.execute(
                    select(func.count(RawImportRecord.id))
                )
                total_raw = raw_count.scalar()

                total_apps = 0
                if APPLICATION_AVAILABLE:
                    app_count = await session.execute(
                        select(func.count(Application.id))
                    )
                    total_apps = app_count.scalar()

                # Get sample recent assets
                recent_assets_result = await session.execute(
                    select(Asset).order_by(Asset.created_at.desc()).limit(3)
                )
                recent_assets = recent_assets_result.scalars().all()

                # Get sample recent imports
                recent_imports_result = await session.execute(
                    select(DataImport).order_by(DataImport.created_at.desc()).limit(3)
                )
                recent_imports = recent_imports_result.scalars().all()

                baseline = {
                    "client_account_id": (
                        str(client_account.id) if client_account else None
                    ),
                    "engagement_id": str(engagement.id) if engagement else None,
                    "total_assets": total_assets,
                    "total_imports": total_imports,
                    "total_raw_records": total_raw,
                    "total_applications": total_apps,
                    "recent_assets": [
                        {
                            "id": str(asset.id),
                            "name": asset.name,
                            "asset_type": asset.asset_type,
                            "discovery_source": asset.discovery_source,
                            "discovery_method": asset.discovery_method,
                            "workflow_status": getattr(asset, "workflow_status", None),
                            "discovery_status": getattr(
                                asset, "discovery_status", None
                            ),
                            "created_at": asset.created_at.isoformat(),
                        }
                        for asset in recent_assets
                    ],
                    "recent_imports": [
                        {
                            "id": str(imp.id),
                            "original_filename": imp.original_filename,
                            "total_records": imp.total_records,
                            "processed_records": imp.processed_records,
                            "status": imp.status,
                            "created_at": imp.created_at.isoformat(),
                        }
                        for imp in recent_imports
                    ],
                    "timestamp": datetime.now().isoformat(),
                }

                self.test_results["database_baseline"] = baseline

                print("🗄️ Database Baseline:")
                print(f"   Client Account: {baseline['client_account_id']}")
                print(f"   Engagement: {baseline['engagement_id']}")
                print(f"   Assets: {total_assets}")
                print(f"   Data Imports: {total_imports}")
                print(f"   Raw Import Records: {total_raw}")
                print(f"   Applications: {total_apps}")
                print(f"   Recent Assets: {len(recent_assets)}")
                print(f"   Recent Imports: {len(recent_imports)}")

                if recent_assets:
                    sample = recent_assets[0]
                    print(
                        f"   Sample Asset: {sample.name} ({sample.asset_type}) - {sample.discovery_method}"
                    )

        except Exception as e:
            error_msg = f"Failed to analyze database baseline: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

    async def test_csv_upload_flow(self):
        """Test CSV upload flow end-to-end."""
        print("\n📄 Phase 2: Testing CSV Upload Flow")
        print("-" * 50)

        try:
            # Create test CSV data
            test_data = [
                {
                    "NAME": "debug-web-server-01",
                    "HOSTNAME": "debug-web01.test.com",
                    "IP_ADDRESS": "192.168.1.10",
                    "CITYPE": "server",
                    "ENVIRONMENT": "Test",
                    "OS": "Ubuntu 22.04",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": "Debug User",
                    "LOCATION": "Test-DC",
                },
                {
                    "NAME": "debug-database-01",
                    "HOSTNAME": "debug-db01.test.com",
                    "IP_ADDRESS": "192.168.1.20",
                    "CITYPE": "database",
                    "ENVIRONMENT": "Test",
                    "OS": "CentOS 8",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": "Debug User",
                    "LOCATION": "Test-DC",
                },
            ]

            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as tmp_file:
                csv_path = tmp_file.name
                fieldnames = test_data[0].keys()
                writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(test_data)

            print(f"📄 Created test CSV: {csv_path}")
            print(f"📊 Test data records: {len(test_data)}")

            # Test CSV upload via API
            base_url = "http://localhost:8000"

            async with aiohttp.ClientSession() as session:
                # Test file upload
                with open(csv_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file", f, filename="debug_test.csv", content_type="text/csv"
                    )

                    async with session.post(
                        f"{base_url}/api/v1/data-import/upload-csv", data=data
                    ) as response:
                        if response.status == 200:
                            upload_result = await response.json()

                            self.test_results["csv_upload"] = {
                                "success": True,
                                "import_session_id": upload_result.get(
                                    "import_session_id"
                                ),
                                "total_records": upload_result.get("total_records"),
                                "message": upload_result.get("message"),
                                "test_data_count": len(test_data),
                            }

                            print("✅ CSV Upload successful:")
                            print(
                                f"   Import Session ID: {upload_result.get('import_session_id')}"
                            )
                            print(
                                f"   Total Records: {upload_result.get('total_records')}"
                            )
                            print(f"   Message: {upload_result.get('message')}")

                        else:
                            error_text = await response.text()
                            self.test_results["csv_upload"] = {
                                "success": False,
                                "status": response.status,
                                "error": error_text,
                            }
                            print(
                                f"❌ CSV Upload failed: {response.status} - {error_text}"
                            )

            # Clean up temp file
            os.unlink(csv_path)

        except Exception as e:
            error_msg = f"Failed to test CSV upload flow: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

    async def test_crewai_processing(self):
        """Test CrewAI processing of uploaded data."""
        print("\n🤖 Phase 3: Testing CrewAI Processing")
        print("-" * 50)

        try:
            # Get the import session ID from upload
            import_session_id = self.test_results.get("csv_upload", {}).get(
                "import_session_id"
            )

            if not import_session_id:
                print(
                    "⚠️ No import session ID available, checking for recent imports..."
                )

                # Find most recent import session
                async with AsyncSessionLocal() as session:
                    recent_import_result = await session.execute(
                        select(DataImport)
                        .order_by(DataImport.created_at.desc())
                        .limit(1)
                    )
                    recent_import = recent_import_result.scalar_one_or_none()

                    if recent_import:
                        import_session_id = str(recent_import.id)
                        print(f"🔍 Found recent import session: {import_session_id}")
                    else:
                        self.test_results["crewai_processing"] = {
                            "success": False,
                            "error": "No import session available for processing",
                        }
                        print("❌ No import sessions found")
                        return

            # Test CrewAI processing via API
            base_url = "http://localhost:8000"

            async with aiohttp.ClientSession() as session:
                # Test process-raw-to-assets endpoint
                async with session.post(
                    f"{base_url}/api/v1/data-import/process-raw-to-assets",
                    json={"import_session_id": import_session_id},
                ) as response:
                    if response.status == 200:
                        process_result = await response.json()

                        self.test_results["crewai_processing"] = {
                            "success": True,
                            "import_session_id": import_session_id,
                            "result": process_result,
                            "assets_created": process_result.get("assets_created", 0),
                            "message": process_result.get("message"),
                        }

                        print("✅ CrewAI Processing successful:")
                        print(f"   Import Session: {import_session_id}")
                        print(
                            f"   Assets Created: {process_result.get('assets_created', 0)}"
                        )
                        print(f"   Message: {process_result.get('message')}")

                    else:
                        error_text = await response.text()
                        self.test_results["crewai_processing"] = {
                            "success": False,
                            "import_session_id": import_session_id,
                            "status": response.status,
                            "error": error_text,
                        }
                        print(
                            f"❌ CrewAI Processing failed: {response.status} - {error_text}"
                        )

        except Exception as e:
            error_msg = f"Failed to test CrewAI processing: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

    async def analyze_database_final(self):
        """Analyze database state after processing."""
        print("\n🗄️ Phase 4: Final Database Analysis")
        print("-" * 50)

        try:
            async with AsyncSessionLocal() as session:
                # Count entities after processing
                asset_count = await session.execute(select(func.count(Asset.id)))
                total_assets_after = asset_count.scalar()

                import_count = await session.execute(select(func.count(DataImport.id)))
                total_imports_after = import_count.scalar()

                raw_count = await session.execute(
                    select(func.count(RawImportRecord.id))
                )
                total_raw_after = raw_count.scalar()

                if APPLICATION_AVAILABLE:
                    app_count = await session.execute(
                        select(func.count(Application.id))
                    )
                    app_count.scalar()

                # Get assets created in the last 10 minutes
                ten_minutes_ago = datetime.now() - timedelta(minutes=10)
                new_assets_result = await session.execute(
                    select(Asset)
                    .where(Asset.created_at >= ten_minutes_ago)
                    .order_by(Asset.created_at.desc())
                )
                new_assets = new_assets_result.scalars().all()

                # Get debug test assets specifically
                debug_assets_result = await session.execute(
                    select(Asset)
                    .where(Asset.name.like("debug-%"))
                    .order_by(Asset.created_at.desc())
                )
                debug_assets = debug_assets_result.scalars().all()

                # Compare with baseline
                baseline = self.test_results["database_baseline"]

                final_analysis = {
                    "total_assets_before": baseline["total_assets"],
                    "total_assets_after": total_assets_after,
                    "assets_added": total_assets_after - baseline["total_assets"],
                    "total_imports_before": baseline["total_imports"],
                    "total_imports_after": total_imports_after,
                    "imports_added": total_imports_after - baseline["total_imports"],
                    "total_raw_before": baseline["total_raw_records"],
                    "total_raw_after": total_raw_after,
                    "raw_added": total_raw_after - baseline["total_raw_records"],
                    "new_assets_last_10min": [
                        {
                            "id": str(asset.id),
                            "name": asset.name,
                            "asset_type": asset.asset_type,
                            "discovery_source": asset.discovery_source,
                            "discovery_method": asset.discovery_method,
                            "workflow_status": getattr(asset, "workflow_status", None),
                            "discovery_status": getattr(
                                asset, "discovery_status", None
                            ),
                            "created_at": asset.created_at.isoformat(),
                        }
                        for asset in new_assets
                    ],
                    "debug_test_assets": [
                        {
                            "id": str(asset.id),
                            "name": asset.name,
                            "asset_type": asset.asset_type,
                            "discovery_source": asset.discovery_source,
                            "discovery_method": asset.discovery_method,
                            "workflow_status": getattr(asset, "workflow_status", None),
                            "discovery_status": getattr(
                                asset, "discovery_status", None
                            ),
                            "created_at": asset.created_at.isoformat(),
                        }
                        for asset in debug_assets
                    ],
                    "timestamp": datetime.now().isoformat(),
                }

                self.test_results["database_final"] = final_analysis

                print("📊 Database Changes:")
                print(
                    f"   Assets: {baseline['total_assets']} → {total_assets_after} (+{total_assets_after - baseline['total_assets']})"
                )
                print(
                    f"   Imports: {baseline['total_imports']} → {total_imports_after} (+{total_imports_after - baseline['total_imports']})"
                )
                print(
                    f"   Raw Records: {baseline['total_raw_records']} → {total_raw_after} (+{total_raw_after - baseline['total_raw_records']})"
                )
                print(f"   New Assets (10min): {len(new_assets)}")
                print(f"   Debug Test Assets: {len(debug_assets)}")

                if debug_assets:
                    for asset in debug_assets:
                        print(
                            f"   Debug Asset: {asset.name} ({asset.asset_type}) - {asset.discovery_method} - {asset.created_at}"
                        )

        except Exception as e:
            error_msg = f"Failed to analyze final database state: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

    async def test_discovery_apis(self):
        """Test all discovery-related APIs."""
        print("\n🔌 Phase 5: Testing Discovery APIs")
        print("-" * 50)

        base_url = "http://localhost:8000"

        apis_to_test = [
            {
                "name": "discovery_metrics",
                "url": f"{base_url}/api/v1/discovery/assets/discovery-metrics",
                "method": "GET",
            },
            {
                "name": "assets_list",
                "url": f"{base_url}/api/v1/discovery/assets",
                "method": "GET",
            },
            {
                "name": "applications_list",
                "url": f"{base_url}/api/v1/discovery/applications",
                "method": "GET",
            },
            {"name": "health_check", "url": f"{base_url}/health", "method": "GET"},
        ]

        api_results = {}

        async with aiohttp.ClientSession() as session:
            for api in apis_to_test:
                try:
                    print(f"🔌 Testing {api['name']}: {api['url']}")

                    async with session.request(api["method"], api["url"]) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                api_results[api["name"]] = {
                                    "success": True,
                                    "status": response.status,
                                    "data": data,
                                }

                                # Extract key metrics for discovery APIs
                                if api["name"] == "discovery_metrics":
                                    total_assets = data.get("totalAssets", 0)
                                    total_apps = data.get("totalApplications", 0)
                                    print(
                                        f"   ✅ Discovery Metrics: {total_assets} assets, {total_apps} applications"
                                    )

                                elif api["name"] == "assets_list":
                                    assets = data.get("assets", [])
                                    print(
                                        f"   ✅ Assets List: {len(assets)} assets returned"
                                    )

                                elif api["name"] == "applications_list":
                                    apps = data.get("applications", [])
                                    print(
                                        f"   ✅ Applications List: {len(apps)} applications returned"
                                    )

                                else:
                                    print(f"   ✅ {api['name']}: Success")

                            except json.JSONDecodeError:
                                text_data = await response.text()
                                api_results[api["name"]] = {
                                    "success": True,
                                    "status": response.status,
                                    "data": (
                                        text_data[:200] + "..."
                                        if len(text_data) > 200
                                        else text_data
                                    ),
                                }
                                print(
                                    f"   ✅ {api['name']}: Success (non-JSON response)"
                                )

                        else:
                            error_text = await response.text()
                            api_results[api["name"]] = {
                                "success": False,
                                "status": response.status,
                                "error": (
                                    error_text[:200] + "..."
                                    if len(error_text) > 200
                                    else error_text
                                ),
                            }
                            print(
                                f"   ❌ {api['name']}: {response.status} - {error_text[:100]}"
                            )

                except Exception as e:
                    api_results[api["name"]] = {"success": False, "error": str(e)}
                    print(f"   ❌ {api['name']}: Exception - {e}")

        self.test_results["api_tests"] = api_results

    async def identify_workflow_gaps(self):
        """Identify gaps in the workflow based on test results."""
        print("\n🔍 Phase 6: Identifying Workflow Gaps")
        print("-" * 50)

        gaps = []

        # Check CSV upload → CrewAI processing gap
        csv_success = self.test_results.get("csv_upload", {}).get("success", False)
        crewai_success = self.test_results.get("crewai_processing", {}).get(
            "success", False
        )

        if csv_success and not crewai_success:
            gaps.append(
                {
                    "type": "CSV_TO_CREWAI_GAP",
                    "description": "CSV upload successful but CrewAI processing failed",
                    "impact": "Raw data stored but not processed into assets",
                    "recommendation": "Debug CrewAI Flow processing endpoint",
                }
            )

        # Check CrewAI processing → database persistence gap
        assets_created = self.test_results.get("crewai_processing", {}).get(
            "assets_created", 0
        )
        actual_assets_added = self.test_results.get("database_final", {}).get(
            "assets_added", 0
        )

        if crewai_success and assets_created > 0 and actual_assets_added == 0:
            gaps.append(
                {
                    "type": "CREWAI_TO_DATABASE_GAP",
                    "description": f"CrewAI reported {assets_created} assets created but no assets found in database",
                    "impact": "Processing appears successful but no persistent data",
                    "recommendation": "Check database transaction handling in CrewAI Flow",
                }
            )

        # Check database → API response gap
        api_discovery_metrics = self.test_results.get("api_tests", {}).get(
            "discovery_metrics", {}
        )
        api_assets_list = self.test_results.get("api_tests", {}).get("assets_list", {})

        if api_discovery_metrics.get("success") and api_assets_list.get("success"):
            api_asset_count = api_discovery_metrics.get("data", {}).get(
                "totalAssets", 0
            )
            db_asset_count = self.test_results.get("database_final", {}).get(
                "total_assets_after", 0
            )

            if db_asset_count > 0 and api_asset_count == 0:
                gaps.append(
                    {
                        "type": "DATABASE_TO_API_GAP",
                        "description": f"Database has {db_asset_count} assets but API returns {api_asset_count}",
                        "impact": "Data exists but not accessible via APIs",
                        "recommendation": "Check API context headers and client account scoping",
                    }
                )

        # Check API → frontend display gap (inferred)
        if api_discovery_metrics.get("success"):
            api_data = api_discovery_metrics.get("data", {})
            if api_data.get("totalAssets", 0) > 0:
                # We can't directly test frontend without browser, but we can note the gap
                gaps.append(
                    {
                        "type": "API_TO_FRONTEND_GAP",
                        "description": "API returns asset data but frontend may show zeros (requires frontend verification)",
                        "impact": "Backend data not reflected in user interface",
                        "recommendation": "Check frontend API calls, CORS, and response parsing",
                    }
                )

        # Check application discovery gap
        api_apps = self.test_results.get("api_tests", {}).get("applications_list", {})
        if api_apps.get("success"):
            app_count = len(api_apps.get("data", {}).get("applications", []))
            if app_count == 0:
                gaps.append(
                    {
                        "type": "APPLICATION_DISCOVERY_GAP",
                        "description": "No applications discovered despite having assets",
                        "impact": "Asset-to-application grouping not working",
                        "recommendation": "Check application discovery agents and portfolio logic",
                    }
                )

        self.test_results["workflow_gaps"] = gaps

        print(f"🔍 Workflow Gaps Identified: {len(gaps)}")
        for i, gap in enumerate(gaps, 1):
            print(f"   {i}. {gap['type']}: {gap['description']}")
            print(f"      Impact: {gap['impact']}")
            print(f"      Recommendation: {gap['recommendation']}")
            print()

    async def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report."""
        print("\n📋 Phase 7: Generating Diagnostic Report")
        print("-" * 50)

        try:
            # Save detailed results to JSON
            report_path = Path("discovery_workflow_debug_report.json")
            with open(report_path, "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)

            # Generate executive summary
            print("\n📊 DISCOVERY WORKFLOW DEBUG SUMMARY")
            print("=" * 80)

            # Test results overview
            csv_success = self.test_results.get("csv_upload", {}).get("success", False)
            crewai_success = self.test_results.get("crewai_processing", {}).get(
                "success", False
            )
            api_count = len(
                [
                    api
                    for api in self.test_results.get("api_tests", {}).values()
                    if api.get("success")
                ]
            )
            total_apis = len(self.test_results.get("api_tests", {}))
            gap_count = len(self.test_results.get("workflow_gaps", []))

            print(f"CSV Upload Success: {'✅' if csv_success else '❌'}")
            print(f"CrewAI Processing Success: {'✅' if crewai_success else '❌'}")
            print(f"API Tests Passed: {api_count}/{total_apis}")
            print(f"Workflow Gaps Identified: {gap_count}")

            # Database changes summary
            final_db = self.test_results.get("database_final", {})
            if final_db:
                print("\nDatabase Changes During Test:")
                print(f"   Assets Added: {final_db.get('assets_added', 0)}")
                print(f"   Imports Added: {final_db.get('imports_added', 0)}")
                print(f"   Raw Records Added: {final_db.get('raw_added', 0)}")
                print(
                    f"   Debug Test Assets Created: {len(final_db.get('debug_test_assets', []))}"
                )

            # Critical findings
            print("\n🚨 CRITICAL FINDINGS:")

            # Check for mock success vs real persistence
            crewai_assets_claimed = self.test_results.get("crewai_processing", {}).get(
                "assets_created", 0
            )
            actual_assets_added = final_db.get("assets_added", 0)

            if (
                crewai_success
                and crewai_assets_claimed > 0
                and actual_assets_added == 0
            ):
                print(
                    f"   🚨 MOCK SUCCESS DETECTED: CrewAI claims {crewai_assets_claimed} assets created but 0 actually persisted"
                )
                print("      This confirms the user's suspicion of mock functionality!")

            elif crewai_success and actual_assets_added > 0:
                print(
                    f"   ✅ REAL PERSISTENCE CONFIRMED: {actual_assets_added} assets actually created"
                )

            else:
                print(
                    "   ⚠️ PROCESSING FAILURE: CrewAI processing did not complete successfully"
                )

            # API availability
            discovery_metrics_working = (
                self.test_results.get("api_tests", {})
                .get("discovery_metrics", {})
                .get("success", False)
            )
            if discovery_metrics_working:
                metrics_data = (
                    self.test_results.get("api_tests", {})
                    .get("discovery_metrics", {})
                    .get("data", {})
                )
                api_assets = metrics_data.get("totalAssets", 0)
                api_apps = metrics_data.get("totalApplications", 0)

                print(
                    f"   🔌 API RESPONSES: {api_assets} assets, {api_apps} applications via discovery-metrics"
                )

                if api_assets == 0 and final_db.get("total_assets_after", 0) > 0:
                    print(
                        "   🚨 API-DATABASE DISCONNECT: Database has assets but API returns 0"
                    )

            # Workflow gaps summary
            if gap_count > 0:
                print("\n🔧 WORKFLOW GAPS TO FIX:")
                for gap in self.test_results.get("workflow_gaps", []):
                    print(f"   - {gap['type']}: {gap['description']}")

            # Next steps
            print("\n🎯 RECOMMENDED NEXT STEPS:")
            if gap_count > 0:
                print(f"   1. Fix the {gap_count} identified workflow gaps")
                for gap in self.test_results.get("workflow_gaps", [])[:3]:  # Top 3
                    print(f"      - {gap['recommendation']}")
            else:
                print("   1. All major workflow components appear functional")
                print("   2. Check frontend integration and user interface display")

            print(f"\n📁 Detailed report saved to: {report_path}")

        except Exception as e:
            print(f"❌ Failed to generate diagnostic report: {e}")


async def main():
    """Run the discovery workflow debugger."""
    debugger = DiscoveryWorkflowDebugger()
    await debugger.run_complete_debug()


if __name__ == "__main__":
    asyncio.run(main())
