"""
Flow Validator

Validation logic for flow phases and transitions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FlowValidator:
    """Handles flow phase validation and AI-powered checks"""
    
    def __init__(self, flow_repo):
        """Initialize with flow repository for database operations"""
        self.flow_repo = flow_repo
    
    async def validate_and_get_next_phase(self, flow) -> str:
        """
        AI-powered validation of phase completion and determination of next phase.
        Uses agent intelligence to verify phase results.
        """
        try:
            logger.info(f"🤖 Starting intelligent phase validation for flow {flow.flow_id}")
            
            # Check data import phase
            if not flow.data_import_completed:
                return "data_import"
            
            data_import_valid = await self.validate_data_import(flow)
            if not data_import_valid:
                await self._reset_phase_with_insight(flow, "data_import", 
                    "AI validation detected insufficient data import results")
                return "data_import"
            
            # Check attribute mapping phase
            if not flow.attribute_mapping_completed:
                return "attribute_mapping"
            
            mapping_valid = await self.validate_attribute_mapping(flow)
            if not mapping_valid:
                await self._reset_phase_with_insight(flow, "attribute_mapping",
                    "AI validation detected insufficient field mapping results")
                return "attribute_mapping"
            
            # Check data cleansing phase
            if not flow.data_cleansing_completed:
                return "data_cleansing"
            
            cleansing_valid = await self.validate_data_cleansing(flow)
            if not cleansing_valid:
                await self._reset_phase_with_insight(flow, "data_cleansing",
                    "AI validation detected insufficient data cleansing results")
                return "data_cleansing"
            
            # Check remaining phases
            if not flow.inventory_completed:
                return "inventory"
            if not flow.dependencies_completed:
                return "dependencies"
            if not flow.tech_debt_completed:
                return "tech_debt"
            
            logger.info("🎉 All phases validated by AI - flow is complete")
            return "completed"
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return await self._determine_safe_fallback_phase(flow)
    
    async def validate_data_import(self, flow) -> bool:
        """AI-powered validation of data import completion"""
        try:
            logger.info(f"🤖 Validating data import for flow {flow.flow_id}")
            
            # Check for validation insights
            has_insights = await self._check_agent_insights(flow, "data_import", [
                "validation", "import", "records", "quality", "format"
            ])
            
            # Check for processed records
            has_records = await self._check_processed_records(flow)
            
            # Get AI confidence score
            confidence = await self._get_ai_quality_confidence(flow, "data_import")
            
            is_valid = has_insights and has_records and confidence >= 0.7
            
            logger.info(f"Data Import Validation: insights={has_insights}, "
                       f"records={has_records}, confidence={confidence:.2f}, valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Data import validation error: {e}")
            return False
    
    async def validate_attribute_mapping(self, flow) -> bool:
        """AI-powered validation of attribute mapping completion"""
        try:
            logger.info(f"🤖 Validating attribute mapping for flow {flow.flow_id}")
            
            # Check for mapping insights
            has_insights = await self._check_agent_insights(flow, "attribute_mapping", [
                "field_mapping", "attribute", "mapping", "confidence", "critical"
            ])
            
            # Check database mappings
            has_mappings = await self._check_database_field_mappings(flow)
            
            # Get AI confidence
            confidence = await self._get_ai_quality_confidence(flow, "attribute_mapping")
            
            is_valid = has_insights and has_mappings and confidence >= 0.6
            
            logger.info(f"Attribute Mapping Validation: insights={has_insights}, "
                       f"mappings={has_mappings}, confidence={confidence:.2f}, valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Attribute mapping validation error: {e}")
            return False
    
    async def validate_data_cleansing(self, flow) -> bool:
        """AI-powered validation of data cleansing completion"""
        try:
            logger.info(f"🤖 Validating data cleansing for flow {flow.flow_id}")
            
            # Check for cleansing insights
            has_insights = await self._check_agent_insights(flow, "data_cleansing", [
                "cleansing", "quality", "validation", "completeness", "consistency"
            ])
            
            # Check quality metrics
            has_metrics = await self._check_quality_metrics(flow)
            
            # Get AI confidence
            confidence = await self._get_ai_quality_confidence(flow, "data_cleansing")
            
            is_valid = has_insights and has_metrics and confidence >= 0.7
            
            logger.info(f"Data Cleansing Validation: insights={has_insights}, "
                       f"metrics={has_metrics}, confidence={confidence:.2f}, valid={is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Data cleansing validation error: {e}")
            return False
    
    async def _check_agent_insights(self, flow, phase: str, keywords: List[str]) -> bool:
        """Check if flow has relevant agent insights for the phase"""
        if not flow.crewai_state_data:
            return False
            
        state_data = flow.crewai_state_data
        if not isinstance(state_data, dict):
            return False
            
        agent_insights = state_data.get("agent_insights", [])
        if not agent_insights:
            return False
            
        # Look for insights related to this phase
        phase_insights = []
        for insight in agent_insights:
            if isinstance(insight, dict):
                content = str(insight.get("insight", "")).lower()
                # Check if any keywords match
                if any(keyword in content for keyword in keywords):
                    phase_insights.append(insight)
        
        has_recent_insights = len(phase_insights) > 0
        logger.info(f"Found {len(phase_insights)} insights for phase {phase}")
        
        return has_recent_insights
    
    async def _check_processed_records(self, flow) -> bool:
        """Check if flow has processed records"""
        if flow.crewai_state_data and isinstance(flow.crewai_state_data, dict):
            raw_data = flow.crewai_state_data.get("raw_data", [])
            processed_count = len(raw_data) if isinstance(raw_data, list) else 0
            return processed_count > 0
        return False
    
    async def _check_database_field_mappings(self, flow) -> bool:
        """Check if field mappings exist in database"""
        try:
            from app.models.field_mapping import FieldMapping
            from sqlalchemy import select, and_
            
            stmt = select(FieldMapping).where(
                and_(
                    FieldMapping.flow_id == str(flow.flow_id),
                    FieldMapping.is_approved == True
                )
            )
            result = await self.flow_repo.db.execute(stmt)
            mappings = result.scalars().all()
            
            return len(mappings) > 0
        except Exception as e:
            logger.error(f"Error checking field mappings: {e}")
            return False
    
    async def _check_quality_metrics(self, flow) -> bool:
        """Check if quality metrics exist for the flow"""
        if flow.crewai_state_data and isinstance(flow.crewai_state_data, dict):
            # Check for quality analysis results
            quality_data = flow.crewai_state_data.get("data_quality", {})
            cleansing_results = flow.crewai_state_data.get("data_cleansing_results", {})
            
            has_quality = bool(quality_data) or bool(cleansing_results)
            return has_quality
        return False
    
    async def _get_ai_quality_confidence(self, flow, phase: str) -> float:
        """Get AI confidence score for phase quality"""
        if not flow.crewai_state_data or not isinstance(flow.crewai_state_data, dict):
            return 0.0
            
        # Look for agent confidence scores
        agent_confidences = flow.crewai_state_data.get("agent_confidences", {})
        
        # Map phase names to agent names
        phase_to_agent = {
            "data_import": "data_import_validation",
            "attribute_mapping": "attribute_mapping",
            "data_cleansing": "data_cleansing"
        }
        
        agent_name = phase_to_agent.get(phase, phase)
        confidence = agent_confidences.get(agent_name, 0.0)
        
        # Normalize confidence to 0-1 range if it's a percentage
        if confidence > 1.0:
            confidence = confidence / 100.0
            
        return confidence
    
    async def _reset_phase_with_insight(self, flow, phase: str, reason: str):
        """Reset a phase with AI-generated insight"""
        agent_insight = {
            "agent": "AI Flow Validation System",
            "insight": f"Phase '{phase}' requires completion: {reason}",
            "action_required": f"Please complete the {phase.replace('_', ' ')} phase properly",
            "ai_recommendation": self._get_phase_recommendation(phase),
            "timestamp": datetime.now().isoformat(),
            "validation_failed": True
        }
        
        await self.flow_repo.update_phase_completion(
            flow_id=str(flow.flow_id),
            phase=phase,
            data={"reset_reason": reason, "ai_validation": "failed"},
            crew_status={"status": "reset", "reason": "agentic_validation_failed"},
            agent_insights=[agent_insight],
            completed=False
        )
    
    def _get_phase_recommendation(self, phase: str) -> str:
        """Get recommendation for completing a specific phase"""
        recommendations = {
            "data_import": "Ensure data is properly uploaded and validated by import agents",
            "attribute_mapping": "Complete field mappings with sufficient confidence scores",
            "data_cleansing": "Run data quality analysis and address any issues found",
            "inventory": "Create comprehensive asset inventory from cleansed data",
            "dependencies": "Analyze and map all application dependencies",
            "tech_debt": "Assess technical debt and migration complexity"
        }
        return recommendations.get(phase, f"Complete the {phase} phase with proper validation")
    
    async def _determine_safe_fallback_phase(self, flow) -> str:
        """Determine safe fallback phase when validation fails"""
        # Start from the beginning and find first incomplete phase
        phases = [
            ("data_import_completed", "data_import"),
            ("attribute_mapping_completed", "attribute_mapping"),
            ("data_cleansing_completed", "data_cleansing"),
            ("inventory_completed", "inventory"),
            ("dependencies_completed", "dependencies"),
            ("tech_debt_completed", "tech_debt")
        ]
        
        for attr, phase_name in phases:
            if not getattr(flow, attr, False):
                return phase_name
                
        return "completed"