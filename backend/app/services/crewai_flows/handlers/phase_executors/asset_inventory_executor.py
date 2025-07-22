"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class AssetInventoryExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "inventory"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 50.0  # 3/6 phases
    
    def _get_phase_timeout(self) -> int:
        """Asset inventory processing has no timeout restrictions for agentic activities"""
        return None  # No timeout for asset classification processing
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for inventory crew
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        logger.info(f"🚀 Starting asset inventory crew execution with {len(cleaned_data)} records")
        
        crew = self.crew_manager.create_crew_on_demand(
            "inventory", 
            cleaned_data=cleaned_data,
            field_mappings=field_mappings,
            **self._get_crew_context()
        )
        # Run crew in thread to avoid blocking async execution
        import asyncio
        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)
        
        # Process crew results
        results = self._process_crew_result(crew_result)
        
        # Persist assets to database after crew processing
        await self._persist_assets_to_database(results)
        
        return results
    
    async def execute_fallback(self) -> Dict[str, Any]:
        # NO FALLBACK LOGIC - FAIL FAST TO IDENTIFY REAL ISSUES
        logger.error("❌ FALLBACK EXECUTION DISABLED - Asset inventory crew must work properly")
        logger.error("❌ If you see this error, fix the actual crew execution issues")
        raise RuntimeError("Asset inventory fallback disabled - crew execution failed")
    
    def _get_crew_context(self) -> Dict[str, Any]:
        """Override to provide context for deduplication tools"""
        context = super()._get_crew_context()
        
        # Add context info needed for deduplication tools
        context_info = {
            'client_account_id': getattr(self.state, 'client_account_id', None),
            'engagement_id': getattr(self.state, 'engagement_id', None),
            'user_id': getattr(self.state, 'user_id', None),
            'flow_id': getattr(self.state, 'flow_id', None)
        }
        
        # If state attributes are not available, try to get from flow_bridge
        if not context_info['client_account_id'] and self.flow_bridge and hasattr(self.flow_bridge, 'context'):
            bridge_context = self.flow_bridge.context
            context_info['client_account_id'] = bridge_context.client_account_id
            context_info['engagement_id'] = bridge_context.engagement_id
            context_info['user_id'] = bridge_context.user_id
            context_info['flow_id'] = bridge_context.flow_id
        
        context['context_info'] = context_info
        logger.info(f"🔧 Providing context for deduplication tools: client={context_info['client_account_id']}, engagement={context_info['engagement_id']}")
        
        return context
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        cleaned_data = getattr(self.state, 'cleaned_data', [])
        raw_data = getattr(self.state, 'raw_data', [])
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        logger.info(f"🔍 Asset inventory crew input: {len(cleaned_data)} cleaned_data, {len(raw_data)} raw_data")
        logger.info(f"🔍 Field mappings available: {list(field_mappings.keys()) if field_mappings else 'None'}")
        
        # If cleaned_data is empty but raw_data exists, use raw_data with field mappings
        if not cleaned_data and raw_data:
            logger.info("🔧 Using raw_data since cleaned_data is empty - applying field mappings")
            
            # Apply field mappings to raw data to create cleaned data
            processed_data = []
            for item in raw_data:
                cleaned_item = {}
                # Apply field mappings
                for source_field, target_field in field_mappings.items():
                    if source_field in item:
                        cleaned_item[target_field] = item[source_field]
                
                # Also keep original data for reference
                cleaned_item['_original'] = item
                processed_data.append(cleaned_item)
            
            logger.info(f"✅ Processed {len(processed_data)} items with field mappings")
            return {"cleaned_data": processed_data}
        
        return {"cleaned_data": cleaned_data}
    
    def _store_results(self, results: Dict[str, Any]):
        """Store results in state - persistence is handled in execute_with_crew"""
        self.state.asset_inventory = results
        
    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process asset inventory crew result and extract asset data - NO FALLBACKS"""
        logger.info(f"🔍 Processing asset inventory crew result: {type(crew_result)}")
        
        if hasattr(crew_result, 'raw') and crew_result.raw:
            logger.info(f"📄 Asset inventory crew raw output: {crew_result.raw}")
            
            # Try to parse JSON from crew output
            import json
            try:
                if '{' in crew_result.raw and '}' in crew_result.raw:
                    start = crew_result.raw.find('{')
                    end = crew_result.raw.rfind('}') + 1
                    json_str = crew_result.raw[start:end]
                    parsed_result = json.loads(json_str)
                    
                    if any(key in parsed_result for key in ['servers', 'applications', 'devices', 'assets']):
                        logger.info("✅ Found structured asset data in crew output")
                        return parsed_result
                    else:
                        logger.error(f"❌ Crew returned JSON but missing required keys. Got: {list(parsed_result.keys())}")
                        raise ValueError("Asset inventory crew returned JSON without required asset categories")
                else:
                    logger.error(f"❌ Crew output does not contain valid JSON structure: {crew_result.raw}")
                    raise ValueError("Asset inventory crew did not return JSON output")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Failed to parse JSON from crew output: {e}")
                logger.error(f"❌ Raw crew output: {crew_result.raw}")
                raise RuntimeError(f"Asset inventory crew output parsing failed: {e}")
        
        elif isinstance(crew_result, dict):
            # Validate that required keys exist
            if any(key in crew_result for key in ['servers', 'applications', 'devices', 'assets']):
                logger.info("✅ Crew returned valid dict with asset data")
                return crew_result
            else:
                logger.error(f"❌ Crew returned dict but missing required asset keys. Got: {list(crew_result.keys())}")
                raise ValueError("Asset inventory crew returned dict without required asset categories")
        
        else:
            logger.error(f"❌ Unexpected crew result format: {type(crew_result)}")
            logger.error(f"❌ Crew result: {crew_result}")
            raise RuntimeError(f"Asset inventory crew returned unexpected result type: {type(crew_result)}")
    
    def _execute_fallback_sync(self) -> Dict[str, Any]:
        """NO SYNC FALLBACK - This method should never be called"""
        logger.error("❌ _execute_fallback_sync called - this method is disabled")
        raise RuntimeError("Sync fallback disabled - crew execution must work properly")
    
    async def _persist_assets_to_database(self, results: Dict[str, Any]):
        """Persist discovered assets to the database with deduplication"""
        try:
            logger.info("📦 Starting asset persistence to database")
            
            # Extract assets from results
            all_assets = []
            
            # Gather assets from different categories
            servers = results.get('servers', [])
            applications = results.get('applications', [])
            devices = results.get('devices', [])
            generic_assets = results.get('assets', [])
            
            # Combine all assets
            all_assets.extend(servers)
            all_assets.extend(applications)
            all_assets.extend(devices)
            all_assets.extend(generic_assets)
            
            if not all_assets:
                logger.warning("⚠️ No assets found to persist")
                return
            
            logger.info(f"📊 Found {len(all_assets)} assets to persist")
            
            # Note: Deduplication is handled by intelligent agents using deduplication tools
            # The inventory manager has instructions to avoid creating duplicates
            
            # Debug: Log state attributes
            logger.info(f"🔍 State attributes: {[attr for attr in dir(self.state) if not attr.startswith('_')]}")
            logger.info(f"🔍 State has flow_id: {hasattr(self.state, 'flow_id')}")
            logger.info(f"🔍 State has client_account_id: {hasattr(self.state, 'client_account_id')}")
            logger.info(f"🔍 State has engagement_id: {hasattr(self.state, 'engagement_id')}")
            
            # Get database session and context
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                # Get context from state
                context = None
                if hasattr(self.state, 'context'):
                    context = self.state.context
                elif hasattr(self.state, 'client_account_id') and hasattr(self.state, 'engagement_id'):
                    # Build context from state
                    from app.core.context import RequestContext
                    context = RequestContext(
                        client_account_id=self.state.client_account_id,
                        engagement_id=self.state.engagement_id,
                        user_id=getattr(self.state, 'user_id', None),
                        flow_id=getattr(self.state, 'flow_id', None)
                    )
                else:
                    # Try to get context from flow_bridge if available
                    if self.flow_bridge and hasattr(self.flow_bridge, 'context'):
                        context = self.flow_bridge.context
                        logger.info(f"🔄 Using context from flow_bridge: client={context.client_account_id}, engagement={context.engagement_id}")
                
                if not context:
                    logger.error("❌ No context available for asset persistence")
                    return
                
                logger.info(f"📋 Using context: client={context.client_account_id}, engagement={context.engagement_id}")
                
                # Get discovery flow ID
                discovery_flow_id = None
                if hasattr(self.state, 'discovery_flow_id'):
                    discovery_flow_id = self.state.discovery_flow_id
                elif hasattr(self.state, 'flow_internal_id'):
                    discovery_flow_id = self.state.flow_internal_id
                elif hasattr(self.state, 'flow_id'):
                    discovery_flow_id = self.state.flow_id
                
                if not discovery_flow_id:
                    logger.error("❌ No discovery flow ID available for asset persistence")
                    return
                
                logger.info(f"🔗 Using discovery flow ID: {discovery_flow_id}")
                
                # Use AssetManager to persist assets
                from app.services.discovery_flow_service.managers.asset_manager import AssetManager
                asset_manager = AssetManager(db, context)
                
                # Get existing asset identifiers to prevent duplicates
                from sqlalchemy import select

                from app.models.asset import Asset
                existing_assets_query = select(Asset.name, Asset.hostname, Asset.ip_address).where(
                    Asset.client_account_id == context.client_account_id,
                    Asset.engagement_id == context.engagement_id
                )
                existing_assets_result = await db.execute(existing_assets_query)
                existing_assets = existing_assets_result.fetchall()
                existing_names = {row[0] for row in existing_assets if row[0]}
                existing_hostnames = {row[1] for row in existing_assets if row[1]}
                existing_ips = {row[2] for row in existing_assets if row[2]}
                
                logger.info(f"📋 Found {len(existing_names)} existing asset names, {len(existing_hostnames)} hostnames, {len(existing_ips)} IPs in database")
                
                # Prepare asset data for persistence using field mappings
                asset_data_list = []
                seen_names = set(existing_names)  # Start with existing names from database
                seen_hostnames = set(existing_hostnames)  # Track hostnames
                seen_ips = set(existing_ips)  # Track IP addresses
                
                for idx, asset in enumerate(all_assets):
                    # Transform raw asset data using field mappings
                    # Get asset name from field mappings - don't generate random names
                    asset_name = self._get_mapped_value(asset, 'asset_name')
                    hostname = self._get_mapped_value(asset, 'hostname')
                    ip_address = self._get_mapped_value(asset, 'ip_address')
                    
                    # If no asset name, use hostname or IP as identifier, or leave blank
                    if not asset_name or asset_name.strip() == '':
                        if hostname:
                            asset_name = hostname
                        elif ip_address:
                            asset_name = ip_address
                        else:
                            # Leave blank for user to fill in manually
                            asset_name = ""
                    
                    # Handle empty names (database constraint requires non-empty name)
                    if not asset_name:
                        asset_name = f"Asset-{idx + 1}"  # Simple numeric identifier
                    
                    # Ensure unique names by adding suffix if needed (check against both existing DB names and current batch)
                    original_name = asset_name
                    counter = 1
                    while asset_name in seen_names:
                        if original_name:
                            asset_name = f"{original_name}-{counter}"
                        else:
                            asset_name = f"Asset-{idx + 1}-{counter}"
                        counter += 1
                    seen_names.add(asset_name)
                    
                    # Check for hostname conflicts and skip if duplicate
                    if hostname and hostname in seen_hostnames:
                        logger.warning(f"⚠️ Skipping asset {idx + 1} - hostname '{hostname}' already exists")
                        continue
                    elif hostname:
                        seen_hostnames.add(hostname)
                    
                    # Check for IP conflicts and skip if duplicate
                    if ip_address and ip_address in seen_ips:
                        logger.warning(f"⚠️ Skipping asset {idx + 1} - IP address '{ip_address}' already exists")
                        continue
                    elif ip_address:
                        seen_ips.add(ip_address)
                    
                    logger.debug(f"🏷️ Asset {idx + 1}: original_name='{original_name}', final_name='{asset_name}', hostname='{hostname}', ip='{ip_address}'")
                    
                    asset_data = {
                        'name': asset_name,
                        'type': self._determine_asset_type(asset),
                        'raw_import_record_id': asset.get('raw_import_record_id'),  # Preserve linkage from data cleansing
                        'hostname': hostname,
                        'ip_address': ip_address,
                        'operating_system': self._get_mapped_value(asset, 'operating_system'),
                        'environment': self._get_mapped_value(asset, 'environment') or 'production',
                        'criticality': self._get_mapped_value(asset, 'criticality') or 'medium',
                        'status': 'discovered',
                        'application_name': self._get_mapped_value(asset, 'application_name'),
                        'cpu_cores': self._parse_int(self._get_mapped_value(asset, 'cpu_cores')),
                        'memory_gb': self._parse_float(self._get_mapped_value(asset, 'memory_gb')),
                        'storage_gb': self._parse_float(self._get_mapped_value(asset, 'storage_gb')),
                        'business_owner': self._get_mapped_value(asset, 'business_owner'),
                        'technical_owner': self._get_mapped_value(asset, 'technical_owner'),
                        'department': self._get_mapped_value(asset, 'department'),
                        'location': self._get_mapped_value(asset, 'location'),
                        'datacenter': self._get_mapped_value(asset, 'datacenter'),
                        'raw_data': asset,  # Store original data
                        'field_mappings_used': getattr(self.state, 'field_mappings', {}),
                        'normalized_data': {  # Normalized data using field mappings
                            'hostname': hostname,
                            'ip_address': ip_address,
                            'operating_system': self._get_mapped_value(asset, 'operating_system'),
                            'environment': self._get_mapped_value(asset, 'environment') or 'production',
                            'criticality': self._get_mapped_value(asset, 'criticality') or 'medium',
                            'application_name': self._get_mapped_value(asset, 'application_name'),
                            'cpu_cores': self._parse_int(self._get_mapped_value(asset, 'cpu_cores')),
                            'memory_gb': self._parse_float(self._get_mapped_value(asset, 'memory_gb')),
                            'storage_gb': self._parse_float(self._get_mapped_value(asset, 'storage_gb'))
                        }
                    }
                    asset_data_list.append(asset_data)
                
                # Create assets in database
                created_assets = await asset_manager.create_assets_from_discovery(
                    discovery_flow_id=discovery_flow_id,
                    asset_data_list=asset_data_list,
                    discovered_in_phase='inventory'
                )
                
                logger.info(f"✅ Successfully persisted {len(created_assets)} assets to database")
                
                # Link created assets back to raw import records
                await self._link_assets_to_raw_records(created_assets, asset_data_list)
                
                # Note: Asset enrichment is now handled by agents using enrichment tools
                # The inventory manager has instructions to enrich assets intelligently
                
                # Update state with created asset information
                asset_ids = [str(asset.id) for asset in created_assets]
                
                # Update asset_inventory field with results
                if hasattr(self.state, 'asset_inventory'):
                    logger.info(f"🔍 Current asset_inventory type: {type(self.state.asset_inventory)}")
                    logger.info(f"🔍 Current asset_inventory value: {self.state.asset_inventory}")
                    
                    # Ensure asset_inventory is a dictionary, not a string
                    if not isinstance(self.state.asset_inventory, dict):
                        logger.info(f"🔧 Converting asset_inventory from {type(self.state.asset_inventory)} to dict")
                        self.state.asset_inventory = {}
                    
                    self.state.asset_inventory['created_asset_ids'] = asset_ids
                    self.state.asset_inventory['total_assets'] = len(created_assets)
                    self.state.asset_inventory['status'] = 'completed'
                    self.state.asset_inventory['created_at'] = datetime.utcnow().isoformat()
                    logger.info(f"✅ Updated asset_inventory: {self.state.asset_inventory}")
                else:
                    # Initialize asset_inventory if it doesn't exist
                    logger.info("🔧 Initializing asset_inventory (not found)")
                    self.state.asset_inventory = {
                        'created_asset_ids': asset_ids,
                        'total_assets': len(created_assets),
                        'status': 'completed',
                        'created_at': datetime.utcnow().isoformat()
                    }
                
                # Also update asset_creation_results for backward compatibility
                if hasattr(self.state, 'asset_creation_results'):
                    # Ensure asset_creation_results is a dictionary
                    if not isinstance(self.state.asset_creation_results, dict):
                        self.state.asset_creation_results = {}
                    
                    self.state.asset_creation_results['created_asset_ids'] = asset_ids
                    self.state.asset_creation_results['total_created'] = len(created_assets)
                else:
                    # Initialize asset_creation_results if it doesn't exist
                    self.state.asset_creation_results = {
                        'created_asset_ids': asset_ids,
                        'total_created': len(created_assets)
                    }
                
        except Exception as e:
            logger.error(f"❌ Failed to persist assets to database: {e}", exc_info=True)
    
    def _determine_asset_type(self, asset: Dict[str, Any]) -> str:
        """Determine asset type from asset data using field mappings"""
        
        # PRIORITY 0: Check if asset_type is already set by the crew
        if 'asset_type' in asset and asset['asset_type']:
            crew_asset_type = str(asset['asset_type']).lower()
            if crew_asset_type in ['server', 'application', 'database', 'device']:
                return crew_asset_type
        
        # Use field mappings from the attribute mapping phase
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        # Get the source field that maps to asset_type
        asset_type_field = None
        asset_name_field = None
        os_field = None
        
        for source_field, target_field in field_mappings.items():
            if target_field == 'asset_type':
                asset_type_field = source_field
            elif target_field == 'asset_name':
                asset_name_field = source_field
            elif target_field == 'operating_system':
                os_field = source_field
        
        # Extract values using mapped fields AND direct asset keys
        asset_type = asset.get(asset_type_field, '') if asset_type_field else asset.get('asset_type', '')
        asset_name = asset.get(asset_name_field, '') if asset_name_field else asset.get('asset_name', asset.get('name', ''))
        os_info = asset.get(os_field, '') if os_field else asset.get('operating_system', asset.get('os', ''))
        
        # Convert to lowercase for comparison
        asset_type_lower = str(asset_type).lower()
        asset_name_lower = str(asset_name).lower()
        os_info_lower = str(os_info).lower()
        
        # PRIORITY 1: Direct asset type mapping from field mappings
        if asset_type_lower:
            if 'server' in asset_type_lower or 'host' in asset_type_lower or 'vm' in asset_type_lower or 'virtual' in asset_type_lower:
                return 'server'
            elif 'application' in asset_type_lower or 'app' in asset_type_lower or 'service' in asset_type_lower or 'software' in asset_type_lower:
                return 'application'
            elif 'database' in asset_type_lower or 'db' in asset_type_lower:
                return 'database'
            elif 'network' in asset_type_lower or 'device' in asset_type_lower or 'router' in asset_type_lower or 'switch' in asset_type_lower or 'firewall' in asset_type_lower:
                return 'device'
        
        # PRIORITY 2: OS-based classification (typically indicates servers)
        if os_info_lower and any(os in os_info_lower for os in ['linux', 'windows', 'unix', 'centos', 'ubuntu', 'redhat', 'solaris', 'aix']):
            return 'server'
        
        # PRIORITY 3: Name-based classification
        if asset_name_lower:
            if any(keyword in asset_name_lower for keyword in ['server', 'host', 'vm', 'srv']):
                return 'server'
            elif any(keyword in asset_name_lower for keyword in ['app', 'api', 'service', 'web']):
                return 'application'
            elif any(keyword in asset_name_lower for keyword in ['db', 'database', 'mysql', 'postgresql', 'oracle', 'sql']):
                return 'database'
            elif any(keyword in asset_name_lower for keyword in ['device', 'network', 'router', 'switch', 'firewall']):
                return 'device'
        
        # PRIORITY 4: Advanced pattern matching for applications
        if any(keyword in asset_type_lower for keyword in ['web', 'api', 'microservice']) or \
           any(keyword in asset_name_lower for keyword in ['payment', 'user', 'order', 'inventory']):
            return 'application'
        
        # PRIORITY 5: Advanced pattern matching for databases
        if any(keyword in asset_type_lower for keyword in ['mysql', 'postgresql', 'oracle', 'sql', 'mongo', 'redis']) or \
           any(keyword in asset_name_lower for keyword in ['userdb', 'orderdb', 'paymentdb']):
            return 'database'
        
        # PRIORITY 6: All asset names as fallback - classify based on common patterns
        all_asset_text = f"{asset_name_lower} {asset_type_lower} {os_info_lower}"
        if any(keyword in all_asset_text for keyword in ['server', 'host', 'vm', 'linux', 'windows', 'ubuntu', 'centos']):
            return 'server'
        elif any(keyword in all_asset_text for keyword in ['app', 'web', 'api', 'service', 'ui', 'frontend', 'backend']):
            return 'application'
        elif any(keyword in all_asset_text for keyword in ['db', 'database', 'mysql', 'postgres', 'oracle', 'mongo']):
            return 'database'
        elif any(keyword in all_asset_text for keyword in ['network', 'router', 'switch', 'firewall', 'device']):
            return 'device'
        
        # Default classification - classify as server if we can't determine
        logger.warning(f"Unable to determine asset type for asset: {asset_name}, defaulting to 'server'")
        return 'server'
    
    def _get_mapped_value(self, asset: Dict[str, Any], target_field: str) -> Any:
        """Get value from asset using field mappings"""
        # First, try to get the value directly from the target field (if data was already processed)
        if target_field in asset:
            return asset.get(target_field)
        
        # If not found, try to use field mappings to find the source field
        field_mappings = getattr(self.state, 'field_mappings', {})
        
        # Find the source field that maps to the target field
        source_field = None
        for source, target in field_mappings.items():
            if target == target_field:
                source_field = source
                break
        
        # Return the value from the source field if found
        if source_field:
            # Try original data first
            if '_original' in asset and source_field in asset['_original']:
                return asset['_original'][source_field]
            # Then try the asset itself
            return asset.get(source_field)
        
        return None
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Safely parse integer value"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Safely parse float value"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def _link_assets_to_raw_records(self, created_assets: List, asset_data_list: List[Dict[str, Any]]):
        """Link created assets back to their raw import records for full traceability"""
        from datetime import datetime

        from sqlalchemy import update

        from app.core.database import AsyncSessionLocal
        from app.models.data_import.core import RawImportRecord
        
        try:
            async with AsyncSessionLocal() as session:
                linked_count = 0
                
                for i, (asset, asset_data) in enumerate(zip(created_assets, asset_data_list)):
                    raw_record_id = asset_data.get('raw_import_record_id')
                    
                    if raw_record_id:
                        # Update the raw import record with the created asset ID
                        update_stmt = update(RawImportRecord).where(
                            RawImportRecord.id == raw_record_id
                        ).values(
                            asset_id=asset.id,
                            is_processed=True,
                            processed_at=datetime.utcnow(),
                            processing_notes=f"Linked to asset: {asset.name} (ID: {asset.id})"
                        )
                        
                        await session.execute(update_stmt)
                        linked_count += 1
                        logger.debug(f"🔗 Linked asset {asset.name} to raw record {raw_record_id}")
                    else:
                        logger.warning(f"⚠️ Asset {asset.name} has no raw_import_record_id for linkage")
                
                await session.commit()
                logger.info(f"✅ Successfully linked {linked_count}/{len(created_assets)} assets to raw import records")
                
        except Exception as e:
            logger.error(f"❌ Failed to link assets to raw import records: {e}", exc_info=True)
    
