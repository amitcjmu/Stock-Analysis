"""
Data Import Service - Database-backed Asset Management
Handles CMDB data import with the new comprehensive Asset model.
Preserves existing classification and intelligence while using database persistence.
"""

import logging
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset, AssetType, AssetStatus, SixRStrategy
from app.repositories.asset_repository import AssetRepository, WorkflowProgressRepository
from app.services.asset_intelligence_service import AssetIntelligenceService

# Import existing processors for compatibility
try:
    from app.api.v1.discovery.processor import CMDBDataProcessor
    from app.api.v1.discovery.utils import AssetClassifier
    LEGACY_PROCESSORS_AVAILABLE = True
except ImportError:
    LEGACY_PROCESSORS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataImportService:
    """
    Comprehensive data import service for the new database-backed asset management.
    Integrates with existing classification and intelligence while using database persistence.
    """
    
    def __init__(self):
        self.asset_intelligence = AssetIntelligenceService()
        
        # Initialize legacy processors if available
        if LEGACY_PROCESSORS_AVAILABLE:
            self.cmdb_processor = CMDBDataProcessor()
            self.asset_classifier = AssetClassifier()
        else:
            self.cmdb_processor = None
            self.asset_classifier = None
            logger.warning("Legacy processors not available, using simplified processing")
    
    async def import_cmdb_data(
        self, 
        file_content: str, 
        file_type: str, 
        filename: str,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import CMDB data from file content into the database.
        
        Args:
            file_content: Raw file content
            file_type: MIME type of the file
            filename: Original filename
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping
            
        Returns:
            Import results with statistics and any errors
        """
        import_batch_id = f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Parse file content using existing processor if available
            if self.cmdb_processor:
                df, parse_result = self.cmdb_processor.parse_file_content(file_content, file_type, filename)
            else:
                df, parse_result = self._simple_parse_content(file_content, file_type)
            
            if df is None:
                # Handle unstructured content
                return await self._handle_unstructured_content(
                    parse_result, filename, import_batch_id, client_account_id, engagement_id
                )
            
            # Process structured data
            return await self._process_structured_data(
                df, filename, import_batch_id, client_account_id, engagement_id
            )
            
        except Exception as e:
            logger.error(f"Error importing CMDB data: {e}")
            return {
                "status": "error",
                "message": f"Failed to import data: {str(e)}",
                "import_batch_id": import_batch_id,
                "assets_imported": 0,
                "errors": [str(e)]
            }
    
    def _simple_parse_content(self, content: str, file_type: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Simple content parsing fallback when legacy processors aren't available."""
        try:
            if file_type in ['text/csv', 'application/csv']:
                import io
                df = pd.read_csv(io.StringIO(content))
                return df, {"type": "structured", "parsed_as": "csv"}
            elif file_type == 'application/json':
                data = json.loads(content)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame([data])
                return df, {"type": "structured", "parsed_as": "json"}
            else:
                return None, {
                    "type": "unstructured",
                    "content": content[:1000],
                    "message": "Unstructured content - manual processing required"
                }
        except Exception as e:
            raise ValueError(f"Failed to parse content: {str(e)}")
    
    async def _handle_unstructured_content(
        self, 
        parse_result: Dict[str, Any], 
        filename: str,
        import_batch_id: str,
        client_account_id: Optional[str],
        engagement_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle unstructured content that couldn't be parsed as tabular data."""
        
        # Create a placeholder asset for unstructured content
        async with AsyncSessionLocal() as db:
            asset_repo = AssetRepository(db, client_account_id, engagement_id)
            
            asset_data = {
                'name': f"Unstructured Content: {filename}",
                'asset_name': filename,
                'asset_type': AssetType.OTHER,
                'description': f"Unstructured content from {filename}",
                'status': AssetStatus.DISCOVERED,
                'source_system': 'cmdb_import',
                'source_file': filename,
                'import_batch_id': import_batch_id,
                'discovery_status': 'completed',
                'mapping_status': 'pending',
                'cleanup_status': 'pending',
                'assessment_readiness': 'not_ready',
                'custom_attributes': {
                    'original_content_type': parse_result.get('type'),
                    'ai_analysis': parse_result.get('ai_analysis'),
                    'requires_manual_processing': True
                }
            }
            
            asset = await asset_repo.create(**asset_data)
            
            return {
                "status": "partial_success",
                "message": f"Unstructured content imported as placeholder asset",
                "import_batch_id": import_batch_id,
                "assets_imported": 1,
                "unstructured_assets": 1,
                "requires_manual_processing": True,
                "asset_id": asset.id
            }
    
    async def _process_structured_data(
        self,
        df: pd.DataFrame,
        filename: str,
        import_batch_id: str,
        client_account_id: Optional[str],
        engagement_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process structured DataFrame into Asset records."""
        
        assets_imported = 0
        assets_updated = 0
        errors = []
        
        async with AsyncSessionLocal() as db:
            asset_repo = AssetRepository(db, client_account_id, engagement_id)
            
            for index, row in df.iterrows():
                try:
                    # Convert row to asset data
                    asset_data = await self._convert_row_to_asset(row, filename, import_batch_id)
                    
                    # Check if asset already exists
                    existing_asset = None
                    if asset_data.get('hostname'):
                        existing_assets = await asset_repo.get_by_filters(hostname=asset_data['hostname'])
                        if existing_assets:
                            existing_asset = existing_assets[0]
                    
                    if not existing_asset and asset_data.get('asset_name'):
                        existing_assets = await asset_repo.get_by_filters(asset_name=asset_data['asset_name'])
                        if existing_assets:
                            existing_asset = existing_assets[0]
                    
                    if existing_asset:
                        # Update existing asset
                        await asset_repo.update(existing_asset.id, **asset_data)
                        assets_updated += 1
                        logger.info(f"Updated existing asset: {existing_asset.name}")
                    else:
                        # Create new asset
                        new_asset = await asset_repo.create(**asset_data)
                        assets_imported += 1
                        logger.info(f"Created new asset: {new_asset.name}")
                        
                        # Initialize workflow progress
                        await self._initialize_workflow_progress(new_asset.id, db, client_account_id, engagement_id)
                
                except Exception as e:
                    error_msg = f"Error processing row {index}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # Run post-import analysis
        analysis_results = await self._run_post_import_analysis(import_batch_id, client_account_id, engagement_id)
        
        return {
            "status": "success" if not errors else "partial_success",
            "message": f"Imported {assets_imported} new assets, updated {assets_updated} existing assets",
            "import_batch_id": import_batch_id,
            "assets_imported": assets_imported,
            "assets_updated": assets_updated,
            "total_processed": assets_imported + assets_updated,
            "errors": errors,
            "error_count": len(errors),
            "analysis_results": analysis_results
        }
    
    async def _convert_row_to_asset(self, row: pd.Series, filename: str, import_batch_id: str) -> Dict[str, Any]:
        """Convert a DataFrame row to Asset model data."""
        
        # Map common field names
        field_mapping = {
            'hostname': ['hostname', 'host_name', 'server_name', 'name', 'asset_name'],
            'asset_name': ['asset_name', 'application_name', 'app_name', 'service_name'],
            'ip_address': ['ip_address', 'ip', 'ipaddress', 'ip_addr'],
            'operating_system': ['operating_system', 'os', 'platform', 'os_type'],
            'environment': ['environment', 'env', 'stage', 'tier'],
            'business_criticality': ['business_criticality', 'criticality', 'priority', 'importance'],
            'department': ['department', 'dept', 'business_unit', 'team'],
            'business_owner': ['business_owner', 'owner', 'responsible_person'],
            'technical_owner': ['technical_owner', 'tech_owner', 'admin', 'administrator']
        }
        
        # Extract mapped fields
        mapped_data = {}
        for target_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                if source_field in row.index and pd.notna(row[source_field]):
                    mapped_data[target_field] = str(row[source_field]).strip()
                    break
        
        # Determine asset type using existing classifier if available
        asset_type = AssetType.OTHER
        intelligent_asset_type = None
        
        if self.asset_classifier:
            try:
                # Use existing classification logic
                classification_result = self.asset_classifier.classify_asset(row.to_dict())
                asset_type = self._map_classification_to_enum(classification_result.get('asset_type'))
                intelligent_asset_type = classification_result.get('intelligent_asset_type')
            except Exception as e:
                logger.warning(f"Asset classification failed: {e}")
        
        # Calculate data quality scores
        quality_metrics = self._calculate_data_quality(row)
        
        # Determine workflow status based on data completeness
        workflow_status = self._determine_workflow_status(mapped_data)
        
        # Build asset data
        asset_data = {
            # Core identification
            'name': mapped_data.get('asset_name') or mapped_data.get('hostname', f'Asset_{import_batch_id}_{row.name}'),
            'asset_name': mapped_data.get('asset_name'),
            'hostname': mapped_data.get('hostname'),
            'asset_type': asset_type,
            'intelligent_asset_type': intelligent_asset_type,
            'description': f"Imported from {filename}",
            
            # Infrastructure details
            'ip_address': mapped_data.get('ip_address'),
            'operating_system': mapped_data.get('operating_system'),
            'environment': mapped_data.get('environment'),
            
            # Business information
            'business_owner': mapped_data.get('business_owner'),
            'technical_owner': mapped_data.get('technical_owner'),
            'department': mapped_data.get('department'),
            'business_criticality': mapped_data.get('business_criticality'),
            
            # Migration details
            'status': AssetStatus.DISCOVERED,
            
            # Source information
            'source_system': 'cmdb_import',
            'source_file': filename,
            'import_batch_id': import_batch_id,
            
            # Workflow status
            **workflow_status,
            
            # Quality metrics
            **quality_metrics,
            
            # Custom attributes (preserve any unmapped fields)
            'custom_attributes': {k: str(v) for k, v in row.to_dict().items() 
                                if k not in field_mapping and pd.notna(v)}
        }
        
        # Remove None values
        return {k: v for k, v in asset_data.items() if v is not None}
    
    def _map_classification_to_enum(self, classification: str) -> AssetType:
        """Map classification result to AssetType enum."""
        if not classification:
            return AssetType.OTHER
        
        classification_lower = classification.lower()
        
        mapping = {
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
        
        return mapping.get(classification_lower, AssetType.OTHER)
    
    def _calculate_data_quality(self, row: pd.Series) -> Dict[str, Any]:
        """Calculate data quality metrics for a row."""
        # Critical fields for migration assessment
        critical_fields = ['hostname', 'asset_name', 'operating_system', 'environment', 'business_criticality']
        
        # Count filled critical fields
        filled_critical = sum(1 for field in critical_fields if field in row.index and pd.notna(row[field]))
        completeness_score = (filled_critical / len(critical_fields)) * 100 if critical_fields else 0
        
        # Quality score based on data richness
        total_fields = len(row.index)
        filled_fields = sum(1 for value in row.values if pd.notna(value))
        quality_score = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Missing critical fields
        missing_fields = [field for field in critical_fields 
                         if field not in row.index or pd.isna(row.get(field))]
        
        return {
            'completeness_score': completeness_score,
            'quality_score': quality_score,
            'missing_critical_fields': missing_fields if missing_fields else None
        }
    
    def _determine_workflow_status(self, mapped_data: Dict[str, Any]) -> Dict[str, str]:
        """Determine initial workflow status based on data completeness."""
        has_basic_info = bool(mapped_data.get('hostname') or mapped_data.get('asset_name'))
        has_detailed_info = bool(mapped_data.get('operating_system') or mapped_data.get('environment'))
        
        # Initialize workflow statuses
        discovery_status = 'completed' if has_basic_info else 'discovered'
        mapping_status = 'completed' if has_detailed_info else 'pending'
        cleanup_status = 'pending'  # Always starts as pending for new imports
        
        # Assessment readiness based on completeness
        if has_detailed_info and has_basic_info:
            assessment_readiness = 'partial'
        elif has_basic_info:
            assessment_readiness = 'not_ready'
        else:
            assessment_readiness = 'not_ready'
        
        return {
            'discovery_status': discovery_status,
            'mapping_status': mapping_status,
            'cleanup_status': cleanup_status,
            'assessment_readiness': assessment_readiness
        }
    
    async def _initialize_workflow_progress(
        self, 
        asset_id: int, 
        db: AsyncSession,
        client_account_id: Optional[str],
        engagement_id: Optional[str]
    ) -> None:
        """Initialize workflow progress tracking for a new asset."""
        workflow_repo = WorkflowProgressRepository(db, client_account_id, engagement_id)
        
        # Initialize discovery phase as completed
        await workflow_repo.create(
            asset_id=asset_id,
            phase='discovery',
            status='completed',
            progress_percentage=100.0,
            notes='Asset discovered during CMDB import'
        )
    
    async def _run_post_import_analysis(
        self,
        import_batch_id: str,
        client_account_id: Optional[str],
        engagement_id: Optional[str]
    ) -> Dict[str, Any]:
        """Run post-import analysis using asset intelligence service."""
        try:
            async with AsyncSessionLocal() as db:
                asset_repo = AssetRepository(db, client_account_id, engagement_id)
                
                # Get assets from this import batch
                imported_assets = await asset_repo.get_by_filters(import_batch_id=import_batch_id)
                
                if not imported_assets:
                    return {"message": "No assets found for analysis"}
                
                # Run comprehensive analysis
                analysis_result = await self.asset_intelligence.analyze_assets_comprehensive(
                    [asset.__dict__ for asset in imported_assets]
                )
                
                # Update assets with analysis results
                for asset in imported_assets:
                    if analysis_result.get('asset_analysis'):
                        asset_analysis = analysis_result['asset_analysis'].get(str(asset.id))
                        if asset_analysis:
                            await asset_repo.update(asset.id, 
                                ai_analysis_result=asset_analysis,
                                ai_confidence_score=asset_analysis.get('confidence_score'),
                                last_ai_analysis=datetime.now()
                            )
                
                return {
                    "assets_analyzed": len(imported_assets),
                    "analysis_summary": analysis_result.get('summary', {}),
                    "recommendations": analysis_result.get('recommendations', [])
                }
                
        except Exception as e:
            logger.error(f"Post-import analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def get_import_status(self, import_batch_id: str, client_account_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of a specific import batch."""
        async with AsyncSessionLocal() as db:
            asset_repo = AssetRepository(db, client_account_id)
            
            assets = await asset_repo.get_by_filters(import_batch_id=import_batch_id)
            
            if not assets:
                return {"status": "not_found", "message": "Import batch not found"}
            
            # Calculate statistics
            total_assets = len(assets)
            workflow_summary = await asset_repo.get_workflow_summary()
            quality_summary = await asset_repo.get_data_quality_summary()
            
            return {
                "status": "found",
                "import_batch_id": import_batch_id,
                "total_assets": total_assets,
                "workflow_summary": workflow_summary,
                "quality_summary": quality_summary,
                "assets": [{"id": asset.id, "name": asset.name, "type": asset.asset_type} for asset in assets[:10]]
            } 