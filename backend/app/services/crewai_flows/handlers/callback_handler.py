"""
Callback Handler for Discovery Flow
Handles comprehensive callback system for monitoring crew and agent activities
Enhanced for Agent Observability Enhancement Phase 2.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Import agent registry for performance tracking
try:
    from app.services.agent_registry import agent_registry

    AGENT_REGISTRY_AVAILABLE = True
except ImportError:
    AGENT_REGISTRY_AVAILABLE = False
    logger.warning("Agent registry not available for performance tracking")

# Import agent monitor for task persistence
try:
    from app.services.agent_monitor import agent_monitor

    AGENT_MONITOR_AVAILABLE = True
except ImportError:
    AGENT_MONITOR_AVAILABLE = False
    logger.warning("Agent monitor not available for task persistence")


class CallbackHandler:
    """Handles comprehensive callback system for monitoring with database persistence"""

    def __init__(
        self,
        flow_id: Optional[str] = None,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        self.flow_id = flow_id
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.active_tasks = {}  # Map agent+task to task_id for tracking

        self.callback_state = {
            "total_steps": 0,
            "completed_steps": 0,
            "current_crew": None,
            "current_task": None,
            "current_agent": None,
            "step_history": [],
            "error_history": [],
            "performance_metrics": {},
        }

    def setup_callbacks(self):
        """Setup comprehensive callback system for monitoring"""
        self.callback_handlers = {
            "step_callback": self._step_callback,
            "crew_step_callback": self._crew_step_callback,
            "task_completion_callback": self._task_completion_callback,
            "error_callback": self._error_callback,
            "agent_callback": self._agent_callback,
        }

        logger.info("Callback system initialized with 5 callback types")

    def _step_callback(self, step_info: Dict[str, Any]):
        """Callback for individual agent steps with task tracking"""
        try:
            timestamp = datetime.now().isoformat()
            agent_name = step_info.get("agent", "unknown")
            task_name = step_info.get("task", "unknown")

            step_entry = {
                "timestamp": timestamp,
                "step_type": step_info.get("type", "unknown"),
                "agent": agent_name,
                "crew": self.callback_state.get("current_crew", "unknown"),
                "task": task_name,
                "content": step_info.get("content", ""),
                "status": step_info.get("status", "in_progress"),
            }

            # Store step in history
            self.callback_state["step_history"].append(step_entry)

            # Update counters
            self.callback_state["total_steps"] += 1
            if step_info.get("status") == "completed":
                self.callback_state["completed_steps"] += 1

            # Track task in agent monitor
            if AGENT_MONITOR_AVAILABLE and agent_name != "unknown":
                task_key = f"{agent_name}:{task_name}"

                if (
                    step_info.get("status") == "starting"
                    and task_key not in self.active_tasks
                ):
                    # Start tracking new task
                    task_id = f"task_{uuid.uuid4().hex[:8]}_{agent_name}"
                    self.active_tasks[task_key] = task_id

                    agent_monitor.start_task_with_context(
                        task_id=task_id,
                        agent_name=agent_name,
                        description=step_info.get("content", task_name),
                        flow_id=self.flow_id,
                        client_account_id=self.client_account_id,
                        engagement_id=self.engagement_id,
                        agent_type="individual",
                    )

                elif task_key in self.active_tasks:
                    # Update existing task
                    task_id = self.active_tasks[task_key]

                    if step_info.get("type") == "thinking":
                        agent_monitor.record_thinking_phase(
                            task_id=task_id,
                            phase_description=step_info.get("content", "")[:100],
                        )
                    elif step_info.get("type") == "llm_call":
                        agent_monitor.start_llm_call(
                            task_id=task_id,
                            action=step_info.get("action", "unknown"),
                            prompt_length=len(str(step_info.get("prompt", ""))),
                        )

            # Log step activity
            logger.info(
                f"Step Callback - {step_entry['agent']}: {step_entry['content'][:100]}..."
            )

        except Exception as e:
            logger.error(f"Error in step callback: {e}")

    def _crew_step_callback(self, crew_info: Dict[str, Any]):
        """Callback for crew-level activities"""
        try:
            timestamp = datetime.now().isoformat()
            crew_name = crew_info.get("crew_name", "unknown")

            crew_entry = {
                "timestamp": timestamp,
                "crew_name": crew_name,
                "action": crew_info.get("action", "unknown"),
                "status": crew_info.get("status", "active"),
                "agents_involved": crew_info.get("agents", []),
                "current_task": crew_info.get("current_task", ""),
                "progress": crew_info.get("progress", 0),
                "metrics": crew_info.get("metrics", {}),
            }

            # Update current crew tracking
            self.callback_state["current_crew"] = crew_name

            # Log crew activity
            logger.info(
                f"Crew Callback - {crew_name}: {crew_entry['action']} ({crew_entry['status']})"
            )

        except Exception as e:
            logger.error(f"Error in crew step callback: {e}")

    def _task_completion_callback(self, task_info: Dict[str, Any]):
        """Callback for task completion events with persistence"""
        try:
            timestamp = datetime.now().isoformat()
            agent_name = task_info.get("agent", "unknown")
            task_name = task_info.get("task_name", "unknown")

            completion_entry = {
                "timestamp": timestamp,
                "task_id": task_info.get("task_id", "unknown"),
                "task_name": task_name,
                "agent": agent_name,
                "crew": task_info.get("crew", "unknown"),
                "status": task_info.get("status", "completed"),
                "duration": task_info.get("duration", 0),
                "output_size": len(str(task_info.get("output", ""))),
                "success": task_info.get("success", True),
                "quality_score": task_info.get("quality_score", 0.0),
            }

            # Update current task tracking
            self.callback_state["current_task"] = completion_entry["task_name"]

            # Calculate performance metrics
            if completion_entry["success"]:
                crew_name = completion_entry["crew"]
                if crew_name not in self.callback_state["performance_metrics"]:
                    self.callback_state["performance_metrics"][crew_name] = {
                        "completed_tasks": 0,
                        "total_duration": 0,
                        "average_quality": 0.0,
                        "success_rate": 1.0,
                    }

                metrics = self.callback_state["performance_metrics"][crew_name]
                metrics["completed_tasks"] += 1
                metrics["total_duration"] += completion_entry["duration"]

                # Update average quality score
                current_avg = metrics["average_quality"]
                new_score = completion_entry["quality_score"]
                task_count = metrics["completed_tasks"]
                metrics["average_quality"] = (
                    (current_avg * (task_count - 1)) + new_score
                ) / task_count

            # Complete task in agent monitor
            if AGENT_MONITOR_AVAILABLE and agent_name != "unknown":
                task_key = f"{agent_name}:{task_name}"

                if task_key in self.active_tasks:
                    task_id = self.active_tasks[task_key]

                    # Extract token usage if available
                    token_usage = None
                    if "token_usage" in task_info:
                        token_usage = task_info["token_usage"]
                    elif "llm_usage" in task_info:
                        llm_usage = task_info["llm_usage"]
                        token_usage = {
                            "input_tokens": llm_usage.get("prompt_tokens", 0),
                            "output_tokens": llm_usage.get("completion_tokens", 0),
                            "total_tokens": llm_usage.get("total_tokens", 0),
                        }

                    # Complete with metrics
                    agent_monitor.complete_task_with_metrics(
                        task_id=task_id,
                        result=str(task_info.get("output", ""))[:500],
                        confidence_score=completion_entry["quality_score"],
                        token_usage=token_usage,
                        memory_usage_mb=task_info.get("memory_usage_mb"),
                    )

                    # Clean up tracking
                    del self.active_tasks[task_key]

                    # Check for discovered patterns
                    if "patterns" in task_info:
                        for pattern in task_info["patterns"]:
                            agent_monitor.discover_pattern(
                                agent_name=agent_name,
                                pattern_id=pattern.get("id", str(uuid.uuid4())),
                                pattern_data=pattern,
                                task_id=task_id,
                                confidence_score=pattern.get("confidence", 0.5),
                                client_account_id=self.client_account_id,
                                engagement_id=self.engagement_id,
                            )

            # Log task completion
            logger.info(
                f"Task Completion - {completion_entry['task_name']}: {completion_entry['status']} "
                f"in {completion_entry['duration']}s"
            )

            # Record in agent registry for real performance tracking
            if AGENT_REGISTRY_AVAILABLE and completion_entry["agent"] != "unknown":
                try:
                    agent_registry.record_task_completion(
                        agent_name=completion_entry["agent"],
                        crew_name=completion_entry["crew"],
                        task_info=task_info,
                    )
                except Exception as registry_error:
                    logger.warning(
                        f"Failed to record task completion in agent registry: {registry_error}"
                    )

        except Exception as e:
            logger.error(f"Error in task completion callback: {e}")

    def _error_callback(self, error_info: Dict[str, Any]):
        """Callback for error handling and recovery"""
        try:
            timestamp = datetime.now().isoformat()

            error_entry = {
                "timestamp": timestamp,
                "error_type": error_info.get("error_type", "unknown"),
                "error_message": str(error_info.get("error", "")),
                "component": error_info.get("component", "unknown"),
                "crew": error_info.get(
                    "crew", self.callback_state.get("current_crew", "unknown")
                ),
                "agent": error_info.get(
                    "agent", self.callback_state.get("current_agent", "unknown")
                ),
                "task": error_info.get(
                    "task", self.callback_state.get("current_task", "unknown")
                ),
                "severity": error_info.get("severity", "medium"),
                "recoverable": error_info.get("recoverable", True),
                "recovery_action": error_info.get("recovery_action", "none"),
                "context": error_info.get("context", {}),
            }

            # Store in error history
            self.callback_state["error_history"].append(error_entry)

            # Log error with appropriate level
            severity = error_entry["severity"]
            error_msg = (
                f"Error in {error_entry['component']}: {error_entry['error_message']}"
            )

            if severity == "critical":
                logger.critical(error_msg)
            elif severity == "high":
                logger.error(error_msg)
            elif severity == "medium":
                logger.warning(error_msg)
            else:
                logger.info(error_msg)

            # Trigger recovery actions if needed
            if error_entry["recoverable"] and error_entry["recovery_action"] != "none":
                self._execute_recovery_action(error_entry)

        except Exception as e:
            logger.critical(f"Error in error callback (meta-error): {e}")

    def _agent_callback(self, agent_info: Dict[str, Any]):
        """Callback for individual agent activities"""
        try:
            timestamp = datetime.now().isoformat()

            agent_entry = {
                "timestamp": timestamp,
                "agent_name": agent_info.get("agent_name", "unknown"),
                "agent_role": agent_info.get("role", "unknown"),
                "crew": agent_info.get("crew", "unknown"),
                "action": agent_info.get("action", "unknown"),
                "tool_used": agent_info.get("tool", "none"),
                "memory_accessed": agent_info.get("memory_accessed", False),
                "collaboration_event": agent_info.get("collaboration", False),
                "performance_score": agent_info.get("performance_score", 0.0),
            }

            # Update current agent tracking
            self.callback_state["current_agent"] = agent_entry["agent_name"]

            # Log agent activity
            logger.debug(
                f"Agent Activity - {agent_entry['agent_name']}: {agent_entry['action']}"
            )

        except Exception as e:
            logger.error(f"Error in agent callback: {e}")

    def _execute_recovery_action(self, error_entry: Dict[str, Any]):
        """Execute recovery actions for errors"""
        try:
            recovery_action = error_entry["recovery_action"]

            if recovery_action == "retry_with_fallback":
                logger.info(
                    f"Executing retry with fallback for {error_entry['component']}"
                )
                # Implement specific retry logic here

            elif recovery_action == "skip_and_continue":
                logger.info(
                    f"Skipping failed component {error_entry['component']} and continuing"
                )
                # Mark component as skipped

            elif recovery_action == "use_cached_result":
                logger.info(f"Using cached result for {error_entry['component']}")
                # Implement cache lookup and usage

            elif recovery_action == "graceful_degradation":
                logger.info(
                    f"Applying graceful degradation for {error_entry['component']}"
                )
                # Implement simplified processing

            else:
                logger.warning(f"Unknown recovery action: {recovery_action}")

        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")

    def get_callback_metrics(self) -> Dict[str, Any]:
        """Get comprehensive callback and monitoring metrics"""
        return {
            "callback_state": self.callback_state,
            "error_summary": {
                "total_errors": len(self.callback_state["error_history"]),
                "critical_errors": len(
                    [
                        e
                        for e in self.callback_state["error_history"]
                        if e["severity"] == "critical"
                    ]
                ),
                "recoverable_errors": len(
                    [
                        e
                        for e in self.callback_state["error_history"]
                        if e["recoverable"]
                    ]
                ),
                "recent_errors": [e for e in self.callback_state["error_history"][-5:]],
            },
            "performance_summary": self.callback_state["performance_metrics"],
            "step_completion_rate": (
                self.callback_state["completed_steps"]
                / self.callback_state["total_steps"]
                if self.callback_state["total_steps"] > 0
                else 0
            ),
        }
