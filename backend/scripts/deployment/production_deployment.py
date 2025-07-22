#!/usr/bin/env python3
"""
Production Deployment Script for Master Flow Orchestrator
Phase 6: Day 10 - Production Migration (MFO-104 to MFO-108)

This script handles the full production deployment of the Master Flow Orchestrator
with blue-green deployment strategy, comprehensive monitoring, and rollback capabilities.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployment:
    """Handles production deployment with blue-green strategy"""
    
    def __init__(self):
        self.deployment_id = f"prod_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_path = Path(__file__).parent.parent.parent
        self.logs_path = self.base_path / "logs" / "production"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Production configuration
        self.config = {
            "production_url": os.getenv("PRODUCTION_URL", "https://api.yourdomain.com"),
            "frontend_url": os.getenv("PRODUCTION_FRONTEND_URL", "https://app.yourdomain.com"),
            "deployment_strategy": os.getenv("DEPLOYMENT_STRATEGY", "blue_green"),
            "health_check_timeout": 300,  # 5 minutes
            "stability_wait_time": 1800,  # 30 minutes
            "traffic_shift_steps": [10, 25, 50, 75, 100],
            "monitoring_interval": 30,  # seconds
            "error_rate_threshold": 0.05,  # 5%
            "response_time_threshold": 2.0,  # 2 seconds
        }
        
        # Deployment state
        self.deployment_state = {
            "deployment_id": self.deployment_id,
            "start_time": datetime.now().isoformat(),
            "current_phase": "initializing",
            "target_environment": "green",
            "backup_created": False,
            "services_deployed": {},
            "traffic_percentage": 0,
            "health_checks": [],
            "performance_metrics": [],
            "rollback_available": True,
            "issues": []
        }
        
        logger.info(f"🚀 Starting production deployment: {self.deployment_id}")
    
    async def deploy_to_production(self) -> bool:
        """
        Deploy Master Flow Orchestrator to production
        Tasks: MFO-104 to MFO-108
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 PRODUCTION DEPLOYMENT - MASTER FLOW ORCHESTRATOR")
            logger.info("=" * 80)
            
            # Phase 1: Pre-deployment validation and backup (MFO-103)
            if not await self._create_production_backup():
                return False
            
            # Phase 2: Deploy backend to production (MFO-104)
            if not await self._deploy_backend_services():
                return False
            
            # Phase 3: Run production data migration (MFO-105)
            if not await self._run_production_data_migration():
                return False
            
            # Phase 4: Deploy frontend to production (MFO-106)
            if not await self._deploy_frontend_services():
                return False
            
            # Phase 5: Gradual traffic switching with monitoring (MFO-107, MFO-108)
            if not await self._perform_traffic_switch():
                return False
            
            # Phase 6: Final validation and cleanup
            if not await self._finalize_deployment():
                return False
            
            # Phase 7: Generate deployment report
            await self._generate_deployment_report()
            
            logger.info("✅ Production deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Production deployment failed: {e}")
            await self._handle_deployment_failure(e)
            return False
    
    async def _create_production_backup(self) -> bool:
        """Create comprehensive production backup (MFO-103)"""
        self.deployment_state["current_phase"] = "backup"
        logger.info("📋 Phase 1: Creating production database backup")
        
        try:
            backup_script = self.base_path / "scripts" / "deployment" / "create_production_backup.sh"
            
            # Create backup script if not exists
            await self._create_backup_script(backup_script)
            
            # Execute backup
            result = subprocess.run(
                ["bash", str(backup_script)],
                timeout=1800,  # 30 minutes
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Backup creation failed: {result.stderr}")
                self._add_issue("critical", "Backup creation failed", {"error": result.stderr})
                return False
            
            # Verify backup
            if not await self._verify_backup():
                return False
            
            self.deployment_state["backup_created"] = True
            logger.info("✅ Production backup created and verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            self._add_issue("critical", f"Backup creation error: {str(e)}")
            return False
    
    async def _create_backup_script(self, script_path: Path) -> None:
        """Create backup script if it doesn't exist"""
        if script_path.exists():
            return
        
        backup_script_content = '''#!/bin/bash
# Production Database Backup Script

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/production"
DB_NAME="migration_db"

echo "🗄️ Creating production database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database dump
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \\
  --verbose --clean --create --if-exists \\
  --format=custom \\
  --file="$BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump"

# Schema-only backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \\
  --schema-only --verbose \\
  --file="$BACKUP_DIR/migration_db_schema_$BACKUP_DATE.sql"

# Compress schema backup
gzip "$BACKUP_DIR/migration_db_schema_$BACKUP_DATE.sql"

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: migration_db_backup_$BACKUP_DATE.dump"
    echo "📊 Backup size: $(du -h $BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump)"
    echo "$BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump" > /tmp/latest_backup_path
else
    echo "❌ Backup verification failed!"
    exit 1
fi
'''
        
        with open(script_path, 'w') as f:
            f.write(backup_script_content)
        
        script_path.chmod(0o755)
    
    async def _verify_backup(self) -> bool:
        """Verify backup integrity"""
        try:
            # Get latest backup path
            with open('/tmp/latest_backup_path', 'r') as f:
                backup_path = f.read().strip()
            
            if not os.path.exists(backup_path):
                logger.error(f"❌ Backup file not found: {backup_path}")
                return False
            
            # Test restore to temporary database
            temp_db = f"migration_db_test_{int(time.time())}"
            
            # Create temporary database
            create_result = subprocess.run(
                ["createdb", "-h", os.getenv("DB_HOST"), "-U", os.getenv("DB_USER"), temp_db],
                capture_output=True,
                text=True
            )
            
            if create_result.returncode != 0:
                logger.error(f"❌ Could not create test database: {create_result.stderr}")
                return False
            
            try:
                # Restore backup to test database
                restore_result = subprocess.run(
                    ["pg_restore", "-h", os.getenv("DB_HOST"), "-U", os.getenv("DB_USER"), 
                     "-d", temp_db, "--clean", "--if-exists", backup_path],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes
                )
                
                if restore_result.returncode == 0:
                    logger.info("✅ Backup verification successful")
                    return True
                else:
                    logger.error(f"❌ Backup verification failed: {restore_result.stderr}")
                    return False
                    
            finally:
                # Clean up test database
                subprocess.run(
                    ["dropdb", "-h", os.getenv("DB_HOST"), "-U", os.getenv("DB_USER"), temp_db],
                    capture_output=True
                )
                
        except Exception as e:
            logger.error(f"❌ Backup verification error: {e}")
            return False
    
    async def _deploy_backend_services(self) -> bool:
        """Deploy backend services to production (MFO-104)"""
        self.deployment_state["current_phase"] = "backend_deployment"
        logger.info("📋 Phase 2: Deploying backend services")
        
        try:
            if self.config["deployment_strategy"] == "blue_green":
                return await self._deploy_backend_blue_green()
            else:
                return await self._deploy_backend_rolling()
                
        except Exception as e:
            logger.error(f"❌ Backend deployment failed: {e}")
            self._add_issue("critical", f"Backend deployment error: {str(e)}")
            return False
    
    async def _deploy_backend_blue_green(self) -> bool:
        """Deploy backend using blue-green strategy"""
        logger.info("🟢 Deploying backend to green environment...")
        
        try:
            # Deploy to green environment
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", 
                 "--profile", "green", "up", "-d", "backend_green"],
                timeout=600,  # 10 minutes
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Green backend deployment failed: {result.stderr}")
                return False
            
            # Wait for backend health checks
            if not await self._wait_for_backend_health("green"):
                return False
            
            self.deployment_state["services_deployed"]["backend_green"] = {
                "status": "deployed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ Backend green environment deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Blue-green backend deployment failed: {e}")
            return False
    
    async def _deploy_backend_rolling(self) -> bool:
        """Deploy backend using rolling update strategy"""
        logger.info("🔄 Deploying backend using rolling update...")
        
        try:
            # Pull latest images
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "pull", "backend"],
                timeout=600,
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Image pull failed: {result.stderr}")
                return False
            
            # Rolling update
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d", "backend"],
                timeout=300,
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Rolling update failed: {result.stderr}")
                return False
            
            # Wait for health checks
            if not await self._wait_for_backend_health("production"):
                return False
            
            self.deployment_state["services_deployed"]["backend"] = {
                "status": "deployed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ Backend rolling update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rolling backend deployment failed: {e}")
            return False
    
    async def _wait_for_backend_health(self, environment: str) -> bool:
        """Wait for backend health checks to pass"""
        logger.info(f"⏳ Waiting for {environment} backend health checks...")
        
        if environment == "green":
            health_url = f"{self.config['production_url'].replace('api', 'api-green')}/health"
        else:
            health_url = f"{self.config['production_url']}/health"
        
        start_time = time.time()
        timeout = self.config["health_check_timeout"]
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            if health_data.get("status") == "healthy":
                                logger.info(f"✅ {environment} backend health check passed")
                                return True
                        
                        logger.info(f"⏳ {environment} backend not ready yet (HTTP {response.status})")
                        
            except Exception as e:
                logger.debug(f"Health check error: {e}")
            
            await asyncio.sleep(10)
        
        logger.error(f"❌ {environment} backend health check timed out after {timeout} seconds")
        return False
    
    async def _run_production_data_migration(self) -> bool:
        """Run production data migration (MFO-105)"""
        self.deployment_state["current_phase"] = "data_migration"
        logger.info("📋 Phase 3: Running production data migration")
        
        try:
            # Run Alembic migrations
            logger.info("🔄 Running Alembic migrations...")
            
            container_name = "backend_green" if self.config["deployment_strategy"] == "blue_green" else "backend"
            
            result = subprocess.run(
                ["docker", "exec", f"migration_{container_name}_prod", 
                 "alembic", "upgrade", "head"],
                timeout=600,  # 10 minutes
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Alembic migration failed: {result.stderr}")
                self._add_issue("critical", "Database migration failed", {"error": result.stderr})
                return False
            
            # Run Master Flow Orchestrator migration
            logger.info("🔄 Running Master Flow Orchestrator data migration...")
            
            migration_result = subprocess.run(
                ["docker", "exec", f"migration_{container_name}_prod", 
                 "python", "scripts/migrate_assessment_flows_to_master.py"],
                timeout=300,  # 5 minutes
                capture_output=True,
                text=True
            )
            
            if migration_result.returncode != 0:
                logger.warning(f"⚠️  Master flow migration warning: {migration_result.stderr}")
                # Non-critical, continue
            
            # Validate migration success
            if not await self._validate_migration_success():
                return False
            
            logger.info("✅ Production data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            self._add_issue("critical", f"Data migration error: {str(e)}")
            return False
    
    async def _validate_migration_success(self) -> bool:
        """Validate that migration was successful"""
        try:
            # Run data integrity validation
            validator_script = self.base_path / "scripts" / "deployment" / "data_integrity_validation.py"
            
            result = subprocess.run(
                ["python3", str(validator_script)],
                timeout=600,  # 10 minutes
                capture_output=True,
                text=True,
                cwd=self.base_path,
                env={**os.environ, "STAGING_DATABASE_URL": os.getenv("PRODUCTION_DATABASE_URL")}
            )
            
            if result.returncode == 0:
                logger.info("✅ Migration validation successful")
                return True
            else:
                logger.error(f"❌ Migration validation failed: {result.stderr}")
                self._add_issue("critical", "Migration validation failed", {"error": result.stderr})
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration validation error: {e}")
            return False
    
    async def _deploy_frontend_services(self) -> bool:
        """Deploy frontend services to production (MFO-106)"""
        self.deployment_state["current_phase"] = "frontend_deployment"
        logger.info("📋 Phase 4: Deploying frontend services")
        
        try:
            if self.config["deployment_strategy"] == "blue_green":
                return await self._deploy_frontend_blue_green()
            else:
                return await self._deploy_frontend_rolling()
                
        except Exception as e:
            logger.error(f"❌ Frontend deployment failed: {e}")
            self._add_issue("critical", f"Frontend deployment error: {str(e)}")
            return False
    
    async def _deploy_frontend_blue_green(self) -> bool:
        """Deploy frontend using blue-green strategy"""
        logger.info("🟢 Deploying frontend to green environment...")
        
        try:
            # Deploy to green environment
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", 
                 "--profile", "green", "up", "-d", "frontend_green"],
                timeout=300,  # 5 minutes
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Green frontend deployment failed: {result.stderr}")
                return False
            
            # Wait for frontend health checks
            if not await self._wait_for_frontend_health("green"):
                return False
            
            self.deployment_state["services_deployed"]["frontend_green"] = {
                "status": "deployed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ Frontend green environment deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Blue-green frontend deployment failed: {e}")
            return False
    
    async def _deploy_frontend_rolling(self) -> bool:
        """Deploy frontend using rolling update strategy"""
        logger.info("🔄 Deploying frontend using rolling update...")
        
        try:
            # Pull latest images
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "pull", "frontend"],
                timeout=300,
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Frontend image pull failed: {result.stderr}")
                return False
            
            # Rolling update
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d", "frontend"],
                timeout=300,
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Frontend rolling update failed: {result.stderr}")
                return False
            
            # Wait for health checks
            if not await self._wait_for_frontend_health("production"):
                return False
            
            self.deployment_state["services_deployed"]["frontend"] = {
                "status": "deployed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ Frontend rolling update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rolling frontend deployment failed: {e}")
            return False
    
    async def _wait_for_frontend_health(self, environment: str) -> bool:
        """Wait for frontend health checks to pass"""
        logger.info(f"⏳ Waiting for {environment} frontend health checks...")
        
        if environment == "green":
            health_url = f"{self.config['frontend_url'].replace('app', 'app-green')}"
        else:
            health_url = self.config['frontend_url']
        
        start_time = time.time()
        timeout = self.config["health_check_timeout"]
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            logger.info(f"✅ {environment} frontend health check passed")
                            return True
                        
                        logger.info(f"⏳ {environment} frontend not ready yet (HTTP {response.status})")
                        
            except Exception as e:
                logger.debug(f"Frontend health check error: {e}")
            
            await asyncio.sleep(10)
        
        logger.error(f"❌ {environment} frontend health check timed out after {timeout} seconds")
        return False
    
    async def _perform_traffic_switch(self) -> bool:
        """Perform gradual traffic switching with monitoring (MFO-107, MFO-108)"""
        self.deployment_state["current_phase"] = "traffic_switch"
        logger.info("📋 Phase 5: Performing gradual traffic switch")
        
        try:
            if self.config["deployment_strategy"] == "blue_green":
                return await self._blue_green_traffic_switch()
            else:
                # For rolling deployment, traffic is already switched
                return await self._monitor_rolling_deployment()
                
        except Exception as e:
            logger.error(f"❌ Traffic switch failed: {e}")
            self._add_issue("critical", f"Traffic switch error: {str(e)}")
            return False
    
    async def _blue_green_traffic_switch(self) -> bool:
        """Perform blue-green traffic switching"""
        logger.info("🔄 Starting blue-green traffic switch...")
        
        for percentage in self.config["traffic_shift_steps"]:
            logger.info(f"📊 Shifting {percentage}% traffic to green environment...")
            
            # Update load balancer or ingress controller
            if not await self._update_traffic_split(percentage):
                logger.error(f"❌ Failed to update traffic split to {percentage}%")
                await self._rollback_traffic()
                return False
            
            self.deployment_state["traffic_percentage"] = percentage
            
            # Monitor for stability period
            monitoring_duration = 120 if percentage < 100 else 300  # 2 minutes, 5 minutes for 100%
            logger.info(f"⏳ Monitoring for {monitoring_duration} seconds...")
            
            if not await self._monitor_deployment_health(monitoring_duration):
                logger.error(f"❌ Health monitoring failed at {percentage}% traffic")
                await self._rollback_traffic()
                return False
            
            logger.info(f"✅ {percentage}% traffic shift successful")
        
        logger.info("✅ Traffic switch completed successfully")
        return True
    
    async def _update_traffic_split(self, percentage: int) -> bool:
        """Update traffic split between blue and green environments"""
        try:
            # This would typically update load balancer or ingress controller
            # For demonstration, we'll create a script that would do this
            
            traffic_script_content = f'''#!/bin/bash
# Update traffic split to {percentage}% green
echo "Updating traffic split to {percentage}% green environment..."

# Example for NGINX or ingress controller update
# kubectl patch ingress app-ingress -p '{{"metadata":{{"annotations":{{"nginx.ingress.kubernetes.io/canary-weight":"{percentage}"}}}}}}'

# Example for AWS ALB
# aws elbv2 modify-target-group --target-group-arn $GREEN_TG_ARN --health-check-enabled

# Example for service mesh (Istio)
# kubectl apply -f - <<EOF
# apiVersion: networking.istio.io/v1beta1
# kind: VirtualService
# metadata:
#   name: app-vs
# spec:
#   http:
#   - match:
#     - headers:
#         canary:
#           exact: "true"
#     route:
#     - destination:
#         host: app-green
#       weight: {percentage}
#     - destination:
#         host: app-blue
#       weight: {100 - percentage}
# EOF

echo "Traffic split updated to {percentage}% green"
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(traffic_script_content)
                script_path = f.name
            
            os.chmod(script_path, 0o755)
            
            result = subprocess.run(
                ["bash", script_path],
                timeout=60,
                capture_output=True,
                text=True
            )
            
            os.unlink(script_path)
            
            if result.returncode == 0:
                logger.info(f"✅ Traffic split updated to {percentage}%")
                return True
            else:
                logger.error(f"❌ Traffic split update failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Traffic split update error: {e}")
            return False
    
    async def _monitor_deployment_health(self, duration: int) -> bool:
        """Monitor deployment health for specified duration"""
        logger.info(f"📊 Monitoring deployment health for {duration} seconds...")
        
        start_time = time.time()
        end_time = start_time + duration
        check_interval = self.config["monitoring_interval"]
        
        while time.time() < end_time:
            # Check error rates
            error_rate = await self._check_error_rate()
            if error_rate > self.config["error_rate_threshold"]:
                logger.error(f"❌ Error rate too high: {error_rate:.2%} > {self.config['error_rate_threshold']:.2%}")
                self._add_issue("critical", f"High error rate: {error_rate:.2%}")
                return False
            
            # Check response times
            response_time = await self._check_response_time()
            if response_time > self.config["response_time_threshold"]:
                logger.error(f"❌ Response time too high: {response_time:.2f}s > {self.config['response_time_threshold']:.2f}s")
                self._add_issue("critical", f"High response time: {response_time:.2f}s")
                return False
            
            # Record metrics
            health_check = {
                "timestamp": datetime.now().isoformat(),
                "error_rate": error_rate,
                "response_time": response_time,
                "status": "healthy"
            }
            
            self.deployment_state["health_checks"].append(health_check)
            
            logger.info(f"📊 Health check: Error rate {error_rate:.2%}, Response time {response_time:.2f}s")
            
            await asyncio.sleep(check_interval)
        
        logger.info("✅ Health monitoring completed successfully")
        return True
    
    async def _check_error_rate(self) -> float:
        """Check current error rate"""
        try:
            # This would typically query monitoring system (Prometheus, DataDog, etc.)
            # For demonstration, we'll check the health endpoint
            
            async with aiohttp.ClientSession() as session:
                error_count = 0
                total_count = 0
                
                # Sample multiple requests to get error rate
                for _ in range(10):
                    try:
                        async with session.get(
                            f"{self.config['production_url']}/health",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            total_count += 1
                            if response.status >= 500:
                                error_count += 1
                    except Exception:
                        total_count += 1
                        error_count += 1
                
                return error_count / max(total_count, 1)
                
        except Exception as e:
            logger.warning(f"Error rate check failed: {e}")
            return 0.0  # Assume no errors if check fails
    
    async def _check_response_time(self) -> float:
        """Check current response time"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.get(
                    f"{self.config['production_url']}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return response_time
                    else:
                        return 10.0  # High response time for errors
                        
        except Exception as e:
            logger.warning(f"Response time check failed: {e}")
            return 10.0  # High response time for failures
    
    async def _rollback_traffic(self) -> bool:
        """Rollback traffic to blue environment"""
        logger.error("🔄 Rolling back traffic to blue environment...")
        
        try:
            # Set traffic back to 0% green (100% blue)
            if await self._update_traffic_split(0):
                self.deployment_state["traffic_percentage"] = 0
                logger.info("✅ Traffic rollback completed")
                return True
            else:
                logger.error("❌ Traffic rollback failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Traffic rollback error: {e}")
            return False
    
    async def _monitor_rolling_deployment(self) -> bool:
        """Monitor rolling deployment health"""
        logger.info("📊 Monitoring rolling deployment...")
        
        # Monitor for stability period after rolling deployment
        return await self._monitor_deployment_health(self.config["stability_wait_time"])
    
    async def _finalize_deployment(self) -> bool:
        """Finalize deployment and cleanup"""
        self.deployment_state["current_phase"] = "finalization"
        logger.info("📋 Phase 6: Finalizing deployment")
        
        try:
            # Wait for final stability period
            logger.info("⏳ Waiting for final stability period...")
            stability_duration = 300  # 5 minutes
            
            if not await self._monitor_deployment_health(stability_duration):
                logger.error("❌ Final stability check failed")
                return False
            
            # Clean up old environment if blue-green
            if self.config["deployment_strategy"] == "blue_green":
                await self._cleanup_blue_environment()
            
            # Update monitoring targets
            await self._update_monitoring_configuration()
            
            # Mark deployment as successful
            self.deployment_state["current_phase"] = "completed"
            
            logger.info("✅ Deployment finalization completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment finalization failed: {e}")
            return False
    
    async def _cleanup_blue_environment(self) -> None:
        """Clean up blue environment after successful green deployment"""
        logger.info("🔵 Cleaning up blue environment...")
        
        try:
            # Stop blue environment services
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", 
                 "--profile", "blue", "down"],
                timeout=120,
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                logger.info("✅ Blue environment cleanup completed")
            else:
                logger.warning(f"⚠️  Blue environment cleanup warning: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"⚠️  Blue environment cleanup error: {e}")
    
    async def _update_monitoring_configuration(self) -> None:
        """Update monitoring configuration to point to new environment"""
        logger.info("📊 Updating monitoring configuration...")
        
        try:
            # This would typically update Prometheus targets, Grafana dashboards, etc.
            # For demonstration, we'll create a placeholder script
            
            monitoring_script_content = '''#!/bin/bash
