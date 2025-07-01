"""
Flow Service

Core business logic for flow operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import uuid as uuid_pkg

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.asset import Asset
from app.models.data_import import RawImportRecord
from app.models.field_mapping import FieldMapping

logger = logging.getLogger(__name__)


class FlowService:
    """Core service for flow business logic"""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session"""
        self.db = db
    
    async def create_discovery_assets_from_cleaned_data(
        self, 
        flow, 
        cleaned_data: List[Dict[str, Any]], 
        field_mappings: List[Any]
    ) -> int:
        """Create discovery assets from cleaned data during data cleansing phase"""
        try:
            if not cleaned_data:
                logger.warning("⚠️ No cleaned data available for discovery asset creation")
                return 0
                
            logger.info(f"📊 Creating discovery assets from {len(cleaned_data)} cleaned records")
            
            # Create mapping dictionary from field mappings
            mapping_dict = {}
            for mapping in field_mappings:
                if hasattr(mapping, 'source_field') and hasattr(mapping, 'target_field'):
                    mapping_dict[mapping.source_field] = mapping.target_field
                    
            assets_created = 0
            
            # Process each cleaned record into a discovery asset
            for index, record in enumerate(cleaned_data):
                try:
                    # Apply field mappings to get standardized data
                    mapped_data = self._apply_field_mappings_to_record(record, mapping_dict)
                    
                    # Create asset with discovery metadata in custom_attributes
                    asset = Asset(
                        # Multi-tenant isolation
                        client_account_id=flow.client_account_id,
                        engagement_id=flow.engagement_id,
                        
                        # Asset identification
                        name=mapped_data.get('asset_name') or mapped_data.get('Asset_Name') or 
                             mapped_data.get('hostname') or f"Asset_{index + 1}",
                        type=self._determine_asset_type_from_data(mapped_data, record),
                        status='discovered',
                        
                        # Store discovery metadata in custom_attributes
                        custom_attributes={
                            'discovery_flow_id': str(flow.id),
                            'discovered_in_phase': 'data_cleansing',
                            'discovery_method': 'postgresql_flow_manager',
                            'confidence_score': 0.85,
                            'raw_data': record,
                            'normalized_data': mapped_data,
                            'migration_ready': False,
                            'migration_complexity': 'Medium',
                            'migration_priority': 3,
                            'validation_status': 'pending'
                        },
                        
                        # Timestamps
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    self.db.add(asset)
                    assets_created += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create discovery asset {index}: {e}")
                    continue
                    
            # Commit all discovery assets
            await self.db.commit()
            
            logger.info(f"✅ Created {assets_created} assets during data cleansing")
            return assets_created
            
        except Exception as e:
            logger.error(f"❌ Failed to create discovery assets: {e}")
            await self.db.rollback()
            return 0
    
    async def classify_assets(self, assets: List[Asset]) -> Dict[str, Any]:
        """Classify and enhance assets during inventory phase"""
        try:
            classification_results = {
                "assets_processed": len(assets),
                "asset_type_distribution": {},
                "classification_updates": [],
                "enhancement_summary": {}
            }
            
            for asset in assets:
                # Enhance asset type classification if needed
                current_type = asset.type or "UNKNOWN"
                
                # Improve classification based on custom attributes
                custom_attrs = asset.custom_attributes or {}
                if 'raw_data' in custom_attrs or 'normalized_data' in custom_attrs:
                    data = custom_attrs.get('normalized_data', custom_attrs.get('raw_data', {}))
                    enhanced_type = self._enhance_asset_classification(data, current_type)
                    if enhanced_type != current_type:
                        asset.type = enhanced_type
                        classification_results["classification_updates"].append({
                            "asset_id": str(asset.id),
                            "old_type": current_type,
                            "new_type": enhanced_type
                        })
                
                # Update distribution count
                final_type = asset.type or "UNKNOWN"
                classification_results["asset_type_distribution"][final_type] = \
                    classification_results["asset_type_distribution"].get(final_type, 0) + 1
            
            # Commit classification updates
            await self.db.commit()
            
            logger.info(f"✅ Classified {len(assets)} assets: {classification_results['asset_type_distribution']}")
            return classification_results
            
        except Exception as e:
            logger.error(f"❌ Asset classification failed: {e}")
            return {"error": str(e), "assets_processed": 0}
    
    async def check_processed_records(self, flow) -> bool:
        """Check if there are processed records for the flow"""
        if not flow.import_session_id:
            return False
            
        try:
            # Check if there are processed raw records
            records_query = await self.db.execute(
                select(func.count(RawImportRecord.id)).where(
                    RawImportRecord.session_id == flow.import_session_id
                )
            )
            record_count = records_query.scalar() or 0
            
            return record_count > 0
            
        except Exception as e:
            logger.error(f"Error checking processed records: {e}")
            return False
    
    async def check_field_mappings(self, flow_id: str) -> bool:
        """Check if field mappings exist and are approved"""
        try:
            stmt = select(func.count(FieldMapping.id)).where(
                FieldMapping.flow_id == flow_id,
                FieldMapping.is_approved == True
            )
            result = await self.db.execute(stmt)
            count = result.scalar() or 0
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking field mappings: {e}")
            return False
    
    async def perform_data_cleansing(
        self, 
        raw_data: List[Dict[str, Any]], 
        field_mappings: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Perform data cleansing operations on raw data.
        
        Returns:
            Tuple of (cleaned_data, quality_metrics)
        """
        cleaned_records = []
        quality_metrics = {
            "total_records": len(raw_data),
            "cleaned_records": 0,
            "invalid_records": 0,
            "duplicate_records": 0,
            "missing_fields": 0,
            "data_types_corrected": 0,
            "cleansing_rules_applied": 0
        }
        
        seen_records = set()
        
        for index, record in enumerate(raw_data):
            try:
                # Skip empty records
                if not record:
                    quality_metrics["invalid_records"] += 1
                    continue
                
                # Check for duplicates
                record_hash = hash(frozenset(record.items()))
                if record_hash in seen_records:
                    quality_metrics["duplicate_records"] += 1
                    continue
                seen_records.add(record_hash)
                
                # Apply field mappings and cleansing
                cleaned_record = {}
                has_required_fields = True
                
                for field, value in record.items():
                    # Clean the value
                    cleaned_value = self._clean_field_value(value, field)
                    
                    # Track missing required fields
                    if cleaned_value is None or cleaned_value == "":
                        if field in field_mappings.get("required_fields", []):
                            has_required_fields = False
                            quality_metrics["missing_fields"] += 1
                    
                    # Apply mapping if exists
                    mapped_field = field_mappings.get("mappings", {}).get(field, field)
                    cleaned_record[mapped_field] = cleaned_value
                
                # Only add records with required fields
                if has_required_fields:
                    cleaned_records.append(cleaned_record)
                    quality_metrics["cleaned_records"] += 1
                else:
                    quality_metrics["invalid_records"] += 1
                    
            except Exception as e:
                logger.error(f"Error cleaning record {index}: {e}")
                quality_metrics["invalid_records"] += 1
                continue
        
        # Calculate quality score
        if quality_metrics["total_records"] > 0:
            quality_metrics["quality_score"] = (
                quality_metrics["cleaned_records"] / quality_metrics["total_records"]
            ) * 100
        else:
            quality_metrics["quality_score"] = 0
        
        logger.info(f"✅ Data cleansing complete: {quality_metrics['cleaned_records']} cleaned, "
                   f"{quality_metrics['invalid_records']} invalid, "
                   f"{quality_metrics['duplicate_records']} duplicates")
        
        return cleaned_records, quality_metrics
    
    def _apply_field_mappings_to_record(self, record: dict, mapping_dict: dict) -> dict:
        """Apply field mappings to transform record data"""
        mapped_data = {}
        
        for source_field, value in record.items():
            # Get target field from mapping, or use original field name
            target_field = mapping_dict.get(source_field, source_field)
            mapped_data[target_field] = value
            
        return mapped_data
    
    def _determine_asset_type_from_data(self, mapped_data: dict, original_data: dict) -> str:
        """Determine asset type from available data"""
        # Check mapped data first
        asset_type = (mapped_data.get("asset_type") or 
                     original_data.get("asset_type") or 
                     original_data.get("TYPE"))
        
        if asset_type:
            asset_type_str = str(asset_type).upper()
            # Map common types
            if "SERVER" in asset_type_str or "SRV" in asset_type_str:
                return "SERVER"
            elif "DATABASE" in asset_type_str or "DB" in asset_type_str:
                return "DATABASE"
            elif "NETWORK" in asset_type_str or "NET" in asset_type_str:
                return "NETWORK"
            elif "STORAGE" in asset_type_str:
                return "STORAGE"
            elif "APPLICATION" in asset_type_str or "APP" in asset_type_str:
                return "APPLICATION"
            elif "VIRTUAL" in asset_type_str or "VM" in asset_type_str:
                return "VIRTUAL_MACHINE"
                
        # Default fallback
        return "SERVER"
    
    def _enhance_asset_classification(self, data: dict, current_type: str) -> str:
        """Enhance asset type classification based on normalized data"""
        # Look for more specific indicators in the data
        os_info = str(data.get("operating_system", "")).lower()
        hostname = str(data.get("hostname", "")).lower()
        app_name = str(data.get("application_name", "")).lower()
        asset_name = str(data.get("asset_name", "")).lower()
        
        # Database indicators
        db_indicators = ["sql", "oracle", "postgres", "mysql", "mongodb", "db", "database"]
        if any(ind in os_info or ind in hostname or ind in app_name 
               for ind in db_indicators):
            return "DATABASE"
        
        # Application indicators
        app_indicators = ["web", "app", "api", "service", "portal", "tomcat", "iis", "nginx"]
        if any(ind in hostname or ind in app_name or ind in asset_name
               for ind in app_indicators):
            return "APPLICATION"
        
        # Virtual machine indicators
        vm_indicators = ["vm", "virtual", "esx", "vmware", "hyper-v", "kvm", "xen"]
        if any(ind in os_info or ind in hostname or ind in asset_name
               for ind in vm_indicators):
            return "VIRTUAL_MACHINE"
        
        # Network device indicators
        net_indicators = ["switch", "router", "firewall", "lb", "balancer", "gateway", "vpn"]
        if any(ind in hostname or ind in asset_name
               for ind in net_indicators):
            return "NETWORK"
        
        # Storage indicators
        storage_indicators = ["storage", "nas", "san", "backup", "archive"]
        if any(ind in hostname or ind in asset_name
               for ind in storage_indicators):
            return "STORAGE"
        
        # Keep current type if no better classification found
        return current_type
    
    def _clean_field_value(self, value: Any, field_name: str) -> Any:
        """Clean and standardize field values"""
        if value is None:
            return None
            
        # Convert to string for cleaning
        str_value = str(value).strip()
        
        # Remove common null indicators
        if str_value.lower() in ["null", "none", "n/a", "na", "-", ""]:
            return None
        
        # Clean whitespace
        str_value = " ".join(str_value.split())
        
        # Type-specific cleaning
        if "date" in field_name.lower():
            # TODO: Implement date parsing/standardization
            return str_value
        elif "number" in field_name.lower() or "count" in field_name.lower():
            # Try to extract numeric value
            try:
                return float(str_value.replace(",", ""))
            except:
                return str_value
        
        return str_value