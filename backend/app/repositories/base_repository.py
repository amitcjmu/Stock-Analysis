"""
Base repository for context-aware database operations with multi-tenant support.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, List, Optional, Dict, Any, Union
import logging
import os

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select, and_, or_, func, delete, update
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None
    select = and_ = or_ = func = delete = update = object
    class selectinload:
        @staticmethod
        def options(*args):
            return None

# Type variable for model classes
ModelType = TypeVar("ModelType")

logger = logging.getLogger(__name__)


class ContextAwareRepository(Generic[ModelType], ABC):
    """
    Base repository class providing context-aware database operations.
    Supports multi-tenant data isolation and mock data fallback.
    """
    
    def __init__(self, db: AsyncSession, context: Optional[Dict[str, Any]] = None):
        self.db = db
        self.context = context or {}
        self.demo_mode = os.getenv("DEMO_DATA", "true").lower() == "true"
        
    def _get_base_filters(self, model_class: Type[ModelType]) -> List:
        """Get base filters for multi-tenant context filtering."""
        filters = []
        
        # Only apply context filters if the model has the required fields
        if hasattr(model_class, 'client_account_id') and self.context.get('client_account_id'):
            filters.append(model_class.client_account_id == self.context['client_account_id'])
            
        if hasattr(model_class, 'engagement_id') and self.context.get('engagement_id'):
            filters.append(model_class.engagement_id == self.context['engagement_id'])
            
        return filters
    
    def _apply_mock_data_logic(self, query, model_class: Type[ModelType]):
        """Apply mock data logic based on demo mode and data availability."""
        if not self.demo_mode:
            # If demo mode is disabled, exclude mock data
            if hasattr(model_class, 'is_mock'):
                query = query.where(model_class.is_mock == False)
            return query
        
        # Demo mode enabled - include both real and mock data
        # Real data takes precedence, but show mock data if no real data exists
        return query
    
    async def _has_real_data(self, model_class: Type[ModelType]) -> bool:
        """Check if real (non-mock) data exists for the current context."""
        try:
            base_filters = self._get_base_filters(model_class)
            
            if hasattr(model_class, 'is_mock'):
                base_filters.append(model_class.is_mock == False)
            
            query = select(func.count(model_class.id)).where(and_(*base_filters))
            result = await self.db.execute(query)
            count = result.scalar()
            return count > 0
        except Exception as e:
            logger.warning(f"Error checking for real data: {e}")
            return False
    
    async def find_all(
        self, 
        model_class: Type[ModelType],
        filters: Optional[List] = None,
        order_by: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """Find all records matching the criteria with context filtering."""
        try:
            # Start with base context filters
            all_filters = self._get_base_filters(model_class)
            
            # Add custom filters
            if filters:
                all_filters.extend(filters)
            
            # Build query
            query = select(model_class)
            
            if all_filters:
                query = query.where(and_(*all_filters))
            
            # Handle mock data logic
            if self.demo_mode and hasattr(model_class, 'is_mock'):
                has_real = await self._has_real_data(model_class)
                if not has_real:
                    # No real data, include mock data
                    logger.info(f"No real data found for {model_class.__name__}, including mock data")
                else:
                    # Real data exists, exclude mock data
                    query = query.where(model_class.is_mock == False)
            
            # Apply ordering
            if order_by:
                for order_clause in order_by:
                    query = query.order_by(order_clause)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_all: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in find_all: {e}")
            raise
    
    async def find_by_id(self, model_class: Type[ModelType], id: str) -> Optional[ModelType]:
        """Find a record by ID with context filtering."""
        try:
            filters = self._get_base_filters(model_class)
            filters.append(model_class.id == id)
            
            query = select(model_class).where(and_(*filters))
            query = self._apply_mock_data_logic(query, model_class)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_id: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in find_by_id: {e}")
            raise
    
    async def find_by_criteria(
        self, 
        model_class: Type[ModelType], 
        criteria: Dict[str, Any]
    ) -> List[ModelType]:
        """Find records matching specific criteria."""
        try:
            filters = self._get_base_filters(model_class)
            
            # Add criteria filters
            for field, value in criteria.items():
                if hasattr(model_class, field):
                    filters.append(getattr(model_class, field) == value)
            
            query = select(model_class).where(and_(*filters))
            query = self._apply_mock_data_logic(query, model_class)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in find_by_criteria: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in find_by_criteria: {e}")
            raise
    
    async def create(self, model_class: Type[ModelType], **kwargs) -> ModelType:
        """Create a new record with context data."""
        try:
            # Add context data automatically
            if hasattr(model_class, 'client_account_id') and self.context.get('client_account_id'):
                kwargs['client_account_id'] = self.context['client_account_id']
                
            if hasattr(model_class, 'engagement_id') and self.context.get('engagement_id'):
                kwargs['engagement_id'] = self.context['engagement_id']
                
            if hasattr(model_class, 'created_by') and self.context.get('user_id'):
                kwargs['created_by'] = self.context['user_id']
            
            # Ensure mock flag is set appropriately
            if hasattr(model_class, 'is_mock') and 'is_mock' not in kwargs:
                kwargs['is_mock'] = False
            
            instance = model_class(**kwargs)
            self.db.add(instance)
            await self.db.flush()  # Get the ID without committing
            
            logger.info(f"Created {model_class.__name__} with ID: {instance.id}")
            return instance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in create: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create: {e}")
            raise
    
    async def update(
        self, 
        model_class: Type[ModelType], 
        id: str, 
        **kwargs
    ) -> Optional[ModelType]:
        """Update a record by ID with context filtering."""
        try:
            # Find the record first
            instance = await self.find_by_id(model_class, id)
            if not instance:
                return None
            
            # Add audit data
            if hasattr(model_class, 'updated_by') and self.context.get('user_id'):
                kwargs['updated_by'] = self.context['user_id']
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            await self.db.flush()
            logger.info(f"Updated {model_class.__name__} with ID: {id}")
            return instance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in update: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update: {e}")
            raise
    
    async def delete(self, model_class: Type[ModelType], id: str) -> bool:
        """Delete a record by ID with context filtering."""
        try:
            instance = await self.find_by_id(model_class, id)
            if not instance:
                return False
            
            await self.db.delete(instance)
            await self.db.flush()
            
            logger.info(f"Deleted {model_class.__name__} with ID: {id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in delete: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            raise
    
    async def count(
        self, 
        model_class: Type[ModelType],
        filters: Optional[List] = None
    ) -> int:
        """Count records matching the criteria with context filtering."""
        try:
            all_filters = self._get_base_filters(model_class)
            
            if filters:
                all_filters.extend(filters)
            
            query = select(func.count(model_class.id))
            
            if all_filters:
                query = query.where(and_(*all_filters))
            
            # Handle mock data logic
            if self.demo_mode and hasattr(model_class, 'is_mock'):
                has_real = await self._has_real_data(model_class)
                if not has_real:
                    # No real data, count mock data
                    query = query.where(model_class.is_mock == True)
                else:
                    # Real data exists, count only real data
                    query = query.where(model_class.is_mock == False)
            
            result = await self.db.execute(query)
            return result.scalar()
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in count: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in count: {e}")
            raise
    
    async def exists(
        self, 
        model_class: Type[ModelType],
        criteria: Dict[str, Any]
    ) -> bool:
        """Check if a record exists matching the criteria."""
        try:
            count = await self.count(
                model_class,
                filters=[getattr(model_class, k) == v for k, v in criteria.items() if hasattr(model_class, k)]
            )
            return count > 0
            
        except Exception as e:
            logger.error(f"Error in exists check: {e}")
            return False


class AssetRepository(ContextAwareRepository):
    """Repository for Asset operations with context awareness."""
    
    async def find_by_asset_type(self, asset_type: str) -> List:
        """Find assets by asset type."""
        from app.models.asset import Asset, AssetType
        
        return await self.find_by_criteria(
            Asset,
            {"asset_type": AssetType(asset_type)}
        )
    
    async def find_by_six_r_strategy(self, strategy: str) -> List:
        """Find assets by 6R migration strategy."""
        from app.models.asset import Asset, SixRStrategy
        
        return await self.find_by_criteria(
            Asset,
            {"six_r_strategy": SixRStrategy(strategy)}
        )
    
    async def find_by_migration_wave(self, wave_number: int) -> List:
        """Find assets by migration wave."""
        from app.models.asset import Asset
        
        return await self.find_by_criteria(
            Asset,
            {"migration_wave": wave_number}
        )
    
    async def find_critical_assets(self) -> List:
        """Find assets marked as critical."""
        from app.models.asset import Asset
        
        return await self.find_by_criteria(
            Asset,
            {"criticality": "Critical"}
        )
    
    async def get_asset_summary(self) -> Dict[str, Any]:
        """Get summary statistics for assets."""
        from app.models.asset import Asset, AssetType, SixRStrategy
        
        try:
            # Get total count
            total_assets = await self.count(Asset)
            
            # Get counts by asset type
            type_counts = {}
            for asset_type in AssetType:
                count = await self.count(
                    Asset,
                    [Asset.asset_type == asset_type]
                )
                type_counts[asset_type.value] = count
            
            # Get counts by 6R strategy
            strategy_counts = {}
            for strategy in SixRStrategy:
                count = await self.count(
                    Asset,
                    [Asset.six_r_strategy == strategy]
                )
                strategy_counts[strategy.value] = count
            
            # Get cost summary
            filters = self._get_base_filters(Asset)
            if self.demo_mode and hasattr(Asset, 'is_mock'):
                has_real = await self._has_real_data(Asset)
                if not has_real:
                    filters.append(Asset.is_mock == True)
                else:
                    filters.append(Asset.is_mock == False)
            
            cost_query = select(
                func.sum(Asset.current_monthly_cost).label('total_current_cost'),
                func.sum(Asset.estimated_cloud_cost).label('total_estimated_cost')
            )
            
            if filters:
                cost_query = cost_query.where(and_(*filters))
            
            result = await self.db.execute(cost_query)
            cost_data = result.first()
            
            return {
                "total_assets": total_assets,
                "asset_types": type_counts,
                "six_r_strategies": strategy_counts,
                "cost_summary": {
                    "total_current_cost": float(cost_data.total_current_cost or 0),
                    "total_estimated_cost": float(cost_data.total_estimated_cost or 0),
                    "potential_savings": float((cost_data.total_current_cost or 0) - (cost_data.total_estimated_cost or 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating asset summary: {e}")
            return {
                "total_assets": 0,
                "asset_types": {},
                "six_r_strategies": {},
                "cost_summary": {
                    "total_current_cost": 0,
                    "total_estimated_cost": 0,
                    "potential_savings": 0
                }
            } 