"""
Session to Flow Compatibility Service

Provides backward compatibility during migration from session_id to flow_id.
- Maps old session_id calls to flow_id
- Handles dual-key lookups during transition
- Logs deprecation warnings
- Provides migration utilities
"""

import logging
import uuid
from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

try:
    from app.models.data_import_session import DataImportSession
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.asset import Asset
    from app.models.flow_deletion_audit import FlowDeletionAudit
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    DataImportSession = DiscoveryFlow = Asset = FlowDeletionAudit = object

logger = logging.getLogger(__name__)


class SessionFlowCompatibilityService:
    """
    Provides backward compatibility during migration from session_id to flow_id.
    
    This service acts as a bridge between the old session-based architecture
    and the new flow-based architecture, ensuring smooth transition while
    maintaining data integrity.
    """
    
    def __init__(self, db: Session, client_account_id: Optional[str] = None):
        """Initialize the compatibility service."""
        self.db = db
        self.client_account_id = client_account_id
        self._session_flow_cache: Dict[str, str] = {}
        self._flow_session_cache: Dict[str, str] = {}
    
    def get_flow_id_from_session_id(self, session_id: str) -> Optional[str]:
        """
        Get flow_id from session_id with caching and fallback strategies.
        
        Args:
            session_id: The session ID to map to flow ID
            
        Returns:
            flow_id if found, None otherwise
        """
        if not MODELS_AVAILABLE:
            logger.warning("Models not available, returning None for session_id: %s", session_id)
            return None
        
        # Check cache first
        if session_id in self._session_flow_cache:
            return self._session_flow_cache[session_id]
        
        try:
            # Strategy 1: Direct lookup in discovery_flows table
            result = self.db.execute(text("""
                SELECT flow_id 
                FROM discovery_flows 
                WHERE import_session_id = :session_id
                LIMIT 1
            """), {"session_id": session_id}).fetchone()
            
            if result:
                flow_id = str(result.flow_id)
                self._session_flow_cache[session_id] = flow_id
                self._flow_session_cache[flow_id] = session_id
                logger.debug("✅ Found flow_id %s for session_id %s", flow_id, session_id)
                return flow_id
            
            # Strategy 2: Check if session_id is actually a flow_id in old format
            result = self.db.execute(text("""
                SELECT flow_id 
                FROM discovery_flows 
                WHERE flow_id::text = :session_id
                LIMIT 1
            """), {"session_id": session_id}).fetchone()
            
            if result:
                flow_id = str(result.flow_id)
                logger.debug("✅ session_id %s is actually a flow_id", session_id)
                return flow_id
            
            # Strategy 3: Generate new flow for orphaned session
            session_result = self.db.execute(text("""
                SELECT id, client_account_id, engagement_id, session_name, created_by, created_at
                FROM data_import_sessions 
                WHERE id = :session_id
                LIMIT 1
            """), {"session_id": session_id}).fetchone()
            
            if session_result:
                new_flow_id = str(uuid.uuid4())
                
                # Create corresponding discovery_flow
                self.db.execute(text("""
                    INSERT INTO discovery_flows (
                        id, flow_id, client_account_id, engagement_id, user_id, 
                        import_session_id, flow_name, flow_description, status, 
                        progress_percentage, crewai_state_data, created_at
                    ) VALUES (
                        :id, :flow_id, :client_account_id, :engagement_id, :user_id,
                        :import_session_id, :flow_name, :flow_description, :status,
                        :progress_percentage, :crewai_state_data, :created_at
                    )
                """), {
                    'id': str(uuid.uuid4()),
                    'flow_id': new_flow_id,
                    'client_account_id': session_result.client_account_id,
                    'engagement_id': session_result.engagement_id,
                    'user_id': session_result.created_by,
                    'import_session_id': session_result.id,
                    'flow_name': f"Legacy Migration: {session_result.session_name}",
                    'flow_description': f"Auto-created during compatibility lookup",
                    'status': 'migrated',
                    'progress_percentage': 100.0,
                    'crewai_state_data': '{}',
                    'created_at': session_result.created_at
                })
                
                self.db.commit()
                
                self._session_flow_cache[session_id] = new_flow_id
                self._flow_session_cache[new_flow_id] = session_id
                
                logger.warning("⚠️ Created new flow %s for orphaned session %s", new_flow_id, session_id)
                return new_flow_id
            
            logger.warning("❌ No flow_id found for session_id %s", session_id)
            return None
            
        except Exception as e:
            logger.error("Error mapping session_id %s to flow_id: %s", session_id, e)
            return None
    
    def get_session_id_from_flow_id(self, flow_id: str) -> Optional[str]:
        """
        Get session_id from flow_id for backward compatibility.
        
        Args:
            flow_id: The flow ID to map to session ID
            
        Returns:
            session_id if found, None otherwise
        """
        if not MODELS_AVAILABLE:
            logger.warning("Models not available, returning None for flow_id: %s", flow_id)
            return None
        
        # Check cache first
        if flow_id in self._flow_session_cache:
            return self._flow_session_cache[flow_id]
        
        try:
            result = self.db.execute(text("""
                SELECT import_session_id 
                FROM discovery_flows 
                WHERE flow_id = :flow_id
                LIMIT 1
            """), {"flow_id": flow_id}).fetchone()
            
            if result and result.import_session_id:
                session_id = str(result.import_session_id)
                self._flow_session_cache[flow_id] = session_id
                self._session_flow_cache[session_id] = flow_id
                logger.debug("✅ Found session_id %s for flow_id %s", session_id, flow_id)
                return session_id
            
            logger.debug("No session_id found for flow_id %s", flow_id)
            return None
            
        except Exception as e:
            logger.error("Error mapping flow_id %s to session_id: %s", flow_id, e)
            return None
    
    def find_assets_by_identifier(self, identifier: str) -> List[Asset]:
        """
        Find assets using either session_id or flow_id.
        
        Args:
            identifier: Either session_id or flow_id
            
        Returns:
            List of assets found
        """
        if not MODELS_AVAILABLE:
            logger.warning("Models not available, returning empty list")
            return []
        
        try:
            # Try direct session_id lookup first
            assets_by_session = self.db.query(Asset).filter(
                Asset.session_id == identifier
            ).all()
            
            if assets_by_session:
                logger.debug("Found %d assets by session_id %s", len(assets_by_session), identifier)
                return assets_by_session
            
            # Try flow_id lookup
            assets_by_flow = self.db.query(Asset).filter(
                Asset.flow_id == identifier
            ).all()
            
            if assets_by_flow:
                logger.debug("Found %d assets by flow_id %s", len(assets_by_flow), identifier)
                return assets_by_flow
            
            # Try mapping session_id to flow_id
            flow_id = self.get_flow_id_from_session_id(identifier)
            if flow_id:
                assets_by_mapped_flow = self.db.query(Asset).filter(
                    Asset.flow_id == flow_id
                ).all()
                
                if assets_by_mapped_flow:
                    logger.debug("Found %d assets by mapped flow_id %s", len(assets_by_mapped_flow), flow_id)
                    return assets_by_mapped_flow
            
            # Try mapping flow_id to session_id
            session_id = self.get_session_id_from_flow_id(identifier)
            if session_id:
                assets_by_mapped_session = self.db.query(Asset).filter(
                    Asset.session_id == session_id
                ).all()
                
                if assets_by_mapped_session:
                    logger.debug("Found %d assets by mapped session_id %s", len(assets_by_mapped_session), session_id)
                    return assets_by_mapped_session
            
            logger.debug("No assets found for identifier %s", identifier)
            return []
            
        except Exception as e:
            logger.error("Error finding assets for identifier %s: %s", identifier, e)
            return []
    
    def migrate_asset_references(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Migrate asset references from session_id to flow_id.
        
        Args:
            batch_size: Number of assets to process in each batch
            
        Returns:
            Dictionary with migration statistics
        """
        if not MODELS_AVAILABLE:
            logger.warning("Models not available, returning empty stats")
            return {"total_processed": 0, "migrated": 0, "errors": 0}
        
        stats = {"total_processed": 0, "migrated": 0, "errors": 0, "skipped": 0}
        
        try:
            # Get assets that have session_id but no flow_id
            assets_to_migrate = self.db.query(Asset).filter(
                and_(Asset.session_id.isnot(None), Asset.flow_id.is_(None))
            ).limit(batch_size).all()
            
            for asset in assets_to_migrate:
                stats["total_processed"] += 1
                
                try:
                    flow_id = self.get_flow_id_from_session_id(str(asset.session_id))
                    
                    if flow_id:
                        asset.flow_id = flow_id
                        stats["migrated"] += 1
                        logger.debug("✅ Migrated asset %s from session %s to flow %s", 
                                   asset.id, asset.session_id, flow_id)
                    else:
                        stats["skipped"] += 1
                        logger.warning("⚠️ Could not find flow_id for asset %s with session_id %s", 
                                     asset.id, asset.session_id)
                
                except Exception as e:
                    stats["errors"] += 1
                    logger.error("❌ Error migrating asset %s: %s", asset.id, e)
            
            if stats["migrated"] > 0:
                self.db.commit()
                logger.info("✅ Committed migration of %d assets", stats["migrated"])
            
            return stats
            
        except Exception as e:
            logger.error("Error during asset migration: %s", e)
            self.db.rollback()
            stats["errors"] = stats["total_processed"]
            return stats
    
    def validate_migration_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the session-to-flow migration.
        
        Returns:
            Dictionary with validation results
        """
        if not MODELS_AVAILABLE:
            return {"status": "error", "message": "Models not available"}
        
        validation_results = {
            "status": "success",
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        try:
            # Check 1: Assets with session_id but no flow_id
            orphaned_assets = self.db.execute(text("""
                SELECT COUNT(*) as count
                FROM assets
                WHERE session_id IS NOT NULL AND flow_id IS NULL
            """)).fetchone().count
            
            validation_results["checks"]["orphaned_assets"] = orphaned_assets
            if orphaned_assets > 0:
                validation_results["warnings"].append(f"{orphaned_assets} assets have session_id but no flow_id")
            
            # Check 2: Sessions without corresponding flows
            orphaned_sessions = self.db.execute(text("""
                SELECT COUNT(*) as count
                FROM data_import_sessions dis
                LEFT JOIN discovery_flows df ON df.import_session_id = dis.id
                WHERE df.id IS NULL
            """)).fetchone().count
            
            validation_results["checks"]["orphaned_sessions"] = orphaned_sessions
            if orphaned_sessions > 0:
                validation_results["warnings"].append(f"{orphaned_sessions} sessions have no corresponding flows")
            
            # Check 3: Flow consistency
            flow_inconsistencies = self.db.execute(text("""
                SELECT COUNT(*) as count
                FROM assets a
                JOIN discovery_flows df ON a.flow_id = df.flow_id
                WHERE a.session_id IS NOT NULL 
                  AND a.session_id != df.import_session_id
            """)).fetchone().count
            
            validation_results["checks"]["flow_inconsistencies"] = flow_inconsistencies
            if flow_inconsistencies > 0:
                validation_results["errors"].append(f"{flow_inconsistencies} assets have inconsistent session/flow mappings")
            
            # Check 4: Mapping completeness
            total_sessions = self.db.execute(text("SELECT COUNT(*) as count FROM data_import_sessions")).fetchone().count
            mapped_sessions = self.db.execute(text("""
                SELECT COUNT(DISTINCT import_session_id) as count 
                FROM discovery_flows 
                WHERE import_session_id IS NOT NULL
            """)).fetchone().count
            
            validation_results["checks"]["total_sessions"] = total_sessions
            validation_results["checks"]["mapped_sessions"] = mapped_sessions
            validation_results["checks"]["mapping_percentage"] = (mapped_sessions / max(total_sessions, 1)) * 100
            
            if validation_results["checks"]["mapping_percentage"] < 95:
                validation_results["warnings"].append(
                    f"Only {validation_results['checks']['mapping_percentage']:.1f}% of sessions are mapped to flows"
                )
            
            # Set overall status
            if validation_results["errors"]:
                validation_results["status"] = "error"
            elif validation_results["warnings"]:
                validation_results["status"] = "warning"
            
            return validation_results
            
        except Exception as e:
            logger.error("Error during migration validation: %s", e)
            return {
                "status": "error",
                "message": f"Validation failed: {str(e)}",
                "checks": {},
                "warnings": [],
                "errors": [str(e)]
            }
    
    def cleanup_compatibility_cache(self):
        """Clear the internal caches."""
        self._session_flow_cache.clear()
        self._flow_session_cache.clear()
        logger.debug("Cleared compatibility service caches")
    
    def log_deprecation_warning(self, method_name: str, session_id: str):
        """Log a deprecation warning for session_id usage."""
        logger.warning(
            "🚨 DEPRECATION WARNING: Method '%s' called with session_id '%s'. "
            "Please migrate to use flow_id instead. "
            "Session-based methods will be removed in a future version.",
            method_name, session_id
        )
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """Get comprehensive migration statistics."""
        if not MODELS_AVAILABLE:
            return {"error": "Models not available"}
        
        try:
            stats = {}
            
            # Asset migration stats
            stats["assets"] = {
                "total": self.db.execute(text("SELECT COUNT(*) as count FROM assets")).fetchone().count,
                "with_flow_id": self.db.execute(text("SELECT COUNT(*) as count FROM assets WHERE flow_id IS NOT NULL")).fetchone().count,
                "with_session_id": self.db.execute(text("SELECT COUNT(*) as count FROM assets WHERE session_id IS NOT NULL")).fetchone().count,
                "dual_reference": self.db.execute(text("SELECT COUNT(*) as count FROM assets WHERE flow_id IS NOT NULL AND session_id IS NOT NULL")).fetchone().count,
                "orphaned": self.db.execute(text("SELECT COUNT(*) as count FROM assets WHERE flow_id IS NULL AND session_id IS NOT NULL")).fetchone().count
            }
            
            # Flow stats
            stats["flows"] = {
                "total": self.db.execute(text("SELECT COUNT(*) as count FROM discovery_flows")).fetchone().count,
                "with_session_reference": self.db.execute(text("SELECT COUNT(*) as count FROM discovery_flows WHERE import_session_id IS NOT NULL")).fetchone().count,
                "auto_created": self.db.execute(text("SELECT COUNT(*) as count FROM discovery_flows WHERE status = 'migrated'")).fetchone().count
            }
            
            # Session stats
            stats["sessions"] = {
                "total": self.db.execute(text("SELECT COUNT(*) as count FROM data_import_sessions")).fetchone().count,
                "mapped_to_flows": self.db.execute(text("""
                    SELECT COUNT(DISTINCT dis.id) as count 
                    FROM data_import_sessions dis
                    JOIN discovery_flows df ON df.import_session_id = dis.id
                """)).fetchone().count
            }
            
            # Calculate percentages
            if stats["assets"]["total"] > 0:
                stats["assets"]["flow_migration_percentage"] = (stats["assets"]["with_flow_id"] / stats["assets"]["total"]) * 100
            
            if stats["sessions"]["total"] > 0:
                stats["sessions"]["mapping_percentage"] = (stats["sessions"]["mapped_to_flows"] / stats["sessions"]["total"]) * 100
            
            return stats
            
        except Exception as e:
            logger.error("Error getting migration stats: %s", e)
            return {"error": str(e)}


# Utility functions for backward compatibility
def get_compatibility_service(db: Session, client_account_id: Optional[str] = None) -> SessionFlowCompatibilityService:
    """Factory function to create compatibility service."""
    return SessionFlowCompatibilityService(db, client_account_id)


def map_session_to_flow(db: Session, session_id: str) -> Optional[str]:
    """Quick utility to map session_id to flow_id."""
    service = get_compatibility_service(db)
    return service.get_flow_id_from_session_id(session_id)


def map_flow_to_session(db: Session, flow_id: str) -> Optional[str]:
    """Quick utility to map flow_id to session_id."""
    service = get_compatibility_service(db)
    return service.get_session_id_from_flow_id(flow_id)