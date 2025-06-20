"""
Enhanced dependency repository for application and server relationships.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func
import logging

from app.models.asset import Asset, AssetDependency, AssetType
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)

class DependencyRepository(ContextAwareRepository[AssetDependency]):
    """Enhanced dependency repository with application-specific operations."""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        """Initialize dependency repository with context."""
        super().__init__(db, AssetDependency, client_account_id, engagement_id)

    async def get_app_server_dependencies(self) -> List[Dict[str, Any]]:
        """Get all application-to-server dependencies."""
        query = select(
            AssetDependency,
            Asset.name.label('app_name'),
            Asset.asset_type.label('app_type'),
            Asset.id.label('app_id'),
            Asset.application_name.label('app_display_name'),
            func.json_build_object(
                'name', Asset.name,
                'type', Asset.asset_type,
                'id', Asset.id,
                'hostname', Asset.hostname
            ).label('server_info')
        ).join(
            Asset,
            and_(
                Asset.id == AssetDependency.asset_id,
                Asset.asset_type == AssetType.APPLICATION
            )
        ).join(
            Asset,
            and_(
                Asset.id == AssetDependency.depends_on_asset_id,
                Asset.asset_type == AssetType.SERVER
            ),
            from_joinpoint=True
        )
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def get_app_app_dependencies(self) -> List[Dict[str, Any]]:
        """Get all application-to-application dependencies."""
        query = select(
            AssetDependency,
            Asset.name.label('source_app_name'),
            Asset.asset_type.label('source_app_type'),
            Asset.id.label('source_app_id'),
            Asset.application_name.label('source_app_display_name'),
            func.json_build_object(
                'name', Asset.name,
                'type', Asset.asset_type,
                'id', Asset.id,
                'application_name', Asset.application_name
            ).label('target_app_info')
        ).join(
            Asset,
            and_(
                Asset.id == AssetDependency.asset_id,
                Asset.asset_type == AssetType.APPLICATION
            )
        ).join(
            Asset,
            and_(
                Asset.id == AssetDependency.depends_on_asset_id,
                Asset.asset_type == AssetType.APPLICATION
            ),
            from_joinpoint=True
        )
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def get_available_applications(self) -> List[Dict[str, Any]]:
        """Get list of all applications."""
        query = select(
            Asset.id,
            Asset.name,
            Asset.application_name,
            Asset.description
        ).where(
            Asset.asset_type == AssetType.APPLICATION
        )
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def get_available_servers(self) -> List[Dict[str, Any]]:
        """Get list of all servers."""
        query = select(
            Asset.id,
            Asset.name,
            Asset.hostname,
            Asset.description
        ).where(
            Asset.asset_type == AssetType.SERVER
        )
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def create_app_server_dependency(
        self,
        app_id: str,
        server_id: str,
        dependency_type: str,
        description: Optional[str] = None
    ) -> AssetDependency:
        """Create a new application-to-server dependency."""
        # Validate that app_id is an application and server_id is a server
        app = await self.db.execute(
            select(Asset).where(
                and_(
                    Asset.id == app_id,
                    Asset.asset_type == AssetType.APPLICATION
                )
            )
        )
        server = await self.db.execute(
            select(Asset).where(
                and_(
                    Asset.id == server_id,
                    Asset.asset_type == AssetType.SERVER
                )
            )
        )
        
        if not app.scalar() or not server.scalar():
            raise ValueError("Invalid application or server ID")
            
        return await self.create(
            asset_id=app_id,
            depends_on_asset_id=server_id,
            dependency_type=dependency_type,
            description=description
        )

    async def create_app_app_dependency(
        self,
        source_app_id: str,
        target_app_id: str,
        dependency_type: str,
        description: Optional[str] = None
    ) -> AssetDependency:
        """Create a new application-to-application dependency."""
        # Validate that both IDs are applications
        apps = await self.db.execute(
            select(Asset).where(
                and_(
                    Asset.id.in_([source_app_id, target_app_id]),
                    Asset.asset_type == AssetType.APPLICATION
                )
            )
        )
        
        if len(list(apps.scalars())) != 2:
            raise ValueError("Invalid application IDs")
            
        return await self.create(
            asset_id=source_app_id,
            depends_on_asset_id=target_app_id,
            dependency_type=dependency_type,
            description=description
        ) 