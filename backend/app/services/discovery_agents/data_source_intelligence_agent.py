"""
Data Source Intelligence Agent
Analyzes incoming data (CMDB, migration tools, documentation) to understand format, structure, and content patterns.
"""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime
from langchain.tools import tool
from pydantic import BaseModel, Field
from crewai import Agent
import asyncio

if TYPE_CHECKING:
    from app.services.crewai_flow_handlers.flow_state_handler import DiscoveryFlowState

from app.models.agent_communication import ConfidenceLevel, DataClassification, QuestionType, AgentInsight
from .data_source_handlers import (
    SourceTypeAnalyzer,
    DataStructureAnalyzer,
    QualityAnalyzer,
    InsightGenerator,
    QuestionGenerator
)
from app.services.tools.field_mapping_tool import field_mapping_tool

logger = logging.getLogger(__name__)

class DataSourceIntelligenceAgent:
    """
    Agent specialized in analyzing data sources to understand their format, structure, and migration value.
    Uses agentic intelligence rather than hardcoded heuristics.
    """
    
    def __init__(self):
        self.agent_id = "data_source_intelligence_001"
        self.agent_name = "Data Source Intelligence Agent"
        self.tools = {}
        self._load_tools()
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Initialize specialized handlers
        self.source_type_analyzer = SourceTypeAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.data_structure_analyzer = DataStructureAnalyzer()
        self.insight_generator = InsightGenerator()
        self.question_generator = QuestionGenerator()
        
        # Pattern learning memory (starts empty, learns over time)
        self.learned_patterns = {
            "cmdb_formats": [],
            "migration_tool_patterns": [],
            "documentation_indicators": [],
            "field_name_patterns": [],
            "data_quality_indicators": []
        }
        
        self.agent = self._create_agent()
        
        logger.info("Initialized Data Source Intelligence Agent and its handlers successfully.")
    
    def _create_agent(self):
        """Create the CrewAI agent."""
        try:
            from crewai import Agent
            
            # Try to get LLM from crewai service
            llm = None
            try:
                from app.services.crewai_flow_service import crewai_flow_service
                llm = crewai_flow_service.llm
            except ImportError:
                logger.debug("CrewAI flow service not available - agent will use default LLM")
            
            agent = Agent(
                role="Data Source Intelligence Specialist",
                goal="Analyze and understand any given data source, including its structure, quality, and potential value for migration",
                backstory=(
                    "You are an expert AI assistant designed to be the first point of contact for new data sources. "
                    "Your primary function is to perform a comprehensive, agentic analysis without relying on predefined rules. "
                    "You intelligently assess data formats, structures, and content to provide actionable insights. "
                    "You learn from user feedback to continuously improve your analytical capabilities."
                ),
                llm=llm,
                allow_delegation=False,
                verbose=True,
                memory=True
            )
            agent.tools = list(self.tools.values())
            return agent
        except ImportError:
            logger.error("CrewAI not available - agent creation skipped")
            return None
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
    
    def _load_tools(self):
        """Load required tools for the agent."""
        # Directly use the imported tool instance
        self.tools['field_mapping_tool'] = field_mapping_tool
        logger.info("Loaded tools for DataSourceIntelligenceAgent")
    
    async def analyze_data_source(self, 
                                data_source: Dict[str, Any], 
                                flow_state: "DiscoveryFlowState",
                                page_context: str = "data-import") -> Dict[str, Any]:
        """
        Main entry point for analyzing any data source.
        
        Args:
            data_source: Contains file_data, metadata, upload_context
            flow_state: Current flow state
            page_context: UI page where this analysis is happening
            
        Returns:
            Analysis results with agent insights and questions
        """
        try:
            analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract data for analysis
            file_data = data_source.get('file_data', [])
            metadata = data_source.get('metadata', {})
            
            logger.info(f"Starting data source analysis: {analysis_id}")
            
            # Perform multi-dimensional analysis using handlers
            analysis_result = {
                "analysis_id": analysis_id,
                "agent_analysis": await self._perform_comprehensive_analysis(
                    file_data, metadata
                ),
                "data_classification": await self.quality_analyzer.classify_data_quality(file_data),
                "agent_insights": await self.insight_generator.generate(file_data),
                "clarification_questions": await self.question_generator.generate_clarification_questions(
                    file_data, metadata, page_context
                ),
                "confidence_assessment": await self._assess_analysis_confidence(file_data),
                "next_steps": await self._recommend_next_steps(file_data, metadata)
            }
            
            # Store analysis for learning
            self.analysis_history.append(analysis_result)
            
            # Add data classification to UI bridge
            if analysis_result.get("data_classification"):
                classification_data = analysis_result["data_classification"]
                
                # Map classification string to enum properly
                classification_str = classification_data.get("overall_classification", "good_data")
                if classification_str == "good_data":
                    classification_type = DataClassification.GOOD_DATA
                elif classification_str == "needs_clarification":
                    classification_type = DataClassification.NEEDS_CLARIFICATION
                elif classification_str == "unusable":
                    classification_type = DataClassification.UNUSABLE
                else:
                    classification_type = DataClassification.GOOD_DATA  # Default fallback
                
                # Store each data item with classification (when available)
                try:
                    from app.services.crewai_flow_service import crewai_flow_service
                    for i, row in enumerate(file_data[:10]):  # Sample first 10 rows for classification
                        crewai_flow_service.ui_interaction_handler.classification_handler.classify_data_item(
                            item_id=f"data_row_{i}_{analysis_id}",
                            data_type="asset_record",
                            content=row,
                            classification=classification_type,  # Pass enum, not .value
                            agent_analysis=classification_data,
                            confidence=ConfidenceLevel.MEDIUM,  # Pass enum, not .value
                            page=page_context,
                            issues=classification_data.get("issues", []),
                            recommendations=classification_data.get("recommendations", [])
                        )
                except ImportError:
                    # Skip UI bridge integration if not available
                    pass
            
            # Add insights to UI bridge (when available)
            try:
                from app.services.crewai_flow_service import crewai_flow_service
                for insight in analysis_result["agent_insights"]:
                    logger.info(f"Adding insight with page_context: {page_context}")
                    crewai_flow_service.ui_interaction_handler.add_agent_insight(
                        flow_state=flow_state,
                        agent_id=self.agent_id,
                        agent_name=self.agent_name,
                        insight_type=insight["type"],
                        title=insight["title"],
                        description=insight["description"],
                        confidence=ConfidenceLevel(insight["confidence"]),
                        supporting_data=insight["supporting_data"],
                        page=page_context,
                        actionable=insight.get("actionable", True)
                    )
                
                # Add clarification questions to UI bridge
                for question in analysis_result["clarification_questions"]:
                    logger.info(f"Adding question with page_context: {page_context}")
                    crewai_flow_service.ui_interaction_handler.add_agent_question(
                        flow_state=flow_state,
                        agent_id=self.agent_id,
                        agent_name=self.agent_name,
                        question_type=QuestionType(question["type"]),
                        page=page_context,
                        title=question["title"],
                        question=question["question"],
                        context=question["context"],
                        options=question.get("options"),
                        confidence=ConfidenceLevel(question["confidence"]),
                        priority=question["priority"]
                    )
            except ImportError:
                # Skip UI bridge integration if not available
                logger.debug("UI bridge not available - skipping insight/question integration")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Critical error in data source analysis: {e}", exc_info=True)
            # Re-raising the exception to ensure the frontend knows the analysis truly failed.
            # This will result in a 500 error on the API endpoint, which is the correct behavior.
            raise
    
    async def _perform_comprehensive_analysis(self, data: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a comprehensive analysis of the data using all available handlers."""
        
        source_type_result = await self.source_type_analyzer.analyze(data, metadata)
        quality_result = await self.quality_analyzer.classify_data_quality(data)
        content_result = await self.data_structure_analyzer.analyze_data_structure(data)
        insights_result = await self.insight_generator.generate_intelligent_insights(data, metadata)

        # Combine results into a structured response
        analysis_summary = {
            "source_type_analysis": source_type_result,
            "quality_analysis": quality_result,
            "data_structure_analysis": content_result,
            "insights": insights_result
        }
        
        return analysis_summary
    
    async def _assess_analysis_confidence(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess confidence in the analysis results."""
        
        if not data:
            return {
                "overall_confidence": ConfidenceLevel.UNCERTAIN.value,
                "reasoning": "No data provided for analysis",
                "confidence_factors": {}
            }
        
        # Assess different confidence factors
        sample_size = len(data)
        structure_consistency = await self._assess_structure_consistency(data)
        data_completeness = await self._assess_data_completeness(data)
        
        confidence_factors = {
            "sample_size": min(sample_size / 100, 1.0),  # More data = higher confidence
            "structure_consistency": structure_consistency,
            "data_completeness": data_completeness
        }
        
        # Calculate overall confidence
        overall_score = sum(confidence_factors.values()) / len(confidence_factors)
        
        if overall_score >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif overall_score >= 0.6:
            confidence_level = ConfidenceLevel.MEDIUM
        elif overall_score >= 0.4:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.UNCERTAIN
        
        return {
            "overall_confidence": confidence_level.value,
            "confidence_score": overall_score,
            "reasoning": f"Based on {len(data)} records with {overall_score:.1%} confidence factors",
            "confidence_factors": confidence_factors
        }
    
    async def _recommend_next_steps(self, data: List[Dict[str, Any]], 
                                  metadata: Dict[str, Any]) -> List[str]:
        """Recommend next steps based on analysis results."""
        
        recommendations = []
        
        if not data:
            recommendations.append("Upload a data file to begin analysis")
            return recommendations
        
        # Get quality assessment
        quality_result = await self.quality_analyzer.classify_data_quality(data)
        quality_classification = quality_result.get("overall_classification")
        
        if quality_classification == DataClassification.GOOD_DATA.value:
            recommendations.append("Data quality is good - proceed with asset mapping")
            recommendations.append("Review agent insights for optimization opportunities")
        elif quality_classification == DataClassification.NEEDS_CLARIFICATION.value:
            recommendations.append("Address agent clarification questions to improve data quality")
            recommendations.append("Consider data cleanup before proceeding")
        else:
            recommendations.append("Data quality issues detected - review and clean data")
            recommendations.append("Validate data source and format")
        
        # Migration value assessment
        migration_value = await self.data_structure_analyzer.assess_migration_value(data)
        value_level = migration_value.get("migration_value", "low")
        
        if value_level == "high":
            recommendations.append("High migration value detected - prioritize this data source")
        elif value_level == "medium":
            recommendations.append("Good migration value - supplement with additional data sources")
        else:
            recommendations.append("Limited migration value - consider alternative data sources")
        
        return recommendations
    
    async def _assess_structure_consistency(self, data: List[Dict[str, Any]]) -> float:
        """Assess how consistent the data structure is."""
        
        if len(data) <= 1:
            return 1.0
        
        # Check for consistent column structure
        column_sets = [set(row.keys()) for row in data[:10]]  # Sample first 10 rows
        
        if not column_sets:
            return 0.0
        
        # Calculate consistency as ratio of common columns
        common_columns = set.intersection(*column_sets)
        all_columns = set.union(*column_sets)
        
        return len(common_columns) / len(all_columns) if all_columns else 0.0
    
    async def _assess_data_completeness(self, data: List[Dict[str, Any]]) -> float:
        """Assess overall data completeness."""
        
        if not data:
            return 0.0
        
        # Sample data for completeness assessment
        sample_data = data[:20]
        total_fields = 0
        filled_fields = 0
        
        for row in sample_data:
            for value in row.values():
                total_fields += 1
                if value is not None and str(value).strip():
                    filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    async def _detect_relationship_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect basic relationship patterns in the data."""
        
        relationships = {
            "potential_keys": [],
            "grouping_fields": [],
            "dependency_hints": []
        }
        
        if not data or len(data) < 2:
            return relationships
        
        # Sample data for pattern detection
        sample_data = data[:20]
        all_columns = set()
        for row in sample_data:
            all_columns.update(row.keys())
        
        # Check for potential unique identifiers
        for column in all_columns:
            values = [str(row.get(column, "")) for row in sample_data if row.get(column)]
            if len(values) == len(set(values)) and len(values) > len(sample_data) * 0.8:
                relationships["potential_keys"].append(column)
        
        # Check for grouping fields
        for column in all_columns:
            values = [str(row.get(column, "")) for row in sample_data if row.get(column)]
            unique_ratio = len(set(values)) / len(values) if values else 0
            if 0.1 < unique_ratio < 0.5:  # Some repetition but not too much
                relationships["grouping_fields"].append(column)
        
        return relationships
    
    def learn_from_feedback(self, feedback: Dict[str, Any]) -> None:
        """Learn from user feedback to improve future analysis."""
        
        feedback_type = feedback.get("type")
        feedback_data = feedback.get("data", {})
        
        logger.info(f"Learning from feedback: {feedback_type}")
        
        if feedback_type == "source_type_correction":
            # Learn from source type corrections
            corrected_type = feedback_data.get("corrected_type")
            original_analysis = feedback_data.get("original_analysis", {})
            
            # Update learned patterns based on correction
            self.source_type_analyzer.learn_from_feedback(
                original_analysis.get("predicted_type"),
                original_analysis.get("columns", []),
                corrected_type
            )
        
        elif feedback_type == "field_mapping_correction":
            # Learn from field mapping corrections
            field_mappings = feedback_data.get("field_mappings", {})
            self._update_field_mapping_patterns(field_mappings)
        
        elif feedback_type == "quality_assessment_correction":
            # Learn from quality assessment corrections
            corrected_classification = feedback_data.get("corrected_classification")
            self._update_quality_patterns(corrected_classification, feedback_data)
        
        # Store learning experience
        learning_experience = {
            "timestamp": datetime.utcnow().isoformat(),
            "feedback_type": feedback_type,
            "feedback_data": feedback_data,
            "agent_id": self.agent_id
        }
        
        crewai_flow_service.ui_interaction_handler.set_cross_page_context(
            f"learning_experience_{datetime.utcnow().timestamp()}", 
            learning_experience,
            "data_source_intelligence"
        )
    
    def _update_field_mapping_patterns(self, field_mappings: Dict[str, str]) -> None:
        """Update field mapping patterns based on user corrections."""
        
        for original_field, corrected_mapping in field_mappings.items():
            # Store the mapping pattern for future use
            if "field_name_patterns" not in self.learned_patterns:
                self.learned_patterns["field_name_patterns"] = []
            
            self.learned_patterns["field_name_patterns"].append({
                "original": original_field,
                "mapped_to": corrected_mapping,
                "learned_at": datetime.utcnow().isoformat()
            })
    
    def _update_quality_patterns(self, corrected_classification: str, 
                               feedback_data: Dict[str, Any]) -> None:
        """Update quality assessment patterns based on user corrections."""
        
        quality_indicators = feedback_data.get("quality_indicators", {})
        
        if "data_quality_indicators" not in self.learned_patterns:
            self.learned_patterns["data_quality_indicators"] = []
        
        self.learned_patterns["data_quality_indicators"].append({
            "corrected_classification": corrected_classification,
            "indicators": quality_indicators,
            "learned_at": datetime.utcnow().isoformat()
        })
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and learning progress."""
        
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "analyses_performed": len(self.analysis_history),
            "learned_patterns": {
                "cmdb_patterns": len(self.learned_patterns.get("cmdb_formats", [])),
                "migration_patterns": len(self.learned_patterns.get("migration_tool_patterns", [])),
                "field_mappings": len(self.learned_patterns.get("field_name_patterns", [])),
                "quality_patterns": len(self.learned_patterns.get("data_quality_indicators", []))
            },
            "handler_status": {
                "source_type_analyzer": self.source_type_analyzer.analyzer_id,
                "data_structure_analyzer": self.data_structure_analyzer.analyzer_id,
                "quality_analyzer": self.quality_analyzer.analyzer_id,
                "insight_generator": self.insight_generator.generator_id,
                "question_generator": self.question_generator.generator_id
            }
        }

    def _get_page_context_summary(self, page_context: str) -> Dict[str, Any]:
        """
        Get a summary of the current page context from the agent UI bridge.
        (This method is now deprecated)
        """
        return {
            "status": "deprecated",
            "message": "Direct page context summary is no longer available in the new flow-based service."
        }

# Global instance for use across the application
data_source_intelligence_agent = DataSourceIntelligenceAgent() 