"""
Optimized Base Crew Configuration
Implements performance optimizations for all CrewAI crews:
- Enhanced memory integration
- Parallel task execution
- Response caching
- Optimized LLM settings
- Performance monitoring
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task

from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)
from crewai.memory import LongTermMemory, ShortTermMemory

from app.services.agent_learning_system import LearningContext
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.llm_config import get_crewai_llm
from app.services.performance.response_optimizer import response_optimizer

logger = logging.getLogger(__name__)


class OptimizedCrewBase:
    """Base class for optimized CrewAI crews with enhanced memory and performance"""

    def __init__(
        self,
        crewai_service,
        context: Optional[LearningContext] = None,
        enable_memory: bool = False,  # Per ADR-024: Use TenantMemoryManager
        enable_caching: bool = True,
        enable_parallel: bool = True,
    ):
        self.crewai_service = crewai_service
        self.context = context or LearningContext()
        self.enable_memory = enable_memory
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel

        # Get optimized LLM configuration
        self.llm_model = self._get_optimized_llm()

        # Initialize memory configuration
        self.memory_config = self._get_memory_configuration()

        # Performance tracking
        self.performance_metrics = {
            "tasks_executed": 0,
            "avg_task_duration": 0.0,
            "memory_hits": 0,
            "cache_hits": 0,
        }

        logger.info(
            f"🚀 Optimized crew base initialized with memory={enable_memory}, "
            f"caching={enable_caching}, parallel={enable_parallel}"
        )

    def _get_optimized_llm(self):
        """Get optimized LLM configuration"""
        try:
            llm_model = get_crewai_llm()
            # Note: With string model names, we can't directly set temperature/max_tokens
            # These need to be configured in the agent creation or through environment variables
            return llm_model

        except Exception as e:
            logger.warning(f"Failed to get optimized LLM: {e}")
            return getattr(self.crewai_service, "llm", None)

    def _get_memory_configuration(self) -> Optional[Dict[str, Any]]:
        """Get memory configuration for crew"""
        if not self.enable_memory:
            return None

        try:
            # Use CrewAI's native memory with our enhanced backend
            memory_config = {
                "memory": False,  # Per ADR-024: Use TenantMemoryManager
                "long_term_memory": LongTermMemory(
                    storage_type="chroma",
                    embedder_config={
                        "provider": "openai",
                        "model": "text-embedding-3-small",
                    },
                ),
                "short_term_memory": ShortTermMemory(),
                "memory_config": {"max_items": 1000, "similarity_threshold": 0.7},
            }

            return memory_config

        except Exception as e:
            logger.warning(f"Failed to configure CrewAI memory: {e}")
            return {"memory": False}  # Per ADR-024: Use TenantMemoryManager

    def create_optimized_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List] = None,
        **kwargs,
    ) -> Agent:
        """Create an optimized agent with enhanced configuration"""

        # Default optimized settings
        agent_config = {
            "role": role,
            "goal": goal,
            "backstory": backstory,
            "llm": self.llm_model,
            "tools": tools or [],
            "verbose": True,
            "max_iter": 3,  # Limit iterations for performance
            "max_execution_time": 300,  # 5 minute timeout
            "allow_delegation": kwargs.get("allow_delegation", False),
            "system_template": kwargs.get("system_template", None),
            "prompt_template": kwargs.get("prompt_template", None),
            "response_template": kwargs.get("response_template", None),
        }

        # Add memory configuration if enabled
        if self.enable_memory and self.memory_config:
            agent_config["memory"] = False  # Per ADR-024: Use TenantMemoryManager

        # Apply any additional kwargs
        agent_config.update(kwargs)

        # Create agent
        agent = create_agent(**agent_config)

        # Initialize agent-specific memory context
        if self.enable_memory:
            asyncio.create_task(self._initialize_agent_memory(agent, role))

        return agent

    async def _initialize_agent_memory(self, agent: Agent, role: str):
        """Initialize memory for specific agent"""
        try:
            # Store agent initialization in memory
            await enhanced_agent_memory.store_memory(
                {
                    "agent_role": role,
                    "agent_id": id(agent),
                    "initialization_time": datetime.utcnow().isoformat(),
                    "capabilities": agent.tools if hasattr(agent, "tools") else [],
                },
                memory_type="agent_metadata",
                context=self.context,
            )

            # Load relevant past experiences
            past_experiences = await enhanced_agent_memory.retrieve_memories(
                {"role": role, "type": "successful_execution"},
                context=self.context,
                limit=5,
            )

            if past_experiences:
                self.performance_metrics["memory_hits"] += 1
                logger.info(
                    f"Loaded {len(past_experiences)} past experiences for {role}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize agent memory: {e}")

    def create_optimized_task(
        self, description: str, agent: Agent, expected_output: str, **kwargs
    ) -> Task:
        """Create an optimized task with performance settings"""

        task_config = {
            "description": description,
            "agent": agent,
            "expected_output": expected_output,
            "max_execution_time": kwargs.get("max_execution_time", 300),
            "max_retry": kwargs.get("max_retry", 2),
            "human_input": kwargs.get("human_input", False),
            "async_execution": self.enable_parallel
            and kwargs.get("async_execution", False),
            "tools": kwargs.get("tools", []),
            "context": kwargs.get("context", []),
        }

        # Apply caching decorator if enabled
        if self.enable_caching:
            task_config["callback"] = self._create_cached_callback(agent.role)

        return create_task(**task_config)

    def _create_cached_callback(self, agent_role: str):
        """Create a cached callback for task execution"""

        async def cached_callback(task_output):
            # Cache successful task outputs
            if task_output and not task_output.get("error"):
                await response_optimizer.cache.set(
                    f"task_{agent_role}",
                    {"task_description": task_output.get("description", "")},
                    task_output,
                )
                self.performance_metrics["cache_hits"] += 1

        return cached_callback

    def create_optimized_crew(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.sequential,
        **kwargs,
    ) -> Crew:
        """Create an optimized crew with enhanced configuration"""

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
            "max_rpm": kwargs.get("max_rpm", 100),  # Rate limiting
            "share_crew": kwargs.get("share_crew", False),
            "step_callback": kwargs.get("step_callback", None),
            "task_callback": kwargs.get("task_callback", None),
        }

        # Add memory configuration
        if self.enable_memory and self.memory_config:
            crew_config.update(self.memory_config)

        # Enable parallel execution if configured
        if self.enable_parallel and process == Process.hierarchical:
            crew_config["manager_llm"] = self.llm
            crew_config["planning"] = True
            crew_config["planning_llm"] = self.llm

        # Apply any additional kwargs
        crew_config.update(kwargs)

        crew = create_crew(**crew_config)

        # Add performance monitoring
        self._add_performance_monitoring(crew)

        return crew

    def _add_performance_monitoring(self, crew: Crew):
        """Add performance monitoring to crew execution"""
        original_kickoff = crew.kickoff

        async def monitored_kickoff(*args, **kwargs):
            start_time = datetime.utcnow()

            try:
                # Check cache first if enabled
                if self.enable_caching:
                    cache_key = f"crew_{crew.__class__.__name__}_{str(args)}"
                    cached_result = await response_optimizer.cache.get(
                        "crew_execution", {"key": cache_key}
                    )
                    if cached_result:
                        logger.info("🎯 Crew execution cache hit")
                        return cached_result

                # Execute crew
                result = await original_kickoff(*args, **kwargs)

                # Track performance
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._update_performance_metrics(duration)

                # Store successful execution in memory
                if self.enable_memory and result:
                    await enhanced_agent_memory.store_memory(
                        {
                            "crew_type": crew.__class__.__name__,
                            "execution_time": duration,
                            "task_count": len(crew.tasks),
                            "result_summary": str(result)[:500],
                        },
                        memory_type="crew_execution",
                        context=self.context,
                    )

                # Cache result if enabled
                if self.enable_caching and result:
                    await response_optimizer.cache.set(
                        "crew_execution", {"key": cache_key}, result
                    )

                return result

            except Exception as e:
                logger.error(f"Crew execution failed: {e}")
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._update_performance_metrics(duration, success=False)
                raise

        crew.kickoff = monitored_kickoff

    def _update_performance_metrics(self, duration: float, success: bool = True):
        """Update performance metrics"""
        self.performance_metrics["tasks_executed"] += 1

        # Update average duration
        current_avg = self.performance_metrics["avg_task_duration"]
        total_tasks = self.performance_metrics["tasks_executed"]

        self.performance_metrics["avg_task_duration"] = (
            current_avg * (total_tasks - 1) + duration
        ) / total_tasks

        # Log performance
        status = "✅" if success else "❌"
        logger.info(
            f"{status} Task completed in {duration:.2f}s (avg: {self.performance_metrics['avg_task_duration']:.2f}s)"
        )

    async def optimize_crew_performance(self) -> Dict[str, Any]:
        """Optimize crew performance based on metrics"""
        optimization_results = {
            "memory_optimized": False,
            "cache_cleared": False,
            "recommendations": [],
        }

        try:
            # Optimize memory if needed
            if self.enable_memory:
                memory_stats = enhanced_agent_memory.get_memory_statistics()
                if memory_stats["total_memory_items"] > 5000:
                    await enhanced_agent_memory.optimize_memory_performance()
                    optimization_results["memory_optimized"] = True

            # Clear cache if hit rate is low
            if self.enable_caching:
                cache_stats = response_optimizer.get_performance_summary()
                if cache_stats.get("cache_hit_rate", 0) < 0.2:
                    response_optimizer.clear_cache()
                    optimization_results["cache_cleared"] = True

            # Generate recommendations
            if self.performance_metrics["avg_task_duration"] > 30:
                optimization_results["recommendations"].append(
                    "Consider enabling parallel task execution"
                )

            if self.performance_metrics.get("memory_hits", 0) < 10:
                optimization_results["recommendations"].append(
                    "Memory system underutilized - consider pre-loading relevant experiences"
                )

            return optimization_results

        except Exception as e:
            logger.error(f"Failed to optimize crew performance: {e}")
            return {"error": str(e)}

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            "crew_metrics": self.performance_metrics,
            "memory_enabled": self.enable_memory,
            "caching_enabled": self.enable_caching,
            "parallel_enabled": self.enable_parallel,
        }

        if self.enable_memory:
            report["memory_stats"] = enhanced_agent_memory.get_memory_statistics()

        if self.enable_caching:
            report["cache_stats"] = response_optimizer.get_performance_summary()

        return report


# Import required for async operations
