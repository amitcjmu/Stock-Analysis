"""
Assessment Flow Metrics Collection

Provides comprehensive metrics collection for assessment flow operations
using Prometheus-compatible metrics.
"""

import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Mock classes when Prometheus is not available
    PROMETHEUS_AVAILABLE = False
    
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self, amount=1):
            pass
        def dec(self, amount=1):
            pass
        def observe(self, amount):
            pass
        def set(self, value):
            pass
    
    Counter = Histogram = Gauge = Info = MockMetric

logger = logging.getLogger(__name__)

# Assessment Flow Metrics
ASSESSMENT_FLOWS_TOTAL = Counter(
    'assessment_flows_total',
    'Total number of assessment flows initiated',
    ['client_account_id', 'engagement_id']
)

ASSESSMENT_FLOWS_COMPLETED = Counter(
    'assessment_flows_completed_total',
    'Total number of assessment flows completed',
    ['client_account_id', 'status']
)

ASSESSMENT_PHASE_DURATION = Histogram(
    'assessment_phase_duration_seconds',
    'Time spent in each assessment phase',
    ['phase', 'client_account_id'],
    buckets=[10, 30, 60, 300, 600, 1800, 3600]  # 10s to 1hr
)

ASSESSMENT_APPLICATIONS_PROCESSED = Counter(
    'assessment_applications_processed_total',
    'Total number of applications processed',
    ['client_account_id', 'phase']
)

CREWAI_AGENT_EXECUTIONS = Counter(
    'crewai_agent_executions_total',
    'Total CrewAI agent executions',
    ['agent_type', 'status', 'client_account_id']
)

CREWAI_AGENT_DURATION = Histogram(
    'crewai_agent_duration_seconds',
    'CrewAI agent execution duration',
    ['agent_type', 'client_account_id'],
    buckets=[1, 5, 10, 30, 60, 300, 600]  # 1s to 10min
)

ASSESSMENT_FLOW_ERRORS = Counter(
    'assessment_flow_errors_total',
    'Total assessment flow errors',
    ['error_type', 'phase', 'client_account_id']
)

ACTIVE_ASSESSMENT_FLOWS = Gauge(
    'active_assessment_flows',
    'Number of currently active assessment flows',
    ['status', 'client_account_id']
)

LLM_TOKEN_USAGE = Counter(
    'llm_token_usage_total',
    'Total LLM tokens consumed',
    ['model', 'operation_type', 'client_account_id']
)

ASSESSMENT_USER_INTERACTIONS = Counter(
    'assessment_user_interactions_total',
    'User interactions with assessment flow',
    ['interaction_type', 'phase', 'client_account_id']
)

