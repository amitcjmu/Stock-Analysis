"""
Agent Performance Aggregation Service
Daily aggregation service for agent performance metrics
Part of the Agent Observability Enhancement Phase 2
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_performance_daily import AgentPerformanceDaily
from app.models.agent_task_history import AgentTaskHistory
from app.models.client_account import ClientAccount, Engagement

logger = logging.getLogger(__name__)


class AgentPerformanceAggregationService:
    """Service for aggregating agent performance metrics daily"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled jobs for daily aggregation"""
        # Run daily aggregation at 2 AM
        self.scheduler.add_job(
            func=self.run_daily_aggregation,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_agent_performance_aggregation',
            name='Daily Agent Performance Aggregation',
            replace_existing=True
        )
        
        # Also run aggregation for yesterday on startup (in case it was missed)
        self.scheduler.add_job(
            func=lambda: self.aggregate_for_date(date.today() - timedelta(days=1)),
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='startup_yesterday_aggregation',
            name='Startup Yesterday Aggregation'
        )
    
    def start(self):
        """Start the aggregation service"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Agent performance aggregation service started")
    
    def stop(self):
        """Stop the aggregation service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Agent performance aggregation service stopped")
    
    def run_daily_aggregation(self):
        """Run daily aggregation for yesterday's data"""
        yesterday = date.today() - timedelta(days=1)
        self.aggregate_for_date(yesterday)
    
    def aggregate_for_date(self, target_date: date):
        """Aggregate performance metrics for a specific date"""
        logger.info(f"Starting performance aggregation for {target_date}")
        
        db = next(get_db())
        try:
            # Get all unique agent/client/engagement combinations that had activity
            combinations = self._get_active_agent_combinations(db, target_date)
            
            for agent_name, client_account_id, engagement_id in combinations:
                try:
                    self._aggregate_agent_performance(
                        db, agent_name, client_account_id, engagement_id, target_date
                    )
                except Exception as e:
                    logger.error(f"Error aggregating for {agent_name}: {e}")
            
            db.commit()
            logger.info(f"Completed performance aggregation for {target_date}")
            
        except Exception as e:
            logger.error(f"Error in daily aggregation: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _get_active_agent_combinations(self, db: Session, target_date: date) -> List[Tuple[str, str, str]]:
        """Get all unique agent/client/engagement combinations for a date"""
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        results = db.query(
            AgentTaskHistory.agent_name,
            AgentTaskHistory.client_account_id,
            AgentTaskHistory.engagement_id
        ).filter(
            AgentTaskHistory.started_at >= start_time,
            AgentTaskHistory.started_at < end_time
        ).distinct().all()
        
        return results
    
    def _aggregate_agent_performance(self, db: Session, agent_name: str,
                                   client_account_id: str, engagement_id: str,
                                   target_date: date):
        """Aggregate performance for a specific agent/client/engagement/date"""
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        # Query all tasks for this agent on this date
        tasks = db.query(AgentTaskHistory).filter(
            AgentTaskHistory.agent_name == agent_name,
            AgentTaskHistory.client_account_id == client_account_id,
            AgentTaskHistory.engagement_id == engagement_id,
            AgentTaskHistory.started_at >= start_time,
            AgentTaskHistory.started_at < end_time
        ).all()
        
        if not tasks:
            return
        
        # Calculate metrics
        tasks_attempted = len(tasks)
        tasks_completed = sum(1 for t in tasks if t.success is True)
        tasks_failed = sum(1 for t in tasks if t.success is False)
        
        # Duration metrics (only for completed tasks with duration)
        durations = [float(t.duration_seconds) for t in tasks 
                    if t.duration_seconds is not None and t.success is True]
        avg_duration = sum(durations) / len(durations) if durations else None
        
        # Confidence metrics (only for tasks with confidence scores)
        confidence_scores = [float(t.confidence_score) for t in tasks 
                           if t.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
        
        # Resource usage metrics
        total_llm_calls = sum(t.llm_calls_count or 0 for t in tasks)
        total_tokens = 0
        for task in tasks:
            if task.token_usage:
                total_tokens += task.token_usage.get('total_tokens', 0)
        
        # Success rate
        success_rate = (tasks_completed / tasks_attempted * 100) if tasks_attempted > 0 else 0
        
        # Check if record already exists
        existing = db.query(AgentPerformanceDaily).filter(
            AgentPerformanceDaily.agent_name == agent_name,
            AgentPerformanceDaily.date_recorded == target_date,
            AgentPerformanceDaily.client_account_id == client_account_id,
            AgentPerformanceDaily.engagement_id == engagement_id
        ).first()
        
        if existing:
            # Update existing record
            existing.tasks_attempted = tasks_attempted
            existing.tasks_completed = tasks_completed
            existing.tasks_failed = tasks_failed
            existing.avg_duration_seconds = Decimal(str(avg_duration)) if avg_duration else None
            existing.avg_confidence_score = Decimal(str(avg_confidence)) if avg_confidence else None
            existing.success_rate = Decimal(str(success_rate))
            existing.total_llm_calls = total_llm_calls
            existing.total_tokens_used = total_tokens
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            performance_daily = AgentPerformanceDaily(
                agent_name=agent_name,
                date_recorded=target_date,
                tasks_attempted=tasks_attempted,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                avg_duration_seconds=Decimal(str(avg_duration)) if avg_duration else None,
                avg_confidence_score=Decimal(str(avg_confidence)) if avg_confidence else None,
                success_rate=Decimal(str(success_rate)),
                total_llm_calls=total_llm_calls,
                total_tokens_used=total_tokens,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            db.add(performance_daily)
        
        logger.info(f"Aggregated performance for {agent_name} on {target_date}: "
                   f"{tasks_attempted} tasks, {success_rate:.1f}% success rate")
    
    def get_agent_performance_trends(self, agent_name: str,
                                   client_account_id: str,
                                   engagement_id: str,
                                   days: int = 30) -> Dict[str, Any]:
        """Get performance trends for an agent over specified days"""
        db = next(get_db())
        try:
            since_date = date.today() - timedelta(days=days)
            
            records = db.query(AgentPerformanceDaily).filter(
                AgentPerformanceDaily.agent_name == agent_name,
                AgentPerformanceDaily.client_account_id == client_account_id,
                AgentPerformanceDaily.engagement_id == engagement_id,
                AgentPerformanceDaily.date_recorded >= since_date
            ).order_by(AgentPerformanceDaily.date_recorded).all()
            
            trends = {
                "agent_name": agent_name,
                "period_days": days,
                "daily_metrics": []
            }
            
            for record in records:
                trends["daily_metrics"].append({
                    "date": record.date_recorded.isoformat(),
                    "tasks_attempted": record.tasks_attempted,
                    "tasks_completed": record.tasks_completed,
                    "tasks_failed": record.tasks_failed,
                    "success_rate": float(record.success_rate) if record.success_rate else 0,
                    "avg_duration_seconds": float(record.avg_duration_seconds) if record.avg_duration_seconds else None,
                    "avg_confidence_score": float(record.avg_confidence_score) if record.avg_confidence_score else None,
                    "total_llm_calls": record.total_llm_calls,
                    "total_tokens_used": record.total_tokens_used
                })
            
            # Calculate overall statistics
            if records:
                total_tasks = sum(r.tasks_attempted for r in records)
                total_completed = sum(r.tasks_completed for r in records)
                overall_success_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
                
                trends["overall_stats"] = {
                    "total_tasks_attempted": total_tasks,
                    "total_tasks_completed": total_completed,
                    "overall_success_rate": round(overall_success_rate, 2),
                    "avg_daily_tasks": round(total_tasks / len(records), 2),
                    "total_llm_calls": sum(r.total_llm_calls for r in records),
                    "total_tokens_used": sum(r.total_tokens_used for r in records)
                }
            else:
                trends["overall_stats"] = {
                    "total_tasks_attempted": 0,
                    "total_tasks_completed": 0,
                    "overall_success_rate": 0,
                    "avg_daily_tasks": 0,
                    "total_llm_calls": 0,
                    "total_tokens_used": 0
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def get_all_agents_summary(self, client_account_id: str,
                              engagement_id: str,
                              days: int = 7) -> List[Dict[str, Any]]:
        """Get summary for all agents in a client/engagement"""
        db = next(get_db())
        try:
            since_date = date.today() - timedelta(days=days)
            
            # Get aggregated stats for all agents
            results = db.query(
                AgentPerformanceDaily.agent_name,
                func.sum(AgentPerformanceDaily.tasks_attempted).label('total_tasks'),
                func.sum(AgentPerformanceDaily.tasks_completed).label('total_completed'),
                func.avg(AgentPerformanceDaily.success_rate).label('avg_success_rate'),
                func.avg(AgentPerformanceDaily.avg_duration_seconds).label('avg_duration'),
                func.sum(AgentPerformanceDaily.total_llm_calls).label('total_llm_calls')
            ).filter(
                AgentPerformanceDaily.client_account_id == client_account_id,
                AgentPerformanceDaily.engagement_id == engagement_id,
                AgentPerformanceDaily.date_recorded >= since_date
            ).group_by(AgentPerformanceDaily.agent_name).all()
            
            summaries = []
            for result in results:
                summaries.append({
                    "agent_name": result.agent_name,
                    "total_tasks": result.total_tasks or 0,
                    "total_completed": result.total_completed or 0,
                    "avg_success_rate": float(result.avg_success_rate) if result.avg_success_rate else 0,
                    "avg_duration_seconds": float(result.avg_duration) if result.avg_duration else None,
                    "total_llm_calls": result.total_llm_calls or 0
                })
            
            return sorted(summaries, key=lambda x: x['total_tasks'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting all agents summary: {e}")
            return []
        finally:
            db.close()
    
    def manual_trigger_aggregation(self, target_date: Optional[date] = None):
        """Manually trigger aggregation for a specific date"""
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"Manually triggering aggregation for {target_date}")
        self.aggregate_for_date(target_date)


# Global instance
agent_performance_aggregation_service = AgentPerformanceAggregationService()