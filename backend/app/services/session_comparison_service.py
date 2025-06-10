"""
Session Comparison Service for "what-if" scenario analysis.
Enables session-to-session comparison with comprehensive metrics and diff visualization.
"""

from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, desc, text
from sqlalchemy.future import select
from sqlalchemy.sql import Select
import logging
from datetime import datetime, timezone
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from app.models.data_import_session import DataImportSession
    from app.models.asset import Asset
    from app.models.raw_import_record import RawImportRecord
    from app.repositories.deduplicating_repository import DeduplicatingRepository
    from app.core.context import get_current_context
    SESSION_MODELS_AVAILABLE = True
except ImportError:
    SESSION_MODELS_AVAILABLE = False
    DataImportSession = Asset = RawImportRecord = DeduplicatingRepository = None

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType')


class ComparisonType(str, Enum):
    """Types of session comparisons."""
    FULL_COMPARISON = "full_comparison"
    METRICS_ONLY = "metrics_only"
    ASSETS_DIFF = "assets_diff"
    QUALITY_ANALYSIS = "quality_analysis"
    BUSINESS_IMPACT = "business_impact"


class DiffType(str, Enum):
    """Types of differences between sessions."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class SessionSnapshot:
    """Comprehensive session snapshot for comparison."""
    session_id: str
    session_name: str
    created_at: str
    status: str
    
    # Core Metrics
    total_assets: int
    unique_assets: int
    duplicate_assets: int
    quality_score: float
    completeness_score: float
    
    # Asset Breakdown
    assets_by_type: Dict[str, int]
    assets_by_department: Dict[str, int]
    assets_by_status: Dict[str, int]
    
    # Data Quality Metrics
    data_quality_issues: List[Dict[str, Any]]
    validation_errors: int
    missing_critical_fields: int
    data_consistency_score: float
    
    # Business Metrics
    estimated_cost_savings: float
    migration_complexity_score: float
    business_criticality_distribution: Dict[str, int]
    risk_score: float
    
    # Technical Metrics
    technologies_detected: List[str]
    dependencies_mapped: int
    integration_complexity: float
    modernization_potential: float
    
    # Agent Intelligence
    agent_confidence_score: float
    classification_accuracy: float
    recommendations_count: int
    learning_insights: List[Dict[str, Any]]
    
    # Processing Information
    processing_time_seconds: float
    data_source_count: int
    import_method: str
    errors_encountered: int


@dataclass
class SessionDiff:
    """Difference analysis between two sessions."""
    source_session_id: str
    target_session_id: str
    comparison_type: ComparisonType
    generated_at: str
    
    # Metrics Differences
    metrics_diff: Dict[str, Dict[str, Any]]  # metric_name -> {source_value, target_value, diff, percentage_change}
    
    # Asset Differences
    assets_added: List[Dict[str, Any]]
    assets_removed: List[Dict[str, Any]]
    assets_modified: List[Dict[str, Any]]
    assets_unchanged: List[Dict[str, Any]]
    
    # Quality Impact
    quality_improvements: List[Dict[str, Any]]
    quality_regressions: List[Dict[str, Any]]
    
    # Business Impact Analysis
    cost_impact: Dict[str, Any]
    risk_impact: Dict[str, Any]
    complexity_impact: Dict[str, Any]
    
    # Summary Statistics
    summary: Dict[str, Any]


class SessionComparisonService:
    """
    Service for comprehensive session comparison and "what-if" analysis.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize session comparison service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    async def create_session_snapshot(
        self,
        session_id: str,
        include_assets: bool = True
    ) -> SessionSnapshot:
        """
        Create comprehensive snapshot of a session for comparison.
        
        Args:
            session_id: Session ID to snapshot
            include_assets: Whether to include detailed asset data
            
        Returns:
            SessionSnapshot object with all comparison metrics
        """
        if not SESSION_MODELS_AVAILABLE:
            logger.warning("Session models not available, using mock snapshot")
            return self._create_mock_snapshot(session_id)
        
        # Get session details
        session_query = select(DataImportSession).where(DataImportSession.id == session_id)
        session_result = await self.db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create session-aware repository for assets
        asset_repo = DeduplicatingRepository(
            db=self.db,
            model_class=Asset,
            client_account_id=session.client_account_id,
            engagement_id=session.engagement_id,
            session_id=session_id
        )
        
        # Get all assets for this session
        assets = await asset_repo.get_all() if include_assets else []
        
        # Calculate core metrics
        total_assets = len(assets)
        unique_assets = len(set(getattr(asset, 'hostname', f'asset_{asset.id}') for asset in assets))
        duplicate_assets = total_assets - unique_assets
        
        # Calculate quality scores
        quality_score = await self._calculate_quality_score(assets)
        completeness_score = await self._calculate_completeness_score(assets)
        
        # Asset breakdowns
        assets_by_type = await self._get_assets_by_type(assets)
        assets_by_department = await self._get_assets_by_department(assets)
        assets_by_status = await self._get_assets_by_status(assets)
        
        # Data quality analysis
        data_quality_issues = await self._analyze_data_quality_issues(assets)
        validation_errors = len([issue for issue in data_quality_issues if issue.get('severity') == 'error'])
        missing_critical_fields = await self._count_missing_critical_fields(assets)
        data_consistency_score = await self._calculate_data_consistency(assets)
        
        # Business metrics (calculated from session metadata and agent insights)
        estimated_cost_savings = session.metadata.get('estimated_cost_savings', 0.0) if session.metadata else 0.0
        migration_complexity_score = await self._calculate_migration_complexity(assets)
        business_criticality_distribution = await self._get_business_criticality_distribution(assets)
        risk_score = await self._calculate_risk_score(assets, session)
        
        # Technical metrics
        technologies_detected = await self._detect_technologies(assets)
        dependencies_mapped = await self._count_dependencies(assets)
        integration_complexity = await self._calculate_integration_complexity(assets)
        modernization_potential = await self._calculate_modernization_potential(assets)
        
        # Agent intelligence metrics
        agent_confidence_score = session.agent_insights.get('classification_confidence', 0.0) if session.agent_insights else 0.0
        classification_accuracy = await self._calculate_classification_accuracy(assets)
        recommendations_count = len(session.agent_insights.get('recommendations', [])) if session.agent_insights else 0
        learning_insights = session.agent_insights.get('learning_outcomes', []) if session.agent_insights else []
        
        # Processing information
        processing_time = (session.completed_at - session.started_at).total_seconds() if session.completed_at else 0.0
        data_source_count = len(session.metadata.get('data_sources', [])) if session.metadata else 1
        import_method = session.metadata.get('import_method', 'unknown') if session.metadata else 'unknown'
        errors_encountered = len(session.agent_insights.get('data_quality_issues', [])) if session.agent_insights else 0
        
        return SessionSnapshot(
            session_id=session_id,
            session_name=session.name,
            created_at=session.created_at.isoformat(),
            status=session.status,
            total_assets=total_assets,
            unique_assets=unique_assets,
            duplicate_assets=duplicate_assets,
            quality_score=quality_score,
            completeness_score=completeness_score,
            assets_by_type=assets_by_type,
            assets_by_department=assets_by_department,
            assets_by_status=assets_by_status,
            data_quality_issues=data_quality_issues,
            validation_errors=validation_errors,
            missing_critical_fields=missing_critical_fields,
            data_consistency_score=data_consistency_score,
            estimated_cost_savings=estimated_cost_savings,
            migration_complexity_score=migration_complexity_score,
            business_criticality_distribution=business_criticality_distribution,
            risk_score=risk_score,
            technologies_detected=technologies_detected,
            dependencies_mapped=dependencies_mapped,
            integration_complexity=integration_complexity,
            modernization_potential=modernization_potential,
            agent_confidence_score=agent_confidence_score,
            classification_accuracy=classification_accuracy,
            recommendations_count=recommendations_count,
            learning_insights=learning_insights,
            processing_time_seconds=processing_time,
            data_source_count=data_source_count,
            import_method=import_method,
            errors_encountered=errors_encountered
        )
    
    async def compare_sessions(
        self,
        source_session_id: str,
        target_session_id: str,
        comparison_type: ComparisonType = ComparisonType.FULL_COMPARISON
    ) -> SessionDiff:
        """
        Compare two sessions and generate comprehensive diff analysis.
        
        Args:
            source_session_id: First session for comparison
            target_session_id: Second session for comparison
            comparison_type: Type of comparison to perform
            
        Returns:
            SessionDiff object with detailed comparison results
        """
        # Create snapshots of both sessions
        source_snapshot = await self.create_session_snapshot(source_session_id)
        target_snapshot = await self.create_session_snapshot(target_session_id)
        
        # Calculate metrics differences
        metrics_diff = self._compare_metrics(source_snapshot, target_snapshot)
        
        # Asset-level comparison
        assets_diff = await self._compare_assets(source_session_id, target_session_id)
        
        # Quality impact analysis
        quality_impact = self._analyze_quality_impact(source_snapshot, target_snapshot)
        
        # Business impact analysis
        business_impact = self._analyze_business_impact(source_snapshot, target_snapshot)
        
        # Generate summary
        summary = self._generate_comparison_summary(source_snapshot, target_snapshot, metrics_diff)
        
        return SessionDiff(
            source_session_id=source_session_id,
            target_session_id=target_session_id,
            comparison_type=comparison_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
            metrics_diff=metrics_diff,
            assets_added=assets_diff['added'],
            assets_removed=assets_diff['removed'],
            assets_modified=assets_diff['modified'],
            assets_unchanged=assets_diff['unchanged'],
            quality_improvements=quality_impact['improvements'],
            quality_regressions=quality_impact['regressions'],
            cost_impact=business_impact['cost'],
            risk_impact=business_impact['risk'],
            complexity_impact=business_impact['complexity'],
            summary=summary
        )
    
    async def get_session_comparison_history(
        self,
        engagement_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get history of session comparisons for an engagement.
        
        Args:
            engagement_id: Engagement ID to get comparison history for
            limit: Maximum number of comparisons to return
            
        Returns:
            List of comparison history records
        """
        # For now, return mock history
        # In production, this would query a session_comparisons table
        return [
            {
                "id": "comp_001",
                "source_session_name": "Initial Discovery",
                "target_session_name": "Updated Discovery",
                "created_at": "2024-06-01T10:30:00Z",
                "created_by": "john.smith@company.com",
                "comparison_type": "full_comparison",
                "key_findings": [
                    "15% improvement in data quality",
                    "12 new assets discovered",
                    "3 duplicates resolved"
                ]
            },
            {
                "id": "comp_002",
                "source_session_name": "Updated Discovery",
                "target_session_name": "Final Assessment",
                "created_at": "2024-06-02T14:45:00Z",
                "created_by": "sarah.wilson@company.com",
                "comparison_type": "metrics_only",
                "key_findings": [
                    "Risk score reduced by 8%",
                    "Migration complexity optimized",
                    "Cost savings increased by $125K"
                ]
            }
        ]
    
    def _compare_metrics(self, source: SessionSnapshot, target: SessionSnapshot) -> Dict[str, Dict[str, Any]]:
        """Compare metrics between two session snapshots."""
        metrics_to_compare = [
            'total_assets', 'unique_assets', 'duplicate_assets', 'quality_score',
            'completeness_score', 'validation_errors', 'missing_critical_fields',
            'data_consistency_score', 'estimated_cost_savings', 'migration_complexity_score',
            'risk_score', 'dependencies_mapped', 'integration_complexity',
            'modernization_potential', 'agent_confidence_score', 'classification_accuracy',
            'recommendations_count', 'processing_time_seconds', 'errors_encountered'
        ]
        
        diff = {}
        for metric in metrics_to_compare:
            source_value = getattr(source, metric, 0)
            target_value = getattr(target, metric, 0)
            
            if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
                raw_diff = target_value - source_value
                percentage_change = (raw_diff / source_value * 100) if source_value != 0 else 0
                
                diff[metric] = {
                    'source_value': source_value,
                    'target_value': target_value,
                    'difference': raw_diff,
                    'percentage_change': round(percentage_change, 2),
                    'improvement': raw_diff > 0 if metric in ['quality_score', 'completeness_score', 'estimated_cost_savings'] else raw_diff < 0
                }
        
        return diff
    
    async def _compare_assets(self, source_session_id: str, target_session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Compare assets between two sessions."""
        if not SESSION_MODELS_AVAILABLE:
            return {
                'added': [],
                'removed': [],
                'modified': [],
                'unchanged': []
            }
        
        # Get assets from both sessions
        source_assets = await self._get_session_assets(source_session_id)
        target_assets = await self._get_session_assets(target_session_id)
        
        # Create lookup dictionaries by hostname
        source_lookup = {getattr(asset, 'hostname', f'asset_{asset.id}'): asset for asset in source_assets}
        target_lookup = {getattr(asset, 'hostname', f'asset_{asset.id}'): asset for asset in target_assets}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        # Find added assets (in target but not in source)
        for hostname, asset in target_lookup.items():
            if hostname not in source_lookup:
                added.append(self._asset_to_dict(asset))
        
        # Find removed assets (in source but not in target)
        for hostname, asset in source_lookup.items():
            if hostname not in target_lookup:
                removed.append(self._asset_to_dict(asset))
        
        # Find modified and unchanged assets
        for hostname in set(source_lookup.keys()) & set(target_lookup.keys()):
            source_asset = source_lookup[hostname]
            target_asset = target_lookup[hostname]
            
            if self._assets_are_different(source_asset, target_asset):
                modified.append({
                    'hostname': hostname,
                    'source': self._asset_to_dict(source_asset),
                    'target': self._asset_to_dict(target_asset),
                    'changes': self._get_asset_changes(source_asset, target_asset)
                })
            else:
                unchanged.append(self._asset_to_dict(source_asset))
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': unchanged
        }
    
    def _analyze_quality_impact(self, source: SessionSnapshot, target: SessionSnapshot) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze quality improvements and regressions between sessions."""
        improvements = []
        regressions = []
        
        # Quality score comparison
        if target.quality_score > source.quality_score:
            improvements.append({
                'metric': 'Overall Quality Score',
                'improvement': target.quality_score - source.quality_score,
                'description': f"Quality improved by {target.quality_score - source.quality_score:.2f} points"
            })
        elif target.quality_score < source.quality_score:
            regressions.append({
                'metric': 'Overall Quality Score',
                'regression': source.quality_score - target.quality_score,
                'description': f"Quality decreased by {source.quality_score - target.quality_score:.2f} points"
            })
        
        # Validation errors comparison
        if target.validation_errors < source.validation_errors:
            improvements.append({
                'metric': 'Validation Errors',
                'improvement': source.validation_errors - target.validation_errors,
                'description': f"Reduced validation errors by {source.validation_errors - target.validation_errors}"
            })
        elif target.validation_errors > source.validation_errors:
            regressions.append({
                'metric': 'Validation Errors',
                'regression': target.validation_errors - source.validation_errors,
                'description': f"Increased validation errors by {target.validation_errors - source.validation_errors}"
            })
        
        return {
            'improvements': improvements,
            'regressions': regressions
        }
    
    def _analyze_business_impact(self, source: SessionSnapshot, target: SessionSnapshot) -> Dict[str, Dict[str, Any]]:
        """Analyze business impact of session changes."""
        return {
            'cost': {
                'savings_change': target.estimated_cost_savings - source.estimated_cost_savings,
                'description': f"Cost savings {'increased' if target.estimated_cost_savings > source.estimated_cost_savings else 'decreased'} by ${abs(target.estimated_cost_savings - source.estimated_cost_savings):,.2f}"
            },
            'risk': {
                'risk_change': target.risk_score - source.risk_score,
                'description': f"Risk score {'increased' if target.risk_score > source.risk_score else 'decreased'} by {abs(target.risk_score - source.risk_score):.2f} points"
            },
            'complexity': {
                'complexity_change': target.migration_complexity_score - source.migration_complexity_score,
                'description': f"Migration complexity {'increased' if target.migration_complexity_score > source.migration_complexity_score else 'decreased'} by {abs(target.migration_complexity_score - source.migration_complexity_score):.2f} points"
            }
        }
    
    def _generate_comparison_summary(self, source: SessionSnapshot, target: SessionSnapshot, metrics_diff: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate high-level summary of session comparison."""
        significant_changes = []
        
        for metric, diff_data in metrics_diff.items():
            if abs(diff_data['percentage_change']) >= 5:  # 5% threshold for significance
                significant_changes.append({
                    'metric': metric.replace('_', ' ').title(),
                    'change': diff_data['percentage_change'],
                    'direction': 'improvement' if diff_data.get('improvement', False) else 'regression'
                })
        
        return {
            'total_metrics_compared': len(metrics_diff),
            'significant_changes': significant_changes,
            'overall_improvement': len([c for c in significant_changes if c['direction'] == 'improvement']),
            'overall_regression': len([c for c in significant_changes if c['direction'] == 'regression']),
            'source_session': source.session_name,
            'target_session': target.session_name,
            'comparison_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    # Helper methods for calculations
    async def _calculate_quality_score(self, assets: List[Any]) -> float:
        """Calculate overall data quality score for assets."""
        if not assets:
            return 0.0
        
        total_score = 0.0
        for asset in assets:
            # Simple quality calculation based on field completeness
            fields_with_data = sum(1 for field in ['hostname', 'os_type', 'application', 'department'] 
                                 if hasattr(asset, field) and getattr(asset, field))
            total_fields = 4
            asset_score = (fields_with_data / total_fields) * 100
            total_score += asset_score
        
        return round(total_score / len(assets), 2)
    
    async def _calculate_completeness_score(self, assets: List[Any]) -> float:
        """Calculate data completeness score."""
        if not assets:
            return 0.0
        
        # Count non-null critical fields across all assets
        critical_fields = ['hostname', 'asset_type', 'status']
        total_possible = len(assets) * len(critical_fields)
        total_complete = 0
        
        for asset in assets:
            for field in critical_fields:
                if hasattr(asset, field) and getattr(asset, field):
                    total_complete += 1
        
        return round((total_complete / total_possible) * 100, 2) if total_possible > 0 else 0.0
    
    async def _get_assets_by_type(self, assets: List[Any]) -> Dict[str, int]:
        """Get asset distribution by type."""
        type_counts = {}
        for asset in assets:
            asset_type = getattr(asset, 'asset_type', 'Unknown')
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        return type_counts
    
    async def _get_assets_by_department(self, assets: List[Any]) -> Dict[str, int]:
        """Get asset distribution by department."""
        dept_counts = {}
        for asset in assets:
            department = getattr(asset, 'department', 'Unknown')
            dept_counts[department] = dept_counts.get(department, 0) + 1
        return dept_counts
    
    async def _get_assets_by_status(self, assets: List[Any]) -> Dict[str, int]:
        """Get asset distribution by status."""
        status_counts = {}
        for asset in assets:
            status = getattr(asset, 'status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts
    
    async def _analyze_data_quality_issues(self, assets: List[Any]) -> List[Dict[str, Any]]:
        """Analyze data quality issues in assets."""
        issues = []
        for asset in assets:
            if not getattr(asset, 'hostname', None):
                issues.append({
                    'asset_id': getattr(asset, 'id', 'unknown'),
                    'issue_type': 'missing_hostname',
                    'severity': 'error',
                    'description': 'Asset missing hostname identifier'
                })
        return issues
    
    async def _count_missing_critical_fields(self, assets: List[Any]) -> int:
        """Count assets with missing critical fields."""
        critical_fields = ['hostname', 'asset_type']
        missing_count = 0
        
        for asset in assets:
            for field in critical_fields:
                if not getattr(asset, field, None):
                    missing_count += 1
                    break
        
        return missing_count
    
    async def _calculate_data_consistency(self, assets: List[Any]) -> float:
        """Calculate data consistency score."""
        # Simple consistency check - assets with consistent naming patterns
        if not assets:
            return 100.0
        
        hostnames = [getattr(asset, 'hostname', '') for asset in assets if getattr(asset, 'hostname', None)]
        if not hostnames:
            return 0.0
        
        # Check for consistent naming patterns (simplified)
        consistent_count = len([h for h in hostnames if h and len(h) > 3])
        return round((consistent_count / len(hostnames)) * 100, 2)
    
    async def _calculate_migration_complexity(self, assets: List[Any]) -> float:
        """Calculate migration complexity score."""
        if not assets:
            return 0.0
        
        # Simple complexity based on asset types and dependencies
        complexity_weights = {
            'database': 3.0,
            'application_server': 2.5,
            'web_server': 2.0,
            'desktop': 1.0,
            'unknown': 1.5
        }
        
        total_complexity = 0.0
        for asset in assets:
            asset_type = getattr(asset, 'asset_type', 'unknown').lower()
            weight = complexity_weights.get(asset_type, 1.5)
            total_complexity += weight
        
        return round(total_complexity / len(assets), 2)
    
    async def _get_business_criticality_distribution(self, assets: List[Any]) -> Dict[str, int]:
        """Get distribution of business criticality levels."""
        criticality_counts = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        
        for asset in assets:
            criticality = getattr(asset, 'business_criticality', 'unknown').lower()
            if criticality in criticality_counts:
                criticality_counts[criticality] += 1
            else:
                criticality_counts['unknown'] += 1
        
        return criticality_counts
    
    async def _calculate_risk_score(self, assets: List[Any], session: Any) -> float:
        """Calculate overall risk score."""
        if not assets:
            return 0.0
        
        # Risk factors: old systems, high criticality, poor quality
        risk_score = 0.0
        for asset in assets:
            asset_risk = 1.0  # Base risk
            
            # Age factor (if available)
            if hasattr(asset, 'install_date') and getattr(asset, 'install_date'):
                # Simplified age calculation
                asset_risk += 0.5
            
            # Criticality factor
            criticality = getattr(asset, 'business_criticality', 'medium').lower()
            if criticality == 'high':
                asset_risk += 1.0
            elif criticality == 'low':
                asset_risk -= 0.3
            
            risk_score += asset_risk
        
        return round(risk_score / len(assets), 2)
    
    async def _detect_technologies(self, assets: List[Any]) -> List[str]:
        """Detect technologies from asset data."""
        technologies = set()
        
        for asset in assets:
            # Extract technologies from OS, applications, etc.
            os_type = getattr(asset, 'os_type', '')
            if os_type:
                technologies.add(os_type)
            
            application = getattr(asset, 'application', '')
            if application:
                technologies.add(application)
        
        return list(technologies)
    
    async def _count_dependencies(self, assets: List[Any]) -> int:
        """Count mapped dependencies."""
        # Simplified dependency counting
        return len([asset for asset in assets if getattr(asset, 'dependencies', None)])
    
    async def _calculate_integration_complexity(self, assets: List[Any]) -> float:
        """Calculate integration complexity score."""
        if not assets:
            return 0.0
        
        # Simple integration complexity based on asset types
        integration_scores = []
        for asset in assets:
            asset_type = getattr(asset, 'asset_type', 'unknown').lower()
            if 'database' in asset_type:
                integration_scores.append(3.0)
            elif 'server' in asset_type:
                integration_scores.append(2.0)
            else:
                integration_scores.append(1.0)
        
        return round(sum(integration_scores) / len(integration_scores), 2)
    
    async def _calculate_modernization_potential(self, assets: List[Any]) -> float:
        """Calculate modernization potential score."""
        if not assets:
            return 0.0
        
        # Higher potential for older, simpler systems
        potential_scores = []
        for asset in assets:
            # Simple scoring based on asset type
            asset_type = getattr(asset, 'asset_type', 'unknown').lower()
            if 'legacy' in asset_type or 'mainframe' in asset_type:
                potential_scores.append(4.0)
            elif 'server' in asset_type:
                potential_scores.append(3.0)
            else:
                potential_scores.append(2.0)
        
        return round(sum(potential_scores) / len(potential_scores), 2)
    
    async def _calculate_classification_accuracy(self, assets: List[Any]) -> float:
        """Calculate classification accuracy score."""
        if not assets:
            return 0.0
        
        # Simple accuracy based on completeness of classification fields
        classified_count = 0
        for asset in assets:
            if (getattr(asset, 'asset_type', None) and 
                getattr(asset, 'asset_type') != 'unknown'):
                classified_count += 1
        
        return round((classified_count / len(assets)) * 100, 2)
    
    async def _get_session_assets(self, session_id: str) -> List[Any]:
        """Get all assets for a session."""
        if not SESSION_MODELS_AVAILABLE:
            return []
        
        query = select(Asset).where(Asset.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def _asset_to_dict(self, asset: Any) -> Dict[str, Any]:
        """Convert asset object to dictionary for comparison."""
        return {
            'id': getattr(asset, 'id', None),
            'hostname': getattr(asset, 'hostname', None),
            'asset_type': getattr(asset, 'asset_type', None),
            'status': getattr(asset, 'status', None),
            'department': getattr(asset, 'department', None),
            'os_type': getattr(asset, 'os_type', None),
            'application': getattr(asset, 'application', None)
        }
    
    def _assets_are_different(self, asset1: Any, asset2: Any) -> bool:
        """Check if two assets are different."""
        comparison_fields = ['asset_type', 'status', 'department', 'os_type', 'application']
        
        for field in comparison_fields:
            val1 = getattr(asset1, field, None)
            val2 = getattr(asset2, field, None)
            if val1 != val2:
                return True
        
        return False
    
    def _get_asset_changes(self, source_asset: Any, target_asset: Any) -> List[Dict[str, Any]]:
        """Get list of changes between two assets."""
        changes = []
        comparison_fields = ['asset_type', 'status', 'department', 'os_type', 'application']
        
        for field in comparison_fields:
            source_val = getattr(source_asset, field, None)
            target_val = getattr(target_asset, field, None)
            
            if source_val != target_val:
                changes.append({
                    'field': field,
                    'from_value': source_val,
                    'to_value': target_val
                })
        
        return changes
    
    def _create_mock_snapshot(self, session_id: str) -> SessionSnapshot:
        """Create mock snapshot for testing."""
        return SessionSnapshot(
            session_id=session_id,
            session_name=f"Mock Session {session_id[:8]}",
            created_at=datetime.now(timezone.utc).isoformat(),
            status="completed",
            total_assets=150,
            unique_assets=142,
            duplicate_assets=8,
            quality_score=87.5,
            completeness_score=92.3,
            assets_by_type={"server": 45, "desktop": 78, "database": 12, "network": 15},
            assets_by_department={"IT": 60, "Finance": 35, "HR": 25, "Operations": 30},
            assets_by_status={"active": 130, "inactive": 15, "maintenance": 5},
            data_quality_issues=[
                {"type": "missing_hostname", "count": 3},
                {"type": "duplicate_entries", "count": 8}
            ],
            validation_errors=5,
            missing_critical_fields=12,
            data_consistency_score=89.7,
            estimated_cost_savings=245000.0,
            migration_complexity_score=3.2,
            business_criticality_distribution={"high": 25, "medium": 85, "low": 40},
            risk_score=2.8,
            technologies_detected=["Windows Server", "Oracle", "Apache", "MySQL"],
            dependencies_mapped=67,
            integration_complexity=2.5,
            modernization_potential=3.7,
            agent_confidence_score=91.2,
            classification_accuracy=94.5,
            recommendations_count=15,
            learning_insights=[
                {"type": "pattern_recognition", "confidence": 0.89},
                {"type": "classification_improvement", "accuracy": 0.94}
            ],
            processing_time_seconds=1247.5,
            data_source_count=3,
            import_method="csv_upload",
            errors_encountered=5
        )


def create_session_comparison_service(db: AsyncSession) -> SessionComparisonService:
    """
    Factory function to create session comparison service.
    
    Args:
        db: Database session
        
    Returns:
        SessionComparisonService instance
    """
    return SessionComparisonService(db) 