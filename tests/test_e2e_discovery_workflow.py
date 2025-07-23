#!/usr/bin/env python3
"""
End-to-End Discovery Workflow Test with Playwright Integration

This script tests the complete discovery workflow from CSV upload through 
agentic processing to database persistence, capturing frontend behavior
and verifying actual backend data storage.
"""

import asyncio
import sys
import os
import csv
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to the path
sys.path.append('/app')

# Playwright imports
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not available - install with: pip install playwright")

# Backend imports for database verification
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.data_import import DataImport, RawImportRecord, MappingLearningPattern

class DiscoveryWorkflowTester:
    """Comprehensive end-to-end discovery workflow tester."""
    
    def __init__(self):
        self.screenshots_dir = Path("test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.test_results = {
            "test_start": datetime.now().isoformat(),
            "stages": {},
            "database_checks": {},
            "api_responses": {},
            "frontend_captures": {},
            "errors": [],
            "success": False
        }
        
    async def run_complete_test(self):
        """Run the complete end-to-end discovery workflow test."""
        print("🧪 Starting Comprehensive Discovery Workflow Test")
        print("=" * 80)
        
        try:
            # Phase 1: Database baseline
            await self.capture_database_baseline()
            
            # Phase 2: Frontend workflow test with Playwright
            if PLAYWRIGHT_AVAILABLE:
                await self.test_frontend_workflow()
            else:
                print("⚠️ Skipping frontend test - Playwright not available")
                
            # Phase 3: Backend API verification
            await self.test_backend_apis()
            
            # Phase 4: Database verification after workflow
            await self.verify_database_persistence()
            
            # Phase 5: Discovery dashboard verification
            if PLAYWRIGHT_AVAILABLE:
                await self.verify_discovery_dashboard()
            
            # Phase 6: Generate comprehensive report
            await self.generate_test_report()
            
            self.test_results["success"] = len(self.test_results["errors"]) == 0
            
        except Exception as e:
            self.test_results["errors"].append(f"Test execution failed: {e}")
            print(f"❌ Test execution failed: {e}")
        
        finally:
            self.test_results["test_end"] = datetime.now().isoformat()
            print(f"\n📊 Test completed. Success: {self.test_results['success']}")
            print(f"📁 Screenshots saved to: {self.screenshots_dir}")
            
    async def capture_database_baseline(self):
        """Capture the current state of the database before testing."""
        print("\n📊 Phase 1: Capturing Database Baseline")
        print("-" * 50)
        
        try:
            async with AsyncSessionLocal() as session:
                # Count existing assets
                asset_count = await session.execute(select(func.count(Asset.id)))
                total_assets = asset_count.scalar()
                
                # Count existing data imports
                import_count = await session.execute(select(func.count(DataImport.id)))
                total_imports = import_count.scalar()
                
                # Count raw import records
                raw_count = await session.execute(select(func.count(RawImportRecord.id)))
                total_raw = raw_count.scalar()
                
                # Count learning patterns
                mapping_count = await session.execute(select(func.count(MappingLearningPattern.id)))
                total_mapping_patterns = mapping_count.scalar()
                
                baseline = {
                    "assets": total_assets,
                    "data_imports": total_imports,
                    "raw_import_records": total_raw,
                    "mapping_patterns": total_mapping_patterns,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results["database_checks"]["baseline"] = baseline
                
                print("📈 Current Database State:")
                print(f"   Assets: {total_assets}")
                print(f"   Data Imports: {total_imports}")
                print(f"   Raw Import Records: {total_raw}")
                print(f"   Mapping Patterns: {total_mapping_patterns}")
                
        except Exception as e:
            error_msg = f"Failed to capture database baseline: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def test_frontend_workflow(self):
        """Test the complete frontend workflow using Playwright."""
        print("\n🎭 Phase 2: Testing Frontend Workflow with Playwright")
        print("-" * 50)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            page = await browser.new_page()
            
            try:
                # Step 1: Navigate to discovery dashboard
                await self.step_navigate_to_discovery(page)
                
                # Step 2: Check initial dashboard state
                await self.step_capture_initial_dashboard(page)
                
                # Step 3: Navigate to data import
                await self.step_navigate_to_import(page)
                
                # Step 4: Create and upload test CSV
                await self.step_upload_test_csv(page)
                
                # Step 5: Monitor import progress
                await self.step_monitor_import_progress(page)
                
                # Step 6: Verify CrewAI Flow execution
                await self.step_verify_crewai_flow(page)
                
                # Step 7: Navigate back to dashboard
                await self.step_return_to_dashboard(page)
                
                # Step 8: Capture final dashboard state
                await self.step_capture_final_dashboard(page)
                
            except Exception as e:
                error_msg = f"Frontend workflow test failed: {e}"
                self.test_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
                # Capture error screenshot
                await page.screenshot(path=self.screenshots_dir / "error_state.png")
                
            finally:
                await browser.close()
    
    async def step_navigate_to_discovery(self, page: Page):
        """Step 1: Navigate to discovery dashboard."""
        print("🔗 Step 1: Navigating to Discovery Dashboard")
        
        try:
            await page.goto("http://localhost:8081/discovery/overview")
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Capture screenshot
            await page.screenshot(path=self.screenshots_dir / "01_discovery_dashboard.png")
            
            # Check if page loaded properly
            title = await page.title()
            self.test_results["frontend_captures"]["discovery_navigation"] = {
                "url": page.url,
                "title": title,
                "success": "discovery" in page.url.lower()
            }
            
            print(f"✅ Successfully navigated to: {page.url}")
            print(f"   Page title: {title}")
            
        except Exception as e:
            error_msg = f"Failed to navigate to discovery dashboard: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_capture_initial_dashboard(self, page: Page):
        """Step 2: Capture initial dashboard metrics."""
        print("📊 Step 2: Capturing Initial Dashboard Metrics")
        
        try:
            # Wait for dashboard to load
            await page.wait_for_timeout(3000)
            
            # Extract dashboard metrics
            metrics = {}
            
            # Try to find asset count
            try:
                asset_element = await page.query_selector('[data-testid="total-assets"], .text-2xl:has-text("Assets")')
                if asset_element:
                    asset_text = await asset_element.text_content()
                    metrics["total_assets_displayed"] = asset_text
            except:
                pass
            
            # Try to find application count
            try:
                app_element = await page.query_selector('[data-testid="total-applications"], .text-2xl:has-text("Applications")')
                if app_element:
                    app_text = await app_element.text_content()
                    metrics["total_applications_displayed"] = app_text
            except:
                pass
            
            # Try to get any metrics from h3 elements or similar
            metric_elements = await page.query_selector_all("h3, .text-2xl, .font-bold")
            displayed_numbers = []
            for element in metric_elements[:10]:  # Check first 10 elements
                try:
                    text = await element.text_content()
                    if text and text.strip().isdigit():
                        displayed_numbers.append(text.strip())
                except:
                    pass
            
            metrics["displayed_numbers"] = displayed_numbers
            
            self.test_results["frontend_captures"]["initial_dashboard"] = metrics
            
            print("📊 Initial Dashboard Metrics Captured:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
            
            # Capture screenshot
            await page.screenshot(path=self.screenshots_dir / "02_initial_dashboard_metrics.png")
            
        except Exception as e:
            error_msg = f"Failed to capture initial dashboard metrics: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_navigate_to_import(self, page: Page):
        """Step 3: Navigate to data import page."""
        print("📁 Step 3: Navigating to Data Import")
        
        try:
            await page.goto("http://localhost:8081/discovery/data-import")
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Capture screenshot
            await page.screenshot(path=self.screenshots_dir / "03_data_import_page.png")
            
            # Verify import page loaded
            import_success = "import" in page.url.lower() or "upload" in page.url.lower()
            self.test_results["frontend_captures"]["import_navigation"] = {
                "url": page.url,
                "success": import_success
            }
            
            print(f"✅ Successfully navigated to: {page.url}")
            
        except Exception as e:
            error_msg = f"Failed to navigate to data import: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_upload_test_csv(self, page: Page):
        """Step 4: Create and upload test CSV file."""
        print("📄 Step 4: Creating and Uploading Test CSV")
        
        try:
            # Create test CSV data
            test_data = [
                {
                    "NAME": "web-server-prod-01",
                    "HOSTNAME": "web01.company.com", 
                    "IP_ADDRESS": "10.1.1.10",
                    "CITYPE": "server",
                    "ENVIRONMENT": "Production",
                    "OS": "Ubuntu 20.04",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": "John Smith",
                    "LOCATION": "DataCenter-East"
                },
                {
                    "NAME": "database-prod-mysql",
                    "HOSTNAME": "db01.company.com",
                    "IP_ADDRESS": "10.1.1.20", 
                    "CITYPE": "database",
                    "ENVIRONMENT": "Production",
                    "OS": "CentOS 8",
                    "DEPARTMENT": "IT",
                    "BUSINESS_OWNER": "Jane Doe",
                    "LOCATION": "DataCenter-East"
                },
                {
                    "NAME": "app-server-api",
                    "HOSTNAME": "api01.company.com",
                    "IP_ADDRESS": "10.1.1.30",
                    "CITYPE": "application", 
                    "ENVIRONMENT": "Production",
                    "OS": "Windows Server 2019",
                    "DEPARTMENT": "Development",
                    "BUSINESS_OWNER": "Bob Johnson",
                    "LOCATION": "DataCenter-West"
                }
            ]
            
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                csv_path = tmp_file.name
                fieldnames = test_data[0].keys()
                writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(test_data)
            
            print(f"📄 Created test CSV with {len(test_data)} records: {csv_path}")
            
            # Find file input and upload
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(csv_path)
                print("✅ File uploaded successfully")
                
                # Wait a moment for file processing
                await page.wait_for_timeout(2000)
                
                # Capture screenshot after upload
                await page.screenshot(path=self.screenshots_dir / "04_file_uploaded.png")
                
                # Look for upload success indicators
                upload_success = False
                try:
                    # Check for success messages or processing indicators
                    success_selectors = [
                        '.alert-success', '.success', '[class*="success"]',
                        'text:has("success")', 'text:has("uploaded")', 'text:has("processing")'
                    ]
                    
                    for selector in success_selectors:
                        element = await page.query_selector(selector)
                        if element:
                            upload_success = True
                            break
                except:
                    pass
                
                self.test_results["frontend_captures"]["csv_upload"] = {
                    "file_path": csv_path,
                    "records_count": len(test_data),
                    "upload_success": upload_success
                }
                
                # Clean up temp file
                os.unlink(csv_path)
                
            else:
                error_msg = "File input not found on page"
                self.test_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
        except Exception as e:
            error_msg = f"Failed to upload test CSV: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_monitor_import_progress(self, page: Page):
        """Step 5: Monitor import progress and capture states."""
        print("⏱️ Step 5: Monitoring Import Progress")
        
        try:
            # Look for processing button or trigger
            process_buttons = [
                'button:has-text("Process")', 'button:has-text("Import")', 
                'button:has-text("Upload")', 'button:has-text("Submit")',
                '[type="submit"]', '.btn-primary'
            ]
            
            process_button = None
            for selector in process_buttons:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        if is_visible:
                            process_button = button
                            break
                except:
                    continue
            
            if process_button:
                print("🔄 Found process button, clicking...")
                await process_button.click()
                
                # Capture screenshot after clicking process
                await page.screenshot(path=self.screenshots_dir / "05_processing_started.png")
                
                # Monitor for progress indicators or completion
                max_wait_time = 30  # 30 seconds max
                start_time = datetime.now()
                
                while (datetime.now() - start_time).seconds < max_wait_time:
                    await page.wait_for_timeout(2000)
                    
                    # Look for completion indicators
                    completion_indicators = [
                        'text:has("completed")', 'text:has("success")', 'text:has("finished")',
                        '.alert-success', '.progress-complete', '[class*="complete"]'
                    ]
                    
                    completed = False
                    for indicator in completion_indicators:
                        try:
                            element = await page.query_selector(indicator)
                            if element:
                                completed = True
                                break
                        except:
                            continue
                    
                    if completed:
                        print("✅ Processing completed")
                        break
                        
                    # Look for error indicators
                    error_indicators = [
                        'text:has("error")', 'text:has("failed")', '.alert-error', '.error'
                    ]
                    
                    for indicator in error_indicators:
                        try:
                            element = await page.query_selector(indicator)
                            if element:
                                error_text = await element.text_content()
                                self.test_results["errors"].append(f"Frontend error: {error_text}")
                                break
                        except:
                            continue
                
                # Capture final processing state
                await page.screenshot(path=self.screenshots_dir / "06_processing_complete.png")
                
                self.test_results["frontend_captures"]["import_processing"] = {
                    "processing_triggered": True,
                    "wait_time_seconds": (datetime.now() - start_time).seconds
                }
                
            else:
                error_msg = "No process/submit button found"
                self.test_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
        except Exception as e:
            error_msg = f"Failed to monitor import progress: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_verify_crewai_flow(self, page: Page):
        """Step 6: Verify CrewAI Flow execution through API calls."""
        print("🤖 Step 6: Verifying CrewAI Flow Execution")
        
        try:
            # Check for any import session IDs or processing indicators on the page
            page_content = await page.content()
            
            # Look for session IDs or flow IDs in the page
            import re
            session_ids = re.findall(r'session[_-]?id["\s]*:?["\s]*([a-f0-9-]{36})', page_content, re.IGNORECASE)
            flow_ids = re.findall(r'flow[_-]?id["\s]*:?["\s]*([a-f0-9-]{36})', page_content, re.IGNORECASE)
            
            self.test_results["frontend_captures"]["crewai_verification"] = {
                "session_ids_found": session_ids,
                "flow_ids_found": flow_ids,
                "page_has_processing_indicators": "processing" in page_content.lower() or "crewai" in page_content.lower()
            }
            
            print(f"🔍 Session IDs found: {session_ids}")
            print(f"🔍 Flow IDs found: {flow_ids}")
            
        except Exception as e:
            error_msg = f"Failed to verify CrewAI flow: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_return_to_dashboard(self, page: Page):
        """Step 7: Return to dashboard."""
        print("🏠 Step 7: Returning to Dashboard")
        
        try:
            await page.goto("http://localhost:8081/discovery/overview")
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(3000)  # Wait for any API calls
            
            print("✅ Successfully returned to dashboard")
            
        except Exception as e:
            error_msg = f"Failed to return to dashboard: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def step_capture_final_dashboard(self, page: Page):
        """Step 8: Capture final dashboard state after processing."""
        print("📊 Step 8: Capturing Final Dashboard State")
        
        try:
            # Extract final dashboard metrics
            metrics = {}
            
            # Try to find asset count
            try:
                asset_element = await page.query_selector('[data-testid="total-assets"], .text-2xl:has-text("Assets")')
                if asset_element:
                    asset_text = await asset_element.text_content()
                    metrics["total_assets_displayed"] = asset_text
            except:
                pass
            
            # Try to find application count
            try:
                app_element = await page.query_selector('[data-testid="total-applications"], .text-2xl:has-text("Applications")')
                if app_element:
                    app_text = await app_element.text_content()
                    metrics["total_applications_displayed"] = app_text
            except:
                pass
            
            # Try to get any metrics from h3 elements or similar
            metric_elements = await page.query_selector_all("h3, .text-2xl, .font-bold")
            displayed_numbers = []
            for element in metric_elements[:10]:  # Check first 10 elements
                try:
                    text = await element.text_content()
                    if text and text.strip().isdigit():
                        displayed_numbers.append(text.strip())
                except:
                    pass
            
            metrics["displayed_numbers"] = displayed_numbers
            
            self.test_results["frontend_captures"]["final_dashboard"] = metrics
            
            print("📊 Final Dashboard Metrics Captured:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
            
            # Capture final screenshot
            await page.screenshot(path=self.screenshots_dir / "08_final_dashboard_state.png")
            
        except Exception as e:
            error_msg = f"Failed to capture final dashboard metrics: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def test_backend_apis(self):
        """Test backend APIs directly."""
        print("\n🔌 Phase 3: Testing Backend APIs Directly")
        print("-" * 50)
        
        
        base_url = "http://localhost:8000"
        
        # Test discovery metrics API
        await self.test_discovery_metrics_api(base_url)
        
        # Test assets API
        await self.test_assets_api(base_url)
        
        # Test applications API
        await self.test_applications_api(base_url)
        
        # Test process-raw-to-assets API
        await self.test_process_raw_assets_api(base_url)
    
    async def test_discovery_metrics_api(self, base_url: str):
        """Test the discovery metrics API."""
        print("📊 Testing Discovery Metrics API")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/discovery/assets/discovery-metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.test_results["api_responses"]["discovery_metrics"] = {
                            "status": response.status,
                            "data": data,
                            "success": True
                        }
                        print(f"✅ Discovery Metrics API: {data}")
                    else:
                        error_data = await response.text()
                        self.test_results["api_responses"]["discovery_metrics"] = {
                            "status": response.status,
                            "error": error_data,
                            "success": False
                        }
                        print(f"❌ Discovery Metrics API failed: {response.status} - {error_data}")
                        
        except Exception as e:
            error_msg = f"Discovery Metrics API test failed: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def test_assets_api(self, base_url: str):
        """Test the assets API."""
        print("📦 Testing Assets API")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/discovery/assets") as response:
                    if response.status == 200:
                        data = await response.json()
                        asset_count = len(data.get("assets", []))
                        self.test_results["api_responses"]["assets"] = {
                            "status": response.status,
                            "asset_count": asset_count,
                            "success": True
                        }
                        print(f"✅ Assets API: {asset_count} assets found")
                    else:
                        error_data = await response.text()
                        self.test_results["api_responses"]["assets"] = {
                            "status": response.status,
                            "error": error_data,
                            "success": False
                        }
                        print(f"❌ Assets API failed: {response.status} - {error_data}")
                        
        except Exception as e:
            error_msg = f"Assets API test failed: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def test_applications_api(self, base_url: str):
        """Test the applications API."""
        print("🏢 Testing Applications API")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/discovery/applications") as response:
                    if response.status == 200:
                        data = await response.json()
                        app_count = len(data.get("applications", [])) if isinstance(data.get("applications"), list) else 0
                        self.test_results["api_responses"]["applications"] = {
                            "status": response.status,
                            "application_count": app_count,
                            "data_structure": type(data.get("applications")).__name__,
                            "success": True
                        }
                        print(f"✅ Applications API: {app_count} applications found")
                    else:
                        error_data = await response.text()
                        self.test_results["api_responses"]["applications"] = {
                            "status": response.status,
                            "error": error_data,
                            "success": False
                        }
                        print(f"❌ Applications API failed: {response.status} - {error_data}")
                        
        except Exception as e:
            error_msg = f"Applications API test failed: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def test_process_raw_assets_api(self, base_url: str):
        """Test the process raw assets API if we have an import session."""
        print("⚙️ Testing Process Raw Assets API")
        
        try:
            # First, check if we have any recent import sessions
            async with AsyncSessionLocal() as session:
                recent_imports = await session.execute(
                    select(DataImport).order_by(DataImport.created_at.desc()).limit(1)
                )
                latest_import = recent_imports.scalar_one_or_none()
                
                if latest_import:
                    import_session_id = str(latest_import.id)
                    print(f"🔍 Found recent import session: {import_session_id}")
                    
                    # Test the process endpoint
                    import aiohttp
                    async with aiohttp.ClientSession() as http_session:
                        async with http_session.post(
                            f"{base_url}/api/v1/data-import/process-raw-to-assets",
                            json={"import_session_id": import_session_id}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                self.test_results["api_responses"]["process_raw_assets"] = {
                                    "status": response.status,
                                    "data": data,
                                    "success": True
                                }
                                print(f"✅ Process Raw Assets API: {data.get('message', 'Success')}")
                            else:
                                error_data = await response.text()
                                self.test_results["api_responses"]["process_raw_assets"] = {
                                    "status": response.status,
                                    "error": error_data,
                                    "success": False
                                }
                                print(f"❌ Process Raw Assets API failed: {response.status} - {error_data}")
                else:
                    print("ℹ️ No recent import sessions found to test process API")
                    
        except Exception as e:
            error_msg = f"Process Raw Assets API test failed: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def verify_database_persistence(self):
        """Verify that data was actually persisted in the database."""
        print("\n🗄️ Phase 4: Verifying Database Persistence")
        print("-" * 50)
        
        try:
            async with AsyncSessionLocal() as session:
                # Count assets after test
                asset_count = await session.execute(select(func.count(Asset.id)))
                total_assets_after = asset_count.scalar()
                
                # Count data imports after test
                import_count = await session.execute(select(func.count(DataImport.id)))
                total_imports_after = import_count.scalar()
                
                # Count raw import records after test
                raw_count = await session.execute(select(func.count(RawImportRecord.id)))
                total_raw_after = raw_count.scalar()
                
                # Get recent assets (last hour)
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_assets = await session.execute(
                    select(Asset).where(Asset.created_at >= one_hour_ago).order_by(Asset.created_at.desc())
                )
                recent_asset_list = recent_assets.scalars().all()
                
                # Get recent imports
                recent_imports = await session.execute(
                    select(DataImport).where(DataImport.created_at >= one_hour_ago).order_by(DataImport.created_at.desc())
                )
                recent_import_list = recent_imports.scalars().all()
                
                # Compare with baseline
                baseline = self.test_results["database_checks"]["baseline"]
                
                persistence_results = {
                    "assets_before": baseline["assets"],
                    "assets_after": total_assets_after,
                    "assets_added": total_assets_after - baseline["assets"],
                    "imports_before": baseline["data_imports"],
                    "imports_after": total_imports_after,
                    "imports_added": total_imports_after - baseline["data_imports"],
                    "raw_records_before": baseline["raw_import_records"],
                    "raw_records_after": total_raw_after,
                    "raw_records_added": total_raw_after - baseline["raw_import_records"],
                    "recent_assets_count": len(recent_asset_list),
                    "recent_imports_count": len(recent_import_list),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Analyze recent assets
                if recent_asset_list:
                    sample_asset = recent_asset_list[0]
                    persistence_results["sample_recent_asset"] = {
                        "id": str(sample_asset.id),
                        "name": sample_asset.name,
                        "asset_type": sample_asset.asset_type,
                        "discovery_source": sample_asset.discovery_source,
                        "discovery_method": sample_asset.discovery_method,
                        "created_at": sample_asset.created_at.isoformat()
                    }
                
                self.test_results["database_checks"]["persistence"] = persistence_results
                
                print("📊 Database Persistence Results:")
                print(f"   Assets: {baseline['assets']} → {total_assets_after} (+{total_assets_after - baseline['assets']})")
                print(f"   Imports: {baseline['data_imports']} → {total_imports_after} (+{total_imports_after - baseline['data_imports']})")
                print(f"   Raw Records: {baseline['raw_import_records']} → {total_raw_after} (+{total_raw_after - baseline['raw_import_records']})")
                print(f"   Recent Assets (last hour): {len(recent_asset_list)}")
                print(f"   Recent Imports (last hour): {len(recent_import_list)}")
                
                if recent_asset_list:
                    sample = recent_asset_list[0]
                    print(f"   Sample Recent Asset: {sample.name} ({sample.asset_type}, {sample.discovery_method})")
                
        except Exception as e:
            error_msg = f"Failed to verify database persistence: {e}"
            self.test_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
    
    async def verify_discovery_dashboard(self):
        """Verify the discovery dashboard shows updated data."""
        print("\n📱 Phase 5: Verifying Discovery Dashboard Updates")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto("http://localhost:8081/discovery/overview")
                await page.wait_for_load_state("networkidle", timeout=10000)
                await page.wait_for_timeout(5000)  # Extra wait for API calls
                
                # Capture final dashboard screenshot
                await page.screenshot(path=self.screenshots_dir / "09_final_verification_dashboard.png")
                
                # Compare initial vs final dashboard metrics
                initial = self.test_results["frontend_captures"].get("initial_dashboard", {})
                
                # Extract current metrics
                current_metrics = {}
                metric_elements = await page.query_selector_all("h3, .text-2xl, .font-bold")
                displayed_numbers = []
                for element in metric_elements[:10]:
                    try:
                        text = await element.text_content()
                        if text and text.strip().isdigit():
                            displayed_numbers.append(text.strip())
                    except:
                        pass
                
                current_metrics["displayed_numbers"] = displayed_numbers
                
                verification_results = {
                    "initial_metrics": initial,
                    "final_metrics": current_metrics,
                    "metrics_changed": initial.get("displayed_numbers") != displayed_numbers,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results["frontend_captures"]["dashboard_verification"] = verification_results
                
                print("📊 Dashboard Verification:")
                print(f"   Initial numbers: {initial.get('displayed_numbers', [])}")
                print(f"   Final numbers: {displayed_numbers}")
                print(f"   Metrics changed: {verification_results['metrics_changed']}")
                
            except Exception as e:
                error_msg = f"Failed to verify dashboard updates: {e}"
                self.test_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
            finally:
                await browser.close()
    
    async def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 Phase 6: Generating Test Report")
        print("-" * 50)
        
        try:
            # Save detailed results to JSON
            report_path = Path("e2e_test_report.json")
            with open(report_path, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            # Generate summary
            print("\n📊 TEST SUMMARY")
            print("=" * 60)
            print(f"Test Duration: {self.test_results.get('test_start')} → {self.test_results.get('test_end')}")
            print(f"Total Errors: {len(self.test_results['errors'])}")
            print(f"Overall Success: {self.test_results['success']}")
            
            # Database changes
            if "persistence" in self.test_results["database_checks"]:
                persistence = self.test_results["database_checks"]["persistence"]
                print("\n📊 DATABASE CHANGES:")
                print(f"   Assets Added: {persistence['assets_added']}")
                print(f"   Imports Added: {persistence['imports_added']}")
                print(f"   Raw Records Added: {persistence['raw_records_added']}")
            
            # API results
            print("\n🔌 API TEST RESULTS:")
            for api_name, result in self.test_results["api_responses"].items():
                status_icon = "✅" if result.get("success", False) else "❌"
                print(f"   {status_icon} {api_name}: {result.get('status', 'N/A')}")
            
            # Frontend workflow
            print("\n🎭 FRONTEND WORKFLOW:")
            for step_name, result in self.test_results["frontend_captures"].items():
                if isinstance(result, dict) and "success" in result:
                    status_icon = "✅" if result["success"] else "❌"
                    print(f"   {status_icon} {step_name}")
                else:
                    print(f"   📊 {step_name}: Captured")
            
            # Errors
            if self.test_results["errors"]:
                print("\n❌ ERRORS ENCOUNTERED:")
                for i, error in enumerate(self.test_results["errors"], 1):
                    print(f"   {i}. {error}")
            
            print(f"\n📁 Detailed report saved to: {report_path}")
            print(f"📸 Screenshots saved to: {self.screenshots_dir}")
            
        except Exception as e:
            print(f"❌ Failed to generate test report: {e}")

async def main():
    """Run the comprehensive end-to-end discovery workflow test."""
    if not PLAYWRIGHT_AVAILABLE:
        print("⚠️ Installing Playwright...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright installed")
    
    tester = DiscoveryWorkflowTester()
    await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main()) 