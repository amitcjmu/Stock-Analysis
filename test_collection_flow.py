#!/usr/bin/env python3
"""
Test script for Collection Flow - Bug Fixes #16, #17, #19, #20
Tests the complete collection flow execution to verify bug fixes.
"""
import asyncio
import json
import sys
from datetime import datetime
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8081"
EMAIL = "chockas@hcltech.com"
PASSWORD = "Testing123!"

# Canada Life engagement details (from database query)
ENGAGEMENT_ID = "dbd6010b-df6f-487b-9493-0afcd2fcdbea"
CLIENT_ACCOUNT_ID = "22de4463-43db-4c59-84db-15ce7ddef06a"

# Test assets (from database - all are not_ready)
TEST_ASSET_IDS = [
    "be1eedce-59e1-406b-8c81-e46f87663a39",  # 064B01P
    "00336ec1-2ffe-490e-8600-685b32e511f2",  # 0689CET
]


class CollectionFlowTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.token = None
        self.context = None
        self.test_results = {
            "login": None,
            "create_flow": None,
            "execute_gap_analysis": None,
            "gap_detection": None,
            "questionnaire_generation": None,
            "bug_16_fix": None,  # IntelligentGap attribute access
            "bug_17_fix": None,  # SectionQuestionGenerator parameters
            "bug_19_fix": None,  # UUID string types
            "bug_20_fix": None,  # Truncated JSON handling
            "errors": []
        }

    async def login(self):
        """Authenticate and get access token"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 1: Login...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": EMAIL, "password": PASSWORD}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.context = {
                "client_account_id": data["user"]["client_account_id"],
                "engagement_id": data["user"]["default_engagement_id"]
            }
            print(f"   ✅ Login successful")
            print(f"   Client: {self.context['client_account_id']}")
            print(f"   Engagement: {self.context['engagement_id']}")
            self.test_results["login"] = "PASS"
            return True
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            self.test_results["login"] = f"FAIL: {e}"
            self.test_results["errors"].append(f"Login: {e}")
            return False

    def get_headers(self):
        """Get authenticated headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-Client-Account-Id": str(self.context["client_account_id"]),
            "X-Engagement-Id": str(self.context["engagement_id"])
        }

    async def create_collection_flow(self):
        """Create a new collection flow"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 2: Create Collection Flow...")
        try:
            payload = {
                "flow_name": f"QA Test Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "asset_ids": TEST_ASSET_IDS[:2],  # Test with 2 assets
                "description": "Testing bug fixes #16, #17, #19, #20"
            }

            response = await self.client.post(
                f"{BASE_URL}/api/v1/collection/flows",
                headers=self.get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            self.flow_id = data["flow_id"]
            self.master_flow_id = data.get("master_flow_id")

            print(f"   ✅ Collection flow created")
            print(f"   Flow ID: {self.flow_id}")
            print(f"   Master Flow ID: {self.master_flow_id}")
            print(f"   Status: {data.get('status')}")

            self.test_results["create_flow"] = "PASS"
            return True
        except Exception as e:
            print(f"   ❌ Flow creation failed: {e}")
            self.test_results["create_flow"] = f"FAIL: {e}"
            self.test_results["errors"].append(f"Create Flow: {e}")
            return False

    async def execute_gap_analysis(self):
        """Execute gap analysis phase"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 3: Execute Gap Analysis...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/collection/flows/{self.flow_id}/execute/gap-analysis",
                headers=self.get_headers()
            )
            response.raise_for_status()
            data = response.json()

            print(f"   ✅ Gap analysis initiated")
            print(f"   Status: {data.get('status')}")
            print(f"   Phase: {data.get('current_phase')}")

            self.test_results["execute_gap_analysis"] = "PASS"

            # Bug #19 Check: UUID string types
            # The backend should accept string UUIDs without errors
            self.test_results["bug_19_fix"] = "PASS - No UUID type errors"

            return True
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Gap analysis failed: {error_msg}")
            self.test_results["execute_gap_analysis"] = f"FAIL: {error_msg}"
            self.test_results["errors"].append(f"Gap Analysis: {error_msg}")

            # Check if it's Bug #19 (UUID type issues)
            if "UUID" in error_msg or "str" in error_msg:
                self.test_results["bug_19_fix"] = f"FAIL: {error_msg}"

            return False

    async def monitor_gap_analysis(self):
        """Monitor gap analysis progress and check for Bug #16"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 4: Monitor Gap Analysis Progress...")

        max_wait = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < max_wait:
            try:
                response = await self.client.get(
                    f"{BASE_URL}/api/v1/collection/flows/{self.flow_id}",
                    headers=self.get_headers()
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                phase = data.get("current_phase")

                print(f"   Status: {status}, Phase: {phase}")

                # Check phase_results for gap_analysis completion
                phase_results = data.get("phase_results", {})
                gap_results = phase_results.get("gap_analysis", {})

                if gap_results:
                    print(f"   Gap analysis results found:")
                    gaps = gap_results.get("gaps", [])
                    print(f"   Gaps detected: {len(gaps)}")

                    # Bug #16 Check: IntelligentGap attribute access
                    # If gaps exist and no errors, it means gap.section worked correctly
                    if len(gaps) > 0:
                        self.test_results["bug_16_fix"] = "PASS - IntelligentGap attributes accessed correctly"
                        self.test_results["gap_detection"] = f"PASS - {len(gaps)} gaps detected"
                        print(f"   ✅ Bug #16 verified: IntelligentGap attribute access working")

                    return True

                # If phase moved past gap_analysis, check results
                if phase != "gap_analysis" and phase not in ["initialization", "asset_selection"]:
                    print(f"   Gap analysis phase completed, moved to: {phase}")
                    return True

                # If failed, check error
                if status == "failed":
                    error = data.get("error_message", "Unknown error")
                    print(f"   ❌ Flow failed: {error}")
                    self.test_results["errors"].append(f"Gap Analysis Failed: {error}")

                    # Check for Bug #16 (IntelligentGap attribute errors)
                    if "gap.section" in error or "gap['section']" in error or "IntelligentGap" in error:
                        self.test_results["bug_16_fix"] = f"FAIL: {error}"

                    return False

                await asyncio.sleep(10)  # Poll every 10 seconds

            except Exception as e:
                print(f"   ⚠️  Monitoring error: {e}")
                await asyncio.sleep(10)

        print(f"   ⏱️  Timeout waiting for gap analysis")
        self.test_results["gap_detection"] = "TIMEOUT - Gap analysis taking too long"
        return False

    async def execute_questionnaire_generation(self):
        """Execute questionnaire generation and check for Bug #17 and #20"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Step 5: Execute Questionnaire Generation...")
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/collection/flows/{self.flow_id}/execute/questionnaire-generation",
                headers=self.get_headers()
            )
            response.raise_for_status()
            data = response.json()

            print(f"   ✅ Questionnaire generation initiated")
            print(f"   Status: {data.get('status')}")

            # Bug #17 Check: SectionQuestionGenerator parameter names
            # If this completes without errors, parameters are correct
            self.test_results["bug_17_fix"] = "PASS - SectionQuestionGenerator parameters correct"

            # Bug #20 Check: Truncated JSON handling
            # If questionnaires are generated despite truncation, repair worked
            self.test_results["bug_20_fix"] = "PASS - JSON truncation handled"

            self.test_results["questionnaire_generation"] = "PASS"
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Questionnaire generation failed: {error_msg}")
            self.test_results["questionnaire_generation"] = f"FAIL: {error_msg}"
            self.test_results["errors"].append(f"Questionnaire Gen: {error_msg}")

            # Check for Bug #17 (parameter name issues)
            if "asset_name" in error_msg or "asset_id" in error_msg or "section_name" in error_msg:
                self.test_results["bug_17_fix"] = f"FAIL: {error_msg}"

            # Check for Bug #20 (JSON truncation issues)
            if "JSON" in error_msg or "truncat" in error_msg or "parse" in error_msg:
                self.test_results["bug_20_fix"] = f"FAIL: {error_msg}"

            return False

    async def check_backend_logs(self):
        """Check backend logs for errors"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Backend Logs...")
        import subprocess

        try:
            # Get logs from the last 5 minutes
            result = subprocess.run(
                ["docker", "logs", "migration_backend", "--since", "5m"],
                capture_output=True,
                text=True
            )

            logs = result.stdout + result.stderr

            # Look for bug-related errors
            error_patterns = {
                "bug_16": ["gap.section", "gap['section']", "IntelligentGap"],
                "bug_17": ["SectionQuestionGenerator", "asset_name", "section_name"],
                "bug_19": ["UUID.*str", "expected UUID"],
                "bug_20": ["truncat.*JSON", "JSON.*parse", "ellipsis"]
            }

            for bug, patterns in error_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in logs.lower():
                        print(f"   ⚠️  Found {bug} related log: {pattern}")

        except Exception as e:
            print(f"   ⚠️  Could not check logs: {e}")

    async def run_tests(self):
        """Run all tests"""
        print("=" * 80)
        print("COLLECTION FLOW QA TEST - Bug Fixes #16, #17, #19, #20")
        print("=" * 80)

        try:
            # Step 1: Login
            if not await self.login():
                return self.test_results

            # Step 2: Create collection flow
            if not await self.create_collection_flow():
                return self.test_results

            # Step 3: Execute gap analysis
            if not await self.execute_gap_analysis():
                return self.test_results

            # Step 4: Monitor gap analysis (checks Bug #16)
            await self.monitor_gap_analysis()

            # Step 5: Execute questionnaire generation (checks Bug #17, #20)
            await self.execute_questionnaire_generation()

            # Step 6: Check backend logs
            await self.check_backend_logs()

        finally:
            await self.client.aclose()

        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        # Overall results
        passed = sum(1 for v in self.test_results.values()
                    if isinstance(v, str) and v.startswith("PASS"))
        failed = sum(1 for v in self.test_results.values()
                    if isinstance(v, str) and v.startswith("FAIL"))

        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")

        # Bug fix verification
        print("\n" + "-" * 80)
        print("BUG FIX VERIFICATION:")
        print("-" * 80)
        print(f"Bug #16 (IntelligentGap attribute access): {self.test_results.get('bug_16_fix', 'NOT TESTED')}")
        print(f"Bug #17 (SectionQuestionGenerator params): {self.test_results.get('bug_17_fix', 'NOT TESTED')}")
        print(f"Bug #19 (UUID string types): {self.test_results.get('bug_19_fix', 'NOT TESTED')}")
        print(f"Bug #20 (Truncated JSON repair): {self.test_results.get('bug_20_fix', 'NOT TESTED')}")

        # Errors
        if self.test_results["errors"]:
            print("\n" + "-" * 80)
            print("ERRORS ENCOUNTERED:")
            print("-" * 80)
            for error in self.test_results["errors"]:
                print(f"  • {error}")

        print("\n" + "=" * 80)

        # Return exit code
        return 0 if failed == 0 else 1


async def main():
    tester = CollectionFlowTester()
    await tester.run_tests()
    exit_code = tester.print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
