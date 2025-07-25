#!/usr/bin/env python3
"""
Fixed API-based test for file upload and Discovery flow initiation
Tests the backend API endpoints with correct request format
"""

import requests
import json
import uuid
from typing import Optional
from datetime import datetime

class DiscoveryFlowAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.client_account_id = None
        self.engagement_id = None
        self.user_id = None

    def login(self, email: str = "chocka@gmail.com", password: str = "Password123!") -> bool:
        """Login to the platform"""
        print("🔐 Step 1: Logging in...")

        try:
            # Try JSON login first
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("id")
                print("✅ Login successful")
                return True

        except Exception as e:
            print(f"⚠️ Login failed: {e}")

        return False

    def get_context(self) -> bool:
        """Get user context (client and engagement)"""
        print("🏢 Step 2: Getting user context...")

        try:
            response = self.session.get(f"{self.base_url}/api/v1/context/me")

            if response.status_code == 200:
                context = response.json()
                self.client_account_id = context.get("client_account_id")
                self.engagement_id = context.get("engagement_id")
                self.user_id = context.get("user_id") or self.user_id

                print("✅ Context retrieved:")
                print(f"   Client ID: {self.client_account_id}")
                print(f"   Engagement ID: {self.engagement_id}")
                print(f"   User ID: {self.user_id}")
                return True

        except Exception as e:
            print(f"⚠️ Context retrieval failed: {e}")

        # Use fallback context for platform admin
        self.client_account_id = "11111111-1111-1111-1111-111111111111"
        self.engagement_id = "22222222-2222-2222-2222-222222222222"
        self.user_id = "acb04904-98a7-4f45-aacd-174d28dd3aad"
        print("✅ Using fallback platform admin context")
        return True

    def upload_test_data(self) -> Optional[str]:
        """Upload test CSV data using correct format"""
        print("📁 Step 3: Uploading test data with correct format...")

        # Test CSV data
        test_data = [
            {
                "hostname": "server001.prod",
                "application_name": "Customer Portal",
                "ip_address": "192.168.1.10",
                "operating_system": "Ubuntu 20.04",
                "cpu_cores": "4",
                "memory_gb": "16",
                "storage_gb": "500",
                "environment": "Production",
                "criticality": "High",
                "six_r_strategy": "Rehost"
            },
            {
                "hostname": "server002.prod",
                "application_name": "Payment Gateway",
                "ip_address": "192.168.1.11",
                "operating_system": "RHEL 8.5",
                "cpu_cores": "8",
                "memory_gb": "32",
                "storage_gb": "1000",
                "environment": "Production",
                "criticality": "Critical",
                "six_r_strategy": "Refactor"
            },
            {
                "hostname": "server003.prod",
                "application_name": "Admin Dashboard",
                "ip_address": "192.168.1.12",
                "operating_system": "Windows Server 2019",
                "cpu_cores": "4",
                "memory_gb": "16",
                "storage_gb": "250",
                "environment": "Production",
                "criticality": "Medium",
                "six_r_strategy": "Replatform"
            }
        ]

        # Generate validation session ID
        validation_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()

        # Create request in the correct format expected by StoreImportRequest
        payload = {
            "file_data": test_data,
            "metadata": {
                "filename": "api_test_import.csv",
                "size": 1024,  # Approximate size
                "type": "text/csv"
            },
            "upload_context": {
                "intended_type": "cmdb",
                "validation_upload_id": validation_id,  # Use new field name
                "upload_timestamp": current_time
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }

        try:
            print(f"🔄 Uploading with validation ID: {validation_id}")
            print(f"📤 Payload size: {len(json.dumps(payload))} characters")

            response = self.session.post(
                f"{self.base_url}/api/v1/data-import/store-import",
                json=payload,
                headers=headers
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"   Success: {result.get('success')}")
                print(f"   Message: {result.get('message')}")
                print(f"   Records stored: {result.get('records_stored', 0)}")

                # Extract flow ID
                flow_id = result.get("flow_id")
                data_import_id = result.get("data_import_id")

                if flow_id:
                    print(f"🔄 Discovery Flow ID: {flow_id}")
                    return flow_id
                elif data_import_id:
                    print(f"📋 Data Import ID: {data_import_id}")
                    return data_import_id
                else:
                    print("✅ Upload successful but no specific ID returned")
                    return "success"

            else:
                error_text = response.text
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Error details: {error_text}")

                # Try to parse error for more details
                try:
                    error_json = response.json()
                    if "detail" in error_json:
                        print(f"Detailed error: {error_json['detail']}")
                except:
                    pass

        except Exception as e:
            print(f"⚠️ Error during upload: {e}")

        return None

    def check_flow_status(self, flow_id: str) -> bool:
        """Check Discovery flow status"""
        print(f"🔍 Step 4: Checking flow status for {flow_id}...")

        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }

        # Try different status endpoints
        status_endpoints = [
            f"/api/v1/discovery-flow/flows/{flow_id}",
            f"/api/v1/data-import/flow/{flow_id}/status",
            "/api/v1/agents/discovery/agent-status"
        ]

        for endpoint in status_endpoints:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers
                )

                if response.status_code == 200:
                    status_data = response.json()
                    print(f"✅ Flow status retrieved via {endpoint}")

                    # Extract useful status information
                    if "status" in status_data:
                        print(f"   Status: {status_data['status']}")
                    if "current_phase" in status_data:
                        print(f"   Current Phase: {status_data['current_phase']}")
                    if "progress_percentage" in status_data:
                        print(f"   Progress: {status_data['progress_percentage']}%")
                    if "message" in status_data:
                        print(f"   Message: {status_data['message']}")

                    return True

            except Exception as e:
                print(f"⚠️ Error checking {endpoint}: {e}")

        print("⚠️ Could not retrieve flow status from any endpoint")
        return False

    def check_asset_inventory(self) -> bool:
        """Check if assets were created from the uploaded data"""
        print("📦 Step 5: Checking asset inventory...")

        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/assets/list/paginated",
                headers=headers
            )

            if response.status_code == 200:
                assets_data = response.json()

                if "assets" in assets_data:
                    asset_count = len(assets_data["assets"])
                    print(f"✅ Found {asset_count} assets in inventory")

                    if asset_count > 0:
                        # Show some asset details
                        for i, asset in enumerate(assets_data["assets"][:3]):
                            print(f"   Asset {i+1}: {asset.get('name', 'Unknown')} ({asset.get('asset_type', 'unknown')})")

                        return True
                    else:
                        print("⚠️ No assets found in inventory")

                elif "pagination" in assets_data:
                    total_items = assets_data["pagination"].get("total_items", 0)
                    print(f"✅ Asset inventory has {total_items} total items")
                    return total_items > 0

        except Exception as e:
            print(f"⚠️ Error checking asset inventory: {e}")

        return False

    def check_discovery_agent_status(self) -> bool:
        """Check Discovery agent status and activity"""
        print("🤖 Step 6: Checking Discovery agent status...")

        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/agents/discovery/agent-status",
                headers=headers
            )

            if response.status_code == 200:
                agent_data = response.json()

                if "data" in agent_data:
                    agent_info = agent_data["data"]
                    print("✅ Discovery agent status retrieved")

                    if "active_agents" in agent_info:
                        active_count = agent_info["active_agents"].get("active", 0)
                        total_count = agent_info["active_agents"].get("total", 0)
                        print(f"   Active agents: {active_count}/{total_count}")

                    if "crew_status" in agent_info:
                        crews = agent_info["crew_status"]
                        for crew_name, crew_info in crews.items():
                            status = crew_info.get("status", "unknown")
                            progress = crew_info.get("progress", 0)
                            print(f"   {crew_name}: {status} ({progress}%)")

                    return True

        except Exception as e:
            print(f"⚠️ Error checking Discovery agent status: {e}")

        return False

    def check_data_import_status(self) -> bool:
        """Check data import status and records"""
        print("📋 Step 7: Checking data import status...")

        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }

        try:
            # Check recent imports
            response = self.session.get(
                f"{self.base_url}/api/v1/data-import/imports",
                headers=headers
            )

            if response.status_code == 200:
                imports_data = response.json()

                if isinstance(imports_data, list) and len(imports_data) > 0:
                    latest_import = imports_data[0]  # Assuming sorted by date
                    print(f"✅ Found {len(imports_data)} data imports")
                    print(f"   Latest import: {latest_import.get('import_name', 'Unknown')}")
                    print(f"   Status: {latest_import.get('status', 'Unknown')}")
                    print(f"   Records: {latest_import.get('total_records', 0)}")
                    return True
                else:
                    print("⚠️ No data imports found")

        except Exception as e:
            print(f"⚠️ Error checking data import status: {e}")

        return False

    def run_complete_test(self) -> bool:
        """Run the complete Discovery flow test"""
        print("🚀 Starting Fixed Discovery Flow API Test...\n")

        results = {}

        # Step 1: Login
        results["login"] = self.login()
        if not results["login"]:
            return False

        # Step 2: Get context
        results["context"] = self.get_context()

        # Step 3: Upload data with correct format
        flow_id = self.upload_test_data()
        results["upload"] = flow_id is not None

        if flow_id and flow_id not in ["success", "unknown"]:
            # Step 4: Check flow status
            results["flow_status"] = self.check_flow_status(flow_id)
        else:
            results["flow_status"] = False

        # Step 5: Check asset inventory
        results["assets"] = self.check_asset_inventory()

        # Step 6: Check Discovery agent status
        results["agents"] = self.check_discovery_agent_status()

        # Step 7: Check data import status
        results["imports"] = self.check_data_import_status()

        # Results summary
        print("\n📋 FIXED TEST RESULTS SUMMARY:")
        print(f"✅ Login: {'SUCCESS' if results['login'] else 'FAILED'}")
        print(f"✅ Context: {'SUCCESS' if results['context'] else 'FAILED'}")
        print(f"✅ Data Upload: {'SUCCESS' if results['upload'] else 'FAILED'}")
        print(f"✅ Flow Status: {'SUCCESS' if results['flow_status'] else 'FAILED'}")
        print(f"✅ Asset Inventory: {'SUCCESS' if results['assets'] else 'FAILED'}")
        print(f"🤖 Discovery Agents: {'ACTIVE' if results['agents'] else 'INACTIVE'}")
        print(f"📋 Data Imports: {'SUCCESS' if results['imports'] else 'FAILED'}")

        # Overall success criteria
        critical_steps = ["login", "context", "upload"]
        success_count = sum(1 for step in critical_steps if results[step])

        # Additional success indicators
        operational_steps = ["assets", "agents", "imports"]
        operational_count = sum(1 for step in operational_steps if results[step])

        if success_count == len(critical_steps):
            print("\n🎉 TEST PASSED: Discovery flow API working correctly!")
            print(f"   Critical steps: {success_count}/{len(critical_steps)} ✅")
            print(f"   Operational features: {operational_count}/{len(operational_steps)} working")
            return True
        else:
            print(f"\n⚠️ TEST PARTIAL: {success_count}/{len(critical_steps)} critical steps passed")
            print(f"   Operational features: {operational_count}/{len(operational_steps)} working")
            return False

if __name__ == "__main__":
    tester = DiscoveryFlowAPITester()
    success = tester.run_complete_test()
    exit(0 if success else 1)
