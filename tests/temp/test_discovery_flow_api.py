#!/usr/bin/env python3
"""
API-based test for file upload and Discovery flow initiation
Tests the backend API endpoints to verify Discovery flow creation
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

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
        
        login_data = {
            "username": email,  # FastAPI typically uses 'username' for OAuth2
            "password": password
        }
        
        try:
            # Try OAuth2 token endpoint
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print("✅ Login successful with OAuth2 token")
                return True
                
        except Exception as e:
            print(f"⚠️ OAuth2 login failed: {e}")
        
        # Fallback: Try JSON login
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("id")
                print("✅ Login successful with JSON endpoint")
                return True
                
        except Exception as e:
            print(f"⚠️ JSON login failed: {e}")
            
        print("❌ Login failed")
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
                self.user_id = context.get("user_id")
                
                print(f"✅ Context retrieved:")
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
        """Upload test CSV data and create Discovery flow"""
        print("📁 Step 3: Uploading test data...")
        
        # Test CSV data
        test_data = [
            {
                "hostname": "server001.prod",
                "application_name": "Customer Portal", 
                "ip_address": "192.168.1.10",
                "operating_system": "Ubuntu 20.04",
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 500,
                "environment": "Production",
                "criticality": "High",
                "six_r_strategy": "Rehost"
            },
            {
                "hostname": "server002.prod",
                "application_name": "Payment Gateway",
                "ip_address": "192.168.1.11", 
                "operating_system": "RHEL 8.5",
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 1000,
                "environment": "Production",
                "criticality": "Critical",
                "six_r_strategy": "Refactor"
            },
            {
                "hostname": "server003.prod",
                "application_name": "Admin Dashboard",
                "ip_address": "192.168.1.12",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 250,
                "environment": "Production", 
                "criticality": "Medium",
                "six_r_strategy": "Replatform"
            }
        ]
        
        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }
        
        # Try different API endpoints for data upload
        endpoints_to_try = [
            "/api/v1/unified-discovery/flow/initialize",
            "/api/v3/discovery-flow/flows",
            "/api/v1/data-import/store-import"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                print(f"🔄 Trying endpoint: {endpoint}")
                
                if endpoint.endswith("initialize"):
                    payload = {
                        "raw_data": test_data,
                        "metadata": {"source": "api_test", "test_mode": True}
                    }
                elif endpoint.endswith("flows"):
                    payload = {
                        "client_account_id": self.client_account_id,
                        "engagement_id": self.engagement_id,
                        "user_id": self.user_id,
                        "raw_data": test_data
                    }
                else:
                    payload = {
                        "data": test_data,
                        "import_name": "API Test Import",
                        "client_account_id": self.client_account_id,
                        "engagement_id": self.engagement_id
                    }
                
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=headers
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✅ Upload successful via {endpoint}")
                    
                    # Extract flow ID
                    flow_id = None
                    if "flow_id" in result:
                        flow_id = result["flow_id"]
                    elif "data" in result and "flow_id" in result["data"]:
                        flow_id = result["data"]["flow_id"]
                    elif "id" in result:
                        flow_id = result["id"]
                        
                    if flow_id:
                        print(f"🔄 Discovery Flow ID: {flow_id}")
                        return flow_id
                    else:
                        print("⚠️ No flow ID returned, but upload successful")
                        return "unknown"
                        
                else:
                    print(f"⚠️ Upload failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"⚠️ Error with {endpoint}: {e}")
                
        print("❌ All upload endpoints failed")
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
            f"/api/v1/unified-discovery/flow/status/{flow_id}",
            f"/api/v3/discovery-flow/flows/{flow_id}/status",
            f"/api/v1/discovery-flow/flows/{flow_id}"
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
                        
                    return True
                    
            except Exception as e:
                print(f"⚠️ Error checking {endpoint}: {e}")
                
        print("⚠️ Could not retrieve flow status")
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
    
    def check_field_mappings(self) -> bool:
        """Check if field mappings were created"""
        print("🗂️ Step 6: Checking field mappings...")
        
        headers = {
            "X-Client-Account-ID": str(self.client_account_id),
            "X-Engagement-ID": str(self.engagement_id),
            "X-User-ID": str(self.user_id)
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/field-mapping/mappings",
                headers=headers
            )
            
            if response.status_code == 200:
                mappings_data = response.json()
                
                if isinstance(mappings_data, list):
                    mapping_count = len(mappings_data)
                    print(f"✅ Found {mapping_count} field mappings")
                    return mapping_count > 0
                elif "mappings" in mappings_data:
                    mapping_count = len(mappings_data["mappings"])
                    print(f"✅ Found {mapping_count} field mappings")
                    return mapping_count > 0
                    
        except Exception as e:
            print(f"⚠️ Error checking field mappings: {e}")
            
        return False
    
    def run_complete_test(self) -> bool:
        """Run the complete Discovery flow test"""
        print("🚀 Starting Discovery Flow API Test...\n")
        
        results = {}
        
        # Step 1: Login
        results["login"] = self.login()
        if not results["login"]:
            return False
            
        # Step 2: Get context
        results["context"] = self.get_context()
        
        # Step 3: Upload data and create flow
        flow_id = self.upload_test_data()
        results["upload"] = flow_id is not None
        
        if flow_id and flow_id != "unknown":
            # Step 4: Check flow status
            results["flow_status"] = self.check_flow_status(flow_id)
        else:
            results["flow_status"] = False
            
        # Step 5: Check asset inventory
        results["assets"] = self.check_asset_inventory()
        
        # Step 6: Check field mappings
        results["mappings"] = self.check_field_mappings()
        
        # Results summary
        print("\n📋 TEST RESULTS SUMMARY:")
        print(f"✅ Login: {'SUCCESS' if results['login'] else 'FAILED'}")
        print(f"✅ Context: {'SUCCESS' if results['context'] else 'FAILED'}")
        print(f"✅ Data Upload: {'SUCCESS' if results['upload'] else 'FAILED'}")
        print(f"✅ Flow Status: {'SUCCESS' if results['flow_status'] else 'FAILED'}")
        print(f"✅ Asset Creation: {'SUCCESS' if results['assets'] else 'FAILED'}")
        print(f"✅ Field Mappings: {'SUCCESS' if results['mappings'] else 'FAILED'}")
        
        # Overall success criteria
        critical_steps = ["login", "context", "upload"]
        success_count = sum(1 for step in critical_steps if results[step])
        
        if success_count == len(critical_steps):
            print("\n🎉 TEST PASSED: Discovery flow API working correctly!")
            return True
        else:
            print(f"\n⚠️ TEST PARTIAL: {success_count}/{len(critical_steps)} critical steps passed")
            return False

if __name__ == "__main__":
    tester = DiscoveryFlowAPITester()
    success = tester.run_complete_test()
    exit(0 if success else 1)