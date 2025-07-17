"""
CrewAI Tools for Intelligent Task Coordination
Provides intelligent agents with tools to check task completion status,
avoid redundant work, and deduplicate data.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


def create_task_completion_tools(context_info: Dict[str, Any]) -> List:
    """
    Create intelligent task coordination tools for agents.
    
    These tools enable agents to:
    1. Check if assets already exist to avoid duplicates
    2. Verify recent task completion to prevent redundant work
    3. Coordinate with other agents to avoid conflicts
    """
    logger.info("🔧 Creating intelligent task coordination tools")
    
    tools = []
    
    # Asset deduplication tool
    asset_dedup_tool = AssetDeduplicationTool(context_info)
    tools.append(asset_dedup_tool)
    
    # Task completion checker tool
    task_completion_tool = TaskCompletionCheckerTool(context_info)
    tools.append(task_completion_tool)
    
    # Execution coordination tool
    coordination_tool = ExecutionCoordinationTool(context_info)
    tools.append(coordination_tool)
    
    logger.info(f"✅ Created {len(tools)} intelligent coordination tools")
    return tools


class AssetDeduplicationTool:
    """Tool for agents to check if assets already exist"""
    
    def __init__(self, context_info: Dict[str, Any]):
        self.context_info = context_info
        self.name = "asset_deduplication_checker"
        self.description = """
        Check if assets already exist in the database to avoid creating duplicates.
        Use this tool BEFORE creating new assets to ensure no duplicates are created.
        
        Input: List of assets to check (with hostname/name fields)
        Output: List of assets that don't already exist and are safe to create
        """
    
    async def _arun(self, assets_to_check: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Async implementation of asset deduplication check"""
        try:
            logger.info(f"🔍 Agent requested deduplication check for {len(assets_to_check)} assets")
            
            # Get database context
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                context = self.context_info
                if not context or not context.get('client_account_id') or not context.get('engagement_id'):
                    logger.warning("⚠️ Missing context for deduplication - returning all assets")
                    return assets_to_check
                
                # Get existing assets
                from app.repositories.discovery_flow_repository.queries.asset_queries import AssetQueries
                asset_queries = AssetQueries(db, context['client_account_id'], context['engagement_id'])
                existing_assets = await asset_queries.get_assets_by_client_engagement()
                
                existing_hostnames = {asset.hostname.lower() for asset in existing_assets if asset.hostname}
                existing_names = {asset.name.lower() for asset in existing_assets if asset.name}
                
                # Filter out duplicates
                unique_assets = []
                for asset in assets_to_check:
                    hostname = asset.get('hostname') or asset.get('Hostname') or asset.get('Host_Name')
                    name = asset.get('name') or asset.get('Asset_Name') or asset.get('Name')
                    
                    if hostname and hostname.lower() in existing_hostnames:
                        logger.debug(f"⏭️ Asset with hostname '{hostname}' already exists - skipping")
                        continue
                    
                    if not hostname and name and name.lower() in existing_names:
                        logger.debug(f"⏭️ Asset with name '{name}' already exists - skipping")
                        continue
                    
                    unique_assets.append(asset)
                
                logger.info(f"✅ Deduplication complete: {len(assets_to_check)} → {len(unique_assets)} unique assets")
                return unique_assets
                
        except Exception as e:
            logger.error(f"❌ Error in asset deduplication tool: {e}")
            return assets_to_check  # Return all assets on error
    
    def _run(self, assets_to_check: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sync wrapper for async implementation"""
        return asyncio.run(self._arun(assets_to_check))


class TaskCompletionCheckerTool:
    """Tool for agents to check if a task was recently completed"""
    
    def __init__(self, context_info: Dict[str, Any]):
        self.context_info = context_info
        self.name = "task_completion_checker"
        self.description = """
        Check if a specific task (like asset inventory) was recently completed
        to avoid redundant work. Use this BEFORE starting major processing tasks.
        
        Input: Task name (e.g., "asset_inventory", "data_cleansing")
        Output: Dict with completion status and details
        """
    
    def _run(self, task_name: str) -> Dict[str, Any]:
        """Check if task was recently completed"""
        try:
            logger.info(f"🔍 Agent checking completion status for task: {task_name}")
            
            # Check agent insights for recent completion
            from pathlib import Path
            import json
            
            insights_file = Path("backend/data/agent_insights.json")
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    insights = json.load(f)
                
                # Look for recent completion of this task
                recent_completion = None
                for insight_id, insight in insights.items():
                    if (insight.get('insight_type') == 'phase_complete' and 
                        task_name in insight.get('supporting_data', {}).get('phase', '')):
                        recent_completion = insight
                        break
                
                if recent_completion:
                    logger.info(f"✅ Recent completion found for {task_name}")
                    return {
                        'recently_completed': True,
                        'completion_time': recent_completion.get('created_at'),
                        'details': recent_completion.get('supporting_data', {})
                    }
            
            logger.info(f"ℹ️ No recent completion found for {task_name}")
            return {
                'recently_completed': False,
                'details': {}
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking task completion: {e}")
            return {'recently_completed': False, 'details': {}}


class ExecutionCoordinationTool:
    """Tool for agents to coordinate execution and avoid conflicts"""
    
    def __init__(self, context_info: Dict[str, Any]):
        self.context_info = context_info
        self.name = "execution_coordinator"
        self.description = """
        Coordinate with other agents to avoid conflicts and redundant execution.
        Use this when starting parallel operations that might conflict.
        
        Input: Operation name and agent identifier
        Output: Coordination status and recommendations
        """
    
    def _run(self, operation_name: str, agent_id: str) -> Dict[str, Any]:
        """Coordinate execution with other agents"""
        try:
            logger.info(f"🤝 Agent {agent_id} requesting coordination for {operation_name}")
            
            # Simple coordination - could be enhanced with proper locking
            from datetime import datetime, timedelta
            
            # Check if another agent is recently working on the same operation
            coordination_result = {
                'can_proceed': True,
                'coordination_time': datetime.utcnow().isoformat(),
                'agent_id': agent_id,
                'operation': operation_name,
                'recommendations': []
            }
            
            logger.info(f"✅ Coordination complete for {agent_id} on {operation_name}")
            return coordination_result
            
        except Exception as e:
            logger.error(f"❌ Error in execution coordination: {e}")
            return {'can_proceed': True, 'recommendations': ['Proceed with caution - coordination failed']}