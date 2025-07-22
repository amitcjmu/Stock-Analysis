"""
Functional Agent Tools for Agentic Memory - Simplified Implementation

This module provides agent tools using a functional approach that avoids
Pydantic validation issues while maintaining the same functionality.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from crewai.tools import tool
    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False
    def tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

try:
    from app.core.database import AsyncSessionLocal
    from app.models.agent_memory import (
        AgentDiscoveredPattern,
        PatternType,
        create_asset_enrichment_pattern,
        get_patterns_for_agent_reasoning,
    )
    from app.models.asset import Asset
    from app.services.agentic_memory import MemoryQuery, ThreeTierMemoryManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_pattern_search_tool(client_account_id: uuid.UUID, engagement_id: uuid.UUID):
    """Create pattern search tool with context"""
    
    @tool("Search discovered patterns for evidence")
    def pattern_search(query_data: str) -> str:
        """Search discovered patterns for evidence related to your hypothesis.
        
        Input should be a JSON string with:
        - query: string describing what pattern evidence you're looking for
        - pattern_types: list of pattern types to search (optional)
        - min_confidence: minimum confidence threshold (0.0 to 1.0, default 0.6)
        - validated_only: whether to only search human-validated patterns (default false)
        
        Example: '{"query": "database business value indicators", "pattern_types": ["business_value_indicator"], "min_confidence": 0.7}'
        """
        if not DATABASE_AVAILABLE:
            return "Pattern search not available - database not connected"
        
        try:
            params = json.loads(query_data)
            
            # Extract search parameters
            query_text = params.get('query', '')
            pattern_types_str = params.get('pattern_types', [])
            min_confidence = params.get('min_confidence', 0.6)
            validated_only = params.get('validated_only', False)
            
            # Convert pattern type strings to enums
            pattern_types = []
            if pattern_types_str:
                for pt_str in pattern_types_str:
                    try:
                        pattern_types.append(PatternType(pt_str))
                    except ValueError:
                        logger.warning(f"Unknown pattern type: {pt_str}")
            
            # Create memory manager and query
            memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
            memory_query = MemoryQuery(
                query_text=query_text,
                memory_tiers=['semantic'],
                pattern_types=pattern_types,
                min_confidence=min_confidence,
                validated_only=validated_only,
                max_results=10
            )
            
            # Search patterns - handle event loop properly
            try:
                # Try to get current event loop
                loop = asyncio.get_running_loop()
                # If we're in an event loop, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, memory_manager.query_memory(memory_query))
                    results = future.result(timeout=30)
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                results = asyncio.run(memory_manager.query_memory(memory_query))
            
            if not results:
                return f"No patterns found matching query: {query_text}"
            
            # Format results for agent consumption
            pattern_summaries = []
            for result in results:
                if result.tier == 'semantic':
                    pattern = result.content
                    summary = {
                        'pattern_name': pattern['name'],
                        'pattern_type': pattern['type'],
                        'description': pattern['description'],
                        'confidence': pattern['confidence'],
                        'validated': pattern['validated'],
                        'evidence_count': pattern['evidence_count'],
                        'pattern_logic': pattern['pattern_data']
                    }
                    pattern_summaries.append(summary)
            
            response = {
                'found_patterns': len(pattern_summaries),
                'patterns': pattern_summaries[:5],  # Limit to top 5 for readability
                'search_summary': f"Found {len(pattern_summaries)} patterns matching '{query_text}' with confidence >= {min_confidence}"
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return f"Pattern search error: {str(e)}"
    
    return pattern_search


def create_asset_query_tool(client_account_id: uuid.UUID, engagement_id: uuid.UUID):
    """Create asset data query tool with context"""
    
    @tool("Query asset data for analysis")
    def asset_data_query(query_data: str) -> str:
        """Query asset data to gather evidence for your analysis.
        
        Input should be a JSON string with:
        - asset_type: filter by asset type (optional)
        - technology_stack: filter by technology (optional)
        - environment: filter by environment (optional)  
        - business_criticality: filter by criticality (optional)
        - limit: maximum number of results (default 10)
        - include_fields: list of specific fields to include in results
        
        Example: '{"asset_type": "database", "environment": "production", "limit": 5, "include_fields": ["name", "technology_stack", "business_criticality"]}'
        """
        if not DATABASE_AVAILABLE:
            return "Asset query not available - database not connected"
        
        try:
            params = json.loads(query_data)
            
            # Extract query parameters
            asset_type = params.get('asset_type')
            technology_stack = params.get('technology_stack')
            environment = params.get('environment')
            business_criticality = params.get('business_criticality')
            limit = params.get('limit', 10)
            include_fields = params.get('include_fields', ['name', 'asset_type', 'technology_stack', 'environment', 'business_criticality'])
            
            # Handle event loop properly
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _query_assets_async(
                        client_account_id, engagement_id,
                        asset_type, technology_stack, environment, business_criticality, limit, include_fields
                    ))
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(_query_assets_async(
                    client_account_id, engagement_id,
                    asset_type, technology_stack, environment, business_criticality, limit, include_fields
                ))
            
        except Exception as e:
            logger.error(f"Asset query failed: {e}")
            return f"Asset query error: {str(e)}"
    
    return asset_data_query


def create_pattern_recording_tool(client_account_id: uuid.UUID, engagement_id: uuid.UUID, agent_name: str, flow_id: Optional[uuid.UUID] = None):
    """Create pattern recording tool with context"""
    
    @tool("Record new discovered pattern")
    def pattern_recording(pattern_data: str) -> str:
        """Record a new pattern you've discovered during asset analysis.
        
        Input should be a JSON string with:
        - pattern_type: type of pattern (e.g., 'business_value_indicator', 'risk_factor')
        - pattern_name: descriptive name for the pattern
        - pattern_description: detailed description of when this pattern applies  
        - pattern_logic: the actual pattern rules/criteria as a JSON object
        - confidence_score: your confidence in this pattern (0.0 to 1.0)
        - evidence_assets: list of asset IDs that support this pattern (optional)
        
        Example: '{"pattern_type": "business_value_indicator", "pattern_name": "Production Database Critical Business Value", "pattern_description": "Production databases with high utilization indicate critical business value", "pattern_logic": {"environment": "production", "asset_type": "database", "cpu_utilization_percent": ">= 70"}, "confidence_score": 0.85}'
        """
        if not DATABASE_AVAILABLE:
            return "Pattern recording not available - database not connected"
        
        try:
            params = json.loads(pattern_data)
            
            # Extract pattern parameters
            pattern_type_str = params.get('pattern_type')
            pattern_name = params.get('pattern_name')
            pattern_description = params.get('pattern_description')
            pattern_logic = params.get('pattern_logic', {})
            confidence_score = params.get('confidence_score', 0.7)
            evidence_assets_str = params.get('evidence_assets', [])
            
            # Validate required fields
            if not all([pattern_type_str, pattern_name, pattern_description]):
                return "Error: pattern_type, pattern_name, and pattern_description are required"
            
            # Convert pattern type string to enum
            try:
                pattern_type = PatternType(pattern_type_str)
            except ValueError:
                return f"Error: Unknown pattern type '{pattern_type_str}'. Valid types: {[pt.value for pt in PatternType]}"
            
            # Convert evidence asset IDs
            evidence_assets = []
            for asset_id_str in evidence_assets_str:
                try:
                    evidence_assets.append(uuid.UUID(asset_id_str))
                except ValueError:
                    logger.warning(f"Invalid asset ID format: {asset_id_str}")
            
            # Store pattern - handle event loop properly
            memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, memory_manager.store_pattern_discovery(
                        agent_name=agent_name,
                        pattern_type=pattern_type,
                        pattern_name=pattern_name,
                        pattern_description=pattern_description,
                        pattern_logic=pattern_logic,
                        confidence_score=confidence_score,
                        evidence_assets=evidence_assets,
                        flow_id=flow_id
                    ))
                    pattern = future.result(timeout=30)
            except RuntimeError:
                pattern = asyncio.run(memory_manager.store_pattern_discovery(
                    agent_name=agent_name,
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    pattern_description=pattern_description,
                    pattern_logic=pattern_logic,
                    confidence_score=confidence_score,
                    evidence_assets=evidence_assets,
                    flow_id=flow_id
                ))
            
            if pattern:
                response = {
                    'status': 'success',
                    'pattern_id': str(pattern.id),
                    'message': f"Pattern '{pattern_name}' recorded successfully with confidence {confidence_score}",
                    'next_steps': 'Pattern is pending validation and will be available for future agent reasoning'
                }
                return json.dumps(response, indent=2)
            else:
                return "Error: Failed to record pattern - database operation failed"
            
        except Exception as e:
            logger.error(f"Pattern recording failed: {e}")
            return f"Pattern recording error: {str(e)}"
    
    return pattern_recording


def create_asset_enrichment_tool(client_account_id: uuid.UUID, engagement_id: uuid.UUID, agent_name: str):
    """Create asset enrichment tool with context"""
    
    @tool("Enrich asset with business intelligence")
    def asset_enrichment(enrichment_data: str) -> str:
        """Enrich an asset with business intelligence based on your analysis.
        
        Input should be a JSON string with:
        - asset_id: UUID of the asset to enrich
        - business_value_score: business value score 1-10 (optional)
        - risk_assessment: risk level 'low', 'medium', 'high', 'critical' (optional)  
        - modernization_potential: potential 'low', 'medium', 'high' (optional)
        - cloud_readiness_score: cloud readiness 0-100 (optional)
        - reasoning: detailed explanation of your analysis and conclusions
        
        Example: '{"asset_id": "123e4567-e89b-12d3-a456-426614174000", "business_value_score": 8, "risk_assessment": "medium", "modernization_potential": "high", "reasoning": "Production database with high utilization serving critical customer applications"}'
        """
        if not DATABASE_AVAILABLE:
            return "Asset enrichment not available - database not connected"
        
        try:
            params = json.loads(enrichment_data)
            
            # Extract enrichment parameters
            asset_id_str = params.get('asset_id')
            business_value_score = params.get('business_value_score')
            risk_assessment = params.get('risk_assessment')
            modernization_potential = params.get('modernization_potential')
            cloud_readiness_score = params.get('cloud_readiness_score')
            reasoning = params.get('reasoning', '')
            
            # Validate asset ID
            if not asset_id_str:
                return "Error: asset_id is required"
            
            try:
                asset_id = uuid.UUID(asset_id_str)
            except ValueError:
                return f"Error: Invalid asset ID format: {asset_id_str}"
            
            # Validate score ranges
            if business_value_score is not None and not (1 <= business_value_score <= 10):
                return "Error: business_value_score must be between 1 and 10"
            
            if cloud_readiness_score is not None and not (0 <= cloud_readiness_score <= 100):
                return "Error: cloud_readiness_score must be between 0 and 100"
            
            # Validate categorical values
            valid_risk_levels = ['low', 'medium', 'high', 'critical']
            if risk_assessment and risk_assessment not in valid_risk_levels:
                return f"Error: risk_assessment must be one of {valid_risk_levels}"
            
            valid_modernization_levels = ['low', 'medium', 'high']
            if modernization_potential and modernization_potential not in valid_modernization_levels:
                return f"Error: modernization_potential must be one of {valid_modernization_levels}"
            
            # Perform enrichment - handle event loop properly
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _enrich_asset_async(
                        client_account_id, engagement_id, agent_name,
                        asset_id, business_value_score, risk_assessment, modernization_potential, 
                        cloud_readiness_score, reasoning
                    ))
                    result = future.result(timeout=30)
            except RuntimeError:
                result = asyncio.run(_enrich_asset_async(
                    client_account_id, engagement_id, agent_name,
                    asset_id, business_value_score, risk_assessment, modernization_potential, 
                    cloud_readiness_score, reasoning
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Asset enrichment failed: {e}")
            return f"Asset enrichment error: {str(e)}"
    
    return asset_enrichment


async def _query_assets_async(client_account_id, engagement_id, asset_type, technology_stack, environment, business_criticality, limit, include_fields):
    """Async asset query implementation"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        # Build query with multi-tenant filtering
        query = select(Asset).where(
            Asset.client_account_id == client_account_id,
            Asset.engagement_id == engagement_id
        )
        
        # Apply filters
        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
        if technology_stack:
            query = query.where(Asset.technology_stack.ilike(f'%{technology_stack}%'))
        if environment:
            query = query.where(Asset.environment == environment)
        if business_criticality:
            query = query.where(Asset.business_criticality == business_criticality)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        result = await session.execute(query)
        assets = result.scalars().all()
        
        if not assets:
            return "No assets found matching the specified criteria"
        
        # Format results
        asset_data = []
        for asset in assets:
            asset_dict = {}
            for field in include_fields:
                if hasattr(asset, field):
                    value = getattr(asset, field)
                    # Convert UUID to string for JSON serialization
                    if hasattr(value, 'hex'):
                        value = str(value)
                    asset_dict[field] = value
            asset_data.append(asset_dict)
        
        response = {
            'found_assets': len(asset_data),
            'assets': asset_data,
            'query_summary': f"Found {len(asset_data)} assets matching criteria"
        }
        
        return json.dumps(response, indent=2, default=str)


