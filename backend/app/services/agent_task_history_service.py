"""
Agent Task History Service
Provides data access and query methods for agent task history
Part of the Agent Observability Enhancement Phase 2
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.models.agent_task_history import AgentTaskHistory

logger = logging.getLogger(__name__)


class AgentTaskHistoryService:
    """Service for querying and analyzing agent task history"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_agent_performance_summary(self, agent_name: str, 
                                    client_account_id: str, 
                                    engagement_id: str,
                                    days: int = 7) -> Dict[str, Any]:
        """Get performance summary for an agent over the specified period"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Query task statistics
            task_stats = self.db.query(
                func.count(AgentTaskHistory.id).label('total_tasks'),
                func.count(func.nullif(AgentTaskHistory.success, False)).label('successful_tasks'),
                func.avg(AgentTaskHistory.duration_seconds).label('avg_duration'),
                func.avg(AgentTaskHistory.confidence_score).label('avg_confidence'),
                func.sum(AgentTaskHistory.llm_calls_count).label('total_llm_calls'),
                func.sum(AgentTaskHistory.thinking_phases_count).label('total_thinking_phases')
            ).filter(
                AgentTaskHistory.agent_name == agent_name,
                AgentTaskHistory.client_account_id == client_account_id,
                AgentTaskHistory.engagement_id == engagement_id,
                AgentTaskHistory.started_at >= since_date
            ).first()
            
            # Calculate success rate
            total_tasks = task_stats.total_tasks or 0
            successful_tasks = task_stats.successful_tasks or 0
            success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get token usage
            token_usage = self._calculate_token_usage(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            # Get recent error patterns
            error_patterns = self._get_error_patterns(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            # Get performance trends
            trends = self._get_performance_trends(
                agent_name, client_account_id, engagement_id, days
            )
            
            return {
                "agent_name": agent_name,
                "period_days": days,
                "summary": {
                    "total_tasks": total_tasks,
                    "successful_tasks": successful_tasks,
                    "failed_tasks": total_tasks - successful_tasks,
                    "success_rate": round(success_rate, 2),
                    "avg_duration_seconds": float(task_stats.avg_duration or 0),
                    "avg_confidence_score": float(task_stats.avg_confidence or 0),
                    "total_llm_calls": task_stats.total_llm_calls or 0,
                    "total_thinking_phases": task_stats.total_thinking_phases or 0
                },
                "token_usage": token_usage,
                "error_patterns": error_patterns,
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Error getting agent performance summary: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e)
            }
    
    def get_agent_task_history(self, agent_name: str,
                              client_account_id: str,
                              engagement_id: str,
                              limit: int = 50,
                              offset: int = 0,
                              status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated task history for an agent"""
        try:
            query = self.db.query(AgentTaskHistory).filter(
                AgentTaskHistory.agent_name == agent_name,
                AgentTaskHistory.client_account_id == client_account_id,
                AgentTaskHistory.engagement_id == engagement_id
            )
            
            if status_filter:
                query = query.filter(AgentTaskHistory.status == status_filter)
            
            # Get total count
            total_count = query.count()
            
            # Get paginated results
            tasks = query.order_by(desc(AgentTaskHistory.started_at))\
                        .limit(limit)\
                        .offset(offset)\
                        .all()
            
            return {
                "agent_name": agent_name,
                "total_tasks": total_count,
                "limit": limit,
                "offset": offset,
                "tasks": [task.to_dict() for task in tasks]
            }
            
        except Exception as e:
            logger.error(f"Error getting agent task history: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e)
            }
    
    def get_agent_analytics(self, agent_name: str,
                           client_account_id: str,
                           engagement_id: str,
                           period_days: int = 7) -> Dict[str, Any]:
        """Get detailed analytics for an agent"""
        try:
            since_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Performance distribution
            performance_dist = self._get_performance_distribution(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            # Resource usage analysis
            resource_usage = self._get_resource_usage_analysis(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            # Pattern discovery stats
            pattern_stats = self._get_pattern_discovery_stats(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            # Task complexity analysis
            complexity_analysis = self._get_task_complexity_analysis(
                agent_name, client_account_id, engagement_id, since_date
            )
            
            return {
                "agent_name": agent_name,
                "period_days": period_days,
                "analytics": {
                    "performance_distribution": performance_dist,
                    "resource_usage": resource_usage,
                    "pattern_discovery": pattern_stats,
                    "task_complexity": complexity_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting agent analytics: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e)
            }
    
    def get_discovered_patterns(self, agent_name: Optional[str] = None,
                               client_account_id: str = None,
                               engagement_id: str = None,
                               pattern_type: Optional[str] = None,
                               min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Get discovered patterns with optional filters"""
        try:
            query = self.db.query(AgentDiscoveredPatterns)
            
            if agent_name:
                query = query.filter(AgentDiscoveredPatterns.discovered_by_agent == agent_name)
            if client_account_id:
                query = query.filter(AgentDiscoveredPatterns.client_account_id == client_account_id)
            if engagement_id:
                query = query.filter(AgentDiscoveredPatterns.engagement_id == engagement_id)
            if pattern_type:
                query = query.filter(AgentDiscoveredPatterns.pattern_type == pattern_type)
            if min_confidence > 0:
                query = query.filter(AgentDiscoveredPatterns.confidence_score >= min_confidence)
            
            patterns = query.order_by(desc(AgentDiscoveredPatterns.confidence_score)).all()
            
            return [pattern.to_dict() for pattern in patterns]
            
        except Exception as e:
            logger.error(f"Error getting discovered patterns: {e}")
            return []
    
    def _calculate_token_usage(self, agent_name: str, client_account_id: str,
                              engagement_id: str, since_date: datetime) -> Dict[str, Any]:
        """Calculate token usage statistics"""
        tasks = self.db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= since_date
        ).all()
        
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        
        for task in tasks:
            if task.token_usage:
                total_input_tokens += task.token_usage.get('input_tokens', 0)
                total_output_tokens += task.token_usage.get('output_tokens', 0)
                total_tokens += task.token_usage.get('total_tokens', 0)
        
        return {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "avg_tokens_per_task": total_tokens / len(tasks) if tasks else 0
        }
    
    def _get_error_patterns(self, agent_name: str, client_account_id: str,
                           engagement_id: str, since_date: datetime) -> List[Dict[str, Any]]:
        """Analyze error patterns"""
        failed_tasks = self.db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= since_date,
            AgentTaskHistory.status.in_(['failed', 'timeout'])
        ).all()
        
        error_counts = {}
        for task in failed_tasks:
            error_type = task.status
            if task.error_message:
                # Simple error categorization
                if 'timeout' in task.error_message.lower():
                    error_type = 'timeout'
                elif 'llm' in task.error_message.lower():
                    error_type = 'llm_error'
                elif 'validation' in task.error_message.lower():
                    error_type = 'validation_error'
                else:
                    error_type = 'other_error'
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return [
            {"error_type": error_type, "count": count}
            for error_type, count in error_counts.items()
        ]
    
    def _get_performance_trends(self, agent_name: str, client_account_id: str,
                               engagement_id: str, days: int) -> Dict[str, Any]:
        """Calculate daily performance trends"""
        trends = {
            "dates": [],
            "success_rates": [],
            "avg_durations": [],
            "task_counts": [],
            "confidence_scores": []
        }
        
        for i in range(days):
            day_date = date.today() - timedelta(days=i)
            day_start = datetime.combine(day_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)
            
            day_stats = self.db.query(
                func.count(AgentTaskHistory.id).label('total'),
                func.count(func.nullif(AgentTaskHistory.success, False)).label('successful'),
                func.avg(AgentTaskHistory.duration_seconds).label('avg_duration'),
                func.avg(AgentTaskHistory.confidence_score).label('avg_confidence')
            ).filter(
                AgentTaskHistory.agent_name == agent_name,
                AgentTaskHistory.client_account_id == client_account_id,
                AgentTaskHistory.engagement_id == engagement_id,
                AgentTaskHistory.started_at >= day_start,
                AgentTaskHistory.started_at < day_end
            ).first()
            
            total = day_stats.total or 0
            successful = day_stats.successful or 0
            success_rate = (successful / total * 100) if total > 0 else 0
            
            trends["dates"].insert(0, day_date.isoformat())
            trends["success_rates"].insert(0, round(success_rate, 2))
            trends["avg_durations"].insert(0, float(day_stats.avg_duration or 0))
            trends["task_counts"].insert(0, total)
            trends["confidence_scores"].insert(0, float(day_stats.avg_confidence or 0))
        
        return trends
    
    def _get_performance_distribution(self, agent_name: str, client_account_id: str,
                                     engagement_id: str, since_date: datetime) -> Dict[str, Any]:
        """Get performance distribution metrics"""
        tasks = self.db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= since_date,
            AgentTaskHistory.duration_seconds.isnot(None)
        ).all()
        
        if not tasks:
            return {"duration_percentiles": {}, "status_distribution": {}}
        
        durations = sorted([float(task.duration_seconds) for task in tasks])
        
        # Calculate percentiles
        percentiles = {}
        for p in [25, 50, 75, 90, 95, 99]:
            idx = int(len(durations) * p / 100)
            if idx < len(durations):
                percentiles[f"p{p}"] = round(durations[idx], 2)
        
        # Status distribution
        status_counts = {}
        for task in tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        return {
            "duration_percentiles": percentiles,
            "status_distribution": status_counts
        }
    
    def _get_resource_usage_analysis(self, agent_name: str, client_account_id: str,
                                    engagement_id: str, since_date: datetime) -> Dict[str, Any]:
        """Analyze resource usage patterns"""
        tasks = self.db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= since_date
        ).all()
        
        total_memory = 0
        memory_count = 0
        llm_call_distribution = {}
        
        for task in tasks:
            if task.memory_usage_mb:
                total_memory += float(task.memory_usage_mb)
                memory_count += 1
            
            call_bucket = f"{(task.llm_calls_count // 5) * 5}-{(task.llm_calls_count // 5 + 1) * 5}"
            llm_call_distribution[call_bucket] = llm_call_distribution.get(call_bucket, 0) + 1
        
        return {
            "avg_memory_usage_mb": round(total_memory / memory_count, 2) if memory_count > 0 else 0,
            "peak_memory_usage_mb": max([float(t.memory_usage_mb) for t in tasks if t.memory_usage_mb] or [0]),
            "llm_call_distribution": llm_call_distribution
        }
    
    def _get_pattern_discovery_stats(self, agent_name: str, client_account_id: str,
                                    engagement_id: str, since_date: datetime) -> Dict[str, Any]:
        """Get pattern discovery statistics"""
        patterns = self.db.query(AgentDiscoveredPatterns).filter(
            AgentDiscoveredPatterns.discovered_by_agent == agent_name,
            AgentDiscoveredPatterns.client_account_id == client_account_id,
            AgentDiscoveredPatterns.engagement_id == engagement_id,
            AgentDiscoveredPatterns.created_at >= since_date
        ).all()
        
        pattern_types = {}
        total_references = 0
        high_confidence_patterns = 0
        
        for pattern in patterns:
            pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1
            total_references += pattern.times_referenced
            if pattern.confidence_score >= Decimal('0.8'):
                high_confidence_patterns += 1
        
        return {
            "total_patterns_discovered": len(patterns),
            "pattern_types": pattern_types,
            "total_pattern_references": total_references,
            "high_confidence_patterns": high_confidence_patterns,
            "avg_confidence_score": float(sum(p.confidence_score for p in patterns) / len(patterns)) if patterns else 0
        }
    
    def _get_task_complexity_analysis(self, agent_name: str, client_account_id: str,
                                     engagement_id: str, since_date: datetime) -> Dict[str, Any]:
        """Analyze task complexity based on various metrics"""
        tasks = self.db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= since_date
        ).all()
        
        complexity_buckets = {
            "simple": 0,    # < 10s, < 3 LLM calls
            "moderate": 0,  # 10-60s, 3-5 LLM calls
            "complex": 0,   # 60-300s, 5-10 LLM calls
            "very_complex": 0  # > 300s, > 10 LLM calls
        }
        
        for task in tasks:
            duration = float(task.duration_seconds or 0)
            llm_calls = task.llm_calls_count or 0
            
            if duration < 10 and llm_calls < 3:
                complexity_buckets["simple"] += 1
            elif duration < 60 and llm_calls <= 5:
                complexity_buckets["moderate"] += 1
            elif duration < 300 and llm_calls <= 10:
                complexity_buckets["complex"] += 1
            else:
                complexity_buckets["very_complex"] += 1
        
        return {
            "complexity_distribution": complexity_buckets,
            "avg_thinking_phases_per_task": sum(t.thinking_phases_count for t in tasks) / len(tasks) if tasks else 0
        }


def get_agent_task_history_service(db: Session = None) -> AgentTaskHistoryService:
    """Factory function to get agent task history service instance"""
    if db is None:
        db = next(get_db())
    return AgentTaskHistoryService(db)