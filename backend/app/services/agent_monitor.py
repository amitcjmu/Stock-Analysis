"""
Agent Monitoring Service for CrewAI agents.
Provides real-time observability into agent task execution.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    THINKING = "thinking"
    WAITING_LLM = "waiting_llm"
    PROCESSING_RESPONSE = "processing_response"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class LLMCall:
    timestamp: datetime
    action: str
    prompt_length: int = 0
    response_length: int = 0
    duration: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None


@dataclass
class TaskExecution:
    task_id: str
    agent_name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    llm_calls: List[LLMCall] = field(default_factory=list)
    error: Optional[str] = None
    result_preview: Optional[str] = None
    last_activity: Optional[datetime] = None
    thinking_phases: List[Dict] = field(default_factory=list)
    
    @property
    def elapsed_time(self) -> float:
        if self.start_time:
            end = self.end_time or datetime.utcnow()
            return (end - self.start_time).total_seconds()
        return 0.0
    
    @property
    def time_since_activity(self) -> float:
        """Time since last recorded activity."""
        if self.last_activity:
            return (datetime.utcnow() - self.last_activity).total_seconds()
        return self.elapsed_time
    
    @property
    def is_hanging(self) -> bool:
        """Check if task appears to be hanging (no activity > 30 seconds)."""
        return self.time_since_activity > 30 and self.status in [
            TaskStatus.RUNNING, TaskStatus.THINKING, TaskStatus.WAITING_LLM
        ]
    
    @property
    def hanging_reason(self) -> str:
        """Determine why the task might be hanging."""
        if not self.is_hanging:
            return "Not hanging"
        
        if self.status == TaskStatus.THINKING:
            return f"Stuck in thinking phase for {self.time_since_activity:.1f}s"
        elif self.status == TaskStatus.WAITING_LLM:
            return f"Waiting for LLM response for {self.time_since_activity:.1f}s"
        elif len(self.llm_calls) == 0:
            return f"No LLM calls made in {self.elapsed_time:.1f}s"
        else:
            last_call = self.llm_calls[-1]
            if last_call.status == "pending":
                return f"LLM call pending for {self.time_since_activity:.1f}s"
            else:
                return f"No activity after last LLM call for {self.time_since_activity:.1f}s"


class AgentMonitor:
    """Real-time monitoring for CrewAI agent task execution."""
    
    def __init__(self):
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: List[TaskExecution] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
    def start_monitoring(self):
        """Start the real-time monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Agent monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Agent monitoring stopped")
    
    def start_task(self, task_id: str, agent_name: str, description: str) -> TaskExecution:
        """Register a new task execution."""
        with self._lock:
            task_exec = TaskExecution(
                task_id=task_id,
                agent_name=agent_name,
                description=description[:100] + "..." if len(description) > 100 else description,
                status=TaskStatus.STARTING,
                start_time=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            self.active_tasks[task_id] = task_exec
            
        logger.info(f"🚀 Task started: {agent_name} - {task_id}")
        self._print_status_update(task_exec, "STARTED")
        return task_exec
    
    def update_task_status(self, task_id: str, status: TaskStatus, details: Optional[str] = None):
        """Update task status."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                old_status = task.status
                task.status = status
                task.last_activity = datetime.utcnow()
                
                if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
                    task.end_time = datetime.utcnow()
                    task.duration = task.elapsed_time
                    
                if details:
                    if status == TaskStatus.FAILED:
                        task.error = details
                    elif status == TaskStatus.COMPLETED:
                        task.result_preview = details[:200] + "..." if len(details) > 200 else details
                
                self._print_status_update(task, f"{old_status.value.upper()} → {status.value.upper()}")
    
    def record_thinking_phase(self, task_id: str, phase_description: str):
        """Record a thinking phase for detailed analysis."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.THINKING
                task.last_activity = datetime.utcnow()
                
                thinking_phase = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "description": phase_description,
                    "elapsed_time": task.elapsed_time
                }
                task.thinking_phases.append(thinking_phase)
                
                self._print_status_update(task, f"THINKING: {phase_description}")
    
    def start_llm_call(self, task_id: str, action: str, prompt_length: int = 0) -> str:
        """Start tracking an LLM call."""
        call_id = f"{task_id}_call_{len(self.active_tasks.get(task_id, TaskExecution('', '', '')).llm_calls)}"
        
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.WAITING_LLM
                task.last_activity = datetime.utcnow()
                
                llm_call = LLMCall(
                    timestamp=datetime.utcnow(),
                    action=action,
                    prompt_length=prompt_length,
                    status="pending"
                )
                task.llm_calls.append(llm_call)
                
                self._print_status_update(task, f"LLM CALL: {action} (prompt: {prompt_length} chars)")
        
        return call_id
    
    def complete_llm_call(self, task_id: str, response_length: int = 0, error: Optional[str] = None):
        """Complete tracking an LLM call."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.last_activity = datetime.utcnow()
                
                if task.llm_calls:
                    last_call = task.llm_calls[-1]
                    last_call.duration = (datetime.utcnow() - last_call.timestamp).total_seconds()
                    last_call.response_length = response_length
                    last_call.status = "failed" if error else "completed"
                    last_call.error = error
                    
                    if error:
                        task.status = TaskStatus.FAILED
                        self._print_status_update(task, f"LLM CALL FAILED: {error}")
                    else:
                        task.status = TaskStatus.PROCESSING_RESPONSE
                        self._print_status_update(task, f"LLM RESPONSE: {response_length} chars in {last_call.duration:.1f}s")
    
    def add_llm_call(self, task_id: str, llm_call_info: Dict):
        """Record an LLM call for a task (legacy method for compatibility)."""
        action = llm_call_info.get('action', 'unknown')
        prompt_length = len(str(llm_call_info.get('prompt', '')))
        self.start_llm_call(task_id, action, prompt_length)
    
    def complete_task(self, task_id: str, result: Optional[str] = None):
        """Mark task as completed."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.end_time = datetime.utcnow()
                task.duration = task.elapsed_time
                
                if result:
                    task.result_preview = result[:200] + "..." if len(result) > 200 else result
                
                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                
                self._print_status_update(task, f"COMPLETED in {task.duration:.2f}s")
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.end_time = datetime.utcnow()
                task.duration = task.elapsed_time
                task.error = error
                
                # Move to completed tasks
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                
                self._print_status_update(task, f"FAILED after {task.duration:.2f}s: {error}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        with self._lock:
            hanging_tasks = [task for task in self.active_tasks.values() if task.is_hanging]
            
            return {
                "monitoring_active": self.monitoring_active,
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "hanging_tasks": len(hanging_tasks),
                "active_task_details": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "status": task.status.value,
                        "elapsed": f"{task.elapsed_time:.1f}s",
                        "since_activity": f"{task.time_since_activity:.1f}s",
                        "description": task.description,
                        "is_hanging": task.is_hanging,
                        "hanging_reason": task.hanging_reason,
                        "llm_calls": len(task.llm_calls),
                        "thinking_phases": len(task.thinking_phases)
                    }
                    for task in self.active_tasks.values()
                ],
                "hanging_task_details": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "elapsed": f"{task.elapsed_time:.1f}s",
                        "since_activity": f"{task.time_since_activity:.1f}s",
                        "description": task.description,
                        "hanging_reason": task.hanging_reason,
                        "llm_calls": len(task.llm_calls),
                        "last_llm_call": task.llm_calls[-1].action if task.llm_calls else "None",
                        "thinking_phases": len(task.thinking_phases),
                        "last_thinking": task.thinking_phases[-1]['description'] if task.thinking_phases else "None"
                    }
                    for task in hanging_tasks
                ]
            }
    
    def _print_status_update(self, task: TaskExecution, action: str):
        """Print a formatted status update."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        elapsed = f"{task.elapsed_time:.1f}s" if task.start_time else "0.0s"
        
        print(f"[{timestamp}] 🤖 {task.agent_name} | {action} | {elapsed} | {task.description}")
        
        # Print warning for long-running tasks
        if task.elapsed_time > 15:
            print(f"⚠️  Task running for {elapsed} - {task.hanging_reason}")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                with self._lock:
                    current_time = datetime.utcnow()
                    
                    # Check for hanging tasks
                    for task in self.active_tasks.values():
                        if task.is_hanging and task.status != TaskStatus.TIMEOUT:
                            task.status = TaskStatus.TIMEOUT
                            print(f"🚨 HANGING DETECTED: {task.agent_name} task {task.task_id}")
                            print(f"   Reason: {task.hanging_reason}")
                            print(f"   Description: {task.description}")
                            print(f"   LLM calls made: {len(task.llm_calls)}")
                            print(f"   Thinking phases: {len(task.thinking_phases)}")
                            
                            if task.llm_calls:
                                last_call = task.llm_calls[-1]
                                print(f"   Last LLM call: {last_call.action} ({last_call.status})")
                            
                            if task.thinking_phases:
                                last_thinking = task.thinking_phases[-1]
                                print(f"   Last thinking: {last_thinking['description']}")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def print_summary(self):
        """Print a summary of all task executions."""
        print("\n" + "=" * 80)
        print("AGENT MONITORING SUMMARY")
        print("=" * 80)
        
        with self._lock:
            if self.active_tasks:
                print(f"\n🔄 ACTIVE TASKS ({len(self.active_tasks)}):")
                for task in self.active_tasks.values():
                    status_icon = "🚨" if task.is_hanging else "⏳"
                    print(f"  {status_icon} {task.agent_name}: {task.description}")
                    print(f"     Status: {task.status.value} | Elapsed: {task.elapsed_time:.1f}s | Since Activity: {task.time_since_activity:.1f}s")
                    if task.is_hanging:
                        print(f"     🚨 HANGING: {task.hanging_reason}")
                    print(f"     LLM Calls: {len(task.llm_calls)} | Thinking Phases: {len(task.thinking_phases)}")
            
            if self.completed_tasks:
                print(f"\n✅ COMPLETED TASKS ({len(self.completed_tasks)}):")
                for task in self.completed_tasks[-5:]:  # Show last 5
                    status_icon = "✅" if task.status == TaskStatus.COMPLETED else "❌"
                    print(f"  {status_icon} {task.agent_name}: {task.description} "
                          f"({task.duration:.1f}s)")
        
        print("=" * 80)


# Global monitor instance
agent_monitor = AgentMonitor() 