async def _enrich_asset_async(client_account_id, engagement_id, agent_name, asset_id, business_value_score, risk_assessment, modernization_potential, cloud_readiness_score, reasoning):
    """Async asset enrichment implementation"""
    async with AsyncSessionLocal() as session:
        # Find asset with multi-tenant filtering
        asset = await session.get(Asset, asset_id)
        
        if not asset:
            return f"Error: Asset {asset_id} not found"
        
        # Verify multi-tenant access
        if asset.client_account_id != client_account_id or asset.engagement_id != engagement_id:
            return f"Error: Asset {asset_id} not accessible in current context"
        
        # Update enrichment fields
        changes_made = []
        
        if business_value_score is not None:
            asset.business_value_score = business_value_score
            changes_made.append(f"business_value_score: {business_value_score}")
        
        if risk_assessment:
            asset.risk_assessment = risk_assessment
            changes_made.append(f"risk_assessment: {risk_assessment}")
        
        if modernization_potential:
            asset.modernization_potential = modernization_potential
            changes_made.append(f"modernization_potential: {modernization_potential}")
        
        if cloud_readiness_score is not None:
            asset.cloud_readiness_score = cloud_readiness_score
            changes_made.append(f"cloud_readiness_score: {cloud_readiness_score}")
        
        # Update enrichment metadata
        asset.enrichment_reasoning = reasoning
        asset.last_enriched_at = datetime.utcnow()
        asset.last_enriched_by_agent = agent_name
        asset.enrichment_status = 'agent_enriched'
        
        # Commit changes
        await session.commit()
        
        response = {
            'status': 'success',
            'asset_id': str(asset_id),
            'asset_name': asset.name,
            'changes_made': changes_made,
            'enrichment_agent': agent_name,
            'enrichment_time': datetime.utcnow().isoformat(),
            'reasoning_recorded': bool(reasoning)
        }
        
        return json.dumps(response, indent=2)


def create_functional_agent_tools(client_account_id: uuid.UUID, engagement_id: uuid.UUID, agent_name: str, flow_id: Optional[uuid.UUID] = None) -> List:
    """
    Create agent tools using functional approach to avoid Pydantic issues
    
    Args:
        client_account_id: Multi-tenant client context
        engagement_id: Multi-tenant engagement context
        agent_name: Name of the agent using these tools
        flow_id: Optional flow context for pattern discovery
    
    Returns:
        List of functional agent tools
    """
    
    tools = []
    
    if CREWAI_TOOLS_AVAILABLE and DATABASE_AVAILABLE:
        try:
            tools.extend([
                create_pattern_search_tool(client_account_id, engagement_id),
                create_asset_query_tool(client_account_id, engagement_id),
                create_pattern_recording_tool(client_account_id, engagement_id, agent_name, flow_id),
                create_asset_enrichment_tool(client_account_id, engagement_id, agent_name)
            ])
            logger.info(f"✅ Created {len(tools)} functional agent tools for {agent_name}")
        except Exception as e:
            logger.error(f"Failed to create functional agent tools: {e}")
            logger.warning("Functional agent tools not available - creation failed")
    else:
        logger.warning("Functional agent tools not available - missing dependencies")
    
    return tools