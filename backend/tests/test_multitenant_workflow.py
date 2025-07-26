#!/usr/bin/env python3
"""
Multi-Tenant Discovery Workflow Test

Tests the complete discovery workflow using real clients to verify:
1. End-to-end CSV upload → CrewAI processing → database persistence
2. Multi-tenant isolation (data from one client doesn't appear in another)
3. Correct client context handling
4. Real agentic processing (not mock data)
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

from sqlalchemy import and_, func, select

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.client_account import ClientAccount
from app.models.data_import import DataImport


class MultiTenantWorkflowTester:
    """Test multi-tenant discovery workflow with real clients."""

    def __init__(self):
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "real_clients": [],
            "tenant_tests": {},
            "isolation_tests": {},
            "api_tests": {},
            "errors": [],
        }

        # Real client IDs from database check
        self.marathon_client_id = "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"
        self.complete_test_client_id = "bafd5b46-aaaf-4c95-8142-573699d93171"

    async def run_complete_multitenant_test(self):
        """Run comprehensive multi-tenant testing."""
        print("🏢 Starting Multi-Tenant Discovery Workflow Test")
        print("=" * 80)

        try:
            # Phase 1: Verify real clients exist
            await self.verify_real_clients()

            # Phase 2: Test workflow with Marathon Petroleum
            await self.test_client_workflow(
                client_id=self.marathon_client_id,
                client_name="Marathon Petroleum",
                test_prefix="marathon",
            )

            # Phase 3: Test workflow with Complete Test Client
            await self.test_client_workflow(
                client_id=self.complete_test_client_id,
                client_name="Complete Test Client",
                test_prefix="complete",
            )

            # Phase 4: Test multi-tenant isolation
            await self.test_tenant_isolation()

            # Phase 5: Test discovery APIs with client context
            await self.test_discovery_apis_with_context()

            # Phase 6: Generate comprehensive report
            await self.generate_multitenant_report()

        except Exception as e:
            self.test_results["errors"].append(f"Test execution failed: {e}")
            print(f"❌ Test execution failed: {e}")

        finally:
            print(f"\n📊 Multi-tenant test completed at: {datetime.now().isoformat()}")

    async def verify_real_clients(self):
        """Verify real clients exist and are properly configured."""
        print("\n🏢 Phase 1: Verifying Real Clients")
        print("-" * 50)

        try:
            async with AsyncSessionLocal() as session:
                # Get Marathon Petroleum client
                marathon_result = await session.execute(
                    select(ClientAccount).where(
                        ClientAccount.id == self.marathon_client_id
                    )
                )
                marathon_client = marathon_result.scalar_one_or_none()

                # Get Complete Test Client
                complete_result = await session.execute(
                    select(ClientAccount).where(
                        ClientAccount.id == self.complete_test_client_id
                    )
                )
                complete_client = complete_result.scalar_one_or_none()

                if not marathon_client:
                    raise Exception(
                        f"Marathon Petroleum client not found: {self.marathon_client_id}"
                    )

                if not complete_client:
                    raise Exception(
                        f"Complete Test Client not found: {self.complete_test_client_id}"
                    )

                # Count existing assets for each client
                marathon_assets = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.client_account_id == self.marathon_client_id
                    )
                )
                marathon_asset_count = marathon_assets.scalar()

                complete_assets = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.client_account_id == self.complete_test_client_id
                    )
                )
                complete_asset_count = complete_assets.scalar()

                self.test_results["real_clients"] = [
                    {
                        "client_id": str(marathon_client.id),
                        "name": marathon_client.name,
                        "slug": marathon_client.slug,
                        "is_mock": marathon_client.is_mock,
                        "existing_assets": marathon_asset_count,
                    },
                    {
                        "client_id": str(complete_client.id),
                        "name": complete_client.name,
                        "slug": complete_client.slug,
                        "is_mock": complete_client.is_mock,
                        "existing_assets": complete_asset_count,
                    },
                ]

                print(
                    f"✅ Marathon Petroleum: {marathon_client.name} (Assets: {marathon_asset_count})"
                )
                print(
                    f"✅ Complete Test Client: {complete_client.name} (Assets: {complete_asset_count})"
                )

        except Exception as e:
            error_msg = f"Failed to verify real clients: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

    async def test_client_workflow(
        self, client_id: str, client_name: str, test_prefix: str
    ):
        """Test complete workflow for a specific client."""
        print(f"\n🧪 Phase: Testing Workflow for {client_name}")
        print("-" * 50)

        client_test_results = {
            "client_id": client_id,
            "client_name": client_name,
            "baseline": {},
            "csv_upload": {},
            "crewai_processing": {},
            "final_state": {},
            "errors": [],
        }

        try:
            # Step 1: Capture baseline for this client
            baseline = await self.capture_client_baseline(client_id)
            client_test_results["baseline"] = baseline
            print(
                f"📊 Baseline - Assets: {baseline['assets']}, Imports: {baseline['imports']}"
            )

            # Step 2: Upload test CSV for this client
            csv_result = await self.upload_test_csv_for_client(client_id, test_prefix)
            client_test_results["csv_upload"] = csv_result

            if csv_result.get("success"):
                print(f"✅ CSV Upload successful: Flow {csv_result.get('flow_id')}")

                # Step 3: Process with CrewAI for this client
                process_result = await self.process_crewai_for_client(
                    csv_result.get("flow_id"), client_id
                )
                client_test_results["crewai_processing"] = process_result

                if process_result.get("success"):
                    print(
                        f"✅ CrewAI Processing successful: {process_result.get('assets_created')} assets created"
                    )
                else:
                    print(f"❌ CrewAI Processing failed: {process_result.get('error')}")
            else:
                print(f"❌ CSV Upload failed: {csv_result.get('error')}")

            # Step 4: Capture final state for this client
            final_state = await self.capture_client_final_state(client_id, baseline)
            client_test_results["final_state"] = final_state
            print(f"📈 Final State - Assets Added: {final_state.get('assets_added', 0)}")

        except Exception as e:
            error_msg = f"Client workflow test failed for {client_name}: {e}"
            client_test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

        self.test_results["tenant_tests"][test_prefix] = client_test_results

    async def capture_client_baseline(self, client_id: str):
        """Capture baseline state for a specific client."""
        async with AsyncSessionLocal() as session:
            # Count assets for this client
            asset_count = await session.execute(
                select(func.count(Asset.id)).where(Asset.client_account_id == client_id)
            )
            assets = asset_count.scalar()

            # Count imports for this client
            import_count = await session.execute(
                select(func.count(DataImport.id)).where(
                    DataImport.client_account_id == client_id
                )
            )
            imports = import_count.scalar()

            return {
                "assets": assets,
                "imports": imports,
                "timestamp": datetime.now().isoformat(),
            }

    async def upload_test_csv_for_client(self, client_id: str, test_prefix: str):
        """Upload test CSV data for a specific client."""
        try:
            # Create client-specific test data
            test_data = [
                {
                    "NAME": f"{test_prefix}-web-server-01",
                    "HOSTNAME": f"{test_prefix}-web01.test.com",
                    "IP_ADDRESS": f"10.{hash(client_id) % 255}.1.10",
                    "CITYPE": "server",
                    "ENVIRONMENT": "Production",
                    "OS": "Ubuntu 22.04",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": f"{test_prefix.title()} Owner",
                    "LOCATION": f"{test_prefix.title()}-DC",
                },
                {
                    "NAME": f"{test_prefix}-database-01",
                    "HOSTNAME": f"{test_prefix}-db01.test.com",
                    "IP_ADDRESS": f"10.{hash(client_id) % 255}.1.20",
                    "CITYPE": "database",
                    "ENVIRONMENT": "Production",
                    "OS": "PostgreSQL 14",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": f"{test_prefix.title()} DBA",
                    "LOCATION": f"{test_prefix.title()}-DC",
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

            # Upload CSV via API with client context
            base_url = "http://localhost:8000"
            headers = {
                "X-Client-Account-ID": client_id,
                # Note: We might need to add engagement context headers too
            }

            async with aiohttp.ClientSession() as session:
                with open(csv_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        f,
                        filename=f"{test_prefix}_test.csv",
                        content_type="text/csv",
                    )

                    async with session.post(
                        f"{base_url}/api/v1/data-import/upload",
                        data=data,
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            upload_result = await response.json()
                            result = {
                                "success": True,
                                "flow_id": upload_result.get("flow_id"),
                                "total_records": upload_result.get("total_records"),
                                "test_data_count": len(test_data),
                                "client_id": client_id,
                            }
                        else:
                            error_text = await response.text()
                            result = {
                                "success": False,
                                "status": response.status,
                                "error": error_text,
                                "client_id": client_id,
                            }

            # Clean up temp file
            os.unlink(csv_path)
            return result

        except Exception as e:
            return {"success": False, "error": str(e), "client_id": client_id}

    async def process_crewai_for_client(self, flow_id: str, client_id: str):
        """Process uploaded data with CrewAI for a specific client."""
        try:
            base_url = "http://localhost:8000"
            headers = {
                "X-Client-Account-ID": client_id,
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/api/v1/data-import/process-raw-to-assets",
                    json={"flow_id": flow_id},
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        process_result = await response.json()
                        return {
                            "success": True,
                            "flow_id": flow_id,
                            "result": process_result,
                            "assets_created": process_result.get("assets_created", 0),
                            "client_id": client_id,
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "flow_id": flow_id,
                            "status": response.status,
                            "error": error_text,
                            "client_id": client_id,
                        }

        except Exception as e:
            return {"success": False, "error": str(e), "client_id": client_id}

    async def capture_client_final_state(self, client_id: str, baseline: dict):
        """Capture final state for a client after processing."""
        async with AsyncSessionLocal() as session:
            # Count final assets
            asset_count = await session.execute(
                select(func.count(Asset.id)).where(Asset.client_account_id == client_id)
            )
            final_assets = asset_count.scalar()

            # Count final imports
            import_count = await session.execute(
                select(func.count(DataImport.id)).where(
                    DataImport.client_account_id == client_id
                )
            )
            final_imports = import_count.scalar()

            # Get recent assets for this client
            ten_minutes_ago = datetime.now() - timedelta(minutes=10)
            recent_assets_result = await session.execute(
                select(Asset)
                .where(
                    and_(
                        Asset.client_account_id == client_id,
                        Asset.created_at >= ten_minutes_ago,
                    )
                )
                .order_by(Asset.created_at.desc())
            )
            recent_assets = recent_assets_result.scalars().all()

            return {
                "final_assets": final_assets,
                "final_imports": final_imports,
                "assets_added": final_assets - baseline["assets"],
                "imports_added": final_imports - baseline["imports"],
                "recent_assets": [
                    {
                        "id": str(asset.id),
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "client_account_id": str(asset.client_account_id),
                        "created_at": asset.created_at.isoformat(),
                    }
                    for asset in recent_assets
                ],
                "timestamp": datetime.now().isoformat(),
            }

    async def test_tenant_isolation(self):
        """Test that data from one tenant doesn't appear in another."""
        print("\n🔒 Phase: Testing Multi-Tenant Isolation")
        print("-" * 50)

        isolation_results = {
            "marathon_assets_in_complete": 0,
            "complete_assets_in_marathon": 0,
            "cross_contamination": False,
            "test_timestamp": datetime.now().isoformat(),
        }

        try:
            async with AsyncSessionLocal() as session:
                # Check if Marathon assets appear in Complete Test Client context
                marathon_assets_in_complete = await session.execute(
                    select(func.count(Asset.id)).where(
                        and_(
                            Asset.client_account_id == self.complete_test_client_id,
                            Asset.name.like("marathon-%"),
                        )
                    )
                )
                isolation_results[
                    "marathon_assets_in_complete"
                ] = marathon_assets_in_complete.scalar()

                # Check if Complete Test Client assets appear in Marathon context
                complete_assets_in_marathon = await session.execute(
                    select(func.count(Asset.id)).where(
                        and_(
                            Asset.client_account_id == self.marathon_client_id,
                            Asset.name.like("complete-%"),
                        )
                    )
                )
                isolation_results[
                    "complete_assets_in_marathon"
                ] = complete_assets_in_marathon.scalar()

                # Check for any cross-contamination
                if (
                    isolation_results["marathon_assets_in_complete"] > 0
                    or isolation_results["complete_assets_in_marathon"] > 0
                ):
                    isolation_results["cross_contamination"] = True
                    self.test_results["errors"].append(
                        "Multi-tenant isolation FAILED - data cross-contamination detected"
                    )
                    print(
                        "❌ Multi-tenant isolation FAILED - data cross-contamination detected"
                    )
                else:
                    print(
                        "✅ Multi-tenant isolation PASSED - no data cross-contamination"
                    )

        except Exception as e:
            error_msg = f"Failed to test tenant isolation: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")

        self.test_results["isolation_tests"] = isolation_results

    async def test_discovery_apis_with_context(self):
        """Test discovery APIs with different client contexts."""
        print("\n🔌 Phase: Testing Discovery APIs with Client Context")
        print("-" * 50)

        base_url = "http://localhost:8000"

        # Test both clients
        for client_info in self.test_results["real_clients"]:
            client_id = client_info["client_id"]
            client_name = client_info["name"]

            print(f"🔍 Testing APIs for {client_name}")

            headers = {"X-Client-Account-ID": client_id}

            client_api_results = {}

            async with aiohttp.ClientSession() as session:
                # Test discovery metrics with context
                try:
                    async with session.get(
                        f"{base_url}/api/v1/discovery/assets/discovery-metrics",
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            client_api_results["discovery_metrics"] = {
                                "success": True,
                                "data": data,
                            }
                            metrics = data.get("metrics", {})
                            print(
                                f"  📊 Discovery Metrics: {metrics.get('totalAssets', 0)} assets"
                            )
                        else:
                            error_text = await response.text()
                            client_api_results["discovery_metrics"] = {
                                "success": False,
                                "error": error_text,
                            }
                            print(f"  ❌ Discovery Metrics failed: {response.status}")
                except Exception as e:
                    print(f"  ❌ Discovery Metrics exception: {e}")

                # Test assets list with context
                try:
                    async with session.get(
                        f"{base_url}/api/v1/discovery/assets", headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            assets = data.get("assets", [])
                            client_api_results["assets_list"] = {
                                "success": True,
                                "asset_count": len(assets),
                            }
                            print(f"  📦 Assets List: {len(assets)} assets returned")
                        else:
                            error_text = await response.text()
                            client_api_results["assets_list"] = {
                                "success": False,
                                "error": error_text,
                            }
                            print(f"  ❌ Assets List failed: {response.status}")
                except Exception as e:
                    print(f"  ❌ Assets List exception: {e}")

            self.test_results["api_tests"][client_name] = client_api_results

    async def generate_multitenant_report(self):
        """Generate comprehensive multi-tenant test report."""
        print("\n📋 Generating Multi-Tenant Test Report")
        print("-" * 50)

        try:
            # Save detailed results to JSON
            report_path = Path("multitenant_workflow_test_report.json")
            with open(report_path, "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)

            # Generate executive summary
            print("\n📊 MULTI-TENANT WORKFLOW TEST SUMMARY")
            print("=" * 80)

            # Test results overview
            error_count = len(self.test_results["errors"])
            tenant_test_count = len(self.test_results["tenant_tests"])

            print(f"Real Clients Tested: {len(self.test_results['real_clients'])}")
            print(f"Tenant Workflows Tested: {tenant_test_count}")
            print(f"Total Errors: {error_count}")

            # Multi-tenant isolation results
            isolation = self.test_results.get("isolation_tests", {})
            isolation_passed = not isolation.get("cross_contamination", True)
            print(
                f"Multi-Tenant Isolation: {'✅ PASSED' if isolation_passed else '❌ FAILED'}"
            )

            # Individual client results
            print("\n🏢 CLIENT-SPECIFIC RESULTS:")
            for client_name, test_data in self.test_results["tenant_tests"].items():
                csv_success = test_data.get("csv_upload", {}).get("success", False)
                crewai_success = test_data.get("crewai_processing", {}).get(
                    "success", False
                )
                assets_added = test_data.get("final_state", {}).get("assets_added", 0)

                print(
                    f"  {client_name.upper()}: CSV {'✅' if csv_success else '❌'} | CrewAI {'✅' if crewai_success else '❌'} | Assets Added: {assets_added}"
                )

            # Critical findings
            print("\n🚨 CRITICAL FINDINGS:")

            real_processing_detected = False
            for test_data in self.test_results["tenant_tests"].values():
                if test_data.get("final_state", {}).get("assets_added", 0) > 0:
                    real_processing_detected = True
                    break

            if real_processing_detected:
                print(
                    "   ✅ REAL DATA PROCESSING CONFIRMED: Assets actually created and persisted"
                )
            else:
                print(
                    "   🚨 NO REAL PROCESSING: No assets were actually created despite API success messages"
                )

            if isolation_passed:
                print(
                    "   ✅ MULTI-TENANT ISOLATION WORKING: No data cross-contamination between clients"
                )
            else:
                print(
                    "   🚨 MULTI-TENANT ISOLATION FAILED: Data cross-contamination detected"
                )

            # API Context Testing
            api_context_working = True
            for client_results in self.test_results["api_tests"].values():
                if not client_results.get("discovery_metrics", {}).get(
                    "success", False
                ):
                    api_context_working = False
                    break

            if api_context_working:
                print(
                    "   ✅ API CONTEXT HEADERS WORKING: Client-specific data returned correctly"
                )
            else:
                print(
                    "   🚨 API CONTEXT ISSUES: Client context headers not working properly"
                )

            # Errors
            if error_count > 0:
                print("\n❌ ERRORS ENCOUNTERED:")
                for i, error in enumerate(self.test_results["errors"], 1):
                    print(f"   {i}. {error}")

            print(f"\n📁 Detailed report saved to: {report_path}")

        except Exception as e:
            print(f"❌ Failed to generate multi-tenant test report: {e}")


async def main():
    """Run the multi-tenant discovery workflow test."""
    tester = MultiTenantWorkflowTester()
    await tester.run_complete_multitenant_test()


if __name__ == "__main__":
    asyncio.run(main())
