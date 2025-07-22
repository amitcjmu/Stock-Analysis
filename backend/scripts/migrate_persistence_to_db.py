#!/usr/bin/env python3
"""
Data migration script to migrate existing persistence layer data to database.
Migrates assets from file-based storage to the new comprehensive Asset model.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from app.core.database import AsyncSessionLocal

# Import models directly to avoid relationship issues
try:
    from app.models.asset import Asset, AssetStatus, AssetType
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import models: {e}")
    MODELS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersistenceToDbMigrator:
    """Migrates data from persistence layer to database."""
    
    def __init__(self):
        self.data_dir = Path("data/persistence")
        self.migrated_count = 0
        self.error_count = 0
        self.errors = []
    
    def load_persistence_data(self) -> List[Dict[str, Any]]:
        """Load assets from persistence layer files."""
        assets = []
        
        # Load from processed_assets_backup.json
        backup_file = self.data_dir / "processed_assets_backup.json"
        if backup_file.exists():
            try:
                with open(backup_file, 'r') as f:
                    backup_assets = json.load(f)
                    assets.extend(backup_assets)
                    logger.info(f"Loaded {len(backup_assets)} assets from backup file")
            except Exception as e:
                logger.error(f"Error loading backup file: {e}")
        
        # Load from any other asset files in the directory
        for file_path in self.data_dir.glob("*.json"):
            if file_path.name != "processed_assets_backup.json":
                try:
                    with open(file_path, 'r') as f:
                        file_data = json.load(f)
                        if isinstance(file_data, list):
                            assets.extend(file_data)
                        elif isinstance(file_data, dict):
                            assets.append(file_data)
                        logger.info(f"Loaded data from {file_path.name}")
                except Exception as e:
                    logger.warning(f"Error loading {file_path.name}: {e}")
        
        # Remove duplicates based on hostname or name
        unique_assets = []
        seen_identifiers = set()
        
        for asset in assets:
            # Create identifier based on hostname or name
            hostname = asset.get('hostname', '').strip().lower()
            name = asset.get('asset_name', asset.get('name', '')).strip().lower()
            
            identifier = hostname if hostname else name
            if identifier and identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_assets.append(asset)
        
        logger.info(f"Found {len(unique_assets)} unique assets after deduplication")
        return unique_assets
    
    def map_asset_type(self, asset_data: Dict[str, Any]) -> AssetType:
        """Map persistence asset type to database enum."""
        asset_type = asset_data.get('asset_type', '').lower()
        intelligent_type = asset_data.get('intelligent_asset_type', '').lower()
        
        # Map based on intelligent type first, then fallback to asset_type
        type_mapping = {
            'application': AssetType.APPLICATION,
            'server': AssetType.SERVER,
            'database': AssetType.DATABASE,
            'network': AssetType.NETWORK,
            'storage': AssetType.STORAGE,
            'container': AssetType.CONTAINER,
            'virtual_machine': AssetType.VIRTUAL_MACHINE,
            'vm': AssetType.VIRTUAL_MACHINE,
            'load_balancer': AssetType.LOAD_BALANCER,
            'security_group': AssetType.SECURITY_GROUP,
        }
        
        # Try intelligent type first
        if intelligent_type in type_mapping:
            return type_mapping[intelligent_type]
        
        # Try asset type
        if asset_type in type_mapping:
            return type_mapping[asset_type]
        
        # Default to OTHER
        return AssetType.OTHER
    
    def map_workflow_status(self, asset_data: Dict[str, Any]) -> Dict[str, str]:
        """Determine initial workflow status based on existing data."""
        # Check data completeness to determine workflow phase
        has_basic_info = bool(asset_data.get('hostname') or asset_data.get('asset_name'))
        has_detailed_info = bool(asset_data.get('operating_system') or asset_data.get('environment'))
        has_6r_analysis = bool(asset_data.get('sixr_ready') or asset_data.get('recommended_6r_strategy'))
        
        # Initialize workflow statuses
        discovery_status = 'completed' if has_basic_info else 'discovered'
        mapping_status = 'completed' if has_detailed_info else 'pending'
        cleanup_status = 'completed' if has_detailed_info else 'pending'
        
        # Assessment readiness based on completeness
        if has_6r_analysis and has_detailed_info:
            assessment_readiness = 'ready'
        elif has_detailed_info:
            assessment_readiness = 'partial'
        else:
            assessment_readiness = 'not_ready'
        
        return {
            'discovery_status': discovery_status,
            'mapping_status': mapping_status,
            'cleanup_status': cleanup_status,
            'assessment_readiness': assessment_readiness
        }
    
    def calculate_data_quality_scores(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate data quality and completeness scores."""
        # Critical fields for migration assessment
        critical_fields = [
            'hostname', 'asset_name', 'asset_type', 'environment', 
            'operating_system', 'business_criticality'
        ]
        
        # Count filled critical fields
        filled_critical = sum(1 for field in critical_fields if asset_data.get(field))
        completeness_score = (filled_critical / len(critical_fields)) * 100
        
        # Quality score based on data richness
        quality_indicators = [
            bool(asset_data.get('description')),
            bool(asset_data.get('ip_address')),
            bool(asset_data.get('department')),
            bool(asset_data.get('business_owner')),
            bool(asset_data.get('dependencies')),
        ]
        
        quality_score = (sum(quality_indicators) / len(quality_indicators)) * 100
        
        # Missing critical fields
        missing_fields = [field for field in critical_fields if not asset_data.get(field)]
        
        return {
            'completeness_score': completeness_score,
            'quality_score': quality_score,
            'missing_critical_fields': missing_fields if missing_fields else None
        }
    
    def convert_asset_data(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert persistence asset data to database asset format."""
        # Map workflow status
        workflow_status = self.map_workflow_status(asset_data)
        
        # Calculate quality scores
        quality_metrics = self.calculate_data_quality_scores(asset_data)
        
        # Convert to database format
        db_asset = {
            # Core identification
            'name': asset_data.get('asset_name') or asset_data.get('name') or asset_data.get('hostname', 'Unknown'),
            'asset_name': asset_data.get('asset_name'),
            'hostname': asset_data.get('hostname'),
            'asset_type': self.map_asset_type(asset_data),
            'intelligent_asset_type': asset_data.get('intelligent_asset_type'),
            'description': asset_data.get('description'),
            
            # Infrastructure details
            'ip_address': asset_data.get('ip_address'),
            'operating_system': asset_data.get('operating_system'),
            'os_version': asset_data.get('os_version'),
            'environment': asset_data.get('environment'),
            
            # Business information
            'business_owner': asset_data.get('business_owner'),
            'technical_owner': asset_data.get('technical_owner'),
            'department': asset_data.get('department'),
            'business_criticality': asset_data.get('business_criticality'),
            
            # Migration details
            'status': AssetStatus.DISCOVERED,
            'sixr_ready': asset_data.get('sixr_ready'),
            'migration_complexity': asset_data.get('migration_complexity'),
            'migration_priority': asset_data.get('migration_priority'),
            'recommended_6r_strategy': asset_data.get('recommended_6r_strategy'),
            
            # Dependencies
            'dependencies': asset_data.get('dependencies'),
            'dependents': asset_data.get('dependents'),
            'server_dependencies': asset_data.get('server_dependencies'),
            'application_dependencies': asset_data.get('application_dependencies'),
            'database_dependencies': asset_data.get('database_dependencies'),
            
            # Source information
            'source_system': 'persistence_migration',
            'source_file': asset_data.get('source_file'),
            'import_batch_id': f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            
            # Workflow status
            **workflow_status,
            
            # Quality metrics
            **quality_metrics,
            
            # AI analysis (preserve existing)
            'ai_analysis_result': asset_data.get('ai_analysis_result'),
            'ai_confidence_score': asset_data.get('ai_confidence_score'),
            'ai_recommendations': asset_data.get('ai_recommendations'),
            'confidence_score': asset_data.get('confidence_score'),
            
            # Custom attributes (preserve any extra fields)
            'custom_attributes': {k: v for k, v in asset_data.items() 
                                if k not in ['asset_name', 'hostname', 'asset_type', 'description',
                                           'ip_address', 'operating_system', 'environment', 'business_criticality']}
        }
        
        # Remove None values
        return {k: v for k, v in db_asset.items() if v is not None}
    
    async def migrate_assets(self, assets_data: List[Dict[str, Any]]) -> None:
        """Migrate assets to database."""
        if not MODELS_AVAILABLE:
            logger.error("Models not available, cannot migrate assets")
            return
            
        async with AsyncSessionLocal() as db:
            for i, asset_data in enumerate(assets_data):
                try:
                    # Convert asset data
                    db_asset_data = self.convert_asset_data(asset_data)
                    
                    # Create asset instance directly
                    asset = Asset(**db_asset_data)
                    
                    # Add to session
                    db.add(asset)
                    await db.commit()
                    await db.refresh(asset)
                    
                    logger.info(f"Created asset: {asset.name}")
                    self.migrated_count += 1
                    
                    # Progress logging
                    if (i + 1) % 10 == 0:
                        logger.info(f"Migrated {i + 1}/{len(assets_data)} assets...")
                
                except Exception as e:
                    self.error_count += 1
                    error_msg = f"Error migrating asset {asset_data.get('hostname', 'unknown')}: {e}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    await db.rollback()
    
    async def run_migration(self) -> None:
        """Run the complete migration process."""
        logger.info("Starting persistence to database migration...")
        
        # Check if persistence data exists
        if not self.data_dir.exists():
            logger.warning(f"Persistence directory {self.data_dir} does not exist")
            return
        
        # Load persistence data
        assets_data = self.load_persistence_data()
        if not assets_data:
            logger.warning("No assets found in persistence layer")
            return
        
        # Migrate assets
        await self.migrate_assets(assets_data)
        
        # Report results
        logger.info("Migration completed:")
        logger.info(f"  Successfully migrated: {self.migrated_count} assets")
        logger.info(f"  Errors: {self.error_count}")
        
        if self.errors:
            logger.error("Migration errors:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.error(f"  {error}")
            if len(self.errors) > 10:
                logger.error(f"  ... and {len(self.errors) - 10} more errors")


async def main():
    """Main migration function."""
    migrator = PersistenceToDbMigrator()
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main()) 