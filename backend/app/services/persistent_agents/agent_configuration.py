"""
Agent Configuration Module

This module contains agent configuration functionality extracted from
tenant_scoped_agent_pool.py to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AgentConfiguration:
    """Manages agent configurations and templates"""

    @classmethod
    def get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """Get configuration for specific agent type with enhanced templates"""
        configs = {
            "data_analyst": {
                "role": "Senior Data Analyst",
                "goal": "Analyze and validate data integrity, identify patterns, and ensure data quality",
                "backstory": "You are an expert data analyst with deep experience in data validation, "
                "pattern recognition, and quality assessment. You excel at identifying "
                "anomalies, inconsistencies, and opportunities for data improvement.",
                "tools": [
                    "data_validation",
                    "statistical_analysis",
                    "pattern_detection",
                ],
                "provider": "openai",
                "config": {
                    "temperature": 0.1,
                    "max_tokens": 2000,
                },
            },
            "quality_assessor": {
                "role": "Quality Assessment Specialist",
                "goal": "Assess data quality, completeness, and reliability for migration readiness",
                "backstory": "You are a meticulous quality assessor with expertise in data quality "
                "frameworks, completeness analysis, and migration readiness evaluation. "
                "Your assessments are thorough and actionable.",
                "tools": [
                    "quality_metrics",
                    "completeness_analysis",
                    "validation_rules",
                ],
                "provider": "openai",
                "config": {
                    "temperature": 0.2,
                    "max_tokens": 1500,
                },
            },
            "business_value_analyst": {
                "role": "Business Value Analyst",
                "goal": "Evaluate business impact, ROI, and strategic value of migration initiatives",
                "backstory": "You are a senior business analyst with deep understanding of cloud "
                "economics, migration ROI, and business impact assessment. You provide "
                "data-driven insights that guide strategic decisions.",
                "tools": ["roi_calculator", "cost_analysis", "business_metrics"],
                "provider": "openai",
                "config": {
                    "temperature": 0.3,
                    "max_tokens": 2500,
                },
            },
            "field_mapper": {
                "role": "Field Mapping Specialist",
                "goal": "Create intelligent field mappings between source and target systems",
                "backstory": "You are an expert in data mapping with deep knowledge of common "
                "field patterns, data transformation rules, and semantic matching. "
                "You excel at creating accurate, confident field mappings.",
                "tools": [
                    "field_analysis",
                    "semantic_matching",
                    "transformation_rules",
                ],
                "provider": "openai",
                "config": {
                    "temperature": 0.1,
                    "max_tokens": 1800,
                },
            },
            "risk_assessment_agent": {
                "role": "Risk Assessment Specialist",
                "goal": "Identify, evaluate, and provide mitigation strategies for migration risks",
                "backstory": "You are a seasoned risk management professional with expertise in "
                "cloud migration risks, security assessments, and risk mitigation. "
                "Your assessments help prevent costly migration issues.",
                "tools": ["risk_analysis", "security_assessment", "compliance_check"],
                "provider": "openai",
                "config": {
                    "temperature": 0.2,
                    "max_tokens": 2200,
                },
            },
            "pattern_discovery_agent": {
                "role": "Pattern Discovery Analyst",
                "goal": "Discover hidden patterns, relationships, and insights in migration data",
                "backstory": "You are a data scientist specialized in pattern recognition and "
                "anomaly detection. You excel at uncovering hidden relationships "
                "and providing actionable insights from complex datasets.",
                "tools": ["pattern_analysis", "clustering", "anomaly_detection"],
                "provider": "openai",
                "config": {
                    "temperature": 0.4,
                    "max_tokens": 2000,
                },
            },
            "memory_manager": {
                "role": "Memory Management Agent",
                "goal": "Manage agent memory, learning, and knowledge retention",
                "backstory": "You are responsible for maintaining agent memory, organizing "
                "knowledge, and ensuring effective learning across agent interactions.",
                "tools": ["memory_storage", "knowledge_graph", "learning_optimizer"],
                "provider": "openai",
                "config": {
                    "temperature": 0.1,
                    "max_tokens": 1500,
                },
            },
            "asset_inventory_agent": {
                "role": "Asset Inventory Specialist",
                "goal": "Create database asset records efficiently from cleaned CMDB data",
                "backstory": "You are an expert asset inventory specialist focused on direct execution "
                "of asset creation tasks. You transform validated CMDB data into database records "
                "without extensive analysis, ensuring efficient and accurate asset cataloging.",
                "tools": [
                    "asset_creation",
                    "data_validation",
                ],
                "provider": "openai",
                "config": {
                    "temperature": 0.1,
                    "max_tokens": 1500,
                },
            },
        }

        # Return specific config or generic fallback
        return configs.get(agent_type, cls._get_generic_config(agent_type))

    @classmethod
    def _get_generic_config(cls, agent_type: str) -> Dict[str, Any]:
        """Get generic configuration for unknown agent types"""
        return {
            "role": f"Generic {agent_type.replace('_', ' ').title()}",
            "goal": f"Perform {agent_type} tasks with learning capabilities",
            "backstory": f"You are a specialized {agent_type} agent with memory and learning capabilities.",
            "tools": [],
            "provider": "openai",
            "config": {
                "temperature": 0.2,
                "max_tokens": 1500,
            },
        }

    @classmethod
    def extract_context_info(cls, context) -> Dict[str, Any]:
        """Extract context information for agent configuration"""
        try:
            context_info = {
                "client_account_id": getattr(context, "client_account_id", None),
                "engagement_id": getattr(context, "engagement_id", None),
                "user_id": getattr(context, "user_id", None),
            }

            # Add additional context if available
            if hasattr(context, "request_id"):
                context_info["request_id"] = context.request_id
            if hasattr(context, "flow_id"):
                context_info["flow_id"] = context.flow_id

            return context_info

        except Exception as e:
            logger.error(f"Failed to extract context info: {e}")
            return {
                "client_account_id": None,
                "engagement_id": None,
                "user_id": None,
            }

    @classmethod
    async def warm_up_agent(cls, agent, agent_type: str):
        """Warm up agent with initial context and capabilities"""
        try:
            # Perform basic agent initialization
            logger.debug(f"🔥 Warming up {agent_type} agent")

            # Set execution count if not present
            if not hasattr(agent, "_execution_count"):
                agent._execution_count = 0

            # Initialize memory if available
            if hasattr(agent, "memory") and agent.memory:
                logger.debug(f"Memory initialized for {agent_type}")

            # Log agent readiness
            logger.info(f"✅ {agent_type} agent warmed up and ready")

        except Exception as e:
            logger.error(f"❌ Agent warm-up failed for {agent_type}: {e}")
            # Don't raise - agent can still function without warm-up
