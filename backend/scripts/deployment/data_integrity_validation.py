#!/usr/bin/env python3
"""
Data Integrity Validation Script for Master Flow Orchestrator
Phase 6: Day 9 - Validate Data Integrity (MFO-098)

This script validates data integrity across the Master Flow Orchestrator
deployment to ensure no data loss or corruption occurred during migration.
"""

import os
import sys
import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_integrity_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIntegrityValidator:
    """Validates data integrity across the Master Flow Orchestrator system"""
    
    def __init__(self):
        self.validation_id = f"data_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_path = Path(__file__).parent.parent.parent
        self.results_path = self.base_path / "validation_reports"
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # Database configuration
        self.db_url = os.getenv("STAGING_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5434/migration_db_staging")
        self.engine = create_async_engine(self.db_url)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
        # Validation configuration
        self.config = {
            "check_referential_integrity": True,
            "check_data_consistency": True,
            "check_master_flow_orchestrator": True,
            "check_flow_relationships": True,
            "check_audit_trails": True,
            "check_performance_metrics": True,
            "sample_size": 1000,  # Number of records to sample for validation
            "tolerance_threshold": 0.01,  # 1% tolerance for statistical checks
        }
        
        # Validation results
        self.validation_results = {
            "validation_id": self.validation_id,
            "start_time": datetime.now().isoformat(),
            "configuration": self.config,
            "database_info": {
                "url": self.db_url.split('@')[1] if '@' in self.db_url else self.db_url,
                "tables_validated": [],
                "total_records": 0
            },
            "validation_checks": {
                "referential_integrity": {"status": "pending", "issues": []},
                "data_consistency": {"status": "pending", "issues": []},
                "master_flow_orchestrator": {"status": "pending", "issues": []},
                "flow_relationships": {"status": "pending", "issues": []},
                "audit_trails": {"status": "pending", "issues": []},
                "performance_metrics": {"status": "pending", "issues": []},
                "orphaned_records": {"status": "pending", "issues": []},
                "duplicate_detection": {"status": "pending", "issues": []},
                "data_types": {"status": "pending", "issues": []},
                "business_rules": {"status": "pending", "issues": []}
            },
            "statistics": {
                "total_issues": 0,
                "critical_issues": 0,
                "warning_issues": 0,
                "info_issues": 0
            },
            "summary": {
                "overall_status": "pending",
                "data_integrity_score": 0.0,
                "recommendations": []
            }
        }
        
        logger.info(f"🔍 Starting data integrity validation: {self.validation_id}")
    
    async def validate_data_integrity(self) -> bool:
        """
        Validate comprehensive data integrity
        Task: MFO-098
        """
        try:
            logger.info("=" * 80)
            logger.info("🔍 DATA INTEGRITY VALIDATION - MASTER FLOW ORCHESTRATOR")
            logger.info("=" * 80)
            
            # Phase 1: Database connectivity and schema validation
            if not await self._validate_database_connectivity():
                return False
            
            # Phase 2: Referential integrity checks
            await self._validate_referential_integrity()
            
            # Phase 3: Data consistency checks
            await self._validate_data_consistency()
            
            # Phase 4: Master Flow Orchestrator specific validation
            await self._validate_master_flow_orchestrator()
            
            # Phase 5: Flow relationship validation
            await self._validate_flow_relationships()
            
            # Phase 6: Audit trail validation
            await self._validate_audit_trails()
            
            # Phase 7: Performance metrics validation
            await self._validate_performance_metrics()
            
            # Phase 8: Orphaned records detection
            await self._detect_orphaned_records()
            
            # Phase 9: Duplicate detection
            await self._detect_duplicates()
            
            # Phase 10: Data type validation
            await self._validate_data_types()
            
            # Phase 11: Business rules validation
            await self._validate_business_rules()
            
            # Phase 12: Generate validation report
            await self._generate_validation_report()
            
            # Determine overall success
            critical_issues = self.validation_results["statistics"]["critical_issues"]
            
            if critical_issues == 0:
                logger.info("✅ Data integrity validation PASSED!")
                return True
            else:
                logger.error(f"❌ Data integrity validation FAILED - {critical_issues} critical issues found")
                return False
            
        except Exception as e:
            logger.error(f"❌ Data integrity validation failed: {e}")
            await self._handle_validation_failure(e)
            return False
        finally:
            await self.engine.dispose()
    
    async def _validate_database_connectivity(self) -> bool:
        """Validate database connectivity and basic schema"""
        logger.info("📋 Phase 1: Database connectivity and schema validation")
        
        try:
            async with self.async_session() as session:
                # Test basic connectivity
                result = await session.execute(sa.text("SELECT 1"))
                result.fetchone()
                
                # Get table list
                tables_query = sa.text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                
                tables_result = await session.execute(tables_query)
                tables = [row.table_name for row in tables_result.fetchall()]
                
                self.validation_results["database_info"]["tables_validated"] = tables
                
                # Check required tables exist
                required_tables = [
                    "crewai_flow_state_extensions",
                    "discovery_flows",
                    "assessment_flows",
                    "assets",
                    "users",
                    "client_accounts",
                    "engagements"
                ]
                
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    self._add_issue(
                        "referential_integrity",
                        "critical",
                        f"Missing required tables: {missing_tables}",
                        {"missing_tables": missing_tables}
                    )
                    return False
                
                # Get total record count
                total_records = 0
                for table in tables:
                    try:
                        count_result = await session.execute(sa.text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        total_records += count
                    except Exception as e:
                        logger.warning(f"Could not count records in table {table}: {e}")
                
                self.validation_results["database_info"]["total_records"] = total_records
                
                logger.info(f"✅ Database connectivity validated - {len(tables)} tables, {total_records} total records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Database connectivity validation failed: {e}")
            self._add_issue(
                "referential_integrity",
                "critical",
                f"Database connectivity failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def _validate_referential_integrity(self) -> None:
        """Validate referential integrity constraints"""
        logger.info("🔍 Phase 2: Referential integrity validation")
        
        try:
            self.validation_results["validation_checks"]["referential_integrity"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check foreign key constraints
                referential_checks = [
                    {
                        "name": "crewai_flow_state_extensions -> client_accounts",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions cse
                            LEFT JOIN client_accounts ca ON cse.client_account_id = ca.id
                            WHERE ca.id IS NULL AND cse.client_account_id IS NOT NULL
                        """
                    },
                    {
                        "name": "crewai_flow_state_extensions -> engagements",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions cse
                            LEFT JOIN engagements e ON cse.engagement_id = e.id
                            WHERE e.id IS NULL AND cse.engagement_id IS NOT NULL
                        """
                    },
                    {
                        "name": "discovery_flows -> crewai_flow_state_extensions",
                        "query": """
                            SELECT COUNT(*) FROM discovery_flows df
                            LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                            WHERE cse.flow_id IS NULL
                        """
                    },
                    {
                        "name": "assessment_flows -> crewai_flow_state_extensions",
                        "query": """
                            SELECT COUNT(*) FROM assessment_flows af
                            LEFT JOIN crewai_flow_state_extensions cse ON af.flow_id = cse.flow_id
                            WHERE cse.flow_id IS NULL
                        """
                    },
                    {
                        "name": "assets -> client_accounts",
                        "query": """
                            SELECT COUNT(*) FROM assets a
                            LEFT JOIN client_accounts ca ON a.client_account_id = ca.id
                            WHERE ca.id IS NULL AND a.client_account_id IS NOT NULL
                        """
                    },
                    {
                        "name": "assets -> flows (via flow_id)",
                        "query": """
                            SELECT COUNT(*) FROM assets a
                            LEFT JOIN crewai_flow_state_extensions cse ON a.flow_id = cse.flow_id
                            WHERE cse.flow_id IS NULL AND a.flow_id IS NOT NULL
                        """
                    }
                ]
                
                for check in referential_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        orphan_count = result.scalar()
                        
                        if orphan_count > 0:
                            self._add_issue(
                                "referential_integrity",
                                "critical",
                                f"Referential integrity violation: {check['name']} - {orphan_count} orphaned records",
                                {"check": check["name"], "orphan_count": orphan_count}
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "referential_integrity",
                            "warning",
                            f"Could not validate {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
            
            self.validation_results["validation_checks"]["referential_integrity"]["status"] = "completed"
            logger.info("✅ Referential integrity validation completed")
            
        except Exception as e:
            logger.error(f"❌ Referential integrity validation failed: {e}")
            self.validation_results["validation_checks"]["referential_integrity"]["status"] = "failed"
            self._add_issue(
                "referential_integrity",
                "critical",
                f"Referential integrity validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_data_consistency(self) -> None:
        """Validate data consistency across tables"""
        logger.info("🔍 Phase 3: Data consistency validation")
        
        try:
            self.validation_results["validation_checks"]["data_consistency"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check data consistency rules
                consistency_checks = [
                    {
                        "name": "Flow status consistency",
                        "query": """
                            SELECT flow_status, COUNT(*) as count
                            FROM crewai_flow_state_extensions
                            GROUP BY flow_status
                        """,
                        "expected_statuses": ["initialized", "running", "paused", "completed", "failed", "deleted"]
                    },
                    {
                        "name": "Flow type consistency",
                        "query": """
                            SELECT flow_type, COUNT(*) as count
                            FROM crewai_flow_state_extensions
                            GROUP BY flow_type
                        """,
                        "expected_types": ["discovery", "assessment", "planning", "execution", "modernize", "finops", "observability", "decommission"]
                    },
                    {
                        "name": "Timestamp consistency",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE created_at > updated_at
                        """,
                        "expected_result": 0
                    },
                    {
                        "name": "JSON field consistency",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE flow_configuration IS NULL 
                            OR flow_persistence_data IS NULL
                        """,
                        "expected_result": 0
                    }
                ]
                
                for check in consistency_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        rows = result.fetchall()
                        
                        if "expected_statuses" in check:
                            # Check valid statuses
                            actual_statuses = [row.flow_status for row in rows]
                            invalid_statuses = [status for status in actual_statuses if status not in check["expected_statuses"]]
                            
                            if invalid_statuses:
                                self._add_issue(
                                    "data_consistency",
                                    "warning",
                                    f"Invalid flow statuses found: {invalid_statuses}",
                                    {"invalid_statuses": invalid_statuses}
                                )
                            else:
                                logger.info(f"✅ {check['name']}: OK")
                                
                        elif "expected_types" in check:
                            # Check valid types
                            actual_types = [row.flow_type for row in rows]
                            invalid_types = [ftype for ftype in actual_types if ftype not in check["expected_types"]]
                            
                            if invalid_types:
                                self._add_issue(
                                    "data_consistency",
                                    "warning",
                                    f"Invalid flow types found: {invalid_types}",
                                    {"invalid_types": invalid_types}
                                )
                            else:
                                logger.info(f"✅ {check['name']}: OK")
                                
                        elif "expected_result" in check:
                            # Check expected count
                            actual_count = rows[0][0] if rows else 0
                            
                            if actual_count != check["expected_result"]:
                                self._add_issue(
                                    "data_consistency",
                                    "warning",
                                    f"{check['name']}: Expected {check['expected_result']}, got {actual_count}",
                                    {"expected": check["expected_result"], "actual": actual_count}
                                )
                            else:
                                logger.info(f"✅ {check['name']}: OK")
                        
                    except Exception as e:
                        self._add_issue(
                            "data_consistency",
                            "warning",
                            f"Could not validate {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
            
            self.validation_results["validation_checks"]["data_consistency"]["status"] = "completed"
            logger.info("✅ Data consistency validation completed")
            
        except Exception as e:
            logger.error(f"❌ Data consistency validation failed: {e}")
            self.validation_results["validation_checks"]["data_consistency"]["status"] = "failed"
            self._add_issue(
                "data_consistency",
                "critical",
                f"Data consistency validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_master_flow_orchestrator(self) -> None:
        """Validate Master Flow Orchestrator specific data"""
        logger.info("🔍 Phase 4: Master Flow Orchestrator validation")
        
        try:
            self.validation_results["validation_checks"]["master_flow_orchestrator"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check Master Flow Orchestrator specific fields
                mfo_checks = [
                    {
                        "name": "Flow performance metrics",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE phase_execution_times IS NULL
                            OR agent_performance_metrics IS NULL
                        """
                    },
                    {
                        "name": "Flow collaboration logs",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE agent_collaboration_log IS NULL
                            OR jsonb_array_length(agent_collaboration_log) = 0
                        """
                    },
                    {
                        "name": "Flow memory usage",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE memory_usage_metrics IS NULL
                        """
                    },
                    {
                        "name": "Knowledge base analytics",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE knowledge_base_analytics IS NULL
                        """
                    },
                    {
                        "name": "Learning patterns",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE learning_patterns IS NULL
                        """
                    }
                ]
                
                for check in mfo_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        missing_count = result.scalar()
                        
                        if missing_count > 0:
                            severity = "warning" if missing_count < 10 else "critical"
                            self._add_issue(
                                "master_flow_orchestrator",
                                severity,
                                f"{check['name']}: {missing_count} flows missing required Master Flow Orchestrator data",
                                {"check": check["name"], "missing_count": missing_count}
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "master_flow_orchestrator",
                            "warning",
                            f"Could not validate {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
                
                # Check flow ID format consistency
                flow_id_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE flow_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                """))
                
                invalid_flow_ids = flow_id_check.scalar()
                if invalid_flow_ids > 0:
                    self._add_issue(
                        "master_flow_orchestrator",
                        "critical",
                        f"Invalid flow ID format: {invalid_flow_ids} flows have non-UUID flow IDs",
                        {"invalid_count": invalid_flow_ids}
                    )
                else:
                    logger.info("✅ Flow ID format validation: OK")
            
            self.validation_results["validation_checks"]["master_flow_orchestrator"]["status"] = "completed"
            logger.info("✅ Master Flow Orchestrator validation completed")
            
        except Exception as e:
            logger.error(f"❌ Master Flow Orchestrator validation failed: {e}")
            self.validation_results["validation_checks"]["master_flow_orchestrator"]["status"] = "failed"
            self._add_issue(
                "master_flow_orchestrator",
                "critical",
                f"Master Flow Orchestrator validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_flow_relationships(self) -> None:
        """Validate flow relationships and dependencies"""
        logger.info("🔍 Phase 5: Flow relationship validation")
        
        try:
            self.validation_results["validation_checks"]["flow_relationships"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check discovery flow to master flow relationships
                discovery_relationship_check = await session.execute(sa.text("""
                    SELECT 
                        COUNT(df.*) as discovery_count,
                        COUNT(cse.*) as master_count
                    FROM discovery_flows df
                    LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                """))
                
                discovery_stats = discovery_relationship_check.fetchone()
                
                if discovery_stats.discovery_count != discovery_stats.master_count:
                    missing_count = discovery_stats.discovery_count - discovery_stats.master_count
                    self._add_issue(
                        "flow_relationships",
                        "critical",
                        f"Discovery flow relationship mismatch: {missing_count} discovery flows missing master flow records",
                        {"discovery_count": discovery_stats.discovery_count, "master_count": discovery_stats.master_count}
                    )
                else:
                    logger.info("✅ Discovery flow relationships: OK")
                
                # Check assessment flow to master flow relationships
                assessment_relationship_check = await session.execute(sa.text("""
                    SELECT 
                        COUNT(af.*) as assessment_count,
                        COUNT(cse.*) as master_count
                    FROM assessment_flows af
                    LEFT JOIN crewai_flow_state_extensions cse ON af.flow_id = cse.flow_id
                """))
                
                assessment_stats = assessment_relationship_check.fetchone()
                
                if assessment_stats.assessment_count != assessment_stats.master_count:
                    missing_count = assessment_stats.assessment_count - assessment_stats.master_count
                    self._add_issue(
                        "flow_relationships",
                        "critical",
                        f"Assessment flow relationship mismatch: {missing_count} assessment flows missing master flow records",
                        {"assessment_count": assessment_stats.assessment_count, "master_count": assessment_stats.master_count}
                    )
                else:
                    logger.info("✅ Assessment flow relationships: OK")
                
                # Check asset to flow relationships
                asset_flow_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM assets a
                    LEFT JOIN crewai_flow_state_extensions cse ON a.flow_id = cse.flow_id
                    WHERE a.flow_id IS NOT NULL AND cse.flow_id IS NULL
                """))
                
                orphaned_assets = asset_flow_check.scalar()
                if orphaned_assets > 0:
                    self._add_issue(
                        "flow_relationships",
                        "warning",
                        f"Orphaned assets: {orphaned_assets} assets reference non-existent flows",
                        {"orphaned_count": orphaned_assets}
                    )
                else:
                    logger.info("✅ Asset-flow relationships: OK")
            
            self.validation_results["validation_checks"]["flow_relationships"]["status"] = "completed"
            logger.info("✅ Flow relationship validation completed")
            
        except Exception as e:
            logger.error(f"❌ Flow relationship validation failed: {e}")
            self.validation_results["validation_checks"]["flow_relationships"]["status"] = "failed"
            self._add_issue(
                "flow_relationships",
                "critical",
                f"Flow relationship validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_audit_trails(self) -> None:
        """Validate audit trails and logging"""
        logger.info("🔍 Phase 6: Audit trail validation")
        
        try:
            self.validation_results["validation_checks"]["audit_trails"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check collaboration log completeness
                collaboration_check = await session.execute(sa.text("""
                    SELECT 
                        flow_id,
                        flow_status,
                        jsonb_array_length(agent_collaboration_log) as log_entries
                    FROM crewai_flow_state_extensions
                    WHERE flow_status IN ('completed', 'failed')
                    AND jsonb_array_length(agent_collaboration_log) = 0
                """))
                
                flows_missing_logs = collaboration_check.fetchall()
                if flows_missing_logs:
                    self._add_issue(
                        "audit_trails",
                        "warning",
                        f"Completed flows missing collaboration logs: {len(flows_missing_logs)} flows",
                        {"missing_log_flows": [str(flow.flow_id) for flow in flows_missing_logs]}
                    )
                else:
                    logger.info("✅ Collaboration logs: OK")
                
                # Check timestamp consistency in logs
                timestamp_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE created_at > updated_at
                    OR updated_at > NOW()
                """))
                
                invalid_timestamps = timestamp_check.scalar()
                if invalid_timestamps > 0:
                    self._add_issue(
                        "audit_trails",
                        "critical",
                        f"Invalid timestamps: {invalid_timestamps} flows have inconsistent timestamps",
                        {"invalid_count": invalid_timestamps}
                    )
                else:
                    logger.info("✅ Timestamp consistency: OK")
                
                # Check user ID tracking
                user_tracking_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE user_id IS NULL OR user_id = ''
                """))
                
                missing_user_ids = user_tracking_check.scalar()
                if missing_user_ids > 0:
                    self._add_issue(
                        "audit_trails",
                        "warning",
                        f"Missing user tracking: {missing_user_ids} flows missing user ID",
                        {"missing_count": missing_user_ids}
                    )
                else:
                    logger.info("✅ User ID tracking: OK")
            
            self.validation_results["validation_checks"]["audit_trails"]["status"] = "completed"
            logger.info("✅ Audit trail validation completed")
            
        except Exception as e:
            logger.error(f"❌ Audit trail validation failed: {e}")
            self.validation_results["validation_checks"]["audit_trails"]["status"] = "failed"
            self._add_issue(
                "audit_trails",
                "critical",
                f"Audit trail validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_performance_metrics(self) -> None:
        """Validate performance metrics integrity"""
        logger.info("🔍 Phase 7: Performance metrics validation")
        
        try:
            self.validation_results["validation_checks"]["performance_metrics"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check execution time consistency
                execution_time_check = await session.execute(sa.text("""
                    SELECT 
                        flow_id,
                        phase_execution_times
                    FROM crewai_flow_state_extensions
                    WHERE phase_execution_times IS NOT NULL
                    AND phase_execution_times != '{}'::jsonb
                """))
                
                flows_with_metrics = execution_time_check.fetchall()
                
                invalid_metrics_count = 0
                for flow in flows_with_metrics:
                    try:
                        if isinstance(flow.phase_execution_times, dict):
                            for phase, time_ms in flow.phase_execution_times.items():
                                if not isinstance(time_ms, (int, float)) or time_ms < 0:
                                    invalid_metrics_count += 1
                                    break
                    except Exception:
                        invalid_metrics_count += 1
                
                if invalid_metrics_count > 0:
                    self._add_issue(
                        "performance_metrics",
                        "warning",
                        f"Invalid performance metrics: {invalid_metrics_count} flows have invalid execution times",
                        {"invalid_count": invalid_metrics_count}
                    )
                else:
                    logger.info("✅ Execution time metrics: OK")
                
                # Check memory usage metrics
                memory_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE flow_status = 'completed'
                    AND (memory_usage_metrics IS NULL OR memory_usage_metrics = '{}'::jsonb)
                """))
                
                missing_memory_metrics = memory_check.scalar()
                if missing_memory_metrics > 0:
                    self._add_issue(
                        "performance_metrics",
                        "info",
                        f"Missing memory metrics: {missing_memory_metrics} completed flows missing memory usage data",
                        {"missing_count": missing_memory_metrics}
                    )
                else:
                    logger.info("✅ Memory usage metrics: OK")
                
                # Check agent performance metrics
                agent_performance_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE flow_status = 'completed'
                    AND (agent_performance_metrics IS NULL OR agent_performance_metrics = '{}'::jsonb)
                """))
                
                missing_agent_metrics = agent_performance_check.scalar()
                if missing_agent_metrics > 0:
                    self._add_issue(
                        "performance_metrics",
                        "info",
                        f"Missing agent metrics: {missing_agent_metrics} completed flows missing agent performance data",
                        {"missing_count": missing_agent_metrics}
                    )
                else:
                    logger.info("✅ Agent performance metrics: OK")
            
            self.validation_results["validation_checks"]["performance_metrics"]["status"] = "completed"
            logger.info("✅ Performance metrics validation completed")
            
        except Exception as e:
            logger.error(f"❌ Performance metrics validation failed: {e}")
            self.validation_results["validation_checks"]["performance_metrics"]["status"] = "failed"
            self._add_issue(
                "performance_metrics",
                "critical",
                f"Performance metrics validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _detect_orphaned_records(self) -> None:
        """Detect orphaned records across tables"""
        logger.info("🔍 Phase 8: Orphaned records detection")
        
        try:
            self.validation_results["validation_checks"]["orphaned_records"]["status"] = "running"
            
            async with self.async_session() as session:
                orphan_checks = [
                    {
                        "name": "Orphaned assets",
                        "query": """
                            SELECT COUNT(*) FROM assets a
                            LEFT JOIN client_accounts ca ON a.client_account_id = ca.id
                            WHERE ca.id IS NULL
                        """
                    },
                    {
                        "name": "Orphaned discovery flows",
                        "query": """
                            SELECT COUNT(*) FROM discovery_flows df
                            LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                            WHERE cse.flow_id IS NULL
                        """
                    },
                    {
                        "name": "Orphaned assessment flows",
                        "query": """
                            SELECT COUNT(*) FROM assessment_flows af
                            LEFT JOIN crewai_flow_state_extensions cse ON af.flow_id = cse.flow_id
                            WHERE cse.flow_id IS NULL
                        """
                    },
                    {
                        "name": "Orphaned user profiles",
                        "query": """
                            SELECT COUNT(*) FROM user_profiles up
                            LEFT JOIN users u ON up.user_id = u.id
                            WHERE u.id IS NULL
                        """
                    }
                ]
                
                total_orphans = 0
                for check in orphan_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        orphan_count = result.scalar()
                        total_orphans += orphan_count
                        
                        if orphan_count > 0:
                            severity = "critical" if orphan_count > 10 else "warning"
                            self._add_issue(
                                "orphaned_records",
                                severity,
                                f"{check['name']}: {orphan_count} orphaned records found",
                                {"check": check["name"], "orphan_count": orphan_count}
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "orphaned_records",
                            "warning",
                            f"Could not check {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
                
                if total_orphans == 0:
                    logger.info("✅ No orphaned records found")
            
            self.validation_results["validation_checks"]["orphaned_records"]["status"] = "completed"
            logger.info("✅ Orphaned records detection completed")
            
        except Exception as e:
            logger.error(f"❌ Orphaned records detection failed: {e}")
            self.validation_results["validation_checks"]["orphaned_records"]["status"] = "failed"
            self._add_issue(
                "orphaned_records",
                "critical",
                f"Orphaned records detection failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _detect_duplicates(self) -> None:
        """Detect duplicate records"""
        logger.info("🔍 Phase 9: Duplicate detection")
        
        try:
            self.validation_results["validation_checks"]["duplicate_detection"]["status"] = "running"
            
            async with self.async_session() as session:
                duplicate_checks = [
                    {
                        "name": "Duplicate flow IDs",
                        "query": """
                            SELECT flow_id, COUNT(*) as count
                            FROM crewai_flow_state_extensions
                            GROUP BY flow_id
                            HAVING COUNT(*) > 1
                        """
                    },
                    {
                        "name": "Duplicate user emails",
                        "query": """
                            SELECT email, COUNT(*) as count
                            FROM users
                            GROUP BY email
                            HAVING COUNT(*) > 1
                        """
                    },
                    {
                        "name": "Duplicate asset identifiers",
                        "query": """
                            SELECT asset_name, client_account_id, COUNT(*) as count
                            FROM assets
                            WHERE asset_name IS NOT NULL
                            GROUP BY asset_name, client_account_id
                            HAVING COUNT(*) > 1
                        """
                    }
                ]
                
                total_duplicates = 0
                for check in duplicate_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        duplicate_groups = result.fetchall()
                        
                        if duplicate_groups:
                            total_duplicates += len(duplicate_groups)
                            self._add_issue(
                                "duplicate_detection",
                                "warning",
                                f"{check['name']}: {len(duplicate_groups)} duplicate groups found",
                                {"check": check["name"], "duplicate_groups": len(duplicate_groups)}
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "duplicate_detection",
                            "warning",
                            f"Could not check {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
                
                if total_duplicates == 0:
                    logger.info("✅ No duplicates found")
            
            self.validation_results["validation_checks"]["duplicate_detection"]["status"] = "completed"
            logger.info("✅ Duplicate detection completed")
            
        except Exception as e:
            logger.error(f"❌ Duplicate detection failed: {e}")
            self.validation_results["validation_checks"]["duplicate_detection"]["status"] = "failed"
            self._add_issue(
                "duplicate_detection",
                "critical",
                f"Duplicate detection failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_data_types(self) -> None:
        """Validate data types and formats"""
        logger.info("🔍 Phase 10: Data type validation")
        
        try:
            self.validation_results["validation_checks"]["data_types"]["status"] = "running"
            
            async with self.async_session() as session:
                # Check JSON field validity
                json_checks = [
                    {
                        "table": "crewai_flow_state_extensions",
                        "field": "flow_configuration",
                        "name": "Flow configuration JSON"
                    },
                    {
                        "table": "crewai_flow_state_extensions",
                        "field": "flow_persistence_data",
                        "name": "Flow persistence data JSON"
                    },
                    {
                        "table": "crewai_flow_state_extensions",
                        "field": "agent_collaboration_log",
                        "name": "Agent collaboration log JSON"
                    }
                ]
                
                for check in json_checks:
                    try:
                        # Check for invalid JSON
                        result = await session.execute(sa.text(f"""
                            SELECT COUNT(*) FROM {check['table']}
                            WHERE {check['field']} IS NOT NULL
                            AND NOT (
                                {check['field']}::text ~ '^[\\s]*[\\[\\{{].*[\\]\\}}][\\s]*$'
                                OR {check['field']}::text IN ('null', '{}', '[]')
                            )
                        """))
                        
                        invalid_json_count = result.scalar()
                        
                        if invalid_json_count > 0:
                            self._add_issue(
                                "data_types",
                                "critical",
                                f"{check['name']}: {invalid_json_count} records have invalid JSON format",
                                {"check": check["name"], "invalid_count": invalid_json_count}
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "data_types",
                            "warning",
                            f"Could not validate {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
                
                # Check UUID format for flow IDs
                uuid_check = await session.execute(sa.text("""
                    SELECT COUNT(*) FROM crewai_flow_state_extensions
                    WHERE flow_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                """))
                
                invalid_uuids = uuid_check.scalar()
                if invalid_uuids > 0:
                    self._add_issue(
                        "data_types",
                        "critical",
                        f"Invalid UUID format: {invalid_uuids} flows have invalid flow ID format",
                        {"invalid_count": invalid_uuids}
                    )
                else:
                    logger.info("✅ UUID format validation: OK")
            
            self.validation_results["validation_checks"]["data_types"]["status"] = "completed"
            logger.info("✅ Data type validation completed")
            
        except Exception as e:
            logger.error(f"❌ Data type validation failed: {e}")
            self.validation_results["validation_checks"]["data_types"]["status"] = "failed"
            self._add_issue(
                "data_types",
                "critical",
                f"Data type validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _validate_business_rules(self) -> None:
        """Validate business rules and constraints"""
        logger.info("🔍 Phase 11: Business rules validation")
        
        try:
            self.validation_results["validation_checks"]["business_rules"]["status"] = "running"
            
            async with self.async_session() as session:
                business_rule_checks = [
                    {
                        "name": "Flow name constraints",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE flow_name IS NULL OR TRIM(flow_name) = ''
                        """,
                        "severity": "warning",
                        "description": "Flows should have meaningful names"
                    },
                    {
                        "name": "Client account association",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE client_account_id IS NULL
                        """,
                        "severity": "critical",
                        "description": "All flows must be associated with a client account"
                    },
                    {
                        "name": "Engagement association",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE engagement_id IS NULL
                        """,
                        "severity": "critical",
                        "description": "All flows must be associated with an engagement"
                    },
                    {
                        "name": "Asset ownership validation",
                        "query": """
                            SELECT COUNT(*) FROM assets
                            WHERE client_account_id IS NULL
                        """,
                        "severity": "critical",
                        "description": "All assets must have an owner (client account)"
                    },
                    {
                        "name": "Flow lifecycle consistency",
                        "query": """
                            SELECT COUNT(*) FROM crewai_flow_state_extensions
                            WHERE flow_status = 'completed'
                            AND (
                                jsonb_array_length(agent_collaboration_log) = 0
                                OR phase_execution_times IS NULL
                                OR phase_execution_times = '{}'::jsonb
                            )
                        """,
                        "severity": "warning",
                        "description": "Completed flows should have execution data"
                    }
                ]
                
                for check in business_rule_checks:
                    try:
                        result = await session.execute(sa.text(check["query"]))
                        violation_count = result.scalar()
                        
                        if violation_count > 0:
                            self._add_issue(
                                "business_rules",
                                check["severity"],
                                f"{check['name']}: {violation_count} violations - {check['description']}",
                                {
                                    "check": check["name"],
                                    "violation_count": violation_count,
                                    "description": check["description"]
                                }
                            )
                        else:
                            logger.info(f"✅ {check['name']}: OK")
                            
                    except Exception as e:
                        self._add_issue(
                            "business_rules",
                            "warning",
                            f"Could not validate {check['name']}: {str(e)}",
                            {"check": check["name"], "error": str(e)}
                        )
            
            self.validation_results["validation_checks"]["business_rules"]["status"] = "completed"
            logger.info("✅ Business rules validation completed")
            
        except Exception as e:
            logger.error(f"❌ Business rules validation failed: {e}")
            self.validation_results["validation_checks"]["business_rules"]["status"] = "failed"
            self._add_issue(
                "business_rules",
                "critical",
                f"Business rules validation failed: {str(e)}",
                {"error": str(e)}
            )
    
    def _add_issue(self, category: str, severity: str, description: str, details: Dict[str, Any]) -> None:
        """Add a validation issue"""
        issue = {
            "id": f"ISSUE-{self.validation_results['statistics']['total_issues'] + 1:04d}",
            "category": category,
            "severity": severity.lower(),
            "description": description,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_results["validation_checks"][category]["issues"].append(issue)
        self.validation_results["statistics"]["total_issues"] += 1
        self.validation_results["statistics"][f"{severity.lower()}_issues"] += 1
        
        logger.warning(f"🚨 {severity.upper()}: {description}")
    
    async def _generate_validation_report(self) -> None:
        """Generate comprehensive validation report"""
        self.validation_results["end_time"] = datetime.now().isoformat()
        
        # Calculate validation duration
        start_time = datetime.fromisoformat(self.validation_results["start_time"])
        end_time = datetime.fromisoformat(self.validation_results["end_time"])
        duration = (end_time - start_time).total_seconds()
        
        self.validation_results["duration_seconds"] = duration
        
        # Calculate data integrity score
        total_issues = self.validation_results["statistics"]["total_issues"]
        critical_issues = self.validation_results["statistics"]["critical_issues"]
        
        if total_issues == 0:
            integrity_score = 100.0
        else:
            # Score based on severity weights
            critical_weight = 10
            warning_weight = 3
            info_weight = 1
            
            weighted_issues = (
                critical_issues * critical_weight +
                self.validation_results["statistics"]["warning_issues"] * warning_weight +
                self.validation_results["statistics"]["info_issues"] * info_weight
            )
            
            # Calculate score (100 - penalty based on weighted issues)
            max_penalty = 100
            penalty = min(weighted_issues * 5, max_penalty)  # Max 5 points per weighted issue
            integrity_score = max(0, 100 - penalty)
        
        self.validation_results["summary"]["data_integrity_score"] = integrity_score
        
        # Determine overall status
        if critical_issues == 0:
            if self.validation_results["statistics"]["warning_issues"] == 0:
                overall_status = "excellent"
            elif self.validation_results["statistics"]["warning_issues"] <= 5:
                overall_status = "good"
            else:
                overall_status = "acceptable"
        else:
            overall_status = "failed"
        
        self.validation_results["summary"]["overall_status"] = overall_status
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Save detailed report
        report_file = self.results_path / f"data_integrity_report_{self.validation_id}.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        # Generate executive summary
        summary_file = self.results_path / f"data_integrity_summary_{self.validation_id}.txt"
        with open(summary_file, 'w') as f:
            self._write_validation_summary(f)
        
        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("🔍 DATA INTEGRITY VALIDATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Validation ID: {self.validation_id}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Total Records Validated: {self.validation_results['database_info']['total_records']}")
        logger.info(f"Total Issues: {total_issues}")
        logger.info(f"Critical Issues: {critical_issues}")
        logger.info(f"Warning Issues: {self.validation_results['statistics']['warning_issues']}")
        logger.info(f"Info Issues: {self.validation_results['statistics']['info_issues']}")
        logger.info(f"Data Integrity Score: {integrity_score:.1f}%")
        logger.info(f"Overall Status: {overall_status.upper()}")
        logger.info(f"Detailed report: {report_file}")
        logger.info(f"Executive summary: {summary_file}")
        
        # Validation checks summary
        logger.info("\n📋 Validation Checks Summary:")
        for check_name, check_result in self.validation_results["validation_checks"].items():
            status = check_result["status"]
            issue_count = len(check_result["issues"])
            status_icon = "✅" if status == "completed" and issue_count == 0 else "⚠️" if issue_count > 0 else "❌"
            logger.info(f"  {check_name}: {status_icon} {status} ({issue_count} issues)")
        
        # Overall assessment
        if critical_issues == 0:
            logger.info("\n🎉 DATA INTEGRITY VALIDATION PASSED!")
            logger.info("✅ No critical data integrity issues found")
            logger.info("✅ Ready for rollback procedure testing (MFO-099)")
        else:
            logger.error(f"\n❌ DATA INTEGRITY VALIDATION FAILED!")
            logger.error(f"🚨 {critical_issues} critical issues must be resolved")
            logger.error("🔧 Data integrity issues must be fixed before production")
        
        logger.info("=" * 80)
    
    def _generate_recommendations(self) -> None:
        """Generate data integrity recommendations"""
        recommendations = []
        
        # Category-based recommendations
        category_issues = {}
        for check_name, check_result in self.validation_results["validation_checks"].items():
            if check_result["issues"]:
                category_issues[check_name] = len(check_result["issues"])
        
        category_recommendations = {
            "referential_integrity": "Fix foreign key constraints and ensure proper relationships between tables",
            "data_consistency": "Implement data validation rules and ensure consistent data formats",
            "master_flow_orchestrator": "Complete Master Flow Orchestrator data migration and ensure all required fields are populated",
            "flow_relationships": "Repair flow relationships and ensure proper linkage between flow types and master flows",
            "audit_trails": "Improve audit logging and ensure complete tracking of flow operations",
            "performance_metrics": "Implement comprehensive performance tracking for all flow operations",
            "orphaned_records": "Clean up orphaned records and implement proper cascade delete operations",
            "duplicate_detection": "Implement unique constraints and remove duplicate records",
            "data_types": "Fix data type inconsistencies and implement proper validation",
            "business_rules": "Implement business rule validation and ensure data meets business requirements"
        }
        
        for category, issue_count in category_issues.items():
            if category in category_recommendations:
                priority = "critical" if issue_count > 5 else "high" if issue_count > 2 else "medium"
                recommendations.append({
                    "category": category,
                    "priority": priority,
                    "recommendation": category_recommendations[category],
                    "affected_items": issue_count
                })
        
        # Add general recommendations
        if self.validation_results["statistics"]["critical_issues"] > 0:
            recommendations.append({
                "category": "general",
                "priority": "critical",
                "recommendation": "Resolve all critical data integrity issues before production deployment",
                "affected_items": self.validation_results["statistics"]["critical_issues"]
            })
        
        if self.validation_results["statistics"]["warning_issues"] > 10:
            recommendations.append({
                "category": "general",
                "priority": "high",
                "recommendation": "Address warning-level issues to improve data quality and system reliability",
                "affected_items": self.validation_results["statistics"]["warning_issues"]
            })
        
        self.validation_results["summary"]["recommendations"] = recommendations
    
    def _write_validation_summary(self, file_handle) -> None:
        """Write validation executive summary"""
        file_handle.write("DATA INTEGRITY VALIDATION - EXECUTIVE SUMMARY\n")
        file_handle.write("=" * 50 + "\n\n")
        
        file_handle.write(f"Validation ID: {self.validation_id}\n")
        file_handle.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file_handle.write(f"Database: {self.validation_results['database_info']['url']}\n")
        file_handle.write(f"Total Records: {self.validation_results['database_info']['total_records']}\n\n")
        
        file_handle.write("VALIDATION SUMMARY:\n")
        file_handle.write(f"  Overall Status: {self.validation_results['summary']['overall_status'].upper()}\n")
        file_handle.write(f"  Data Integrity Score: {self.validation_results['summary']['data_integrity_score']:.1f}%\n")
        file_handle.write(f"  Total Issues: {self.validation_results['statistics']['total_issues']}\n")
        file_handle.write(f"  Critical: {self.validation_results['statistics']['critical_issues']}\n")
        file_handle.write(f"  Warning: {self.validation_results['statistics']['warning_issues']}\n")
        file_handle.write(f"  Info: {self.validation_results['statistics']['info_issues']}\n\n")
        
        file_handle.write("VALIDATION CHECKS:\n")
        for check_name, check_result in self.validation_results["validation_checks"].items():
            status = check_result["status"]
            issue_count = len(check_result["issues"])
            file_handle.write(f"  {check_name}: {status.upper()} ({issue_count} issues)\n")
        
        if self.validation_results["summary"]["recommendations"]:
            file_handle.write("\nTOP RECOMMENDATIONS:\n")
            for rec in self.validation_results["summary"]["recommendations"][:5]:
                file_handle.write(f"  [{rec['priority'].upper()}] {rec['recommendation']}\n")
        
        file_handle.write("\nNext Steps:\n")
        if self.validation_results["statistics"]["critical_issues"] == 0:
            file_handle.write("  - Data integrity validation PASSED\n")
            file_handle.write("  - Proceed to rollback procedure testing (MFO-099)\n")
        else:
            file_handle.write("  - Resolve critical data integrity issues\n")
            file_handle.write("  - Re-run validation after fixes\n")
            file_handle.write("  - Do not proceed to production until all critical issues are resolved\n")
    
    async def _handle_validation_failure(self, error: Exception) -> None:
        """Handle validation failure"""
        self.validation_results["execution_error"] = str(error)
        self.validation_results["end_time"] = datetime.now().isoformat()
        
        # Save failure report
        failure_report_file = self.results_path / f"data_validation_failure_{self.validation_id}.json"
        with open(failure_report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        logger.error("=" * 80)
        logger.error("❌ DATA INTEGRITY VALIDATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {error}")
        logger.error(f"Failure report saved: {failure_report_file}")
        logger.error("=" * 80)


async def main():
    """Main validation function"""
    validator = DataIntegrityValidator()
    
    try:
        success = await validator.validate_data_integrity()
        
        if success:
            logger.info("✅ Data integrity validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Data integrity validation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Data integrity validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Data integrity validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())