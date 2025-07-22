"""
Deduplication service for engagement-level views.
Provides intelligent deduplication logic for multi-session data with CrewAI agent integration.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import and_, desc, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType')


class DeduplicationService:
    """
    Service for intelligent deduplication across sessions within an engagement.
    
    Features:
    - Smart asset matching based on multiple criteria
    - Priority-based deduplication (latest session wins)
    - CrewAI agent integration for complex deduplication decisions
    - Configurable deduplication strategies
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize deduplication service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.deduplication_strategies = {
            'hostname_priority': self._hostname_priority_strategy,
            'latest_session': self._latest_session_strategy,
            'data_quality': self._data_quality_strategy,
            'agent_assisted': self._agent_assisted_strategy
        }
    
    async def deduplicate_assets(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        strategy: str = 'latest_session',
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Deduplicate assets across sessions using specified strategy.
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            strategy: Deduplication strategy to use
            filters: Optional additional filters
            
        Returns:
            List of deduplicated model instances
        """
        if strategy not in self.deduplication_strategies:
            raise ValueError(f"Unknown deduplication strategy: {strategy}")
        
        strategy_func = self.deduplication_strategies[strategy]
        return await strategy_func(model_class, engagement_id, filters)
    
    async def _hostname_priority_strategy(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Deduplication strategy based on hostname priority.
        
        Priority order:
        1. Most recent session
        2. Best data quality (non-null fields)
        3. Longest hostname (more specific)
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            filters: Optional additional filters
            
        Returns:
            List of deduplicated model instances
        """
        # Find hostname field
        hostname_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(model_class, field_name):
                hostname_field = getattr(model_class, field_name)
                break
        
        if not hostname_field:
            logger.warning(f"No hostname field found for {model_class.__name__}, falling back to latest_session")
            return await self._latest_session_strategy(model_class, engagement_id, filters)
        
        # Build query with ranking
        query = select(
            model_class,
            func.row_number().over(
                partition_by=hostname_field,
                order_by=[
                    desc(model_class.flow_id),  # Latest flow first
                    desc(func.length(hostname_field)),  # Longer hostname first
                    desc(model_class.created_at) if hasattr(model_class, 'created_at') else text('1')
                ]
            ).label('rn')
        )
        
        # Apply engagement filter
        if hasattr(model_class, 'engagement_id'):
            query = query.where(model_class.engagement_id == engagement_id)
        
        # Apply additional filters
        if filters:
            for field_name, value in filters.items():
                if hasattr(model_class, field_name):
                    field = getattr(model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
        
        # Wrap in subquery and select only rank 1
        subquery = query.alias('ranked_assets')
        final_query = select(subquery.c).where(subquery.c.rn == 1)
        
        result = await self.db.execute(final_query)
        records = []
        
        # Convert result rows back to model instances
        for row in result:
            instance = model_class()
            for column in model_class.__table__.columns:
                if hasattr(row, column.name):
                    setattr(instance, column.name, getattr(row, column.name))
            records.append(instance)
        
        logger.info(f"Hostname priority deduplication returned {len(records)} records for {model_class.__name__}")
        return records
    
    async def _latest_session_strategy(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Simple deduplication strategy: latest session wins.
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            filters: Optional additional filters
            
        Returns:
            List of deduplicated model instances
        """
        # Find deduplication key
        dedup_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(model_class, field_name):
                dedup_field = getattr(model_class, field_name)
                break
        
        if not dedup_field:
            logger.warning(f"No deduplication field found for {model_class.__name__}")
            # Return all records without deduplication
            query = select(model_class)
            if hasattr(model_class, 'engagement_id'):
                query = query.where(model_class.engagement_id == engagement_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        
        # Subquery to get latest session for each unique asset
        # Use created_at timestamp to determine latest session since UUID max() is not supported
        latest_records_subquery = (
            select(
                dedup_field,
                model_class.flow_id,
                func.row_number().over(
                    partition_by=dedup_field,
                    order_by=desc(model_class.created_at)
                ).label('row_num')
            )
        )
        
        # Apply engagement filter to latest records subquery
        if hasattr(model_class, 'engagement_id'):
            latest_records_subquery = latest_records_subquery.where(model_class.engagement_id == engagement_id)
        
        # Apply additional filters to latest records subquery
        if filters:
            for field_name, value in filters.items():
                if hasattr(model_class, field_name):
                    field = getattr(model_class, field_name)
                    if isinstance(value, list):
                        latest_records_subquery = latest_records_subquery.where(field.in_(value))
                    else:
                        latest_records_subquery = latest_records_subquery.where(field == value)
        
        latest_records_subquery = latest_records_subquery.alias('latest_records')
        
        # Subquery to get only the latest record for each asset (row_num = 1)
        subquery = (
            select(
                latest_records_subquery.c[dedup_field.name],
                latest_records_subquery.c.flow_id.label('latest_flow_id')
            )
            .where(latest_records_subquery.c.row_num == 1)
        )
        
        subquery = subquery.alias('latest_assets')
        
        # Main query to get full records for latest sessions
        query = select(model_class).join(
            subquery,
            and_(
                dedup_field == subquery.c[dedup_field.name],
                model_class.flow_id == subquery.c.latest_flow_id
            )
        )
        
        # Apply engagement filter to main query
        if hasattr(model_class, 'engagement_id'):
            query = query.where(model_class.engagement_id == engagement_id)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        logger.info(f"Latest session deduplication returned {len(records)} records for {model_class.__name__}")
        return records
    
    async def _data_quality_strategy(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Deduplication strategy based on data quality scoring.
        
        Prioritizes records with:
        1. More non-null fields
        2. More complete data
        3. Latest session as tiebreaker
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            filters: Optional additional filters
            
        Returns:
            List of deduplicated model instances
        """
        # Find deduplication key
        dedup_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(model_class, field_name):
                dedup_field = getattr(model_class, field_name)
                break
        
        if not dedup_field:
            return await self._latest_session_strategy(model_class, engagement_id, filters)
        
        # Calculate data quality score (count of non-null fields)
        quality_fields = []
        for column in model_class.__table__.columns:
            if column.name not in ['id', 'created_at', 'updated_at', 'flow_id']:
                quality_fields.append(
                    func.case((getattr(model_class, column.name).is_not(None), 1), else_=0)
                )
        
        quality_score = func.sum(*quality_fields) if quality_fields else text('0')
        
        # Build query with quality ranking
        query = select(
            model_class,
            func.row_number().over(
                partition_by=dedup_field,
                order_by=[
                    desc(quality_score),  # Best quality first
                    desc(model_class.flow_id),  # Latest flow as tiebreaker
                    desc(model_class.created_at) if hasattr(model_class, 'created_at') else text('1')
                ]
            ).label('rn')
        )
        
        # Apply engagement filter
        if hasattr(model_class, 'engagement_id'):
            query = query.where(model_class.engagement_id == engagement_id)
        
        # Apply additional filters
        if filters:
            for field_name, value in filters.items():
                if hasattr(model_class, field_name):
                    field = getattr(model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
        
        # Wrap in subquery and select only rank 1
        subquery = query.alias('quality_ranked_assets')
        final_query = select(subquery.c).where(subquery.c.rn == 1)
        
        result = await self.db.execute(final_query)
        records = []
        
        # Convert result rows back to model instances
        for row in result:
            instance = model_class()
            for column in model_class.__table__.columns:
                if hasattr(row, column.name):
                    setattr(instance, column.name, getattr(row, column.name))
            records.append(instance)
        
        logger.info(f"Data quality deduplication returned {len(records)} records for {model_class.__name__}")
        return records
    
    async def _agent_assisted_strategy(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        CrewAI agent-assisted deduplication strategy.
        
        Uses AI agents to make intelligent deduplication decisions
        based on data patterns and business context.
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            filters: Optional additional filters
            
        Returns:
            List of deduplicated model instances
        """
        # For now, fall back to data quality strategy
        # Use MasterFlowOrchestrator for intelligent deduplication
        logger.info("Agent-assisted deduplication not yet implemented, using data quality strategy")
        return await self._data_quality_strategy(model_class, engagement_id, filters)
    
    async def get_duplicate_groups(
        self,
        model_class: Type[ModelType],
        engagement_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[ModelType]]:
        """
        Get groups of duplicate records for analysis.
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            filters: Optional additional filters
            
        Returns:
            Dictionary mapping deduplication keys to lists of duplicate records
        """
        # Find deduplication key
        dedup_field = None
        for field_name in ['hostname', 'name', 'asset_name', 'identifier']:
            if hasattr(model_class, field_name):
                dedup_field = getattr(model_class, field_name)
                break
        
        if not dedup_field:
            return {}
        
        # Query for all records
        query = select(model_class)
        
        # Apply engagement filter
        if hasattr(model_class, 'engagement_id'):
            query = query.where(model_class.engagement_id == engagement_id)
        
        # Apply additional filters
        if filters:
            for field_name, value in filters.items():
                if hasattr(model_class, field_name):
                    field = getattr(model_class, field_name)
                    if isinstance(value, list):
                        query = query.where(field.in_(value))
                    else:
                        query = query.where(field == value)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        # Group by deduplication key
        duplicate_groups = {}
        for record in records:
            key = getattr(record, dedup_field.name)
            if key not in duplicate_groups:
                duplicate_groups[key] = []
            duplicate_groups[key].append(record)
        
        # Filter to only groups with duplicates
        duplicate_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups for {model_class.__name__}")
        return duplicate_groups
    
    async def get_deduplication_stats(
        self,
        model_class: Type[ModelType],
        engagement_id: str
    ) -> Dict[str, Any]:
        """
        Get deduplication statistics for an engagement.
        
        Args:
            model_class: SQLAlchemy model class
            engagement_id: Engagement ID for scoping
            
        Returns:
            Dictionary with deduplication statistics
        """
        # Total records
        total_query = select(func.count(model_class.id))
        if hasattr(model_class, 'engagement_id'):
            total_query = total_query.where(model_class.engagement_id == engagement_id)
        
        total_result = await self.db.execute(total_query)
        total_records = total_result.scalar()
        
        # Deduplicated records
        deduplicated_records = await self.deduplicate_assets(
            model_class, engagement_id, strategy='latest_session'
        )
        deduplicated_count = len(deduplicated_records)
        
        # Duplicate groups
        duplicate_groups = await self.get_duplicate_groups(model_class, engagement_id)
        duplicate_count = sum(len(group) - 1 for group in duplicate_groups.values())
        
        # Sessions count
        sessions_query = select(func.count(func.distinct(model_class.flow_id)))
        if hasattr(model_class, 'engagement_id'):
            sessions_query = sessions_query.where(model_class.engagement_id == engagement_id)
        
        sessions_result = await self.db.execute(sessions_query)
        sessions_count = sessions_result.scalar()
        
        return {
            'total_records': total_records,
            'deduplicated_records': deduplicated_count,
            'duplicate_records': duplicate_count,
            'duplicate_groups': len(duplicate_groups),
            'sessions_count': sessions_count,
            'deduplication_ratio': deduplicated_count / total_records if total_records > 0 else 0,
            'duplicate_percentage': (duplicate_count / total_records * 100) if total_records > 0 else 0
        } 