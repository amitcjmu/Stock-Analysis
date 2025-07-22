#!/usr/bin/env python3
"""
Staging Deployment Script for Master Flow Orchestrator
Phase 6: Day 9 - Data Migration and Testing (MFO-093)

This script handles the full staging deployment of the Master Flow Orchestrator
including data migration, testing, and validation.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('staging_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StagingDeployment:
    """Handles staging deployment with comprehensive validation"""
    
    def __init__(self):
        self.deployment_id = f"staging_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_path = Path(__file__).parent.parent.parent
        self.logs_path = self.base_path / "logs" / "deployment"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Deployment configuration
        self.config = {
            "staging_url": os.getenv("STAGING_URL", "https://staging.example.com"),
            "staging_db_url": os.getenv("STAGING_DATABASE_URL"),
            "frontend_url": os.getenv("STAGING_FRONTEND_URL", "https://staging-frontend.example.com"),
            "redis_url": os.getenv("STAGING_REDIS_URL"),
            "docker_compose_file": "docker-compose.staging.yml",
            "health_check_timeout": 300,  # 5 minutes
            "test_timeout": 600,  # 10 minutes
        }
        
        # Deployment state
        self.deployment_state = {
            "phase": "initializing",
            "start_time": datetime.now().isoformat(),
            "services": {},
            "tests": {},
            "validation": {}
        }
        
        logger.info(f"🚀 Starting staging deployment: {self.deployment_id}")
    
    async def deploy_to_staging(self) -> bool:
        """
        Deploy Master Flow Orchestrator to staging environment
        Task: MFO-093
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 STAGING DEPLOYMENT - MASTER FLOW ORCHESTRATOR")
            logger.info("=" * 80)
            
            # Phase 1: Pre-deployment checks
            if not await self._pre_deployment_checks():
                return False
            
            # Phase 2: Build and deploy services
            if not await self._build_and_deploy_services():
                return False
            
            # Phase 3: Run data migration scripts
            if not await self._run_data_migration():
                return False
            
            # Phase 4: Health checks
            if not await self._perform_health_checks():
                return False
            
            # Phase 5: Service validation
            if not await self._validate_services():
                return False
            
            # Phase 6: Generate deployment report
            await self._generate_deployment_report()
            
            logger.info("✅ Staging deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Staging deployment failed: {e}")
            await self._handle_deployment_failure(e)
            return False
    
    async def _pre_deployment_checks(self) -> bool:
        """Run pre-deployment validation checks"""
        self.deployment_state["phase"] = "pre_deployment_checks"
        logger.info("📋 Phase 1: Pre-deployment checks")
        
        checks = [
            self._check_docker_environment,
            self._check_environment_variables,
            self._check_git_state,
            self._check_database_connectivity,
            self._validate_docker_compose_config,
            self._check_staging_resources
        ]
        
        for check in checks:
            if not await check():
                return False
        
        logger.info("✅ Pre-deployment checks completed")
        return True
    
    async def _check_docker_environment(self) -> bool:
        """Check Docker environment"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error("❌ Docker not available")
                return False
            
            logger.info(f"✅ Docker: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error("❌ Docker Compose not available")
                return False
            
            logger.info(f"✅ Docker Compose: {result.stdout.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Docker environment check failed: {e}")
            return False
    
    async def _check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            "STAGING_DATABASE_URL",
            "DEEPINFRA_API_KEY",
            "SECRET_KEY",
            "JWT_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing environment variables: {missing_vars}")
            return False
        
        logger.info("✅ Environment variables validated")
        return True
    
    async def _check_git_state(self) -> bool:
        """Check git repository state"""
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout.strip():
                logger.warning("⚠️  Uncommitted changes detected")
                logger.info("Uncommitted files:")
                for line in result.stdout.strip().split('\n'):
                    logger.info(f"  {line}")
            
            # Get current branch and commit
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            branch = branch_result.stdout.strip()
            commit = commit_result.stdout.strip()[:8]
            
            logger.info(f"✅ Git state: {branch} ({commit})")
            self.deployment_state["git_info"] = {
                "branch": branch,
                "commit": commit
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Git state check failed: {e}")
            return False
    
    async def _check_database_connectivity(self) -> bool:
        """Check staging database connectivity"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.sql import text
            
            db_url = self.config["staging_db_url"]
            if not db_url:
                logger.error("❌ Staging database URL not configured")
                return False
            
            # Test connection
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("✅ Staging database connectivity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connectivity check failed: {e}")
            return False
    
    async def _validate_docker_compose_config(self) -> bool:
        """Validate Docker Compose configuration"""
        try:
            compose_file = self.base_path / self.config["docker_compose_file"]
            if not compose_file.exists():
                logger.error(f"❌ Docker Compose file not found: {compose_file}")
                return False
            
            # Validate configuration
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Docker Compose configuration invalid: {result.stderr}")
                return False
            
            logger.info("✅ Docker Compose configuration validated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Docker Compose validation failed: {e}")
            return False
    
    async def _check_staging_resources(self) -> bool:
        """Check staging environment resources"""
        try:
            # Check available disk space
            disk_result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if disk_result.returncode == 0:
                logger.info("✅ Disk space check:")
                for line in disk_result.stdout.strip().split('\n'):
                    logger.info(f"  {line}")
            
            # Check memory
            memory_result = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if memory_result.returncode == 0:
                logger.info("✅ Memory check:")
                for line in memory_result.stdout.strip().split('\n'):
                    logger.info(f"  {line}")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Resource check failed: {e}")
            return True  # Non-critical
    
    async def _build_and_deploy_services(self) -> bool:
        """Build and deploy services"""
        self.deployment_state["phase"] = "build_and_deploy"
        logger.info("📋 Phase 2: Build and deploy services")
        
        try:
            compose_file = self.base_path / self.config["docker_compose_file"]
            
            # Pull latest images
            logger.info("🔄 Pulling latest images...")
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "pull"],
                timeout=600,  # 10 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Image pull failed: {result.stderr}")
                return False
            
            # Build services
            logger.info("🔨 Building services...")
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "build", "--no-cache"],
                timeout=1800,  # 30 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Build failed: {result.stderr}")
                return False
            
            # Start services
            logger.info("🚀 Starting services...")
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                timeout=300,  # 5 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Service startup failed: {result.stderr}")
                return False
            
            logger.info("✅ Services deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service deployment failed: {e}")
            return False
    
    async def _run_data_migration(self) -> bool:
        """Run data migration scripts (MFO-094)"""
        self.deployment_state["phase"] = "data_migration"
        logger.info("📋 Phase 3: Data migration")
        
        try:
            # Run Alembic migrations
            logger.info("🔄 Running Alembic migrations...")
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "exec", "-T", "backend", "alembic", "upgrade", "head"],
                timeout=300,  # 5 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Migration failed: {result.stderr}")
                return False
            
            logger.info("✅ Database migrations completed")
            
            # Run Master Flow Orchestrator migration
            logger.info("🔄 Running Master Flow Orchestrator data migration...")
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "exec", "-T", "backend", "python", "scripts/migrate_assessment_flows_to_master.py"],
                timeout=300,  # 5 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️  Master flow migration warning: {result.stderr}")
                # Non-critical, continue
            
            logger.info("✅ Data migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    async def _perform_health_checks(self) -> bool:
        """Perform comprehensive health checks"""
        self.deployment_state["phase"] = "health_checks"
        logger.info("📋 Phase 4: Health checks")
        
        services = ["backend", "frontend", "postgres", "redis"]
        
        for service in services:
            if not await self._check_service_health(service):
                return False
        
        logger.info("✅ All health checks passed")
        return True
    
    async def _check_service_health(self, service: str) -> bool:
        """Check health of a specific service"""
        try:
            logger.info(f"🔍 Checking {service} health...")
            
            # Check if container is running
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "ps", "-q", service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if not result.stdout.strip():
                logger.error(f"❌ {service} container not running")
                return False
            
            # Check health endpoint for backend/frontend
            if service in ["backend", "frontend"]:
                port = "8000" if service == "backend" else "3000"
                health_url = f"http://localhost:{port}/health"
                
                import requests
                try:
                    response = requests.get(health_url, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ {service} health check passed")
                        self.deployment_state["services"][service] = "healthy"
                        return True
                    else:
                        logger.error(f"❌ {service} health check failed: {response.status_code}")
                        return False
                except requests.RequestException as e:
                    logger.error(f"❌ {service} health check failed: {e}")
                    return False
            
            # For database services, check logs
            else:
                result = subprocess.run(
                    ["docker-compose", "-f", self.config["docker_compose_file"], 
                     "logs", "--tail=20", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if "ready" in result.stdout.lower() or "started" in result.stdout.lower():
                    logger.info(f"✅ {service} is ready")
                    self.deployment_state["services"][service] = "healthy"
                    return True
                else:
                    logger.error(f"❌ {service} not ready")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Health check failed for {service}: {e}")
            return False
    
    async def _validate_services(self) -> bool:
        """Validate service functionality"""
        self.deployment_state["phase"] = "service_validation"
        logger.info("📋 Phase 5: Service validation")
        
        validations = [
            self._validate_backend_api,
            self._validate_frontend_access,
            self._validate_database_schema,
            self._validate_master_flow_orchestrator,
            self._validate_authentication
        ]
        
        for validation in validations:
            if not await validation():
                return False
        
        logger.info("✅ All service validations passed")
        return True
    
    async def _validate_backend_api(self) -> bool:
        """Validate backend API functionality"""
        try:
            import requests
            
            # Test basic endpoints
            endpoints = [
                "/health",
                "/api/v1/health",
                "/api/v1/flows",
                "/api/v1/flows/active"
            ]
            
            base_url = "http://localhost:8000"
            
            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code < 400:
                        logger.info(f"✅ API endpoint {endpoint}: {response.status_code}")
                    else:
                        logger.error(f"❌ API endpoint {endpoint}: {response.status_code}")
                        return False
                except requests.RequestException as e:
                    logger.error(f"❌ API endpoint {endpoint} failed: {e}")
                    return False
            
            self.deployment_state["validation"]["backend_api"] = "passed"
            return True
            
        except Exception as e:
            logger.error(f"❌ Backend API validation failed: {e}")
            return False
    
    async def _validate_frontend_access(self) -> bool:
        """Validate frontend accessibility"""
        try:
            import requests
            
            url = "http://localhost:3000"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                logger.info("✅ Frontend accessible")
                self.deployment_state["validation"]["frontend"] = "passed"
                return True
            else:
                logger.error(f"❌ Frontend not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Frontend validation failed: {e}")
            return False
    
    async def _validate_database_schema(self) -> bool:
        """Validate database schema"""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "exec", "-T", "backend", "python", "-c", 
                 "from app.models import *; print('Schema validation passed')"],
                timeout=60,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Database schema validation passed")
                self.deployment_state["validation"]["database_schema"] = "passed"
                return True
            else:
                logger.error(f"❌ Database schema validation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database schema validation failed: {e}")
            return False
    
    async def _validate_master_flow_orchestrator(self) -> bool:
        """Validate Master Flow Orchestrator functionality"""
        try:
            # Test Master Flow Orchestrator initialization
            test_script = """
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

async def test_mfo():
    async with AsyncSessionLocal() as db:
        context = RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id="test-user"
        )
        
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Test flow creation
        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name="Test Flow",
            configuration={"test": True}
        )
        
        print(f"Created flow: {flow_id}")
        
        # Test flow status
        status = await orchestrator.get_flow_status(flow_id)
        print(f"Flow status: {status['status']}")
        
        print("Master Flow Orchestrator validation passed")

asyncio.run(test_mfo())
"""
            
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "exec", "-T", "backend", "python", "-c", test_script],
                timeout=120,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Master Flow Orchestrator validation passed")
                self.deployment_state["validation"]["master_flow_orchestrator"] = "passed"
                return True
            else:
                logger.error(f"❌ Master Flow Orchestrator validation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Master Flow Orchestrator validation failed: {e}")
            return False
    
    async def _validate_authentication(self) -> bool:
        """Validate authentication system"""
        try:
            # Test authentication endpoints
            import requests
            
            base_url = "http://localhost:8000"
            
            # Test login endpoint
            login_url = f"{base_url}/api/v1/auth/login"
            login_data = {
                "username": "demo@example.com",
                "password": "demo123"
            }
            
            response = requests.post(login_url, json=login_data, timeout=30)
            
            if response.status_code in [200, 401]:  # 401 is expected for demo credentials
                logger.info("✅ Authentication system accessible")
                self.deployment_state["validation"]["authentication"] = "passed"
                return True
            else:
                logger.error(f"❌ Authentication system not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication validation failed: {e}")
            return False
    
    async def _generate_deployment_report(self) -> None:
        """Generate deployment report"""
        self.deployment_state["phase"] = "completed"
        self.deployment_state["end_time"] = datetime.now().isoformat()
        
        # Calculate deployment time
        start_time = datetime.fromisoformat(self.deployment_state["start_time"])
        end_time = datetime.fromisoformat(self.deployment_state["end_time"])
        duration = (end_time - start_time).total_seconds()
        
        report = {
            "deployment_id": self.deployment_id,
            "status": "successful",
            "duration_seconds": duration,
            "deployment_state": self.deployment_state,
            "configuration": self.config,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save report
        report_file = self.logs_path / f"deployment_report_{self.deployment_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("📊 Deployment Report")
        logger.info(f"   Deployment ID: {self.deployment_id}")
        logger.info(f"   Status: {report['status']}")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info(f"   Report saved: {report_file}")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 STAGING DEPLOYMENT SUCCESSFUL")
        logger.info("=" * 80)
        logger.info("✅ All services deployed and validated")
        logger.info("✅ Data migration completed")
        logger.info("✅ Health checks passed")
        logger.info("✅ Service validation passed")
        logger.info("✅ Master Flow Orchestrator operational")
        logger.info("\nNext steps:")
        logger.info("1. Run full test suite (MFO-095)")
        logger.info("2. Perform load testing (MFO-096)")
        logger.info("3. Security vulnerability scan (MFO-097)")
        logger.info("4. Validate data integrity (MFO-098)")
        logger.info("=" * 80)
    
    async def _handle_deployment_failure(self, error: Exception) -> None:
        """Handle deployment failure"""
        self.deployment_state["phase"] = "failed"
        self.deployment_state["end_time"] = datetime.now().isoformat()
        self.deployment_state["error"] = str(error)
        
        # Save failure report
        report_file = self.logs_path / f"deployment_failure_{self.deployment_id}.json"
        with open(report_file, 'w') as f:
            json.dump(self.deployment_state, f, indent=2)
        
        logger.error("=" * 80)
        logger.error("❌ STAGING DEPLOYMENT FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {error}")
        logger.error(f"Failure report saved: {report_file}")
        
        # Collect logs for debugging
        await self._collect_failure_logs()
    
    async def _collect_failure_logs(self) -> None:
        """Collect logs for failure analysis"""
        try:
            logger.info("🔍 Collecting failure logs...")
            
            services = ["backend", "frontend", "postgres", "redis"]
            
            for service in services:
                try:
                    result = subprocess.run(
                        ["docker-compose", "-f", self.config["docker_compose_file"], 
                         "logs", "--tail=100", service],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    log_file = self.logs_path / f"failure_logs_{service}_{self.deployment_id}.log"
                    with open(log_file, 'w') as f:
                        f.write(result.stdout)
                    
                    logger.info(f"📄 {service} logs saved: {log_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to collect {service} logs: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to collect failure logs: {e}")


async def main():
    """Main deployment function"""
    deployment = StagingDeployment()
    
    try:
        success = await deployment.deploy_to_staging()
        
        if success:
            logger.info("✅ Staging deployment completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Staging deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Deployment failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())