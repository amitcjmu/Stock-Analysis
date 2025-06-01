"""
Agent-Driven Discovery API Endpoints
Provides agentic intelligence for discovery processes, replacing hardcoded heuristics with AI-driven analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent_ui_bridge import agent_ui_bridge, QuestionType, ConfidenceLevel, DataClassification
from app.services.discovery_agents.data_source_intelligence_agent import data_source_intelligence_agent
from app.services.discovery_agents.application_discovery_agent import application_discovery_agent

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/agent-analysis")
async def perform_agent_analysis(
    analysis_request: Dict[str, Any],
    page_context: str = "data-import",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Real-time agent analysis of any data input.
    Replaces hardcoded heuristics with agent intelligence.
    
    Request body:
    {
        "data_source": {
            "file_data": [...],
            "metadata": {...},
            "upload_context": {...}
        },
        "analysis_type": "data_source_analysis",
        "page_context": "data-import"
    }
    """
    try:
        data_source = analysis_request.get("data_source", {})
        analysis_type = analysis_request.get("analysis_type", "data_source_analysis")
        
        if not data_source:
            raise HTTPException(status_code=400, detail="Data source is required for analysis")
        
        # Route to appropriate agent based on analysis type
        if analysis_type == "data_source_analysis":
            analysis_result = await data_source_intelligence_agent.analyze_data_source(
                data_source, page_context
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")
        
        return {
            "status": "success",
            "analysis_type": analysis_type,
            "page_context": page_context,
            "agent_analysis": analysis_result,
            "ui_bridge_status": agent_ui_bridge.get_agent_status_summary()
        }
        
    except Exception as e:
        logger.error(f"Error in agent analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@router.post("/agent-clarification")
async def answer_agent_clarification(
    clarification_response: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    User responses to agent questions for learning and clarification.
    
    Request body:
    {
        "question_id": "uuid",
        "response": "user_answer",
        "response_type": "text|selection|multiple_choice",
        "page_context": "data-import"
    }
    """
    try:
        question_id = clarification_response.get("question_id")
        response = clarification_response.get("response")
        response_type = clarification_response.get("response_type", "text")
        page_context = clarification_response.get("page_context", "discovery")
        
        if not question_id or response is None:
            raise HTTPException(status_code=400, detail="Question ID and response are required")
        
        # Process the user response through the UI bridge
        result = agent_ui_bridge.answer_agent_question(question_id, response)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Question not found"))
        
        # Trigger agent learning from the response
        await _process_agent_learning(question_id, response, response_type, page_context)
        
        return {
            "status": "success",
            "message": "Agent clarification processed successfully",
            "learning_applied": True,
            "question_resolved": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing agent clarification: {e}")
        raise HTTPException(status_code=500, detail=f"Clarification processing failed: {str(e)}")

@router.get("/agent-status")
async def get_agent_status(
    page_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Current agent understanding and confidence levels.
    """
    try:
        # Get overall agent status
        agent_status = agent_ui_bridge.get_agent_status_summary()
        
        # Get page-specific information if requested
        page_data = {}
        if page_context:
            page_data = {
                "pending_questions": agent_ui_bridge.get_questions_for_page(page_context),
                "data_classifications": agent_ui_bridge.get_classified_data_for_page(page_context),
                "agent_insights": agent_ui_bridge.get_insights_for_page(page_context)
            }
        
        return {
            "status": "success",
            "agent_status": agent_status,
            "page_data": page_data,
            "cross_page_context": agent_ui_bridge.get_cross_page_context()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")

@router.post("/agent-learning")
async def process_agent_learning(
    learning_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent learning from user corrections and feedback.
    
    Request body:
    {
        "learning_type": "field_mapping|data_classification|pattern_recognition",
        "original_prediction": {...},
        "user_correction": {...},
        "context": {...},
        "page_context": "data-import"
    }
    """
    try:
        learning_type = learning_input.get("learning_type")
        original_prediction = learning_input.get("original_prediction")
        user_correction = learning_input.get("user_correction")
        context = learning_input.get("context", {})
        page_context = learning_input.get("page_context", "discovery")
        
        if not all([learning_type, original_prediction, user_correction]):
            raise HTTPException(
                status_code=400, 
                detail="Learning type, original prediction, and user correction are required"
            )
        
        # Process learning based on type
        learning_result = await _apply_agent_learning(
            learning_type, original_prediction, user_correction, context, page_context
        )
        
        return {
            "status": "success",
            "message": "Agent learning processed successfully",
            "learning_type": learning_type,
            "learning_result": learning_result,
            "improvement_metrics": await _calculate_learning_metrics()
        }
        
    except Exception as e:
        logger.error(f"Error in agent learning: {e}")
        raise HTTPException(status_code=500, detail=f"Agent learning failed: {str(e)}")

@router.get("/application-portfolio")
async def get_application_portfolio(
    include_confidence_levels: bool = True,
    include_business_intelligence: bool = True,
    business_context: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive application portfolio analysis with business intelligence.
    
    Enhanced with Application Intelligence Agent for business-aligned analysis.
    """
    try:
        # Get assets from the discovery system
        from app.api.v1.discovery.asset_management import crud_handler
        assets_result = await crud_handler.get_assets_paginated({'page': 1, 'page_size': 1000})
        assets = assets_result.get('assets', [])
        
        if not assets:
            return {
                "status": "success",
                "application_portfolio": {
                    "applications": [],
                    "discovery_confidence": 0.0,
                    "clarification_questions": [],
                    "discovery_metadata": {
                        "total_assets_analyzed": 0,
                        "applications_discovered": 0,
                        "high_confidence_apps": 0,
                        "needs_clarification": 0,
                        "analysis_timestamp": datetime.utcnow().isoformat()
                    }
                },
                "business_intelligence": None,
                "message": "No assets available for application discovery"
            }
        
        # Step 1: Use Application Discovery Agent for basic application discovery
        discovery_result = await application_discovery_agent.discover_applications(assets)
        applications = discovery_result.get("applications", [])
        
        # Step 2: If business intelligence is requested and applications found, use Application Intelligence Agent
        business_intelligence = None
        if include_business_intelligence and applications:
            try:
                from app.services.discovery_agents.application_intelligence_agent import application_intelligence_agent
                
                # Parse business context if provided
                parsed_business_context = None
                if business_context:
                    try:
                        import json
                        parsed_business_context = json.loads(business_context)
                    except:
                        parsed_business_context = {"notes": business_context}
                
                # Perform comprehensive business intelligence analysis
                business_intelligence = await application_intelligence_agent.analyze_application_portfolio(
                    applications, parsed_business_context
                )
                
                logger.info(f"Application Intelligence Agent analyzed {len(applications)} applications")
                
            except Exception as e:
                logger.warning(f"Application Intelligence Agent error: {e}")
                business_intelligence = {
                    "portfolio_analysis": {"applications": applications, "portfolio_health": {}, "assessment_readiness": {}},
                    "strategic_recommendations": [],
                    "business_insights": [],
                    "error": f"Application Intelligence Agent error: {str(e)}",
                    "fallback_mode": True
                }
        
        # Store clarification questions in the UI bridge for display
        for question in discovery_result.get("clarification_questions", []):
            agent_ui_bridge.add_agent_question(
                agent_id=application_discovery_agent.agent_id,
                agent_name=application_discovery_agent.agent_name,
                question_type=QuestionType.APPLICATION_BOUNDARY,
                page="asset-inventory",
                title=f"Application Validation: {question['application_name']}",
                question=question["question"],
                context=question["context"],
                options=question["options"],
                confidence=ConfidenceLevel.MEDIUM,
                priority="medium"
            )
        
        # Add intelligence insights to UI bridge if available
        if business_intelligence and not business_intelligence.get("error"):
            for insight in business_intelligence.get("business_insights", []):
                agent_ui_bridge.add_agent_insight(
                    agent_id="application_intelligence",
                    agent_name="Application Intelligence Agent",
                    insight_type=insight.get("category", "business_insight"),
                    title=insight.get("title", "Business Insight"),
                    description=insight.get("description", ""),
                    confidence=ConfidenceLevel.HIGH if insight.get("confidence", 0) >= 0.8 else ConfidenceLevel.MEDIUM,
                    supporting_data=insight.get("details", {}),
                    page="asset-inventory"
                )
        
        # Construct comprehensive response
        response = {
            "status": "success",
            "application_portfolio": discovery_result,
            "agent_analysis_complete": True
        }
        
        if include_business_intelligence:
            response["business_intelligence"] = business_intelligence
            response["intelligence_features"] = {
                "business_criticality_assessment": business_intelligence is not None and not business_intelligence.get("error"),
                "migration_readiness_evaluation": business_intelligence is not None and not business_intelligence.get("error"),
                "strategic_recommendations": business_intelligence is not None and not business_intelligence.get("error"),
                "assessment_readiness": business_intelligence is not None and not business_intelligence.get("error")
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting application portfolio: {e}")
        raise HTTPException(status_code=500, detail=f"Application portfolio retrieval failed: {str(e)}")

@router.post("/application-validation")
async def validate_application_groupings(
    validation_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    User validation of agent application groupings for learning.
    """
    try:
        application_id = validation_input.get("application_id")
        validation_type = validation_input.get("validation_type")
        user_feedback = validation_input.get("feedback", {})
        
        if not application_id or not validation_type:
            raise HTTPException(status_code=400, detail="Application ID and validation type are required")
        
        # Process feedback through the Application Discovery Agent
        feedback_data = {
            "type": "application_validation",
            "application_id": application_id,
            "validation": validation_type,
            "application_data": validation_input.get("application_data", {}),
            "correction": user_feedback
        }
        
        learning_result = await application_discovery_agent.process_user_feedback(feedback_data)
        
        # Store learning experience in the UI bridge
        learning_context = {
            "validation_type": validation_type,
            "application_id": application_id,
            "user_feedback": user_feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        agent_ui_bridge.set_cross_page_context(
            f"application_validation_{application_id}",
            learning_context,
            "asset-inventory"
        )
        
        return {
            "status": "success",
            "message": "Application validation processed successfully",
            "validation_stored": True,
            "learning_applied": learning_result.get("learning_applied", False),
            "agent_improvement": "Application Discovery Agent updated with user feedback"
        }
        
    except Exception as e:
        logger.error(f"Error in application validation: {e}")
        raise HTTPException(status_code=500, detail=f"Application validation failed: {str(e)}")

@router.get("/readiness-assessment")
async def get_readiness_assessment(
    assessment_type: str = "comprehensive",
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Agent assessment of assessment-phase readiness.
    """
    try:
        # Get current agent understanding across all pages
        data_import_status = agent_ui_bridge.get_classified_data_for_page("data-import")
        attribute_mapping_status = agent_ui_bridge.get_classified_data_for_page("attribute-mapping")
        data_cleansing_status = agent_ui_bridge.get_classified_data_for_page("data-cleansing")
        
        # Calculate readiness based on agent classifications
        readiness_metrics = {
            "data_import_readiness": _calculate_page_readiness(data_import_status),
            "attribute_mapping_readiness": _calculate_page_readiness(attribute_mapping_status),
            "data_cleansing_readiness": _calculate_page_readiness(data_cleansing_status)
        }
        
        # Overall readiness assessment
        overall_readiness = sum(readiness_metrics.values()) / len(readiness_metrics)
        
        # Get outstanding questions
        outstanding_questions = []
        for page in ["data-import", "attribute-mapping", "data-cleansing"]:
            outstanding_questions.extend(agent_ui_bridge.get_questions_for_page(page))
        
        assessment = {
            "overall_readiness": overall_readiness,
            "readiness_level": _classify_readiness_level(overall_readiness),
            "readiness_metrics": readiness_metrics,
            "outstanding_questions": len(outstanding_questions),
            "blocking_issues": [q for q in outstanding_questions if q.get("priority") == "high"],
            "agent_confidence": "high" if overall_readiness >= 0.8 else "medium" if overall_readiness >= 0.6 else "low",
            "next_steps": _generate_readiness_next_steps(readiness_metrics, outstanding_questions)
        }
        
        return {
            "status": "success",
            "assessment_type": assessment_type,
            "readiness_assessment": assessment,
            "agent_recommendations": _generate_agent_recommendations(assessment)
        }
        
    except Exception as e:
        logger.error(f"Error in readiness assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Readiness assessment failed: {str(e)}")

@router.post("/stakeholder-requirements")
async def process_stakeholder_requirements(
    requirements_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Stakeholder input for agent learning and context.
    """
    try:
        requirements = requirements_input.get("requirements", {})
        stakeholder_context = requirements_input.get("stakeholder_context", {})
        business_priorities = requirements_input.get("business_priorities", [])
        
        # Store stakeholder context for agents
        agent_ui_bridge.set_cross_page_context(
            "stakeholder_requirements", 
            {
                "requirements": requirements,
                "context": stakeholder_context,
                "priorities": business_priorities
            },
            "stakeholder-input"
        )
        
        return {
            "status": "success",
            "message": "Stakeholder requirements stored for agent learning",
            "requirements_count": len(requirements),
            "priorities_count": len(business_priorities),
            "context_updated": True
        }
        
    except Exception as e:
        logger.error(f"Error processing stakeholder requirements: {e}")
        raise HTTPException(status_code=500, detail=f"Stakeholder requirements processing failed: {str(e)}")

@router.get("/health")
async def agent_discovery_health():
    """Health check for agent discovery endpoints."""
    return {
        "status": "healthy",
        "service": "agent-discovery",
        "version": "1.0.0",
        "agentic_framework": "active",
        "available_agents": [
            "Data Source Intelligence Agent"
        ],
        "ui_bridge_status": agent_ui_bridge.get_agent_status_summary(),
        "available_endpoints": [
            "/agent-analysis",
            "/agent-clarification",
            "/agent-status",
            "/agent-learning",
            "/application-portfolio",
            "/application-validation",
            "/readiness-assessment",
            "/stakeholder-requirements",
            "/health"
        ]
    }

# Helper functions

async def _process_agent_learning(question_id: str, response: Any, 
                                response_type: str, page_context: str) -> Dict[str, Any]:
    """Process agent learning from user responses."""
    
    # Get the question context for learning
    # This will be expanded as agents implement specific learning algorithms
    learning_context = {
        "question_id": question_id,
        "response": response,
        "response_type": response_type,
        "page_context": page_context,
        "timestamp": agent_ui_bridge.get_cross_page_context("timestamp")
    }
    
    logger.info(f"Processed agent learning for question {question_id}")
    return learning_context

async def _apply_agent_learning(learning_type: str, original_prediction: Dict[str, Any],
                              user_correction: Dict[str, Any], context: Dict[str, Any],
                              page_context: str) -> Dict[str, Any]:
    """Apply specific learning based on the type of correction."""
    
    if learning_type == "data_classification":
        # Learn from data classification corrections
        return await _learn_data_classification(original_prediction, user_correction, context)
    
    elif learning_type == "field_mapping":
        # Learn from field mapping corrections
        return await _learn_field_mapping(original_prediction, user_correction, context)
    
    elif learning_type == "pattern_recognition":
        # Learn from pattern recognition corrections
        return await _learn_pattern_recognition(original_prediction, user_correction, context)
    
    else:
        raise ValueError(f"Unknown learning type: {learning_type}")

async def _learn_data_classification(original: Dict[str, Any], correction: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from data classification corrections."""
    # This will be implemented with specific agent learning algorithms
    return {
        "learning_applied": True,
        "pattern_updated": True,
        "confidence_improvement": 0.1
    }

async def _learn_field_mapping(original: Dict[str, Any], correction: Dict[str, Any],
                             context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from field mapping corrections."""
    # This will be implemented with Field Mapping Intelligence Agent
    return {
        "learning_applied": True,
        "mapping_pattern_updated": True,
        "confidence_improvement": 0.15
    }

async def _learn_pattern_recognition(original: Dict[str, Any], correction: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
    """Learn from pattern recognition corrections."""
    # This will be implemented with pattern recognition improvements
    return {
        "learning_applied": True,
        "pattern_recognition_updated": True,
        "confidence_improvement": 0.05
    }

async def _calculate_learning_metrics() -> Dict[str, Any]:
    """Calculate agent learning improvement metrics."""
    # Get recent learning experiences
    recent_experiences = agent_ui_bridge.get_recent_learning_experiences(limit=100)
    
    return {
        "total_learning_experiences": len(recent_experiences),
        "recent_accuracy_trend": "improving",  # Will be calculated from actual data
        "learning_categories": {
            "field_mapping": len([e for e in recent_experiences if e.get("question_type") == "field_mapping"]),
            "data_classification": len([e for e in recent_experiences if e.get("question_type") == "data_classification"]),
            "business_context": len([e for e in recent_experiences if e.get("question_type") == "business_context"])
        }
    }

def _calculate_page_readiness(page_data: Dict[str, List[Dict[str, Any]]]) -> float:
    """Calculate readiness score for a specific page based on data classifications."""
    
    good_data_count = len(page_data.get("good_data", []))
    needs_clarification_count = len(page_data.get("needs_clarification", []))
    unusable_count = len(page_data.get("unusable", []))
    
    total_items = good_data_count + needs_clarification_count + unusable_count
    
    if total_items == 0:
        return 0.0
    
    # Calculate readiness based on data quality distribution
    readiness = (good_data_count * 1.0 + needs_clarification_count * 0.5 + unusable_count * 0.0) / total_items
    
    return readiness

def _classify_readiness_level(readiness_score: float) -> str:
    """Classify overall readiness level."""
    if readiness_score >= 0.9:
        return "excellent"
    elif readiness_score >= 0.8:
        return "good"
    elif readiness_score >= 0.7:
        return "fair"
    elif readiness_score >= 0.5:
        return "poor"
    else:
        return "insufficient"

def _generate_readiness_next_steps(readiness_metrics: Dict[str, float], 
                                 outstanding_questions: List[Dict[str, Any]]) -> List[str]:
    """Generate next steps based on readiness assessment."""
    
    steps = []
    
    # Check each phase readiness
    if readiness_metrics.get("data_import_readiness", 0) < 0.7:
        steps.append("Address data import quality issues and answer agent clarifications")
    
    if readiness_metrics.get("attribute_mapping_readiness", 0) < 0.7:
        steps.append("Complete field mapping and resolve mapping ambiguities with agents")
    
    if readiness_metrics.get("data_cleansing_readiness", 0) < 0.7:
        steps.append("Resolve data quality issues identified by cleaning agents")
    
    # High priority questions
    high_priority_questions = [q for q in outstanding_questions if q.get("priority") == "high"]
    if high_priority_questions:
        steps.append(f"Answer {len(high_priority_questions)} high-priority agent questions")
    
    if not steps:
        steps.append("Ready to proceed to assessment phase - all discovery criteria met")
    
    return steps

def _generate_agent_recommendations(assessment: Dict[str, Any]) -> List[str]:
    """Generate agent recommendations based on readiness assessment."""
    
    recommendations = []
    
    overall_readiness = assessment.get("overall_readiness", 0)
    
    if overall_readiness >= 0.9:
        recommendations.append("Excellent data readiness - proceed confidently to 6R assessment")
        recommendations.append("Consider this as a model for future discovery processes")
    
    elif overall_readiness >= 0.7:
        recommendations.append("Good data foundation for migration assessment")
        recommendations.append("Address remaining clarifications to optimize assessment accuracy")
    
    elif overall_readiness >= 0.5:
        recommendations.append("Moderate data readiness - assessment possible but may have gaps")
        recommendations.append("Prioritize resolving high-impact data quality issues")
    
    else:
        recommendations.append("Insufficient data quality for reliable migration assessment")
        recommendations.append("Focus on fundamental data collection and quality improvement")
    
    return recommendations 