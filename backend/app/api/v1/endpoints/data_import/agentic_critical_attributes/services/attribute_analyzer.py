"""
Core attribute analysis service containing business logic.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.context import RequestContext
from app.models.data_import import DataImport, RawImportRecord
from ..models.attribute_schemas import (
    CriticalAttribute, AttributeSuggestion, AnalysisStatistics,
    AttributeAnalysisRequest, AttributeAnalysisResponse
)
from .agent_coordinator import AgentCoordinator

logger = logging.getLogger(__name__)


class AttributeAnalyzer:
    """Service for analyzing critical attributes using AI agents."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.agent_coordinator = AgentCoordinator(db, context)
        self._analysis_cache = {}
    
    async def analyze_critical_attributes(
        self, 
        request: AttributeAnalysisRequest
    ) -> AttributeAnalysisResponse:
        """
        Analyze critical attributes for migration using AI agents.
        
        This is the main entry point for attribute analysis that coordinates
        between CrewAI agents and fallback analysis.
        """
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())
        
        logger.info(f"🤖 Starting critical attributes analysis {analysis_id}")
        
        try:
            # Get the data import to analyze
            data_import = await self._get_target_import(request)
            if not data_import:
                return self._create_no_data_response(analysis_id, start_time)
            
            # Check for cached results if not forcing reanalysis
            if not request.force_reanalysis:
                cached_result = await self._get_cached_analysis(data_import.id)
                if cached_result:
                    logger.info(f"📊 Returning cached analysis for import {data_import.id}")
                    cached_result.analysis_id = analysis_id
                    cached_result.cache_hit = True
                    return cached_result
            
            # Get sample data for analysis
            sample_data = await self._get_sample_data(data_import)
            if not sample_data:
                return self._create_no_data_response(analysis_id, start_time)
            
            # Execute analysis based on request parameters
            if request.include_crew_analysis:
                # Use CrewAI agents for analysis
                analysis_result = await self.agent_coordinator.execute_crew_analysis(
                    data_import, sample_data, request.analysis_depth
                )
                execution_mode = "crew_ai"
            else:
                # Use fallback analysis
                analysis_result = await self._execute_fallback_analysis(data_import, sample_data)
                execution_mode = "fallback"
            
            # Process results into standardized format
            attributes = self._extract_critical_attributes(analysis_result)
            suggestions = self._extract_suggestions(analysis_result)
            statistics = self._calculate_statistics(attributes, suggestions, start_time)
            
            # Create response
            response = AttributeAnalysisResponse(
                success=True,
                analysis_id=analysis_id,
                attributes=attributes,
                suggestions=suggestions,
                statistics=statistics,
                execution_mode=execution_mode,
                cache_hit=False,
                timestamp=datetime.utcnow(),
                context={
                    "import_id": data_import.id,
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id,
                    "sample_records": len(sample_data)
                }
            )
            
            # Cache the results for future requests
            await self._cache_analysis_result(data_import.id, response)
            
            logger.info(f"✅ Analysis {analysis_id} completed in {statistics.analysis_duration_seconds:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ Analysis {analysis_id} failed: {e}")
            return self._create_error_response(analysis_id, start_time, str(e))
    
    async def _get_target_import(self, request: AttributeAnalysisRequest) -> Optional[DataImport]:
        """Get the data import to analyze based on request parameters."""
        
        if request.import_id:
            # Use specific import ID
            query = select(DataImport).where(
                and_(
                    DataImport.id == request.import_id,
                    DataImport.client_account_id == self.context.client_account_id
                )
            )
        else:
            # Use latest import for the engagement
            query = select(DataImport).where(
                and_(
                    DataImport.client_account_id == self.context.client_account_id,
                    DataImport.engagement_id == self.context.engagement_id,
                    DataImport.status.in_(['processed', 'completed'])
                )
            ).order_by(DataImport.completed_at.desc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_sample_data(self, data_import: DataImport) -> List[Dict[str, Any]]:
        """Get sample data from the import for analysis."""
        
        query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import.id
        ).limit(10)  # Get first 10 records for analysis
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        sample_data = []
        for record in records:
            if record.raw_data:
                sample_data.append(record.raw_data)
        
        return sample_data
    
    async def _execute_fallback_analysis(
        self, 
        data_import: DataImport, 
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute fallback analysis when CrewAI is not available."""
        
        if not sample_data:
            return {"analysis_result": "no_data", "attributes": [], "suggestions": []}
        
        field_names = list(sample_data[0].keys())
        
        logger.info(f"🔄 Executing fallback analysis for {len(field_names)} fields")
        
        # Analyze each field using pattern matching
        attributes = []
        suggestions = []
        
        for field_name in field_names:
            # Extract sample values for this field
            field_values = [record.get(field_name) for record in sample_data[:5]]
            field_values = [v for v in field_values if v is not None]
            
            # Analyze field importance using heuristics
            importance = self._calculate_field_importance(field_name, field_values)
            
            if importance > 0.5:  # Only include significant fields
                attribute = {
                    "name": field_name,
                    "importance": importance,
                    "confidence": 0.6,  # Lower confidence for fallback
                    "reasoning": f"Pattern-based analysis identified '{field_name}' as potentially critical",
                    "migration_impact": self._assess_migration_impact(field_name),
                    "data_type": self._infer_data_type(field_values),
                    "sample_values": [str(v) for v in field_values[:3]],
                    "mapping_suggestions": self._suggest_target_mappings(field_name),
                    "agent_source": "fallback_analyzer"
                }
                attributes.append(attribute)
                
                # Create suggestion
                suggestion = {
                    "source_field": field_name,
                    "suggested_target": self._suggest_primary_target(field_name),
                    "importance_score": importance,
                    "confidence_score": 0.6,
                    "reasoning": f"Fallback pattern matching for {field_name}",
                    "migration_priority": self._calculate_migration_priority(importance)
                }
                suggestions.append(suggestion)
        
        return {
            "analysis_result": "fallback_completed",
            "attributes": attributes,
            "suggestions": suggestions,
            "execution_mode": "fallback"
        }
    
    def _calculate_field_importance(self, field_name: str, values: List[Any]) -> float:
        """Calculate field importance using pattern matching."""
        
        field_lower = field_name.lower()
        importance = 0.0
        
        # High importance patterns
        if any(pattern in field_lower for pattern in ['id', 'name', 'hostname', 'ip']):
            importance += 0.4
        
        # Medium importance patterns  
        if any(pattern in field_lower for pattern in ['type', 'os', 'env', 'cpu', 'memory']):
            importance += 0.3
        
        # Business importance
        if any(pattern in field_lower for pattern in ['owner', 'dept', 'critical', 'app']):
            importance += 0.2
        
        # Data quality boost
        if values:
            non_null_ratio = len([v for v in values if v]) / len(values)
            unique_ratio = len(set(values)) / len(values) if values else 0
            importance += min(0.3, non_null_ratio * 0.2 + unique_ratio * 0.1)
        
        return min(1.0, importance)
    
    def _assess_migration_impact(self, field_name: str) -> str:
        """Assess migration impact for a field."""
        field_lower = field_name.lower()
        
        if any(pattern in field_lower for pattern in ['id', 'name', 'hostname']):
            return "High - Critical for asset identification"
        elif any(pattern in field_lower for pattern in ['type', 'os', 'env']):
            return "Medium - Important for migration planning"
        elif any(pattern in field_lower for pattern in ['cpu', 'memory', 'storage']):
            return "Medium - Needed for capacity planning"
        else:
            return "Low - Supplementary information"
    
    def _infer_data_type(self, values: List[Any]) -> str:
        """Infer data type from sample values."""
        if not values:
            return "unknown"
        
        if all(isinstance(v, (int, float)) for v in values):
            return "numeric"
        elif all(isinstance(v, str) for v in values):
            return "string"
        else:
            return "mixed"
    
    def _suggest_target_mappings(self, field_name: str) -> List[str]:
        """Suggest target field mappings."""
        field_lower = field_name.lower()
        
        mapping_patterns = {
            'id': ['asset_id', 'name'],
            'name': ['name', 'asset_name', 'hostname'],
            'hostname': ['hostname', 'name'],
            'ip': ['ip_address'],
            'type': ['asset_type'],
            'os': ['operating_system'],
            'env': ['environment'],
            'cpu': ['cpu_cores'],
            'memory': ['memory_gb'],
            'storage': ['storage_gb']
        }
        
        for pattern, targets in mapping_patterns.items():
            if pattern in field_lower:
                return targets
        
        return ['name']  # Default fallback
    
    def _suggest_primary_target(self, field_name: str) -> str:
        """Suggest primary target field mapping."""
        suggestions = self._suggest_target_mappings(field_name)
        return suggestions[0] if suggestions else 'name'
    
    def _calculate_migration_priority(self, importance: float) -> int:
        """Calculate migration priority (1-10) based on importance."""
        if importance >= 0.8:
            return 9
        elif importance >= 0.6:
            return 7
        elif importance >= 0.4:
            return 5
        else:
            return 3
    
    def _extract_critical_attributes(self, analysis_result: Dict[str, Any]) -> List[CriticalAttribute]:
        """Extract critical attributes from analysis results."""
        attributes_data = analysis_result.get("attributes", [])
        
        attributes = []
        for attr_data in attributes_data:
            try:
                attribute = CriticalAttribute(
                    name=attr_data["name"],
                    importance=attr_data["importance"],
                    confidence=attr_data["confidence"],
                    reasoning=attr_data["reasoning"],
                    migration_impact=attr_data["migration_impact"],
                    data_type=attr_data["data_type"],
                    sample_values=attr_data.get("sample_values", []),
                    mapping_suggestions=attr_data.get("mapping_suggestions", []),
                    validation_rules=attr_data.get("validation_rules"),
                    agent_source=attr_data["agent_source"]
                )
                attributes.append(attribute)
            except Exception as e:
                logger.warning(f"Failed to parse attribute {attr_data.get('name', 'unknown')}: {e}")
        
        return attributes
    
    def _extract_suggestions(self, analysis_result: Dict[str, Any]) -> List[AttributeSuggestion]:
        """Extract suggestions from analysis results."""
        suggestions_data = analysis_result.get("suggestions", [])
        
        suggestions = []
        for sugg_data in suggestions_data:
            try:
                suggestion = AttributeSuggestion(
                    source_field=sugg_data["source_field"],
                    suggested_target=sugg_data["suggested_target"],
                    importance_score=sugg_data["importance_score"],
                    confidence_score=sugg_data["confidence_score"],
                    reasoning=sugg_data["reasoning"],
                    crew_analysis=sugg_data.get("crew_analysis"),
                    migration_priority=sugg_data.get("migration_priority", 5)
                )
                suggestions.append(suggestion)
            except Exception as e:
                logger.warning(f"Failed to parse suggestion for {sugg_data.get('source_field', 'unknown')}: {e}")
        
        return suggestions
    
    def _calculate_statistics(
        self, 
        attributes: List[CriticalAttribute], 
        suggestions: List[AttributeSuggestion],
        start_time: datetime
    ) -> AnalysisStatistics:
        """Calculate analysis statistics."""
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Categorize attributes by importance
        high_importance = len([a for a in attributes if a.importance >= 0.8])
        medium_importance = len([a for a in attributes if 0.5 <= a.importance < 0.8])
        low_importance = len([a for a in attributes if a.importance < 0.5])
        
        # Calculate average confidence
        if attributes:
            avg_confidence = sum(a.confidence for a in attributes) / len(attributes)
        else:
            avg_confidence = 0.0
        
        return AnalysisStatistics(
            total_attributes=len(attributes),
            critical_count=high_importance,
            high_importance_count=high_importance,
            medium_importance_count=medium_importance,
            low_importance_count=low_importance,
            mapped_count=len(suggestions),
            unmapped_count=len(attributes) - len(suggestions),
            average_confidence=avg_confidence,
            analysis_duration_seconds=duration
        )
    
    async def _get_cached_analysis(self, import_id: str) -> Optional[AttributeAnalysisResponse]:
        """Get cached analysis result if available."""
        return self._analysis_cache.get(import_id)
    
    async def _cache_analysis_result(self, import_id: str, response: AttributeAnalysisResponse):
        """Cache analysis result for future requests."""
        # Simple in-memory cache - in production, use Redis or database
        self._analysis_cache[import_id] = response
    
    def _create_no_data_response(self, analysis_id: str, start_time: datetime) -> AttributeAnalysisResponse:
        """Create response for when no data is available."""
        return AttributeAnalysisResponse(
            success=False,
            analysis_id=analysis_id,
            attributes=[],
            suggestions=[],
            statistics=AnalysisStatistics(
                total_attributes=0,
                critical_count=0,
                high_importance_count=0,
                medium_importance_count=0,
                low_importance_count=0,
                mapped_count=0,
                unmapped_count=0,
                average_confidence=0.0,
                analysis_duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            ),
            execution_mode="no_data",
            timestamp=datetime.utcnow()
        )
    
    def _create_error_response(self, analysis_id: str, start_time: datetime, error: str) -> AttributeAnalysisResponse:
        """Create error response."""
        return AttributeAnalysisResponse(
            success=False,
            analysis_id=analysis_id,
            attributes=[],
            suggestions=[],
            statistics=AnalysisStatistics(
                total_attributes=0,
                critical_count=0,
                high_importance_count=0,
                medium_importance_count=0,
                low_importance_count=0,
                mapped_count=0,
                unmapped_count=0,
                average_confidence=0.0,
                analysis_duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            ),
            execution_mode="error",
            timestamp=datetime.utcnow(),
            context={"error": error}
        )