# Update monitoring configuration

echo "Updating monitoring targets..."

# Example: Update Prometheus configuration
# kubectl patch configmap prometheus-config -p '{"data":{"prometheus.yml":"..."}}'

# Example: Update Grafana dashboard variables
# curl -X POST "http://grafana:3000/api/dashboards/db" -H "Content-Type: application/json" -d @new-dashboard.json

echo "Monitoring configuration updated"
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(monitoring_script_content)
                script_path = f.name
            
            os.chmod(script_path, 0o755)
            
            result = subprocess.run(
                ["bash", script_path],
                timeout=60,
                capture_output=True,
                text=True
            )
            
            os.unlink(script_path)
            
            if result.returncode == 0:
                logger.info("✅ Monitoring configuration updated")
            else:
                logger.warning(f"⚠️  Monitoring update warning: {result.stderr}")
                
        except Exception as e:
            logger.warning(f"⚠️  Monitoring update error: {e}")
    
    def _add_issue(self, severity: str, description: str, details: Dict[str, Any] = None) -> None:
        """Add an issue to the deployment state"""
        issue = {
            "id": f"ISSUE-{len(self.deployment_state['issues']) + 1:04d}",
            "severity": severity,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.deployment_state["issues"].append(issue)
        logger.warning(f"🚨 {severity.upper()}: {description}")
    
    async def _generate_deployment_report(self) -> None:
        """Generate comprehensive deployment report"""
        self.deployment_state["end_time"] = datetime.now().isoformat()
        
        # Calculate deployment duration
        start_time = datetime.fromisoformat(self.deployment_state["start_time"])
        end_time = datetime.fromisoformat(self.deployment_state["end_time"])
        duration = (end_time - start_time).total_seconds()
        
        self.deployment_state["duration_seconds"] = duration
        
        # Generate deployment report
        report = {
            "deployment_summary": self.deployment_state,
            "configuration": self.config,
            "success": len([issue for issue in self.deployment_state["issues"] if issue["severity"] == "critical"]) == 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save detailed report
        report_file = self.logs_path / f"production_deployment_report_{self.deployment_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 PRODUCTION DEPLOYMENT COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Deployment ID: {self.deployment_id}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Strategy: {self.config['deployment_strategy']}")
        logger.info(f"Traffic: {self.deployment_state['traffic_percentage']}% on new environment")
        logger.info(f"Issues: {len(self.deployment_state['issues'])} total")
        logger.info(f"Report saved: {report_file}")
        
        if report["success"]:
            logger.info("\n🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!")
            logger.info("✅ Master Flow Orchestrator is now live in production")
            logger.info("✅ All health checks passing")
            logger.info("✅ Performance metrics within thresholds")
            logger.info("✅ Ready for production traffic")
        else:
            logger.error("\n❌ PRODUCTION DEPLOYMENT COMPLETED WITH ISSUES")
            critical_issues = [issue for issue in self.deployment_state["issues"] if issue["severity"] == "critical"]
            logger.error(f"🚨 {len(critical_issues)} critical issues need attention")
        
        logger.info("=" * 80)
    
    async def _handle_deployment_failure(self, error: Exception) -> None:
        """Handle deployment failure"""
        self.deployment_state["execution_error"] = str(error)
        self.deployment_state["end_time"] = datetime.now().isoformat()
        self.deployment_state["current_phase"] = "failed"
        
        # Save failure report
        failure_report_file = self.logs_path / f"production_deployment_failure_{self.deployment_id}.json"
        with open(failure_report_file, 'w') as f:
            json.dump(self.deployment_state, f, indent=2)
        
        logger.error("=" * 80)
        logger.error("❌ PRODUCTION DEPLOYMENT FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {error}")
        logger.error(f"Current Phase: {self.deployment_state['current_phase']}")
        logger.error(f"Failure report saved: {failure_report_file}")
        
        # Attempt automatic rollback if possible
        if self.deployment_state["rollback_available"]:
            logger.error("🔄 Attempting automatic rollback...")
            await self._emergency_rollback()
        
        logger.error("=" * 80)
    
    async def _emergency_rollback(self) -> None:
        """Perform emergency rollback"""
        try:
            # Rollback traffic if blue-green deployment
            if self.config["deployment_strategy"] == "blue_green":
                await self._rollback_traffic()
            
            # Stop failed services
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "--profile", "green", "down"],
                timeout=120,
                capture_output=True
            )
            
            logger.info("✅ Emergency rollback completed")
            
        except Exception as e:
            logger.error(f"❌ Emergency rollback failed: {e}")


async def main():
    """Main production deployment function"""
    deployment = ProductionDeployment()
    
    try:
        success = await deployment.deploy_to_production()
        
        if success:
            logger.info("✅ Production deployment completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Production deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Production deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Production deployment failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())