ASSESSMENT_FLOW_QUALITY = Histogram(
    'assessment_flow_quality_score',
    'Quality scores for assessment flow results',
    ['phase', 'client_account_id'],
    buckets=[0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

ASSESSMENT_DATA_VOLUME = Histogram(
    'assessment_data_volume',
    'Volume of data processed in assessment flows',
    ['data_type', 'client_account_id'],
    buckets=[1, 10, 50, 100, 500, 1000, 5000, 10000]
)

# Assessment Flow Info
ASSESSMENT_INFO = Info(
    'assessment_flow_info',
    'Information about assessment flow configuration'
)


def track_assessment_phase(phase: str, client_account_id: int):
    """Decorator to track assessment phase metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                ASSESSMENT_PHASE_DURATION.labels(
                    phase=phase,
                    client_account_id=client_account_id
                ).observe(duration)
                
                logger.debug(f"Phase {phase} completed in {duration:.2f}s for client {client_account_id}")
                
                return result
                
            except Exception as e:
                ASSESSMENT_FLOW_ERRORS.labels(
                    error_type=type(e).__name__,
                    phase=phase,
                    client_account_id=client_account_id
                ).inc()
                
                logger.error(f"Phase {phase} failed for client {client_account_id}: {str(e)}")
                raise
        
        return wrapper
    return decorator


def track_crewai_execution(agent_type: str, client_account_id: int):
    """Decorator to track CrewAI agent execution metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                CREWAI_AGENT_EXECUTIONS.labels(
                    agent_type=agent_type,
                    status='success',
                    client_account_id=client_account_id
                ).inc()
                
                CREWAI_AGENT_DURATION.labels(
                    agent_type=agent_type,
                    client_account_id=client_account_id
                ).observe(duration)
                
                logger.debug(f"Agent {agent_type} executed successfully in {duration:.2f}s")
                
                return result
                
            except Exception as e:
                CREWAI_AGENT_EXECUTIONS.labels(
                    agent_type=agent_type,
                    status='error',
                    client_account_id=client_account_id
                ).inc()
                
                logger.error(f"Agent {agent_type} failed: {str(e)}")
                raise
        
        return wrapper
    return decorator


def track_user_interaction(interaction_type: str, phase: str, client_account_id: int):
    """Track user interactions with assessment flow"""
    ASSESSMENT_USER_INTERACTIONS.labels(
        interaction_type=interaction_type,
        phase=phase,
        client_account_id=client_account_id
    ).inc()
    
    logger.debug(f"User interaction: {interaction_type} in phase {phase}")


def record_quality_score(phase: str, quality_score: float, client_account_id: int):
    """Record quality score for assessment phase"""
    ASSESSMENT_FLOW_QUALITY.labels(
        phase=phase,
        client_account_id=client_account_id
    ).observe(quality_score)
    
    logger.debug(f"Quality score {quality_score} recorded for phase {phase}")


def record_data_volume(data_type: str, volume: int, client_account_id: int):
    """Record data volume processed"""
    ASSESSMENT_DATA_VOLUME.labels(
        data_type=data_type,
        client_account_id=client_account_id
    ).observe(volume)
    
    logger.debug(f"Data volume {volume} recorded for type {data_type}")


class AssessmentFlowMonitor:
    """Centralized monitoring for assessment flows"""
    
    def __init__(self):
        self.active_flows = {}
        self.flow_start_times = {}
        
        # Set assessment flow info
        if PROMETHEUS_AVAILABLE:
            ASSESSMENT_INFO.info({
                'version': '1.0.0',
                'enabled': 'true',
                'environment': 'development'
            })
    
    def flow_started(self, flow_id: str, client_account_id: int, engagement_id: int, selected_apps: int = 0):
        """Track flow start"""
        ASSESSMENT_FLOWS_TOTAL.labels(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        ).inc()
        
        ACTIVE_ASSESSMENT_FLOWS.labels(
            status='active',
            client_account_id=client_account_id
        ).inc()
        
        self.active_flows[flow_id] = {
            'start_time': time.time(),
            'client_account_id': client_account_id,
            'engagement_id': engagement_id,
            'selected_apps': selected_apps
        }
        self.flow_start_times[flow_id] = time.time()
        
        # Record data volume
        if selected_apps > 0:
            record_data_volume('applications', selected_apps, client_account_id)
        
        logger.info(f"Assessment flow {flow_id} started for client {client_account_id} with {selected_apps} applications")
    
    def flow_completed(self, flow_id: str, status: str):
        """Track flow completion"""
        if flow_id in self.active_flows:
            flow_info = self.active_flows[flow_id]
            
            ASSESSMENT_FLOWS_COMPLETED.labels(
                client_account_id=flow_info['client_account_id'],
                status=status
            ).inc()
            
            ACTIVE_ASSESSMENT_FLOWS.labels(
                status='active',
                client_account_id=flow_info['client_account_id']
            ).dec()
            
            # Calculate total flow duration
            if flow_id in self.flow_start_times:
                total_duration = time.time() - self.flow_start_times[flow_id]
                ASSESSMENT_PHASE_DURATION.labels(
                    phase='total_flow',
                    client_account_id=flow_info['client_account_id']
                ).observe(total_duration)
                
                del self.flow_start_times[flow_id]
            
            del self.active_flows[flow_id]
            
            logger.info(f"Assessment flow {flow_id} completed with status {status}")
    
    def applications_processed(self, count: int, phase: str, client_account_id: int):
        """Track applications processed in phase"""
        ASSESSMENT_APPLICATIONS_PROCESSED.labels(
            client_account_id=client_account_id,
            phase=phase
        ).inc(count)
        
        logger.debug(f"Processed {count} applications in phase {phase}")
    
    def llm_usage(self, model: str, tokens: int, operation: str, client_account_id: int):
        """Track LLM token usage"""
        LLM_TOKEN_USAGE.labels(
            model=model,
            operation_type=operation,
            client_account_id=client_account_id
        ).inc(tokens)
        
        logger.debug(f"LLM usage: {tokens} tokens for {operation} using {model}")
    
    def phase_transition(self, flow_id: str, from_phase: str, to_phase: str, client_account_id: int):
        """Track phase transitions"""
        # This could be expanded to track phase transition patterns
        logger.info(f"Flow {flow_id} transitioned from {from_phase} to {to_phase}")
    
    def error_occurred(self, flow_id: str, error_type: str, phase: str, client_account_id: int, error_details: str = ""):
        """Track errors in assessment flows"""
        ASSESSMENT_FLOW_ERRORS.labels(
            error_type=error_type,
            phase=phase,
            client_account_id=client_account_id
        ).inc()
        
        logger.error(f"Error in flow {flow_id}, phase {phase}: {error_type} - {error_details}")
    
    def get_flow_metrics(self) -> Dict[str, Any]:
        """Get current flow metrics summary"""
        return {
            'active_flows': len(self.active_flows),
            'flows_by_client': self._get_flows_by_client(),
            'average_flow_duration': self._get_average_flow_duration(),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _get_flows_by_client(self) -> Dict[int, int]:
        """Get count of active flows by client"""
        client_counts = {}
        for flow_info in self.active_flows.values():
            client_id = flow_info['client_account_id']
            client_counts[client_id] = client_counts.get(client_id, 0) + 1
        return client_counts
    
    def _get_average_flow_duration(self) -> float:
        """Get average duration of currently active flows"""
        if not self.flow_start_times:
            return 0.0
        
        current_time = time.time()
        durations = [current_time - start_time for start_time in self.flow_start_times.values()]
        return sum(durations) / len(durations) if durations else 0.0


# Global monitor instance
assessment_monitor = AssessmentFlowMonitor()


# Utility functions for common monitoring tasks
def monitor_assessment_flow(flow_id: str, client_account_id: int, engagement_id: int, selected_apps: int = 0):
    """Convenience function to start monitoring a flow"""
    assessment_monitor.flow_started(flow_id, client_account_id, engagement_id, selected_apps)


def complete_assessment_flow(flow_id: str, status: str = "completed"):
    """Convenience function to mark flow as completed"""
    assessment_monitor.flow_completed(flow_id, status)


def record_phase_applications(phase: str, count: int, client_account_id: int):
    """Convenience function to record applications processed"""
    assessment_monitor.applications_processed(count, phase, client_account_id)


def record_llm_usage(model: str, tokens: int, operation: str, client_account_id: int):
    """Convenience function to record LLM usage"""
    assessment_monitor.llm_usage(model, tokens, operation, client_account_id)


# Context manager for phase monitoring
class PhaseMonitor:
    """Context manager for monitoring assessment phases"""
    
    def __init__(self, phase: str, client_account_id: int):
        self.phase = phase
        self.client_account_id = client_account_id
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        logger.debug(f"Starting phase {self.phase} for client {self.client_account_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            if exc_type is None:
                ASSESSMENT_PHASE_DURATION.labels(
                    phase=self.phase,
                    client_account_id=self.client_account_id
                ).observe(duration)
                
                logger.debug(f"Phase {self.phase} completed successfully in {duration:.2f}s")
            else:
                ASSESSMENT_FLOW_ERRORS.labels(
                    error_type=exc_type.__name__ if exc_type else "Unknown",
                    phase=self.phase,
                    client_account_id=self.client_account_id
                ).inc()
                
                logger.error(f"Phase {self.phase} failed after {duration:.2f}s: {str(exc_val)}")
        
        return False  # Don't suppress exceptions